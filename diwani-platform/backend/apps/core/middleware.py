"""
Middleware المشترك
==================

Rate Limiting, Logging, Security
"""

import time
import hashlib
import json
import logging
from typing import Optional, Callable, Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


# =============================================
# Rate Limiting Middleware
# =============================================

class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate Limiting Middleware

    يحد من عدد الطلبات لكل مستخدم/IP
    """

    # الإعدادات الافتراضية
    DEFAULT_RATE_LIMIT = 100  # طلب
    DEFAULT_RATE_PERIOD = 60  # ثانية
    BURST_LIMIT = 10  # طلبات متتالية سريعة

    # حدود مخصصة حسب المسار
    PATH_LIMITS = {
        '/api/v1/auth/login': {'limit': 5, 'period': 60},
        '/api/v1/auth/register': {'limit': 3, 'period': 60},
        '/api/v1/auth/verify': {'limit': 10, 'period': 60},
        '/api/v1/search': {'limit': 30, 'period': 60},
    }

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """معالجة الطلب الوارد"""
        # تجاوز في وضع التطوير
        if settings.DEBUG and not getattr(settings, 'ENABLE_RATE_LIMIT_DEBUG', False):
            return None

        # الحصول على المعرف
        client_id = self._get_client_identifier(request)

        # الحصول على الحدود
        path = request.path
        limits = self._get_path_limits(path)

        rate_limit = limits.get('limit', self.DEFAULT_RATE_LIMIT)
        rate_period = limits.get('period', self.DEFAULT_RATE_PERIOD)

        # التحقق من Rate Limit
        is_limited, remaining, reset_time = self._check_rate_limit(
            client_id, rate_limit, rate_period
        )

        # إضافة headers
        request.rate_limit_remaining = remaining
        request.rate_limit_reset = reset_time

        if is_limited:
            return self._rate_limit_response(remaining, reset_time)

        return None

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """إضافة headers للاستجابة"""
        if hasattr(request, 'rate_limit_remaining'):
            response['X-RateLimit-Remaining'] = request.rate_limit_remaining
            response['X-RateLimit-Reset'] = request.rate_limit_reset

        return response

    def _get_client_identifier(self, request: HttpRequest) -> str:
        """الحصول على معرف العميل"""
        # إذا كان مصادقاً، استخدم user_id
        if hasattr(request, 'auth') and request.auth:
            return f'user:{request.auth.id}'

        # وإلا استخدم IP
        ip = self._get_client_ip(request)
        return f'ip:{ip}'

    def _get_client_ip(self, request: HttpRequest) -> str:
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    def _get_path_limits(self, path: str) -> Dict[str, int]:
        """الحصول على حدود المسار"""
        for pattern, limits in self.PATH_LIMITS.items():
            if path.startswith(pattern):
                return limits
        return {}

    def _check_rate_limit(
        self,
        client_id: str,
        limit: int,
        period: int
    ) -> tuple:
        """
        التحقق من Rate Limit

        يستخدم خوارزمية Sliding Window
        """
        now = time.time()
        key = f'rate_limit:{client_id}'

        # الحصول على السجل الحالي
        record = cache.get(key) or {'timestamps': [], 'count': 0}
        timestamps = record['timestamps']

        # إزالة الطلبات القديمة
        window_start = now - period
        timestamps = [t for t in timestamps if t > window_start]

        # التحقق من الحد
        if len(timestamps) >= limit:
            # محدود
            reset_time = int(timestamps[0] + period)
            return True, 0, reset_time

        # إضافة الطلب الجديد
        timestamps.append(now)
        record['timestamps'] = timestamps
        record['count'] = len(timestamps)

        # حفظ السجل
        cache.set(key, record, timeout=period + 10)

        remaining = limit - len(timestamps)
        reset_time = int(now + period)

        return False, remaining, reset_time

    def _rate_limit_response(self, remaining: int, reset_time: int) -> JsonResponse:
        """استجابة Rate Limit"""
        return JsonResponse({
            'error': 'تم تجاوز حد الطلبات',
            'code': 'rate_limit_exceeded',
            'retry_after': reset_time - int(time.time()),
        }, status=429, headers={
            'Retry-After': str(reset_time - int(time.time())),
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(reset_time),
        })


# =============================================
# Request Logging Middleware
# =============================================

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    تسجيل الطلبات

    يسجل جميع طلبات API للمراقبة والتحليل
    """

    # المسارات المستثناة من التسجيل
    EXCLUDED_PATHS = [
        '/health',
        '/static/',
        '/media/',
        '/favicon.ico',
    ]

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> None:
        """تسجيل بداية الطلب"""
        request.start_time = time.time()

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """تسجيل نهاية الطلب"""
        # تجاوز المسارات المستثناة
        if self._should_skip(request.path):
            return response

        # حساب وقت الاستجابة
        duration = 0
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000  # بالميلي ثانية

        # تسجيل الطلب
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': round(duration, 2),
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        }

        # إضافة معرف المستخدم إذا كان مصادقاً
        if hasattr(request, 'auth') and request.auth:
            log_data['user_id'] = str(request.auth.id)

        # تسجيل الأخطاء بمستوى أعلى
        if response.status_code >= 500:
            logger.error(f'API Error: {json.dumps(log_data)}')
        elif response.status_code >= 400:
            logger.warning(f'API Warning: {json.dumps(log_data)}')
        else:
            logger.info(f'API Request: {json.dumps(log_data)}')

        # إضافة معرف الطلب للاستجابة
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id

        return response

    def _should_skip(self, path: str) -> bool:
        """هل يجب تجاوز المسار؟"""
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return True
        return False

    def _get_client_ip(self, request: HttpRequest) -> str:
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


