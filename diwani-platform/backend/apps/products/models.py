"""
نماذج المنتجات
==============

يدعم:
- منتجات المخزون (Stock Products)
- منتجات حسب الطلب (On-Demand Products) - مثل الخرسانة الجاهزة
- تسعير مرن (ثابت، بالساعة، باليوم، بالوحدة، إلخ)
- خيارات ومتغيرات المنتجات
- صور وملفات المنتجات
"""

import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, List

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


# =============================================
# Enums
# =============================================

class ProductType(models.TextChoices):
    """نوع المنتج"""
    STOCK = 'stock', _('منتج مخزون')
    ON_DEMAND = 'on_demand', _('حسب الطلب')
    RENTAL = 'rental', _('تأجير')
    SERVICE = 'service', _('خدمة')


class ProductStatus(models.TextChoices):
    """حالة المنتج"""
    DRAFT = 'draft', _('مسودة')
    ACTIVE = 'active', _('نشط')
    INACTIVE = 'inactive', _('غير نشط')
    OUT_OF_STOCK = 'out_of_stock', _('نفد المخزون')
    DISCONTINUED = 'discontinued', _('متوقف')


class PricingType(models.TextChoices):
    """نوع التسعير"""
    FIXED = 'fixed', _('سعر ثابت')
    PER_UNIT = 'per_unit', _('لكل وحدة')
    PER_HOUR = 'per_hour', _('بالساعة')
    PER_DAY = 'per_day', _('باليوم')
    PER_WEEK = 'per_week', _('بالأسبوع')
    PER_MONTH = 'per_month', _('بالشهر')
    PER_KG = 'per_kg', _('بالكيلوغرام')
    PER_TON = 'per_ton', _('بالطن')
    PER_M3 = 'per_m3', _('بالمتر المكعب')
    PER_M2 = 'per_m2', _('بالمتر المربع')
    PER_METER = 'per_meter', _('بالمتر')
    TIERED = 'tiered', _('متدرج')
    QUOTE = 'quote', _('حسب العرض')


class UnitType(models.TextChoices):
    """وحدة القياس"""
    PIECE = 'piece', _('قطعة')
    PACK = 'pack', _('عبوة')
    BOX = 'box', _('صندوق')
    BAG = 'bag', _('كيس')
    PALLET = 'pallet', _('طبلية')
    KG = 'kg', _('كيلوغرام')
    TON = 'ton', _('طن')
    LITER = 'liter', _('لتر')
    M3 = 'm3', _('متر مكعب')
    M2 = 'm2', _('متر مربع')
    METER = 'meter', _('متر')
    HOUR = 'hour', _('ساعة')
    DAY = 'day', _('يوم')
    WEEK = 'week', _('أسبوع')
    MONTH = 'month', _('شهر')


class DeliveryOption(models.TextChoices):
    """خيارات التوصيل"""
    VENDOR_DELIVERY = 'vendor', _('توصيل التاجر')
    PLATFORM_DELIVERY = 'platform', _('توصيل المنصة')
    CUSTOMER_PICKUP = 'pickup', _('استلام العميل')
    BOTH = 'both', _('توصيل واستلام')


# =============================================
# Abstract Base Model
# =============================================

class TimeStampedModel(models.Model):
    """نموذج أساسي مع التواريخ"""

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        abstract = True


# =============================================
# Category Model
# =============================================

