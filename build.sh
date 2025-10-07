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

echo "Build script completed."