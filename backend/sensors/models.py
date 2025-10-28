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
    temperature_limit = models.FloatField(default=25.0)  # Limite dinâmico de temperatura
    last_seen = models.DateTimeField(null=True, blank=True)  # Última vez que o dispositivo se comunicou
    
    @property
    def is_online(self):
        """
        Verifica se o dispositivo está online (última comunicação nos últimos 2 minutos)
        """
        if not self.last_seen:
            return False
            
        from django.utils import timezone
        time_since_last_seen = timezone.now() - self.last_seen
        return time_since_last_seen.total_seconds() <= 120  # 2 minutos
    
    @classmethod
    def get_default_config(cls):
        """
        Retorna ou cria a configuração padrão
        """
        config, created = cls.objects.get_or_create(device_id='default-device')
        if created:
            config.last_seen = None
            config.save()
        return config
    
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
    
    def save(self, *args, **kwargs):
        # Garante que os horários estão no formato correto antes de salvar
        if isinstance(self.start_hour, str):
            from datetime import datetime
            try:
                time_obj = datetime.strptime(self.start_hour, '%H:%M:%S').time()
                self.start_hour = time_obj
            except ValueError:
                try:
                    time_obj = datetime.strptime(self.start_hour, '%H:%M').time()
                    self.start_hour = time_obj
                except ValueError:
                    pass
                
        if isinstance(self.end_hour, str):
            from datetime import datetime
            try:
                time_obj = datetime.strptime(self.end_hour, '%H:%M:%S').time()
                self.end_hour = time_obj
            except ValueError:
                try:
                    time_obj = datetime.strptime(self.end_hour, '%H:%M').time()
                    self.end_hour = time_obj
                except ValueError:
                    pass
        
        super().save(*args, **kwargs)

    @classmethod
    def get_default_config(cls):
        """Retorna ou cria a configuração padrão do sistema"""
        try:
            # Primeiro tenta pegar qualquer configuração existente
            config = cls.objects.first()
            if config:
                return config  # Retorna a configuração existente sem modificar
            
            # Se não existir, cria uma nova com valores padrão
            return cls.objects.create(
                device_id='default-device',
                wifi_ssid='Ambienta-WiFi',
                wifi_password='padrao',
                start_hour='08:00:00',
                end_hour='18:00:00',
                force_on=False,
                ml_control=False,
                ml_duration=0,
                ml_start_time=None
            )
        except Exception as e:
            print(f"Erro ao obter/criar configuração: {str(e)}")
            return None  # Retorna None em caso de erro para evitar criar objeto inválido


# --- SIGNAL PARA ENVIAR COMANDO MQTT ---

@receiver(post_save, sender=DeviceConfig)
def send_config_to_mqtt(sender, instance, **kwargs):
    """
    Dispara a função de publicação MQTT sempre que um objeto DeviceConfig é salvo.
    """
    try:
        # Sempre publica quando houver qualquer salvamento
        publish_config(instance)
        print(f"MQTT Config Update - Start: {instance.start_hour}, End: {instance.end_hour}")
    except Exception as e:
        print(f"Aviso: Não foi possível publicar no MQTT: {str(e)}")
        # Não propaga o erro para permitir o funcionamento sem MQTT