#!/usr/bin/env python3
"""Typed, fail-closed validator for the AD-DOCS-02 control-plane amendment."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLAN = "multi-runtime-semantic-platform.locked"
ANCHOR = "f25d9ac7d3f25f0f45821cdff27ff968a0ef5cfb"
MATRIX = "92-m0-issue-matrix.yaml"
INTEGRITY = "106-ad-docs-02-integrity.json"
EXACT_IDS = (
    "MSP-00A", "MSP-00B", "MSP-00C", "MSP-01A", "MSP-01B", "MSP-01C",
    "MSP-020", "MSP-02A", "MSP-02B", "MSP-02C", "MSP-03A", "MSP-03B",
    "MSP-03C", "MSP-03D-G01", "MSP-R00", "MSP-R00-L", "DOCS-VERIFY",
    "MSP-DOCS-API-SCHEMA", "MSP-DOCS-PLATFORM", "MSP-DOCS-E2",
    "MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-E2R-PUBLISH",
    "MSP-DOCS-E2R-AGGREGATE", "MSP-DOCS-CLEAN",
    "MSP-DOCS-CANDIDATE-CLEANUP", "MSP-03D-R", "MSP-035", "MSP-04A",
    "MSP-036", "MSP-DOCS-API-CANDIDATE", "MSP-055", "MSP-DOCS-API-FREEZE",
    "MSP-04B", "MSP-04C", "MSP-045", "MSP-05A", "MSP-05B", "MSP-06",
    "MSP-065", "MSP-07", "MSP-08", "MSP-085", "MSP-09A", "MSP-09B",
    "MSP-09C", "MSP-09D",
)
E2_ROOTS = (
    "62e4c2f2022c22f5129db923079268aafdc5617b",
    "6476e39811677041ba11911457baab4c602ac557",
)
SERIAL_EDGES = {
    "MSP-DOCS-E2R-PLATFORM": ["MSP-DOCS-E2"],
    "MSP-DOCS-E2R-PUBLISH": ["MSP-DOCS-E2R-PLATFORM"],
    "MSP-DOCS-E2R-AGGREGATE": ["MSP-DOCS-E2R-PUBLISH"],
    "MSP-DOCS-CLEAN": ["MSP-DOCS-E2R-AGGREGATE"],
}
MUTABLE_PREFIXES = (
    "multi-runtime-semantic-platform.locked/plan.yaml",
    "multi-runtime-semantic-platform.locked/00-", "multi-runtime-semantic-platform.locked/01-",
    "multi-runtime-semantic-platform.locked/10-", "multi-runtime-semantic-platform.locked/11-",
    "multi-runtime-semantic-platform.locked/12-", "multi-runtime-semantic-platform.locked/13-",
    "multi-runtime-semantic-platform.locked/14-", "multi-runtime-semantic-platform.locked/90-",
    "multi-runtime-semantic-platform.locked/91-", "multi-runtime-semantic-platform.locked/92-",
    "multi-runtime-semantic-platform.locked/99-", "multi-runtime-semantic-platform.locked/105-",
    "multi-runtime-semantic-platform.locked/106-", "multi-runtime-semantic-platform.locked/107-",
    "scripts/validate_ad_docs_02.py", "scripts/validate_msp_r00_l_ledger.py", "scripts/validate_plans_repo.sh",
    "tests/test_ad_docs_02_red.py", "tests/test_validate_ad_docs_02.py",
    "tests/test_validate_msp_r00_l_ledger.py",
)

class ValidationError(ValueError):
    pass

class UniqueLoader(yaml.SafeLoader):
    pass

def fail(message: str) -> None:
    raise ValidationError(message)

def _mapping(loader: UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            fail("matrix: duplicate YAML key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)

def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            fail("integrity: duplicate JSON key")
        value[key] = item
    return value

def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValidationError("matrix: invalid YAML") from exc
    if not isinstance(data, dict):
        fail("matrix: expected object")
    return data

def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_json_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("integrity: invalid JSON") from exc
    if not isinstance(data, dict):
        fail("integrity: expected object")
    return data

def exact_keys(value: Any, keys: set[str], where: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        fail(f"{where}: closed schema violation")

def validate_integrity(data: dict[str, Any]) -> None:
    keys = {"schema_version", "e2_merge_roots", "completion_token_roots", "evidence_inputs",
            "routing_contract", "entry_kinds", "publication_entry_kinds", "eligible_channels",
            "exact_memberships", "channel_registry", "absence_constraints",
            "hermetic_git_object_evidence", "token_envelope", "readiness_categories",
            "planned_expiry", "candidate_cleanup", "process_attestation"}
    exact_keys(data, keys, "integrity")
    if data["schema_version"] != 2 or data["e2_merge_roots"] != list(E2_ROOTS):
        fail("integrity: E2 roots drift")
    if data["completion_token_roots"] != sorted(E2_ROOTS):
        fail("integrity: completion roots drift")
    exact_keys(data["evidence_inputs"], {"MSP-R00", "MSP-03D-G01"}, "evidence_inputs")
    if data["evidence_inputs"] != {"MSP-R00": ["Project-Helianthus/helianthus-eebusreg#14"], "MSP-03D-G01": ["MSP-03D-G01"]}:
        fail("integrity: evidence authority drift")
    exact_keys(data["routing_contract"], {"resolver", "policy_digest", "forbidden_tier"}, "routing_contract")
    if data["routing_contract"] != {"resolver": "canonical", "policy_digest": "required_at_dispatch", "forbidden_tier": "highest_reserved_tier"}:
        fail("integrity: routing contract drift")
    if set(data["entry_kinds"]) != {"eligibility", "exact_membership", "channel_registry", "absence_constraint"}:
        fail("integrity: entry kinds drift")
    exact_keys(data["eligible_channels"], {"stable"}, "eligible_channels")
    exact_keys(data["exact_memberships"], {"stable"}, "exact_memberships")
    exact_keys(data["exact_memberships"]["stable"], {"canonical"}, "exact_memberships.stable")
    exact_keys(data["channel_registry"], {"canonical"}, "channel_registry")
    exact_keys(data["channel_registry"]["canonical"], {"visibility", "owner"}, "channel_registry.canonical")
    exact_keys(data["hermetic_git_object_evidence"], {"required", "moving_refs_rejected"}, "hermetic_git_object_evidence")
    if set(data["hermetic_git_object_evidence"]["required"]) != {"base_oid", "head_oid", "merge_oid", "tree_oid", "evidence_core_sha256"} or data["hermetic_git_object_evidence"]["moving_refs_rejected"] is not True:
        fail("integrity: hermetic git-object evidence drift")
    exact_keys(data["token_envelope"], {"schema_version", "identity_fields", "replay_rejected", "drift_rejected"}, "token_envelope")
    if data["token_envelope"]["schema_version"] != 2 or set(data["token_envelope"]["identity_fields"]) != {"producer_id", "consumer_id", "repository", "pr", "base_oid", "head_oid", "merge_oid", "tree_oid", "evidence_core_sha256", "prior_token_digest", "observation_source"} or data["token_envelope"]["replay_rejected"] is not True or data["token_envelope"]["drift_rejected"] is not True:
        fail("integrity: token envelope identity/replay/drift drift")
    if data["readiness_categories"] != ["historical_snapshot", "logical_ready", "dispatchable", "selected_batch"]:
        fail("integrity: readiness categories drift")
    exact_keys(data["planned_expiry"], {"state", "action"}, "planned_expiry")
    exact_keys(data["candidate_cleanup"], {"state", "fail_closed", "post_consumption_rollback", "action"}, "candidate_cleanup")
    if data["candidate_cleanup"]["fail_closed"] is not True or data["candidate_cleanup"]["post_consumption_rollback"] != "forward_fix_only":
        fail("integrity: expiry/cleanup drift")
    exact_keys(data["process_attestation"], {"distinct_from"}, "process_attestation")
    if data["process_attestation"]["distinct_from"] != "technical_git_object_proof":
        fail("integrity: process attestation drift")

def validate_matrix(data: dict[str, Any]) -> None:
    rows = data.get("issues")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        fail("matrix: issues must be mappings")
    ids = [row.get("id") for row in rows]
    if tuple(ids) != EXACT_IDS:
        fail("matrix: exact 46 ID contract drift")
    by_id = {row["id"]: row for row in rows}
    visiting: set[str] = set()
    visited: set[str] = set()
    for row in rows:
        if "model_lane" in row or "predecessors" in row:
            fail("matrix: active legacy routing/dependency field")
        contract, evidence = "routing_contract" in row, "routing_evidence" in row
        if contract == evidence:
            fail("matrix: exactly one routing authority required")
        if contract:
            exact_keys(row["routing_contract"], {"resolver", "policy_digest", "forbidden_tier"}, f"matrix.{row['id']}.routing_contract")
            if row["routing_contract"].get("forbidden_tier") != "highest_reserved_tier" or "ultra" in json.dumps(row["routing_contract"]).lower():
                fail("matrix: forbidden active routing tier")
        if not isinstance(row.get("requires_completion_tokens", []), list):
            fail("matrix: completion tokens must be a list")
    def visit(row_id: str) -> None:
        if row_id in visiting:
            fail("matrix: dependency cycle")
        if row_id in visited:
            return
        visiting.add(row_id)
        for dep in by_id[row_id].get("requires_completion_tokens", []):
            if dep not in by_id:
                fail("matrix: unknown completion token")
            visit(dep)
        visiting.remove(row_id)
        visited.add(row_id)
    for row_id in by_id:
        visit(row_id)
    for row_id, expected in SERIAL_EDGES.items():
        if by_id[row_id].get("requires_completion_tokens") != expected:
            fail("matrix: required serial edge drift")
    if "MSP-DOCS-E2" in by_id["MSP-DOCS-CLEAN"].get("requires_completion_tokens", []):
        fail("matrix: direct E2-to-CLEAN path")

def validate_surfaces(root: Path) -> None:
    plan_dir = root / PLAN
    matrix = load_yaml(plan_dir / MATRIX)
    integrity = load_json(plan_dir / INTEGRITY)
    validate_matrix(matrix)
    validate_integrity(integrity)
    names = ("plan.yaml", "00-canonical.md", "01-index.md", "12-eebus-mcp-first-vr940f.md",
             "14-execution-roadmap-issues-and-gates.md", "90-issue-map.md", "91-milestone-map.md",
             "92-m0-issue-matrix.yaml", "99-status.md", "107-ad-docs-02-topology-audit.md")
    text = "\n".join((plan_dir / name).read_text(encoding="utf-8") for name in names)
    if "MSP-DOCS-E2 -> MSP-DOCS-CLEAN" in text:
        fail("surfaces: direct E2-to-CLEAN path")
    if "model_lane:" in text:
        fail("surfaces: active model_lane")
    if "forbidden_tier: ultra" in text.lower():
        fail("surfaces: active forbidden tier")
    compact = " ".join(text.split())
    if "MSP-DOCS-E2R-PLATFORM -> MSP-DOCS-E2R-PUBLISH -> MSP-DOCS-E2R-AGGREGATE -> MSP-DOCS-CLEAN" not in compact:
        fail("surfaces: serial chain is not synchronized")

def validate_changed_paths(root: Path = ROOT) -> None:
    result = subprocess.run(["git", "-C", str(root), "diff", "--name-only", ANCHOR, "--"], text=True, capture_output=True, check=True)
    for path in filter(None, result.stdout.splitlines()):
        if not path.startswith(MUTABLE_PREFIXES):
            fail(f"protected path changed: {path}")

def main(argv: list[str]) -> int:
    try:
        if len(argv) != 1:
            fail("usage: validate_ad_docs_02.py")
        validate_surfaces(ROOT)
        validate_changed_paths(ROOT)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print("validated AD-DOCS-02")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
