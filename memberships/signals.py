from django.db.models.signals import post_save
from django.dispatch import receiver

from clubs.models import Club
from .models import Membership, RoleChoices


@receiver(post_save, sender=Club)
def create_admin_membership(sender, instance, created, **kwargs):
    """
    Automatically create an admin membership for the club creator
    when a new club is created (works for admin panel, shell, etc.)
    """
    if created and instance.created_by:
        # Check if membership already exists (avoid duplicates)
        Membership.objects.get_or_create(
            user=instance.created_by,
            club=instance,
            defaults={"role": RoleChoices.ADMIN},
        )
