# ForestIQ soak and load profile

`scripts/soak_test.py` is the long-running quality gate for the high-volume GIS and registry path. It exercises both Mapbox Vector Tile and bounded GeoJSON reads and can periodically send two overlapping cadastre synchronization requests to verify that Celery/WFS single-flight protection accepts only one run.

## Recommended profiles

Quick developer smoke profile:

```bash
FORESTIQ_SOAK_TOKEN='<jwt>' \
FORESTIQ_SOAK_CADASTRE_ID='17101:001:2307' \
python scripts/soak_test.py --duration-seconds 120 --concurrency 4
```

Release soak profile:

```bash
FORESTIQ_SOAK_BASE_URL='https://staging-api.example/api' \
FORESTIQ_SOAK_TOKEN='<jwt>' \
FORESTIQ_SOAK_CADASTRE_ID='17101:001:2307' \
DATABASE_URL='postgresql://...staging...' \
FORESTIQ_SOAK_DURATION_SECONDS=3600 \
FORESTIQ_SOAK_CONCURRENCY=16 \
python scripts/soak_test.py
```

Run the release profile only against an isolated staging organization whose WFS refreshes are safe to repeat.

## Default gate

The script exits non-zero when any of the following budgets are exceeded:

- p95 HTTP latency: 750 ms (`FORESTIQ_SOAK_P95_MS`);
- p99 HTTP latency: 1500 ms (`FORESTIQ_SOAK_P99_MS`);
- request error rate: 1% (`FORESTIQ_SOAK_MAX_ERROR_RATE`);
- PostgreSQL connections: 50 (`FORESTIQ_SOAK_MAX_DB_CONNECTIONS`) when `DATABASE_URL` is provided;
- overlapping synchronization probe does not resolve to exactly one `202 Accepted` and one `409 Conflict`.

The MVT and GeoJSON paths are configurable with `FORESTIQ_SOAK_MVT_PATH` and `FORESTIQ_SOAK_GEOJSON_PATH`. The selected tile should contain representative data; an empty ocean tile is not a meaningful load profile.

## What to capture

Archive the script stdout/stderr together with server Prometheus metrics for the test window. The release record should contain request count, mean, p95, p99, error rate, maximum observed DB connection count and synchronization probe failures. Memory growth is evaluated from the server's `process_resident_memory_bytes` metric over the same window; sustained growth after traffic stabilizes is a failed soak even when latency remains within budget.

A performance-budget failure blocks release until either the regression is fixed or a time-limited documented exception is approved under the repository quality-gate process.
