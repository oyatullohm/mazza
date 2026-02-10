
from rest_framework.permissions import  AllowAny, IsAuthenticated 
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import F , Prefetch, Count, Q
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from .serializers import *
from .models import *
from .utils import *
import datetime
import random



class UserViewsets(viewsets.ViewSet):
    serializer_class = RegisterSerializer
    queryset = CustomUser.objects.all()
    
    @action(methods=['get'],detail=False, permission_classes=[AllowAny])
    def role(self, request):
        return Response([{'key': i[0], 'value': i[1]} for i in CustomUser.USER_CHOISE])
    
    @action(methods=['post'],detail=False, permission_classes=[AllowAny])
    def email_login(self, request, pk=None):
        data = request.data
        email = data.get('email')
        first_name = data.get('name')
        firebase_token = data.get('firebase_token')
        
        if not email:
            return Response({'error': ' email shart'}, status=400)
        try:
            user = CustomUser.objects.get(username=email)
        except:
            user = CustomUser.objects.create_user(
            email=email,
            role='client',
            username=email,
            firebase_token=firebase_token,
         
        )
        user.first_name = first_name
        user.firebase_token = firebase_token
        user.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'phone': user.phone,
                'role': user.role, 
                'first_name':user.first_name,
                'is_confirmation': user.is_confirmation
            }
        }, status=200)

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
        if CustomUser.objects.filter(Q(phone=phone) | Q(email=email)).exists():
            return Response(
                {'error': 'Bu telefon raqam yoki email allaqachon ro‘yxatdan o‘tgan'},
                status=400
            )
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
        if user.role == 'agent':
            Balans.objects.get_or_create(user=user)

        
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
    def login_user(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        firebase_token = request.data.get("firebase_token")

        if not email or not password:
            return Response(
                {'error': 'email va password yuborilishi shart'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = CustomUser.objects.filter(email=email).first()
        if not user:
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

        return Response({
            'success': True,
            'message': 'Tasdiqlash kodi yuborildi',
            'code': code
        }, status=status.HTTP_200_OK)

    
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
                'name':user.first_name,
                'phone': user.phone,
                'role': user.role,
                'is_confirmation': user.is_confirmation
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
            'is_confirmation': user.is_confirmation
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

        # phone = data.get('phone')
        email = data.get('email')
        image = data.get('image')
        name = data.get('name')

        if name:
            user.first_name = name

        if email:
            user.email = email
            user.username = email
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

class BalansViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BalansSerializer
    queryset = Balans.objects.all() 

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        return Balans.objects.filter(user=self.request.user)


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        amount = request.data.get('balans')

        if amount is not None:
            try:
                amount = float(amount)
            except ValueError:
                return Response({'error': 'Invalid amount'}, status=400)

            instance.balans = F('balans') + amount
            instance.save()
            instance.refresh_from_db()

            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'Amount is required'}, status=400)