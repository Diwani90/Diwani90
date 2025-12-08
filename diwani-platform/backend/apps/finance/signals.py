"""
إشارات النظام المالي
====================

التسجيل التلقائي للمعاملات المالية
"""

import logging
from decimal import Decimal
from typing import Any, Dict

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone

logger = logging.getLogger(__name__)


# =============================================
# إشارات مخصصة
# =============================================

# عند إتمام الدفع
payment_completed = Signal()

# عند تأكيد الطلب
order_confirmed = Signal()

# عند اكتمال التوصيل
delivery_completed = Signal()

# عند طلب استرجاع
refund_requested = Signal()


# =============================================
# معالجات الإشارات
# =============================================

@receiver(payment_completed)
def handle_payment_completed(sender, **kwargs):
    """
    معالجة إتمام الدفع

    يُسجل المعاملة في:
    1. جدول Transaction
    2. السجل المالي (Ledger)
    """
    from .models import Transaction, LedgerEntry
    from .services import ledger_service, commission_service

    order = kwargs.get('order')
    payment_data = kwargs.get('payment_data', {})

    if not order:
        logger.warning("Payment completed signal received without order")
        return

    try:
        # إنشاء سجل المعاملة
        transaction = Transaction.objects.create(
            order=order,
            amount=order.total_amount,
            currency='SAR',
            status='completed',
            payment_method=payment_data.get('method', 'card'),
            tap_charge_id=payment_data.get('tap_charge_id'),
            tap_transaction_id=payment_data.get('tap_transaction_id'),
            metadata=payment_data,
        )

        # حساب التوزيعات
        split = commission_service.calculate_split(
            order_amount=order.items_total,
            delivery_amount=order.delivery_total or Decimal('0'),
            vendor_id=str(order.vendor_id),
            driver_id=str(order.driver_id) if order.driver_id else None,
        )

        # تسجيل في السجل المالي
        # 1. استلام المبلغ من العميل
        ledger_service.record_transaction(
            transaction_type='payment_received',
            amount=order.total_amount,
            currency='SAR',
            debit_account='cash',
            credit_account='customer_payments',
            reference_type='order',
            reference_id=str(order.id),
            metadata={
                'transaction_id': str(transaction.id),
                'tap_charge_id': payment_data.get('tap_charge_id'),
            }
        )

        # 2. عمولة المنصة من التاجر
        ledger_service.record_transaction(
            transaction_type='commission',
            amount=split['vendor_commission'],
            currency='SAR',
            debit_account='vendor_payable',
            credit_account='platform_revenue',
            reference_type='order',
            reference_id=str(order.id),
            metadata={
                'vendor_id': str(order.vendor_id),
                'commission_rate': float(split['vendor_commission'] / order.items_total * 100) if order.items_total else 0,
            }
        )

        # 3. تسجيل مستحقات التاجر
        ledger_service.record_transaction(
            transaction_type='vendor_earning',
            amount=split['vendor_payout'],
            currency='SAR',
            debit_account='customer_payments',
            credit_account='vendor_payable',
            reference_type='order',
            reference_id=str(order.id),
            metadata={
                'vendor_id': str(order.vendor_id),
            }
        )

        # 4. عمولة ومستحقات السائق (إن وجد)
        if split['driver_payout'] > 0:
            ledger_service.record_transaction(
                transaction_type='commission',
                amount=split['driver_commission'],
                currency='SAR',
                debit_account='driver_payable',
                credit_account='platform_revenue',
                reference_type='order',
                reference_id=str(order.id),
                metadata={
                    'driver_id': str(order.driver_id),
                }
            )

            ledger_service.record_transaction(
                transaction_type='driver_earning',
                amount=split['driver_payout'],
                currency='SAR',
                debit_account='customer_payments',
                credit_account='driver_payable',
                reference_type='order',
                reference_id=str(order.id),
                metadata={
                    'driver_id': str(order.driver_id),
                }
            )

        # تحديث أرصدة البائعين
        _update_vendor_balance(order.vendor_id, split['vendor_payout'])

        if order.driver_id:
            _update_driver_balance(order.driver_id, split['driver_payout'])

        logger.info(f"Payment completed processed for order {order.id}")

    except Exception as e:
        logger.error(f"Error processing payment completed: {e}")
        raise


@receiver(order_confirmed)
def handle_order_confirmed(sender, **kwargs):
    """
    معالجة تأكيد الطلب

    إنشاء الفاتورة وإرسالها لبرنامج المحاسبة
    """
    from .models import Invoice
    from .services import invoice_service
    from .tasks import sync_invoice_to_accounting

    order = kwargs.get('order')

    if not order:
        return

    try:
        # إنشاء بيانات الفاتورة
        invoice_data = invoice_service.create_invoice(
            order_id=str(order.id),
            customer_info={
                'id': str(order.customer_id),
                'name': order.customer.name,
                'vat_number': getattr(order.customer, 'vat_number', None),
                'phone': order.customer.phone,
                'address': order.delivery_address,
            },
            vendor_info={
                'id': str(order.vendor_id),
                'name': order.vendor.name,
                'vat_number': order.vendor.vat_number,
                'cr_number': order.vendor.cr_number,
                'address': order.vendor.address,
            },
            line_items=[
                {
                    'name': item.product_name,
                    'quantity': item.quantity,
                    'price': float(item.unit_price),
                }
                for item in order.items.all()
            ],
            delivery_info={
                'amount': float(order.delivery_total or 0),
                'description': 'رسوم التوصيل',
            } if order.delivery_total else None
        )

        # حفظ الفاتورة
        invoice = Invoice.objects.create(
            order=order,
            invoice_number=invoice_data['invoice_number'],
            invoice_date=timezone.now(),
            vendor_name=invoice_data['vendor']['name'],
            vendor_vat=invoice_data['vendor']['vat_number'],
            vendor_cr=invoice_data['vendor']['cr_number'],
            customer_name=invoice_data['customer']['name'],
            customer_vat=invoice_data['customer'].get('vat_number'),
            customer_phone=invoice_data['customer']['phone'],
            line_items=invoice_data['line_items'],
            subtotal=invoice_data['subtotal'],
            delivery_total=invoice_data['delivery_total'],
            tax_rate=invoice_data['tax_rate'],
            tax_amount=invoice_data['tax_amount'],
            total=invoice_data['total'],
        )

        # إرسال لبرنامج المحاسبة (async)
        sync_invoice_to_accounting.delay(str(invoice.id))

        logger.info(f"Invoice created for order {order.id}: {invoice.invoice_number}")

    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        # لا نريد إيقاف الطلب بسبب خطأ في الفاتورة
        # سيتم إعادة المحاولة لاحقاً


