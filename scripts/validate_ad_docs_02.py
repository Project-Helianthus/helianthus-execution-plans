#!/usr/bin/env python3
"""Typed, fail-closed validator for the AD-DOCS-02 control-plane amendment."""
from __future__ import annotations

import hashlib
import json
import re
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
    "MSP-03D-R": ["MSP-DOCS-CLEAN", "MSP-03C"],
}
ACTIVE_ROUTING_CONTRACT = {
    "resolver": "canonical_resolver",
    "policy_digest": "canonical_policy_digest",
    "forbidden_tier": "Ultra",
}
MUTABLE_PATHS = frozenset({
    "multi-runtime-semantic-platform.locked/00-canonical.md",
    "multi-runtime-semantic-platform.locked/01-index.md",
    "multi-runtime-semantic-platform.locked/10-platform-taxonomy-and-boundaries.md",
    "multi-runtime-semantic-platform.locked/11-ebus-040-baseline-and-profile-split.md",
    "multi-runtime-semantic-platform.locked/12-eebus-mcp-first-vr940f.md",
    "multi-runtime-semantic-platform.locked/13-semantic-fact-graph-and-integration.md",
    "multi-runtime-semantic-platform.locked/14-execution-roadmap-issues-and-gates.md",
    "multi-runtime-semantic-platform.locked/90-issue-map.md",
    "multi-runtime-semantic-platform.locked/91-milestone-map.md",
    "multi-runtime-semantic-platform.locked/92-m0-issue-matrix.yaml",
    "multi-runtime-semantic-platform.locked/99-status.md",
    "multi-runtime-semantic-platform.locked/plan.yaml",
    "multi-runtime-semantic-platform.locked/105-ad-docs-02-amendment.md",
    "multi-runtime-semantic-platform.locked/106-ad-docs-02-integrity.json",
    "multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md",
    "scripts/validate_ad_docs_02.py",
    "scripts/validate_msp_r00_l_ledger.py",
    "scripts/validate_plans_repo.sh",
    "tests/test_ad_docs_02_red.py",
    "tests/test_validate_ad_docs_02.py",
    "tests/test_validate_msp_r00_l_ledger.py",
})

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
    if data["routing_contract"] != ACTIVE_ROUTING_CONTRACT:
        fail("integrity: routing contract drift")
    if data["entry_kinds"] != ["eligibility", "exact_membership", "channel_registry", "absence_constraint"]:
        fail("integrity: entry kinds drift")
    if data["publication_entry_kinds"] != ["canonical_document", "canonical_collection", "summary_pointer"]:
        fail("integrity: publication entry kinds drift")
    exact_keys(data["eligible_channels"], {"stable"}, "eligible_channels")
    if data["eligible_channels"] != {"stable": ["canonical"]}:
        fail("integrity: eligibility drift")
    exact_keys(data["exact_memberships"], {"stable"}, "exact_memberships")
    exact_keys(data["exact_memberships"]["stable"], {"canonical"}, "exact_memberships.stable")
    if data["exact_memberships"] != {"stable": {"canonical": []}}:
        fail("integrity: exact memberships drift")
    exact_keys(data["channel_registry"], {"canonical"}, "channel_registry")
    exact_keys(data["channel_registry"]["canonical"], {"visibility", "owner"}, "channel_registry.canonical")
    if data["channel_registry"] != {"canonical": {"visibility": "stable", "owner": "canonical_documentation_owner"}}:
        fail("integrity: channel registry drift")
    if data["absence_constraints"] != ["candidate entries are absent from stable outputs", "summary pointers do not claim canonical membership"]:
        fail("integrity: absence constraints drift")
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
    if data["planned_expiry"] != {"state": "planned", "action": "block_new_publication"}:
        fail("integrity: planned expiry drift")
    if data["candidate_cleanup"] != {"state": "candidate", "fail_closed": True, "post_consumption_rollback": "forward_fix_only", "action": "withdraw_candidate_and_require_fresh_cycle"}:
        fail("integrity: expiry/cleanup drift")
    exact_keys(data["process_attestation"], {"distinct_from"}, "process_attestation")
    if data["process_attestation"] != {"distinct_from": "technical_git_object_proof"}:
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
            if row["routing_contract"] != ACTIVE_ROUTING_CONTRACT:
                fail("matrix: active routing contract drift")
        else:
            exact_keys(row["routing_evidence"], {"recorded"}, f"matrix.{row['id']}.routing_evidence")
            if row["routing_evidence"] != {"recorded": "historical_observed"}:
                fail("matrix: historical routing evidence drift")
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
    if by_id["MSP-03D-R"].get("evidence_inputs") != ["MSP-03D-G01"]:
        fail("matrix: MSP-03D-G01 must remain evidence-only")
    if "MSP-DOCS-E2" in by_id["MSP-DOCS-CLEAN"].get("requires_completion_tokens", []):
        fail("matrix: direct E2-to-CLEAN path")

