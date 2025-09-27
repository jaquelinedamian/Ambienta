"""
Django settings for Ambienta project.

Configuração principal ajustada para uso com variáveis de ambiente (decouple)
e deploy em serviços como o Render (dj_database_url, whitenoise).
"""
import os
import dj_database_url
from decouple import config, Csv
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# 💡 AJUSTE: Otimizado para ler 'DEBUG' com cast=bool
DEBUG = config('DEBUG', default=False, cast=bool)

# 💡 AJUSTE: Usando 'Csv()' do decouple para parse mais limpo e seguro de listas,
#           especialmente para 'ALLOWED_HOSTS' e 'CSRF_TRUSTED_ORIGINS'
# ALLOWED_HOSTS: Lê a variável DJANGO_ALLOWED_HOSTS (ex: do Render), com fallback.
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='', cast=Csv())
if DEBUG:
    # Adiciona 'localhost' e '127.0.0.1' automaticamente em desenvolvimento
    ALLOWED_HOSTS += ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition

INSTALLED_APPS = [
    # 💡 AJUSTE: Core Apps do Django primeiro por convenção
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'crispy_forms',
    'crispy_bootstrap5',


    # Local apps
    'home',
    'accounts',
    'dashboard',
    'sensors',
]


# CONFIGURAÇÃO OBRIGATÓRIA PARA O DJANGO-CRISPY-FORMS:
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 💡 WhiteNoise deve vir logo após SecurityMiddleware em produção
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Ambienta.urls'

# ----------------------------------------------------------------------
# Templates
# ----------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # DIRS para templates de projeto (no seu caso, 'frontend/templates')
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

WSGI_APPLICATION = 'Ambienta.wsgi.application'


# ----------------------------------------------------------------------
# Database (Ajuste Crucial para o Render/Produção)
# ----------------------------------------------------------------------
# 💡 AJUSTE: Simplificando a leitura. dj_database_url.config() já prioriza
#           a variável de ambiente DATABASE_URL.
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3'), # Fallback seguro ou dev local
        conn_max_age=600, # Mantém conexões abertas
        ssl_require=not DEBUG, # Habilita SSL em produção (Render, etc.)
    )
}

# ----------------------------------------------------------------------
# Password validation
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
# Static files (Configuração para Produção com WhiteNoise)
# ----------------------------------------------------------------------
STATIC_URL = 'static/'

# Local onde o 'collectstatic' irá coletar todos os arquivos estáticos:
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Diretórios adicionais para arquivos estáticos (no seu caso, 'frontend/static'):
STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend' / 'static',
]

# 💡 AJUSTE: Habilita compressão e cache para arquivos estáticos em produção (WhiteNoise)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
# ----------------------------------------------------------------------

# 💡 AJUSTE: Configuração opcional de HTTPS/CSRF para produção no Render
# Garante que os cookies de sessão e CSRF só sejam enviados via HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
# Confiança em origens para CSRF (útil se estiver rodando em subdomínio ou Render)
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuração do Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        # 💡 AJUSTE: Permite acesso irrestrito se DEBUG=True (ajuda no desenvolvimento local)
        #            Mantém IsAuthenticated em produção
        'rest_framework.permissions.AllowAny' if DEBUG else 'rest_framework.permissions.IsAuthenticated',
    ),
}