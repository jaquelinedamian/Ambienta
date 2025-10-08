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
from .base import BaseMLModel
from .cache import model_cache


class TemperaturePredictionModel(BaseMLModel):
    """
    Modelo para predição de temperatura baseado em dados históricos
    """
    
    def __init__(self):
        super().__init__(model_type='temperature_prediction')
        self._scaler = None
        self.feature_columns = [
            'hour', 'day_of_week', 'month', 
            'temp_lag_1', 'temp_lag_2', 'temp_lag_3',
            'temp_rolling_mean_3', 'temp_rolling_std_3',
            'fan_state'
        ]

    @property
    def scaler(self):
        if self._scaler is None:
            self._scaler = StandardScaler()
        return self._scaler
        
    def get_default_model(self):
        """
        Retorna um modelo padrão quando nenhum modelo salvo está disponível
        """
        return RandomForestRegressor(n_estimators=50, random_state=42)
    
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
        
        # Buscar dados de temperatura
        readings = Reading.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        if not readings.exists():
            raise ValueError("Não há dados suficientes para treinamento")
        
        # Converter para DataFrame
        df = pd.DataFrame(list(readings.values()))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Buscar estados do ventilador
        fan_states = FanState.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        if fan_states.exists():
            fan_df = pd.DataFrame(list(fan_states.values()))
            fan_df['timestamp'] = pd.to_datetime(fan_df['timestamp'])
            
            # Merge com interpolação
            df = pd.merge_asof(
                df.sort_values('timestamp'),
                fan_df[['timestamp', 'state']].sort_values('timestamp'),
                on='timestamp',
                direction='backward'
            )
            df['fan_state'] = df['state'].fillna(0).astype(int)
        else:
            df['fan_state'] = 0
        
        return df
    
    def train(self, days_back=30, test_size=0.2, force_retrain=False):
        """
        Desativado em produção - use o script de treinamento separado
        """
        print("Treinamento desativado em produção")
        return False
        
    def _train_legacy(self, days_back=30, test_size=0.2, force_retrain=False):
        """
        Método legado mantido para referência e desenvolvimento
        """
        # Verificar cache
        if not force_retrain and model_cache.get('temperature_prediction'):
            print("Usando modelo em cache")
            self._model = model_cache.get('temperature_prediction')
            return True

        try:
            # Obter dados
            df = self.get_training_data(days_back)
            
            # Preparar features
            df = self.prepare_features(df)
            
            # Remover linhas com NaN (devido aos lags)
            df = df.dropna()
            
            if len(df) < 10:
                raise ValueError("Dados insuficientes após limpeza (mínimo 10 amostras)")
            
            # Separar features e target
            X = df[self.feature_columns]
            y = df['temperature']
            
            # Split treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )
            
            # Criar pipeline com normalização
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                ))
            ])
            
            # Treinar modelo
            model.fit(X_train, y_train)
            
            # Avaliar
            y_pred = model.predict(X_test)
            
            metrics = {
                'mse': float(mean_squared_error(y_test, y_pred)),
                'mae': float(mean_absolute_error(y_test, y_pred)),
                'r2': float(r2_score(y_test, y_pred)),
                'training_samples': int(len(X_train)),
                'test_samples': int(len(X_test))
            }
            
            # Salvar modelo no cache e no disco
            self._model = model
            model_cache.set('temperature_prediction', model)
            self.save_model(metrics)
            
            return metrics
            
        except Exception as e:
            print(f"Erro no treinamento: {str(e)}")
            self._model = self.get_default_model()
            return False
    
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


