#!/usr/bin/env python3
"""Import forest notification summary rows and subparts into MetsIS.

The script reads a CSV with at least these columns:

    katastri_nr, raiekups_pindala_ha, eraldised

Optional columns such as maakond and vald are used to enrich cadastres. It uses
the running Postgres Docker container and psql, so no third-party Python
packages are required.

It can also import WFS eraldis exports with columns such as:

    katastri_nr, eraldise_nr, pindala, peapuuliik_kood, shape

And live Metsaregister WFS notification exports from metsaregister:teatis
with columns such as:

    sys_id, teatise_nr, katastri_nr, eraldise_nr, pindala, too_kood,
    raiutav_maht, otsus, otsus_kinnitatud_kp
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree


csv.field_size_limit(sys.maxsize)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAIKUPS_CSV = WORKSPACE_ROOT / "Andmed" / "raiekups_eraisikud_maakond_vald_eraldised.csv"
DEFAULT_WFS_ERALDIS_CSV = PROJECT_ROOT / "Andmed" / "eraldis.csv"
DEFAULT_WFS_ERALDIS_FULL_CSV = PROJECT_ROOT / "Andmed" / "eraldis_full.csv"
DEFAULT_WFS_TEATIS_CSV = PROJECT_ROOT / "Andmed" / "teatis.csv"
DEFAULT_WFS_TEATIS_FULL_CSV = PROJECT_ROOT / "Andmed" / "teatis_full.csv"
DEFAULT_WFS_TEATIS_ARCHIVE_CSV = PROJECT_ROOT / "Andmed" / "teatis_arhiiv.csv"
DEFAULT_WFS_TEATIS_ARCHIVE_FULL_CSV = PROJECT_ROOT / "Andmed" / "teatis_arhiiv_full.csv"
DEFAULT_WFS_URL = "https://gsavalik.envir.ee/geoserver/metsaregister/wfs"
DEFAULT_WFS_TYPENAME = "metsaregister:eraldis"
DEFAULT_WFS_TEATIS_TYPENAME = "metsaregister:teatis"
DEFAULT_WFS_TEATIS_ARCHIVE_TYPENAME = "metsaregister:teatis_arhiiv"
CONTAINER_WFS_CSV = "/tmp/metsis_wfs_eraldis.csv"
CONTAINER_WFS_TEATIS_CSV = "/tmp/metsis_wfs_teatis.csv"
CONTAINER_WFS_FEATURES_CSV = "/tmp/metsis_wfs_registry_features.csv"
WFS_STAGING_COLUMNS = [
    "FID",
    "sys_id",
    "versioon",
    "id",
    "invent_kp",
    "registreerimise_kp",
    "katastri_nr",
    "kvartali_nr",
    "eraldise_nr",
    "pindala",
    "kuivendatud",
    "kasvukoht_kood",
    "peapuuliik_kood",
    "omandivorm_kood",
    "shape",
]
WFS_TEATIS_STAGING_COLUMNS = [
    "FID",
    "shape",
    "sys_id",
    "teatis_id",
    "teatise_nr",
    "kinnistu_nimetus",
    "kinnistu_nr",
    "metskond",
    "katastri_nr",
    "kvartali_nr",
    "eraldise_nr",
    "pindala",
    "too_kood",
    "raiutav_maht",
    "otsus",
    "otsuse_pohjendus",
    "otsuse_pojendus",
    "otsus_kinnitatud_kp",
    "kehtiv_kuni",
    "arhiveerimise_aeg",
]
WFS_FEATURE_STAGING_COLUMNS = [
    "source_layer",
    "source_id",
    "cadastre_id",
    "subpart_code",
    "title",
    "work_code",
    "decision",
    "area",
    "volume",
    "event_date",
    "attributes",
    "geometry",
]


@dataclass(frozen=True)
class CadastreRow:
    cadastre_id: str
    county: str | None
    municipality: str | None
    ripe_area_ha: Decimal | None
    subparts_json: str | None


@dataclass(frozen=True)
class SubpartRow:
    cadastre_id: str
    subpart_code: int | None
    tree_type_code: str | None
    area: Decimal | None


@dataclass(frozen=True)
class NotificationRow:
    notification_id: int
    notification_number: int
    cadastre_id: str
    area: Decimal | None


def parse_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    normalized = value.strip().replace(",", ".")
    if not normalized:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def parse_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def clean_text(value: str | None, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if max_length is not None:
        return cleaned[:max_length]
    return cleaned


def sql_value(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def chunks(items: list[object], batch_size: int) -> Iterable[list[object]]:
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def read_csv(path: Path, notification_id_base: int, notification_number_base: int) -> tuple[list[CadastreRow], list[NotificationRow], list[SubpartRow]]:
    cadastres_by_id: dict[str, CadastreRow] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"katastri_nr", "raiekups_pindala_ha", "eraldised"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        for raw_row in reader:
            cadastre_id = clean_text(raw_row.get("katastri_nr"), 50)
            if cadastre_id is None:
                continue
            cadastres_by_id[cadastre_id] = CadastreRow(
                cadastre_id=cadastre_id,
                county=clean_text(raw_row.get("maakond"), 100),
                municipality=clean_text(raw_row.get("vald"), 50),
                ripe_area_ha=parse_decimal(raw_row.get("raiekups_pindala_ha")),
                subparts_json=clean_text(raw_row.get("eraldised")),
            )

    cadastres = [cadastres_by_id[key] for key in sorted(cadastres_by_id)]
    notifications: list[NotificationRow] = []
    subparts: list[SubpartRow] = []

    for offset, cadastre in enumerate(cadastres, start=1):
        notifications.append(
            NotificationRow(
                notification_id=notification_id_base + offset,
                notification_number=notification_number_base + offset,
                cadastre_id=cadastre.cadastre_id,
                area=cadastre.ripe_area_ha,
            )
        )
        if not cadastre.subparts_json:
            continue
        try:
            raw_subparts = json.loads(cadastre.subparts_json)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw_subparts, list):
            continue
        for raw_subpart in raw_subparts:
            if not isinstance(raw_subpart, dict):
                continue
            subparts.append(
                SubpartRow(
                    cadastre_id=cadastre.cadastre_id,
                    subpart_code=parse_int(raw_subpart.get("eraldise_nr")),
                    tree_type_code=clean_text(str(raw_subpart.get("peapuuliik_kood") or ""), 20),
                    area=parse_decimal(str(raw_subpart.get("pindala_ha") or "")),
                )
            )

    return cadastres, notifications, subparts


def values_sql(rows: Iterable[tuple[object, ...]]) -> str:
    return ",\n".join("(" + ", ".join(sql_value(value) for value in row) + ")" for row in rows)


def execute_psql(sql: str, container: str, database: str, user: str) -> None:
    command = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", user, "-d", database]
    subprocess.run(command, input=sql, text=True, check=True)


def docker_cp_to_container(source: Path, container: str, target: str) -> None:
    subprocess.run(["docker", "cp", str(source), f"{container}:{target}"], check=True)
    subprocess.run(["docker", "exec", container, "chmod", "0644", target], check=True)


def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def normalize_wfs_eraldis_csv(source: Path, target: Path) -> int:
    row_count = 0
    with source.open(newline="", encoding="utf-8-sig") as input_handle, target.open("w", newline="", encoding="utf-8") as output_handle:
        reader = csv.DictReader(input_handle)
        if reader.fieldnames is None:
            raise SystemExit(f"WFS eraldis CSV has no header: {source}")
        missing = {"katastri_nr", "eraldise_nr", "pindala", "peapuuliik_kood", "shape"} - set(reader.fieldnames)
        if missing:
            raise SystemExit(f"WFS eraldis CSV is missing required columns: {', '.join(sorted(missing))}")

        writer = csv.DictWriter(output_handle, fieldnames=WFS_STAGING_COLUMNS)
        writer.writeheader()
        for row in reader:
            writer.writerow({column: row.get(column, "") for column in WFS_STAGING_COLUMNS})
            row_count += 1
    return row_count


def wfs_url(args: argparse.Namespace, start_index: int, count: int, result_type: str = "results") -> str:
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
                "count": str(count),
                "startIndex": str(start_index),
            }
        )
    return f"{args.wfs_url}?{urlencode(query)}"


def fetch_url_text(url: str, timeout: int) -> str:
    request = Request(url, headers={"User-Agent": "metsis-wfs-import/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except URLError as exc:
        raise SystemExit(f"WFS request failed: {exc}") from exc


def fetch_wfs_total_count(args: argparse.Namespace) -> int | None:
    body = fetch_url_text(wfs_url(args, 0, args.wfs_page_size, "hits"), args.wfs_timeout)
    root = ElementTree.fromstring(body)
    number_matched = root.attrib.get("numberMatched")
    if number_matched is None or number_matched.lower() == "unknown":
        return None
    return int(number_matched)


def fetch_wfs_eraldis_csv(args: argparse.Namespace) -> Path:
    total_count = fetch_wfs_total_count(args)
    if total_count is None:
        print("WFS total count is unknown; fetching until an empty page is returned", file=sys.stderr)
    else:
        print(f"WFS reports {total_count} eraldis rows", file=sys.stderr)

    args.wfs_output.parent.mkdir(parents=True, exist_ok=True)
    written_rows = 0
    start_index = args.wfs_start_index
    page_number = 0
    with args.wfs_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=WFS_STAGING_COLUMNS)
        writer.writeheader()
        while True:
            if args.wfs_max_pages is not None and page_number >= args.wfs_max_pages:
                break
            if total_count is not None and start_index >= total_count:
                break

            body = fetch_url_text(wfs_url(args, start_index, args.wfs_page_size), args.wfs_timeout)
            reader = csv.DictReader(io.StringIO(body))
            if reader.fieldnames is None:
                raise SystemExit(f"WFS returned an empty response at startIndex={start_index}")
            if "ExceptionReport" in body[:500] or "ServiceExceptionReport" in body[:500]:
                raise SystemExit(f"WFS returned an exception at startIndex={start_index}:\n{body[:1000]}")

            page_rows = 0
            for row in reader:
                writer.writerow({column: row.get(column, "") for column in WFS_STAGING_COLUMNS})
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

    return args.wfs_output


def fetch_wfs_teatis_csv(args: argparse.Namespace) -> Path:
    original_typename = args.wfs_typename
    original_output = args.wfs_output
    args.wfs_typename = args.wfs_teatis_typename
    args.wfs_output = args.wfs_teatis_output
    try:
        total_count = fetch_wfs_total_count(args)
        if total_count is None:
            print("WFS total count is unknown; fetching teatis rows until an empty page is returned", file=sys.stderr)
        else:
            print(f"WFS reports {total_count} teatis rows", file=sys.stderr)

        args.wfs_output.parent.mkdir(parents=True, exist_ok=True)
        written_rows = 0
        start_index = args.wfs_start_index
        page_number = 0
        with args.wfs_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=WFS_TEATIS_STAGING_COLUMNS)
            writer.writeheader()
            while True:
                if args.wfs_max_pages is not None and page_number >= args.wfs_max_pages:
                    break
                if total_count is not None and start_index >= total_count:
                    break

                body = fetch_url_text(wfs_url(args, start_index, args.wfs_page_size), args.wfs_timeout)
                reader = csv.DictReader(io.StringIO(body))
                if reader.fieldnames is None:
                    raise SystemExit(f"WFS returned an empty teatis response at startIndex={start_index}")
                if "ExceptionReport" in body[:500] or "ServiceExceptionReport" in body[:500]:
                    raise SystemExit(f"WFS returned an exception at startIndex={start_index}:\n{body[:1000]}")

                page_rows = 0
                for row in reader:
                    writer.writerow({column: row.get(column, "") for column in WFS_TEATIS_STAGING_COLUMNS})
                    page_rows += 1

                page_number += 1
                written_rows += page_rows
                print(f"Fetched WFS teatis page {page_number}: startIndex={start_index}, rows={page_rows}, total_written={written_rows}", file=sys.stderr)
                if page_rows == 0:
                    break

                start_index += page_rows
                if page_rows < args.wfs_page_size:
                    break
                if args.wfs_sleep > 0:
                    time.sleep(args.wfs_sleep)

        return args.wfs_output
    finally:
        args.wfs_typename = original_typename
        args.wfs_output = original_output


def fetch_wfs_generic_csv(args: argparse.Namespace) -> Path:
    original_typename = args.wfs_typename
    original_output = args.wfs_output
    args.wfs_typename = args.wfs_generic_typename
    args.wfs_output = args.wfs_generic_output
    try:
        total_count = fetch_wfs_total_count(args)
        if total_count is None:
            print("WFS total count is unknown; fetching generic rows until an empty page is returned", file=sys.stderr)
        else:
            print(f"WFS reports {total_count} rows for {args.wfs_generic_typename}", file=sys.stderr)

        args.wfs_output.parent.mkdir(parents=True, exist_ok=True)
        written_rows = 0
        start_index = args.wfs_start_index
        page_number = 0
        fieldnames: list[str] | None = None
        with args.wfs_output.open("w", newline="", encoding="utf-8") as handle:
            writer = None
            while True:
                if args.wfs_max_pages is not None and page_number >= args.wfs_max_pages:
                    break
                if total_count is not None and start_index >= total_count:
                    break

                body = fetch_url_text(wfs_url(args, start_index, args.wfs_page_size), args.wfs_timeout)
                reader = csv.DictReader(io.StringIO(body))
                if reader.fieldnames is None:
                    raise SystemExit(f"WFS returned an empty response at startIndex={start_index}")
                if "ExceptionReport" in body[:500] or "ServiceExceptionReport" in body[:500]:
                    raise SystemExit(f"WFS returned an exception at startIndex={start_index}:\n{body[:1000]}")
                if fieldnames is None:
                    fieldnames = reader.fieldnames
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()

                page_rows = 0
                for row in reader:
                    writer.writerow({column: row.get(column, "") for column in fieldnames})
                    page_rows += 1

                page_number += 1
                written_rows += page_rows
                print(f"Fetched WFS generic page {page_number}: startIndex={start_index}, rows={page_rows}, total_written={written_rows}", file=sys.stderr)
                if page_rows == 0:
                    break

                start_index += page_rows
                if page_rows < args.wfs_page_size:
                    break
                if args.wfs_sleep > 0:
                    time.sleep(args.wfs_sleep)

        return args.wfs_output
    finally:
        args.wfs_typename = original_typename
        args.wfs_output = original_output


def row_value(row: dict[str, str], column: str | None) -> str | None:
    if not column:
        return None
    return clean_text(row.get(column))


def normalize_wfs_generic_csv(source: Path, target: Path, args: argparse.Namespace) -> int:
    row_count = 0
    source_layer = args.wfs_generic_typename
    with source.open(newline="", encoding="utf-8-sig") as input_handle, target.open("w", newline="", encoding="utf-8") as output_handle:
        reader = csv.DictReader(input_handle)
        if reader.fieldnames is None:
            raise SystemExit(f"WFS generic CSV has no header: {source}")
        if args.wfs_generic_cadastre_column not in reader.fieldnames:
            raise SystemExit(f"WFS generic CSV is missing cadastre column {args.wfs_generic_cadastre_column}: {source}")

        writer = csv.DictWriter(output_handle, fieldnames=WFS_FEATURE_STAGING_COLUMNS)
        writer.writeheader()
        for row in reader:
            cadastre_id = row_value(row, args.wfs_generic_cadastre_column)
            if not cadastre_id:
                continue
            source_id = (
                row_value(row, args.wfs_generic_id_column)
                or row_value(row, "FID")
                or row_value(row, "sys_id")
                or row_value(row, "id")
            )
            if not source_id:
                continue
            writer.writerow(
                {
                    "source_layer": source_layer,
                    "source_id": source_id,
                    "cadastre_id": cadastre_id,
                    "subpart_code": row_value(row, args.wfs_generic_subpart_column),
                    "title": row_value(row, args.wfs_generic_title_column),
                    "work_code": row_value(row, args.wfs_generic_work_column),
                    "decision": row_value(row, args.wfs_generic_decision_column),
                    "area": row_value(row, args.wfs_generic_area_column),
                    "volume": row_value(row, args.wfs_generic_volume_column),
                    "event_date": row_value(row, args.wfs_generic_date_column),
                    "attributes": json.dumps(row, ensure_ascii=False, sort_keys=True),
                    "geometry": row_value(row, args.wfs_generic_geometry_column),
                }
            )
            row_count += 1
    return row_count


def import_wfs_generic_csv(args: argparse.Namespace) -> None:
    if not args.wfs_generic_csv.exists():
        raise SystemExit(f"WFS generic CSV does not exist: {args.wfs_generic_csv}")

    normalized_csv = args.wfs_generic_csv.with_name(f"{args.wfs_generic_csv.stem}.registry.normalized.csv")
    row_count = normalize_wfs_generic_csv(args.wfs_generic_csv, normalized_csv, args)
    print(f"Prepared {row_count} WFS registry feature rows from {args.wfs_generic_csv}", file=sys.stderr)
    if args.dry_run:
        return

    docker_cp_to_container(normalized_csv, args.container, CONTAINER_WFS_FEATURES_CSV)
    execute_psql(
        f"""
