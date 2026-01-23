from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import  AllowAny, IsAuthenticated 
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from .models import CustomUser

@api_view(['GET'])
@permission_classes([AllowAny])
def test(request):
    return Response({'message': 'Test endpoint is working.'}, status=200)
