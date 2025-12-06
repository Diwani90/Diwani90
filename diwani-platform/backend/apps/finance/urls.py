"""
مسارات النظام المالي
====================
"""

from django.urls import path

from . import webhooks

app_name = 'finance'

urlpatterns = [
    # Webhooks
    path('webhooks/tap/', webhooks.tap_webhook, name='tap_webhook'),
    path('webhooks/accounting/', webhooks.accounting_webhook, name='accounting_webhook'),
]
