
from rest_framework.permissions import  AllowAny, IsAuthenticated 
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import F , Prefetch, Count, Q
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.response import Response
from product.permissions import IsStaff
from rest_framework import viewsets
from rest_framework import status
from .serializers import *
from .models import *
from product.models import Property
from product.serializers import PropertySerializer
from .utils import *
import datetime
import random
import requests
from datetime import timedelta
from django.utils import timezone
from Admin.settings import ESKIZ_EMAIL, ESKIZ_PASSWORD

def get_eskiz_token():

    token  = EskizToken.objects.last()
    if token and timezone.now() - token.created_at < timedelta(hours=24):
        return token.token
        

    url = "https://notify.eskiz.uz/api/auth/login"
    payload = {
        "email": ESKIZ_EMAIL,
        "password": ESKIZ_PASSWORD
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        token = response.json().get("data", {}).get("token")
        data = response.json()

    if "data" in data and "token" in data["data"]:
        new_token = data["data"]["token"]
        EskizToken.objects.all().delete()  # eski tokenlarni o‘chirish
        EskizToken.objects.create(token=new_token)  # yangisini saqlash
        return new_token
    else:
        raise Exception(f"Eskiz token olishda xatolik: {data}")


def send_sms(phone_number, code):
    """Eskiz orqali SMS yuborish"""
    token = get_eskiz_token()
    if not token:
        return {"error": "Eskiz API tokenini olishda xatolik!"}

    url = "https://notify.eskiz.uz/api/message/sms/send"

    headers = {"Authorization": f"Bearer {token}"}

    phone_number = phone_number.replace("+", "").replace(" ", "").strip()
    if not phone_number.startswith("998") or len(phone_number) != 12:
        return {"error": "Telefon raqami noto‘g‘ri formatda!"}
    payload = {
    "mobile_phone": phone_number,
    "message": f"Kodni hech kimga bermang! Mazzajoy mobil ilovasiga kirish uchun tasdiqlash kodi: {code}",
    "from": "4546",
    "callback_url": ""
    }

    response = requests.post(url, headers=headers, data=payload)
    # print("Eskizdan javob:", response.json())
    return response.json()


class UserViewsets(viewsets.ViewSet):
    serializer_class = RegisterSerializer
    queryset = CustomUser.objects.all()
    
    @action(methods=['get'],detail=False, permission_classes=[AllowAny])
    def role(self, request):
        return Response([{'key': i[0], 'value': i[1]} for i in CustomUser.USER_CHOISE])


    @action(methods=['post'], detail=False, permission_classes=[AllowAny])
    def login_user(self, request):

        phone = request.data.get("phone")

        firebase_token = request.data.get("firebase_token")

        if not phone:
            return Response(
                {'error': 'phone yuborilishi shart'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = CustomUser.objects.get_or_create(phone=phone, defaults={'username': phone})[0]

        code = random_number()
        user.confirmation_code = code
        user.firebase_token = firebase_token
        user.save()
        
        if user.phone == '+998992511100':
            code = '12345'
        
        
        set_verify_code(code, user.phone)
        try:
            result = send_sms(user.phone, code)
        except:
            result = None
        # print("SMS yuborish natijasi:", result)
        return Response({
            'success': True,
            'message': 'Tasdiqlash kodi yuborildi',
            # 'code': code
            'result':result
        }, status=status.HTTP_200_OK)

    
    @action(methods=['post'], detail=False, permission_classes=[AllowAny])
    def verify(self, request):
        code = request.data.get('code')

        if not code:
            return Response({'error': 'code yuborilishi shart'}, status=400)

        data = get_verify_email_by_code(code)

        if not data:
            return Response({'error': 'Kod eskirgan yoki noto‘g‘ri'}, status=400)

        phone = data['phone']
        user = CustomUser.objects.get(phone=phone)

        user.is_confirmation = True
        user.save()

        delete_verify_code(code)

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                # 'email': user.email,
                # 'name':user.first_name,
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
            # 'email': user.email,
            'role': user.role,
            'is_confirmation': user.is_confirmation,
            'image': user.image.url if user.image else None
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


   

    def update(self, request, pk=None):
        user = request.user
        data = request.data

        # phone = data.get('phone')
        # email = data.get('email')
        image = data.get('image')
        name = data.get('name')

        if name:
            user.first_name = name

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
            # 'email': user.email,
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
    
    # queryset = Balans.objects.all() 
    http_method_names = ['get','retrieve','update','put', 'patch']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        return Balans.objects.filter(user=self.request.user)


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        amount = request.data.get('balans')
        new_balans = request.data.get('new_balans')
        if new_balans is not None:
            try:
                new_balans = float(new_balans)
            except ValueError:
                return Response({'error': 'Invalid new_balans'}, status=400)

            instance.balans = new_balans
            instance.save()
            instance.refresh_from_db()

            serializer = self.get_serializer(instance)
            return Response(serializer.data)
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

class BannerViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.filter(is_banner=True)
    serializer_class = PropertySerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsStaff()]
        return [AllowAny()]

