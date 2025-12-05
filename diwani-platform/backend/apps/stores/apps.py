"""
===================================
منصة ديواني - Stores App Config
===================================
"""

from django.apps import AppConfig


class StoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.stores'
    verbose_name = 'إدارة المتاجر'

    def ready(self):
        try:
            import apps.stores.signals  # noqa
        except ImportError:
            pass
