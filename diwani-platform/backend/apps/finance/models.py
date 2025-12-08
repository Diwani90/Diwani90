"""
نماذج النظام المالي
====================

نظام سجلات مالية غير قابل للتعديل (Immutable Ledger)
يسجل كل حركة مالية للمراجعة والمطابقة

المبدأ: Tap يحسب، نحن نسجل ونراقب
"""

import hashlib
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


# =============================================================================
# Enums & Choices
# =============================================================================

class TransactionType(models.TextChoices):
    """أنواع المعاملات"""

    # إيرادات
    ORDER_PAYMENT = 'order_payment', 'دفع طلب'
    RENTAL_PAYMENT = 'rental_payment', 'دفع إيجار'
    SERVICE_PAYMENT = 'service_payment', 'دفع خدمة'
    DEPOSIT = 'deposit', 'عربون'

    # عمولات
    PLATFORM_COMMISSION = 'platform_commission', 'عمولة المنصة'
    PAYMENT_FEE = 'payment_fee', 'رسوم الدفع'

    # مصروفات
    VENDOR_PAYOUT = 'vendor_payout', 'تحويل للتاجر'
    DRIVER_PAYOUT = 'driver_payout', 'تحويل للسائق'
    REFUND = 'refund', 'استرداد'

    # تسويات
    ADJUSTMENT = 'adjustment', 'تسوية'
    RECONCILIATION = 'reconciliation', 'مطابقة'


class TransactionStatus(models.TextChoices):
    """حالات المعاملة"""

    PENDING = 'pending', 'قيد الانتظار'
    PROCESSING = 'processing', 'قيد المعالجة'
    COMPLETED = 'completed', 'مكتملة'
    FAILED = 'failed', 'فاشلة'
    CANCELLED = 'cancelled', 'ملغية'
    REFUNDED = 'refunded', 'مستردة'
    DISPUTED = 'disputed', 'متنازع عليها'


class PayoutStatus(models.TextChoices):
    """حالات التحويل"""

    PENDING = 'pending', 'قيد الانتظار'
    SCHEDULED = 'scheduled', 'مجدول'
    PROCESSING = 'processing', 'قيد التحويل'
    COMPLETED = 'completed', 'تم التحويل'
    FAILED = 'failed', 'فشل التحويل'
    ON_HOLD = 'on_hold', 'معلق'


class PricingType(models.TextChoices):
    """أنواع التسعير"""

    FIXED = 'fixed', 'سعر ثابت'
    PER_UNIT = 'per_unit', 'بالوحدة'
    PER_HOUR = 'per_hour', 'بالساعة'
    PER_DAY = 'per_day', 'باليوم'
    PER_WEEK = 'per_week', 'بالأسبوع'
    PER_MONTH = 'per_month', 'بالشهر'
    PER_KM = 'per_km', 'بالكيلومتر'
    PER_TRIP = 'per_trip', 'بالرحلة'
    PER_TON = 'per_ton', 'بالطن'
    PER_CUBIC_METER = 'per_m3', 'بالمتر المكعب'
    QUOTE = 'quote', 'بالاتفاق'
    FREE = 'free', 'مجاني'


class DeliveryPricingType(models.TextChoices):
    """أنواع تسعير التوصيل"""

    FREE = 'free', 'مجاني'
    FIXED = 'fixed', 'ثابت'
    PER_KM = 'per_km', 'بالكيلومتر'
    PER_HOUR = 'per_hour', 'بالساعة'
    PER_DAY = 'per_day', 'باليوم'
    BY_ZONE = 'by_zone', 'حسب المنطقة'
    BY_WEIGHT = 'by_weight', 'حسب الوزن'
    DYNAMIC = 'dynamic', 'ديناميكي'
    MERCHANT_DELIVERY = 'merchant', 'توصيل التاجر'
    CUSTOMER_PICKUP = 'pickup', 'استلام العميل'


# =============================================================================
# Core Financial Models
# =============================================================================

