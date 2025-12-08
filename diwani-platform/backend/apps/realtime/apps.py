"""
تكوين تطبيق Real-time
"""
from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    """تكوين تطبيق الاتصالات الفورية"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.realtime'
    verbose_name = 'نظام الاتصالات الفورية'

    def ready(self):
        """تهيئة التطبيق عند بدء التشغيل"""
        # تسجيل معالجات الإشارات
        from . import signals  # noqa: F401
