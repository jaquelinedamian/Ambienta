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
    if created and not getattr(instance, '_processing_ml', False):
        try:
            # Marca a instância para evitar loops
            instance._processing_ml = True
            
            # Processar a leitura com ML
            process_sensor_reading(instance)
            
            logger.info(f"Leitura {instance.id} processada com ML")
            
        except Exception as e:
            logger.error(f"Erro ao processar leitura {instance.id} com ML: {str(e)}")
        finally:
            # Remove a marca
            instance._processing_ml = False