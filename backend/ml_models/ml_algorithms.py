# backend/ml_models/ml_algorithms.py

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from datetime import datetime, timedelta
import joblib
import os
from django.utils import timezone
from django.db import models
from sensors.models import Reading, FanState, FanLog
from .models import MLModel, MLPrediction, TrainingSession, ModelPerformanceMetric


class TemperaturePredictionModel:
    """
    Modelo para predição de temperatura baseado em dados históricos
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler(with_feature_names=False)  # Desabilita feature names no scikit-learn 1.4+
        self.feature_columns = [
            'hour', 'day_of_week', 'month', 
            'temp_lag_1', 'temp_lag_2', 'temp_lag_3',
            'temp_rolling_mean_3', 'temp_rolling_std_3',
            'fan_state'
        ]
    
    def prepare_features(self, df):
        """
        Prepara features temporais e de lag para o modelo
        """
        # Features temporais
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        # Features de lag (temperaturas anteriores)
        df['temp_lag_1'] = df['temperature'].shift(1)
        df['temp_lag_2'] = df['temperature'].shift(2)
        df['temp_lag_3'] = df['temperature'].shift(3)
        
        # Features de rolling (médias móveis)
        df['temp_rolling_mean_3'] = df['temperature'].rolling(window=3).mean()
        df['temp_rolling_std_3'] = df['temperature'].rolling(window=3).std()
        
        # Estado do ventilador (assumindo que existe um modelo FanState)
        # Se não houver correspondência exata, usar interpolação
        df['fan_state'] = 0  # Default
        
        return df
    
    def get_training_data(self, days_back=30):
        """
        Obtém dados de treinamento dos últimos N dias
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)
        print(f"\nTemperaturePredictionModel - Buscando dados de {start_date} até {end_date}")
        
        # Buscar dados de temperatura
        readings = Reading.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        if not readings.exists():
            raise ValueError("Não há dados suficientes para treinamento")
            
        readings_count = readings.count()
        print(f"TemperaturePredictionModel - Encontradas {readings_count} leituras de temperatura")
        
        # Converter para DataFrame
        df = pd.DataFrame(list(readings.values()))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Buscar estados do ventilador
        fan_states = FanState.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        if fan_states.exists():
            fan_states_count = fan_states.count()
            print(f"TemperaturePredictionModel - Encontrados {fan_states_count} estados do ventilador")
            
            fan_df = pd.DataFrame(list(fan_states.values()))
            fan_df['timestamp'] = pd.to_datetime(fan_df['timestamp'])
            
            # Merge com interpolação e tolerância de 5 minutos
            df = pd.merge_asof(
                df.sort_values('timestamp'),
                fan_df[['timestamp', 'state']].sort_values('timestamp'),
                on='timestamp',
                direction='nearest',  # Pega o estado mais próximo
                tolerance=pd.Timedelta('5min')  # Máximo 5 minutos de diferença
            )
            
            # Se ainda houver NaN após o merge, preenche com estado anterior ou 0
            df['state'] = df['state'].fillna(method='ffill').fillna(0)
            df['fan_state'] = df['state'].astype(int)
        else:
            df['fan_state'] = 0
            
        # Remove linhas onde não temos estado do ventilador após muito tempo sem leitura
        if len(df) > 0:
            print(f"Total de amostras antes da limpeza: {len(df)}")
        
        return df
    
    def train(self, days_back=30, test_size=0.2, training_session=None):
        """
        Treina o modelo de predição de temperatura
        """
        # Obter dados
        df = self.get_training_data(days_back)
        
        # Preparar features
        df = self.prepare_features(df)
        
        # Remover linhas com NaN (devido aos lags)
        df = df.dropna()
        
        if len(df) < 10:
            raise ValueError("Dados insuficientes após limpeza (mínimo 10 amostras)")
            
        # Atualizar número de amostras na sessão de treinamento
        if training_session:
            training_session.training_samples = len(df)
            training_session.save()
        
        # Separar features e target
        X = df[self.feature_columns]
        y = df['temperature']
        
        # Split treino/teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )
        
        # Criar pipeline com normalização
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ))
        ])
        
        # Treinar modelo
        self.model.fit(X_train, y_train)
        
        # Avaliar
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'mse': float(mean_squared_error(y_test, y_pred)),
            'mae': float(mean_absolute_error(y_test, y_pred)),
            'r2': float(r2_score(y_test, y_pred)),
            'training_samples': int(len(X_train)),
            'test_samples': int(len(X_test))
        }
        
        return metrics
    
    def predict(self, hours_ahead=1):
        """
        Faz predição de temperatura para as próximas horas
        """
        if self.model is None:
            raise ValueError("Modelo não foi treinado")
        
        # Obter dados recentes para construir features
        recent_data = self.get_training_data(days_back=7)
        recent_data = self.prepare_features(recent_data)
        recent_data = recent_data.dropna()
        
        if len(recent_data) == 0:
            raise ValueError("Não há dados recentes suficientes para predição")
        
        predictions = []
        current_data = recent_data.iloc[-1:].copy()
        
        for i in range(hours_ahead):
            # Ajustar hora
            next_hour = current_data['hour'].iloc[0] + 1
            if next_hour >= 24:
                next_hour = 0
            current_data['hour'] = next_hour
            
            # Fazer predição
            X = current_data[self.feature_columns]
            pred = self.model.predict(X)[0]
            predictions.append(pred)
            
            # Atualizar features de lag para próxima iteração
            current_data['temp_lag_3'] = current_data['temp_lag_2']
            current_data['temp_lag_2'] = current_data['temp_lag_1']
            current_data['temp_lag_1'] = pred
        
        return predictions


