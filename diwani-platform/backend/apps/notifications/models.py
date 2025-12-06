"""
نماذج نظام الإشعارات
====================
"""

import uuid
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class NotificationCategory(models.TextChoices):
    """تصنيفات الإشعارات"""

    # طلبات
    ORDER = 'order', 'الطلبات'
    ORDER_STATUS = 'order_status', 'حالة الطلب'
    ORDER_DELIVERY = 'order_delivery', 'التوصيل'

    # مدفوعات
    PAYMENT = 'payment', 'المدفوعات'
    PAYMENT_RECEIVED = 'payment_received', 'استلام الدفع'
    PAYMENT_REFUND = 'payment_refund', 'استرداد'

    # محادثات
    CHAT = 'chat', 'المحادثات'
    NEW_MESSAGE = 'new_message', 'رسالة جديدة'
    MENTION = 'mention', 'إشارة'

    # منتجات
    PRODUCT = 'product', 'المنتجات'
    PRICE_DROP = 'price_drop', 'انخفاض السعر'
    BACK_IN_STOCK = 'back_in_stock', 'توفر المنتج'
    LOW_STOCK = 'low_stock', 'نفاد المخزون'

    # تسويق
    PROMOTION = 'promotion', 'العروض'
    COUPON = 'coupon', 'كوبونات'

    # نظام
    SYSTEM = 'system', 'النظام'
    ACCOUNT = 'account', 'الحساب'
    SECURITY = 'security', 'الأمان'


class NotificationPriority(models.IntegerChoices):
    """أولويات الإشعارات"""

    CRITICAL = 0, 'حرج'
    HIGH = 1, 'عالي'
    NORMAL = 2, 'عادي'
    LOW = 3, 'منخفض'


class DeliveryChannel(models.TextChoices):
    """قنوات التوصيل"""

    WEBSOCKET = 'websocket', 'WebSocket'
    PUSH = 'push', 'Push Notification'
    SMS = 'sms', 'رسالة نصية'
    EMAIL = 'email', 'بريد إلكتروني'
    IN_APP = 'in_app', 'داخل التطبيق'


class DeliveryStatus(models.TextChoices):
    """حالات التوصيل"""

    PENDING = 'pending', 'قيد الانتظار'
    QUEUED = 'queued', 'في الطابور'
    SENT = 'sent', 'تم الإرسال'
    DELIVERED = 'delivered', 'تم التوصيل'
    READ = 'read', 'تمت القراءة'
    FAILED = 'failed', 'فشل'
    CANCELLED = 'cancelled', 'ملغي'


