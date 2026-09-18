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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    enabled = models.BooleanField(default=True)
    event_types = models.JSONField(default=default_notification_events)
    channels = models.JSONField(default=default_notification_channels)
    updated_at = models.DateTimeField(auto_now=True)
    organization_parent_fields = ("user",)

    class Meta:
        db_table = "p3_notification_preferences"
        constraints = [
            models.UniqueConstraint(fields=("organization", "user"), name="p3_uq_notification_preference_user"),
        ]


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


class RealtimeEvent(OrganizationScopedModel):
    """Durable event envelope used for websocket deduplication and audit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)
    topic = models.CharField(max_length=100, default="organization")
    payload = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="emitted_realtime_events",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="realtime_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("actor", "recipient")

    class Meta:
        db_table = "p3_realtime_events"
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("organization", "created_at"), name="p3_realtime_org_time_idx"),
            models.Index(fields=("organization", "recipient", "created_at"), name="p3_realtime_user_time_idx"),
        ]
