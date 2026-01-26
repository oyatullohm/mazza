from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from .permissions import IsStaff
from .serializers import *
from .models import *


class CurrencyRateViewSet(viewsets.ModelViewSet):
    queryset = CurrencyRate.objects.last()
    serializer_class = CurrencyRate
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=False)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        course = request.data['course']
        if self.get_queryset():
            serializer = self.get_serializer(self.get_queryset(), many=False)
            return Response(serializer.data, status=200)
        course = Course.objects.create(**course)
        serializer = self.get_serializer(course)

        return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        course_data = request.data['course']
        course = self.get_queryset()
        course.course = course_data
        course.save()
        serializer = self.get_serializer(course)
        return Response(serializer.data, status=200)
    
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
    queryset = Comfortable.objects.all().select_related('category')
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