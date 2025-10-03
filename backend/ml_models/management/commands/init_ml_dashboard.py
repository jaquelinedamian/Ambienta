from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from ml_models.models import MLModel, MLPrediction
import random
import json

class Command(BaseCommand):
    help = 'Inicializa dados de exemplo para o dashboard ML'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            # 1. Garante que os modelos estão ativos
            models_updated = MLModel.objects.filter(
                model_file_path__isnull=False
            ).update(is_active=True)
            
            self.stdout.write(
                self.style.SUCCESS(f'Modelos ativados: {models_updated}')
            )

            # 2. Cria algumas predições de exemplo se não existirem
            if MLPrediction.objects.count() == 0:
                now = timezone.now()
                models = MLModel.objects.filter(is_active=True)
                
                for model in models:
                    # Criar algumas predições nas últimas 24 horas
                    for i in range(5):  # 5 predições por modelo
                        created_at = now - timedelta(
                            hours=random.randint(1, 24)
                        )
                        
                        # Dados de predição baseados no tipo de modelo
                        if model.model_type == 'temperature_prediction':
                            prediction_data = {
                                'temperatures': [
                                    round(random.uniform(20.0, 30.0), 1)
                                    for _ in range(3)
                                ]
                            }
                        elif model.model_type == 'fan_optimization':
                            prediction_data = {
                                'should_turn_on': random.choice([True, False]),
                                'recommended_duration_minutes': random.randint(5, 30),
                                'confidence': random.uniform(0.7, 0.95)
                            }
                        else:  # anomaly_detection
                            prediction_data = {
                                'is_anomaly': random.choice([True, False]),
                                'anomaly_score': random.uniform(0.1, 0.9),
                                'confidence': random.uniform(0.75, 0.98)
                            }

                        # Gerar dados de entrada apropriados
                        if model.model_type == 'temperature_prediction':
                            input_data = {'hours_ahead': 3}
                        elif model.model_type == 'fan_optimization':
                            input_data = {
                                'current_temperature': round(random.uniform(22.0, 28.0), 1),
                                'current_hour': random.randint(0, 23)
                            }
                        else:  # anomaly_detection
                            input_data = {
                                'temperature': round(random.uniform(20.0, 30.0), 1),
                                'hour': random.randint(0, 23)
                            }

                        MLPrediction.objects.create(
                            model=model,
                            input_data=input_data,
                            prediction=prediction_data,
                            created_at=created_at,
                            confidence=prediction_data.get('confidence', 0.8)
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Criadas {MLPrediction.objects.count()} predições de exemplo'
                    )
                )