class LedgerEntry(models.Model):
    """
    سجل القيد المحاسبي (غير قابل للتعديل)

    هذا هو السجل الذهبي - لا يُعدَّل أبداً
    أي تصحيح يكون بقيد عكسي جديد
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # التصنيف
    entry_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        verbose_name='نوع القيد',
    )

    # المبالغ
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='المبلغ',
    )
    currency = models.CharField(max_length=3, default='SAR', verbose_name='العملة')

    # الأطراف
    from_account = models.CharField(max_length=100, verbose_name='من حساب')
    to_account = models.CharField(max_length=100, verbose_name='إلى حساب')

    # المرجع
    reference_type = models.CharField(max_length=50, verbose_name='نوع المرجع')
    reference_id = models.CharField(max_length=100, verbose_name='معرف المرجع')

    # البيانات الإضافية
    description = models.TextField(blank=True, verbose_name='الوصف')
    metadata = models.JSONField(default=dict, verbose_name='بيانات إضافية')

    # مصدر البيانات
    source = models.CharField(
        max_length=50,
        default='system',
        verbose_name='المصدر',
        help_text='tap, qoyod, system, manual',
    )
    source_reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='مرجع المصدر',
    )

    # التوقيت
    transaction_date = models.DateTimeField(verbose_name='تاريخ المعاملة')
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت التسجيل')

    # التحقق من السلامة
    checksum = models.CharField(max_length=64, editable=False, verbose_name='Checksum')
    previous_checksum = models.CharField(
        max_length=64,
        blank=True,
        editable=False,
        verbose_name='Checksum السابق',
    )

    class Meta:
        db_table = 'finance_ledger'
        verbose_name = 'قيد محاسبي'
        verbose_name_plural = 'السجل المحاسبي'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['entry_type', '-recorded_at']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['from_account', '-recorded_at']),
            models.Index(fields=['to_account', '-recorded_at']),
        ]

    def save(self, *args, **kwargs):
        """حفظ مع حساب Checksum"""
        if not self.checksum:
            self.checksum = self._calculate_checksum()
        super().save(*args, **kwargs)

    def _calculate_checksum(self) -> str:
        """حساب checksum للتحقق من السلامة"""
        data = f"{self.entry_type}:{self.amount}:{self.from_account}:{self.to_account}:{self.reference_id}:{self.transaction_date.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """التحقق من سلامة القيد"""
        return self.checksum == self._calculate_checksum()

    def __str__(self):
        return f"{self.entry_type} - {self.amount} {self.currency}"


class Transaction(models.Model):
    """
    المعاملة المالية

    تمثل عملية مالية واحدة (دفع، استرداد، تحويل)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # النوع والحالة
    type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        verbose_name='النوع',
    )
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name='الحالة',
    )

    # المبالغ
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='المبلغ الإجمالي',
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='المبلغ الصافي',
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='رسوم المنصة',
    )
    payment_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='رسوم الدفع',
    )
    vat_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='ضريبة القيمة المضافة',
    )
    currency = models.CharField(max_length=3, default='SAR')

    # الأطراف
    payer_type = models.CharField(max_length=50, verbose_name='نوع الدافع')
    payer_id = models.IntegerField(verbose_name='معرف الدافع')
    payee_type = models.CharField(max_length=50, verbose_name='نوع المستلم')
    payee_id = models.IntegerField(verbose_name='معرف المستلم')

    # المرجع
    order_id = models.IntegerField(null=True, blank=True, verbose_name='معرف الطلب')
    booking_id = models.IntegerField(null=True, blank=True, verbose_name='معرف الحجز')

    # بيانات مزود الدفع
    payment_provider = models.CharField(
        max_length=50,
        default='tap',
        verbose_name='مزود الدفع',
    )
    provider_transaction_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='معرف المزود',
    )
    provider_response = models.JSONField(
        default=dict,
        verbose_name='استجابة المزود',
    )

    # طريقة الدفع
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='طريقة الدفع',
    )
    card_last_four = models.CharField(
        max_length=4,
        blank=True,
        verbose_name='آخر 4 أرقام',
    )
    card_brand = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='نوع البطاقة',
    )

    # التوقيت
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # البيانات الإضافية
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    # الروابط
    ledger_entries = models.ManyToManyField(
        LedgerEntry,
        blank=True,
        related_name='transactions',
    )

    class Meta:
        db_table = 'finance_transactions'
        verbose_name = 'معاملة مالية'
        verbose_name_plural = 'المعاملات المالية'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payer_type', 'payer_id']),
            models.Index(fields=['payee_type', 'payee_id']),
            models.Index(fields=['order_id']),
            models.Index(fields=['provider_transaction_id']),
        ]

    def __str__(self):
        return f"{self.type} - {self.gross_amount} {self.currency}"


class CommissionRule(models.Model):
    """
    قواعد العمولة

    تحدد نسب العمولة حسب الفئة والتاجر والمنتج
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, verbose_name='اسم القاعدة')
    description = models.TextField(blank=True, verbose_name='الوصف')

    # النطاق
    applies_to = models.CharField(
        max_length=50,
        default='all',
        verbose_name='ينطبق على',
        help_text='all, category, store, product',
    )
    category_id = models.IntegerField(null=True, blank=True)
    store_id = models.IntegerField(null=True, blank=True)
    product_id = models.IntegerField(null=True, blank=True)

    # النسب
    platform_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        verbose_name='نسبة المنصة %',
    )
    fixed_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='رسوم ثابتة',
    )

    # الحدود
    min_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name='الحد الأدنى للعمولة',
    )
    max_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الحد الأقصى للعمولة',
    )

    # الأولوية (الأعلى تُطبَّق أولاً)
    priority = models.IntegerField(default=0, verbose_name='الأولوية')

    # الحالة
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_commission_rules'
        verbose_name = 'قاعدة عمولة'
        verbose_name_plural = 'قواعد العمولة'
        ordering = ['-priority', '-created_at']

    def calculate_commission(self, amount: Decimal) -> Decimal:
        """حساب العمولة"""
        commission = (amount * self.platform_percentage / 100) + self.fixed_fee

        if commission < self.min_commission:
            commission = self.min_commission

        if self.max_commission and commission > self.max_commission:
            commission = self.max_commission

        return commission.quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.name} ({self.platform_percentage}%)"


class VendorBalance(models.Model):
    """
    رصيد التاجر/السائق

    يتتبع الرصيد المتاح للتحويل
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # المالك
    owner_type = models.CharField(
        max_length=50,
        verbose_name='نوع المالك',
        help_text='vendor, driver',
    )
    owner_id = models.IntegerField(verbose_name='معرف المالك')

    # الأرصدة
    available_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد المتاح',
    )
    pending_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد المعلق',
    )
    reserved_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد المحجوز',
    )
    total_earned = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='إجمالي الأرباح',
    )
    total_withdrawn = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='إجمالي المسحوب',
    )
    currency = models.CharField(max_length=3, default='SAR')

    # الإعدادات
    auto_payout = models.BooleanField(default=True, verbose_name='تحويل تلقائي')
    payout_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00'),
        verbose_name='حد التحويل',
    )
    payout_schedule = models.CharField(
        max_length=20,
        default='weekly',
        verbose_name='جدول التحويل',
        help_text='daily, weekly, biweekly, monthly',
    )

    # بيانات البنك
    bank_name = models.CharField(max_length=100, blank=True, verbose_name='اسم البنك')
    bank_account_name = models.CharField(max_length=200, blank=True, verbose_name='اسم صاحب الحساب')
    bank_iban = models.CharField(max_length=34, blank=True, verbose_name='IBAN')

    # التحديث
    last_payout_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_vendor_balances'
        verbose_name = 'رصيد تاجر'
        verbose_name_plural = 'أرصدة التجار'
        unique_together = [['owner_type', 'owner_id']]

    def __str__(self):
        return f"{self.owner_type}:{self.owner_id} - {self.available_balance} {self.currency}"


