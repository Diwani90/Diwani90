"""
نظام التخزين المؤقت
===================

Cache Service للبحث والبيانات المتكررة
"""

import hashlib
import json
import logging
from typing import Optional, Any, Callable, List, Dict
from functools import wraps
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache, caches
from django.utils import timezone


logger = logging.getLogger(__name__)


# =============================================
# إعدادات التخزين المؤقت
# =============================================

class CacheConfig:
    """إعدادات التخزين المؤقت"""

    # أوقات الانتهاء الافتراضية (بالثواني)
    SEARCH_RESULTS_TTL = 300  # 5 دقائق
    PRODUCT_TTL = 600  # 10 دقائق
    CATEGORY_TTL = 3600  # ساعة
    STORE_TTL = 600  # 10 دقائق
    USER_TTL = 300  # 5 دقائق
    AUTOCOMPLETE_TTL = 1800  # 30 دقيقة
    TRENDING_TTL = 900  # 15 دقيقة

    # البادئات
    PREFIX_SEARCH = 'search:'
    PREFIX_PRODUCT = 'product:'
    PREFIX_CATEGORY = 'category:'
    PREFIX_STORE = 'store:'
    PREFIX_USER = 'user:'
    PREFIX_AUTOCOMPLETE = 'autocomplete:'
    PREFIX_TRENDING = 'trending:'


# =============================================
# خدمة التخزين المؤقت
# =============================================

class CacheService:
    """خدمة التخزين المؤقت الرئيسية"""

    def __init__(self, cache_alias: str = 'default'):
        self.cache = caches[cache_alias]
        self.config = CacheConfig()

    def get(self, key: str) -> Optional[Any]:
        """الحصول على قيمة من الكاش"""
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.warning(f'Cache get error: {e}')
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """تخزين قيمة في الكاش"""
        try:
            self.cache.set(key, value, timeout=ttl)
            return True
        except Exception as e:
            logger.warning(f'Cache set error: {e}')
            return False

    def delete(self, key: str) -> bool:
        """حذف قيمة من الكاش"""
        try:
            self.cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f'Cache delete error: {e}')
            return False

    def delete_pattern(self, pattern: str) -> int:
        """حذف مفاتيح بنمط معين"""
        try:
            # يتطلب Redis
            if hasattr(self.cache, 'delete_pattern'):
                return self.cache.delete_pattern(pattern)

            # Fallback: لا يدعم الأنماط
            return 0
        except Exception as e:
            logger.warning(f'Cache delete pattern error: {e}')
            return 0

    def get_or_set(
        self,
        key: str,
        default_func: Callable,
        ttl: int = 300
    ) -> Any:
        """الحصول من الكاش أو حساب وتخزين"""
        value = self.get(key)

        if value is None:
            value = default_func()
            if value is not None:
                self.set(key, value, ttl)

        return value

    def incr(self, key: str, delta: int = 1) -> int:
        """زيادة قيمة رقمية"""
        try:
            return self.cache.incr(key, delta)
        except ValueError:
            # المفتاح غير موجود
            self.cache.set(key, delta, timeout=3600)
            return delta

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """توليد مفتاح كاش"""
        key_parts = [prefix] + [str(a) for a in args]

        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(
                hashlib.md5(
                    json.dumps(sorted_kwargs, sort_keys=True).encode()
                ).hexdigest()[:12]
            )

        return ':'.join(key_parts)


# =============================================
# كاش البحث
# =============================================

