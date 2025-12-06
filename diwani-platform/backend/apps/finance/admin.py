"""
لوحة تحكم النظام المالي
========================
"""

from decimal import Decimal

from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    LedgerEntry,
    Transaction,
    CommissionRule,
    VendorBalance,
    Payout,
    ReconciliationRecord,
    PricingRule,
    DeliveryPricingRule,
    Invoice,
)


# =============================================
# السجل المالي
# =============================================

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    """إدارة السجل المالي - للقراءة فقط"""

    list_display = [
        'id', 'transaction_type', 'amount_display', 'currency',
        'debit_account', 'credit_account', 'reference_type',
        'created_at'
    ]
    list_filter = ['transaction_type', 'currency', 'created_at']
    search_fields = ['reference_id', 'debit_account', 'credit_account']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'id', 'transaction_type', 'amount', 'currency',
        'debit_account', 'credit_account', 'reference_type',
        'reference_id', 'metadata', 'checksum', 'created_at'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def amount_display(self, obj):
        color = 'green' if obj.amount > 0 else 'red'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, obj.amount, obj.currency
        )
    amount_display.short_description = 'المبلغ'


# =============================================
# المعاملات
# =============================================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """إدارة المعاملات"""

    list_display = [
        'id', 'order_link', 'amount_display', 'status_badge',
        'payment_method', 'tap_charge_id', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['tap_charge_id', 'tap_transaction_id', 'order__id']
    date_hierarchy = 'created_at'
    readonly_fields = ['tap_charge_id', 'tap_transaction_id', 'checksum']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('order', 'amount', 'currency', 'status')
        }),
        ('طريقة الدفع', {
            'fields': ('payment_method', 'tap_charge_id', 'tap_transaction_id')
        }),
        ('تفاصيل إضافية', {
            'fields': ('failure_reason', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    def order_link(self, obj):
        if obj.order:
            return format_html(
                '<a href="/admin/orders/order/{}/change/">{}</a>',
                obj.order.id, obj.order.id
            )
        return '-'
    order_link.short_description = 'الطلب'

    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'المبلغ'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'gray',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'


# =============================================
# قواعد العمولات
# =============================================

@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    """إدارة قواعد العمولات"""

    list_display = [
        'name', 'rule_type', 'rate_display', 'category',
        'min_amount', 'max_amount', 'is_active', 'priority'
    ]
    list_filter = ['rule_type', 'is_active', 'category']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'priority']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'rule_type', 'is_active', 'priority')
        }),
        ('نسبة العمولة', {
            'fields': ('rate', 'fixed_amount')
        }),
        ('الشروط', {
            'fields': ('category', 'vendor', 'min_amount', 'max_amount')
        }),
        ('الصلاحية', {
            'fields': ('valid_from', 'valid_until')
        }),
    )

    def rate_display(self, obj):
        if obj.rate:
            return f"{obj.rate}%"
        elif obj.fixed_amount:
            return f"{obj.fixed_amount} SAR"
        return '-'
    rate_display.short_description = 'النسبة/المبلغ'


# =============================================
# أرصدة البائعين
# =============================================

@admin.register(VendorBalance)
class VendorBalanceAdmin(admin.ModelAdmin):
    """إدارة أرصدة البائعين"""

    list_display = [
        'vendor', 'vendor_type', 'available_balance', 'pending_balance',
        'total_earned', 'total_withdrawn', 'last_synced_at'
    ]
    list_filter = ['vendor_type', 'last_synced_at']
    search_fields = ['vendor__name']
    readonly_fields = [
        'available_balance', 'pending_balance', 'total_earned',
        'total_withdrawn', 'last_synced_at'
    ]

    def has_add_permission(self, request):
        return False


# =============================================
# طلبات السحب
# =============================================

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """إدارة طلبات السحب"""

    list_display = [
        'id', 'vendor', 'amount_display', 'status_badge',
        'method', 'created_at', 'processed_at'
    ]
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['vendor__name', 'bank_account']
    date_hierarchy = 'created_at'
    actions = ['approve_payouts', 'reject_payouts']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('vendor', 'amount', 'method', 'status')
        }),
        ('معلومات البنك', {
            'fields': ('bank_account', 'bank_name')
        }),
        ('المعالجة', {
            'fields': ('processed_at', 'processed_by', 'failure_reason')
        }),
    )

    def amount_display(self, obj):
        return f"{obj.amount} SAR"
    amount_display.short_description = 'المبلغ'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    @admin.action(description='الموافقة على طلبات السحب المحددة')
    def approve_payouts(self, request, queryset):
        from .tasks import process_vendor_payout
        for payout in queryset.filter(status='pending'):
            payout.status = 'processing'
            payout.save()
            process_vendor_payout.delay(str(payout.id))
        self.message_user(request, f'تمت الموافقة على {queryset.count()} طلب')

    @admin.action(description='رفض طلبات السحب المحددة')
    def reject_payouts(self, request, queryset):
        queryset.filter(status='pending').update(
            status='cancelled',
            failure_reason='Rejected by admin'
        )


