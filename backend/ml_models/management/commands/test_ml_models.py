# backend/ml_models/management/commands/test_ml_models.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from ml_models.models import MLModel, MLPrediction
from sensors.models import Reading
import numpy as np
import pandas as pd
from datetime import timedelta

class Command(BaseCommand):
    help = 'Testa os modelos de ML ativos no sistema'

    def handle(self, *args, **kwargs):
        # 1. Listar modelos ativos
        active_models = MLModel.objects.filter(is_active=True)
        self.stdout.write("\n=== Modelos Ativos ===")
        
        if not active_models:
            self.stdout.write(self.style.WARNING("Nenhum modelo ativo encontrado!"))
            return
            
        for model in active_models:
            self.stdout.write(f"\nModelo: {model.name}")
            self.stdout.write(f"Tipo: {model.get_model_type_display()}")
            self.stdout.write(f"Versão: {model.version}")
            self.stdout.write(f"Última atualização: {model.updated_at}")
            
            # 2. Mostrar métricas do modelo
            self.stdout.write("\nMétricas:")
            if model.accuracy:
                self.stdout.write(f"- Acurácia: {model.accuracy:.2%}")
            if model.mse:
                self.stdout.write(f"- MSE: {model.mse:.4f}")
            if model.mae:
                self.stdout.write(f"- MAE: {model.mae:.4f}")
            if model.r2_score:
                self.stdout.write(f"- R²: {model.r2_score:.4f}")
                
            # 3. Últimas predições
            last_predictions = MLPrediction.objects.filter(
                model=model
            ).order_by('-created_at')[:5]
            
            self.stdout.write("\nÚltimas Predições:")
            for pred in last_predictions:
                self.stdout.write(f"- {pred.created_at}: {pred.prediction}")
            
            # 4. Fazer uma nova predição de teste
            self.stdout.write("\nTestando nova predição...")
            try:
                ml_model = model.load_model()
                if ml_model:
                    # Pegar últimas leituras para teste
                    recent_readings = Reading.objects.order_by('-timestamp')[:10]
                    if recent_readings:
                        # Preparar dados de entrada baseado no tipo de modelo
                        if model.model_type == 'temperature_prediction':
                            # Para predição de temperatura, usamos as últimas temperaturas
                            input_data = {
                                'last_temps': [r.temperature for r in recent_readings],
                                'timestamp': timezone.now().isoformat(),
                            }
                        elif model.model_type == 'anomaly_detection':
                            # Para detecção de anomalias, usamos a temperatura mais recente
                            input_data = {
                                'temperature': recent_readings[0].temperature,
                                'timestamp': recent_readings[0].timestamp.isoformat(),
                            }
                        else:
                            input_data = {'error': 'Tipo de modelo não suportado para teste'}
                        
                        # Criar predição
                        prediction = MLPrediction.objects.create(
                            model=model,
                            input_data=input_data,
                            prediction={'test': 'Test prediction'},
                            confidence=0.95  # Valor exemplo
                        )
                        
                        self.stdout.write(self.style.SUCCESS(
                            f"Predição de teste criada com sucesso! ID: {prediction.id}"
                        ))
                    else:
                        self.stdout.write(self.style.WARNING("Nenhuma leitura recente encontrada para teste"))
                else:
                    self.stdout.write(self.style.ERROR("Erro ao carregar o modelo do arquivo"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao testar modelo: {str(e)}"))