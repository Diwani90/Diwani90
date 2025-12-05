"""
===================================
منصة ديواني - Core URLs
Health check and system endpoints
===================================
"""

from django.urls import path
from django.http import JsonResponse


def health_check(request):
    """API health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'platform': 'Diwani',
        'version': '1.0.0'
    })


app_name = 'core'

urlpatterns = [
    path('', health_check, name='health_check'),
]
