"""
===================================
منصة ديواني - Search Schemas
مخططات البحث (Pydantic)
===================================
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ===================================
# Enums
# ===================================
class SortOption(str, Enum):
    """خيارات الترتيب"""
    relevance = 'relevance'
    price_asc = 'price_asc'
    price_desc = 'price_desc'
    rating = 'rating'
    newest = 'newest'
    popularity = 'popularity'
    bestseller = 'bestseller'
    distance = 'distance'
    name_asc = 'name_asc'
    name_desc = 'name_desc'


class SearchScope(str, Enum):
    """نطاق البحث"""
    all = 'all'
    products = 'products'
    stores = 'stores'
    categories = 'categories'


# ===================================
# Request Schemas
# ===================================
class GeoLocationSchema(BaseModel):
    """الموقع الجغرافي"""
    latitude: float = Field(..., ge=-90, le=90, description="خط العرض")
    longitude: float = Field(..., ge=-180, le=180, description="خط الطول")
    radius_km: float = Field(default=50, ge=1, le=500, description="نصف القطر بالكيلومتر")


class SearchFiltersSchema(BaseModel):
    """فلاتر البحث"""
    category_ids: List[int] = Field(default=[], description="معرفات التصنيفات")
    store_ids: List[int] = Field(default=[], description="معرفات المتاجر")
    vendor_ids: List[int] = Field(default=[], description="معرفات الموردين")
    price_min: Optional[float] = Field(default=None, ge=0, description="الحد الأدنى للسعر")
    price_max: Optional[float] = Field(default=None, ge=0, description="الحد الأقصى للسعر")
    rating_min: Optional[float] = Field(default=None, ge=0, le=5, description="الحد الأدنى للتقييم")
    in_stock: Optional[bool] = Field(default=None, description="متوفر في المخزون")
    has_discount: Optional[bool] = Field(default=None, description="يحتوي على خصم")
    is_featured: Optional[bool] = Field(default=None, description="منتج مميز")
    is_new: Optional[bool] = Field(default=None, description="منتج جديد")
    brands: List[str] = Field(default=[], description="العلامات التجارية")
    tags: List[str] = Field(default=[], description="الوسوم")
    city: Optional[str] = Field(default=None, description="المدينة")
    region: Optional[str] = Field(default=None, description="المنطقة")
    attributes: Dict[str, List[str]] = Field(default={}, description="الخصائص")


class SearchRequestSchema(BaseModel):
    """طلب البحث الرئيسي"""
    q: str = Field(default='', min_length=0, max_length=200, description="نص البحث")
    scope: SearchScope = Field(default=SearchScope.products, description="نطاق البحث")
    filters: SearchFiltersSchema = Field(default_factory=SearchFiltersSchema, description="الفلاتر")
    sort: SortOption = Field(default=SortOption.relevance, description="الترتيب")
    page: int = Field(default=1, ge=1, le=1000, description="رقم الصفحة")
    page_size: int = Field(default=20, ge=1, le=100, description="حجم الصفحة")
    location: Optional[GeoLocationSchema] = Field(default=None, description="الموقع")
    include_facets: bool = Field(default=True, description="تضمين الفاسيتات")
    include_suggestions: bool = Field(default=True, description="تضمين الاقتراحات")
    highlight: bool = Field(default=True, description="تمييز النتائج")
    fuzzy: bool = Field(default=True, description="البحث الضبابي")


class AutocompleteRequestSchema(BaseModel):
    """طلب الإكمال التلقائي"""
    q: str = Field(..., min_length=2, max_length=100, description="نص البحث")
    scope: SearchScope = Field(default=SearchScope.all, description="نطاق البحث")
    limit: int = Field(default=10, ge=1, le=20, description="عدد النتائج")
    category: Optional[str] = Field(default=None, description="تصنيف محدد")
    store: Optional[str] = Field(default=None, description="متجر محدد")


class NearbyStoresRequestSchema(BaseModel):
    """طلب المتاجر القريبة"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=50, ge=1, le=200)
    limit: int = Field(default=20, ge=1, le=50)
    category_id: Optional[int] = Field(default=None, description="تصنيف محدد")


# ===================================
# Response Schemas
# ===================================
class CategoryHitSchema(BaseModel):
    """التصنيف في نتيجة البحث"""
    id: int
    name: str
    name_en: Optional[str] = None
    slug: str


