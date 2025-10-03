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
    Signal para processar automaticamente novas leituras com ML e atualizar predições
    """
    if not created:  # Ignorar atualizações de leituras existentes
        return

    try:
        from .models import MLModel, MLPrediction
        
        # Processar a leitura com ML
        process_sensor_reading(instance)
        logger.info(f"Leitura {instance.id} processada com ML automaticamente")
        
        # Buscar modelos ativos que podem precisar de atualização
        active_models = MLModel.objects.filter(is_active=True)
        
        for model in active_models:
            try:
                if model.model_type == 'anomaly_detection':
                    # Processar detecção de anomalias para a nova leitura
                    model_instance = model.load_model()
                    if model_instance:
                        input_data = {
                            'temperature': instance.temperature,
                            'hour': instance.timestamp.hour
                        }
                        prediction = model_instance.predict([input_data])
                        
                        MLPrediction.objects.create(
                            model=model,
                            input_data=input_data,
                            prediction={
                                'is_anomaly': bool(prediction[0]),
                                'anomaly_score': float(prediction[1]) if len(prediction) > 1 else 0.5
                            }
                        )
                        
            except Exception as model_error:
                logger.error(f"Erro ao processar modelo {model.name}: {str(model_error)}")
                continue
                
    except Exception as e:
        # Log do erro, mas não interrompe o salvamento da leitura
        logger.error(f"Erro ao processar leitura {instance.id} com ML: {str(e)}")