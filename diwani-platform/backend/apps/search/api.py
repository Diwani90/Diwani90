"""
===================================
منصة ديواني - Search API
واجهات برمجة البحث المتقدم
===================================

Endpoints:
- GET  /search                 - بحث شامل
- GET  /search/products        - بحث المنتجات
- GET  /search/stores          - بحث المتاجر
- GET  /search/autocomplete    - الإكمال التلقائي
- GET  /search/suggestions     - الاقتراحات
- GET  /search/nearby-stores   - المتاجر القريبة
- GET  /search/trending        - الأكثر بحثاً
- POST /search/advanced        - بحث متقدم
"""

import logging
from typing import Optional, List

from ninja import Router, Query
from ninja.errors import HttpError
from django.http import HttpRequest
from django.core.cache import cache
from django.conf import settings

from .schemas import (
    SearchRequestSchema,
    AutocompleteRequestSchema,
    NearbyStoresRequestSchema,
    ProductSearchResponseSchema,
    StoreSearchResponseSchema,
    AutocompleteResponseSchema,
    MultiSearchResultSchema,
    NearbyStoresResponseSchema,
    SearchErrorSchema,
    SortOption,
    SearchScope,
    SearchMetaSchema,
    ProductHitSchema,
    StoreSearchHitSchema,
    FacetGroupSchema,
    FacetBucketSchema,
    NearbyStoreSchema,
    AutocompleteSuggestionSchema
)
from .services import (
    SearchRequest,
    SearchFilters,
    GeoLocation,
    SortOption as ServiceSortOption,
    SearchScope as ServiceSearchScope,
    search_facade
)

logger = logging.getLogger(__name__)

router = Router(tags=['البحث المتقدم'])


# ===================================
# Helper Functions
# ===================================
def convert_sort_option(sort: SortOption) -> ServiceSortOption:
    """تحويل خيار الترتيب"""
    mapping = {
        SortOption.relevance: ServiceSortOption.RELEVANCE,
        SortOption.price_asc: ServiceSortOption.PRICE_ASC,
        SortOption.price_desc: ServiceSortOption.PRICE_DESC,
        SortOption.rating: ServiceSortOption.RATING,
        SortOption.newest: ServiceSortOption.NEWEST,
        SortOption.popularity: ServiceSortOption.POPULARITY,
        SortOption.bestseller: ServiceSortOption.BESTSELLER,
        SortOption.distance: ServiceSortOption.DISTANCE,
        SortOption.name_asc: ServiceSortOption.NAME_ASC,
        SortOption.name_desc: ServiceSortOption.NAME_DESC,
    }
    return mapping.get(sort, ServiceSortOption.RELEVANCE)


def convert_scope(scope: SearchScope) -> ServiceSearchScope:
    """تحويل نطاق البحث"""
    mapping = {
        SearchScope.all: ServiceSearchScope.ALL,
        SearchScope.products: ServiceSearchScope.PRODUCTS,
        SearchScope.stores: ServiceSearchScope.STORES,
        SearchScope.categories: ServiceSearchScope.CATEGORIES,
    }
    return mapping.get(scope, ServiceSearchScope.PRODUCTS)


def build_search_request(params: SearchRequestSchema) -> SearchRequest:
    """بناء طلب البحث من المعاملات"""
    filters = SearchFilters(
        category_ids=params.filters.category_ids,
        store_ids=params.filters.store_ids,
        vendor_ids=params.filters.vendor_ids,
        price_min=params.filters.price_min,
        price_max=params.filters.price_max,
        rating_min=params.filters.rating_min,
        in_stock=params.filters.in_stock,
        has_discount=params.filters.has_discount,
        is_featured=params.filters.is_featured,
        is_new=params.filters.is_new,
        brands=params.filters.brands,
        tags=params.filters.tags,
        city=params.filters.city,
        region=params.filters.region,
        attributes=params.filters.attributes
    )

    location = None
    if params.location:
        location = GeoLocation(
            latitude=params.location.latitude,
            longitude=params.location.longitude,
            radius_km=params.location.radius_km
        )

    return SearchRequest(
        query=params.q,
        scope=convert_scope(params.scope),
        filters=filters,
        sort=convert_sort_option(params.sort),
        page=params.page,
        page_size=params.page_size,
        location=location,
        include_facets=params.include_facets,
        include_suggestions=params.include_suggestions,
        highlight=params.highlight,
        fuzzy=params.fuzzy
    )


