from django.contrib import admin
from django.urls import path
from .views import *
from .viewsets import (
    UserViewsets,
    BalansViewset,
    BannerViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users',UserViewsets,basename='users')
router.register('balans',BalansViewset,basename='balans')
router.register(r'banners', BannerViewSet, basename='banners')
urlpatterns = [
   
    path('chat/chat-create/',chat_create, name='chat_create'),
    path('chat/chat-list/',chat_list, name='chat_list'),
    path('chat/message-create/<int:chat_id>/',message_create, name='message_create'),
    path('chat/message-list/<int:chat_id>/',message_list, name='message_list'),
    path('chat/message-delete/<int:pk>/',message_delete, name='message_delete'),
    path('chat/chat-delete/<int:pk>/',chat_delete, name='chat_delete'),

]
urlpatterns += router.urls