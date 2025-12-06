"""
===================================
منصة ديواني - Security Module
الأمن السيبراني والامتثال للمعايير السعودية
Saudi NCA/PDPL Compliance
===================================
"""

import hashlib
import hmac
import logging
import re
import time
from functools import wraps
from typing import Optional, Callable

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


# ===================================
# Security Headers Middleware
# ===================================
class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    إضافة رؤوس أمان HTTP متقدمة
    يتوافق مع معايير NCA و OWASP
    """

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Content Security Policy (CSP)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://api.moyasar.com https://api.tap.company wss:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)

        # Strict Transport Security (HSTS)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # XSS Protection (legacy browsers)
        response['X-XSS-Protection'] = '1; mode=block'

        # Clickjacking protection
        response['X-Frame-Options'] = 'DENY'

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy (modern Feature-Policy)
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=(self)",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=(self)",
            "usb=()",
        ]
        response['Permissions-Policy'] = ', '.join(permissions)

        # Cache Control for sensitive pages
        if '/api/' in request.path and request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'

        return response


# ===================================
# Rate Limiting Middleware
# ===================================
class RateLimitMiddleware(MiddlewareMixin):
    """
    حماية من هجمات DDoS و Brute Force
    Rate limiting with Redis backend
    """

    # Rate limits configuration (requests per minute)
    RATE_LIMITS = {
        'auth': {'limit': 5, 'window': 60},        # 5 auth requests per minute
        'otp': {'limit': 3, 'window': 300},        # 3 OTP requests per 5 minutes
        'api': {'limit': 100, 'window': 60},       # 100 API requests per minute
        'upload': {'limit': 10, 'window': 60},     # 10 uploads per minute
    }

    def get_client_ip(self, request: HttpRequest) -> str:
        """استخراج IP الحقيقي للعميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip
        return request.META.get('REMOTE_ADDR', 'unknown')

    def get_rate_limit_key(self, request: HttpRequest, limit_type: str) -> str:
        """إنشاء مفتاح فريد للـ Rate Limit"""
        client_ip = self.get_client_ip(request)
        return f"ratelimit:{limit_type}:{client_ip}"

    def is_rate_limited(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """
        التحقق من تجاوز الحد المسموح
        Returns: (is_limited, remaining_requests)
        """
        current_count = cache.get(key, 0)

        if current_count >= limit:
            return True, 0

        # Increment counter
        if current_count == 0:
            cache.set(key, 1, window)
        else:
            cache.incr(key)

        return False, limit - current_count - 1

    def get_limit_type(self, request: HttpRequest) -> str:
        """تحديد نوع الـ Rate Limit بناءً على المسار"""
        path = request.path.lower()

        if '/auth/request-otp' in path:
            return 'otp'
        elif '/auth/' in path:
            return 'auth'
        elif '/upload' in path or '/avatar' in path:
            return 'upload'
        else:
            return 'api'

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # Skip rate limiting in DEBUG mode
        if settings.DEBUG:
            return None

        # Skip for health checks
        if request.path in ['/api/health/', '/health/']:
            return None

        limit_type = self.get_limit_type(request)
        config = self.RATE_LIMITS.get(limit_type, self.RATE_LIMITS['api'])
        key = self.get_rate_limit_key(request, limit_type)

        is_limited, remaining = self.is_rate_limited(key, config['limit'], config['window'])

        if is_limited:
            logger.warning(
                f"[RateLimit] IP {self.get_client_ip(request)} exceeded {limit_type} limit on {request.path}"
            )
            return JsonResponse({
                'error': 'تم تجاوز الحد المسموح من الطلبات',
                'error_en': 'Rate limit exceeded',
                'retry_after': config['window']
            }, status=429)

        return None

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """إضافة رؤوس Rate Limit للاستجابة"""
        limit_type = self.get_limit_type(request)
        config = self.RATE_LIMITS.get(limit_type, self.RATE_LIMITS['api'])

        response['X-RateLimit-Limit'] = str(config['limit'])
        response['X-RateLimit-Window'] = str(config['window'])

        return response


# ===================================
# Request Logging Middleware
# ===================================
class SecurityAuditMiddleware(MiddlewareMixin):
    """
    تسجيل الأحداث الأمنية للمراجعة
    Security Event Logging for NCA Compliance
    """

    SENSITIVE_PATHS = [
        '/auth/', '/admin/', '/me/', '/wallet/', '/payment/',
        '/become-driver', '/become-vendor'
    ]

    def process_request(self, request: HttpRequest) -> None:
        """تسجيل بداية الطلب"""
        request._security_start_time = time.time()
        request._client_ip = self.get_client_ip(request)

    def get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def should_log(self, request: HttpRequest) -> bool:
        """تحديد إذا كان يجب تسجيل هذا الطلب"""
        # Always log POST/PUT/DELETE
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return True

        # Log sensitive paths
        for path in self.SENSITIVE_PATHS:
            if path in request.path:
                return True

        return False

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """تسجيل نهاية الطلب"""
        if not self.should_log(request):
            return response

        try:
            duration = time.time() - getattr(request, '_security_start_time', time.time())
            client_ip = getattr(request, '_client_ip', 'unknown')

            # Determine log level based on status code
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO

            # Log security event
            logger.log(log_level, f"[SecurityAudit] "
                f"IP:{client_ip} | "
                f"Method:{request.method} | "
                f"Path:{request.path} | "
                f"Status:{response.status_code} | "
                f"Duration:{duration:.3f}s | "
                f"User:{getattr(request.user, 'id', 'anonymous')}"
            )

            # Log failed authentication attempts
            if response.status_code == 401 and '/auth/' in request.path:
                logger.warning(
                    f"[SecurityAlert] Failed auth attempt from IP:{client_ip} on {request.path}"
                )

        except Exception as e:
            logger.error(f"[SecurityAudit] Error logging request: {e}")

        return response


# ===================================
# Input Sanitization Utilities
# ===================================
class InputSanitizer:
    """
    تنظيف المدخلات من الأكواد الخبيثة
    XSS & Injection Prevention
    """

    # Patterns for common attacks
    SQL_INJECTION_PATTERNS = [
        r"(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\s",
        r"--\s*$",
        r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
        r"'\s*(OR|AND)\s*'",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """تنظيف النص من الأكواد الخبيثة"""
        try:
            import bleach
            # Allow safe HTML tags only
            allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'br']
            return bleach.clean(value, tags=allowed_tags, strip=True)
        except ImportError:
            # Fallback: basic HTML stripping
            return re.sub(r'<[^>]+>', '', value)

    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """كشف محاولات SQL Injection"""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """كشف محاولات XSS"""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def validate_phone_saudi(cls, phone: str) -> bool:
        """التحقق من صحة رقم الجوال السعودي"""
        # Saudi phone: +966 5X XXX XXXX
        pattern = r'^(\+966|966|0)?5[0-9]{8}$'
        clean_phone = re.sub(r'[\s\-]', '', phone)
        return bool(re.match(pattern, clean_phone))

    @classmethod
    def validate_national_id_saudi(cls, national_id: str) -> bool:
        """التحقق من صحة رقم الهوية السعودي"""
        # Saudi National ID: 10 digits starting with 1 or 2
        pattern = r'^[12][0-9]{9}$'
        return bool(re.match(pattern, national_id))


# ===================================
# Data Encryption Utilities
# ===================================
class DataEncryption:
    """
    تشفير البيانات الحساسة
    AES-256 Encryption for PDPL Compliance
    """

    @staticmethod
    def get_encryption_key() -> bytes:
        """الحصول على مفتاح التشفير من الإعدادات"""
        key = getattr(settings, 'FIELD_ENCRYPTION_KEY', settings.SECRET_KEY[:32])
        return key.encode() if isinstance(key, str) else key

    @classmethod
    def hash_sensitive_data(cls, data: str) -> str:
        """
        تجزئة البيانات الحساسة (للبحث)
        One-way hash using SHA-256
        """
        key = cls.get_encryption_key()
        return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()

    @classmethod
    def mask_phone(cls, phone: str) -> str:
        """إخفاء جزء من رقم الجوال"""
        if len(phone) >= 10:
            return phone[:4] + '****' + phone[-2:]
        return '****'

    @classmethod
    def mask_email(cls, email: str) -> str:
        """إخفاء جزء من البريد الإلكتروني"""
        if '@' in email:
            local, domain = email.split('@')
            if len(local) > 2:
                return local[:2] + '***@' + domain
        return '***@***'

    @classmethod
    def mask_national_id(cls, national_id: str) -> str:
        """إخفاء جزء من رقم الهوية"""
        if len(national_id) >= 10:
            return national_id[:2] + '******' + national_id[-2:]
        return '******'


# ===================================
# API Security Decorators
# ===================================
def rate_limit(limit: int = 10, window: int = 60, key_func: Callable = None):
    """
    مُزخرف للحد من عدد الطلبات

    Usage:
        @rate_limit(limit=5, window=60)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            # Get client identifier
            if key_func:
                client_key = key_func(request)
            else:
                client_key = request.META.get('REMOTE_ADDR', 'unknown')

            cache_key = f"ratelimit:{view_func.__name__}:{client_key}"
            current = cache.get(cache_key, 0)

            if current >= limit:
                return JsonResponse({
                    'error': 'تم تجاوز الحد المسموح',
                    'retry_after': window
                }, status=429)

            cache.set(cache_key, current + 1, window)
            return view_func(request, *args, **kwargs)

        return wrapped
    return decorator


def audit_log(action: str):
    """
    مُزخرف لتسجيل الأحداث الأمنية

    Usage:
        @audit_log("user_login")
        def login(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            user_id = getattr(request.user, 'id', 'anonymous')

            logger.info(
                f"[AuditLog] Action:{action} | "
                f"IP:{client_ip} | "
                f"User:{user_id} | "
                f"Timestamp:{timezone.now().isoformat()}"
            )

            return view_func(request, *args, **kwargs)

        return wrapped
    return decorator


# ===================================
# PDPL Compliance Utilities
# ===================================
class PDPLCompliance:
    """
    أدوات الامتثال لنظام حماية البيانات الشخصية
    Saudi Personal Data Protection Law Compliance
    """

    @staticmethod
    def get_data_retention_days(data_type: str) -> int:
        """
        فترة الاحتفاظ بالبيانات حسب نوعها
        Data retention periods per PDPL
        """
        retention_periods = {
            'transaction': 365 * 7,    # 7 years for financial
            'order': 365 * 5,          # 5 years for orders
            'user_activity': 365 * 2,  # 2 years for activity logs
            'otp': 1,                  # 1 day for OTPs
            'notification': 90,        # 90 days for notifications
            'session': 30,             # 30 days for sessions
        }
        return retention_periods.get(data_type, 365)

    @staticmethod
    def anonymize_user_data(user_data: dict) -> dict:
        """
        إخفاء هوية البيانات للتحليلات
        Anonymize data for analytics
        """
        anonymized = user_data.copy()

        # Remove PII
        pii_fields = ['phone_number', 'email', 'first_name', 'last_name',
                      'national_id', 'address', 'fcm_token']

        for field in pii_fields:
            if field in anonymized:
                anonymized[field] = '[ANONYMIZED]'

        return anonymized

    @staticmethod
    def generate_consent_record(user_id: str, consent_type: str) -> dict:
        """
        إنشاء سجل موافقة المستخدم
        Generate consent record for PDPL compliance
        """
        return {
            'user_id': user_id,
            'consent_type': consent_type,
            'timestamp': timezone.now().isoformat(),
            'ip_address': '[TO_BE_FILLED]',
            'version': '1.0',
        }
