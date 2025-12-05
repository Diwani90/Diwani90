"""
===================================
منصة ديواني - Accounts App Config
===================================
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'إدارة المستخدمين'

    def ready(self):
        # Import signals when app is ready
        try:
            import apps.accounts.signals  # noqa
        except ImportError:
            pass
