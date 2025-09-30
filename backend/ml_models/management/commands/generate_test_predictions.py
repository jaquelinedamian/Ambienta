# backend/ml_models/management/commands/generate_test_predictions.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from ml_models.models import MLModel, MLPrediction
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Gera predições de teste para visualização no dashboard'

    def handle(self, *args, **kwargs):
        # Buscar modelos ativos
        temp_model = MLModel.objects.filter(model_type='temperature_prediction', is_active=True).first()
        anomaly_model = MLModel.objects.filter(model_type='anomaly_detection', is_active=True).first()

        if not temp_model or not anomaly_model:
            self.stdout.write(self.style.ERROR('Modelos necessários não estão ativos'))
            return

        # Gerar algumas predições de temperatura
        now = timezone.now()
        for i in range(10):
            timestamp = now - timedelta(hours=i)
            temp = random.uniform(18, 25)
            
            MLPrediction.objects.create(
                model=temp_model,
                input_data={
                    'timestamp': timestamp.isoformat(),
                    'last_temps': [temp - random.uniform(-1, 1) for _ in range(5)]
                },
                prediction={
                    'predicted_temp': temp,
                    'confidence_interval': [temp - 0.5, temp + 0.5]
                },
                confidence=random.uniform(0.85, 0.95),
                created_at=timestamp
            )

        # Gerar algumas detecções de anomalia
        for i in range(5):
            timestamp = now - timedelta(hours=i*2)
            temp = random.uniform(15, 30)
            is_anomaly = random.random() > 0.7  # 30% de chance de ser anomalia
            
            MLPrediction.objects.create(
                model=anomaly_model,
                input_data={
                    'timestamp': timestamp.isoformat(),
                    'temperature': temp
                },
                prediction={
                    'is_anomaly': is_anomaly,
                    'anomaly_score': random.uniform(0.1, 0.9)
                },
                confidence=random.uniform(0.8, 0.99),
                created_at=timestamp
            )

        self.stdout.write(self.style.SUCCESS('Predições de teste geradas com sucesso'))