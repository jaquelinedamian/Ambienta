# backend/sensors/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from .serializers import ReadingSerializer, FanStateSerializer
from .models import Reading, FanState, FanLog # Adicione FanLog
from django.utils import timezone # Adicione esta linha


class ReadingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = ReadingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            self.check_and_update_fan_state(serializer.validated_data['temperature'])

            return Response(
                {"message": "Dados recebidos com sucesso!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def check_and_update_fan_state(self, current_temperature):
        fan_state, created = FanState.objects.get_or_create(id=1, defaults={'state': False})
        
        temperature_limit = 25.0

        if current_temperature > temperature_limit and not fan_state.state:
            fan_state.state = True
            fan_state.save()
            # Inicia um novo registro de log
            FanLog.objects.create(start_time=timezone.now())
            print("LIGANDO VENTILADOR - TEMPERATURA ACIMA DO LIMITE")
        elif current_temperature <= temperature_limit and fan_state.state:
            fan_state.state = False
            fan_state.save()
            # Encerra o registro de log mais recente
            last_log = FanLog.objects.filter(end_time__isnull=True).order_by('-start_time').first()
            if last_log:
                last_log.end_time = timezone.now()
                last_log.duration = last_log.end_time - last_log.start_time
                last_log.save()
            print("DESLIGANDO VENTILADOR - TEMPERATURA ABAIXO DO LIMITE")

class ReadingListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Reading.objects.all()
    serializer_class = ReadingSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['id', 'timestamp']

class FanStateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        fan_state, created = FanState.objects.get_or_create(id=1, defaults={'state': False})
        serializer = FanStateSerializer(fan_state)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        fan_state, created = FanState.objects.get_or_create(id=1, defaults={'state': False})
        serializer = FanStateSerializer(fan_state, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)