BEGIN;
SET LOCAL statement_timeout = 0;
SET LOCAL lock_timeout = 0;

DROP TABLE IF EXISTS stg_metsis_wfs_registry_features;
CREATE UNLOGGED TABLE stg_metsis_wfs_registry_features (
  source_layer text,
  source_id text,
  cadastre_id text,
  subpart_code text,
  title text,
  work_code text,
  decision text,
  area text,
  volume text,
  event_date text,
  attributes text,
  geometry text
);

COPY stg_metsis_wfs_registry_features
FROM '{CONTAINER_WFS_FEATURES_CSV}'
WITH (FORMAT csv, HEADER true);

CREATE INDEX stg_metsis_wfs_registry_features_cadastre_idx
ON stg_metsis_wfs_registry_features (btrim(cadastre_id), btrim(source_layer));

INSERT INTO cadastres (id, name, marked)
SELECT DISTINCT btrim(cadastre_id), btrim(cadastre_id), false
FROM stg_metsis_wfs_registry_features
WHERE nullif(btrim(cadastre_id), '') IS NOT NULL
ON CONFLICT (id) DO NOTHING;

DELETE FROM forest_registry_features AS frf
USING (
  SELECT DISTINCT btrim(source_layer) AS source_layer, btrim(cadastre_id) AS cadastre_id
  FROM stg_metsis_wfs_registry_features
  WHERE nullif(btrim(cadastre_id), '') IS NOT NULL
) AS source
WHERE frf.source_layer = source.source_layer
  AND frf.cadastre_id = source.cadastre_id;

