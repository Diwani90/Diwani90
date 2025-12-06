"""
تكوين تطبيق المحادثات
"""
from django.apps import AppConfig


class ChatConfig(AppConfig):
    """تكوين تطبيق المحادثات"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'
    verbose_name = 'نظام المحادثات'

    def ready(self):
        """تهيئة التطبيق عند بدء التشغيل"""
        from . import signals  # noqa: F401
