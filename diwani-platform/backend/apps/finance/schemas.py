"""
Schemas للنظام المالي
====================

Django Ninja Schemas للـ API
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ninja import Schema, Field


# =============================================
# حساب الأسعار
# =============================================

class PricingItemSchema(Schema):
    """عنصر للتسعير"""
    id: Optional[str] = None
    name: Optional[str] = None
    pricing_type: str = 'fixed'
    base_price: float
    quantity: float = 1
    context: Optional[Dict[str, Any]] = None
    strategy_kwargs: Optional[Dict[str, Any]] = None


class DeliveryInfoSchema(Schema):
    """معلومات التوصيل"""
    type: str = 'free'  # free, merchant, pickup, per_km, per_hour, etc.
    base_rate: float = 0
    context: Optional[Dict[str, Any]] = None
    kwargs: Optional[Dict[str, Any]] = None


class PriceCalculationRequestSchema(Schema):
    """طلب حساب السعر"""
    items: List[PricingItemSchema]
    delivery_info: Optional[DeliveryInfoSchema] = None
    vendor_commission_rate: Optional[float] = None
    driver_commission_rate: Optional[float] = None
    include_tax: bool = True


class PriceCalculationResponseSchema(Schema):
    """استجابة حساب السعر"""
    items_total: float
    delivery_total: float
    subtotal: float
    tax_amount: float
    platform_fee: float
    total: float
    vendor_payout: float
    driver_payout: float
    platform_revenue: float
    breakdown: Dict[str, Any]


# =============================================
# المعاملات
# =============================================

class TransactionListSchema(Schema):
    """Schema لقائمة المعاملات"""
    id: UUID
    order_id: UUID
    amount: float
    currency: str
    status: str
    payment_method: Optional[str] = None
    created_at: datetime


class TransactionSchema(Schema):
    """Schema للمعاملة"""
    id: UUID
    order_id: UUID
    amount: float
    currency: str
    status: str
    transaction_type: str
    payment_method: Optional[str] = None
    tap_charge_id: Optional[str] = None
    tap_transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


# =============================================
# الأرصدة
# =============================================

class VendorBalanceSchema(Schema):
    """Schema لرصيد التاجر"""
    vendor_id: UUID
    vendor_type: str
    available_balance: float
    pending_balance: float
    total_earned: float
    total_withdrawn: float
    last_synced_at: Optional[datetime] = None
    updated_at: datetime

    @staticmethod
    def resolve_vendor_id(obj):
        return obj.vendor_id


# =============================================
# طلبات السحب
# =============================================

class PayoutCreateSchema(Schema):
    """Schema لإنشاء طلب سحب"""
    amount: float = Field(..., gt=0)
    method: Optional[str] = 'bank_transfer'


class PayoutListSchema(Schema):
    """Schema لقائمة طلبات السحب"""
    id: UUID
    amount: float
    status: str
    method: str
    created_at: datetime
    processed_at: Optional[datetime] = None


class PayoutSchema(Schema):
    """Schema لطلب السحب"""
    id: UUID
    amount: float
    currency: str = 'SAR'
    status: str
    method: str
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


# =============================================
# الفواتير
# =============================================

class InvoiceListSchema(Schema):
    """Schema لقائمة الفواتير"""
    id: UUID
    invoice_number: str
    order_id: UUID
    customer_name: str
    total: float
    zatca_status: str
    invoice_date: datetime


class InvoiceSchema(Schema):
    """Schema للفاتورة"""
    id: UUID
    invoice_number: str
    order_id: UUID
    invoice_date: datetime

    vendor_name: str
    vendor_vat: Optional[str] = None
    vendor_cr: Optional[str] = None

    customer_name: str
    customer_vat: Optional[str] = None
    customer_phone: Optional[str] = None

    line_items: List[Dict[str, Any]]
    subtotal: float
    delivery_total: float
    tax_rate: float
    tax_amount: float
    total: float

    zatca_status: str
    zatca_qr_code: Optional[str] = None
    accounting_provider: Optional[str] = None

    created_at: datetime


# =============================================
# التسوية
# =============================================

class ReconciliationSummarySchema(Schema):
    """ملخص التسوية"""
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    total_records: int
    matched: int
    discrepancies: int
    match_rate: float


# =============================================
# التقارير
# =============================================

class FinancialReportSchema(Schema):
    """Schema للتقرير المالي"""
    period: str
    start_date: str
    end_date: str
    total_sales: float
    transactions_count: int
    total_withdrawn: float
    available_balance: float
    pending_balance: float


# =============================================
# سجل القيود المحاسبية
# =============================================

class LedgerEntrySchema(Schema):
    """سجل القيد المحاسبي"""
    id: UUID
    entry_type: str
    amount: Decimal
    currency: str
    from_account: str
    to_account: str
    reference_type: str
    reference_id: str
    description: Optional[str] = None
    source: str
    transaction_date: datetime
    recorded_at: datetime

    class Config:
        from_attributes = True


# =============================================
# عام
# =============================================

class MessageSchema(Schema):
    """رسالة عامة"""
    message: str
    task_id: Optional[str] = None
    error: Optional[str] = None
