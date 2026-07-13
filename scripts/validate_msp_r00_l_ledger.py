#!/usr/bin/env python3
from __future__ import annotations

import json
import importlib.util
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

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
MATRIX_FILENAME = "92-m0-issue-matrix.yaml"
ISSUE_MAP_FILENAME = "90-issue-map.md"
STATUS_FILENAME = "99-status.md"
TOPOLOGY_FILENAME = "100-topology-audit.md"
LIVE_TOPOLOGY_FILENAME = "107-ad-docs-02-topology-audit.md"

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


class _UniqueKeySafeLoader(yaml.SafeLoader):
    pass


def _fail(message: str) -> None:
    raise ValidationError(message)


def _construct_unique_yaml_mapping(
    loader: _UniqueKeySafeLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            _fail(f"{MATRIX_FILENAME}: duplicate YAML key")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_yaml_mapping,
)


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
        formatted = ", ".join(path.name for path in candidates)
        _fail(f"multiple active {PLAN_SLUG} directories found: {formatted}")
    ledger = candidates[0] / LEDGER_FILENAME
    if not ledger.is_file():
        _fail(f"{candidates[0].name}: missing {LEDGER_FILENAME}")
    return ledger


def resolve_default_plan_dir(root: Path = ROOT) -> Path:
    ledger = resolve_default_ledger(root)
    return ledger.parent


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON key")
        result[key] = value
    return result


def _load_json_without_duplicate_keys(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationError("ledger: unable to read UTF-8 input") from exc
    try:
        return json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_object_keys,
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"ledger: invalid JSON: {exc}") from exc


def _read_required_text(path: Path) -> str:
    if not path.is_file():
        _fail(f"{path.name}: missing required file")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"{path.name}: unable to read UTF-8 required input") from exc


def _extract_matrix_row(text: str, row_id: str) -> str:
    pattern = re.compile(
        rf"(?ms)^  - id: {re.escape(row_id)}\n(?P<row>.*?)(?=^  - id: |\Z)"
    )
    match = pattern.search(text)
    if match is None:
        _fail(f"{MATRIX_FILENAME}: missing row {row_id}")
    return match.group("row")


def _require_contains(text: str, needle: str, where: str) -> None:
    if needle not in text:
        _fail(f"{where}: missing {needle!r}")


def _acceptance_state(row: str, row_id: str) -> str:
    states = re.findall(r"(?m)^    acceptance_state: ([a-z_]+)$", row)
    if len(states) != 1:
        _fail(f"{row_id} matrix row: expected exactly one acceptance_state")
    return states[0]


