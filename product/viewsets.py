from rest_framework.permissions import IsAuthenticated ,AllowAny
from django.db.models import OuterRef, Subquery, DecimalField, Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.db.models.functions import Coalesce
from rest_framework.permissions import AllowAny
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from datetime import datetime
from decimal import Decimal
from .serializers import *
from .models import *

class PropertyPagination(PageNumberPagination):
    page_size = 20


class BookingPropertyViewSet(ReadOnlyModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]
    pagination_class = PropertyPagination   # 🔴 SHU YERDA

    def get_queryset(self):
        min_item = (
            PropertyItem.objects
            .filter(property=OuterRef('pk'), is_active=True)
            .order_by('price')
        )

        queryset = (
            Property.objects
            .annotate(
                min_price=Coalesce(
                    Subquery(min_item.values('price')[:1]),
                    0,
                    output_field=DecimalField(
                        max_digits=15,
                        decimal_places=2
                    )
                ),
                min_sum=Subquery(min_item.values('sum')[:1])
            )
            .select_related('user', 'region', 'category')
        )

        category = self.request.query_params.get('category')
        region = self.request.query_params.get('region')

        if category:
            queryset = queryset.filter(category_id=category)

        if region:
            queryset = queryset.filter(region_id=region)

        return queryset

    @action(methods=['get'],detail=True)
    def comentary(self, request, pk):
        property = Property.objects.get(id=pk)
        comments = property.comentariya.all().select_related('user','property').order_by('-id')
        return Response(ComentariyaSerializer(comments, many=True).data)



class BookingPropertyItemViewSet(ReadOnlyModelViewSet):
    serializer_class = PropertyItemSerializer
    permission_classes = [AllowAny]
    pagination_class = PropertyPagination 

    def get_queryset(self):
        property_id = self.request.query_params.get('property')

        if not property_id:
            return PropertyItem.objects.none()  # 🔥 ENG TO‘G‘RISI

        return (
            PropertyItem.objects
            .filter(
                is_active=True,
                property_id=property_id
            )
            .select_related('property')  # 🔴 minimal
            .prefetch_related(
                'rules',
                'images',
                'comfortable',
                'access_times'
            )
        )

    def retrieve(self, request, *args, **kwargs):
        property_item = PropertyItem.objects.get(id=kwargs['pk'])
        return Response(PropertyItemSerializer(property_item).data)
    

