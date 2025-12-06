"""
تكوين تطبيق الإشعارات
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """تكوين تطبيق الإشعارات"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'نظام الإشعارات'

    def ready(self):
        """تهيئة التطبيق عند بدء التشغيل"""
        from . import signals  # noqa: F401
