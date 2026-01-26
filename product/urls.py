from django.contrib import admin
from django.urls import path
from . import admin_viewsets
from . import agent_viewserts
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'regions', admin_viewsets.RegionViewSet, basename='region')
router.register(r'courses', admin_viewsets.CurrencyRateViewSet, basename='course')
router.register(r'categories', admin_viewsets.CategoryViewSet, basename='category')
router.register(r'the_rules', admin_viewsets.TheRuleViewSet, basename='the_rule')
router.register(r'comfortables', admin_viewsets.ComfortableViewSet, basename='comfortable')
router.register(r'dates', admin_viewsets.AccessExitTimeViewSet, basename='date')
router.register(r'properties', agent_viewserts.PropertyViewSet, basename='property')
router.register(r'propertiesitems', agent_viewserts.PropertyItemViewSet, basename='propertyitem')

urlpatterns = [

]
urlpatterns += router.urls