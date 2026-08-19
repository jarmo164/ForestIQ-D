#!/usr/bin/env python3
"""Import cadastral boundary polygons from the public cadastral WFS service."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "Andmed" / "kataster_ky_kehtiv_boundaries.csv"
DEFAULT_WFS_URL = "https://gsavalik.envir.ee/geoserver/kataster/wfs"
DEFAULT_WFS_TYPENAME = "kataster:ky_kehtiv"
CONTAINER_CSV = "/tmp/metsis_kataster_boundaries.csv"
CSV_COLUMNS = ["FID", "tunnus", "geom"]


def wfs_url(args: argparse.Namespace, start_index: int, result_type: str = "results") -> str:
    query = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": args.wfs_typename,
        "resultType": result_type,
    }
    if result_type == "results":
        query.update(
            {
                "outputFormat": "csv",
                "propertyName": "geom,tunnus",
                "count": str(args.wfs_page_size),
                "startIndex": str(start_index),
            }
        )
    return f"{args.wfs_url}?{urlencode(query)}"


def fetch_url_text(url: str, timeout: int) -> str:
    last_error = ""
    for attempt in range(1, 6):
        result = subprocess.run(
            ["curl", "-L", "-sS", "--fail", "--max-time", str(timeout), "-A", "metsis-cadastre-boundary-import/1.0", url],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout
        last_error = result.stderr.strip()
        time.sleep(attempt * 2)
    raise SystemExit(f"WFS request failed after retries: {last_error}")


def fetch_total_count(args: argparse.Namespace) -> int:
    body = fetch_url_text(wfs_url(args, 0, "hits"), args.wfs_timeout)
    root = ElementTree.fromstring(body)
    number_matched = root.attrib.get("numberMatched")
    if number_matched is None or number_matched.lower() == "unknown":
        raise SystemExit("WFS did not return a usable numberMatched value")
    return int(number_matched)


def fetch_boundaries(args: argparse.Namespace) -> Path:
    total_count = fetch_total_count(args)
    print(f"WFS reports {total_count} cadastre boundary rows", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    written_rows = 0
    start_index = args.wfs_start_index
    page_number = 0
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        while start_index < total_count:
            if args.wfs_max_pages is not None and page_number >= args.wfs_max_pages:
                break

            body = fetch_url_text(wfs_url(args, start_index), args.wfs_timeout)
            if "ExceptionReport" in body[:500] or "ServiceExceptionReport" in body[:500]:
                raise SystemExit(f"WFS returned an exception at startIndex={start_index}:\n{body[:1000]}")
            reader = csv.DictReader(body.splitlines())
            if reader.fieldnames is None:
                raise SystemExit(f"WFS returned an empty response at startIndex={start_index}")

            page_rows = 0
            for row in reader:
                writer.writerow(
                    {
                        "FID": row.get("FID", ""),
                        "tunnus": row.get("tunnus", ""),
                        "geom": row.get("geom", ""),
                    }
                )
                page_rows += 1

            page_number += 1
            written_rows += page_rows
            print(f"Fetched WFS page {page_number}: startIndex={start_index}, rows={page_rows}, total_written={written_rows}", file=sys.stderr)
            if page_rows == 0:
                break
            start_index += page_rows
            if page_rows < args.wfs_page_size:
                break
            if args.wfs_sleep > 0:
                time.sleep(args.wfs_sleep)

    return args.output


def execute_psql(sql: str, container: str, database: str, user: str) -> None:
    command = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", user, "-d", database]
    subprocess.run(command, input=sql, text=True, check=True)


def copy_to_container(source: Path, container: str, target: str) -> None:
    subprocess.run(["docker", "cp", str(source), f"{container}:{target}"], check=True)
    subprocess.run(["docker", "exec", container, "chmod", "0644", target], check=True)


def import_boundaries(args: argparse.Namespace, csv_path: Path) -> None:
    copy_to_container(csv_path, args.container, CONTAINER_CSV)
    execute_psql(
        f"""
BEGIN;
SET LOCAL statement_timeout = 0;
SET LOCAL lock_timeout = 0;

DROP TABLE IF EXISTS stg_metsis_kataster_boundaries;
CREATE UNLOGGED TABLE stg_metsis_kataster_boundaries (
  fid text,
  tunnus text,
  geom text
);

COPY stg_metsis_kataster_boundaries
FROM '{CONTAINER_CSV}'
WITH (FORMAT csv, HEADER true);

CREATE INDEX stg_metsis_kataster_boundaries_tunnus_idx
ON stg_metsis_kataster_boundaries (btrim(tunnus));

UPDATE cadastres AS c
SET polygon = nullif(btrim(s.geom), ''),
    centroid = NULL
FROM stg_metsis_kataster_boundaries AS s
WHERE c.id = btrim(s.tunnus)
  AND nullif(btrim(s.geom), '') IS NOT NULL;

ANALYZE cadastres;

COMMIT;

SELECT count(*) AS cadastres_with_polygon FROM cadastres WHERE polygon IS NOT NULL;
""",
        args.container,
        args.database,
        args.user,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--wfs-url", default=DEFAULT_WFS_URL)
    parser.add_argument("--wfs-typename", default=DEFAULT_WFS_TYPENAME)
    parser.add_argument("--wfs-page-size", type=int, default=50_000)
    parser.add_argument("--wfs-start-index", type=int, default=0)
    parser.add_argument("--wfs-max-pages", type=int, default=None)
    parser.add_argument("--wfs-timeout", type=int, default=300)
    parser.add_argument("--wfs-sleep", type=float, default=1.0)
    parser.add_argument("--container", default="metsis-db-1")
    parser.add_argument("--database", default="metsis")
    parser.add_argument("--user", default="metsis")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fetch-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = fetch_boundaries(args)
    if args.dry_run or args.fetch_only:
        return 0
    import_boundaries(args, csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
