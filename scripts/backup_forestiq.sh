#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"

BACKUP_DIR="${FORESTIQ_BACKUP_DIR:-./backups}"
MEDIA_ROOT="${FORESTIQ_MEDIA_ROOT:-./django_backend/media}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="${BACKUP_DIR}/${STAMP}"
mkdir -p "${TARGET}"

DB_FILE="${TARGET}/postgres.dump"
MEDIA_FILE="${TARGET}/media.tar.gz"
MANIFEST="${TARGET}/manifest.sha256"
REPORT="${TARGET}/backup-report.txt"

started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
pg_dump --format=custom --no-owner --no-acl --dbname="${DATABASE_URL}" --file="${DB_FILE}"

if [[ -d "${MEDIA_ROOT}" ]]; then
  tar -C "${MEDIA_ROOT}" -czf "${MEDIA_FILE}" .
else
  mkdir -p "${TARGET}/empty-media"
  tar -C "${TARGET}/empty-media" -czf "${MEDIA_FILE}" .
fi

(
  cd "${TARGET}"
  sha256sum postgres.dump media.tar.gz > manifest.sha256
)

pg_restore --list "${DB_FILE}" >/dev/null
sha256sum --check "${MANIFEST}" >/dev/null
finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat >"${REPORT}" <<EOF
backup_id=${STAMP}
started_at=${started}
finished_at=${finished}
database_file=postgres.dump
media_file=media.tar.gz
manifest_file=manifest.sha256
database_bytes=$(wc -c <"${DB_FILE}" | tr -d ' ')
media_bytes=$(wc -c <"${MEDIA_FILE}" | tr -d ' ')
pg_restore_catalog=OK
checksum_validation=OK
EOF

printf 'ForestIQ backup completed: %s\n' "${TARGET}"
