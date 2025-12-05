"""
===================================
منصة ديواني - User Models
نظام المستخدمين المتقدم
===================================
"""

import uuid
import secrets
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.gis.db import models as gis_models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# ===================================
# Validators
# ===================================
phone_validator = RegexValidator(
    regex=r'^(\+966|966|0)?5[0-9]{8}$',
    message='رقم الجوال يجب أن يكون سعودي صالح (مثال: 0512345678)'
)

national_id_validator = RegexValidator(
    regex=r'^[12][0-9]{9}$',
    message='رقم الهوية يجب أن يكون 10 أرقام ويبدأ بـ 1 أو 2'
)


# ===================================
# User Manager
# ===================================
class UserManager(BaseUserManager):
    """Custom user manager for Diwani platform."""

    def _create_user(self, phone_number, password=None, **extra_fields):
        """Create and save a user with the given phone number."""
        if not phone_number:
            raise ValueError('رقم الجوال مطلوب')

        # Normalize phone number to Saudi format
        phone_number = self.normalize_phone(phone_number)
        user = self.model(phone_number=phone_number, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        """Create a regular user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Create a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('user_type', User.UserType.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone_number, password, **extra_fields)

    @staticmethod
    def normalize_phone(phone_number):
        """Normalize phone number to +966 format."""
        phone = ''.join(filter(str.isdigit, phone_number))

        if phone.startswith('966'):
            phone = phone[3:]
        elif phone.startswith('0'):
            phone = phone[1:]

        return f'+966{phone}'


# ===================================
# User Model
# ===================================
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for Diwani platform.
    Uses phone number as the unique identifier.
    """

    class UserType(models.TextChoices):
        CUSTOMER = 'customer', _('عميل')
        VENDOR = 'vendor', _('تاجر')
        DRIVER = 'driver', _('سائق')
        ADMIN = 'admin', _('مدير')

    class Gender(models.TextChoices):
        MALE = 'male', _('ذكر')
        FEMALE = 'female', _('أنثى')

    # Primary Key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Authentication
    phone_number = models.CharField(
        _('رقم الجوال'),
        max_length=15,
        unique=True,
        validators=[phone_validator],
        help_text='رقم الجوال السعودي'
    )

    email = models.EmailField(
        _('البريد الإلكتروني'),
        blank=True,
        null=True,
        unique=True
    )

    # Profile Information
    first_name = models.CharField(_('الاسم الأول'), max_length=50)
    last_name = models.CharField(_('اسم العائلة'), max_length=50)

    avatar = models.ImageField(
        _('الصورة الشخصية'),
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True
    )

    gender = models.CharField(
        _('الجنس'),
        max_length=10,
        choices=Gender.choices,
        blank=True
    )

    date_of_birth = models.DateField(
        _('تاريخ الميلاد'),
        blank=True,
        null=True
    )

    # User Type
    user_type = models.CharField(
        _('نوع المستخدم'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.CUSTOMER
    )

    # Verification Status
    is_verified = models.BooleanField(
        _('تم التحقق'),
        default=False,
        help_text='تم التحقق من رقم الجوال'
    )

    is_identity_verified = models.BooleanField(
        _('تم التحقق من الهوية'),
        default=False,
        help_text='تم التحقق من الهوية الوطنية'
    )

    national_id = models.CharField(
        _('رقم الهوية'),
        max_length=10,
        blank=True,
        validators=[national_id_validator]
    )

    # Permissions
    is_active = models.BooleanField(_('نشط'), default=True)
    is_staff = models.BooleanField(_('موظف'), default=False)

    # Wallet & Balance
    wallet_balance = models.DecimalField(
        _('رصيد المحفظة'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    # Referral System
    referral_code = models.CharField(
        _('كود الإحالة'),
        max_length=10,
        unique=True,
        blank=True
    )

    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        verbose_name=_('تمت إحالته بواسطة')
    )

    # Settings
    language = models.CharField(
        _('اللغة'),
        max_length=5,
        default='ar',
        choices=[('ar', 'العربية'), ('en', 'English')]
    )

    push_notifications_enabled = models.BooleanField(
        _('تفعيل الإشعارات'),
        default=True
    )

    sms_notifications_enabled = models.BooleanField(
        _('تفعيل رسائل SMS'),
        default=True
    )

    # FCM Token for Push Notifications
    fcm_token = models.TextField(
        _('رمز FCM'),
        blank=True,
        help_text='Firebase Cloud Messaging token'
    )

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    last_login_at = models.DateTimeField(_('آخر تسجيل دخول'), blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمين')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

    def save(self, *args, **kwargs):
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @staticmethod
    def generate_referral_code():
        """Generate unique referral code."""
        while True:
            code = secrets.token_hex(4).upper()
            if not User.objects.filter(referral_code=code).exists():
                return code

    def add_to_wallet(self, amount, description=''):
        """Add amount to wallet balance."""
        from apps.accounts.models import WalletTransaction
        self.wallet_balance += amount
        self.save(update_fields=['wallet_balance'])

        WalletTransaction.objects.create(
            user=self,
            amount=amount,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            description=description
        )

    def deduct_from_wallet(self, amount, description=''):
        """Deduct amount from wallet balance."""
        from apps.accounts.models import WalletTransaction
        if self.wallet_balance < amount:
            raise ValueError('رصيد المحفظة غير كافي')

        self.wallet_balance -= amount
        self.save(update_fields=['wallet_balance'])

        WalletTransaction.objects.create(
            user=self,
            amount=amount,
            transaction_type=WalletTransaction.TransactionType.DEBIT,
            description=description
        )


# ===================================
# OTP Model
# ===================================
class OTP(models.Model):
    """One-Time Password for phone verification."""

    class Purpose(models.TextChoices):
        REGISTRATION = 'registration', _('تسجيل جديد')
        LOGIN = 'login', _('تسجيل دخول')
        PASSWORD_RESET = 'password_reset', _('إعادة تعيين كلمة المرور')
        PHONE_CHANGE = 'phone_change', _('تغيير رقم الجوال')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    phone_number = models.CharField(
        _('رقم الجوال'),
        max_length=15,
        validators=[phone_validator]
    )

    code = models.CharField(_('الرمز'), max_length=6)

    purpose = models.CharField(
        _('الغرض'),
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.LOGIN
    )

    attempts = models.PositiveSmallIntegerField(
        _('عدد المحاولات'),
        default=0
    )

    is_used = models.BooleanField(_('مستخدم'), default=False)

    expires_at = models.DateTimeField(_('تاريخ الانتهاء'))
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('رمز التحقق')
        verbose_name_plural = _('رموز التحقق')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'purpose']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"OTP {self.phone_number} - {self.purpose}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            expiry_minutes = settings.DIWANI_SETTINGS.get('OTP_EXPIRY_MINUTES', 5)
            self.expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if OTP is expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if OTP is still valid."""
        max_attempts = settings.DIWANI_SETTINGS.get('OTP_MAX_ATTEMPTS', 3)
        return not self.is_used and not self.is_expired and self.attempts < max_attempts

    @classmethod
    def generate(cls, phone_number, purpose=Purpose.LOGIN):
        """Generate new OTP for phone number."""
        import random

        # Invalidate old OTPs
        cls.objects.filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)

        # Generate 6-digit code
        otp_length = settings.DIWANI_SETTINGS.get('OTP_LENGTH', 6)
        code = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])

        return cls.objects.create(
            phone_number=phone_number,
            code=code,
            purpose=purpose
        )

    def verify(self, code):
        """Verify OTP code."""
        self.attempts += 1
        self.save(update_fields=['attempts'])

        if not self.is_valid:
            return False, 'رمز التحقق منتهي الصلاحية أو غير صالح'

        if self.code != code:
            return False, 'رمز التحقق غير صحيح'

        self.is_used = True
        self.save(update_fields=['is_used'])
        return True, 'تم التحقق بنجاح'


# ===================================
# Address Model
# ===================================
class Address(models.Model):
    """User addresses for delivery."""

    class AddressType(models.TextChoices):
        HOME = 'home', _('المنزل')
        WORK = 'work', _('العمل')
        OTHER = 'other', _('أخرى')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('المستخدم')
    )

    label = models.CharField(
        _('العنوان المختصر'),
        max_length=50,
        help_text='مثال: المنزل، العمل'
    )

    address_type = models.CharField(
        _('نوع العنوان'),
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.HOME
    )

    # Full Address
    street_address = models.CharField(_('العنوان'), max_length=255)
    building_number = models.CharField(_('رقم المبنى'), max_length=20, blank=True)
    apartment_number = models.CharField(_('رقم الشقة'), max_length=20, blank=True)
    floor = models.CharField(_('الطابق'), max_length=10, blank=True)

    # Area
    city = models.CharField(_('المدينة'), max_length=100)
    district = models.CharField(_('الحي'), max_length=100)
    postal_code = models.CharField(_('الرمز البريدي'), max_length=10, blank=True)

    # Geographic Location (PostGIS)
    location = gis_models.PointField(
        _('الموقع الجغرافي'),
        geography=True,
        null=True,
        blank=True,
        help_text='إحداثيات GPS'
    )

    # Additional Info
    additional_directions = models.TextField(
        _('توجيهات إضافية'),
        blank=True,
        help_text='مثال: بجوار مسجد النور'
    )

    phone_number = models.CharField(
        _('رقم التواصل'),
        max_length=15,
        blank=True,
        validators=[phone_validator]
    )

    is_default = models.BooleanField(_('العنوان الافتراضي'), default=False)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('عنوان')
        verbose_name_plural = _('العناوين')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.label} - {self.user.full_name}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [self.street_address]
        if self.building_number:
            parts.append(f"مبنى {self.building_number}")
        if self.apartment_number:
            parts.append(f"شقة {self.apartment_number}")
        parts.extend([self.district, self.city])
        return '، '.join(filter(None, parts))


# ===================================
# Wallet Transaction Model
# ===================================
class WalletTransaction(models.Model):
    """Track wallet transactions."""

    class TransactionType(models.TextChoices):
        CREDIT = 'credit', _('إيداع')
        DEBIT = 'debit', _('سحب')

    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        COMPLETED = 'completed', _('مكتمل')
        FAILED = 'failed', _('فشل')
        REFUNDED = 'refunded', _('مسترد')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wallet_transactions',
        verbose_name=_('المستخدم')
    )

    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    transaction_type = models.CharField(
        _('نوع العملية'),
        max_length=10,
        choices=TransactionType.choices
    )

    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=TransactionStatus.choices,
        default=TransactionStatus.COMPLETED
    )

    description = models.CharField(
        _('الوصف'),
        max_length=255,
        blank=True
    )

    reference_id = models.CharField(
        _('رقم المرجع'),
        max_length=100,
        blank=True
    )

    balance_after = models.DecimalField(
        _('الرصيد بعد العملية'),
        max_digits=10,
        decimal_places=2,
        null=True
    )

    created_at = models.DateTimeField(_('تاريخ العملية'), auto_now_add=True)

    class Meta:
        verbose_name = _('عملية محفظة')
        verbose_name_plural = _('عمليات المحفظة')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.transaction_type} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.balance_after:
            self.balance_after = self.user.wallet_balance
        super().save(*args, **kwargs)


# ===================================
# Driver Profile Model
# ===================================
class DriverProfile(models.Model):
    """Extended profile for drivers."""

    class VehicleType(models.TextChoices):
        MOTORCYCLE = 'motorcycle', _('دراجة نارية')
        CAR = 'car', _('سيارة')
        VAN = 'van', _('فان')
        TRUCK = 'truck', _('شاحنة')

    class DriverStatus(models.TextChoices):
        PENDING = 'pending', _('قيد المراجعة')
        APPROVED = 'approved', _('معتمد')
        SUSPENDED = 'suspended', _('موقوف')
        REJECTED = 'rejected', _('مرفوض')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile',
        verbose_name=_('المستخدم')
    )

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=DriverStatus.choices,
        default=DriverStatus.PENDING
    )

    is_online = models.BooleanField(_('متصل'), default=False)
    is_available = models.BooleanField(_('متاح للطلبات'), default=True)

    # Vehicle Information
    vehicle_type = models.CharField(
        _('نوع المركبة'),
        max_length=15,
        choices=VehicleType.choices
    )

    vehicle_model = models.CharField(_('موديل المركبة'), max_length=100)
    vehicle_year = models.PositiveSmallIntegerField(_('سنة الصنع'))
    vehicle_color = models.CharField(_('لون المركبة'), max_length=50)
    plate_number = models.CharField(_('رقم اللوحة'), max_length=20, unique=True)

    # Documents
    driving_license = models.ImageField(
        _('رخصة القيادة'),
        upload_to='drivers/licenses/%Y/%m/'
    )

    vehicle_registration = models.ImageField(
        _('استمارة المركبة'),
        upload_to='drivers/registrations/%Y/%m/'
    )

    vehicle_insurance = models.ImageField(
        _('تأمين المركبة'),
        upload_to='drivers/insurance/%Y/%m/',
        blank=True,
        null=True
    )

    # Current Location (Real-time tracking)
    current_location = gis_models.PointField(
        _('الموقع الحالي'),
        geography=True,
        null=True,
        blank=True
    )

    last_location_update = models.DateTimeField(
        _('آخر تحديث للموقع'),
        null=True,
        blank=True
    )

    # Statistics
    total_deliveries = models.PositiveIntegerField(_('إجمالي التوصيلات'), default=0)
    total_earnings = models.DecimalField(
        _('إجمالي الأرباح'),
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    rating = models.DecimalField(
        _('التقييم'),
        max_digits=3,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    rating_count = models.PositiveIntegerField(_('عدد التقييمات'), default=0)

    # Timestamps
    approved_at = models.DateTimeField(_('تاريخ الاعتماد'), null=True, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('ملف السائق')
        verbose_name_plural = _('ملفات السائقين')
        ordering = ['-created_at']

    def __str__(self):
        return f"Driver: {self.user.full_name}"

    def update_location(self, latitude, longitude):
        """Update driver's current location."""
        from django.contrib.gis.geos import Point
        self.current_location = Point(longitude, latitude, srid=4326)
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_location', 'last_location_update'])

    def go_online(self):
        """Set driver as online."""
        self.is_online = True
        self.save(update_fields=['is_online'])

    def go_offline(self):
        """Set driver as offline."""
        self.is_online = False
        self.is_available = False
        self.save(update_fields=['is_online', 'is_available'])


# ===================================
# Vendor Profile Model
# ===================================
class VendorProfile(models.Model):
    """Extended profile for vendors/merchants."""

    class VendorStatus(models.TextChoices):
        PENDING = 'pending', _('قيد المراجعة')
        APPROVED = 'approved', _('معتمد')
        SUSPENDED = 'suspended', _('موقوف')
        REJECTED = 'rejected', _('مرفوض')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='vendor_profile',
        verbose_name=_('المستخدم')
    )

    # Business Information
    business_name = models.CharField(_('اسم النشاط التجاري'), max_length=200)
    business_name_en = models.CharField(
        _('اسم النشاط بالإنجليزية'),
        max_length=200,
        blank=True
    )

    commercial_registration = models.CharField(
        _('السجل التجاري'),
        max_length=20,
        unique=True
    )

    tax_number = models.CharField(
        _('الرقم الضريبي'),
        max_length=15,
        blank=True
    )

    # Documents
    commercial_registration_doc = models.FileField(
        _('وثيقة السجل التجاري'),
        upload_to='vendors/docs/%Y/%m/'
    )

    # Bank Information
    bank_name = models.CharField(_('اسم البنك'), max_length=100, blank=True)
    iban = models.CharField(_('رقم الآيبان'), max_length=30, blank=True)

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=15,
        choices=VendorStatus.choices,
        default=VendorStatus.PENDING
    )

    # Commission
    commission_rate = models.DecimalField(
        _('نسبة العمولة'),
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Statistics
    total_sales = models.DecimalField(
        _('إجمالي المبيعات'),
        max_digits=14,
        decimal_places=2,
        default=0.00
    )

    total_orders = models.PositiveIntegerField(_('إجمالي الطلبات'), default=0)

    # Timestamps
    approved_at = models.DateTimeField(_('تاريخ الاعتماد'), null=True, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('ملف التاجر')
        verbose_name_plural = _('ملفات التجار')
        ordering = ['-created_at']

    def __str__(self):
        return f"Vendor: {self.business_name}"
