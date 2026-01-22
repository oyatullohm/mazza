from django.db import models
from main.models import CustomUser

class Region(models.Model):
    state =  models.CharField(max_length=55)
    name = models.CharField(max_length=55)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=55)
    icon = models.ImageField(
        upload_to='icons/',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
    
class Comfortable(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='comfortable_items')
    name = models.CharField(max_length=55)
    image = models.ImageField(upload_to="comfortable/")


class Images(models.Model):
    image = models.ImageField(upload_to='images/')


class Date(models.Model):
    """
    bu class kirish chiqish vaqtlari masalan 1 PropertyItem odata 10:00 dan 18:00 gacha
    belgilashi mumkin 
    """
    access = models.TimeField()
    exit = models.TimeField()


class The_rule(models.Model):
    "qoidalar"
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="the_rule/")


class Property(models.Model):
    user = models.ForeignKey(CustomUser, on_delete= models.CASCADE, related_name='property')
    name = models.CharField(max_length=255)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, related_name='regions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='categories')
    comfortable = models.ManyToManyField(Comfortable, related_name='comfortables')
    rating = models.FloatField()
    info = models.TextField()
    lat = models.FloatField()
    lon = models.FloatField()

class PropertyItem(models.Model):
    SUMMA_TYPE = (
        ("UZS","UZS"),
        ("USD","USD"),
        ("RU","RU"),
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='propertys')
    image = models.ManyToManyField(Images, related_name='images')
    name = models.CharField(max_length=55)
    price = models.DecimalField(max_digits=15,decimal_places=2)
    sum = models.CharField(max_length=5, choices=SUMMA_TYPE)
    access_exit = models.ManyToManyField(Date, related_name='access_exit_items')
    the_rule = models.ManyToManyField(The_rule, related_name='the_rule_items')
    is_active = models.BooleanField(default=True)

 
class Order(models.Model):
    TYPE_CHOICES = [
        ('Rad etilgan', 'Rad etilgan'),
        ('Kutilmoqda', 'Kutilmoqda'),
        ('Tasdiqlangan', 'Tasdiqlangan'),
        ('Tugallangan', 'Tugallangan'),
        
    ]
    user = models.ForeignKey(CustomUser, on_delete= models.CASCADE, related_name='orders')
    item = models.ForeignKey(PropertyItem, on_delete=models.CASCADE, related_name='orders')
    is_paid = models.BooleanField(default=False)
    payment = models.DecimalField(max_digits=15, decimal_places=2)
    date_access = models.DateTimeField()
    date_exit = models.DateTimeField()
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, choices=TYPE_CHOICES, default='Kutilmoqda')
    is_active = models.BooleanField(default=True)