"""
===================================
منصة ديواني - Orders Admin
لوحة تحكم الطلبات
===================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    Coupon
)


# ===================================
# Cart Item Inline
# ===================================
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ['product', 'variant']
    readonly_fields = ['total_price']


# ===================================
# Cart Admin
# ===================================
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'store', 'items_count', 'subtotal', 'created_at']
    list_filter = ['store', 'created_at']
    search_fields = ['user__phone_number', 'store__name']
    raw_id_fields = ['user', 'store']
    inlines = [CartItemInline]
    readonly_fields = ['items_count', 'subtotal', 'delivery_fee', 'total']


# ===================================
# Order Item Inline
# ===================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'variant_name', 'quantity', 'unit_price', 'addons_total', 'total_price']
    exclude = ['product', 'variant', 'product_name_en']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ===================================
# Order Status History Inline
# ===================================
class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['status', 'notes', 'changed_by', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ===================================
# Order Admin
# ===================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number',
        'customer_link',
        'store_link',
        'status_badge',
        'payment_badge',
        'total',
        'driver',
        'placed_at'
    ]

    list_filter = [
        'status',
        'payment_status',
        'payment_method',
        'delivery_type',
        'store',
        'placed_at'
    ]

    search_fields = [
        'order_number',
        'customer__phone_number',
        'customer__first_name',
        'store__name',
        'driver__phone_number'
    ]

    raw_id_fields = ['customer', 'store', 'driver', 'delivery_address', 'coupon', 'cancelled_by']

    readonly_fields = [
        'id',
        'order_number',
        'subtotal',
        'total',
        'placed_at',
        'confirmed_at',
        'preparing_at',
        'ready_at',
        'picked_up_at',
        'delivered_at',
        'cancelled_at',
        'created_at',
        'updated_at'
    ]

    inlines = [OrderItemInline, OrderStatusHistoryInline]

    fieldsets = (
        (_('معلومات الطلب'), {
            'fields': ('id', 'order_number', 'customer', 'store')
        }),
        (_('الحالة'), {
            'fields': ('status', 'payment_status', 'payment_method', 'delivery_type')
        }),
        (_('التوصيل'), {
            'fields': (
                'delivery_address',
                'delivery_address_text',
                'driver'
            )
        }),
        (_('التسعير'), {
            'fields': (
                'subtotal',
                'delivery_fee',
                'discount_amount',
                'tax_amount',
                'tip_amount',
                'total',
                'coupon'
            )
        }),
        (_('الملاحظات'), {
            'fields': (
                'customer_notes',
                'store_notes',
                'driver_notes'
            ),
            'classes': ('collapse',)
        }),
        (_('الأوقات المتوقعة'), {
            'fields': (
                'estimated_preparation_time',
                'estimated_delivery_time'
            )
        }),
        (_('التواريخ'), {
            'fields': (
                'placed_at',
                'confirmed_at',
                'preparing_at',
                'ready_at',
                'picked_up_at',
                'delivered_at',
                'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
        (_('الإلغاء'), {
            'fields': (
                'cancellation_reason',
                'cancelled_by'
            ),
            'classes': ('collapse',)
        }),
    )

    def customer_link(self, obj):
        if obj.customer:
            url = reverse('admin:accounts_user_change', args=[obj.customer.id])
            return format_html('<a href="{}">{}</a>', url, obj.customer.full_name)
        return '-'
    customer_link.short_description = _('العميل')

    def store_link(self, obj):
        if obj.store:
            url = reverse('admin:stores_store_change', args=[obj.store.id])
            return format_html('<a href="{}">{}</a>', url, obj.store.name)
        return '-'
    store_link.short_description = _('المتجر')

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'preparing': '#6f42c1',
            'ready': '#20c997',
            'picked_up': '#fd7e14',
            'on_the_way': '#007bff',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
            'refunded': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('الحالة')

    def payment_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'paid': '#28a745',
            'failed': '#dc3545',
            'refunded': '#17a2b8',
            'partially_refunded': '#6c757d',
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_badge.short_description = _('الدفع')

    actions = ['confirm_orders', 'cancel_orders', 'mark_delivered']

    @admin.action(description='تأكيد الطلبات المحددة')
    def confirm_orders(self, request, queryset):
        for order in queryset.filter(status=Order.OrderStatus.PENDING):
            order.confirm()

    @admin.action(description='إلغاء الطلبات المحددة')
    def cancel_orders(self, request, queryset):
        for order in queryset.exclude(status__in=[Order.OrderStatus.DELIVERED, Order.OrderStatus.CANCELLED]):
            order.cancel(reason='إلغاء من لوحة التحكم', cancelled_by=request.user)

    @admin.action(description='تحديد كمكتملة')
    def mark_delivered(self, request, queryset):
        for order in queryset.filter(status=Order.OrderStatus.ON_THE_WAY):
            order.complete()


# ===================================
# Coupon Admin
# ===================================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'discount_display',
        'store',
        'usage_display',
        'is_valid_badge',
        'valid_until'
    ]

    list_filter = ['is_active', 'discount_type', 'store', 'valid_until']

    search_fields = ['code', 'description']

    raw_id_fields = ['store']

    fieldsets = (
        (_('الكود'), {
            'fields': ('code', 'description')
        }),
        (_('الخصم'), {
            'fields': (
                'discount_type',
                'discount_value',
                'min_order_amount',
                'max_discount_amount'
            )
        }),
        (_('القيود'), {
            'fields': ('store',)
        }),
        (_('حدود الاستخدام'), {
            'fields': (
                'max_uses',
                'max_uses_per_user',
                'used_count'
            )
        }),
        (_('الصلاحية'), {
            'fields': (
                'is_active',
                'valid_from',
                'valid_until'
            )
        }),
    )

    def discount_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        return f"{obj.discount_value} ر.س"
    discount_display.short_description = _('الخصم')

    def usage_display(self, obj):
        if obj.max_uses:
            return f"{obj.used_count} / {obj.max_uses}"
        return obj.used_count
    usage_display.short_description = _('الاستخدام')

    def is_valid_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ صالح</span>')
        return format_html('<span style="color: red;">✗ منتهي</span>')
    is_valid_badge.short_description = _('الصلاحية')
