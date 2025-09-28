# Ambienta/urls.py (Seu arquivo de URLs principal)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('sensors/', include('sensors.urls')),
]

# ESTA É A CORREÇÃO PRINCIPAL: Adicionar o manuseio de arquivos estáticos e de mídia em modo DEBUG
if settings.DEBUG:
    # 1. Manuseio de arquivos estáticos de APPS e STATICFILES_DIRS (CORREÇÃO)
    urlpatterns += staticfiles_urlpatterns()

    # 2. Manuseio de arquivos de mídia (MEDIA)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

