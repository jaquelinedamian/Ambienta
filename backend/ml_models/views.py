# backend/ml_models/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import json

from .models import MLModel, MLPrediction, TrainingSession
from .ml_algorithms import (
    TemperaturePredictionModel, 
    FanOptimizationModel, 
    AnomalyDetectionModel,
    train_all_models
)
from sensors.models import Reading


class TrainModelsAPIView(APIView):
    """
    Endpoint para treinar todos os modelos de ML
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        training_session = None
        try:
            # Iniciar sessão de treinamento
            training_session = TrainingSession.objects.create(
                model=None,  # Será atualizado depois
                data_start_date=timezone.now() - timedelta(days=30),
                data_end_date=timezone.now(),
                status='running',
                training_samples=0
            )
            
            # Validar dados disponíveis
            from sensors.models import Reading, FanState
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            readings_count = Reading.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).count()
            
            fan_states_count = FanState.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).count()
            
            training_session.training_metrics = {
                'data_validation': {
                    'readings_available': readings_count,
                    'fan_states_available': fan_states_count,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            training_session.save()
            
            if readings_count < 10:
                raise ValueError(f"Dados insuficientes para treinamento. Encontrados apenas {readings_count} registros nos últimos 30 dias.")
            
            # Treinar modelos
            results = train_all_models()
            
            # Atualizar sessão
            training_session.status = 'completed'
            training_session.completed_at = timezone.now()
            training_session.training_metrics.update(results)
            training_session.save()
            
            return Response({
                'message': 'Modelos treinados com sucesso',
                'error': False,
                'details': {
                    'results': results,
                    'data_summary': training_session.training_metrics['data_validation'],
                    'training_session_id': training_session.id
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            error_message = f"Dados insuficientes para treinamento: {str(e)}"
            if training_session:
                training_session.status = 'failed'
                training_session.error_message = error_message
                training_session.save()
            
            return Response({
                'message': error_message,
                'error': True,
                'details': {
                    'type': 'insufficient_data',
                    'description': str(e),
                    'data_summary': training_session.training_metrics.get('data_validation') if training_session else None
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_message = f"Erro durante o treinamento: {str(e)}"
            
            if training_session:
                training_session.status = 'failed'
                training_session.error_message = f"{error_message}\n\nStack trace:\n{error_details}"
                training_session.save()
            
            return Response({
                'message': error_message,
                'error': True,
                'details': {
                    'type': 'training_error',
                    'description': str(e),
                    'stack_trace': error_details if settings.DEBUG else None,
                    'data_summary': training_session.training_metrics.get('data_validation') if training_session else None
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TemperaturePredictionAPIView(APIView):
    """
    Endpoint para predição de temperatura
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            hours_ahead = int(request.GET.get('hours_ahead', 1))
            if hours_ahead > 24:
                hours_ahead = 24
            
            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='temperature_prediction',
                is_active=True
            ).first()
            
            if not ml_model:
                return Response({
                    'error': 'Nenhum modelo de predição de temperatura ativo'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Carregar e usar modelo
            temp_model = TemperaturePredictionModel()
            temp_model.model = ml_model.load_model()
            
            if temp_model.model is None:
                return Response({
                    'error': 'Erro ao carregar modelo'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Fazer predição
            predictions = temp_model.predict(hours_ahead)
            
            # Salvar predição
            prediction_record = MLPrediction.objects.create(
                model=ml_model,
                input_data={'hours_ahead': hours_ahead},
                prediction={'temperatures': predictions}
            )
            
            # Preparar timestamps para cada predição
            now = timezone.now()
            prediction_data = []
            for i, temp in enumerate(predictions):
                prediction_time = now + timedelta(hours=i+1)
                prediction_data.append({
                    'hour': prediction_time.strftime('%Y-%m-%d %H:%M'),
                    'predicted_temperature': round(temp, 2)
                })
            
            return Response({
                'predictions': prediction_data,
                'model_info': {
                    'name': ml_model.name,
                    'version': ml_model.version,
                    'accuracy': ml_model.r2_score
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro na predição',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FanOptimizationAPIView(APIView):
    """
    Endpoint para otimização do ventilador
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            current_temp = float(request.data.get('current_temperature'))
            current_hour = request.data.get('current_hour', datetime.now().hour)
            current_day = datetime.now().weekday()
            
            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='fan_optimization',
                is_active=True
            ).first()
            
            if not ml_model:
                # Fallback para regra simples
                if current_temp > 25.0:
                    duration = max(5, (current_temp - 25.0) * 10)
                    return Response({
                        'recommended_duration_minutes': int(duration),
                        'reason': 'Regra simples (modelo não disponível)',
                        'should_turn_on': True,
                        'confidence': None
                    })
                else:
                    return Response({
                        'recommended_duration_minutes': 0,
                        'reason': 'Temperatura abaixo do limiar',
                        'should_turn_on': False,
                        'confidence': None
                    })
            
            # Usar modelo ML
            fan_model = FanOptimizationModel()
            fan_model.model = ml_model.load_model()
            
            # Fazer predição
            should_turn_on, confidence = fan_model.predict(current_temp, current_hour, current_day)
            
            # Calcular duração baseada na temperatura e confiança
            if should_turn_on:
                base_duration = max(5, (current_temp - 25.0) * 10)
                optimal_duration = int(base_duration * confidence)
            else:
                optimal_duration = 0
            
            # Salvar predição
            MLPrediction.objects.create(
                model=ml_model,
                input_data={
                    'current_temperature': current_temp,
                    'current_hour': current_hour,
                    'current_day': current_day
                },
                prediction={
                    'should_turn_on': bool(should_turn_on),
                    'confidence': float(confidence),
                    'optimal_duration_minutes': optimal_duration
                }
            )
            
            return Response({
                'should_turn_on': bool(should_turn_on),
                'confidence': float(confidence),
                'recommended_duration_minutes': optimal_duration,
                'reason': f'Otimização ML (modelo {ml_model.name})',
                'current_temperature': current_temp
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro na otimização',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnomalyDetectionAPIView(APIView):
    """
    Endpoint para detecção de anomalias
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            temperature = float(request.data.get('temperature'))
            hour = request.data.get('hour', datetime.now().hour)
            
            # Buscar modelo ativo
            ml_model = MLModel.objects.filter(
                model_type='anomaly_detection',
                is_active=True
            ).first()
            
            if not ml_model:
                # Fallback para regra simples
                is_anomaly = temperature < 0 or temperature > 50
                return Response({
                    'is_anomaly': is_anomaly,
                    'confidence': 0.5,
                    'reason': 'Regra simples (modelo não disponível)',
                    'anomaly_score': 0
                })
            
            # Usar modelo ML
            anomaly_model = AnomalyDetectionModel()
            loaded_model = ml_model.load_model()
            if loaded_model:
                anomaly_model.model = loaded_model['model']
                anomaly_model.scaler = loaded_model['scaler']
                anomaly_model.is_fitted = True
                
                result = anomaly_model.detect_anomaly(temperature, hour)
                
                # Salvar predição
                MLPrediction.objects.create(
                    model=ml_model,
                    input_data={
                        'temperature': temperature,
                        'hour': hour
                    },
                    prediction=result,
                    confidence=result['confidence']
                )
                
                return Response({
                    'is_anomaly': result['is_anomaly'],
                    'confidence': result['confidence'],
                    'anomaly_score': result['anomaly_score'],
                    'reason': f'Análise ML (modelo {ml_model.name})'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'error': 'Erro ao carregar modelo de anomalias'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'error': 'Erro na detecção de anomalias',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelStatusAPIView(APIView):
    """
    Endpoint para verificar status dos modelos
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        models = MLModel.objects.filter(is_active=True)
        
        model_data = []
        for model in models:
            last_prediction = model.predictions.first()
            
            model_info = {
                'id': model.id,
                'name': model.name,
                'type': model.model_type,
                'version': model.version,
                'accuracy': model.accuracy,
                'mse': model.mse,
                'mae': model.mae,
                'r2_score': model.r2_score,
                'last_trained': model.last_trained.isoformat() if model.last_trained else None,
                'last_prediction': last_prediction.created_at.isoformat() if last_prediction else None,
                'total_predictions': model.predictions.count()
            }
            model_data.append(model_info)
        
        # Estatísticas gerais
        recent_readings = Reading.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        return Response({
            'active_models': model_data,
            'total_active_models': len(model_data),
            'recent_readings_24h': recent_readings,
            'system_status': 'operational' if model_data else 'no_models'
        }, status=status.HTTP_200_OK)


class ModelMetricsAPIView(APIView):
    """
    Endpoint para métricas detalhadas dos modelos
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, model_id):
        try:
            model = MLModel.objects.get(id=model_id)
            
            # Predições recentes
            recent_predictions = model.predictions.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).order_by('-created_at')[:10]
            
            predictions_data = []
            for pred in recent_predictions:
                predictions_data.append({
                    'id': pred.id,
                    'input_data': pred.input_data,
                    'prediction': pred.prediction,
                    'confidence': pred.confidence,
                    'created_at': pred.created_at.isoformat(),
                    'is_verified': pred.is_verified
                })
            
            # Sessões de treinamento
            training_sessions = model.training_sessions.order_by('-started_at')[:5]
            sessions_data = []
            for session in training_sessions:
                sessions_data.append({
                    'id': session.id,
                    'status': session.status,
                    'started_at': session.started_at.isoformat(),
                    'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                    'duration': str(session.duration) if session.completed_at else None,
                    'training_samples': session.training_samples,
                    'metrics': session.training_metrics
                })
            
            return Response({
                'model': {
                    'id': model.id,
                    'name': model.name,
                    'type': model.model_type,
                    'description': model.description,
                    'version': model.version,
                    'is_active': model.is_active,
                    'hyperparameters': model.hyperparameters,
                    'metrics': {
                        'accuracy': model.accuracy,
                        'mse': model.mse,
                        'mae': model.mae,
                        'r2_score': model.r2_score
                    }
                },
                'recent_predictions': predictions_data,
                'training_history': sessions_data
            }, status=status.HTTP_200_OK)
            
        except MLModel.DoesNotExist:
            return Response({
                'error': 'Modelo não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Erro ao buscar métricas',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
