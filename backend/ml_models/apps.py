# backend/ml_models/apps.py

from django.apps import AppConfig


class MlModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_models'
    verbose_name = 'Modelos de Machine Learning'
    
    def ready(self):
        """
        Importa apenas os signals, modelos serão carregados sob demanda
        """
        import os
        import sys
        
        # Evita múltiplas inicializações
        if os.environ.get('RUN_MAIN') or 'gunicorn' in sys.modules:
            # Carrega apenas os signals
            import ml_models.signals
            print("ML Models signals carregados!")
            
            # Configura o cache para lazy loading
            from .cache import model_cache
            model_cache.enable_lazy_loading = True
