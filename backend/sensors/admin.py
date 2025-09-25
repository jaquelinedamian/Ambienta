# backend/sensors/admin.py

from django.contrib import admin
from .models import Reading, FanState  # Importe ambos os modelos

admin.site.register(Reading)
admin.site.register(FanState) # Registre o modelo FanState