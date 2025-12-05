"""
===================================
منصة ديواني - Notification Models
نماذج الإشعارات والرسائل
===================================
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings


# ===================================
# Notification Template Model
# ===================================
class NotificationTemplate(models.Model):
    """Templates for notifications."""

    class TemplateType(models.TextChoices):
        ORDER_PLACED = 'order_placed', _('طلب جديد')
        ORDER_CONFIRMED = 'order_confirmed', _('تأكيد الطلب')
        ORDER_PREPARING = 'order_preparing', _('جاري التحضير')
        ORDER_READY = 'order_ready', _('الطلب جاهز')
        ORDER_ON_WAY = 'order_on_way', _('في الطريق')
        ORDER_DELIVERED = 'order_delivered', _('تم التوصيل')
        ORDER_CANCELLED = 'order_cancelled', _('إلغاء الطلب')
        PAYMENT_SUCCESS = 'payment_success', _('نجاح الدفع')
        PAYMENT_FAILED = 'payment_failed', _('فشل الدفع')
        REFUND_PROCESSED = 'refund_processed', _('تم الاسترداد')
        PROMO_CODE = 'promo_code', _('كود خصم')
        NEW_STORE = 'new_store', _('متجر جديد')
        REVIEW_REMINDER = 'review_reminder', _('تذكير بالتقييم')
        WALLET_CREDIT = 'wallet_credit', _('إضافة للمحفظة')
        DRIVER_ASSIGNED = 'driver_assigned', _('تعيين السائق')
        GENERAL = 'general', _('عام')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    template_type = models.CharField(
        _('نوع القالب'),
        max_length=30,
        choices=TemplateType.choices,
        unique=True
    )

    # Arabic content
    title_ar = models.CharField(_('العنوان بالعربية'), max_length=200)
    body_ar = models.TextField(_('المحتوى بالعربية'))

    # English content
    title_en = models.CharField(_('العنوان بالإنجليزية'), max_length=200)
    body_en = models.TextField(_('المحتوى بالإنجليزية'))

    # Push notification settings
    is_push_enabled = models.BooleanField(_('إشعار فوري'), default=True)
    is_sms_enabled = models.BooleanField(_('رسالة SMS'), default=False)
    is_email_enabled = models.BooleanField(_('بريد إلكتروني'), default=False)

    # Icon and action
    icon = models.CharField(_('الأيقونة'), max_length=50, blank=True)
    action_url = models.CharField(_('رابط الإجراء'), max_length=255, blank=True)

    is_active = models.BooleanField(_('نشط'), default=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('قالب إشعار')
        verbose_name_plural = _('قوالب الإشعارات')

    def __str__(self):
        return f"{self.template_type} - {self.title_ar}"

    def render(self, context: dict, language: str = 'ar') -> dict:
        """Render template with context variables."""
        if language == 'ar':
            title = self.title_ar
            body = self.body_ar
        else:
            title = self.title_en
            body = self.body_en

        # Replace placeholders
        for key, value in context.items():
            title = title.replace(f'{{{{{key}}}}}', str(value))
            body = body.replace(f'{{{{{key}}}}}', str(value))

        return {
            'title': title,
            'body': body,
            'icon': self.icon,
            'action_url': self.action_url
        }


# ===================================
# Notification Model
# ===================================
class Notification(models.Model):
    """User notifications."""

    class NotificationType(models.TextChoices):
        ORDER = 'order', _('طلب')
        PAYMENT = 'payment', _('دفع')
        PROMO = 'promo', _('عرض')
        SYSTEM = 'system', _('نظام')
        CHAT = 'chat', _('محادثة')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('المستخدم')
    )

    # Content
    title = models.CharField(_('العنوان'), max_length=200)
    body = models.TextField(_('المحتوى'))

    notification_type = models.CharField(
        _('نوع الإشعار'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )

    # Reference to related object
    reference_type = models.CharField(_('نوع المرجع'), max_length=50, blank=True)
    reference_id = models.UUIDField(_('معرف المرجع'), null=True, blank=True)

    # Image
    image_url = models.URLField(_('صورة'), blank=True)

    # Action
    action_url = models.CharField(_('رابط الإجراء'), max_length=255, blank=True)
    action_data = models.JSONField(_('بيانات الإجراء'), default=dict, blank=True)

    # Status
    is_read = models.BooleanField(_('مقروء'), default=False)
    read_at = models.DateTimeField(_('وقت القراءة'), null=True, blank=True)

    # Push status
    push_sent = models.BooleanField(_('تم إرسال Push'), default=False)
    push_sent_at = models.DateTimeField(_('وقت إرسال Push'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type']),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# ===================================
# SMS Log Model
# ===================================
class SMSLog(models.Model):
    """Log of sent SMS messages."""

    class SMSStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        SENT = 'sent', _('تم الإرسال')
        DELIVERED = 'delivered', _('تم التسليم')
        FAILED = 'failed', _('فشل')

    class SMSProvider(models.TextChoices):
        UNIFONIC = 'unifonic', _('يونيفونك')
        MSEGAT = 'msegat', _('مسجات')
        TWILIO = 'twilio', _('تويليو')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipient
    phone_number = models.CharField(_('رقم الجوال'), max_length=15)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_logs',
        verbose_name=_('المستخدم')
    )

    # Content
    message = models.TextField(_('الرسالة'))
    message_type = models.CharField(_('نوع الرسالة'), max_length=50, blank=True)

    # Provider
    provider = models.CharField(
        _('المزود'),
        max_length=20,
        choices=SMSProvider.choices,
        default=SMSProvider.UNIFONIC
    )

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=SMSStatus.choices,
        default=SMSStatus.PENDING
    )

    # Provider response
    provider_message_id = models.CharField(_('معرف الرسالة'), max_length=100, blank=True)
    provider_response = models.JSONField(_('استجابة المزود'), default=dict, blank=True)
    error_message = models.TextField(_('رسالة الخطأ'), blank=True)

    # Cost
    cost = models.DecimalField(_('التكلفة'), max_digits=6, decimal_places=4, default=0)

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    sent_at = models.DateTimeField(_('وقت الإرسال'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('وقت التسليم'), null=True, blank=True)

    class Meta:
        verbose_name = _('سجل SMS')
        verbose_name_plural = _('سجلات SMS')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {self.status}"


# ===================================
# Email Log Model
# ===================================
class EmailLog(models.Model):
    """Log of sent emails."""

    class EmailStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        SENT = 'sent', _('تم الإرسال')
        DELIVERED = 'delivered', _('تم التسليم')
        OPENED = 'opened', _('تم الفتح')
        CLICKED = 'clicked', _('تم النقر')
        BOUNCED = 'bounced', _('مرتجع')
        FAILED = 'failed', _('فشل')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipient
    email = models.EmailField(_('البريد الإلكتروني'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs',
        verbose_name=_('المستخدم')
    )

    # Content
    subject = models.CharField(_('الموضوع'), max_length=200)
    body_html = models.TextField(_('المحتوى HTML'))
    body_text = models.TextField(_('المحتوى النصي'), blank=True)
    email_type = models.CharField(_('نوع البريد'), max_length=50, blank=True)

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING
    )

    # Provider response
    provider_message_id = models.CharField(_('معرف الرسالة'), max_length=100, blank=True)
    error_message = models.TextField(_('رسالة الخطأ'), blank=True)

    # Tracking
    opened_at = models.DateTimeField(_('وقت الفتح'), null=True, blank=True)
    clicked_at = models.DateTimeField(_('وقت النقر'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    sent_at = models.DateTimeField(_('وقت الإرسال'), null=True, blank=True)

    class Meta:
        verbose_name = _('سجل بريد')
        verbose_name_plural = _('سجلات البريد')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.subject}"


# ===================================
# Push Notification Log Model
# ===================================
class PushLog(models.Model):
    """Log of sent push notifications."""

    class PushStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        SENT = 'sent', _('تم الإرسال')
        DELIVERED = 'delivered', _('تم التسليم')
        OPENED = 'opened', _('تم الفتح')
        FAILED = 'failed', _('فشل')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipient
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_logs',
        verbose_name=_('المستخدم')
    )

    fcm_token = models.TextField(_('رمز FCM'))

    # Content
    title = models.CharField(_('العنوان'), max_length=200)
    body = models.TextField(_('المحتوى'))
    data = models.JSONField(_('البيانات'), default=dict, blank=True)

    # Related notification
    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='push_logs',
        verbose_name=_('الإشعار')
    )

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=PushStatus.choices,
        default=PushStatus.PENDING
    )

    # FCM response
    fcm_message_id = models.CharField(_('معرف FCM'), max_length=255, blank=True)
    error_message = models.TextField(_('رسالة الخطأ'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    sent_at = models.DateTimeField(_('وقت الإرسال'), null=True, blank=True)
    opened_at = models.DateTimeField(_('وقت الفتح'), null=True, blank=True)

    class Meta:
        verbose_name = _('سجل Push')
        verbose_name_plural = _('سجلات Push')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"


# ===================================
# User Notification Preferences Model
# ===================================
class NotificationPreference(models.Model):
    """User's notification preferences."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('المستخدم')
    )

    # Push notifications
    push_orders = models.BooleanField(_('إشعارات الطلبات'), default=True)
    push_promotions = models.BooleanField(_('العروض والخصومات'), default=True)
    push_news = models.BooleanField(_('الأخبار والتحديثات'), default=True)
    push_chat = models.BooleanField(_('رسائل المحادثة'), default=True)

    # SMS
    sms_orders = models.BooleanField(_('رسائل الطلبات'), default=True)
    sms_otp = models.BooleanField(_('رسائل OTP'), default=True)
    sms_promotions = models.BooleanField(_('رسائل العروض'), default=False)

    # Email
    email_orders = models.BooleanField(_('بريد الطلبات'), default=True)
    email_promotions = models.BooleanField(_('بريد العروض'), default=False)
    email_newsletter = models.BooleanField(_('النشرة البريدية'), default=False)

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(_('ساعات الهدوء'), default=False)
    quiet_hours_start = models.TimeField(_('بداية الهدوء'), null=True, blank=True)
    quiet_hours_end = models.TimeField(_('نهاية الهدوء'), null=True, blank=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('تفضيلات الإشعارات')
        verbose_name_plural = _('تفضيلات الإشعارات')

    def __str__(self):
        return f"تفضيلات {self.user.full_name}"