def _validate_topology_ready_set(matrix: str, topology: str) -> None:
    try:
        document = yaml.load(matrix, Loader=_UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        raise ValidationError(f"{MATRIX_FILENAME}: invalid YAML") from exc
    if not isinstance(document, dict) or not isinstance(document.get("issues"), list):
        _fail(f"{MATRIX_FILENAME}: issues must be a list")
    rows = document["issues"]
    if not rows or not all(isinstance(row, dict) for row in rows):
        _fail(f"{MATRIX_FILENAME}: issues must contain mappings")

    row_ids: list[str] = []
    for row in rows:
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id:
            _fail(f"{MATRIX_FILENAME}: every issue requires a non-empty string id")
        row_ids.append(row_id)
    if len(set(row_ids)) != len(row_ids):
        _fail(f"{MATRIX_FILENAME}: duplicate issue IDs")

    states: dict[str, str] = {}
    predecessors: dict[str, list[str]] = {}
    model_lanes: dict[str, str] = {}
    complexities: dict[str, int] = {}
    rows_by_id = dict(zip(row_ids, rows, strict=True))
    for row_id, row in rows_by_id.items():
        state = row.get("acceptance_state")
        deps = row.get("predecessors")
        lane = row.get("model_lane")
        complexity = row.get("complexity")
        if not isinstance(state, str):
            _fail(f"{MATRIX_FILENAME}: issue acceptance_state must be a string")
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps):
            _fail(f"{MATRIX_FILENAME}: issue predecessors must be a string list")
        if not isinstance(lane, str):
            _fail(f"{MATRIX_FILENAME}: issue model_lane must be a string")
        if type(complexity) is not int or not 1 <= complexity <= 10:
            _fail(f"{MATRIX_FILENAME}: issue complexity must be an integer from 1 through 10")
        states[row_id] = state
        predecessors[row_id] = deps
        model_lanes[row_id] = lane
        complexities[row_id] = complexity

    missing = [
        [row_id, dep]
        for row_id in row_ids
        for dep in predecessors[row_id]
        if dep not in states
    ]
    if missing:
        _fail(f"{MATRIX_FILENAME}: missing predecessor references")

    visits: dict[str, int] = {}
    cycles: list[list[str]] = []

    def visit(row_id: str, stack: list[str]) -> None:
        if visits.get(row_id) == 1:
            cycles.append(stack + [row_id])
            return
        if visits.get(row_id) == 2:
            return
        visits[row_id] = 1
        for predecessor in predecessors[row_id]:
            visit(predecessor, stack + [row_id])
        visits[row_id] = 2

    for row_id in row_ids:
        visit(row_id, [])
    if cycles:
        _fail(f"{MATRIX_FILENAME}: dependency cycles")

    accepted = {
        "accepted",
        "accepted_partial_no_successor_unlock",
        "completed_local_no_code_acceptance",
    }
    ready = [
        row_id
        for row_id in row_ids
        if states[row_id] == "ready"
        and all(states.get(dep) in accepted for dep in predecessors[row_id])
    ]

    lane_mismatches: list[list[Any]] = []
    for row_id in row_ids:
        complexity = complexities[row_id]
        expected = (
            "GPT-5.3-Codex-Spark"
            if complexity in (1, 2)
            else "gpt-5.4-mini"
            if complexity in (3, 4)
            else "GPT-5.5 medium"
            if complexity == 5
            else "GPT-5.5 high"
            if complexity in (6, 7)
            else "GPT-5.5 xhigh"
        )
        if model_lanes[row_id] != expected:
            lane_mismatches.append([row_id, model_lanes[row_id], expected])
    if lane_mismatches:
        _fail(f"{MATRIX_FILENAME}: model-lane mismatches")

    def reported_json(label: str) -> Any:
        match = re.search(rf"(?m)^- {re.escape(label)}: `(?P<value>[^\n]+)`$", topology)
        if match is None:
            _fail(f"{TOPOLOGY_FILENAME}: missing {label.lower()}")
        try:
            return json.loads(match.group("value"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{TOPOLOGY_FILENAME}: invalid JSON for {label}") from exc

    expected_results = {
        "Row count": len(row_ids),
        "Unique IDs": len(set(row_ids)),
        "Missing predecessor references": missing,
        "Cycles": cycles,
        "Current ready set": ready,
        "Model-lane mismatches": lane_mismatches,
    }
    for label, expected in expected_results.items():
        reported = reported_json(label)
        if reported != expected:
            _fail(f"{TOPOLOGY_FILENAME}: {label} does not match computed result")

    cleanup_row = rows_by_id.get("MSP-DOCS-CANDIDATE-CLEANUP")
    cleanup = cleanup_row.get("conditional") if isinstance(cleanup_row, dict) else None
    cleanup_keys = {
        "activates_when",
        "initially_ready",
        "required_predecessor_for_normal_successors",
        "preempts_same_repo_successors",
        "blocks_cross_repo_source_rows",
    }
    cleanup_ok = (
        isinstance(cleanup, dict)
        and set(cleanup) == cleanup_keys
        and cleanup_row.get("acceptance_state") == "dormant_conditional"
        and cleanup.get("activates_when") == "candidate expires or source PR closes unmerged"
        and cleanup.get("initially_ready") is False
        and cleanup.get("required_predecessor_for_normal_successors") is False
        and cleanup.get("preempts_same_repo_successors") is True
        and cleanup.get("blocks_cross_repo_source_rows") == ["MSP-055"]
    )
    if not cleanup_ok:
        _fail("MSP-DOCS-CANDIDATE-CLEANUP matrix row: conditional contract drift")
    _require_contains(
        topology,
        "- Dormant conditional cleanup row with `MSP-055` cross-repo blocker:\n  `MSP-DOCS-CANDIDATE-CLEANUP`",
        TOPOLOGY_FILENAME,
    )


def validate_plan_state_surfaces(root: Path = ROOT) -> None:
    module_path = ROOT / "scripts" / "validate_ad_docs_02.py"
    spec = importlib.util.spec_from_file_location("validate_ad_docs_02", module_path)
    if spec is None or spec.loader is None:
        _fail("AD-DOCS-02 validator unavailable")
    ad_validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ad_validator)
    try:
        ad_validator.validate_surfaces(root)
    except ad_validator.ValidationError as exc:
        raise ValidationError(str(exc)) from exc


def _require_exact_keys(value: Any, expected: frozenset[str], where: str) -> None:
    if not isinstance(value, dict):
        _fail(f"{where}: expected object")
    actual = set(value)
    if actual != expected:
        _fail(f"{where}: object keys do not match the public schema")
    for key in actual:
        lowered = key.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
            _fail(f"{where}: forbidden key category")


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
                _fail(f"{where}: forbidden key category")
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
        if not isinstance(entry["public_class"], str) or entry["public_class"] not in ALLOWED_ENUMS:
            _fail(f"{where}.public_class: unexpected enum")
        if not isinstance(entry["disposition"], str) or entry["disposition"] not in ALLOWED_ENUMS:
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
        if len(argv) not in (1, 2):
            _fail("usage: validate_msp_r00_l_ledger.py [ledger.json]")
        path = Path(argv[1]) if len(argv) == 2 else resolve_default_ledger()
        validate_ledger(path)
        if len(argv) != 2:
            validate_plan_state_surfaces()
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"validated {ARTIFACT_KIND}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
