#!/usr/bin/env python3
"""Fail CI when high/critical dependency advisories lack a valid temporary exception."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BLOCKING_SEVERITIES = {"high", "critical"}


def read_json(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"dependency audit validation failed: cannot read {path}: {error}", file=sys.stderr)
        raise SystemExit(1) from error


def exception_ids(document: object, scanner: str) -> set[str]:
    if not isinstance(document, dict) or not isinstance(document.get("exceptions"), list):
        print("dependency audit validation failed: invalid security exceptions document", file=sys.stderr)
        raise SystemExit(1)
    return {
        entry["id"]
        for entry in document["exceptions"]
        if isinstance(entry, dict) and entry.get("scanner") == scanner and isinstance(entry.get("id"), str)
    }


def pip_audit_findings(report: object) -> list[tuple[str, str, str]]:
    findings: list[tuple[str, str, str]] = []
    if not isinstance(report, dict):
        return findings
    for dependency in report.get("dependencies", []):
        if not isinstance(dependency, dict):
            continue
        package = str(dependency.get("name", "unknown"))
        for vulnerability in dependency.get("vulns", []):
            if not isinstance(vulnerability, dict):
                continue
            identifier = str(vulnerability.get("id", "unknown"))
            # pip-audit does not emit a normalized severity field. Any known
            # advisory is merge-blocking unless explicitly time-boxed.
            findings.append((identifier, "known", package))
    return findings


def pnpm_audit_findings(report: object) -> list[tuple[str, str, str]]:
    findings: list[tuple[str, str, str]] = []
    if not isinstance(report, dict) or not isinstance(report.get("advisories"), dict):
        return findings
    for fallback_id, advisory in report["advisories"].items():
        if not isinstance(advisory, dict):
            continue
        severity = str(advisory.get("severity", "unknown")).lower()
        if severity not in BLOCKING_SEVERITIES:
            continue
        identifier = str(advisory.get("github_advisory_id") or fallback_id)
        package = str(advisory.get("module_name", "unknown"))
        findings.append((identifier, severity, package))
    return findings


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in {"pip-audit", "pnpm-audit"}:
        raise SystemExit("usage: check_dependency_audit.py <pip-audit|pnpm-audit> <report.json> <exceptions.json>")
    scanner, report_path, exceptions_path = sys.argv[1:]
    ignored = exception_ids(read_json(exceptions_path), scanner)
    report = read_json(report_path)
    findings = pip_audit_findings(report) if scanner == "pip-audit" else pnpm_audit_findings(report)
    unapproved = [finding for finding in findings if finding[0] not in ignored]
    if unapproved:
        details = ", ".join(f"{identifier} ({severity}, {package})" for identifier, severity, package in unapproved)
        print(f"{scanner} blocking advisories: {details}", file=sys.stderr)
        raise SystemExit(1)
    print(f"{scanner} audit passed: {len(findings)} finding(s), {len(ignored)} documented exception(s)")


if __name__ == "__main__":
    main()