class BookingViewSet(ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PropertyPagination 

    def get_queryset(self):
        user = self.request.user
        return (
            Booking.objects.filter(
                user=user, is_active=True
            )
            .select_related('user','item','access_times')  # 🔴 minimal
        )



    def create(self, request, *args, **kwargs):
        data = request.data

        # 🔎 ITEM
        try:
            item = PropertyItem.objects.get(id=data.get('item'))
        except PropertyItem.DoesNotExist:
            return Response({'detail': 'Item not found'}, status=404)

        # 📅 DATES
        date_access = parse_date(data.get('date_access'))
        date_exit = parse_date(data.get('date_exit'))

        if not date_access or not date_exit:
            return Response({'detail': 'Dates required'}, status=400)

        if date_exit < date_access:
            return Response(
                {'detail': 'date_exit cannot be before date_access'},
                status=400
            )

        access_time = None
        base_price = Decimal('0')

        # =========================
        # 🕒 SOATLIK BRON
        # =========================
        if data.get('access_times'):
            try:
                access_time = AccessExitTime.objects.get(
                    id=data.get('access_times')
                )
            except AccessExitTime.DoesNotExist:
                return Response(
                    {'detail': 'Access time not found'},
                    status=404
                )

            start_dt = datetime.combine(date_access, access_time.access)
            end_dt = datetime.combine(date_access, access_time.exit)

            if end_dt <= start_dt:
                return Response(
                    {'detail': 'Exit time must be after access time'},
                    status=400
                )

            # ⏱ SOATLAR
            hours = Decimal(
                (end_dt - start_dt).seconds
            ) / Decimal('3600')

            # ❗ kamida 3 soat
            if hours < 3:
                return Response(
                    {'detail': 'Minimum booking time is 3 hours'},
                    status=400
                )

            # 🚫 BANDLIKNI TEKSHIRISH (OVERLAP + PAID)
            conflict_exists = Booking.objects.filter(
                item=item,
                date_access=date_access,
                is_paid=True,
                access_times__isnull=False,
            ).filter(
                Q(
                    access_times__access__lt=access_time.exit,
                    access_times__exit__gt=access_time.access,
                )
            ).exists()

            if conflict_exists:
                return Response(
                    {'detail': 'This time slot is already booked'},
                    status=400
                )

            base_price = item.price * hours

        # =========================
        # 📅 KUNLIK BRON
        # =========================
        else:
            days = (date_exit - date_access).days + 1

            # 🚫 AGAR SHU ORALIQDA PAID BRON BO‘LSA
            conflict_exists = Booking.objects.filter(
                item=item,
                is_paid=True,
                date_access__lte=date_exit,
                date_exit__gte=date_access,
            ).exists()

            if conflict_exists:
                return Response(
                    {'detail': 'This item is already booked for these dates'},
                    status=400
                )

            base_price = item.price * Decimal(days)

        # =========================
        # 💱 VALYUTA
        # =========================
        if item.sum == 'USD':
            rate = CurrencyRate.objects.last()
            if not rate:
                return Response(
                    {'detail': 'Currency rate not set'},
                    status=400
                )
            base_price = base_price * rate.rate

        # =========================
        # ➕ 15% KOMISSIYA
        # =========================
        total_payment = base_price + (base_price * Decimal('0.15'))

        # =========================
        # 💾 CREATE BOOKING
        # =========================
        booking = Booking.objects.create(
            user=request.user,
            item=item,
            access_times=access_time,
            date_access=date_access,
            date_exit=date_exit,
            phone_number=data.get('phone_number'),
            payment=total_payment,
            status='Kutilmoqda'
        )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )

        

    @action(detail=True, methods=['post'])
    def cancel(self, request, *args, **kwargs):
        booking = Booking.objects.get(id=kwargs['pk'])  
        booking.status = 'Rad etilgan'
        booking.save()
        return Response(BookingSerializer(booking).data)
    


    @action(detail=True, methods=['post'])
    def payment(self, request, *args, **kwargs):
        try:
            booking = Booking.objects.get(id=kwargs['pk'])
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found'}, status=404)

        # ❗ allaqachon to‘langan bo‘lsa
        if booking.is_paid:
            return Response(
                {'detail': 'This booking is already paid'},
                status=400
            )

        # =========================
        # 🕒 SOATLIK BRON
        # =========================
        if booking.access_times:
            conflict_exists = Booking.objects.filter(
                item=booking.item,
                date_access=booking.date_access,
                is_paid=True,
                access_times__isnull=False
            ).exclude(id=booking.id).filter(
                Q(
                    access_times__access__lt=booking.access_times.exit,
                    access_times__exit__gt=booking.access_times.access,
                )
            ).exists()

            if conflict_exists:
                return Response(
                    {
                        'detail': 'Another paid booking already exists for this time slot'
                    },
                    status=400
                )

        # =========================
        # 📅 KUNLIK BRON
        # =========================
        else:
            conflict_exists = Booking.objects.filter(
                item=booking.item,
                is_paid=True,
                date_access__lte=booking.date_exit,
                date_exit__gte=booking.date_access,
            ).exclude(id=booking.id).exists()

            if conflict_exists:
                return Response(
                    {
                        'detail': 'Another paid booking already exists for these dates'
                    },
                    status=400
                )

        # =========================
        # ✅ TO‘LOVNI TASDIQLASH
        # =========================
        booking.is_paid = True
        booking.status = 'Tasdiqlangan'
        booking.save(update_fields=['is_paid', 'status'])

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK
        )

        
    def destroy(self, request, *args, **kwargs):
        booking = Booking.objects.get(id=kwargs['pk'])
        booking.is_active = False
        booking.save()
        return Response({'detail': 'Booking deleted successfully.'})


class ComentariyaViewSet(viewsets.ModelViewSet):
    serializer_class = ComentariyaSerializer
    # permission_classes = [IsAuthenticated]
    # pagination_class = PropertyPagination 
    def get_queryset(self):
        return Comentariya.objects\
            .filter(property_id=self.request.query_params.get('property'))\
            .select_related('user','property')
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        data = request.data
        comentariya = Comentariya.objects.create(
            user=request.user,
            property_id=data.get('property'),
            text=data.get('text')
        )
        return Response(
            ComentariyaSerializer(comentariya).data,
            status=status.HTTP_201_CREATED
        )
    def update(self, request, *args, **kwargs):
        data = request.data
        comentariya = Comentariya.objects.get(id=kwargs['pk'])
        if comentariya.user != request.user:
            return Response(
                {'detail': 'You do not have permission to edit this comment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        comentariya.text = data.get('text', comentariya.text)
        comentariya.save()
        return Response(
            ComentariyaSerializer(comentariya).data,
            status=status.HTTP_200_OK
        )
    def destroy(self, request, *args, **kwargs):
        comentariya = Comentariya.objects.get(id=kwargs['pk'])
        if comentariya.user != request.user:
            return Response(
                {'detail': 'You do not have permission to delete this comment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        comentariya.delete()
        return Response({'detail': 'Comment deleted successfully.'})