"""
===================================
منصة ديواني - Stores Admin
لوحة تحكم المتاجر
===================================
"""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    StoreCategory,
    Store,
    StoreWorkingHours,
    StoreGallery,
    StoreReview,
    FavoriteStore
)


# ===================================
# Store Category Admin
# ===================================
@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'parent',
        'commission_rate',
        'sort_order',
        'is_active',
        'is_featured',
        'stores_count'
    ]

    list_filter = ['is_active', 'is_featured', 'parent']
    search_fields = ['name', 'name_en']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']

    def stores_count(self, obj):
        return obj.stores.count()
    stores_count.short_description = _('عدد المتاجر')


# ===================================
# Store Working Hours Inline
# ===================================
class StoreWorkingHoursInline(admin.TabularInline):
    model = StoreWorkingHours
    extra = 0
    max_num = 7


# ===================================
# Store Gallery Inline
# ===================================
class StoreGalleryInline(admin.TabularInline):
    model = StoreGallery
    extra = 1
    max_num = 10


# ===================================
# Store Admin
# ===================================
@admin.register(Store)
class StoreAdmin(GISModelAdmin):
    list_display = [
        'name',
        'owner',
        'category',
        'city',
        'status_badge',
        'is_open_icon',
        'rating_display',
        'total_orders',
        'created_at'
    ]

    list_filter = [
        'status',
        'category',
        'store_type',
        'city',
        'is_open',
        'is_featured',
        'is_verified'
    ]

    search_fields = [
        'name',
        'name_en',
        'owner__phone_number',
        'owner__first_name',
        'phone_number'
    ]

    prepopulated_fields = {'slug': ('name',)}

    readonly_fields = [
        'id',
        'rating',
        'rating_count',
        'total_orders',
        'total_sales',
        'created_at',
        'updated_at'
    ]

    raw_id_fields = ['owner', 'category']

    inlines = [StoreWorkingHoursInline, StoreGalleryInline]

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                'owner',
                'name',
                'name_en',
                'slug',
                'description',
                'description_en',
                'category',
                'store_type'
            )
        }),
        (_('الصور'), {
            'fields': ('logo', 'cover_image')
        }),
        (_('التواصل'), {
            'fields': ('phone_number', 'whatsapp_number', 'email')
        }),
        (_('الموقع'), {
            'fields': ('address', 'city', 'district', 'location')
        }),
        (_('إعدادات التوصيل'), {
            'fields': (
                'delivery_radius_km',
                'min_order_amount',
                'delivery_fee',
                'free_delivery_threshold',
                'estimated_delivery_time'
            )
        }),
        (_('ساعات العمل'), {
            'fields': ('is_open_24h',),
            'description': 'استخدم الجدول أدناه لتحديد ساعات العمل التفصيلية'
        }),
        (_('الحالة'), {
            'fields': (
                'status',
                'is_open',
                'is_featured',
                'is_verified'
            )
        }),
        (_('التقييمات والإحصائيات'), {
            'fields': (
                'rating',
                'rating_count',
                'total_orders',
                'total_sales'
            ),
            'classes': ('collapse',)
        }),
        (_('العمولة'), {
            'fields': ('commission_rate',)
        }),
        (_('التواريخ'), {
            'fields': ('approved_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'active': '#28a745',
            'suspended': '#dc3545',
            'closed': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('الحالة')

    def is_open_icon(self, obj):
        if obj.is_open:
            return format_html('<span style="color: green;">●</span>')
        return format_html('<span style="color: red;">●</span>')
    is_open_icon.short_description = _('مفتوح')

    def rating_display(self, obj):
        stars = '⭐' * int(obj.rating)
        return format_html('{} ({:.1f})', stars, obj.rating)
    rating_display.short_description = _('التقييم')

    actions = ['approve_stores', 'suspend_stores', 'activate_stores']

    @admin.action(description='اعتماد المتاجر المحددة')
    def approve_stores(self, request, queryset):
        from django.utils import timezone
        queryset.update(status=Store.StoreStatus.ACTIVE, approved_at=timezone.now())

    @admin.action(description='إيقاف المتاجر المحددة')
    def suspend_stores(self, request, queryset):
        queryset.update(status=Store.StoreStatus.SUSPENDED)

    @admin.action(description='تنشيط المتاجر المحددة')
    def activate_stores(self, request, queryset):
        queryset.update(status=Store.StoreStatus.ACTIVE, is_open=True)


# ===================================
# Store Review Admin
# ===================================
@admin.register(StoreReview)
class StoreReviewAdmin(admin.ModelAdmin):
    list_display = [
        'store',
        'user',
        'rating_stars',
        'is_verified',
        'is_visible',
        'created_at'
    ]

    list_filter = ['rating', 'is_verified', 'is_visible', 'created_at']

    search_fields = [
        'store__name',
        'user__phone_number',
        'comment'
    ]

    readonly_fields = ['id', 'created_at', 'updated_at']

    raw_id_fields = ['store', 'user', 'order']

    def rating_stars(self, obj):
        return '⭐' * obj.rating
    rating_stars.short_description = _('التقييم')


# ===================================
# Favorite Store Admin
# ===================================
@admin.register(FavoriteStore)
class FavoriteStoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'store', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__phone_number', 'store__name']
    raw_id_fields = ['user', 'store']
