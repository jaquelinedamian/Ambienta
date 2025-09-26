"""
Django settings for Ambienta project.
"""
import os
import dj_database_url
from decouple import config 
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS: Lê a variável DJANGO_ALLOWED_HOSTS do Render, com fallback seguro
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default=[], cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition

INSTALLED_APPS = [
    # ... (Seus apps existentes)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'crispy_forms',
    'crispy_bootstrap5',
    'home',
    'accounts',
    'dashboard',
    'sensors',
    'corsheaders',
]


# CONFIGURAÇÃO OBRIGATÓRIA PARA O DJANGO-CRISPY-FORMS:
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',    # Para servir estáticos
    'corsheaders.middleware.CorsMiddleware',         # Para comunicação Frontend/Backend

    # Ordem correta de autenticação e sessão:
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Deve estar aqui
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # 🛑 Se você tinha um middleware de login global, remova-o daqui!
    # EXEMPLO DO QUE DEVE SER REMOVIDO: 'login_required.middleware.LoginRequiredMiddleware',
]

ROOT_URLCONF = 'Ambienta.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'frontend' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend' / 'static',
]

WSGI_APPLICATION = 'Ambienta.wsgi.application'


# ----------------------------------------------------------------------
# Database (Ajuste Crucial para o Render)
# ----------------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL') or config('DATABASE_URL'),
        conn_max_age=600
    )
}

# ----------------------------------------------------------------------
# Configurações de Autenticação (Redirecionamento)
# ----------------------------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Configurações de segurança para HTTPS/Produção
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
CSRF_TRUSTED_ORIGINS = ['https://ambienta-cnys.onrender.com']


# ----------------------------------------------------------------------
# Static files (Ajuste para Produção no Render)
# ----------------------------------------------------------------------

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ----------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# Configuração de CORS
CORS_ALLOWED_ORIGINS = [
    "https://ambienta-cnys.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True
