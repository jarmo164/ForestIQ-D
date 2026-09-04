"""Strict DRF input serializers for legacy-compatible ForestIQ mutation endpoints.

The legacy API accepts a number of historical field names, but it must not silently
coerce booleans, numbers or collection values into another type. These serializers
are intentionally validation-only: existing views keep their response compatibility
while every registered mutation is type-checked before it reaches persistence code.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from accounts.models import PrivilegeCode
from forestry.models import OwnerType


class StrictCharField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if not isinstance(data, bool):
            self.fail("invalid")
        return data


class StrictChoiceField(serializers.ChoiceField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid_choice", input=data)
        return super().to_internal_value(data)


class StrictListField(serializers.ListField):
    def to_internal_value(self, data):
        if not isinstance(data, list):
            self.fail("not_a_list", input_type=type(data).__name__)
        return super().to_internal_value(data)


class LegacyDateTimeField(serializers.Field):
    """Accept the two explicitly documented legacy date formats: epoch-ms or ISO-8601."""

    default_error_messages = {"invalid": "Expected epoch milliseconds or an ISO-8601 datetime string."}

    def to_internal_value(self, data):
        if isinstance(data, bool):
            self.fail("invalid")
        if isinstance(data, int):
            try:
                return datetime.fromtimestamp(data / 1000)
            except (OverflowError, OSError, ValueError):
                self.fail("invalid")
        if isinstance(data, str):
            parsed = parse_datetime(data.replace("Z", "+00:00"))
            if parsed is not None:
                return parsed
        self.fail("invalid")

    def to_representation(self, value):
        return value.isoformat()


class AdminUserCreateSerializer(serializers.Serializer):
    id = StrictCharField(max_length=50)
    name = StrictCharField(max_length=100)
    password = StrictCharField(min_length=12, write_only=True)
    privileges = StrictListField(child=StrictChoiceField(choices=PrivilegeCode.values), required=False, default=list)


class AdminUserUpdateSerializer(serializers.Serializer):
    name = StrictCharField(max_length=100, required=False)
    privileges = StrictListField(child=StrictChoiceField(choices=PrivilegeCode.values), required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one editable field is required.")
        return attrs


class OwnerStatusWriteSerializer(serializers.Serializer):
    id = StrictCharField(max_length=100)
    colorHex = StrictCharField(min_length=6, max_length=7, required=False)
    durationDays = StrictIntegerField(min_value=0, required=False)
    protectedStatus = StrictBooleanField(required=False)

    def validate_colorHex(self, value: str) -> str:
        clean = value.removeprefix("#")
        if len(clean) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in clean):
            raise serializers.ValidationError("Expected a six-digit hexadecimal color.")
        return value


class OwnerCreateSerializer(serializers.Serializer):
    ownerName = StrictCharField(max_length=100, required=False)
    name = StrictCharField(max_length=100, required=False)
    ownerType = StrictChoiceField(choices=OwnerType.values, required=False)
    type = StrictChoiceField(choices=OwnerType.values, required=False)

    def validate(self, attrs):
        if not (attrs.get("ownerName") or attrs.get("name")):
            raise serializers.ValidationError({"name": "Owner name is required."})
        return attrs


class OwnerUpdateSerializer(serializers.Serializer):
    version = StrictIntegerField(min_value=1)
    name = StrictCharField(max_length=100, required=False, allow_blank=True)
    type = StrictChoiceField(choices=OwnerType.values, required=False, allow_blank=True)
    phone = StrictCharField(max_length=100, required=False, allow_blank=True)
    email = serializers.EmailField(max_length=100, required=False, allow_blank=True)
    address = StrictCharField(max_length=500, required=False, allow_blank=True)
    info = StrictCharField(required=False, allow_blank=True)
    out_of_admin_search_reason = StrictCharField(max_length=50, required=False, allow_blank=True)


class VersionedStatusSerializer(serializers.Serializer):
    version = StrictIntegerField(min_value=1)
    code = StrictCharField(max_length=100)


class AssigneeSerializer(serializers.Serializer):
    version = StrictIntegerField(min_value=1)
    assignee = StrictCharField(max_length=50, required=False, allow_blank=True, allow_null=True)


class OwnerLogSerializer(serializers.Serializer):
    message = StrictCharField(allow_blank=False)


class MarkCadastresSerializer(serializers.Serializer):
    cadastres = StrictListField(child=StrictCharField(max_length=50))


class CadastreEvaluationSerializer(serializers.Serializer):
    ownerPrice = StrictCharField(max_length=255, required=False, allow_blank=True)
    ourPrice = StrictCharField(max_length=255, required=False, allow_blank=True)


class AdminWorkdeskAssignSerializer(serializers.Serializer):
    owners = StrictListField(child=StrictCharField(max_length=50), allow_empty=False)
    userId = StrictCharField(max_length=50)
    reassign = StrictBooleanField(required=False)


class ReminderCreateSerializer(serializers.Serializer):
    ownerId = StrictCharField(max_length=50, required=False, allow_blank=True)
    dueTime = LegacyDateTimeField()
    text = StrictCharField(required=False, allow_blank=True)
    cadastre = StrictCharField(required=False, allow_blank=True)
    propertyName = StrictCharField(required=False, allow_blank=True)


class PersonDumpCreateSerializer(serializers.Serializer):
    source = StrictCharField(max_length=100, required=False, allow_blank=True)
    name = StrictCharField(max_length=100)
    phone = StrictCharField(max_length=100, required=False, allow_blank=True)
    address = StrictCharField(max_length=500, required=False, allow_blank=True)
    code = StrictCharField(max_length=20, required=False, allow_blank=True)


class SendMessageSerializer(serializers.Serializer):
    recipient = StrictCharField(max_length=50)
    message = StrictCharField(allow_blank=False)


class MarkMessagesReadSerializer(serializers.Serializer):
    ids = StrictListField(child=StrictIntegerField(min_value=1), required=False)
    markReadUntil = LegacyDateTimeField(required=False)

    def validate(self, attrs):
        if "ids" in attrs and "markReadUntil" in attrs:
            raise serializers.ValidationError("Use ids or markReadUntil, not both.")
        return attrs


class ContractUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    version = StrictIntegerField(min_value=1, required=False)

    def validate_file(self, upload):
        if getattr(upload, "content_type", "") not in {"application/pdf", "application/x-pdf"}:
            raise serializers.ValidationError("Only PDF contract files are accepted.")
        return upload


MUTATION_RULES: tuple[tuple[str, str, type[serializers.Serializer]], ...] = (
    ("POST", r"^/services/admin/users$", AdminUserCreateSerializer),
    ("POST", r"^/services/admin/users/[^/]+$", AdminUserUpdateSerializer),
    ("POST", r"^/services/owner-statuses$", OwnerStatusWriteSerializer),
    ("POST", r"^/services/owners/[^/]+/add$", OwnerCreateSerializer),
    ("POST", r"^/services/owners/[^/]+$", OwnerUpdateSerializer),
    ("POST", r"^/services/owners/[^/]+/change-status$", VersionedStatusSerializer),
    ("POST", r"^/services/owner/[^/]+/status$", VersionedStatusSerializer),
    ("POST", r"^/services/owner/[^/]+/assignee$", AssigneeSerializer),
    ("POST", r"^/services/owners/[^/]+/log$", OwnerLogSerializer),
    ("POST", r"^/services/owners/[^/]+/mark-cadastres$", MarkCadastresSerializer),
    ("POST", r"^/services/cadastres/[^/]+/evaluation$", CadastreEvaluationSerializer),
    ("POST", r"^/services/admin-workdesk/assign$", AdminWorkdeskAssignSerializer),
    ("POST", r"^/services/reminders$", ReminderCreateSerializer),
    ("POST", r"^/services/persons-dump$", PersonDumpCreateSerializer),
    ("POST", r"^/services/messages/send$", SendMessageSerializer),
    ("POST", r"^/services/messages/(read|received/mark-as-read)$", MarkMessagesReadSerializer),
    ("POST", r"^/services/contracts/[^/]+/document$", ContractUploadSerializer),
)


def validation_error_payload(errors: Any, *, status_code: int, correlation_id: str | None) -> dict[str, Any]:
    return {
        "detail": "Request validation failed.",
        "code": "validation_error",
        "errors": errors,
        "status": status_code,
        "correlationId": correlation_id or None,
    }
