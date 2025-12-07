"""
===================================
منصة ديواني - Search Signals
إشارات المزامنة التلقائية مع Elasticsearch
===================================

يتم تحديث الفهرس تلقائياً عند:
- إضافة منتج/متجر/مورد جديد
- تحديث منتج/متجر/مورد
- حذف منتج/متجر/مورد
- تغيير التصنيفات
"""

import logging
from typing import Any

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.conf import settings

from .tasks import (
    index_product_task,
    delete_product_from_index_task,
    index_store_task,
    delete_store_from_index_task,
    index_vendor_task,
    delete_vendor_from_index_task,
    index_category_task,
    delete_category_from_index_task,
    bulk_update_products_by_store_task,
    bulk_update_products_by_category_task
)

logger = logging.getLogger(__name__)


# ===================================
# تحقق من تفعيل البحث
# ===================================
def is_search_enabled() -> bool:
    """التحقق من تفعيل Elasticsearch"""
    return getattr(settings, 'ELASTICSEARCH_ENABLED', True)


# ===================================
# Product Signals
# ===================================
@receiver(post_save, sender='products.Product')
def product_post_save(sender, instance, created: bool, **kwargs):
    """
    فهرسة المنتج عند الإنشاء أو التحديث
    """
    if not is_search_enabled():
        return

    try:
        # استخدام Celery task للفهرسة غير المتزامنة
        index_product_task.delay(instance.id)

        action = 'created' if created else 'updated'
        logger.info(f"[Search] Product {action}: {instance.id} - {instance.name}")
    except Exception as e:
        logger.error(f"[Search] Error indexing product {instance.id}: {e}")


@receiver(post_delete, sender='products.Product')
def product_post_delete(sender, instance, **kwargs):
    """
    حذف المنتج من الفهرس
    """
    if not is_search_enabled():
        return

    try:
        delete_product_from_index_task.delay(instance.id)
        logger.info(f"[Search] Product deleted from index: {instance.id}")
    except Exception as e:
        logger.error(f"[Search] Error deleting product {instance.id}: {e}")


@receiver(post_save, sender='products.ProductImage')
def product_image_post_save(sender, instance, **kwargs):
    """
    إعادة فهرسة المنتج عند تغيير الصور
    """
    if not is_search_enabled():
        return

    try:
        if instance.product_id:
            index_product_task.delay(instance.product_id)
            logger.debug(f"[Search] Product re-indexed after image update: {instance.product_id}")
    except Exception as e:
        logger.error(f"[Search] Error re-indexing product after image update: {e}")


@receiver(post_save, sender='products.ProductVariant')
def product_variant_post_save(sender, instance, **kwargs):
    """
    إعادة فهرسة المنتج عند تغيير المتغيرات
    """
    if not is_search_enabled():
        return

    try:
        if instance.product_id:
            index_product_task.delay(instance.product_id)
            logger.debug(f"[Search] Product re-indexed after variant update: {instance.product_id}")
    except Exception as e:
        logger.error(f"[Search] Error re-indexing product after variant update: {e}")


@receiver(post_save, sender='products.ProductReview')
def product_review_post_save(sender, instance, **kwargs):
    """
    إعادة فهرسة المنتج عند إضافة تقييم
    """
    if not is_search_enabled():
        return

    try:
        if instance.product_id:
            # تأخير قليل للتأكد من تحديث التقييم الإجمالي
            index_product_task.apply_async(
                args=[instance.product_id],
                countdown=2  # تأخير 2 ثانية
            )
            logger.debug(f"[Search] Product re-indexed after review: {instance.product_id}")
    except Exception as e:
        logger.error(f"[Search] Error re-indexing product after review: {e}")


# ===================================
# Store Signals
# ===================================
@receiver(post_save, sender='stores.Store')
def store_post_save(sender, instance, created: bool, **kwargs):
    """
    فهرسة المتجر عند الإنشاء أو التحديث
    """
    if not is_search_enabled():
        return

    try:
        index_store_task.delay(instance.id)

        # إذا تغيرت حالة المتجر، نحدث جميع منتجاته
        if not created:
            bulk_update_products_by_store_task.delay(instance.id)

        action = 'created' if created else 'updated'
        logger.info(f"[Search] Store {action}: {instance.id} - {instance.name}")
    except Exception as e:
        logger.error(f"[Search] Error indexing store {instance.id}: {e}")


@receiver(post_delete, sender='stores.Store')
def store_post_delete(sender, instance, **kwargs):
    """
    حذف المتجر من الفهرس
    """
    if not is_search_enabled():
        return

    try:
        delete_store_from_index_task.delay(instance.id)
        logger.info(f"[Search] Store deleted from index: {instance.id}")
    except Exception as e:
        logger.error(f"[Search] Error deleting store {instance.id}: {e}")


@receiver(post_save, sender='stores.StoreReview')
def store_review_post_save(sender, instance, **kwargs):
    """
    إعادة فهرسة المتجر عند إضافة تقييم
    """
    if not is_search_enabled():
        return

    try:
        if instance.store_id:
            index_store_task.apply_async(
                args=[instance.store_id],
                countdown=2
            )
    except Exception as e:
        logger.error(f"[Search] Error re-indexing store after review: {e}")