class FanOptimizationModel(BaseMLModel):
    """
    Modelo para otimização inteligente do controle do ventilador
    """
    
    def __init__(self):
        super().__init__(model_type='fan_optimization')
        self._scaler = None
        self.temperature_threshold = 25.0
        
    def get_default_model(self):
        """
        Retorna um modelo padrão quando nenhum modelo salvo está disponível
        """
        return LinearRegression()

    @property
    def scaler(self):
        if self._scaler is None:
            self._scaler = StandardScaler()
        return self._scaler
    
    def create_dummy_data(self):
        """
        Cria dados sintéticos básicos para treino inicial com as mesmas colunas dos dados reais
        """
        # Criar 50 amostras de dados sintéticos
        n_samples = 50
        data = []
        
        # Gerar dados aleatórios que seguem regras simples
        for _ in range(n_samples):
            # Temperatura inicial entre 20°C e 35°C
            temp_before = np.random.uniform(20, 35)
            hour = np.random.randint(0, 24)
            day_of_week = np.random.randint(0, 7)
            
            # Define duração baseada na temperatura
            if temp_before > self.temperature_threshold:
                duration_minutes = max(5, min(60, (temp_before - self.temperature_threshold) * 5))
            else:
                duration_minutes = 0
                
            # Simula redução de temperatura baseada na duração
            # Quanto maior a duração, maior a redução, mas com um limite
            cooling_efficiency = min(5, duration_minutes * 0.1) if duration_minutes > 0 else 0
            
            data.append({
                'temp_before': temp_before,
                'duration_minutes': duration_minutes,
                'hour': hour,
                'day_of_week': day_of_week,
                'cooling_efficiency': cooling_efficiency
            })
        
        return pd.DataFrame(data)
    
    def get_training_data(self, days_back=30):
        """
        Obtém dados de eficiência do ventilador de forma otimizada
        """
        data = []
        
        try:
            # Limita o período de busca
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Busca limitada de estados do ventilador
            fan_states = list(FanState.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date,
                state=True  # Só estados ativos
            ).order_by('timestamp')[:50])  # Limite máximo de registros
            
            if not fan_states:
                print("Sem dados de ventilador suficientes. Usando dados sintéticos.")
                return self.create_dummy_data()
            
            # Processa os estados em lote
            for i in range(len(fan_states) - 1):
                current_state = fan_states[i]
                next_state = fan_states[i + 1]
                
                # Ignora ciclos muito longos
                duration = (next_state.timestamp - current_state.timestamp).total_seconds() / 60
                if duration > 60:  # Máximo 1 hora
                    continue
                
                try:
                    # Busca leituras de temperatura de forma otimizada
                    readings = list(Reading.objects.filter(
                        timestamp__gte=current_state.timestamp,
                        timestamp__lte=next_state.timestamp
                    ).order_by('timestamp')[:30])  # Limite de leituras por ciclo
                    
                    if len(readings) < 3:
                        continue
                    
                    temp_before = readings[0].temperature
                    temp_after = readings[-1].temperature
                    temps_during = [r.temperature for r in readings[1:-1]]
                    temp_during_avg = sum(temps_during) / len(temps_during)
                    
                    if temp_after < temp_before:  # Só considera ciclos com resfriamento
                        cooling_efficiency = temp_before - temp_after
                        data.append({
                            'temp_before': temp_before,
                            'duration_minutes': duration,
                            'hour': current_state.timestamp.hour,
                            'day_of_week': current_state.timestamp.weekday(),
                            'cooling_efficiency': cooling_efficiency
                        })
                except Exception as e:
                    print(f"Erro ao processar ciclo: {str(e)}")
                    continue
                    
            if len(data) < 5:
                print("Dados reais insuficientes. Usando dados sintéticos.")
                return self.create_dummy_data()
                
        except Exception as e:
            print(f"Erro ao buscar dados de treinamento: {str(e)}")
            return self.create_dummy_data()
            
        return pd.DataFrame(data)
    
    def train(self, days_back=30, force_retrain=False):
        """
        Desativado em produção - use o script de treinamento separado
        """
        print("Treinamento desativado em produção")
        return False
        
    def _train_legacy(self, days_back=30, force_retrain=False):
        """
        Método legado mantido para referência e desenvolvimento
        """
        features = ['temp_before', 'duration_minutes', 'hour', 'day_of_week']
        
        # Verificar cache
        if not force_retrain and model_cache.get('fan_optimization'):
            print("Usando modelo em cache")
            self._model = model_cache.get('fan_optimization')
            return True
            
        try:
            # Obtém dados limitados a 7 dias
            df = self.get_training_data(days_back=min(days_back, 7))
            
            # Verifica se precisa usar dados sintéticos
            if len(df) < 5:
                print("Usando dados sintéticos (dados insuficientes)")
                df = self.create_dummy_data()
                using_synthetic = True
            else:
                using_synthetic = False
            
            # Verifica features necessárias
            if not all(feature in df.columns for feature in features):
                print("Features ausentes no DataFrame, usando dados sintéticos")
                df = self.create_dummy_data()
                using_synthetic = True
            
            # Prepara dados para treino
            X = df[features]
            y = df['cooling_efficiency']
            
            # Escolhe e treina o modelo
            if using_synthetic:
                model = LinearRegression()
            else:
                model = RandomForestRegressor(n_estimators=20, max_depth=5)
            
            model.fit(X, y)
            
            # Avaliar modelo
            y_pred = model.predict(X)
            metrics = {
                'mse': float(mean_squared_error(y, y_pred)),
                'mae': float(mean_absolute_error(y, y_pred)),
                'r2': float(r2_score(y, y_pred)),
                'training_samples': int(len(X)),
                'using_synthetic': using_synthetic
            }
            
            # Salvar no cache e no disco
            self._model = model
            model_cache.set('fan_optimization', model)
            self.save_model(metrics)
            
            return metrics
            
        except Exception as e:
            print(f"Erro no treinamento: {str(e)}")
            self._model = self.get_default_model()
            return False
    
    def optimize_fan_duration(self, current_temp, current_hour):
        """
        Sugere duração otimizada para ligar o ventilador
        """
        # Configurações padrão
        default_duration = 15
        max_duration = 30
        
        # Regra básica: não ligar se temperatura abaixo do limiar
        if current_temp <= self.temperature_threshold:
            return 0
        
        try:
            # Se não tem modelo, usa regra simples
            if self.model is None:
                return max(5, min(max_duration, (current_temp - self.temperature_threshold) * 5))
            
            # Lista reduzida de durações para otimização
            durations = [5, 10, 15, 20, 30]
            best_duration = default_duration
            best_efficiency = 0
            
            # Base features para predição
            features = {
                'temp_before': current_temp,
                'hour': current_hour,
                'day_of_week': datetime.now().weekday()
            }
            
            # Testa diferentes durações
            for duration in durations:
                try:
                    X_pred = pd.DataFrame([{
                        **features,
                        'duration_minutes': duration
                    }])
                    
                    predicted_efficiency = float(self.model.predict(X_pred)[0])
                    adjusted_efficiency = predicted_efficiency * (1 - (duration / 120))
                    
                    if adjusted_efficiency > best_efficiency:
                        best_efficiency = adjusted_efficiency
                        best_duration = duration
                except:
                    continue
            
            return best_duration
            
        except Exception as e:
            print(f"Erro na otimização: {str(e)}")
            # Fallback para regra simples em caso de erro
            return max(5, min(max_duration, (current_temp - self.temperature_threshold) * 5))


