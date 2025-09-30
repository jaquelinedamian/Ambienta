# dashboard/views.py

from django.shortcuts import render
from django.utils import timezone
from sensors.models import Reading, FanState, FanLog
from ml_models.models import MLModel, MLPrediction
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.db.models import Sum, Count, Avg
from django.core.paginator import Paginator
from datetime import timedelta
from django.utils import timezone
from datetime import timedelta, datetime
import requests
from django.contrib.auth.decorators import login_required


# @login_required  # Removido temporariamente para teste
def dashboard_view(request):
    readings_list = Reading.objects.all().order_by('-timestamp')
    paginator_readings = Paginator(readings_list, 10)
    page_number_readings = request.GET.get('page')
    page_obj_readings = paginator_readings.get_page(page_number_readings)

    fan_logs_list = FanLog.objects.all().order_by('-start_time')
    paginator_fan = Paginator(fan_logs_list, 10)
    page_number_fan = request.GET.get('page')
    page_obj_fan = paginator_fan.get_page(page_number_fan)

    # Buscar o estado mais recente do ventilador
    fan_state = FanState.objects.order_by('-timestamp').first()
    
    # Se não houver nenhum estado, criar um estado inicial
    if not fan_state:
        fan_state = FanState.objects.create(
            state=False,
            timestamp=timezone.now()
        )

    # Dados de Machine Learning
    active_models = MLModel.objects.filter(is_active=True)
    
    # Últimas predições
    recent_predictions = MLPrediction.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-created_at')[:5]
    
    # Estatísticas de anomalias hoje
    today = timezone.now().date()
    anomalies_today = MLPrediction.objects.filter(
        model__model_type='anomaly_detection',
        created_at__date=today,
        prediction__is_anomaly=True
    ).count()
    
    # Última anomalia
    latest_anomaly = MLPrediction.objects.filter(
        model__model_type='anomaly_detection',
        prediction__is_anomaly=True
    ).order_by('-created_at').first()
    
    # Última predição de temperatura
    latest_temp_prediction = MLPrediction.objects.filter(
        model__model_type='temperature_prediction'
    ).order_by('-created_at').first()
    
    # Recomendação do ventilador
    latest_fan_prediction = MLPrediction.objects.filter(
        model__model_type='fan_optimization'
    ).order_by('-created_at').first()
    
    # Score de anomalia mais recente
    latest_anomaly_score = MLPrediction.objects.filter(
        model__model_type='anomaly_detection'
    ).order_by('-created_at').first()
    
    # Estrutura ml_status que o template espera
    ml_status = {
        'active_models': active_models.count(),
        'latest_prediction': recent_predictions.first() if recent_predictions.exists() else None,
        'anomalies_today': anomalies_today,
        'latest_anomaly': latest_anomaly,
        'temperature_prediction': latest_temp_prediction,
        'fan_recommendation': {
            'should_be_on': latest_fan_prediction.prediction.get('should_be_on', False) if latest_fan_prediction else False,
            'energy_savings': latest_fan_prediction.prediction.get('energy_savings', 0) if latest_fan_prediction else 0
        } if latest_fan_prediction else None,
        'anomaly_score': latest_anomaly_score.prediction.get('anomaly_score', 0) if latest_anomaly_score else None
    }
    
    # Leitura mais recente
    latest_reading = readings_list.first()

    # Obter data atual para as queries
    now = timezone.now()

    # Preparar dados JSON para os gráficos
    # Formatar temperaturas com uma casa decimal
    readings_data = list(readings_list.values())
    for reading in readings_data:
        reading['temperature'] = round(float(reading['temperature']), 1)
    readings_json = json.dumps(readings_data, cls=DjangoJSONEncoder)
    
    # Valores fixos para demonstração
    fan_hours_today = 9.0  # 9 horas para hoje
    fan_hours_week = 64.0  # 64 horas para a semana
    fan_hours_month = 256.0  # 256 horas para o mês
    
    # Estatísticas de leituras
    readings_today = readings_list.filter(timestamp__date=now.date()).count()
    readings_week = readings_list.filter(timestamp__gte=now - timedelta(days=7)).count()
    readings_month = readings_list.filter(timestamp__gte=now - timedelta(days=30)).count()
    avg_temperature = readings_list.aggregate(Avg('temperature'))['temperature__avg']
    
    # Temperatura atual (mais recente)
    current_temperature = latest_reading.temperature if latest_reading else None

    context = {
        'fan_state': fan_state,
        'page_obj_readings': page_obj_readings,
        'page_obj_fan': page_obj_fan,
        'latest_reading': latest_reading,
        'ml_status': ml_status,
        'readings_json': readings_json,
        'fan_hours_today': fan_hours_today,
        'fan_hours_week': fan_hours_week,
        'fan_hours_month': fan_hours_month,
        'readings_today': readings_today,
        'readings_week': readings_week,
        'readings_month': readings_month,
        'avg_temperature': avg_temperature,
        'current_temperature': current_temperature,
    }

    return render(request, 'dashboard/index.html', context)