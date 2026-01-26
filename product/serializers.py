from rest_framework import serializers
from .models import AccessExitTime, CurrencyRate, PropertyItem, Region, The_rule, Comfortable, Property, Images, Category

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = '__all__'

class TheRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = The_rule
        fields = '__all__'

class ComfortableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comfortable
        fields = '__all__'

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'
        # depth = True

class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = '__all__'

class AccessExitTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessExitTime
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        
class PropertyItemSerializer(serializers.ModelSerializer):
    property = PropertySerializer(read_only=True)
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
            'property',
            'images',
            'comfortable',
            'rules',
            'access_times',
        )