class FanOptimizationModel:
    """
    Modelo para otimização inteligente do controle do ventilador
    """
    
    def __init__(self):
        self.model = None
        self.temperature_threshold = 25.0
        
    def get_current_state(self):
        """
        Obtém o estado atual do sistema
        """
        try:
            # Pegar última leitura de temperatura
            last_reading = Reading.objects.order_by('-timestamp').first()
            
            # Pegar último estado do ventilador
            last_fan_state = FanState.objects.order_by('-timestamp').first()
            
            if not last_reading:
                return {
                    'error': 'Sem leituras disponíveis',
                    'state': False,
                    'confidence': 0,
                    'temperature': None
                }
            
            # Se não tiver estado do ventilador, assume desligado
            current_state = last_fan_state.state if last_fan_state else False
            
            # Fazer predição com os dados atuais
            should_turn_on, confidence = self.predict(
                current_temp=last_reading.temperature,
                current_hour=last_reading.timestamp.hour,
                current_day=last_reading.timestamp.weekday()
            )
            
            return {
                'state': should_turn_on,
                'confidence': float(confidence),
                'temperature': float(last_reading.temperature)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'state': False,
                'confidence': 0,
                'temperature': None
            }
    
    def get_training_data(self, days_back=30):
        """
        Obtém dados de eficiência do ventilador
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)
        print(f"\nFanOptimizationModel - Buscando dados de {start_date} até {end_date}")
        
        # Buscar estados do ventilador
        fan_states = FanState.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        fan_states_count = fan_states.count()
        print(f"FanOptimizationModel - Encontrados {fan_states_count} estados do ventilador")
        
        data = []
        for i in range(len(fan_states) - 1):
            current_state = fan_states[i]
            next_state = fan_states[i + 1]
            
            if current_state.state:  # Se o ventilador está ligado
                # Calcular duração do ciclo
                duration = (next_state.timestamp - current_state.timestamp).total_seconds() / 60
                
                # Pegar temperatura no início do ciclo
                temp_before = Reading.objects.filter(
                    timestamp__lte=current_state.timestamp
                ).order_by('-timestamp').first()
                
                # Pegar temperatura no fim do ciclo
                temp_after = Reading.objects.filter(
                    timestamp__gte=next_state.timestamp
                ).order_by('timestamp').first()
                
                # Pegar temperaturas durante o ciclo
                temps_during = list(Reading.objects.filter(
                    timestamp__gt=current_state.timestamp,
                    timestamp__lt=next_state.timestamp
                ).values_list('temperature', flat=True))
                
                if temp_before and temp_after and temps_during:  # Agora temps_during é uma lista
                    temp_during_avg = sum(temps_during) / len(temps_during)
                    
                    # Só adiciona se tiver pelo menos 3 leituras durante o ciclo
                    if len(temps_during) >= 3:
                        data.append({
                            'temp_before': temp_before.temperature,
                            'temp_during': temp_during_avg,
                            'temp_after': temp_after.temperature,
                            'duration_minutes': duration,
                            'hour': current_state.timestamp.hour,
                            'day_of_week': current_state.timestamp.weekday(),
                            'cooling_efficiency': temp_before.temperature - temp_after.temperature
                        })
        
        return pd.DataFrame(data)
    
    def train(self, days_back=30, training_session=None):
        """
        Treina modelo de otimização do ventilador
        """
        df = self.get_training_data(days_back)
        
        if len(df) < 5:
            raise ValueError("Dados insuficientes para treinamento de otimização")
        
        # Features para predizer eficiência de resfriamento
        features = ['temp_before', 'duration_minutes', 'hour', 'day_of_week']
        X = df[features]
        y = df['cooling_efficiency']
        
        self.model = RandomForestRegressor(
            n_estimators=50,
            max_depth=8,
            random_state=42
        )
        
        self.model.fit(X, y)
        
        # Calcular métricas
        y_pred = self.model.predict(X)
        metrics = {
            'mse': float(mean_squared_error(y, y_pred)),
            'mae': float(mean_absolute_error(y, y_pred)),
            'r2': float(r2_score(y, y_pred)),
            'training_samples': int(len(X))
        }
        
        # Atualizar número de amostras na sessão de treinamento
        if training_session:
            training_session.training_samples = len(X)
            training_session.save()
        
        return metrics
    
    def predict(self, current_temp, current_hour, current_day):
        """
        Prediz se o ventilador deve ser ligado e com qual confiança.
        Retorna uma tupla (should_turn_on, confidence, duration, efficiency)
        """
        from sensors.models import FanState, Reading
        from django.utils import timezone
        from datetime import timedelta
        
        if self.model is None:
            # Fallback para regra simples
            should_turn_on = current_temp > self.temperature_threshold
            return should_turn_on, 0.5, 5, 0.0  # Valores padrão para modo fallback
        
        # Buscar histórico recente de efetividade
        recent_fan_states = FanState.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-timestamp')
        
        historical_effectiveness = 0.0
        if recent_fan_states.exists():
            successful_activations = 0
            total_activations = 0
            for state in recent_fan_states:
                if state.start_time and state.end_time:
                    temp_before = Reading.objects.filter(
                        timestamp__lte=state.start_time
                    ).order_by('-timestamp').first()
                    
                    temp_after = Reading.objects.filter(
                        timestamp__gte=state.end_time
                    ).order_by('timestamp').first()
                    
                    if temp_before and temp_after:
                        if temp_before.temperature > temp_after.temperature:
                            successful_activations += 1
                        total_activations += 1
            
            if total_activations > 0:
                historical_effectiveness = successful_activations / total_activations
        
        # Testar diferentes durações
        durations = [5, 10, 15, 20, 30, 45, 60]
        best_duration = 5
        best_efficiency = 0
        total_efficiency = 0
        positive_scenarios = 0
        
        for duration in durations:
            predicted_efficiency = self.model.predict([[
                current_temp, duration, current_hour, current_day
            ]])[0]
            
            # Ajustar eficiência baseado no histórico
            adjusted_efficiency = predicted_efficiency * (0.7 + 0.3 * historical_effectiveness)
            
            total_efficiency += adjusted_efficiency
            if adjusted_efficiency > 0:
                positive_scenarios += 1
            
            if adjusted_efficiency > best_efficiency:
                best_efficiency = adjusted_efficiency
                best_duration = duration
        
        # Determinar se deve ligar baseado na eficiência média ajustada
        avg_efficiency = total_efficiency / len(durations)
        min_efficiency_threshold = 0.1  # Eficiência mínima requerida
        
        should_turn_on = (
            avg_efficiency > min_efficiency_threshold and 
            current_temp > self.temperature_threshold and
            positive_scenarios >= len(durations) // 2  # Pelo menos metade dos cenários positivos
        )
        
        # Calcular confiança com base em múltiplos fatores
        if should_turn_on:
            efficiency_factor = best_efficiency / max(predicted_efficiency for duration in durations)
            historical_factor = 0.7 + 0.3 * historical_effectiveness
            temperature_factor = min(1.0, (current_temp - self.temperature_threshold) / 5.0)
            
            confidence = min(1.0, max(0.1,
                efficiency_factor * 0.4 +  # Peso da eficiência prevista
                historical_factor * 0.4 +  # Peso do histórico
                temperature_factor * 0.2    # Peso da temperatura atual
            ))
        else:
            confidence = min(1.0, max(0.1, 1.0 - (positive_scenarios / len(durations))))
        
        return should_turn_on, confidence, best_duration, best_efficiency

    def optimize_fan_duration(self, current_temp, current_hour):
        """
        Sugere duração otimizada para ligar o ventilador
        """
        if self.model is None:
            # Fallback para regra simples
            if current_temp > self.temperature_threshold:
                return max(5, (current_temp - self.temperature_threshold) * 10)
            return 0
        
        # Testar diferentes durações
        durations = [5, 10, 15, 20, 30, 45, 60]
        best_duration = 5
        best_efficiency = 0
        
        for duration in durations:
            predicted_efficiency = self.model.predict([[
                current_temp, duration, current_hour, datetime.now().weekday()
            ]])[0]
            
            if predicted_efficiency > best_efficiency:
                best_efficiency = predicted_efficiency
                best_duration = duration
        
        return best_duration if current_temp > self.temperature_threshold else 0


class AnomalyDetectionModel:
    """
    Modelo para detecção de anomalias nos dados dos sensores
    """
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,  # 10% de dados anômalos esperados
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def get_training_data(self, days_back=30):
        """
        Obtém dados para treinamento de detecção de anomalias
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)
        print(f"\nAnomalyDetectionModel - Buscando dados de {start_date} até {end_date}")
        
        readings = Reading.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        df = pd.DataFrame(list(readings.values()))
        if df.empty:
            raise ValueError("Não há dados para treinamento de anomalias")
            
        readings_count = len(df)
        print(f"AnomalyDetectionModel - Encontradas {readings_count} leituras de temperatura")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Features para detecção de anomalias
        df['hour'] = df['timestamp'].dt.hour
        df['temp_diff'] = df['temperature'].diff()
        df['temp_rolling_mean'] = df['temperature'].rolling(window=5).mean()
        df['temp_deviation'] = abs(df['temperature'] - df['temp_rolling_mean'])
        
        return df.dropna()
    
    def train(self, days_back=30, training_session=None):
        """
        Treina modelo de detecção de anomalias
        """
        df = self.get_training_data(days_back)
        
        features = ['temperature', 'hour', 'temp_diff', 'temp_deviation']
        X = df[features]
        
        # Normalizar dados
        X_scaled = self.scaler.fit_transform(X)
        
        # Treinar modelo
        self.model.fit(X_scaled)
        self.is_fitted = True
        
        # Avaliar em dados de treinamento
        predictions = self.model.predict(X_scaled)
        anomaly_ratio = (predictions == -1).sum() / len(predictions)
        
        # Atualizar número de amostras na sessão de treinamento
        if training_session:
            training_session.training_samples = len(X)
            training_session.save()
        
        return {
            'anomaly_ratio': float(anomaly_ratio),
            'total_samples': int(len(X)),
            'anomalies_detected': int((predictions == -1).sum())
        }
    
    def detect_anomaly(self, temperature, hour=None):
        """
        Detecta se uma leitura é anômala
        """
        if not self.is_fitted:
            raise ValueError("Modelo não foi treinado")
        
        if hour is None:
            hour = datetime.now().hour
        
        # Calcular features básicas (sem dados históricos completos)
        temp_diff = 0  # Simplificado
        temp_deviation = 0  # Simplificado
        
        X = np.array([[temperature, hour, temp_diff, temp_deviation]])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        anomaly_score = self.model.score_samples(X_scaled)[0]
        
        return {
            'is_anomaly': prediction == -1,
            'anomaly_score': anomaly_score,
            'confidence': abs(anomaly_score)
        }


