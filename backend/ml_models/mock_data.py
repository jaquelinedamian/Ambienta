from datetime import datetime, timedelta
import random

def generate_mock_ml_data():
    """
    Gera dados simulados para os modelos de Machine Learning
    """
    now = datetime.now()
    
    # Simulação de predições recentes
    recent_predictions = []
    prediction_types = ['temperature_prediction', 'fan_optimization', 'anomaly_detection']
    
    for _ in range(5):
        prediction_time = now - timedelta(minutes=random.randint(1, 120))
        model_type = random.choice(prediction_types)
        
        if model_type == 'temperature_prediction':
            prediction = {
                'temperatures': [round(random.uniform(20, 30), 1) for _ in range(3)],
                'confidence': random.uniform(0.7, 0.95)
            }
        elif model_type == 'fan_optimization':
            prediction = {
                'should_turn_on': random.random() > 0.5,
                'optimal_duration': random.randint(5, 30),
                'confidence': random.uniform(0.7, 0.95)
            }
        else:  # anomaly_detection
            prediction = {
                'is_anomaly': random.random() > 0.8,
                'anomaly_score': random.uniform(0, 1),
                'confidence': random.uniform(0.7, 0.95)
            }
        
        recent_predictions.append({
            'model_type': model_type,
            'created_at': prediction_time,
            'prediction': prediction,
            'timestamp': prediction_time  # Campo adicional para compatibilidade com o template
        })
    
    # Ordenar por timestamp mais recente
    recent_predictions.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Criar algumas anomalias recentes
    anomalies = []
    for _ in range(random.randint(1, 3)):  # 1 a 3 anomalias hoje
        anomaly_time = now - timedelta(minutes=random.randint(1, 1440))  # Últimas 24h
        anomalies.append({
            'created_at': anomaly_time,
            'prediction': {
                'is_anomaly': True,
                'anomaly_score': random.uniform(0.8, 1),
                'confidence': random.uniform(0.85, 0.98)
            },
            'timestamp': anomaly_time  # Campo adicional para compatibilidade com o template
        })
    
    # Ordenar anomalias por timestamp
    anomalies.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {
        'active_models': 3,  # Número fixo de modelos ativos
        'latest_prediction': recent_predictions[0] if recent_predictions else None,
        'anomalies_today': len(anomalies),
        'latest_anomaly': anomalies[0] if anomalies else None,
        'recent_predictions': recent_predictions,
        'anomalies': anomalies
    }

def generate_mock_fan_data():
    """
    Gera dados simulados para o dashboard de otimização do ventilador
    """
    now = datetime.now()
    
    # Simular estado atual do ventilador (mais probabilidade de estar desligado)
    fan_state = random.random() > 0.7  # 30% de chance de estar ligado
    
    # Simular confiança do modelo (70-99%)
    fan_confidence = random.randint(70, 99)
    
    # Simular economia de energia (15-40%)
    energy_savings = random.uniform(15.0, 40.0)
    
    # Simular efetividade na redução de temperatura (50-90%)
    fan_effectiveness = random.uniform(50.0, 90.0)
    
    # Gerar histórico de otimizações
    fan_optimization_history = []
    for i in range(10):
        # Timestamp decrementando a cada registro (de 10 em 10 minutos)
        timestamp = now - timedelta(minutes=i*10)
        
        # Temperatura base entre 24-30°C
        base_temp = random.uniform(24.0, 30.0)
        
        # Decidir ação baseada na temperatura
        action = base_temp > 25.0
        
        # Duração do acionamento (5-30 min)
        duration = random.randint(5, 30) if action else 0
        
        # Redução de temperatura (0.5-2.0°C se acionado)
        temp_reduction = random.uniform(0.5, 2.0) if action else 0.0
        
        fan_optimization_history.append({
            'timestamp': timestamp,
            'temperature': round(base_temp, 1),
            'action': action,
            'duration': duration,
            'temperature_reduction': round(temp_reduction, 1)
        })
    
    return {
        'fan_state': fan_state,
        'fan_confidence': fan_confidence,
        'energy_savings': round(energy_savings, 1),
        'fan_effectiveness': round(fan_effectiveness, 1),
        'fan_optimization_history': fan_optimization_history
    }
    
    return {
        'fan_state': fan_state,
        'fan_confidence': fan_confidence,
        'energy_savings': round(energy_savings, 1),
        'fan_effectiveness': round(fan_effectiveness, 1),
        'fan_optimization_history': fan_optimization_history
    }