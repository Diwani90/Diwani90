"""
API المالية
===========

Django Ninja API للنظام المالي
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router, Query
from ninja.pagination import paginate, LimitOffsetPagination

from .models import (
    Transaction,
    VendorBalance,
    Payout,
    ReconciliationRecord,
    Invoice,
)
from .schemas import (
    TransactionSchema,
    TransactionListSchema,
    VendorBalanceSchema,
    PayoutSchema,
    PayoutCreateSchema,
    PayoutListSchema,
    InvoiceSchema,
    InvoiceListSchema,
    ReconciliationSummarySchema,
    FinancialReportSchema,
    PriceCalculationRequestSchema,
    PriceCalculationResponseSchema,
    MessageSchema,
)
from .services import pricing_service, commission_service

router = Router()


# =============================================
# حساب الأسعار - Pricing Calculator
# =============================================

@router.post('/pricing/calculate', response=PriceCalculationResponseSchema, tags=['التسعير'])
def calculate_order_price(request, data: PriceCalculationRequestSchema):
    """
    حساب سعر الطلب الكامل

    يدعم جميع أنواع التسعير:
    - ثابت، بالساعة، باليوم، بالمسافة، بالوزن، متدرج، مجاني
    """
    result = pricing_service.calculate_order_total(
        items=data.items,
        delivery_info=data.delivery_info,
        vendor_commission_rate=Decimal(str(data.vendor_commission_rate or 0.05)),
        driver_commission_rate=Decimal(str(data.driver_commission_rate or 0.15)),
        include_tax=data.include_tax,
    )

    return result.to_dict()


@router.get('/pricing/commission-rates', tags=['التسعير'])
def get_commission_rates(request, vendor_id: Optional[UUID] = None, order_amount: Optional[float] = None):
    """
    الحصول على نسب العمولات

    تتغير النسب حسب:
    - حجم الطلب (خصومات للطلبات الكبيرة)
    - التاجر (اتفاقيات خاصة)
    """
    vendor_rate = commission_service.get_vendor_commission_rate(
        vendor_id=str(vendor_id) if vendor_id else '',
        order_amount=Decimal(str(order_amount)) if order_amount else None
    )

    driver_rate = commission_service.get_driver_commission_rate(
        driver_id=''
    )

    return {
        'vendor_commission_rate': float(vendor_rate * 100),
        'driver_commission_rate': float(driver_rate * 100),
        'platform_commission': float((vendor_rate + driver_rate) * 100),
    }


# =============================================
# المعاملات - Transactions
# =============================================

@router.get('/transactions', response=List[TransactionListSchema], tags=['المعاملات'])
@paginate(LimitOffsetPagination)
def list_transactions(
    request,
    status: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """قائمة المعاملات (للتاجر)"""
    from apps.stores.models import Store

    # الحصول على متجر التاجر
    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return []

    queryset = Transaction.objects.filter(order__vendor=store)

    if status:
        queryset = queryset.filter(status=status)

    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    return queryset.select_related('order').order_by('-created_at')


@router.get('/transactions/{transaction_id}', response=TransactionSchema, tags=['المعاملات'])
def get_transaction(request, transaction_id: UUID):
    """تفاصيل معاملة"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()

    return get_object_or_404(
        Transaction,
        id=transaction_id,
        order__vendor=store
    )


# =============================================
# الأرصدة - Balances
# =============================================

@router.get('/balance', response=VendorBalanceSchema, tags=['الأرصدة'])
def get_balance(request):
    """رصيد التاجر"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return {'error': 'لا يوجد متجر مسجل'}

    balance, created = VendorBalance.objects.get_or_create(
        vendor=store,
        defaults={
            'available_balance': Decimal('0'),
            'pending_balance': Decimal('0'),
        }
    )

    return balance


@router.get('/balance/history', tags=['الأرصدة'])
@paginate(LimitOffsetPagination)
def balance_history(
    request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """سجل حركة الرصيد"""
    from apps.stores.models import Store
    from .models import LedgerEntry

    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return []

    queryset = LedgerEntry.objects.filter(
        Q(debit_account=f'vendor:{store.id}') |
        Q(credit_account=f'vendor:{store.id}')
    )

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    return queryset.order_by('-created_at')


# =============================================
# طلبات السحب - Payouts
# =============================================

@router.get('/payouts', response=List[PayoutListSchema], tags=['السحب'])
@paginate(LimitOffsetPagination)
def list_payouts(request, status: Optional[str] = None):
    """قائمة طلبات السحب"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return []

    queryset = Payout.objects.filter(vendor=store)

    if status:
        queryset = queryset.filter(status=status)

    return queryset.order_by('-created_at')


