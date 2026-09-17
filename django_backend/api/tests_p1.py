"""Regression coverage for P1 issues #98-#105."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Organization, Privilege, PrivilegeCode, User
from api.auth import token_pair
from forestry.models import Cadastre, Owner, OwnerCadastre
from operations.models import Contract, Deal, DealOffer, DealStage
from operations.p1_models import (
    ContactActivity,
    ContractVersion,
    DataQualityIssue,
    DealLossOutcome,
    NextAction,
    OwnershipRelation,
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
