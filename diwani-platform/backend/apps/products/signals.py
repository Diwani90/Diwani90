"""
===================================
منصة ديواني - Products Signals
===================================
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg

from .models import Product, ProductReview


@receiver(post_save, sender=ProductReview)
def update_product_rating(sender, instance, created, **kwargs):
    """Update product rating when a review is added."""
    if created:
        product = instance.product
        result = product.reviews.aggregate(avg_rating=Avg('rating'))
        if result['avg_rating']:
            product.rating = round(result['avg_rating'], 2)
            product.rating_count = product.reviews.count()
            product.save(update_fields=['rating', 'rating_count'])
