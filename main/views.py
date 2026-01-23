from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CustomUser

@api_view(['POST'])
def email_login(request):
    data = request.data
    email = data.get('email')
    firebase_token = data.get('firebase_token')
    
    if not email:
        return Response({'error': ' email shart'}, status=400)
    
    user, created = CustomUser.objects.get_or_create(
        email=email,
        role='client',
        username=email,
        firebase_token=firebase_token,
        
    )
    user.firebase_token = firebase_token
    refresh = RefreshToken.for_user(user)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'is_confirmation': user.is_confirmation
        }
    }, status=200)