"""
نماذج نظام المستخدمين
=====================

نظام مستخدمين متكامل يدعم:
- المصادقة بالهاتف (OTP)
- المصادقة بالبريد الإلكتروني
- أنواع متعددة من المستخدمين (عميل، تاجر، سائق، مسؤول)
- التحقق من الهوية (KYC)
- إدارة العناوين والأجهزة
"""

import uuid
import hashlib
import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.gis.db import models as gis_models
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


# =============================================
# المدير المخصص للمستخدمين
# =============================================

class UserManager(BaseUserManager):
    """مدير المستخدمين المخصص"""

    def create_user(self, phone_number, password=None, **extra_fields):
        """إنشاء مستخدم عادي"""
        if not phone_number:
            raise ValueError('رقم الهاتف مطلوب')

        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """إنشاء مستخدم مسؤول"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', UserType.ADMIN)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('المسؤول يجب أن يكون is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('المسؤول يجب أن يكون is_superuser=True')

        return self.create_user(phone_number, password, **extra_fields)


# =============================================
# الثوابت والخيارات
# =============================================

class UserType(models.TextChoices):
    """أنواع المستخدمين"""
    CUSTOMER = 'customer', 'عميل'
    VENDOR = 'vendor', 'تاجر'
    DRIVER = 'driver', 'سائق'
    ADMIN = 'admin', 'مسؤول'
    SUPPORT = 'support', 'دعم فني'


class UserStatus(models.TextChoices):
    """حالات المستخدم"""
    ACTIVE = 'active', 'نشط'
    INACTIVE = 'inactive', 'غير نشط'
    SUSPENDED = 'suspended', 'موقوف'
    BANNED = 'banned', 'محظور'
    PENDING = 'pending', 'قيد المراجعة'


class VerificationStatus(models.TextChoices):
    """حالات التحقق"""
    NONE = 'none', 'لم يبدأ'
    PENDING = 'pending', 'قيد المراجعة'
    VERIFIED = 'verified', 'تم التحقق'
    REJECTED = 'rejected', 'مرفوض'
    EXPIRED = 'expired', 'منتهي'


class Gender(models.TextChoices):
    """الجنس"""
    MALE = 'male', 'ذكر'
    FEMALE = 'female', 'أنثى'


class AddressType(models.TextChoices):
    """أنواع العناوين"""
    HOME = 'home', 'المنزل'
    WORK = 'work', 'العمل'
    OTHER = 'other', 'آخر'


class DevicePlatform(models.TextChoices):
    """منصات الأجهزة"""
    IOS = 'ios', 'iOS'
    ANDROID = 'android', 'Android'
    WEB = 'web', 'ويب'


# =============================================
# نموذج المستخدم الرئيسي
# =============================================

phone_validator = RegexValidator(
    regex=r'^(\+966|05|5)\d{8}$',
    message='رقم الهاتف يجب أن يكون سعودي صحيح'
)


class User(AbstractBaseUser, PermissionsMixin):
    """
    نموذج المستخدم المخصص

    يدعم المصادقة برقم الهاتف والبريد الإلكتروني
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # المعلومات الأساسية
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[phone_validator],
        verbose_name='رقم الهاتف'
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='البريد الإلكتروني'
    )

    # الاسم
    first_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='الاسم الأول'
    )
    last_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='اسم العائلة'
    )
    display_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='الاسم المعروض'
    )

    # نوع المستخدم والحالة
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.CUSTOMER,
        verbose_name='نوع المستخدم'
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        verbose_name='الحالة'
    )

    # الصورة الشخصية
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='الصورة الشخصية'
    )
    avatar_url = models.URLField(
        blank=True,
        verbose_name='رابط الصورة'
    )

    # معلومات إضافية
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        verbose_name='الجنس'
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الميلاد'
    )
    national_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='رقم الهوية'
    )

    # التحقق
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تم التحقق'
    )
    phone_verified = models.BooleanField(
        default=False,
        verbose_name='الهاتف مُحقق'
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name='البريد مُحقق'
    )
    identity_verified = models.BooleanField(
        default=False,
        verbose_name='الهوية مُحققة'
    )

    # اللغة والإقليم
    language = models.CharField(
        max_length=10,
        default='ar',
        verbose_name='اللغة'
    )
    timezone = models.CharField(
        max_length=50,
        default='Asia/Riyadh',
        verbose_name='المنطقة الزمنية'
    )

    # الإحصائيات
    orders_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الطلبات'
    )
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الإنفاق'
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name='التقييم'
    )
    ratings_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد التقييمات'
    )

    # النقاط والولاء
    loyalty_points = models.PositiveIntegerField(
        default=0,
        verbose_name='نقاط الولاء'
    )
    loyalty_tier = models.CharField(
        max_length=20,
        default='bronze',
        verbose_name='مستوى الولاء'
    )

    # الإدارة
    is_staff = models.BooleanField(
        default=False,
        verbose_name='موظف'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )

    # التوقيت
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر تسجيل دخول'
    )
    last_activity_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر نشاط'
    )

    # البيانات الإضافية
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات إضافية'
    )

    # Referral
    referral_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name='كود الإحالة'
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        verbose_name='أُحيل بواسطة'
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['user_type', 'status']),
            models.Index(fields=['referral_code']),
        ]

    def __str__(self):
        return self.get_full_name() or self.phone_number

    def get_full_name(self):
        """الاسم الكامل"""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return self.display_name or ''

    def get_short_name(self):
        """الاسم المختصر"""
        return self.first_name or self.display_name or self.phone_number[:4]

    def save(self, *args, **kwargs):
        # توليد كود الإحالة
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()

        # تطبيع رقم الهاتف
        if self.phone_number:
            self.phone_number = self._normalize_phone(self.phone_number)

        super().save(*args, **kwargs)

    def _normalize_phone(self, phone: str) -> str:
        """تطبيع رقم الهاتف للصيغة الدولية"""
        phone = phone.replace(' ', '').replace('-', '')
        if phone.startswith('05'):
            phone = '+966' + phone[1:]
        elif phone.startswith('5'):
            phone = '+966' + phone
        return phone

    def _generate_referral_code(self) -> str:
        """توليد كود إحالة فريد"""
        return secrets.token_urlsafe(6).upper()[:8]

    def update_last_activity(self):
        """تحديث آخر نشاط"""
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])

    @property
    def is_customer(self) -> bool:
        return self.user_type == UserType.CUSTOMER

    @property
    def is_vendor(self) -> bool:
        return self.user_type == UserType.VENDOR

    @property
    def is_driver(self) -> bool:
        return self.user_type == UserType.DRIVER

    @property
    def is_admin_user(self) -> bool:
        return self.user_type == UserType.ADMIN


