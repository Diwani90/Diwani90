"""
===================================
منصة ديواني - Production Settings
===================================
"""

from .base import *

# ===================================
# Security - Production
# ===================================
DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# HTTPS Settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS Settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ===================================
# CORS - Strict in production
# ===================================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')

# ===================================
# Email - Production SMTP
# ===================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@diwani.sa')

# ===================================
# AWS S3 for Media Storage
# ===================================
USE_S3 = env.bool('USE_S3', default=False)

if USE_S3:
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='me-south-1')  # Bahrain
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False

    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# ===================================
# Sentry Error Tracking
# ===================================
SENTRY_DSN = env('SENTRY_DSN', default=None)

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# ===================================
# Logging - Production
# ===================================
LOGGING['handlers']['file'] = {
    'level': 'ERROR',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': '/var/log/diwani/django.log',
    'maxBytes': 1024 * 1024 * 10,  # 10 MB
    'backupCount': 10,
    'formatter': 'json',
}

LOGGING['root']['handlers'] = ['console', 'file']
LOGGING['root']['level'] = 'WARNING'

print("🔒 Diwani Platform - Production Mode")
