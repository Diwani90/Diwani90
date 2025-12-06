"""
نماذج المتاجر
=============

يدعم:
- التاجر كبائع ومقاول في نفس الوقت
- إعداد سهل للمتجر مع صور المنتجات
- ربط مع Tap Connect للمدفوعات
- أنواع متعددة من المتاجر
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


# =============================================
# Enums
# =============================================

class StoreType(models.TextChoices):
    """نوع المتجر"""
    SUPPLIER = 'supplier', _('مورد مواد بناء')
    EQUIPMENT = 'equipment', _('تأجير معدات')
    CONTRACTOR = 'contractor', _('مقاول')
    LOGISTICS = 'logistics', _('خدمات لوجستية')
    MIXED = 'mixed', _('متعدد الخدمات')


class StoreStatus(models.TextChoices):
    """حالة المتجر"""
    PENDING = 'pending', _('قيد المراجعة')
    ACTIVE = 'active', _('نشط')
    SUSPENDED = 'suspended', _('موقوف')
    CLOSED = 'closed', _('مغلق')


class VerificationStatus(models.TextChoices):
    """حالة التحقق"""
    NOT_VERIFIED = 'not_verified', _('غير موثق')
    PENDING = 'pending', _('قيد التحقق')
    VERIFIED = 'verified', _('موثق')
    REJECTED = 'rejected', _('مرفوض')


# =============================================
# Store Model
# =============================================

class Store(models.Model):
    """
    المتجر / البائع

    يمكن أن يكون:
    - مورد مواد بناء
    - شركة تأجير معدات
    - مقاول (خدمات)
    - شركة لوجستيات (شاحنات)
    - متعدد الخدمات
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # المالك
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stores',
        verbose_name=_('المالك')
    )

    # نوع المتجر
    store_type = models.CharField(
        _('نوع المتجر'),
        max_length=20,
        choices=StoreType.choices,
        default=StoreType.SUPPLIER
    )

    # المعلومات الأساسية
    name = models.CharField(_('اسم المتجر'), max_length=200)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=200, blank=True)
    slug = models.SlugField(_('الرابط'), max_length=220, unique=True, blank=True)

    # الوصف
    short_description = models.CharField(_('وصف قصير'), max_length=300, blank=True)
    description = models.TextField(_('الوصف الكامل'), blank=True)

    # الصور
    logo = models.ImageField(
        _('الشعار'),
        upload_to='stores/logos/',
        null=True,
        blank=True
    )
    cover_image = models.ImageField(
        _('صورة الغلاف'),
        upload_to='stores/covers/',
        null=True,
        blank=True
    )

    # بيانات الشركة
    cr_number = models.CharField(
        _('رقم السجل التجاري'),
        max_length=20,
        blank=True
    )
    vat_number = models.CharField(
        _('الرقم الضريبي'),
        max_length=20,
        blank=True
    )
    license_number = models.CharField(
        _('رقم الترخيص'),
        max_length=50,
        blank=True
    )

    # معلومات الاتصال
    phone = models.CharField(_('رقم الهاتف'), max_length=20)
    whatsapp = models.CharField(_('واتساب'), max_length=20, blank=True)
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)
    website = models.URLField(_('الموقع الإلكتروني'), blank=True)

    # العنوان والموقع
    address = models.TextField(_('العنوان'))
    city = models.CharField(_('المدينة'), max_length=100)
    district = models.CharField(_('الحي'), max_length=100, blank=True)
    postal_code = models.CharField(_('الرمز البريدي'), max_length=10, blank=True)

    # الموقع الجغرافي
    location = gis_models.PointField(
        _('الموقع'),
        null=True,
        blank=True,
        srid=4326
    )

    # نطاق التوصيل
    delivery_radius_km = models.PositiveIntegerField(
        _('نطاق التوصيل (كم)'),
        default=50
    )
    delivery_zones = models.JSONField(
        _('مناطق التوصيل'),
        default=list,
        blank=True,
        help_text=_('قائمة المناطق التي يتم التوصيل إليها')
    )

    # إعدادات التوصيل
    free_delivery_threshold = models.DecimalField(
        _('حد التوصيل المجاني'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    offers_free_delivery = models.BooleanField(_('يوفر توصيل مجاني'), default=False)
    offers_pickup = models.BooleanField(_('يوفر استلام من الموقع'), default=True)

    # ساعات العمل
    working_hours = models.JSONField(
        _('ساعات العمل'),
        default=dict,
        blank=True,
        help_text=_('{"saturday": {"open": "08:00", "close": "22:00"}, ...}')
    )
    is_24_hours = models.BooleanField(_('يعمل 24 ساعة'), default=False)

    # الحد الأدنى للطلب
    min_order_amount = models.DecimalField(
        _('الحد الأدنى للطلب'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Tap Connect
    tap_account_id = models.CharField(
        _('معرف حساب Tap'),
        max_length=100,
        blank=True,
        help_text=_('Connected Account ID من Tap')
    )
    tap_account_status = models.CharField(
        _('حالة حساب Tap'),
        max_length=20,
        default='pending',
        choices=[
            ('pending', _('قيد الإعداد')),
            ('active', _('نشط')),
            ('restricted', _('مقيد')),
        ]
    )

    # معلومات البنك (للتحويلات)
    bank_name = models.CharField(_('اسم البنك'), max_length=100, blank=True)
    bank_iban = models.CharField(_('رقم الآيبان'), max_length=34, blank=True)
    bank_account_name = models.CharField(_('اسم صاحب الحساب'), max_length=200, blank=True)

    # الحالة
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=StoreStatus.choices,
        default=StoreStatus.PENDING
    )

    # التوثيق
    verification_status = models.CharField(
        _('حالة التوثيق'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.NOT_VERIFIED
    )
    verified_at = models.DateTimeField(_('تاريخ التوثيق'), null=True, blank=True)
    verification_notes = models.TextField(_('ملاحظات التوثيق'), blank=True)

    # الإحصائيات
    rating = models.DecimalField(
        _('التقييم'),
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    reviews_count = models.PositiveIntegerField(_('عدد التقييمات'), default=0)
    products_count = models.PositiveIntegerField(_('عدد المنتجات'), default=0)
    orders_count = models.PositiveIntegerField(_('عدد الطلبات'), default=0)
    total_sales = models.DecimalField(
        _('إجمالي المبيعات'),
        max_digits=14,
        decimal_places=2,
        default=0
    )

    # الميزات
    is_featured = models.BooleanField(_('متجر مميز'), default=False)
    is_top_rated = models.BooleanField(_('أعلى تقييم'), default=False)

    # إعدادات إضافية
    settings = models.JSONField(_('الإعدادات'), default=dict, blank=True)
    metadata = models.JSONField(_('بيانات إضافية'), default=dict, blank=True)

    # التواريخ
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('متجر')
        verbose_name_plural = _('المتاجر')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['status', 'store_type']),
            models.Index(fields=['city', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['-rating']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name_en or self.name, allow_unicode=True)
            self.slug = f"{base_slug}-{str(self.id)[:8]}" if self.id else base_slug
        super().save(*args, **kwargs)

    @property
    def is_open(self) -> bool:
        """هل المتجر مفتوح الآن؟"""
        if self.is_24_hours:
            return True

        from datetime import datetime
        import pytz

        tz = pytz.timezone('Asia/Riyadh')
        now = datetime.now(tz)
        day_name = now.strftime('%A').lower()

        hours = self.working_hours.get(day_name)
        if not hours:
            return False

        current_time = now.strftime('%H:%M')
        return hours.get('open', '00:00') <= current_time <= hours.get('close', '23:59')

    def update_stats(self):
        """تحديث الإحصائيات"""
        from django.db.models import Avg, Count, Sum

        # تحديث عدد المنتجات
        self.products_count = self.products.filter(status='active').count()

        # تحديث التقييم
        reviews = StoreReview.objects.filter(store=self, is_approved=True)
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        self.rating = stats['avg_rating'] or 0
        self.reviews_count = stats['count']

        self.save(update_fields=['products_count', 'rating', 'reviews_count'])


# =============================================
# Store Documents
# =============================================

class StoreDocument(models.Model):
    """مستندات المتجر للتوثيق"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('المتجر')
    )

    document_type = models.CharField(
        _('نوع المستند'),
        max_length=50,
        choices=[
            ('cr', _('السجل التجاري')),
            ('vat', _('شهادة ضريبة القيمة المضافة')),
            ('license', _('رخصة النشاط')),
            ('id', _('هوية المالك')),
            ('bank', _('شهادة الآيبان')),
            ('other', _('أخرى')),
        ]
    )

    file = models.FileField(_('الملف'), upload_to='stores/documents/')
    name = models.CharField(_('اسم المستند'), max_length=200)
    expires_at = models.DateField(_('تاريخ الانتهاء'), null=True, blank=True)

    is_verified = models.BooleanField(_('موثق'), default=False)
    verified_at = models.DateTimeField(_('تاريخ التوثيق'), null=True, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    created_at = models.DateTimeField(_('تاريخ الرفع'), auto_now_add=True)

    class Meta:
        verbose_name = _('مستند المتجر')
        verbose_name_plural = _('مستندات المتاجر')

    def __str__(self):
        return f"{self.store.name} - {self.get_document_type_display()}"


# =============================================
# Store Review
# =============================================

class StoreReview(models.Model):
    """تقييمات المتاجر"""

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
        verbose_name=_('الطلب')
    )

    rating = models.PositiveSmallIntegerField(
        _('التقييم'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('العنوان'), max_length=200, blank=True)
    comment = models.TextField(_('التعليق'), blank=True)

    # تقييمات فرعية
    delivery_rating = models.PositiveSmallIntegerField(
        _('تقييم التوصيل'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    quality_rating = models.PositiveSmallIntegerField(
        _('تقييم الجودة'),
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

    is_verified_purchase = models.BooleanField(_('شراء موثق'), default=False)
    is_approved = models.BooleanField(_('معتمد'), default=True)

    # رد المتجر
    store_reply = models.TextField(_('رد المتجر'), blank=True)
    replied_at = models.DateTimeField(_('تاريخ الرد'), null=True, blank=True)

    created_at = models.DateTimeField(_('تاريخ التقييم'), auto_now_add=True)

    class Meta:
        verbose_name = _('تقييم متجر')
        verbose_name_plural = _('تقييمات المتاجر')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['store', 'user', 'order'],
                name='unique_store_review_per_order'
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.store.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.store.update_stats()


# =============================================
# Store Service Area
# =============================================

class StoreServiceArea(models.Model):
    """مناطق خدمة المتجر"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='service_areas',
        verbose_name=_('المتجر')
    )

    name = models.CharField(_('اسم المنطقة'), max_length=100)
    city = models.CharField(_('المدينة'), max_length=100)
    districts = models.JSONField(
        _('الأحياء'),
        default=list,
        help_text=_('قائمة الأحياء المخدومة')
    )

    # منطقة جغرافية (Polygon)
    area = gis_models.PolygonField(
        _('المنطقة'),
        null=True,
        blank=True,
        srid=4326
    )

    # رسوم التوصيل لهذه المنطقة
    delivery_fee = models.DecimalField(
        _('رسوم التوصيل'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    min_order = models.DecimalField(
        _('الحد الأدنى للطلب'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(_('نشط'), default=True)

    class Meta:
        verbose_name = _('منطقة خدمة')
        verbose_name_plural = _('مناطق الخدمة')

    def __str__(self):
        return f"{self.store.name} - {self.name}"
