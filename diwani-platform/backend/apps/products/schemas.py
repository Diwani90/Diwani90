"""
===================================
منصة ديواني - Products Schemas
Pydantic schemas for Product APIs
===================================
"""

from typing import Optional, List
from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from ninja import Schema, Field


# ===================================
# Product Category Schemas
# ===================================
class ProductCategoryOutSchema(Schema):
    """Schema for product category output."""
    id: UUID
    name: str
    name_en: str
    slug: str
    image: Optional[str]
    description: str
    products_count: int
    sort_order: int
    is_active: bool


class ProductCategoryListSchema(Schema):
    """Schema for category listing."""
    id: UUID
    name: str
    name_en: str
    slug: str
    image: Optional[str]
    products_count: int


class ProductCategoryCreateSchema(Schema):
    """Schema for creating a product category."""
    name: str = Field(..., max_length=100)
    name_en: str = ''
    description: str = ''
    parent_id: Optional[UUID] = None
    sort_order: int = 0


class ProductCategoryUpdateSchema(Schema):
    """Schema for updating a product category."""
    name: Optional[str] = Field(None, max_length=100)
    name_en: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# ===================================
# Product Image Schemas
# ===================================
class ProductImageSchema(Schema):
    """Schema for product image."""
    id: UUID
    image: str
    alt_text: str
    sort_order: int


# ===================================
# Product Variant Schemas
# ===================================
class ProductVariantOutSchema(Schema):
    """Schema for product variant output."""
    id: UUID
    name: str
    name_en: str
    sku: str
    price_adjustment: Decimal
    final_price: Decimal
    stock_quantity: int
    is_active: bool


class ProductVariantCreateSchema(Schema):
    """Schema for creating a variant."""
    name: str = Field(..., max_length=100)
    name_en: str = ''
    sku: str = ''
    price_adjustment: Decimal = Decimal('0')
    stock_quantity: int = 0


class ProductVariantUpdateSchema(Schema):
    """Schema for updating a variant."""
    name: Optional[str] = Field(None, max_length=100)
    name_en: Optional[str] = None
    sku: Optional[str] = None
    price_adjustment: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None


# ===================================
# Product Addon Schemas
# ===================================
class ProductAddonOutSchema(Schema):
    """Schema for product addon output."""
    id: UUID
    name: str
    name_en: str
    price: Decimal
    is_active: bool
    is_required: bool
    max_quantity: int


class ProductAddonCreateSchema(Schema):
    """Schema for creating an addon."""
    name: str = Field(..., max_length=100)
    name_en: str = ''
    price: Decimal = Decimal('0')
    is_required: bool = False
    max_quantity: int = 5


# ===================================
# Product Addon Group Schemas
# ===================================
class AddonGroupItemOutSchema(Schema):
    """Schema for addon group item output."""
    id: UUID
    name: str
    name_en: str
    price: Decimal
    is_default: bool
    is_active: bool


class AddonGroupItemCreateSchema(Schema):
    """Schema for creating addon group item."""
    name: str = Field(..., max_length=100)
    name_en: str = ''
    price: Decimal = Decimal('0')
    is_default: bool = False


class ProductAddonGroupOutSchema(Schema):
    """Schema for addon group output."""
    id: UUID
    name: str
    name_en: str
    is_required: bool
    min_selections: int
    max_selections: int
    items: List[AddonGroupItemOutSchema]


class ProductAddonGroupCreateSchema(Schema):
    """Schema for creating addon group."""
    name: str = Field(..., max_length=100)
    name_en: str = ''
    is_required: bool = False
    min_selections: int = 0
    max_selections: int = 1
    items: List[AddonGroupItemCreateSchema] = []


