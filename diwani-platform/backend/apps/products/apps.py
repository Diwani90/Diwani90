"""
تكوين تطبيق المنتجات
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """تكوين تطبيق المنتجات"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = 'المنتجات'

    def ready(self):
        """تهيئة التطبيق"""
        from . import signals  # noqa: F401
