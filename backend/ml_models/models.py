# backend/ml_models/models.py

from django.db import models
from django.utils import timezone
import pickle
import os
from datetime import timedelta


class MLModel(models.Model):
    """
    Armazena informações sobre modelos de Machine Learning treinados
    """
    MODEL_TYPES = [
        ('temperature_prediction', 'Predição de Temperatura'),
        ('fan_optimization', 'Otimização de Ventilador'),
        ('anomaly_detection', 'Detecção de Anomalias'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    description = models.TextField(blank=True)
    
    # Métricas do modelo
    accuracy = models.FloatField(null=True, blank=True)
    mse = models.FloatField(null=True, blank=True)  # Mean Squared Error
    mae = models.FloatField(null=True, blank=True)  # Mean Absolute Error
    r2_score = models.FloatField(null=True, blank=True)
    
    # Controle de versão
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_trained = models.DateTimeField(null=True, blank=True)
    
    # Parâmetros do modelo (JSON)
    hyperparameters = models.JSONField(default=dict, blank=True)
    
    # Arquivo do modelo treinado
    model_file_path = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['model_type', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({'Ativo' if self.is_active else 'Inativo'})"
    
    def load_model(self):
        """Carrega o modelo pickle do arquivo"""
        if self.model_file_path and os.path.exists(self.model_file_path):
            with open(self.model_file_path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def save_model(self, model, base_path='models/'):
        """Salva o modelo pickle em arquivo"""
        os.makedirs(base_path, exist_ok=True)
        filename = f"{self.model_type}_v{self.version}_{self.id}.pkl"
        filepath = os.path.join(base_path, filename)
        
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        
        self.model_file_path = filepath
        self.save()


class MLPrediction(models.Model):
    """
    Armazena predições feitas pelos modelos de ML
    """
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='predictions')
    
    # Dados de entrada (JSON)
    input_data = models.JSONField()
    
    # Resultado da predição
    prediction = models.JSONField()
    confidence = models.FloatField(null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Se a predição foi verificada posteriormente
    actual_value = models.JSONField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Predição {self.model.model_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class TrainingSession(models.Model):
    """
    Registra sessões de treinamento dos modelos
    """
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='training_sessions', null=True, blank=True)
    
    # Período dos dados usados no treinamento
    data_start_date = models.DateTimeField()
    data_end_date = models.DateTimeField()
    
    # Quantidade de dados
    training_samples = models.IntegerField()
    validation_samples = models.IntegerField(null=True, blank=True)
    
    # Métricas de treinamento
    training_metrics = models.JSONField(default=dict)
    validation_metrics = models.JSONField(default=dict)
    
    # Status
    STATUS_CHOICES = [
        ('running', 'Executando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Log de erros
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Treinamento {self.model.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        return timezone.now() - self.started_at


class ModelPerformanceMetric(models.Model):
    """
    Armazena métricas de performance dos modelos ao longo do tempo
    """
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='performance_metrics')
    
    # Tipo de métrica
    metric_name = models.CharField(max_length=50)  # ex: 'accuracy', 'mse', 'precision'
    metric_value = models.FloatField()
    
    # Período avaliado
    evaluation_start = models.DateTimeField()
    evaluation_end = models.DateTimeField()
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model', 'metric_name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.metric_name}: {self.metric_value:.4f}"
