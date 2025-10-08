# backend/ml_models/cache.py

import threading
from datetime import datetime, timedelta

class MLModelCache:
    """
    Cache thread-safe para modelos ML
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
    
    def get(self, key):
        """Obtém um modelo do cache"""
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