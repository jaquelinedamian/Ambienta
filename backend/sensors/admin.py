# backend/sensors/admin.py

from django.contrib import admin
# Importe todos os modelos da sua aplicação sensors
from .models import Reading, FanState, FanLog, DeviceConfig 

# Registro dos modelos:
admin.site.register(Reading)
admin.site.register(FanState) 
admin.site.register(FanLog)       # Adicionado o registro de FanLog
admin.site.register(DeviceConfig) # Adicionado o registro de DeviceConfig