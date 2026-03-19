from email.mime import message
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import  AllowAny, IsAuthenticated 
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from .models import CustomUser , Message , ChatRoom
from .serializers import *
from django.db.models import (
    Q, OuterRef, Subquery, Count, IntegerField, BooleanField
)
from Admin.settings import DEEPL_KEY
from django.db.models.functions import Coalesce
from rest_framework import status
from .fcm_service import FCMService
from deepl.exceptions import DeepLException
import deepl

from Admin.fcm import send_push_notification, send_bulk_push_notification

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_create(request):
    user_1 = request.user
    user_2_id = request.data.get('user_2_id')
    property = request.data.get('property')

    try:
        user_2 = CustomUser.objects.get(id=user_2_id)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if user_1.id == user_2.id:
        return Response({'error': 'Cannot create chat with yourself'}, status=status.HTTP_400_BAD_REQUEST)

    # ChatRoom nomini yaratish (kichik ID birinchi bo'lishi kerak)
    ids = sorted([user_1.id, user_2.id])
    room_name = f"chat_{ids[0]}_{ids[1]}"

    chat_room, created = ChatRoom.objects.get_or_create(

        user_1__in=[user_1, user_2],
        user_2__in=[user_1, user_2],
        defaults={'user_1': user_1, 'user_2': user_2, 'owner': user_1, 'room_name': room_name}
    )
    chat_room.property_id=property
    chat_room.save()
    serializer = ChatRoomSerializer(chat_room, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_list(request):
    user = request.user

    last_message_qs = (
        Message.objects
        .filter(room=OuterRef('pk'))
        .order_by('-timestamp')
    )

    chats = (
        ChatRoom.objects
        .filter(Q(user_1=user) | Q(user_2=user))
        .select_related('property', 'user_1', 'user_2', 'owner')
        .annotate(
            # 🔹 oxirgi xabar
            last_message_content=Subquery(
                last_message_qs.values('content')[:1]
            ),
            last_message_time=Subquery(
                last_message_qs.values('timestamp')[:1]
            ),
            last_message_sender_id=Subquery(
                last_message_qs.values('sender_id')[:1]
            ),

            # 🔹 unread count (eng muhim joy)
            unread_count_db=Count(
                'messages',
                filter=Q(
                    messages__flowed=False
                ) & ~Q(messages__sender=user),
            )
        )
        .order_by('-last_message_time')
    )

    serializer = ChatRoomSerializer(
        chats,
        many=True,
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def message_create(request, chat_id):
    user = request.user

    try:
        chat_room = ChatRoom.objects.select_related(
            'user_1',
            'user_2'
        ).get(id=chat_id)
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Chat room not found'}, status=404)

    if user.id not in (chat_room.user_1_id, chat_room.user_2_id):
        return Response({'error': 'Permission denied'}, status=403)

    message = Message.objects.create(
        sender=user,
        room=chat_room,
        content=request.data.get('content', ''),
        # image=request.FILES.get('image')
    )

    send_push_notification(
        chat_room.user_2.firebase_token,
        "New message",
        message.content[25:] + "..." if len(message.content) > 25 else message.content
    )
    serializer = MessageSerializer(
        message,
        context={'request': request}
    )
    return Response(serializer.data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_list(request, chat_id):
    user = request.user
    try:
        chat_room = ChatRoom.objects.select_related('user_1', 'user_2').get(id=chat_id)
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Chat room not found'}, status=status.HTTP_404_NOT_FOUND)

    if user != chat_room.user_1 and user != chat_room.user_2:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    other_user = (
            chat_room.user_2 
            if chat_room.user_1 == request.user 
            else chat_room.user_1
        )
        
    
    messages = Message.objects.filter(room=chat_room).select_related('sender','room').order_by('-id')

    messages.filter( sender=other_user,flowed=False).update(flowed=True)


    serializer = MessageSerializer(messages, many=True,context={'request': request})
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def message_delete(request, pk):
    user = request.user
    try:
        message = Message.objects.get(id=pk)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

    if message.sender != user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    message.delete()
    return Response({'success': 'Message deleted'}, status=status.HTTP_200_OK)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def chat_delete(request, pk):
    user = request.user
    try:
        chat_room = ChatRoom.objects.get(id=pk)
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Chat room not found'}, status=status.HTTP_404_NOT_FOUND)

    if chat_room.owner != user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    message = Message.objects.filter(room=chat_room)
    if message:
        message.delete()
    chat_room.delete()
    return Response({'success': 'Chat room deleted'}, status=status.HTTP_200_OK)


@api_view(["POST"])
def translate(request, pk=None):

    text = request.data.get("text")
    source_lang = request.data.get("source_lang", None)
    target_lang = request.data.get("target_lang", "EN-US")

    if not text:
        return Response(
            {"error": "text is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        translator = deepl.Translator(DEEPL_KEY)

        result = translator.translate_text(
            text,
            source_lang=source_lang,
            target_lang=target_lang
        )

        return Response({
            "translated_text": result.text
        })

    except DeepLException as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )