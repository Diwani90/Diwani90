"""
Schemas للمنتجات
================

Django Ninja Schemas للـ API
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ninja import Schema, Field


# =============================================
# الأقسام
# =============================================

class CategorySchema(Schema):
    """Schema للقسم"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    color: str
    category_type: str
    level: int
    is_featured: bool
    products_count: int = 0

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else None

    @staticmethod
    def resolve_products_count(obj):
        return getattr(obj, 'products_count', 0)


class CategoryChildSchema(Schema):
    """Schema للقسم الفرعي"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    icon: Optional[str] = None


class CategoryTreeSchema(Schema):
    """Schema لشجرة الأقسام"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    icon: Optional[str] = None
    image: Optional[str] = None
    children: List['CategoryTreeSchema'] = []

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else None

    @staticmethod
    def resolve_children(obj):
        return obj.children.filter(is_active=True).order_by('sort_order')


# =============================================
# المنتجات
# =============================================

class VendorMiniSchema(Schema):
    """Schema مختصر للمتجر"""
    id: UUID
    name: str
    slug: str
    rating: float
    is_verified: bool = False

    @staticmethod
    def resolve_is_verified(obj):
        return obj.verification_status == 'verified'


class ProductImageSchema(Schema):
    """Schema لصورة المنتج"""
    id: UUID
    url: str
    alt_text: Optional[str] = None
    is_primary: bool

    @staticmethod
    def resolve_url(obj):
        return obj.image.url if obj.image else None


class ProductVariantSchema(Schema):
    """Schema لمتغير المنتج"""
    id: UUID
    name: str
    sku: Optional[str] = None
    options: Dict[str, Any]
    price: Optional[float] = None
    stock_quantity: float
    image: Optional[str] = None
    is_active: bool

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else None


class ProductSpecificationSchema(Schema):
    """Schema لمواصفة المنتج"""
    name: str
    value: str
    unit: Optional[str] = None


class ProductOptionValueSchema(Schema):
    """Schema لقيمة خيار"""
    id: UUID
    value: str
    value_en: Optional[str] = None
    price_adjustment: float
    is_default: bool