# =============================================
# ملف تعريف التاجر
# =============================================

class VendorProfile(models.Model):
    """
    ملف تعريف التاجر الإضافي

    يحتوي على معلومات خاصة بالتجار
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='vendor_profile',
        verbose_name='المستخدم'
    )

    # معلومات الشركة
    company_name = models.CharField(
        max_length=200,
        verbose_name='اسم الشركة'
    )
    company_name_en = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='اسم الشركة (إنجليزي)'
    )
    commercial_register = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='السجل التجاري'
    )
    tax_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='الرقم الضريبي'
    )

    # التصنيف
    business_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='نوع النشاط'
    )
    categories = models.JSONField(
        default=list,
        verbose_name='التصنيفات'
    )

    # التحقق
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.NONE,
        verbose_name='حالة التحقق'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ التحقق'
    )
    verification_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات التحقق'
    )

    # المستندات
    commercial_register_doc = models.FileField(
        upload_to='vendor_docs/cr/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='صورة السجل التجاري'
    )
    tax_certificate_doc = models.FileField(
        upload_to='vendor_docs/tax/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='شهادة التسجيل الضريبي'
    )
    id_document = models.FileField(
        upload_to='vendor_docs/id/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='صورة الهوية'
    )

    # الإعدادات
    auto_accept_orders = models.BooleanField(
        default=False,
        verbose_name='قبول الطلبات تلقائياً'
    )
    notification_email = models.EmailField(
        blank=True,
        verbose_name='بريد الإشعارات'
    )

    # الإحصائيات
    total_sales = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي المبيعات'
    )
    total_orders = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الطلبات'
    )
    products_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد المنتجات'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendor_profiles'
        verbose_name = 'ملف تعريف تاجر'
        verbose_name_plural = 'ملفات تعريف التجار'

    def __str__(self):
        return self.company_name


# =============================================
# ملف تعريف السائق
# =============================================

class DriverProfile(models.Model):
    """
    ملف تعريف السائق

    يحتوي على معلومات خاصة بالسائقين
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='driver_profile',
        verbose_name='المستخدم'
    )

    # رخصة القيادة
    license_number = models.CharField(
        max_length=50,
        verbose_name='رقم الرخصة'
    )
    license_expiry = models.DateField(
        verbose_name='تاريخ انتهاء الرخصة'
    )
    license_image = models.ImageField(
        upload_to='driver_docs/license/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='صورة الرخصة'
    )

    # المركبة
    vehicle_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='نوع المركبة'
    )
    vehicle_model = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='موديل المركبة'
    )
    vehicle_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='سنة الصنع'
    )
    vehicle_plate = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='رقم اللوحة'
    )
    vehicle_color = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='لون المركبة'
    )
    vehicle_image = models.ImageField(
        upload_to='driver_docs/vehicle/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='صورة المركبة'
    )

    # التحقق
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.NONE,
        verbose_name='حالة التحقق'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ التحقق'
    )
    background_check_passed = models.BooleanField(
        default=False,
        verbose_name='اجتياز الفحص الأمني'
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

    # الحالة
    is_online = models.BooleanField(
        default=False,
        verbose_name='متصل'
    )
    is_available = models.BooleanField(
        default=False,
        verbose_name='متاح'
    )
    current_order = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='الطلب الحالي'
    )

    # مناطق العمل
    service_areas = models.JSONField(
        default=list,
        verbose_name='مناطق الخدمة'
    )
    max_distance_km = models.PositiveIntegerField(
        default=50,
        verbose_name='أقصى مسافة (كم)'
    )

    # الإحصائيات
    total_deliveries = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد التوصيلات'
    )
    total_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي الأرباح'
    )
    acceptance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        verbose_name='نسبة القبول'
    )
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        verbose_name='نسبة الإكمال'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'driver_profiles'
        verbose_name = 'ملف تعريف سائق'
        verbose_name_plural = 'ملفات تعريف السائقين'

    def __str__(self):
        return f'سائق: {self.user.get_full_name()}'

    def update_location(self, latitude: float, longitude: float):
        """تحديث الموقع"""
        from django.contrib.gis.geos import Point
        self.current_location = Point(longitude, latitude, srid=4326)
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_location', 'last_location_update'])


