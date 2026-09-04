#!/usr/bin/env python3
"""Long-running ForestIQ load profile with enforceable p95/p99 and error budgets."""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import statistics
import sys
import time
from dataclasses import dataclass

import requests

try:
    import psycopg
except ImportError:  # pragma: no cover - dependency is present in the backend image
    psycopg = None


@dataclass
class Sample:
    name: str
    latency_ms: float
    status: int


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percentile_value))))
    return ordered[index]


def request_once(base_url: str, path: str, token: str) -> Sample:
    started = time.perf_counter()
    try:
        response = requests.get(
            f"{base_url.rstrip('/')}{path}",
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=float(os.getenv("FORESTIQ_SOAK_HTTP_TIMEOUT_SECONDS", "30")),
        )
        status_code = response.status_code
        response.content
    except requests.RequestException:
        status_code = 599
    return Sample(path, (time.perf_counter() - started) * 1000.0, status_code)


def overlapping_sync_probe(base_url: str, token: str, cadastre_id: str) -> tuple[int, int]:
    url = f"{base_url.rstrip('/')}/services/admin/cadastres/{cadastre_id}/sync"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    def trigger() -> int:
        try:
            return requests.post(url, headers=headers, timeout=30).status_code
        except requests.RequestException:
            return 599

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        first, second = executor.map(lambda _: trigger(), range(2))
    return first, second


def database_connections(database_url: str) -> int | None:
    if not database_url or psycopg is None:
        return None
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from pg_stat_activity where datname = current_database()")
            return int(cursor.fetchone()[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("FORESTIQ_SOAK_BASE_URL", "http://localhost:8000/api"))
    parser.add_argument("--duration-seconds", type=int, default=int(os.getenv("FORESTIQ_SOAK_DURATION_SECONDS", "900")))
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("FORESTIQ_SOAK_CONCURRENCY", "8")))
    parser.add_argument("--cadastre-id", default=os.getenv("FORESTIQ_SOAK_CADASTRE_ID", ""))
    args = parser.parse_args()

    token = os.getenv("FORESTIQ_SOAK_TOKEN", "")
    paths = [
        os.getenv("FORESTIQ_SOAK_MVT_PATH", "/services/map/tiles/cadastres/7/72/39.pbf"),
        os.getenv("FORESTIQ_SOAK_GEOJSON_PATH", "/services/map/cadastres?limit=250"),
    ]
    p95_budget = float(os.getenv("FORESTIQ_SOAK_P95_MS", "750"))
    p99_budget = float(os.getenv("FORESTIQ_SOAK_P99_MS", "1500"))
    max_error_rate = float(os.getenv("FORESTIQ_SOAK_MAX_ERROR_RATE", "0.01"))
    max_db_connections = int(os.getenv("FORESTIQ_SOAK_MAX_DB_CONNECTIONS", "50"))
    database_url = os.getenv("DATABASE_URL", "")

    started = time.monotonic()
    samples: list[Sample] = []
    max_connections_seen = 0
    sync_probe_failures = 0
    next_sync_probe = started
    next_db_probe = started

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        while time.monotonic() - started < args.duration_seconds:
            futures = [executor.submit(request_once, args.base_url, paths[index % len(paths)], token) for index in range(args.concurrency)]
            samples.extend(future.result() for future in futures)

            now = time.monotonic()
            if args.cadastre_id and now >= next_sync_probe:
                statuses = overlapping_sync_probe(args.base_url, token, args.cadastre_id)
                # Single-flight should accept at most one overlapping dispatch. 202/409 in either order is valid.
                if sorted(statuses) != [202, 409]:
                    sync_probe_failures += 1
                next_sync_probe = now + 60
            if database_url and now >= next_db_probe:
                current = database_connections(database_url)
                max_connections_seen = max(max_connections_seen, current or 0)
                next_db_probe = now + 30

    latencies = [sample.latency_ms for sample in samples]
    errors = [sample for sample in samples if not (200 <= sample.status < 400)]
    p95 = percentile(latencies, 0.95)
    p99 = percentile(latencies, 0.99)
    error_rate = len(errors) / len(samples) if samples else 1.0

    print(f"requests={len(samples)}")
    print(f"mean_ms={statistics.fmean(latencies) if latencies else 0:.2f}")
    print(f"p95_ms={p95:.2f}")
    print(f"p99_ms={p99:.2f}")
    print(f"error_rate={error_rate:.4f}")
    print(f"sync_probe_failures={sync_probe_failures}")
    print(f"max_db_connections={max_connections_seen}")

    failures = []
    if p95 > p95_budget:
        failures.append(f"p95 {p95:.2f}ms > {p95_budget:.2f}ms")
    if p99 > p99_budget:
        failures.append(f"p99 {p99:.2f}ms > {p99_budget:.2f}ms")
    if error_rate > max_error_rate:
        failures.append(f"error rate {error_rate:.4f} > {max_error_rate:.4f}")
    if sync_probe_failures:
        failures.append(f"{sync_probe_failures} overlapping Celery/WFS sync probes violated single-flight")
    if database_url and max_connections_seen > max_db_connections:
        failures.append(f"DB connections {max_connections_seen} > {max_db_connections}")

    if failures:
        print("SOAK GATE FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("SOAK GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
