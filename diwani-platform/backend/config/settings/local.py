"""
إعدادات التطوير المحلي
======================

للاستخدام في بيئة التطوير
"""

from .base import *

# ===================================
# Debug Settings
# ===================================
DEBUG = True
ALLOWED_HOSTS = ['*']

# ===================================
# Database - SQLite for local dev
# ===================================
# يمكن استخدام SQLite للتطوير السريع أو PostgreSQL
import os
import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # استخدام PostgreSQL محلياً
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': os.environ.get('DB_NAME', 'diwani_db'),
            'USER': os.environ.get('DB_USER', 'diwani_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'diwani_secure_pass_2025'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# ===================================
# Cache - Redis or Local Memory
# ===================================
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

# ===================================
# Email - Console Backend
# ===================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===================================
# Static & Media
# ===================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===================================
# CORS - Allow All for Development
# ===================================
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ===================================
# Debug Toolbar (optional)
# ===================================
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# ===================================
# Logging
# ===================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
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
# Celery
# ===================================
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = False  # Set to True for synchronous testing

# ===================================
# Elasticsearch - Optional in Dev
# ===================================
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.environ.get('ELASTICSEARCH_HOSTS', 'http://localhost:9200'),
    },
}
ELASTICSEARCH_DSL_AUTOSYNC = os.environ.get('ELASTICSEARCH_ENABLED', 'False').lower() == 'true'

# ===================================
# SMS & Notifications - Test Mode
# ===================================
SMS_CONFIG = {
    'ENABLED': True,
    'TEST_MODE': True,  # لا يرسل SMS فعلي
    'PROVIDER': 'unifonic',
}

FCM_CONFIG = {
    'ENABLED': True,
    'TEST_MODE': True,  # لا يرسل إشعارات فعلية
}

APNS_CONFIG = {
    'ENABLED': True,
    'TEST_MODE': True,
}

# ===================================
# Payment - Test Mode
# ===================================
TAP_PAYMENT_CONFIG = {
    'TEST_MODE': True,
    'PUBLIC_KEY': os.environ.get('TAP_PUBLIC_KEY', 'pk_test_xxx'),
    'SECRET_KEY': os.environ.get('TAP_SECRET_KEY', 'sk_test_xxx'),
}
