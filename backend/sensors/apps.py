# backend/sensors/apps.py

from django.apps import AppConfig

class SensorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sensors'
    
    def ready(self):
        # Esta linha garante que o código no signals.py seja carregado
        import sensors.signals