def format_product_hit(hit) -> ProductHitSchema:
    """تنسيق نتيجة منتج"""
    source = hit.source

    category = None
    if 'category' in source and source['category']:
        category = {
            'id': source['category'].get('id'),
            'name': source['category'].get('name', ''),
            'name_en': source['category'].get('name_en', ''),
            'slug': source['category'].get('slug', '')
        }

    store = None
    if 'store' in source and source['store']:
        store = {
            'id': source['store'].get('id'),
            'name': source['store'].get('name', ''),
            'slug': source['store'].get('slug', ''),
            'logo': source['store'].get('logo'),
            'rating': source['store'].get('rating'),
            'is_verified': source['store'].get('is_verified', False)
        }

    return ProductHitSchema(
        id=hit.id,
        name=source.get('name', ''),
        name_en=source.get('name_en'),
        slug=source.get('slug', ''),
        sku=source.get('sku'),
        description=source.get('description'),
        price=source.get('price', 0),
        original_price=source.get('original_price'),
        discount_percentage=source.get('discount_percentage'),
        has_discount=source.get('has_discount', False),
        in_stock=source.get('in_stock', True),
        stock_status=source.get('stock_status', 'in_stock'),
        rating=source.get('rating'),
        reviews_count=source.get('reviews_count', 0),
        primary_image=source.get('primary_image'),
        category=category,
        store=store,
        is_featured=source.get('is_featured', False),
        is_new=source.get('is_new', False),
        is_bestseller=source.get('is_bestseller', False),
        distance_km=hit.distance_km,
        highlight=hit.highlight
    )


def format_store_hit(hit) -> StoreSearchHitSchema:
    """تنسيق نتيجة متجر"""
    source = hit.source

    return StoreSearchHitSchema(
        id=hit.id,
        name=source.get('name', ''),
        name_en=source.get('name_en'),
        slug=source.get('slug', ''),
        description=source.get('description'),
        logo=source.get('logo'),
        cover_image=source.get('cover_image'),
        rating=source.get('rating'),
        reviews_count=source.get('reviews_count', 0),
        products_count=source.get('products_count', 0),
        city=source.get('city'),
        district=source.get('district'),
        is_verified=source.get('is_verified', False),
        is_featured=source.get('is_featured', False),
        delivery_enabled=source.get('delivery_enabled', True),
        min_order_amount=source.get('min_order_amount'),
        distance_km=hit.distance_km,
        highlight=hit.highlight
    )


def format_facets(facets) -> List[FacetGroupSchema]:
    """تنسيق الفاسيتات"""
    return [
        FacetGroupSchema(
            name=fg.name,
            label=fg.label,
            buckets=[
                FacetBucketSchema(
                    key=b.key,
                    doc_count=b.doc_count,
                    label=b.label or b.key
                )
                for b in fg.buckets
            ]
        )
        for fg in facets
    ]


