# backend/ml_models/apps.py

from django.apps import AppConfig


class MlModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_models'
    verbose_name = 'Modelos de Machine Learning'
    
    def ready(self):
        # Importar signals para ativar processamento automático
        try:
            from . import signals
        except ImportError:
            pass
