"""
مهام Celery المالية
===================

المهام المجدولة للتسوية والمزامنة
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


# =============================================
# مهام التسوية - Reconciliation Tasks
# =============================================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue='finance'
)
def run_daily_reconciliation(self, date_str: Optional[str] = None):
    """
    التسوية اليومية مع Tap

    تُنفذ يومياً الساعة 2 صباحاً (بعد انتهاء يوم العمل)
    """
    from .models import Transaction, ReconciliationRecord
    from .services import reconciliation_engine
    from .integrations import tap_client

    try:
        # تحديد التاريخ
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=1)).date()

        start_datetime = timezone.make_aware(
            datetime.combine(target_date, datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            datetime.combine(target_date, datetime.max.time())
        )

        logger.info(f"Starting reconciliation for: {target_date}")

        # جلب معاملاتنا
        our_transactions = Transaction.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime,
            status='completed'
        ).values(
            'id', 'tap_charge_id', 'amount', 'currency'
        )

        our_records = [
            {
                'transaction_id': str(t['id']),
                'tap_charge_id': t['tap_charge_id'],
                'amount': t['amount'],
            }
            for t in our_transactions
        ]

        # جلب بيانات Tap
        tap_report = tap_client.get_settlement_report(
            start_date=start_datetime,
            end_date=end_datetime
        )

        provider_records = [
            {
                'transaction_id': c.get('reference', {}).get('transaction'),
                'amount': Decimal(str(c.get('amount', 0))),
                'reference': c.get('id'),
            }
            for c in tap_report.get('charges', [])
            if c.get('status') == 'CAPTURED'
        ]

        # تنفيذ التسوية
        results = reconciliation_engine.reconcile_batch(
            our_records=our_records,
            provider_records=provider_records,
            match_key='transaction_id'
        )

        # إنشاء تقرير
        report = reconciliation_engine.generate_report(results)

        # حفظ النتائج
        with transaction.atomic():
            for result in results['matched']:
                ReconciliationRecord.objects.create(
                    transaction_id=result.transaction_id,
                    reconciliation_date=target_date,
                    our_amount=result.our_amount,
                    provider_amount=result.provider_amount,
                    status='matched',
                    provider='tap',
                    provider_reference=result.provider_reference,
                )

            for result in results['discrepancies']:
                ReconciliationRecord.objects.create(
                    transaction_id=result.transaction_id,
                    reconciliation_date=target_date,
                    our_amount=result.our_amount,
                    provider_amount=result.provider_amount,
                    difference=result.difference,
                    status='discrepancy',
                    provider='tap',
                    provider_reference=result.provider_reference,
                    notes=f"Discrepancy: {result.details}",
                    requires_review=True,
                )

            for result in results['missing_in_provider']:
                ReconciliationRecord.objects.create(
                    transaction_id=result.transaction_id,
                    reconciliation_date=target_date,
                    our_amount=result.our_amount,
                    status='missing_in_provider',
                    provider='tap',
                    requires_review=True,
                )

        logger.info(f"Reconciliation completed: {report}")

        # إرسال تنبيه إذا كانت هناك مشاكل
        if report['requires_investigation']:
            notify_finance_team.delay(
                subject=f"تنبيه: مشاكل في تسوية {target_date}",
                report=report
            )

        return report

    except Exception as e:
        logger.error(f"Reconciliation failed: {e}")
        self.retry(exc=e)


@shared_task(queue='finance')
def run_weekly_reconciliation_summary():
    """
    ملخص التسوية الأسبوعي

    يُرسل للإدارة المالية كل أحد
    """
    from .models import ReconciliationRecord

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)

    # إحصائيات الأسبوع
    stats = ReconciliationRecord.objects.filter(
        reconciliation_date__gte=start_date,
        reconciliation_date__lte=end_date
    ).aggregate(
        total_matched=Sum('our_amount', filter=Q(status='matched')),
        total_discrepancies=Sum('difference', filter=Q(status='discrepancy')),
        discrepancy_count=Sum(
            1, filter=Q(status='discrepancy'), output_field=models.IntegerField()
        ),
    )

    pending_review = ReconciliationRecord.objects.filter(
        requires_review=True,
        reviewed_at__isnull=True
    ).count()

    report = {
        'period': f"{start_date} - {end_date}",
        'total_matched': float(stats.get('total_matched') or 0),
        'total_discrepancies': float(stats.get('total_discrepancies') or 0),
        'discrepancy_count': stats.get('discrepancy_count') or 0,
        'pending_review': pending_review,
    }

    logger.info(f"Weekly reconciliation summary: {report}")

    # إرسال التقرير
    notify_finance_team.delay(
        subject=f"ملخص التسوية الأسبوعي: {start_date} - {end_date}",
        report=report
    )

    return report


# =============================================
# مهام المزامنة - Sync Tasks
# =============================================

@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    queue='finance'
)
def sync_invoice_to_accounting(self, invoice_id: str):
    """
    مزامنة فاتورة مع برنامج المحاسبة (قيود/دفاتر)
    """
    from .models import Invoice
    from .integrations import accounting_sync

    try:
        invoice = Invoice.objects.select_related('order').get(id=invoice_id)

        # تحضير البيانات
        invoice_data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date.isoformat(),
            'vendor': {
                'name': invoice.vendor_name,
                'vat_number': invoice.vendor_vat,
                'cr_number': invoice.vendor_cr,
            },
            'customer': {
                'name': invoice.customer_name,
                'vat_number': invoice.customer_vat,
                'phone': invoice.customer_phone,
            },
            'line_items': invoice.line_items,
            'subtotal': float(invoice.subtotal),
            'tax_amount': float(invoice.tax_amount),
            'total': float(invoice.total),
        }

        # المزامنة
        result = accounting_sync.sync_order_invoice(
            order_id=str(invoice.order_id),
            invoice_data=invoice_data
        )

        if result['success']:
            invoice.accounting_provider = result['accounting_provider']
            invoice.accounting_provider_id = result['provider_invoice_id']
            invoice.zatca_status = result.get('zatca_status', 'pending')
            invoice.save()

            logger.info(f"Invoice {invoice_id} synced to accounting")
        else:
            logger.error(f"Invoice sync failed: {result.get('error')}")
            raise Exception(result.get('error'))

        return result

    except Invoice.DoesNotExist:
        logger.error(f"Invoice not found: {invoice_id}")
        return {'success': False, 'error': 'Invoice not found'}

    except Exception as e:
        logger.error(f"Invoice sync error: {e}")
        self.retry(exc=e)


@shared_task(queue='finance')
def sync_pending_zatca_invoices():
    """
    مزامنة حالة ZATCA للفواتير المعلقة

    تُنفذ كل ساعة
    """
    from .integrations import accounting_sync

    result = accounting_sync.sync_pending_invoices()
    logger.info(f"ZATCA sync completed: {result}")
    return result


# =============================================
# مهام الأرصدة والتحويلات
# =============================================

@shared_task(
    bind=True,
    max_retries=3,
    queue='finance'
)
def process_vendor_payout(self, payout_id: str):
    """
    معالجة طلب سحب رصيد التاجر

    ملاحظة: Tap Connect يتولى التحويلات تلقائياً
    هذا للتحويلات اليدوية أو الخاصة
    """
    from .models import Payout, VendorBalance
    from .integrations import tap_client

    try:
        payout = Payout.objects.select_related('vendor').get(id=payout_id)

        if payout.status != 'pending':
            return {'success': False, 'error': 'Payout already processed'}

        # التحقق من الرصيد
        balance = VendorBalance.objects.get(vendor=payout.vendor)

        if balance.available_balance < payout.amount:
            payout.status = 'failed'
            payout.failure_reason = 'Insufficient balance'
            payout.save()
            return {'success': False, 'error': 'Insufficient balance'}

        # تنفيذ التحويل (إذا لم يكن عبر Tap Connect)
        if payout.method == 'bank_transfer':
            # هنا يمكن التكامل مع بنك محلي
            # أو الإبقاء كـ manual للمراجعة
            payout.status = 'processing'
            payout.save()

            logger.info(f"Payout {payout_id} marked for manual processing")

        return {
            'success': True,
            'payout_id': str(payout_id),
            'status': payout.status,
        }

    except Payout.DoesNotExist:
        return {'success': False, 'error': 'Payout not found'}

    except Exception as e:
        logger.error(f"Payout processing error: {e}")
        self.retry(exc=e)


@shared_task(queue='finance')
def update_vendor_balances():
    """
    تحديث أرصدة التجار من Tap

    تُنفذ كل 6 ساعات
    """
    from .models import VendorBalance
    from .integrations import tap_client

    updated = 0
    errors = []

    balances = VendorBalance.objects.filter(
        vendor__tap_account_id__isnull=False
    ).select_related('vendor')

    for balance in balances:
        try:
            tap_balance = tap_client.get_balance(
                account_id=balance.vendor.tap_account_id
            )

            balance.pending_balance = Decimal(
                str(tap_balance.get('pending', 0))
            )
            balance.last_synced_at = timezone.now()
            balance.save()

            updated += 1

        except Exception as e:
            errors.append({
                'vendor_id': str(balance.vendor_id),
                'error': str(e)
            })

    logger.info(f"Vendor balances updated: {updated}, errors: {len(errors)}")

    return {
        'updated': updated,
        'errors': errors,
    }


# =============================================
# مهام سلامة البيانات
# =============================================

@shared_task(queue='finance')
def verify_ledger_integrity():
    """
    التحقق من سلامة السجل المالي

    تُنفذ يومياً للتأكد من عدم التلاعب
    """
    from .services import ledger_service

    # التحقق من آخر 7 أيام
    start_date = timezone.now() - timedelta(days=7)

    result = ledger_service.verify_chain_integrity(start_date=start_date)

    if not result['valid']:
        logger.critical(f"LEDGER INTEGRITY VIOLATION: {result['errors']}")

        # تنبيه فوري
        notify_finance_team.delay(
            subject="🚨 تحذير: مشكلة في سلامة السجل المالي",
            report=result,
            priority='critical'
        )

    logger.info(f"Ledger integrity check: {result}")
    return result


@shared_task(queue='finance')
def generate_daily_financial_report():
    """
    تقرير مالي يومي

    يُرسل للإدارة كل صباح
    """
    from .models import Transaction, LedgerEntry
    from django.db.models import Count

    yesterday = (timezone.now() - timedelta(days=1)).date()

    # إحصائيات المعاملات
    transactions_stats = Transaction.objects.filter(
        created_at__date=yesterday
    ).aggregate(
        total_amount=Sum('amount'),
        count=Count('id'),
        successful=Count('id', filter=Q(status='completed')),
        failed=Count('id', filter=Q(status='failed')),
    )

    # إحصائيات العمولات
    commissions = LedgerEntry.objects.filter(
        created_at__date=yesterday,
        transaction_type='commission'
    ).aggregate(
        platform_revenue=Sum('amount'),
    )

    report = {
        'date': str(yesterday),
        'transactions': {
            'count': transactions_stats.get('count') or 0,
            'total_amount': float(transactions_stats.get('total_amount') or 0),
            'successful': transactions_stats.get('successful') or 0,
            'failed': transactions_stats.get('failed') or 0,
        },
        'revenue': {
            'platform_commissions': float(commissions.get('platform_revenue') or 0),
        },
    }

    logger.info(f"Daily financial report: {report}")

    notify_finance_team.delay(
        subject=f"التقرير المالي اليومي: {yesterday}",
        report=report
    )

    return report


# =============================================
# مهام الإشعارات
# =============================================

@shared_task(queue='notifications')
def notify_finance_team(
    subject: str,
    report: Dict[str, Any],
    priority: str = 'normal'
):
    """
    إرسال إشعار لفريق المالية
    """
    from apps.notifications.services import NotificationService

    # قائمة البريد الإلكتروني للفريق المالي
    finance_emails = getattr(settings, 'FINANCE_TEAM_EMAILS', [])

    for email in finance_emails:
        try:
            # إرسال بريد إلكتروني
            NotificationService.send_email(
                to=email,
                subject=subject,
                template='finance/report_email.html',
                context={'report': report, 'priority': priority}
            )
        except Exception as e:
            logger.error(f"Failed to notify {email}: {e}")

    # إرسال إشعار داخلي للمستخدمين المعنيين
    # يمكن التوسع لاحقاً

    return {'notified': len(finance_emails)}


# =============================================
# مهام التنظيف
# =============================================

@shared_task(queue='finance')
def cleanup_old_reconciliation_records():
    """
    تنظيف سجلات التسوية القديمة

    الاحتفاظ بـ 2 سنة فقط (متطلبات ZATCA)
    """
    from .models import ReconciliationRecord

    cutoff_date = timezone.now().date() - timedelta(days=730)  # 2 سنة

    # حذف السجلات المتطابقة القديمة فقط
    # الاحتفاظ بالتناقضات للأرشيف
    deleted, _ = ReconciliationRecord.objects.filter(
        reconciliation_date__lt=cutoff_date,
        status='matched',
        requires_review=False
    ).delete()

    logger.info(f"Cleaned up {deleted} old reconciliation records")

    return {'deleted': deleted}