@router.post('/payouts', response=PayoutSchema, tags=['السحب'])
def create_payout(request, data: PayoutCreateSchema):
    """طلب سحب رصيد"""
    from apps.stores.models import Store
    from django.conf import settings

    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return {'error': 'لا يوجد متجر مسجل'}

    # التحقق من الرصيد
    balance = VendorBalance.objects.filter(vendor=store).first()
    if not balance or balance.available_balance < Decimal(str(data.amount)):
        return {'error': 'الرصيد غير كافٍ'}

    # التحقق من الحد الأدنى
    min_amount = settings.FINANCE_SETTINGS.get('MIN_PAYOUT_AMOUNT', 100)
    if data.amount < min_amount:
        return {'error': f'الحد الأدنى للسحب {min_amount} ر.س'}

    # التحقق من وجود حساب بنكي
    if not store.bank_iban:
        return {'error': 'يجب إضافة الحساب البنكي أولاً'}

    payout = Payout.objects.create(
        vendor=store,
        amount=Decimal(str(data.amount)),
        method=data.method or 'bank_transfer',
        bank_account=store.bank_iban,
        bank_name=store.bank_name,
        status='pending',
    )

    # خصم من الرصيد المتاح
    balance.available_balance -= payout.amount
    balance.save()

    return payout


@router.get('/payouts/{payout_id}', response=PayoutSchema, tags=['السحب'])
def get_payout(request, payout_id: UUID):
    """تفاصيل طلب سحب"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()

    return get_object_or_404(
        Payout,
        id=payout_id,
        vendor=store
    )


@router.post('/payouts/{payout_id}/cancel', response=MessageSchema, tags=['السحب'])
def cancel_payout(request, payout_id: UUID):
    """إلغاء طلب سحب"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()

    payout = get_object_or_404(
        Payout,
        id=payout_id,
        vendor=store,
        status='pending'
    )

    # إعادة المبلغ للرصيد
    balance = VendorBalance.objects.get(vendor=store)
    balance.available_balance += payout.amount
    balance.save()

    payout.status = 'cancelled'
    payout.save()

    return {'message': 'تم إلغاء طلب السحب بنجاح'}


# =============================================
# الفواتير - Invoices
# =============================================

@router.get('/invoices', response=List[InvoiceListSchema], tags=['الفواتير'])
@paginate(LimitOffsetPagination)
def list_invoices(
    request,
    zatca_status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """قائمة الفواتير"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return []

    queryset = Invoice.objects.filter(order__vendor=store)

    if zatca_status:
        queryset = queryset.filter(zatca_status=zatca_status)

    if start_date:
        queryset = queryset.filter(invoice_date__gte=start_date)

    if end_date:
        queryset = queryset.filter(invoice_date__lte=end_date)

    return queryset.order_by('-invoice_date')


@router.get('/invoices/{invoice_id}', response=InvoiceSchema, tags=['الفواتير'])
def get_invoice(request, invoice_id: UUID):
    """تفاصيل فاتورة"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()

    return get_object_or_404(
        Invoice,
        id=invoice_id,
        order__vendor=store
    )


@router.get('/invoices/{invoice_id}/pdf', tags=['الفواتير'])
def download_invoice_pdf(request, invoice_id: UUID):
    """تحميل الفاتورة PDF"""
    from django.http import HttpResponse

    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        order__vendor=store
    )

    # إنشاء PDF للفاتورة
    pdf_content = _generate_invoice_pdf(invoice, store)

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'

    return response