# ===================================
# Search Endpoints
# ===================================
@router.get(
    '/products',
    response={200: ProductSearchResponseSchema, 500: SearchErrorSchema},
    summary="بحث المنتجات",
    description="بحث متقدم في المنتجات مع دعم الفلاتر والفاسيتات"
)
def search_products(
    request: HttpRequest,
    q: str = Query('', description="نص البحث"),
    category_ids: List[int] = Query([], description="معرفات التصنيفات"),
    store_ids: List[int] = Query([], description="معرفات المتاجر"),
    price_min: Optional[float] = Query(None, description="الحد الأدنى للسعر"),
    price_max: Optional[float] = Query(None, description="الحد الأقصى للسعر"),
    rating_min: Optional[float] = Query(None, description="الحد الأدنى للتقييم"),
    in_stock: Optional[bool] = Query(None, description="متوفر فقط"),
    has_discount: Optional[bool] = Query(None, description="مع خصم فقط"),
    is_featured: Optional[bool] = Query(None, description="مميز فقط"),
    brands: List[str] = Query([], description="العلامات التجارية"),
    city: Optional[str] = Query(None, description="المدينة"),
    sort: SortOption = Query(SortOption.relevance, description="الترتيب"),
    page: int = Query(1, ge=1, description="رقم الصفحة"),
    page_size: int = Query(20, ge=1, le=100, description="حجم الصفحة"),
    lat: Optional[float] = Query(None, description="خط العرض"),
    lon: Optional[float] = Query(None, description="خط الطول"),
    radius_km: float = Query(50, description="نصف القطر (كم)"),
):
    """
    بحث متقدم في المنتجات

    ### الميزات:
    - بحث نصي بالعربي والإنجليزي
    - فلترة متعددة (تصنيف، سعر، تقييم، إلخ)
    - بحث جغرافي (بالقرب من موقع)
    - ترتيب متعدد
    - فاسيتات للفلترة الديناميكية
    - اقتراحات بديلة
    """
    try:
        # بناء الفلاتر
        filters = SearchFilters(
            category_ids=category_ids,
            store_ids=store_ids,
            price_min=price_min,
            price_max=price_max,
            rating_min=rating_min,
            in_stock=in_stock,
            has_discount=has_discount,
            is_featured=is_featured,
            brands=brands,
            city=city
        )

        # الموقع الجغرافي
        location = None
        if lat is not None and lon is not None:
            location = GeoLocation(
                latitude=lat,
                longitude=lon,
                radius_km=radius_km
            )

        # طلب البحث
        search_request = SearchRequest(
            query=q,
            scope=ServiceSearchScope.PRODUCTS,
            filters=filters,
            sort=convert_sort_option(sort),
            page=page,
            page_size=page_size,
            location=location
        )

        # تنفيذ البحث
        result = search_facade.search(search_request)

        # تنسيق النتائج
        return ProductSearchResponseSchema(
            meta=SearchMetaSchema(
                total=result.total,
                page=result.page,
                page_size=result.page_size,
                total_pages=result.total_pages,
                took_ms=result.took_ms,
                query=result.query
            ),
            hits=[format_product_hit(hit) for hit in result.hits],
            facets=format_facets(result.facets),
            suggestions=result.suggestions
        )

    except Exception as e:
        logger.error(f"Product search error: {e}")
        return 500, SearchErrorSchema(
            error="Search failed",
            error_ar="فشل البحث",
            details={"message": str(e)}
        )


