"""
لوحة تحكم النظام المالي
========================
"""

from decimal import Decimal

from django.contrib import admin
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
        'id', 'entry_type', 'amount_display', 'currency',
        'from_account', 'to_account', 'reference_type',
        'recorded_at'
    ]
    list_filter = ['entry_type', 'currency', 'recorded_at']
    search_fields = ['reference_id', 'from_account', 'to_account']
    date_hierarchy = 'recorded_at'
    readonly_fields = [
        'id', 'entry_type', 'amount', 'currency',
        'from_account', 'to_account', 'reference_type',
        'reference_id', 'metadata', 'checksum', 'recorded_at'
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
        'id', 'type', 'gross_amount_display', 'status_badge',
        'payment_method', 'provider_transaction_id', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['provider_transaction_id', 'order_id']
    date_hierarchy = 'created_at'
    readonly_fields = ['provider_transaction_id', 'provider_response']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('type', 'gross_amount', 'net_amount', 'currency', 'status')
        }),
        ('طريقة الدفع', {
            'fields': ('payment_method', 'payment_provider', 'provider_transaction_id')
        }),
        ('الأطراف', {
            'fields': ('payer_type', 'payer_id', 'payee_type', 'payee_id')
        }),
        ('المرجع', {
            'fields': ('order_id', 'booking_id')
        }),
        ('تفاصيل إضافية', {
            'fields': ('description', 'metadata', 'provider_response'),
            'classes': ('collapse',)
        }),
    )

    def gross_amount_display(self, obj):
        return f"{obj.gross_amount} {obj.currency}"
    gross_amount_display.short_description = 'المبلغ'

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
        'name', 'applies_to', 'rate_display',
        'min_commission', 'max_commission', 'is_active', 'priority'
    ]
    list_filter = ['applies_to', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'priority']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'applies_to', 'is_active', 'priority')
        }),
        ('نسبة العمولة', {
            'fields': ('platform_percentage', 'fixed_fee')
        }),
        ('الحدود', {
            'fields': ('min_commission', 'max_commission')
        }),
        ('النطاق', {
            'fields': ('category_id', 'store_id', 'product_id')
        }),
        ('الصلاحية', {
            'fields': ('valid_from', 'valid_until')
        }),
    )

    def rate_display(self, obj):
        if obj.platform_percentage:
            return f"{obj.platform_percentage}%"
        elif obj.fixed_fee:
            return f"{obj.fixed_fee} SAR"
        return '-'
    rate_display.short_description = 'النسبة/المبلغ'


# =============================================
# أرصدة البائعين
# =============================================

@admin.register(VendorBalance)
class VendorBalanceAdmin(admin.ModelAdmin):
    """إدارة أرصدة البائعين"""

    list_display = [
        'owner_type', 'owner_id', 'available_balance', 'pending_balance',
        'total_earned', 'total_withdrawn', 'updated_at'
    ]
    list_filter = ['owner_type', 'auto_payout']
    search_fields = ['owner_id', 'bank_name', 'bank_iban']
    readonly_fields = [
        'available_balance', 'pending_balance', 'reserved_balance',
        'total_earned', 'total_withdrawn', 'updated_at'
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
        'id', 'balance', 'amount_display', 'status_badge',
        'method', 'requested_at', 'processed_at'
    ]
    list_filter = ['status', 'method', 'requested_at']
    search_fields = ['balance__owner_id', 'provider_payout_id']
    date_hierarchy = 'requested_at'
    actions = ['approve_payouts', 'reject_payouts']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('balance', 'amount', 'fee', 'net_amount', 'method', 'status')
        }),
        ('الوجهة', {
            'fields': ('destination',)
        }),
        ('المعالجة', {
            'fields': ('processed_at', 'completed_at', 'approved_by', 'approved_at', 'failure_reason')
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
            'on_hold': 'gray',
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
            status='on_hold',
            failure_reason='Rejected by admin'
        )


# =============================================
# سجلات التسوية
# =============================================

@admin.register(ReconciliationRecord)
class ReconciliationRecordAdmin(admin.ModelAdmin):
    """إدارة سجلات التسوية"""

    list_display = [
        'period_start', 'period_end', 'provider', 'is_matched_badge',
        'our_total_amount', 'provider_total_amount', 'amount_difference',
        'reviewed_at'
    ]
    list_filter = ['is_matched', 'provider', 'period_start']
    search_fields = ['provider_report_id']
    date_hierarchy = 'period_start'
    readonly_fields = [
        'our_total_transactions', 'our_total_amount', 'our_total_fees',
        'provider_total_transactions', 'provider_total_amount', 'provider_total_fees',
        'amount_difference', 'transaction_count_difference', 'fee_difference',
    ]
    actions = ['mark_as_reviewed']

    def is_matched_badge(self, obj):
        if obj.is_matched:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">متطابق ✓</span>'
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px;">غير متطابق ✗</span>'
        )
    is_matched_badge.short_description = 'الحالة'

    @admin.action(description='تعليم كمراجع')
    def mark_as_reviewed(self, request, queryset):
        queryset.update(
            reviewed_at=timezone.now(),
            reviewed_by=request.user.id
        )


# =============================================
# قواعد التسعير
# =============================================

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    """إدارة قواعد التسعير"""

    list_display = [
        'name', 'pricing_type', 'base_price', 'unit_price',
        'is_active'
    ]
    list_filter = ['pricing_type', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'pricing_type', 'is_active')
        }),
        ('التسعير', {
            'fields': ('base_price', 'unit_price', 'min_charge')
        }),
        ('الحدود', {
            'fields': ('min_units', 'max_units')
        }),
        ('إعدادات إضافية', {
            'fields': ('tiered_pricing', 'peak_hours_multiplier', 'peak_hours'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeliveryPricingRule)
class DeliveryPricingRuleAdmin(admin.ModelAdmin):
    """إدارة قواعد تسعير التوصيل"""

    list_display = [
        'id', 'pricing_type', 'base_fee', 'per_km_fee',
        'free_delivery_threshold', 'is_active'
    ]
    list_filter = ['pricing_type', 'is_active']
    list_editable = ['is_active']


# =============================================
# الفواتير
# =============================================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """إدارة الفواتير"""

    list_display = [
        'invoice_number', 'seller_type', 'seller_id', 'buyer_type', 'buyer_id',
        'total', 'zatca_status_badge', 'invoice_date'
    ]
    list_filter = ['zatca_status', 'invoice_date', 'seller_type']
    search_fields = ['invoice_number', 'seller_id', 'buyer_id']
    date_hierarchy = 'invoice_date'
    readonly_fields = [
        'invoice_number', 'external_system', 'external_invoice_id',
        'zatca_status', 'zatca_qr_code', 'zatca_invoice_hash'
    ]

    fieldsets = (
        ('معلومات الفاتورة', {
            'fields': ('invoice_number', 'invoice_date', 'due_date', 'order_id')
        }),
        ('البائع', {
            'fields': ('seller_type', 'seller_id')
        }),
        ('المشتري', {
            'fields': ('buyer_type', 'buyer_id')
        }),
        ('المبالغ', {
            'fields': ('subtotal', 'discount', 'vat_rate', 'vat_amount', 'total', 'currency')
        }),
        ('البنود', {
            'fields': ('line_items',),
            'classes': ('collapse',)
        }),
        ('ZATCA', {
            'fields': (
                'zatca_status', 'external_system', 'external_invoice_id',
                'zatca_qr_code', 'zatca_invoice_hash', 'zatca_response'
            ),
            'classes': ('collapse',)
        }),
    )

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
