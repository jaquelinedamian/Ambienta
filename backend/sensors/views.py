# backend/sensors/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from datetime import time # <-- IMPORT NECESSÁRIO
from .serializers import ReadingSerializer, FanStateSerializer
from .models import Reading, FanState, FanLog, DeviceConfig


# ===============================================
# 1. API VIEWS (Para Comunicação ESP32)
# Essas views exigem autenticação (IsAuthenticated)
# ===============================================

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

        # OBTÉM A CONFIGURAÇÃO ATUAL (onde o force_on está)
        config, config_created = DeviceConfig.objects.get_or_create(id=1)

        # Ajuste: Use uma variável de limite, idealmente configurável no DeviceConfig
        temperature_limit = 25.0

        # 1. PRIORITY CHECK: Se o modo manual estiver ATIVO, o Django NÃO PODE desligar.
        if config.force_on:
            if not fan_state.state:
                # Se o comando manual for LIGAR, garantimos que o estado do DB também seja LIGADO.
                fan_state.state = True
                fan_state.save()
                FanLog.objects.create(start_time=timezone.now())
                print("ESTADO DO VENTILADOR FORÇADO (MANUAL) - DB ATUALIZADO")
            # Se já está True, não faz nada para evitar que a temperatura o desligue.
            return

        # 2. LÓGICA AUTOMÁTICA NORMAL (Executa apenas se force_on for False)
        # ------------------------------------------------------------------

        if current_temperature > temperature_limit and not fan_state.state:
            fan_state.state = True
            fan_state.save()
            FanLog.objects.create(start_time=timezone.now())
            print("LIGANDO VENTILADOR - TEMPERATURA ACIMA DO LIMITE")

        elif current_temperature <= temperature_limit and fan_state.state:
            # Se o ventilador estava ligado (fan_state.state é True) e a temperatura baixou
            fan_state.state = False
            fan_state.save()
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


# ===============================================
# 2. API DE CONTROLE DE FORÇA BRUTA (HTTP GET)
# ===============================================
@method_decorator(csrf_exempt, name='dispatch')
class FanControlAPIView(APIView):
    """
    API de Força Bruta para testar a ativação imediata do ventilador.
    O ESP8266 acessa esta API para obter o status 'force_on'.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        config, created = DeviceConfig.objects.get_or_create(id=1)

        # Retorna o status de force_on
        return JsonResponse({
            'device_id': config.device_id,
            'force_on': config.force_on  # O campo booleano
        })


# ===============================================
# 3. WEB VIEW (Para a Página de Configuração HTML)
# Esta view exige autenticação (LoginRequiredMixin)
# ===============================================

class DeviceConfigUpdateView(LoginRequiredMixin, UpdateView):
    # Garante que apenas usuários logados acessem esta view

    model = DeviceConfig
    fields = [
        'wifi_ssid', 'wifi_password', 
        'start_hour', 'end_hour', 
        'force_on', 'ml_control'
    ]
    template_name = 'sensors/device_config_form.html'

    # Lembrete: Se 'dashboard' não funcionar, mude para 'dashboard_view'
    success_url = reverse_lazy('dashboard')

    def get_object(self, queryset=None):
        """
        Retorna ou cria uma configuração com valores padrão.
        Todos os campos são inicializados para evitar erros NULL.
        """
        config, created = DeviceConfig.objects.get_or_create(
            pk=1,
            defaults={
                'device_id': 'ambienta_esp32_1',
                'wifi_ssid': 'Ambienta-WiFi',
                'wifi_password': 'padrao',
                'start_hour': time(8, 0),
                'end_hour': time(18, 0),
                'force_on': False,
                'ml_control': False,
                'ml_duration': 0,
                'ml_start_time': None,
                'last_updated': timezone.now()
            }
        )
        
        # Garante que campos obrigatórios tenham valores mesmo se já existir
        if created or not config.last_updated:
            config.last_updated = timezone.now()
            config.save()
        return config