INSERT INTO forest_registry_features (
  source_layer,
  source_id,
  cadastre_id,
  subpart_code,
  title,
  work_code,
  decision,
  area,
  volume,
  event_date,
  attributes,
  geometry
)
SELECT
  left(btrim(source_layer), 100),
  left(btrim(source_id), 100),
  btrim(cadastre_id),
  nullif(btrim(subpart_code), '')::integer,
  left(nullif(btrim(title), ''), 255),
  left(nullif(btrim(work_code), ''), 50),
  left(nullif(btrim(decision), ''), 100),
  nullif(replace(btrim(area), ',', '.'), '')::numeric,
  nullif(replace(btrim(volume), ',', '.'), '')::numeric,
  CASE
    WHEN nullif(btrim(event_date), '') IS NULL THEN NULL
    ELSE floor(extract(epoch from nullif(btrim(event_date), '')::timestamptz) * 1000)::bigint
  END,
  attributes,
  nullif(btrim(geometry), '')
FROM stg_metsis_wfs_registry_features
WHERE nullif(btrim(source_layer), '') IS NOT NULL
  AND nullif(btrim(source_id), '') IS NOT NULL
  AND nullif(btrim(cadastre_id), '') IS NOT NULL
ON CONFLICT (source_layer, source_id) DO UPDATE SET
  cadastre_id = EXCLUDED.cadastre_id,
  subpart_code = EXCLUDED.subpart_code,
  title = EXCLUDED.title,
  work_code = EXCLUDED.work_code,
  decision = EXCLUDED.decision,
  area = EXCLUDED.area,
  volume = EXCLUDED.volume,
  event_date = EXCLUDED.event_date,
  attributes = EXCLUDED.attributes,
  geometry = EXCLUDED.geometry;

