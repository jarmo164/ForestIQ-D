"""Small explicit serializers for the legacy ForestIQ REST contract."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from accounts.models import User
from forestry.models import Cadastre, CadastreNotification, CadastreSubPart, Owner, OwnerLog, OwnerStatus
from operations.models import DirectMessage, Reminder


def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    return value


def user_data(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": user.id, "name": user.full_name}


def owner_summary(owner: Owner) -> dict:
    return {
        "id": owner.id,
        "name": owner.name,
        "version": owner.version,
        "status": owner.status or None,
        "statusSetAt": json_value(owner.status_set_at),
        "assignee": user_data(owner.assignee),
        "phone": owner.phone or None,
    }


def owner_data(owner: Owner) -> dict:
    payload = owner_summary(owner)
    payload.update(
        {
            "type": owner.type or None,
            "email": owner.email or None,
            "address": owner.address or None,
            "info": owner.info or None,
            "lastCadastreListRefresh": json_value(owner.last_cadastre_list_refresh),
            "cadastres": [cadastre_summary(cadastre) for cadastre in owner.cadastres.all()],
        }
    )
    return payload


def cadastre_summary(cadastre: Cadastre) -> dict:
    return {
        "id": cadastre.id,
        "name": cadastre.name or None,
        "type": cadastre.type or None,
        "marked": cadastre.marked,
        "area": json_value(cadastre.area),
        "centroid": cadastre.centroid or None,
        "polygon": cadastre.polygon or [],
    }


def subpart_data(part: CadastreSubPart) -> dict:
    return {
        "sectionNo": part.sub_part_code,
        "subPartCode": part.sub_part_code,
        "treeSpecies": part.tree_type_code or None,
        "treeTypeCode": part.tree_type_code or None,
        "area": json_value(part.area),
        "polygon": part.polygon or [],
    }


def cadastre_data(cadastre: Cadastre) -> dict:
    payload = cadastre_summary(cadastre)
    payload.update(
        {
            "municipality": cadastre.municipality or None,
            "county": cadastre.county or None,
            "address": cadastre.address or None,
            "regNr": cadastre.registration_number or None,
            "postal": cadastre.postal or None,
            "owners": [owner_summary(owner) for owner in cadastre.owners.select_related("assignee").all()],
            "labels": list(cadastre.labels.values_list("code", flat=True)),
            "cadastreSubParts": [subpart_data(part) for part in cadastre.sub_parts.all()],
            "mkDate": json_value(cadastre.mk_date),
        }
    )
    return payload


def notification_data(notification: CadastreNotification) -> dict:
    return {
        "notificationId": notification.id,
        "notificationNumber": notification.notification_number,
        "cadastreSubPartCode": notification.cadastre_subpart_code,
        "workCode": notification.work_code or None,
        "state": notification.state,
        "damageCode": notification.damage_code or None,
        "decision": notification.decision or None,
        "registrationDate": json_value(notification.registration_date),
        "confirmationDate": json_value(notification.confirmation_date),
        "area": json_value(notification.area),
        "amountToBeCut": json_value(notification.amount_to_be_cut),
        "cadastreNo": notification.cadastre_id,
        "archived": notification.archived,
        "archiveDate": json_value(notification.archive_date),
    }


def owner_log_data(entry: OwnerLog) -> dict:
    return {
        "id": entry.id,
        "message": entry.message,
        "createdAt": json_value(entry.created_at),
        "createdBy": entry.creator_id,
    }


def owner_status_data(status: OwnerStatus) -> dict:
    return {
        "id": status.id,
        "colorHex": status.color_hex,
        "durationDays": status.days_out_of_search,
        "protectedStatus": status.protected,
    }


def reminder_data(reminder: Reminder) -> dict:
    return {
        "id": str(reminder.id),
        "owner": owner_summary(reminder.owner) if reminder.owner else None,
        "text": reminder.text,
        "dueTime": json_value(reminder.due_time),
        "creator": reminder.creator_id,
        "cadastre": reminder.cadastre or None,
        "propertyName": reminder.property_name or None,
    }


def message_data(message: DirectMessage) -> dict:
    return {
        "id": str(message.id),
        "message": message.text,
        "createdAt": json_value(message.created_at),
        "noticedAt": json_value(message.noticed_at),
        "sender": user_data(message.sender),
        "recipient": user_data(message.recipient),
    }
