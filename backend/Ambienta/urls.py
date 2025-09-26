# backend/Ambienta/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('sensors/', include('sensors.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]