def _generate_invoice_pdf(invoice, store) -> bytes:
    """
    إنشاء PDF للفاتورة

    يدعم:
    - ReportLab (مفضل)
    - PDF نصي بسيط (Fallback)
    """
    import logging
    from io import BytesIO

    logger = logging.getLogger(__name__)

    # محاولة استخدام ReportLab
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm)

        styles = getSampleStyleSheet()
        elements = []

        # عنوان الفاتورة
        elements.append(Paragraph(f"<b>Invoice: {invoice.invoice_number}</b>", styles['Heading1']))
        elements.append(Spacer(1, 0.5*cm))

        # معلومات المتجر
        elements.append(Paragraph(f"<b>Store:</b> {store.name}", styles['Normal']))
        elements.append(Paragraph(f"<b>Date:</b> {invoice.issue_date}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

        # معلومات العميل
        if invoice.order and invoice.order.customer:
            customer = invoice.order.customer
            customer_name = customer.get_full_name() or str(customer.phone_number)
            elements.append(Paragraph(f"<b>Customer:</b> {customer_name}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

        # جدول العناصر
        table_data = [['Product', 'Qty', 'Price', 'Total']]

        if invoice.order:
            for item in invoice.order.items.all():
                table_data.append([
                    str(item.product_name or 'Product')[:30],
                    str(item.quantity),
                    f"{item.unit_price} SAR",
                    f"{item.total_price} SAR",
                ])

        if len(table_data) > 1:
            table = Table(table_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))

        # المجاميع
        elements.append(Paragraph(f"<b>Subtotal:</b> {invoice.subtotal} SAR", styles['Normal']))
        elements.append(Paragraph(f"<b>Tax (15%):</b> {invoice.tax_amount} SAR", styles['Normal']))
        elements.append(Paragraph(f"<b>Total:</b> {invoice.total_amount} SAR", styles['Heading2']))

        doc.build(elements)
        return buffer.getvalue()

    except ImportError:
        logger.warning('ReportLab not installed. Using basic PDF. Install with: pip install reportlab')

    # Fallback: PDF نصي بسيط
    content_stream = f"""BT
/F1 16 Tf
50 750 Td
(INVOICE: {invoice.invoice_number}) Tj
/F1 12 Tf
0 -30 Td
(Store: {store.name}) Tj
0 -20 Td
(Date: {invoice.issue_date}) Tj
0 -40 Td
(Subtotal: {invoice.subtotal} SAR) Tj
0 -20 Td
(Tax (15%): {invoice.tax_amount} SAR) Tj
0 -20 Td
(Total: {invoice.total_amount} SAR) Tj
ET"""

    pdf_content = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length {len(content_stream)} >>
stream
{content_stream}
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000333 00000 n
trailer << /Size 6 /Root 1 0 R >>
startxref
{400 + len(content_stream)}
%%EOF"""

    return pdf_content.encode('latin-1')


# =============================================
# التقارير المالية
# =============================================

@router.get('/reports/summary', response=FinancialReportSchema, tags=['التقارير'])
def financial_summary(
    request,
    period: str = 'month',  # day, week, month, year
):
    """ملخص مالي"""
    from apps.stores.models import Store
    from datetime import timedelta

    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return {'error': 'لا يوجد متجر مسجل'}

    today = timezone.now().date()

    if period == 'day':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today.replace(day=1)
    else:  # year
        start_date = today.replace(month=1, day=1)

    # إحصائيات المعاملات
    transactions = Transaction.objects.filter(
        order__vendor=store,
        created_at__date__gte=start_date,
        status='completed'
    ).aggregate(
        total_sales=Sum('amount'),
        count=Count('id'),
    )

    # إحصائيات السحوبات
    payouts = Payout.objects.filter(
        vendor=store,
        created_at__date__gte=start_date,
        status='completed'
    ).aggregate(
        total_withdrawn=Sum('amount'),
    )

    balance = VendorBalance.objects.filter(vendor=store).first()

    return {
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': today.isoformat(),
        'total_sales': float(transactions.get('total_sales') or 0),
        'transactions_count': transactions.get('count') or 0,
        'total_withdrawn': float(payouts.get('total_withdrawn') or 0),
        'available_balance': float(balance.available_balance if balance else 0),
        'pending_balance': float(balance.pending_balance if balance else 0),
    }


@router.get('/reports/reconciliation', response=ReconciliationSummarySchema, tags=['التقارير'])
def reconciliation_report(
    request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """تقرير التسوية"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.user).first()
    if not store:
        return {'error': 'لا يوجد متجر مسجل'}

    queryset = ReconciliationRecord.objects.filter(
        transaction__order__vendor=store
    )

    if start_date:
        queryset = queryset.filter(reconciliation_date__gte=start_date)

    if end_date:
        queryset = queryset.filter(reconciliation_date__lte=end_date)

    stats = queryset.aggregate(
        total=Count('id'),
        matched=Count('id', filter=Q(status='matched')),
        discrepancies=Count('id', filter=Q(status='discrepancy')),
    )

    return {
        'period_start': start_date.isoformat() if start_date else None,
        'period_end': end_date.isoformat() if end_date else None,
        'total_records': stats.get('total') or 0,
        'matched': stats.get('matched') or 0,
        'discrepancies': stats.get('discrepancies') or 0,
        'match_rate': (
            (stats.get('matched') or 0) / (stats.get('total') or 1) * 100
        ),
    }


# =============================================
# Admin APIs (للإدارة)
# =============================================

@router.get('/admin/reconciliation/run', tags=['إدارة'])
def run_reconciliation(request, date_str: Optional[str] = None):
    """تشغيل التسوية يدوياً (للمسؤولين فقط)"""
    # التحقق من صلاحيات المسؤول
    if not request.user.is_authenticated:
        return {'error': 'يجب تسجيل الدخول'}

    if not (request.user.is_staff or request.user.is_superuser):
        return {'error': 'هذه الوظيفة متاحة للمسؤولين فقط'}

    # التحقق من صلاحية محددة إن وجدت
    if hasattr(request.user, 'has_perm') and not request.user.has_perm('finance.run_reconciliation'):
        if not request.user.is_superuser:
            return {'error': 'لا تملك صلاحية تشغيل التسوية'}

    from .tasks import run_daily_reconciliation

    task = run_daily_reconciliation.delay(date_str)

    return {
        'message': 'تم بدء عملية التسوية',
        'task_id': str(task.id),
    }


@router.get('/admin/ledger/verify', tags=['إدارة'])
def verify_ledger(request):
    """التحقق من سلامة السجل المالي"""
    # التحقق من صلاحيات المسؤول
    if not request.user.is_authenticated:
        return {'error': 'يجب تسجيل الدخول'}

    if not (request.user.is_staff or request.user.is_superuser):
        return {'error': 'هذه الوظيفة متاحة للمسؤولين فقط'}

    # التحقق من صلاحية محددة إن وجدت
    if hasattr(request.user, 'has_perm') and not request.user.has_perm('finance.verify_ledger'):
        if not request.user.is_superuser:
            return {'error': 'لا تملك صلاحية التحقق من السجل المالي'}

    from .services import ledger_service

    result = ledger_service.verify_chain_integrity()

    return result
