# backend/ml_models/cache.py

import threading
import joblib
from datetime import datetime, timedelta
from django.conf import settings
import os

class MLModelCache:
    """
    Cache thread-safe para modelos ML com lazy loading
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._cache = {}
        self._last_access = {}
        self._lock = threading.Lock()
        self._ttl = timedelta(hours=1)  # Cache expira em 1 hora
        self.enable_lazy_loading = False  # Habilitado no AppConfig.ready()
    
    def get(self, key):
        """
        Obtém um modelo do cache com lazy loading
        """
        with self._lock:
            if key in self._cache:
                now = datetime.now()
                if now - self._last_access[key] < self._ttl:
                    self._last_access[key] = now
                    return self._cache[key]
                else:
                    # Cache expirou
                    del self._cache[key]
                    del self._last_access[key]
            
            # Se lazy loading estiver ativado, tenta carregar do disco
            if self.enable_lazy_loading:
                try:
                    from .models import MLModel
                    model_obj = MLModel.objects.filter(
                        model_type=key,
                        is_active=True
                    ).first()
                    
                    if model_obj and model_obj.model_file:
                        model = joblib.load(model_obj.model_file.path)
                        self.set(key, model)
                        return model
                except Exception as e:
                    print(f"Erro no lazy loading do modelo {key}: {str(e)}")
                    
            return None
    
    def set(self, key, value):
        """Armazena um modelo no cache"""
        with self._lock:
            self._cache[key] = value
            self._last_access[key] = datetime.now()
    
    def clear(self):
        """Limpa o cache"""
        with self._lock:
            self._cache.clear()
            self._last_access.clear()

model_cache = MLModelCache()