"""
نماذج نظام التتبع
==================

يوفر:
- تتبع التوصيل في الوقت الحقيقي
- نقاط المسار وسجل المواقع
- حالات التوصيل المختلفة
- تكامل مع نظام الطلبات
"""

import uuid
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# =============================================
# Enums
# =============================================

class DeliveryStatus(models.TextChoices):
    """حالات التوصيل"""
    PENDING = 'pending', _('قيد الانتظار')
    ASSIGNED = 'assigned', _('تم التعيين')
    ACCEPTED = 'accepted', _('تم القبول')
    PICKING_UP = 'picking_up', _('في طريقه للاستلام')
    AT_PICKUP = 'at_pickup', _('وصل نقطة الاستلام')
    PICKED_UP = 'picked_up', _('تم الاستلام')
    IN_TRANSIT = 'in_transit', _('في الطريق')
    NEAR_DESTINATION = 'near_destination', _('قريب من الوجهة')
    ARRIVED = 'arrived', _('وصل الوجهة')
    DELIVERED = 'delivered', _('تم التسليم')
    FAILED = 'failed', _('فشل التوصيل')
    CANCELLED = 'cancelled', _('ملغي')
    RETURNED = 'returned', _('مرتجع')


class DeliveryType(models.TextChoices):
    """نوع التوصيل"""
    STANDARD = 'standard', _('عادي')
    EXPRESS = 'express', _('سريع')
    SAME_DAY = 'same_day', _('نفس اليوم')
    SCHEDULED = 'scheduled', _('مجدول')
    PICKUP = 'pickup', _('استلام من الموقع')


class VehicleType(models.TextChoices):
    """نوع المركبة"""
    MOTORCYCLE = 'motorcycle', _('دراجة نارية')
    CAR = 'car', _('سيارة')
    VAN = 'van', _('فان')
    PICKUP_TRUCK = 'pickup_truck', _('بيك أب')
    TRUCK = 'truck', _('شاحنة صغيرة')
    LARGE_TRUCK = 'large_truck', _('شاحنة كبيرة')
    TRAILER = 'trailer', _('مقطورة')


class TrackingEventType(models.TextChoices):
    """أنواع أحداث التتبع"""
    STATUS_CHANGE = 'status_change', _('تغيير الحالة')
    LOCATION_UPDATE = 'location_update', _('تحديث الموقع')
    DRIVER_ACTION = 'driver_action', _('إجراء السائق')
    CUSTOMER_ACTION = 'customer_action', _('إجراء العميل')
    SYSTEM_EVENT = 'system_event', _('حدث النظام')
    GEOFENCE_EVENT = 'geofence_event', _('حدث السياج الجغرافي')
    EXCEPTION = 'exception', _('استثناء')


# =============================================
# Delivery Model
# =============================================

