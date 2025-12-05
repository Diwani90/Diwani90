"""
===================================
منصة ديواني - Accounts Admin
لوحة تحكم المستخدمين
===================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import User, OTP, Address, WalletTransaction, DriverProfile, VendorProfile


# ===================================
# User Admin
# ===================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""

    list_display = [
        'phone_number',
        'full_name',
        'user_type_badge',
        'is_verified_icon',
        'wallet_balance',
        'created_at'
    ]

    list_filter = [
        'user_type',
        'is_verified',
        'is_active',
        'is_staff',
        'created_at'
    ]

    search_fields = [
        'phone_number',
        'email',
        'first_name',
        'last_name',
        'national_id'
    ]

    ordering = ['-created_at']

    readonly_fields = [
        'id',
        'referral_code',
        'created_at',
        'updated_at',
        'last_login_at'
    ]

    fieldsets = (
        (_('معلومات الدخول'), {
            'fields': ('phone_number', 'email', 'password')
        }),
        (_('المعلومات الشخصية'), {
            'fields': (
                'first_name',
                'last_name',
                'avatar',
                'gender',
                'date_of_birth',
                'national_id'
            )
        }),
        (_('نوع الحساب'), {
            'fields': ('user_type',)
        }),
        (_('التحقق'), {
            'fields': ('is_verified', 'is_identity_verified')
        }),
        (_('المحفظة'), {
            'fields': ('wallet_balance',)
        }),
        (_('الإحالة'), {
            'fields': ('referral_code', 'referred_by')
        }),
        (_('الإعدادات'), {
            'fields': (
                'language',
                'push_notifications_enabled',
                'sms_notifications_enabled',
                'fcm_token'
            )
        }),
        (_('الصلاحيات'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at', 'last_login_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'first_name',
                'last_name',
                'user_type',
                'password1',
                'password2'
            ),
        }),
    )

    def user_type_badge(self, obj):
        """Display user type as colored badge."""
        colors = {
            'customer': '#28a745',
            'vendor': '#007bff',
            'driver': '#fd7e14',
            'admin': '#dc3545',
        }
        color = colors.get(obj.user_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px;">{}</span>',
            color,
            obj.get_user_type_display()
        )
    user_type_badge.short_description = _('نوع المستخدم')

    def is_verified_icon(self, obj):
        """Display verification status as icon."""
        if obj.is_verified:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    is_verified_icon.short_description = _('تم التحقق')


# ===================================
# OTP Admin
# ===================================
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Admin configuration for OTP model."""

    list_display = [
        'phone_number',
        'purpose',
        'code',
        'is_used',
        'attempts',
        'status_badge',
        'expires_at',
        'created_at'
    ]

    list_filter = ['purpose', 'is_used', 'created_at']

    search_fields = ['phone_number']

    readonly_fields = ['id', 'code', 'created_at']

    ordering = ['-created_at']

    def status_badge(self, obj):
        """Display OTP status as badge."""
        if obj.is_used:
            return format_html(
                '<span style="color: #6c757d;">مستخدم</span>'
            )
        elif obj.is_expired:
            return format_html(
                '<span style="color: #dc3545;">منتهي</span>'
            )
        else:
            return format_html(
                '<span style="color: #28a745;">صالح</span>'
            )
    status_badge.short_description = _('الحالة')


# ===================================
# Address Admin
# ===================================
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin configuration for Address model."""

    list_display = [
        'label',
        'user',
        'address_type',
        'city',
        'district',
        'is_default',
        'created_at'
    ]

    list_filter = ['address_type', 'city', 'is_default']

    search_fields = [
        'user__phone_number',
        'user__first_name',
        'street_address',
        'district'
    ]

    readonly_fields = ['id', 'created_at', 'updated_at']

    raw_id_fields = ['user']


# ===================================
# Wallet Transaction Admin
# ===================================
@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for WalletTransaction model."""

    list_display = [
        'user',
        'transaction_type_badge',
        'amount',
        'status_badge',
        'balance_after',
        'description',
        'created_at'
    ]

    list_filter = ['transaction_type', 'status', 'created_at']

    search_fields = ['user__phone_number', 'user__first_name', 'reference_id']

    readonly_fields = ['id', 'created_at', 'balance_after']

    raw_id_fields = ['user']

    ordering = ['-created_at']

    def transaction_type_badge(self, obj):
        """Display transaction type as badge."""
        if obj.transaction_type == 'credit':
            return format_html(
                '<span style="color: #28a745;">+{}</span>',
                obj.get_transaction_type_display()
            )
        return format_html(
            '<span style="color: #dc3545;">-{}</span>',
            obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = _('نوع العملية')

    def status_badge(self, obj):
        """Display status as badge."""
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'refunded': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('الحالة')


# ===================================
# Driver Profile Admin
# ===================================
@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    """Admin configuration for DriverProfile model."""

    list_display = [
        'user',
        'vehicle_type',
        'plate_number',
        'status_badge',
        'is_online_icon',
        'rating',
        'total_deliveries',
        'created_at'
    ]

    list_filter = ['status', 'vehicle_type', 'is_online', 'is_available']

    search_fields = [
        'user__phone_number',
        'user__first_name',
        'plate_number',
        'vehicle_model'
    ]

    readonly_fields = [
        'id',
        'total_deliveries',
        'total_earnings',
        'rating',
        'rating_count',
        'created_at',
        'updated_at'
    ]

    raw_id_fields = ['user']

    fieldsets = (
        (_('معلومات السائق'), {
            'fields': ('user', 'status')
        }),
        (_('الحالة'), {
            'fields': ('is_online', 'is_available')
        }),
        (_('معلومات المركبة'), {
            'fields': (
                'vehicle_type',
                'vehicle_model',
                'vehicle_year',
                'vehicle_color',
                'plate_number'
            )
        }),
        (_('المستندات'), {
            'fields': (
                'driving_license',
                'vehicle_registration',
                'vehicle_insurance'
            )
        }),
        (_('الموقع'), {
            'fields': ('current_location', 'last_location_update')
        }),
        (_('الإحصائيات'), {
            'fields': (
                'total_deliveries',
                'total_earnings',
                'rating',
                'rating_count'
            )
        }),
        (_('التواريخ'), {
            'fields': ('approved_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'suspended': '#dc3545',
            'rejected': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('الحالة')

    def is_online_icon(self, obj):
        """Display online status as icon."""
        if obj.is_online:
            return format_html('<span style="color: green;">●</span>')
        return format_html('<span style="color: gray;">○</span>')
    is_online_icon.short_description = _('متصل')


# ===================================
# Vendor Profile Admin
# ===================================
@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    """Admin configuration for VendorProfile model."""

    list_display = [
        'business_name',
        'user',
        'commercial_registration',
        'status_badge',
        'commission_rate',
        'total_orders',
        'total_sales',
        'created_at'
    ]

    list_filter = ['status', 'created_at']

    search_fields = [
        'business_name',
        'user__phone_number',
        'commercial_registration'
    ]

    readonly_fields = [
        'id',
        'total_sales',
        'total_orders',
        'created_at',
        'updated_at'
    ]

    raw_id_fields = ['user']

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'suspended': '#dc3545',
            'rejected': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('الحالة')
