from rest_framework.permissions import IsAuthenticated ,AllowAny
from django.db.models import OuterRef, Subquery, DecimalField
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

        item = PropertyItem.objects.select_related().get(id=data.get('item'))

        date_access = parse_date(data.get('date_access'))
        date_exit = parse_date(data.get('date_exit'))

        if not date_access or not date_exit or date_exit <= date_access:
            return Response(
                {'detail': 'Date exit must be greater than date access'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1️⃣ Kunlar soni
        days = (date_exit - date_access).days

        # 2️⃣ Asosiy narx
        base_price = item.price * Decimal(days)

        # 3️⃣ Valyuta bo‘yicha hisoblash
        if item.sum == 'USD':
            rate = CurrencyRate.objects.last()
            if not rate:
                return Response(
                    {'detail': 'Currency rate not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            base_price = base_price * rate.rate

        # 4️⃣ 15% komissiya
        total_payment = base_price + (base_price * Decimal('0.15'))

        # 5️⃣ Booking yaratish
        booking = Booking.objects.create(
            user=request.user,
            item=item,
            access_times_id=data.get('access_times'),
            date_access=date_access,
            date_exit=date_exit,
            phone_number=data.get('phone_number'),
            payment=total_payment
        )

        return Response(
            {
                'id': booking.id,
                'payment': booking.payment,
                'days': days,
                'currency': 'UZS',
            },
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
        booking = Booking.objects.get(id=kwargs['pk'])  
        booking.is_paid = True
        booking.status = 'Tasdiqlangan'
        booking.save()
        return Response(BookingSerializer(booking).data)
    
    def destroy(self, request, *args, **kwargs):
        booking = Booking.objects.get(id=kwargs['pk'])
        booking.is_active = False
        booking.save()
        return Response({'detail': 'Booking deleted successfully.'})

class ComentariyaViewSet(viewsets.ModelViewSet):
    serializer_class = ComentariyaSerializer
    # permission_classes = [IsAuthenticated]
    pagination_class = PropertyPagination 
    def get_queryset(self):
        return super().get_queryset()\
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