"""
WSGI config for Diwani Platform

يوفر تكوين WSGI لـ HTTP requests (Django)
للاستخدام مع Gunicorn
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

application = get_wsgi_application()