ANALYZE forest_registry_features;

COMMIT;

SELECT source_layer, count(*) AS rows, count(DISTINCT cadastre_id) AS cadastres
FROM forest_registry_features
GROUP BY source_layer
ORDER BY source_layer;
""",
        args.container,
        args.database,
        args.user,
    )


def normalize_wfs_teatis_csv(source: Path, target: Path) -> int:
    row_count = 0
    with source.open(newline="", encoding="utf-8-sig") as input_handle, target.open("w", newline="", encoding="utf-8") as output_handle:
        reader = csv.DictReader(input_handle)
        if reader.fieldnames is None:
            raise SystemExit(f"WFS teatis CSV has no header: {source}")
        missing = {"sys_id", "teatise_nr", "katastri_nr", "eraldise_nr", "pindala", "too_kood", "raiutav_maht", "otsus", "otsus_kinnitatud_kp"} - set(reader.fieldnames)
        if missing:
            raise SystemExit(f"WFS teatis CSV is missing required columns: {', '.join(sorted(missing))}")

        writer = csv.DictWriter(output_handle, fieldnames=WFS_TEATIS_STAGING_COLUMNS)
        writer.writeheader()
        for row in reader:
            writer.writerow({column: row.get(column, "") for column in WFS_TEATIS_STAGING_COLUMNS})
            row_count += 1
    return row_count


def import_wfs_teatis_csv(args: argparse.Namespace) -> None:
    if not args.wfs_teatis_csv.exists():
        raise SystemExit(f"WFS teatis CSV does not exist: {args.wfs_teatis_csv}")

    archived = "true" if args.wfs_teatis_archived else "false"
    normalized_csv = args.wfs_teatis_csv.with_name(f"{args.wfs_teatis_csv.stem}.normalized.csv")
    row_count = normalize_wfs_teatis_csv(args.wfs_teatis_csv, normalized_csv)
    print(f"Prepared {row_count} WFS teatis rows from {args.wfs_teatis_csv}", file=sys.stderr)
    if args.dry_run:
        return

    docker_cp_to_container(normalized_csv, args.container, CONTAINER_WFS_TEATIS_CSV)
    execute_psql(
        f"""
