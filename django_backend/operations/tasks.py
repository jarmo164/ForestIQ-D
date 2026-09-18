"""Celery tasks for operations notifications."""
from celery import shared_task

from operations.notifications import deliver_due_reminders


@shared_task(name="operations.dispatch_due_reminder_notifications")
def dispatch_due_reminder_notifications():
    return deliver_due_reminders()
