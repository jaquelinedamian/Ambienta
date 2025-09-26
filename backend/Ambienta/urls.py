# backend/Ambienta/urls.py - CÓDIGO FINAL CORRIGIDO E DEFINITIVO

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Admin
    path('admin/', admin.site.urls),

    # 2. Rotas Principais (Home, Cadastro, Login, Config)
    # 💡 AJUSTE: Incluímos TUDO na raiz ('') para evitar prefixos redundantes.
    path('', include('home.urls')),
    path('', include('accounts.urls')),

    # 3. Outros Apps com prefixos claros:
    path('dashboard/', include('dashboard.urls')),
    path('sensors/', include('sensors.urls')),

    # 🛑 TODAS AS DUPLICAÇÕES E CONFLITOS FORAM REMOVIDOS
]