# =============================================
# العناوين
# =============================================

class UserAddress(models.Model):
    """
    عناوين المستخدم

    يدعم عناوين متعددة مع الإحداثيات
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name='المستخدم'
    )

    # التسمية
    label = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='التسمية'
    )
    address_type = models.CharField(
        max_length=20,
        choices=AddressType.choices,
        default=AddressType.HOME,
        verbose_name='نوع العنوان'
    )

    # العنوان
    street_address = models.CharField(
        max_length=500,
        verbose_name='العنوان'
    )
    building_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='رقم المبنى'
    )
    floor = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='الطابق'
    )
    apartment = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='رقم الشقة'
    )
    landmark = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='علامة مميزة'
    )

    # المدينة والمنطقة
    city = models.CharField(
        max_length=100,
        verbose_name='المدينة'
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='الحي'
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='المنطقة'
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='الرمز البريدي'
    )
    country = models.CharField(
        max_length=100,
        default='المملكة العربية السعودية',
        verbose_name='الدولة'
    )

    # الإحداثيات
    location = gis_models.PointField(
        null=True,
        blank=True,
        srid=4326,
        verbose_name='الموقع'
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name='خط العرض'
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name='خط الطول'
    )

    # العنوان الوطني
    national_address = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='العنوان الوطني'
    )

    # جهة الاتصال
    contact_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='اسم جهة الاتصال'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='هاتف جهة الاتصال'
    )

    # الإعدادات
    is_default = models.BooleanField(
        default=False,
        verbose_name='العنوان الافتراضي'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تم التحقق'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_addresses'
        verbose_name = 'عنوان'
        verbose_name_plural = 'العناوين'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.label or self.address_type} - {self.city}'

    def save(self, *args, **kwargs):
        # تحديث الإحداثيات من الموقع
        if self.location:
            self.longitude = self.location.x
            self.latitude = self.location.y
        elif self.latitude and self.longitude:
            from django.contrib.gis.geos import Point
            self.location = Point(float(self.longitude), float(self.latitude), srid=4326)

        # إلغاء العنوان الافتراضي السابق
        if self.is_default:
            UserAddress.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)

        super().save(*args, **kwargs)


# =============================================
# الأجهزة والجلسات
# =============================================

class UserDevice(models.Model):
    """
    أجهزة المستخدم

    لإدارة Push notifications والجلسات
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name='المستخدم'
    )

    # معرف الجهاز
    device_id = models.CharField(
        max_length=200,
        verbose_name='معرف الجهاز'
    )
    device_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='اسم الجهاز'
    )

    # المنصة
    platform = models.CharField(
        max_length=20,
        choices=DevicePlatform.choices,
        verbose_name='المنصة'
    )
    os_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='إصدار النظام'
    )
    app_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='إصدار التطبيق'
    )

    # Push Notification
    push_token = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='رمز الإشعارات'
    )
    push_enabled = models.BooleanField(
        default=True,
        verbose_name='الإشعارات مفعلة'
    )

    # الحالة
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    last_used_at = models.DateTimeField(
        auto_now=True,
        verbose_name='آخر استخدام'
    )

    # معلومات إضافية
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='عنوان IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_devices'
        verbose_name = 'جهاز'
        verbose_name_plural = 'الأجهزة'
        unique_together = [['user', 'device_id']]

    def __str__(self):
        return f'{self.device_name or self.device_id} ({self.platform})'


