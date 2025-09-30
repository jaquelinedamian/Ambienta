# dashboard/ml_views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json

from ml_models.models import MLModel, MLPrediction, TrainingSession
from sensors.models import Reading
from ml_models.ml_algorithms import (
    TemperaturePredictionModel,
    FanOptimizationModel,
    AnomalyDetectionModel
)


@login_required
def ml_dashboard_view(request):
    """
    View específica para dashboard de Machine Learning
    """
    active_models = MLModel.objects.filter(is_active=True)
    
    # Estatísticas gerais
    total_predictions = MLPrediction.objects.count()
    predictions_24h = MLPrediction.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Últimas sessões de treinamento
    recent_training = TrainingSession.objects.filter(
        status='completed'
    ).order_by('-completed_at')[:5]
    
    # Buscar todas as predições recentes
    recent_predictions = MLPrediction.objects.select_related('model').filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-created_at')[:10]

    # Processar predições para garantir que estão no formato correto
    for prediction in recent_predictions:
        if isinstance(prediction.prediction, str):
            try:
                prediction.prediction = json.loads(prediction.prediction)
            except json.JSONDecodeError:
                pass

    # Anomalias detectadas hoje
    today = timezone.now().date()
    anomaly_predictions = MLPrediction.objects.filter(
        model__model_type='anomaly_detection',
        created_at__date=today
    ).select_related('model').order_by('-created_at')

    # Separar anomalias confirmadas
    anomalies = anomaly_predictions.filter(prediction__is_anomaly=True)
    anomalies_today = anomalies.count()
    
    # Histórico de treinamento
    recent_training = TrainingSession.objects.all().order_by('-started_at')[:5]
    
    context = {
        'active_models': active_models,
        'total_predictions': total_predictions,
        'predictions_24h': predictions_24h,
        'recent_predictions': recent_predictions,
        'anomaly_predictions': anomaly_predictions,
        'anomalies_today': anomalies_today,
        'recent_training': recent_training,
        'models_count': {
            'temperature': active_models.filter(model_type='temperature_prediction').count(),
            'anomaly': active_models.filter(model_type='anomaly_detection').count(),
            'fan': active_models.filter(model_type='fan_optimization').count(),
        }
    }
    
    return render(request, 'dashboard/ml_dashboard.html', context)


@login_required
def get_ml_predictions_api(request):
    """
    API para obter predições via AJAX
    """
    prediction_type = request.GET.get('type', 'temperature')
    hours_back = int(request.GET.get('hours', 24))
    
    predictions = MLPrediction.objects.filter(
        model__model_type=f"{prediction_type}_prediction",
        created_at__gte=timezone.now() - timedelta(hours=hours_back)
    ).order_by('-created_at')
    
    data = []
    for pred in predictions:
        data.append({
            'id': pred.id,
            'timestamp': pred.created_at.isoformat(),
            'input_data': pred.input_data,
            'prediction': pred.prediction,
            'confidence': pred.confidence,
            'model_name': pred.model.name
        })
    
    return JsonResponse({'predictions': data})


@login_required
@login_required
def ml_stats_api(request):
    """
    API para estatísticas em tempo real
    """
    # Estatísticas dos últimos 7 dias
    week_ago = timezone.now() - timedelta(days=7)
    
    stats = {
        'models': {
            'active': MLModel.objects.filter(is_active=True).count(),
            'total': MLModel.objects.count(),
        },
        'predictions': {
            'today': MLPrediction.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=1)
            ).count(),
            'week': MLPrediction.objects.filter(
                created_at__gte=week_ago
            ).count(),
            'total': MLPrediction.objects.count(),
        },
        'anomalies': {
            'today': MLPrediction.objects.filter(
                model__model_type='anomaly_detection',
                created_at__gte=timezone.now() - timedelta(days=1),
                prediction__is_anomaly=True
            ).count(),
            'week': MLPrediction.objects.filter(
                model__model_type='anomaly_detection',
                created_at__gte=week_ago,
                prediction__is_anomaly=True
            ).count(),
        },
        'training': {
            'last_session': None
        }
    }
    
    # Última sessão de treinamento
    last_training = TrainingSession.objects.filter(
        status='completed'
    ).order_by('-completed_at').first()
    
    if last_training:
        stats['training']['last_session'] = {
            'date': last_training.completed_at.isoformat(),
            'duration': str(last_training.duration),
            'samples': last_training.training_samples
        }
    
    return JsonResponse(stats)


@login_required
def trigger_ml_training(request):
    """
    Endpoint para disparar treinamento via interface
    """
    if request.method == 'POST':
        try:
            from ml_models.ml_algorithms import train_all_models
            results = train_all_models()
            
            return JsonResponse({
                'success': True,
                'message': 'Treinamento concluído',
                'results': results
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)