class Payout(models.Model):
    """
    طلب تحويل/سحب

    تتبع عمليات التحويل للتجار والسائقين
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # المستفيد
    balance = models.ForeignKey(
        VendorBalance,
        on_delete=models.PROTECT,
        related_name='payouts',
        verbose_name='الرصيد',
    )

    # المبلغ
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='المبلغ',
    )
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='رسوم التحويل',
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='المبلغ الصافي',
    )
    currency = models.CharField(max_length=3, default='SAR')

    # الحالة
    status = models.CharField(
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
        verbose_name='الحالة',
    )

    # طريقة التحويل
    method = models.CharField(
        max_length=50,
        default='bank_transfer',
        verbose_name='طريقة التحويل',
    )
    destination = models.JSONField(
        default=dict,
        verbose_name='وجهة التحويل',
    )

    # بيانات المزود
    provider = models.CharField(max_length=50, default='tap', verbose_name='مزود التحويل')
    provider_payout_id = models.CharField(max_length=200, blank=True)
    provider_response = models.JSONField(default=dict)

    # التوقيت
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # الموافقة
    requires_approval = models.BooleanField(default=False)
    approved_by = models.IntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # الملاحظات
    notes = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'finance_payouts'
        verbose_name = 'تحويل'
        verbose_name_plural = 'التحويلات'
        ordering = ['-requested_at']

    def __str__(self):
        return f"Payout {self.id} - {self.amount} {self.currency}"


class ReconciliationRecord(models.Model):
    """
    سجل المطابقة

    يسجل نتائج مطابقة بياناتنا مع بيانات مزود الدفع
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # الفترة
    period_start = models.DateTimeField(verbose_name='بداية الفترة')
    period_end = models.DateTimeField(verbose_name='نهاية الفترة')

    # المصدر
    provider = models.CharField(max_length=50, verbose_name='المزود')
    provider_report_id = models.CharField(max_length=200, blank=True)

    # الملخص - جانبنا
    our_total_transactions = models.IntegerField(default=0)
    our_total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    our_total_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # الملخص - جانب المزود
    provider_total_transactions = models.IntegerField(default=0)
    provider_total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    provider_total_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # الفروقات
    amount_difference = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_count_difference = models.IntegerField(default=0)
    fee_difference = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # الحالة
    is_matched = models.BooleanField(default=False, verbose_name='متطابق')
    discrepancies = models.JSONField(default=list, verbose_name='التناقضات')

    # المراجعة
    reviewed_by = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_reconciliation'
        verbose_name = 'سجل مطابقة'
        verbose_name_plural = 'سجلات المطابقة'
        ordering = ['-period_end']

    def __str__(self):
        status = "✓" if self.is_matched else "✗"
        return f"{status} {self.provider} - {self.period_start.date()} to {self.period_end.date()}"


# =============================================================================
# Pricing Models
# =============================================================================

