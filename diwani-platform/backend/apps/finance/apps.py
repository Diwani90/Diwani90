"""
تكوين تطبيق المالية
"""
from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """تكوين تطبيق المالية"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finance'
    verbose_name = 'النظام المالي'

    def ready(self):
        """تهيئة التطبيق عند بدء التشغيل"""
        from . import signals  # noqa: F401

        # ربط إشارات الطلبات
        try:
            signals.connect_order_signals()
        except Exception:
            pass  # الطلبات قد لا تكون متاحة بعد
