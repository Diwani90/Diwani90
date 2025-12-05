"""
===================================
منصة ديواني - Stores Schemas
Pydantic schemas for Store APIs
===================================
"""

from typing import Optional, List
from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from ninja import Schema, Field


# ===================================
# Store Category Schemas
# ===================================
class StoreCategoryOutSchema(Schema):
    """Schema for store category output."""
    id: UUID
    name: str
    name_en: str
    slug: str
    icon: Optional[str]
    image: Optional[str]
    description: str
    is_featured: bool
    sort_order: int
    stores_count: int = 0

    @staticmethod
    def resolve_stores_count(obj):
        return obj.stores.filter(status='active').count()


class StoreCategoryListSchema(Schema):
    """Schema for category listing."""
    id: UUID
    name: str
    name_en: str
    slug: str
    icon: Optional[str]
    is_featured: bool


# ===================================
# Store Schemas
# ===================================
class StoreOutSchema(Schema):
    """Schema for store output."""
    id: UUID
    name: str
    name_en: str
    slug: str
    description: str
    store_type: str
    logo: Optional[str]
    cover_image: Optional[str]
    phone_number: str
    whatsapp_number: str
    email: str
    address: str
    city: str
    district: str
    latitude: Optional[float]
    longitude: Optional[float]
    delivery_radius_km: int
    min_order_amount: Decimal
    delivery_fee: Decimal
    free_delivery_threshold: Optional[Decimal]
    estimated_delivery_time: int
    is_open: bool
    is_open_24h: bool
    is_featured: bool
    is_verified: bool
    rating: Decimal
    rating_count: int
    total_orders: int
    category: Optional[StoreCategoryListSchema]
    created_at: datetime

    @staticmethod
    def resolve_latitude(obj):
        if obj.location:
            return obj.location.y
        return None

    @staticmethod
    def resolve_longitude(obj):
        if obj.location:
            return obj.location.x
        return None


class StoreListSchema(Schema):
    """Schema for store listing (minimal data)."""
    id: UUID
    name: str
    name_en: str
    slug: str
    logo: Optional[str]
    city: str
    district: str
    delivery_fee: Decimal
    min_order_amount: Decimal
    estimated_delivery_time: int
    is_open: bool
    is_featured: bool
    is_verified: bool
    rating: Decimal
    rating_count: int
    category_name: str = ''

    @staticmethod
    def resolve_category_name(obj):
        return obj.category.name if obj.category else ''


class StoreCreateSchema(Schema):
    """Schema for creating a store."""
    name: str = Field(..., max_length=200)
    name_en: str = Field('', max_length=200)
    description: str = ''
    description_en: str = ''
    category_id: Optional[UUID] = None
    store_type: str = 'other'
    phone_number: str = Field(..., max_length=15)
    whatsapp_number: str = ''
    email: str = ''
    address: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    district: str = Field(..., max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    delivery_radius_km: int = Field(10, ge=1, le=50)
    min_order_amount: Decimal = Field(Decimal('20.00'), ge=0)
    delivery_fee: Decimal = Field(Decimal('15.00'), ge=0)
    free_delivery_threshold: Optional[Decimal] = None
    estimated_delivery_time: int = Field(30, ge=5)
    is_open_24h: bool = False


class StoreUpdateSchema(Schema):
    """Schema for updating a store."""
    name: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    description_en: Optional[str] = None
    category_id: Optional[UUID] = None
    store_type: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=15)
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    delivery_radius_km: Optional[int] = Field(None, ge=1, le=50)
    min_order_amount: Optional[Decimal] = None
    delivery_fee: Optional[Decimal] = None
    free_delivery_threshold: Optional[Decimal] = None
    estimated_delivery_time: Optional[int] = None
    is_open: Optional[bool] = None
    is_open_24h: Optional[bool] = None


# ===================================
# Working Hours Schemas
# ===================================
class WorkingHoursSchema(Schema):
    """Schema for working hours."""
    weekday: int = Field(..., ge=0, le=6)
    opening_time: time
    closing_time: time
    is_closed: bool = False


class WorkingHoursOutSchema(Schema):
    """Schema for working hours output."""
    id: UUID
    weekday: int
    weekday_name: str
    opening_time: time
    closing_time: time
    is_closed: bool

    @staticmethod
    def resolve_weekday_name(obj):
        days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
        return days[obj.weekday]


# ===================================
# Store Gallery Schemas
# ===================================
class StoreGalleryOutSchema(Schema):
    """Schema for store gallery output."""
    id: UUID
    image: str
    caption: str
    sort_order: int


# ===================================
# Store Review Schemas
# ===================================
class StoreReviewCreateSchema(Schema):
    """Schema for creating a store review."""
    rating: int = Field(..., ge=1, le=5)
    comment: str = ''
    food_rating: Optional[int] = Field(None, ge=1, le=5)
    service_rating: Optional[int] = Field(None, ge=1, le=5)
    delivery_rating: Optional[int] = Field(None, ge=1, le=5)
    order_id: Optional[UUID] = None


class StoreReviewOutSchema(Schema):
    """Schema for store review output."""
    id: UUID
    rating: int
    comment: str
    food_rating: Optional[int]
    service_rating: Optional[int]
    delivery_rating: Optional[int]
    store_response: str
    responded_at: Optional[datetime]
    is_verified: bool
    user_name: str
    created_at: datetime

    @staticmethod
    def resolve_user_name(obj):
        return obj.user.full_name if obj.user else 'مستخدم'


class StoreReviewResponseSchema(Schema):
    """Schema for store response to review."""
    response: str


# ===================================
# Favorite Store Schemas
# ===================================
class FavoriteStoreOutSchema(Schema):
    """Schema for favorite store output."""
    id: UUID
    store: StoreListSchema
    created_at: datetime


# ===================================
# Store Search/Filter Schemas
# ===================================
class StoreFilterSchema(Schema):
    """Schema for filtering stores."""
    category_id: Optional[UUID] = None
    city: Optional[str] = None
    district: Optional[str] = None
    store_type: Optional[str] = None
    is_open: Optional[bool] = None
    is_featured: Optional[bool] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    search: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[int] = Field(None, ge=1, le=50)


# ===================================
# Pagination Schemas
# ===================================
class PaginatedStoreSchema(Schema):
    """Schema for paginated store response."""
    items: List[StoreListSchema]
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
