"""
===================================
منصة ديواني - Accounts Signals
===================================
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User, DriverProfile, VendorProfile


@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """Handle new user creation."""
    if created:
        # Log user creation
        print(f"[Diwani] New user created: {instance.phone_number}")

        # TODO: Send welcome SMS/notification


@receiver(pre_save, sender=DriverProfile)
def driver_status_change(sender, instance, **kwargs):
    """Handle driver status changes."""
    if instance.pk:
        try:
            old_instance = DriverProfile.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == DriverProfile.DriverStatus.APPROVED:
                    instance.approved_at = timezone.now()
                    # TODO: Send approval notification
                elif instance.status == DriverProfile.DriverStatus.REJECTED:
                    # TODO: Send rejection notification
                    pass
        except DriverProfile.DoesNotExist:
            pass


@receiver(pre_save, sender=VendorProfile)
def vendor_status_change(sender, instance, **kwargs):
    """Handle vendor status changes."""
    if instance.pk:
        try:
            old_instance = VendorProfile.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == VendorProfile.VendorStatus.APPROVED:
                    instance.approved_at = timezone.now()
                    # TODO: Send approval notification
        except VendorProfile.DoesNotExist:
            pass