class SearchCacheService(CacheService):
    """خدمة تخزين نتائج البحث"""

    def cache_search_results(
        self,
        query: str,
        filters: Dict[str, Any],
        results: Dict[str, Any],
        entity_type: str = 'product'
    ) -> bool:
        """تخزين نتائج البحث"""
        key = self._generate_search_key(query, filters, entity_type)
        return self.set(key, results, self.config.SEARCH_RESULTS_TTL)

    def get_search_results(
        self,
        query: str,
        filters: Dict[str, Any],
        entity_type: str = 'product'
    ) -> Optional[Dict[str, Any]]:
        """الحصول على نتائج بحث مخزنة"""
        key = self._generate_search_key(query, filters, entity_type)
        return self.get(key)

    def cache_autocomplete(
        self,
        prefix: str,
        suggestions: List[Dict[str, Any]]
    ) -> bool:
        """تخزين اقتراحات الإكمال التلقائي"""
        key = self.generate_key(self.config.PREFIX_AUTOCOMPLETE, prefix.lower())
        return self.set(key, suggestions, self.config.AUTOCOMPLETE_TTL)

    def get_autocomplete(self, prefix: str) -> Optional[List[Dict[str, Any]]]:
        """الحصول على اقتراحات الإكمال التلقائي"""
        key = self.generate_key(self.config.PREFIX_AUTOCOMPLETE, prefix.lower())
        return self.get(key)

    def cache_trending(
        self,
        trending: List[str],
        category: str = 'all'
    ) -> bool:
        """تخزين عمليات البحث الرائجة"""
        key = self.generate_key(self.config.PREFIX_TRENDING, category)
        return self.set(key, trending, self.config.TRENDING_TTL)

    def get_trending(self, category: str = 'all') -> Optional[List[str]]:
        """الحصول على عمليات البحث الرائجة"""
        key = self.generate_key(self.config.PREFIX_TRENDING, category)
        return self.get(key)

    def record_search_query(self, query: str, results_count: int):
        """تسجيل استعلام بحث للإحصائيات"""
        if len(query) < 2:
            return

        # زيادة عداد الاستعلام
        key = f'search_stats:{query.lower()}'
        self.incr(key)

    def invalidate_product_searches(self, product_id: str):
        """إبطال كاش البحث المتعلق بمنتج"""
        # حذف جميع نتائج البحث المخزنة
        # في الإنتاج، يمكن استخدام tags أو versioning
        pattern = f'{self.config.PREFIX_SEARCH}*'
        self.delete_pattern(pattern)

    def _generate_search_key(
        self,
        query: str,
        filters: Dict[str, Any],
        entity_type: str
    ) -> str:
        """توليد مفتاح البحث"""
        # تطبيع الاستعلام
        normalized_query = query.lower().strip()

        # فرز وتشفير الفلاتر
        filter_hash = ''
        if filters:
            sorted_filters = sorted(
                (k, v) for k, v in filters.items()
                if v is not None
            )
            filter_hash = hashlib.md5(
                json.dumps(sorted_filters, sort_keys=True).encode()
            ).hexdigest()[:12]

        return self.generate_key(
            self.config.PREFIX_SEARCH,
            entity_type,
            normalized_query,
            filter_hash
        )


# =============================================
# كاش المنتجات
# =============================================

class ProductCacheService(CacheService):
    """خدمة تخزين المنتجات"""

    def cache_product(self, product_id: str, data: Dict[str, Any]) -> bool:
        """تخزين منتج"""
        key = self.generate_key(self.config.PREFIX_PRODUCT, product_id)
        return self.set(key, data, self.config.PRODUCT_TTL)

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على منتج"""
        key = self.generate_key(self.config.PREFIX_PRODUCT, product_id)
        return self.get(key)

    def cache_products_batch(
        self,
        products: Dict[str, Dict[str, Any]]
    ) -> bool:
        """تخزين عدة منتجات"""
        try:
            for product_id, data in products.items():
                self.cache_product(product_id, data)
            return True
        except Exception as e:
            logger.warning(f'Batch cache error: {e}')
            return False

    def invalidate_product(self, product_id: str) -> bool:
        """إبطال كاش منتج"""
        key = self.generate_key(self.config.PREFIX_PRODUCT, product_id)
        return self.delete(key)

    def invalidate_vendor_products(self, vendor_id: str) -> int:
        """إبطال كاش منتجات متجر"""
        pattern = f'{self.config.PREFIX_PRODUCT}*:{vendor_id}'
        return self.delete_pattern(pattern)


# =============================================
# كاش الفئات
# =============================================

class CategoryCacheService(CacheService):
    """خدمة تخزين الفئات"""

    def cache_categories_tree(self, tree: List[Dict[str, Any]]) -> bool:
        """تخزين شجرة الفئات"""
        key = f'{self.config.PREFIX_CATEGORY}tree'
        return self.set(key, tree, self.config.CATEGORY_TTL)

    def get_categories_tree(self) -> Optional[List[Dict[str, Any]]]:
        """الحصول على شجرة الفئات"""
        key = f'{self.config.PREFIX_CATEGORY}tree'
        return self.get(key)

    def invalidate_categories(self) -> bool:
        """إبطال كاش الفئات"""
        pattern = f'{self.config.PREFIX_CATEGORY}*'
        self.delete_pattern(pattern)
        return True


# =============================================
# Decorators
# =============================================

def cached(
    key_prefix: str,
    ttl: int = 300,
    key_builder: Callable = None
):
    """
    Decorator للتخزين المؤقت

    @cached('products', ttl=600)
    def get_product(product_id):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # بناء المفتاح
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f'{key_prefix}:{":".join(str(a) for a in args)}'

            # التحقق من الكاش
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # تنفيذ الدالة
            result = func(*args, **kwargs)

            # تخزين النتيجة
            if result is not None:
                cache.set(cache_key, result, timeout=ttl)

            return result

        return wrapper
    return decorator


def invalidate_cache(*keys):
    """
    Decorator لإبطال الكاش بعد التعديل

    @invalidate_cache('products:*', 'search:*')
    def update_product(product_id, data):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # إبطال المفاتيح
            for key in keys:
                if '*' in key:
                    cache_service.delete_pattern(key)
                else:
                    cache.delete(key)

            return result

        return wrapper
    return decorator


# =============================================
# Singletons
# =============================================

cache_service = CacheService()
search_cache = SearchCacheService()
product_cache = ProductCacheService()
category_cache = CategoryCacheService()
