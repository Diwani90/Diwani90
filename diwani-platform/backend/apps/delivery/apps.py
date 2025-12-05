"""
===================================
منصة ديواني - Delivery App Config
===================================
"""

from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.delivery'
    verbose_name = 'إدارة التوصيل'
