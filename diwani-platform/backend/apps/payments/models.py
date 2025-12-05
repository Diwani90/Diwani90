"""
===================================
منصة ديواني - Payment Models
نماذج المدفوعات والمعاملات المالية
===================================
"""

import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings


# ===================================
# Payment Gateway Model
# ===================================
class PaymentGateway(models.Model):
    """Supported payment gateways configuration."""

    class GatewayType(models.TextChoices):
        MOYASAR = 'moyasar', _('ميسر')
        TAP = 'tap', _('تاب')
        HYPERPAY = 'hyperpay', _('هايبر باي')
        TABBY = 'tabby', _('تابي - تقسيط')
        TAMARA = 'tamara', _('تمارا - تقسيط')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_('الاسم'), max_length=50)
    gateway_type = models.CharField(
        _('نوع البوابة'),
        max_length=20,
        choices=GatewayType.choices,
        unique=True
    )

    # Credentials (encrypted in production)
    api_key = models.CharField(_('مفتاح API'), max_length=255)
    secret_key = models.CharField(_('المفتاح السري'), max_length=255, blank=True)
    publishable_key = models.CharField(_('المفتاح العام'), max_length=255, blank=True)

    # Settings
    is_active = models.BooleanField(_('نشط'), default=True)
    is_sandbox = models.BooleanField(_('وضع الاختبار'), default=True)

    # Supported methods
    supports_mada = models.BooleanField(_('يدعم مدى'), default=True)
    supports_visa = models.BooleanField(_('يدعم فيزا'), default=True)
    supports_mastercard = models.BooleanField(_('يدعم ماستركارد'), default=True)
    supports_apple_pay = models.BooleanField(_('يدعم Apple Pay'), default=False)
    supports_installments = models.BooleanField(_('يدعم التقسيط'), default=False)

    # Fees
    transaction_fee_percent = models.DecimalField(
        _('نسبة الرسوم'),
        max_digits=5,
        decimal_places=2,
        default=2.5
    )
    transaction_fee_fixed = models.DecimalField(
        _('رسوم ثابتة'),
        max_digits=10,
        decimal_places=2,
        default=1.00
    )

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('بوابة الدفع')
        verbose_name_plural = _('بوابات الدفع')

    def __str__(self):
        return self.name


