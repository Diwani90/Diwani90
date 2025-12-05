"""
===================================
منصة ديواني - Delivery Models
نماذج التوصيل والشحن
===================================
"""

import uuid
from decimal import Decimal

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings


# ===================================
# Delivery Zone Model
# ===================================
class DeliveryZone(models.Model):
    """Delivery zones for pricing and availability."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_('اسم المنطقة'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)

    # Geographic boundary
    boundary = gis_models.PolygonField(
        _('الحدود الجغرافية'),
        geography=True,
        null=True,
        blank=True
    )

    # Or simple city/district based
    city = models.CharField(_('المدينة'), max_length=100, blank=True)
    districts = models.JSONField(_('الأحياء'), default=list, blank=True)

    # Pricing
    base_delivery_fee = models.DecimalField(
        _('رسوم التوصيل الأساسية'),
        max_digits=10,
        decimal_places=2,
        default=15.00
    )

    per_km_fee = models.DecimalField(
        _('رسوم الكيلومتر'),
        max_digits=10,
        decimal_places=2,
        default=2.00
    )

    min_delivery_fee = models.DecimalField(
        _('الحد الأدنى للتوصيل'),
        max_digits=10,
        decimal_places=2,
        default=10.00
    )

    max_delivery_fee = models.DecimalField(
        _('الحد الأقصى للتوصيل'),
        max_digits=10,
        decimal_places=2,
        default=50.00
    )

    # Time
    estimated_delivery_time = models.PositiveIntegerField(
        _('وقت التوصيل المتوقع (دقيقة)'),
        default=45
    )

    # Status
    is_active = models.BooleanField(_('نشط'), default=True)
    is_available = models.BooleanField(_('متاح للتوصيل'), default=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('منطقة التوصيل')
        verbose_name_plural = _('مناطق التوصيل')

    def __str__(self):
        return self.name


# ===================================
# Delivery Request Model
# ===================================
class DeliveryRequest(models.Model):
    """Delivery request for an order."""

    class RequestStatus(models.TextChoices):
        PENDING = 'pending', _('قيد البحث')
        ASSIGNED = 'assigned', _('تم التعيين')
        ACCEPTED = 'accepted', _('مقبول')
        REJECTED = 'rejected', _('مرفوض')
        PICKED_UP = 'picked_up', _('تم الاستلام')
        IN_TRANSIT = 'in_transit', _('في الطريق')
        DELIVERED = 'delivered', _('تم التوصيل')
        CANCELLED = 'cancelled', _('ملغي')
        FAILED = 'failed', _('فشل')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Reference
    delivery_number = models.CharField(
        _('رقم التوصيل'),
        max_length=20,
        unique=True,
        editable=False
    )

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery_request',
        verbose_name=_('الطلب')
    )

    # Driver
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_requests',
        verbose_name=_('السائق')
    )

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )

    # Pickup location (store)
    pickup_address = models.TextField(_('عنوان الاستلام'))
    pickup_location = gis_models.PointField(
        _('موقع الاستلام'),
        geography=True,
        null=True
    )

    pickup_contact_name = models.CharField(_('اسم التواصل للاستلام'), max_length=100)
    pickup_contact_phone = models.CharField(_('رقم التواصل للاستلام'), max_length=15)

    # Delivery location (customer)
    delivery_address = models.TextField(_('عنوان التوصيل'))
    delivery_location = gis_models.PointField(
        _('موقع التوصيل'),
        geography=True,
        null=True
    )

    delivery_contact_name = models.CharField(_('اسم العميل'), max_length=100)
    delivery_contact_phone = models.CharField(_('رقم العميل'), max_length=15)

    # Distance & Time
    distance_km = models.DecimalField(
        _('المسافة (كم)'),
        max_digits=10,
        decimal_places=2,
        null=True
    )

    estimated_duration = models.PositiveIntegerField(
        _('الوقت المتوقع (دقيقة)'),
        null=True
    )

    actual_duration = models.PositiveIntegerField(
        _('الوقت الفعلي (دقيقة)'),
        null=True,
        blank=True
    )

    # Fees
    delivery_fee = models.DecimalField(
        _('رسوم التوصيل'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    driver_earnings = models.DecimalField(
        _('أرباح السائق'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Notes
    pickup_notes = models.TextField(_('ملاحظات الاستلام'), blank=True)
    delivery_notes = models.TextField(_('ملاحظات التوصيل'), blank=True)
    driver_notes = models.TextField(_('ملاحظات السائق'), blank=True)

    # Attempts
    assignment_attempts = models.PositiveIntegerField(_('محاولات التعيين'), default=0)

    # Proof of delivery
    delivery_photo = models.ImageField(
        _('صورة التسليم'),
        upload_to='delivery/proofs/%Y/%m/',
        blank=True,
        null=True
    )

    recipient_signature = models.ImageField(
        _('توقيع المستلم'),
        upload_to='delivery/signatures/%Y/%m/',
        blank=True,
        null=True
    )

    # Rating
    customer_rating = models.PositiveSmallIntegerField(
        _('تقييم العميل'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    customer_feedback = models.TextField(_('ملاحظات العميل'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    assigned_at = models.DateTimeField(_('وقت التعيين'), null=True, blank=True)
    accepted_at = models.DateTimeField(_('وقت القبول'), null=True, blank=True)
    picked_up_at = models.DateTimeField(_('وقت الاستلام'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('وقت التوصيل'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('وقت الإلغاء'), null=True, blank=True)

    class Meta:
        verbose_name = _('طلب توصيل')
        verbose_name_plural = _('طلبات التوصيل')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['driver']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"توصيل #{self.delivery_number}"

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = self.generate_delivery_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_delivery_number():
        """Generate unique delivery number."""
        import random
        import string
        prefix = timezone.now().strftime('%y%m%d')
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"DL{prefix}{suffix}"

    def assign_driver(self, driver):
        """Assign driver to delivery."""
        self.driver = driver
        self.status = self.RequestStatus.ASSIGNED
        self.assigned_at = timezone.now()
        self.save(update_fields=['driver', 'status', 'assigned_at'])

    def accept(self):
        """Driver accepts the delivery."""
        self.status = self.RequestStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at'])

    def pickup(self):
        """Mark as picked up from store."""
        self.status = self.RequestStatus.PICKED_UP
        self.picked_up_at = timezone.now()
        self.save(update_fields=['status', 'picked_up_at'])

    def start_delivery(self):
        """Start delivery to customer."""
        self.status = self.RequestStatus.IN_TRANSIT
        self.save(update_fields=['status'])

    def complete(self, photo=None, signature=None):
        """Complete the delivery."""
        self.status = self.RequestStatus.DELIVERED
        self.delivered_at = timezone.now()
        if photo:
            self.delivery_photo = photo
        if signature:
            self.recipient_signature = signature
        # Calculate actual duration
        if self.picked_up_at:
            self.actual_duration = int((self.delivered_at - self.picked_up_at).total_seconds() / 60)
        self.save()


# ===================================
# Driver Location History Model
# ===================================
class DriverLocationHistory(models.Model):
    """Track driver location over time."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='location_history',
        verbose_name=_('السائق')
    )

    delivery_request = models.ForeignKey(
        DeliveryRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='location_history',
        verbose_name=_('طلب التوصيل')
    )

    location = gis_models.PointField(_('الموقع'), geography=True)

    speed = models.DecimalField(
        _('السرعة (كم/س)'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    heading = models.DecimalField(
        _('الاتجاه'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    accuracy = models.DecimalField(
        _('الدقة (متر)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    recorded_at = models.DateTimeField(_('وقت التسجيل'), auto_now_add=True)

    class Meta:
        verbose_name = _('موقع السائق')
        verbose_name_plural = _('مواقع السائقين')
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['driver', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.driver.full_name} @ {self.recorded_at}"


# ===================================
# Delivery Assignment Log Model
# ===================================
class DeliveryAssignmentLog(models.Model):
    """Log of delivery assignment attempts."""

    class AssignmentResult(models.TextChoices):
        SENT = 'sent', _('تم الإرسال')
        ACCEPTED = 'accepted', _('مقبول')
        REJECTED = 'rejected', _('مرفوض')
        TIMEOUT = 'timeout', _('انتهت المهلة')
        CANCELLED = 'cancelled', _('ملغي')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    delivery_request = models.ForeignKey(
        DeliveryRequest,
        on_delete=models.CASCADE,
        related_name='assignment_logs',
        verbose_name=_('طلب التوصيل')
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_logs',
        verbose_name=_('السائق')
    )

    # Distance from driver to pickup
    distance_to_pickup = models.DecimalField(
        _('المسافة للاستلام (كم)'),
        max_digits=10,
        decimal_places=2,
        null=True
    )

    # Result
    result = models.CharField(
        _('النتيجة'),
        max_length=20,
        choices=AssignmentResult.choices,
        default=AssignmentResult.SENT
    )

    rejection_reason = models.TextField(_('سبب الرفض'), blank=True)

    # Timing
    sent_at = models.DateTimeField(_('وقت الإرسال'), auto_now_add=True)
    responded_at = models.DateTimeField(_('وقت الرد'), null=True, blank=True)

    # Response time in seconds
    response_time = models.PositiveIntegerField(_('وقت الاستجابة (ثانية)'), null=True)

    class Meta:
        verbose_name = _('سجل التعيين')
        verbose_name_plural = _('سجلات التعيين')
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.delivery_request.delivery_number} -> {self.driver.full_name}"


# ===================================
# Driver Availability Model
# ===================================
class DriverAvailability(models.Model):
    """Driver availability schedule."""

    class Weekday(models.IntegerChoices):
        SUNDAY = 0, _('الأحد')
        MONDAY = 1, _('الإثنين')
        TUESDAY = 2, _('الثلاثاء')
        WEDNESDAY = 3, _('الأربعاء')
        THURSDAY = 4, _('الخميس')
        FRIDAY = 5, _('الجمعة')
        SATURDAY = 6, _('السبت')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability_schedule',
        verbose_name=_('السائق')
    )

    weekday = models.PositiveSmallIntegerField(
        _('اليوم'),
        choices=Weekday.choices
    )

    start_time = models.TimeField(_('وقت البدء'))
    end_time = models.TimeField(_('وقت الانتهاء'))

    is_available = models.BooleanField(_('متاح'), default=True)

    class Meta:
        verbose_name = _('جدول توفر السائق')
        verbose_name_plural = _('جداول توفر السائقين')
        unique_together = ['driver', 'weekday']
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"{self.driver.full_name} - {self.get_weekday_display()}"


# ===================================
# Delivery Earnings Model
# ===================================
class DeliveryEarnings(models.Model):
    """Driver earnings record."""

    class EarningType(models.TextChoices):
        DELIVERY = 'delivery', _('توصيل')
        TIP = 'tip', _('بقشيش')
        BONUS = 'bonus', _('مكافأة')
        PENALTY = 'penalty', _('خصم')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_earnings',
        verbose_name=_('السائق')
    )

    delivery_request = models.ForeignKey(
        DeliveryRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='earnings',
        verbose_name=_('طلب التوصيل')
    )

    earning_type = models.CharField(
        _('نوع الربح'),
        max_length=20,
        choices=EarningType.choices,
        default=EarningType.DELIVERY
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=10,
        decimal_places=2
    )

    description = models.CharField(_('الوصف'), max_length=255)

    # Settlement
    is_settled = models.BooleanField(_('تمت التسوية'), default=False)
    settled_at = models.DateTimeField(_('تاريخ التسوية'), null=True, blank=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('أرباح التوصيل')
        verbose_name_plural = _('أرباح التوصيل')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.driver.full_name} - {self.amount} SAR"
