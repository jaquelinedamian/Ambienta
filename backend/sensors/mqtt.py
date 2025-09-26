# backend/sensors/mqtt.py (CORREÇÃO DA PUBLICAÇÃO)

import paho.mqtt.publish as publish
import json

MQTT_SERVER = "broker.hivemq.com" # Ou "broker.emqx.io"
MQTT_TOPIC_CONFIG = "ambienta/comando/ambienta_esp32_1"

def publish_config(device_config_instance):
    """
    Publica a configuração do dispositivo para o tópico MQTT do ESP32.
    """
    
    # Garantimos que os objetos de hora sejam strings válidas
    start_time_str = device_config_instance.start_hour.strftime('%H:%M:%S')
    end_time_str = device_config_instance.end_hour.strftime('%H:%M:%S')
    
    # Prepara o payload JSON com todos os campos
    payload = {
        'device_id': device_config_instance.device_id,
        'wifi_ssid': device_config_instance.wifi_ssid,
        'wifi_password': device_config_instance.wifi_password,
        'start_hour': start_time_str, 
        'end_hour': end_time_str,
        # O campo já é um booleano do Django, o json.dumps() o converte corretamente.
        'force_on': device_config_instance.force_on 
    }
    
    json_payload = json.dumps(payload)
    
    try:
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