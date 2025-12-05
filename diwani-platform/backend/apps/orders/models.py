"""
===================================
منصة ديواني - Order Models
نماذج الطلبات والسلة
===================================
"""

import uuid
from decimal import Decimal

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings


# ===================================
# Cart Model
# ===================================
class Cart(models.Model):
    """Shopping cart for users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name=_('المستخدم'),
        null=True,
        blank=True
    )

    # Session-based cart for anonymous users
    session_key = models.CharField(
        _('مفتاح الجلسة'),
        max_length=100,
        blank=True,
        null=True
    )

    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name=_('المتجر')
    )

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('سلة التسوق')
        verbose_name_plural = _('سلات التسوق')
        ordering = ['-updated_at']

    def __str__(self):
        if self.user:
            return f"سلة {self.user.full_name} - {self.store.name}"
        return f"سلة مجهولة - {self.store.name}"

    @property
    def items_count(self):
        """Get total items count."""
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        """Calculate subtotal (before delivery)."""
        return sum(item.total_price for item in self.items.all())

    @property
    def delivery_fee(self):
        """Get delivery fee."""
        if self.store.free_delivery_threshold and self.subtotal >= self.store.free_delivery_threshold:
            return Decimal('0.00')
        return self.store.delivery_fee

    @property
    def total(self):
        """Calculate total (with delivery)."""
        return self.subtotal + self.delivery_fee

    def clear(self):
        """Clear all items from cart."""
        self.items.all().delete()

    def merge_with(self, other_cart):
        """Merge another cart into this one."""
        for item in other_cart.items.all():
            existing = self.items.filter(
                product=item.product,
                variant=item.variant
            ).first()

            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                item.cart = self
                item.save()

        other_cart.delete()


# ===================================
# Cart Item Model
# ===================================
class CartItem(models.Model):
    """Items in shopping cart."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('السلة')
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('المنتج')
    )

    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items',
        verbose_name=_('الخيار')
    )

    quantity = models.PositiveIntegerField(
        _('الكمية'),
        default=1,
        validators=[MinValueValidator(1)]
    )

    # Special instructions
    notes = models.TextField(_('ملاحظات'), blank=True)

    created_at = models.DateTimeField(_('تاريخ الإضافة'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('عنصر السلة')
        verbose_name_plural = _('عناصر السلة')
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def unit_price(self):
        """Get unit price (product + variant adjustment)."""
        if self.variant:
            return self.variant.final_price
        return self.product.price

    @property
    def total_price(self):
        """Calculate total price for this item."""
        base = self.unit_price * self.quantity
        # Add addons
        addons_total = sum(
            addon.price * addon.quantity
            for addon in self.addons.all()
        )
        return base + addons_total


# ===================================
# Cart Item Addon Model
# ===================================
class CartItemAddon(models.Model):
    """Addons for cart items."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart_item = models.ForeignKey(
        CartItem,
        on_delete=models.CASCADE,
        related_name='addons',
        verbose_name=_('عنصر السلة')
    )

    addon = models.ForeignKey(
        'products.ProductAddon',
        on_delete=models.CASCADE,
        related_name='cart_item_addons',
        verbose_name=_('الإضافة')
    )

    quantity = models.PositiveIntegerField(_('الكمية'), default=1)

    @property
    def price(self):
        return self.addon.price

    class Meta:
        verbose_name = _('إضافة لعنصر السلة')
        verbose_name_plural = _('إضافات عناصر السلة')


# ===================================
# Order Model
# ===================================
class Order(models.Model):
    """Main order model."""

    class OrderStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        CONFIRMED = 'confirmed', _('تم التأكيد')
        PREPARING = 'preparing', _('جاري التحضير')
        READY = 'ready', _('جاهز للاستلام')
        PICKED_UP = 'picked_up', _('تم الاستلام من المتجر')
        ON_THE_WAY = 'on_the_way', _('في الطريق')
        DELIVERED = 'delivered', _('تم التوصيل')
        CANCELLED = 'cancelled', _('ملغي')
        REFUNDED = 'refunded', _('مسترد')

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        PAID = 'paid', _('مدفوع')
        FAILED = 'failed', _('فشل')
        REFUNDED = 'refunded', _('مسترد')
        PARTIALLY_REFUNDED = 'partially_refunded', _('مسترد جزئياً')

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('الدفع عند الاستلام')
        CARD = 'card', _('بطاقة ائتمان')
        MADA = 'mada', _('مدى')
        APPLE_PAY = 'apple_pay', _('Apple Pay')
        WALLET = 'wallet', _('المحفظة')

    class DeliveryType(models.TextChoices):
        DELIVERY = 'delivery', _('توصيل')
        PICKUP = 'pickup', _('استلام من المتجر')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Order Number (Human readable)
    order_number = models.CharField(
        _('رقم الطلب'),
        max_length=20,
        unique=True,
        editable=False
    )

    # Customer
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name=_('العميل')
    )

    # Store
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name=_('المتجر')
    )

    # Status
    status = models.CharField(
        _('حالة الطلب'),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    # Payment
    payment_status = models.CharField(
        _('حالة الدفع'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    payment_method = models.CharField(
        _('طريقة الدفع'),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )

    # Delivery
    delivery_type = models.CharField(
        _('نوع التوصيل'),
        max_length=15,
        choices=DeliveryType.choices,
        default=DeliveryType.DELIVERY
    )

    # Delivery Address
    delivery_address = models.ForeignKey(
        'accounts.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('عنوان التوصيل')
    )

    # Snapshot of delivery address (in case original is deleted/modified)
    delivery_address_text = models.TextField(_('نص العنوان'), blank=True)

    delivery_location = gis_models.PointField(
        _('موقع التوصيل'),
        geography=True,
        null=True,
        blank=True
    )

    # Driver
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders',
        verbose_name=_('السائق')
    )

    # Pricing
    subtotal = models.DecimalField(
        _('المجموع الفرعي'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    delivery_fee = models.DecimalField(
        _('رسوم التوصيل'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    discount_amount = models.DecimalField(
        _('قيمة الخصم'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    tax_amount = models.DecimalField(
        _('الضريبة'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    tip_amount = models.DecimalField(
        _('البقشيش'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    total = models.DecimalField(
        _('الإجمالي'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Coupon
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('كود الخصم')
    )

    # Notes
    customer_notes = models.TextField(_('ملاحظات العميل'), blank=True)
    store_notes = models.TextField(_('ملاحظات المتجر'), blank=True)
    driver_notes = models.TextField(_('ملاحظات السائق'), blank=True)

    # Estimated Times
    estimated_preparation_time = models.PositiveIntegerField(
        _('وقت التحضير المتوقع (دقيقة)'),
        null=True,
        blank=True
    )

    estimated_delivery_time = models.PositiveIntegerField(
        _('وقت التوصيل المتوقع (دقيقة)'),
        null=True,
        blank=True
    )

    # Timestamps
    placed_at = models.DateTimeField(_('وقت الطلب'), auto_now_add=True)
    confirmed_at = models.DateTimeField(_('وقت التأكيد'), null=True, blank=True)
    preparing_at = models.DateTimeField(_('وقت بدء التحضير'), null=True, blank=True)
    ready_at = models.DateTimeField(_('وقت الجاهزية'), null=True, blank=True)
    picked_up_at = models.DateTimeField(_('وقت الاستلام من المتجر'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('وقت التوصيل'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('وقت الإلغاء'), null=True, blank=True)

    # Cancellation
    cancellation_reason = models.TextField(_('سبب الإلغاء'), blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_orders',
        verbose_name=_('ملغي بواسطة')
    )

    # Rating (after delivery)
    is_rated = models.BooleanField(_('تم التقييم'), default=False)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('طلب')
        verbose_name_plural = _('الطلبات')
        ordering = ['-placed_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['store']),
            models.Index(fields=['driver']),
            models.Index(fields=['placed_at']),
        ]

    def __str__(self):
        return f"طلب #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        """Generate unique order number."""
        import random
        import string
        prefix = timezone.now().strftime('%y%m%d')
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"DW{prefix}{suffix}"

    def calculate_total(self):
        """Calculate order total."""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total = self.subtotal + self.delivery_fee + self.tax_amount + self.tip_amount - self.discount_amount
        return self.total

    def confirm(self):
        """Confirm the order."""
        self.status = self.OrderStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at'])

    def start_preparing(self):
        """Start preparing the order."""
        self.status = self.OrderStatus.PREPARING
        self.preparing_at = timezone.now()
        self.save(update_fields=['status', 'preparing_at'])

    def mark_ready(self):
        """Mark order as ready."""
        self.status = self.OrderStatus.READY
        self.ready_at = timezone.now()
        self.save(update_fields=['status', 'ready_at'])

    def assign_driver(self, driver):
        """Assign driver to order."""
        self.driver = driver
        self.status = self.OrderStatus.PICKED_UP
        self.picked_up_at = timezone.now()
        self.save(update_fields=['driver', 'status', 'picked_up_at'])

    def start_delivery(self):
        """Start delivery."""
        self.status = self.OrderStatus.ON_THE_WAY
        self.save(update_fields=['status'])

    def complete(self):
        """Complete the order."""
        self.status = self.OrderStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])

        # Update store stats
        if self.store:
            self.store.total_orders += 1
            self.store.total_sales += self.total
            self.store.save(update_fields=['total_orders', 'total_sales'])

    def cancel(self, reason='', cancelled_by=None):
        """Cancel the order."""
        self.status = self.OrderStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by
        self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'cancelled_by'])


# ===================================
# Order Item Model
# ===================================
class OrderItem(models.Model):
    """Items in an order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('الطلب')
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name=_('المنتج')
    )

    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_('الخيار')
    )

    # Snapshot of product info
    product_name = models.CharField(_('اسم المنتج'), max_length=200)
    product_name_en = models.CharField(_('اسم المنتج بالإنجليزية'), max_length=200, blank=True)
    variant_name = models.CharField(_('اسم الخيار'), max_length=100, blank=True)

    quantity = models.PositiveIntegerField(_('الكمية'), validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        _('سعر الوحدة'),
        max_digits=10,
        decimal_places=2
    )

    # Addons total
    addons_total = models.DecimalField(
        _('مجموع الإضافات'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('عنصر الطلب')
        verbose_name_plural = _('عناصر الطلب')

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def total_price(self):
        """Calculate total price for this item."""
        return (self.unit_price * self.quantity) + self.addons_total


# ===================================
# Order Item Addon Model
# ===================================
class OrderItemAddon(models.Model):
    """Addons for order items (snapshot)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='addons',
        verbose_name=_('عنصر الطلب')
    )

    addon_name = models.CharField(_('اسم الإضافة'), max_length=100)
    addon_name_en = models.CharField(_('اسم الإضافة بالإنجليزية'), max_length=100, blank=True)

    quantity = models.PositiveIntegerField(_('الكمية'), default=1)
    price = models.DecimalField(_('السعر'), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _('إضافة لعنصر الطلب')
        verbose_name_plural = _('إضافات عناصر الطلب')

    def __str__(self):
        return self.addon_name


# ===================================
# Order Status History Model
# ===================================
class OrderStatusHistory(models.Model):
    """Track order status changes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('الطلب')
    )

    status = models.CharField(_('الحالة'), max_length=20)
    notes = models.TextField(_('ملاحظات'), blank=True)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('تم التغيير بواسطة')
    )

    created_at = models.DateTimeField(_('التاريخ'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل حالة الطلب')
        verbose_name_plural = _('سجل حالات الطلبات')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"


# ===================================
# Coupon Model
# ===================================
class Coupon(models.Model):
    """Discount coupons."""

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', _('نسبة مئوية')
        FIXED = 'fixed', _('مبلغ ثابت')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(_('الكود'), max_length=20, unique=True)
    description = models.TextField(_('الوصف'), blank=True)

    discount_type = models.CharField(
        _('نوع الخصم'),
        max_length=15,
        choices=DiscountType.choices
    )

    discount_value = models.DecimalField(
        _('قيمة الخصم'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    min_order_amount = models.DecimalField(
        _('الحد الأدنى للطلب'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    max_discount_amount = models.DecimalField(
        _('الحد الأقصى للخصم'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Restrictions
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name=_('المتجر')
    )

    # Usage limits
    max_uses = models.PositiveIntegerField(_('الحد الأقصى للاستخدام'), null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField(_('الحد الأقصى لكل مستخدم'), default=1)
    used_count = models.PositiveIntegerField(_('عدد مرات الاستخدام'), default=0)

    # Validity
    is_active = models.BooleanField(_('نشط'), default=True)
    valid_from = models.DateTimeField(_('صالح من'))
    valid_until = models.DateTimeField(_('صالح حتى'))

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('كوبون')
        verbose_name_plural = _('الكوبونات')
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        """Check if coupon is valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def calculate_discount(self, order_total):
        """Calculate discount amount for order."""
        if order_total < self.min_order_amount:
            return Decimal('0')

        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = order_total * (self.discount_value / 100)
        else:
            discount = self.discount_value

        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)

        return discount

    def use(self):
        """Mark coupon as used."""
        self.used_count += 1
        self.save(update_fields=['used_count'])
