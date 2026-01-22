from rest_framework.permissions import  AllowAny, IsAuthenticated 
from rest_framework.decorators import permission_classes
from rest_framework.pagination import PageNumberPagination
from django.db.models import F , Prefetch, Count
from rest_framework.decorators import action
from rest_framework.response import Response
from urllib3 import request
# from announcement.decorators import IsStaff
from .serializers import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets
from rest_framework import status
from .models import *
import datetime
import random
from .utils import *



class UserViewsets(viewsets.ViewSet):
    serializer_class = RegisterSerializer
    queryset = CustomUser.objects.all()
    
    @action(methods=['get'],detail=False, permission_classes=[AllowAny])
    def role(self, request):
        return Response([{'key': i[0], 'value': i[1]} for i in CustomUser.USER_CHOISE])

    @action(methods=['post'], detail=False, permission_classes=[AllowAny])
    def register(self, request):
        data = request.data
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        firebase_token = data.get('firebase_token')

        if not phone and not email:
            return Response({'error': 'phone yoki email shart'}, status=400)

        code = random_number()

        user = CustomUser.objects.create_user(
            phone=phone,
            email=email,
            first_name=name,
            role=role,
            password=password,
            firebase_token=firebase_token,
            username=email,
            confirmation_code= code,
            is_confirmation= False
        )

        
        user.confirmation_code = code
        user.save()
        set_verify_code(code, email)
        # 👉 bu yerda SMS yoki EMAIL yuborasan
        # print("CONFIRM CODE:", code)

        return Response({
            'success': True,
            'message': f'Tasdiqlash kodi {user.phone} yuborildi',
            'code':code
        }, status=201)
    

    @action(methods=['post'], detail=False, permission_classes=[AllowAny])
    def login(self, request):
        return Response(
                {'error': ' email yuborilishi shart'})
        email = request.data.get("email")
        password = request.data.get("password")
        firebase_token = request.data.get("firebase_token")

        if not email:
            return Response(
                {'error': ' email yuborilishi shart'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(username=email)

            if user is None:
                return Response(
                    {'error': 'Noto\'g\'ri email yoki parol'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        if not user.check_password(password):
            return Response(
                {'error': 'Parol noto‘g‘ri'},
                status=status.HTTP_401_UNAUTHORIZED
            )


        code = random_number()
        user.confirmation_code = code
        user.firebase_token = firebase_token
        user.save()
        set_verify_code(code, email)

        # bu yerda sms yoki email yuborasiz

        return Response({
            'success': True,
            'message': f'Tasdiqlash kodi {user.phone}yuborildi',
            
            'code':code
        }, status=status.HTTP_201_CREATED)
    
    @action(methods=['post'], detail=False, permission_classes=[AllowAny])
    def verify(self, request):
        code = request.data.get('code')

        if not code:
            return Response({'error': 'code yuborilishi shart'}, status=400)

        data = get_verify_email_by_code(code)

        if not data:
            return Response({'error': 'Kod eskirgan yoki noto‘g‘ri'}, status=400)

        email = data['email']
        user = CustomUser.objects.get(email=email)

        user.is_confirmation = True
        user.save()

        delete_verify_code(code)

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'phone': user.phone,
                'role': user.role
            }
        }, status=200)

    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated])
    def my(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'name': user.first_name,
            'phone': user.phone,
            'email': user.email,
            'role': user.role,
            # 'password': user.password
        },status=200)
    
    @action(methods=['post'],detail=False, permission_classes=[IsAuthenticated])
    def refresh(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token is None:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({'access': access_token}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(methods=['post'],detail=False, permission_classes=[IsAuthenticated])
    def update(self, request):
        user = request.user
        data = request.data
        phone = data.get('phone')
        email = data.get('email')
        image = data.get('image')
        name = data.get('name')
        
        if name:
            user.first_name = name
        if phone:
            user.phone = phone
        if email:
            user.email = email
        if image:
            user.image = image
        try:
            user.save()
        except Exception as e:
            return Response({'error': str(e)}, status=400)

        return Response({
            'id': user.id,
            'name': user.first_name,
            'phone': user.phone,
            'email': user.email,
            'role': user.role,
            'image': user.image.url if user.image else None
        }, status=200)  
    
    @action(methods=['post'], detail=False, permission_classes=[AllowAny])
    def forgotten_password(self, request):
        email = request.data.get('email')
        phone = request.data.get('phone')

        if not email and not phone:
            return Response({'error': 'email yoki phone yuborilishi shart'}, status=400)

        try:
            try:
                user = CustomUser.objects.get(username=email)
            except CustomUser.DoesNotExist:
                user = CustomUser.objects.get(phone=phone)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi'}, status=404)

        code = random_number()
        user.confirmation_code = code
        user.save()

        # bu yerda sms yoki email yuborasiz

        set_verify_code(code, email)
        return Response({
            'success': True,
            'message': f'Tasdiqlash kodi {user.phone} yuborildi',
            'code': code
        }, status=status.HTTP_201_CREATED)
    
    @action(methods=['post'], detail=False, permission_classes=[AllowAny])
    def reset_password(self, request):
        code = request.data.get('code')
        data = get_verify_email_by_code(code)
        if not data:
            return Response({'error': 'Kod eskirgan yoki noto‘g‘ri'}, status=400)

        email = data['email']
        new_password = request.data.get('new_password')

        
        try:
            user = CustomUser.objects.get(username=email, confirmation_code=code)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Noto\'g\'ri kod yoki email'}, status=404)

        user.set_password(new_password)
        user.confirmation_code = ''
        user.save()

        return Response({'success': True, 'message': 'Parol muvaffaqiyatli yangilandi'}, status=200)
    
    def update(self, request, pk=None):
        user = request.user
        data = request.data

        phone = data.get('phone')
        email = data.get('email')
        image = data.get('image')
        name = data.get('name')

        if name:
            user.first_name = name
        if phone:
            user.phone = phone
        if email:
            user.email = email
        if image:
            user.image = image
        try:
            user.save()
        except Exception as e:
            return Response({'error': str(e)}, status=400)

        return Response({
            'id': user.id,
            'name': user.first_name,
            'phone': user.phone,
            'email': user.email,
            'role': user.role,
            'image': user.image.url if user.image else None
        }, status=200)

    def destroy(self, request, pk=None):
        user = request.user
        user.image.delete(save=False)  # Rasmni o'chirish
        user.delete()
        return Response({'message': 'Foydalanuvchi o\'chirildi'}, status=204)