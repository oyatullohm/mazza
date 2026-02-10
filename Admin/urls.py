
from django.contrib import admin
from django.urls import path, include
import os
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Brauzerda sinash uchun Swagger interfeysi
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('product.urls')),
    path('api/', include('main.urls')),

]
