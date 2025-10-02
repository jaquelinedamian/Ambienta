# backend/ml_models/views_dashboard.py
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import json
from .models import MLModel, MLPrediction, TrainingSession
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, FloatField
from sensors.models import FanState, FanLog, Reading
from django.conf import settings
from functools import wraps
from django.http import HttpResponse
import logging
import traceback

logger = logging.getLogger(__name__)

def handle_dashboard_errors(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Erro no dashboard ML: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Contexto mínimo para o template
            error_context = {
                'error_message': 'Desculpe, ocorreu um erro ao carregar o dashboard.',
                'active_models': [],
                'recent_predictions': [],
                'predictions_24h': 0,
                'anomaly_predictions': [],
                'anomalies_today': 0,
                'total_predictions': 0,
                'recent_training': [],
                'fan_state': False,
                'fan_confidence': None,
                'energy_savings': 0,
                'fan_effectiveness': 0,
                'fan_optimization_history': []
            }
            
            return render(request, 'dashboard/ml_dashboard.html', error_context)
    return wrapper

@login_required
@handle_dashboard_errors
def ml_dashboard(request):
    """View para o dashboard de Machine Learning"""
    
    print("\n=== INÍCIO DO PROCESSAMENTO DA VIEW ===")
    print(f"DEBUG - URL acessada: {request.path}")

    try:
        # Buscar modelos ativos
        active_models = MLModel.objects.filter(is_active=True)
        if not active_models.exists():
            logger.warning("Nenhum modelo ML ativo encontrado")
    except Exception as e:
        logger.error(f"Erro ao buscar modelos ativos: {e}")
        active_models = MLModel.objects.none()
    
    try:
        # Buscar últimas predições com seus modelos relacionados
        recent_predictions = MLPrediction.objects.select_related('model').order_by('-created_at')[:10]
    except Exception as e:
        logger.error(f"Erro ao buscar predições recentes: {e}")
        recent_predictions = MLPrediction.objects.none()
    
    # Converter e formatar os dados de predição para um formato mais amigável
    for prediction in recent_predictions:
        # Converter de string para dict se necessário
        if isinstance(prediction.prediction, str):
            try:
                prediction.prediction = json.loads(prediction.prediction)
            except json.JSONDecodeError:
                continue
        
        # Garantir que prediction.prediction é um dicionário
        if not isinstance(prediction.prediction, dict):
            prediction.prediction = {}
        
        # Formatar dados específicos para cada tipo de modelo
        if prediction.model.model_type == 'temperature_prediction':
            # Garantir que temperatures é uma lista
            if 'temperatures' not in prediction.prediction:
                prediction.prediction = {
                    'temperatures': [prediction.prediction.get('predicted_temp', 0.0)]
                }
            elif isinstance(prediction.prediction['temperatures'], (int, float)):
                prediction.prediction['temperatures'] = [prediction.prediction['temperatures']]
        
        elif prediction.model.model_type == 'fan_optimization':
            # Garantir campos necessários para otimização do ventilador
            default_fan_data = {
                'should_turn_on': prediction.prediction.get('should_turn_on', False),
                'recommended_duration_minutes': prediction.prediction.get('recommended_duration_minutes', 0),
                'confidence': prediction.prediction.get('confidence', 0.0)
            }
            prediction.prediction.update(default_fan_data)
        
        elif prediction.model.model_type == 'anomaly_detection':
            # Garantir campos necessários para detecção de anomalias
            default_anomaly_data = {
                'is_anomaly': prediction.prediction.get('is_anomaly', False),
                'anomaly_score': prediction.prediction.get('anomaly_score', 0.0)
            }
            prediction.prediction.update(default_anomaly_data)
    
    # Predições nas últimas 24h por tipo de modelo
    last_24h = timezone.now() - timedelta(hours=24)
    recent_predictions_24h = MLPrediction.objects.filter(
        created_at__gte=last_24h
    ).select_related('model').order_by('-created_at')
    
    # Anomalias detectadas hoje
    today = timezone.now().date()
    anomaly_predictions = MLPrediction.objects.filter(
        model__model_type='anomaly_detection',
        created_at__date=today
    ).select_related('model').order_by('-created_at')

    # Separar anomalias confirmadas
    anomalies = anomaly_predictions.filter(prediction__is_anomaly=True)
    
    # Histórico de treinamento recente
    recent_training = TrainingSession.objects.all().order_by('-started_at')[:5]
    
    # Métricas gerais
    total_predictions = MLPrediction.objects.count()
    predictions_24h = recent_predictions_24h.count()

    # Dados de otimização do ventilador
    try:
        # Buscar estado do ventilador de forma segura
        fan_state = FanState.objects.last()
        fan_state = fan_state.state if fan_state else False
    except Exception as e:
        print(f"Erro ao buscar estado do ventilador: {e}")
        fan_state = False
    
    try:
        # Última predição do ventilador
        last_fan_prediction = MLPrediction.objects.filter(
            model__model_type='fan_optimization'
        ).order_by('-created_at').first()

        fan_confidence = None
        if last_fan_prediction and isinstance(last_fan_prediction.prediction, dict):
            fan_confidence = int(last_fan_prediction.prediction.get('confidence', 0) * 100)
    except Exception as e:
        print(f"Erro ao buscar predição do ventilador: {e}")
        fan_confidence = None

    try:
        # Calcular economia de energia
        last_month = timezone.now() - timedelta(days=30)
        fan_logs = FanLog.objects.filter(start_time__gte=last_month)
        
        # Tempo médio ligado antes da otimização vs depois
        optimization_model = MLModel.objects.filter(
            model_type='fan_optimization',
            is_active=True
        ).first()
        
        optimization_start = optimization_model.created_at if optimization_model else None
    except Exception as e:
        print(f"Erro ao calcular economia de energia: {e}")
        fan_logs = []
        optimization_start = None

    if optimization_start:
        before_optimization = fan_logs.filter(
            start_time__lt=optimization_start
        ).aggregate(
            avg_duration=Avg('duration')
        )['avg_duration'] or 0

        after_optimization = fan_logs.filter(
            start_time__gte=optimization_start
        ).aggregate(
            avg_duration=Avg('duration')
        )['avg_duration'] or 0

        if before_optimization > 0:
            energy_savings = ((before_optimization - after_optimization) / before_optimization) * 100
        else:
            energy_savings = 0
    else:
        energy_savings = 0

    # Calcular efetividade (redução média de temperatura)
    fan_effectiveness = 0
    recent_fan_logs = FanLog.objects.filter(
        start_time__gte=timezone.now() - timedelta(days=7)
    ).order_by('-start_time')[:50]

    if recent_fan_logs:
        temperature_reductions = []
        for log in recent_fan_logs:
            # Pegar temperatura antes e depois
            try:
                # Processa apenas logs com timestamps válidos
                if log.start_time:
                    temp_before = Reading.objects.filter(
                        timestamp__lte=log.start_time
                    ).order_by('-timestamp').first()
                else:
                    print(f"Log {log.id} não tem start_time definido")
                    continue

                if log.end_time:
                    temp_after = Reading.objects.filter(
                        timestamp__gte=log.end_time
                    ).order_by('timestamp').first()
                else:
                    print(f"Log {log.id} não tem end_time definido")
                    continue

            except Exception as e:
                print(f"Erro ao buscar leituras para log {log.id}: {e}")
                continue

            if temp_before and temp_after:
                reduction = temp_before.temperature - temp_after.temperature
                if reduction > 0:  # Só considerar quando houve redução
                    temperature_reductions.append(reduction)

        if temperature_reductions:
            fan_effectiveness = (sum(temperature_reductions) / len(temperature_reductions)) * 100

    # Histórico de otimizações
    fan_optimization_history = []
    logger.info(f"Total de logs recentes: {recent_fan_logs.count()}")
    
    for idx, log in enumerate(recent_fan_logs[:10], 1):
        try:
            logger.info(f"Processando log {idx}/10 (ID: {log.id})")
            if not log.start_time:
                logger.warning(f"Log {log.id} sem start_time")
                continue
                
            # Temperaturas antes e depois do ventilador ligado
            temp_before = Reading.objects.filter(
                timestamp__lte=log.start_time
            ).order_by('-timestamp').first()
            
            temp_after = None
            if log.end_time:
                temp_after = Reading.objects.filter(
                    timestamp__gte=log.end_time
                ).order_by('timestamp').first()
            elif log.duration:
                # Se não tem end_time mas tem duration, calcula o end_time
                temp_after = Reading.objects.filter(
                    timestamp__gte=log.start_time + log.duration
                ).order_by('timestamp').first()

            logger.debug(f"Log {log.id}: Temp antes: {temp_before.temperature if temp_before else 'N/A'}, "
                        f"Temp depois: {temp_after.temperature if temp_after else 'N/A'}")

            # Calcular redução de temperatura
            reduction = 0
            if temp_before and temp_after and temp_before.temperature > temp_after.temperature:
                reduction = temp_before.temperature - temp_after.temperature
                logger.debug(
                    f"Log {log.id}: Redução de temperatura: {reduction:.1f}°C "
                    f"(de {temp_before.temperature:.1f}°C para {temp_after.temperature:.1f}°C)"
                )

            # Criar entrada para o histórico
            entry = {
                'timestamp': log.start_time,
                'temperature': temp_before.temperature if temp_before else None,
                'duration': log.duration.total_seconds() / 60 if log.duration else None,
                'temperature_reduction': round(reduction, 1),
                'end_time': log.end_time
            }
            fan_optimization_history.append(entry)
            
        except Exception as e:
            logger.error(f"Erro ao processar log {log.id}: {e}")
            continue
    anomalies_today = anomalies.count()
    
    print("\n=== INICIALIZANDO DADOS DO VENTILADOR ===")
    # Valores padrão para segurança
    default_fan_data = {
        'fan_state': False,
        'fan_confidence': None,
        'energy_savings': 0,
        'fan_effectiveness': 0,
        'fan_optimization_history': []
    }
    
    try:
        # Inicializar dados do ventilador com valores reais
        fan_data = {
            'fan_state': fan_state,
            'fan_confidence': fan_confidence,
            'energy_savings': round(float(energy_savings), 1) if energy_savings is not None else 0,
            'fan_effectiveness': round(float(fan_effectiveness), 1) if fan_effectiveness is not None else 0,
            'fan_optimization_history': fan_optimization_history if fan_optimization_history else []
        }
        
        # Validar dados antes de usar
        if not isinstance(fan_data['energy_savings'], (int, float)):
            logger.warning(f"Valor inválido para energy_savings: {fan_data['energy_savings']}")
            fan_data['energy_savings'] = 0
            
        if not isinstance(fan_data['fan_effectiveness'], (int, float)):
            logger.warning(f"Valor inválido para fan_effectiveness: {fan_data['fan_effectiveness']}")
            fan_data['fan_effectiveness'] = 0
            
    except Exception as e:
        logger.error(f"Erro ao processar dados do ventilador: {e}")
        fan_data = default_fan_data.copy()
    
    # Garantir que todos os campos necessários existem
    for key in default_fan_data:
        if key not in fan_data:
            fan_data[key] = default_fan_data[key]
    
    # Montar contexto completo
    context = {
        # Dados base
        'active_models': active_models or [],
        'recent_predictions': recent_predictions or [],
        'predictions_24h': predictions_24h or 0,
        'anomaly_predictions': anomaly_predictions or [],
        'anomalies_today': anomalies_today or 0,
        'total_predictions': total_predictions or 0,
        'recent_training': recent_training or [],
        
        # Dados do ventilador
        **fan_data
    }

    # Log detalhado do contexto final
    logger.info("=== RESUMO DO DASHBOARD ===")
    logger.info(f"Modelos ativos: {active_models.count() if active_models else 0}")
    logger.info(f"Predições recentes: {len(recent_predictions)}")
    logger.info(f"Predições 24h: {predictions_24h}")
    logger.info(f"Anomalias hoje: {anomalies_today}")
    logger.info(f"Estado do ventilador: {'LIGADO' if fan_state else 'DESLIGADO'}")
    logger.info(f"Confiança ML: {fan_confidence}%")
    logger.info(f"Economia de energia: {fan_data['energy_savings']:.1f}%")
    logger.info(f"Efetividade: {fan_data['fan_effectiveness']:.1f}%")
    logger.info(f"Histórico de otimizações: {len(fan_optimization_history)} registros")
    logger.info("==========================")
    
    return render(request, 'dashboard/ml_dashboard.html', context)