#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${1:?usage: run_restore_drill.sh <backup-dir> [report-path]}"
REPORT="${2:-./restore-audit-$(date -u +%Y%m%dT%H%M%SZ).json}"
CONTAINER="forestiq-restore-drill-$$"
PORT="${FORESTIQ_RESTORE_DRILL_PORT:-55432}"
MEDIA_DIR="$(mktemp -d -t forestiq-restore-media.XXXXXX)"

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$MEDIA_DIR"
}
trap cleanup EXIT

docker run -d --rm --name "$CONTAINER" \
  -e POSTGRES_PASSWORD=forestiq \
  -e POSTGRES_DB=forestiq_restore \
  -p "127.0.0.1:${PORT}:5432" \
  postgis/postgis:16-3.4 >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER" pg_isready -U postgres -d forestiq_restore >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$CONTAINER" pg_isready -U postgres -d forestiq_restore >/dev/null
RESTORE_DATABASE_URL="postgresql://postgres:forestiq@127.0.0.1:${PORT}/forestiq_restore" \
RESTORE_MEDIA_ROOT="$MEDIA_DIR" \
RESTORE_AUDIT_REPORT="$REPORT" \
python3 scripts/forestiq_backup.py restore "$BACKUP_DIR"

echo "Restore drill succeeded. Audit: $REPORT"
