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
            import ml_models.signals
            
            # Apenas verifica status dos modelos
            from .models import MLModel
            
            try:
                active_models = MLModel.objects.filter(is_active=True).count()
                if active_models > 0:
                    print(f"{active_models} modelos ML ativos encontrados")
                else:
                    print("Nenhum modelo ML ativo encontrado")
                    print("Use 'python manage.py train_ml_models' para treinar")
            except Exception as e:
                print(f"Aviso: Não foi possível verificar status dos modelos: {str(e)}")
                print("Execute as migrações se este for o primeiro deploy")
