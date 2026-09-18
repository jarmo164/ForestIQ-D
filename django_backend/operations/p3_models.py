"""P3 notification preference and delivery models."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from accounts.models import OrganizationScopedModel


def default_notification_events():
    return ["REMINDER_DUE"]


def default_notification_channels():
    return ["IN_APP"]


class NotificationPreference(OrganizationScopedModel):
    """Per-user delivery policy. Only explicitly supported channels may be persisted."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="notification_preference",
    )
    enabled = models.BooleanField(default=True)
    event_types = models.JSONField(default=default_notification_events)
    channels = models.JSONField(default=default_notification_channels)
    updated_at = models.DateTimeField(auto_now=True)
    organization_parent_fields = ("user",)

    class Meta:
        db_table = "p3_notification_preferences"


class ReminderNotificationDelivery(OrganizationScopedModel):
    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        SKIPPED = "SKIPPED", "Skipped"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reminder = models.ForeignKey("operations.Reminder", on_delete=models.CASCADE, related_name="notification_deliveries")
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reminder_notification_deliveries",
    )
    channel = models.CharField(max_length=20, default="IN_APP")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    reason = models.CharField(max_length=255, blank=True)
    dispatched_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("reminder", "recipient")

    class Meta:
        db_table = "p3_reminder_notification_deliveries"
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "reminder", "recipient", "channel"),
                name="p3_uq_reminder_notification_delivery",
            )
        ]
        indexes = [
            models.Index(
                fields=("organization", "recipient", "dispatched_at"),
                name="p3_reminder_delivery_user_idx",
            )
        ]
