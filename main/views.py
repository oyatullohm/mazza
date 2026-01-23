from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import  AllowAny, IsAuthenticated 
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from .models import CustomUser

@api_view(['GET'])
@permission_classes([AllowAny])
def test(request):
    return Response({'message': 'Test endpoint is working.'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def email_login(request):
    return Response({'error': 'This endpoint has been moved to UserViewsets.email_login method.'}, status=400)
    # data = request.data
    # email = data.get('email')
    # firebase_token = data.get('firebase_token')
    
    # if not email:
    #     return Response({'error': ' email shart'}, status=400)
    # try:
    #     user = CustomUser.objects.get(email=email)
    # except CustomUser.DoesNotExist:
    #     user = CustomUser.objects.create_user(
    #         email=email,
    #         role='client',
    #         username=email,
    #         firebase_token=firebase_token,
    #     )

    # user.firebase_token = firebase_token
    # refresh = RefreshToken.for_user(user)

    # return Response({
    #     'refresh': str(refresh),
    #     'access': str(refresh.access_token),
    #     'user': {
    #         'id': user.id,
    #         'email': user.email,
    #         'phone': user.phone,
    #         'role': user.role,
    #         'is_confirmation': user.is_confirmation
    #     }
    # }, status=200)