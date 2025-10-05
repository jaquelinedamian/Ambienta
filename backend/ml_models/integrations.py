from datetime import datetime, timedelta
import logging

from .models import MLModel, MLPrediction
from .utils import serialize_ml_output
from .ml_algorithms import (
    TemperaturePredictionModel,
    FanOptimizationModel,
    AnomalyDetectionModel
)
from sensors.models import Reading, FanState, DeviceConfig
from django.utils import timezone

logger = logging.getLogger(__name__)


class MLIntegrationService:
    """
    Serviço principal para integrar ML com o sistema de sensores
    """
    
    @staticmethod
    def process_new_reading(reading):
        """
        Processa uma nova leitura de sensor com ML
        
        Args:
            reading: Instância do modelo Reading
        """
        try:
            # 1. Detectar anomalias
            anomaly_result = MLIntegrationService.check_anomaly(
                reading.temperature, 
                reading.timestamp.hour
            )
            
            # 2. Otimizar ventilador se necessário
            if reading.temperature > 24.0:  # Limiar configurável
                fan_optimization = MLIntegrationService.optimize_fan_control(
                    reading.temperature,
                    reading.timestamp.hour
                )
                
                # Se ML sugere ligar o ventilador, atualizar configuração
                if fan_optimization.get('should_turn_on', False):
                    MLIntegrationService.update_fan_config(fan_optimization)
            
            # 3. Log dos resultados
            logger.info(
                f"Leitura processada: {reading.temperature}°C - "
                f"Anomalia: {anomaly_result.get('is_anomaly', False)}"
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar leitura com ML: {str(e)}")
    
    @staticmethod
    def check_anomaly(temperature, hour=None):
        """
        Verifica se uma temperatura é anômala
        """
        try:
            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='anomaly_detection',
                is_active=True
            ).first()
            
            if not ml_model:
                # Fallback para regra simples
                result = {
                    'is_anomaly': temperature < 0 or temperature > 50,
                    'confidence': 0.5,
                    'method': 'rule_based'
                }
                return serialize_ml_output(result)  # Serializa resultado
            
            # Usar modelo ML
            anomaly_model = AnomalyDetectionModel()
            loaded_model = ml_model.load_model()
            
            if loaded_model and isinstance(loaded_model, dict):
                anomaly_model.model = loaded_model['model']
                anomaly_model.scaler = loaded_model['scaler']
                anomaly_model.is_fitted = True
                
                result = anomaly_model.detect_anomaly(temperature, hour)
                result['method'] = 'ml_model'
                
                # Serializa o resultado para garantir compatibilidade JSON
                result = serialize_ml_output(result)
                
                # Salvar predição
                MLPrediction.objects.create(
                    model=ml_model,
                    input_data={
                        'temperature': float(temperature), 
                        'hour': int(hour) if hour is not None else None
                    },
                    prediction=result,
                    confidence=float(result.get('confidence', 0))
                )
                
                return result
            
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias: {str(e)}")
        
        # Fallback
        result = {
            'is_anomaly': False,
            'confidence': 0,
            'method': 'error_fallback'
        }
        return serialize_ml_output(result)
    
    @staticmethod
    def optimize_fan_control(current_temperature, current_hour):
        """
        Otimiza controle do ventilador usando ML
        """
        try:
            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='fan_optimization',
                is_active=True
            ).first()
            
            if not ml_model:
                # Fallback para regra simples
                if current_temperature > 25.0:
                    duration = max(5, (current_temperature - 25.0) * 10)
                    result = {
                        'recommended_duration_minutes': int(duration),
                        'should_turn_on': True,
                        'method': 'rule_based'
                    }
                    return serialize_ml_output(result)
                else:
                    result = {
                        'recommended_duration_minutes': 0,
                        'should_turn_on': False,
                        'method': 'rule_based'
                    }
                    return serialize_ml_output(result)
            
            # Usar modelo ML
            fan_model = FanOptimizationModel()
            fan_model.model = ml_model.load_model()
            
            if fan_model.model:
                optimal_duration = fan_model.optimize_fan_duration(
                    current_temperature, 
                    current_hour
                )
                
                result = {
                    'recommended_duration_minutes': int(optimal_duration),
                    'should_turn_on': optimal_duration > 0,
                    'method': 'ml_model',
                    'current_temperature': current_temperature
                }
                
                # Serializa resultado antes de salvar
                serialized_result = serialize_ml_output(result)
                
                # Salvar predição
                MLPrediction.objects.create(
                    model=ml_model,
                    input_data={
                        'current_temperature': float(current_temperature),
                        'current_hour': current_hour
                    },
                    prediction=serialized_result
                )
                
                return serialized_result
            
        except Exception as e:
            logger.error(f"Erro na otimização do ventilador: {str(e)}")
        
        # Fallback
        result = {
            'recommended_duration_minutes': 10,
            'should_turn_on': current_temperature > 25.0,
            'method': 'error_fallback'
        }
        return serialize_ml_output(result)
    
    @staticmethod
    def update_fan_config(optimization_result):
        """
        Atualiza configuração do ventilador baseado na otimização ML
        """
        try:
            if not optimization_result.get('should_turn_on', False):
                return
            
            # Buscar ou criar configuração do dispositivo
            try:
                config = DeviceConfig.objects.get(device_id='default-device')
            except DeviceConfig.DoesNotExist:
                # Criar novo com valores padrão
                config = DeviceConfig.objects.create(
                    device_id='default-device',
                    wifi_ssid='NomeDaSuaRede',
                    wifi_password='SuaSenhaAqui',
                    start_hour='08:00:00',
                    end_hour='18:00:00',
                    force_on=False,
                    ml_control=False,
                    ml_duration=0,
                    ml_start_time=None
                )
            
            # Ativar ventilador se ML recomenda
            duration = optimization_result.get('recommended_duration_minutes', 10)
            
            # Atualizar campos de controle ML
            if duration > 0:
                now = timezone.now()
                config.ml_control = True
                config.ml_duration = duration
                config.ml_start_time = now
                config.force_on = True
                # Salvar explicitamente os campos que foram alterados
                config.save(update_fields=['ml_control', 'ml_duration', 'ml_start_time', 'force_on'])
                
                logger.info(
                    f"Ventilador ativado por ML - Duração recomendada: {duration} min - Início: {now.strftime('%H:%M:%S')}"
                )
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração do ventilador: {str(e)}")
    
    @staticmethod
    def get_temperature_forecast(hours_ahead=6):
        """
        Obtém previsão de temperatura para as próximas horas
        """
        try:
            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='temperature_prediction',
                is_active=True
            ).first()
            
            if not ml_model:
                result = {
                    'error': 'Nenhum modelo de predição disponível',
                    'method': 'no_model'
                }
                return serialize_ml_output(result)
            
            # Usar modelo ML
            temp_model = TemperaturePredictionModel()
            temp_model.model = ml_model.load_model()
            
            if temp_model.model:
                predictions = temp_model.predict(hours_ahead)
                
                # Preparar dados de resposta
                now = timezone.now()
                forecast_data = []
                
                for i, temp in enumerate(predictions):
                    forecast_time = now + timedelta(hours=i+1)
                    forecast_data.append({
                        'hour': forecast_time,  # Será serializado automaticamente
                        'predicted_temperature': round(float(temp), 2),
                        'hour_offset': i + 1
                    })
                
                result = {
                    'forecast': forecast_data,
                    'method': 'ml_model',
                    'model_name': ml_model.name
                }
                
                # Serializar resultado antes de salvar
                serialized_result = serialize_ml_output(result)
                
                # Salvar predição
                MLPrediction.objects.create(
                    model=ml_model,
                    input_data={'hours_ahead': hours_ahead},
                    prediction=serialized_result
                )
                
                return serialized_result
            
        except Exception as e:
            logger.error(f"Erro na previsão de temperatura: {str(e)}")
        
        # Fallback - previsão simples baseada na última leitura
        try:
            last_reading = Reading.objects.latest('timestamp')
            simple_forecast = []
            
            for i in range(hours_ahead):
                # Variação simples baseada na hora
                hour_variation = 0  # Simplificado
                predicted_temp = last_reading.temperature + hour_variation
                
                forecast_time = timezone.now() + timedelta(hours=i+1)
                simple_forecast.append({
                    'hour': forecast_time,  # Será serializado automaticamente
                    'predicted_temperature': round(float(predicted_temp), 2),
                    'hour_offset': i + 1
                })
            
            result = {
                'forecast': simple_forecast,
                'method': 'simple_fallback'
            }
            return serialize_ml_output(result)
            
        except Reading.DoesNotExist:
            result = {
                'error': 'Nenhum dado histórico disponível',
                'method': 'no_data'
            }
            return serialize_ml_output(result)
    
    @staticmethod
    def get_system_recommendations():
        """
        Obtém recomendações gerais do sistema baseadas em ML
        """
        recommendations = []
        
        try:
            # Verificar última leitura
            last_reading = Reading.objects.latest('timestamp')
            
            # 1. Recomendação de temperatura
            if last_reading.temperature > 27:
                recommendations.append({
                    'type': 'temperature_alert',
                    'priority': 'high',
                    'message': f'Temperatura alta detectada: {last_reading.temperature}°C',
                    'action': 'Considere ligar o ventilador'
                })
            
            # 2. Verificar anomalias recentes
            recent_anomalies = MLPrediction.objects.filter(
                model__model_type='anomaly_detection',
                created_at__gte=timezone.now() - timedelta(hours=2),
                prediction__is_anomaly=True
            ).count()
            
            if recent_anomalies > 0:
                recommendations.append({
                    'type': 'anomaly_alert',
                    'priority': 'medium',
                    'message': f'{recent_anomalies} anomalia(s) detectada(s) nas últimas 2 horas',
                    'action': 'Verificar sensores'
                })
            
            # 3. Recomendação de treinamento
            oldest_model = MLModel.objects.filter(
                is_active=True
            ).order_by('last_trained').first()
            
            if oldest_model and oldest_model.last_trained:
                days_since_training = (timezone.now() - oldest_model.last_trained).days
                if days_since_training > 7:
                    recommendations.append({
                        'type': 'training_recommendation',
                        'priority': 'low',
                        'message': f'Modelo mais antigo treinado há {days_since_training} dias',
                        'action': 'Considere retreinar os modelos'
                    })
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {str(e)}")
        
        return serialize_ml_output(recommendations)


# Funções utilitárias para uso em outros apps
def process_sensor_reading(reading):
    """Função pública para processar leitura de sensor"""
    return MLIntegrationService.process_new_reading(reading)

def get_ml_recommendations():
    """Função pública para obter recomendações ML"""
    return MLIntegrationService.get_system_recommendations()

def check_temperature_anomaly(temperature, hour=None):
    """Função pública para verificar anomalias"""
    return MLIntegrationService.check_anomaly(temperature, hour)