# backend/sensors/urls.py
from django.urls import path
from .views import ReadingCreateAPIView, ReadingListAPIView, FanStateAPIView

urlpatterns = [
    path('receive-data/', ReadingCreateAPIView.as_view(), name='receive_data'),
    path('data/', ReadingListAPIView.as_view(), name='list_data'),
    path('fan/', FanStateAPIView.as_view(), name='fan_state'), # Esta linha cria o endpoint
]