BEGIN;
SET LOCAL statement_timeout = 0;
SET LOCAL lock_timeout = 0;

DROP TABLE IF EXISTS stg_metsis_wfs_teatis;
CREATE UNLOGGED TABLE stg_metsis_wfs_teatis (
  fid text,
  shape text,
  sys_id text,
  teatis_id text,
  teatise_nr text,
  kinnistu_nimetus text,
  kinnistu_nr text,
  metskond text,
  katastri_nr text,
  kvartali_nr text,
  eraldise_nr text,
  pindala text,
  too_kood text,
  raiutav_maht text,
  otsus text,
  otsuse_pohjendus text,
  otsuse_pojendus text,
  otsus_kinnitatud_kp text,
  kehtiv_kuni text,
  arhiveerimise_aeg text
);

COPY stg_metsis_wfs_teatis
FROM '{CONTAINER_WFS_TEATIS_CSV}'
WITH (FORMAT csv, HEADER true);

CREATE INDEX stg_metsis_wfs_teatis_cadastre_idx
ON stg_metsis_wfs_teatis (btrim(katastri_nr));

INSERT INTO cadastres (id, name, marked)
SELECT DISTINCT btrim(katastri_nr), btrim(katastri_nr), false
FROM stg_metsis_wfs_teatis
WHERE nullif(btrim(katastri_nr), '') IS NOT NULL
ON CONFLICT (id) DO NOTHING;

DELETE FROM cadastre_notifications AS cn
USING (
  SELECT DISTINCT btrim(katastri_nr) AS cadastre_id
  FROM stg_metsis_wfs_teatis
  WHERE nullif(btrim(katastri_nr), '') IS NOT NULL
) AS source
WHERE cn.cadastre_id = source.cadastre_id
  AND cn.archived = {archived};

INSERT INTO cadastre_notifications (
  id,
  notification_number,
  cadastre_subpart_code,
  work_code,
  state,
  damage_code,
  decision,
  registration_date,
  confirmation_date,
  archive_date,
  archived,
  area,
  amount_to_be_cut,
  cadastre_id
)
SELECT
  COALESCE(nullif(btrim(teatis_id), '')::bigint, nullif(btrim(sys_id), '')::bigint),
  nullif(regexp_replace(btrim(teatise_nr), '[^0-9]', '', 'g'), '')::bigint,
  nullif(btrim(eraldise_nr), '')::integer,
  nullif(btrim(too_kood), ''),
  NULL,
  NULL,
  left(nullif(btrim(otsus), ''), 20),
  CASE
    WHEN nullif(btrim(otsus_kinnitatud_kp), '') IS NULL THEN NULL
    ELSE floor(extract(epoch from nullif(btrim(otsus_kinnitatud_kp), '')::timestamptz) * 1000)::bigint
  END,
  CASE
    WHEN nullif(btrim(otsus_kinnitatud_kp), '') IS NULL THEN NULL
    ELSE floor(extract(epoch from nullif(btrim(otsus_kinnitatud_kp), '')::timestamptz) * 1000)::bigint
  END,
  CASE
    WHEN nullif(btrim(arhiveerimise_aeg), '') IS NULL THEN NULL
    ELSE floor(extract(epoch from nullif(btrim(arhiveerimise_aeg), '')::timestamptz) * 1000)::bigint
  END,
  {archived},
  nullif(replace(btrim(pindala), ',', '.'), '')::numeric,
  nullif(replace(btrim(raiutav_maht), ',', '.'), '')::numeric,
  btrim(katastri_nr)
FROM stg_metsis_wfs_teatis
WHERE nullif(btrim(katastri_nr), '') IS NOT NULL
  AND nullif(regexp_replace(btrim(teatise_nr), '[^0-9]', '', 'g'), '') IS NOT NULL
  AND COALESCE(nullif(btrim(teatis_id), ''), nullif(btrim(sys_id), '')) IS NOT NULL
