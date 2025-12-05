"""
===================================
منصة ديواني - Development Settings
===================================
"""

from .base import *

# ===================================
# Debug Mode
# ===================================
DEBUG = True
ALLOWED_HOSTS = ['*']

# ===================================
# Development Apps
# ===================================
INSTALLED_APPS += [
    'debug_toolbar',
    'silk',
]

# ===================================
# Development Middleware
# ===================================
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'silk.middleware.SilkyMiddleware',
] + MIDDLEWARE

# ===================================
# Debug Toolbar Settings
# ===================================
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'INTERCEPT_REDIRECTS': False,
}

# ===================================
# Silk Profiler Settings
# ===================================
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_MAX_REQUEST_BODY_SIZE = -1
SILKY_MAX_RESPONSE_BODY_SIZE = 1024

# ===================================
# CORS - Allow all in development
# ===================================
CORS_ALLOW_ALL_ORIGINS = True

# ===================================
# Email Backend - Console
# ===================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===================================
# Logging - More verbose
# ===================================
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

# ===================================
# Cache - Use local memory in dev
# ===================================
# Uncomment to use local memory cache instead of Redis
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }

# ===================================
# JWT - Longer tokens for dev
# ===================================
from datetime import timedelta
NINJA_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(days=1)
NINJA_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=30)

print("🚀 Diwani Platform - Development Mode Activated")
