# backend/ml_models/views_dashboard.py

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import json
from .models import MLModel, MLPrediction, TrainingSession
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, FloatField
from sensors.models import FanState, FanLog, Reading
from .mock_data import generate_mock_fan_data
from django.conf import settings

@login_required
def ml_dashboard(request):
    """View para o dashboard de Machine Learning"""
    
    print("\n=== INÍCIO DO PROCESSAMENTO DA VIEW ===")
    
    # Verificar se devemos usar dados simulados
    use_mock = getattr(settings, 'USE_MOCK_DATA', True)
    print(f"DEBUG - USE_MOCK_DATA setting: {use_mock}")
    print(f"DEBUG - URL acessada: {request.path}")

    # Buscar modelos ativos
    active_models = MLModel.objects.filter(is_active=True)
    
    # Buscar últimas predições com seus modelos relacionados
    recent_predictions = MLPrediction.objects.select_related('model').order_by('-created_at')[:10]
    
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
    if use_mock:
        # Usar dados simulados
        print("DEBUG - Gerando dados simulados")
        mock_data = generate_mock_fan_data()
        fan_state = mock_data['fan_state']
        fan_confidence = mock_data['fan_confidence']
        energy_savings = mock_data['energy_savings']
        fan_effectiveness = mock_data['fan_effectiveness']
        fan_optimization_history = mock_data['fan_optimization_history']
        print("DEBUG - Dados simulados gerados:", mock_data)
    else:
        # Usar dados reais
        fan_state = FanState.objects.last()
        fan_state = fan_state.state if fan_state else False
        
        # Última predição do ventilador
        last_fan_prediction = MLPrediction.objects.filter(
            model__model_type='fan_optimization'
        ).order_by('-created_at').first()

        fan_confidence = None
        if last_fan_prediction and isinstance(last_fan_prediction.prediction, dict):
            fan_confidence = int(last_fan_prediction.prediction.get('confidence', 0) * 100)

        # Calcular economia de energia
        last_month = timezone.now() - timedelta(days=30)
        fan_logs = FanLog.objects.filter(timestamp__gte=last_month)
        
        # Tempo médio ligado antes da otimização vs depois
        optimization_start = MLModel.objects.filter(
            model_type='fan_optimization',
            is_active=True
        ).first().created_at if MLModel.objects.filter(model_type='fan_optimization', is_active=True).exists() else None

        if optimization_start:
            before_optimization = fan_logs.filter(
                timestamp__lt=optimization_start
            ).aggregate(
                avg_duration=Avg('duration')
            )['avg_duration'] or 0

            after_optimization = fan_logs.filter(
                timestamp__gte=optimization_start
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
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).order_by('-timestamp')[:50]

        if recent_fan_logs:
            temperature_reductions = []
            for log in recent_fan_logs:
                # Pegar temperatura antes e depois
                temp_before = Reading.objects.filter(
                    timestamp__lte=log.timestamp
                ).order_by('-timestamp').first()
                
                temp_after = Reading.objects.filter(
                    timestamp__gte=log.timestamp + timedelta(minutes=log.duration)
                ).order_by('timestamp').first()

                if temp_before and temp_after:
                    reduction = temp_before.temperature - temp_after.temperature
                    if reduction > 0:  # Só considerar quando houve redução
                        temperature_reductions.append(reduction)

            if temperature_reductions:
                fan_effectiveness = (sum(temperature_reductions) / len(temperature_reductions)) * 100

        # Histórico de otimizações
        fan_optimization_history = []
        for log in recent_fan_logs[:10]:  # Últimas 10 otimizações
            temp_before = Reading.objects.filter(
                timestamp__lte=log.timestamp
            ).order_by('-timestamp').first()
            
            temp_after = Reading.objects.filter(
                timestamp__gte=log.timestamp + timedelta(minutes=log.duration)
            ).order_by('timestamp').first()

            reduction = 0
            if temp_before and temp_after:
                reduction = temp_before.temperature - temp_after.temperature

            fan_optimization_history.append({
                'timestamp': log.timestamp,
                'temperature': temp_before.temperature if temp_before else None,
                'action': log.state,
                'duration': log.duration,
                'temperature_reduction': reduction
            })
    anomalies_today = anomalies.count()
    
    print("\n=== INICIALIZANDO DADOS DO VENTILADOR ===")
    # Inicializar dados do ventilador
    if use_mock:
        print("DEBUG - Gerando dados simulados do ventilador")
        try:
            mock_data = generate_mock_fan_data()
            print("DEBUG - Dados gerados com sucesso")
            print("DEBUG - fan_state:", mock_data.get('fan_state'))
            print("DEBUG - fan_confidence:", mock_data.get('fan_confidence'))
            print("DEBUG - energy_savings:", mock_data.get('energy_savings'))
            print("DEBUG - fan_effectiveness:", mock_data.get('fan_effectiveness'))
            print("DEBUG - history items:", len(mock_data.get('fan_optimization_history', [])))
            
            fan_data = {
                'fan_state': mock_data['fan_state'],
                'fan_confidence': mock_data['fan_confidence'],
                'energy_savings': mock_data['energy_savings'],
                'fan_effectiveness': mock_data['fan_effectiveness'],
                'fan_optimization_history': mock_data['fan_optimization_history']
            }
        except Exception as e:
            print("ERRO - Falha ao gerar dados simulados:", str(e))
            fan_data = {
                'fan_state': False,
                'fan_confidence': None,
                'energy_savings': 0,
                'fan_effectiveness': 0,
                'fan_optimization_history': []
            }
    else:
        fan_data = {
            'fan_state': fan_state,
            'fan_confidence': fan_confidence,
            'energy_savings': round(energy_savings, 1),
            'fan_effectiveness': round(fan_effectiveness, 1),
            'fan_optimization_history': fan_optimization_history
        }

    # Montar contexto completo
    context = {
        # Dados base
        'active_models': active_models,
        'recent_predictions': recent_predictions,
        'predictions_24h': predictions_24h,
        'anomaly_predictions': anomaly_predictions,
        'anomalies_today': anomalies_today,
        'total_predictions': total_predictions,
        'recent_training': recent_training,
        
        # Dados do ventilador
        **fan_data
    }

    print("DEBUG - Contexto Final:", {
        'fan_state': context['fan_state'],
        'fan_confidence': context['fan_confidence'],
        'energy_savings': context['energy_savings'],
        'fan_effectiveness': context['fan_effectiveness'],
        'history_count': len(context['fan_optimization_history'])
    })
    
    return render(request, 'dashboard/ml_dashboard.html', context)