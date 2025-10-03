from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import MLModel, MLPrediction
from .serializers import MLModelSerializer, MLPredictionSerializer
from sensors.models import FanState, FanLog, Reading
from django.db.models import Max
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def dashboard_data(request):
    """API endpoint para buscar dados atualizados do dashboard"""
    try:
        # Buscar modelos ativos com últimas predições
        active_models = MLModel.objects.filter(is_active=True).prefetch_related(
            'predictions'
        ).annotate(
            last_prediction_time=Max('predictions__created_at')
        ).order_by('-last_prediction_time')
        
        # Últimas predições
        recent_predictions = MLPrediction.objects.select_related('model').order_by('-created_at')[:10]
        
        # Anomalias recentes (24h)
        last_24h = timezone.now() - timedelta(hours=24)
        anomaly_predictions = MLPrediction.objects.filter(
            model__model_type='anomaly_detection',
            created_at__gte=last_24h
        ).select_related('model').order_by('-created_at')
        
        # Estado do ventilador
        fan_state = FanState.objects.last()
        fan_state_value = fan_state.state if fan_state else False
        
        # Preparar resposta
        return Response({
            'active_models': MLModelSerializer(active_models, many=True).data,
            'recent_predictions': MLPredictionSerializer(recent_predictions, many=True).data,
            'anomaly_predictions': MLPredictionSerializer(anomaly_predictions, many=True).data,
            'fan_state': fan_state_value,
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados do dashboard: {e}")
        return Response({'error': str(e)}, status=500)