class PricingRule(models.Model):
    """
    قواعد التسعير المرنة

    تدعم التسعير بالساعة، اليوم، المسافة، أو مجاني
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, verbose_name='اسم القاعدة')

    # النوع
    pricing_type = models.CharField(
        max_length=20,
        choices=PricingType.choices,
        default=PricingType.FIXED,
        verbose_name='نوع التسعير',
    )

    # الأسعار
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='السعر الأساسي',
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر الوحدة',
    )

    # الحدود
    min_units = models.IntegerField(default=1, verbose_name='الحد الأدنى للوحدات')
    max_units = models.IntegerField(null=True, blank=True, verbose_name='الحد الأقصى')
    min_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الحد الأدنى للسعر',
    )

    # التسعير المتدرج
    tiered_pricing = models.JSONField(
        default=list,
        verbose_name='التسعير المتدرج',
        help_text='[{"from": 0, "to": 10, "price": 50}, {"from": 10, "to": 20, "price": 40}]',
    )

    # ساعات الذروة
    peak_hours_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name='معامل ساعات الذروة',
    )
    peak_hours = models.JSONField(
        default=list,
        verbose_name='ساعات الذروة',
        help_text='[{"start": "16:00", "end": "19:00", "days": [0,1,2,3,4]}]',
    )

    # الحالة
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_pricing_rules'
        verbose_name = 'قاعدة تسعير'
        verbose_name_plural = 'قواعد التسعير'

    def calculate_price(
        self,
        units: int = 1,
        duration_hours: float = 0,
        distance_km: float = 0,
    ) -> Decimal:
        """حساب السعر"""
        if self.pricing_type == PricingType.FREE:
            return Decimal('0.00')

        if self.pricing_type == PricingType.FIXED:
            return self.base_price

        if self.pricing_type == PricingType.PER_UNIT:
            return self.base_price + (self.unit_price * units)

        if self.pricing_type == PricingType.PER_HOUR:
            hours = max(duration_hours, self.min_units)
            return self.base_price + (self.unit_price * Decimal(str(hours)))

        if self.pricing_type == PricingType.PER_DAY:
            days = max(1, int(duration_hours / 24) + (1 if duration_hours % 24 > 0 else 0))
            return self.base_price + (self.unit_price * days)

        if self.pricing_type == PricingType.PER_KM:
            km = max(distance_km, self.min_units)
            return self.base_price + (self.unit_price * Decimal(str(km)))

        # التسعير المتدرج
        if self.tiered_pricing:
            total = self.base_price
            remaining = units

            for tier in sorted(self.tiered_pricing, key=lambda x: x['from']):
                tier_from = tier['from']
                tier_to = tier.get('to', float('inf'))
                tier_price = Decimal(str(tier['price']))

                if remaining <= 0:
                    break

                tier_units = min(remaining, tier_to - tier_from)
                total += tier_price * tier_units
                remaining -= tier_units

            return total

        return self.base_price

    def __str__(self):
        return f"{self.name} ({self.pricing_type})"


class DeliveryPricingRule(models.Model):
    """
    قواعد تسعير التوصيل

    مرونة عالية لدعم مختلف السيناريوهات
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # الربط
    store_id = models.IntegerField(null=True, blank=True, verbose_name='معرف المتجر')
    category_id = models.IntegerField(null=True, blank=True, verbose_name='معرف الفئة')

    # النوع
    pricing_type = models.CharField(
        max_length=20,
        choices=DeliveryPricingType.choices,
        default=DeliveryPricingType.PER_KM,
        verbose_name='نوع التسعير',
    )

    # الأسعار
    base_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرسوم الأساسية',
    )
    per_km_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('2.00'),
        verbose_name='الرسوم لكل كم',
    )
    per_hour_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('50.00'),
        verbose_name='الرسوم لكل ساعة',
    )
    per_day_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('300.00'),
        verbose_name='الرسوم لكل يوم',
    )

    # التوصيل المجاني
    free_delivery_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='حد التوصيل المجاني',
    )
    free_delivery_radius_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='نطاق التوصيل المجاني (كم)',
    )

    # المناطق
    zone_pricing = models.JSONField(
        default=list,
        verbose_name='تسعير المناطق',
        help_text='[{"zone": "north_riyadh", "fee": 25}, ...]',
    )

    # الوزن
    per_kg_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرسوم لكل كجم',
    )
    free_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الوزن المجاني (كجم)',
    )

    # الحدود
    min_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('10.00'),
        verbose_name='الحد الأدنى',
    )
    max_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الحد الأقصى',
    )
    max_distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('50.00'),
        verbose_name='أقصى مسافة (كم)',
    )

    # الحالة
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_delivery_pricing'
        verbose_name = 'تسعير توصيل'
        verbose_name_plural = 'تسعير التوصيل'
        ordering = ['-priority']

    def calculate_delivery_fee(
        self,
        distance_km: float,
        weight_kg: float = 0,
        order_amount: Decimal = Decimal('0'),
        duration_hours: float = 0,
        zone: str = '',
    ) -> Decimal:
        """حساب رسوم التوصيل"""

        # مجاني
        if self.pricing_type == DeliveryPricingType.FREE:
            return Decimal('0.00')

        # توصيل التاجر أو استلام العميل
        if self.pricing_type in [
            DeliveryPricingType.MERCHANT_DELIVERY,
            DeliveryPricingType.CUSTOMER_PICKUP,
        ]:
            return Decimal('0.00')

        # التوصيل المجاني بناءً على قيمة الطلب
        if self.free_delivery_threshold and order_amount >= self.free_delivery_threshold:
            return Decimal('0.00')

        # التوصيل المجاني بناءً على المسافة
        if self.free_delivery_radius_km and distance_km <= float(self.free_delivery_radius_km):
            return Decimal('0.00')

        fee = self.base_fee

        # ثابت
        if self.pricing_type == DeliveryPricingType.FIXED:
            fee = self.base_fee

        # بالكيلومتر
        elif self.pricing_type == DeliveryPricingType.PER_KM:
            fee = self.base_fee + (self.per_km_fee * Decimal(str(distance_km)))

        # بالساعة
        elif self.pricing_type == DeliveryPricingType.PER_HOUR:
            hours = max(1, duration_hours)
            fee = self.base_fee + (self.per_hour_fee * Decimal(str(hours)))

        # باليوم
        elif self.pricing_type == DeliveryPricingType.PER_DAY:
            days = max(1, int(duration_hours / 24) + (1 if duration_hours % 24 > 0 else 0))
            fee = self.base_fee + (self.per_day_fee * days)

        # بالمنطقة
        elif self.pricing_type == DeliveryPricingType.BY_ZONE:
            for zone_rule in self.zone_pricing:
                if zone_rule.get('zone') == zone:
                    fee = Decimal(str(zone_rule.get('fee', 0)))
                    break

        # بالوزن
        elif self.pricing_type == DeliveryPricingType.BY_WEIGHT:
            chargeable_weight = max(0, weight_kg - float(self.free_weight_kg))
            fee = self.base_fee + (self.per_kg_fee * Decimal(str(chargeable_weight)))

        # تطبيق الحدود
        if fee < self.min_fee:
            fee = self.min_fee

        if self.max_fee and fee > self.max_fee:
            fee = self.max_fee

        return fee.quantize(Decimal('0.01'))

    def __str__(self):
        return f"Delivery Pricing ({self.pricing_type})"


