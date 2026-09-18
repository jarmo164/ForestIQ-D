"""Regression coverage for P1 issues #98-#105."""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Organization, OrganizationRole, Privilege, PrivilegeCode, User
from api.auth import token_pair
from forestry.models import Cadastre, CadastreLabel, CadastreNotification, Owner, OwnerCadastre
from operations.models import Contract, Deal, DealOffer, DealStage, OwnershipTransitionEvent
from operations.p1_models import (
    ContactActivity,
    ContractVersion,
    DataQualityIssue,
    DataQualityScanRun,
    DecisionEvidenceSnapshot,
    DealLossOutcome,
    LossReasonCode,
    MapWorkbasket,
    NextAction,
    OwnershipRelation,
    SalesSegment,
    SalesStageProbability,
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
        self.admin.organization_memberships.filter(organization=self.organization).update(roles=[OrganizationRole.ADMIN])
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

    @override_settings(CONTRACT_SIGNATURE_WEBHOOK_SECRET="sandbox-signature-secret")
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
        unverified = self.client.patch(
            f"/api/services/contracts/{contract.id}/signing",
            {"version": sent.data["version"], "state": "SIGNED", "signedUrl": "https://signing.example.test/final/P1-CONTRACT-1"},
            format="json",
        )
        self.assertEqual(unverified.status_code, 409, unverified.data)
        evidence = {
            "documentSha256": hashlib.sha256(b"external signed document").hexdigest(),
            "providerReference": "sandbox-verification-1",
            "signedUrl": "https://signing.example.test/final/P1-CONTRACT-1",
            "signer": {"identifier": self.owner.id, "name": self.owner.name},
            "certificate": {"serialNumber": "SANDBOX-1", "trusted": True, "validAtSigning": True},
            "signatureValid": True,
            "timestampValid": True,
        }
        canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        evidence["providerSignature"] = hmac.new(b"sandbox-signature-secret", canonical, hashlib.sha256).hexdigest()
        signed = self.client.post(f"/api/services/contracts/{contract.id}/signing/verification", evidence, format="json")
        self.assertEqual(signed.status_code, 200, signed.data)
        self.assertEqual(signed.data["state"], "SIGNED")
        self.assertEqual(signed.data["verification"]["status"], "VERIFIED")
        self.assertEqual(signed.data["verification"]["reference"], "sandbox-verification-1")

    @override_settings(CONTRACT_SIGNATURE_WEBHOOK_SECRET="sandbox-signature-secret")
    def test_signature_upload_waits_for_matching_valid_provider_evidence(self):
        deal = self.create_deal(stage=DealStage.WON)
        offer = DealOffer.objects.create(deal=deal, revision=1, kind=DealOffer.Kind.OFFER, status=DealOffer.Status.ACCEPTED, amount=Decimal("100.00"), terms="Terms", created_by=self.admin, organization=self.organization)
        contract = Contract.objects.create(id="P1-SIGNATURE-CHECK", source_deal=deal, source_offer=offer, document=b"%PDF contract", organization=self.organization)
        initial = self.client.get(f"/api/services/contracts/{contract.id}/signing")
        sent = self.client.patch(f"/api/services/contracts/{contract.id}/signing", {"version": initial.data["version"], "state": "SENT_FOR_SIGNATURE"}, format="json")
        content = b"%PDF-1.7 signed sandbox document"
        uploaded = self.client.post(
            f"/api/services/contracts/{contract.id}/signing/document",
            {"file": SimpleUploadedFile("signed.pdf", content, content_type="application/pdf")},
            format="multipart",
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.data)
        self.assertEqual(uploaded.data["state"], "SENT_FOR_SIGNATURE")
        self.assertEqual(uploaded.data["verification"]["status"], "PENDING")

        evidence = {
            "documentSha256": hashlib.sha256(b"tampered").hexdigest(),
            "providerReference": "sandbox-invalid",
            "signer": {"identifier": self.owner.id},
            "certificate": {"serialNumber": "SANDBOX-2", "trusted": True, "validAtSigning": True},
            "signatureValid": True,
            "timestampValid": True,
        }
        canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        evidence["providerSignature"] = hmac.new(b"sandbox-signature-secret", canonical, hashlib.sha256).hexdigest()
        rejected = self.client.post(f"/api/services/contracts/{contract.id}/signing/verification", evidence, format="json")
        self.assertEqual(rejected.status_code, 422, rejected.data)
        self.assertEqual(rejected.data["verification"]["status"], "FAILED")
        self.assertIn("hash", rejected.data["verification"]["failureReason"].lower())

        evidence["documentSha256"] = hashlib.sha256(content).hexdigest()
        evidence["providerReference"] = "sandbox-valid"
        evidence.pop("providerSignature")
        canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        evidence["providerSignature"] = hmac.new(b"sandbox-signature-secret", canonical, hashlib.sha256).hexdigest()
        verified = self.client.post(f"/api/services/contracts/{contract.id}/signing/verification", evidence, format="json")
        self.assertEqual(verified.status_code, 200, verified.data)
        self.assertEqual(verified.data["state"], "SIGNED")
        self.assertTrue(verified.data["verification"]["integrityValid"])

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

    def test_data_quality_scan_reports_audited_status_and_auto_resolves_fixed_signal(self):
        first = self.client.post("/api/services/admin/data-quality/scan", {}, format="json")
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data["status"], DataQualityScanRun.Status.SUCCESS)
        self.assertGreaterEqual(first.data["processedOwners"], 1)
        self.assertTrue(DataQualityScanRun.objects.filter(id=first.data["id"]).exists())

        missing = DataQualityIssue.objects.get(owner=self.owner, issue_type="MISSING_CONTACT")
        self.owner.phone = "5551234"
        self.owner.email = "fixed@example.test"
        self.owner.save(update_fields=("phone", "email"))

        second = self.client.post("/api/services/admin/data-quality/scan", {}, format="json")
        self.assertEqual(second.status_code, 200, second.data)
        self.assertGreaterEqual(second.data["autoResolved"], 1)
        missing.refresh_from_db()
        self.assertEqual(missing.status, DataQualityIssue.Status.RESOLVED)

        status_response = self.client.get("/api/services/admin/data-quality/scan")
        self.assertEqual(status_response.status_code, 200, status_response.data)
        self.assertEqual(status_response.data["lastRun"]["id"], second.data["id"])
        self.assertIn("queueSize", status_response.data)

    def test_loss_analysis_filters_by_period_seller_and_previous_stage(self):
        reason = LossReasonCode.objects.create(code="PRICE_TEST", label="Price test", sort_order=10)
        evaluation = self.create_deal(stage=DealStage.LOST)
        qualification = self.create_deal(stage=DealStage.LOST)
        DealLossOutcome.objects.create(
            deal=evaluation,
            reason=reason,
            previous_stage=DealStage.EVALUATION,
            recorded_by=self.admin,
        )
        DealLossOutcome.objects.create(
            deal=qualification,
            reason=reason,
            previous_stage=DealStage.QUALIFICATION,
            recorded_by=self.admin,
        )
        today = timezone.localdate().isoformat()
        response = self.client.get(
            "/api/services/admin/loss-analysis",
            {
                "from": today,
                "to": today,
                "sellerId": str(self.admin.id),
                "previousStage": DealStage.EVALUATION,
            },
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["reasonCode"], "PRICE_TEST")
        self.assertEqual(response.data[0]["previousStage"], DealStage.EVALUATION)
        self.assertEqual(response.data[0]["count"], 1)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "forestiq-data-quality-scan": {
                "task": "operations.run_scheduled_data_quality_scans",
                "schedule": 21600.0,
            }
        }
    )
    def test_data_quality_schedule_contract_is_registered(self):
        from django.conf import settings

        schedule = settings.CELERY_BEAT_SCHEDULE["forestiq-data-quality-scan"]
        self.assertEqual(schedule["task"], "operations.run_scheduled_data_quality_scans")
        self.assertEqual(schedule["schedule"], 21600.0)

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

    def test_owner_360_loads_summary_relations_map_workflow_and_normalized_timeline(self):
        OwnerCadastre.objects.create(owner=self.owner, cadastre=self.cadastre, organization=self.organization)
        active = self.client.get(f"/api/services/owners/{self.owner.id}/ownership-relations", {"active": "true", "limit": 1})
        self.assertEqual(active.status_code, 200, active.data)
        relation = OwnershipRelation.objects.get(id=active.data["items"][0]["id"])
        ended = self.client.patch(
            f"/api/services/ownership-relations/{relation.id}",
            {"operation": "END", "reason": "Sold parcel", "protected": False},
            format="json",
        )
        self.assertEqual(ended.status_code, 200, ended.data)
        second = Cadastre.objects.create(id="12345:001:0002", name="Current parcel", area=Decimal("7.50"), organization=self.organization)
        recreated = self.client.post(
            f"/api/services/owners/{self.owner.id}/ownership-relations",
            {"cadastreId": second.id, "reason": "Current ownership", "protected": True},
            format="json",
        )
        self.assertEqual(recreated.status_code, 201, recreated.data)
        deal = self.create_deal(stage=DealStage.EVALUATION)
        action = NextAction.objects.create(
            owner=self.owner,
            deal=deal,
            text="Call before offer",
            due_at=timezone.now() + timedelta(days=1),
            assignee=self.admin,
            created_by=self.admin,
            organization=self.organization,
        )
        ContactActivity.objects.create(
            owner=self.owner,
            deal=deal,
            channel=ContactActivity.Channel.PHONE,
            outcome_code="INTERESTED",
            note="Asked for an indicative price.",
            created_by=self.admin,
            organization=self.organization,
        )
        WorkflowAuditEvent.objects.create(
            owner=self.owner,
            deal=deal,
            event_type="OWNER_360_TEST_AUDIT",
            actor=self.admin,
            organization=self.organization,
        )
        offer = DealOffer.objects.create(
            deal=deal,
            revision=1,
            kind=DealOffer.Kind.OFFER,
            status=DealOffer.Status.ACCEPTED,
            amount=Decimal("42000.00"),
            terms="Accepted",
            created_by=self.admin,
            organization=self.organization,
        )
        Contract.objects.create(id="OWNER-360-CONTRACT", source_deal=deal, source_offer=offer, organization=self.organization)
        OwnershipTransitionEvent.objects.create(
            owner=self.owner,
            cadastre=second,
            event_type="OWNER_CHANGED",
            occurred_at=timezone.now(),
            source_reference="registry-360",
            organization=self.organization,
        )

        summary = self.client.get(f"/api/services/owners/{self.owner.id}/360/summary")
        self.assertEqual(summary.status_code, 200, summary.data)
        self.assertEqual(summary.data["relations"]["active"], 1)
        self.assertEqual(summary.data["relations"]["historical"], 1)
        self.assertEqual(summary.data["openNextActionCount"], 1)
        self.assertEqual(summary.data["activeDealCount"], 1)

        active_page = self.client.get(f"/api/services/owners/{self.owner.id}/ownership-relations", {"active": "true"})
        history_page = self.client.get(f"/api/services/owners/{self.owner.id}/ownership-relations", {"active": "false"})
        self.assertEqual([item["cadastre"]["id"] for item in active_page.data["items"]], [second.id])
        self.assertEqual([item["cadastre"]["id"] for item in history_page.data["items"]], [self.cadastre.id])

        map_layer = self.client.get(f"/api/services/owners/{self.owner.id}/360/map")
        self.assertEqual(map_layer.status_code, 200, map_layer.data)
        self.assertEqual(map_layer.data["type"], "FeatureCollection")
        self.assertEqual(map_layer.data["features"][0]["properties"]["cadastreId"], second.id)

        workflow = self.client.get(f"/api/services/owners/{self.owner.id}/360/workflow")
        self.assertEqual(workflow.status_code, 200, workflow.data)
        self.assertEqual(workflow.data["nextActions"][0]["id"], str(action.id))
        self.assertEqual(workflow.data["activeDeals"][0]["id"], str(deal.id))
        self.assertEqual(workflow.data["recentOwnershipChanges"][0]["sourceReference"], "registry-360")

        timeline = self.client.get(f"/api/services/owners/{self.owner.id}/360/timeline")
        self.assertEqual(timeline.status_code, 200, timeline.data)
        timeline_types = {item["type"] for item in timeline.data}
        self.assertTrue({"CONTACT", "NEXT_ACTION", "DEAL", "CONTRACT", "OWNERSHIP_RELATION", "OWNERSHIP_CHANGE", "WORKFLOW_AUDIT"}.issubset(timeline_types))

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

    def test_sales_funnel_uses_configured_probabilities_and_documented_weighted_value(self):
        older = timezone.now() - timedelta(days=5)
        won = self.create_deal(stage=DealStage.WON)
        won.closed_at = older + timedelta(days=4)
        won.save(update_fields=("closed_at",))
        DealOffer.objects.create(
            deal=won,
            revision=1,
            kind=DealOffer.Kind.OFFER,
            status=DealOffer.Status.ACCEPTED,
            amount=Decimal("125000.00"),
            created_by=self.admin,
            organization=self.organization,
        )
        evaluation = self.create_deal(stage=DealStage.EVALUATION)
        evaluation.recommended_purchase_price = Decimal("100000.00")
        evaluation.save(update_fields=("recommended_purchase_price",))
        Deal.objects.filter(id__in=[won.id, evaluation.id]).update(created_at=older, updated_at=older + timedelta(days=2))

        probability = self.client.post(
            "/api/services/admin/sales/stage-probabilities",
            {"stage": "EVALUATION", "probability": "0.5000", "validFrom": (timezone.localdate() - timedelta(days=1)).isoformat(), "note": "Regression fixture"},
            format="json",
        )
        self.assertEqual(probability.status_code, 201, probability.data)
        self.assertEqual(SalesStageProbability.objects.filter(stage=DealStage.EVALUATION).count(), 1)

        response = self.client.get("/api/services/sales/funnel")
        self.assertEqual(response.status_code, 200, response.data)
        stages = {item["stage"]: item for item in response.data["stages"]}
        self.assertIn("weightedValue = deterministic deal value", response.data["formula"])
        self.assertEqual(stages["EVALUATION"]["volume"], 1)
        self.assertEqual(stages["EVALUATION"]["probability"], 0.5)
        self.assertEqual(stages["EVALUATION"]["probabilitySource"], "configured")
        self.assertEqual(stages["EVALUATION"]["weightedValue"], 50000.0)
        self.assertEqual(stages["WON"]["weightedValue"], 125000.0)
        self.assertGreaterEqual(stages["QUALIFICATION"]["conversionToNext"], 0)

    def test_sales_segments_preview_token_required_before_assignment_apply(self):
        stale = self.create_deal(stage=DealStage.QUALIFICATION)
        stale.price_expectation = Decimal("40000.00")
        stale.save(update_fields=("price_expectation",))
        fresh = self.create_deal(stage=DealStage.EVALUATION)
        fresh.price_expectation = Decimal("80000.00")
        fresh.save(update_fields=("price_expectation",))
        Deal.objects.filter(id__in=[stale.id, fresh.id]).update(updated_at=timezone.now() - timedelta(days=20))
        target = User.objects.create_user("sales-target", "Sales Target", "very-secure-password", default_organization=self.organization)
        target.organization_memberships.filter(organization=self.organization).update(roles=[OrganizationRole.CRM_MANAGER])

        created = self.client.post(
            "/api/services/sales/segments",
            {"name": "Stale qualification", "filters": {"stages": ["QUALIFICATION"], "staleDays": 7, "activeOnly": True, "minValue": "10000"}, "shared": True},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(SalesSegment.objects.filter(name="Stale qualification").count(), 1)
        segment_id = created.data["id"]

        blocked = self.client.post(
            f"/api/services/sales/segments/{segment_id}/assignment-apply",
            {"targetAssigneeId": target.id},
            format="json",
        )
        self.assertEqual(blocked.status_code, 400, blocked.data)

        preview = self.client.post(
            f"/api/services/sales/segments/{segment_id}/assignment-preview",
            {"targetAssigneeId": target.id},
            format="json",
        )
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertEqual(preview.data["dealCount"], 1)
        self.assertEqual(preview.data["ownerCount"], 1)
        self.assertTrue(preview.data["previewToken"])

        applied = self.client.post(
            f"/api/services/sales/segments/{segment_id}/assignment-apply",
            {"targetAssigneeId": target.id, "previewToken": preview.data["previewToken"]},
            format="json",
        )
        self.assertEqual(applied.status_code, 200, applied.data)
        self.assertEqual(applied.data["changedOwnerCount"], 1)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.assignee_id, target.id)
