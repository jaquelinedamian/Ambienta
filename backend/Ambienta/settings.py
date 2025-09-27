import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(file).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-unsafe-secret-key')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='', cast=Csv())
if DEBUG:
ALLOWED_HOSTS += ['localhost', '127.0.0.1', '0.0.0.0']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
if DEBUG:
# Exemplo: adicione o host/porta do frontend em dev, se houver
# CSRF_TRUSTED_ORIGINS += ['http://localhost:3000', 'http://127.0.0.1:3000']
pass
if not DEBUG:
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

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

# Allauth/dj-rest-auth (ajuste conforme seu uso)
'django.contrib.sites',
'allauth',
'allauth.account',
'allauth.socialaccount',
# 'dj_rest_auth',
# 'dj_rest_auth.registration',

# Apps locais
'home',
'accounts',
'dashboard',
'sensors',
]
SITE_ID = 1

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
MIDDLEWARE = [
'django.middleware.security.SecurityMiddleware',
'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise logo após SecurityMiddleware
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
# frontend/ está no mesmo nível do manage.py, conforme sua captura
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
ASGI_APPLICATION = 'Ambienta.asgi.application'  # Deixe habilitado se for usar Channels/WebSockets

DATABASES = {
'default': dj_database_url.config(
default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
conn_max_age=600,
ssl_require=not DEBUG,
)
}

AUTHENTICATION_BACKENDS = (
'django.contrib.auth.backends.ModelBackend',
'allauth.account.auth_backends.AuthenticationBackend',
)
ACCOUNT_EMAIL_VERIFICATION = config('ACCOUNT_EMAIL_VERIFICATION', default='optional')
ACCOUNT_AUTHENTICATION_METHOD = config('ACCOUNT_AUTHENTICATION_METHOD', default='username_email')
ACCOUNT_EMAIL_REQUIRED = config('ACCOUNT_EMAIL_REQUIRED', default=True, cast=bool)

REST_FRAMEWORK = {
'DEFAULT_AUTHENTICATION_CLASSES': (
# Se usar JWT, troque por 'rest_framework_simplejwt.authentication.JWTAuthentication',
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

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
front_static_path = BASE_DIR / 'frontend' / 'static'
if front_static_path.exists():
STATICFILES_DIRS = [front_static_path]
else:
STATICFILES_DIRS = []
STORAGES = {
"staticfiles": {
"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
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
