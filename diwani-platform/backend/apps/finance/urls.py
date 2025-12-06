"""
مسارات النظام المالي
====================
"""

from django.urls import path

from . import webhooks

app_name = 'finance'

urlpatterns = [
    # Webhooks
    path('tap/', webhooks.tap_webhook, name='tap_webhook'),
    path('accounting/', webhooks.accounting_webhook, name='accounting_webhook'),
]
