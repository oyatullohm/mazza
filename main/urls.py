
from django.contrib import admin
from django.urls import path
from .viewsets import (
    UserViewsets
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users',UserViewsets,basename='users')

urlpatterns = [
    
]
urlpatterns+=router.urls