import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

LOGIN_URL = 'accounts:login'
# --- CORREÇÃO DO CAMINHO BASE (BASE_DIR) ---
# Sobe três níveis para apontar para a raiz do projeto (e não a pasta 'backend/Ambienta')
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-unsafe-secret-key')
DEBUG = True  # Forçado para True em desenvolvimento
# DEBUG = config('DEBUG', default=False, cast=bool)  # Comentado temporariamente

# --- 1. CONFIGURAÇÕES DE HOSTS E SEGURANÇA ---

# LENDO APENAS UMA VARIÁVEL: Django_Allowed_Hosts
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='*', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Configurações Condicionais (DEBUG vs. Produção)
if DEBUG:
    # Adiciona hosts de desenvolvimento
    ALLOWED_HOSTS += ['localhost', '127.0.0.1', '0.0.0.0', '127.0.0.1:8000', '127.0.0.1:8080']

    # CORREÇÃO AQUI: Adicionar explicitamente o domínio do Render para testes (DEBUG)
    ALLOWED_HOSTS.append('ambienta-83aj.onrender.com')

    # Em debug, desativamos COMPLETAMENTE redirecionamentos e cookies seguros
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    
    # Desabilitar proxy SSL para desenvolvimento local
    SECURE_PROXY_SSL_HEADER = None
    
    # Forçar HTTP em desenvolvimento
    SECURE_SCHEMA = 'http'
    
    # Desabilitar redirecionamento para HTTPS permanentemente
    SECURE_REDIRECT_EXEMPT = [r'^.*$']  # Todas as URLs são isentas de redirecionamento HTTPS
    
    # NOVA: Desabilitar HSTS completamente em desenvolvimento
    SECURE_HSTS_SECONDS = None
    
    # NOVA: Garantir que não há upgrade para HTTPS
    USE_TLS = False
else:
    # --- AJUSTE PARA O RENDER (INJEÇÃO FORÇADA DO DOMÍNIO) ---
    RENDER_EXTERNAL_HOSTNAME = 'ambienta-83aj.onrender.com'

    # 1. Adiciona o domínio do Render a ALLOWED_HOSTS (Se não estiver lá)
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

    # 2. Adiciona o domínio seguro ao CSRF_TRUSTED_ORIGINS
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

    # Em produção, ativamos redirecionamentos, cookies seguros e HSTS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # Configuração para ambientes que usam proxy SSL (como Render) - APENAS EM PRODUÇÃO
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- 2. APPS E MIDDLEWARE ---

INSTALLED_APPS = [
    # Core Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceiros
    'rest_framework',
    'rest_framework.authtoken',
    'crispy_forms',
    'crispy_bootstrap5',

    # Allauth/dj-rest-auth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Apps locais
    'home',
    'accounts',
    'dashboard',
    'sensors',
    'ml_models',
]
SITE_ID = 1

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',  # Removido temporariamente para teste
    # 'whitenoise.middleware.WhiteNoiseMiddleware',  # Removido temporariamente
    'Ambienta.middleware.ForceHTTPMiddleware',  # Middleware customizado para forçar HTTP
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'Ambienta.urls'

# --- 3. TEMPLATES, WSGI/ASGI E DATABASE ---

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # DIRS agora aponta para /src/frontend/templates/
        'DIRS': [BASE_DIR / 'frontend' / 'templates'],
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
ASGI_APPLICATION = 'Ambienta.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- 4. AUTHENTICATION (ALLAUTH & REST_FRAMEWORK) ---

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Configurações atualizadas do allauth (corrigindo deprecações)
ACCOUNT_EMAIL_VERIFICATION = config('ACCOUNT_EMAIL_VERIFICATION', default='optional')
ACCOUNT_LOGIN_METHODS = {'username', 'email'}  # Substitui ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']  # Substitui ACCOUNT_EMAIL_REQUIRED

# URLs de redirecionamento
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny' if DEBUG else 'rest_framework.permissions.IsAuthenticated',
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- 5. INTERNACIONALIZAÇÃO E ARQUIVOS (STATIC/MEDIA) ---

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# STATIC_ROOT aponta para /src/staticfiles/
STATIC_ROOT = BASE_DIR / 'staticfiles'

# CORREÇÃO MANTIDA: Define o caminho diretamente
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'static',
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    # MUDANÇA TEMPORÁRIA: Use StaticFilesStorage em vez de CompressedManifestStaticFilesStorage
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL', default='redis://127.0.0.1:6379/0')],
        },
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'