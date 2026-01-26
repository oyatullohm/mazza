from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from .permissions import IsAgent
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
            .prefetch_related('image','comfortable','access_exit','the_rule')

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
                property_item.access_exit.add(date)
        if the_rule:
            for rule in the_rule:
                the_rule_obj = The_rule.objects.get(id=rule)
                property_item.the_rule.add(the_rule_obj)
        
            
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
    @ action(detail=True, methods=['post'], url_path='add-images')
    def add_images(self, request, pk=None):
        property_item = self.get_object()
        images = request.FILES.getlist('images')
        if images and len(images) + property_item.image.count() <= 5:
            for img in images:
                img_instance = Images.objects.create(
                    image=img
                )
                property_item.image.add(img_instance)
            return Response({"status": "success", "data": PropertyItemSerializer(property_item).data}, status=200)
        else:
            return Response({"status": "error", "message": "Maximum 5 images are allowed."}, status=400)
    @ action(detail=True, methods=['post'], url_path='remove-image')
    def remove_image(self, request, pk=None):
        property_item = self.get_object()
        image_id = request.data.get('image_id')
        try:
            image = Images.objects.get(id=image_id)
            property_item.image.remove(image)
            image.image.delete(save=False)
            image.delete()
            return Response({"status": "success", "data": PropertyItemSerializer(property_item).data}, status=200)
        except Images.DoesNotExist:
            return Response({"status": "error", "message": "Image not found."}, status=404) 
        