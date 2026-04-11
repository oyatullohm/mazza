
from django.contrib import admin
from django.urls import path, include
import os
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from product.click import (
    ClickWebhookAPIView,
    create_payment_link,
    payment_success,
    booking_detail
)
urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Brauzerda sinash uchun Swagger interfeysi
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('product.urls')),
    path('api/', include('main.urls')),
    
    path('api/click/webhook/', ClickWebhookAPIView.as_view()),
    path('api/payment-link/<int:booking_id>/', create_payment_link),
    path('api/payment-success/<int:order_id>/', payment_success),
    path('api/booking/<int:pk>/', booking_detail),

]
