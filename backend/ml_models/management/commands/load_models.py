# backend/ml_models/management/commands/load_models.py

from django.core.management.base import BaseCommand
from ml_models.ml_algorithms import (
    TemperaturePredictionModel,
    FanOptimizationModel, 
    AnomalyDetectionModel
)
from ml_models.cache import model_cache

class Command(BaseCommand):
    help = 'Carrega modelos ML pré-treinados para o cache'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write("Carregando modelos ML pré-treinados...")
            
            # Carrega os modelos
            temp_model = TemperaturePredictionModel()
            fan_model = FanOptimizationModel()
            anomaly_model = AnomalyDetectionModel()
            
            # Força o carregamento dos modelos do disco
            model_cache.enable_lazy_loading = True
            _ = temp_model.model
            _ = fan_model.model
            _ = anomaly_model.model
            
            self.stdout.write(self.style.SUCCESS("Modelos carregados com sucesso!"))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Erro ao carregar modelos: {str(e)}")
            )