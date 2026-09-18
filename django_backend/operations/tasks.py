"""Celery tasks for operations notifications."""
from celery import shared_task

from accounts.models import Organization
from accounts.organization_context import organization_scope
from operations.data_quality import run_data_quality_scan
from operations.notifications import deliver_due_reminders


@shared_task(name="operations.dispatch_due_reminder_notifications")
def dispatch_due_reminder_notifications():
    return deliver_due_reminders()


@shared_task(name="operations.run_scheduled_data_quality_scans")
def run_scheduled_data_quality_scans():
    """Run a bounded quality scan independently for every active organization."""

    scanned = 0
    failed = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        try:
            with organization_scope(str(organization_id)):
                run_data_quality_scan(trigger="SCHEDULED")
            scanned += 1
        except Exception:
            failed += 1
    return {"scanned": scanned, "failed": failed}
