# backend/sensors/urls.py

from django.urls import path
# ATENÇÃO: Adicione 'FanControlAPIView' à lista de importações
from .views import ReadingCreateAPIView, ReadingListAPIView, FanStateAPIView, DeviceConfigUpdateView, FanControlAPIView 

app_name = 'sensors' 

urlpatterns = [
    path('receive-data/', ReadingCreateAPIView.as_view(), name='receive_data'),
    path('data/', ReadingListAPIView.as_view(), name='list_data'),
    path('fan/', FanStateAPIView.as_view(), name='fan_state'),
    path('config/', DeviceConfigUpdateView.as_view(), name='config'),
   
    # Rota que estava causando o erro, agora importada:
    path('control-fan/', FanControlAPIView.as_view(), name='control-fan'),
]