from rest_framework.permissions import IsAuthenticated ,AllowAny ,IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from .serializers import *
from .models import *
from django.db.models import Min, Q, Value ,OuterRef, Subquery, DecimalField
from django.db.models.functions import Coalesce
from rest_framework.viewsets import ReadOnlyModelViewSet

from rest_framework.pagination import PageNumberPagination

class PropertyPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20

class PropertyViewSet(ReadOnlyModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]
    pagination_class = PropertyPagination

    def get_queryset(self):
        min_item = (
            PropertyItem.objects
            .filter(
                property=OuterRef('pk'),
                is_active=True
            )
            .order_by('price')
        )

        return (
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
                min_sum=Subquery(
                    min_item.values('sum')[:1]
                )
            )
            .select_related(
                'user',
                'region',
                'category'
            )
        )
    def list(self, request, *args, **kwargs):
        category = request.query_params.get('category')
        region = request.query_params.get('region')
        
        if category:
            queryset = self.get_queryset().filter(category_id=category)
        if region:
            queryset = self.get_queryset().filter(region_id=region)
        return Response(PropertySerializer(queryset, many= True).data, status=200)
            

class PropertyItemViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyItemSerializer
    http_method_names = ['get']
    permission_classes = [AllowAny]
    def list(self,request,pk):
        queryset = self.get_queryset().filter(property_id=pk)
        serializer = PropertyItemSerializer(queryset, many=True)
        return Response(serializer.data)

    
    def get_queryset(self):
        return PropertyItem.objects.filter(is_active=True)\
            .select_related('property', 'property__region', 'property__category', 'property__user')\
            .prefetch_related(
                'rules',
                'images',
                'comfortable',
                'access_times'
            )   