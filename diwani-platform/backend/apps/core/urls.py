"""
===================================
منصة ديواني - Core URLs
Health check and system endpoints
===================================
"""

from django.urls import path
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import time


def health_check(request):
    """
    API health check endpoint.
    Checks database and cache connectivity.
    """
    health = {
        'status': 'healthy',
        'platform': 'Diwani',
        'version': '1.0.0',
        'checks': {}
    }

    # Check database
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        health['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health['status'] = 'unhealthy'

    # Check cache (Redis)
    try:
        start = time.time()
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health['checks']['cache'] = {
                'status': 'healthy',
                'response_time_ms': round((time.time() - start) * 1000, 2)
            }
        else:
            health['checks']['cache'] = {
                'status': 'unhealthy',
                'error': 'Cache read/write failed'
            }
            health['status'] = 'degraded'
    except Exception as e:
        health['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        # Cache failure is degraded, not unhealthy
        if health['status'] == 'healthy':
            health['status'] = 'degraded'

    # Return appropriate status code
    status_code = 200 if health['status'] == 'healthy' else (
        503 if health['status'] == 'unhealthy' else 200
    )

    return JsonResponse(health, status=status_code)


def readiness_check(request):
    """
    Readiness check for Kubernetes/Docker.
    Returns 200 if the application is ready to receive traffic.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'ready': True})
    except Exception:
        return JsonResponse({'ready': False}, status=503)


def liveness_check(request):
    """
    Liveness check for Kubernetes/Docker.
    Returns 200 if the application is alive.
    """
    return JsonResponse({'alive': True})


app_name = 'core'

urlpatterns = [
    path('', health_check, name='health_check'),
    path('ready/', readiness_check, name='readiness_check'),
    path('live/', liveness_check, name='liveness_check'),
]
