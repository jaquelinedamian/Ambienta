# backend/sensors/models.py

from django.db import models
from django.db.models.signals import post_save # Necessário para enviar o comando MQTT
from django.dispatch import receiver
from .mqtt import publish_config # Iremos criar isso no sensors/mqtt.py

# --- Modelos de Leitura de Sensores ---

class Reading(models.Model):
    temperature = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leitura de {self.timestamp}"
        
    def save(self, *args, **kwargs):
        # Arredonda a temperatura para uma casa decimal antes de salvar
        if self.temperature is not None:
            self.temperature = round(float(self.temperature), 1)
        super().save(*args, **kwargs)
        
    @property
    def formatted_temperature(self):
        """Retorna a temperatura formatada com uma casa decimal"""
        return "{:.1f}".format(self.temperature)

class FanState(models.Model):
    state = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self): # <-- CORREÇÃO DA SINTAXE AQUI
        return f"Ventilador: {'LIGADO' if self.state else 'DESLIGADO'}"

class FanLog(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"Ventilador Ligado: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"


# --- Modelo de Configuração do Dispositivo (para controle MQTT) ---

class DeviceConfig(models.Model):
    device_id = models.CharField(max_length=50, unique=True, default='default-device')
    
    wifi_ssid = models.CharField(max_length=100, default='NomeDaSuaRede')
    wifi_password = models.CharField(max_length=100, default='SuaSenhaAqui')
    
    start_hour = models.TimeField(default='08:00:00')
    end_hour = models.TimeField(default='18:00:00')
    
    # NOVO: Campo para ligar o ventilador imediatamente (controle manual)
    force_on = models.BooleanField(default=False, verbose_name="Forçar Ventilador Ligado")
    
    # NOVO: Campo para tracking do controle ML
    ml_control = models.BooleanField(default=False, verbose_name="Controle por ML")
    ml_duration = models.IntegerField(default=0, verbose_name="Duração recomendada (minutos)")
    ml_start_time = models.DateTimeField(null=True, blank=True)

    last_updated = models.DateTimeField(auto_now=True)
    
    def get_time_string(self, time_field):
        """Helper para retornar horário como string"""
        if isinstance(time_field, str):
            from datetime import datetime
            time_obj = datetime.strptime(time_field, '%H:%M:%S').time()
            return time_obj.strftime('%H:%M:%S')
        return time_field.strftime('%H:%M:%S')

    def __str__(self):
        return f"Configuração do Dispositivo {self.device_id}"

    @classmethod
    def get_default_config(cls):
        """Retorna ou cria a configuração padrão do sistema"""
        try:
            # Primeiro tenta pegar qualquer configuração existente
            config = cls.objects.first()
            if config:
                # Atualiza para os valores padrão se necessário
                config.device_id = 'default-device'
                config.save()
                return config
            
            # Se não existir nenhuma configuração, cria uma nova
            return cls.objects.create(
                device_id='default-device',
                wifi_ssid='Ambienta-WiFi',
                wifi_password='padrao',
                start_hour='08:00:00',
                end_hour='18:00:00',
                force_on=False,
                ml_control=False
            )
        except Exception as e:
            # Se algo der errado, tenta criar uma nova configuração
            return cls.objects.create(
                device_id='default-device',
                wifi_ssid='Ambienta-WiFi',
                wifi_password='padrao',
                start_hour='08:00:00',
                end_hour='18:00:00',
                force_on=False,
                ml_control=False
            )


# --- SIGNAL PARA ENVIAR COMANDO MQTT ---

@receiver(post_save, sender=DeviceConfig)
def send_config_to_mqtt(sender, instance, **kwargs):
    """
    Dispara a função de publicação MQTT sempre que um objeto DeviceConfig é salvo.
    """
    if kwargs.get('created', False) or kwargs.get('update_fields'): 
        publish_config(instance)