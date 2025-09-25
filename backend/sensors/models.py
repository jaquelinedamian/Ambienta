# backend/sensors/models.py

from django.db import models

class Reading(models.Model):
    temperature = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leitura de {self.timestamp}"

class FanState(models.Model):
    state = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ventilador: {'LIGADO' if self.state else 'DESLIGADO'}"

class FanLog(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"Ventilador Ligado: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"