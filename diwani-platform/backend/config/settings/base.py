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
# CRITICAL: SECRET_KEY must be set in environment, no default for production safety
SECRET_KEY = env('SECRET_KEY')
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
    'channels',  # WebSockets
]

LOCAL_APPS = [
    'apps.core.apps.CoreConfig',  # النواة والـ Middleware
    'apps.users.apps.UsersConfig',  # نظام المستخدمين والمصادقة
    'apps.stores.apps.StoresConfig',  # المتاجر
    'apps.products.apps.ProductsConfig',  # المنتجات
    'apps.orders.apps.OrdersConfig',  # الطلبات
    'apps.finance.apps.FinanceConfig',  # النظام المالي
    'apps.notifications.apps.NotificationsConfig',  # الإشعارات
    'apps.search.apps.SearchConfig',  # البحث المتقدم
    'apps.realtime.apps.RealtimeConfig',  # Real-time & WebSockets
    'apps.chat.apps.ChatConfig',  # المحادثات
    'apps.tracking.apps.TrackingConfig',  # نظام التتبع والتوصيل
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ===================================
# Middleware
# ===================================
MIDDLEWARE = [
    # Security & Performance (First Layer)
    'apps.core.middleware.RequestIDMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
    'apps.core.middleware.RateLimitMiddleware',
    'apps.core.middleware.RequestLoggingMiddleware',
    # Django Core
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
    # Error Handling (Last Layer)
    'apps.core.middleware.JSONErrorMiddleware',
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
AUTH_USER_MODEL = 'users.User'

# JWT Secret Key (for users.services)
JWT_SECRET_KEY = env('JWT_SECRET_KEY', default=SECRET_KEY)

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

# Where collectstatic puts all static files (must NOT be in STATICFILES_DIRS)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Source directories for static files (before collection)
# Note: STATIC_ROOT (staticfiles) != static directory, so no conflict
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

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
# Elasticsearch Configuration
# البحث المتقدم
# ===================================
ELASTICSEARCH_ENABLED = env.bool('ELASTICSEARCH_ENABLED', default=True)

ELASTICSEARCH_DSL = {
    'hosts': env('ELASTICSEARCH_HOSTS', default='http://localhost:9200'),
    'timeout': 30,
    'retry_on_timeout': True,
    'max_retries': 3,
}

# Indexes settings
ELASTICSEARCH_INDEX_SETTINGS = {
    'products': 'diwani_products',
    'stores': 'diwani_stores',
    'categories': 'diwani_categories',
    'vendors': 'diwani_vendors',
}

# Search settings
SEARCH_SETTINGS = {
    'MIN_SEARCH_LENGTH': 2,
    'MAX_RESULTS': 1000,
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
    'CACHE_TIMEOUT': 300,  # 5 minutes
    'SUGGESTION_LIMIT': 10,
    'FUZZY_ENABLED': True,
    'HIGHLIGHT_ENABLED': True,
}

# ===================================
# Django Channels Configuration
# Real-time WebSockets
# ===================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL', default='redis://localhost:6379/0')],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# Real-time Settings
REALTIME_SETTINGS = {
    # Connection
    'HEARTBEAT_INTERVAL': 30,  # seconds
    'CONNECTION_TIMEOUT': 120,  # seconds
    'MAX_CONNECTIONS_PER_USER': 5,

    # Rate Limiting
    'MAX_MESSAGES_PER_MINUTE': 100,
    'BURST_SIZE': 20,

    # Backpressure
    'QUEUE_SIZE': 1000,
    'HIGH_WATERMARK': 800,
    'LOW_WATERMARK': 200,

    # Presence
    'ONLINE_THRESHOLD': 30,  # seconds
    'AWAY_THRESHOLD': 300,  # 5 minutes
    'OFFLINE_THRESHOLD': 600,  # 10 minutes
}

# Chat Settings
CHAT_SETTINGS = {
    'MAX_MESSAGE_LENGTH': 4000,
    'MAX_ATTACHMENTS_PER_MESSAGE': 10,
    'MAX_ATTACHMENT_SIZE_MB': 25,
    'MESSAGE_EDIT_TIMEOUT_MINUTES': 5,
    'TYPING_INDICATOR_TIMEOUT': 10,  # seconds
    'ENCRYPTION_ENABLED': True,
}

# Tracking Settings
TRACKING_SETTINGS = {
    'LOCATION_UPDATE_INTERVAL': 5,  # seconds
    'MAX_HISTORY_POINTS': 1000,
    'GEOFENCE_RADIUS_DEFAULT': 100,  # meters
    'ETA_RECALCULATE_INTERVAL': 30,  # seconds
}

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

    # SMS Provider (Unifonic)
    'UNIFONIC': {
        'APP_SID': env('UNIFONIC_APP_SID', default=''),
        'SENDER_ID': env('UNIFONIC_SENDER_ID', default='DIWANI'),
    },

    # Push Notifications (Firebase)
    'FIREBASE': {
        'SERVER_KEY': env('FIREBASE_SERVER_KEY', default=''),
        'PROJECT_ID': env('FIREBASE_PROJECT_ID', default=''),
    },

    # Payment Gateways
    'MOYASAR': {
        'API_KEY': env('MOYASAR_API_KEY', default=''),
        'SECRET_KEY': env('MOYASAR_SECRET_KEY', default=''),
        'PUBLISHABLE_KEY': env('MOYASAR_PUBLISHABLE_KEY', default=''),
        'SANDBOX': env.bool('MOYASAR_SANDBOX', default=True),
    },

    'TAP': {
        'SECRET_KEY': env('TAP_SECRET_KEY', default=''),
        'PUBLISHABLE_KEY': env('TAP_PUBLISHABLE_KEY', default=''),
        'SANDBOX': env.bool('TAP_SANDBOX', default=True),
    },

    'TABBY': {
        'API_KEY': env('TABBY_API_KEY', default=''),
        'MERCHANT_CODE': env('TABBY_MERCHANT_CODE', default=''),
        'SANDBOX': env.bool('TABBY_SANDBOX', default=True),
    },

    'TAMARA': {
        'API_TOKEN': env('TAMARA_API_TOKEN', default=''),
        'MERCHANT_ID': env('TAMARA_MERCHANT_ID', default=''),
        'SANDBOX': env.bool('TAMARA_SANDBOX', default=True),
    },
}

# ===================================
# Advanced Security Settings
# Saudi NCA / PDPL Compliance
# ===================================

# Django Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# HTTPS Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session Security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# CSRF Security
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])

