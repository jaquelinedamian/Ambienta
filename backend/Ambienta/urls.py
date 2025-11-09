# Ambienta/urls.py (Seu arquivo de URLs principal)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    # URLs de Administração e Frontend Principal
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),  # URLs do django-allauth
    path('dashboard/', include('dashboard.urls')),
    

    path('api/', include('sensors.urls')),

    path('api/ml/', include('ml_models.urls')),
]

if settings.DEBUG:
   
    urlpatterns += staticfiles_urlpatterns()

   
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 