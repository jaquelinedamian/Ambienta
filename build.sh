#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Current directory: $(pwd)"
echo "Listing directory contents:"
ls -la

echo "Moving to backend directory..."
cd backend || exit 1
echo "New current directory: $(pwd)"
echo "Listing backend directory contents:"
ls -la

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running collectstatic..."
python manage.py collectstatic --no-input

echo "Creating superuser if not exists..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

echo "Creating ESP8266 user and token if not exists..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()
esp_user, created = User.objects.get_or_create(username='esp8266')
if created:
    esp_user.set_password('esp8266pass')
    esp_user.save()
    print('ESP8266 user created')
token, created = Token.objects.get_or_create(user=esp_user)
print(f'ESP8266 token: {token.key}')
EOF

echo "Running makemigrations merge to resolve conflicts..."
python manage.py makemigrations --merge --noinput

echo "Running migrations..."
python manage.py migrate

echo "Training ML models..."
python manage.py shell << EOF
from ml_models.models import MLModel
from ml_models.ml_algorithms import TemperaturePredictionModel, AnomalyDetectionModel, FanOptimizationModel
from django.utils import timezone

def ensure_model(model_type, name, model_class):
    model, created = MLModel.objects.get_or_create(
        model_type=model_type,
        defaults={
            'name': name,
            'version': '1.0',
            'is_active': True
        }
    )
    
    if created or not model.model_data:
        print(f"Training {name}...")
        ml_instance = model_class()
        try:
            metrics = ml_instance.train()
            model.save_model(ml_instance.model)
            model.accuracy = metrics.get('r2', metrics.get('accuracy'))
            model.mse = metrics.get('mse')
            model.mae = metrics.get('mae')
            model.r2_score = metrics.get('r2')
            model.last_trained = timezone.now()
            model.save()
            print(f"{name} trained and saved successfully")
        except Exception as e:
            print(f"Error training {name}: {str(e)}")
    else:
        print(f"{name} already exists and has model data")

# Train all models
ensure_model('temperature_prediction', 'Temperature Prediction Model', TemperaturePredictionModel)
ensure_model('anomaly_detection', 'Anomaly Detection Model', AnomalyDetectionModel)
ensure_model('fan_optimization', 'Fan Optimization Model', FanOptimizationModel)
EOF

echo "Running Gunicorn with optimized settings..."
cd backend && gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 120 \
    --limit-request-line 8190 \
    --limit-request-fields 100 \
    --limit-request-field_size 8190 \
    --log-level warning \
    Ambienta.wsgi:application