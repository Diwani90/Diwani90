"""
===================================
منصة ديواني - Products App Config
===================================
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = 'إدارة المنتجات'

    def ready(self):
        try:
            import apps.products.signals  # noqa
        except ImportError:
            pass
