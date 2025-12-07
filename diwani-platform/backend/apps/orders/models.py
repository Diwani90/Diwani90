"""
نماذج نظام الطلبات
==================

نظام طلبات متكامل يدعم:
- أنواع متعددة من الطلبات (منتجات، خدمات، تأجير، نقل)
- تتبع حالة الطلب بالتفصيل
- نظام التوصيل مع التتبع
- المراجعات والتقييمات
- الإلغاء والاسترداد
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone


# =============================================
# الثوابت والخيارات
# =============================================

class OrderType(models.TextChoices):
    """أنواع الطلبات"""
    PRODUCT = 'product', 'منتجات'
    SERVICE = 'service', 'خدمة'
    RENTAL = 'rental', 'تأجير'
    TRANSPORT = 'transport', 'نقل'
    INSTALLATION = 'installation', 'تركيب'
    MAINTENANCE = 'maintenance', 'صيانة'
    LABOR = 'labor', 'عمالة'
    MIXED = 'mixed', 'مختلط'


class OrderStatus(models.TextChoices):
    """حالات الطلب الرئيسية"""
    # البداية
    DRAFT = 'draft', 'مسودة'
    PENDING = 'pending', 'بانتظار الموافقة'
    PENDING_PAYMENT = 'pending_payment', 'بانتظار الدفع'

    # التأكيد
    CONFIRMED = 'confirmed', 'مؤكد'
    ACCEPTED = 'accepted', 'مقبول من التاجر'

    # التجهيز
    PROCESSING = 'processing', 'قيد التجهيز'
    PREPARING = 'preparing', 'قيد التحضير'
    READY = 'ready', 'جاهز للشحن'

    # التوصيل
    SHIPPED = 'shipped', 'تم الشحن'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'قيد التوصيل'
    DELIVERED = 'delivered', 'تم التوصيل'

    # الإنهاء
    COMPLETED = 'completed', 'مكتمل'
    CANCELLED = 'cancelled', 'ملغي'
    REFUNDED = 'refunded', 'مسترد'
    FAILED = 'failed', 'فاشل'

    # للخدمات
    SCHEDULED = 'scheduled', 'مجدول'
    IN_PROGRESS = 'in_progress', 'قيد التنفيذ'


class PaymentStatus(models.TextChoices):
    """حالات الدفع"""
    PENDING = 'pending', 'بانتظار الدفع'
    AUTHORIZED = 'authorized', 'مُصرح'
    CAPTURED = 'captured', 'تم التحصيل'
    PARTIALLY_PAID = 'partially_paid', 'مدفوع جزئياً'
    PAID = 'paid', 'مدفوع بالكامل'
    REFUNDED = 'refunded', 'مسترد'
    PARTIALLY_REFUNDED = 'partially_refunded', 'مسترد جزئياً'
    FAILED = 'failed', 'فشل الدفع'
    CANCELLED = 'cancelled', 'ملغي'


class PaymentMethod(models.TextChoices):
    """طرق الدفع"""
    CARD = 'card', 'بطاقة ائتمان'
    MADA = 'mada', 'مدى'
    APPLE_PAY = 'apple_pay', 'Apple Pay'
    STC_PAY = 'stc_pay', 'STC Pay'
    BANK_TRANSFER = 'bank_transfer', 'تحويل بنكي'
    CASH = 'cash', 'دفع عند الاستلام'
    WALLET = 'wallet', 'المحفظة'
    CREDIT = 'credit', 'الدفع الآجل'


class DeliveryType(models.TextChoices):
    """أنواع التوصيل"""
    STANDARD = 'standard', 'توصيل عادي'
    EXPRESS = 'express', 'توصيل سريع'
    SAME_DAY = 'same_day', 'نفس اليوم'
    SCHEDULED = 'scheduled', 'موعد محدد'
    PICKUP = 'pickup', 'استلام من المتجر'
    CRANE = 'crane', 'توصيل بالرافعة'
    TRUCK = 'truck', 'شاحنة كبيرة'


class CancellationReason(models.TextChoices):
    """أسباب الإلغاء"""
    CUSTOMER_REQUEST = 'customer_request', 'طلب العميل'
    OUT_OF_STOCK = 'out_of_stock', 'نفاد المخزون'
    PAYMENT_FAILED = 'payment_failed', 'فشل الدفع'
    VENDOR_UNAVAILABLE = 'vendor_unavailable', 'التاجر غير متاح'
    DELIVERY_ISSUE = 'delivery_issue', 'مشكلة في التوصيل'
    PRICE_CHANGE = 'price_change', 'تغيير السعر'
    DUPLICATE = 'duplicate', 'طلب مكرر'
    FRAUD = 'fraud', 'احتيال'
    OTHER = 'other', 'سبب آخر'


# =============================================
# نموذج الطلب الرئيسي
# =============================================

class Order(models.Model):
    """
    نموذج الطلب الرئيسي

    يمثل طلب واحد يمكن أن يحتوي على عناصر متعددة
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # رقم الطلب للعرض
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رقم الطلب'
    )

    # العلاقات الأساسية
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='العميل'
    )
    vendor = models.ForeignKey(
        'stores.Store',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='المتجر'
    )

    # نوع الطلب
    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.PRODUCT,
        verbose_name='نوع الطلب'
    )

    # الحالة
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
        verbose_name='الحالة'
    )
    previous_status = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='الحالة السابقة'
    )
    status_changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='وقت تغيير الحالة'
    )

    # الدفع
    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='حالة الدفع'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True,
        verbose_name='طريقة الدفع'
    )

    # المبالغ
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='المجموع الفرعي'
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='رسوم التوصيل'
    )
    service_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='رسوم الخدمة'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='الخصم'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='الضريبة'
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='المبلغ الإجمالي'
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='المبلغ المدفوع'
    )

    # العمولات
    vendor_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='عمولة التاجر'
    )
    driver_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='عمولة السائق'
    )
    platform_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='عمولة المنصة'
    )

    # الكوبون
    coupon_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='كود الخصم'
    )
    coupon_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='خصم الكوبون'
    )

    # التوصيل
    delivery_type = models.CharField(
        max_length=20,
        choices=DeliveryType.choices,
        default=DeliveryType.STANDARD,
        verbose_name='نوع التوصيل'
    )
    delivery_address = models.ForeignKey(
        'users.UserAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='عنوان التوصيل'
    )
    delivery_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات التوصيل'
    )
    scheduled_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ التوصيل المحدد'
    )
    scheduled_delivery_time = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='وقت التوصيل المحدد'
    )

    # التوقيت
    placed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت تأكيد الطلب'
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت التأكيد'
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت القبول'
    )
    prepared_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت التجهيز'
    )
    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الشحن'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت التوصيل'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الاكتمال'
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الإلغاء'
    )

    # الإلغاء
    cancellation_reason = models.CharField(
        max_length=30,
        choices=CancellationReason.choices,
        blank=True,
        verbose_name='سبب الإلغاء'
    )
    cancellation_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات الإلغاء'
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_orders',
        verbose_name='ألغي بواسطة'
    )

    # الملاحظات
    customer_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات العميل'
    )
    vendor_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات التاجر'
    )
    internal_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات داخلية'
    )

    # العملة
    currency = models.CharField(
        max_length=3,
        default='SAR',
        verbose_name='العملة'
    )

    # المصدر
    source = models.CharField(
        max_length=20,
        default='app',
        verbose_name='المصدر'
    )
    device_type = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='نوع الجهاز'
    )

    # بيانات إضافية
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات إضافية'
    )

    # للخدمات والتأجير
    service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الخدمة'
    )
    service_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='وقت الخدمة'
    )
    rental_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='بداية التأجير'
    )
    rental_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='نهاية التأجير'
    )

    # التتبع
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP العميل'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )

    class Meta:
        db_table = 'orders'
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['vendor', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f'طلب #{self.order_number}'

    def save(self, *args, **kwargs):
        # توليد رقم الطلب
        if not self.order_number:
            self.order_number = self._generate_order_number()

        # حساب المجموع
        self.calculate_totals()

        super().save(*args, **kwargs)

    def _generate_order_number(self) -> str:
        """توليد رقم طلب فريد"""
        import random
        from django.utils import timezone

        prefix = timezone.now().strftime('%y%m')
        suffix = random.randint(10000, 99999)
        return f'DW{prefix}{suffix}'

    def calculate_totals(self):
        """حساب المجاميع"""
        # المجموع الفرعي من العناصر
        items_total = sum(
            item.total_price for item in self.items.all()
        ) if self.pk else Decimal('0')

        self.subtotal = items_total
        self.tax_amount = (self.subtotal * Decimal('0.15')).quantize(Decimal('0.01'))

        self.total_amount = (
            self.subtotal
            + self.delivery_fee
            + self.service_fee
            + self.tax_amount
            - self.discount_amount
            - self.coupon_discount
        )

    def update_status(self, new_status: str, user=None, notes: str = ''):
        """تحديث حالة الطلب"""
        if new_status == self.status:
            return

        self.previous_status = self.status
        self.status = new_status
        self.status_changed_at = timezone.now()

        # تحديث التواريخ المناسبة
        status_timestamps = {
            OrderStatus.CONFIRMED: 'confirmed_at',
            OrderStatus.ACCEPTED: 'accepted_at',
            OrderStatus.PREPARING: 'prepared_at',
            OrderStatus.SHIPPED: 'shipped_at',
            OrderStatus.DELIVERED: 'delivered_at',
            OrderStatus.COMPLETED: 'completed_at',
            OrderStatus.CANCELLED: 'cancelled_at',
        }

        if new_status in status_timestamps:
            setattr(self, status_timestamps[new_status], timezone.now())

        self.save()

        # تسجيل السجل
        OrderStatusHistory.objects.create(
            order=self,
            status=new_status,
            previous_status=self.previous_status,
            changed_by=user,
            notes=notes
        )

    @property
    def can_cancel(self) -> bool:
        """هل يمكن إلغاء الطلب؟"""
        non_cancellable = [
            OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED,
        ]
        return self.status not in non_cancellable

    @property
    def is_paid(self) -> bool:
        """هل تم دفع الطلب؟"""
        return self.payment_status in [
            PaymentStatus.PAID,
            PaymentStatus.CAPTURED
        ]

    @property
    def remaining_amount(self) -> Decimal:
        """المبلغ المتبقي"""
        return self.total_amount - self.paid_amount


# =============================================
# عناصر الطلب
# =============================================

class OrderItem(models.Model):
    """
    عناصر الطلب

    كل عنصر يمثل منتج أو خدمة في الطلب
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الطلب'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='المنتج'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name='المتغير'
    )

    # التسعير
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='سعر الوحدة'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name='الكمية'
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='الخصم'
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='السعر الإجمالي'
    )

    # نوع التسعير
    pricing_type = models.CharField(
        max_length=20,
        default='fixed',
        verbose_name='نوع التسعير'
    )

    # الخيارات المحددة
    selected_options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='الخيارات المحددة'
    )
    options_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='سعر الخيارات'
    )

    # معلومات المنتج وقت الطلب (لحفظ البيانات التاريخية)
    product_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='لقطة المنتج'
    )

    # للتأجير
    rental_days = models.PositiveIntegerField(
        default=0,
        verbose_name='أيام التأجير'
    )
    rental_hours = models.PositiveIntegerField(
        default=0,
        verbose_name='ساعات التأجير'
    )

    # للخدمات
    service_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='تفاصيل الخدمة'
    )

    # الحالة
    is_available = models.BooleanField(
        default=True,
        verbose_name='متاح'
    )
    availability_note = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='ملاحظة التوفر'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'عنصر طلب'
        verbose_name_plural = 'عناصر الطلبات'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        # حساب السعر الإجمالي
        self.total_price = (
            (self.unit_price + self.options_price)
            * self.quantity
            - self.discount
        )

        # حفظ لقطة المنتج
        if not self.product_snapshot and self.product:
            self.product_snapshot = {
                'name': self.product.name,
                'name_en': self.product.name_en,
                'sku': self.product.sku,
                'unit': self.product.unit,
                'image': str(self.product.images.first().image.url) if self.product.images.exists() else '',
            }

        super().save(*args, **kwargs)


# =============================================
# سجل حالات الطلب
# =============================================

class OrderStatusHistory(models.Model):
    """
    سجل تغييرات حالة الطلب
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='الطلب'
    )

    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        verbose_name='الحالة'
    )
    previous_status = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='الحالة السابقة'
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='غُيّر بواسطة'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='وقت التغيير'
    )

    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'سجل حالة'
        verbose_name_plural = 'سجل الحالات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order.order_number}: {self.status}'


