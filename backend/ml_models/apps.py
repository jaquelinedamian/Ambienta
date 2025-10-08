# backend/ml_models/apps.py

from django.apps import AppConfig


class MlModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_models'
    verbose_name = 'Modelos de Machine Learning'
    
    def ready(self):
        """
        Importa signals e carrega modelos pré-treinados
        """
        import os
        import sys
        
        # Evita múltiplas inicializações
        if os.environ.get('RUN_MAIN') or 'gunicorn' in sys.modules:
            # Carrega signals
            import ml_models.signals
            print("ML Models signals carregados!")
            
            # Carrega modelos pré-treinados
            from .ml_algorithms import (
                TemperaturePredictionModel,
                FanOptimizationModel,
                AnomalyDetectionModel
            )
            from .cache import model_cache
            
            try:
                # Carrega os modelos sem treinar
                temp_model = TemperaturePredictionModel()
                fan_model = FanOptimizationModel()
                anomaly_model = AnomalyDetectionModel()
                
                # Carrega os modelos salvos para o cache
                model_cache.set('temperature_prediction', temp_model.model)
                model_cache.set('fan_optimization', fan_model.model)
                model_cache.set('anomaly_detection', anomaly_model.model)
                
                print("Modelos ML pré-treinados carregados com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar modelos ML: {str(e)}")
                # Continua mesmo se houver erro, os modelos serão carregados sob demanda
