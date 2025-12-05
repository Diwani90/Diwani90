"""
===================================
منصة ديواني - Payments Schemas
Pydantic schemas for Payment APIs
===================================
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema, Field


# ===================================
# Payment Gateway Schemas
# ===================================
class PaymentGatewayOutSchema(Schema):
    """Schema for payment gateway output."""
    id: UUID
    name: str
    gateway_type: str
    is_active: bool
    supports_mada: bool
    supports_visa: bool
    supports_mastercard: bool
    supports_apple_pay: bool
    supports_installments: bool


class AvailablePaymentMethodSchema(Schema):
    """Schema for available payment methods."""
    id: str
    name: str
    name_en: str
    icon: str
    type: str  # card, wallet, cash, installment
    is_available: bool
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


# ===================================
# Payment Initialization Schemas
# ===================================
class PaymentInitializeSchema(Schema):
    """Schema for initializing a payment."""
    order_id: UUID
    payment_method: str  # mada, visa, mastercard, apple_pay, wallet
    save_card: bool = False
    card_token: Optional[str] = None  # For saved cards
    return_url: Optional[str] = None


class PaymentInitializeResponseSchema(Schema):
    """Schema for payment initialization response."""
    transaction_id: str
    payment_url: Optional[str]  # Redirect URL for 3D Secure
    client_secret: Optional[str]  # For client-side SDK
    status: str
    message: str


# ===================================
# Payment Transaction Schemas
# ===================================
class PaymentTransactionOutSchema(Schema):
    """Schema for payment transaction output."""
    id: UUID
    transaction_id: str
    order_id: Optional[UUID]
    transaction_type: str
    payment_method: str
    status: str
    status_display: str
    amount: Decimal
    currency: str
    fee_amount: Decimal
    net_amount: Decimal
    card_brand: str
    card_last_four: str
    error_code: str
    error_message: str
    initiated_at: datetime
    completed_at: Optional[datetime]

    @staticmethod
    def resolve_status_display(obj):
        return obj.get_status_display()


class PaymentTransactionListSchema(Schema):
    """Schema for transaction listing."""
    id: UUID
    transaction_id: str
    transaction_type: str
    payment_method: str
    status: str
    amount: Decimal
    currency: str
    initiated_at: datetime


# ===================================
# Refund Schemas
# ===================================
class RefundRequestSchema(Schema):
    """Schema for requesting a refund."""
    transaction_id: str
    amount: Optional[Decimal] = None  # None = full refund
    reason: str = ''


class RefundResponseSchema(Schema):
    """Schema for refund response."""
    refund_transaction_id: str
    original_transaction_id: str
    refunded_amount: Decimal
    status: str
    message: str


# ===================================
# Saved Card Schemas
# ===================================
class SavedCardOutSchema(Schema):
    """Schema for saved card output."""
    id: UUID
    card_brand: str
    card_last_four: str
    card_holder_name: str
    expiry_month: str
    expiry_year: str
    is_default: bool
    is_expired: bool
    created_at: datetime

    @staticmethod
    def resolve_is_expired(obj):
        from datetime import date
        today = date.today()
        expiry = date(int(obj.expiry_year), int(obj.expiry_month), 1)
        return expiry < today


class SavedCardCreateSchema(Schema):
    """Schema for saving a card (token from gateway)."""
    token: str
    card_brand: str
    card_last_four: str
    card_holder_name: str = ''
    expiry_month: str
    expiry_year: str
    is_default: bool = False


class SetDefaultCardSchema(Schema):
    """Schema for setting default card."""
    card_id: UUID


# ===================================
# Vendor Payout Schemas
# ===================================
class VendorPayoutOutSchema(Schema):
    """Schema for vendor payout output."""
    id: UUID
    payout_id: str
    store_name: str
    gross_amount: Decimal
    commission_amount: Decimal
    net_amount: Decimal
    bank_name: str
    iban_last_four: str
    status: str
    status_display: str
    period_start: datetime
    period_end: datetime
    orders_count: int
    created_at: datetime
    processed_at: Optional[datetime]

    @staticmethod
    def resolve_store_name(obj):
        return obj.store.name if obj.store else ''

    @staticmethod
    def resolve_iban_last_four(obj):
        return obj.iban[-4:] if obj.iban else ''

    @staticmethod
    def resolve_status_display(obj):
        return obj.get_status_display()


class VendorPayoutListSchema(Schema):
    """Schema for payout listing."""
    id: UUID
    payout_id: str
    net_amount: Decimal
    status: str
    period_start: datetime
    period_end: datetime
    orders_count: int
    created_at: datetime


class VendorBankDetailsSchema(Schema):
    """Schema for vendor bank details."""
    bank_name: str = Field(..., max_length=100)
    iban: str = Field(..., min_length=15, max_length=34)
    account_holder_name: str = Field(..., max_length=100)


# ===================================
# Installment Schemas
# ===================================
class InstallmentPlanOutSchema(Schema):
    """Schema for installment plan output."""
    id: UUID
    plan_id: str
    order_id: Optional[UUID]
    gateway_name: str
    total_amount: Decimal
    installments_count: int
    installment_amount: Decimal
    status: str
    paid_installments: int
    paid_amount: Decimal
    remaining_amount: Decimal
    next_payment_date: Optional[datetime]
    created_at: datetime

    @staticmethod
    def resolve_gateway_name(obj):
        return obj.gateway.name if obj.gateway else ''

    @staticmethod
    def resolve_remaining_amount(obj):
        return obj.total_amount - obj.paid_amount


class InstallmentCheckSchema(Schema):
    """Schema for checking installment eligibility."""
    amount: Decimal
    gateway: str = 'tamara'  # tamara or tabby


class InstallmentEligibilitySchema(Schema):
    """Schema for installment eligibility response."""
    is_eligible: bool
    min_amount: Decimal
    max_amount: Decimal
    available_plans: List[dict]  # [{installments: 3, amount_per_installment: 100}, ...]
    message: str


# ===================================
# Webhook Schemas
# ===================================
class WebhookPayloadSchema(Schema):
    """Schema for webhook payload."""
    event_type: str
    transaction_id: str
    status: str
    amount: Decimal
    currency: str
    gateway_data: dict


# ===================================
# Payment Summary Schemas
# ===================================
class PaymentSummarySchema(Schema):
    """Schema for payment summary (for vendors)."""
    total_received: Decimal
    pending_payout: Decimal
    total_commission: Decimal
    total_payouts: Decimal
    transactions_count: int
    last_payout_date: Optional[datetime]


# ===================================
# Pagination Schemas
# ===================================
class PaginatedTransactionSchema(Schema):
    """Schema for paginated transactions."""
    items: List[PaymentTransactionListSchema]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedPayoutSchema(Schema):
    """Schema for paginated payouts."""
    items: List[VendorPayoutListSchema]
    total: int
    page: int
    page_size: int
    pages: int


# ===================================
# Common Response Schemas
# ===================================
class MessageSchema(Schema):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorSchema(Schema):
    """Error response schema."""
    message: str
    code: Optional[str] = None
