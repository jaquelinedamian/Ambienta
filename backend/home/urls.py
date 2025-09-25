# backend/home/urls.py
from django.urls import path
from . import views  # Certifique-se de que esta linha está correta

urlpatterns = [
    path('', views.home_view, name='home'),
]