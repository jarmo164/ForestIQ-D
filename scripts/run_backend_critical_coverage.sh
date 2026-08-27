#!/usr/bin/env bash
# Measure high-impact backend code paths that protect data isolation and sync reliability.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backend_dir="${repo_root}/django_backend"
report_dir="${repo_root}/coverage"
threshold="${FORESTIQ_BACKEND_CRITICAL_COVERAGE_MIN:-70}"

mkdir -p "${report_dir}"
cd "${backend_dir}"

python -m coverage erase
python -m coverage run \
  --branch \
  --source=api.health,forestry.services.single_flight,forestry.services.tile_cache,forestry.services.wfs_client,forestry.services.metsaregister_full_import,forestry.tasks \
  manage.py test --verbosity 2
python -m coverage report --precision=2 --fail-under="${threshold}"
python -m coverage xml -o "${report_dir}/backend-critical.xml"