@receiver(delivery_completed)
def handle_delivery_completed(sender, **kwargs):
    """
    معالجة اكتمال التوصيل

    تحديث حالة المعاملة وإرسال الإيصال
    """
    from .models import Transaction

    order = kwargs.get('order')
    delivery_data = kwargs.get('delivery_data', {})

    if not order:
        return

    try:
        # تحديث المعاملة
        Transaction.objects.filter(
            order=order,
            status='completed'
        ).update(
            delivery_confirmed_at=timezone.now(),
            metadata__delivery=delivery_data,
        )

        # يمكن إرسال إيصال للعميل هنا
        logger.info(f"Delivery completed for order {order.id}")

    except Exception as e:
        logger.error(f"Error processing delivery completed: {e}")


@receiver(refund_requested)
def handle_refund_requested(sender, **kwargs):
    """
    معالجة طلب الاسترجاع
    """
    from .models import Transaction
    from .services import ledger_service
    from .integrations import tap_client

    order = kwargs.get('order')
    refund_amount = kwargs.get('amount')
    reason = kwargs.get('reason', '')

    if not order or not refund_amount:
        return

    try:
        # البحث عن المعاملة الأصلية
        original_transaction = Transaction.objects.filter(
            order=order,
            status='completed'
        ).first()

        if not original_transaction:
            logger.error(f"No completed transaction found for order {order.id}")
            return

        # طلب الاسترجاع من Tap
        if original_transaction.tap_charge_id:
            tap_refund = tap_client.refund_payment(
                charge_id=original_transaction.tap_charge_id,
                amount=Decimal(str(refund_amount)),
                reason=reason,
                metadata={'order_id': str(order.id)}
            )

            # إنشاء معاملة الاسترجاع
            refund_transaction = Transaction.objects.create(
                order=order,
                amount=-refund_amount,  # سالب للاسترجاع
                currency='SAR',
                status='completed',
                transaction_type='refund',
                tap_charge_id=tap_refund.get('id'),
                parent_transaction=original_transaction,
                metadata={
                    'reason': reason,
                    'tap_refund': tap_refund,
                }
            )

            # تسجيل في السجل المالي
            ledger_service.record_transaction(
                transaction_type='refund',
                amount=refund_amount,
                currency='SAR',
                debit_account='customer_payments',
                credit_account='cash',
                reference_type='refund',
                reference_id=str(refund_transaction.id),
                metadata={
                    'original_transaction': str(original_transaction.id),
                    'reason': reason,
                }
            )

            logger.info(f"Refund processed for order {order.id}: {refund_amount}")

    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        raise


# =============================================
# وظائف مساعدة
# =============================================

def _update_vendor_balance(vendor_id: str, amount: Decimal):
    """تحديث رصيد التاجر"""
    from .models import VendorBalance

    balance, created = VendorBalance.objects.get_or_create(
        vendor_id=vendor_id,
        defaults={'available_balance': Decimal('0'), 'pending_balance': Decimal('0')}
    )

    # المبلغ يذهب للرصيد المعلق أولاً
    # سيتحول لمتاح بعد فترة الانتظار أو التأكيد
    balance.pending_balance += amount
    balance.save(update_fields=['pending_balance', 'updated_at'])


def _update_driver_balance(driver_id: str, amount: Decimal):
    """تحديث رصيد السائق"""
    from .models import VendorBalance

    # نستخدم نفس النموذج للسائقين
    balance, created = VendorBalance.objects.get_or_create(
        vendor_id=driver_id,
        vendor_type='driver',
        defaults={'available_balance': Decimal('0'), 'pending_balance': Decimal('0')}
    )

    balance.pending_balance += amount
    balance.save(update_fields=['pending_balance', 'updated_at'])


def connect_order_signals():
    """
    ربط الإشارات بنماذج الطلبات

    يُستدعى من apps.py
    """
    try:
        from apps.orders.models import Order

        @receiver(post_save, sender=Order)
        def order_saved_handler(sender, instance, created, **kwargs):
            """معالجة حفظ الطلب"""
            if not created:
                # تحديث حالة الطلب
                if instance.status == 'confirmed' and not hasattr(instance, '_confirmed_signal_sent'):
                    instance._confirmed_signal_sent = True
                    order_confirmed.send(sender=sender, order=instance)

                elif instance.status == 'delivered' and not hasattr(instance, '_delivered_signal_sent'):
                    instance._delivered_signal_sent = True
                    delivery_completed.send(sender=sender, order=instance)

        logger.info("Order signals connected successfully")

    except ImportError:
        logger.warning("Orders app not found, signals not connected")
