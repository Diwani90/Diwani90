"""
تكوين تطبيق المتاجر
"""

from django.apps import AppConfig


class StoresConfig(AppConfig):
    """تكوين تطبيق المتاجر"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.stores'
    verbose_name = 'المتاجر'
