from django.contrib import admin
from .models import Region, The_rule, Comfortable, Property, Images, Category, PropertyItem ,AccessExitTime , CurrencyRate
# Register your models here.
admin.site.register(Region)
admin.site.register(AccessExitTime)
admin.site.register(The_rule)
admin.site.register(Comfortable)
admin.site.register(Property)
admin.site.register(Images)
admin.site.register(CurrencyRate)
admin.site.register(Category)
admin.site.register(PropertyItem)
