"""Import data from the former MetsIS PostgreSQL schema into Django models.

The source database is read only. Run after `migrate` and only with a verified backup.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone as datetime_timezone

import psycopg
from psycopg.errors import UndefinedTable
from psycopg.rows import dict_row
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import OrganizationMembership, Privilege, User
from accounts.organization_context import organization_scope
from accounts.organization_selection import active_organization
from forestry.models import (
    Cadastre,
    CadastreLabel,
    CadastreNotification,
    CadastreSubPart,
    ForestRegistryFeature,
    Owner,
    OwnerCadastre,
    OwnerFollowing,
    OwnerLog,
    OwnerStatus,
    OwnerStatusChange,
)
from operations.models import ApplicationMessage, Contract, ContractHistory, DirectMessage, PersonDump, Reminder


def parse_json(value, default):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def legacy_time(value):
    """Normalise legacy bigint epochs, timestamps and ISO strings to datetimes."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        divisor = 1000 if value > 10_000_000_000 else 1
        return datetime.fromtimestamp(value / divisor, tz=datetime_timezone.utc)
    return value


class Command(BaseCommand):
    help = "Import legacy MetsIS PostgreSQL data from LEGACY_DATABASE_URL."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Confirm that the legacy database is a read-only migration source.")
        parser.add_argument("--organization", required=True, help="Organization UUID or slug that will own the imported business records")

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Pass --confirm only after backing up the target database and reviewing the source URL.")
        source_url = os.getenv("LEGACY_DATABASE_URL")
        if not source_url:
            raise CommandError("LEGACY_DATABASE_URL is required.")
        self.organization = active_organization(options["organization"])
        if self.organization is None:
            raise CommandError("--organization must identify an active organization by UUID or slug.")
        with psycopg.connect(source_url, row_factory=dict_row) as source:
            self.source = source
            with organization_scope(self.organization.id):
                with transaction.atomic():
                    self.import_users()
                    self.import_owner_statuses()
                    self.import_owners_and_cadastres()
                    self.import_owner_activity()
                    self.import_operational_data()
        self.stdout.write(self.style.SUCCESS("Legacy MetsIS data import completed."))

    def rows(self, table):
        try:
            with self.source.cursor() as cursor:
                cursor.execute(f'SELECT * FROM "{table}"')
                return cursor.fetchall()
        except UndefinedTable:
            self.stdout.write(self.style.WARNING(f"Source table {table!r} does not exist; skipped."))
            return []

    def import_users(self):
        for row in self.rows("users"):
            defaults = {
                "full_name": row.get("fullname") or row["id"],
                "password": row.get("password_hash") or "!",
                "totp_secret": row.get("totp_secret"),
                "visible": bool(row.get("ivisible", False)),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            }
            user = User.objects.filter(id=row["id"]).first()
            if user is None:
                user = User.objects.create(id=row["id"], default_organization=self.organization, **defaults)
            else:
                for field, value in defaults.items():
                    setattr(user, field, value)
                user.save(update_fields=tuple(defaults))
                OrganizationMembership.objects.get_or_create(organization=self.organization, user=user)
        for row in self.rows("privileges"):
            if User.objects.filter(id=row["user_id"]).exists():
                Privilege.objects.get_or_create(user_id=row["user_id"], code=row["id"])
        admin_ids = Privilege.objects.filter(code="ADMIN").values_list("user_id", flat=True)
        User.objects.filter(id__in=admin_ids).update(is_staff=True, is_superuser=True)

    def import_owner_statuses(self):
        for row in self.rows("owner_statuses"):
            OwnerStatus.objects.update_or_create(
                id=row["id"],
                defaults={
                    "days_out_of_search": row.get("days_out_of_search", 0),
                    "color_hex": row.get("reason_color", "ed7a6f"),
                    "protected": bool(row.get("protected", False)),
                },
            )

    def import_owners_and_cadastres(self):
        for row in self.rows("owners"):
            Owner.objects.update_or_create(
                id=row["id"],
                defaults={
                    "name": row.get("name") or row["id"],
                    "type": row.get("type") or "",
                    "phone": row.get("phone") or "",
                    "email": row.get("email") or "",
                    "address": row.get("address") or "",
                    "info": row.get("info") or "",
                    "out_of_admin_search_from": legacy_time(row.get("out_of_admin_search_from")),
                    "out_of_admin_search_to": legacy_time(row.get("out_of_admin_search_to")),
                    "out_of_admin_search_reason": row.get("out_of_admin_search_reason") or "",
                    "status": row.get("status") or "",
                    "status_set_at": legacy_time(row.get("status_set_at")),
                    "assignee_id": row.get("caller_id") if User.objects.filter(id=row.get("caller_id")).exists() else None,
                    "last_cadastre_list_refresh": legacy_time(row.get("last_cadastre_list_refresh")),
                },
            )
        for row in self.rows("cadastres"):
            Cadastre.objects.update_or_create(
                id=row["id"],
                defaults={
                    "name": row.get("name") or "",
                    "municipality": row.get("municipality") or "",
                    "county": row.get("county") or "",
                    "address": row.get("address") or "",
                    "registration_number": row.get("reg_nr") or "",
                    "type": row.get("type") or "",
                    "postal": row.get("postal") or "",
                    "polygon": parse_json(row.get("polygon"), []),
                    "centroid": parse_json(row.get("centroid"), {}),
                    "area": row.get("area"),
                    "arable_area": row.get("arable_area"),
                    "yard_area": row.get("yard_area"),
                    "meadow_area": row.get("meadow_area"),
                    "forest_area": row.get("forest_area"),
                    "underwater_area": row.get("underwater_area"),
                    "buildings_area": row.get("buildings_area"),
                    "other_area": row.get("other_area"),
                    "marked": bool(row.get("marked", False)),
                    "our_price": str(row.get("our_price") or ""),
                    "owners_price": str(row.get("owners_price") or ""),
                    "mk_date": legacy_time(row.get("mk_date")),
                },
            )
        for row in self.rows("owner_cadastre"):
            if Owner.objects.filter(id=row["owner_id"]).exists() and Cadastre.objects.filter(id=row["cadastre_id"]).exists():
                OwnerCadastre.objects.get_or_create(owner_id=row["owner_id"], cadastre_id=row["cadastre_id"])
        for row in self.rows("cadastre_labels"):
            if Cadastre.objects.filter(id=row["cadastre_id"]).exists():
                CadastreLabel.objects.get_or_create(cadastre_id=row["cadastre_id"], code=row["id"])
        for row in self.rows("cadastre_sub_parts"):
            if Cadastre.objects.filter(id=row["cadastre_id"]).exists():
                CadastreSubPart.objects.update_or_create(
                    cadastre_id=row["cadastre_id"], sub_part_code=row.get("sub_part_code"),
                    defaults={"tree_type_code": row.get("tree_type_code") or "", "area": row.get("area"), "polygon": parse_json(row.get("polygon"), [])},
                )
        for row in self.rows("cadastre_notifications"):
            if Cadastre.objects.filter(id=row["cadastre_id"]).exists():
                CadastreNotification.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "notification_number": row["notification_number"], "cadastre_subpart_code": row.get("cadastre_subpart_code"),
                        "work_code": row.get("work_code") or "", "state": row.get("state"), "damage_code": row.get("damage_code") or "",
                        "decision": row.get("decision") or "", "registration_date": legacy_time(row.get("registration_date")),
                        "confirmation_date": legacy_time(row.get("confirmation_date")), "area": row.get("area"),
                        "amount_to_be_cut": row.get("amount_to_be_cut"), "cadastre_id": row["cadastre_id"],
                        "archived": bool(row.get("archived", False)), "archive_date": legacy_time(row.get("archive_date")),
                    },
                )
        for row in self.rows("forest_registry_features"):
            if Cadastre.objects.filter(id=row["cadastre_id"]).exists():
                ForestRegistryFeature.objects.update_or_create(
                    source_layer=row["source_layer"], source_id=row["source_id"],
                    defaults={
                        "cadastre_id": row["cadastre_id"], "subpart_code": row.get("subpart_code"), "title": row.get("title") or "",
                        "work_code": row.get("work_code") or "", "decision": row.get("decision") or "", "area": row.get("area"),
                        "volume": row.get("volume"), "event_date": legacy_time(row.get("event_date")),
                        "attributes": parse_json(row.get("attributes"), {}), "geometry": parse_json(row.get("geometry"), {}),
                    },
                )

    def import_owner_activity(self):
        for row in self.rows("owner_log"):
            if Owner.objects.filter(id=row["owner_id"]).exists() and User.objects.filter(id=row["creator"]).exists():
                OwnerLog.objects.update_or_create(
                    id=row["id"],
                    defaults={"owner_id": row["owner_id"], "creator_id": row["creator"], "message": row["message"], "created_at": legacy_time(row.get("timestamp"))},
                )
        for row in self.rows("user_owner_status_change_statistics"):
            if User.objects.filter(id=row["user_id"]).exists():
                OwnerStatusChange.objects.get_or_create(
                    user_id=row["user_id"], timestamp=legacy_time(row.get("timestamp")),
                    defaults={"from_status": row.get("from_status") or "", "to_status": row.get("to_status") or ""},
                )
        for row in self.rows("owner_followings"):
            if User.objects.filter(id=row["user_id"]).exists() and Owner.objects.filter(id=row["owner_id"]).exists():
                OwnerFollowing.objects.get_or_create(owner_id=row["owner_id"], user_id=row["user_id"])

    def import_operational_data(self):
        for row in self.rows("persons_dump"):
            PersonDump.objects.update_or_create(id=row["id"], defaults={key: row.get(key) or "" for key in ("source", "name", "phone", "address", "code")})
        for row in self.rows("reminders"):
            owner_id = row.get("owner_id") if Owner.objects.filter(id=row.get("owner_id")).exists() else None
            creator_id = row.get("creator") if User.objects.filter(id=row.get("creator")).exists() else None
            Reminder.objects.update_or_create(
                id=row["id"],
                defaults={"due_time": legacy_time(row["duetime"]), "text": row.get("reminder_text") or "", "owner_id": owner_id, "creator_id": creator_id,
                          "created_time": legacy_time(row.get("created_time")) or legacy_time(row["duetime"]), "cadastre": row.get("cadastre") or "", "property_name": row.get("property_name") or ""},
            )
        for row in self.rows("application_messages"):
            recipient = row.get("recipient") if User.objects.filter(id=row.get("recipient")).exists() else None
            ApplicationMessage.objects.update_or_create(id=row["id"], defaults={"text": row["message_text"], "admin_message": bool(row.get("admin_message", False)), "recipient_id": recipient})
        for row in self.rows("messages"):
            sender = row.get("sender") if User.objects.filter(id=row.get("sender")).exists() else None
            recipient = row.get("recipient") if User.objects.filter(id=row.get("recipient")).exists() else None
            DirectMessage.objects.update_or_create(id=row["id"], defaults={"text": row["message"], "created_at": legacy_time(row["created_at"]), "noticed_at": legacy_time(row.get("noticed_at")), "sender_id": sender, "recipient_id": recipient})
        for row in self.rows("contracts"):
            Contract.objects.update_or_create(id=row["id"], defaults={"document": row.get("contract"), "base_id": row.get("base_id") or ""})
        for row in self.rows("contract_history"):
            ContractHistory.objects.update_or_create(
                id=row["id"],
                defaults={"sellers": row["sellers"], "buyer": row["buyer"], "contract_number": row["contract_no"], "created_at": legacy_time(row["created"]), "data": parse_json(row["data"], {}), "cadastres": row.get("cadastres") or ""},
            )
