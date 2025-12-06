"""
===================================
منصة ديواني - Search Services
خدمات البحث المتقدم
===================================

يوفر:
- بحث متقدم بالمنتجات
- بحث جغرافي بالمتاجر
- اقتراحات ذكية (Autocomplete)
- بحث متعدد (Multi-search)
- فلترة متقدمة (Faceted Search)
- بحث ضبابي (Fuzzy Search)
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from elasticsearch_dsl import (
    Search, Q, A,
    connections, MultiSearch
)
from elasticsearch_dsl.query import (
    Bool, MultiMatch, Match, Term, Terms, Range,
    GeoDistance, Nested, FunctionScore, ScriptScore
)
from elasticsearch_dsl.aggs import (
    Terms as TermsAgg, Range as RangeAgg,
    Nested as NestedAgg, Avg, Sum, Max, Min,
    GeoDistance as GeoDistanceAgg
)

from django.conf import settings
from django.core.cache import cache

from .documents import (
    ProductDocument, StoreDocument,
    CategoryDocument, VendorDocument,
    setup_elasticsearch_connection
)

logger = logging.getLogger(__name__)


# ===================================
# Enums & Constants
# ===================================
class SortOption(str, Enum):
    """خيارات الترتيب"""
    RELEVANCE = 'relevance'
    PRICE_ASC = 'price_asc'
    PRICE_DESC = 'price_desc'
    RATING = 'rating'
    NEWEST = 'newest'
    POPULARITY = 'popularity'
    BESTSELLER = 'bestseller'
    DISTANCE = 'distance'
    NAME_ASC = 'name_asc'
    NAME_DESC = 'name_desc'


class SearchScope(str, Enum):
    """نطاق البحث"""
    ALL = 'all'
    PRODUCTS = 'products'
    STORES = 'stores'
    CATEGORIES = 'categories'
    VENDORS = 'vendors'


# ===================================
# Data Classes
# ===================================
@dataclass
class SearchFilters:
    """فلاتر البحث"""
    category_ids: List[int] = field(default_factory=list)
    store_ids: List[int] = field(default_factory=list)
    vendor_ids: List[int] = field(default_factory=list)
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    rating_min: Optional[float] = None
    in_stock: Optional[bool] = None
    has_discount: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_new: Optional[bool] = None
    brands: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, List[str]] = field(default_factory=dict)
    city: Optional[str] = None
    region: Optional[str] = None


@dataclass
class GeoLocation:
    """الموقع الجغرافي"""
    latitude: float
    longitude: float
    radius_km: float = 50.0


@dataclass
class SearchRequest:
    """طلب البحث"""
    query: str = ''
    scope: SearchScope = SearchScope.ALL
    filters: SearchFilters = field(default_factory=SearchFilters)
    sort: SortOption = SortOption.RELEVANCE
    page: int = 1
    page_size: int = 20
    location: Optional[GeoLocation] = None
    include_facets: bool = True
    include_suggestions: bool = True
    highlight: bool = True
    fuzzy: bool = True
    min_score: float = 0.1


@dataclass
class SearchHit:
    """نتيجة بحث واحدة"""
    id: int
    type: str
    score: float
    source: Dict[str, Any]
    highlight: Dict[str, List[str]] = field(default_factory=dict)
    distance_km: Optional[float] = None


@dataclass
class Facet:
    """فاسيت (فلتر) واحد"""
    key: str
    doc_count: int
    label: str = ''


@dataclass
class FacetGroup:
    """مجموعة فاسيتات"""
    name: str
    label: str
    buckets: List[Facet] = field(default_factory=list)


@dataclass
class SearchResponse:
    """استجابة البحث"""
    hits: List[SearchHit] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    facets: List[FacetGroup] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    took_ms: int = 0
    query: str = ''


# ===================================
# Search Service Base
# ===================================
class BaseSearchService:
    """الخدمة الأساسية للبحث"""

    def __init__(self):
        setup_elasticsearch_connection()

    def _build_highlight(self, fields: List[str]) -> dict:
        """بناء إعدادات التمييز"""
        return {
            'pre_tags': ['<mark>'],
            'post_tags': ['</mark>'],
            'fields': {
                field: {
                    'number_of_fragments': 3,
                    'fragment_size': 150
                }
                for field in fields
            }
        }

    def _parse_hits(self, response, hit_type: str) -> Tuple[List[SearchHit], int]:
        """تحليل نتائج البحث"""
        hits = []
        for hit in response:
            search_hit = SearchHit(
                id=hit.meta.id,
                type=hit_type,
                score=hit.meta.score or 0,
                source=hit.to_dict(),
                highlight=dict(hit.meta.highlight) if hasattr(hit.meta, 'highlight') else {}
            )

            # المسافة إذا كانت متوفرة
            if hasattr(hit.meta, 'sort') and hit.meta.sort:
                for sort_value in hit.meta.sort:
                    if isinstance(sort_value, float) and sort_value < 1000000:
                        search_hit.distance_km = round(sort_value, 2)
                        break

            hits.append(search_hit)

        total = response.hits.total.value if hasattr(response.hits.total, 'value') else response.hits.total
        return hits, total


# ===================================
# Product Search Service
# ===================================
class ProductSearchService(BaseSearchService):
    """خدمة البحث في المنتجات"""

    def search(self, request: SearchRequest) -> SearchResponse:
        """
        البحث المتقدم في المنتجات
        """
        cache_key = self._get_cache_key(request)
        cached = cache.get(cache_key)
        if cached:
            return cached

        search = ProductDocument.search()

        # بناء الاستعلام الرئيسي
        if request.query:
            search = self._build_query(search, request)
        else:
            search = search.query('match_all')

        # تطبيق الفلاتر
        search = self._apply_filters(search, request.filters)

        # الموقع الجغرافي
        if request.location:
            search = self._apply_geo_filter(search, request.location)

        # الترتيب
        search = self._apply_sorting(search, request.sort, request.location)

        # الفاسيتات
        if request.include_facets:
            search = self._add_facets(search)

        # التمييز
        if request.highlight:
            search = search.highlight_options(**self._build_highlight([
                'name', 'name_en', 'description', 'brand', 'tags'
            ]))
            search = search.highlight('name', 'name_en', 'description', 'brand')

        # الصفحات
        start = (request.page - 1) * request.page_size
        search = search[start:start + request.page_size]

        # الحد الأدنى للنقاط
        if request.min_score and request.query:
            search = search.min_score(request.min_score)

        # تنفيذ البحث
        try:
            response = search.execute()
        except Exception as e:
            logger.error(f"Elasticsearch error: {e}")
            return SearchResponse(query=request.query)

        # تحليل النتائج
        hits, total = self._parse_hits(response, 'product')

        # بناء الاستجابة
        result = SearchResponse(
            hits=hits,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total + request.page_size - 1) // request.page_size,
            took_ms=response.took,
            query=request.query
        )

        # الفاسيتات
        if request.include_facets and hasattr(response, 'aggregations'):
            result.facets = self._parse_facets(response.aggregations)

        # الاقتراحات
        if request.include_suggestions and request.query:
            result.suggestions = self._get_suggestions(request.query)

        # تخزين مؤقت
        cache.set(cache_key, result, timeout=300)

        return result

    def _build_query(self, search: Search, request: SearchRequest) -> Search:
        """بناء استعلام البحث المتقدم"""
        query = request.query

        # البحث المتعدد
        multi_match = MultiMatch(
            query=query,
            fields=[
                'name^5',           # اسم المنتج (أعلى أولوية)
                'name.autocomplete^4',
                'name.synonyms^3',
                'name_en^3',
                'description^2',
                'brand^2',
                'tags^2',
                'category.name^2',
                'search_text',
                'sku^4',            # رقم المنتج
            ],
            type='best_fields',
            operator='or',
            minimum_should_match='70%',
            fuzziness='AUTO' if request.fuzzy else '0',
            prefix_length=2,
            max_expansions=50,
            tie_breaker=0.3
        )

        # استخدام Function Score لتحسين الترتيب
        function_score = FunctionScore(
            query=multi_match,
            functions=[
                # المنتجات المميزة
                {
                    'filter': {'term': {'is_featured': True}},
                    'weight': 1.5
                },
                # المنتجات الأكثر مبيعاً
                {
                    'filter': {'term': {'is_bestseller': True}},
                    'weight': 1.3
                },
                # التقييم العالي
                {
                    'filter': {'range': {'rating': {'gte': 4.0}}},
                    'weight': 1.2
                },
                # المنتجات المتوفرة
                {
                    'filter': {'term': {'in_stock': True}},
                    'weight': 1.1
                },
                # نقاط الشعبية
                {
                    'field_value_factor': {
                        'field': 'popularity_score',
                        'factor': 0.1,
                        'modifier': 'log1p',
                        'missing': 1
                    }
                },
                # حداثة المنتج
                {
                    'gauss': {
                        'created_at': {
                            'scale': '30d',
                            'decay': 0.5
                        }
                    },
                    'weight': 1.1
                }
            ],
            score_mode='sum',
            boost_mode='multiply'
        )

        return search.query(function_score)

    def _apply_filters(self, search: Search, filters: SearchFilters) -> Search:
        """تطبيق الفلاتر"""
        must_filters = []

        # فلتر التصنيف
        if filters.category_ids:
            must_filters.append(Terms(category_ids=filters.category_ids))

        # فلتر المتجر
        if filters.store_ids:
            must_filters.append(Terms(**{'store.id': filters.store_ids}))

        # فلتر المورد
        if filters.vendor_ids:
            must_filters.append(Terms(**{'vendor.id': filters.vendor_ids}))

        # نطاق السعر
        if filters.price_min is not None or filters.price_max is not None:
            price_range = {}
            if filters.price_min is not None:
                price_range['gte'] = filters.price_min
            if filters.price_max is not None:
                price_range['lte'] = filters.price_max
            must_filters.append(Range(price=price_range))

        # التقييم
        if filters.rating_min is not None:
            must_filters.append(Range(rating={'gte': filters.rating_min}))

        # التوفر
        if filters.in_stock is not None:
            must_filters.append(Term(in_stock=filters.in_stock))

        # الخصم
        if filters.has_discount is not None:
            must_filters.append(Term(has_discount=filters.has_discount))

        # المميز
        if filters.is_featured is not None:
            must_filters.append(Term(is_featured=filters.is_featured))

        # الجديد
        if filters.is_new is not None:
            must_filters.append(Term(is_new=filters.is_new))

        # البراند
        if filters.brands:
            must_filters.append(Terms(**{'brand.keyword': filters.brands}))

        # التاجات
        if filters.tags:
            must_filters.append(Terms(tags=filters.tags))

        # المدينة
        if filters.city:
            must_filters.append(Match(**{'location.city': filters.city}))

        # المنطقة
        if filters.region:
            must_filters.append(Match(**{'location.region': filters.region}))

        # الخصائص الديناميكية
        for attr_key, attr_values in filters.attributes.items():
            must_filters.append(Terms(**{f'attributes.{attr_key}': attr_values}))

        # فلتر المنتجات النشطة دائماً
        must_filters.append(Term(is_active=True))

        if must_filters:
            search = search.filter('bool', must=must_filters)

        return search

    def _apply_geo_filter(self, search: Search, location: GeoLocation) -> Search:
        """تطبيق فلتر الموقع الجغرافي"""
        return search.filter(
            'geo_distance',
            distance=f'{location.radius_km}km',
            **{'location.coordinates': {
                'lat': location.latitude,
                'lon': location.longitude
            }}
        )

    def _apply_sorting(
        self,
        search: Search,
        sort: SortOption,
        location: Optional[GeoLocation] = None
    ) -> Search:
        """تطبيق الترتيب"""
        sort_options = {
            SortOption.RELEVANCE: ['_score', '-popularity_score'],
            SortOption.PRICE_ASC: ['price', '_score'],
            SortOption.PRICE_DESC: ['-price', '_score'],
            SortOption.RATING: ['-rating', '-reviews_count', '_score'],
            SortOption.NEWEST: ['-created_at', '_score'],
            SortOption.POPULARITY: ['-popularity_score', '-sales_count', '_score'],
            SortOption.BESTSELLER: ['-sales_count', '-popularity_score', '_score'],
            SortOption.NAME_ASC: ['name.keyword', '_score'],
            SortOption.NAME_DESC: ['-name.keyword', '_score'],
        }

        if sort == SortOption.DISTANCE and location:
            search = search.sort({
                '_geo_distance': {
                    'location.coordinates': {
                        'lat': location.latitude,
                        'lon': location.longitude
                    },
                    'order': 'asc',
                    'unit': 'km'
                }
            }, '_score')
        else:
            search = search.sort(*sort_options.get(sort, ['_score']))

        return search

    def _add_facets(self, search: Search) -> Search:
        """إضافة الفاسيتات"""
        # التصنيفات
        search.aggs.bucket('categories', 'terms', field='category.name.keyword', size=20)

        # البراندات
        search.aggs.bucket('brands', 'terms', field='brand.keyword', size=20)

        # نطاقات الأسعار
        search.aggs.bucket('price_ranges', 'range', field='price', ranges=[
            {'key': '0-50', 'from': 0, 'to': 50},
            {'key': '50-100', 'from': 50, 'to': 100},
            {'key': '100-500', 'from': 100, 'to': 500},
            {'key': '500-1000', 'from': 500, 'to': 1000},
            {'key': '1000+', 'from': 1000},
        ])

        # التقييمات
        search.aggs.bucket('ratings', 'range', field='rating', ranges=[
            {'key': '4+', 'from': 4},
            {'key': '3+', 'from': 3, 'to': 4},
            {'key': '2+', 'from': 2, 'to': 3},
            {'key': '1+', 'from': 1, 'to': 2},
        ])

        # المتاجر
        search.aggs.bucket('stores', 'terms', field='store.name.keyword', size=20)

        # التوفر
        search.aggs.bucket('availability', 'terms', field='stock_status')

        # الخصومات
        search.aggs.bucket('has_discount', 'terms', field='has_discount')

        # إحصائيات السعر
        search.aggs.metric('price_stats', 'stats', field='price')

        return search

    def _parse_facets(self, aggregations) -> List[FacetGroup]:
        """تحليل الفاسيتات"""
        facets = []

        facet_labels = {
            'categories': 'التصنيفات',
            'brands': 'العلامات التجارية',
            'price_ranges': 'نطاق السعر',
            'ratings': 'التقييم',
            'stores': 'المتاجر',
            'availability': 'التوفر',
            'has_discount': 'الخصومات'
        }

        for name, label in facet_labels.items():
            if hasattr(aggregations, name):
                agg = getattr(aggregations, name)
                buckets = [
                    Facet(
                        key=str(bucket.key),
                        doc_count=bucket.doc_count,
                        label=str(bucket.key)
                    )
                    for bucket in agg.buckets
                    if bucket.doc_count > 0
                ]
                if buckets:
                    facets.append(FacetGroup(name=name, label=label, buckets=buckets))

        return facets

    def _get_suggestions(self, query: str, size: int = 5) -> List[str]:
        """الحصول على اقتراحات"""
        search = ProductDocument.search()
        search = search.suggest(
            'product_suggest',
            query,
            completion={
                'field': 'suggest',
                'size': size,
                'skip_duplicates': True,
                'fuzzy': {
                    'fuzziness': 'AUTO'
                }
            }
        )

        try:
            response = search.execute()
            suggestions = []
            if hasattr(response, 'suggest') and response.suggest.product_suggest:
                for option in response.suggest.product_suggest[0].options:
                    suggestions.append(option.text)
            return suggestions
        except Exception as e:
            logger.error(f"Suggestion error: {e}")
            return []

    def _get_cache_key(self, request: SearchRequest) -> str:
        """إنشاء مفتاح التخزين المؤقت"""
        import hashlib
        import json
        key_data = {
            'q': request.query,
            's': request.scope.value,
            'sort': request.sort.value,
            'p': request.page,
            'ps': request.page_size,
            'f': request.filters.__dict__
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"search:product:{hashlib.md5(key_str.encode()).hexdigest()}"


# ===================================
# Store Search Service
# ===================================
class StoreSearchService(BaseSearchService):
    """خدمة البحث في المتاجر"""

    def search(self, request: SearchRequest) -> SearchResponse:
        """البحث في المتاجر"""
        search = StoreDocument.search()

        if request.query:
            search = search.query(
                MultiMatch(
                    query=request.query,
                    fields=[
                        'name^5',
                        'name.autocomplete^4',
                        'name_en^3',
                        'description^2',
                        'category.name^2',
                        'city^2',
                        'district'
                    ],
                    type='best_fields',
                    fuzziness='AUTO' if request.fuzzy else '0'
                )
            )
        else:
            search = search.query('match_all')

        # فلتر النشط
        search = search.filter('term', is_active=True)

        # فلتر المدينة
        if request.filters.city:
            search = search.filter('match', city=request.filters.city)

        # فلتر التقييم
        if request.filters.rating_min:
            search = search.filter('range', rating={'gte': request.filters.rating_min})

        # الموقع الجغرافي
        if request.location:
            search = search.filter(
                'geo_distance',
                distance=f'{request.location.radius_km}km',
                location={
                    'lat': request.location.latitude,
                    'lon': request.location.longitude
                }
            )

            # الترتيب بالمسافة
            if request.sort == SortOption.DISTANCE:
                search = search.sort({
                    '_geo_distance': {
                        'location': {
                            'lat': request.location.latitude,
                            'lon': request.location.longitude
                        },
                        'order': 'asc',
                        'unit': 'km'
                    }
                })

        # الترتيب
        if request.sort == SortOption.RATING:
            search = search.sort('-rating', '-reviews_count')
        elif request.sort == SortOption.POPULARITY:
            search = search.sort('-popularity_score')
        elif request.sort == SortOption.NEWEST:
            search = search.sort('-created_at')
        elif request.sort != SortOption.DISTANCE:
            search = search.sort('_score', '-popularity_score')

        # التمييز
        if request.highlight:
            search = search.highlight('name', 'description')

        # الفاسيتات
        if request.include_facets:
            search.aggs.bucket('cities', 'terms', field='city.keyword', size=20)
            search.aggs.bucket('categories', 'terms', field='category.name.keyword', size=20)
            search.aggs.bucket('ratings', 'range', field='rating', ranges=[
                {'key': '4+', 'from': 4},
                {'key': '3+', 'from': 3, 'to': 4},
            ])

        # الصفحات
        start = (request.page - 1) * request.page_size
        search = search[start:start + request.page_size]

        try:
            response = search.execute()
        except Exception as e:
            logger.error(f"Store search error: {e}")
            return SearchResponse(query=request.query)

        hits, total = self._parse_hits(response, 'store')

        result = SearchResponse(
            hits=hits,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total + request.page_size - 1) // request.page_size,
            took_ms=response.took,
            query=request.query
        )

        if request.include_facets and hasattr(response, 'aggregations'):
            result.facets = self._parse_store_facets(response.aggregations)

        return result

    def _parse_store_facets(self, aggregations) -> List[FacetGroup]:
        """تحليل فاسيتات المتاجر"""
        facets = []

        if hasattr(aggregations, 'cities'):
            buckets = [
                Facet(key=b.key, doc_count=b.doc_count)
                for b in aggregations.cities.buckets
            ]
            facets.append(FacetGroup(name='cities', label='المدن', buckets=buckets))

        if hasattr(aggregations, 'categories'):
            buckets = [
                Facet(key=b.key, doc_count=b.doc_count)
                for b in aggregations.categories.buckets
            ]
            facets.append(FacetGroup(name='categories', label='التصنيفات', buckets=buckets))

        return facets

    def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50,
        limit: int = 20
    ) -> List[SearchHit]:
        """البحث عن المتاجر القريبة"""
        search = StoreDocument.search()
        search = search.filter('term', is_active=True)
        search = search.filter(
            'geo_distance',
            distance=f'{radius_km}km',
            location={'lat': latitude, 'lon': longitude}
        )
        search = search.sort({
            '_geo_distance': {
                'location': {'lat': latitude, 'lon': longitude},
                'order': 'asc',
                'unit': 'km'
            }
        })
        search = search[:limit]

        try:
            response = search.execute()
            hits, _ = self._parse_hits(response, 'store')
            return hits
        except Exception as e:
            logger.error(f"Nearby stores error: {e}")
            return []


# ===================================
# Autocomplete Service
# ===================================
class AutocompleteService(BaseSearchService):
    """خدمة الإكمال التلقائي"""

    def suggest(
        self,
        query: str,
        scope: SearchScope = SearchScope.ALL,
        limit: int = 10,
        context: Optional[Dict] = None
    ) -> Dict[str, List[Dict]]:
        """
        الحصول على اقتراحات الإكمال التلقائي
        """
        results = {
            'products': [],
            'stores': [],
            'categories': []
        }

        if not query or len(query) < 2:
            return results

        # البحث في المنتجات
        if scope in [SearchScope.ALL, SearchScope.PRODUCTS]:
            results['products'] = self._suggest_products(query, limit, context)

        # البحث في المتاجر
        if scope in [SearchScope.ALL, SearchScope.STORES]:
            results['stores'] = self._suggest_stores(query, limit)

        # البحث في التصنيفات
        if scope in [SearchScope.ALL, SearchScope.CATEGORIES]:
            results['categories'] = self._suggest_categories(query, limit)

        return results

    def _suggest_products(
        self,
        query: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """اقتراحات المنتجات"""
        search = ProductDocument.search()

        # استخدام completion suggest
        completion_context = {}
        if context:
            if 'category' in context:
                completion_context['category'] = [context['category']]
            if 'store' in context:
                completion_context['store'] = [context['store']]

        search = search.suggest(
            'products',
            query,
            completion={
                'field': 'suggest',
                'size': limit,
                'skip_duplicates': True,
                'fuzzy': {'fuzziness': 'AUTO'},
                'contexts': completion_context if completion_context else None
            }
        )

        # بحث إضافي بالـ prefix
        search = search.query(
            Bool(
                should=[
                    Match(**{'name.autocomplete': {'query': query, 'boost': 3}}),
                    Match(**{'name': {'query': query, 'boost': 2}}),
                    Match(**{'sku': {'query': query, 'boost': 4}}),
                ],
                minimum_should_match=1
            )
        )
        search = search.filter('term', is_active=True)
        search = search[:limit]

        try:
            response = search.execute()
            suggestions = []

            # من completion suggest
            if hasattr(response, 'suggest') and response.suggest.products:
                for option in response.suggest.products[0].options:
                    suggestions.append({
                        'text': option.text,
                        'id': option._source.id if hasattr(option, '_source') else None,
                        'type': 'suggest'
                    })

            # من البحث العادي
            for hit in response:
                if not any(s['text'] == hit.name for s in suggestions):
                    suggestions.append({
                        'text': hit.name,
                        'id': hit.meta.id,
                        'type': 'search',
                        'image': hit.primary_image if hasattr(hit, 'primary_image') else None,
                        'price': hit.price if hasattr(hit, 'price') else None
                    })

            return suggestions[:limit]
        except Exception as e:
            logger.error(f"Product suggest error: {e}")
            return []

    def _suggest_stores(self, query: str, limit: int) -> List[Dict]:
        """اقتراحات المتاجر"""
        search = StoreDocument.search()
        search = search.query(
            Bool(
                should=[
                    Match(**{'name.autocomplete': {'query': query, 'boost': 3}}),
                    Match(**{'name': {'query': query, 'boost': 2}}),
                ],
                minimum_should_match=1
            )
        )
        search = search.filter('term', is_active=True)
        search = search[:limit]

        try:
            response = search.execute()
            return [
                {
                    'text': hit.name,
                    'id': hit.meta.id,
                    'logo': hit.logo if hasattr(hit, 'logo') else None,
                    'rating': hit.rating if hasattr(hit, 'rating') else None
                }
                for hit in response
            ]
        except Exception as e:
            logger.error(f"Store suggest error: {e}")
            return []

    def _suggest_categories(self, query: str, limit: int) -> List[Dict]:
        """اقتراحات التصنيفات"""
        search = CategoryDocument.search()
        search = search.query(
            Bool(
                should=[
                    Match(**{'name.autocomplete': {'query': query, 'boost': 3}}),
                    Match(**{'name': {'query': query, 'boost': 2}}),
                ],
                minimum_should_match=1
            )
        )
        search = search.filter('term', is_active=True)
        search = search[:limit]

        try:
            response = search.execute()
            return [
                {
                    'text': hit.name,
                    'id': hit.meta.id,
                    'slug': hit.slug if hasattr(hit, 'slug') else None,
                    'icon': hit.icon if hasattr(hit, 'icon') else None
                }
                for hit in response
            ]
        except Exception as e:
            logger.error(f"Category suggest error: {e}")
            return []


# ===================================
# Multi Search Service
# ===================================
class MultiSearchService(BaseSearchService):
    """خدمة البحث المتعدد (عبر جميع الكيانات)"""

    def search_all(self, query: str, limit_per_type: int = 5) -> Dict[str, Any]:
        """
        البحث في جميع الكيانات في استعلام واحد
        """
        ms = MultiSearch()

        # بحث المنتجات
        product_search = ProductDocument.search()
        product_search = product_search.query(
            MultiMatch(query=query, fields=['name^3', 'name_en^2', 'description'])
        )
        product_search = product_search.filter('term', is_active=True)
        product_search = product_search[:limit_per_type]
        ms = ms.add(product_search)

        # بحث المتاجر
        store_search = StoreDocument.search()
        store_search = store_search.query(
            MultiMatch(query=query, fields=['name^3', 'name_en^2', 'description'])
        )
        store_search = store_search.filter('term', is_active=True)
        store_search = store_search[:limit_per_type]
        ms = ms.add(store_search)

        # بحث التصنيفات
        category_search = CategoryDocument.search()
        category_search = category_search.query(
            MultiMatch(query=query, fields=['name^3', 'name_en^2'])
        )
        category_search = category_search[:limit_per_type]
        ms = ms.add(category_search)

        try:
            responses = ms.execute()

            return {
                'products': [
                    {'id': h.meta.id, 'name': h.name, 'price': getattr(h, 'price', None)}
                    for h in responses[0]
                ],
                'stores': [
                    {'id': h.meta.id, 'name': h.name, 'rating': getattr(h, 'rating', None)}
                    for h in responses[1]
                ],
                'categories': [
                    {'id': h.meta.id, 'name': h.name, 'slug': getattr(h, 'slug', None)}
                    for h in responses[2]
                ],
                'total': {
                    'products': responses[0].hits.total.value,
                    'stores': responses[1].hits.total.value,
                    'categories': responses[2].hits.total.value
                }
            }
        except Exception as e:
            logger.error(f"Multi search error: {e}")
            return {'products': [], 'stores': [], 'categories': [], 'total': {}}


# ===================================
# Search Facade
# ===================================
class SearchFacade:
    """واجهة موحدة لجميع خدمات البحث"""

    def __init__(self):
        self.product_service = ProductSearchService()
        self.store_service = StoreSearchService()
        self.autocomplete_service = AutocompleteService()
        self.multi_search_service = MultiSearchService()

    def search(self, request: SearchRequest) -> SearchResponse:
        """البحث حسب النطاق"""
        if request.scope == SearchScope.PRODUCTS:
            return self.product_service.search(request)
        elif request.scope == SearchScope.STORES:
            return self.store_service.search(request)
        else:
            return self.product_service.search(request)

    def autocomplete(self, query: str, **kwargs) -> Dict:
        """الإكمال التلقائي"""
        return self.autocomplete_service.suggest(query, **kwargs)

    def search_all(self, query: str, **kwargs) -> Dict:
        """البحث في الكل"""
        return self.multi_search_service.search_all(query, **kwargs)

    def nearby_stores(self, lat: float, lon: float, **kwargs) -> List[SearchHit]:
        """المتاجر القريبة"""
        return self.store_service.find_nearby(lat, lon, **kwargs)


# ===================================
# Singleton Instance
# ===================================
search_facade = SearchFacade()
