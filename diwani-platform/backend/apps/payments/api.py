"""
===================================
منصة ديواني - Payments API
Django Ninja API Endpoints for Payments
===================================
"""

from typing import List, Optional
from uuid import UUID
from math import ceil
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from ninja import Router, Query

from apps.orders.models import Order
from apps.stores.models import Store
from .models import (
    PaymentGateway, PaymentTransaction, SavedCard,
    VendorPayout, InstallmentPlan
)
from .schemas import (
    PaymentGatewayOutSchema,
    AvailablePaymentMethodSchema,
    PaymentInitializeSchema,
    PaymentInitializeResponseSchema,
    PaymentTransactionOutSchema,
    PaymentTransactionListSchema,
    RefundRequestSchema,
    RefundResponseSchema,
    SavedCardOutSchema,
    SavedCardCreateSchema,
    SetDefaultCardSchema,
    VendorPayoutOutSchema,
    VendorPayoutListSchema,
    VendorBankDetailsSchema,
    InstallmentPlanOutSchema,
    InstallmentCheckSchema,
    InstallmentEligibilitySchema,
    PaymentSummarySchema,
    PaginatedTransactionSchema,
    PaginatedPayoutSchema,
    MessageSchema,
    ErrorSchema,
)

# Create router
router = Router(tags=['المدفوعات'])


# ===================================
# Payment Methods Endpoints
# ===================================
@router.get('/methods', response=List[AvailablePaymentMethodSchema])
def get_available_payment_methods(request, amount: Decimal = Query(None)):
    """
    طرق الدفع المتاحة
    ---
    قائمة طرق الدفع المتاحة للمستخدم
    """
    methods = []

    # Cash on delivery
    methods.append(AvailablePaymentMethodSchema(
        id='cash',
        name='الدفع عند الاستلام',
        name_en='Cash on Delivery',
        icon='cash',
        type='cash',
        is_available=True,
        max_amount=Decimal('5000')
    ))

    # Mada
    if PaymentGateway.objects.filter(is_active=True, supports_mada=True).exists():
        methods.append(AvailablePaymentMethodSchema(
            id='mada',
            name='مدى',
            name_en='Mada',
            icon='mada',
            type='card',
            is_available=True
        ))

    # Visa/Mastercard
    if PaymentGateway.objects.filter(is_active=True, supports_visa=True).exists():
        methods.append(AvailablePaymentMethodSchema(
            id='card',
            name='بطاقة ائتمان',
            name_en='Credit Card',
            icon='credit-card',
            type='card',
            is_available=True
        ))

    # Apple Pay
    if PaymentGateway.objects.filter(is_active=True, supports_apple_pay=True).exists():
        methods.append(AvailablePaymentMethodSchema(
            id='apple_pay',
            name='Apple Pay',
            name_en='Apple Pay',
            icon='apple',
            type='wallet',
            is_available=True
        ))

    # Wallet
    if request.user.is_authenticated:
        wallet_available = request.user.wallet_balance >= (amount or 0)
        methods.append(AvailablePaymentMethodSchema(
            id='wallet',
            name=f'المحفظة ({request.user.wallet_balance} ر.س)',
            name_en='Wallet',
            icon='wallet',
            type='wallet',
            is_available=wallet_available
        ))

    # Installments (Tamara/Tabby)
    if amount and amount >= 100:
        if PaymentGateway.objects.filter(is_active=True, supports_installments=True).exists():
            methods.append(AvailablePaymentMethodSchema(
                id='installment',
                name='تقسيط بدون فوائد',
                name_en='Buy Now Pay Later',
                icon='calendar',
                type='installment',
                is_available=True,
                min_amount=Decimal('100'),
                max_amount=Decimal('10000')
            ))

    return methods


@router.get('/gateways', response=List[PaymentGatewayOutSchema])
def list_payment_gateways(request):
    """
    بوابات الدفع
    ---
    قائمة بوابات الدفع المفعلة
    """
    return PaymentGateway.objects.filter(is_active=True)


