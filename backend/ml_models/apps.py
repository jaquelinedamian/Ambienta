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
        import os
        import sys
        
        # Evita múltiplas inicializações
        if 'gunicorn' in sys.modules:
            # Em produção (Gunicorn)
            try:
                import ml_models.signals
                from .models import MLModel
                
                # Verifica se já existem modelos treinados
                if not MLModel.objects.filter(is_active=True).exists():
                    print("Iniciando treinamento inicial dos modelos...")
                else:
                    print("Modelos ML já existem e estão ativos")
            except Exception as e:
                print(f"Erro ao inicializar modelos ML: {str(e)}")
        else:
            # Em desenvolvimento
            if os.environ.get('RUN_MAIN'):
                import ml_models.signals
                print("ML Models signals carregados (desenvolvimento)")
