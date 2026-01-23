
from django.contrib import admin
from django.urls import path, include
from main.views import test
urlpatterns = [
    
    path('admin/', admin.site.urls),
    path('apiv1/product/', include('product.urls')),
    path('api/', include('main.urls')),
    path('test/', test)
  
]