class NotificationTemplate(models.Model):
    """
    قوالب الإشعارات

    تسمح بإنشاء قوالب قابلة لإعادة الاستخدام مع متغيرات
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # التعريف
    name = models.CharField(max_length=100, unique=True, verbose_name='اسم القالب')
    code = models.SlugField(max_length=100, unique=True, verbose_name='رمز القالب')
    description = models.TextField(blank=True, verbose_name='الوصف')

    # التصنيف
    category = models.CharField(
        max_length=50,
        choices=NotificationCategory.choices,
        verbose_name='التصنيف',
    )

    # المحتوى
    title_template = models.CharField(max_length=200, verbose_name='قالب العنوان')
    body_template = models.TextField(verbose_name='قالب المحتوى')
    body_html_template = models.TextField(blank=True, verbose_name='قالب HTML')

    # إعدادات
    default_priority = models.IntegerField(
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name='الأولوية الافتراضية',
    )
    default_channels = models.JSONField(
        default=list,
        verbose_name='القنوات الافتراضية',
    )

    # إعدادات متقدمة
    is_batched = models.BooleanField(default=False, verbose_name='تجميع')
    batch_window_seconds = models.IntegerField(default=300, verbose_name='نافذة التجميع')
    ttl_seconds = models.IntegerField(null=True, blank=True, verbose_name='مدة الصلاحية')
    is_cancellable = models.BooleanField(default=True, verbose_name='قابل للإلغاء')

    # الحالة
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'قالب إشعار'
        verbose_name_plural = 'قوالب الإشعارات'

    def __str__(self):
        return self.name

    def render(self, context: dict) -> dict:
        """تطبيق القالب مع السياق"""
        from string import Template

        return {
            'title': Template(self.title_template).safe_substitute(context),
            'body': Template(self.body_template).safe_substitute(context),
            'body_html': Template(self.body_html_template).safe_substitute(context)
            if self.body_html_template else None,
        }


class Notification(models.Model):
    """
    الإشعار الفردي

    يمثل إشعار واحد لمستخدم واحد
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # المستلم
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='المستلم',
    )

    # المحتوى
    title = models.CharField(max_length=200, verbose_name='العنوان')
    body = models.TextField(verbose_name='المحتوى')
    body_html = models.TextField(blank=True, verbose_name='محتوى HTML')

    # البيانات الإضافية
    data = models.JSONField(default=dict, verbose_name='بيانات إضافية')
    action_url = models.URLField(blank=True, verbose_name='رابط الإجراء')
    image_url = models.URLField(blank=True, verbose_name='رابط الصورة')
    icon = models.CharField(max_length=50, blank=True, verbose_name='الأيقونة')

    # التصنيف
    category = models.CharField(
        max_length=50,
        choices=NotificationCategory.choices,
        verbose_name='التصنيف',
    )
    priority = models.IntegerField(
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name='الأولوية',
    )

    # القالب
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='القالب',
    )

    # الربط بكيان
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # الحالة
    is_read = models.BooleanField(default=False, verbose_name='مقروء')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت القراءة')
    is_archived = models.BooleanField(default=False, verbose_name='مؤرشف')
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت الأرشفة')

    # التوقيت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت الإنشاء')
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت الجدولة')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت الانتهاء')

    # التجميع
    group_key = models.CharField(max_length=100, blank=True, verbose_name='مفتاح التجميع')
    group_count = models.IntegerField(default=1, verbose_name='عدد المجمّعة')

    # التتبع
    correlation_id = models.CharField(max_length=100, blank=True, verbose_name='معرف الارتباط')

    class Meta:
        db_table = 'notifications'
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['group_key']),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient}"

    def mark_as_read(self):
        """تحديد كمقروء"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def archive(self):
        """أرشفة الإشعار"""
        if not self.is_archived:
            self.is_archived = True
            self.archived_at = timezone.now()
            self.save(update_fields=['is_archived', 'archived_at'])

    @property
    def is_expired(self) -> bool:
        """هل انتهت الصلاحية؟"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NotificationDelivery(models.Model):
    """
    سجل توصيل الإشعار

    يتتبع حالة التوصيل لكل قناة
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='الإشعار',
    )

    # القناة
    channel = models.CharField(
        max_length=20,
        choices=DeliveryChannel.choices,
        verbose_name='القناة',
    )

    # الحالة
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        verbose_name='الحالة',
    )

    # التوقيت
    queued_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    # المحاولات
    attempts = models.IntegerField(default=0, verbose_name='عدد المحاولات')
    max_attempts = models.IntegerField(default=3, verbose_name='الحد الأقصى للمحاولات')
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_attempt_at = models.DateTimeField(null=True, blank=True)

    # الخطأ
    error_message = models.TextField(blank=True, verbose_name='رسالة الخطأ')
    error_code = models.CharField(max_length=50, blank=True, verbose_name='رمز الخطأ')

    # البيانات
    provider_response = models.JSONField(default=dict, verbose_name='استجابة المزود')
    provider_message_id = models.CharField(max_length=200, blank=True, verbose_name='معرف المزود')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_deliveries'
        verbose_name = 'توصيل إشعار'
        verbose_name_plural = 'توصيلات الإشعارات'
        unique_together = [['notification', 'channel']]

    def __str__(self):
        return f"{self.notification_id} - {self.channel} - {self.status}"

    def mark_sent(self, provider_message_id: str = ''):
        """تحديد كمرسل"""
        self.status = DeliveryStatus.SENT
        self.sent_at = timezone.now()
        self.provider_message_id = provider_message_id
        self.save(update_fields=['status', 'sent_at', 'provider_message_id', 'updated_at'])

    def mark_delivered(self):
        """تحديد كموصّل"""
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])

    def mark_failed(self, error_message: str, error_code: str = ''):
        """تحديد كفاشل"""
        self.status = DeliveryStatus.FAILED
        self.failed_at = timezone.now()
        self.error_message = error_message
        self.error_code = error_code
        self.save(update_fields=['status', 'failed_at', 'error_message', 'error_code', 'updated_at'])


class UserNotificationPreferences(models.Model):
    """
    تفضيلات إشعارات المستخدم
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        primary_key=True,
        verbose_name='المستخدم',
    )

    # إعدادات عامة
    notifications_enabled = models.BooleanField(default=True, verbose_name='الإشعارات مفعلة')
    quiet_hours_enabled = models.BooleanField(default=False, verbose_name='ساعات الهدوء')
    quiet_hours_start = models.TimeField(null=True, blank=True, verbose_name='بداية الهدوء')
    quiet_hours_end = models.TimeField(null=True, blank=True, verbose_name='نهاية الهدوء')

    # تفضيلات القنوات
    websocket_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)

    # تفضيلات التصنيفات (JSON)
    category_preferences = models.JSONField(
        default=dict,
        verbose_name='تفضيلات التصنيفات',
        help_text='{"order": {"push": true, "email": false}, ...}',
    )

    # إعدادات التجميع
    batch_notifications = models.BooleanField(default=False, verbose_name='تجميع الإشعارات')
    batch_interval_minutes = models.IntegerField(default=15, verbose_name='فترة التجميع')

    # الأجهزة
    push_tokens = models.JSONField(default=list, verbose_name='رموز Push')

    # اللغة
    preferred_language = models.CharField(max_length=10, default='ar', verbose_name='اللغة')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_notification_preferences'
        verbose_name = 'تفضيلات إشعارات المستخدم'
        verbose_name_plural = 'تفضيلات إشعارات المستخدمين'

    def __str__(self):
        return f"تفضيلات {self.user}"

    def is_channel_enabled(self, channel: str, category: str = None) -> bool:
        """التحقق من تفعيل قناة"""
        if not self.notifications_enabled:
            return False

        # التحقق من القناة العامة
        channel_map = {
            'websocket': self.websocket_enabled,
            'push': self.push_enabled,
            'sms': self.sms_enabled,
            'email': self.email_enabled,
        }

        if not channel_map.get(channel, True):
            return False

        # التحقق من تفضيلات التصنيف
        if category and category in self.category_preferences:
            cat_prefs = self.category_preferences[category]
            if isinstance(cat_prefs, dict):
                return cat_prefs.get(channel, True)

        return True

    def is_quiet_hours(self) -> bool:
        """هل نحن في ساعات الهدوء؟"""
        if not self.quiet_hours_enabled:
            return False

        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        now = timezone.localtime().time()

        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            # يمتد لليوم التالي
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end

    def add_push_token(self, token: str, device_id: str, platform: str = 'unknown'):
        """إضافة رمز Push"""
        # إزالة النسخ المكررة
        self.push_tokens = [
            t for t in self.push_tokens
            if t.get('device_id') != device_id
        ]

        self.push_tokens.append({
            'token': token,
            'device_id': device_id,
            'platform': platform,
            'added_at': timezone.now().isoformat(),
        })
        self.save(update_fields=['push_tokens', 'updated_at'])

    def remove_push_token(self, device_id: str):
        """إزالة رمز Push"""
        self.push_tokens = [
            t for t in self.push_tokens
            if t.get('device_id') != device_id
        ]
        self.save(update_fields=['push_tokens', 'updated_at'])