class Category(TimeStampedModel):
    """
    الأقسام - هرمية قابلة للتوسع

    المرحلة 1: لوجستيات (معدات وشاحنات) + مواد البناء
    المستقبل: مزادات، إيجارات، صيانة، استشارات، رخص، إلخ
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # الهيكل الهرمي
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('القسم الأب')
    )
    level = models.PositiveIntegerField(_('المستوى'), default=0)
    path = models.CharField(_('المسار'), max_length=500, blank=True)

    # المعلومات الأساسية
    name = models.CharField(_('الاسم'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)
    slug = models.SlugField(_('الرابط'), max_length=120, unique=True)
    description = models.TextField(_('الوصف'), blank=True)

    # المظهر
    icon = models.CharField(_('الأيقونة'), max_length=50, blank=True)
    image = models.ImageField(
        _('الصورة'),
        upload_to='categories/',
        null=True,
        blank=True
    )
    color = models.CharField(_('اللون'), max_length=7, default='#2196F3')

    # الإعدادات
    is_active = models.BooleanField(_('نشط'), default=True)
    is_featured = models.BooleanField(_('مميز'), default=False)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    # نوع القسم (للتوسع المستقبلي)
    category_type = models.CharField(
        _('نوع القسم'),
        max_length=50,
        default='products',
        choices=[
            ('products', _('منتجات')),
            ('services', _('خدمات')),
            ('rentals', _('تأجير')),
            ('logistics', _('لوجستيات')),
            ('auctions', _('مزادات')),
            ('consultations', _('استشارات')),
        ]
    )

    # إعدادات خاصة بالقسم
    settings = models.JSONField(_('الإعدادات'), default=dict, blank=True)

    # SEO
    meta_title = models.CharField(_('عنوان SEO'), max_length=160, blank=True)
    meta_description = models.TextField(_('وصف SEO'), blank=True)

    class Meta:
        verbose_name = _('قسم')
        verbose_name_plural = _('الأقسام')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['category_type', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # توليد الـ slug
        if not self.slug:
            self.slug = slugify(self.name_en or self.name, allow_unicode=True)

        # حساب المستوى والمسار
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path}/{self.slug}" if self.parent.path else self.slug
        else:
            self.level = 0
            self.path = self.slug

        super().save(*args, **kwargs)

    def get_ancestors(self) -> List['Category']:
        """الحصول على الآباء"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> models.QuerySet:
        """الحصول على الأبناء (كل المستويات)"""
        return Category.objects.filter(path__startswith=f"{self.path}/")


# =============================================
# Product Model
# =============================================