class ProductOptionSchema(Schema):
    """Schema لخيار المنتج"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    option_type: str
    is_required: bool
    values: List[ProductOptionValueSchema]


class ProductListSchema(Schema):
    """Schema لقائمة المنتجات"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    short_description: Optional[str] = None
    product_type: str
    pricing_type: str
    price: float
    compare_at_price: Optional[float] = None
    unit: str
    rating: float
    reviews_count: int
    is_featured: bool
    is_new: bool
    free_delivery: bool
    primary_image: Optional[str] = None
    discount_percentage: Optional[int] = None
    vendor: VendorMiniSchema
    category_name: str

    @staticmethod
    def resolve_primary_image(obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url
        first_image = obj.images.first()
        return first_image.image.url if first_image else None

    @staticmethod
    def resolve_category_name(obj):
        return obj.category.name if obj.category else ''


class ProductDetailSchema(Schema):
    """Schema لتفاصيل المنتج"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    sku: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None

    product_type: str
    pricing_type: str
    price: float
    compare_at_price: Optional[float] = None
    price_display: str
    unit: str

    min_quantity: float
    max_quantity: Optional[float] = None
    quantity_step: float

    track_inventory: bool
    stock_quantity: float
    is_available: bool
    allow_backorder: bool

    lead_time_hours: Optional[int] = None
    requires_scheduling: bool

    delivery_option: str
    free_delivery: bool
    delivery_radius_km: Optional[int] = None
    delivery_notes: Optional[str] = None

    weight: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

    rating: float
    reviews_count: int
    orders_count: int
    views_count: int
    is_featured: bool
    is_new: bool
    discount_percentage: Optional[int] = None

    images: List[ProductImageSchema]
    variants: List[ProductVariantSchema]
    specifications: List[ProductSpecificationSchema]
    options: List[ProductOptionSchema]

    vendor: VendorMiniSchema
    category: CategorySchema

    created_at: datetime

    @staticmethod
    def resolve_price_display(obj):
        return obj.get_price_display()

    @staticmethod
    def resolve_is_available(obj):
        return obj.is_available

    @staticmethod
    def resolve_discount_percentage(obj):
        return obj.discount_percentage


class ProductSchema(Schema):
    """Schema كامل للمنتج"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    sku: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    product_type: str
    pricing_type: str
    pricing_config: Dict[str, Any] = {}
    price: float
    compare_at_price: Optional[float] = None
    cost_price: Optional[float] = None
    unit: str
    min_quantity: float
    max_quantity: Optional[float] = None
    quantity_step: float
    track_inventory: bool
    stock_quantity: float
    low_stock_threshold: float
    allow_backorder: bool
    lead_time_hours: Optional[int] = None
    production_capacity_daily: Optional[float] = None
    requires_scheduling: bool
    delivery_option: str
    free_delivery: bool
    delivery_radius_km: Optional[int] = None
    delivery_notes: Optional[str] = None
    weight: Optional[float] = None
    status: str
    is_featured: bool
    is_new: bool
    views_count: int
    orders_count: int
    rating: float
    reviews_count: int
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime


# =============================================
# إنشاء وتحديث المنتجات
# =============================================

class ProductCreateSchema(Schema):
    """Schema لإنشاء منتج"""
    vendor_id: UUID
    category_id: UUID
    product_type: str = 'stock'
    name: str
    name_en: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    pricing_type: str = 'fixed'
    pricing_config: Optional[Dict[str, Any]] = None
    price: float
    compare_at_price: Optional[float] = None
    unit: str = 'piece'
    min_quantity: float = 1
    max_quantity: Optional[float] = None
    track_inventory: bool = True
    stock_quantity: float = 0
    lead_time_hours: Optional[int] = None
    delivery_option: str = 'both'
    free_delivery: bool = False


class ProductUpdateSchema(Schema):
    """Schema لتحديث منتج"""
    name: Optional[str] = None
    name_en: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    pricing_type: Optional[str] = None
    pricing_config: Optional[Dict[str, Any]] = None
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    unit: Optional[str] = None
    min_quantity: Optional[float] = None
    max_quantity: Optional[float] = None
    track_inventory: Optional[bool] = None
    stock_quantity: Optional[float] = None
    lead_time_hours: Optional[int] = None
    delivery_option: Optional[str] = None
    free_delivery: Optional[bool] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


# =============================================
# الفلترة
# =============================================

class ProductFilterSchema(Schema):
    """Schema لفلترة المنتجات"""
    search: Optional[str] = None
    category_id: Optional[UUID] = None
    vendor_id: Optional[UUID] = None
    product_type: Optional[str] = None
    pricing_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    free_delivery: Optional[bool] = None
    in_stock: Optional[bool] = None
    sort_by: str = 'newest'  # newest, price_low, price_high, rating, popular


# =============================================
# حساب السعر
# =============================================

class PriceCalculationRequest(Schema):
    """طلب حساب السعر"""
    quantity: float
    selected_options: Optional[Dict[str, UUID]] = None
    context: Optional[Dict[str, Any]] = None


class PriceCalculationResponse(Schema):
    """استجابة حساب السعر"""
    product_id: UUID
    quantity: float
    unit_price: float
    item_total: float
    options_adjustment: float
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    breakdown: Dict[str, Any]
    pricing_type: str


# =============================================
# التقييمات
# =============================================

class UserMiniSchema(Schema):
    """Schema مختصر للمستخدم"""
    id: UUID
    name: str
    avatar: Optional[str] = None


class ProductReviewSchema(Schema):
    """Schema للتقييم"""
    id: UUID
    user: UserMiniSchema
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    images: List[str] = []
    is_verified_purchase: bool
    vendor_reply: Optional[str] = None
    vendor_replied_at: Optional[datetime] = None
    helpful_count: int
    created_at: datetime


class ProductReviewCreateSchema(Schema):
    """Schema لإنشاء تقييم"""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None


# =============================================
# عام
# =============================================

class MessageSchema(Schema):
    """رسالة عامة"""
    message: str
    image_id: Optional[str] = None
