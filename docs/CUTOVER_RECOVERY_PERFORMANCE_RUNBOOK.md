# ForestIQ-D cutover, recovery and performance runbook

This runbook is the operator gate for legacy MetsIS/Java -> ForestIQ-D Django cutover. It covers migration, reconciliation, backup/restore, performance and rollback. Production routing must not be switched until every **GO** gate below is green.

## Recovery objectives and evidence

Project recovery objectives:

- **Database RPO:** <= 24 hours. Take an explicit pre-cutover backup immediately before the write freeze even when the hosting provider also has managed backups.
- **Uploaded contract/media RPO:** <= 24 hours. Database and media backup timestamps must belong to the same cutover window.
- **RTO target:** <= 4 hours for restoring database + media to an isolated environment and completing smoke/reconciliation checks.
- Every backup and restore drill produces a JSON report. Store the report together with the backup artifact or in the incident/cutover ticket.

Create an auditable backup:

```bash
python scripts/backup_restore.py backup --output backups
```

The command creates a PostgreSQL custom-format dump, optionally archives `MEDIA_ROOT`, calculates SHA-256 checksums and writes a JSON manifest. Do not consider a backup usable merely because a file exists: a restore drill is the integrity gate.

Restore only into an isolated target database:

```bash
python scripts/backup_restore.py restore \
  --dump backups/forestiq-<timestamp>.dump \
  --sha256 <sha256-from-backup-manifest> \
  --target-database-url postgresql://.../forestiq_restore_drill \
  --report restore-report.json
```

The utility refuses to restore into the active `DATABASE_URL`, runs `pg_restore`, validates the restored database with `SELECT 1`, optionally restores media, and records duration/checksum evidence. For Render persistent-disk deployments, include the mounted media directory in `--media-path`; for S3/object storage, use the bucket's versioning/backup policy and retain the corresponding provider evidence alongside the DB manifest.

## Migration preparation and dry-run

1. Confirm `LEGACY_DATABASE_URL` is a **read-only** credential.
2. Run target Django migrations and application checks.
3. Create and verify a backup/restore drill.
4. Run the migration in dry-run mode; target writes are rolled back:

```bash
cd django_backend
python manage.py migrate_legacy_cutover \
  --organization <organization-id-or-slug> \
  --checkpoint ../cutover-checkpoint.json \
  --quarantine ../cutover-quarantine.jsonl
```

5. Review quarantine output. Any malformed source row is a **NO-GO** until corrected or explicitly resolved. Never silently discard a source row.
6. Re-run the same command until the dry-run succeeds. The underlying importer uses idempotent `update_or_create`/`get_or_create`; an interrupted run is resumed by safely replaying from the durable source of truth. `--resume` validates the checkpoint and does not bypass validation.

Only after dry-run success may the write run be executed:

```bash
python manage.py migrate_legacy_cutover \
  --organization <organization-id-or-slug> \
  --checkpoint ../cutover-checkpoint.json \
  --quarantine ../cutover-quarantine.jsonl \
  --confirm-write
```

## Automated reconciliation / GO-NO-GO

Run after every migration rehearsal and immediately before traffic switch:

```bash
python manage.py reconcile_legacy_cutover \
  --organization <organization-id-or-slug> \
  --output ../cutover-reconciliation.json \
  --max-count-delta 0 \
  --max-missing-ids 0
```

The report compares source/target counts and identity sets for users, owners, cadastres, owner-cadastre relationships, subparts, notices, contracts and audit entries, and reports the Django-native deal aggregate. Default thresholds are intentionally zero-tolerance. Any missing source identity or count delta is a **NO-GO**; inspect the drill-down IDs before continuing.

## Performance and soak gate

Critical read paths must remain bounded under concurrent access. Run the HTTP profile against a realistic restored dataset:

```bash
FORESTIQ_SOAK_TOKEN=<access-token> python scripts/soak_profile.py \
  --base-url https://candidate.example \
  --path /api/v1/services/map/cadastres \
  --path /api/v1/services/map/tiles/cadastres/8/145/83.pbf \
  --requests 500 \
  --concurrency 16 \
  --p95-ms 750 \
  --p99-ms 1500 \
  --max-error-rate 0.01 \
  --output soak-profile.json
```

The command exits non-zero when p95, p99 or the error budget is exceeded. During a long WFS/Celery rehearsal also capture:

- worker RSS before/after and peak RSS;
- PostgreSQL active/idle connection counts and connection-pool saturation;
- Celery queue depth, retries and failed task count;
- `DataSyncRun` overlap behaviour: a second single-flight import must be skipped/reused rather than creating duplicate writes;
- WFS retry/backoff behaviour with a controlled transient failure;
- MVT/GeoJSON request p95/p99 from the same restored dataset.

A growing RSS trend, unbounded DB connections, duplicate overlapping imports, unbounded queue growth or a latency/error budget failure is **NO-GO**.

## Production cutover sequence

1. **Preflight:** deployment version recorded; migrations/tests green; backup restore drill successful; dry-run migration and reconciliation green; soak profile green.
2. **Write freeze:** stop writes in the Java/MetsIS application. Keep reads available if operationally useful. Record exact freeze timestamp.
3. **Final migration:** run `migrate_legacy_cutover --confirm-write`. If the source changed after the last rehearsal, replay safely from source; idempotency prevents duplicates.
4. **Final reconciliation:** zero-tolerance reconciliation must return `go: true`.
5. **Django smoke test:** authenticate; open owner/cadastre/map; create/update a permitted non-destructive test record; verify reminders/messages; verify admin integrations; verify a contract/media read; verify Keycloak login and organization boundary.
6. **Route switch:** switch Render/custom-domain route or DNS to ForestIQ-D. Record timestamp and old/new target.
7. **Observe:** monitor HTTP 5xx/4xx anomaly rate, p95/p99, DB connections, Celery failures/backlog, integration freshness and authentication failures.
8. Keep the legacy application frozen and recoverable for the agreed rollback window; do not resume dual writes.

## Rollback

Rollback immediately when any of these occurs after switch: data reconciliation failure, organization-boundary/security failure, sustained critical 5xx/auth failure, corrupted document access, or operational performance outside the accepted budget.

1. Stop ForestIQ-D writes / maintenance-mode the candidate.
2. Switch route/DNS back to the frozen legacy application.
3. If legacy remained frozen and authoritative, resume its writes only after route restoration is confirmed.
4. Preserve the failed Django database and logs for investigation; do not overwrite evidence.
5. If the Django target itself must be recovered, restore the verified pre-cutover dump/media into a **new isolated database/storage target**, verify it, and only then promote it.
6. Record rollback cause, correlation IDs, migration checkpoint, reconciliation report, backup manifest and restore report.

## Trial evidence checklist

A production cutover is **NO-GO** unless at least one rehearsal has produced all of the following artifacts:

- successful dry-run checkpoint;
- empty/resolved quarantine file;
- `go: true` reconciliation report;
- database backup JSON manifest + SHA-256;
- successful isolated restore JSON report within the RTO target;
- performance/soak JSON report within budgets;
- smoke-test notes including auth, owner/cadastre/map, documents and integrations;
- tested route-switch and rollback steps.
