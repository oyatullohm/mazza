
from rest_framework import serializers
from .models import *

class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    role = serializers.CharField(required=False)
    

class UserSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)  
    class Meta:
        model = CustomUser
        fields = ('phone', 'email', 'role', 'image')
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

