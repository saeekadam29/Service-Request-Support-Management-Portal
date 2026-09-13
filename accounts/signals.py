from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Whenever a User is created, automatically create a matching Profile
    (defaulting to the Customer role) so every user always has one.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        # Profile might not exist yet for users created before this signal existed
        Profile.objects.get_or_create(user=instance)