# =============================================
# التوصيل
# =============================================

class OrderDelivery(models.Model):
    """
    معلومات توصيل الطلب
    """

    class DeliveryStatus(models.TextChoices):
        """حالات التوصيل"""
        PENDING = 'pending', 'بانتظار التعيين'
        ASSIGNED = 'assigned', 'تم تعيين سائق'
        PICKED_UP = 'picked_up', 'تم الاستلام'
        IN_TRANSIT = 'in_transit', 'في الطريق'
        ARRIVED = 'arrived', 'وصل للموقع'
        DELIVERED = 'delivered', 'تم التسليم'
        FAILED = 'failed', 'فشل التوصيل'
        RETURNED = 'returned', 'مرتجع'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='delivery',
        verbose_name='الطلب'
    )

    # السائق
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries',
        verbose_name='السائق'
    )

    # الحالة
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        verbose_name='الحالة'
    )

    # رقم التتبع
    tracking_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='رقم التتبع'
    )

    # الموقع الحالي
    current_location = gis_models.PointField(
        null=True,
        blank=True,
        srid=4326,
        verbose_name='الموقع الحالي'
    )
    last_location_update = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر تحديث للموقع'
    )

    # المسافة والوقت
    estimated_distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='المسافة المقدرة (كم)'
    )
    actual_distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='المسافة الفعلية (كم)'
    )
    estimated_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='الوقت المقدر (دقيقة)'
    )
    actual_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='الوقت الفعلي (دقيقة)'
    )

    # التوقيت
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت التعيين'
    )
    picked_up_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الاستلام'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت التسليم'
    )

    # إثبات التسليم
    delivery_photo = models.ImageField(
        upload_to='delivery_proofs/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='صورة التسليم'
    )
    signature = models.ImageField(
        upload_to='delivery_signatures/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='التوقيع'
    )
    recipient_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='اسم المستلم'
    )
    delivery_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات التسليم'
    )

    # محاولات التوصيل
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد المحاولات'
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name='الحد الأقصى للمحاولات'
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر محاولة'
    )
    failure_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='سبب الفشل'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_deliveries'
        verbose_name = 'توصيل طلب'
        verbose_name_plural = 'توصيلات الطلبات'

    def __str__(self):
        return f'توصيل {self.order.order_number}'

    def update_location(self, latitude: float, longitude: float):
        """تحديث الموقع"""
        from django.contrib.gis.geos import Point
        self.current_location = Point(longitude, latitude, srid=4326)
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_location', 'last_location_update'])


