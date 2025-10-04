# backend/ml_models/apps.py

from django.apps import AppConfig


class MlModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_models'
    verbose_name = 'Modelos de Machine Learning'
    
    def ready(self):
        """
        Importa e inicializa os signals do app
        """
        import ml_models.signals  # importação explícita
        print("ML Models signals carregados!")
