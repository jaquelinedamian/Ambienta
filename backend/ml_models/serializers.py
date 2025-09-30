# backend/ml_models/serializers.py

from rest_framework import serializers
from .models import MLModel, MLPrediction, TrainingSession, ModelPerformanceMetric


class MLModelSerializer(serializers.ModelSerializer):
    """
    Serializer para modelos de ML
    """
    class Meta:
        model = MLModel
        fields = [
            'id', 'name', 'model_type', 'description', 'version', 'is_active',
            'accuracy', 'mse', 'mae', 'r2_score', 'created_at', 'updated_at',
            'last_trained', 'hyperparameters'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MLPredictionSerializer(serializers.ModelSerializer):
    """
    Serializer para predições
    """
    model_name = serializers.CharField(source='model.name', read_only=True)
    model_type = serializers.CharField(source='model.model_type', read_only=True)
    
    class Meta:
        model = MLPrediction
        fields = [
            'id', 'model', 'model_name', 'model_type', 'input_data', 
            'prediction', 'confidence', 'created_at', 'actual_value', 'is_verified'
        ]
        read_only_fields = ['id', 'created_at', 'model_name', 'model_type']


class TrainingSessionSerializer(serializers.ModelSerializer):
    """
    Serializer para sessões de treinamento
    """
    model_name = serializers.CharField(source='model.name', read_only=True)
    duration_str = serializers.SerializerMethodField()
    
    class Meta:
        model = TrainingSession
        fields = [
            'id', 'model', 'model_name', 'data_start_date', 'data_end_date',
            'training_samples', 'validation_samples', 'training_metrics',
            'validation_metrics', 'status', 'started_at', 'completed_at',
            'duration_str', 'error_message'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'model_name', 'duration_str']
    
    def get_duration_str(self, obj):
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return None


class ModelPerformanceMetricSerializer(serializers.ModelSerializer):
    """
    Serializer para métricas de performance
    """
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelPerformanceMetric
        fields = [
            'id', 'model', 'model_name', 'metric_name', 'metric_value',
            'evaluation_start', 'evaluation_end', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'model_name']


class TemperaturePredictionRequestSerializer(serializers.Serializer):
    """
    Serializer para requisições de predição de temperatura
    """
    hours_ahead = serializers.IntegerField(default=1, min_value=1, max_value=24)


class FanOptimizationRequestSerializer(serializers.Serializer):
    """
    Serializer para requisições de otimização do ventilador
    """
    current_temperature = serializers.FloatField()
    current_hour = serializers.IntegerField(default=None, min_value=0, max_value=23, allow_null=True)


class AnomalyDetectionRequestSerializer(serializers.Serializer):
    """
    Serializer para requisições de detecção de anomalias
    """
    temperature = serializers.FloatField()
    hour = serializers.IntegerField(default=None, min_value=0, max_value=23, allow_null=True)


class TrainingRequestSerializer(serializers.Serializer):
    """
    Serializer para requisições de treinamento
    """
    days_back = serializers.IntegerField(default=30, min_value=7, max_value=365)
    model_type = serializers.ChoiceField(
        choices=['temperature_prediction', 'fan_optimization', 'anomaly_detection'],
        required=False
    )
    force_retrain = serializers.BooleanField(default=False)


class ModelStatusResponseSerializer(serializers.Serializer):
    """
    Serializer para resposta de status dos modelos
    """
    active_models = MLModelSerializer(many=True)
    total_active_models = serializers.IntegerField()
    recent_readings_24h = serializers.IntegerField()
    system_status = serializers.CharField()