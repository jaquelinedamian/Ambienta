from datetime import datetime, timedelta
import random

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