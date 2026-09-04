#!/usr/bin/env python3
"""Portable ForestIQ PostgreSQL + media backup verification and restore drill tooling."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=capture)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact_database_url(url: str) -> str:
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


def media_stats(root: Path, *, excluded: Path | None = None) -> dict[str, int]:
    files = 0
    bytes_total = 0
    if not root.exists():
        return {"files": 0, "bytes": 0}
    excluded_resolved = excluded.resolve() if excluded else None
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if excluded_resolved and excluded_resolved in path.resolve().parents:
            continue
        files += 1
        bytes_total += path.stat().st_size
    return {"files": files, "bytes": bytes_total}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    temporary.replace(path)


def verify_backup(backup_dir: Path) -> dict:
    manifest_path = backup_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks: dict[str, object] = {}
    for key in ("database", "media"):
        artifact = backup_dir / manifest[key]["file"]
        actual = sha256(artifact)
        expected = manifest[key]["sha256"]
        checks[f"{key}Sha256"] = {"ok": actual == expected, "expected": expected, "actual": actual}
        if actual != expected:
            raise RuntimeError(f"{key} backup checksum mismatch")
    run(["pg_restore", "--list", str(backup_dir / manifest["database"]["file"])], capture=True)
    with tarfile.open(backup_dir / manifest["media"]["file"], "r:gz") as archive:
        archive.getmembers()
    checks["pgRestoreList"] = {"ok": True}
    checks["mediaArchive"] = {"ok": True}
    return {"manifest": manifest, "checks": checks}


def create_backup(database_url: str, media_root: Path, output_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final_dir = output_root / timestamp
    output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="forestiq-backup-", dir=output_root) as temp_name:
        temp_dir = Path(temp_name)
        database_file = temp_dir / "database.dump"
        media_file = temp_dir / "media.tar.gz"
        run(["pg_dump", "--format=custom", "--no-owner", "--no-acl", "--file", str(database_file), database_url])
        run(["pg_restore", "--list", str(database_file)], capture=True)
        with tarfile.open(media_file, "w:gz") as archive:
            if media_root.exists():
                for child in media_root.iterdir():
                    if child.resolve() == output_root.resolve() or output_root.resolve() in child.resolve().parents:
                        continue
                    archive.add(child, arcname=child.name, recursive=True)
        stats = media_stats(media_root, excluded=output_root)
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "createdAt": utc_now(),
            "database": {
                "source": redact_database_url(database_url),
                "file": database_file.name,
                "sha256": sha256(database_file),
                "bytes": database_file.stat().st_size,
            },
            "media": {
                "source": str(media_root),
                "file": media_file.name,
                "sha256": sha256(media_file),
                **stats,
            },
            "targets": {"databaseRpoMinutes": 15, "mediaRpoHours": 24, "rtoHours": 4},
        }
        write_json(temp_dir / "manifest.json", manifest)
        shutil.move(str(temp_dir), final_dir)
    verify_backup(final_dir)
    return final_dir


def restore_backup(backup_dir: Path, target_database_url: str, target_media_root: Path, production_database_url: str | None, production_media_root: Path | None, report_path: Path) -> dict:
    started = utc_now()
    report: dict[str, object] = {"startedAt": started, "status": "RUNNING", "backup": str(backup_dir), "checks": {}}
    try:
        if production_database_url and target_database_url == production_database_url:
            raise RuntimeError("Restore target must not be the production DATABASE_URL")
        if production_media_root and target_media_root.resolve() == production_media_root.resolve():
            raise RuntimeError("Restore media target must not be the production media directory")
        verification = verify_backup(backup_dir)
        manifest = verification["manifest"]
        report["checks"] = verification["checks"]
        database_file = backup_dir / manifest["database"]["file"]
        media_file = backup_dir / manifest["media"]["file"]
        run(["pg_restore", "--clean", "--if-exists", "--no-owner", "--no-acl", "--dbname", target_database_url, str(database_file)])
        target_media_root.mkdir(parents=True, exist_ok=True)
        for child in target_media_root.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        with tarfile.open(media_file, "r:gz") as archive:
            archive.extractall(target_media_root, filter="data")
        migrations = run(["psql", target_database_url, "-Atc", "SELECT count(*) FROM django_migrations;"], capture=True).stdout.strip()
        restored_media = media_stats(target_media_root)
        expected_media = {"files": manifest["media"]["files"], "bytes": manifest["media"]["bytes"]}
        report["checks"]["djangoMigrations"] = {"ok": int(migrations or "0") > 0, "rows": int(migrations or "0")}
        report["checks"]["mediaStats"] = {"ok": restored_media == expected_media, "expected": expected_media, "actual": restored_media}
        if not report["checks"]["djangoMigrations"]["ok"] or not report["checks"]["mediaStats"]["ok"]:
            raise RuntimeError("Restore integrity checks failed")
        report["status"] = "SUCCESS"
    except Exception as exc:
        report["status"] = "FAILED"
        report["error"] = str(exc)
        raise
    finally:
        report["finishedAt"] = utc_now()
        write_json(report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    backup.add_argument("--media-root", default=os.getenv("FORESTIQ_MEDIA_ROOT", "/app/media"))
    backup.add_argument("--output", default=os.getenv("FORESTIQ_BACKUP_DIR", "./backups"))
    verify = sub.add_parser("verify")
    verify.add_argument("backup_dir")
    restore = sub.add_parser("restore")
    restore.add_argument("backup_dir")
    restore.add_argument("--target-database-url", default=os.getenv("RESTORE_DATABASE_URL"))
    restore.add_argument("--target-media-root", default=os.getenv("RESTORE_MEDIA_ROOT", "./restore-media"))
    restore.add_argument("--report", default=os.getenv("RESTORE_AUDIT_REPORT", "./restore-audit.json"))
    args = parser.parse_args()

    if args.command == "backup":
        if not args.database_url:
            parser.error("DATABASE_URL or --database-url is required")
        created = create_backup(args.database_url, Path(args.media_root), Path(args.output))
        print(created)
        return 0
    if args.command == "verify":
        print(json.dumps(verify_backup(Path(args.backup_dir)), indent=2, default=str))
        return 0
    if not args.target_database_url:
        parser.error("RESTORE_DATABASE_URL or --target-database-url is required")
    restore_backup(
        Path(args.backup_dir),
        args.target_database_url,
        Path(args.target_media_root),
        os.getenv("DATABASE_URL"),
        Path(os.getenv("FORESTIQ_MEDIA_ROOT", "/app/media")) if os.getenv("DATABASE_URL") else None,
        Path(args.report),
    )
    print(args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