ON CONFLICT (id) DO UPDATE SET
  notification_number = EXCLUDED.notification_number,
  cadastre_subpart_code = EXCLUDED.cadastre_subpart_code,
  work_code = EXCLUDED.work_code,
  decision = EXCLUDED.decision,
  registration_date = EXCLUDED.registration_date,
  confirmation_date = EXCLUDED.confirmation_date,
  archive_date = EXCLUDED.archive_date,
  archived = EXCLUDED.archived,
  area = EXCLUDED.area,
  amount_to_be_cut = EXCLUDED.amount_to_be_cut,
  cadastre_id = EXCLUDED.cadastre_id;

ANALYZE cadastres;
ANALYZE cadastre_notifications;

COMMIT;

SELECT 'cadastre_notifications' AS table_name, count(*) FROM cadastre_notifications
UNION ALL SELECT 'notifications_with_volume', count(*) FROM cadastre_notifications WHERE amount_to_be_cut IS NOT NULL
UNION ALL SELECT 'notification_cadastres', count(DISTINCT cadastre_id) FROM cadastre_notifications
ORDER BY table_name;
""",
        args.container,
        args.database,
        args.user,
    )


def import_wfs_eraldis_csv(args: argparse.Namespace) -> None:
    if not args.wfs_csv.exists():
        raise SystemExit(f"WFS eraldis CSV does not exist: {args.wfs_csv}")

    normalized_csv = args.wfs_csv.with_name(f"{args.wfs_csv.stem}.normalized.csv")
    row_count = normalize_wfs_eraldis_csv(args.wfs_csv, normalized_csv)
    print(f"Prepared {row_count} WFS eraldis rows from {args.wfs_csv}", file=sys.stderr)
    if args.dry_run:
        return

    docker_cp_to_container(normalized_csv, args.container, CONTAINER_WFS_CSV)
    execute_psql(
        f"""
BEGIN;
SET LOCAL statement_timeout = 0;
SET LOCAL lock_timeout = 0;

DROP TABLE IF EXISTS stg_metsis_wfs_eraldis;
CREATE UNLOGGED TABLE stg_metsis_wfs_eraldis (
  fid text,
  sys_id text,
  versioon text,
  id text,
  invent_kp text,
  registreerimise_kp text,
  katastri_nr text,
  kvartali_nr text,
  eraldise_nr text,
  pindala text,
  kuivendatud text,
  kasvukoht_kood text,
  peapuuliik_kood text,
  omandivorm_kood text,
  shape text
);

COPY stg_metsis_wfs_eraldis
FROM '{CONTAINER_WFS_CSV}'
WITH (FORMAT csv, HEADER true);

CREATE INDEX stg_metsis_wfs_eraldis_cadastre_idx
ON stg_metsis_wfs_eraldis (btrim(katastri_nr));

INSERT INTO cadastres (id, name, marked)
SELECT DISTINCT btrim(katastri_nr), btrim(katastri_nr), false
FROM stg_metsis_wfs_eraldis
WHERE nullif(btrim(katastri_nr), '') IS NOT NULL
ON CONFLICT (id) DO NOTHING;

DELETE FROM cadastre_sub_parts AS csp
USING (
  SELECT DISTINCT btrim(katastri_nr) AS cadastre_id
  FROM stg_metsis_wfs_eraldis
  WHERE nullif(btrim(katastri_nr), '') IS NOT NULL
) AS source
WHERE csp.cadastre_id = source.cadastre_id;

INSERT INTO cadastre_sub_parts (sub_part_code, tree_type_code, area, polygon, cadastre_id)
SELECT
  nullif(btrim(eraldise_nr), '')::integer,
  nullif(btrim(peapuuliik_kood), ''),
  nullif(replace(btrim(pindala), ',', '.'), '')::numeric,
  nullif(btrim(shape), ''),
  btrim(katastri_nr)
FROM stg_metsis_wfs_eraldis
WHERE nullif(btrim(katastri_nr), '') IS NOT NULL;

ANALYZE cadastres;
ANALYZE cadastre_sub_parts;

COMMIT;

