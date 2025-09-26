from rest_framework import serializers
from .models import Reading, FanState, DeviceConfig # Importe DeviceConfig

class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = ['id', 'temperature', 'timestamp']
        read_only_fields = ['timestamp']
        extra_kwargs = {'temperature': {'required': False}}

class FanStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FanState
        fields = '__all__'

# NOVO: Serializer para o modelo de Configuração do Dispositivo
class DeviceConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceConfig
        # Incluímos apenas os campos que o Arduino precisa para se configurar
        fields = ['wifi_ssid', 'wifi_password', 'start_hour', 'end_hour']
        read_only_fields = ['wifi_ssid', 'wifi_password', 'start_hour', 'end_hour'] 
        # Geralmente, a API só lê a configuração, a escrita é feita pelo Admin/Página Web