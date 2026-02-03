from product.viewsets import PropertyPagination
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.dateparse import parse_date
from datetime import timedelta , date
from rest_framework import viewsets
from django.utils import timezone 
from .permissions import IsAgent
from django.db.models import Q
from decimal import Decimal
from rest_framework import status
from .serializers import *
from .models import *


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer

    def get_queryset(self):
        return Property.objects.filter(user=self.request.user)\
            .select_related('user','region', 'category')\
            .prefetch_related('items',
                              'items__image',
                              'items__access_times',
                              'items__rules',
                              'items__comfortable'
                              )

    def get_permissions(self):

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsAgent]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        name = data['name']
        region = data['region']
        category = data['category']
        rating = data['rating']
        info = data['info']
        lat = data['lat']
        lon = data['lon']
        image = data['image']
        property = Property.objects.create(
            user=user,
            name=name,
            region_id=region,
            category_id=category,
            rating=rating,
            info=info,
            lat=lat,
            lon=lon,
            image=image
        )
        return Response({"status": "success", "data": PropertySerializer(property).data}, status=201)
     
    def update(self, request, *args, **kwargs):
        data = request.data
        name = data.get('name')
        region = data.get('region')
        category = data.get('category')
        rating = data.get('rating')
        info = data.get('info')
        lat = data.get('lat')
        lon = data.get('lon')
        image = data.get('image')
        property = self.get_object()
        if name:
            property.name = name
        if region:
            property.region_id = region
        if category:
            property.category_id = category
        if rating:
            property.rating = rating
        if info:
            property.info = info
        if lat:
            property.lat = lat
        if lon:
            property.lon = lon
        if image:
            try:
                property.image.delete(save=False)
            except:
                pass
            property.image = image
        property.save()
        return Response({"status": "success", "data": PropertySerializer(property).data}, status=200)

class PropertyItemViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyItemSerializer

    
    def get_queryset(self):
        return PropertyItem.objects.filter(property__user=self.request.user)\
            .select_related('property', 'property__user')\
            .prefetch_related('images','comfortable','rules','access_times')

    def get_permissions(self):

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsAgent]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        data = request.data
        property = data.get('property')
        name = data.get('name')
        price = data.get('price')
        sum = data.get('sum')
        comfortable = data.get('comfortable')
        access_exit = data.get('access_exit')
        the_rule = data.get('the_rule')
        info = data.get('info')
      
        property_item = PropertyItem.objects.create(
            property_id=property,
            name=name,
            price=price,
            info=info,
            sum=sum
        )
        if comfortable:
            for id in comfortable:
                try:
                    comf_obj = Comfortable.objects.get(id=id)
                    property_item.comfortable.add(comf_obj)
                except Comfortable.DoesNotExist:
                    continue
        if access_exit:
            for access in access_exit:
                date = AccessExitTime.objects.get(id=access)
                property_item.access_times.add(date)
        if the_rule:
            for rule in the_rule:
                the_rule_obj = The_rule.objects.get(id=rule)
                property_item.rules.add(the_rule_obj)

            
        return Response({"status": "success", "data": PropertyItemSerializer(property_item).data}, status=201)
    
    def update(self, request, *args, **kwargs):
        data = request.data
        property_item = self.get_object()
        name = data.get('name')
        price = data.get('price')
        sum = data.get('sum')
        access_exit = data.get('access_exit')
        the_rule = data.get('the_rule')
        info = data.get('info')
        if name:
            property_item.name = name
        if price:
            property_item.price = price
        if sum:
               property_item.sum = sum
        if info:
            property_item.info = info
        if access_exit:
            dates = Date.objects.filter(id__in=access_exit)
            property_item.access_exit.set(dates)

        if the_rule:
            rules = The_rule.objects.filter(id__in=the_rule)
            property_item.the_rule.set(rules)
        property_item.save()
        return Response({"status": "success", "data": PropertyItemSerializer(property_item).data}, status=200)
    
    @action(detail=True, methods=['post'], url_path='add-images')
    def add_images(self, request, pk=None):
        property_item = self.get_object()
        images = request.FILES.getlist('images')
        if images and len(images) + property_item.images.count() <= 5:
            for img in images:
                img_instance = Images.objects.create(
                    image=img
                )
                property_item.images.add(img_instance)
            return Response({"status": "success", "data": PropertyItemSerializer(property_item).data}, status=200)
        else:
            return Response({"status": "error", "message": "Maximum 5 images are allowed."}, status=400)
    
    @action(detail=True, methods=['post'], url_path='remove-image')
    def remove_image(self, request, pk=None):
        property_item = self.get_object()
        image_id = request.data.get('image_id')
        try:
            image = Images.objects.get(id=image_id)
            property_item.images.remove(image)
            image.image.delete(save=False)
            image.delete()
            return Response({"status": "success", "data": PropertyItemSerializer(property_item).data}, status=200)
        except Images.DoesNotExist:
            return Response({"status": "error", "message": "Image not found."}, status=404) 

    
    @action(methods=['get'], detail=True)
    def calendar(self, request, *args, **kwargs):
        try:
            property_item = PropertyItem.objects.get(id=kwargs['pk'])
        except PropertyItem.DoesNotExist:
            return Response({'detail': 'Property item not found'}, status=404)
        
        today = date.today()
        start_date = today
        end_date = today + timedelta(days=30)
        
        # 📊 Barcha bookinglarni bir queryda olish
        bookings = Booking.objects.filter(
            item=property_item,
            date_access__lte=end_date,
            date_exit__gte=start_date
        ).filter(
            Q(is_paid=True) | 
            Q(is_paid=False, created_at__gte=timezone.now() - timedelta(hours=3))
        ).select_related('access_times')
        
        # 🔄 Kun bo'yicha guruhlash
        bookings_by_date = {}
        for booking in bookings:
            # Bookingning barcha kunlarini kiritamiz
            current = max(booking.date_access, start_date)
            last = min(booking.date_exit, end_date)
            
            while current <= last:
                if current not in bookings_by_date:
                    bookings_by_date[current] = []
                
                bookings_by_date[current].append(booking)
                current += timedelta(days=1)
        
        # 📅 Kalendar ma'lumotlari
        calendar_data = []
        current_date = start_date
        
        # Barcha vaqt slotlari
        all_time_slots = list(property_item.access_times.all())
        all_slot_ids = set(slot.id for slot in all_time_slots)
        
        while current_date <= end_date:
            day_bookings = bookings_by_date.get(current_date, [])
            
            # 🔍 HOLATNI ANIQLASH
            status = "bo'sh"
            
            if day_bookings:
                # TO'LIQ KUNLIK BRON TEKSHIRISH
                has_full_day = False
                has_hourly = False
                hourly_slot_ids = set()
                
                for booking in day_bookings:
                    # Kunlik bron (bir necha kun yoki access_times yo'q)
                    if (booking.date_access != booking.date_exit or 
                        booking.access_times is None):
                        has_full_day = True
                        break
                    
                    # Soatli bron (bir kun, access_times bor)
                    if (booking.date_access == current_date == booking.date_exit and 
                        booking.access_times):
                        has_hourly = True
                        hourly_slot_ids.add(booking.access_times.id)
                
                if has_full_day:
                    status = "to'liq band"
                elif has_hourly:
                    if hourly_slot_ids == all_slot_ids:
                        status = "to'liq band"
                    else:
                        status = "qisman band"
            
            # 📋 Vaqt slotlari holati
            time_slots_info = []
            if all_time_slots:
                for slot in all_time_slots:
                    is_booked = any(
                        b for b in day_bookings 
                        if b.access_times and 
                        b.access_times.id == slot.id and
                        b.date_access == current_date == b.date_exit
                    )
                    
                    time_slots_info.append({
                        'id': slot.id,
                        'time': f"{slot.access.strftime('%H:%M')} - {slot.exit.strftime('%H:%M')}",
                        'is_available': not is_booked
                    })
            
            calendar_data.append({
                'date': current_date.isoformat(),
                'status': status,
                # 'is_today': current_date == today,
                'time_slots': time_slots_info
            })
            
            current_date += timedelta(days=1)
        
        return Response({
            'calendar': calendar_data
        })
    
    
class AgentBookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAgent]
    pagination_class = PropertyPagination

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
        payment = data.get('payment')
        if not date_access or not date_exit:
            return Response({'detail': 'Dates required'}, status=400)

        if date_exit < date_access:
            return Response(
                {'detail': 'date_exit cannot be before date_access'},
                status=400
            )

        access_time = None

        # =========================
        # 🕒 VAQT ORALIG'I TEKSHIRISH
        # =========================
        access_time_id = data.get('access_times')
        if access_time_id:
            try:
                access_time = AccessExitTime.objects.get(id=access_time_id)
            except AccessExitTime.DoesNotExist:
                return Response(
                    {'detail': 'Access time not found'},
                    status=404
                )

        # =========================
        # 🚫 BANDLIKNI TEKSHIRISH
        # =========================
        conflict_query = Booking.objects.filter(
            item=item,
            date_access=date_access,
            date_exit=date_exit
        ).exclude(status='Rad etilgan')

        if access_time:
            conflict_query = conflict_query.filter(access_times=access_time)
        else:
            conflict_query = conflict_query.exclude(access_times__isnull=False)

        # 🔥 3 soat qoidasi
        now = timezone.now()
        three_hours_ago = now - timedelta(hours=3)

        active_conflicts = conflict_query.filter(
            Q(is_paid=True) |
            Q(created_at__gte=three_hours_ago, is_paid=False)
        )

        if active_conflicts.exists():
            old_unpaid = conflict_query.filter(
                is_paid=False,
                created_at__lt=three_hours_ago
            )
            
            if old_unpaid.exists() and not active_conflicts.filter(is_paid=True).exists():
                old_unpaid.delete()
            else:
                return Response(
                    {'detail': 'Bu vaqt oraligʻi allaqachon band qilingan'},
                    status=400
                )


        # =========================
        booking = Booking.objects.create(
            user=request.user,
            item=item,
            access_times=access_time,
            date_access=date_access,
            date_exit=date_exit,
            phone_number=data.get('phone_number'),
            payment=payment,
            status='Kutilmoqda',
            is_paid=False
        )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )

    def list(self, request):
        queriset = self.get_queryset().filter(date_access__gte=date.today())
        return Response(BookingSerializer(queriset, many=True).data)

    @action(methods=['get'], detail=False)
    def arhive(self, request):
        queriset = self.get_queryset().filter(date_access__lt=date.today())
        return Response(BookingSerializer(queriset, many=True).data)
    
    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(item__property__user=user).select_related('item','user','access_times')

    @action(methods=['get'], detail=False)
    def today(self, request):
        bookings = self.get_queryset().filter(date_access=date.today())
        return Response({
            'booking': BookingSerializer(bookings, many=True).data,
            'count': bookings.count()
            
        })
    @action(detail=True, methods=['post'])
    def cancel(self, request, *args, **kwargs):
        try:
            booking = self.get_queryset().get(id=kwargs['pk'])  
        except Booking.DoesNotExist:
            return Response({'success': False, 'data': 'Booking not found'}, status=404)

        if booking.user == request.user and not booking.is_paid:
            booking.status = 'Rad etilgan'
            booking.is_active = False
            booking.save()
            return Response(BookingSerializer(booking).data)
        elif booking.item.property.user == request.user and not booking.is_paid:
            booking.status = 'Rad etilgan'
            booking.is_active = False
            booking.save()
            return Response(BookingSerializer(booking).data)
        return Response({'success':False,
                         'data':'no authorized'})
            
class AccessExitTimeViewSet(viewsets.ModelViewSet):
    queryset = AccessExitTime.objects.all()
    serializer_class = AccessExitTimeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsAgent]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]