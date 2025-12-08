"""
===================================
منصة ديواني - Search Celery Tasks
مهام الفهرسة غير المتزامنة
===================================

مهام Celery للفهرسة في الخلفية:
- فهرسة فردية
- فهرسة مجمعة
- حذف من الفهرس
- إعادة بناء الفهارس
"""

import logging
from typing import Optional, List
from datetime import timedelta

from celery import shared_task, group, chain
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings

logger = logging.getLogger(__name__)


# ===================================
# Configuration
# ===================================
ELASTICSEARCH_ENABLED = getattr(settings, 'ELASTICSEARCH_ENABLED', True)
MAX_RETRIES = 3
RETRY_DELAY = 60  # ثانية


def get_es_connection():
    """الحصول على اتصال Elasticsearch"""
    from .documents import setup_elasticsearch_connection
    setup_elasticsearch_connection()


# ===================================
# Product Indexing Tasks
# ===================================
@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def index_product_task(self, product_id: int):
    """
    فهرسة منتج واحد في Elasticsearch
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped', 'reason': 'elasticsearch_disabled'}

    try:
        get_es_connection()
        from apps.products.models import Product
        from .documents import ProductDocument

        product = Product.objects.select_related(
            'category', 'store', 'store__vendor'
        ).prefetch_related(
            'images', 'variants', 'reviews'
        ).get(id=product_id)

        doc = ProductDocument.from_django_model(product)
        doc.save()

        logger.info(f"[Search Task] Product indexed: {product_id}")
        return {'status': 'success', 'product_id': product_id}

    except Product.DoesNotExist:
        logger.warning(f"[Search Task] Product not found: {product_id}")
        return {'status': 'not_found', 'product_id': product_id}

    except Exception as e:
        logger.error(f"[Search Task] Error indexing product {product_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=MAX_RETRIES)
def delete_product_from_index_task(self, product_id: int):
    """
    حذف منتج من الفهرس
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from .documents import ProductDocument

        doc = ProductDocument.get(id=product_id, ignore=404)
        if doc:
            doc.delete()
            logger.info(f"[Search Task] Product deleted from index: {product_id}")

        return {'status': 'success', 'product_id': product_id}

    except Exception as e:
        logger.error(f"[Search Task] Error deleting product {product_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True)
def bulk_index_products_task(self, product_ids: List[int]):
    """
    فهرسة مجموعة من المنتجات
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from apps.products.models import Product
        from .documents import ProductDocument
        from elasticsearch.helpers import bulk
        from elasticsearch_dsl import connections

        products = Product.objects.filter(
            id__in=product_ids
        ).select_related(
            'category', 'store', 'store__vendor'
        ).prefetch_related(
            'images', 'variants'
        )

        actions = []
        for product in products:
            doc = ProductDocument.from_django_model(product)
            actions.append(doc.to_dict(include_meta=True))

        if actions:
            es = connections.get_connection()
            success, failed = bulk(es, actions, raise_on_error=False)
            logger.info(f"[Search Task] Bulk indexed {success} products, {len(failed)} failed")
            return {'status': 'success', 'indexed': success, 'failed': len(failed)}

        return {'status': 'no_products'}

    except Exception as e:
        logger.error(f"[Search Task] Bulk index error: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True)
def bulk_update_products_by_store_task(self, store_id: int):
    """
    تحديث جميع منتجات متجر معين
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        from apps.products.models import Product

        product_ids = list(
            Product.objects.filter(store_id=store_id, status='active')
            .values_list('id', flat=True)
        )

        if product_ids:
            # تقسيم إلى مجموعات صغيرة
            chunk_size = 50
            for i in range(0, len(product_ids), chunk_size):
                chunk = product_ids[i:i + chunk_size]
                bulk_index_products_task.delay(chunk)

            logger.info(f"[Search Task] Queued {len(product_ids)} products for store {store_id}")

        return {'status': 'success', 'products_queued': len(product_ids)}

    except Exception as e:
        logger.error(f"[Search Task] Error updating products for store {store_id}: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True)
def bulk_update_products_by_category_task(self, category_id: int):
    """
    تحديث جميع منتجات تصنيف معين
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        from apps.products.models import Product

        product_ids = list(
            Product.objects.filter(category_id=category_id, status='active')
            .values_list('id', flat=True)
        )

        if product_ids:
            chunk_size = 50
            for i in range(0, len(product_ids), chunk_size):
                chunk = product_ids[i:i + chunk_size]
                bulk_index_products_task.delay(chunk)

            logger.info(f"[Search Task] Queued {len(product_ids)} products for category {category_id}")

        return {'status': 'success', 'products_queued': len(product_ids)}

    except Exception as e:
        logger.error(f"[Search Task] Error updating products for category {category_id}: {e}")
        return {'status': 'error', 'error': str(e)}


# ===================================
# Store Indexing Tasks
# ===================================
@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def index_store_task(self, store_id: int):
    """
    فهرسة متجر واحد
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from apps.stores.models import Store
        from .documents import StoreDocument

        store = Store.objects.select_related(
            'category', 'vendor'
        ).prefetch_related(
            'products', 'reviews'
        ).get(id=store_id)

        doc = StoreDocument.from_django_model(store)
        doc.save()

        logger.info(f"[Search Task] Store indexed: {store_id}")
        return {'status': 'success', 'store_id': store_id}

    except Store.DoesNotExist:
        logger.warning(f"[Search Task] Store not found: {store_id}")
        return {'status': 'not_found', 'store_id': store_id}

    except Exception as e:
        logger.error(f"[Search Task] Error indexing store {store_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=MAX_RETRIES)
def delete_store_from_index_task(self, store_id: int):
    """
    حذف متجر من الفهرس
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from .documents import StoreDocument

        doc = StoreDocument.get(id=store_id, ignore=404)
        if doc:
            doc.delete()
            logger.info(f"[Search Task] Store deleted from index: {store_id}")

        return {'status': 'success', 'store_id': store_id}

    except Exception as e:
        logger.error(f"[Search Task] Error deleting store {store_id}: {e}")
        raise self.retry(exc=e)


# ===================================
# Vendor Indexing Tasks
# ===================================
@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def index_vendor_task(self, vendor_id: int):
    """
    فهرسة مورد واحد
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from apps.accounts.models import VendorProfile
        from .documents import VendorDocument

        vendor = VendorProfile.objects.select_related('user').get(id=vendor_id)

        doc = VendorDocument(meta={'id': vendor.id})
        doc.id = vendor.id
        doc.user_id = vendor.user_id
        doc.company_name = vendor.company_name
        doc.company_name_en = getattr(vendor, 'company_name_en', '')
        doc.commercial_register = vendor.commercial_register
        doc.tax_number = getattr(vendor, 'tax_number', '')
        doc.city = getattr(vendor, 'city', '')
        doc.region = getattr(vendor, 'region', '')
        doc.status = vendor.status
        doc.is_verified = vendor.is_verified
        doc.is_active = vendor.status == 'approved'
        doc.created_at = vendor.created_at
        doc.verified_at = getattr(vendor, 'verified_at', None)

        # الإحصائيات
        if hasattr(vendor, 'stores'):
            doc.stores_count = vendor.stores.filter(status='active').count()

        doc.save()

        logger.info(f"[Search Task] Vendor indexed: {vendor_id}")
        return {'status': 'success', 'vendor_id': vendor_id}

    except VendorProfile.DoesNotExist:
        logger.warning(f"[Search Task] Vendor not found: {vendor_id}")
        return {'status': 'not_found', 'vendor_id': vendor_id}

    except Exception as e:
        logger.error(f"[Search Task] Error indexing vendor {vendor_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=MAX_RETRIES)
def delete_vendor_from_index_task(self, vendor_id: int):
    """
    حذف مورد من الفهرس
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from .documents import VendorDocument

        doc = VendorDocument.get(id=vendor_id, ignore=404)
        if doc:
            doc.delete()
            logger.info(f"[Search Task] Vendor deleted from index: {vendor_id}")

        return {'status': 'success', 'vendor_id': vendor_id}

    except Exception as e:
        logger.error(f"[Search Task] Error deleting vendor {vendor_id}: {e}")
        raise self.retry(exc=e)


# ===================================
# Category Indexing Tasks
# ===================================
@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def index_category_task(self, category_id: int, category_type: str = 'product'):
    """
    فهرسة تصنيف
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from .documents import CategoryDocument

        if category_type == 'product':
            from apps.products.models import ProductCategory as Category
        else:
            from apps.stores.models import StoreCategory as Category

        category = Category.objects.get(id=category_id)

        doc = CategoryDocument(meta={'id': category.id})
        doc.id = category.id
        doc.name = category.name
        doc.name_en = getattr(category, 'name_en', '')
        doc.slug = category.slug
        doc.description = getattr(category, 'description', '')
        doc.icon = getattr(category, 'icon', '')
        doc.image = category.image.url if category.image else None
        doc.is_active = getattr(category, 'is_active', True)
        doc.sort_order = getattr(category, 'sort_order', 0)

        if hasattr(category, 'parent') and category.parent:
            doc.parent_id = category.parent.id
            doc.parent_name = category.parent.name
            doc.level = getattr(category, 'level', 1)

        # عدد المنتجات
        if category_type == 'product':
            doc.products_count = category.products.filter(status='active').count()

        doc.save()

        logger.info(f"[Search Task] Category indexed: {category_id}")
        return {'status': 'success', 'category_id': category_id}

    except Exception as e:
        logger.error(f"[Search Task] Error indexing category {category_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=MAX_RETRIES)
def delete_category_from_index_task(self, category_id: int):
    """
    حذف تصنيف من الفهرس
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from .documents import CategoryDocument

        doc = CategoryDocument.get(id=category_id, ignore=404)
        if doc:
            doc.delete()
            logger.info(f"[Search Task] Category deleted from index: {category_id}")

        return {'status': 'success', 'category_id': category_id}

    except Exception as e:
        logger.error(f"[Search Task] Error deleting category {category_id}: {e}")
        raise self.retry(exc=e)


# ===================================
# Full Reindex Tasks
# ===================================
@shared_task(bind=True)
def full_reindex_products_task(self, batch_size: int = 100):
    """
    إعادة فهرسة جميع المنتجات
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        from apps.products.models import Product

        # حذف الفهرس وإعادة إنشائه
        get_es_connection()
        from .documents import ProductDocument
        ProductDocument._index.delete(ignore=404)
        ProductDocument._index.create()

        # فهرسة جميع المنتجات
        products = Product.objects.filter(status='active')
        total = products.count()
        indexed = 0

        product_ids = list(products.values_list('id', flat=True))

        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]
            bulk_index_products_task.delay(batch)
            indexed += len(batch)

        logger.info(f"[Search Task] Full product reindex queued: {total} products")
        return {'status': 'success', 'total': total, 'queued': indexed}

    except Exception as e:
        logger.error(f"[Search Task] Full reindex error: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True)
def full_reindex_stores_task(self, batch_size: int = 50):
    """
    إعادة فهرسة جميع المتاجر
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        from apps.stores.models import Store

        get_es_connection()
        from .documents import StoreDocument
        StoreDocument._index.delete(ignore=404)
        StoreDocument._index.create()

        stores = Store.objects.filter(status='active')
        total = stores.count()

        for store in stores.iterator(chunk_size=batch_size):
            index_store_task.delay(store.id)

        logger.info(f"[Search Task] Full store reindex queued: {total} stores")
        return {'status': 'success', 'total': total}

    except Exception as e:
        logger.error(f"[Search Task] Full store reindex error: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True)
def full_reindex_all_task(self):
    """
    إعادة فهرسة كل شيء
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        # تشغيل جميع مهام إعادة الفهرسة بالتتابع
        chain(
            full_reindex_products_task.s(),
            full_reindex_stores_task.s(),
        ).apply_async()

        logger.info("[Search Task] Full reindex initiated for all indexes")
        return {'status': 'success', 'message': 'Full reindex initiated'}

    except Exception as e:
        logger.error(f"[Search Task] Full reindex all error: {e}")
        return {'status': 'error', 'error': str(e)}


# ===================================
# Maintenance Tasks
# ===================================
@shared_task
def cleanup_orphaned_documents_task():
    """
    تنظيف المستندات اليتيمة (موجودة في ES لكن محذوفة من DB)
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        get_es_connection()
        from apps.products.models import Product
        from .documents import ProductDocument

        # الحصول على جميع IDs من Elasticsearch
        search = ProductDocument.search()
        search = search.source(['id'])
        search = search[:10000]  # حد أقصى

        es_ids = set()
        for hit in search.scan():
            es_ids.add(int(hit.meta.id))

        # الحصول على جميع IDs من قاعدة البيانات
        db_ids = set(Product.objects.values_list('id', flat=True))

        # المستندات اليتيمة
        orphaned_ids = es_ids - db_ids

        # حذف المستندات اليتيمة
        for orphan_id in orphaned_ids:
            delete_product_from_index_task.delay(orphan_id)

        logger.info(f"[Search Task] Cleanup: found {len(orphaned_ids)} orphaned documents")
        return {'status': 'success', 'orphaned': len(orphaned_ids)}

    except Exception as e:
        logger.error(f"[Search Task] Cleanup error: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def update_popularity_scores_task():
    """
    تحديث نقاط الشعبية لجميع المنتجات
    """
    if not ELASTICSEARCH_ENABLED:
        return {'status': 'skipped'}

    try:
        from apps.products.models import Product

        # تحديث المنتجات الأكثر مبيعاً ومشاهدة
        popular_products = Product.objects.filter(
            status='active'
        ).order_by('-sales_count', '-views_count')[:100]

        for product in popular_products:
            index_product_task.delay(product.id)

        logger.info(f"[Search Task] Updated popularity for {popular_products.count()} products")
        return {'status': 'success', 'updated': popular_products.count()}

    except Exception as e:
        logger.error(f"[Search Task] Popularity update error: {e}")
        return {'status': 'error', 'error': str(e)}