# =============================================
# مسار التتبع
# =============================================

class DeliveryTrackingPoint(models.Model):
    """
    نقاط تتبع التوصيل
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    delivery = models.ForeignKey(
        OrderDelivery,
        on_delete=models.CASCADE,
        related_name='tracking_points',
        verbose_name='التوصيل'
    )

    location = gis_models.PointField(
        srid=4326,
        verbose_name='الموقع'
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='خط العرض'
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='خط الطول'
    )
    accuracy = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الدقة (متر)'
    )
    speed = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='السرعة (كم/س)'
    )
    heading = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الاتجاه'
    )

    recorded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='وقت التسجيل'
    )

    class Meta:
        db_table = 'delivery_tracking_points'
        verbose_name = 'نقطة تتبع'
        verbose_name_plural = 'نقاط التتبع'
        ordering = ['recorded_at']

    def save(self, *args, **kwargs):
        if self.location:
            self.longitude = self.location.x
            self.latitude = self.location.y
        super().save(*args, **kwargs)


# =============================================
# تقييمات الطلبات
# =============================================

class OrderReview(models.Model):
    """
    تقييم الطلب
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='الطلب'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='order_reviews',
        verbose_name='العميل'
    )

    # تقييم المتجر
    vendor_rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='تقييم المتجر'
    )
    vendor_comment = models.TextField(
        blank=True,
        verbose_name='تعليق على المتجر'
    )

    # تقييم المنتجات
    products_rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        verbose_name='تقييم المنتجات'
    )
    products_comment = models.TextField(
        blank=True,
        verbose_name='تعليق على المنتجات'
    )

    # تقييم التوصيل
    delivery_rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        verbose_name='تقييم التوصيل'
    )
    delivery_comment = models.TextField(
        blank=True,
        verbose_name='تعليق على التوصيل'
    )

    # صور
    images = models.JSONField(
        default=list,
        blank=True,
        verbose_name='صور التقييم'
    )

    # رد التاجر
    vendor_response = models.TextField(
        blank=True,
        verbose_name='رد التاجر'
    )
    vendor_responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت رد التاجر'
    )

    is_anonymous = models.BooleanField(
        default=False,
        verbose_name='مجهول'
    )
    is_verified_purchase = models.BooleanField(
        default=True,
        verbose_name='عملية شراء مؤكدة'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_reviews'
        verbose_name = 'تقييم طلب'
        verbose_name_plural = 'تقييمات الطلبات'
        ordering = ['-created_at']

    def __str__(self):
        return f'تقييم {self.order.order_number}'

    @property
    def overall_rating(self) -> float:
        """التقييم العام"""
        ratings = [self.vendor_rating]
        if self.products_rating:
            ratings.append(self.products_rating)
        if self.delivery_rating:
            ratings.append(self.delivery_rating)
        return sum(ratings) / len(ratings)


# =============================================
# المبالغ المستردة
# =============================================

# =============================================
# سلة التسوق
# =============================================

class Cart(models.Model):
    """
    سلة التسوق
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='المستخدم'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'
        verbose_name = 'سلة'
        verbose_name_plural = 'السلات'

    def __str__(self):
        return f'سلة {self.user}'

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    """
    عنصر في سلة التسوق
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='السلة'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='المنتج'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='الكمية'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'عنصر سلة'
        verbose_name_plural = 'عناصر السلة'
        unique_together = ['cart', 'product']

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def unit_price(self):
        return self.product.price

    @property
    def total_price(self):
        return self.unit_price * self.quantity


class OrderRefund(models.Model):
    """
    طلبات الاسترداد
    """

    class RefundStatus(models.TextChoices):
        """حالات الاسترداد"""
        REQUESTED = 'requested', 'مطلوب'
        APPROVED = 'approved', 'موافق عليه'
        PROCESSING = 'processing', 'قيد المعالجة'
        COMPLETED = 'completed', 'مكتمل'
        REJECTED = 'rejected', 'مرفوض'
        CANCELLED = 'cancelled', 'ملغي'

    class RefundReason(models.TextChoices):
        """أسباب الاسترداد"""
        DEFECTIVE = 'defective', 'منتج معيب'
        WRONG_ITEM = 'wrong_item', 'منتج خاطئ'
        NOT_AS_DESCRIBED = 'not_as_described', 'لا يطابق الوصف'
        DAMAGED = 'damaged', 'تالف'
        LATE_DELIVERY = 'late_delivery', 'تأخر التوصيل'
        NOT_NEEDED = 'not_needed', 'لم أعد أحتاجه'
        DUPLICATE = 'duplicate', 'طلب مكرر'
        SERVICE_ISSUE = 'service_issue', 'مشكلة في الخدمة'
        OTHER = 'other', 'سبب آخر'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name='الطلب'
    )
    item = models.ForeignKey(
        OrderItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds',
        verbose_name='العنصر'
    )

    # المبلغ
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='المبلغ'
    )

    # الحالة
    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.REQUESTED,
        verbose_name='الحالة'
    )

    # السبب
    reason = models.CharField(
        max_length=30,
        choices=RefundReason.choices,
        verbose_name='السبب'
    )
    reason_details = models.TextField(
        blank=True,
        verbose_name='تفاصيل السبب'
    )

    # الصور
    evidence_images = models.JSONField(
        default=list,
        blank=True,
        verbose_name='صور الإثبات'
    )

    # المعالجة
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='refund_requests',
        verbose_name='طُلب بواسطة'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds',
        verbose_name='عُولج بواسطة'
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name='سبب الرفض'
    )

    # معرف المعاملة
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='معرف المعاملة'
    )

    # التوقيت
    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='وقت الطلب'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الموافقة'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الإكمال'
    )

    class Meta:
        db_table = 'order_refunds'
        verbose_name = 'استرداد'
        verbose_name_plural = 'الاستردادات'
        ordering = ['-requested_at']

    def __str__(self):
        return f'استرداد {self.order.order_number} - {self.amount} ر.س'