# ===================================
# Vendor Signals
# ===================================
@receiver(post_save, sender='users.VendorProfile')
def vendor_post_save(sender, instance, created: bool, **kwargs):
    """
    فهرسة المورد عند الإنشاء أو التحديث
    """
    if not is_search_enabled():
        return

    try:
        index_vendor_task.delay(instance.id)

        action = 'created' if created else 'updated'
        logger.info(f"[Search] Vendor {action}: {instance.id} - {instance.company_name}")
    except Exception as e:
        logger.error(f"[Search] Error indexing vendor {instance.id}: {e}")


@receiver(post_delete, sender='users.VendorProfile')
def vendor_post_delete(sender, instance, **kwargs):
    """
    حذف المورد من الفهرس
    """
    if not is_search_enabled():
        return

    try:
        delete_vendor_from_index_task.delay(instance.id)
        logger.info(f"[Search] Vendor deleted from index: {instance.id}")
    except Exception as e:
        logger.error(f"[Search] Error deleting vendor {instance.id}: {e}")


# ===================================
# Category Signals
# ===================================
@receiver(post_save, sender='products.Category')
def category_post_save(sender, instance, created: bool, **kwargs):
    """
    فهرسة التصنيف عند الإنشاء أو التحديث
    """
    if not is_search_enabled():
        return

    try:
        index_category_task.delay(instance.id)

        # إذا تغير التصنيف، نحدث جميع منتجاته
        if not created:
            bulk_update_products_by_category_task.delay(instance.id)

        action = 'created' if created else 'updated'
        logger.info(f"[Search] Category {action}: {instance.id} - {instance.name}")
    except Exception as e:
        logger.error(f"[Search] Error indexing category {instance.id}: {e}")


@receiver(post_delete, sender='products.Category')
def category_post_delete(sender, instance, **kwargs):
    """
    حذف التصنيف من الفهرس
    """
    if not is_search_enabled():
        return

    try:
        delete_category_from_index_task.delay(instance.id)
        logger.info(f"[Search] Category deleted from index: {instance.id}")
    except Exception as e:
        logger.error(f"[Search] Error deleting category {instance.id}: {e}")


# ===================================
# User Signals (للعملاء الجدد)
# ===================================
@receiver(post_save, sender='users.User')
def user_post_save(sender, instance, created: bool, **kwargs):
    """
    معالجة المستخدم الجديد
    """
    if not created:
        return

    try:
        # يمكن إضافة منطق إضافي هنا
        # مثل: إرسال ترحيب، تحديث إحصائيات، إلخ
        logger.info(f"[Search] New user registered: {instance.id}")
    except Exception as e:
        logger.error(f"[Search] Error processing new user: {e}")


# ===================================
# Order Signals (لتحديث شعبية المنتجات)
# ===================================
@receiver(post_save, sender='orders.Order')
def order_post_save(sender, instance, **kwargs):
    """
    تحديث شعبية المنتجات بعد الطلب
    """
    if not is_search_enabled():
        return

    # فقط للطلبات المكتملة
    if instance.status != 'delivered':
        return

    try:
        # تحديث جميع منتجات الطلب
        for item in instance.items.all():
            index_product_task.apply_async(
                args=[item.product_id],
                countdown=5  # تأخير 5 ثواني
            )
        logger.debug(f"[Search] Products re-indexed after order completion: {instance.id}")
    except Exception as e:
        logger.error(f"[Search] Error re-indexing products after order: {e}")


# ===================================
# Bulk Operations Handler
# ===================================
class SearchIndexManager:
    """
    مدير فهرسة البحث للعمليات المجمعة
    """

    @staticmethod
    def reindex_all_products():
        """إعادة فهرسة جميع المنتجات"""
        from apps.products.models import Product

        products = Product.objects.filter(status='active')
        for product in products.iterator(chunk_size=100):
            index_product_task.delay(product.id)

        logger.info(f"[Search] Queued {products.count()} products for reindexing")

    @staticmethod
    def reindex_all_stores():
        """إعادة فهرسة جميع المتاجر"""
        from apps.stores.models import Store

        stores = Store.objects.filter(status='active')
        for store in stores.iterator(chunk_size=100):
            index_store_task.delay(store.id)

        logger.info(f"[Search] Queued {stores.count()} stores for reindexing")

    @staticmethod
    def reindex_all_vendors():
        """إعادة فهرسة جميع الموردين"""
        from apps.users.models import VendorProfile

        vendors = VendorProfile.objects.filter(is_verified=True)
        for vendor in vendors.iterator(chunk_size=100):
            index_vendor_task.delay(vendor.id)

        logger.info(f"[Search] Queued {vendors.count()} vendors for reindexing")

    @staticmethod
    def reindex_all():
        """إعادة فهرسة كل شيء"""
        SearchIndexManager.reindex_all_products()
        SearchIndexManager.reindex_all_stores()
        SearchIndexManager.reindex_all_vendors()
        logger.info("[Search] Full reindex initiated")
