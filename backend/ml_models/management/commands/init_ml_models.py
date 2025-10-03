from django.core.management.base import BaseCommand
from ml_models.models import MLModel
from django.utils import timezone
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Inicializa os modelos ML no banco de dados'

    def handle(self, *args, **kwargs):
        # Lista de modelos para criar
        models_to_create = [
            {
                'name': 'Predição de Temperatura v1.0',
                'model_type': 'temperature_prediction',
                'version': '1.0',
                'file_path': 'temperature_prediction_v1.0_1.pkl',
                'description': 'Modelo de predição de temperatura baseado em histórico',
                'is_active': True,
                'accuracy': 0.85,
                'r2_score': 0.82,
                'mse': 0.15,
                'mae': 0.12
            },
            {
                'name': 'Otimização do Ventilador v1.0',
                'model_type': 'fan_optimization',
                'version': '1.0',
                'file_path': 'fan_optimization_v1.0_3.pkl',
                'description': 'Modelo de otimização do ventilador',
                'is_active': True,
                'accuracy': 0.88,
                'r2_score': 0.84,
                'mse': 0.12,
                'mae': 0.10
            },
            {
                'name': 'Detecção de Anomalias v1.0',
                'model_type': 'anomaly_detection',
                'version': '1.0',
                'file_path': 'anomaly_detection_v1.0_2.pkl',
                'description': 'Modelo de detecção de anomalias de temperatura',
                'is_active': True,
                'accuracy': 0.92,
                'r2_score': 0.89,
                'mse': 0.08,
                'mae': 0.06
            }
        ]

        # Criar ou atualizar cada modelo
        for model_data in models_to_create:
            file_path = os.path.join(settings.ML_MODELS_DIR, model_data['file_path'])
            
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(
                        f"Arquivo {model_data['file_path']} não encontrado em {settings.ML_MODELS_DIR}"
                    )
                )
                continue

            # Atualizar ou criar o modelo
            model, created = MLModel.objects.update_or_create(
                model_type=model_data['model_type'],
                version=model_data['version'],
                defaults={
                    'name': model_data['name'],
                    'model_file_path': model_data['file_path'],
                    'description': model_data['description'],
                    'is_active': model_data['is_active'],
                    'accuracy': model_data['accuracy'],
                    'r2_score': model_data['r2_score'],
                    'mse': model_data['mse'],
                    'mae': model_data['mae'],
                    'last_trained': timezone.now()
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Modelo criado com sucesso: {model.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Modelo atualizado com sucesso: {model.name}')
                )