class UserSession(models.Model):
    """
    جلسات المستخدم

    لتتبع تسجيلات الدخول
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='المستخدم'
    )
    device = models.ForeignKey(
        UserDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        verbose_name='الجهاز'
    )

    # الرمز
    token_hash = models.CharField(
        max_length=128,
        unique=True,
        verbose_name='هاش الرمز'
    )
    refresh_token_hash = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        verbose_name='هاش رمز التحديث'
    )

    # الصلاحية
    expires_at = models.DateTimeField(
        verbose_name='تاريخ الانتهاء'
    )
    refresh_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ انتهاء التحديث'
    )

    # الحالة
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإلغاء'
    )

    # المعلومات
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='عنوان IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='الموقع'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'جلسة'
        verbose_name_plural = 'الجلسات'
        ordering = ['-created_at']

    def __str__(self):
        return f'جلسة {self.user.phone_number}'

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def revoke(self):
        """إلغاء الجلسة"""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=['is_active', 'revoked_at'])


# =============================================
# رموز التحقق OTP
# =============================================

class OTPCode(models.Model):
    """
    رموز التحقق

    للمصادقة برقم الهاتف والبريد
    """

    class OTPPurpose(models.TextChoices):
        """أغراض OTP"""
        LOGIN = 'login', 'تسجيل دخول'
        REGISTER = 'register', 'تسجيل'
        VERIFY_PHONE = 'verify_phone', 'تحقق من الهاتف'
        VERIFY_EMAIL = 'verify_email', 'تحقق من البريد'
        RESET_PASSWORD = 'reset_password', 'إعادة تعيين كلمة المرور'
        TWO_FACTOR = '2fa', 'المصادقة الثنائية'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # الهدف
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='رقم الهاتف'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='البريد'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='otp_codes',
        verbose_name='المستخدم'
    )

    # الرمز
    code = models.CharField(
        max_length=6,
        verbose_name='الرمز'
    )
    code_hash = models.CharField(
        max_length=128,
        verbose_name='هاش الرمز'
    )

    # الغرض
    purpose = models.CharField(
        max_length=20,
        choices=OTPPurpose.choices,
        verbose_name='الغرض'
    )

    # الصلاحية
    expires_at = models.DateTimeField(
        verbose_name='تاريخ الانتهاء'
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name='مستخدم'
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الاستخدام'
    )

    # المحاولات
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد المحاولات'
    )
    max_attempts = models.PositiveIntegerField(
        default=5,
        verbose_name='الحد الأقصى'
    )

    # المعلومات
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='عنوان IP'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_codes'
        verbose_name = 'رمز تحقق'
        verbose_name_plural = 'رموز التحقق'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'purpose', '-created_at']),
            models.Index(fields=['email', 'purpose', '-created_at']),
        ]

    def __str__(self):
        return f'{self.phone_number or self.email} - {self.purpose}'

    def save(self, *args, **kwargs):
        # حساب هاش الرمز
        if self.code and not self.code_hash:
            self.code_hash = hashlib.sha256(self.code.encode()).hexdigest()

        # تحديد تاريخ الانتهاء
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)

        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired and self.attempts < self.max_attempts

    def verify(self, code: str) -> bool:
        """التحقق من الرمز"""
        if not self.is_valid:
            return False

        self.attempts += 1
        self.save(update_fields=['attempts'])

        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if code_hash == self.code_hash:
            self.is_used = True
            self.used_at = timezone.now()
            self.save(update_fields=['is_used', 'used_at'])
            return True

        return False

    @classmethod
    def generate_code(cls) -> str:
        """توليد رمز عشوائي"""
        import random
        return ''.join(random.choices('0123456789', k=6))
