
from django.contrib import admin
from django.urls import path
from .views import (
    email_login
)
from .viewsets import (
    UserViewsets
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users',UserViewsets,basename='users')

urlpatterns = [
    path('login/email/', email_login)
]
urlpatterns+=router.urls