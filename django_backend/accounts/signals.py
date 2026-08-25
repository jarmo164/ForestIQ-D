from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from accounts.authorization import sync_user_groups
from accounts.models import Privilege


@receiver(post_save, sender=Privilege)
@receiver(post_delete, sender=Privilege)
def refresh_django_groups(sender, instance: Privilege, **kwargs) -> None:
    sync_user_groups(instance.user)