def train_all_models(training_session=None):
    """
    Treina todos os modelos de ML disponíveis
    """
    results = {}
    total_samples = 0
    
    try:
        # Modelo de predição de temperatura
        temp_model = TemperaturePredictionModel()
        temp_metrics = temp_model.train(training_session=training_session)
        
        # Buscar ou criar modelo
        ml_model_temp, created = MLModel.objects.get_or_create(
            model_type="temperature_prediction",
            version="1.0",
            defaults={
                'name': "Predição de Temperatura",
                'description': "Modelo para predizer temperatura baseado em dados históricos",
                'is_active': True,
                'last_trained': timezone.now()
            }
        )
        
        # Atualizar métricas
        ml_model_temp.mse = temp_metrics['mse']
        ml_model_temp.mae = temp_metrics['mae']
        ml_model_temp.r2_score = temp_metrics['r2']
        ml_model_temp.last_trained = timezone.now()
        ml_model_temp.is_active = True
        ml_model_temp.save()
        
        ml_model_temp.save_model(temp_model.model)
        
        results['temperature_prediction'] = temp_metrics
        
    except Exception as e:
        results['temperature_prediction'] = {'error': str(e)}
    
    try:
        # Modelo de otimização do ventilador
        fan_model = FanOptimizationModel()
        fan_metrics = fan_model.train(training_session=training_session)
        
        ml_model_fan, created = MLModel.objects.get_or_create(
            model_type="fan_optimization",
            version="1.0",
            defaults={
                'name': "Otimização de Ventilador",
                'description': "Modelo para otimizar controle do ventilador",
                'is_active': True,
                'last_trained': timezone.now()
            }
        )
        
        # Atualizar métricas
        ml_model_fan.mse = fan_metrics['mse']
        ml_model_fan.mae = fan_metrics['mae']
        ml_model_fan.r2_score = fan_metrics['r2']
        ml_model_fan.last_trained = timezone.now()
        ml_model_fan.is_active = True
        ml_model_fan.save()
        
        ml_model_fan.save_model(fan_model.model)
        
        results['fan_optimization'] = fan_metrics
        
    except Exception as e:
        results['fan_optimization'] = {'error': str(e)}
    
    try:
        # Modelo de detecção de anomalias
        anomaly_model = AnomalyDetectionModel()
        anomaly_metrics = anomaly_model.train(training_session=training_session)
        
        ml_model_anomaly, created = MLModel.objects.get_or_create(
            model_type="anomaly_detection",
            version="1.0",
            defaults={
                'name': "Detecção de Anomalias",
                'description': "Modelo para detectar anomalias nos sensores",
                'is_active': True,
                'last_trained': timezone.now()
            }
        )
        
        # Atualizar métricas
        ml_model_anomaly.accuracy = 1 - anomaly_metrics['anomaly_ratio']
        ml_model_anomaly.last_trained = timezone.now()
        ml_model_anomaly.is_active = True
        ml_model_anomaly.save()
        
        # Salvar o modelo com scaler
        model_data = {
            'model': anomaly_model.model,
            'scaler': anomaly_model.scaler
        }
        ml_model_anomaly.save_model(model_data)
        
        results['anomaly_detection'] = anomaly_metrics
        
    except Exception as e:
        results['anomaly_detection'] = {'error': str(e)}
    
    return results