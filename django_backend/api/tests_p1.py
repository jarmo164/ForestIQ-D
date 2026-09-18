"""Regression coverage for P1 issues #98-#105."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Organization, OrganizationRole, Privilege, PrivilegeCode, User
from api.auth import token_pair
from forestry.models import Cadastre, CadastreLabel, CadastreNotification, Owner, OwnerCadastre
from operations.models import Contract, Deal, DealOffer, DealStage
from operations.p1_models import (
    ContactActivity,
    ContractVersion,
    DataQualityIssue,
    DecisionEvidenceSnapshot,
    DealLossOutcome,
    MapWorkbasket,
    NextAction,
    OwnershipRelation,
    WorkflowAuditEvent,
)


class P1WorkflowApiTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(slug="p1-tests", name="P1 tests")
        self.admin = User.objects.create_user(
            "p1-admin",
            "P1 Administrator",
            "very-secure-password",
            default_organization=self.organization,
        )
        Privilege.objects.create(user=self.admin, code=PrivilegeCode.ADMIN)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.admin)['actualToken']['token']}")
        self.owner = Owner.objects.create(
            id="38001010001",
            name="P1 Forest Owner",
            assignee=self.admin,
            organization=self.organization,
        )
        self.cadastre = Cadastre.objects.create(
            id="12345:001:0001",
            name="P1 parcel",
            organization=self.organization,
        )

    def create_deal(self, *, stage=DealStage.QUALIFICATION):
        deal = Deal.objects.create(
            owner=self.owner,
            sale_subject="FOREST",
            stage=stage,
            created_by=self.admin,
            organization=self.organization,
        )
        deal.parcels.add(self.cadastre)
        return deal

    def test_owner_search_uses_stable_bounded_cursor_pages(self):
        Owner.objects.create(id="38001010002", name="Second owner", organization=self.organization)
        Owner.objects.create(id="38001010003", name="Third owner", organization=self.organization)

        first = self.client.get("/api/services/owners", {"limit": 2})
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(len(first.data["items"]), 2)
        self.assertTrue(first.data["nextCursor"])

        second = self.client.get("/api/services/owners", {"limit": 2, "cursor": first.data["nextCursor"]})
        self.assertEqual(second.status_code, 200, second.data)
        first_ids = {item["id"] for item in first.data["items"]}
        second_ids = {item["id"] for item in second.data["items"]}
        self.assertFalse(first_ids.intersection(second_ids))

    def test_structured_contact_creates_audited_next_action_and_can_complete_it(self):
        due_at = timezone.now() + timedelta(days=1)
        response = self.client.post(
            f"/api/services/owners/{self.owner.id}/activities",
            {
                "channel": "PHONE",
                "outcomeCode": "CALLBACK",
                "outcomeReason": "Owner requested a call tomorrow",
                "note": "Discuss timber sale options.",
                "nextAction": {"text": "Call owner back", "dueAt": due_at.isoformat(), "assigneeId": self.admin.id},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(ContactActivity.objects.filter(owner=self.owner).count(), 1)
        action = NextAction.objects.get(owner=self.owner)

        completed = self.client.patch(
            f"/api/services/next-actions/{action.id}",
            {"operation": "COMPLETE"},
            format="json",
        )
        self.assertEqual(completed.status_code, 200, completed.data)
        action.refresh_from_db()
        self.assertEqual(action.status, NextAction.Status.DONE)
        self.assertIsNotNone(action.completed_at)

        timeline = self.client.get(f"/api/services/owners/{self.owner.id}/timeline")
        self.assertEqual(timeline.status_code, 200, timeline.data)
        self.assertTrue(any(event["type"] == "CONTACT_RECORDED" for event in timeline.data))
        self.assertTrue(any(event["type"] == "NEXT_ACTION_COMPLETE" for event in timeline.data))

    def test_deal_health_explains_missing_action_and_evaluation_deadline(self):
        deal = self.create_deal(stage=DealStage.EVALUATION)

        response = self.client.get("/api/services/deals/workbench")
        self.assertEqual(response.status_code, 200, response.data)
        item = next(record for record in response.data if record["id"] == str(deal.id))
        codes = {reason["code"] for reason in item["health"]}
        self.assertIn("NO_NEXT_ACTION", codes)
        self.assertIn("EVALUATION_DEADLINE_MISSING", codes)

        next_action = self.client.post(
            f"/api/services/deals/{deal.id}/next-action",
            {
                "text": "Complete evaluation",
                "dueAt": (timezone.now() + timedelta(days=1)).isoformat(),
                "evaluationDueAt": (timezone.now() + timedelta(days=2)).isoformat(),
                "assigneeId": self.admin.id,
            },
            format="json",
        )
        self.assertEqual(next_action.status_code, 201, next_action.data)
        refreshed = self.client.get("/api/services/deals/workbench")
        item = next(record for record in refreshed.data if record["id"] == str(deal.id))
        codes = {reason["code"] for reason in item["health"]}
        self.assertNotIn("NO_NEXT_ACTION", codes)
        self.assertNotIn("EVALUATION_DEADLINE_MISSING", codes)

    def test_managed_loss_reason_creates_structured_outcome_and_follow_up(self):
        deal = self.create_deal(stage=DealStage.NEGOTIATION)
        reasons = self.client.get("/api/services/admin/loss-reasons")
        self.assertEqual(reasons.status_code, 200, reasons.data)
        self.assertTrue(any(item["code"] == "PRICE" for item in reasons.data))

        response = self.client.post(
            f"/api/services/deals/{deal.id}/commercial/lost",
            {
                "version": deal.version,
                "reasonCode": "PRICE",
                "note": "Seller expectation remained above mandate.",
                "followUpAt": (timezone.now() + timedelta(days=30)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        deal.refresh_from_db()
        self.assertEqual(deal.stage, DealStage.LOST)
        self.assertEqual(deal.loss_reason, "PRICE")
        self.assertEqual(DealLossOutcome.objects.get(deal=deal).reason.code, "PRICE")
        self.assertTrue(NextAction.objects.filter(deal=deal, status=NextAction.Status.OPEN).exists())

    def test_contract_creation_captures_immutable_version_and_signing_lifecycle(self):
        deal = self.create_deal(stage=DealStage.WON)
        offer = DealOffer.objects.create(
            deal=deal,
            revision=1,
            kind=DealOffer.Kind.OFFER,
            status=DealOffer.Status.ACCEPTED,
            amount=Decimal("125000.00"),
            terms="Accepted terms",
            created_by=self.admin,
            organization=self.organization,
        )
        contract = Contract.objects.create(
            id="P1-CONTRACT-1",
            source_deal=deal,
            source_offer=offer,
            document=b"%PDF-1.4 controlled",
            organization=self.organization,
        )
        version = ContractVersion.objects.get(contract=contract, version_number=1)
        self.assertEqual(version.snapshot["acceptedPrice"], "125000.00")
        self.assertEqual(version.snapshot["seller"]["id"], self.owner.id)

        signing = self.client.get(f"/api/services/contracts/{contract.id}/signing")
        self.assertEqual(signing.status_code, 200, signing.data)
        self.assertEqual(signing.data["state"], "PREPARING")
        sent = self.client.patch(
            f"/api/services/contracts/{contract.id}/signing",
            {"version": signing.data["version"], "state": "SENT_FOR_SIGNATURE", "responsibleId": self.admin.id, "dueAt": (timezone.now() + timedelta(days=3)).isoformat()},
            format="json",
        )
        self.assertEqual(sent.status_code, 200, sent.data)
        signed = self.client.patch(
            f"/api/services/contracts/{contract.id}/signing",
            {"version": sent.data["version"], "state": "SIGNED", "signedUrl": "https://signing.example.test/final/P1-CONTRACT-1"},
            format="json",
        )
        self.assertEqual(signed.status_code, 200, signed.data)
        self.assertEqual(signed.data["state"], "SIGNED")

    def test_data_quality_scan_creates_assignable_manual_review_queue(self):
        deal = self.create_deal(stage=DealStage.EVALUATION)
        duplicate = Owner.objects.create(
            id="38001010002",
            name="Possible duplicate",
            phone="5551234",
            email="same@example.test",
            organization=self.organization,
        )
        self.owner.phone = "+372 555 1234"
        self.owner.email = "same@example.test"
        self.owner.save(update_fields=("phone", "email"))

        response = self.client.post("/api/services/admin/data-quality/scan", {}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        issue_types = set(DataQualityIssue.objects.values_list("issue_type", flat=True))
        self.assertIn("DUPLICATE_PHONE", issue_types)
        self.assertIn("DUPLICATE_EMAIL", issue_types)
        self.assertIn("DEAL_NO_NEXT_ACTION", issue_types)
        self.assertIn("EVALUATION_DEADLINE_MISSING", issue_types)

        issue = DataQualityIssue.objects.filter(deal=deal, issue_type="DEAL_NO_NEXT_ACTION").get()
        resolved = self.client.patch(
            f"/api/services/admin/data-quality/issues/{issue.id}",
            {"operation": "RESOLVE", "reason": "Next action added in source workflow."},
            format="json",
        )
        self.assertEqual(resolved.status_code, 200, resolved.data)
        self.assertEqual(resolved.data["status"], "RESOLVED")
        self.client.post("/api/services/admin/data-quality/scan", {}, format="json")
        issue.refresh_from_db()
        self.assertEqual(issue.status, "RESOLVED")
        self.assertEqual(DataQualityIssue.objects.filter(fingerprint=issue.fingerprint).count(), 1)

    def test_protected_manual_owner_cadastre_end_is_not_revived_by_legacy_sync_write(self):
        create = self.client.post(
            f"/api/services/owners/{self.owner.id}/ownership-relations",
            {"cadastreId": self.cadastre.id, "reason": "Verified from registry", "protected": True},
            format="json",
        )
        self.assertEqual(create.status_code, 201, create.data)
        relation = OwnershipRelation.objects.get(id=create.data["id"])
        ended = self.client.patch(
            f"/api/services/ownership-relations/{relation.id}",
            {"operation": "END", "reason": "Manual registry correction", "protected": True},
            format="json",
        )
        self.assertEqual(ended.status_code, 200, ended.data)
        self.assertFalse(OwnerCadastre.objects.filter(owner=self.owner, cadastre=self.cadastre).exists())

        OwnerCadastre.objects.create(owner=self.owner, cadastre=self.cadastre, organization=self.organization)
        self.assertFalse(OwnerCadastre.objects.filter(owner=self.owner, cadastre=self.cadastre).exists())
        relation.refresh_from_db()
        self.assertFalse(relation.is_active)
        self.assertTrue(relation.manual_protected)
        self.assertTrue(relation.events.filter(event_type="EXTERNAL_RESTORE_BLOCKED").exists())

    def test_decision_evidence_preview_and_confirm_freeze_reproducible_snapshot(self):
        self.owner.phone = ""
        self.owner.email = "owner@example.test"
        self.owner.last_cadastre_list_refresh = timezone.now() - timedelta(days=120)
        self.owner.save(update_fields=("phone", "email", "last_cadastre_list_refresh"))
        self.cadastre.area = Decimal("12.5000")
        self.cadastre.forest_area = Decimal("8.2500")
        self.cadastre.mk_date = timezone.now() - timedelta(days=2)
        self.cadastre.save(update_fields=("area", "forest_area", "mk_date"))
        CadastreLabel.objects.create(cadastre=self.cadastre, code="CONSERVATION_AREA", organization=self.organization)
        CadastreNotification.objects.create(
            id=990001,
            notification_number=55001,
            cadastre=self.cadastre,
            registration_date=timezone.now() - timedelta(days=1),
            archived=False,
            organization=self.organization,
        )
        deal = self.create_deal(stage=DealStage.EVALUATION)
        deal.recommended_purchase_price = Decimal("100000.00")
        deal.proposed_offer_price = Decimal("95000.00")
        deal.save(update_fields=("recommended_purchase_price", "proposed_offer_price"))

        preview = self.client.get(f"/api/services/deals/{deal.id}/decision-evidence/preview")
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertEqual(preview.data["snapshot"]["portfolioSummary"]["cadastreCount"], 1)
        preview_codes = {signal["code"] for signal in preview.data["snapshot"]["signals"]}
        self.assertIn("MISSING_CONTACT", preview_codes)
        self.assertIn("STALE_REGISTRY_DATA", preview_codes)
        self.assertIn("FRESH_FOREST_NOTICE", preview_codes)
        self.assertIn("RESTRICTION_LABEL", preview_codes)

        confirmed = self.client.post(
            f"/api/services/deals/{deal.id}/decision-evidence",
            {"decisionType": "EVALUATION"},
            format="json",
        )
        self.assertEqual(confirmed.status_code, 201, confirmed.data)
        snapshot_id = confirmed.data["id"]
        self.assertEqual(confirmed.data["schemaVersion"], 1)
        self.assertEqual(confirmed.data["confirmedBy"]["id"], self.admin.id)
        self.assertEqual(confirmed.data["snapshot"]["deal"]["proposedOfferPrice"], 95000.0)
        self.assertEqual(confirmed.data["snapshot"]["selectedCadastres"][0]["area"], 12.5)

        deal.proposed_offer_price = Decimal("88000.00")
        deal.save(update_fields=("proposed_offer_price",))
        self.cadastre.area = Decimal("20.0000")
        self.cadastre.save(update_fields=("area",))
        stored = self.client.get(f"/api/services/deals/{deal.id}/decision-evidence")
        self.assertEqual(stored.status_code, 200, stored.data)
        frozen = next(item for item in stored.data if item["id"] == snapshot_id)
        self.assertEqual(frozen["snapshot"]["deal"]["proposedOfferPrice"], 95000.0)
        self.assertEqual(frozen["snapshot"]["selectedCadastres"][0]["area"], 12.5)

        second = self.client.post(
            f"/api/services/deals/{deal.id}/decision-evidence",
            {"decisionType": "OFFER"},
            format="json",
        )
        self.assertEqual(second.status_code, 201, second.data)
        self.assertEqual(second.data["sequence"], 2)
        self.assertEqual(second.data["snapshot"]["deal"]["proposedOfferPrice"], 88000.0)

        immutable = DecisionEvidenceSnapshot.objects.get(id=snapshot_id)
        immutable.snapshot = {"changed": True}
        with self.assertRaises(ValidationError):
            immutable.save()

    def test_map_workbasket_transfer_permissions_and_audit(self):
        second = Cadastre.objects.create(id="12345:001:0002", name="Second parcel", organization=self.organization)
        recipient = User.objects.create_user(
            "map-recipient",
            "Map Recipient",
            "very-secure-password",
            default_organization=self.organization,
        )
        recipient.organization_memberships.filter(organization=self.organization).update(roles=[OrganizationRole.CRM_MANAGER])
        recipient_client = APIClient()
        recipient_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(recipient)['actualToken']['token']}")

        created = self.client.post(
            "/api/services/map/workbaskets",
            {"name": "Handover basket", "description": "Field review", "cadastreIds": [self.cadastre.id, second.id]},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        basket_id = created.data["id"]
        self.assertEqual(created.data["cadastreCount"], 2)
        self.assertEqual(MapWorkbasket.objects.get(id=basket_id).items.count(), 2)

        transferred = self.client.post(
            f"/api/services/map/workbaskets/{basket_id}/transfer",
            {
                "assignedToUserId": recipient.id,
                "permission": "VIEW",
                "purpose": "Check access before offer",
                "dueAt": (timezone.now() + timedelta(days=2)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(transferred.status_code, 200, transferred.data)
        self.assertEqual(transferred.data["status"], "PENDING")
        self.assertEqual(transferred.data["assignedToUser"]["id"], recipient.id)

        view_only_update = recipient_client.patch(
            f"/api/services/map/workbaskets/{basket_id}",
            {"cadastreIds": [self.cadastre.id]},
            format="json",
        )
        self.assertEqual(view_only_update.status_code, 403, view_only_update.data)

        accepted = recipient_client.post(f"/api/services/map/workbaskets/{basket_id}/accept", {}, format="json")
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.assertEqual(accepted.data["status"], "ACCEPTED")
        self.assertEqual(accepted.data["acceptedBy"]["id"], recipient.id)

        cancel_accepted = self.client.post(f"/api/services/map/workbaskets/{basket_id}/cancel", {}, format="json")
        self.assertEqual(cancel_accepted.status_code, 409, cancel_accepted.data)
        self.assertTrue(WorkflowAuditEvent.objects.filter(event_type="MAP_WORKBASKET_ACCEPTED", payload__workbasketId=basket_id).exists())

        editable = self.client.post(
            "/api/services/map/workbaskets",
            {"name": "Editable basket", "cadastreIds": [self.cadastre.id]},
            format="json",
        )
        self.assertEqual(editable.status_code, 201, editable.data)
        edit_id = editable.data["id"]
        edit_transfer = self.client.post(
            f"/api/services/map/workbaskets/{edit_id}/transfer",
            {"assignedToUserId": recipient.id, "permission": "EDIT", "purpose": "Add missing units"},
            format="json",
        )
        self.assertEqual(edit_transfer.status_code, 200, edit_transfer.data)
        edit_update = recipient_client.patch(
            f"/api/services/map/workbaskets/{edit_id}",
            {"cadastreIds": [self.cadastre.id, second.id]},
            format="json",
        )
        self.assertEqual(edit_update.status_code, 200, edit_update.data)
        self.assertEqual(edit_update.data["cadastreCount"], 2)

        cancelled = self.client.post(f"/api/services/map/workbaskets/{edit_id}/cancel", {}, format="json")
        self.assertEqual(cancelled.status_code, 200, cancelled.data)
        self.assertEqual(cancelled.data["status"], "CANCELLED")

    def test_map_workbasket_blocks_cross_organization_targets(self):
        other_org = Organization.objects.create(slug="other-map-org", name="Other map org")
        other_user = User.objects.create_user("other-map-user", "Other User", "very-secure-password", default_organization=other_org)
        other_cadastre = Cadastre.objects.create(id="99999:001:0001", name="Other org parcel", organization=other_org)

        inaccessible_cadastre = self.client.post(
            "/api/services/map/workbaskets",
            {"name": "Bad basket", "cadastreIds": [other_cadastre.id]},
            format="json",
        )
        self.assertEqual(inaccessible_cadastre.status_code, 400, inaccessible_cadastre.data)

        created = self.client.post(
            "/api/services/map/workbaskets",
            {"name": "Org safe basket", "cadastreIds": [self.cadastre.id]},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        cross_user = self.client.post(
            f"/api/services/map/workbaskets/{created.data['id']}/transfer",
            {"assignedToUserId": other_user.id, "permission": "VIEW"},
            format="json",
        )
        self.assertEqual(cross_user.status_code, 403, cross_user.data)