class AnomalyDetectionModel(BaseMLModel):
    """
    Modelo para detecção de anomalias nos dados dos sensores
    """
    
    def __init__(self):
        super().__init__(model_type='anomaly_detection')
        self._scaler = StandardScaler()
        self.feature_names = ['temperature', 'hour', 'temp_diff', 'temp_deviation']
        self.normal_range = {'min': 15, 'max': 35}  # Faixa normal de temperatura
        self.is_fitted = False
        
    def get_default_model(self):
        """
        Retorna um modelo padrão quando nenhum modelo salvo está disponível
        """
        return IsolationForest(contamination=0.01, random_state=42)
    
    def get_training_data(self, days_back=30):
        """
        Obtém dados para treinamento de detecção de anomalias
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)
        
        readings = Reading.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        df = pd.DataFrame(list(readings.values()))
        if df.empty:
            raise ValueError("Não há dados para treinamento de anomalias")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Features para detecção de anomalias
        df['hour'] = df['timestamp'].dt.hour
        df['temp_diff'] = df['temperature'].diff()
        df['temp_rolling_mean'] = df['temperature'].rolling(window=5).mean()
        df['temp_deviation'] = abs(df['temperature'] - df['temp_rolling_mean'])
        
        return df.dropna()
    
    def train(self, days_back=30, force_retrain=False):
        """
        Desativado em produção - use o script de treinamento separado
        """
        print("Treinamento desativado em produção")
        return False
        
    def _train_legacy(self, days_back=30, force_retrain=False):
        """
        Método legado mantido para referência e desenvolvimento
        """
        # Verificar cache
        if not force_retrain and model_cache.get('anomaly_detection'):
            print("Usando modelo em cache")
            self._model = model_cache.get('anomaly_detection')
            self.is_fitted = True
            return True
            
        try:
            df = self.get_training_data(days_back)
            
            # Usar feature names definidos na inicialização
            X = df[self.feature_names].copy()
            
            # Garantir que não há valores nulos
            X = X.fillna(0)
            
            # Normalizar dados (fit_transform para treino)
            X_scaled = self._scaler.fit_transform(X)
            
            # Treinar modelo
            model = self.get_default_model()
            model.fit(X_scaled)
            
            # Avaliar em dados de treinamento
            predictions = model.predict(X_scaled)
            scores = model.score_samples(X_scaled)
            anomaly_ratio = (predictions == -1).sum() / len(predictions)
            
            metrics = {
                'anomaly_ratio': float(anomaly_ratio),
                'total_samples': int(len(X)),
                'anomalies_detected': int((predictions == -1).sum()),
                'average_score': float(np.mean(scores)),
                'min_score': float(np.min(scores)),
                'max_score': float(np.max(scores))
            }
            
            # Salvar no cache e no disco
            self._model = model
            self.is_fitted = True
            
            # Salvar também o scaler junto com o modelo
            model_data = {
                'model': model,
                'scaler': self._scaler,
                'is_fitted': True
            }
            
            model_cache.set('anomaly_detection', model_data)
            self.save_model(metrics)
            
            return metrics
            
        except Exception as e:
            print(f"Erro no treinamento: {str(e)}")
            self._model = self.get_default_model()
            self.is_fitted = False
            return False
    
    def detect_anomaly(self, temperature, hour=None):
        """
        Detecta se uma temperatura é anômala usando regras de negócio e modelo ML
        """
        # 1. Verificação baseada em regras de negócio primeiro
        if temperature < self.normal_range['min'] or temperature > self.normal_range['max']:
            return {
                'is_anomaly': True,
                'anomaly_score': -1.0,
                'confidence': 1.0,
                'reason': 'temperature_out_of_range'
            }
            
        if not self.is_fitted:
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.5,
                'reason': 'model_not_fitted'
            }
        
        if hour is None:
            hour = datetime.now().hour
            
        try:
            # Calcular features básicas (sem dados históricos completos)
            temp_diff = 0  # Simplificado
            temp_deviation = 0  # Simplificado
            
            X = np.array([[temperature, hour, temp_diff, temp_deviation]])
            X_scaled = self.scaler.transform(X)
            
            prediction = self.model.predict(X_scaled)[0]
            anomaly_score = self.model.score_samples(X_scaled)[0]
            
            # Determina se é uma anomalia baseado no score
            is_anomaly = prediction == -1 and abs(anomaly_score) > 0.5
            
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': float(anomaly_score),
                'confidence': float(abs(anomaly_score)),
                'reason': 'ml_prediction' if is_anomaly else 'normal'
            }
        except Exception as e:
            # Fallback para regra simples em caso de erro
            return {
                'is_anomaly': False,
                'anomaly_score': 0,
                'confidence': 0.5,
                'reason': f'error: {str(e)}'
            }


def train_all_models(force_retrain=False):
    """
    Função mantida para compatibilidade, mas desativada em produção
    """
    print("Treinamento desativado em produção - modelos já estão pré-treinados")
    return {}