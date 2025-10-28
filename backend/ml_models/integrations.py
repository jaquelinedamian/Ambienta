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
    def get_optimized_temperature_limit(current_temp):
        """
        Calcula o limite de temperatura otimizado baseado nas condições atuais
        
        Args:
            current_temp: Temperatura atual
            
        Returns:
            float: Limite de temperatura otimizado ou None se não puder calcular
        """
        try:
            fan_model = FanOptimizationModel()
            # Carregar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='fan_optimization',
                is_active=True
            ).first()
            
            if not ml_model:
                return None
                
            loaded_model = ml_model.load_model()
            if loaded_model:
                fan_model.model = loaded_model
                
                # Calcular limite dinâmico
                base_limit = 25.0  # Limite base
                
                # Ajustar limite baseado na eficiência do resfriamento
                efficiency = fan_model.estimate_cooling_efficiency(current_temp)
                if efficiency:
                    # Ajusta o limite entre 23°C e 27°C baseado na eficiência
                    dynamic_limit = base_limit - (efficiency * 2) + 2
                    return max(23.0, min(27.0, dynamic_limit))
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao calcular limite de temperatura: {str(e)}")
            return None
    
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
            
            # 2. Predição de temperatura futura
            prediction = MLIntegrationService.predict_temperature(
                reading.temperature,
                reading.timestamp.hour
            )
            
            # 3. Otimizar ventilador baseado na temperatura atual e predita
            should_optimize = (
                reading.temperature > 24.0 or  # Temperatura atual alta
                (prediction and prediction.get('predicted_temperature', 0) > 26.0)  # Previsão alta
            )
            
            if should_optimize:
                fan_optimization = MLIntegrationService.optimize_fan_control(
                    reading.temperature,
                    reading.timestamp.hour,
                    predicted_temp=prediction.get('predicted_temperature') if prediction else None
                )
                
                # Se ML sugere ligar o ventilador, atualizar configuração
                if fan_optimization.get('should_turn_on', False):
                    MLIntegrationService.update_fan_config(fan_optimization)
            
            # 4. Log dos resultados
            logger.info(
                f"Leitura processada: {reading.temperature}°C - "
                f"Anomalia: {anomaly_result.get('is_anomaly', False)} - "
                f"Previsão: {prediction.get('predicted_temperature', 'N/A')}°C"
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
    def optimize_fan_control(current_temperature, current_hour, predicted_temp=None):
        """
        Otimiza controle do ventilador usando ML e previsão de temperatura
        
        Args:
            current_temperature: Temperatura atual
            current_hour: Hora atual (0-23)
            predicted_temp: Temperatura prevista para próxima hora (opcional)
        """
        try:
            # Obter configuração atual
            try:
                config = DeviceConfig.objects.get(device_id='default-device')
            except DeviceConfig.DoesNotExist:
                logger.warning("Configuração não encontrada. Criando padrão...")
                config = DeviceConfig.objects.create(
                    device_id='default-device',
                    ml_control=True,
                    start_hour=timezone.now().replace(hour=8, minute=0),
                    end_hour=timezone.now().replace(hour=22, minute=0)
                )
            
            # Verificar se ML Control está ativado
            if not config.ml_control:
                logger.info("ML Control desativado nas configurações")
                return {
                    'recommended_duration_minutes': 0,
                    'should_turn_on': False,
                    'method': 'ml_disabled',
                    'message': 'Controle ML desativado nas configurações'
                }
            
            # Verificar se está dentro do horário permitido
            current_time = timezone.localtime().time()
            start_time = config.start_hour
            end_time = config.end_hour
            
            # Se o horário atual está fora do período permitido, não liga
            if start_time < end_time:  # Período normal (ex: 8:00 - 22:00)
                if current_time < start_time or current_time > end_time:
                    return {
                        'recommended_duration_minutes': 0,
                        'should_turn_on': False,
                        'method': 'outside_hours',
                        'message': f'Fora do horário permitido ({start_time.strftime("%H:%M")} - {end_time.strftime("%H:%M")})'
                    }
            else:  # Período que cruza meia-noite (ex: 22:00 - 06:00)
                if current_time > end_time and current_time < start_time:
                    return {
                        'recommended_duration_minutes': 0,
                        'should_turn_on': False,
                        'method': 'outside_hours',
                        'message': f'Fora do horário permitido ({start_time.strftime("%H:%M")} - {end_time.strftime("%H:%M")})'
                    }
            
            # Verificar se o ventilador já está em um ciclo de ML
            if config.ml_start_time:
                time_since_start = timezone.now() - config.ml_start_time
                if time_since_start.total_seconds() < (config.ml_duration * 60):
                    # Ainda dentro do período recomendado, não faz nada
                    return {
                        'recommended_duration_minutes': 0,
                        'should_turn_on': False,
                        'method': 'cooling_in_progress',
                        'message': f'Ciclo de resfriamento em andamento: {config.ml_duration}min'
                    }

            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='fan_optimization',
                is_active=True
            ).first()
            
            if not ml_model:
                # Fallback para regra simples mais conservadora
                if current_temperature > 27.0:  # Aumentado o limite
                    duration = max(5, (current_temperature - 27.0) * 15)
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
            loaded_model = ml_model.load_model()
            
            if loaded_model and isinstance(loaded_model, dict):
                fan_model.model = loaded_model['model']
                fan_model.scaler = loaded_model.get('scaler')
                
                # Considera temperatura prevista se disponível
                temp_to_use = max(current_temperature, predicted_temp or 0)
                
                optimal_duration = fan_model.optimize_fan_duration(
                    temp_to_use,
                    current_hour
                )
                
                result = {
                    'recommended_duration_minutes': int(optimal_duration),
                    'should_turn_on': optimal_duration > 0,
                    'method': 'ml_model',
                    'current_temperature': current_temperature,
                    'predicted_temperature': predicted_temp,
                    'temperature_used': temp_to_use
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
            
            # Atualizar campos de controle ML apenas se ML estiver ativado
            if duration > 0 and config.ml_control:
                now = timezone.now()
                config.ml_duration = duration
                config.ml_start_time = now
                config.force_on = True
                # Salvar explicitamente os campos que foram alterados
                config.save(update_fields=['ml_duration', 'ml_start_time', 'force_on'])
                
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

    @staticmethod
    def predict_temperature(current_temperature, current_hour):
        """
        Prediz a temperatura para a próxima hora usando modelo ML
        """
        try:
            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='temperature_prediction',
                is_active=True
            ).first()
            
            if not ml_model:
                # Fallback para regra simples
                next_hour = (current_hour + 1) % 24
                # Ajuste simples baseado no horário do dia
                if 6 <= next_hour <= 12:  # Manhã: temperatura tende a subir
                    predicted = current_temperature + 0.5
                elif 13 <= next_hour <= 18:  # Tarde: temperatura estável ou subindo
                    predicted = current_temperature + 0.2
                else:  # Noite/Madrugada: temperatura tende a cair
                    predicted = current_temperature - 0.3
                
                result = {
                    'predicted_temperature': round(predicted, 1),
                    'confidence': 0.5,
                    'method': 'rule_based'
                }
                return serialize_ml_output(result)
            
            # Usar modelo ML
            temp_model = TemperaturePredictionModel()
            loaded_model = ml_model.load_model()
            
            if loaded_model and isinstance(loaded_model, dict):
                temp_model.model = loaded_model['model']
                temp_model.scaler = loaded_model.get('scaler')  # Pode ser None
                
                prediction = temp_model.predict_next_hour(
                    current_temperature,
                    current_hour
                )
                
                result = {
                    'predicted_temperature': round(float(prediction['temperature']), 1),
                    'confidence': float(prediction.get('confidence', 0.7)),
                    'method': 'ml_model'
                }
                
                # Salvar predição
                MLPrediction.objects.create(
                    model=ml_model,
                    input_data={
                        'current_temperature': float(current_temperature),
                        'hour': int(current_hour)
                    },
                    prediction=result,
                    confidence=result['confidence']
                )
                
                return serialize_ml_output(result)
            
        except Exception as e:
            logger.error(f"Erro na predição de temperatura: {str(e)}")
        
        # Fallback em caso de erro
        return serialize_ml_output({
            'predicted_temperature': current_temperature,  # Mantém a mesma
            'confidence': 0,
            'method': 'error_fallback'
        })


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