# =============================================
# سجلات التسوية
# =============================================

@admin.register(ReconciliationRecord)
class ReconciliationRecordAdmin(admin.ModelAdmin):
    """إدارة سجلات التسوية"""

    list_display = [
        'reconciliation_date', 'transaction_id', 'status_badge',
        'our_amount', 'provider_amount', 'difference',
        'requires_review', 'reviewed_at'
    ]
    list_filter = ['status', 'requires_review', 'provider', 'reconciliation_date']
    search_fields = ['transaction_id', 'provider_reference']
    date_hierarchy = 'reconciliation_date'
    readonly_fields = [
        'transaction_id', 'our_amount', 'provider_amount',
        'difference', 'provider_reference'
    ]
    actions = ['mark_as_reviewed']

    def status_badge(self, obj):
        colors = {
            'matched': 'green',
            'discrepancy': 'red',
            'missing_in_provider': 'orange',
            'missing_in_our_system': 'purple',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.status
        )
    status_badge.short_description = 'الحالة'

    @admin.action(description='تعليم كمراجع')
    def mark_as_reviewed(self, request, queryset):
        queryset.update(
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )


# =============================================
# قواعد التسعير
# =============================================

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    """إدارة قواعد التسعير"""

    list_display = [
        'name', 'pricing_type', 'base_price', 'category',
        'is_active', 'priority'
    ]
    list_filter = ['pricing_type', 'is_active', 'category']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'priority']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'pricing_type', 'is_active', 'priority')
        }),
        ('التسعير', {
            'fields': ('base_price', 'minimum_charge')
        }),
        ('إعدادات إضافية', {
            'fields': ('config', 'category', 'vendor'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeliveryPricingRule)
class DeliveryPricingRuleAdmin(admin.ModelAdmin):
    """إدارة قواعد تسعير التوصيل"""

    list_display = [
        'name', 'pricing_type', 'base_fee', 'rate_per_km',
        'free_km', 'is_active'
    ]
    list_filter = ['pricing_type', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']


# =============================================
# الفواتير
# =============================================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """إدارة الفواتير"""

    list_display = [
        'invoice_number', 'order_link', 'vendor_name', 'customer_name',
        'total', 'zatca_status_badge', 'invoice_date'
    ]
    list_filter = ['zatca_status', 'invoice_date']
    search_fields = ['invoice_number', 'vendor_name', 'customer_name']
    date_hierarchy = 'invoice_date'
    readonly_fields = [
        'invoice_number', 'accounting_provider', 'accounting_provider_id',
        'zatca_status', 'zatca_qr_code', 'zatca_hash'
    ]

    fieldsets = (
        ('معلومات الفاتورة', {
            'fields': ('invoice_number', 'invoice_date', 'order')
        }),
        ('البائع', {
            'fields': ('vendor_name', 'vendor_vat', 'vendor_cr')
        }),
        ('العميل', {
            'fields': ('customer_name', 'customer_vat', 'customer_phone')
        }),
        ('المبالغ', {
            'fields': ('subtotal', 'delivery_total', 'tax_rate', 'tax_amount', 'total')
        }),
        ('ZATCA', {
            'fields': (
                'zatca_status', 'accounting_provider', 'accounting_provider_id',
                'zatca_qr_code', 'zatca_hash'
            ),
            'classes': ('collapse',)
        }),
    )

    def order_link(self, obj):
        if obj.order:
            return format_html(
                '<a href="/admin/orders/order/{}/change/">{}</a>',
                obj.order.id, str(obj.order.id)[:8]
            )
        return '-'
    order_link.short_description = 'الطلب'

    def zatca_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'submitted': 'blue',
            'cleared': 'green',
            'reported': 'green',
            'rejected': 'red',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.zatca_status, 'gray'), obj.zatca_status
        )
    zatca_status_badge.short_description = 'حالة ZATCA'
