# backend/ml_models/cache.py

import threading
from datetime import datetime, timedelta
from django.core.cache import cache

class MLModelCache:
    """
    Cache simples para modelos ML
    """
    def __init__(self):
        self.CACHE_TTL = 3600  # 1 hora
        self._lock = threading.Lock()
    
    def get(self, key):
        """Obtém modelo do cache"""
        return cache.get(f'ml_model_{key}')
    
    def get(self, key):
        """Obtém modelo do cache"""
        return cache.get(f'ml_model_{key}')

    def set(self, key, value):
        """Armazena modelo no cache"""
        cache.set(f'ml_model_{key}', value, self.CACHE_TTL)
    
    def clear(self):
        """Limpa o cache"""
        for key in ['temperature_prediction', 'fan_optimization', 'anomaly_detection']:
            cache.delete(f'ml_model_{key}')
    
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