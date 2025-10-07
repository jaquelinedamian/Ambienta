# backend/ml_models/apps.py

from django.apps import AppConfig


class MlModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_models'
    verbose_name = 'Modelos de Machine Learning'
    
    def ready(self):
        """
        Importa e inicializa apenas os signals do app
        """
        import os
        import sys
        
        # Evita múltiplas inicializações
        if os.environ.get('RUN_MAIN') or 'gunicorn' in sys.modules:
            # Carrega apenas os signals, sem acessar o banco de dados
            import ml_models.signals
            print("ML Models signals carregados!")
