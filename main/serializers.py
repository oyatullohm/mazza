# from  product.serializers import PropertySerializer
from rest_framework import serializers
from .models import *
from django.db.models import Q

class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    role = serializers.CharField(required=False)
    

class UserSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)  
    class Meta:
        model = CustomUser
        fields = ('id', 'phone', 'email', 'role', 'image')
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class MessageSerializer(serializers.ModelSerializer):
    i = serializers.SerializerMethodField()
    sender = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ['id', 'i', 'sender', 'room',  'content', 'timestamp','flowed']
    
    def get_i(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.sender.id == request.user.id
        return False
    
class ChatRoomSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(source='unread_count_db', read_only=True)

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'property',
            'user',
            'user_1',
            'user_2',
            'owner',
            'last_message',
            'room_name',
            'created_at',
            'unread_count'
        ]

    def get_user(self, obj):
        request = self.context.get('request')
        if request.user.id == obj.user_1.id:
            return UserSerializer(obj.user_2).data
        return UserSerializer(obj.user_1).data

    def get_last_message(self, obj):
        # Agar annotate orqali kelgan bo‘lsa
        if hasattr(obj, 'last_message_time'):
            if not obj.last_message_time:
                return None
            return {
                'content': obj.last_message_content,
                'timestamp': obj.last_message_time,
                'sender_id': obj.last_message_sender_id,
            }

        # Agar annotate YO‘Q bo‘lsa (masalan chat_create)
        last_message = obj.messages.order_by('-timestamp').first()
        if not last_message:
            return None

        return {
            'content': last_message.content,
            'timestamp': last_message.timestamp,
            'sender_id': last_message.sender_id,
        }
class BalansSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Balans
        fields = ('id', 'user', 'balans')