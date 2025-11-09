from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    # URLs de Frontend
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls')),
    
    # Rota antiga (CONFLITANTE), desabilitada:
    # path('sensors/', include('sensors.urls')),
    
    # === ROTA CORRIGIDA PARA O ESP8266: /api/ ===
    # Esta linha faz com que as rotas em sensors/urls.py sejam acessadas via /api/
    path('api/', include('sensors.urls')),
    
    path('ml/', include('ml_models.urls')),
]

# Configurações de DEBUG
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)