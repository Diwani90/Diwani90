"""
===================================
منصة ديواني - Simple Development Settings
For local testing without PostGIS
===================================
"""

import os
from pathlib import Path
from datetime import timedelta

import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, True),
)

# Read .env file if exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Security
SECRET_KEY = env('SECRET_KEY', default='diwani-dev-secret-key-for-testing-only')
DEBUG = True
ALLOWED_HOSTS = ['*']

# Application Definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'django_filters',
    'django_extensions',
    'django_celery_beat',
    'django_celery_results',
    'debug_toolbar',
    'silk',
]

LOCAL_APPS = [
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.stores.apps.StoresConfig',
    'apps.products.apps.ProductsConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.delivery.apps.DeliveryConfig',
    'apps.payments.apps.PaymentsConfig',
    'apps.notifications.apps.NotificationsConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database - PostgreSQL with PostGIS
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'diwani_db',
        'USER': 'diwani_user',
        'PASSWORD': 'diwani_pass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# Celery
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# JWT Settings
NINJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Diwani Settings
DIWANI_SETTINGS = {
    'PLATFORM_NAME': 'ديواني',
    'DEFAULT_COUNTRY': 'SA',
    'DEFAULT_CURRENCY': 'SAR',
    'OTP_LENGTH': 6,
    'OTP_EXPIRY_MINUTES': 5,
    'MAX_IMAGE_SIZE_MB': 5,
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/webp'],
    'UNIFONIC': {
        'APP_SID': '',
        'SENDER_ID': 'DIWANI',
    },
    'FIREBASE': {
        'SERVER_KEY': '',
    },
    'MOYASAR': {
        'API_KEY': '',
        'SECRET_KEY': '',
        'SANDBOX': True,
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
