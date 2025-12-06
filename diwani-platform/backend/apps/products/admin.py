"""
لوحة تحكم المنتجات
===================
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Category,
    Product,
    ProductVariant,
    ProductImage,
    ProductSpecification,
    ProductOption,
    ProductOptionValue,
    ProductReview,
)


# =============================================
# الأقسام
# =============================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """إدارة الأقسام"""

    list_display = [
        'name', 'parent', 'category_type', 'level',
        'is_active', 'is_featured', 'sort_order'
    ]
    list_filter = ['category_type', 'is_active', 'is_featured', 'level']
    search_fields = ['name', 'name_en', 'slug']
    list_editable = ['is_active', 'is_featured', 'sort_order']
    prepopulated_fields = {'slug': ('name_en',)}

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'name_en', 'slug', 'parent', 'description')
        }),
        ('المظهر', {
            'fields': ('icon', 'image', 'color')
        }),
        ('الإعدادات', {
            'fields': ('category_type', 'is_active', 'is_featured', 'sort_order')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )


# =============================================
# المنتجات
# =============================================

class ProductImageInline(admin.TabularInline):
    """صور المنتج"""
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    """متغيرات المنتج"""
    model = ProductVariant
    extra = 0


class ProductSpecificationInline(admin.TabularInline):
    """مواصفات المنتج"""
    model = ProductSpecification
    extra = 1


class ProductOptionInline(admin.TabularInline):
    """خيارات المنتج"""
    model = ProductOption
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """إدارة المنتجات"""

    list_display = [
        'name', 'vendor', 'category', 'product_type', 'pricing_type',
        'price_display', 'status_badge', 'stock_display', 'rating_display'
    ]
    list_filter = [
        'status', 'product_type', 'pricing_type', 'category',
        'is_featured', 'free_delivery', 'created_at'
    ]
    search_fields = ['name', 'name_en', 'sku', 'barcode']
    date_hierarchy = 'created_at'
    readonly_fields = ['views_count', 'orders_count', 'rating', 'reviews_count']

    inlines = [
        ProductImageInline,
        ProductVariantInline,
        ProductSpecificationInline,
        ProductOptionInline,
    ]

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': (
                'vendor', 'category', 'product_type', 'status',
                'name', 'name_en', 'slug', 'sku', 'barcode'
            )
        }),
        ('الوصف', {
            'fields': ('short_description', 'description')
        }),
        ('التسعير', {
            'fields': (
                'pricing_type', 'price', 'compare_at_price', 'cost_price',
                'pricing_config', 'unit', 'min_quantity', 'max_quantity', 'quantity_step'
            )
        }),
        ('المخزون', {
            'fields': (
                'track_inventory', 'stock_quantity', 'low_stock_threshold',
                'allow_backorder'
            ),
            'classes': ('collapse',)
        }),
        ('حسب الطلب', {
            'fields': (
                'lead_time_hours', 'production_capacity_daily', 'requires_scheduling'
            ),
            'classes': ('collapse',)
        }),
        ('التوصيل', {
            'fields': (
                'delivery_option', 'free_delivery', 'delivery_radius_km',
                'delivery_notes'
            ),
            'classes': ('collapse',)
        }),
        ('الأبعاد والوزن', {
            'fields': ('weight', 'length', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('الإحصائيات', {
            'fields': (
                'is_featured', 'is_new', 'views_count', 'orders_count',
                'rating', 'reviews_count'
            )
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'tags'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return obj.get_price_display()
    price_display.short_description = 'السعر'

    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'active': 'green',
            'inactive': 'orange',
            'out_of_stock': 'red',
            'discontinued': 'black',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    def stock_display(self, obj):
        if not obj.track_inventory:
            return '-'
        color = 'green' if obj.stock_quantity > obj.low_stock_threshold else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.stock_quantity
        )
    stock_display.short_description = 'المخزون'

    def rating_display(self, obj):
        stars = '★' * int(obj.rating) + '☆' * (5 - int(obj.rating))
        return f"{stars} ({obj.reviews_count})"
    rating_display.short_description = 'التقييم'


# =============================================
# خيارات المنتج
# =============================================

class ProductOptionValueInline(admin.TabularInline):
    """قيم الخيار"""
    model = ProductOptionValue
    extra = 1


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    """إدارة خيارات المنتجات"""

    list_display = ['name', 'product', 'option_type', 'is_required', 'sort_order']
    list_filter = ['option_type', 'is_required']
    search_fields = ['name', 'product__name']

    inlines = [ProductOptionValueInline]


# =============================================
# التقييمات
# =============================================

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """إدارة التقييمات"""

    list_display = [
        'product', 'user', 'rating_stars', 'is_verified_purchase',
        'is_approved', 'helpful_count', 'created_at'
    ]
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__phone', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['is_verified_purchase', 'helpful_count']

    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)
    rating_stars.short_description = 'التقييم'
