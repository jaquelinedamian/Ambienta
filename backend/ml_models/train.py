# backend/ml_models/train.py

import os
import sys
import django

# Adiciona o diretório do projeto ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ambienta.settings')
django.setup()

from ml_algorithms import (
    TemperaturePredictionModel,
    FanOptimizationModel,
    AnomalyDetectionModel
)

def train_models():
    """
    Script para treinar os modelos localmente em desenvolvimento
    """
    print("Iniciando treinamento dos modelos...")
    
    # Treina modelo de temperatura
    print("\n1. Treinando modelo de predição de temperatura...")
    temp_model = TemperaturePredictionModel()
    metrics = temp_model._train_legacy(days_back=30, force_retrain=True)
    print("Métricas:", metrics)
    
    # Treina modelo de ventilador
    print("\n2. Treinando modelo de otimização do ventilador...")
    fan_model = FanOptimizationModel()
    metrics = fan_model._train_legacy(days_back=7, force_retrain=True)
    print("Métricas:", metrics)
    
    # Treina modelo de anomalias
    print("\n3. Treinando modelo de detecção de anomalias...")
    anomaly_model = AnomalyDetectionModel()
    metrics = anomaly_model._train_legacy(days_back=30, force_retrain=True)
    print("Métricas:", metrics)
    
    print("\nTreinamento concluído!")

if __name__ == '__main__':
    train_models()