class Delivery(models.Model):
    """
    نموذج التوصيل الرئيسي

    يربط بين الطلب والسائق ويتتبع عملية التوصيل
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # الطلب المرتبط
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery',
        verbose_name=_('الطلب')
    )

    # السائق
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries',
        verbose_name=_('السائق')
    )

    # نوع التوصيل
    delivery_type = models.CharField(
        _('نوع التوصيل'),
        max_length=20,
        choices=DeliveryType.choices,
        default=DeliveryType.STANDARD
    )

    # نوع المركبة المطلوبة/المستخدمة
    vehicle_type = models.CharField(
        _('نوع المركبة'),
        max_length=20,
        choices=VehicleType.choices,
        null=True,
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING
    )
    previous_status = models.CharField(
        _('الحالة السابقة'),
        max_length=20,
        blank=True
    )

    # نقطة الاستلام
    pickup_location = gis_models.PointField(
        _('موقع الاستلام'),
        srid=4326
    )
    pickup_address = models.TextField(_('عنوان الاستلام'))
    pickup_contact_name = models.CharField(
        _('اسم جهة الاتصال للاستلام'),
        max_length=100
    )
    pickup_contact_phone = models.CharField(
        _('هاتف الاستلام'),
        max_length=20
    )
    pickup_notes = models.TextField(_('ملاحظات الاستلام'), blank=True)

    # نقطة التسليم
    dropoff_location = gis_models.PointField(
        _('موقع التسليم'),
        srid=4326
    )
    dropoff_address = models.TextField(_('عنوان التسليم'))
    dropoff_contact_name = models.CharField(
        _('اسم المستلم'),
        max_length=100
    )
    dropoff_contact_phone = models.CharField(
        _('هاتف المستلم'),
        max_length=20
    )
    dropoff_notes = models.TextField(_('ملاحظات التسليم'), blank=True)

    # الموقع الحالي للسائق
    current_location = gis_models.PointField(
        _('الموقع الحالي'),
        srid=4326,
        null=True,
        blank=True
    )
    current_speed = models.DecimalField(
        _('السرعة الحالية (كم/س)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    current_heading = models.DecimalField(
        _('الاتجاه (درجات)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    last_location_update = models.DateTimeField(
        _('آخر تحديث للموقع'),
        null=True,
        blank=True
    )

    # المسافات
    total_distance_km = models.DecimalField(
        _('المسافة الكلية (كم)'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    distance_traveled_km = models.DecimalField(
        _('المسافة المقطوعة (كم)'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    distance_remaining_km = models.DecimalField(
        _('المسافة المتبقية (كم)'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # أوقات التوصيل
    estimated_pickup_time = models.DateTimeField(
        _('وقت الاستلام المتوقع'),
        null=True,
        blank=True
    )
    actual_pickup_time = models.DateTimeField(
        _('وقت الاستلام الفعلي'),
        null=True,
        blank=True
    )
    estimated_delivery_time = models.DateTimeField(
        _('وقت التسليم المتوقع'),
        null=True,
        blank=True
    )
    actual_delivery_time = models.DateTimeField(
        _('وقت التسليم الفعلي'),
        null=True,
        blank=True
    )
    scheduled_time = models.DateTimeField(
        _('الموعد المجدول'),
        null=True,
        blank=True,
        help_text=_('للتوصيل المجدول')
    )

    # ETA
    eta_minutes = models.PositiveIntegerField(
        _('الوقت المتوقع للوصول (دقائق)'),
        null=True,
        blank=True
    )
    eta_updated_at = models.DateTimeField(
        _('آخر تحديث للـ ETA'),
        null=True,
        blank=True
    )

    # محاولات التسليم
    delivery_attempts = models.PositiveIntegerField(
        _('محاولات التسليم'),
        default=0
    )
    max_delivery_attempts = models.PositiveIntegerField(
        _('الحد الأقصى للمحاولات'),
        default=3
    )

    # التكاليف
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
    platform_fee = models.DecimalField(
        _('عمولة المنصة'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tip_amount = models.DecimalField(
        _('البقشيش'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # التحقق والتوقيعات
    pickup_verification_code = models.CharField(
        _('رمز التحقق للاستلام'),
        max_length=10,
        blank=True
    )
    delivery_verification_code = models.CharField(
        _('رمز التحقق للتسليم'),
        max_length=10,
        blank=True
    )
    signature_image = models.ImageField(
        _('صورة التوقيع'),
        upload_to='deliveries/signatures/',
        null=True,
        blank=True
    )
    delivery_photo = models.ImageField(
        _('صورة التسليم'),
        upload_to='deliveries/photos/',
        null=True,
        blank=True
    )

    # التقييم
    customer_rating = models.PositiveSmallIntegerField(
        _('تقييم العميل'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    customer_feedback = models.TextField(
        _('ملاحظات العميل'),
        blank=True
    )
    driver_rating = models.PositiveSmallIntegerField(
        _('تقييم السائق للعميل'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # سبب الفشل/الإلغاء
    failure_reason = models.TextField(_('سبب الفشل'), blank=True)
    cancellation_reason = models.TextField(_('سبب الإلغاء'), blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_deliveries',
        verbose_name=_('ألغي بواسطة')
    )

    # الأولوية
    priority = models.PositiveSmallIntegerField(
        _('الأولوية'),
        default=0,
        help_text=_('أعلى = أولوية أكبر')
    )
    is_urgent = models.BooleanField(_('عاجل'), default=False)

    # بيانات إضافية
    special_instructions = models.TextField(_('تعليمات خاصة'), blank=True)
    package_description = models.TextField(_('وصف الشحنة'), blank=True)
    package_weight_kg = models.DecimalField(
        _('وزن الشحنة (كجم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    requires_signature = models.BooleanField(
        _('يتطلب توقيع'),
        default=False
    )
    requires_photo = models.BooleanField(
        _('يتطلب صورة'),
        default=True
    )

    # البيانات الوصفية
    metadata = models.JSONField(_('بيانات إضافية'), default=dict, blank=True)

    # التواريخ
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    assigned_at = models.DateTimeField(_('تاريخ التعيين'), null=True, blank=True)
    started_at = models.DateTimeField(_('تاريخ البدء'), null=True, blank=True)
    completed_at = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)

    class Meta:
        verbose_name = _('توصيل')
        verbose_name_plural = _('التوصيلات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['driver', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['delivery_type', 'status']),
            models.Index(fields=['-priority', '-created_at']),
        ]

    def __str__(self):
        return f"توصيل #{str(self.id)[:8]} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # حفظ الحالة السابقة
        if self.pk:
            old = Delivery.objects.filter(pk=self.pk).first()
            if old and old.status != self.status:
                self.previous_status = old.status

        # توليد رموز التحقق
        if not self.pickup_verification_code:
            self.pickup_verification_code = self._generate_verification_code()
        if not self.delivery_verification_code:
            self.delivery_verification_code = self._generate_verification_code()

        super().save(*args, **kwargs)

    def _generate_verification_code(self) -> str:
        """توليد رمز تحقق عشوائي"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    def update_location(self, latitude: float, longitude: float,
                       speed: float = 0, heading: float = 0) -> None:
        """تحديث موقع السائق"""
        from django.contrib.gis.geos import Point

        self.current_location = Point(longitude, latitude, srid=4326)
        self.current_speed = Decimal(str(speed))
        self.current_heading = Decimal(str(heading))
        self.last_location_update = timezone.now()
        self.save(update_fields=[
            'current_location', 'current_speed',
            'current_heading', 'last_location_update'
        ])

    def assign_driver(self, driver) -> None:
        """تعيين سائق"""
        self.driver = driver
        self.status = DeliveryStatus.ASSIGNED
        self.assigned_at = timezone.now()
        self.save(update_fields=['driver', 'status', 'assigned_at'])

    def accept(self) -> None:
        """قبول التوصيل"""
        self.status = DeliveryStatus.ACCEPTED
        self.save(update_fields=['status'])

    def start_pickup(self) -> None:
        """بدء الذهاب للاستلام"""
        self.status = DeliveryStatus.PICKING_UP
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def arrive_at_pickup(self) -> None:
        """الوصول لنقطة الاستلام"""
        self.status = DeliveryStatus.AT_PICKUP
        self.save(update_fields=['status'])

    def confirm_pickup(self) -> None:
        """تأكيد الاستلام"""
        self.status = DeliveryStatus.PICKED_UP
        self.actual_pickup_time = timezone.now()
        self.save(update_fields=['status', 'actual_pickup_time'])

    def start_delivery(self) -> None:
        """بدء التوصيل"""
        self.status = DeliveryStatus.IN_TRANSIT
        self.save(update_fields=['status'])

    def arrive_at_destination(self) -> None:
        """الوصول للوجهة"""
        self.status = DeliveryStatus.ARRIVED
        self.save(update_fields=['status'])

    def complete_delivery(self, signature=None, photo=None) -> None:
        """إتمام التسليم"""
        self.status = DeliveryStatus.DELIVERED
        self.actual_delivery_time = timezone.now()
        self.completed_at = timezone.now()

        if signature:
            self.signature_image = signature
        if photo:
            self.delivery_photo = photo

        self.save()

    def fail_delivery(self, reason: str) -> None:
        """فشل التوصيل"""
        self.delivery_attempts += 1
        self.failure_reason = reason

        if self.delivery_attempts >= self.max_delivery_attempts:
            self.status = DeliveryStatus.FAILED
        else:
            self.status = DeliveryStatus.PENDING

        self.save()

    def cancel(self, cancelled_by, reason: str) -> None:
        """إلغاء التوصيل"""
        self.status = DeliveryStatus.CANCELLED
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        self.completed_at = timezone.now()
        self.save()

    @property
    def is_active(self) -> bool:
        """هل التوصيل نشط؟"""
        return self.status in [
            DeliveryStatus.ASSIGNED,
            DeliveryStatus.ACCEPTED,
            DeliveryStatus.PICKING_UP,
            DeliveryStatus.AT_PICKUP,
            DeliveryStatus.PICKED_UP,
            DeliveryStatus.IN_TRANSIT,
            DeliveryStatus.NEAR_DESTINATION,
            DeliveryStatus.ARRIVED,
        ]

    @property
    def is_completed(self) -> bool:
        """هل اكتمل التوصيل؟"""
        return self.status == DeliveryStatus.DELIVERED

    @property
    def can_be_cancelled(self) -> bool:
        """هل يمكن إلغاء التوصيل؟"""
        return self.status in [
            DeliveryStatus.PENDING,
            DeliveryStatus.ASSIGNED,
            DeliveryStatus.ACCEPTED,
        ]