# ===================================
# Payment Transaction Model
# ===================================
class PaymentTransaction(models.Model):
    """Record of all payment transactions."""

    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        PROCESSING = 'processing', _('جاري المعالجة')
        COMPLETED = 'completed', _('مكتمل')
        FAILED = 'failed', _('فشل')
        CANCELLED = 'cancelled', _('ملغي')
        REFUNDED = 'refunded', _('مسترد')
        PARTIALLY_REFUNDED = 'partially_refunded', _('مسترد جزئياً')

    class TransactionType(models.TextChoices):
        PAYMENT = 'payment', _('دفع')
        REFUND = 'refund', _('استرداد')
        PAYOUT = 'payout', _('تحويل للتاجر')

    class PaymentMethod(models.TextChoices):
        MADA = 'mada', _('مدى')
        VISA = 'visa', _('فيزا')
        MASTERCARD = 'mastercard', _('ماستركارد')
        APPLE_PAY = 'apple_pay', _('Apple Pay')
        WALLET = 'wallet', _('المحفظة')
        CASH = 'cash', _('نقدي')
        INSTALLMENT = 'installment', _('تقسيط')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Reference
    transaction_id = models.CharField(
        _('رقم المعاملة'),
        max_length=100,
        unique=True,
        editable=False
    )

    # Relations
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment_transactions',
        verbose_name=_('الطلب')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_transactions',
        verbose_name=_('المستخدم')
    )

    gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
        verbose_name=_('بوابة الدفع')
    )

    # Transaction details
    transaction_type = models.CharField(
        _('نوع المعاملة'),
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.PAYMENT
    )

    payment_method = models.CharField(
        _('طريقة الدفع'),
        max_length=20,
        choices=PaymentMethod.choices
    )

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )

    # Amounts
    amount = models.DecimalField(
        _('المبلغ'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    currency = models.CharField(_('العملة'), max_length=3, default='SAR')

    fee_amount = models.DecimalField(
        _('الرسوم'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    net_amount = models.DecimalField(
        _('المبلغ الصافي'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Gateway response
    gateway_transaction_id = models.CharField(
        _('رقم معاملة البوابة'),
        max_length=255,
        blank=True
    )

    gateway_response = models.JSONField(
        _('استجابة البوابة'),
        default=dict,
        blank=True
    )

    # Card details (masked)
    card_brand = models.CharField(_('نوع البطاقة'), max_length=20, blank=True)
    card_last_four = models.CharField(_('آخر 4 أرقام'), max_length=4, blank=True)

    # Error handling
    error_code = models.CharField(_('رمز الخطأ'), max_length=50, blank=True)
    error_message = models.TextField(_('رسالة الخطأ'), blank=True)

    # Refund reference
    original_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds',
        verbose_name=_('المعاملة الأصلية')
    )

    refunded_amount = models.DecimalField(
        _('المبلغ المسترد'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Timestamps
    initiated_at = models.DateTimeField(_('وقت البدء'), auto_now_add=True)
    completed_at = models.DateTimeField(_('وقت الاكتمال'), null=True, blank=True)

    # IP and metadata
    ip_address = models.GenericIPAddressField(_('عنوان IP'), null=True, blank=True)
    user_agent = models.TextField(_('المتصفح'), blank=True)
    metadata = models.JSONField(_('بيانات إضافية'), default=dict, blank=True)

    class Meta:
        verbose_name = _('معاملة دفع')
        verbose_name_plural = _('معاملات الدفع')
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['order']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        if not self.net_amount:
            self.net_amount = self.amount - self.fee_amount
        super().save(*args, **kwargs)

    @staticmethod
    def generate_transaction_id():
        """Generate unique transaction ID."""
        import random
        import string
        prefix = timezone.now().strftime('%Y%m%d%H%M')
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TXN{prefix}{suffix}"

    def mark_completed(self, gateway_response=None):
        """Mark transaction as completed."""
        self.status = self.TransactionStatus.COMPLETED
        self.completed_at = timezone.now()
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()

    def mark_failed(self, error_code='', error_message=''):
        """Mark transaction as failed."""
        self.status = self.TransactionStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()

    @property
    def is_refundable(self):
        """Check if transaction can be refunded."""
        return (
            self.status == self.TransactionStatus.COMPLETED and
            self.transaction_type == self.TransactionType.PAYMENT and
            self.amount > self.refunded_amount
        )


# ===================================
# Saved Card Model
# ===================================
class SavedCard(models.Model):
    """User's saved payment cards (tokenized)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_cards',
        verbose_name=_('المستخدم')
    )

    gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.CASCADE,
        related_name='saved_cards',
        verbose_name=_('بوابة الدفع')
    )

    # Token (from payment gateway)
    token = models.CharField(_('رمز البطاقة'), max_length=255)

    # Card info (masked)
    card_brand = models.CharField(_('نوع البطاقة'), max_length=20)
    card_last_four = models.CharField(_('آخر 4 أرقام'), max_length=4)
    card_holder_name = models.CharField(_('اسم حامل البطاقة'), max_length=100, blank=True)
    expiry_month = models.CharField(_('شهر الانتهاء'), max_length=2)
    expiry_year = models.CharField(_('سنة الانتهاء'), max_length=4)

    # Settings
    is_default = models.BooleanField(_('البطاقة الافتراضية'), default=False)
    is_active = models.BooleanField(_('نشطة'), default=True)

    created_at = models.DateTimeField(_('تاريخ الإضافة'), auto_now_add=True)
    last_used_at = models.DateTimeField(_('آخر استخدام'), null=True, blank=True)

    class Meta:
        verbose_name = _('بطاقة محفوظة')
        verbose_name_plural = _('البطاقات المحفوظة')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.card_brand} **** {self.card_last_four}"

    def save(self, *args, **kwargs):
        # Ensure only one default card per user
        if self.is_default:
            SavedCard.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


# ===================================
# Vendor Payout Model
# ===================================
class VendorPayout(models.Model):
    """Payouts to vendors/stores."""

    class PayoutStatus(models.TextChoices):
        PENDING = 'pending', _('قيد الانتظار')
        PROCESSING = 'processing', _('جاري التحويل')
        COMPLETED = 'completed', _('مكتمل')
        FAILED = 'failed', _('فشل')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    payout_id = models.CharField(
        _('رقم التحويل'),
        max_length=50,
        unique=True,
        editable=False
    )

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts',
        verbose_name=_('التاجر')
    )

    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='payouts',
        verbose_name=_('المتجر')
    )

    # Amount
    gross_amount = models.DecimalField(
        _('المبلغ الإجمالي'),
        max_digits=12,
        decimal_places=2
    )

    commission_amount = models.DecimalField(
        _('العمولة'),
        max_digits=12,
        decimal_places=2
    )

    net_amount = models.DecimalField(
        _('المبلغ الصافي'),
        max_digits=12,
        decimal_places=2
    )

    # Bank details
    bank_name = models.CharField(_('اسم البنك'), max_length=100)
    iban = models.CharField(_('رقم الآيبان'), max_length=34)
    account_holder_name = models.CharField(_('اسم صاحب الحساب'), max_length=100)

    # Status
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING
    )

    # Period
    period_start = models.DateField(_('بداية الفترة'))
    period_end = models.DateField(_('نهاية الفترة'))
    orders_count = models.PositiveIntegerField(_('عدد الطلبات'), default=0)

    # Reference
    bank_reference = models.CharField(_('مرجع البنك'), max_length=100, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    processed_at = models.DateTimeField(_('تاريخ التحويل'), null=True, blank=True)

    class Meta:
        verbose_name = _('تحويل للتاجر')
        verbose_name_plural = _('تحويلات التجار')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payout_id} - {self.store.name}"

    def save(self, *args, **kwargs):
        if not self.payout_id:
            prefix = timezone.now().strftime('%Y%m')
            suffix = VendorPayout.objects.filter(
                created_at__year=timezone.now().year,
                created_at__month=timezone.now().month
            ).count() + 1
            self.payout_id = f"PO{prefix}{suffix:04d}"
        super().save(*args, **kwargs)


# ===================================
# Installment Plan Model
# ===================================
class InstallmentPlan(models.Model):
    """Installment plans for BNPL (Tabby/Tamara)."""

    class PlanStatus(models.TextChoices):
        ACTIVE = 'active', _('نشط')
        COMPLETED = 'completed', _('مكتمل')
        DEFAULTED = 'defaulted', _('متعثر')
        CANCELLED = 'cancelled', _('ملغي')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    plan_id = models.CharField(_('رقم الخطة'), max_length=100, unique=True)

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='installment_plans',
        verbose_name=_('الطلب')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='installment_plans',
        verbose_name=_('المستخدم')
    )

    gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('مزود التقسيط')
    )

    # Plan details
    total_amount = models.DecimalField(_('المبلغ الإجمالي'), max_digits=10, decimal_places=2)
    installments_count = models.PositiveIntegerField(_('عدد الأقساط'))
    installment_amount = models.DecimalField(_('قيمة القسط'), max_digits=10, decimal_places=2)

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=PlanStatus.choices,
        default=PlanStatus.ACTIVE
    )

    paid_installments = models.PositiveIntegerField(_('الأقساط المدفوعة'), default=0)
    paid_amount = models.DecimalField(_('المبلغ المدفوع'), max_digits=10, decimal_places=2, default=0)

    next_payment_date = models.DateField(_('تاريخ القسط التالي'), null=True)

    gateway_plan_id = models.CharField(_('رقم الخطة في البوابة'), max_length=255, blank=True)

    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('خطة تقسيط')
        verbose_name_plural = _('خطط التقسيط')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plan_id} - {self.installments_count} أقساط"