@router.get(
    '/stores',
    response={200: StoreSearchResponseSchema, 500: SearchErrorSchema},
    summary="بحث المتاجر",
    description="بحث في المتاجر مع دعم البحث الجغرافي"
)
def search_stores(
    request: HttpRequest,
    q: str = Query('', description="نص البحث"),
    category_id: Optional[int] = Query(None, description="معرف التصنيف"),
    city: Optional[str] = Query(None, description="المدينة"),
    rating_min: Optional[float] = Query(None, description="الحد الأدنى للتقييم"),
    is_verified: Optional[bool] = Query(None, description="موثق فقط"),
    sort: SortOption = Query(SortOption.relevance, description="الترتيب"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lat: Optional[float] = Query(None, description="خط العرض"),
    lon: Optional[float] = Query(None, description="خط الطول"),
    radius_km: float = Query(50, description="نصف القطر (كم)"),
):
    """
    بحث في المتاجر

    ### الميزات:
    - بحث بالاسم والوصف
    - فلترة بالمدينة والتصنيف
    - بحث جغرافي (المتاجر القريبة)
    - ترتيب بالمسافة
    """
    try:
        filters = SearchFilters(
            category_ids=[category_id] if category_id else [],
            city=city,
            rating_min=rating_min
        )

        location = None
        if lat is not None and lon is not None:
            location = GeoLocation(
                latitude=lat,
                longitude=lon,
                radius_km=radius_km
            )

        search_request = SearchRequest(
            query=q,
            scope=ServiceSearchScope.STORES,
            filters=filters,
            sort=convert_sort_option(sort),
            page=page,
            page_size=page_size,
            location=location
        )

        result = search_facade.store_service.search(search_request)

        return StoreSearchResponseSchema(
            meta=SearchMetaSchema(
                total=result.total,
                page=result.page,
                page_size=result.page_size,
                total_pages=result.total_pages,
                took_ms=result.took_ms,
                query=result.query
            ),
            hits=[format_store_hit(hit) for hit in result.hits],
            facets=format_facets(result.facets)
        )

    except Exception as e:
        logger.error(f"Store search error: {e}")
        return 500, SearchErrorSchema(
            error="Search failed",
            error_ar="فشل البحث",
            details={"message": str(e)}
        )


@router.get(
    '/autocomplete',
    response={200: AutocompleteResponseSchema},
    summary="الإكمال التلقائي",
    description="اقتراحات فورية أثناء الكتابة"
)
def autocomplete(
    request: HttpRequest,
    q: str = Query(..., min_length=2, description="نص البحث"),
    scope: SearchScope = Query(SearchScope.all, description="نطاق البحث"),
    limit: int = Query(10, ge=1, le=20, description="عدد النتائج"),
    category: Optional[str] = Query(None, description="تصنيف محدد"),
    store: Optional[str] = Query(None, description="متجر محدد"),
):
    """
    الإكمال التلقائي

    ### الاستخدام:
    يُستخدم في حقل البحث لعرض اقتراحات فورية

    ### الميزات:
    - اقتراحات للمنتجات
    - اقتراحات للمتاجر
    - اقتراحات للتصنيفات
    - يدعم التصفية بالسياق
    """
    try:
        context = {}
        if category:
            context['category'] = category
        if store:
            context['store'] = store

        result = search_facade.autocomplete(
            query=q,
            scope=convert_scope(scope),
            limit=limit,
            context=context if context else None
        )

        return AutocompleteResponseSchema(
            products=[
                AutocompleteSuggestionSchema(**p) for p in result.get('products', [])
            ],
            stores=[
                AutocompleteSuggestionSchema(**s) for s in result.get('stores', [])
            ],
            categories=[
                AutocompleteSuggestionSchema(**c) for c in result.get('categories', [])
            ]
        )

    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        return AutocompleteResponseSchema()


@router.get(
    '/nearby-stores',
    response={200: NearbyStoresResponseSchema, 400: SearchErrorSchema},
    summary="المتاجر القريبة",
    description="البحث عن المتاجر القريبة من موقع محدد"
)
def nearby_stores(
    request: HttpRequest,
    lat: float = Query(..., ge=-90, le=90, description="خط العرض"),
    lon: float = Query(..., ge=-180, le=180, description="خط الطول"),
    radius_km: float = Query(50, ge=1, le=200, description="نصف القطر (كم)"),
    limit: int = Query(20, ge=1, le=50, description="عدد النتائج"),
    category_id: Optional[int] = Query(None, description="تصنيف محدد"),
):
    """
    المتاجر القريبة

    ### الاستخدام:
    للحصول على المتاجر القريبة من موقع العميل

    ### الإرجاع:
    قائمة المتاجر مرتبة بالمسافة مع معلومات المسافة بالكيلومتر
    """
    try:
        hits = search_facade.nearby_stores(
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            limit=limit
        )

        stores = []
        for hit in hits:
            stores.append(NearbyStoreSchema(
                id=hit.id,
                name=hit.source.get('name', ''),
                slug=hit.source.get('slug', ''),
                logo=hit.source.get('logo'),
                rating=hit.source.get('rating'),
                distance_km=hit.distance_km or 0,
                city=hit.source.get('city'),
                is_verified=hit.source.get('is_verified', False),
                products_count=hit.source.get('products_count', 0)
            ))

        return NearbyStoresResponseSchema(
            stores=stores,
            total=len(stores)
        )

    except Exception as e:
        logger.error(f"Nearby stores error: {e}")
        return 400, SearchErrorSchema(
            error="Search failed",
            error_ar="فشل البحث",
            details={"message": str(e)}
        )


@router.get(
    '/multi',
    response={200: MultiSearchResultSchema},
    summary="بحث متعدد",
    description="بحث في جميع الكيانات في استعلام واحد"
)
def multi_search(
    request: HttpRequest,
    q: str = Query(..., min_length=1, description="نص البحث"),
    limit_per_type: int = Query(5, ge=1, le=20, description="عدد النتائج لكل نوع"),
):
    """
    بحث متعدد

    ### الاستخدام:
    للبحث في المنتجات والمتاجر والتصنيفات في استعلام واحد

    ### الفائدة:
    يُستخدم في صفحة البحث الرئيسية لعرض نتائج متنوعة
    """
    try:
        result = search_facade.search_all(
            query=q,
            limit_per_type=limit_per_type
        )

        return MultiSearchResultSchema(
            products=result.get('products', []),
            stores=result.get('stores', []),
            categories=result.get('categories', []),
            total=result.get('total', {})
        )

    except Exception as e:
        logger.error(f"Multi search error: {e}")
        return MultiSearchResultSchema()


@router.post(
    '/advanced',
    response={200: ProductSearchResponseSchema, 500: SearchErrorSchema},
    summary="بحث متقدم (POST)",
    description="بحث متقدم مع فلاتر معقدة عبر POST"
)
def advanced_search(
    request: HttpRequest,
    body: SearchRequestSchema
):
    """
    بحث متقدم (POST)

    ### الاستخدام:
    للبحث مع فلاتر معقدة لا يمكن إرسالها عبر GET

    ### الميزات:
    - فلاتر متعددة القيم
    - خصائص ديناميكية
    - الموقع الجغرافي
    """
    try:
        search_request = build_search_request(body)
        result = search_facade.search(search_request)

        return ProductSearchResponseSchema(
            meta=SearchMetaSchema(
                total=result.total,
                page=result.page,
                page_size=result.page_size,
                total_pages=result.total_pages,
                took_ms=result.took_ms,
                query=result.query
            ),
            hits=[format_product_hit(hit) for hit in result.hits],
            facets=format_facets(result.facets),
            suggestions=result.suggestions
        )

    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return 500, SearchErrorSchema(
            error="Search failed",
            error_ar="فشل البحث",
            details={"message": str(e)}
        )


@router.get(
    '/trending',
    response=List[dict],
    summary="الأكثر بحثاً",
    description="قائمة الكلمات الأكثر بحثاً"
)
def trending_searches(
    request: HttpRequest,
    limit: int = Query(10, ge=1, le=50, description="عدد النتائج"),
):
    """
    الأكثر بحثاً

    ### الاستخدام:
    لعرض الكلمات الأكثر بحثاً في الصفحة الرئيسية
    """
    # يمكن تنفيذ هذا لاحقاً مع تتبع عمليات البحث
    cache_key = f"trending_searches:{limit}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    # بيانات افتراضية للعرض
    trending = [
        {"term": "حديد تسليح", "count": 1520},
        {"term": "اسمنت", "count": 1340},
        {"term": "طوب أحمر", "count": 1180},
        {"term": "بلاط سيراميك", "count": 980},
        {"term": "رمل", "count": 850},
        {"term": "خرسانة جاهزة", "count": 720},
        {"term": "عزل حراري", "count": 650},
        {"term": "دهانات", "count": 580},
        {"term": "مواسير PVC", "count": 490},
        {"term": "أسلاك كهرباء", "count": 420},
    ][:limit]

    cache.set(cache_key, trending, timeout=3600)
    return trending


@router.get(
    '/health',
    response=dict,
    summary="حالة خدمة البحث",
    description="التحقق من صحة اتصال Elasticsearch"
)
def search_health(request: HttpRequest):
    """
    التحقق من صحة خدمة البحث
    """
    try:
        from elasticsearch_dsl import connections
        from .documents import setup_elasticsearch_connection

        setup_elasticsearch_connection()
        es = connections.get_connection()
        health = es.cluster.health()

        return {
            "status": "healthy",
            "elasticsearch": {
                "status": health['status'],
                "cluster_name": health['cluster_name'],
                "number_of_nodes": health['number_of_nodes'],
                "active_shards": health['active_shards']
            }
        }

    except Exception as e:
        logger.error(f"Search health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
