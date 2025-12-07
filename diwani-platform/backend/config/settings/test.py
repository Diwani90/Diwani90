"""
إعدادات الاختبارات
==================

للاستخدام مع pytest و Django test runner
"""

from .base import *

# ===================================
# Test Settings
# ===================================
DEBUG = False
TESTING = True

# ===================================
# Secret Key for Tests
# ===================================
SECRET_KEY = 'test-secret-key-not-for-production-use-only-for-testing'

# ===================================
# Database - SQLite for Speed
# ===================================
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': ':memory:',
    }
}

# For SQLite with SpatiaLite
SPATIALITE_LIBRARY_PATH = 'mod_spatialite'

# ===================================
# Password Hashers - Faster for Tests
# ===================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ===================================
# Cache - Local Memory
# ===================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ===================================
# Email - In-Memory
# ===================================
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ===================================
# Celery - Synchronous
# ===================================
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ===================================
# Static Files
# ===================================
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ===================================
# Media Files
# ===================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'test_media'

# ===================================
# Disable Migrations for Faster Tests
# ===================================
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# ===================================
# Logging - Minimal
# ===================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}

# ===================================
# External Services - Test Mode
# ===================================
SMS_CONFIG = {
    'ENABLED': True,
    'TEST_MODE': True,
    'PROVIDER': 'test',
}

FCM_CONFIG = {
    'ENABLED': True,
    'TEST_MODE': True,
}

APNS_CONFIG = {
    'ENABLED': True,
    'TEST_MODE': True,
}

TAP_PAYMENT_CONFIG = {
    'TEST_MODE': True,
    'PUBLIC_KEY': 'pk_test_xxx',
    'SECRET_KEY': 'sk_test_xxx',
}

# ===================================
# Elasticsearch - Disabled
# ===================================
ELASTICSEARCH_DSL_AUTOSYNC = False

# ===================================
# Security - Relaxed for Tests
# ===================================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ===================================
# Channels - In-Memory
# ===================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# ===================================
# JWT - Short Expiry for Tests
# ===================================
from datetime import timedelta

NINJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=10),
}
