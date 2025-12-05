"""
===================================
منصة ديواني - Orders Signals
===================================
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order, OrderStatusHistory


@receiver(pre_save, sender=Order)
def track_status_change(sender, instance, **kwargs):
    """Track order status changes."""
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Create status history entry
                OrderStatusHistory.objects.create(
                    order=instance,
                    status=instance.status,
                    notes=f'تغيير الحالة من {old_instance.get_status_display()} إلى {instance.get_status_display()}'
                )
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    """Handle new order creation."""
    if created:
        # Create initial status history
        OrderStatusHistory.objects.create(
            order=instance,
            status=instance.status,
            notes='تم إنشاء الطلب'
        )

        # TODO: Send notification to store
        # TODO: Send confirmation to customer
