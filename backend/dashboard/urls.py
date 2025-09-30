from django.urls import path
from . import views, ml_views

app_name = 'dashboard'  # Define o namespace

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    
    # URLs para Machine Learning
    path('ml/', ml_views.ml_dashboard_view, name='ml_dashboard'),
    path('api/ml/predictions/', ml_views.get_ml_predictions_api, name='ml_predictions_api'),
    path('api/ml/stats/', ml_views.ml_stats_api, name='ml_stats_api'),
    path('api/ml/train/', ml_views.trigger_ml_training, name='trigger_ml_training'),
]