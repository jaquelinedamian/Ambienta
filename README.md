# 🌱 Ambienta - Sistema Inteligente de Climatização

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2-green?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-purple?style=for-the-badge&logo=bootstrap)
![MQTT](https://img.shields.io/badge/MQTT-IoT-orange?style=for-the-badge&logo=mqtt)
![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-red?style=for-the-badge&logo=scikit-learn)

*Sistema IoT inteligente para monitoramento e controle automático de temperatura com Machine Learning*

</div>

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Machine Learning](#-machine-learning)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

## 🌟 Sobre o Projeto

O **Ambienta** é um sistema inteligente de climatização que utiliza Machine Learning para otimizar o controle de temperatura em ambientes fechados. O sistema integra coleta de dados, análise preditiva e detecção de anomalias para garantir o conforto térmico e eficiência energética.

### Principais Objetivos

- 🌡️ **Monitoramento Inteligente**: Análise contínua da temperatura
- 🤖 **Machine Learning**: Predições precisas e detecção de anomalias
- 📊 **Dashboard Analítico**: Visualização completa do sistema
- ⚡ **Otimização Energética**: Uso eficiente dos equipamentos
- � **Automação**: Controle automatizado baseado em dados
- 📱 **Acessibilidade**: Interface web responsiva

## ✨ Funcionalidades

### � Principais Recursos
- **Dashboard ML**: Visualização de predições e anomalias
- **Análise Preditiva**: Previsão de temperaturas futuras
- **Detecção de Anomalias**: Identificação automática de problemas
- **Sistema de Login**: Autenticação segura de usuários

### 🤖 Inteligência Artificial
- **Predição de temperatura** das próximas horas usando modelos de regressão
- **Otimização automática do ventilador** usando aprendizado por reforço:
  - Análise de padrões de temperatura
  - Adaptação a diferentes períodos do dia
  - Economia de energia vs efetividade
  - Feedback contínuo para melhorias
- **Detecção de anomalias** em leituras de sensores usando Isolation Forest
- **Sistema de ML adaptativo** com retreinamento automático
- **Métricas em tempo real** de performance dos modelos

### 🌐 Sistema Web
- **Dashboard interativo** com estatísticas em tempo real
- **Visualização de predições** e anomalias
- **Controle manual e automático** do sistema
- **Interface responsiva** para diferentes dispositivos

## 🛠 Tecnologias

### Backend
- **Django 5.2** - Framework web principal
- **Python 3.12+** - Linguagem base
- **SQLite** - Banco de dados
- **Django Allauth** - Sistema de autenticação

### Machine Learning
- **Scikit-learn 1.5.1** - Algoritmos de ML
- **Pandas 2.2.2** - Manipulação de dados
- **NumPy 1.26.4** - Computação numérica
- **Matplotlib/Seaborn** - Visualizações

### IoT & Comunicação
- **Paho MQTT 2.1.0** - Protocolo MQTT
- **Channels Redis** - WebSockets
- **ESP32** - Microcontrolador (hardware)

### Frontend
- **Bootstrap 5** - Framework CSS
- **JavaScript** - Interatividade
- **Chart.js** - Gráficos dinâmicos
- **HTML5/CSS3** - Interface moderna

### DevOps & Deploy
- **Gunicorn** - Servidor WSGI
- **WhiteNoise** - Arquivos estáticos
- **Python Decouple** - Configurações
- **Render** - Plataforma de deploy

## 🏗 Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Hardware      │
│                 │    │                 │    │                 │
│ • Dashboard     │◄──►│ • Django API    │◄──►│ • ESP32         │
│ • Charts        │    │ • ML Models     │    │ • Sensores      │
│ • Controls      │    │ • MQTT Broker   │    │ • Ventiladores  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Database      │
                    │                 │
                    │ • Readings      │
                    │ • ML Models     │
                    │ • Predictions   │
                    └─────────────────┘
```

## 📁 Estrutura do Projeto

```
Ambienta/
├── backend/                # Aplicação Django
│   ├── Ambienta/         # Configurações do projeto
│   ├── accounts/         # Gestão de usuários
│   ├── dashboard/        # Visualização de dados
│   ├── ml_models/        # Modelos de Machine Learning
│   ├── sensors/          # Integração com sensores
│   └── home/            # Página inicial
├── frontend/             # Assets e templates
│   ├── static/          # Arquivos estáticos (CSS, JS)
│   └── templates/       # Templates HTML
└── models/              # Modelos ML treinados
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.12+
- pip (gerenciador de pacotes Python)
- Git

### Passo a Passo

1. **Clone o Repositório**
```bash
git clone https://github.com/jaquelinedamian/Ambienta.git
cd Ambienta
```

2. **Ambiente Virtual**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. **Dependências**
```bash
cd backend
pip install -r requirements.txt
```

4. **Banco de Dados**
```bash
python manage.py migrate
```

### 5. Treinamento dos Modelos ML

```bash
python manage.py train_ml_models
```

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na pasta `backend/`:

```env
# Configurações Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Banco de Dados
DATABASE_URL=sqlite:///db.sqlite3

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC=sensors/#
MQTT_CLIENT_ID=ambienta_backend

# Machine Learning
USE_MOCK_DATA=False  # True para dados simulados em desenvolvimento
```

### Configuração MQTT

O sistema usa MQTT para comunicação com dispositivos IoT:

- **Broker padrão**: `broker.hivemq.com`
- **Tópico de comando**: `ambienta/comando/ambienta_esp32_1`
- **Tópico de dados**: `ambienta/dados/temperatura`

## 📖 Como Usar

### 1. Executar o Servidor

**⚠️ IMPORTANTE**: Você deve navegar para o diretório `backend/` antes de executar o servidor:

```bash
# Windows (PowerShell)
cd backend
python manage.py runserver 127.0.0.1:8080

# Ou usar caminho absoluto:
python "caminho/completo/para/backend/manage.py" runserver 127.0.0.1:8080
```

**🌐 Acesse SEMPRE via HTTP**: `http://127.0.0.1:8080`

**⚠️ SOLUÇÃO para SSL_ERROR_RX_RECORD_TOO_LONG:**
Se você receber erro SSL ou "Falha na conexão segura":

1. **Use porta 8080** em vez de 8000: `http://127.0.0.1:8080`
2. **Abra aba incógnita** (Ctrl+Shift+N)
3. **Digite manualmente** a URL completa: `http://127.0.0.1:8080`
4. **NÃO permita** que o navegador complete automaticamente para HTTPS
5. **Limpe cache** se necessário (Ctrl+Shift+Delete)

### 2. Dashboard Principal

- **Home**: `/` - Página inicial com visão geral
- **Dashboard**: `/dashboard/` - Gráficos e controles em tempo real
- **Admin**: `/admin/` - Painel administrativo Django

### 3. Controle do Ventilador

#### Automático
O sistema liga automaticamente o ventilador quando:
- Temperatura > 25°C
- Dentro do horário configurado
- Modelo ML recomenda ação

#### Manual
- Acesse o dashboard
- Use o botão "Forçar Ligado"
- Configure horários de funcionamento

### 4. Monitoramento

- **Tempo Real**: Gráficos atualizados automaticamente
- **Histórico**: Dados das últimas 24h/7dias/30dias
- **Alertas**: Notificações de anomalias detectadas

## 🧠 Machine Learning

O sistema possui três modelos de IA integrados:

### 🌡️ Predição de Temperatura
```python
# Exemplo de uso da API
GET /api/ml/predict-temperature/
{
  "predicted_temperature": 26.5,
  "confidence": 0.95,
  "next_hours": [25.2, 26.1, 26.8]
}
```

### ⚙️ Otimização do Ventilador
- **🧠 Modelo**: Random Forest Classifier
- **📊 Features**: Temperatura atual, hora do dia, histórico de efetividade
- **📈 Métricas**:
  - Economia de energia vs. controle manual
  - Efetividade na redução de temperatura
  - Nível de confiança nas decisões

```python
# Recomendação automática
POST /api/ml/optimize/fan/
{
  "current_temperature": 27.5,
  "current_hour": 14,
  
  "response": {
    "should_turn_on": true,
    "recommended_duration_minutes": 15,
    "confidence": 0.85,
    "reason": "Temperatura elevada e histórico de efetividade positivo"
  }
}
```

#### Dashboard de Otimização
- **Estado Atual**: Status do ventilador e confiança do modelo
- **Métricas de Performance**:
  - Economia de energia vs. controle manual
  - Efetividade média na redução de temperatura
- **Histórico**: Últimas ações e seus resultados

### 🚨 Detecção de Anomalias
```python
# Análise de leitura atual
POST /api/ml/anomaly-detection/
{
  "temperature": 45.0,
  "is_anomaly": true,
  "anomaly_score": 0.95,
  "message": "Temperatura anormalmente alta detectada"
}
```

### Retreinamento

Os modelos são retreinados automaticamente a cada 100 novas leituras:

```bash
# Retreinamento manual
python manage.py train_ml_models --force
```

## 🔌 API

### Endpoints Principais

#### Sensores
```http
GET    /api/sensors/readings/         # Listar leituras
POST   /api/sensors/readings/         # Nova leitura
GET    /api/sensors/fan-state/        # Estado do ventilador
PUT    /api/sensors/fan-state/        # Controlar ventilador
```

#### Machine Learning
```http
GET    /api/ml/predict-temperature/   # Predizer temperatura
GET    /api/ml/fan-optimization/      # Otimizar ventilador
POST   /api/ml/anomaly-detection/     # Detectar anomalias
POST   /api/ml/retrain/               # Retreinar modelos
```

#### Dashboard
```http
GET    /api/dashboard/summary/        # Resumo geral
GET    /api/dashboard/charts/         # Dados para gráficos
GET    /api/dashboard/alerts/         # Alertas ativos
```

### Exemplo de Uso

```python
import requests

# Nova leitura de temperatura
response = requests.post('http://localhost:8000/api/sensors/readings/', {
    'temperature': 24.5
})

# Obter predição
prediction = requests.get('http://localhost:8000/api/ml/predict-temperature/')
print(f"Próxima temperatura: {prediction.json()['predicted_temperature']}°C")
```

## 📁 Estrutura do Projeto

```
Ambienta/
├── backend/                # Aplicação Django
│   ├── Ambienta/          # Configurações do projeto
│   ├── accounts/          # Gestão de usuários
│   ├── dashboard/         # Dashboard principal
│   ├── ml_models/         # Modelos de Machine Learning
│   ├── sensors/           # Dados dos sensores
│   ├── home/             # Página inicial
│   └── models/           # Modelos ML treinados
├── frontend/             # Frontend
│   ├── static/          # CSS, JS, imagens
│   └── templates/       # Templates HTML
└── README.md           # Documentação
```

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Testes específicos
python manage.py test sensors.tests
python manage.py test ml_models.tests

# Com cobertura
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Deploy

### Render (Recomendado)

1. **Fork** este repositório
2. Conecte ao **Render**
3. Configure as variáveis de ambiente
4. Deploy automático habilitado

### Docker (Opcional)

```dockerfile
# Dockerfile básico
FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
EXPOSE 8000

CMD ["gunicorn", "Ambienta.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🤝 Contribuição

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

### Diretrizes de Código

- Siga o **PEP 8** para Python
- Use **type hints** quando possível
- Adicione **testes** para novas funcionalidades
- Documente **APIs** e **funções complexas**

## 📊 Status do Projeto

- ✅ **Backend Django** - Completo
- ✅ **APIs REST** - Completo
- ✅ **Machine Learning** - Completo
- ✅ **Dashboard** - Completo
- ✅ **MQTT Integration** - Completo
- 🚧 **Mobile App** - Em desenvolvimento
- 📋 **Documentação** - Em andamento

## 🐛 Problemas Conhecidos

- [ ] WebSocket pode desconectar em navegadores antigos
- [ ] Modelos ML precisam de mais dados para melhor precisão
- [ ] Interface mobile precisa de melhorias

## 🔮 Roadmap

### Versão 2.0
- [ ] **App Mobile** (React Native)
- [ ] **Múltiplos sensores** por ambiente
- [ ] **IA mais avançada** (Deep Learning)
- [ ] **Integração com AWS IoT**

### Versão 3.0
- [ ] **Análise preditiva** avançada
- [ ] **Dashboard empresarial**
- [ ] **API GraphQL**
- [ ] **Microserviços**

## 👥 Equipe

- **Frontend & UI/UX**: [Jaqueline Damian](https://github.com/jaquelinedamian)
- **Backend & ML**: [Fernando](https://github.com/FNascim)
- **IoT & Hardware**: [Equipe IoT]
- **DevOps**: [Equipe DevOps]

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**🌱 Ambienta - Sistema Inteligente de Climatização**

</div>