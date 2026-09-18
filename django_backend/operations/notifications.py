"""Deterministic, preference-aware reminder notification delivery."""
from __future__ import annotations

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Organization
from accounts.organization_context import organization_scope
from operations.models import ApplicationMessage, Reminder
from operations.p3_models import NotificationPreference, ReminderNotificationDelivery

SUPPORTED_EVENTS = frozenset({"REMINDER_DUE"})
SUPPORTED_CHANNELS = frozenset({"IN_APP"})
DEFAULT_EVENTS = ("REMINDER_DUE",)
DEFAULT_CHANNELS = ("IN_APP",)


def preference_for(user):
    """Return persisted preference or a safe internal-only default."""
    try:
        preference = NotificationPreference.objects.get(user=user)
        events = [item for item in preference.event_types if item in SUPPORTED_EVENTS]
        channels = [item for item in preference.channels if item in SUPPORTED_CHANNELS]
        return preference.enabled, tuple(events), tuple(channels)
    except NotificationPreference.DoesNotExist:
        return True, DEFAULT_EVENTS, DEFAULT_CHANNELS


def _recipients(reminder: Reminder):
    users = {}
    if reminder.creator_id and reminder.creator and reminder.creator.is_active:
        users[reminder.creator_id] = reminder.creator
    if reminder.owner_id and reminder.owner and reminder.owner.assignee_id:
        assignee = reminder.owner.assignee
        if assignee and assignee.is_active:
            users[assignee.id] = assignee
    return list(users.values())


def deliver_reminder(reminder: Reminder) -> dict:
    sent = skipped = 0
    for recipient in _recipients(reminder):
        enabled, events, channels = preference_for(recipient)
        if not enabled or "REMINDER_DUE" not in events or "IN_APP" not in channels:
            ReminderNotificationDelivery.objects.get_or_create(
                reminder=reminder,
                recipient=recipient,
                channel="IN_APP",
                defaults={"status": ReminderNotificationDelivery.Status.SKIPPED, "reason": "Disabled by user preference."},
            )
            skipped += 1
            continue
        try:
            with transaction.atomic():
                delivery, created = ReminderNotificationDelivery.objects.get_or_create(
                    reminder=reminder,
                    recipient=recipient,
                    channel="IN_APP",
                    defaults={"status": ReminderNotificationDelivery.Status.SENT},
                )
                if not created:
                    continue
                ApplicationMessage.objects.create(
                    organization=reminder.organization,
                    recipient=recipient,
                    text=reminder.text or "Meeldetuletuse tähtaeg on saabunud.",
                    category="REMINDER",
                    event_key=f"reminder:{reminder.pk}:due",
                )
                sent += 1
        except IntegrityError:
            continue
    return {"sent": sent, "skipped": skipped}


def deliver_due_reminders(*, lookback_hours: int = 24) -> dict:
    now = timezone.now()
    earliest = now - timedelta(hours=max(1, lookback_hours))
    result = {"organizations": 0, "reminders": 0, "sent": 0, "skipped": 0}
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        with organization_scope(organization_id):
            result["organizations"] += 1
            reminders = (
                Reminder.objects.select_related("creator", "owner", "owner__assignee")
                .filter(due_time__lte=now, due_time__gte=earliest)
                .filter(Q(creator__isnull=False) | Q(owner__assignee__isnull=False))
                .distinct()
            )
            for reminder in reminders:
                result["reminders"] += 1
                outcome = deliver_reminder(reminder)
                result["sent"] += outcome["sent"]
                result["skipped"] += outcome["skipped"]
    return result