class Invoice(models.Model):
    """
    الفاتورة

    يتم إرسالها للنظام المحاسبي الخارجي
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # الرقم
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الفاتورة',
    )

    # الأطراف
    seller_type = models.CharField(max_length=50)
    seller_id = models.IntegerField()
    buyer_type = models.CharField(max_length=50)
    buyer_id = models.IntegerField()

    # المرجع
    order_id = models.IntegerField(null=True, blank=True)
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
    )

    # المبالغ
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'))
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='SAR')

    # البنود
    line_items = models.JSONField(default=list, verbose_name='البنود')

    # ZATCA
    zatca_status = models.CharField(
        max_length=20,
        default='pending',
        verbose_name='حالة ZATCA',
    )
    zatca_invoice_hash = models.CharField(max_length=200, blank=True)
    zatca_qr_code = models.TextField(blank=True)
    zatca_response = models.JSONField(default=dict)

    # المحاسبة الخارجية
    external_system = models.CharField(max_length=50, blank=True)
    external_invoice_id = models.CharField(max_length=100, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    # التوقيت
    invoice_date = models.DateField(verbose_name='تاريخ الفاتورة')
    due_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الاستحقاق')
    created_at = models.DateTimeField(auto_now_add=True)

    # الملفات
    pdf_file = models.FileField(
        upload_to='invoices/%Y/%m/',
        blank=True,
        verbose_name='ملف PDF',
    )

    class Meta:
        db_table = 'finance_invoices'
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number}"
