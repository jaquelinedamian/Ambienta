from django.core.management.base import BaseCommand
from ml_models.models import MLModel
from ml_models.ml_algorithms import (
    TemperaturePredictionModel,
    FanOptimizationModel,
    AnomalyDetectionModel
)
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Inicializa os modelos de ML padrão'

    def handle(self, *args, **options):
        # Garantir que o diretório de modelos existe
        os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)
        
        # 1. Modelo de Detecção de Anomalias
        anomaly_model, created = MLModel.objects.get_or_create(
            model_type='anomaly_detection',
            version='1.0',
            defaults={
                'name': 'Detecção de Anomalias v1.0',
                'description': 'Modelo para detectar leituras anômalas de temperatura',
                'is_active': True
            }
        )
        if created:
            # Criar e salvar o modelo inicial
            model = AnomalyDetectionModel()
            model.train(days_back=30)  # Treina com dados dos últimos 30 dias
            anomaly_model.save_model({'model': model.model, 'scaler': model.scaler})
            self.stdout.write(self.style.SUCCESS('Modelo de anomalia criado'))

        # 2. Modelo de Predição de Temperatura
        temp_model, created = MLModel.objects.get_or_create(
            model_type='temperature_prediction',
            version='1.0',
            defaults={
                'name': 'Predição de Temperatura v1.0',
                'description': 'Modelo para prever temperaturas futuras',
                'is_active': True
            }
        )
        if created:
            # Criar e salvar o modelo inicial
            model = TemperaturePredictionModel()
            model.train(days_back=30)  # Treina com dados dos últimos 30 dias
            temp_model.save_model(model.model)
            self.stdout.write(self.style.SUCCESS('Modelo de temperatura criado'))

        # 3. Modelo de Otimização do Ventilador
        fan_model, created = MLModel.objects.get_or_create(
            model_type='fan_optimization',
            version='1.0',
            defaults={
                'name': 'Otimização do Ventilador v1.0',
                'description': 'Modelo para otimizar o uso do ventilador',
                'is_active': True
            }
        )
        if created:
            # Criar e salvar o modelo inicial
            model = FanOptimizationModel()
            model.train(days_back=30)  # Treina com dados dos últimos 30 dias
            fan_model.save_model(model.model)
            self.stdout.write(self.style.SUCCESS('Modelo de ventilador criado'))

        self.stdout.write(self.style.SUCCESS('Todos os modelos foram inicializados'))