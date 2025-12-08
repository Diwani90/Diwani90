"""
Schemas للمتاجر
===============

Django Ninja Schemas للـ API
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ninja import Schema, Field


# =============================================
# المتاجر
# =============================================

class StoreListSchema(Schema):
    """Schema لقائمة المتاجر"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    short_description: Optional[str] = None
    store_type: str
    logo: Optional[str] = None
    city: str
    rating: float
    reviews_count: int
    products_count: int
    is_featured: bool
    is_verified: bool
    is_open: bool
    offers_free_delivery: bool
    min_order_amount: float

    @staticmethod
    def resolve_logo(obj):
        return obj.logo.url if obj.logo else None

    @staticmethod
    def resolve_is_verified(obj):
        return obj.verification_status == 'verified'

    @staticmethod
    def resolve_is_open(obj):
        return obj.is_open


class NearbyStoreSchema(StoreListSchema):
    """Schema للمتاجر القريبة"""
    distance_km: Optional[float] = None


class StoreServiceAreaSchema(Schema):
    """Schema لمنطقة الخدمة"""
    id: UUID
    name: str
    city: str
    districts: List[str]
    delivery_fee: float
    min_order: float


class StoreDetailSchema(Schema):
    """Schema لتفاصيل المتجر"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    store_type: str

    logo: Optional[str] = None
    cover_image: Optional[str] = None

    phone: str
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    address: str
    city: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    delivery_radius_km: int
    offers_free_delivery: bool
    free_delivery_threshold: Optional[float] = None
    offers_pickup: bool
    min_order_amount: float

    working_hours: Dict[str, Any]
    is_24_hours: bool
    is_open: bool

    rating: float
    reviews_count: int
    products_count: int
    orders_count: int

    is_featured: bool
    is_verified: bool
    verification_status: str

    service_areas: List[StoreServiceAreaSchema] = []

    created_at: datetime

    @staticmethod
    def resolve_logo(obj):
        return obj.logo.url if obj.logo else None

    @staticmethod
    def resolve_cover_image(obj):
        return obj.cover_image.url if obj.cover_image else None

    @staticmethod
    def resolve_latitude(obj):
        return obj.location.y if obj.location else None

    @staticmethod
    def resolve_longitude(obj):
        return obj.location.x if obj.location else None

    @staticmethod
    def resolve_is_verified(obj):
        return obj.verification_status == 'verified'

    @staticmethod
    def resolve_is_open(obj):
        return obj.is_open


class StoreSchema(Schema):
    """Schema كامل للمتجر"""
    id: UUID
    name: str
    name_en: Optional[str] = None
    slug: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    store_type: str

    logo: Optional[str] = None
    cover_image: Optional[str] = None

    cr_number: Optional[str] = None
    vat_number: Optional[str] = None
    license_number: Optional[str] = None

    phone: str
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    address: str
    city: str
    district: Optional[str] = None
    postal_code: Optional[str] = None

    delivery_radius_km: int
    delivery_zones: List[str] = []
    offers_free_delivery: bool
    free_delivery_threshold: Optional[float] = None
    offers_pickup: bool
    min_order_amount: float

    working_hours: Dict[str, Any]
    is_24_hours: bool

    tap_account_id: Optional[str] = None
    tap_account_status: str
    bank_name: Optional[str] = None
    bank_iban: Optional[str] = None

    status: str
    verification_status: str

    rating: float
    reviews_count: int
    products_count: int
    orders_count: int
    total_sales: float

    is_featured: bool

    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_logo(obj):
        return obj.logo.url if obj.logo else None

    @staticmethod
    def resolve_cover_image(obj):
        return obj.cover_image.url if obj.cover_image else None


# =============================================
# إنشاء وتحديث المتاجر
# =============================================

class StoreCreateSchema(Schema):
    """Schema لإنشاء متجر"""
    store_type: str = 'supplier'
    name: str
    name_en: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    phone: str
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    address: str
    city: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cr_number: Optional[str] = None
    vat_number: Optional[str] = None
    min_order_amount: Optional[float] = None
    delivery_radius_km: Optional[int] = None
    offers_free_delivery: bool = False
    free_delivery_threshold: Optional[float] = None


class StoreUpdateSchema(Schema):
    """Schema لتحديث متجر"""
    name: Optional[str] = None
    name_en: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    delivery_radius_km: Optional[int] = None
    offers_free_delivery: Optional[bool] = None
    free_delivery_threshold: Optional[float] = None
    offers_pickup: Optional[bool] = None
    min_order_amount: Optional[float] = None
    working_hours: Optional[Dict[str, Any]] = None
    is_24_hours: Optional[bool] = None


# =============================================
# الفلترة
# =============================================

class StoreFilterSchema(Schema):
    """Schema لفلترة المتاجر"""
    search: Optional[str] = None
    store_type: Optional[str] = None
    city: Optional[str] = None
    min_rating: Optional[float] = None
    free_delivery: Optional[bool] = None
    verified_only: Optional[bool] = None
    open_now: Optional[bool] = None
    sort_by: str = 'rating'  # rating, newest, popular, nearest


# =============================================
# التقييمات
# =============================================

class UserMiniSchema(Schema):
    """Schema مختصر للمستخدم"""
    id: UUID
    name: str
    avatar: Optional[str] = None


class StoreReviewSchema(Schema):
    """Schema لتقييم المتجر"""
    id: UUID
    user: UserMiniSchema
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    quality_rating: Optional[int] = None
    service_rating: Optional[int] = None
    is_verified_purchase: bool
    store_reply: Optional[str] = None
    replied_at: Optional[datetime] = None
    created_at: datetime


class StoreReviewCreateSchema(Schema):
    """Schema لإنشاء تقييم"""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None
    delivery_rating: Optional[int] = Field(None, ge=1, le=5)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    service_rating: Optional[int] = Field(None, ge=1, le=5)


# =============================================
# المستندات
# =============================================

class StoreDocumentSchema(Schema):
    """Schema لمستند المتجر"""
    id: UUID
    document_type: str
    name: str
    file_url: str
    expires_at: Optional[datetime] = None
    is_verified: bool
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    @staticmethod
    def resolve_file_url(obj):
        return obj.file.url if obj.file else None


# =============================================
# الإحصائيات
# =============================================

class StoreStatsSchema(Schema):
    """Schema لإحصائيات المتجر"""
    store_id: UUID
    rating: float
    reviews_count: int
    products: Dict[str, int]
    orders: Dict[str, int]
    sales: Dict[str, float]
    verification_status: str


# =============================================
# عام
# =============================================

class MessageSchema(Schema):
    """رسالة عامة"""
    message: str
    error: Optional[str] = None
