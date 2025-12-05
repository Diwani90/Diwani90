"""
===================================
منصة ديواني - Base Settings
Django 5.x Configuration
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
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env file if exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ===================================
# Security Settings
# ===================================
SECRET_KEY = env('SECRET_KEY', default='diwani-dev-secret-key-change-in-production')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# ===================================
# Application Definition
# ===================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # PostGIS support
    'django.contrib.postgres',  # PostgreSQL features
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'django_filters',
    'django_extensions',
    'django_celery_beat',
    'django_celery_results',
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

# ===================================
# Middleware
# ===================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ===================================
# Templates
# ===================================
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
ASGI_APPLICATION = 'config.asgi.application'

# ===================================
# Database - PostgreSQL + PostGIS
# ===================================
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('DB_NAME', default='diwani_db'),
        'USER': env('DB_USER', default='diwani_user'),
        'PASSWORD': env('DB_PASSWORD', default='diwani_secure_pass_2025'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Parse DATABASE_URL if provided
DATABASE_URL = env('DATABASE_URL', default=None)
if DATABASE_URL:
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        engine='django.contrib.gis.db.backends.postgis'
    )

# ===================================
# Cache - Redis
# ===================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'diwani',
    }
}

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ===================================
# Custom User Model
# ===================================
AUTH_USER_MODEL = 'accounts.User'

# ===================================
# Password Validation
# ===================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Use Argon2 for password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# ===================================
# Internationalization
# ===================================
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('ar', 'العربية'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ===================================
# Static & Media Files
# ===================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===================================
# Default Primary Key
# ===================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===================================
# CORS Settings
# ===================================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])
CORS_ALLOW_CREDENTIALS = True

# ===================================
# JWT Settings (Django Ninja JWT)
# ===================================
NINJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ===================================
# Celery Configuration
# ===================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ===================================
# Logging Configuration
# ===================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ===================================
# Diwani Platform Settings
# ===================================
DIWANI_SETTINGS = {
    # General
    'PLATFORM_NAME': 'ديواني',
    'PLATFORM_NAME_EN': 'Diwani',
    'PLATFORM_VERSION': '1.0.0',

    # Location Settings (Saudi Arabia)
    'DEFAULT_COUNTRY': 'SA',
    'DEFAULT_CURRENCY': 'SAR',
    'DEFAULT_CITY': 'Riyadh',
    'DEFAULT_LATITUDE': 24.7136,
    'DEFAULT_LONGITUDE': 46.6753,

    # Delivery Settings
    'MAX_DELIVERY_RADIUS_KM': 50,
    'MIN_ORDER_AMOUNT': 20,
    'FREE_DELIVERY_THRESHOLD': 100,
    'BASE_DELIVERY_FEE': 15,
    'PER_KM_DELIVERY_FEE': 2,

    # Commission Settings
    'PLATFORM_COMMISSION_PERCENT': 15,
    'DRIVER_COMMISSION_PERCENT': 80,

    # OTP Settings
    'OTP_LENGTH': 6,
    'OTP_EXPIRY_MINUTES': 5,
    'OTP_MAX_ATTEMPTS': 3,

    # Upload Limits
    'MAX_IMAGE_SIZE_MB': 5,
    'MAX_DOCUMENT_SIZE_MB': 10,
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/webp'],
}
