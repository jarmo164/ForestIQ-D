"""Signals that keep legacy relations compatible with the P1 lifecycle models."""
from __future__ import annotations

import hashlib

from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

from forestry.models import OwnerCadastre
from operations.models import Contract, DealOffer, DealStage
from operations.p1_models import ContractVersion, OwnershipRelation, OwnershipRelationEvent


def _contract_snapshot(contract: Contract) -> dict:
    deal = contract.source_deal
    offer = contract.source_offer
    if deal is None or offer is None:
        raise ValidationError("Controlled contracts require a source deal and accepted offer.")
    if deal.stage != DealStage.WON:
        raise ValidationError("Controlled contracts can only be generated from a won deal.")
    if offer.deal_id != deal.id or offer.status != DealOffer.Status.ACCEPTED:
        raise ValidationError("Controlled contracts require the accepted offer from the source deal.")
    return {
        "dealId": str(deal.id),
        "offerId": str(offer.id),
        "acceptedPrice": str(offer.amount),
        "acceptedTerms": offer.terms,
        "seller": {"id": deal.owner_id, "name": deal.owner.name},
        "parcelIds": sorted(str(value) for value in deal.parcels.values_list("id", flat=True)),
        "templateId": str(contract.template_version_id) if contract.template_version_id else None,
        "templateSnapshot": contract.template_snapshot,
    }


@receiver(post_save, sender=Contract)
def create_initial_controlled_contract_version(sender, instance: Contract, created: bool, **kwargs):
    """Capture the first immutable PDF version as part of contract creation."""
    if not created or not instance.document or not instance.source_deal_id or not instance.source_offer_id:
        return
    snapshot = _contract_snapshot(instance)
    pdf = bytes(instance.document)
    ContractVersion.objects.create(
        contract=instance,
        deal=instance.source_deal,
        offer=instance.source_offer,
        version_number=1,
        pdf=pdf,
        pdf_sha256=hashlib.sha256(pdf).hexdigest(),
        snapshot=snapshot,
        checklist={
            "priceMatched": True,
            "termsMatched": True,
            "sellerMatched": True,
            "parcelsMatched": True,
        },
        created_by=instance.source_deal.created_by,
    )


@receiver(post_save, sender=OwnerCadastre)
def project_or_block_legacy_owner_cadastre(sender, instance: OwnerCadastre, created: bool, **kwargs):
    """Project legacy links and prevent an external get_or_create from reviving protected manual endings."""
    if not created:
        return
    blocked = (
        OwnershipRelation.all_objects.filter(
            organization_id=instance.organization_id,
            owner_id=instance.owner_id,
            cadastre_id=instance.cadastre_id,
            is_active=False,
            manual_protected=True,
        )
        .order_by("-valid_to", "-valid_from")
        .first()
    )
    if blocked:
        OwnershipRelationEvent.all_objects.create(
            organization_id=blocked.organization_id,
            relation=blocked,
            event_type="EXTERNAL_RESTORE_BLOCKED",
            reason=blocked.ended_reason or "Protected manual relation is inactive.",
            payload={"legacyRelationId": instance.pk},
        )
        instance.delete()
        return

    if not OwnershipRelation.all_objects.filter(
        organization_id=instance.organization_id,
        owner_id=instance.owner_id,
        cadastre_id=instance.cadastre_id,
        is_active=True,
    ).exists():
        relation = OwnershipRelation.all_objects.create(
            organization_id=instance.organization_id,
            owner=instance.owner,
            cadastre=instance.cadastre,
            source=OwnershipRelation.Source.EXTERNAL,
            source_reference="LEGACY_OWNER_CADASTRE",
            is_active=True,
        )
        OwnershipRelationEvent.all_objects.create(
            organization_id=instance.organization_id,
            relation=relation,
            event_type="EXTERNAL_RELATION_DISCOVERED",
            payload={"legacyRelationId": instance.pk},
        )
