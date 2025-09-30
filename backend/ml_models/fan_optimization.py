import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime, timedelta
from django.db.models import Avg, StdDev
from django.utils import timezone

from .models import MLModel, MLPrediction
from sensors.models import Reading, FanState, FanLog

class FanOptimizationModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        
    def prepare_features(self, readings, current_hour, current_day):
        """Prepara as features para o modelo."""
        features = []
        for reading in readings:
            # Características temporais
            reading_hour = reading.timestamp.hour
            reading_day = reading.timestamp.weekday()
            
            # Características de temperatura
            temp = reading.temperature
            
            # Histórico de uso do ventilador
            fan_state = FanState.objects.filter(timestamp__lte=reading.timestamp).order_by('-timestamp').first()
            fan_active = 1 if fan_state and fan_state.state else 0
            
            # Calcular média e desvio das últimas horas
            past_readings = Reading.objects.filter(
                timestamp__lt=reading.timestamp,
                timestamp__gte=reading.timestamp - timedelta(hours=3)
            )
            temp_mean = past_readings.values_list('temperature', flat=True).aggregate(Avg('temperature'))['temperature__avg'] or temp
            temp_std = past_readings.values_list('temperature', flat=True).aggregate(StdDev('temperature'))['temperature__std'] or 0
            
            features.append([
                temp,               # Temperatura atual
                temp_mean,         # Média de temperatura (3h)
                temp_std,          # Desvio padrão (3h)
                reading_hour,      # Hora do dia (0-23)
                reading_day,       # Dia da semana (0-6)
                fan_active,        # Estado anterior do ventilador
            ])
            
        return np.array(features)

    def prepare_labels(self, readings):
        """Prepara os labels (se o ventilador deveria estar ligado ou não)."""
        labels = []
        for reading in readings:
            # Verifica se a temperatura estava alta
            temp_high = reading.temperature > 25.0
            
            # Verifica se o ventilador foi efetivo (temperatura reduziu nas próximas leituras)
            future_readings = Reading.objects.filter(
                timestamp__gt=reading.timestamp,
                timestamp__lte=reading.timestamp + timedelta(minutes=30)
            ).order_by('timestamp')
            
            fan_effective = False
            if future_readings.exists():
                temp_reduction = reading.temperature - future_readings.last().temperature
                fan_effective = temp_reduction > 0.5  # Redução de 0.5°C ou mais
            
            # O ventilador deveria estar ligado se:
            # 1. A temperatura estava alta E
            # 2. O uso do ventilador foi efetivo OU ainda não temos dados de efetividade
            should_be_on = temp_high and (fan_effective or not future_readings.exists())
            labels.append(1 if should_be_on else 0)
            
        return np.array(labels)

    def train(self):
        """Treina o modelo com dados históricos."""
        # Obter dados dos últimos 7 dias
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        readings = Reading.objects.filter(timestamp__range=(start_date, end_date)).order_by('timestamp')
        
        if not readings.exists():
            raise ValueError("Não há dados suficientes para treinar o modelo")
            
        current_hour = end_date.hour
        current_day = end_date.weekday()
        
        # Preparar dados
        X = self.prepare_features(readings, current_hour, current_day)
        y = self.prepare_labels(readings)
        
        # Normalizar features
        X = self.scaler.fit_transform(X)
        
        # Treinar modelo
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        
        # Salvar o modelo
        model_path = 'models/fan_optimization_v1.0.pkl'
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler
        }, model_path)
        
        # Registrar/atualizar o modelo no banco de dados
        ml_model, created = MLModel.objects.update_or_create(
            name='Fan Optimization',
            defaults={
                'model_type': 'fan_optimization',
                'version': '1.0',
                'file_path': model_path,
                'is_active': True,
                'last_trained': timezone.now()
            }
        )
        
        return ml_model

    def predict(self, current_temperature, current_hour, current_day):
        """Faz uma predição se o ventilador deve ser ligado."""
        if not self.model:
            # Carregar modelo salvo
            model_data = joblib.load('models/fan_optimization_v1.0.pkl')
            self.model = model_data['model']
            self.scaler = model_data['scaler']
        
        # Preparar features para predição
        features = np.array([[
            current_temperature,
            current_temperature,  # Usar temperatura atual como média também
            0.0,                 # Desvio padrão inicial 0
            current_hour,
            current_day,
            0                    # Estado anterior do ventilador (0 por padrão)
        ]])
        
        # Normalizar features
        features_scaled = self.scaler.transform(features)
        
        # Fazer predição
        should_turn_on = self.model.predict(features_scaled)[0]
        confidence = np.max(self.model.predict_proba(features_scaled)[0])
        
        return should_turn_on, confidence