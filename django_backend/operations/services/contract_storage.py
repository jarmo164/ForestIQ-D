"""Contract-document storage reconciliation for local and S3-compatible backends."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.files.storage import Storage, default_storage
from django.db.models import Q, QuerySet

from operations.models import Contract


CONTRACT_STORAGE_PREFIX = "contracts"


@dataclass
class ContractStorageReport:
    """A serializable report of a document-store comparison or repair."""

    dry_run: bool
    database_objects: list[str]
    legacy_binary_contracts: list[str]
    missing_objects: list[str]
    orphaned_objects: list[str]
    restored_from_database: list[str]
    migrated_legacy_binaries: list[str]
    deleted_orphans: list[str]
    unrepaired_missing_objects: list[str]

    def data(self) -> dict:
        return {
            "dryRun": self.dry_run,
            "databaseObjects": self.database_objects,
            "legacyBinaryContracts": self.legacy_binary_contracts,
            "missingObjects": self.missing_objects,
            "orphanedObjects": self.orphaned_objects,
            "restoredFromDatabase": self.restored_from_database,
            "migratedLegacyBinaries": self.migrated_legacy_binaries,
            "deletedOrphans": self.deleted_orphans,
            "unrepairedMissingObjects": self.unrepaired_missing_objects,
        }


def _storage_objects(storage: Storage, root: str = CONTRACT_STORAGE_PREFIX) -> set[str]:
    """Return object names below the dedicated contract prefix only."""

    try:
        directories, files = storage.listdir(root)
    except (FileNotFoundError, NotImplementedError):
        return set()
    objects = {str(PurePosixPath(root, file)) for file in files}
    for directory in directories:
        objects.update(_storage_objects(storage, str(PurePosixPath(root, directory))))
    return objects


def _contract_queryset(contracts: Iterable[Contract] | QuerySet[Contract] | None) -> list[Contract]:
    if contracts is None:
        return list(Contract.objects.exclude(document_file="").exclude(document_file__isnull=True))
    return list(contracts)


def _legacy_binary_contracts(contracts: Iterable[Contract] | QuerySet[Contract] | None) -> list[Contract]:
    if contracts is None:
        return list(Contract.objects.filter(document__isnull=False).filter(Q(document_file__isnull=True) | Q(document_file="")))
    return [contract for contract in contracts if contract.document and not contract.document_file]


def reconcile_contract_storage(*, apply: bool = False, storage: Storage | None = None, contracts: Iterable[Contract] | QuerySet[Contract] | None = None) -> ContractStorageReport:
    """Compare stored contract records with their document objects.

    Repairs are deliberately opt-in. A repair restores a missing named object from
    its retained database binary, migrates a legacy database-only binary to the
    configured storage backend, and removes orphan objects only under ``contracts/``.
    """

    storage = storage or default_storage
    database_contracts = _contract_queryset(contracts)
    legacy_contracts = _legacy_binary_contracts(contracts)
    database_names = {contract.document_file.name for contract in database_contracts if contract.document_file.name}
    stored_names = _storage_objects(storage)
    missing_names = sorted(database_names - stored_names)
    orphaned_names = sorted(stored_names - database_names)
    missing_contracts = {contract.document_file.name: contract for contract in database_contracts if contract.document_file.name in missing_names}
    report = ContractStorageReport(
        dry_run=not apply,
        database_objects=sorted(database_names),
        legacy_binary_contracts=sorted(str(contract.id) for contract in legacy_contracts),
        missing_objects=missing_names,
        orphaned_objects=orphaned_names,
        restored_from_database=[],
        migrated_legacy_binaries=[],
        deleted_orphans=[],
        unrepaired_missing_objects=[],
    )
    if not apply:
        return report

    for name, contract in missing_contracts.items():
        if contract.document:
            storage.save(name, ContentFile(bytes(contract.document)))
            report.restored_from_database.append(name)
        else:
            report.unrepaired_missing_objects.append(name)

    for contract in legacy_contracts:
        filename = f"contract-{contract.id}.pdf"
        name = contract.document_file.field.generate_filename(contract, filename)
        saved_name = storage.save(name, ContentFile(bytes(contract.document)))
        contract.document_file.name = saved_name
        contract.save(update_fields=("document_file",))
        report.migrated_legacy_binaries.append(saved_name)

    for name in orphaned_names:
        storage.delete(name)
        report.deleted_orphans.append(name)

    return report


__all__ = ["CONTRACT_STORAGE_PREFIX", "ContractStorageReport", "reconcile_contract_storage"]
