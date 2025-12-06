"""
===================================
منصة ديواني - Elasticsearch Documents
مستندات الفهرسة للبحث المتقدم
===================================

يدعم فهرسة:
- المنتجات (Products)
- المتاجر (Stores)
- التصنيفات (Categories)
- الموردين (Vendors)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from elasticsearch_dsl import (
    Document, Text, Keyword, Integer, Float, Boolean,
    Date, Object, Nested, GeoPoint, Completion,
    InnerDoc, analyzer, token_filter, char_filter,
    Index, connections
)

from django.conf import settings

from .analyzers import ARABIC_INDEX_SETTINGS


# ===================================
# Elasticsearch Connection
# ===================================
def setup_elasticsearch_connection():
    """إعداد الاتصال بـ Elasticsearch"""
    es_config = getattr(settings, 'ELASTICSEARCH_DSL', {})
    connections.create_connection(
        alias='default',
        hosts=es_config.get('hosts', ['http://localhost:9200']),
        timeout=es_config.get('timeout', 30),
        retry_on_timeout=True,
        max_retries=3,
    )


# ===================================
# Inner Documents (للكائنات المتداخلة)
# ===================================
class CategoryInner(InnerDoc):
    """التصنيف المتداخل"""
    id = Integer()
    name = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    name_en = Text(analyzer='standard', fields={'keyword': Keyword()})
    slug = Keyword()
    level = Integer()
    parent_id = Integer()


class ImageInner(InnerDoc):
    """الصورة المتداخلة"""
    url = Keyword()
    alt = Text(analyzer='arabic_analyzer')
    is_primary = Boolean()
    order = Integer()


class VariantInner(InnerDoc):
    """متغير المنتج"""
    id = Integer()
    name = Text(analyzer='arabic_analyzer')
    sku = Keyword()
    price = Float()
    stock = Integer()
    attributes = Object()


class ReviewSummary(InnerDoc):
    """ملخص التقييمات"""
    average_rating = Float()
    total_reviews = Integer()
    rating_distribution = Object()  # {5: 10, 4: 5, ...}


class StoreInner(InnerDoc):
    """المتجر المتداخل"""
    id = Integer()
    name = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    slug = Keyword()
    logo = Keyword()
    rating = Float()
    is_verified = Boolean()


class VendorInner(InnerDoc):
    """المورد المتداخل"""
    id = Integer()
    company_name = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    is_verified = Boolean()
    rating = Float()


class LocationInner(InnerDoc):
    """الموقع المتداخل"""
    city = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    district = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    region = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    coordinates = GeoPoint()


class PriceRange(InnerDoc):
    """نطاق السعر"""
    min_price = Float()
    max_price = Float()
    currency = Keyword()


class WorkingHoursInner(InnerDoc):
    """ساعات العمل"""
    day = Keyword()
    open_time = Keyword()
    close_time = Keyword()
    is_closed = Boolean()


# ===================================
# Product Document
# ===================================
class ProductDocument(Document):
    """
    مستند المنتج للفهرسة في Elasticsearch
    """

    # ===== معرفات =====
    id = Integer()
    sku = Keyword()
    barcode = Keyword()
    slug = Keyword()

    # ===== النصوص الرئيسية (عربي) =====
    name = Text(
        analyzer='arabic_analyzer',
        search_analyzer='arabic_search_analyzer',
        boost=3.0,
        fields={
            'keyword': Keyword(normalizer='arabic_normalizer'),
            'autocomplete': Text(
                analyzer='autocomplete_analyzer',
                search_analyzer='autocomplete_search_analyzer'
            ),
            'synonyms': Text(analyzer='arabic_synonym_analyzer')
        }
    )

    description = Text(
        analyzer='arabic_analyzer',
        search_analyzer='arabic_search_analyzer',
        boost=1.5
    )

    short_description = Text(
        analyzer='arabic_analyzer',
        boost=2.0
    )

    # ===== النصوص (إنجليزي) =====
    name_en = Text(
        analyzer='standard',
        boost=2.0,
        fields={
            'keyword': Keyword(),
            'autocomplete': Text(
                analyzer='autocomplete_analyzer',
                search_analyzer='autocomplete_search_analyzer'
            )
        }
    )

    description_en = Text(analyzer='standard')

    # ===== البحث المجمع =====
    search_text = Text(
        analyzer='arabic_synonym_analyzer',
        boost=1.0
    )  # يجمع: الاسم + الوصف + التصنيف + الكلمات المفتاحية

    # ===== التصنيفات =====
    category = Object(CategoryInner)
    categories_path = Keyword(multi=True)  # مسار التصنيفات الكامل
    category_ids = Integer(multi=True)

    # ===== الأسعار =====
    price = Float()
    original_price = Float()
    discount_percentage = Float()
    price_range = Object(PriceRange)
    has_discount = Boolean()

    # ===== المخزون =====
    stock = Integer()
    in_stock = Boolean()
    stock_status = Keyword()  # in_stock, low_stock, out_of_stock

    # ===== المتجر والمورد =====
    store = Object(StoreInner)
    vendor = Object(VendorInner)

    # ===== الصور =====
    images = Nested(ImageInner)
    primary_image = Keyword()
    images_count = Integer()

    # ===== المتغيرات والإضافات =====
    variants = Nested(VariantInner)
    has_variants = Boolean()
    variants_count = Integer()

    # ===== التقييمات =====
    reviews = Object(ReviewSummary)
    rating = Float()
    reviews_count = Integer()

    # ===== الخصائص =====
    attributes = Object(dynamic=True)  # خصائص ديناميكية
    tags = Keyword(multi=True)
    keywords = Text(analyzer='arabic_analyzer')
    brand = Text(
        analyzer='arabic_analyzer',
        fields={'keyword': Keyword()}
    )

    # ===== الموقع الجغرافي =====
    location = Object(LocationInner)
    delivery_zones = Keyword(multi=True)

    # ===== الحالة والعرض =====
    status = Keyword()
    is_active = Boolean()
    is_featured = Boolean()
    is_new = Boolean()
    is_bestseller = Boolean()

    # ===== الضرائب =====
    tax_rate = Float()
    price_includes_tax = Boolean()

    # ===== الوحدات =====
    unit = Keyword()
    unit_name = Text(analyzer='arabic_analyzer')
    min_order_quantity = Integer()
    max_order_quantity = Integer()

    # ===== الترتيب والشعبية =====
    sort_order = Integer()
    popularity_score = Float()
    sales_count = Integer()
    views_count = Integer()

    # ===== التواريخ =====
    created_at = Date()
    updated_at = Date()
    published_at = Date()

    # ===== Autocomplete Suggest =====
    suggest = Completion(
        analyzer='autocomplete_analyzer',
        search_analyzer='autocomplete_search_analyzer',
        preserve_separators=True,
        contexts=[
            {'name': 'category', 'type': 'category'},
            {'name': 'store', 'type': 'category'},
        ]
    )

    class Index:
        name = 'diwani_products'
        settings = ARABIC_INDEX_SETTINGS

    class Django:
        model = 'products.Product'
        related_models = ['products.ProductImage', 'products.ProductVariant']

    @classmethod
    def from_django_model(cls, product) -> 'ProductDocument':
        """
        تحويل نموذج Django إلى مستند Elasticsearch
        """
        doc = cls(meta={'id': product.id})

        # المعرفات
        doc.id = product.id
        doc.sku = product.sku
        doc.barcode = getattr(product, 'barcode', None)
        doc.slug = product.slug

        # النصوص
        doc.name = product.name
        doc.name_en = getattr(product, 'name_en', '')
        doc.description = product.description or ''
        doc.description_en = getattr(product, 'description_en', '')
        doc.short_description = getattr(product, 'short_description', '')

        # نص البحث المجمع
        search_parts = [
            product.name,
            getattr(product, 'name_en', ''),
            product.description or '',
            product.category.name if product.category else '',
        ]
        if hasattr(product, 'tags'):
            search_parts.extend(product.tags or [])
        doc.search_text = ' '.join(filter(None, search_parts))

        # التصنيف
        if product.category:
            doc.category = {
                'id': product.category.id,
                'name': product.category.name,
                'name_en': getattr(product.category, 'name_en', ''),
                'slug': product.category.slug,
                'level': getattr(product.category, 'level', 0),
                'parent_id': product.category.parent_id if product.category.parent else None
            }
            # مسار التصنيفات
            doc.categories_path = _get_category_path(product.category)
            doc.category_ids = _get_category_ids(product.category)

        # الأسعار
        doc.price = float(product.price)
        doc.original_price = float(getattr(product, 'original_price', product.price))
        if doc.original_price > doc.price:
            doc.discount_percentage = round(
                (1 - doc.price / doc.original_price) * 100, 2
            )
            doc.has_discount = True
        else:
            doc.discount_percentage = 0
            doc.has_discount = False

        # المخزون
        doc.stock = product.stock
        doc.in_stock = product.stock > 0
        if product.stock == 0:
            doc.stock_status = 'out_of_stock'
        elif product.stock < 10:
            doc.stock_status = 'low_stock'
        else:
            doc.stock_status = 'in_stock'

        # المتجر
        if product.store:
            doc.store = {
                'id': product.store.id,
                'name': product.store.name,
                'slug': product.store.slug,
                'logo': product.store.logo.url if product.store.logo else None,
                'rating': float(product.store.rating or 0),
                'is_verified': getattr(product.store, 'is_verified', False)
            }

            # الموقع من المتجر
            if hasattr(product.store, 'location') and product.store.location:
                doc.location = {
                    'city': getattr(product.store, 'city', ''),
                    'district': getattr(product.store, 'district', ''),
                    'region': getattr(product.store, 'region', ''),
                    'coordinates': {
                        'lat': product.store.location.y,
                        'lon': product.store.location.x
                    } if product.store.location else None
                }

        # الصور
        images = list(product.images.all().order_by('order'))
        doc.images = [
            {
                'url': img.image.url if img.image else None,
                'alt': img.alt_text or product.name,
                'is_primary': img.is_primary,
                'order': img.order
            }
            for img in images
        ]
        doc.images_count = len(images)
        primary_img = next((img for img in images if img.is_primary), None)
        if primary_img:
            doc.primary_image = primary_img.image.url if primary_img.image else None
        elif images:
            doc.primary_image = images[0].image.url if images[0].image else None

        # المتغيرات
        if hasattr(product, 'variants'):
            variants = list(product.variants.all())
            doc.variants = [
                {
                    'id': v.id,
                    'name': v.name,
                    'sku': v.sku,
                    'price': float(v.price),
                    'stock': v.stock,
                    'attributes': getattr(v, 'attributes', {})
                }
                for v in variants
            ]
            doc.has_variants = len(variants) > 0
            doc.variants_count = len(variants)

            # نطاق السعر
            if variants:
                prices = [float(v.price) for v in variants]
                doc.price_range = {
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'currency': 'SAR'
                }

        # التقييمات
        doc.rating = float(product.rating or 0)
        doc.reviews_count = getattr(product, 'reviews_count', 0)
        doc.reviews = {
            'average_rating': doc.rating,
            'total_reviews': doc.reviews_count,
            'rating_distribution': getattr(product, 'rating_distribution', {})
        }

        # الخصائص
        doc.attributes = getattr(product, 'attributes', {})
        doc.tags = getattr(product, 'tags', [])
        doc.brand = getattr(product, 'brand', '')
        doc.unit = getattr(product, 'unit', 'piece')
        doc.unit_name = getattr(product, 'unit_name', 'قطعة')
        doc.min_order_quantity = getattr(product, 'min_order_quantity', 1)
        doc.max_order_quantity = getattr(product, 'max_order_quantity', 1000)

        # الحالة
        doc.status = product.status
        doc.is_active = product.status == 'active'
        doc.is_featured = getattr(product, 'is_featured', False)
        doc.is_new = getattr(product, 'is_new', False)
        doc.is_bestseller = getattr(product, 'is_bestseller', False)

        # الضرائب
        doc.tax_rate = float(getattr(product, 'tax_rate', 15))
        doc.price_includes_tax = getattr(product, 'price_includes_tax', True)

        # الترتيب والشعبية
        doc.sort_order = getattr(product, 'sort_order', 0)
        doc.popularity_score = _calculate_popularity_score(product)
        doc.sales_count = getattr(product, 'sales_count', 0)
        doc.views_count = getattr(product, 'views_count', 0)

        # التواريخ
        doc.created_at = product.created_at
        doc.updated_at = product.updated_at
        doc.published_at = getattr(product, 'published_at', product.created_at)

        # Suggest
        doc.suggest = {
            'input': [
                product.name,
                getattr(product, 'name_en', ''),
                product.sku or '',
            ],
            'weight': int(doc.popularity_score),
            'contexts': {
                'category': [product.category.slug] if product.category else [],
                'store': [product.store.slug] if product.store else [],
            }
        }

        return doc


# ===================================
# Store Document
# ===================================
class StoreDocument(Document):
    """
    مستند المتجر للفهرسة في Elasticsearch
    """

    # ===== معرفات =====
    id = Integer()
    slug = Keyword()

    # ===== النصوص الرئيسية =====
    name = Text(
        analyzer='arabic_analyzer',
        search_analyzer='arabic_search_analyzer',
        boost=3.0,
        fields={
            'keyword': Keyword(normalizer='arabic_normalizer'),
            'autocomplete': Text(
                analyzer='autocomplete_analyzer',
                search_analyzer='autocomplete_search_analyzer'
            )
        }
    )

    name_en = Text(
        analyzer='standard',
        boost=2.0,
        fields={'keyword': Keyword()}
    )

    description = Text(analyzer='arabic_analyzer', boost=1.5)
    description_en = Text(analyzer='standard')

    # ===== المورد =====
    vendor = Object(VendorInner)
    vendor_id = Integer()

    # ===== التصنيف =====
    category = Object(CategoryInner)
    category_id = Integer()
    categories = Keyword(multi=True)

    # ===== الموقع =====
    location = GeoPoint()
    address = Text(analyzer='arabic_analyzer')
    city = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    district = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    region = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    postal_code = Keyword()

    # ===== التقييمات =====
    rating = Float()
    reviews_count = Integer()
    reviews = Object(ReviewSummary)

    # ===== الإحصائيات =====
    products_count = Integer()
    orders_count = Integer()
    followers_count = Integer()

    # ===== ساعات العمل =====
    working_hours = Nested(WorkingHoursInner)
    is_open_now = Boolean()

    # ===== الصور =====
    logo = Keyword()
    cover_image = Keyword()
    gallery = Keyword(multi=True)

    # ===== التواصل =====
    phone = Keyword()
    email = Keyword()
    website = Keyword()
    whatsapp = Keyword()

    # ===== الحالة =====
    status = Keyword()
    is_active = Boolean()
    is_verified = Boolean()
    is_featured = Boolean()

    # ===== التوصيل =====
    delivery_enabled = Boolean()
    delivery_radius_km = Float()
    delivery_zones = Keyword(multi=True)
    min_order_amount = Float()
    delivery_fee = Float()
    free_delivery_threshold = Float()

    # ===== الترتيب =====
    sort_order = Integer()
    popularity_score = Float()

    # ===== التواريخ =====
    created_at = Date()
    updated_at = Date()

    # ===== Suggest =====
    suggest = Completion(
        analyzer='autocomplete_analyzer',
        search_analyzer='autocomplete_search_analyzer',
        contexts=[
            {'name': 'category', 'type': 'category'},
            {'name': 'city', 'type': 'category'},
            {
                'name': 'location',
                'type': 'geo',
                'precision': '50km'
            }
        ]
    )

    class Index:
        name = 'diwani_stores'
        settings = ARABIC_INDEX_SETTINGS

    class Django:
        model = 'stores.Store'

    @classmethod
    def from_django_model(cls, store) -> 'StoreDocument':
        """تحويل نموذج Django إلى مستند"""
        doc = cls(meta={'id': store.id})

        doc.id = store.id
        doc.slug = store.slug
        doc.name = store.name
        doc.name_en = getattr(store, 'name_en', '')
        doc.description = store.description or ''
        doc.description_en = getattr(store, 'description_en', '')

        # المورد
        if store.vendor:
            doc.vendor = {
                'id': store.vendor.id,
                'company_name': store.vendor.company_name,
                'is_verified': store.vendor.is_verified,
                'rating': float(getattr(store.vendor, 'rating', 0))
            }
            doc.vendor_id = store.vendor.id

        # التصنيف
        if store.category:
            doc.category = {
                'id': store.category.id,
                'name': store.category.name,
                'name_en': getattr(store.category, 'name_en', ''),
                'slug': store.category.slug,
            }
            doc.category_id = store.category.id

        # الموقع
        if store.location:
            doc.location = {
                'lat': store.location.y,
                'lon': store.location.x
            }
        doc.address = store.address or ''
        doc.city = store.city or ''
        doc.district = getattr(store, 'district', '')
        doc.region = getattr(store, 'region', '')
        doc.postal_code = getattr(store, 'postal_code', '')

        # التقييمات
        doc.rating = float(store.rating or 0)
        doc.reviews_count = getattr(store, 'reviews_count', 0)

        # الإحصائيات
        doc.products_count = store.products.filter(status='active').count()
        doc.orders_count = getattr(store, 'orders_count', 0)
        doc.followers_count = getattr(store, 'followers_count', 0)

        # الصور
        doc.logo = store.logo.url if store.logo else None
        doc.cover_image = store.cover_image.url if store.cover_image else None

        # الحالة
        doc.status = store.status
        doc.is_active = store.status == 'active'
        doc.is_verified = getattr(store, 'is_verified', False)
        doc.is_featured = getattr(store, 'is_featured', False)

        # التوصيل
        doc.delivery_enabled = getattr(store, 'delivery_enabled', True)
        doc.delivery_radius_km = float(getattr(store, 'delivery_radius_km', 50))
        doc.min_order_amount = float(getattr(store, 'min_order_amount', 0))
        doc.delivery_fee = float(getattr(store, 'delivery_fee', 0))
        doc.free_delivery_threshold = float(getattr(store, 'free_delivery_threshold', 0))

        # الترتيب
        doc.sort_order = getattr(store, 'sort_order', 0)
        doc.popularity_score = _calculate_store_popularity(store)

        # التواريخ
        doc.created_at = store.created_at
        doc.updated_at = store.updated_at

        # Suggest
        doc.suggest = {
            'input': [store.name, getattr(store, 'name_en', '')],
            'weight': int(doc.popularity_score),
            'contexts': {
                'category': [store.category.slug] if store.category else [],
                'city': [store.city] if store.city else [],
                'location': doc.location if doc.location else None
            }
        }

        return doc


# ===================================
# Category Document
# ===================================
class CategoryDocument(Document):
    """مستند التصنيف"""

    id = Integer()
    name = Text(
        analyzer='arabic_analyzer',
        boost=3.0,
        fields={
            'keyword': Keyword(normalizer='arabic_normalizer'),
            'autocomplete': Text(analyzer='autocomplete_analyzer')
        }
    )
    name_en = Text(analyzer='standard', fields={'keyword': Keyword()})
    slug = Keyword()
    description = Text(analyzer='arabic_analyzer')
    icon = Keyword()
    image = Keyword()

    parent_id = Integer()
    parent_name = Text(analyzer='arabic_analyzer')
    level = Integer()
    path = Keyword()  # "1/5/12" للتصفح السريع

    products_count = Integer()
    stores_count = Integer()
    is_active = Boolean()
    sort_order = Integer()

    # Children للتصنيفات الفرعية
    children = Nested(CategoryInner)

    suggest = Completion(analyzer='autocomplete_analyzer')

    class Index:
        name = 'diwani_categories'
        settings = ARABIC_INDEX_SETTINGS


# ===================================
# Vendor Document
# ===================================
class VendorDocument(Document):
    """مستند المورد"""

    id = Integer()
    user_id = Integer()

    company_name = Text(
        analyzer='arabic_analyzer',
        boost=3.0,
        fields={
            'keyword': Keyword(normalizer='arabic_normalizer'),
            'autocomplete': Text(analyzer='autocomplete_analyzer')
        }
    )
    company_name_en = Text(analyzer='standard', fields={'keyword': Keyword()})

    commercial_register = Keyword()
    tax_number = Keyword()

    # الموقع
    city = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    region = Text(analyzer='arabic_analyzer', fields={'keyword': Keyword()})
    location = GeoPoint()

    # الإحصائيات
    stores_count = Integer()
    products_count = Integer()
    orders_count = Integer()
    total_sales = Float()
    rating = Float()
    reviews_count = Integer()

    # الحالة
    status = Keyword()
    is_verified = Boolean()
    is_active = Boolean()

    # التواريخ
    created_at = Date()
    verified_at = Date()

    suggest = Completion(analyzer='autocomplete_analyzer')

    class Index:
        name = 'diwani_vendors'
        settings = ARABIC_INDEX_SETTINGS


# ===================================
# Helper Functions
# ===================================
def _get_category_path(category) -> List[str]:
    """الحصول على مسار التصنيفات"""
    path = []
    current = category
    while current:
        path.insert(0, current.slug)
        current = current.parent if hasattr(current, 'parent') else None
    return path


def _get_category_ids(category) -> List[int]:
    """الحصول على معرفات التصنيفات"""
    ids = []
    current = category
    while current:
        ids.insert(0, current.id)
        current = current.parent if hasattr(current, 'parent') else None
    return ids


def _calculate_popularity_score(product) -> float:
    """حساب نقاط الشعبية للمنتج"""
    score = 0.0

    # التقييم (0-50 نقطة)
    rating = float(product.rating or 0)
    score += rating * 10

    # عدد المراجعات (0-20 نقطة)
    reviews = getattr(product, 'reviews_count', 0)
    score += min(reviews, 100) * 0.2

    # المبيعات (0-20 نقطة)
    sales = getattr(product, 'sales_count', 0)
    score += min(sales, 500) * 0.04

    # المشاهدات (0-10 نقطة)
    views = getattr(product, 'views_count', 0)
    score += min(views, 10000) * 0.001

    # المنتج المميز (+20 نقطة)
    if getattr(product, 'is_featured', False):
        score += 20

    # المخزون المتوفر (+5 نقاط)
    if product.stock > 0:
        score += 5

    return min(score, 100)  # الحد الأقصى 100


def _calculate_store_popularity(store) -> float:
    """حساب نقاط الشعبية للمتجر"""
    score = 0.0

    # التقييم
    score += float(store.rating or 0) * 10

    # عدد المنتجات
    products_count = store.products.filter(status='active').count()
    score += min(products_count, 100) * 0.3

    # التحقق
    if getattr(store, 'is_verified', False):
        score += 20

    # المتجر المميز
    if getattr(store, 'is_featured', False):
        score += 15

    return min(score, 100)


# ===================================
# Index Management
# ===================================
def create_all_indexes():
    """إنشاء جميع الفهارس"""
    setup_elasticsearch_connection()

    for doc_class in [ProductDocument, StoreDocument, CategoryDocument, VendorDocument]:
        index = doc_class._index
        if not index.exists():
            index.create()
            print(f"Created index: {index._name}")
        else:
            print(f"Index already exists: {index._name}")


def delete_all_indexes():
    """حذف جميع الفهارس"""
    setup_elasticsearch_connection()

    for doc_class in [ProductDocument, StoreDocument, CategoryDocument, VendorDocument]:
        index = doc_class._index
        if index.exists():
            index.delete()
            print(f"Deleted index: {index._name}")


def rebuild_all_indexes():
    """إعادة بناء جميع الفهارس"""
    delete_all_indexes()
    create_all_indexes()
