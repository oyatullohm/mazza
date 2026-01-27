from .models import AccessExitTime, CurrencyRate, PropertyItem, Region, The_rule, Comfortable, Property, Images, Category
from rest_framework import serializers


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'state', 'name']


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ['id', 'rate']


class TheRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = The_rule
        fields = ['id', 'name', 'image']


class ComfortableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comfortable
        fields = ['id',  'name', 'image']


class PropertySerializer(serializers.ModelSerializer):
    min_price = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    mini_sum = serializers.CharField(read_only=True)

    class Meta:
        model = Property
        fields = (
            'id', 'user', 'region', 'category',
            'name', 'info', 'lat', 'lon',
            'image', 'rating', 'min_price',
            'mini_sum'
        )


class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ('id', 'image')


class AccessExitTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessExitTime
        fields = ('id','access', 'exit','intermediate_time')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'icon')

       
class PropertyItemSerializer(serializers.ModelSerializer):
    # property = PropertySerializer(read_only=True)
    images = ImagesSerializer(many=True, read_only=True)
    comfortable = ComfortableSerializer(many=True, read_only=True)
    rules = TheRuleSerializer(many=True, read_only=True)
    access_times = AccessExitTimeSerializer(many=True, read_only=True)

    class Meta:
        model = PropertyItem
        fields = (
            'id',
            'name',
            'price',
            'sum',
            'is_active',
            'info',
            # 'property',
            'images',
            'comfortable',
            'rules',
            'access_times',
        )