# Password Validation (Strong)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password Hashing (Argon2)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Field-Level Encryption Key
# CRITICAL: Must be exactly 32 characters for AES-256
# Generate with: python -c "import secrets; print(secrets.token_hex(16))"
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY')

# Rate Limiting Settings
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_FAIL_OPEN = False

# Security Audit Logging
SECURITY_AUDIT_ENABLED = True
SECURITY_LOG_FAILED_AUTH = True
SECURITY_LOG_SENSITIVE_OPERATIONS = True

# Data Retention (PDPL Compliance)
DATA_RETENTION_DAYS = {
    'otp': 1,
    'session': 30,
    'notification': 90,
    'user_activity': 365 * 2,
    'order': 365 * 5,
    'transaction': 365 * 7,
}

# IP Geolocation (for Saudi-only features)
ALLOWED_COUNTRIES = ['SA', 'AE', 'KW', 'BH', 'QA', 'OM']  # GCC countries

# ===================================
# Finance & Payments Configuration
# تكامل Tap Connect وبرامج المحاسبة
# ===================================

# Tax Rate (Saudi VAT)
TAX_RATE = 0.15  # 15%

# Tap Connect (Marketplace Payments)
TAP_ENVIRONMENT = env('TAP_ENVIRONMENT', default='sandbox')
TAP_SECRET_KEY = env('TAP_SECRET_KEY', default='')
TAP_PUBLIC_KEY = env('TAP_PUBLIC_KEY', default='')
TAP_WEBHOOK_SECRET = env('TAP_WEBHOOK_SECRET', default='')

# Accounting Integration (Qoyod/Dafater)
ACCOUNTING_PROVIDER = env('ACCOUNTING_PROVIDER', default='qoyod')

# Qoyod
QOYOD_API_KEY = env('QOYOD_API_KEY', default='')
QOYOD_ORGANIZATION_ID = env('QOYOD_ORGANIZATION_ID', default='')

# Dafater (Alternative)
DAFATER_API_KEY = env('DAFATER_API_KEY', default='')

# Finance Team Notifications
FINANCE_TEAM_EMAILS = env.list('FINANCE_TEAM_EMAILS', default=[])

# Commission Settings
FINANCE_SETTINGS = {
    # Default Commission Rates
    'DEFAULT_VENDOR_COMMISSION': 0.05,  # 5%
    'DEFAULT_DRIVER_COMMISSION': 0.15,  # 15%

    # Volume Discounts
    'VOLUME_DISCOUNT_TIERS': [
        (50000, 0.04),   # 4% for orders >= 50,000 SAR
        (100000, 0.03),  # 3% for orders >= 100,000 SAR
    ],

    # Payout Settings
    'MIN_PAYOUT_AMOUNT': 100,  # Minimum withdrawal
    'PAYOUT_HOLD_DAYS': 3,     # Days before funds are available

    # Reconciliation
    'RECONCILIATION_TIME': '02:00',  # Run at 2 AM daily
    'RECONCILIATION_TOLERANCE': 0.01,  # 1 halala tolerance

    # Invoice Settings
    'INVOICE_PREFIX': 'INV',
    'AUTO_SYNC_TO_ACCOUNTING': True,

    # Ledger
    'VERIFY_LEDGER_INTEGRITY': True,
    'LEDGER_RETENTION_YEARS': 7,  # ZATCA requirement
}