# ===================================
# Payment Processing Endpoints
# ===================================
@router.post('/initialize', response={200: PaymentInitializeResponseSchema, 400: ErrorSchema})
def initialize_payment(request, data: PaymentInitializeSchema):
    """
    بدء عملية الدفع
    ---
    إنشاء جلسة دفع جديدة
    """
    try:
        order = Order.objects.get(id=data.order_id, customer=request.user)

        if order.payment_status == Order.PaymentStatus.PAID:
            return 400, ErrorSchema(message='تم دفع هذا الطلب مسبقاً')

        # Get active gateway
        gateway = PaymentGateway.objects.filter(is_active=True).first()
        if not gateway:
            return 400, ErrorSchema(message='لا توجد بوابة دفع متاحة')

        # Create transaction record
        transaction_record = PaymentTransaction.objects.create(
            order=order,
            user=request.user,
            gateway=gateway,
            payment_method=data.payment_method,
            amount=order.total,
            status=PaymentTransaction.TransactionStatus.PENDING,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # TODO: Integrate with actual payment gateway
        # For now, return mock response

        # Check if using saved card
        if data.card_token:
            saved_card = SavedCard.objects.filter(
                token=data.card_token,
                user=request.user,
                is_active=True
            ).first()

            if saved_card:
                # Process with saved card token
                pass

        return 200, PaymentInitializeResponseSchema(
            transaction_id=transaction_record.transaction_id,
            payment_url=f"/pay/{transaction_record.transaction_id}",  # Mock URL
            client_secret=None,
            status='pending',
            message='تم إنشاء جلسة الدفع بنجاح'
        )

    except Order.DoesNotExist:
        return 400, ErrorSchema(message='الطلب غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.get('/transactions/{transaction_id}', response={200: PaymentTransactionOutSchema, 404: ErrorSchema})
def get_transaction(request, transaction_id: str):
    """
    تفاصيل المعاملة
    """
    try:
        txn = PaymentTransaction.objects.get(
            transaction_id=transaction_id,
            user=request.user
        )
        return 200, txn
    except PaymentTransaction.DoesNotExist:
        return 404, ErrorSchema(message='المعاملة غير موجودة')


@router.get('/transactions', response=PaginatedTransactionSchema)
def list_transactions(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: Optional[str] = None,
    transaction_type: Optional[str] = None
):
    """
    سجل المعاملات
    """
    queryset = PaymentTransaction.objects.filter(user=request.user)

    if status:
        queryset = queryset.filter(status=status)
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)

    queryset = queryset.order_by('-initiated_at')

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedTransactionSchema(
        items=[PaymentTransactionListSchema.from_orm(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


# ===================================
# Refund Endpoints
# ===================================
@router.post('/refund', response={200: RefundResponseSchema, 400: ErrorSchema})
def request_refund(request, data: RefundRequestSchema):
    """
    طلب استرداد
    ---
    طلب استرداد كلي أو جزئي
    """
    try:
        original_txn = PaymentTransaction.objects.get(
            transaction_id=data.transaction_id,
            user=request.user
        )

        if not original_txn.is_refundable:
            return 400, ErrorSchema(message='لا يمكن استرداد هذه المعاملة')

        refund_amount = data.amount or (original_txn.amount - original_txn.refunded_amount)

        if refund_amount > (original_txn.amount - original_txn.refunded_amount):
            return 400, ErrorSchema(message='مبلغ الاسترداد أكبر من المبلغ المتبقي')

        # Create refund transaction
        refund_txn = PaymentTransaction.objects.create(
            order=original_txn.order,
            user=request.user,
            gateway=original_txn.gateway,
            transaction_type=PaymentTransaction.TransactionType.REFUND,
            payment_method=original_txn.payment_method,
            amount=refund_amount,
            original_transaction=original_txn,
            status=PaymentTransaction.TransactionStatus.PROCESSING
        )

        # TODO: Process refund with payment gateway
        # For now, mark as completed
        refund_txn.mark_completed()

        # Update original transaction
        original_txn.refunded_amount += refund_amount
        if original_txn.refunded_amount >= original_txn.amount:
            original_txn.status = PaymentTransaction.TransactionStatus.REFUNDED
        else:
            original_txn.status = PaymentTransaction.TransactionStatus.PARTIALLY_REFUNDED
        original_txn.save()

        # Update order payment status
        order = original_txn.order
        if original_txn.refunded_amount >= original_txn.amount:
            order.payment_status = Order.PaymentStatus.REFUNDED
        else:
            order.payment_status = Order.PaymentStatus.PARTIALLY_REFUNDED
        order.save(update_fields=['payment_status'])

        return 200, RefundResponseSchema(
            refund_transaction_id=refund_txn.transaction_id,
            original_transaction_id=original_txn.transaction_id,
            refunded_amount=refund_amount,
            status='completed',
            message='تم الاسترداد بنجاح'
        )

    except PaymentTransaction.DoesNotExist:
        return 400, ErrorSchema(message='المعاملة غير موجودة')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


# ===================================
# Saved Cards Endpoints
# ===================================
@router.get('/cards', response=List[SavedCardOutSchema])
def list_saved_cards(request):
    """
    البطاقات المحفوظة
    """
    return SavedCard.objects.filter(user=request.user, is_active=True)


@router.post('/cards', response={201: SavedCardOutSchema, 400: ErrorSchema})
def save_card(request, data: SavedCardCreateSchema):
    """
    حفظ بطاقة جديدة
    """
    try:
        gateway = PaymentGateway.objects.filter(is_active=True).first()
        if not gateway:
            return 400, ErrorSchema(message='لا توجد بوابة دفع متاحة')

        card = SavedCard.objects.create(
            user=request.user,
            gateway=gateway,
            **data.dict()
        )
        return 201, card
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/cards/default', response={200: MessageSchema, 400: ErrorSchema})
def set_default_card(request, data: SetDefaultCardSchema):
    """
    تعيين البطاقة الافتراضية
    """
    try:
        card = SavedCard.objects.get(id=data.card_id, user=request.user)
        card.is_default = True
        card.save()
        return 200, MessageSchema(message='تم تعيين البطاقة كافتراضية')
    except SavedCard.DoesNotExist:
        return 400, ErrorSchema(message='البطاقة غير موجودة')


@router.delete('/cards/{card_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_saved_card(request, card_id: UUID):
    """
    حذف بطاقة محفوظة
    """
    try:
        card = SavedCard.objects.get(id=card_id, user=request.user)
        card.is_active = False
        card.save()
        return 200, MessageSchema(message='تم حذف البطاقة')
    except SavedCard.DoesNotExist:
        return 404, ErrorSchema(message='البطاقة غير موجودة')


# ===================================
# Installments Endpoints
# ===================================
@router.post('/installments/check', response=InstallmentEligibilitySchema)
def check_installment_eligibility(request, data: InstallmentCheckSchema):
    """
    التحقق من أهلية التقسيط
    """
    min_amount = Decimal('100')
    max_amount = Decimal('10000')

    is_eligible = min_amount <= data.amount <= max_amount

    available_plans = []
    if is_eligible:
        # 3 installments
        available_plans.append({
            'installments': 3,
            'amount_per_installment': float(data.amount / 3),
            'first_payment': float(data.amount / 3),
            'fee': 0
        })
        # 4 installments
        available_plans.append({
            'installments': 4,
            'amount_per_installment': float(data.amount / 4),
            'first_payment': float(data.amount / 4),
            'fee': 0
        })

    return InstallmentEligibilitySchema(
        is_eligible=is_eligible,
        min_amount=min_amount,
        max_amount=max_amount,
        available_plans=available_plans,
        message='مؤهل للتقسيط' if is_eligible else 'المبلغ غير مؤهل للتقسيط'
    )


@router.get('/installments', response=List[InstallmentPlanOutSchema])
def list_installment_plans(request):
    """
    خطط التقسيط الخاصة بي
    """
    return InstallmentPlan.objects.filter(user=request.user)


@router.get('/installments/{plan_id}', response={200: InstallmentPlanOutSchema, 404: ErrorSchema})
def get_installment_plan(request, plan_id: UUID):
    """
    تفاصيل خطة التقسيط
    """
    try:
        plan = InstallmentPlan.objects.get(id=plan_id, user=request.user)
        return 200, plan
    except InstallmentPlan.DoesNotExist:
        return 404, ErrorSchema(message='الخطة غير موجودة')


# ===================================
# Vendor Payouts Endpoints
# ===================================
@router.get('/vendor/summary', response=PaymentSummarySchema)
def get_vendor_payment_summary(request):
    """
    ملخص المدفوعات للتاجر
    """
    from django.db.models import Sum

    stores = Store.objects.filter(owner=request.user)

    # Get completed transactions for vendor's stores
    completed_txns = PaymentTransaction.objects.filter(
        order__store__in=stores,
        status=PaymentTransaction.TransactionStatus.COMPLETED,
        transaction_type=PaymentTransaction.TransactionType.PAYMENT
    )

    total_received = completed_txns.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_commission = completed_txns.aggregate(total=Sum('fee_amount'))['total'] or Decimal('0')

    # Get payouts
    payouts = VendorPayout.objects.filter(store__in=stores)
    total_payouts = payouts.filter(
        status=VendorPayout.PayoutStatus.COMPLETED
    ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0')

    pending_payout = total_received - total_commission - total_payouts

    last_payout = payouts.filter(
        status=VendorPayout.PayoutStatus.COMPLETED
    ).order_by('-processed_at').first()

    return PaymentSummarySchema(
        total_received=total_received,
        pending_payout=pending_payout,
        total_commission=total_commission,
        total_payouts=total_payouts,
        transactions_count=completed_txns.count(),
        last_payout_date=last_payout.processed_at if last_payout else None
    )


@router.get('/vendor/payouts', response=PaginatedPayoutSchema)
def list_vendor_payouts(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: Optional[str] = None
):
    """
    سجل التحويلات للتاجر
    """
    queryset = VendorPayout.objects.filter(vendor=request.user)

    if status:
        queryset = queryset.filter(status=status)

    queryset = queryset.order_by('-created_at')

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedPayoutSchema(
        items=[VendorPayoutListSchema.from_orm(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get('/vendor/payouts/{payout_id}', response={200: VendorPayoutOutSchema, 404: ErrorSchema})
def get_vendor_payout(request, payout_id: UUID):
    """
    تفاصيل التحويل
    """
    try:
        payout = VendorPayout.objects.get(id=payout_id, vendor=request.user)
        return 200, payout
    except VendorPayout.DoesNotExist:
        return 404, ErrorSchema(message='التحويل غير موجود')


@router.post('/vendor/bank-details', response={200: MessageSchema, 400: ErrorSchema})
def update_bank_details(request, data: VendorBankDetailsSchema):
    """
    تحديث البيانات البنكية
    """
    try:
        # Validate IBAN format for Saudi Arabia
        if not data.iban.startswith('SA'):
            return 400, ErrorSchema(message='رقم الآيبان يجب أن يبدأ بـ SA')

        # Store in vendor profile
        if hasattr(request.user, 'vendor_profile'):
            profile = request.user.vendor_profile
            profile.bank_name = data.bank_name
            profile.bank_iban = data.iban
            profile.bank_account_name = data.account_holder_name
            profile.save()
            return 200, MessageSchema(message='تم تحديث البيانات البنكية')
        return 400, ErrorSchema(message='لم يتم العثور على ملف التاجر')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


# ===================================
# Webhook Endpoints (for payment gateways)
# ===================================
@router.post('/webhook/{gateway_type}', response=dict, auth=None)
def payment_webhook(request, gateway_type: str):
    """
    Webhook للبوابات الدفع
    ---
    يستقبل إشعارات من بوابات الدفع
    """
    import json

    try:
        payload = json.loads(request.body)

        # TODO: Verify webhook signature based on gateway_type
        # TODO: Process webhook based on gateway

        # Log webhook
        print(f"[WEBHOOK] {gateway_type}: {payload}")

        return {'status': 'received'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# ===================================
# Admin Endpoints
# ===================================
@router.get('/admin/transactions', response=PaginatedTransactionSchema)
def admin_list_transactions(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    payment_method: Optional[str] = None
):
    """
    جميع المعاملات (للإدارة)
    """
    # TODO: Add admin permission check
    queryset = PaymentTransaction.objects.all()

    if status:
        queryset = queryset.filter(status=status)
    if payment_method:
        queryset = queryset.filter(payment_method=payment_method)

    queryset = queryset.order_by('-initiated_at')

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedTransactionSchema(
        items=[PaymentTransactionListSchema.from_orm(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )
