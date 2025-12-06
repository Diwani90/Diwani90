"""
تكوين تطبيق النواة
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'النواة'

    def ready(self):
        """تهيئة التطبيق"""
        pass
