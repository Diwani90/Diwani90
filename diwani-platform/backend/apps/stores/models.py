"""
===================================
منصة ديواني - Store Models
نماذج المتاجر والفئات
===================================
"""

import uuid
from datetime import time

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings


# ===================================
# Store Category Model
# ===================================
class StoreCategory(models.Model):
    """Categories for stores (مطاعم، سوبرماركت، صيدليات، etc)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_('الاسم'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)
    slug = models.SlugField(_('المعرف'), unique=True, allow_unicode=True)

    icon = models.ImageField(
        _('الأيقونة'),
        upload_to='categories/icons/',
        blank=True,
        null=True
    )

    image = models.ImageField(
        _('الصورة'),
        upload_to='categories/images/',
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
    is_featured = models.BooleanField(_('مميز'), default=False)

    # Commission for this category
    commission_rate = models.DecimalField(
        _('نسبة العمولة'),
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('فئة المتاجر')
        verbose_name_plural = _('فئات المتاجر')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    @property
    def full_path(self):
        """Return full category path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


# ===================================
# Store Model
# ===================================
class Store(models.Model):
    """Main store/merchant model."""

    class StoreStatus(models.TextChoices):
        PENDING = 'pending', _('قيد المراجعة')
        ACTIVE = 'active', _('نشط')
        SUSPENDED = 'suspended', _('موقوف')
        CLOSED = 'closed', _('مغلق')

    class StoreType(models.TextChoices):
        RESTAURANT = 'restaurant', _('مطعم')
        GROCERY = 'grocery', _('بقالة')
        SUPERMARKET = 'supermarket', _('سوبرماركت')
        PHARMACY = 'pharmacy', _('صيدلية')
        ELECTRONICS = 'electronics', _('إلكترونيات')
        FASHION = 'fashion', _('أزياء')
        HOME = 'home', _('منزل وحديقة')
        OTHER = 'other', _('أخرى')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Owner
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_stores',
        verbose_name=_('المالك')
    )

    # Basic Info
    name = models.CharField(_('اسم المتجر'), max_length=200)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=200, blank=True)
    slug = models.SlugField(_('المعرف'), unique=True, allow_unicode=True)

    description = models.TextField(_('الوصف'), blank=True)
    description_en = models.TextField(_('الوصف بالإنجليزية'), blank=True)

    # Category
    category = models.ForeignKey(
        StoreCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stores',
        verbose_name=_('الفئة')
    )

    store_type = models.CharField(
        _('نوع المتجر'),
        max_length=20,
        choices=StoreType.choices,
        default=StoreType.OTHER
    )

    # Images
    logo = models.ImageField(
        _('الشعار'),
        upload_to='stores/logos/%Y/%m/',
        blank=True,
        null=True
    )

    cover_image = models.ImageField(
        _('صورة الغلاف'),
        upload_to='stores/covers/%Y/%m/',
        blank=True,
        null=True
    )

    # Contact
    phone_number = models.CharField(_('رقم الجوال'), max_length=15)
    whatsapp_number = models.CharField(_('رقم الواتساب'), max_length=15, blank=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)

    # Location
    address = models.CharField(_('العنوان'), max_length=255)
    city = models.CharField(_('المدينة'), max_length=100)
    district = models.CharField(_('الحي'), max_length=100)

    location = gis_models.PointField(
        _('الموقع الجغرافي'),
        geography=True,
        null=True,
        blank=True
    )

    # Delivery Settings
    delivery_radius_km = models.PositiveIntegerField(
        _('نطاق التوصيل (كم)'),
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )

    min_order_amount = models.DecimalField(
        _('الحد الأدنى للطلب'),
        max_digits=10,
        decimal_places=2,
        default=20.00,
        validators=[MinValueValidator(0)]
    )

    delivery_fee = models.DecimalField(
        _('رسوم التوصيل'),
        max_digits=10,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0)]
    )

    free_delivery_threshold = models.DecimalField(
        _('حد التوصيل المجاني'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='اتركه فارغاً إذا لم يكن هناك توصيل مجاني'
    )

    estimated_delivery_time = models.PositiveIntegerField(
        _('وقت التوصيل المتوقع (دقيقة)'),
        default=30
    )

    # Working Hours
    is_open_24h = models.BooleanField(_('مفتوح 24 ساعة'), default=False)

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=StoreStatus.choices,
        default=StoreStatus.PENDING
    )

    is_open = models.BooleanField(_('مفتوح الآن'), default=True)
    is_featured = models.BooleanField(_('مميز'), default=False)
    is_verified = models.BooleanField(_('موثق'), default=False)

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
    total_orders = models.PositiveIntegerField(_('إجمالي الطلبات'), default=0)
    total_sales = models.DecimalField(
        _('إجمالي المبيعات'),
        max_digits=14,
        decimal_places=2,
        default=0.00
    )

    # Commission
    commission_rate = models.DecimalField(
        _('نسبة العمولة'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='اتركه فارغاً لاستخدام عمولة الفئة'
    )

    # Timestamps
    approved_at = models.DateTimeField(_('تاريخ الاعتماد'), null=True, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('متجر')
        verbose_name_plural = _('المتاجر')
        ordering = ['-is_featured', '-rating', 'name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['city']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Store.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def effective_commission_rate(self):
        """Get effective commission rate."""
        if self.commission_rate is not None:
            return self.commission_rate
        if self.category:
            return self.category.commission_rate
        return settings.DIWANI_SETTINGS['PLATFORM_COMMISSION_PERCENT']

    def is_within_delivery_range(self, latitude, longitude):
        """Check if location is within delivery range."""
        from django.contrib.gis.geos import Point
        from django.contrib.gis.db.models.functions import Distance
        from django.contrib.gis.measure import D

        if not self.location:
            return False

        point = Point(longitude, latitude, srid=4326)
        distance = self.location.distance(point) * 100  # Convert to km approximately

        return distance <= self.delivery_radius_km

    def calculate_delivery_fee(self, latitude, longitude):
        """Calculate delivery fee based on distance."""
        if not self.location:
            return self.delivery_fee

        from django.contrib.gis.geos import Point
        from geopy.distance import geodesic

        customer_location = (latitude, longitude)
        store_location = (self.location.y, self.location.x)
        distance = geodesic(store_location, customer_location).km

        # Base fee + per km fee
        base_fee = settings.DIWANI_SETTINGS['BASE_DELIVERY_FEE']
        per_km_fee = settings.DIWANI_SETTINGS['PER_KM_DELIVERY_FEE']

        return base_fee + (distance * per_km_fee)

    def update_rating(self):
        """Update store rating from reviews."""
        from django.db.models import Avg
        result = self.reviews.aggregate(avg_rating=Avg('rating'))
        if result['avg_rating']:
            self.rating = round(result['avg_rating'], 2)
            self.rating_count = self.reviews.count()
            self.save(update_fields=['rating', 'rating_count'])


# ===================================
# Store Working Hours Model
# ===================================
class StoreWorkingHours(models.Model):
    """Working hours for each day of the week."""

    class Weekday(models.IntegerChoices):
        SUNDAY = 0, _('الأحد')
        MONDAY = 1, _('الإثنين')
        TUESDAY = 2, _('الثلاثاء')
        WEDNESDAY = 3, _('الأربعاء')
        THURSDAY = 4, _('الخميس')
        FRIDAY = 5, _('الجمعة')
        SATURDAY = 6, _('السبت')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='working_hours',
        verbose_name=_('المتجر')
    )

    weekday = models.PositiveSmallIntegerField(
        _('اليوم'),
        choices=Weekday.choices
    )

    opening_time = models.TimeField(_('وقت الفتح'))
    closing_time = models.TimeField(_('وقت الإغلاق'))

    is_closed = models.BooleanField(_('مغلق'), default=False)

    class Meta:
        verbose_name = _('ساعات العمل')
        verbose_name_plural = _('ساعات العمل')
        unique_together = ['store', 'weekday']
        ordering = ['weekday']

    def __str__(self):
        return f"{self.store.name} - {self.get_weekday_display()}"


# ===================================
# Store Gallery Model
# ===================================
class StoreGallery(models.Model):
    """Store images gallery."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='gallery',
        verbose_name=_('المتجر')
    )

    image = models.ImageField(
        _('الصورة'),
        upload_to='stores/gallery/%Y/%m/'
    )

    caption = models.CharField(_('التعليق'), max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(_('الترتيب'), default=0)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('صورة المتجر')
        verbose_name_plural = _('صور المتجر')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.store.name} - Image {self.sort_order}"


# ===================================
# Store Review Model
# ===================================
class StoreReview(models.Model):
    """Customer reviews for stores."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('المتجر')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='store_reviews',
        verbose_name=_('المستخدم')
    )

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='store_reviews',
        verbose_name=_('الطلب')
    )

    rating = models.PositiveSmallIntegerField(
        _('التقييم'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField(_('التعليق'), blank=True)

    # Rating breakdown
    food_rating = models.PositiveSmallIntegerField(
        _('تقييم الطعام'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    service_rating = models.PositiveSmallIntegerField(
        _('تقييم الخدمة'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    delivery_rating = models.PositiveSmallIntegerField(
        _('تقييم التوصيل'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # Store Response
    store_response = models.TextField(_('رد المتجر'), blank=True)
    responded_at = models.DateTimeField(_('تاريخ الرد'), null=True, blank=True)

    is_verified = models.BooleanField(_('تقييم موثق'), default=False)
    is_visible = models.BooleanField(_('مرئي'), default=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('تقييم المتجر')
        verbose_name_plural = _('تقييمات المتاجر')
        ordering = ['-created_at']
        unique_together = ['store', 'user', 'order']

    def __str__(self):
        return f"{self.user.full_name} - {self.store.name} ({self.rating})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update store rating
        self.store.update_rating()


# ===================================
# Favorite Store Model
# ===================================
class FavoriteStore(models.Model):
    """User's favorite stores."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_stores',
        verbose_name=_('المستخدم')
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('المتجر')
    )

    created_at = models.DateTimeField(_('تاريخ الإضافة'), auto_now_add=True)

    class Meta:
        verbose_name = _('متجر مفضل')
        verbose_name_plural = _('المتاجر المفضلة')
        unique_together = ['user', 'store']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.store.name}"
