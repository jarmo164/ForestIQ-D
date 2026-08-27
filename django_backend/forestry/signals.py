"""Signals that preserve organization ownership and invalidate scoped map caches."""

from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from forestry.models import Cadastre, CadastreSubPart, ForestRegistryFeature, OwnerCadastre
from forestry.services.tile_cache import invalidate_vector_tiles


@receiver(m2m_changed, sender=OwnerCadastre)
def enforce_owner_cadastre_organization(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Reject cross-organization links and stamp valid M2M rows with the owner org."""

    if not pk_set and action != "post_clear":
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
            OwnerCadastre.all_objects.filter(owner=instance, cadastre_id__in=pk_set).exclude(organization_id=instance.organization_id).update(organization_id=instance.organization_id)
        else:
            OwnerCadastre.all_objects.filter(cadastre=instance, owner_id__in=pk_set).exclude(organization_id=instance.organization_id).update(organization_id=instance.organization_id)

    if action in {"post_add", "post_remove", "post_clear"}:
        invalidate_vector_tiles(str(instance.organization_id))


@receiver(post_save, sender=Cadastre)
@receiver(post_delete, sender=Cadastre)
def invalidate_cadastre_vector_tiles(sender, instance: Cadastre, **kwargs):
    """Invalidate every large layer derived from a changed cadastral object."""

    invalidate_vector_tiles(str(instance.organization_id))


@receiver(post_save, sender=CadastreSubPart)
@receiver(post_delete, sender=CadastreSubPart)
def invalidate_subpart_vector_tiles(sender, instance: CadastreSubPart, **kwargs):
    """Invalidate only the metsaeraldiste MVT layer after a subpart write."""

    invalidate_vector_tiles(str(instance.organization_id), ("subparts",))


@receiver(post_save, sender=ForestRegistryFeature)
@receiver(post_delete, sender=ForestRegistryFeature)
def invalidate_registry_vector_tiles(sender, instance: ForestRegistryFeature, **kwargs):
    """Invalidate only the Metsaregistri MVT layer after a registry feature write."""

    invalidate_vector_tiles(str(instance.organization_id), ("registry",))
