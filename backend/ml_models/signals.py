# backend/ml_models/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from sensors.models import Reading
from .integrations import process_sensor_reading

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Reading)
def process_reading_with_ml(sender, instance, created, **kwargs):
    """
    Signal para processar automaticamente novas leituras com ML
    """
    if created:  # Apenas para novas leituras
        try:
            # Processar a leitura com ML em background
            # Em produção, considere usar Celery para tarefas assíncronas
            process_sensor_reading(instance)
            
            logger.info(f"Leitura {instance.id} processada com ML automaticamente")
            
        except Exception as e:
            # Log do erro, mas não interrompe o salvamento da leitura
            logger.error(
                f"Erro ao processar leitura {instance.id} com ML: {str(e)}"
            )