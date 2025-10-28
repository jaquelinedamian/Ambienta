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
        # Log dos dados recebidos
        print("\n=== NOVA LEITURA RECEBIDA ===")
        print(f"Data/Hora: {timezone.now()}")
        print(f"Dados recebidos (raw): {request.data}")
        print(f"Headers: {request.headers}")
        
        serializer = ReadingSerializer(data=request.data)
        if serializer.is_valid():
            print(f"Dados validados: {serializer.validated_data}")
            
            # Atualiza o último contato com o dispositivo
            config = DeviceConfig.get_default_config()
            config.last_seen = timezone.now()
            config.save()
            print(f"Last seen atualizado para: {config.last_seen}")
            
            # Salva a leitura
            reading = serializer.save()
            print(f"Leitura salva com ID: {reading.id}")
            
            # Atualiza estado do ventilador
            self.check_and_update_fan_state(serializer.validated_data['temperature'])
            
            # Log da última leitura salva
            last_readings = Reading.objects.order_by('-timestamp')[:5]
            print("\nÚltimas 5 leituras:")
            for r in last_readings:
                print(f"ID: {r.id} | Temp: {r.temperature}°C | Data: {r.timestamp}")
            
            return Response(
                {"message": "Dados recebidos com sucesso!", "reading_id": reading.id},
                status=status.HTTP_201_CREATED
            )
        
        # Log de erro na validação
        print("\nERRO na validação dos dados:")
        print(f"Erros: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def check_and_update_fan_state(self, current_temperature):
        fan_state, created = FanState.objects.get_or_create(id=1, defaults={'state': False})

        # Obtém a configuração atual
        config = DeviceConfig.get_default_config()

        # Obtém o limite de temperatura otimizado do modelo ML ou usa o padrão do config
        from ml_models.integrations import MLIntegrationService
        optimized_temp = MLIntegrationService.get_optimized_temperature_limit(current_temperature)
        temperature_limit = optimized_temp if optimized_temp else config.temperature_limit

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


class FanControlAPIView(APIView):
    """API para o ESP8266 obter configurações de controle"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Obtém configurações atuais
        config = DeviceConfig.get_default_config()
        fan_state = FanState.objects.get_or_create(id=1)[0]
        
        # Obtém última leitura de temperatura
        last_reading = Reading.objects.order_by('-timestamp').first()
        current_temp = last_reading.temperature if last_reading else None
        
        # Obtém limite otimizado se possível
        from ml_models.integrations import MLIntegrationService
        optimized_temp = None
        if current_temp:
            optimized_temp = MLIntegrationService.get_optimized_temperature_limit(current_temp)
        
        # Prepara resposta
        response_data = {
            'force_on': config.force_on,
            'temperature_limit': optimized_temp if optimized_temp else config.temperature_limit,
            'start_hour': config.start_hour,
            'end_hour': config.end_hour
        }
        
        return Response(response_data)

class FanStateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        fan_state, created = FanState.objects.get_or_create(id=1, defaults={'state': False})
        config = DeviceConfig.get_default_config()
        
        # Verifica se o dispositivo está online (última comunicação nos últimos 2 minutos)
        is_online = False
        if config.last_seen:
            time_since_last_seen = timezone.now() - config.last_seen
            is_online = time_since_last_seen.total_seconds() <= 120  # 2 minutos
        
        # Se o dispositivo estiver offline, considera o ventilador desligado
        if not is_online:
            fan_state.state = False
            fan_state.save()
            
        # Adiciona informação de online/offline à resposta
        response_data = {
            'state': fan_state.state,
            'is_online': is_online,
            'last_seen': config.last_seen
        }
        return Response(response_data, status=status.HTTP_200_OK)

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
        config = DeviceConfig.get_default_config()

        # Retorna o status de force_on
        return JsonResponse({
            'device_id': config.device_id,
            'force_on': config.force_on  # O campo booleano
        })
    
    def post(self, request, *args, **kwargs):
        fan_state, created = FanState.objects.get_or_create(id=1, defaults={'state': False})
        serializer = FanStateSerializer(fan_state, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ===============================================
# 3. WEB VIEW (Para a Página de Configuração HTML)
# Esta view exige autenticação (LoginRequiredMixin)
# ===============================================

class DeviceConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = DeviceConfig
    fields = [
        'wifi_ssid', 'wifi_password', 
        'start_hour', 'end_hour', 
        'force_on',
        'ml_control'  # Adicionado campo de ML
    ]
    template_name = 'sensors/device_config_form.html'
    success_url = reverse_lazy('dashboard:dashboard')

    def get_object(self, queryset=None):
        """
        Retorna ou cria a configuração padrão do sistema
        """
        return DeviceConfig.get_default_config()

    def form_invalid(self, form):
        """
        Log dos erros do formulário para debug
        """
        print("Erros do formulário:", form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        """
        Adiciona tratamento adicional antes de salvar
        """
        try:
            # Preserva o device_id existente
            instance = form.save(commit=False)
            if not instance.device_id:
                instance.device_id = 'default-device'
            return super().form_valid(form)  # isso vai salvar a instância
        except Exception as e:
            print("Erro ao salvar:", str(e))
            form.add_error(None, "Erro ao salvar configuração: " + str(e))
            return self.form_invalid(form)