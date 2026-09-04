#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_DATABASE_URL:?TARGET_DATABASE_URL is required}"
: "${BACKUP_PATH:?BACKUP_PATH must point to one backup directory}"

if [[ "${FORESTIQ_RESTORE_CONFIRM:-}" != "RESTORE_NON_PRODUCTION" ]]; then
  echo "Refusing restore. Set FORESTIQ_RESTORE_CONFIRM=RESTORE_NON_PRODUCTION for an isolated restore target." >&2
  exit 2
fi

if [[ "${DATABASE_URL:-}" == "${TARGET_DATABASE_URL}" && -n "${DATABASE_URL:-}" ]]; then
  echo "Refusing restore because TARGET_DATABASE_URL equals DATABASE_URL." >&2
  exit 2
fi

DB_FILE="${BACKUP_PATH}/postgres.dump"
MEDIA_FILE="${BACKUP_PATH}/media.tar.gz"
MANIFEST="${BACKUP_PATH}/manifest.sha256"
RESTORE_MEDIA_ROOT="${FORESTIQ_RESTORE_MEDIA_ROOT:-./restore-media}"
REPORT="${BACKUP_PATH}/restore-report-$(date -u +%Y%m%dT%H%M%SZ).txt"

for file in "${DB_FILE}" "${MEDIA_FILE}" "${MANIFEST}"; do
  [[ -f "${file}" ]] || { echo "Missing backup artifact: ${file}" >&2; exit 3; }
done

(
  cd "${BACKUP_PATH}"
  sha256sum --check manifest.sha256
)
pg_restore --list "${DB_FILE}" >/dev/null

started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
pg_restore --clean --if-exists --no-owner --no-acl --dbname="${TARGET_DATABASE_URL}" "${DB_FILE}"
rm -rf "${RESTORE_MEDIA_ROOT}"
mkdir -p "${RESTORE_MEDIA_ROOT}"
tar -C "${RESTORE_MEDIA_ROOT}" -xzf "${MEDIA_FILE}"

# A restored Django schema must at least expose the tenancy and core forestry tables.
psql "${TARGET_DATABASE_URL}" -v ON_ERROR_STOP=1 -Atc \
  "select case when to_regclass('public.organizations') is not null and to_regclass('public.cadastres') is not null then 'OK' else 'MISSING_CORE_TABLES' end" \
  | grep -qx 'OK'

organizations="$(psql "${TARGET_DATABASE_URL}" -Atc 'select count(*) from organizations')"
cadastres="$(psql "${TARGET_DATABASE_URL}" -Atc 'select count(*) from cadastres')"
owners="$(psql "${TARGET_DATABASE_URL}" -Atc 'select count(*) from owners')"
finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat >"${REPORT}" <<EOF
restore_started_at=${started}
restore_finished_at=${finished}
target=NON_PRODUCTION
checksum_validation=OK
pg_restore_catalog=OK
core_table_validation=OK
organizations=${organizations}
owners=${owners}
cadastres=${cadastres}
media_restore_root=${RESTORE_MEDIA_ROOT}
EOF

printf 'ForestIQ restore drill completed. Audit report: %s\n' "${REPORT}"
