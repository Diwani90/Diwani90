"""
===================================
منصة ديواني - Search App Config
===================================
"""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'
    verbose_name = 'البحث المتقدم'

    def ready(self):
        """تحميل الإشارات عند بدء التطبيق"""
        try:
            import apps.search.signals  # noqa
        except ImportError:
            pass
