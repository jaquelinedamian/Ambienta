# backend/sensors/management/commands/init_fan_state.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from sensors.models import FanState

class Command(BaseCommand):
    help = 'Inicializa o estado do ventilador se não existir'

    def handle(self, *args, **kwargs):
        if not FanState.objects.exists():
            FanState.objects.create(
                state=False,
                timestamp=timezone.now()
            )
            self.stdout.write(self.style.SUCCESS('Estado do ventilador inicializado com sucesso'))