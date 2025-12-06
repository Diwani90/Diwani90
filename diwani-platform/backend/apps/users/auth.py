"""
نظام المصادقة JWT
=================

Django Ninja Authentication classes
"""

from typing import Optional, Any

from django.http import HttpRequest
from ninja.security import HttpBearer

from .services import auth_service


class JWTAuth(HttpBearer):
    """
    مصادقة JWT للـ API

    تُستخدم لحماية الـ endpoints التي تتطلب تسجيل دخول
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        """التحقق من الرمز"""
        user = auth_service.verify_token(token)

        if user:
            # تخزين معلومات إضافية في الطلب
            request.user = user
            return user

        return None


class OptionalJWTAuth(HttpBearer):
    """
    مصادقة JWT اختيارية

    تسمح بالوصول بدون رمز، لكن تُعيد المستخدم إذا كان موجوداً
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        """التحقق من الرمز (اختياري)"""
        if not token:
            return None

        user = auth_service.verify_token(token)

        if user:
            request.user = user
            return user

        return None


class AdminJWTAuth(JWTAuth):
    """
    مصادقة JWT للمسؤولين فقط
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        """التحقق من الرمز والصلاحيات"""
        user = super().authenticate(request, token)

        if user and (user.is_admin_user or user.is_staff):
            return user

        return None


class VendorJWTAuth(JWTAuth):
    """
    مصادقة JWT للتجار فقط
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        """التحقق من الرمز ونوع المستخدم"""
        user = super().authenticate(request, token)

        if user and user.is_vendor:
            return user

        return None


class DriverJWTAuth(JWTAuth):
    """
    مصادقة JWT للسائقين فقط
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        """التحقق من الرمز ونوع المستخدم"""
        user = super().authenticate(request, token)

        if user and user.is_driver:
            return user

        return None


def get_current_user(request: HttpRequest) -> Optional[Any]:
    """
    الحصول على المستخدم الحالي من الطلب

    يُستخدم في الـ views التي تتعامل مع المصادقة يدوياً
    """
    # أولاً، التحقق من وجود المستخدم في الطلب
    if hasattr(request, 'auth') and request.auth:
        return request.auth

    # ثانياً، محاولة استخراج الرمز من الهيدر
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return auth_service.verify_token(token)

    return None


def get_token_from_request(request: HttpRequest) -> Optional[str]:
    """استخراج الرمز من الطلب"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if auth_header.startswith('Bearer '):
        return auth_header[7:]

    return None
