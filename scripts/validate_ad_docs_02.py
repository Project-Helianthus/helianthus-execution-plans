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
REQUIRES_COMPLETION_TOKENS = {
    "MSP-00A": [], "MSP-00B": ["MSP-00A"], "MSP-00C": ["MSP-00A"], "MSP-01A": ["MSP-00A"],
    "MSP-01B": ["MSP-01A"], "MSP-01C": ["MSP-01B"],
    "MSP-020": ["MSP-00A", "MSP-00B", "MSP-00C", "MSP-01A", "MSP-01B", "MSP-01C"],
    "MSP-02A": ["MSP-00A", "MSP-00B", "MSP-00C", "MSP-01A", "MSP-01B", "MSP-01C", "MSP-020"],
    "MSP-02B": ["MSP-02A"], "MSP-02C": ["MSP-01A", "MSP-02B"], "MSP-03A": ["MSP-02C"],
    "MSP-03B": ["MSP-03A"], "MSP-03C": ["MSP-03A", "MSP-03B"], "MSP-03D-G01": ["MSP-03C"],
    "MSP-R00": [], "MSP-R00-L": [], "DOCS-VERIFY": [], "MSP-DOCS-API-SCHEMA": ["DOCS-VERIFY"],
    "MSP-DOCS-PLATFORM": ["MSP-R00-L", "MSP-DOCS-API-SCHEMA"], "MSP-DOCS-E2": ["MSP-DOCS-PLATFORM"],
    "MSP-DOCS-E2R-PLATFORM": ["MSP-DOCS-E2"], "MSP-DOCS-E2R-PUBLISH": ["MSP-DOCS-E2R-PLATFORM"],
    "MSP-DOCS-E2R-AGGREGATE": ["MSP-DOCS-E2R-PUBLISH"], "MSP-DOCS-CLEAN": ["MSP-DOCS-E2R-AGGREGATE"],
    "MSP-DOCS-CANDIDATE-CLEANUP": ["MSP-DOCS-E2R-PUBLISH"], "MSP-03D-R": ["MSP-DOCS-CLEAN", "MSP-03C"],
    "MSP-035": ["MSP-03D-R"], "MSP-04A": ["MSP-035"], "MSP-036": ["MSP-04A"],
    "MSP-DOCS-API-CANDIDATE": ["MSP-036", "MSP-DOCS-E2"], "MSP-055": ["MSP-036", "MSP-DOCS-API-CANDIDATE"],
    "MSP-DOCS-API-FREEZE": ["MSP-055"], "MSP-04B": ["MSP-DOCS-API-FREEZE"], "MSP-04C": ["MSP-04B"],
    "MSP-045": ["MSP-04C"], "MSP-05A": ["MSP-045"], "MSP-05B": ["MSP-05A", "MSP-045"],
    "MSP-06": ["MSP-05B"], "MSP-065": ["MSP-06"], "MSP-07": ["MSP-065"], "MSP-08": ["MSP-07"],
    "MSP-085": ["MSP-08"], "MSP-09A": ["MSP-085"], "MSP-09B": ["MSP-09A"],
    "MSP-09C": ["MSP-09A", "MSP-09B"], "MSP-09D": ["MSP-09A", "MSP-09C"],
}
EVIDENCE_INPUTS = {row_id: [] for row_id in EXACT_IDS} | {
    "MSP-R00-L": ["Project-Helianthus/helianthus-eebusreg#14"], "MSP-03D-R": ["MSP-03D-G01"],
}
ACCEPTANCE_STATES = {
    **{row_id: "accepted" for row_id in EXACT_IDS[:13]}, "MSP-03D-G01": "accepted_partial_no_successor_unlock",
    "MSP-R00": "completed_local_no_code_acceptance", "MSP-R00-L": "accepted", "DOCS-VERIFY": "accepted",
    "MSP-DOCS-API-SCHEMA": "ready", "MSP-DOCS-CANDIDATE-CLEANUP": "dormant_conditional",
    **{row_id: "proposed" for row_id in EXACT_IDS[18:] if row_id != "MSP-DOCS-CANDIDATE-CLEANUP"},
}
BASE_ROW_KEYS = frozenset({"id", "title", "repo", "milestone", "complexity", "docs_owner", "doc_gate", "security_gate", "transport_gate", "rollback_ledger", "review_ledger", "tdd_mode", "smoke_scope", "acceptance_state", "requires_completion_tokens"})
NO_ACCEPTANCE = frozenset({"MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-E2R-PUBLISH", "MSP-DOCS-E2R-AGGREGATE"})
ROW_EXTRAS = {
    "MSP-R00": frozenset({"acceptance", "architecture_review", "coordination_note", "issue", "successor_unlocks"}),
    "MSP-R00-L": frozenset({"acceptance", "completion_note", "evidence_inputs"}),
    "DOCS-VERIFY": frozenset({"acceptance", "completion_note", "coordination_note"}),
    "MSP-DOCS-API-SCHEMA": frozenset({"acceptance", "readiness_note"}),
    "MSP-DOCS-PLATFORM": frozenset({"acceptance", "blocked_note"}),
    "MSP-DOCS-E2R-AGGREGATE": frozenset({"issue_ref"}),
    "MSP-DOCS-CANDIDATE-CLEANUP": frozenset({"acceptance", "conditional"}),
    "MSP-03D-R": frozenset({"acceptance", "evidence_inputs"}),
}
HISTORICAL_IDS = frozenset(EXACT_IDS[:17])
READINESS = {
    "historical_snapshot": list(EXACT_IDS[:17]),
    "logical_ready": ["MSP-DOCS-API-SCHEMA"],
    "dispatchable": ["MSP-R00-L", "DOCS-VERIFY", "MSP-DOCS-API-SCHEMA"],
    "selected_batch": ["MSP-R00-L", "DOCS-VERIFY"],
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
E2R_PREREQUISITES = (
    "MSP-DOCS-E2, MSP-DOCS-E2R-PLATFORM, MSP-DOCS-E2R-PUBLISH, "
    "MSP-DOCS-E2R-AGGREGATE, MSP-DOCS-CLEAN"
)

def active_control_surface_paths() -> tuple[str, ...]:
    """Derive the complete active plan projection from its mutable allowlist."""
    prefix = PLAN + "/"
    return tuple(sorted(path for path in MUTABLE_PATHS if path.startswith(prefix)))

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
    reject_active_routing_pin(data["routing_contract"], "integrity.routing_contract")
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
        row_id = row["id"]
        expected_keys = BASE_ROW_KEYS | ROW_EXTRAS.get(row_id, frozenset())
        if row_id not in NO_ACCEPTANCE:
            expected_keys |= {"acceptance"}
        expected_keys |= {"routing_evidence" if row_id in HISTORICAL_IDS else "routing_contract"}
        exact_keys(row, set(expected_keys), f"matrix.{row_id}")
        if "model_lane" in row or "predecessors" in row:
            fail("matrix: active legacy routing/dependency field")
        contract, evidence = "routing_contract" in row, "routing_evidence" in row
        if contract == evidence:
            fail("matrix: exactly one routing authority required")
        if contract:
            exact_keys(row["routing_contract"], {"resolver", "policy_digest", "forbidden_tier"}, f"matrix.{row['id']}.routing_contract")
            reject_active_routing_pin(row["routing_contract"], f"matrix.{row['id']}.routing_contract")
            if row["routing_contract"] != ACTIVE_ROUTING_CONTRACT:
                fail("matrix: active routing contract drift")
        else:
            exact_keys(row["routing_evidence"], {"recorded"}, f"matrix.{row['id']}.routing_evidence")
            if row["routing_evidence"] != {"recorded": "historical_observed"}:
                fail("matrix: historical routing evidence drift")
        if row["requires_completion_tokens"] != REQUIRES_COMPLETION_TOKENS[row_id]:
            fail("matrix: completion-token authority drift")
        if row.get("evidence_inputs", []) != EVIDENCE_INPUTS[row_id]:
            fail("matrix: evidence-input authority drift")
        if row["acceptance_state"] != ACCEPTANCE_STATES[row_id]:
            fail("matrix: acceptance-state authority drift")
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
        "Readiness snapshot / logical-ready / dispatchable / selected-batch categories: " + json.dumps(READINESS, sort_keys=True, separators=(",", ":")),
        "",
    ))

