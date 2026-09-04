import json

from django.test import RequestFactory, SimpleTestCase
from rest_framework.response import Response

from api.middleware import TraceContextMiddleware, _normalize_error_response
from api.mutation_serializers import (
    ContractGenerateSerializer,
    OwnerCreateSerializer,
    OwnerStatusWriteSerializer,
    OwnerUpdateSerializer,
    ReminderCreateSerializer,
)


class StrictMutationSerializerTests(SimpleTestCase):
    def test_owner_type_rejects_non_string_instead_of_coercing(self):
        serializer = OwnerCreateSerializer(data={"name": "Test", "type": 123})
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_boolean_and_integer_fields_do_not_coerce_strings(self):
        serializer = OwnerStatusWriteSerializer(
            data={"id": "CALL_BACK", "durationDays": "7", "protectedStatus": "false"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("durationDays", serializer.errors)
        self.assertIn("protectedStatus", serializer.errors)

    def test_legacy_datetime_accepts_only_explicit_formats(self):
        valid = ReminderCreateSerializer(data={"dueTime": 1788512400000, "text": "Call"})
        invalid = ReminderCreateSerializer(data={"dueTime": {"tomorrow": True}, "text": "Call"})
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertFalse(invalid.is_valid())
        self.assertIn("dueTime", invalid.errors)

    def test_uuid_references_are_validated(self):
        serializer = ContractGenerateSerializer(
            data={"dealId": "not-a-uuid", "templateId": "also-not-a-uuid", "contractNumber": "L-1"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("dealId", serializer.errors)
        self.assertIn("templateId", serializer.errors)

    def test_version_can_remain_in_if_match_header(self):
        serializer = OwnerUpdateSerializer(data={"name": "Uus nimi"})
        self.assertTrue(serializer.is_valid(), serializer.errors)


class MutationValidationMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_registered_mutation_returns_consistent_400_envelope(self):
        request = self.factory.post(
            "/api/services/owner-statuses",
            data=json.dumps({"id": "NEW", "durationDays": "10"}),
            content_type="application/json",
        )
        response = TraceContextMiddleware(lambda _: Response({"ok": True}))(request)
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["code"], "validation_error")
        self.assertEqual(payload["status"], 400)
        self.assertIn("correlationId", payload)
        self.assertIn("durationDays", payload["errors"])

    def test_conflict_response_is_normalized(self):
        response = _normalize_error_response(Response({"detail": "Conflict"}, status=409))
        self.assertEqual(response.data["status"], 409)
        self.assertEqual(response.data["code"], "conflict")
        self.assertIn("correlationId", response.data)
