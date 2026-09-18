"""Organization-scoped realtime publishing and application-message helpers."""
from __future__ import annotations

import hashlib
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from accounts.organization_context import current_organization_id
from operations.models import ApplicationMessage
from operations.p3_models import RealtimeEvent


def organization_group(organization_id) -> str:
    return f"org_{str(organization_id).replace('-', '_')}"


def user_group(organization_id, user_id: str) -> str:
    digest = hashlib.sha256(str(user_id).encode()).hexdigest()[:24]
    return f"{organization_group(organization_id)}_user_{digest}"


def publish_org_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    actor=None,
    recipient=None,
    organization_id=None,
    topic: str = "organization",
) -> RealtimeEvent:
    organization_id = organization_id or current_organization_id()
    if organization_id is None:
        raise ValueError("Realtime events require an active organization.")
    event = RealtimeEvent.objects.create(
        organization_id=organization_id,
        event_type=event_type,
        topic=topic,
        payload=payload,
        actor=actor,
        recipient=recipient,
    )
    message = {
        "type": "forestiq.event",
        "event": {
            "eventId": str(event.id),
            "eventType": event.event_type,
            "topic": event.topic,
            "payload": event.payload,
            "createdAt": int(event.created_at.timestamp() * 1000),
        },
    }
    layer = get_channel_layer()
    if layer is not None:
        group = user_group(organization_id, recipient.id) if recipient is not None else organization_group(organization_id)
        try:
            async_to_sync(layer.group_send)(group, message)
        except Exception:
            # Realtime transport is advisory; the durable event/business write remains authoritative.
            pass
    return event


def unread_application_message_count(user) -> int:
    return ApplicationMessage.objects.filter(recipient=user, read_at__isnull=True, archived_at__isnull=True).count()


def create_application_message(*, recipient, text: str, category: str = "", event_key: str = "", organization_id=None):
    organization_id = organization_id or current_organization_id()
    message = ApplicationMessage.objects.create(
        organization_id=organization_id,
        recipient=recipient,
        text=text,
        category=category,
        event_key=event_key,
    )
    publish_org_event(
        "APPLICATION_MESSAGE",
        {
            "messageId": message.pk,
            "text": message.text,
            "category": message.category,
            "unreadCount": unread_application_message_count(recipient),
        },
        recipient=recipient,
        organization_id=organization_id,
        topic="user",
    )
    return message
