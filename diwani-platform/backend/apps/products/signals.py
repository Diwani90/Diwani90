"""
إشارات المنتجات
================
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def connect_signals():
    """
    ربط الإشارات

    يُستدعى من apps.py
    """
    from .models import Product, ProductReview

    @receiver(post_save, sender=ProductReview)
    def update_product_rating(sender, instance, created, **kwargs):
        """تحديث تقييم المنتج عند إضافة تقييم جديد"""
        if created:
            instance.product.update_rating()

    @receiver(pre_save, sender=Product)
    def check_stock_status(sender, instance, **kwargs):
        """التحقق من حالة المخزون"""
        from .models import ProductStatus, ProductType

        if instance.product_type == ProductType.STOCK:
            if instance.track_inventory and instance.stock_quantity <= 0:
                if not instance.allow_backorder:
                    instance.status = ProductStatus.OUT_OF_STOCK

    logger.info("Product signals connected")


# ربط الإشارات عند استيراد الملف
try:
    connect_signals()
except Exception:
    pass
