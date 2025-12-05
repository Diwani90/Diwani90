"""
===================================
منصة ديواني - ASGI Configuration
WebSocket & Async Support
===================================
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# For WebSocket support (will be configured later)
application = django_asgi_app
