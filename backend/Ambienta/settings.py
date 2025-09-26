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
]


# CONFIGURAÇÃO OBRIGATÓRIA PARA O DJANGO-CRISPY-FORMS:
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


MIDDLEWARE = [
    # 💡 AJUSTE: WhiteNoise para servir arquivos estáticos em produção (Render)
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
        # Lê a DATABASE_URL do ambiente (Render) ou usa a configuração local/padrão
        default=os.environ.get('DATABASE_URL') or config('DATABASE_URL'), 
        conn_max_age=600  # Mantém conexões abertas
    )
}

# ----------------------------------------------------------------------
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
# ... (permanece o mesmo)
# ----------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# ----------------------------------------------------------------------
# Static files (Ajuste para Produção no Render)
# ----------------------------------------------------------------------

STATIC_URL = 'static/'

# Local onde o Render/collectstatic irá coletar todos os arquivos estáticos:
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 
# ----------------------------------------------------------------------


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuração do Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