SELECT 'cadastre_sub_parts' AS table_name, count(*) FROM cadastre_sub_parts
UNION ALL SELECT 'subparts_with_polygon', count(*) FROM cadastre_sub_parts WHERE polygon IS NOT NULL
UNION ALL SELECT 'cadastres', count(*) FROM cadastres
ORDER BY table_name;
""",
        args.container,
        args.database,
        args.user,
    )


def import_data(
    cadastres: list[CadastreRow],
    notifications: list[NotificationRow],
    subparts: list[SubpartRow],
    args: argparse.Namespace,
) -> None:
    statements: list[str] = [
        "BEGIN;",
        "SET LOCAL statement_timeout = 0;",
        "SET LOCAL lock_timeout = 0;",
    ]

    for batch in chunks(cadastres, args.batch_size):
        statements.append(
            "INSERT INTO cadastres (id, name, county, municipality, area, forest_area, type, marked)\n"
            "VALUES\n" +
            values_sql(
                (
                    row.cadastre_id,
                    row.cadastre_id,
                    row.county,
                    row.municipality,
                    row.ripe_area_ha,
                    row.ripe_area_ha,
                    "RAIEKUPS",
                    False,
                )
                for row in batch
            ) +
            "\nON CONFLICT (id) DO UPDATE SET\n"
            "  county = COALESCE(EXCLUDED.county, cadastres.county),\n"
            "  municipality = COALESCE(EXCLUDED.municipality, cadastres.municipality),\n"
            "  forest_area = COALESCE(EXCLUDED.forest_area, cadastres.forest_area),\n"
            "  type = COALESCE(cadastres.type, EXCLUDED.type);"
        )

    for batch in chunks(cadastres, args.batch_size):
        cadastre_values = values_sql((row.cadastre_id,) for row in batch)
        statements.append(
            "DELETE FROM cadastre_notifications WHERE cadastre_id IN "
            f"(SELECT column1 FROM (VALUES {cadastre_values}) AS v);"
        )
        statements.append(
            "DELETE FROM cadastre_sub_parts WHERE cadastre_id IN "
            f"(SELECT column1 FROM (VALUES {cadastre_values}) AS v);"
        )

    for batch in chunks(notifications, args.batch_size):
        statements.append(
            "INSERT INTO cadastre_notifications "
            "(id, notification_number, cadastre_subpart_code, work_code, state, decision, area, amount_to_be_cut, cadastre_id)\n"
            "VALUES\n" +
            values_sql(
                (
                    row.notification_id,
                    row.notification_number,
                    None,
                    "LR",
                    1,
                    "YES",
                    row.area,
                    None,
                    row.cadastre_id,
                )
                for row in batch
            ) +
            "\nON CONFLICT (id) DO UPDATE SET\n"
            "  notification_number = EXCLUDED.notification_number,\n"
            "  area = EXCLUDED.area,\n"
            "  cadastre_id = EXCLUDED.cadastre_id;"
        )

    for batch in chunks(subparts, args.batch_size):
        statements.append(
            "INSERT INTO cadastre_sub_parts (sub_part_code, tree_type_code, area, polygon, cadastre_id)\n"
            "VALUES\n" +
            values_sql(
                (
                    row.subpart_code,
                    row.tree_type_code,
                    row.area,
                    None,
                    row.cadastre_id,
                )
                for row in batch
            ) +
            ";"
        )

    statements.extend(
        [
            "ANALYZE cadastres;",
            "ANALYZE cadastre_notifications;",
            "ANALYZE cadastre_sub_parts;",
            "COMMIT;",
            "SELECT 'cadastre_notifications' AS table_name, count(*) FROM cadastre_notifications "
            "UNION ALL SELECT 'cadastre_sub_parts', count(*) FROM cadastre_sub_parts "
            "UNION ALL SELECT 'raiekups_cadastres', count(*) FROM cadastres WHERE forest_area IS NOT NULL "
            "ORDER BY table_name;",
        ]
    )

    execute_psql("\n".join(statements), args.container, args.database, args.user)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=("raiekups-csv", "wfs-eraldis-csv", "wfs-eraldis-live", "wfs-teatis-csv", "wfs-teatis-live", "wfs-teatis-archive-csv", "wfs-teatis-archive-live", "wfs-generic-csv", "wfs-generic-live"),
        default="raiekups-csv",
        help="Import source type.",
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_RAIKUPS_CSV, help=f"Raiekups source CSV path. Default: {DEFAULT_RAIKUPS_CSV}")
    parser.add_argument("--wfs-csv", type=Path, default=DEFAULT_WFS_ERALDIS_CSV, help=f"WFS eraldis CSV path. Default: {DEFAULT_WFS_ERALDIS_CSV}")
    parser.add_argument("--wfs-output", type=Path, default=DEFAULT_WFS_ERALDIS_FULL_CSV, help=f"Live WFS download target CSV. Default: {DEFAULT_WFS_ERALDIS_FULL_CSV}")
    parser.add_argument("--wfs-teatis-csv", type=Path, default=DEFAULT_WFS_TEATIS_CSV, help=f"WFS teatis CSV path. Default: {DEFAULT_WFS_TEATIS_CSV}")
    parser.add_argument("--wfs-teatis-output", type=Path, default=DEFAULT_WFS_TEATIS_FULL_CSV, help=f"Live WFS teatis download target CSV. Default: {DEFAULT_WFS_TEATIS_FULL_CSV}")
    parser.add_argument("--wfs-teatis-archive-csv", type=Path, default=DEFAULT_WFS_TEATIS_ARCHIVE_CSV, help=f"WFS teatis_arhiiv CSV path. Default: {DEFAULT_WFS_TEATIS_ARCHIVE_CSV}")
    parser.add_argument("--wfs-teatis-archive-output", type=Path, default=DEFAULT_WFS_TEATIS_ARCHIVE_FULL_CSV, help=f"Live WFS teatis_arhiiv download target CSV. Default: {DEFAULT_WFS_TEATIS_ARCHIVE_FULL_CSV}")
    parser.add_argument("--wfs-generic-csv", type=Path, default=PROJECT_ROOT / "Andmed" / "wfs_registry_features.csv", help="Generic WFS CSV path.")
    parser.add_argument("--wfs-generic-output", type=Path, default=PROJECT_ROOT / "Andmed" / "wfs_registry_features_full.csv", help="Live generic WFS download target CSV.")
    parser.add_argument("--wfs-url", default=DEFAULT_WFS_URL, help=f"WFS endpoint URL. Default: {DEFAULT_WFS_URL}")
    parser.add_argument("--wfs-typename", default=DEFAULT_WFS_TYPENAME, help=f"WFS feature type name. Default: {DEFAULT_WFS_TYPENAME}")
    parser.add_argument("--wfs-teatis-typename", default=DEFAULT_WFS_TEATIS_TYPENAME, help=f"WFS teatis feature type name. Default: {DEFAULT_WFS_TEATIS_TYPENAME}")
    parser.add_argument("--wfs-teatis-archive-typename", default=DEFAULT_WFS_TEATIS_ARCHIVE_TYPENAME, help=f"WFS teatis_arhiiv feature type name. Default: {DEFAULT_WFS_TEATIS_ARCHIVE_TYPENAME}")
    parser.add_argument("--wfs-generic-typename", default="metsaregister:mke", help="Generic WFS feature type name.")
    parser.add_argument("--wfs-generic-id-column", default=None, help="Source id column. Defaults to FID, sys_id, then id.")
    parser.add_argument("--wfs-generic-cadastre-column", default="katastri_nr", help="Cadastre id column.")
    parser.add_argument("--wfs-generic-subpart-column", default="eraldise_nr", help="Subpart code column.")
    parser.add_argument("--wfs-generic-title-column", default="teatise_nr", help="Title column.")
    parser.add_argument("--wfs-generic-work-column", default="too_kood", help="Work code column.")
    parser.add_argument("--wfs-generic-decision-column", default="otsus", help="Decision column.")
    parser.add_argument("--wfs-generic-area-column", default="pindala", help="Area column.")
    parser.add_argument("--wfs-generic-volume-column", default="raiutav_maht", help="Volume column.")
    parser.add_argument("--wfs-generic-date-column", default="otsus_kinnitatud_kp", help="Event date column.")
    parser.add_argument("--wfs-generic-geometry-column", default="shape", help="Geometry column.")
    parser.add_argument("--wfs-page-size", type=int, default=50_000, help="Rows to request from WFS per page.")
    parser.add_argument("--wfs-start-index", type=int, default=0, help="First WFS startIndex to request.")
    parser.add_argument("--wfs-max-pages", type=int, default=None, help="Stop after this many WFS pages; useful for testing.")
    parser.add_argument("--wfs-timeout", type=int, default=300, help="WFS request timeout in seconds.")
    parser.add_argument("--wfs-sleep", type=float, default=0.0, help="Seconds to sleep between WFS pages.")
    parser.add_argument("--fetch-only", action="store_true", help="Download/normalize live WFS CSV without importing it.")
    parser.add_argument("--container", default="metsis-db-1", help="Postgres Docker container name.")
    parser.add_argument("--database", default="metsis", help="Database name.")
    parser.add_argument("--user", default="metsis", help="Database user.")
    parser.add_argument("--batch-size", type=int, default=1000, help="Rows per SQL batch.")
    parser.add_argument("--notification-id-base", type=int, default=900_000_000, help="Synthetic notification id base.")
    parser.add_argument("--notification-number-base", type=int, default=800_000_000, help="Synthetic notification number base.")
    parser.set_defaults(wfs_teatis_archived=False)
    parser.add_argument("--dry-run", action="store_true", help="Read and validate input without writing to DB.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.source == "wfs-eraldis-live":
        args.wfs_csv = fetch_wfs_eraldis_csv(args)
        if args.fetch_only:
            print(f"Downloaded WFS eraldis rows to {args.wfs_csv}", file=sys.stderr)
            return 0
        import_wfs_eraldis_csv(args)
        return 0

    if args.source == "wfs-eraldis-csv":
        import_wfs_eraldis_csv(args)
        return 0

    if args.source == "wfs-teatis-live":
        args.wfs_teatis_archived = False
        args.wfs_teatis_csv = fetch_wfs_teatis_csv(args)
        if args.fetch_only:
            print(f"Downloaded WFS teatis rows to {args.wfs_teatis_csv}", file=sys.stderr)
            return 0
        import_wfs_teatis_csv(args)
        return 0

    if args.source == "wfs-teatis-csv":
        args.wfs_teatis_archived = False
        import_wfs_teatis_csv(args)
        return 0

    if args.source == "wfs-teatis-archive-live":
        args.wfs_teatis_archived = True
        args.wfs_teatis_typename = args.wfs_teatis_archive_typename
        args.wfs_teatis_output = args.wfs_teatis_archive_output
        args.wfs_teatis_csv = fetch_wfs_teatis_csv(args)
        if args.fetch_only:
            print(f"Downloaded WFS teatis_arhiiv rows to {args.wfs_teatis_csv}", file=sys.stderr)
            return 0
        import_wfs_teatis_csv(args)
        return 0

    if args.source == "wfs-teatis-archive-csv":
        args.wfs_teatis_archived = True
        args.wfs_teatis_csv = args.wfs_teatis_archive_csv
        import_wfs_teatis_csv(args)
        return 0

    if args.source == "wfs-generic-live":
        args.wfs_generic_csv = fetch_wfs_generic_csv(args)
        if args.fetch_only:
            print(f"Downloaded WFS generic rows to {args.wfs_generic_csv}", file=sys.stderr)
            return 0
        import_wfs_generic_csv(args)
        return 0

    if args.source == "wfs-generic-csv":
        import_wfs_generic_csv(args)
        return 0

    cadastres, notifications, subparts = read_csv(args.csv, args.notification_id_base, args.notification_number_base)
    print(
        f"Prepared {len(cadastres)} cadastres, "
        f"{len(notifications)} notification rows, {len(subparts)} subpart rows from {args.csv}",
        file=sys.stderr,
    )
    if args.dry_run:
        return 0
    import_data(cadastres, notifications, subparts, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
