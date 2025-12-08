"""
===================================
منصة ديواني - Audit Logging System
نظام تسجيل التدقيق للعمليات الحساسة
===================================

يسجل:
- المعاملات المالية
- تغييرات المستخدمين
- عمليات Admin
- محاولات الدخول الفاشلة
- تغييرات البيانات الحساسة
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """أنواع العمليات"""
    # CRUD
    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'

    # Authentication
    LOGIN = 'login'
    LOGIN_FAILED = 'login_failed'
    LOGOUT = 'logout'
    PASSWORD_CHANGE = 'password_change'
    PASSWORD_RESET = 'password_reset'
    OTP_VERIFIED = 'otp_verified'
    OTP_FAILED = 'otp_failed'
    TWO_FA_ENABLED = '2fa_enabled'
    TWO_FA_DISABLED = '2fa_disabled'

    # Financial
    PAYMENT_INITIATED = 'payment_initiated'
    PAYMENT_COMPLETED = 'payment_completed'
    PAYMENT_FAILED = 'payment_failed'
    REFUND_INITIATED = 'refund_initiated'
    REFUND_COMPLETED = 'refund_completed'
    PAYOUT_INITIATED = 'payout_initiated'
    PAYOUT_COMPLETED = 'payout_completed'
    WALLET_CREDIT = 'wallet_credit'
    WALLET_DEBIT = 'wallet_debit'

    # Orders
    ORDER_CREATED = 'order_created'
    ORDER_CANCELLED = 'order_cancelled'
    ORDER_COMPLETED = 'order_completed'
    ORDER_REFUNDED = 'order_refunded'

    # Admin
    ADMIN_ACCESS = 'admin_access'
    ADMIN_EXPORT = 'admin_export'
    ADMIN_BULK_ACTION = 'admin_bulk_action'

    # Data
    DATA_EXPORT = 'data_export'
    DATA_IMPORT = 'data_import'
    SENSITIVE_VIEW = 'sensitive_view'

    # System
    CONFIG_CHANGE = 'config_change'
    API_KEY_CREATED = 'api_key_created'
    API_KEY_REVOKED = 'api_key_revoked'


class AuditSeverity(Enum):
    """مستويات الخطورة"""
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'


class AuditLog(models.Model):
    """
    نموذج سجل التدقيق

    يخزن جميع العمليات الحساسة مع التفاصيل الكاملة
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # المستخدم
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=50, null=True, blank=True)  # customer, vendor, admin

    # العملية
    action = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(max_length=20, default='info')
    status = models.CharField(max_length=20, default='success')  # success, failed

    # الكائن المتأثر
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    object_repr = models.CharField(max_length=500, null=True, blank=True)

    # التفاصيل
    changes = models.JSONField(null=True, blank=True)  # {field: {old, new}}
    extra_data = models.JSONField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)

    # معلومات الطلب
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    endpoint = models.CharField(max_length=500, null=True, blank=True)
    http_method = models.CharField(max_length=10, null=True, blank=True)

    # معلومات مالية (للمعاملات)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='SAR')
    transaction_ref = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['object_id', 'content_type']),
            models.Index(fields=['severity', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.action} by {self.username or 'system'}"


class AuditLogManager:
    """
    مدير سجلات التدقيق

    يوفر واجهة موحدة لتسجيل الأحداث
    """

    @staticmethod
    def log(
        action: Union[AuditAction, str],
        user=None,
        obj=None,
        changes: Optional[Dict] = None,
        extra_data: Optional[Dict] = None,
        request=None,
        severity: AuditSeverity = AuditSeverity.INFO,
        status: str = 'success',
        reason: Optional[str] = None,
        amount: Optional[Decimal] = None,
        transaction_ref: Optional[str] = None,
    ) -> AuditLog:
        """
        تسجيل حدث في سجل التدقيق

        Args:
            action: نوع العملية
            user: المستخدم (اختياري)
            obj: الكائن المتأثر (اختياري)
            changes: التغييرات {field: {old, new}}
            extra_data: بيانات إضافية
            request: HTTP request
            severity: مستوى الخطورة
            status: حالة العملية
            reason: سبب العملية
            amount: المبلغ (للمعاملات المالية)
            transaction_ref: مرجع المعاملة

        Returns:
            AuditLog instance
        """
        # تحويل الـ action إذا كان Enum
        action_str = action.value if isinstance(action, AuditAction) else action
        severity_str = severity.value if isinstance(severity, AuditSeverity) else severity

        # استخراج معلومات المستخدم
        user_id = None
        username = None
        user_type = None

        if user:
            user_id = getattr(user, 'id', None)
            username = getattr(user, 'username', None) or getattr(user, 'phone', None)
            if hasattr(user, 'user_type'):
                user_type = user.user_type
            elif hasattr(user, 'is_superuser') and user.is_superuser:
                user_type = 'admin'

        # استخراج معلومات الكائن
        content_type = None
        object_id = None
        object_repr = None

        if obj:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = str(getattr(obj, 'pk', getattr(obj, 'id', None)))
            object_repr = str(obj)[:500]

        # استخراج معلومات الطلب
        ip_address = None
        user_agent = None
        request_id = None
        endpoint = None
        http_method = None

        if request:
            ip_address = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
            request_id = request.META.get('HTTP_X_REQUEST_ID', '')
            endpoint = request.path
            http_method = request.method

        # تنظيف البيانات الحساسة
        if changes:
            changes = _sanitize_sensitive_data(changes)
        if extra_data:
            extra_data = _sanitize_sensitive_data(extra_data)

        # إنشاء السجل
        audit_log = AuditLog.objects.create(
            action=action_str,
            severity=severity_str,
            status=status,
            user_id=user_id,
            username=username,
            user_type=user_type,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            extra_data=extra_data,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            endpoint=endpoint,
            http_method=http_method,
            amount=amount,
            transaction_ref=transaction_ref,
        )

        # تسجيل في logs أيضاً (للمراقبة الفورية)
        _log_to_logger(audit_log)

        return audit_log

    @staticmethod
    def log_financial(
        action: Union[AuditAction, str],
        amount: Decimal,
        user=None,
        transaction_ref: Optional[str] = None,
        extra_data: Optional[Dict] = None,
        request=None,
        status: str = 'success',
    ) -> AuditLog:
        """تسجيل معاملة مالية"""
        return AuditLogManager.log(
            action=action,
            user=user,
            extra_data=extra_data,
            request=request,
            severity=AuditSeverity.CRITICAL,
            status=status,
            amount=amount,
            transaction_ref=transaction_ref,
        )

    @staticmethod
    def log_auth(
        action: Union[AuditAction, str],
        user=None,
        request=None,
        status: str = 'success',
        reason: Optional[str] = None,
    ) -> AuditLog:
        """تسجيل حدث مصادقة"""
        severity = AuditSeverity.WARNING if status == 'failed' else AuditSeverity.INFO
        return AuditLogManager.log(
            action=action,
            user=user,
            request=request,
            severity=severity,
            status=status,
            reason=reason,
        )

    @staticmethod
    def log_admin(
        action: Union[AuditAction, str],
        user,
        obj=None,
        changes: Optional[Dict] = None,
        request=None,
    ) -> AuditLog:
        """تسجيل عملية Admin"""
        return AuditLogManager.log(
            action=action,
            user=user,
            obj=obj,
            changes=changes,
            request=request,
            severity=AuditSeverity.WARNING,
        )


# ===================================
# Helper Functions
# ===================================
def _get_client_ip(request) -> Optional[str]:
    """استخراج IP العميل"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _sanitize_sensitive_data(data: Dict) -> Dict:
    """إزالة البيانات الحساسة"""
    sensitive_fields = [
        'password', 'secret', 'token', 'api_key', 'private_key',
        'card_number', 'cvv', 'pin', 'otp', 'verification_code',
        'access_token', 'refresh_token', 'session_key',
    ]

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sf in key_lower for sf in sensitive_fields):
            sanitized[key] = '[REDACTED]'
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_sensitive_data(value)
        else:
            sanitized[key] = value

    return sanitized


def _log_to_logger(audit_log: AuditLog):
    """تسجيل في Python logger"""
    level = {
        'info': logging.INFO,
        'warning': logging.WARNING,
        'critical': logging.CRITICAL,
    }.get(audit_log.severity, logging.INFO)

    message = (
        f"AUDIT: {audit_log.action} | "
        f"user={audit_log.username} | "
        f"object={audit_log.object_repr} | "
        f"status={audit_log.status}"
    )

    if audit_log.amount:
        message += f" | amount={audit_log.amount} {audit_log.currency}"

    logger.log(level, message, extra={
        'audit_id': str(audit_log.id),
        'action': audit_log.action,
        'user_id': audit_log.user_id,
        'ip_address': audit_log.ip_address,
    })


# ===================================
# Decorators
# ===================================
def audit_action(
    action: Union[AuditAction, str],
    severity: AuditSeverity = AuditSeverity.INFO,
    include_args: bool = False,
):
    """
    Decorator لتسجيل العمليات تلقائياً

    الاستخدام:
        @audit_action(AuditAction.PAYMENT_INITIATED)
        def process_payment(request, order_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # استخراج request و user
            request = None
            user = None

            for arg in args:
                if hasattr(arg, 'META'):
                    request = arg
                    user = getattr(request, 'user', None)
                    break

            extra_data = {}
            if include_args:
                extra_data['function_args'] = {
                    'args': [str(a) for a in args[1:]],  # Skip request
                    'kwargs': {k: str(v) for k, v in kwargs.items()},
                }

            try:
                result = func(*args, **kwargs)

                AuditLogManager.log(
                    action=action,
                    user=user,
                    request=request,
                    severity=severity,
                    status='success',
                    extra_data=extra_data,
                )

                return result

            except Exception as e:
                extra_data['error'] = str(e)
                AuditLogManager.log(
                    action=action,
                    user=user,
                    request=request,
                    severity=AuditSeverity.CRITICAL,
                    status='failed',
                    extra_data=extra_data,
                    reason=str(e),
                )
                raise

        return wrapper
    return decorator


# ===================================
# Model Audit Mixin
# ===================================
class AuditModelMixin(models.Model):
    """
    Mixin لتتبع التغييرات على النماذج

    الاستخدام:
        class MyModel(AuditModelMixin, models.Model):
            audit_fields = ['name', 'status', 'amount']
            ...
    """

    # الحقول المراد تتبعها (يمكن تعديلها في النموذج الفرعي)
    audit_fields: List[str] = []
    audit_exclude: List[str] = ['updated_at', 'modified_at']

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_values = self._get_tracked_values()

    def _get_tracked_values(self) -> Dict:
        """الحصول على القيم الحالية للحقول المتتبعة"""
        values = {}
        fields_to_track = self.audit_fields or [
            f.name for f in self._meta.fields
            if f.name not in self.audit_exclude
        ]

        for field_name in fields_to_track:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                # تحويل القيم غير القابلة للـ JSON
                if isinstance(value, Decimal):
                    value = str(value)
                elif hasattr(value, 'pk'):
                    value = str(value.pk)
                values[field_name] = value

        return values

    def get_changes(self) -> Dict:
        """الحصول على التغييرات منذ آخر حفظ"""
        current = self._get_tracked_values()
        changes = {}

        for field, new_value in current.items():
            old_value = self._original_values.get(field)
            if old_value != new_value:
                changes[field] = {
                    'old': old_value,
                    'new': new_value,
                }

        return changes

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        changes = {} if is_new else self.get_changes()

        super().save(*args, **kwargs)

        # تحديث القيم الأصلية
        self._original_values = self._get_tracked_values()

        # يمكن تسجيل التغييرات هنا إذا لزم الأمر
        return changes


# Singleton manager
audit_log = AuditLogManager()
