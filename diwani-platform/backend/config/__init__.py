"""
Diwani Platform - Django Configuration Package
"""

# استيراد تطبيق Celery عند بدء Django
# هذا يضمن أن التطبيق يُحمل دائماً مع Django
from .celery import app as celery_app

__all__ = ('celery_app',)
