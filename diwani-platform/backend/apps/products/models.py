"""
===================================
منصة ديواني - Product Models
نماذج المنتجات والتصنيفات
===================================
"""

import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings


# ===================================
# Product Category Model
# ===================================
class ProductCategory(models.Model):
    """Product categories within a store."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='product_categories',
        verbose_name=_('المتجر')
    )

    name = models.CharField(_('الاسم'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)
    slug = models.SlugField(_('المعرف'), allow_unicode=True)

    image = models.ImageField(
        _('الصورة'),
        upload_to='products/categories/%Y/%m/',
        blank=True,
        null=True
    )

    description = models.TextField(_('الوصف'), blank=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('الفئة الأم')
    )

    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)
    is_active = models.BooleanField(_('نشط'), default=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('فئة المنتجات')
        verbose_name_plural = _('فئات المنتجات')
        ordering = ['sort_order', 'name']
        unique_together = ['store', 'slug']

    def __str__(self):
        return f"{self.store.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    @property
    def products_count(self):
        return self.products.filter(is_active=True).count()


# ===================================
# Product Model
# ===================================
class Product(models.Model):
    """Main product model."""

    class ProductStatus(models.TextChoices):
        DRAFT = 'draft', _('مسودة')
        ACTIVE = 'active', _('نشط')
        OUT_OF_STOCK = 'out_of_stock', _('نفذ المخزون')
        DISCONTINUED = 'discontinued', _('متوقف')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Store & Category
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('المتجر')
    )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('الفئة')
    )

    # Basic Info
    name = models.CharField(_('اسم المنتج'), max_length=200)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=200, blank=True)
    slug = models.SlugField(_('المعرف'), allow_unicode=True)

    description = models.TextField(_('الوصف'), blank=True)
    description_en = models.TextField(_('الوصف بالإنجليزية'), blank=True)

    # SKU & Barcode
    sku = models.CharField(_('رمز المنتج'), max_length=50, blank=True)
    barcode = models.CharField(_('الباركود'), max_length=50, blank=True)

    # Images
    image = models.ImageField(
        _('الصورة الرئيسية'),
        upload_to='products/images/%Y/%m/'
    )

    # Pricing
    price = models.DecimalField(
        _('السعر'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    compare_at_price = models.DecimalField(
        _('السعر قبل الخصم'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='السعر الأصلي قبل الخصم'
    )

    cost_price = models.DecimalField(
        _('سعر التكلفة'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='للاستخدام الداخلي فقط'
    )

    # Tax
    is_taxable = models.BooleanField(_('خاضع للضريبة'), default=True)
    tax_rate = models.DecimalField(
        _('نسبة الضريبة'),
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Inventory
    track_inventory = models.BooleanField(_('تتبع المخزون'), default=True)
    stock_quantity = models.PositiveIntegerField(_('الكمية المتوفرة'), default=0)
    low_stock_threshold = models.PositiveIntegerField(
        _('حد التنبيه للمخزون المنخفض'),
        default=10
    )

    # Weight & Dimensions (for shipping)
    weight = models.DecimalField(
        _('الوزن (كجم)'),
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True
    )

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE
    )

    is_active = models.BooleanField(_('نشط'), default=True)
    is_featured = models.BooleanField(_('مميز'), default=False)

    # Availability
    available_from = models.TimeField(_('متاح من'), null=True, blank=True)
    available_until = models.TimeField(_('متاح حتى'), null=True, blank=True)

    # Order Settings
    min_order_quantity = models.PositiveIntegerField(_('الحد الأدنى للطلب'), default=1)
    max_order_quantity = models.PositiveIntegerField(
        _('الحد الأقصى للطلب'),
        null=True,
        blank=True
    )

    # Preparation Time (for restaurants)
    preparation_time = models.PositiveIntegerField(
        _('وقت التحضير (دقيقة)'),
        null=True,
        blank=True
    )

    # Ratings
    rating = models.DecimalField(
        _('التقييم'),
        max_digits=3,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    rating_count = models.PositiveIntegerField(_('عدد التقييمات'), default=0)

    # Statistics
    total_sold = models.PositiveIntegerField(_('إجمالي المبيعات'), default=0)
    view_count = models.PositiveIntegerField(_('عدد المشاهدات'), default=0)

    # SEO
    meta_title = models.CharField(_('عنوان SEO'), max_length=200, blank=True)
    meta_description = models.TextField(_('وصف SEO'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('منتج')
        verbose_name_plural = _('المنتجات')
        ordering = ['-is_featured', '-created_at']
        unique_together = ['store', 'slug']
        indexes = [
            models.Index(fields=['store', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Product.objects.filter(store=self.store, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Update status based on stock
        if self.track_inventory and self.stock_quantity == 0:
            self.status = self.ProductStatus.OUT_OF_STOCK

        super().save(*args, **kwargs)

    @property
    def is_on_sale(self):
        """Check if product is on sale."""
        return self.compare_at_price and self.compare_at_price > self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage."""
        if self.is_on_sale:
            discount = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            return round(discount)
        return 0

    @property
    def final_price(self):
        """Get final price with tax."""
        if self.is_taxable:
            return self.price * (1 + self.tax_rate / 100)
        return self.price

    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if product is low in stock."""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold

    def decrease_stock(self, quantity):
        """Decrease stock quantity."""
        if self.track_inventory:
            if self.stock_quantity < quantity:
                raise ValueError('الكمية المطلوبة غير متوفرة')
            self.stock_quantity -= quantity
            self.total_sold += quantity
            self.save(update_fields=['stock_quantity', 'total_sold'])

    def increase_stock(self, quantity):
        """Increase stock quantity."""
        if self.track_inventory:
            self.stock_quantity += quantity
            self.save(update_fields=['stock_quantity'])


# ===================================
# Product Image Model
# ===================================
class ProductImage(models.Model):
    """Additional product images."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('المنتج')
    )

    image = models.ImageField(
        _('الصورة'),
        upload_to='products/gallery/%Y/%m/'
    )

    alt_text = models.CharField(_('النص البديل'), max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('صورة المنتج')
        verbose_name_plural = _('صور المنتج')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"


# ===================================
# Product Variant Model
# ===================================
class ProductVariant(models.Model):
    """Product variants (size, color, etc)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('المنتج')
    )

    name = models.CharField(_('الاسم'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)

    sku = models.CharField(_('رمز المنتج'), max_length=50, blank=True)

    # Price difference from base product
    price_adjustment = models.DecimalField(
        _('فرق السعر'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='إضافة أو خصم من السعر الأساسي'
    )

    # Stock
    stock_quantity = models.PositiveIntegerField(_('الكمية المتوفرة'), default=0)

    is_active = models.BooleanField(_('نشط'), default=True)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('خيار المنتج')
        verbose_name_plural = _('خيارات المنتج')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def final_price(self):
        """Get variant price."""
        return self.product.price + self.price_adjustment


# ===================================
# Product Addon Model
# ===================================
class ProductAddon(models.Model):
    """Product addons/extras (for restaurants: extra cheese, etc)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='addons',
        verbose_name=_('المنتج')
    )

    name = models.CharField(_('الاسم'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)

    price = models.DecimalField(
        _('السعر'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    is_active = models.BooleanField(_('نشط'), default=True)
    is_required = models.BooleanField(_('إلزامي'), default=False)

    max_quantity = models.PositiveIntegerField(_('الحد الأقصى'), default=5)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('إضافة للمنتج')
        verbose_name_plural = _('إضافات المنتج')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


# ===================================
# Product Addon Group Model
# ===================================
class ProductAddonGroup(models.Model):
    """Group of addons (e.g., "Choose your sauce", "Select toppings")."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='addon_groups',
        verbose_name=_('المنتج')
    )

    name = models.CharField(_('اسم المجموعة'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)

    is_required = models.BooleanField(_('إلزامي'), default=False)

    min_selections = models.PositiveIntegerField(_('الحد الأدنى للاختيار'), default=0)
    max_selections = models.PositiveIntegerField(_('الحد الأقصى للاختيار'), default=1)

    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('مجموعة الإضافات')
        verbose_name_plural = _('مجموعات الإضافات')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


# ===================================
# Addon Group Item Model
# ===================================
class AddonGroupItem(models.Model):
    """Items within an addon group."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    group = models.ForeignKey(
        ProductAddonGroup,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('المجموعة')
    )

    name = models.CharField(_('الاسم'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)

    price = models.DecimalField(
        _('السعر الإضافي'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    is_default = models.BooleanField(_('الخيار الافتراضي'), default=False)
    is_active = models.BooleanField(_('نشط'), default=True)

    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    class Meta:
        verbose_name = _('عنصر المجموعة')
        verbose_name_plural = _('عناصر المجموعة')
        ordering = ['sort_order']

    def __str__(self):
        return self.name


# ===================================
# Product Review Model
# ===================================
class ProductReview(models.Model):
    """Customer reviews for products."""

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

    rating = models.PositiveSmallIntegerField(
        _('التقييم'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField(_('التعليق'), blank=True)

    is_verified = models.BooleanField(_('مشتري موثق'), default=False)
    is_visible = models.BooleanField(_('مرئي'), default=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('تقييم المنتج')
        verbose_name_plural = _('تقييمات المنتجات')
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.full_name} - {self.product.name} ({self.rating})"


# ===================================
# Favorite Product Model
# ===================================
class FavoriteProduct(models.Model):
    """User's favorite products."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_products',
        verbose_name=_('المستخدم')
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('المنتج')
    )

    created_at = models.DateTimeField(_('تاريخ الإضافة'), auto_now_add=True)

    class Meta:
        verbose_name = _('منتج مفضل')
        verbose_name_plural = _('المنتجات المفضلة')
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.product.name}"
