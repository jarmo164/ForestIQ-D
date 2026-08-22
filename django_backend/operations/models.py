"""Operational workflow models: reminders, messages, contracts and contact data."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from forestry.models import Owner


class Reminder(models.Model):
    due_time = models.DateTimeField(db_column="duetime")
    text = models.TextField(blank=True, db_column="reminder_text")
    owner = models.ForeignKey(Owner, null=True, blank=True, on_delete=models.CASCADE, related_name="reminders", db_column="owner_id")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_reminders",
        db_column="creator",
    )
    created_time = models.DateTimeField(auto_now_add=True, db_column="created_time")
    cadastre = models.TextField(blank=True)
    property_name = models.TextField(blank=True)

    class Meta:
        db_table = "reminders"
        ordering = ("due_time", "id")
        indexes = [models.Index(fields=("due_time",), name="reminder_due_idx")]


class ApplicationMessage(models.Model):
    text = models.TextField(db_column="message_text")
    admin_message = models.BooleanField(default=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="application_messages",
        db_column="recipient",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "application_messages"
        ordering = ("-created_at", "-id")


class DirectMessage(models.Model):
    text = models.TextField(db_column="message")
    created_at = models.DateTimeField(auto_now_add=True)
    noticed_at = models.DateTimeField(null=True, blank=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_direct_messages",
        db_column="sender",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="received_direct_messages",
        db_column="recipient",
    )

    class Meta:
        db_table = "messages"
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("recipient", "noticed_at"), name="message_received_idx"),
            models.Index(fields=("sender", "created_at"), name="message_sent_idx"),
        ]


class PersonDump(models.Model):
    source = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=500, blank=True)
    code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "persons_dump"
        ordering = ("name", "id")


class Contract(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    document = models.BinaryField(null=True, blank=True, db_column="contract")
    base_id = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "contracts"


class ContractHistory(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    sellers = models.CharField(max_length=1000)
    buyer = models.CharField(max_length=100)
    contract_number = models.CharField(max_length=50, db_column="contract_no")
    created_at = models.DateTimeField(db_column="created")
    data = models.JSONField(default=dict)
    cadastres = models.CharField(max_length=100)

    class Meta:
        db_table = "contract_history"
        ordering = ("-created_at",)