# ===================================
# Product Schemas
# ===================================
class ProductOutSchema(Schema):
    """Schema for product output (full details)."""
    id: UUID
    name: str
    name_en: str
    slug: str
    description: str
    description_en: str
    sku: str
    barcode: str
    image: Optional[str]
    images: List[ProductImageSchema]
    price: Decimal
    compare_at_price: Optional[Decimal]
    is_on_sale: bool
    discount_percentage: int
    final_price: Decimal
    is_taxable: bool
    tax_rate: Decimal
    track_inventory: bool
    stock_quantity: int
    is_in_stock: bool
    is_low_stock: bool
    weight: Optional[Decimal]
    status: str
    is_active: bool
    is_featured: bool
    available_from: Optional[time]
    available_until: Optional[time]
    min_order_quantity: int
    max_order_quantity: Optional[int]
    preparation_time: Optional[int]
    rating: Decimal
    rating_count: int
    total_sold: int
    view_count: int
    store_id: UUID
    store_name: str
    category: Optional[ProductCategoryListSchema]
    variants: List[ProductVariantOutSchema]
    addons: List[ProductAddonOutSchema]
    addon_groups: List[ProductAddonGroupOutSchema]
    created_at: datetime

    @staticmethod
    def resolve_store_name(obj):
        return obj.store.name if obj.store else ''

    @staticmethod
    def resolve_images(obj):
        return [ProductImageSchema.from_orm(img) for img in obj.images.all()]

    @staticmethod
    def resolve_variants(obj):
        return [ProductVariantOutSchema.from_orm(v) for v in obj.variants.filter(is_active=True)]

    @staticmethod
    def resolve_addons(obj):
        return [ProductAddonOutSchema.from_orm(a) for a in obj.addons.filter(is_active=True)]

    @staticmethod
    def resolve_addon_groups(obj):
        return [ProductAddonGroupOutSchema.from_orm(g) for g in obj.addon_groups.all()]


class ProductListSchema(Schema):
    """Schema for product listing (minimal data)."""
    id: UUID
    name: str
    name_en: str
    slug: str
    image: Optional[str]
    price: Decimal
    compare_at_price: Optional[Decimal]
    is_on_sale: bool
    discount_percentage: int
    is_in_stock: bool
    is_featured: bool
    rating: Decimal
    rating_count: int
    store_id: UUID
    store_name: str
    category_name: str = ''

    @staticmethod
    def resolve_store_name(obj):
        return obj.store.name if obj.store else ''

    @staticmethod
    def resolve_category_name(obj):
        return obj.category.name if obj.category else ''


class ProductCreateSchema(Schema):
    """Schema for creating a product."""
    name: str = Field(..., max_length=200)
    name_en: str = ''
    description: str = ''
    description_en: str = ''
    category_id: Optional[UUID] = None
    sku: str = ''
    barcode: str = ''
    price: Decimal = Field(..., gt=0)
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    is_taxable: bool = True
    tax_rate: Decimal = Decimal('15.00')
    track_inventory: bool = True
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    weight: Optional[Decimal] = None
    is_active: bool = True
    is_featured: bool = False
    available_from: Optional[time] = None
    available_until: Optional[time] = None
    min_order_quantity: int = 1
    max_order_quantity: Optional[int] = None
    preparation_time: Optional[int] = None
    meta_title: str = ''
    meta_description: str = ''


class ProductUpdateSchema(Schema):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    category_id: Optional[UUID] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    is_taxable: Optional[bool] = None
    tax_rate: Optional[Decimal] = None
    track_inventory: Optional[bool] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    weight: Optional[Decimal] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    available_from: Optional[time] = None
    available_until: Optional[time] = None
    min_order_quantity: Optional[int] = None
    max_order_quantity: Optional[int] = None
    preparation_time: Optional[int] = None


# ===================================
# Product Review Schemas
# ===================================
class ProductReviewCreateSchema(Schema):
    """Schema for creating a product review."""
    rating: int = Field(..., ge=1, le=5)
    comment: str = ''


class ProductReviewOutSchema(Schema):
    """Schema for product review output."""
    id: UUID
    rating: int
    comment: str
    is_verified: bool
    user_name: str
    created_at: datetime

    @staticmethod
    def resolve_user_name(obj):
        return obj.user.full_name if obj.user else 'مستخدم'


# ===================================
# Favorite Product Schemas
# ===================================
class FavoriteProductOutSchema(Schema):
    """Schema for favorite product output."""
    id: UUID
    product: ProductListSchema
    created_at: datetime


# ===================================
# Pagination Schemas
# ===================================
class PaginatedProductSchema(Schema):
    """Schema for paginated product response."""
    items: List[ProductListSchema]
    total: int
    page: int
    page_size: int
    pages: int


# ===================================
# Common Response Schemas
# ===================================
class MessageSchema(Schema):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorSchema(Schema):
    """Error response schema."""
    message: str
    code: Optional[str] = None
