# backend/Ambienta/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Rotas de administração
    path('admin/', admin.site.urls),

    # Rotas do aplicativo 'home' (geralmente mapeadas para a raiz do site)
    path('', include('home.urls')),

    # Rotas de autenticação personalizadas (register, login, logout)
    path('accounts/', include('accounts.urls')),

    # Rotas dos seus aplicativos de negócio
    path('dashboard/', include('dashboard.urls')),
    path('sensors/', include('sensors.urls')),