# =============================================
# Delivery Tracking Point
# =============================================

class DeliveryTrackingPoint(models.Model):
    """
    نقاط تتبع التوصيل

    يحفظ سجل المواقع للتوصيل
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='tracking_points',
        verbose_name=_('التوصيل')
    )

    # الموقع
    location = gis_models.PointField(_('الموقع'), srid=4326)
    altitude = models.DecimalField(
        _('الارتفاع (م)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    accuracy = models.DecimalField(
        _('الدقة (م)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # الحركة
    speed = models.DecimalField(
        _('السرعة (كم/س)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    heading = models.DecimalField(
        _('الاتجاه (درجات)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )

    # الحالة عند هذه النقطة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=DeliveryStatus.choices
    )

    # معلومات الجهاز
    battery_level = models.PositiveSmallIntegerField(
        _('مستوى البطارية (%)'),
        null=True,
        blank=True
    )

    # الوقت
    recorded_at = models.DateTimeField(_('وقت التسجيل'))
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('نقطة تتبع')
        verbose_name_plural = _('نقاط التتبع')
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['delivery', '-recorded_at']),
        ]

    def __str__(self):
        return f"نقطة {self.delivery_id} @ {self.recorded_at}"

    @property
    def latitude(self) -> float:
        return self.location.y

    @property
    def longitude(self) -> float:
        return self.location.x


# =============================================
# Delivery Event
# =============================================

class DeliveryEvent(models.Model):
    """
    أحداث التوصيل

    يسجل جميع الأحداث المتعلقة بالتوصيل
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_('التوصيل')
    )

    # نوع الحدث
    event_type = models.CharField(
        _('نوع الحدث'),
        max_length=30,
        choices=TrackingEventType.choices
    )

    # الوصف
    title = models.CharField(_('العنوان'), max_length=200)
    description = models.TextField(_('الوصف'), blank=True)

    # البيانات
    old_status = models.CharField(
        _('الحالة السابقة'),
        max_length=20,
        blank=True
    )
    new_status = models.CharField(
        _('الحالة الجديدة'),
        max_length=20,
        blank=True
    )

    # الموقع عند الحدث
    location = gis_models.PointField(
        _('الموقع'),
        srid=4326,
        null=True,
        blank=True
    )

    # من قام بالحدث
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('المنفذ')
    )
    actor_type = models.CharField(
        _('نوع المنفذ'),
        max_length=20,
        choices=[
            ('driver', _('السائق')),
            ('customer', _('العميل')),
            ('vendor', _('التاجر')),
            ('support', _('الدعم')),
            ('system', _('النظام')),
        ],
        default='system'
    )

    # بيانات إضافية
    metadata = models.JSONField(_('بيانات إضافية'), default=dict, blank=True)

    # هل الحدث مرئي للعميل؟
    is_customer_visible = models.BooleanField(
        _('مرئي للعميل'),
        default=True
    )

    # التوقيت
    occurred_at = models.DateTimeField(_('وقت الحدث'))
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('حدث توصيل')
        verbose_name_plural = _('أحداث التوصيل')
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['delivery', '-occurred_at']),
            models.Index(fields=['event_type', '-occurred_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.occurred_at}"


# =============================================
# Driver Location (للتتبع المستمر)
# =============================================

class DriverLocation(models.Model):
    """
    موقع السائق الحالي

    يحفظ آخر موقع معروف لكل سائق للمطابقة السريعة
    """

    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='current_location',
        verbose_name=_('السائق')
    )

    # الموقع
    location = gis_models.PointField(_('الموقع'), srid=4326)
    accuracy = models.DecimalField(
        _('الدقة (م)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # الحركة
    speed = models.DecimalField(
        _('السرعة (كم/س)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    heading = models.DecimalField(
        _('الاتجاه (درجات)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )

    # الحالة
    is_online = models.BooleanField(_('متصل'), default=False)
    is_available = models.BooleanField(_('متاح'), default=False)
    is_on_delivery = models.BooleanField(_('في توصيل'), default=False)
    current_delivery = models.ForeignKey(
        Delivery,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver_location',
        verbose_name=_('التوصيل الحالي')
    )

    # معلومات الجهاز
    battery_level = models.PositiveSmallIntegerField(
        _('مستوى البطارية (%)'),
        null=True,
        blank=True
    )

    # التحديث
    last_update = models.DateTimeField(_('آخر تحديث'), auto_now=True)

    class Meta:
        verbose_name = _('موقع سائق')
        verbose_name_plural = _('مواقع السائقين')
        indexes = [
            models.Index(fields=['is_online', 'is_available']),
        ]

    def __str__(self):
        return f"موقع {self.driver}"

    @property
    def latitude(self) -> float:
        return self.location.y

    @property
    def longitude(self) -> float:
        return self.location.x

    @property
    def is_stale(self) -> bool:
        """هل الموقع قديم؟ (أكثر من 5 دقائق)"""
        threshold = timezone.now() - timedelta(minutes=5)
        return self.last_update < threshold


# =============================================
# Geofence
# =============================================

class Geofence(models.Model):
    """
    السياج الجغرافي

    لتحديد مناطق ومراقبة دخول/خروج السائقين
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # الربط
    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='geofences',
        verbose_name=_('التوصيل')
    )

    # التعريف
    name = models.CharField(_('الاسم'), max_length=100)
    geofence_type = models.CharField(
        _('النوع'),
        max_length=20,
        choices=[
            ('pickup', _('نقطة استلام')),
            ('dropoff', _('نقطة تسليم')),
            ('zone', _('منطقة')),
            ('restricted', _('منطقة محظورة')),
        ]
    )

    # الشكل
    center = gis_models.PointField(_('المركز'), srid=4326)
    radius_meters = models.PositiveIntegerField(
        _('نصف القطر (م)'),
        default=100
    )
    polygon = gis_models.PolygonField(
        _('المضلع'),
        srid=4326,
        null=True,
        blank=True
    )

    # الإعدادات
    trigger_on_enter = models.BooleanField(_('تفعيل عند الدخول'), default=True)
    trigger_on_exit = models.BooleanField(_('تفعيل عند الخروج'), default=True)
    is_active = models.BooleanField(_('نشط'), default=True)

    # البيانات الوصفية
    metadata = models.JSONField(_('بيانات إضافية'), default=dict, blank=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('سياج جغرافي')
        verbose_name_plural = _('السياجات الجغرافية')

    def __str__(self):
        return self.name

    def contains_point(self, point) -> bool:
        """التحقق من وجود نقطة داخل السياج"""
        if self.polygon:
            return self.polygon.contains(point)
        else:
            return self.center.distance(point) * 111000 <= self.radius_meters
