"""
تكوين تطبيق الطلبات
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'الطلبات'

    def ready(self):
        """تهيئة التطبيق"""
        try:
            from . import signals  # noqa
        except ImportError:
            pass
