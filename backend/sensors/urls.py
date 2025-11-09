from django.urls import path
# ATENÇÃO: Verifique se estes nomes de classes estão corretos no seu views.py
from .views import (
    ReadingCreateAPIView, 
    ReadingListAPIView, 
    FanStateAPIView, 
    DeviceConfigUpdateView, 
    FanControlAPIView
) 

app_name = 'sensors' 

urlpatterns = [
    # 1. Rota para POST de Temperatura: /api/sensors/readings/
    path('sensors/readings/', ReadingCreateAPIView.as_view(), name='receive_data'),
    
    # 2. Rota para GET/PUT do Estado do Ventilador: /api/sensors/fan-state/
    path('sensors/fan-state/', FanStateAPIView.as_view(), name='fan_state'),
    
    # 3. Rota para controle manual (GET/PUT/POST): /api/sensors/control-fan/
    path('sensors/control-fan/', FanControlAPIView.as_view(), name='control-fan'),
    
    # Rotas de listagem para Dashboard/Frontend
    path('sensors/data/', ReadingListAPIView.as_view(), name='list_data'),
    path('sensors/config/', DeviceConfigUpdateView.as_view(), name='config'),
]