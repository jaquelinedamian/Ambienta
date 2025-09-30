# backend/ml_models/urls.py

from django.urls import path
from . import views
from . import views_dashboard

app_name = 'ml_models'

urlpatterns = [
    # Dashboard view
    path('dashboard/', views_dashboard.ml_dashboard, name='ml_dashboard'),
    
    # API endpoints para ML
    path('api/train/', views.TrainModelsAPIView.as_view(), name='train_models'),
    path('api/predict/temperature/', views.TemperaturePredictionAPIView.as_view(), name='temperature_prediction'),
    path('api/optimize/fan/', views.FanOptimizationAPIView.as_view(), name='fan_optimization'),
    path('api/detect/anomaly/', views.AnomalyDetectionAPIView.as_view(), name='anomaly_detection'),
    path('api/models/status/', views.ModelStatusAPIView.as_view(), name='model_status'),
    path('api/models/<int:model_id>/metrics/', views.ModelMetricsAPIView.as_view(), name='model_metrics'),
]