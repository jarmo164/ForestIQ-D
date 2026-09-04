# ForestIQ backup, restore and recovery drill

## Recovery targets

| Data | Recovery point objective (RPO) | Recovery time objective (RTO) |
|---|---:|---:|
| PostgreSQL | <= 15 minutes on paid Render Postgres PITR | <= 4 hours |
| Media files | <= 24 hours from Render persistent-disk snapshots | <= 4 hours |
| Portable logical backup | created before risky migrations/releases and on demand | <= 4 hours |

The RPO values are operational targets, not an application guarantee. Production must use a paid Render Postgres plan for PITR. Render persistent disks take an automatic snapshot every 24 hours and retain snapshots for at least seven days. A Render cron job cannot access a persistent disk, so media recovery is intentionally based on the disk snapshot facility rather than a second cron process that cannot see `/app/media`.

## Portable backup

The repository also includes `scripts/forestiq_backup.py`. It creates an additional portable pair:

- PostgreSQL custom-format dump (`pg_dump -Fc`)
- compressed media archive
- SHA-256 checksums, sizes and media-file counts in `manifest.json`
- `pg_restore --list` validation before the backup is considered usable

Example:

```bash
DATABASE_URL='postgresql://...' \
FORESTIQ_MEDIA_ROOT=/app/media \
FORESTIQ_BACKUP_DIR=/secure/offsite/forestiq \
python3 scripts/forestiq_backup.py backup
```

Do not treat a directory on the same Render persistent disk as the only backup copy. A portable backup destination must be copied off the production disk after creation. Render PITR/disk snapshots remain the primary automated recovery mechanisms.

## Integrity check

```bash
python3 scripts/forestiq_backup.py verify /path/to/backup/20260904T120000Z
```

The command fails if either SHA-256 differs, if PostgreSQL cannot list the dump, or if the media archive is unreadable.

## Restore into an isolated target

The restore command deliberately refuses to use the current production `DATABASE_URL` or media root.

```bash
RESTORE_DATABASE_URL='postgresql://.../forestiq_restore' \
RESTORE_MEDIA_ROOT=/tmp/forestiq-restore-media \
RESTORE_AUDIT_REPORT=./restore-audit.json \
python3 scripts/forestiq_backup.py restore /path/to/backup/20260904T120000Z
```

A successful report records checksum validation, `django_migrations` presence, restored media count/size and start/finish timestamps. A failed drill still writes the report with `status=FAILED` and the error.

## Reproducible local restore drill

With Docker available, run:

```bash
./scripts/run_restore_drill.sh /path/to/backup/20260904T120000Z
```

The script starts a disposable PostGIS container, restores the database into that isolated instance, restores media into a temporary directory, executes integrity checks, writes the audit report, and removes the disposable environment.

Run this drill after backup/restore code changes and at least monthly for production operations. Store the resulting JSON reports with operational records.

## Render recovery procedure

1. **Database:** use Render Postgres PITR to create a separate recovery instance at the desired timestamp. Validate that instance before changing application connection strings.
2. **Media:** restore a persistent-disk snapshot from the service's Disks page. Because a disk snapshot restore replaces the whole disk state, confirm the selected timestamp first.
3. Run application smoke checks and compare expected owner/cadastre/contract counts.
4. Record recovery timestamp, operator, restored DB instance, disk snapshot timestamp and application smoke-check result in the restore audit record.
5. Switch traffic only after the isolated database recovery and media checks pass.

## Pre-release checklist

Before a migration or other destructive change:

- confirm the database has PITR available;
- confirm a recent media disk snapshot exists;
- create and verify a portable logical backup when the change is high-risk;
- run a restore drill if backup format/schema handling changed;
- never validate a restore by overwriting production.
