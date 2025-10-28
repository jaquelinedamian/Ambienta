# backend/ml_models/management/commands/enable_ml_control.py

from django.core.management.base import BaseCommand
from sensors.models import DeviceConfig
from django.utils import timezone

class Command(BaseCommand):
    help = 'Ativa o controle ML do ventilador e configura horários padrão'

    def handle(self, *args, **kwargs):
        try:
            config = DeviceConfig.objects.first()
            if not config:
                self.stdout.write("Criando nova configuração...")
                config = DeviceConfig.objects.create(
                    device_id='default-device',
                    ml_control=True,
                    start_hour=timezone.now().replace(hour=8, minute=0),
                    end_hour=timezone.now().replace(hour=22, minute=0)
                )
            else:
                self.stdout.write("Atualizando configuração existente...")
                config.ml_control = True
                config.start_hour = timezone.now().replace(hour=8, minute=0)
                config.end_hour = timezone.now().replace(hour=22, minute=0)
                config.save()

            self.stdout.write(self.style.SUCCESS(
                f'ML Control ativado! Horário: {config.start_hour.strftime("%H:%M")} - {config.end_hour.strftime("%H:%M")}'
            ))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao ativar ML Control: {str(e)}')
            )