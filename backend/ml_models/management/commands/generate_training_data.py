from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
import random
from sensors.models import Reading, FanState, FanLog

class Command(BaseCommand):
    help = 'Gera dados simulados para treinamento dos modelos de ML'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de dias de dados históricos para gerar'
        )

    def handle(self, *args, **kwargs):
        days = kwargs['days']
        self.stdout.write(f"Gerando {days} dias de dados simulados...")

        # Limpar dados existentes
        Reading.objects.all().delete()
        FanState.objects.all().delete()
        FanLog.objects.all().delete()

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        current_date = start_date

        # Gerar dados a cada hora
        while current_date <= end_date:
            hour = current_date.hour
            
            # Temperatura base varia com a hora do dia
            base_temp = 22 + (hour / 24) * 8  # 22°C à meia-noite, até 30°C ao meio-dia
            
            # Adicionar variação aleatória
            noise = random.uniform(-1.5, 1.5)
            temperature = base_temp + noise

            # Criar leitura
            Reading.objects.create(
                timestamp=current_date,
                temperature=round(temperature, 1)
            )

            # Decidir se o ventilador deve ser ligado
            if temperature > 25.0:
                # Duração entre 15 e 45 minutos
                duration_minutes = random.randint(15, 45)
                
                # Criar log do ventilador
                fan_log = FanLog.objects.create(
                    start_time=current_date,
                    end_time=current_date + timedelta(minutes=duration_minutes),
                )
                fan_log.duration = fan_log.end_time - fan_log.start_time
                fan_log.save()

                # Criar estado do ventilador (ligado)
                FanState.objects.create(
                    timestamp=current_date,
                    state=True
                )

                # Gerar leituras durante o funcionamento do ventilador
                for minute in range(duration_minutes):
                    reading_time = current_date + timedelta(minutes=minute)
                    # Temperatura diminui gradualmente
                    temp_reduction = (minute / duration_minutes) * random.uniform(1.5, 3.0)
                    new_temp = temperature - temp_reduction
                    Reading.objects.create(
                        timestamp=reading_time,
                        temperature=round(new_temp, 1)
                    )

                # Criar estado do ventilador (desligado)
                FanState.objects.create(
                    timestamp=current_date + timedelta(minutes=duration_minutes),
                    state=False
                )

            # Avançar 1 hora
            current_date += timedelta(hours=1)

        self.stdout.write(self.style.SUCCESS(f'Dados simulados gerados com sucesso para {days} dias!'))