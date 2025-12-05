"""
===================================
منصة ديواني - Stores Signals
===================================
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Store, StoreReview


@receiver(pre_save, sender=Store)
def store_status_change(sender, instance, **kwargs):
    """Handle store status changes."""
    if instance.pk:
        try:
            old_instance = Store.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == Store.StoreStatus.ACTIVE:
                    instance.approved_at = timezone.now()
                    # TODO: Send approval notification to owner
        except Store.DoesNotExist:
            pass


@receiver(post_save, sender=StoreReview)
def update_store_rating(sender, instance, created, **kwargs):
    """Update store rating when a new review is added."""
    if created:
        instance.store.update_rating()
