"""
===================================
منصة ديواني - Orders App Config
===================================
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'إدارة الطلبات'

    def ready(self):
        try:
            import apps.orders.signals  # noqa
        except ImportError:
            pass
