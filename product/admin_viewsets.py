from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework import status
from .permissions import IsStaff
from .serializers import *
from .models import *


class CurrencyRateViewSet(viewsets.ModelViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer

    def list(self, request, *args, **kwargs):
        rate = CurrencyRate.objects.last()
        if not rate:
            return Response({}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(rate)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        course = request.data.get('course')
        if not course:
            return Response(
                {"error": "course majburiy"},
                status=status.HTTP_400_BAD_REQUEST
            )

        rate, created = CurrencyRate.objects.update_or_create(
            id=1,
            defaults={"rate": course}
        )

        serializer = self.get_serializer(rate)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsStaff]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsStaff]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsStaff]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]
    

class TheRuleViewSet(viewsets.ModelViewSet):
    queryset = The_rule.objects.all()
    serializer_class = TheRuleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsStaff]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]


class ComfortableViewSet(viewsets.ModelViewSet):
    queryset = Comfortable.objects.all()
    serializer_class = ComfortableSerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsStaff]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]


class AccessExitTimeViewSet(viewsets.ModelViewSet):
    queryset = AccessExitTime.objects.all()
    serializer_class = AccessExitTimeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [ IsStaff]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]