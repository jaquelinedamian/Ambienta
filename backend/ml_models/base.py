# backend/ml_models/base.py

from django.utils import timezone
from .cache import model_cache
from .models import MLModel
import joblib
import threading

class BaseMLModel:
    """
    Classe base para modelos ML com lazy loading e cache
    """
    def __init__(self, model_type):
        self._model = None
        self._model_type = model_type
        self._lock = threading.Lock()
        
    @property
    def model(self):
        """Lazy loading do modelo com cache"""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    # Tenta obter do cache primeiro
                    cached_model = model_cache.get(self._model_type)
                    if cached_model is not None:
                        self._model = cached_model
                        return self._model
                    
                    try:
                        # Tenta carregar do banco de dados
                        saved_model = MLModel.objects.filter(
                            model_type=self._model_type,
                            is_active=True
                        ).first()
                        
                        if saved_model:
                            self._model = joblib.load(saved_model.model_file.path)
                            # Armazena no cache
                            model_cache.set(self._model_type, self._model)
                    except Exception as e:
                        print(f"Erro ao carregar modelo {self._model_type}: {str(e)}")
                        # Retorna None em caso de erro
                        return None
        
        return self._model
    
    def save_model(self, model_obj):
        """Salva o modelo no banco e atualiza o cache"""
        try:
            # Salva no banco
            model_data = MLModel.objects.create(
                model_type=self._model_type,
                is_active=True,
                created_at=timezone.now()
            )
            model_data.save_model(model_obj)
            
            # Atualiza cache
            model_cache.set(self._model_type, model_obj)
            self._model = model_obj
            
            return True
        except Exception as e:
            print(f"Erro ao salvar modelo {self._model_type}: {str(e)}")
            return False