# =============================================
# Security Headers Middleware
# =============================================

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    إضافة headers الأمان

    يضيف headers الأمان الضرورية لجميع الاستجابات
    """

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """إضافة headers الأمان"""
        # منع embedding في iframes
        response['X-Frame-Options'] = 'DENY'

        # منع MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # تفعيل XSS protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy (للـ API)
        # استثناء صفحات التوثيق (Swagger UI) من CSP الصارم
        if request.path.startswith('/api/') and not request.path.endswith(('/docs', '/openapi.json')):
            response['Content-Security-Policy'] = "default-src 'none'"
        elif request.path.endswith('/docs'):
            # CSP مرن لـ Swagger UI
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://django-ninja.dev; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'"
            )

        # HSTS (في الإنتاج فقط)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response


# =============================================
# Request ID Middleware
# =============================================

class RequestIDMiddleware(MiddlewareMixin):
    """
    إضافة معرف فريد لكل طلب

    يساعد في التتبع والتحليل
    """

    def process_request(self, request: HttpRequest) -> None:
        """إضافة معرف الطلب"""
        import uuid

        # التحقق من وجود معرف في الهيدر
        request_id = request.META.get('HTTP_X_REQUEST_ID')

        if not request_id:
            request_id = str(uuid.uuid4())

        request.request_id = request_id

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """إضافة المعرف للاستجابة"""
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id

        return response


# =============================================
# JSON Error Middleware
# =============================================

class JSONErrorMiddleware(MiddlewareMixin):
    """
    تحويل الأخطاء إلى JSON

    يضمن أن جميع أخطاء API تُرجع كـ JSON
    """

    def process_exception(
        self,
        request: HttpRequest,
        exception: Exception
    ) -> Optional[JsonResponse]:
        """معالجة الاستثناءات"""
        # فقط لمسارات API
        if not request.path.startswith('/api/'):
            return None

        # تسجيل الخطأ
        logger.exception(f'Unhandled exception: {exception}')

        # في وضع التطوير، أظهر التفاصيل
        if settings.DEBUG:
            return JsonResponse({
                'error': str(exception),
                'type': type(exception).__name__,
            }, status=500)

        # في الإنتاج، رسالة عامة
        return JsonResponse({
            'error': 'حدث خطأ في الخادم',
            'code': 'internal_server_error',
        }, status=500)


# =============================================
# CORS Middleware (إذا لم يُستخدم django-cors-headers)
# =============================================

class CORSMiddleware(MiddlewareMixin):
    """
    معالجة CORS

    يسمح بالطلبات من النطاقات المسموح بها
    """

    ALLOWED_ORIGINS = getattr(settings, 'CORS_ALLOWED_ORIGINS', [
        'http://localhost:3000',
        'http://localhost:8080',
        'https://diwani.sa',
        'https://app.diwani.sa',
    ])

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """معالجة طلبات preflight"""
        if request.method == 'OPTIONS':
            response = HttpResponse()
            self._add_cors_headers(request, response)
            return response
        return None

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """إضافة CORS headers"""
        self._add_cors_headers(request, response)
        return response

    def _add_cors_headers(
        self,
        request: HttpRequest,
        response: HttpResponse
    ):
        """إضافة headers CORS"""
        origin = request.META.get('HTTP_ORIGIN', '')

        if origin in self.ALLOWED_ORIGINS or settings.DEBUG:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Accept-Language, Content-Language, Content-Type, '
                'Authorization, X-Request-ID, X-Device-ID'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
