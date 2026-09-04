# ForestIQ backup and restore runbook

## Objectives

Production recovery targets are **RPO 24 hours** and **RTO 4 hours**. Database and local media backups must be treated as one recovery set. S3-backed contract objects remain covered by the storage provider's versioning/backup policy and `reconcile_contract_storage` must be run after a restore.

## Backup

Run from a trusted operations host with PostgreSQL client tools installed:

```bash
export DATABASE_URL='postgresql://...'
export FORESTIQ_MEDIA_ROOT='/var/data/forestiq/media'
export FORESTIQ_BACKUP_DIR='/var/backups/forestiq'
bash scripts/backup_forestiq.sh
```

Each timestamped directory contains:

- `postgres.dump` — PostgreSQL custom-format dump;
- `media.tar.gz` — Render persistent-disk media snapshot;
- `manifest.sha256` — checksums covering both artifacts;
- `backup-report.txt` — timestamps, artifact sizes and validation results.

A backup is not valid unless `pg_restore --list` and the SHA-256 manifest both validate successfully.

## Restore drill

Restores are intentionally blocked unless the operator explicitly confirms that the target is isolated from production.

```bash
export TARGET_DATABASE_URL='postgresql://.../forestiq_restore_drill'
export BACKUP_PATH='/var/backups/forestiq/20260904T120000Z'
export FORESTIQ_RESTORE_MEDIA_ROOT='/tmp/forestiq-restore-media'
export FORESTIQ_RESTORE_CONFIRM='RESTORE_NON_PRODUCTION'
bash scripts/restore_forestiq.sh
```

The restore command refuses to run when `TARGET_DATABASE_URL` equals `DATABASE_URL`. It verifies checksums before writing, restores PostgreSQL with `pg_restore`, extracts media into a separate location, validates core tables and writes a timestamped `restore-report-*.txt` with organization, owner and cadastre counts.

After every restore drill:

1. run Django migrations in check mode and application smoke tests against the restored database;
2. run `python manage.py reconcile_contract_storage` (dry-run first) if contracts use object storage;
3. compare restored organization/owner/cadastre/contract counts against the source backup report or production reconciliation report;
4. retain the restore report with the backup set for audit.

## Render operations

Render PostgreSQL managed backups and persistent disks are separate failure domains. Scheduled platform database backups do not replace the application-level media archive. Store the generated recovery set outside the Render service disk so loss of that disk cannot remove both production media and its backup.

The restore drill should be executed at least quarterly and after material database/storage architecture changes. A failed drill is an operational incident: keep the failed report, correct the cause, and repeat the drill before declaring the backup chain healthy.
