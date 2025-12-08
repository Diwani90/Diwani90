"""
تكوين تطبيق المستخدمين
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'المستخدمون'

    def ready(self):
        """تهيئة التطبيق"""
        # استيراد الإشارات إذا وجدت
        try:
            from . import signals  # noqa
        except ImportError:
            pass
