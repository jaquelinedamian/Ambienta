# backend/sensors/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DeviceConfig 
from .mqtt import publish_config 

@receiver(post_save, sender=DeviceConfig)
def send_config_to_mqtt(sender, instance, **kwargs):
    """
    Dispara a função de publicação MQTT sempre que um objeto DeviceConfig é salvo.
    """
    if kwargs.get('created', False) or kwargs.get('update_fields'): 
        publish_config(instance)