def validate_live_audit(matrix: dict[str, Any], text: str) -> None:
    if text != render_live_audit(matrix):
        fail("live audit: deterministic matrix projection drift")

def reject_active_routing_pin(value: Any, where: str) -> None:
    """Reject provider/model routing facts in active (not historical) contracts."""
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("model", "provider", "vendor")):
                fail(f"{where}: active routing pin")
            reject_active_routing_pin(nested, f"{where}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            reject_active_routing_pin(nested, f"{where}[{index}]")
    elif isinstance(value, str) and any(token in value.lower() for token in ("openai", "anthropic", "gpt-", "gpt_", "claude-", "claude_", "gpt5")):
        fail(f"{where}: active routing pin")

def validate_plan_projection(plan: dict[str, Any]) -> None:
    policy = plan.get("routing_policy")
    exact_keys(policy, {"resolver", "policy_digest", "forbidden_tier"}, "plan.routing_policy")
    reject_active_routing_pin(policy, "plan.routing_policy")
    if policy != {"resolver": "canonical", "policy_digest": "required_at_dispatch", "forbidden_tier": "highest_reserved_tier"}:
        fail("plan: routing policy drift")
    if plan.get("initial_ready_set") != READINESS["selected_batch"]:
        fail("plan: selected batch drift")

def validate_markdown_claims(plan_dir: Path, matrix: dict[str, Any]) -> None:
    expected_reference = "Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json."
    surfaces = tuple(
        Path(relative).name
        for relative in active_control_surface_paths()
        if relative.endswith(".md") and Path(relative).name != "107-ad-docs-02-topology-audit.md"
    )
    for surface in surfaces:
        text = (plan_dir / surface).read_text(encoding="utf-8")
        if expected_reference not in text:
            fail(f"surfaces.{surface}: missing structured routing reference")
        if re.search(r"(?i)\bmodel[ _-]?lane\b|\b(?:provider|vendor)\s*[:=]|\bmodel\s*[:=]|\b(?:gpt|claude)-", text):
            fail(f"surfaces.{surface}: active routing pin")
        if re.search(r"MSP-DOCS-E2\s*(?:->|→|to)\s*MSP-DOCS-CLEAN", text, re.IGNORECASE) or re.search(r"(?m)^\|.*MSP-DOCS-E2.*MSP-DOCS-CLEAN.*\|", text):
            fail(f"surfaces.{surface}: direct E2-to-CLEAN path")
        if re.search(r"MSP-DOCS-CLEAN.{0,160}(?:requires|completion[ -]?token).{0,160}MSP-DOCS-E2", text, re.IGNORECASE | re.DOTALL):
            fail(f"surfaces.{surface}: CLEAN token bypass")
    roadmap = (plan_dir / "14-execution-roadmap-issues-and-gates.md").read_text(encoding="utf-8")
    for row_id, tokens in REQUIRES_COMPLETION_TOKENS.items():
        if row_id in {"MSP-DOCS-E2", "MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-E2R-PUBLISH", "MSP-DOCS-E2R-AGGREGATE", "MSP-DOCS-CLEAN", "MSP-03D-R"}:
            for token in tokens:
                if token not in roadmap:
                    fail("surfaces.14: canonical completion claim drift")
    if matrix["issues"][EXACT_IDS.index("MSP-R00-L")]["acceptance_state"] == "ready":
        fail("surfaces: MSP-R00-L may not be ready")
    for surface in ("00-canonical.md", "12-eebus-mcp-first-vr940f.md"):
        text = " ".join((plan_dir / surface).read_text(encoding="utf-8").split())
        if E2R_PREREQUISITES not in text:
            fail(f"surfaces.{surface}: M3.5 E2R prerequisite drift")

def validate_surfaces(root: Path) -> None:
    plan_dir = root / PLAN
    if set(active_control_surface_paths()) != {
        path for path in MUTABLE_PATHS if path.startswith(PLAN + "/")
    }:
        fail("surfaces: mutable allowlist/projection drift")
    matrix = load_yaml(plan_dir / MATRIX)
    integrity = load_json(plan_dir / INTEGRITY)
    validate_matrix(matrix)
    validate_integrity(integrity)
    validate_plan_projection(load_yaml(plan_dir / "plan.yaml"))
    validate_live_audit(matrix, (plan_dir / "107-ad-docs-02-topology-audit.md").read_text(encoding="utf-8"))
    validate_markdown_claims(plan_dir, matrix)

def validate_changed_paths(root: Path = ROOT) -> None:
    present = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{ANCHOR}^{{commit}}"],
        text=True,
        capture_output=True,
    )
    if present.returncode != 0:
        try:
            subprocess.run(
                ["git", "-C", str(root), "fetch", "--quiet", "origin", ANCHOR],
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise ValidationError("protected-path anchor is unavailable") from exc
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "-z", ANCHOR, "HEAD", "--"],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ValidationError("protected-path anchor is unavailable") from exc
    fields = [field for field in result.stdout.split("\0") if field]
    changed_paths: list[str] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            fail("protected path changed: rename/copy")
        if status.startswith("D"):
            fail("protected path changed: deletion")
        if index >= len(fields):
            fail("protected path changed: malformed name-status")
        path = fields[index]
        index += 1
        if status[:1] != "M" and status[:1] != "A":
            fail("protected path changed: unsupported status")
        if path not in MUTABLE_PATHS:
            fail(f"protected path changed: {path}")
        changed_paths.append(path)
    for path in changed_paths:
        anchor_tree = subprocess.run(
            ["git", "-C", str(root), "ls-tree", ANCHOR, "--", path],
            text=True,
            capture_output=True,
            check=True,
        )
        head_tree = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "HEAD", "--", path],
            text=True,
            capture_output=True,
            check=True,
        )
        anchor_match = re.fullmatch(
            r"(100644|100755) blob [0-9a-f]{40}\t" + re.escape(path) + r"\n",
            anchor_tree.stdout,
        )
        if anchor_tree.stdout and anchor_match is None:
            fail("protected path changed: mode/type drift")
        expected_mode = anchor_match.group(1) if anchor_match else "100644"
        if not re.fullmatch(
            re.escape(expected_mode) + r" blob [0-9a-f]{40}\t" + re.escape(path) + r"\n",
            head_tree.stdout,
        ):
            fail("protected path changed: mode/type drift")

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
