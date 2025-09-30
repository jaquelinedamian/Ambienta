# backend/ml_models/views_dashboard.py

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import json
from .models import MLModel, MLPrediction, TrainingSession
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

@login_required
def ml_dashboard(request):
    """View para o dashboard de Machine Learning"""
    
    # Buscar modelos ativos
    active_models = MLModel.objects.filter(is_active=True)
    
    # Buscar últimas predições com seus modelos relacionados
    recent_predictions = MLPrediction.objects.select_related('model').order_by('-created_at')[:10]
    
    # Converter os dados de predição para um formato mais amigável
    for prediction in recent_predictions:
        if isinstance(prediction.prediction, str):
            try:
                prediction.prediction = json.loads(prediction.prediction)
            except json.JSONDecodeError:
                pass
    
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
    anomalies_today = anomalies.count()
    
    context = {
        'active_models': active_models,
        'recent_predictions': recent_predictions,
        'predictions_24h': predictions_24h,
        'anomaly_predictions': anomaly_predictions,
        'anomalies_today': anomalies_today,
        'total_predictions': total_predictions,
        'recent_training': recent_training
    }
    
    return render(request, 'dashboard/ml_dashboard.html', context)