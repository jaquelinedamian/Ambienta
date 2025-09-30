# GUIA DE USO DO SISTEMA DE MACHINE LEARNING - AMBIENTA

## Visão Geral

O sistema de Machine Learning foi adicionado com sucesso ao projeto Ambienta! Ele inclui três modelos principais:

### 1. 🌡️ **Predição de Temperatura**
- Prevê a temperatura das próximas horas baseado em dados históricos
- Usa features temporais (hora, dia da semana, mês) e dados históricos de temperatura
- Considera o estado do ventilador para melhor precisão

### 2. ⚙️ **Otimização do Ventilador**
- Determina automaticamente quando e por quanto tempo ligar o ventilador
- Analisa padrões históricos de eficiência de resfriamento
- Sugere durações otimizadas baseadas na temperatura atual

### 3. 🚨 **Detecção de Anomalias**
- Identifica leituras de temperatura anômalas
- Detecta falhas de sensores ou condições ambientais incomuns
- Fornece score de confiança para cada detecção

---

## 🚀 Como Usar

### 1. **Instalação das Dependências**
```bash
pip install -r requirements.txt
```

### 2. **Aplicar Migrações**
```bash
python manage.py migrate
```

### 3. **Treinar os Modelos Iniciais**
```bash
# Via comando Django
python manage.py train_ml_models

# Ou via API (POST)
curl -X POST http://localhost:8000/ml/api/train/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 📡 **Endpoints da API**

### 🔧 **Treinamento**
```http
POST /ml/api/train/
Authorization: Token YOUR_TOKEN

Response:
{
  "message": "Modelos treinados com sucesso",
  "results": {
    "temperature_prediction": {"mse": 0.45, "r2": 0.85},
    "fan_optimization": {"mse": 0.32, "r2": 0.78},
    "anomaly_detection": {"anomaly_ratio": 0.08}
  }
}
```

### 🌡️ **Predição de Temperatura**
```http
GET /ml/api/predict/temperature/?hours_ahead=6
Authorization: Token YOUR_TOKEN

Response:
{
  "predictions": [
    {"hour": "2024-09-29 15:00", "predicted_temperature": 24.5},
    {"hour": "2024-09-29 16:00", "predicted_temperature": 25.2}
  ],
  "model_info": {
    "name": "Predição de Temperatura",
    "version": "1.0",
    "accuracy": 0.85
  }
}
```

### ⚙️ **Otimização do Ventilador**
```http
POST /ml/api/optimize/fan/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "current_temperature": 26.5,
  "current_hour": 14
}

Response:
{
  "recommended_duration_minutes": 15,
  "should_turn_on": true,
  "reason": "Otimização ML (modelo Otimização de Ventilador)",
  "current_temperature": 26.5
}
```

### 🚨 **Detecção de Anomalias**
```http
POST /ml/api/detect/anomaly/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "temperature": 45.0,
  "hour": 14
}

Response:
{
  "is_anomaly": true,
  "confidence": 0.92,
  "anomaly_score": -0.8,
  "reason": "Análise ML (modelo Detecção de Anomalias)"
}
```

### 📊 **Status dos Modelos**
```http
GET /ml/api/models/status/
Authorization: Token YOUR_TOKEN

Response:
{
  "active_models": [
    {
      "id": 1,
      "name": "Predição de Temperatura",
      "type": "temperature_prediction",
      "version": "1.0",
      "accuracy": 0.85,
      "last_trained": "2024-09-29T10:30:00Z",
      "total_predictions": 150
    }
  ],
  "total_active_models": 3,
  "recent_readings_24h": 288,
  "system_status": "operational"
}
```

---

## 🔄 **Integração Automática**

O sistema está configurado para processar automaticamente cada nova leitura de sensor:

1. **Detecção de Anomalias**: Verifica se a temperatura é anômala
2. **Otimização Automática**: Se temperatura > 24°C, sugere controle do ventilador
3. **Logging Inteligente**: Registra todas as ações ML para análise posterior

### Exemplo no código:
```python
# Ao salvar uma nova leitura, o ML é ativado automaticamente
reading = Reading.objects.create(temperature=26.5)
# Signal dispara automaticamente:
# - Verificação de anomalia
# - Otimização do ventilador
# - Logging das ações
```

---

## 🎯 **Funções Utilitárias**

### No Dashboard ou Views customizadas:
```python
from ml_models.integrations import (
    get_ml_recommendations,
    check_temperature_anomaly,
    MLIntegrationService
)

# Obter recomendações gerais
recommendations = get_ml_recommendations()

# Verificar anomalia específica
anomaly_result = check_temperature_anomaly(temperature=30.0, hour=15)

# Obter previsão de temperatura
forecast = MLIntegrationService.get_temperature_forecast(hours_ahead=8)
```

---

## 📈 **Melhorias Futuras Possíveis**

### 1. **Modelos Mais Avançados**
- Redes neurais para predições complexas
- Análise de séries temporais com LSTM
- Modelos ensemble para maior precisão

### 2. **Features Adicionais**
- Integração com dados meteorológicos externos
- Predição de consumo energético
- Controle inteligente baseado em ocupação

### 3. **Otimizações de Performance**
- Cache de predições frequentes
- Treinamento incremental
- Processamento assíncrono com Celery

### 4. **Interface Visual**
- Dashboard ML com gráficos de performance
- Visualização de anomalias em tempo real
- Interface para ajuste de hiperparâmetros

---

## ⚠️ **Considerações Importantes**

1. **Dados Mínimos**: O sistema precisa de pelo menos 10 leituras para treinar
2. **Retreinamento**: Recomenda-se retreinar os modelos semanalmente
3. **Monitoramento**: Acompanhe as métricas de performance regularmente
4. **Backup**: Os modelos são salvos em arquivos `.pkl` na pasta `models/`

---

## 🛠️ **Comandos Úteis**

```bash
# Treinar modelos específicos
python manage.py train_ml_models --model-type temperature_prediction

# Forçar retreinamento
python manage.py train_ml_models --force

# Usar dados de mais dias
python manage.py train_ml_models --days-back 60

# Ver status no admin
# Acesse /admin/ e vá para "ML MODELS"
```

---

## 📚 **Estrutura dos Arquivos Criados**

```
ml_models/
├── models.py              # Modelos Django para ML
├── ml_algorithms.py       # Algoritmos de ML (RandomForest, etc.)
├── views.py              # API endpoints
├── integrations.py       # Integração com sistema existente
├── signals.py            # Processamento automático
├── serializers.py        # Serializers DRF
├── admin.py              # Interface de administração
├── urls.py               # URLs das APIs
├── management/commands/
│   └── train_ml_models.py # Comando para treinamento
└── migrations/           # Migrações do banco
```

---

## 🎉 **Pronto para Usar!**

O sistema de Machine Learning está totalmente integrado e funcional. Ele começará a aprender com os dados do seu ambiente automaticamente e fornecerá insights inteligentes para otimizar o controle de temperatura.

Para dúvidas ou melhorias, consulte a documentação dos modelos no Django Admin em `/admin/ml_models/`.