"""
تكوين تطبيق التتبع
"""
from django.apps import AppConfig


class TrackingConfig(AppConfig):
    """تكوين تطبيق التتبع"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tracking'
    verbose_name = 'نظام التتبع'

    def ready(self):
        """تهيئة التطبيق عند بدء التشغيل"""
        from . import signals  # noqa: F401