def render_live_audit(matrix: dict[str, Any]) -> str:
    rows = matrix["issues"]
    snapshot = {
        "ids": [row["id"] for row in rows],
        "completion_tokens": {row["id"]: row.get("requires_completion_tokens", []) for row in rows},
        "routing_authority": {row["id"]: "contract" if "routing_contract" in row else "evidence" for row in rows},
        "evidence_inputs": {row["id"]: row["evidence_inputs"] for row in rows if "evidence_inputs" in row},
    }
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return "\n".join((
        "# AD-DOCS-02 Live Topology Audit",
        "",
        f"Anchor: `{ANCHOR}`",
        f"Matrix snapshot SHA-256: `{digest}`",
        "",
        "```json",
        encoded,
        "```",
        "",
        "107 complete projection: requires_completion_tokens are authoritative; evidence_inputs are non-authoritative.",
        "Readiness: readiness snapshot, logical-ready, dispatchable, selected-batch.",
        "",
    ))

def validate_live_audit(matrix: dict[str, Any], text: str) -> None:
    if text != render_live_audit(matrix):
        fail("live audit: deterministic matrix projection drift")

def validate_surfaces(root: Path) -> None:
    plan_dir = root / PLAN
    matrix = load_yaml(plan_dir / MATRIX)
    integrity = load_json(plan_dir / INTEGRITY)
    validate_matrix(matrix)
    validate_integrity(integrity)
    validate_live_audit(matrix, (plan_dir / "107-ad-docs-02-topology-audit.md").read_text(encoding="utf-8"))
    expected_reference = "Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json."
    for surface in ("00-canonical.md", "12-eebus-mcp-first-vr940f.md", "14-execution-roadmap-issues-and-gates.md", "90-issue-map.md", "91-milestone-map.md", "99-status.md"):
        surface_text = (plan_dir / surface).read_text(encoding="utf-8")
        if expected_reference not in surface_text:
            fail("surfaces: missing structured routing reference")
        if re.search(r"(?i)\bmodel[ _-]?lane\b|\bprovider\s*[:=]|\bmodel\s*[:=]|\bgpt-", surface_text):
            fail("surfaces: active routing pin")
        if re.search(r"MSP-DOCS-E2\s*(?:->|→|to)\s*MSP-DOCS-CLEAN", surface_text, re.IGNORECASE) or re.search(r"(?m)^\|.*MSP-DOCS-E2.*MSP-DOCS-CLEAN.*\|", surface_text):
            fail("surfaces: direct E2-to-CLEAN path")

def validate_changed_paths(root: Path = ROOT) -> None:
    present = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{ANCHOR}^{{commit}}"],
        text=True,
        capture_output=True,
    )
    if present.returncode != 0:
        try:
            subprocess.run(
                ["git", "-C", str(root), "fetch", "--quiet", "--unshallow", "origin"],
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise ValidationError("protected-path anchor is unavailable") from exc
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", ANCHOR, "--"],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ValidationError("protected-path anchor is unavailable") from exc
    for path in filter(None, result.stdout.splitlines()):
        if path not in MUTABLE_PATHS:
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
