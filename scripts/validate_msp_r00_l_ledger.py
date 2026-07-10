#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT_KEYS = frozenset({"artifact_kind", "entries"})
ENTRY_KEYS = frozenset(
    {
        "opaque_public_id",
        "clean_main_issue_ref",
        "public_class",
        "disposition",
        "redaction_categories",
    }
)
REDACTION_KEYS = frozenset(
    {
        "origin_locator",
        "runtime_identity",
        "evidence_payload",
        "integrity_preimage",
        "quantity_observation",
        "temporal_observation",
    }
)
ARTIFACT_KIND = "msp_r00_l_public_redacted_recovery_ledger"
ALLOWED_ISSUE_REF = "Project-Helianthus/helianthus-eebusreg#14"
ALLOWED_ENUMS = frozenset({"public_redacted", "private_restricted", "discarded"})
REDACTION_VALUE = "redacted"
ROOT = Path(__file__).resolve().parents[1]
PLAN_SLUG = "multi-runtime-semantic-platform"
ACTIVE_STATES = ("locked", "implementing", "maintenance")
LEDGER_FILENAME = "104-msp-r00-l-public-redacted-ledger.json"

FORBIDDEN_KEY_FRAGMENTS = (
    "bundle",
    "capture",
    "commit",
    "count",
    "credential",
    "device",
    "hash",
    "hmac",
    "ip",
    "mac",
    "measurement",
    "network",
    "path",
    "serial",
    "sha",
    "shipid",
    "ski",
    "source",
    "timestamp",
    "transcript",
    "trust",
)
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"\b(?:bundle|capture|commit|credential|device|hash|hmac|measurement|network|path|serial|sha|shipid|ski|source|timestamp|transcript|trust)\b", re.IGNORECASE),
    re.compile(r"\b(?:ip|mac)\b", re.IGNORECASE),
    re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE),
    re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b"),
    re.compile(r"(?:^|[\s=])/(?:Users|home|var|tmp|mnt|etc|data|private)\b"),
    re.compile(r"[A-Za-z]:\\"),
)


class ValidationError(ValueError):
    pass


def _fail(message: str) -> None:
    raise ValidationError(message)


def resolve_default_ledger(root: Path = ROOT) -> Path:
    candidates = [
        root / f"{PLAN_SLUG}.{state}"
        for state in ACTIVE_STATES
        if (root / f"{PLAN_SLUG}.{state}").is_dir()
    ]
    if not candidates:
        _fail(
            f"no active {PLAN_SLUG} directory found for states "
            f"{'|'.join(ACTIVE_STATES)}"
        )
    if len(candidates) > 1:
        formatted = ", ".join(str(path) for path in candidates)
        _fail(f"multiple active {PLAN_SLUG} directories found: {formatted}")
    ledger = candidates[0] / LEDGER_FILENAME
    if not ledger.is_file():
        _fail(f"{candidates[0]}: missing {LEDGER_FILENAME}")
    return ledger


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_json_without_duplicate_keys(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_object_keys,
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc


def _require_exact_keys(value: Any, expected: frozenset[str], where: str) -> None:
    if not isinstance(value, dict):
        _fail(f"{where}: expected object")
    actual = set(value)
    if actual != expected:
        _fail(f"{where}: expected keys {sorted(expected)}, got {sorted(actual)}")
    for key in actual:
        lowered = key.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
            _fail(f"{where}: forbidden key {key!r}")


def _require_uuid_v4(value: Any, where: str) -> None:
    if not isinstance(value, str):
        _fail(f"{where}: expected string")
    try:
        parsed = uuid.UUID(value, version=4)
    except ValueError as exc:
        raise ValidationError(f"{where}: expected UUIDv4") from exc
    if str(parsed) != value or parsed.version != 4:
        _fail(f"{where}: expected canonical UUIDv4")


def _scan_value(value: Any, where: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
                _fail(f"{where}: forbidden key {key!r}")
            _scan_value(nested, f"{where}.{key}")
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _scan_value(nested, f"{where}[{index}]")
        return
    if not isinstance(value, str):
        return
    for pattern in FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(value):
            _fail(f"{where}: forbidden public value")


def validate_ledger(path: Path | None = None, root: Path = ROOT) -> None:
    if path is None:
        path = resolve_default_ledger(root)
    data = _load_json_without_duplicate_keys(path)

    _require_exact_keys(data, ROOT_KEYS, "$")
    if data["artifact_kind"] != ARTIFACT_KIND:
        _fail("$.artifact_kind: unexpected artifact kind")
    if not isinstance(data["entries"], list) or not data["entries"]:
        _fail("$.entries: expected non-empty array")

    seen_ids: set[str] = set()
    for index, entry in enumerate(data["entries"]):
        where = f"$.entries[{index}]"
        _require_exact_keys(entry, ENTRY_KEYS, where)
        _require_uuid_v4(entry["opaque_public_id"], f"{where}.opaque_public_id")
        if entry["opaque_public_id"] in seen_ids:
            _fail(f"{where}.opaque_public_id: duplicate UUID")
        seen_ids.add(entry["opaque_public_id"])
        if entry["clean_main_issue_ref"] != ALLOWED_ISSUE_REF:
            _fail(f"{where}.clean_main_issue_ref: unexpected issue reference")
        if entry["public_class"] not in ALLOWED_ENUMS:
            _fail(f"{where}.public_class: unexpected enum")
        if entry["disposition"] not in ALLOWED_ENUMS:
            _fail(f"{where}.disposition: unexpected enum")
        if entry["public_class"] != entry["disposition"]:
            _fail(f"{where}: public_class must match disposition")

        redaction = entry["redaction_categories"]
        _require_exact_keys(redaction, REDACTION_KEYS, f"{where}.redaction_categories")
        for key, value in redaction.items():
            if value != REDACTION_VALUE:
                _fail(f"{where}.redaction_categories.{key}: unexpected value")

        scannable_entry = {
            key: value
            for key, value in entry.items()
            if key not in {"opaque_public_id", "clean_main_issue_ref"}
        }
        _scan_value(scannable_entry, where)


def main(argv: list[str]) -> int:
    try:
        path = Path(argv[1]) if len(argv) == 2 else resolve_default_ledger()
        validate_ledger(path)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"validated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
