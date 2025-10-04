# backend/sensors/mqtt.py

import paho.mqtt.publish as publish
import json
from django.utils import timezone

MQTT_SERVER = "broker.hivemq.com" # Ou "broker.emqx.io"
MQTT_TOPIC_CONFIG = "ambienta/comando/ambienta_esp32_1"

def publish_config(device_config_instance):
    """
    Publica a configuração do dispositivo para o tópico MQTT do ESP32.
    """
    try:
        # Processa os horários usando o helper do modelo
        start_time_str = device_config_instance.get_time_string(device_config_instance.start_hour)
        end_time_str = device_config_instance.get_time_string(device_config_instance.end_hour)
        
        # Processa timestamps ML
        now = timezone.now()
        ml_start_str = None
        if device_config_instance.ml_start_time:
            ml_start_str = device_config_instance.ml_start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepara o payload JSON com todos os campos
        payload = {
            'device_id': str(device_config_instance.device_id),
            'wifi_ssid': str(device_config_instance.wifi_ssid),
            'wifi_password': str(device_config_instance.wifi_password),
            'start_hour': start_time_str, 
            'end_hour': end_time_str,
            'force_on': bool(device_config_instance.force_on),
            'ml_control': bool(device_config_instance.ml_control),
            'ml_duration': int(device_config_instance.ml_duration),
            'ml_start_time': ml_start_str,
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        json_payload = json.dumps(payload)
        
        # Publica a mensagem no broker MQTT
        publish.single(
            topic=MQTT_TOPIC_CONFIG,
            payload=json_payload,
            hostname=MQTT_SERVER,
            port=1883
        )
        print(f"MQTT: Configuração publicada para {MQTT_TOPIC_CONFIG}")
        print(f"MQTT Payload: {json_payload}") # Imprime o payload no terminal do Django!
            
    except Exception as e:
        print(f"ERRO MQTT ao publicar configuração: {e}")