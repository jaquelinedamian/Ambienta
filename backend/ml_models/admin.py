# backend/ml_models/admin.py

from django.contrib import admin
from .models import MLModel, MLPrediction, TrainingSession, ModelPerformanceMetric


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'model_type', 'version', 'is_active', 
        'accuracy', 'r2_score', 'last_trained', 'created_at'
    ]
    list_filter = ['model_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'model_data']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'model_type', 'description', 'version', 'is_active')
        }),
        ('Métricas de Performance', {
            'fields': ('accuracy', 'mse', 'mae', 'r2_score')
        }),
        ('Configurações', {
            'fields': ('hyperparameters',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_trained', 'model_data'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(MLPrediction)
class MLPredictionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'model', 'created_at', 'confidence', 'is_verified'
    ]
    list_filter = ['model__model_type', 'is_verified', 'created_at']
    readonly_fields = ['created_at']
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Predição', {
            'fields': ('model', 'input_data', 'prediction', 'confidence')
        }),
        ('Verificação', {
            'fields': ('actual_value', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'model', 'status', 'started_at', 'completed_at', 
        'training_samples', 'get_duration'
    ]
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'completed_at', 'get_duration']
    raw_id_fields = ['model']
    
    def get_duration(self, obj):
        if obj.completed_at:
            return obj.duration
        return "Em andamento"
    get_duration.short_description = "Duração"
    
    fieldsets = (
        ('Sessão de Treinamento', {
            'fields': ('model', 'status')
        }),
        ('Dados', {
            'fields': ('data_start_date', 'data_end_date', 'training_samples', 'validation_samples')
        }),
        ('Métricas', {
            'fields': ('training_metrics', 'validation_metrics')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'get_duration'),
            'classes': ('collapse',)
        }),
        ('Erros', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )


@admin.register(ModelPerformanceMetric)
class ModelPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'model', 'metric_name', 'metric_value', 
        'evaluation_start', 'evaluation_end', 'created_at'
    ]
    list_filter = ['metric_name', 'model__model_type', 'created_at']
    readonly_fields = ['created_at']
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Métrica', {
            'fields': ('model', 'metric_name', 'metric_value')
        }),
        ('Período Avaliado', {
            'fields': ('evaluation_start', 'evaluation_end')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
