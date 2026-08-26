"""Signals that preserve organization ownership for implicit relationship tables."""

from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from forestry.models import Cadastre, OwnerCadastre


@receiver(m2m_changed, sender=OwnerCadastre)
def enforce_owner_cadastre_organization(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Reject cross-organization links and stamp valid M2M rows with the owner org."""

    if not pk_set:
        return

    if action == "pre_add":
        if reverse:
            invalid = Cadastre.objects.exclude(organization_id=instance.organization_id).filter(pk__in=pk_set).exists()
        else:
            invalid = instance.owners.exclude(organization_id=instance.organization_id).filter(pk__in=pk_set).exists()
        if invalid:
            raise ValidationError("Owner and cadastre must belong to the same organization.")

    if action == "post_add":
        if reverse:
            OwnerCadastre.objects.filter(owner=instance, cadastre_id__in=pk_set).exclude(organization_id=instance.organization_id).update(organization_id=instance.organization_id)
        else:
            OwnerCadastre.objects.filter(cadastre=instance, owner_id__in=pk_set).exclude(organization_id=instance.organization_id).update(organization_id=instance.organization_id)