class StoreHitSchema(BaseModel):
    """المتجر في نتيجة البحث"""
    id: int
    name: str
    slug: str
    logo: Optional[str] = None
    rating: Optional[float] = None
    is_verified: bool = False


class ImageSchema(BaseModel):
    """الصورة"""
    url: str
    alt: Optional[str] = None
    is_primary: bool = False


class ProductHitSchema(BaseModel):
    """نتيجة بحث منتج"""
    id: int
    name: str
    name_en: Optional[str] = None
    slug: str
    sku: Optional[str] = None
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    has_discount: bool = False
    in_stock: bool = True
    stock_status: str = 'in_stock'
    rating: Optional[float] = None
    reviews_count: int = 0
    primary_image: Optional[str] = None
    category: Optional[CategoryHitSchema] = None
    store: Optional[StoreHitSchema] = None
    is_featured: bool = False
    is_new: bool = False
    is_bestseller: bool = False
    distance_km: Optional[float] = None
    highlight: Dict[str, List[str]] = Field(default={})

    class Config:
        from_attributes = True


class StoreSearchHitSchema(BaseModel):
    """نتيجة بحث متجر"""
    id: int
    name: str
    name_en: Optional[str] = None
    slug: str
    description: Optional[str] = None
    logo: Optional[str] = None
    cover_image: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: int = 0
    products_count: int = 0
    city: Optional[str] = None
    district: Optional[str] = None
    is_verified: bool = False
    is_featured: bool = False
    delivery_enabled: bool = True
    min_order_amount: Optional[float] = None
    distance_km: Optional[float] = None
    highlight: Dict[str, List[str]] = Field(default={})

    class Config:
        from_attributes = True


class FacetBucketSchema(BaseModel):
    """قيمة فاسيت"""
    key: str
    doc_count: int
    label: str = ''


class FacetGroupSchema(BaseModel):
    """مجموعة فاسيتات"""
    name: str
    label: str
    buckets: List[FacetBucketSchema]


class SearchMetaSchema(BaseModel):
    """معلومات البحث الوصفية"""
    total: int
    page: int
    page_size: int
    total_pages: int
    took_ms: int
    query: str


class ProductSearchResponseSchema(BaseModel):
    """استجابة بحث المنتجات"""
    meta: SearchMetaSchema
    hits: List[ProductHitSchema]
    facets: List[FacetGroupSchema] = []
    suggestions: List[str] = []


class StoreSearchResponseSchema(BaseModel):
    """استجابة بحث المتاجر"""
    meta: SearchMetaSchema
    hits: List[StoreSearchHitSchema]
    facets: List[FacetGroupSchema] = []


class AutocompleteSuggestionSchema(BaseModel):
    """اقتراح إكمال تلقائي"""
    text: str
    id: Optional[int] = None
    type: str = 'suggest'
    image: Optional[str] = None
    price: Optional[float] = None
    logo: Optional[str] = None
    rating: Optional[float] = None
    slug: Optional[str] = None
    icon: Optional[str] = None


class AutocompleteResponseSchema(BaseModel):
    """استجابة الإكمال التلقائي"""
    products: List[AutocompleteSuggestionSchema] = []
    stores: List[AutocompleteSuggestionSchema] = []
    categories: List[AutocompleteSuggestionSchema] = []


class MultiSearchResultSchema(BaseModel):
    """نتيجة البحث المتعدد"""
    products: List[Dict[str, Any]] = []
    stores: List[Dict[str, Any]] = []
    categories: List[Dict[str, Any]] = []
    total: Dict[str, int] = {}


class NearbyStoreSchema(BaseModel):
    """متجر قريب"""
    id: int
    name: str
    slug: str
    logo: Optional[str] = None
    rating: Optional[float] = None
    distance_km: float
    city: Optional[str] = None
    is_verified: bool = False
    products_count: int = 0


class NearbyStoresResponseSchema(BaseModel):
    """استجابة المتاجر القريبة"""
    stores: List[NearbyStoreSchema]
    total: int


# ===================================
# Error Schemas
# ===================================
class SearchErrorSchema(BaseModel):
    """خطأ في البحث"""
    error: str
    error_ar: str
    details: Optional[Dict[str, Any]] = None
