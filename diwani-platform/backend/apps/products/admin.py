"""
===================================
منصة ديواني - Products Admin
لوحة تحكم المنتجات
===================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    ProductCategory,
    Product,
    ProductImage,
    ProductVariant,
    ProductAddon,
    ProductAddonGroup,
    AddonGroupItem,
    ProductReview,
    FavoriteProduct
)


# ===================================
# Product Category Admin
# ===================================
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'store',
        'parent',
        'products_count',
        'sort_order',
        'is_active'
    ]

    list_filter = ['store', 'is_active', 'parent']
    search_fields = ['name', 'name_en', 'store__name']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['store', 'parent']
    ordering = ['store', 'sort_order']


# ===================================
# Product Image Inline
# ===================================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 10


# ===================================
# Product Variant Inline
# ===================================
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


# ===================================
# Product Addon Inline
# ===================================
class ProductAddonInline(admin.TabularInline):
    model = ProductAddon
    extra = 0


# ===================================
# Product Admin
# ===================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview',
        'name',
        'store',
        'category',
        'price_display',
        'stock_display',
        'status_badge',
        'is_featured',
        'rating_display',
        'created_at'
    ]

    list_filter = [
        'status',
        'store',
        'category',
        'is_active',
        'is_featured',
        'track_inventory',
        'created_at'
    ]

    search_fields = ['name', 'name_en', 'sku', 'barcode', 'store__name']

    prepopulated_fields = {'slug': ('name',)}

    readonly_fields = [
        'id',
        'rating',
        'rating_count',
        'total_sold',
        'view_count',
        'created_at',
        'updated_at'
    ]

    raw_id_fields = ['store', 'category']

    inlines = [ProductImageInline, ProductVariantInline, ProductAddonInline]

    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                'store',
                'category',
                'name',
                'name_en',
                'slug',
                'description',
                'description_en'
            )
        }),
        (_('التعريف'), {
            'fields': ('sku', 'barcode')
        }),
        (_('الصور'), {
            'fields': ('image',)
        }),
        (_('التسعير'), {
            'fields': (
                'price',
                'compare_at_price',
                'cost_price',
                'is_taxable',
                'tax_rate'
            )
        }),
        (_('المخزون'), {
            'fields': (
                'track_inventory',
                'stock_quantity',
                'low_stock_threshold'
            )
        }),
        (_('الشحن'), {
            'fields': ('weight',),
            'classes': ('collapse',)
        }),
        (_('الحالة'), {
            'fields': (
                'status',
                'is_active',
                'is_featured'
            )
        }),
        (_('التوفر'), {
            'fields': (
                'available_from',
                'available_until',
                'min_order_quantity',
                'max_order_quantity',
                'preparation_time'
            )
        }),
        (_('التقييمات والإحصائيات'), {
            'fields': (
                'rating',
                'rating_count',
                'total_sold',
                'view_count'
            ),
            'classes': ('collapse',)
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;"/>',
                obj.image.url
            )
        return '-'
    image_preview.short_description = _('الصورة')

    def price_display(self, obj):
        if obj.is_on_sale:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{}</span> '
                '<span style="color: #dc3545; font-weight: bold;">{}</span>',
                obj.compare_at_price,
                obj.price
            )
        return format_html('<span style="font-weight: bold;">{}</span>', obj.price)
    price_display.short_description = _('السعر')

    def stock_display(self, obj):
        if not obj.track_inventory:
            return format_html('<span style="color: #6c757d;">-</span>')
        if obj.is_low_stock:
            return format_html(
                '<span style="color: #ffc107;">⚠️ {}</span>',
                obj.stock_quantity
            )
        if obj.stock_quantity == 0:
            return format_html('<span style="color: #dc3545;">نفذ</span>')
        return format_html('<span style="color: #28a745;">{}</span>', obj.stock_quantity)
    stock_display.short_description = _('المخزون')

    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'active': '#28a745',
            'out_of_stock': '#dc3545',
            'discontinued': '#343a40',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('الحالة')

    def rating_display(self, obj):
        return format_html('⭐ {:.1f}', obj.rating)
    rating_display.short_description = _('التقييم')

    actions = ['activate_products', 'deactivate_products', 'mark_featured']

    @admin.action(description='تنشيط المنتجات المحددة')
    def activate_products(self, request, queryset):
        queryset.update(status=Product.ProductStatus.ACTIVE, is_active=True)

    @admin.action(description='إلغاء تنشيط المنتجات المحددة')
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='تمييز كمنتجات مميزة')
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)


# ===================================
# Addon Group Item Inline
# ===================================
class AddonGroupItemInline(admin.TabularInline):
    model = AddonGroupItem
    extra = 1


# ===================================
# Product Addon Group Admin
# ===================================
@admin.register(ProductAddonGroup)
class ProductAddonGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'is_required', 'min_selections', 'max_selections']
    list_filter = ['product__store', 'is_required']
    search_fields = ['name', 'product__name']
    raw_id_fields = ['product']
    inlines = [AddonGroupItemInline]


# ===================================
# Product Review Admin
# ===================================
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating_stars', 'is_verified', 'is_visible', 'created_at']
    list_filter = ['rating', 'is_verified', 'is_visible', 'created_at']
    search_fields = ['product__name', 'user__phone_number', 'comment']
    raw_id_fields = ['product', 'user']

    def rating_stars(self, obj):
        return '⭐' * obj.rating
    rating_stars.short_description = _('التقييم')


# ===================================
# Favorite Product Admin
# ===================================
@admin.register(FavoriteProduct)
class FavoriteProductAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__phone_number', 'product__name']
    raw_id_fields = ['user', 'product']
