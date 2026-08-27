#!/usr/bin/env python3
"""Validate temporary security scanning exceptions before merge."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

MAX_EXCEPTION_LIFETIME_DAYS = 90
VALID_SCANNERS = {"pip-audit", "pnpm-audit", "gitleaks"}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{2,127}$")
REFERENCE = re.compile(r"^(?:#\d+|https://[^\s]+)$")


def fail(message: str) -> None:
    print(f"security exception validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "security-exceptions.json")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read {path}: {error}")

    exceptions = document.get("exceptions") if isinstance(document, dict) else None
    if not isinstance(exceptions, list):
        fail("top-level 'exceptions' must be a list")

    seen: set[tuple[str, str]] = set()
    today = date.today()
    for position, entry in enumerate(exceptions, start=1):
        if not isinstance(entry, dict):
            fail(f"record {position} must be an object")
        required = ("id", "scanner", "reference", "rationale", "expires_on")
        missing = [field for field in required if not isinstance(entry.get(field), str) or not entry[field].strip()]
        if missing:
            fail(f"record {position} is missing non-empty fields: {', '.join(missing)}")
        if entry["scanner"] not in VALID_SCANNERS:
            fail(f"record {position} uses unsupported scanner '{entry['scanner']}'")
        if not IDENTIFIER.fullmatch(entry["id"]):
            fail(f"record {position} has an invalid scanner identifier")
        if not REFERENCE.fullmatch(entry["reference"]):
            fail(f"record {position} reference must be an issue number or HTTPS URL")
        if len(entry["rationale"].strip()) < 20:
            fail(f"record {position} rationale must contain at least 20 characters")
        try:
            expires_on = date.fromisoformat(entry["expires_on"])
        except ValueError:
            fail(f"record {position} expiry must use ISO date format YYYY-MM-DD")
        if expires_on <= today:
            fail(f"record {position} is expired on {expires_on.isoformat()}")
        if expires_on > today + timedelta(days=MAX_EXCEPTION_LIFETIME_DAYS):
            fail(f"record {position} exceeds the {MAX_EXCEPTION_LIFETIME_DAYS}-day maximum lifetime")
        key = (entry["scanner"], entry["id"])
        if key in seen:
            fail(f"record {position} duplicates {entry['scanner']} identifier {entry['id']}")
        seen.add(key)

    print(f"security exceptions valid: {len(exceptions)} active temporary exception(s)")


if __name__ == "__main__":
    main()