class Product(TimeStampedModel):
    """
    المنتج الرئيسي

    يدعم:
    - منتجات المخزون العادية
    - منتجات حسب الطلب (خرسانة جاهزة، طوب، إلخ)
    - معدات للتأجير
    - خدمات
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # البائع
    vendor = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('المتجر')
    )

    # التصنيف
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('القسم')
    )

    # نوع المنتج
    product_type = models.CharField(
        _('نوع المنتج'),
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.STOCK
    )

    # المعلومات الأساسية
    name = models.CharField(_('اسم المنتج'), max_length=200)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=200, blank=True)
    slug = models.SlugField(_('الرابط'), max_length=220, blank=True)
    sku = models.CharField(_('رمز المنتج'), max_length=50, blank=True)
    barcode = models.CharField(_('الباركود'), max_length=50, blank=True)

    # الوصف
    short_description = models.CharField(_('وصف قصير'), max_length=300, blank=True)
    description = models.TextField(_('الوصف الكامل'), blank=True)

    # التسعير
    pricing_type = models.CharField(
        _('نوع التسعير'),
        max_length=20,
        choices=PricingType.choices,
        default=PricingType.FIXED
    )
    price = models.DecimalField(
        _('السعر'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    compare_at_price = models.DecimalField(
        _('السعر قبل الخصم'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    cost_price = models.DecimalField(
        _('سعر التكلفة'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # إعدادات التسعير المتقدمة (للتسعير المرن)
    pricing_config = models.JSONField(
        _('إعدادات التسعير'),
        default=dict,
        blank=True,
        help_text=_('للتسعير بالساعة/اليوم/الكمية')
    )

    # الوحدة
    unit = models.CharField(
        _('الوحدة'),
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.PIECE
    )
    min_quantity = models.DecimalField(
        _('الحد الأدنى للطلب'),
        max_digits=10,
        decimal_places=2,
        default=1
    )
    max_quantity = models.DecimalField(
        _('الحد الأقصى للطلب'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    quantity_step = models.DecimalField(
        _('خطوة الكمية'),
        max_digits=10,
        decimal_places=2,
        default=1,
        help_text=_('مثال: 0.5 للخرسانة بنصف المتر المكعب')
    )

    # المخزون (لمنتجات المخزون)
    track_inventory = models.BooleanField(_('تتبع المخزون'), default=True)
    stock_quantity = models.DecimalField(
        _('الكمية المتوفرة'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    low_stock_threshold = models.DecimalField(
        _('حد المخزون المنخفض'),
        max_digits=10,
        decimal_places=2,
        default=10
    )
    allow_backorder = models.BooleanField(
        _('السماح بالطلب المسبق'),
        default=False,
        help_text=_('السماح بالطلب حتى لو نفد المخزون')
    )

    # للمنتجات حسب الطلب (On-Demand)
    lead_time_hours = models.PositiveIntegerField(
        _('وقت التجهيز (ساعات)'),
        null=True,
        blank=True,
        help_text=_('الوقت اللازم لتجهيز المنتج')
    )
    production_capacity_daily = models.DecimalField(
        _('الطاقة الإنتاجية اليومية'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    requires_scheduling = models.BooleanField(
        _('يتطلب جدولة'),
        default=False,
        help_text=_('هل يحتاج العميل لتحديد موعد؟')
    )

    # التوصيل
    delivery_option = models.CharField(
        _('خيار التوصيل'),
        max_length=20,
        choices=DeliveryOption.choices,
        default=DeliveryOption.BOTH
    )
    free_delivery = models.BooleanField(_('توصيل مجاني'), default=False)
    delivery_radius_km = models.PositiveIntegerField(
        _('نطاق التوصيل (كم)'),
        null=True,
        blank=True
    )
    delivery_notes = models.TextField(
        _('ملاحظات التوصيل'),
        blank=True,
        help_text=_('معلومات خاصة بالتوصيل')
    )

    # الأبعاد والوزن
    weight = models.DecimalField(
        _('الوزن (كجم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    length = models.DecimalField(
        _('الطول (سم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    width = models.DecimalField(
        _('العرض (سم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    height = models.DecimalField(
        _('الارتفاع (سم)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT
    )
    is_featured = models.BooleanField(_('منتج مميز'), default=False)
    is_new = models.BooleanField(_('منتج جديد'), default=True)

    # الإحصائيات
    views_count = models.PositiveIntegerField(_('عدد المشاهدات'), default=0)
    orders_count = models.PositiveIntegerField(_('عدد الطلبات'), default=0)
    rating = models.DecimalField(
        _('التقييم'),
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    reviews_count = models.PositiveIntegerField(_('عدد التقييمات'), default=0)

    # SEO
    meta_title = models.CharField(_('عنوان SEO'), max_length=160, blank=True)
    meta_description = models.TextField(_('وصف SEO'), blank=True)
    meta_keywords = models.CharField(_('كلمات SEO'), max_length=255, blank=True)

    # إضافي
    tags = models.JSONField(_('الوسوم'), default=list, blank=True)
    metadata = models.JSONField(_('بيانات إضافية'), default=dict, blank=True)

    class Meta:
        verbose_name = _('منتج')
        verbose_name_plural = _('المنتجات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['product_type', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['pricing_type']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['vendor', 'sku'],
                name='unique_vendor_sku',
                condition=models.Q(sku__gt='')
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name_en or self.name, allow_unicode=True)
            self.slug = f"{base_slug}-{str(self.id)[:8]}" if self.id else base_slug

        # تحديث حالة المخزون
        if self.track_inventory and self.stock_quantity <= 0:
            self.status = ProductStatus.OUT_OF_STOCK

        super().save(*args, **kwargs)

    @property
    def is_available(self) -> bool:
        """هل المنتج متاح؟"""
        if self.status != ProductStatus.ACTIVE:
            return False

        if self.product_type == ProductType.STOCK:
            return not self.track_inventory or self.stock_quantity > 0 or self.allow_backorder

        # المنتجات حسب الطلب دائماً متاحة إذا نشطة
        return True

    @property
    def discount_percentage(self) -> Optional[int]:
        """نسبة الخصم"""
        if self.compare_at_price and self.compare_at_price > self.price:
            discount = (self.compare_at_price - self.price) / self.compare_at_price * 100
            return int(discount)
        return None

    def get_price_display(self) -> str:
        """عرض السعر حسب نوع التسعير"""
        unit_labels = {
            PricingType.PER_HOUR: 'ساعة',
            PricingType.PER_DAY: 'يوم',
            PricingType.PER_KG: 'كجم',
            PricingType.PER_TON: 'طن',
            PricingType.PER_M3: 'م³',
            PricingType.PER_M2: 'م²',
            PricingType.PER_METER: 'متر',
        }

        if self.pricing_type == PricingType.QUOTE:
            return 'حسب العرض'

        label = unit_labels.get(self.pricing_type, '')
        if label:
            return f"{self.price} ر.س / {label}"

        return f"{self.price} ر.س"

    def calculate_price(self, quantity: Decimal, context: Optional[Dict] = None) -> Decimal:
        """حساب السعر بناءً على الكمية والسياق"""
        from apps.finance.services import pricing_service

        price, _ = pricing_service.calculate_item_price(
            pricing_type=self.pricing_type,
            base_price=self.price,
            quantity=quantity,
            context=context or {},
            **self.pricing_config
        )
        return price


# =============================================
# Product Variant
# =============================================

class ProductVariant(TimeStampedModel):
    """
    متغيرات المنتج

    مثال: ألوان مختلفة، أحجام، إلخ
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('المنتج')
    )

    # التعريف
    name = models.CharField(_('اسم المتغير'), max_length=100)
    sku = models.CharField(_('رمز المتغير'), max_length=50, blank=True)

    # الخيارات (مثل: اللون: أحمر، الحجم: كبير)
    options = models.JSONField(_('الخيارات'), default=dict)

    # التسعير (يمكن تجاوز سعر المنتج الأصلي)
    price = models.DecimalField(
        _('السعر'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    compare_at_price = models.DecimalField(
        _('السعر قبل الخصم'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # المخزون
    stock_quantity = models.DecimalField(
        _('الكمية المتوفرة'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # الصورة
    image = models.ImageField(
        _('الصورة'),
        upload_to='products/variants/',
        null=True,
        blank=True
    )

    # الحالة
    is_active = models.BooleanField(_('نشط'), default=True)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    class Meta:
        verbose_name = _('متغير المنتج')
        verbose_name_plural = _('متغيرات المنتجات')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def final_price(self) -> Decimal:
        """السعر النهائي"""
        return self.price if self.price else self.product.price


# =============================================
# Product Image
# =============================================

class ProductImage(TimeStampedModel):
    """صور المنتج"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('المنتج')
    )

    image = models.ImageField(_('الصورة'), upload_to='products/')
    alt_text = models.CharField(_('النص البديل'), max_length=200, blank=True)
    is_primary = models.BooleanField(_('صورة رئيسية'), default=False)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    class Meta:
        verbose_name = _('صورة منتج')
        verbose_name_plural = _('صور المنتجات')
        ordering = ['sort_order']

    def save(self, *args, **kwargs):
        # إذا كانت صورة رئيسية، إلغاء الصور الرئيسية الأخرى
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


# =============================================
# Product Specification
# =============================================

class ProductSpecification(TimeStampedModel):
    """مواصفات المنتج التقنية"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='specifications',
        verbose_name=_('المنتج')
    )

    name = models.CharField(_('المواصفة'), max_length=100)
    value = models.CharField(_('القيمة'), max_length=200)
    unit = models.CharField(_('الوحدة'), max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    class Meta:
        verbose_name = _('مواصفة المنتج')
        verbose_name_plural = _('مواصفات المنتجات')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.name}: {self.value}"


# =============================================
# Product Option (للمنتجات حسب الطلب)
# =============================================

class ProductOption(TimeStampedModel):
    """
    خيارات المنتج للمنتجات حسب الطلب

    مثال للخرسانة:
    - نوع الخرسانة (عادية، مقاومة للكبريتات، إلخ)
    - درجة القوة (B250, B300, B350)
    - إضافات (مسرعات، مثبطات، ألياف)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('المنتج')
    )

    name = models.CharField(_('اسم الخيار'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)
    description = models.TextField(_('الوصف'), blank=True)

    option_type = models.CharField(
        _('نوع الخيار'),
        max_length=20,
        choices=[
            ('select', _('اختيار')),
            ('multi_select', _('اختيار متعدد')),
            ('text', _('نص')),
            ('number', _('رقم')),
            ('date', _('تاريخ')),
            ('time', _('وقت')),
        ],
        default='select'
    )

    is_required = models.BooleanField(_('إجباري'), default=False)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    class Meta:
        verbose_name = _('خيار المنتج')
        verbose_name_plural = _('خيارات المنتجات')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductOptionValue(TimeStampedModel):
    """قيم خيارات المنتج"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_('الخيار')
    )

    value = models.CharField(_('القيمة'), max_length=100)
    value_en = models.CharField(_('القيمة بالإنجليزية'), max_length=100, blank=True)

    # السعر الإضافي (إن وجد)
    price_adjustment = models.DecimalField(
        _('تعديل السعر'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('المبلغ المضاف أو المخصوم')
    )

    is_default = models.BooleanField(_('القيمة الافتراضية'), default=False)
    is_active = models.BooleanField(_('نشط'), default=True)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    class Meta:
        verbose_name = _('قيمة خيار')
        verbose_name_plural = _('قيم الخيارات')
        ordering = ['sort_order']

    def __str__(self):
        return self.value


# =============================================
# Product Review
# =============================================

class ProductReview(TimeStampedModel):
    """تقييمات المنتجات"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('المنتج')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        verbose_name=_('المستخدم')
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الطلب')
    )

    rating = models.PositiveSmallIntegerField(
        _('التقييم'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('العنوان'), max_length=200, blank=True)
    comment = models.TextField(_('التعليق'), blank=True)

    # الصور
    images = models.JSONField(_('الصور'), default=list, blank=True)

    # الإعتدال
    is_verified_purchase = models.BooleanField(_('شراء موثق'), default=False)
    is_approved = models.BooleanField(_('معتمد'), default=True)

    # تفاعل البائع
    vendor_reply = models.TextField(_('رد البائع'), blank=True)
    vendor_replied_at = models.DateTimeField(_('تاريخ الرد'), null=True, blank=True)

    # التفاعل
    helpful_count = models.PositiveIntegerField(_('عدد الإعجابات'), default=0)

    class Meta:
        verbose_name = _('تقييم منتج')
        verbose_name_plural = _('تقييمات المنتجات')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_product_review'
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.product.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # تحديث تقييم المنتج
        self.product.update_rating()


# =============================================
# Methods to add to Product
# =============================================

def update_rating(self):
    """تحديث تقييم المنتج"""
    from django.db.models import Avg, Count

    stats = self.reviews.filter(is_approved=True).aggregate(
        avg_rating=Avg('rating'),
        count=Count('id')
    )

    self.rating = stats['avg_rating'] or 0
    self.reviews_count = stats['count']
    self.save(update_fields=['rating', 'reviews_count'])


# إضافة الدالة للنموذج
Product.update_rating = update_rating
