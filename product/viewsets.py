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

from rest_framework.viewsets import ReadOnlyModelViewSet
from django.db.models import OuterRef, Subquery, DecimalField
from django.db.models.functions import Coalesce
from rest_framework.permissions import AllowAny

class PropertyPagination(PageNumberPagination):
    page_size = 2


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


class BookingPropertyItemViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyItemSerializer
    http_method_names = ['get']
    permission_classes = [AllowAny]

    def get_queryset(self):
        property_id = self.request.query_params.get('property')
        return PropertyItem.objects.filter(is_active=True, property_id=property_id)\
            .select_related('property', 'property__region', 'property__category', 'property__user')\
            .prefetch_related(
                'rules',
                'images',
                'comfortable',
                'access_times'
            )  

    