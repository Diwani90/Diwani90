"""
معالجات Webhooks
================

استقبال ومعالجة الأحداث من Tap وبرامج المحاسبة
"""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .integrations import tap_client
from .signals import payment_completed, refund_requested

logger = logging.getLogger(__name__)


# =============================================
# Tap Webhooks
# =============================================

@csrf_exempt
@require_POST
def tap_webhook(request: HttpRequest) -> JsonResponse:
    """
    معالج Tap Webhook

    الأحداث المدعومة:
    - charge.captured: تم تأكيد الدفع
    - charge.failed: فشل الدفع
    - refund.created: تم إنشاء استرجاع
    - transfer.paid: تم تحويل المبلغ للتاجر
    """
    try:
        # التحقق من التوقيع
        signature = request.headers.get('Tap-Signature', '')
        payload = request.body

        event = tap_client.parse_webhook_event(payload, signature)

        if not event:
            logger.warning("Invalid Tap webhook received")
            return JsonResponse({'error': 'Invalid signature'}, status=401)

        event_type = event.get('type', '')
        data = event.get('data', {})

        logger.info(f"Received Tap webhook: {event_type}")

        # معالجة الحدث
        handler = TAP_WEBHOOK_HANDLERS.get(event_type)

        if handler:
            result = handler(data)
            return JsonResponse({'status': 'processed', 'result': result})
        else:
            logger.info(f"Unhandled Tap webhook type: {event_type}")
            return JsonResponse({'status': 'ignored'})

    except Exception as e:
        logger.error(f"Tap webhook error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def handle_charge_captured(data: Dict[str, Any]) -> Dict[str, Any]:
    """معالجة تأكيد الدفع"""
    from apps.orders.models import Order
    from .models import Transaction

    charge_id = data.get('id')
    reference_id = data.get('reference', {}).get('transaction')
    amount = Decimal(str(data.get('amount', 0)))

    logger.info(f"Charge captured: {charge_id}, order: {reference_id}")

    try:
        order = Order.objects.get(id=reference_id)

        # إرسال إشارة الدفع المكتمل
        payment_completed.send(
            sender=Order,
            order=order,
            payment_data={
                'tap_charge_id': charge_id,
                'tap_transaction_id': data.get('transaction', {}).get('id'),
                'method': data.get('source', {}).get('type', 'card'),
                'amount': float(amount),
                'captured_at': timezone.now().isoformat(),
            }
        )

        # تحديث حالة الطلب
        order.payment_status = 'paid'
        order.save(update_fields=['payment_status', 'updated_at'])

        return {'order_id': str(order.id), 'status': 'processed'}

    except Order.DoesNotExist:
        logger.error(f"Order not found for charge: {charge_id}")
        return {'error': 'Order not found'}


def handle_charge_failed(data: Dict[str, Any]) -> Dict[str, Any]:
    """معالجة فشل الدفع"""
    from apps.orders.models import Order
    from .models import Transaction

    charge_id = data.get('id')
    reference_id = data.get('reference', {}).get('transaction')
    failure_reason = data.get('response', {}).get('message', 'Unknown error')

    logger.warning(f"Charge failed: {charge_id}, reason: {failure_reason}")

    try:
        order = Order.objects.get(id=reference_id)

        # تسجيل المحاولة الفاشلة
        Transaction.objects.create(
            order=order,
            amount=Decimal(str(data.get('amount', 0))),
            currency='SAR',
            status='failed',
            tap_charge_id=charge_id,
            failure_reason=failure_reason,
            metadata=data,
        )

        # تحديث حالة الطلب
        order.payment_status = 'failed'
        order.save(update_fields=['payment_status', 'updated_at'])

        return {'order_id': str(order.id), 'status': 'failed'}

    except Order.DoesNotExist:
        logger.error(f"Order not found for failed charge: {charge_id}")
        return {'error': 'Order not found'}


def handle_refund_created(data: Dict[str, Any]) -> Dict[str, Any]:
    """معالجة إنشاء استرجاع"""
    from .models import Transaction
    from .services import ledger_service

    refund_id = data.get('id')
    charge_id = data.get('charge_id')
    amount = Decimal(str(data.get('amount', 0)))

    logger.info(f"Refund created: {refund_id}, amount: {amount}")

    try:
        # البحث عن المعاملة الأصلية
        original = Transaction.objects.filter(
            tap_charge_id=charge_id,
            status='completed'
        ).first()

        if original:
            # تسجيل الاسترجاع
            Transaction.objects.create(
                order=original.order,
                amount=-amount,
                currency='SAR',
                status='completed',
                transaction_type='refund',
                tap_charge_id=refund_id,
                parent_transaction=original,
                metadata=data,
            )

            # تسجيل في السجل المالي
            ledger_service.record_transaction(
                transaction_type='refund',
                amount=amount,
                currency='SAR',
                debit_account='customer_payments',
                credit_account='cash',
                reference_type='refund',
                reference_id=refund_id,
                metadata={'original_charge': charge_id}
            )

            return {'refund_id': refund_id, 'status': 'processed'}

        return {'error': 'Original transaction not found'}

    except Exception as e:
        logger.error(f"Refund processing error: {e}")
        return {'error': str(e)}


def handle_transfer_paid(data: Dict[str, Any]) -> Dict[str, Any]:
    """معالجة تحويل المبلغ للتاجر/السائق"""
    from .models import VendorBalance

    destination_id = data.get('destination')
    amount = Decimal(str(data.get('amount', 0)))
    transfer_id = data.get('id')

    logger.info(f"Transfer paid: {transfer_id}, destination: {destination_id}")

    try:
        # تحديث رصيد التاجر
        # نقل من المعلق إلى المتاح
        balance = VendorBalance.objects.filter(
            vendor__tap_account_id=destination_id
        ).first()

        if balance:
            balance.pending_balance -= amount
            balance.available_balance += amount
            balance.last_transfer_at = timezone.now()
            balance.save(update_fields=[
                'pending_balance',
                'available_balance',
                'last_transfer_at',
                'updated_at'
            ])

            return {'transfer_id': transfer_id, 'status': 'processed'}

        logger.warning(f"Balance not found for destination: {destination_id}")
        return {'error': 'Balance not found'}

    except Exception as e:
        logger.error(f"Transfer processing error: {e}")
        return {'error': str(e)}


# تسجيل المعالجات
TAP_WEBHOOK_HANDLERS = {
    'charge.captured': handle_charge_captured,
    'charge.failed': handle_charge_failed,
    'refund.created': handle_refund_created,
    'transfer.paid': handle_transfer_paid,
}


# =============================================
# Accounting Webhooks (Qoyod/Dafater)
# =============================================

@csrf_exempt
@require_POST
def accounting_webhook(request: HttpRequest) -> JsonResponse:
    """
    معالج Webhook من برنامج المحاسبة

    يستقبل تحديثات حالة ZATCA
    """
    try:
        import json
        data = json.loads(request.body)

        event_type = data.get('event_type', '')
        invoice_data = data.get('data', {})

        logger.info(f"Received accounting webhook: {event_type}")

        if event_type == 'invoice.zatca_cleared':
            return handle_zatca_cleared(invoice_data)

        elif event_type == 'invoice.zatca_rejected':
            return handle_zatca_rejected(invoice_data)

        elif event_type == 'invoice.zatca_reported':
            return handle_zatca_reported(invoice_data)

        return JsonResponse({'status': 'ignored'})

    except Exception as e:
        logger.error(f"Accounting webhook error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def handle_zatca_cleared(data: Dict[str, Any]) -> JsonResponse:
    """معالجة اعتماد الفاتورة من ZATCA"""
    from .models import Invoice

    provider_invoice_id = data.get('invoice_id')
    qr_code = data.get('qr_code')
    clearance_hash = data.get('clearance_hash')

    try:
        invoice = Invoice.objects.get(
            accounting_provider_id=provider_invoice_id
        )

        invoice.zatca_status = 'cleared'
        invoice.zatca_qr_code = qr_code
        invoice.zatca_hash = clearance_hash
        invoice.zatca_cleared_at = timezone.now()
        invoice.save()

        logger.info(f"Invoice ZATCA cleared: {invoice.invoice_number}")

        return JsonResponse({'status': 'processed'})

    except Invoice.DoesNotExist:
        logger.warning(f"Invoice not found: {provider_invoice_id}")
        return JsonResponse({'error': 'Invoice not found'}, status=404)


def handle_zatca_rejected(data: Dict[str, Any]) -> JsonResponse:
    """معالجة رفض الفاتورة من ZATCA"""
    from .models import Invoice

    provider_invoice_id = data.get('invoice_id')
    rejection_reason = data.get('rejection_reason')

    try:
        invoice = Invoice.objects.get(
            accounting_provider_id=provider_invoice_id
        )

        invoice.zatca_status = 'rejected'
        invoice.zatca_rejection_reason = rejection_reason
        invoice.save()

        logger.warning(f"Invoice ZATCA rejected: {invoice.invoice_number}, reason: {rejection_reason}")

        # إشعار الفريق المالي
        from .tasks import notify_finance_team
        notify_finance_team.delay(
            subject=f"تنبيه: رفض فاتورة من ZATCA - {invoice.invoice_number}",
            report={
                'invoice_number': invoice.invoice_number,
                'rejection_reason': rejection_reason,
            },
            priority='high'
        )

        return JsonResponse({'status': 'processed'})

    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)


def handle_zatca_reported(data: Dict[str, Any]) -> JsonResponse:
    """معالجة الإبلاغ عن الفاتورة لـ ZATCA (simplified)"""
    from .models import Invoice

    provider_invoice_id = data.get('invoice_id')
    report_hash = data.get('report_hash')

    try:
        invoice = Invoice.objects.get(
            accounting_provider_id=provider_invoice_id
        )

        invoice.zatca_status = 'reported'
        invoice.zatca_hash = report_hash
        invoice.save()

        logger.info(f"Invoice ZATCA reported: {invoice.invoice_number}")

        return JsonResponse({'status': 'processed'})

    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
