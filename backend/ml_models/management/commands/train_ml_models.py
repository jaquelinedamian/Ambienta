from django.core.management.base import BaseCommand
from ml_models.models import MLModel
from ml_models.ml_algorithms import (
    TemperaturePredictionModel,
    FanOptimizationModel,
    AnomalyDetectionModel
)

class Command(BaseCommand):
    help = 'Treina os modelos ML iniciais'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Pula o treinamento se já existirem modelos ativos',
        )

    def handle(self, *args, **options):
        skip_if_exists = options['skip_if_exists']
        
        # Verifica se já existem modelos ativos
        if skip_if_exists:
            active_models = MLModel.objects.filter(is_active=True).count()
            if active_models > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Encontrados {active_models} modelos ativos. Pulando treinamento.')
                )
                return
        
        self.stdout.write('Iniciando treinamento dos modelos ML...')
        
        try:
            # Temperatura
            temp_model = TemperaturePredictionModel()
            if not MLModel.objects.filter(model_type='temperature_prediction', is_active=True).exists():
                self.stdout.write('Treinando modelo de previsão de temperatura...')
                temp_model.train()
            
            # Fan Optimization
            fan_model = FanOptimizationModel()
            if not MLModel.objects.filter(model_type='fan_optimization', is_active=True).exists():
                self.stdout.write('Treinando modelo de otimização do ventilador...')
                fan_model.train()
            
            # Anomaly Detection
            anomaly_model = AnomalyDetectionModel()
            if not MLModel.objects.filter(model_type='anomaly_detection', is_active=True).exists():
                self.stdout.write('Treinando modelo de detecção de anomalias...')
                anomaly_model.train()
            
            self.stdout.write(self.style.SUCCESS('Modelos ML treinados com sucesso!'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro durante o treinamento: {str(e)}')
            )