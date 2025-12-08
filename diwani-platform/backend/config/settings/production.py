"""
===================================
منصة ديواني - Production Settings
إعدادات الإنتاج المتقدمة
===================================
"""

import os

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401, F403


# ===================================
# Sentry Filter Functions (must be defined before init)
# ===================================
def filter_sentry_events(event, hint):
    """
    فلترة الأحداث قبل إرسالها لـ Sentry
    """
    # تجاهل أخطاء 4xx
    if 'exception' in event:
        exc_info = hint.get('exc_info')
        if exc_info:
            exc_type = exc_info[0]
            exc_name = exc_type.__name__ if exc_type else ''

            # تجاهل أخطاء الـ 404
            if exc_name in ['Http404', 'NotFound', 'ObjectDoesNotExist']:
                return None

            # تجاهل أخطاء التحقق
            if exc_name in ['ValidationError', 'PermissionDenied']:
                return None

    # إزالة البيانات الحساسة
    if 'request' in event:
        request_data = event['request']

        # إزالة headers الحساسة
        if 'headers' in request_data:
            sensitive_headers = ['Authorization', 'Cookie', 'X-API-Key']
            for header in sensitive_headers:
                if header in request_data['headers']:
                    request_data['headers'][header] = '[Filtered]'

        # إزالة بيانات الدفع
        if 'data' in request_data and isinstance(request_data['data'], dict):
            sensitive_fields = ['card_number', 'cvv', 'password', 'secret_key']
            for field in sensitive_fields:
                if field in request_data['data']:
                    request_data['data'][field] = '[Filtered]'

    return event


def filter_sentry_transactions(event, hint):
    """
    فلترة transactions قبل إرسالها
    """
    # تجاهل health checks
    if 'transaction' in event:
        transaction = event['transaction']
        if '/health' in transaction or '/metrics' in transaction:
            return None

    return event


# ===================================
# Production Security Settings
# ===================================
DEBUG = False
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='').split(',')

# Security Headers
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=86400)  # 24 hours

# CSRF Security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    f"https://{host.strip()}" for host in ALLOWED_HOSTS if host.strip()
]

# ===================================
# Sentry Initialization
# ===================================
SENTRY_DSN = env('SENTRY_DSN', default=None)

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env('SENTRY_ENVIRONMENT', default='production'),
        release=env('SENTRY_RELEASE', default='diwani@1.0.0'),

        integrations=[
            DjangoIntegration(
                transaction_style="url",
                middleware_spans=True,
                signals_spans=True,
                cache_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
            RedisIntegration(),
            LoggingIntegration(
                level=None,
                event_level=None,
            ),
        ],

        # Performance Monitoring
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
        profiles_sample_rate=env.float('SENTRY_PROFILES_SAMPLE_RATE', default=0.1),

        # Options
        send_default_pii=False,
        attach_stacktrace=True,
        request_bodies='medium',
        max_breadcrumbs=50,
        enable_tracing=True,

        # Filtering
        before_send=filter_sentry_events,
        before_send_transaction=filter_sentry_transactions,

        # Ignore specific errors
        ignore_errors=[
            'django.security.DisallowedHost',
            'django.core.exceptions.PermissionDenied',
            'rest_framework.exceptions.NotAuthenticated',
            'rest_framework.exceptions.AuthenticationFailed',
        ],
    )

# ===================================
# Database Configuration
# ===================================
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('DATABASE_HOST', default='db'),
        'PORT': env('DATABASE_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 seconds
        },
        'ATOMIC_REQUESTS': True,
    }
}

# ===================================
# Cache Configuration (Redis)
# ===================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 50,
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'diwani_prod',
        'TIMEOUT': env.int('CACHE_TTL', default=300),
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL').replace('/0', '/2'),  # Use DB 2 for sessions
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'diwani_session',
        'TIMEOUT': 86400,
    },
}

# Session Backend
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# ===================================
# Celery Configuration
# ===================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_TASK_ALWAYS_EAGER = False

# Celery Performance
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Celery Beat
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ===================================
# Elasticsearch Configuration
# ===================================
ELASTICSEARCH_DSL = {
    'hosts': env('ELASTICSEARCH_HOSTS', default='http://elasticsearch:9200'),
    'http_auth': ('elastic', env('ELASTICSEARCH_PASSWORD', default='')),
    'timeout': 30,
    'retry_on_timeout': True,
    'max_retries': 3,
}
ELASTICSEARCH_DSL_AUTOSYNC = True
ELASTICSEARCH_ENABLED = True

# ===================================
# Static & Media Files
# ===================================
# Use S3 in production
USE_S3 = env.bool('USE_S3', default=False)

if USE_S3:
    # AWS S3 Settings
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='me-south-1')
    AWS_S3_CUSTOM_DOMAIN = env('AWS_S3_CUSTOM_DOMAIN', default=None)
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_QUERYSTRING_AUTH = False

    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/' if AWS_S3_CUSTOM_DOMAIN else f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/static/'

    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/' if AWS_S3_CUSTOM_DOMAIN else f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/'
else:
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'static'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ===================================
# Email Configuration
# ===================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='apikey')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@diwani.sa')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ===================================
# Logging Configuration (Production)
# ===================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'root': {
        'handlers': ['console', 'sentry'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'sentry', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.finance': {
            'handlers': ['console', 'sentry'],
            'level': 'WARNING',  # أهمية عالية للمعاملات المالية
            'propagate': False,
        },
    },
}

# ===================================
# Payment Configuration (Production)
# ===================================
TAP_PAYMENT_CONFIG = {
    'TEST_MODE': False,
    'PUBLIC_KEY': env('TAP_PUBLIC_KEY'),
    'SECRET_KEY': env('TAP_SECRET_KEY'),
    'WEBHOOK_SECRET': env('TAP_WEBHOOK_SECRET', default=''),
}

# ===================================
# ZATCA Configuration
# ===================================
ZATCA_CONFIG = {
    'ENVIRONMENT': 'production',
    'CERTIFICATE_PATH': env('ZATCA_CERTIFICATE_PATH', default=''),
    'PRIVATE_KEY_PATH': env('ZATCA_PRIVATE_KEY_PATH', default=''),
    'COMPLIANCE_REQUEST_ID': env('ZATCA_COMPLIANCE_REQUEST_ID', default=''),
    'PIH': env('ZATCA_PIH', default=''),  # Previous Invoice Hash
}

# ===================================
# Rate Limiting (Production)
# ===================================
RATE_LIMIT_CONFIG = {
    'ENABLED': True,
    'DEFAULT_LIMIT': '100/minute',
    'AUTH_LIMIT': '5/minute',
    'SEARCH_LIMIT': '60/minute',
    'PAYMENT_LIMIT': '10/minute',
    'WEBHOOK_LIMIT': '200/minute',
    'STORAGE': 'redis',
    'REDIS_URL': env('REDIS_URL'),
}

# ===================================
# Admin Security
# ===================================
ADMINS = [
    ('Diwani Admin', env('ADMIN_EMAIL', default='admin@diwani.sa')),
]

# 2FA for Admin
OTP_TOTP_ISSUER = 'Diwani Platform'
