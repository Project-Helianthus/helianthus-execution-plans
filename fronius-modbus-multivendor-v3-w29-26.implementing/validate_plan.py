#!/usr/bin/env python3
"""Validate only the structural contract of this locked execution-plan package."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
import yaml
REQUIRED_FILES = set("""
plan.yaml 00-canonical.md 01-index.md 10-architecture-and-repo-boundaries.md
11-fronius-readonly-and-semantic-lock.md 12-vendor-expansion-and-private-bindings.md
13-roadmap-gates-and-risks.md 90-issue-map.md 91-milestone-map.md
92-adversarial-review.md 99-status.md validate_plan.py
""".split())
REQUIRED_KEYS = set("""
    slug title state lock_authorized execution_authorization source_discussion target_repos knowledge_repo canonical_file canonical_sha256
split_index started_on current_milestone supersedes availability_mode accepted_adversarial_rounds
repository_mutex review_epoch review_scope decisions milestones risks phase_gates conditional_gates issues
""".split())
TARGET_REPOS = set("""
Project-Helianthus/.github Project-Helianthus/helianthus-modbus
Project-Helianthus/helianthus-modbusreg Project-Helianthus/helianthus-ebusgateway
Project-Helianthus/helianthus-ebusreg Project-Helianthus/helianthus-ha-integration
Project-Helianthus/helianthus-ha-addon Project-Helianthus/helianthus-docs-ebus
Project-Helianthus/helianthus-eebus-binding-private
Project-Helianthus/helianthus-matter-binding-private
Project-Helianthus/helianthus-execution-plans
""".split())
REVIEW_SCOPE = {"implementability", "correctness/data integrity", "protocol interoperability", "security/safety", "licensing/IP boundary", "operability/recovery", "testability", "dependency/DAG feasibility"}
REQUIRED_PHASE_GATES = set("PG-REPOSITORY-CREATION PG-MODBUS-BOOT PG-MODBUS-DOC-GATE PG-OPAQUE-ACQUISITION-DOC-GATE PG-OPAQUE-ACQUISITION-CONSUMER-PIN PG-MODBUSREG-BOOT PG-EEBUS-BOOT PG-MATTER-BOOT PG-RAW-FIRST PG-PV-DOC-GATE PG-SEMANTIC-LOCK PG-CONSUMER-PROMOTION PG-GRAPHQL-DOC-GATE PG-PUBLIC-ROLLOUT PG-EEBUS-DOC-GATE PG-MATTER-DOC-GATE PG-VENDOR-EXPANSION PG-READ-ONLY PG-RECOVERABLE-RELEASE".split())
EXPECTED_ISSUE_COUNT = 46
AMENDMENT_PR_NUMBER = 91
AMENDMENT_PR_URL = "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/91"
PREDECESSOR_AUTHORIZATION_PR_URL = "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/89"
PLAN_REPOSITORY = "Project-Helianthus/helianthus-execution-plans"
MODBUS_REPOSITORY = "Project-Helianthus/helianthus-modbus"
DOCS_REPOSITORY = "Project-Helianthus/helianthus-docs-ebus"
CANONICAL_GITHUB_REMOTE = {
    PLAN_REPOSITORY: "https://github.com/Project-Helianthus/helianthus-execution-plans.git",
    MODBUS_REPOSITORY: "https://github.com/Project-Helianthus/helianthus-modbus.git",
    DOCS_REPOSITORY: "https://github.com/Project-Helianthus/helianthus-docs-ebus.git",
}
DOCS_CANDIDATE_ENV = "FMV3_DOCS_CANDIDATE_ROOT"
AUTHORIZATION_EVIDENCE_SCHEMA = "helianthus.fmv3-issue-authorization-evidence.v1"
EXTERNAL_REVIEW_ATTESTATION_TAG = (
    "<!-- helianthus-fmv3-pr91-external-review-attestation-v1 -->"
)
EXTERNAL_REVIEW_ATTESTATION_SCHEMA = (
    "helianthus.fmv3-pr91-external-review-attestation.v1"
)
MATERIALIZATION_ENV_PREFIX = "FMV3_ANCHOR_MATERIALIZATION_"
DOCS_MACHINE_FIELDS = (
    "schema", "version", "contract_id", "contract_version", "content_revision",
    "source_kind", "opaque_capability", "m2_ledger", "normalization_record",
    "bounded_values", "public_authorization", "zero_trust_boundary",
)
DOCS_MACHINE_FIELDS_WITHOUT_BOUNDED_VALUES = tuple(
    field for field in DOCS_MACHINE_FIELDS if field != "bounded_values"
)
EXPECTED_DOCS_CANDIDATE_BINDING = {
    "repo": DOCS_REPOSITORY,
    "pr": 386,
    "pr_url": "https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/386",
    "commit_sha": "0dd470495ac69a3a7f30ec235dd0bb83977a99ad",
    "commit_tree_sha": "3ce278dfd1956bfcd62a5adaaced77ee81daef61",
    "pull_request_identity": {
        "number": 386,
        "base_sha": "777954d1dea586409827116f2a0eb887ee5cd4f4",
        "base_repo": DOCS_REPOSITORY,
        "base_ref": "main",
        "head_repo": DOCS_REPOSITORY,
        "head_ref": "issue/385-opaque-runtime-acquisition",
    },
    "manifest_path": "docs/platform/manifests/opaque-runtime-acquisition-v1.json",
    "manifest_sha256": "a221342201bf1fd005ff71694081561fff34b9b6b89346e09ac9097ce31a29c4",
    "policy_path": "docs/platform/opaque-runtime-acquisition-v1.md",
    "policy_sha256": "fd7110af13091cd391244dd5f2f8fa918d0f8606d6309a37144306aa87257c2f",
    "normative_blobs": {
        ".github/workflows/modbus-trusted-revision.yml": "229616e784d7735ff7bf2288a7986f170898b75a9fac5dffbfa1c499f6795b98",
        "docs/platform/manifests/modbus-foundation-profile-contract-v1.json": "c411e3e8a464e4b9d3a59d3f5a0c82b57e176e24dec9550b9bc0c8b3e4b28c70",
        "docs/platform/manifests/opaque-runtime-acquisition-v1.json": "a221342201bf1fd005ff71694081561fff34b9b6b89346e09ac9097ce31a29c4",
        "docs/platform/modbus-foundation-profile-contract-v1.md": "1a53f203eed42766ac2d91580c41f72674b5eaea374a1cf4fff650396f06b196",
        "docs/platform/modbus-multivendor-boundaries.md": "b7edf9fc6073a441a638b392d6dfc92ea5851e2cf0b2080e09a46c395788480c",
        "docs/platform/opaque-runtime-acquisition-v1.md": "fd7110af13091cd391244dd5f2f8fa918d0f8606d6309a37144306aa87257c2f",
        "docs/platform/schemas/modbus-companion-consumer-lock-v1.schema.json": "369a724954d21614d71fd970c8b6224d8c892af8870819cbef159619acce4ad0",
        "protocols/modbus/modbus-phase-one-wire-v1.md": "b941a60b39409c570f904f8e6830787203f8041c2fee462164c4c50c7a8f4444",
        "scripts/validate_modbus_companion.py": "cad2fe98a6c144d43bb5207c99ea054779d0f843f84eec3c29e19872fd7864ff",
        "scripts/validate_modbus_revision_transition.py": "8a024501ecd3c9e89bec049c7bf7d0ffbbc143a8f0128aba56741b361ada6d3b",
        "scripts/validate_opaque_runtime_acquisition.py": "58f1a9ba94b23396f648a33458d82b3d3a76a95b5f507aeafcd0422b2fd19bfc",
    },
    "machine_projection_fields": list(DOCS_MACHINE_FIELDS),
    "machine_projection_sha256": "46de71c72811907fd229577d1d56c803afbc9917c2bce4e97d17d29eaffcc157",
    "machine_projection_without_bounded_values_sha256": "09c54701252002ba3ba7011640aa7734838f9d7dc732372318a7ab0d4b6c754d",
    "r2_rebind": {
        "status": "BOUND_DOCS_R2",
        "blocks_authorization_for": [],
        "required_semantics": [
            "claim_in_progress",
            "cancelling",
            "all_runtime_claims_succeeded_before_seal",
            "CancelOpen_linearization",
            "byte_and_field_bounds",
            "reserved_non_wrapping_terminal_sequences",
        ],
    },
}
EXPECTED_PR_IDENTITY = {
    "number": 91,
    "base_sha": "6fd2b4a8d181f5133250a0f2f1380d057254db60",
    "base_repo": "Project-Helianthus/helianthus-execution-plans",
    "base_ref": "main",
    "head_repo": "Project-Helianthus/helianthus-execution-plans",
    "head_ref": "issue/90-fmv3-capability-ledger-reconcile",
    "merge_method": "squash",
    "merge_parent": "exact_expected_original_base_sha",
    "merged_by": "authorized_issuer",
    "reviewed_content": "squash_merge_tree_equals_attested_pr_head_tree",
}
EXPECTED_EXTERNAL_REVIEW_ATTESTATION = {
    "source": "github_pr_issue_comment",
    "tag": EXTERNAL_REVIEW_ATTESTATION_TAG,
    "schema": EXTERNAL_REVIEW_ATTESTATION_SCHEMA,
    "issuer": "authorized_issuer",
    "trusted_association": "allowed_author_associations",
    "edit_policy": "created_at_equals_updated_at",
    "timing": "strictly_after_head_commit_and_before_merged_at",
    "verdict": "NO_FINDINGS",
    "provider": "openai",
    "fresh_context": True,
    "minimum_unique_reviewer_run_ids": 2,
    "binds": ["repository", "pull_request", "head_sha", "head_tree_sha"],
}
EXPECTED_ISSUE_EVIDENCE_POLICY = {
    "FMV3-M1-05": {
        "external_evidence": "none_before_docs_merge",
    },
    "FMV3-M1-06": {
        "requires": "docs_pr_386_merged_at_exact_bound_candidate_head_and_tree",
    },
    "FMV3-M2-01": {
        "cli": "--authorization-evidence <external-json-file>",
        "schema": AUTHORIZATION_EVIDENCE_SCHEMA,
        "producer_issue": "FMV3-M1-06",
        "producer_repository": MODBUS_REPOSITORY,
        "requires": [
            "full_40_character_merge_sha",
            "canonical_main_ancestry",
            "merged_pull_request",
            "closed_issue_relationship",
        ],
    },
}
EXPECTED_M1_06_PRODUCER_PIN_CONTRACT = {
    "producer_issue": "FMV3-M1-06",
    "repository": MODBUS_REPOSITORY,
    "evidence_interface": "external_json_file",
    "evidence_schema": AUTHORIZATION_EVIDENCE_SCHEMA,
    "merge_sha": "required_full_40_lowercase_hex",
    "github_issue_number": "required_positive_integer",
    "github_pull_request_number": "required_positive_integer",
    "verification": [
        "fixed_github_api_canonical_main_ancestry",
        "exact_merged_pull_request",
        "closed_issue_cross_reference",
    ],
    "consumer_resolution": "exact_sha_verified_before_red",
}
EXPECTED_TOOLING_PATHS = {
    "validator_path": "fronius-modbus-multivendor-v3-w29-26.implementing/validate_plan.py",
    "workflow_path": ".github/workflows/ci.yml",
}
EXPECTED_D13_DECISION = "FMV3-M1-05 documents and FMV3-M1-06 implements OPAQUE_RUNTIME_ACQUISITION_V1 as an additive successor to M1-04 before M2-01. A runtime source privately owns and issues each non-serializable one-shot capability only after all post-correlation successful-dependent deliverability conditions; only copies of that same capability share its state, and M1 state is never an M2 ledger pointer. Endpoint recreation and every new acquisition create fresh independent state even when visible identity or data match. Capability state moves open to claimed, cancelled, failed, or expired and is synchronously reclaimed by a pre-reserved terminal sequence into a finite-positive, byte-bounded, non-reconstructing tombstone ring. M2-01 pins the merged M1-06 producer SHA, keeps runtime and fixture trust distinct, and owns a separately bounded attempt/claim ledger across every retained state. The exact docs R2 binding requires unresolved claims to enter claim_in_progress before one immutable terminal result, open or sealed attempts to enter cancelling before cancelled, an atomic seal predicate in which every data-bearing runtime claim is claim_succeeded, runtime-source-owned CancelOpen linearized by exact bounded AttemptKey, explicit byte and field bounds validated before allocation, one-shot sealed-to-publishing Publish(), and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. Deterministic reclamation preserves only bounded non-reconstructing audit metadata and the complete normalization record round-trips losslessly within admitted bounds."
EXPECTED_M2_EXIT_GATE = "The reused FMV3-M1-00 companion remains merged, and M2-01 starts only after M1-06 merges and external authorization evidence proves its full 40-character producer merge SHA on canonical helianthus-modbus main with the exact merged PR and closed issue relationship. The exact docs R2 head/tree binding requires claim_in_progress and cancelling states, an atomic all-data-bearing-runtime-claims-succeeded seal predicate, runtime-source-owned CancelOpen linearization by exact bounded AttemptKey, byte and field bounds validated before allocation, and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. Profile API, exact wire-response/logical-view/sample identity and provenance, runtime-versus-fixture trust, independently ledger-owned bounded attempt/claim state across all retained states, finite-positive limits with a checked retained-attempt-limit times claim-limit product, duplicate AttemptKey rejection, complete immutable-terminal lifecycles, one-shot sealed publication, deterministic synchronous terminal-sequence reclamation into a finite-positive byte-bounded non-reconstructing audit/tombstone ring, exact bounded normalization round-trip, detector lifecycle, and conformance harness are stable under strict hosted RED/GREEN and fresh independent review."
AMENDMENT_SURFACE_FILES = (
    "00-canonical.md",
    "01-index.md",
    "10-architecture-and-repo-boundaries.md",
    "11-fronius-readonly-and-semantic-lock.md",
    "12-vendor-expansion-and-private-bindings.md",
    "13-roadmap-gates-and-risks.md",
    "90-issue-map.md",
    "91-milestone-map.md",
    "92-adversarial-review.md",
    "99-status.md",
)
AMENDMENT_ISSUE_IDS = ("FMV3-M1-05", "FMV3-M1-06", "FMV3-M2-01")
AUTHORIZED_ISSUES = [
    "FMV3-M0-01", "FMV3-M0-02", "FMV3-M0-03", "FMV3-M0-06",
    "FMV3-M1-00", "FMV3-M1-01", "FMV3-M1-02", "FMV3-M1-03", "FMV3-M1-04",
    "FMV3-M1-05", "FMV3-M1-06",
    "FMV3-M2-01", "FMV3-M2-02", "FMV3-M2-03",
    "FMV3-M3-01", "FMV3-M3-02", "FMV3-M3-03",
]
CANONICAL_AUTHORIZATION_BLOCK = """Execution activates only after PR #91 merges. Its exact merge commit is the sole current
immutable authorization anchor. Issue #90 is tracking metadata only and is not cryptographic
or authorization evidence. PR #89 is retained only as predecessor provenance and is not
authority for the corrected M1 capability or M2 ledger fields.

PR #91 must retain its exact original base/head repository and ref identity. Its squash
merge must have exactly one parent equal to the expected original base SHA and a tree equal
to the externally attested PR head tree. The authorized issuer must create exactly one
unedited trusted-association attestation after the exact head commit and before merge. That
attestation binds the live full head SHA and tree, records `NO_FINDINGS`, and carries at
least two unique fresh OpenAI reviewer run IDs; the plan never self-embeds its own head SHA.

The ordered `authorized_issues` list in `plan.yaml` is the sole normative execution scope:
FMV3-M0-01, FMV3-M0-02, FMV3-M0-03, FMV3-M0-06, FMV3-M1-00, FMV3-M1-01,
FMV3-M1-02, FMV3-M1-03, FMV3-M1-04, FMV3-M1-05, FMV3-M1-06, FMV3-M2-01,
FMV3-M2-02, FMV3-M2-03, FMV3-M3-01, FMV3-M3-02, and FMV3-M3-03. Milestone names
are non-authoritative grouping labels. This amendment corrects FMV3-M1-05, FMV3-M1-06,
and FMV3-M2-01 without changing the allowlist.

Authorization runs only from a fully clean canonical
`Project-Helianthus/helianthus-execution-plans` main checkout resolved through the fixed
GitHub API. A configured remote named `origin` is never main authority and must identify
the canonical repository exactly. Cruise preflight invokes the checked-out validator
without its internal flag; it materializes the validator blob from the plan anchor,
verifies the anchored SHA-256, and re-executes that one-use blob internally.

FMV3-M0-01 creates only the two empty public repositories `helianthus-modbus` and
`helianthus-modbusreg`. FMV3-M1-05 publishes the public
`OPAQUE_RUNTIME_ACQUISITION_V1` companion, FMV3-M1-06 implements it after M1-05, and
FMV3-M2-01 consumes the merged M1-06 producer by exact full-SHA pin. Private governance
creation FMV3-M0-04 and destination bootstraps FMV3-M0-05/FMV3-M0-07 remain deferred.

FMV3-M1-05 remains authorizable before its docs PR merges. FMV3-M1-06 requires docs PR
#386 merged with the exact bound candidate head and tree. FMV3-M2-01 additionally requires
an external authorization-evidence JSON file carrying the full 40-character M1-06 producer
merge SHA plus canonical `helianthus-modbus` issue and PR numbers; live API evidence must
prove that merge is on canonical main and that the merged PR closed the supplied issue.
The exact docs R2 commit/tree, complete predecessor-inclusive normative closure, and expanded
machine projection including `bounded_values` are bound. They require claim-in-progress,
cancelling, atomic all-success-before-seal, source-owned CancelOpen, byte/field bounds, and
pre-reserved non-wrapping, non-reused terminal sequences. M1-06 and M2-01 still fail
authorization until docs PR #386 is merged at that exact head and tree.

The hard stop is immediately before FMV3-M4-01. Gateway work is not authorized. No gateway
issue, branch, PR, import, or code change is authorized by this action. Repository creation,
implementation issues, commits, pushes, reviews, and merges are authorized only for the
ordered issue list above and remain subject to every dependency and gate."""
# The amendment digest binds these normative status facts. Operational lifecycle fields
# remain structurally validated below, but may advance without a new authorization anchor.
AMENDMENT_STATUS_IMMUTABLE_FIELDS = (
    "Authorization scope authority",
    "Authorization anchor",
    "Canonical main authority",
    "External review attestation",
    "Docs R2 rebind",
    "Gateway work authorized",
)
AMENDMENT_STATUS_MUTABLE_FIELDS = (
    "State",
    "Current milestone",
    "Review epoch",
    "Review state",
    "Accepted adversarial rounds",
    "Review target",
)
EXPECTED_MILESTONE_ROWS = {
    "M1": [
        "M1",
        "M0",
        "Modbus bootstrap and M0 boundary docs complete",
        "FMV3-M1-00 fixes existing operations/recovery/coalescing; after M1-04, M1-05 docs PR #386 exact bound R2 head/tree merge precedes M1-06 hosted RED/GREEN with fresh review",
        "Original history stays intact; the corrective docs issue precedes code, and absent RTU hardware blocks no TCP work",
    ],
    "M2": [
        "M2",
        "M0",
        "Modbusreg bootstrap, merged FMV3-M1-00, merged M1-06, external full-SHA canonical-main/PR/issue evidence, and exact docs R2 binding",
        "Independent ledger adds claim_in_progress/cancelling, all runtime claims succeeded before seal, CancelOpen linearization, byte/field bounds, reserved non-wrapping terminal sequences, finite-positive limits and checked product; one-shot immutable Publish(); non-reconstructing reclamation; runtime/fixture trust; exact normalization/provenance/conformance",
        "M2-01 retains M1-00 and adds M1-05 corrective companion metadata; hosted RED/GREEN and fresh review are mandatory",
    ],
}
EXPECTED_CORRECTIVE_GATE_ROWS = [
    [
        "PG-OPAQUE-ACQUISITION-DOC-GATE",
        "FMV3-M1-05 merged after M1-04; docs PR #386 exact bound R2 head/tree merged",
        "FMV3-M1-06",
    ],
    [
        "PG-OPAQUE-ACQUISITION-CONSUMER-PIN",
        "FMV3-M1-06 merged after hosted RED/GREEN and fresh review; external JSON proves full merge SHA on canonical main plus exact PR/issue relationship",
        "FMV3-M2-01",
    ],
]
EXPECTED_CORRECTIVE_PHASE_GATES = [
    {
        "id": "PG-OPAQUE-ACQUISITION-DOC-GATE",
        "kind": "dependency",
        "after_issues": ["FMV3-M1-05"],
        "before_issues": ["FMV3-M1-06"],
        "requirement": "The public OPAQUE_RUNTIME_ACQUISITION_V1 companion merges after M1-04 through docs PR #386 at the exact bound docs R2 head/tree before M1-06 code. That exact binding includes claim_in_progress and cancelling states, an atomic all-data-bearing-runtime-claims-succeeded seal predicate, runtime-source-owned CancelOpen linearization by exact bounded AttemptKey, byte and field bounds validated before allocation, and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. The source-kind, source-private capability, deliverability, copy sharing, fresh acquisition, bounded lifecycle, one-shot Publish, reclamation, coalescing, and normalization contract remains exact. Fresh independent OpenAI review blocks merge.",
    },
    {
        "id": "PG-OPAQUE-ACQUISITION-CONSUMER-PIN",
        "kind": "dependency",
        "after_issues": ["FMV3-M1-06"],
        "before_issues": ["FMV3-M2-01"],
        "requirement": "M2-01 cannot begin until M1-06 has merged and an external authorization-evidence JSON file supplies its exact full 40-character merge SHA plus canonical helianthus-modbus issue and PR numbers. Fixed GitHub API evidence must prove canonical-main ancestry, the exact merged PR, and its closed issue relationship; M1 hosted RED/GREEN, fresh independent review, and the exact docs R2 binding must also verify.",
    },
]
EXPECTED_CORRECTIVE_PHASE_GATE_IDS = [
    gate["id"] for gate in EXPECTED_CORRECTIVE_PHASE_GATES
]
CONDITIONAL_GATE_IDS = {"CG-M4-LIVE-GO", "CG-M5-SEMANTIC-GO"}
M1_IMPLEMENTATION_IDS = {f"FMV3-M1-{number:02d}" for number in range(1, 5)}
M2_IMPLEMENTATION_IDS = {f"FMV3-M2-{number:02d}" for number in range(1, 4)}
COMPANION_IDS = M1_IMPLEMENTATION_IDS | M2_IMPLEMENTATION_IDS
CHUNKS = [f"{number}-{name}.md" for number, name in ((10, "architecture-and-repo-boundaries"), (11, "fronius-readonly-and-semantic-lock"), (12, "vendor-expansion-and-private-bindings"), (13, "roadmap-gates-and-risks"))]
M1_ADMISSION_GATE = Path("runtime-gates/fronius-modbus-m1-admission.json")
M1_DOCS_PR = 376
M1_TRUST_ANCHOR_VALIDATOR_SHA256 = (
    "8a024501ecd3c9e89bec049c7bf7d0ffbbc143a8f0128aba56741b361ada6d3b"
)
M1_ADMISSION_KEYS = {
    "branch_protection_evidence_url",
    "docs_merge_sha",
    "docs_pr",
    "docs_repository",
    "required_check",
    "required_check_run_url",
    "required_check_verified_at",
    "schema",
    "state",
    "trust_anchor_commit",
    "trust_anchor_repository",
    "verification_head_sha",
    "verification_pr",
    "version",
}
class ValidationError(Exception): pass
class UniqueLoader(yaml.SafeLoader): pass
def unique_mapping(loader: UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result: raise ValidationError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result
UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
def require(condition: bool, message: str) -> None:
    if not condition: raise ValidationError(message)
def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
def safe_repository_path(value: Any, label: str) -> Path:
    require(isinstance(value, str) and value, f"{label} must be a non-empty path")
    path = Path(value)
    require(
        not path.is_absolute() and ".." not in path.parts,
        f"{label} must be repository-relative",
    )
    return path


def git_command(
    repo: Path,
    args: list[str],
    label: str,
    *,
    text: bool = True,
) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=text,
    )
    require(result.returncode == 0, f"{label} failed")
    return result.stdout


def require_canonical_remote(repo_root: Path, repository: str, label: str) -> None:
    expected = CANONICAL_GITHUB_REMOTE[repository]
    fetch_urls = git_command(
        repo_root,
        ["remote", "get-url", "--all", "origin"],
        f"{label} origin fetch URL lookup",
    ).splitlines()
    push_urls = git_command(
        repo_root,
        ["remote", "get-url", "--push", "--all", "origin"],
        f"{label} origin push URL lookup",
    ).splitlines()
    require(
        fetch_urls == [expected] and push_urls == [expected],
        f"{label} origin is not the canonical {repository} remote",
    )


def require_standard_index(repo_root: Path, label: str) -> None:
    index_flags = git_command(
        repo_root,
        ["ls-files", "-v"],
        f"{label} index inspection",
    ).splitlines()
    require(
        all(line.startswith("H ") for line in index_flags),
        f"{label} rejects assume-unchanged, skip-worktree, or other nonstandard index flags",
    )


def require_clean_checkout(repo_root: Path, label: str) -> None:
    require_standard_index(repo_root, label)
    status = git_command(
        repo_root,
        ["status", "--porcelain", "--untracked-files=all"],
        f"{label} status inspection",
    ).strip()
    require(not status, f"{label} requires a fully clean checkout")


def committed_regular_blob(
    repo_root: Path,
    commit_sha: str,
    relative_value: Any,
    label: str,
) -> bytes:
    relative = safe_repository_path(relative_value, label)
    tree_row = git_command(
        repo_root,
        ["ls-tree", "-z", commit_sha, "--", relative.as_posix()],
        f"{label} tree lookup",
        text=False,
    )
    rows = [row for row in tree_row.split(b"\0") if row]
    require(len(rows) == 1, f"{label} must resolve to exactly one committed blob")
    metadata, separator, encoded_path = rows[0].partition(b"\t")
    parts = metadata.split()
    require(
        separator == b"\t"
        and encoded_path.decode("utf-8") == relative.as_posix()
        and len(parts) == 3
        and parts[0] in {b"100644", b"100755"}
        and parts[1] == b"blob",
        f"{label} must be a regular committed file",
    )
    return git_command(
        repo_root,
        ["show", f"{commit_sha}:{relative.as_posix()}"],
        f"{label} blob read",
        text=False,
    )


def load_docs_candidate(binding: dict[str, Any]) -> dict[str, Any]:
    require(
        binding == EXPECTED_DOCS_CANDIDATE_BINDING,
        "docs candidate binding mismatch",
    )
    root_value = os.environ.get(DOCS_CANDIDATE_ENV)
    require(root_value is not None and root_value, f"{DOCS_CANDIDATE_ENV} is mandatory")
    root = Path(root_value).resolve()
    require(root.is_dir(), "docs candidate root is absent")
    docs_toplevel = Path(
        git_command(
            root,
            ["rev-parse", "--show-toplevel"],
            "docs candidate git toplevel lookup",
        ).strip()
    ).resolve()
    require(root == docs_toplevel, "docs candidate root must equal the git toplevel")
    require_canonical_remote(root, DOCS_REPOSITORY, "docs candidate")
    require_clean_checkout(root, "docs candidate")
    candidate_head = git_command(
        root,
        ["rev-parse", "HEAD"],
        "docs candidate HEAD lookup",
    ).strip()
    require(
        candidate_head == binding["commit_sha"],
        "docs candidate checkout is not at the exact bound commit",
    )
    candidate_tree = git_command(
        root,
        ["rev-parse", f"{binding['commit_sha']}^{{tree}}"],
        "docs candidate tree lookup",
    ).strip()
    require(
        candidate_tree == binding["commit_tree_sha"],
        "docs candidate commit tree mismatch",
    )
    closure = binding.get("normative_blobs")
    require(
        isinstance(closure, dict) and closure,
        "docs candidate normative closure must be a non-empty mapping",
    )
    blobs: dict[str, bytes] = {}
    for relative, expected_sha256 in closure.items():
        require(
            isinstance(expected_sha256, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None,
            f"docs candidate normative blob SHA-256 is invalid: {relative}",
        )
        blob = committed_regular_blob(
            root,
            binding["commit_sha"],
            relative,
            f"docs normative blob {relative}",
        )
        require(
            hashlib.sha256(blob).hexdigest() == expected_sha256,
            f"docs normative blob SHA-256 mismatch: {relative}",
        )
        blobs[relative] = blob
    manifest_bytes = blobs.get(binding["manifest_path"])
    policy_bytes = blobs.get(binding["policy_path"])
    require(manifest_bytes is not None, "docs manifest is absent from normative closure")
    require(policy_bytes is not None, "docs policy is absent from normative closure")
    require(
        hashlib.sha256(manifest_bytes).hexdigest() == binding["manifest_sha256"],
        "docs candidate manifest SHA-256 mismatch",
    )
    require(
        hashlib.sha256(policy_bytes).hexdigest() == binding["policy_sha256"],
        "docs candidate policy SHA-256 mismatch",
    )
    manifest = json.loads(manifest_bytes)
    require(isinstance(manifest, dict), "docs candidate manifest must be an object")
    require(
        set(DOCS_MACHINE_FIELDS) <= set(manifest),
        "docs candidate manifest lacks bound machine fields",
    )
    projection = {field: manifest[field] for field in DOCS_MACHINE_FIELDS}
    require(
        canonical_json_sha256(projection) == binding["machine_projection_sha256"],
        "docs candidate machine projection SHA-256 mismatch",
    )
    projection_without_bounded_values = {
        field: manifest[field]
        for field in DOCS_MACHINE_FIELDS_WITHOUT_BOUNDED_VALUES
    }
    require(
        canonical_json_sha256(projection_without_bounded_values)
        == binding["machine_projection_without_bounded_values_sha256"],
        "docs candidate pre-bounds machine projection SHA-256 mismatch",
    )
    predecessor_manifest_path = (
        "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
    )
    predecessor_manifest = json.loads(blobs[predecessor_manifest_path])
    predecessor_artifacts = predecessor_manifest.get("artifacts")
    predecessor_hashes = predecessor_manifest.get("artifact_sha256")
    require(
        isinstance(predecessor_artifacts, dict)
        and isinstance(predecessor_hashes, dict)
        and set(predecessor_artifacts) == set(predecessor_hashes),
        "docs predecessor normative artifact closure is invalid",
    )
    for artifact, relative in predecessor_artifacts.items():
        require(
            relative in blobs
            and hashlib.sha256(blobs[relative]).hexdigest()
            == predecessor_hashes[artifact],
            f"docs predecessor normative artifact mismatch: {artifact}",
        )
    return projection


def require_docs_r2_semantics(projection: dict[str, Any]) -> None:
    opaque = projection["opaque_capability"]
    ledger = projection["m2_ledger"]
    normalization = projection["normalization_record"]
    bounded_values = projection["bounded_values"]
    require(
        opaque["attempt_binding"]["source_operation"] == "CancelOpen(AttemptKey)"
        and opaque["attempt_binding"]["cancel_open"]["owner"] == "runtime_source"
        and opaque["attempt_binding"]["cancel_open"]["ledger_mutation"] == "forbidden",
        "docs R2 source-owned CancelOpen contract mismatch",
    )
    capability_sequence = opaque["bounded_state"]["terminal_sequence"]
    ledger_sequence = ledger["bounds"]["terminal_sequence"]
    require(
        capability_sequence["domain"] == "uint64_1_to_2^64_minus_1"
        and capability_sequence["wrap"] == "forbidden_checked_arithmetic"
        and capability_sequence["reuse"]
        == "forbidden_within_owner_lifetime_including_after_reclamation"
        and ledger_sequence["domain"] == "uint64_1_to_2^64_minus_1"
        and ledger_sequence["wrap"] == "forbidden_checked_arithmetic"
        and ledger_sequence["reuse"]
        == "forbidden_within_owner_lifetime_including_after_reclamation",
        "docs R2 reserved terminal-sequence contract mismatch",
    )
    require(
        ledger["attempt_lifecycle"]["seal_condition"]
        == "all_data_bearing_runtime_claims_claim_succeeded"
        and ledger["attempt_lifecycle"]["seal_linearization"]
        == "success_predicate_and_open_to_sealed_atomic"
        and "claim_in_progress"
        in ledger["claim_entry_lifecycle"]["nonterminal"]
        and "open_to_cancelling" in ledger["attempt_lifecycle"]["legal_transitions"]
        and ledger["cancellation_protocol"]["source_operation"]
        == "runtime_source_owned_CancelOpen_exact_AttemptKey"
        and ledger["cancellation_protocol"]["drain"]
        == "wait_for_all_claim_in_progress_finalization",
        "docs R2 claim, seal, and cancellation state-machine mismatch",
    )
    require(
        normalization["bounds"]["validation_order"]
        == "encoded_total_then_fields_before_owner_allocation"
        and bounded_values["activation"]
        == "finite_positive_checked_nonoverflowing_bounds_before_activation"
        and bounded_values["allocation"]
        == "validate_before_decode_copy_hash_intern_or_retain"
        and bounded_values["attempt_key"]["max"] == "attempt_key_max_utf8_bytes"
        and bounded_values["retained_diagnostics"]["oversize"]
        == "reject_without_truncation",
        "docs R2 byte and field bounds mismatch",
    )


def current_tooling_path(
    repo_root: Path,
    plan_root: Path,
    path_key: str,
    bound_path: Path,
) -> Path:
    return plan_root / "validate_plan.py" if path_key == "validator_path" else repo_root / bound_path
def require_current_tooling(
    repo_root: Path,
    plan_root: Path,
    binding: dict[str, Any],
) -> None:
    require(
        binding.get("authorization_execution") == "materialized_from_pr91_anchor",
        "authorization tooling execution mode mismatch",
    )
    for path_key, hash_key in (
        ("validator_path", "validator_sha256"),
        ("workflow_path", "workflow_sha256"),
    ):
        require(
            binding.get(path_key) == EXPECTED_TOOLING_PATHS[path_key],
            f"authorization tooling {path_key} mismatch",
        )
        digest = binding.get(hash_key)
        require(
            isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
            f"authorization tooling {hash_key} must be lowercase SHA-256",
        )
        relative = safe_repository_path(binding[path_key], path_key)
        path = current_tooling_path(repo_root, plan_root, path_key, relative)
        require(path.is_file() and not path.is_symlink(), f"bound tooling file is absent: {path_key}")
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == digest,
            f"current {path_key} blob differs from authorization anchor",
        )
def github_api(endpoint: str) -> Any:
    result = subprocess.run(
        ["gh", "api", endpoint],
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(result.stdout)
    require(isinstance(value, (dict, list)), f"GitHub API returned invalid JSON for {endpoint}")
    return value


def canonical_main_sha(repository: str) -> str:
    ref = github_api(f"repos/{repository}/git/ref/heads/main")
    require(isinstance(ref, dict), f"canonical {repository} main ref is invalid")
    target = ref.get("object", {})
    sha = target.get("sha") if isinstance(target, dict) else None
    require(
        target.get("type") == "commit"
        and isinstance(sha, str)
        and re.fullmatch(r"[0-9a-f]{40}", sha) is not None,
        f"canonical {repository} main ref is not one exact commit",
    )
    return sha


def github_issue_comments(repository: str, issue_number: int) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    for page in range(1, 101):
        value = github_api(
            f"repos/{repository}/issues/{issue_number}/comments?per_page=100&page={page}"
        )
        require(isinstance(value, list), "GitHub issue comments response is invalid")
        require(
            all(isinstance(comment, dict) for comment in value),
            "GitHub issue comments contain an invalid row",
        )
        comments.extend(value)
        if len(value) < 100:
            return comments
    raise ValidationError("GitHub issue comment pagination exceeds the fail-closed bound")


def unique_json_object(text: str, label: str) -> dict[str, Any]:
    def build_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"{label} contains duplicate JSON key: {key}")
            value[key] = item
        return value

    value = json.loads(text, object_pairs_hook=build_object)
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def parse_github_time(value: Any, label: str) -> datetime:
    require(
        isinstance(value, str)
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is not None,
        f"{label} must be an RFC3339 UTC timestamp",
    )
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def require_external_review_attestation(
    anchor: dict[str, Any],
    pr: dict[str, Any],
    head_commit: dict[str, Any],
    head_sha: str,
    head_tree: str,
) -> None:
    require(
        anchor.get("external_review_attestation")
        == EXPECTED_EXTERNAL_REVIEW_ATTESTATION,
        "external review attestation contract mismatch",
    )
    comments = github_issue_comments(PLAN_REPOSITORY, AMENDMENT_PR_NUMBER)
    tagged = [
        comment
        for comment in comments
        if EXTERNAL_REVIEW_ATTESTATION_TAG in str(comment.get("body", ""))
    ]
    require(
        len(tagged) == 1
        and sum(
            str(comment.get("body", "")).count(EXTERNAL_REVIEW_ATTESTATION_TAG)
            for comment in comments
        )
        == 1,
        "PR #91 requires exactly one external review attestation tag",
    )
    comment = tagged[0]
    require(
        comment.get("user", {}).get("login") == anchor["authorized_issuer"],
        "PR #91 review attestation issuer mismatch",
    )
    require(
        comment.get("author_association") in anchor["allowed_author_associations"],
        "PR #91 review attestation association is not trusted",
    )
    require(
        comment.get("created_at") == comment.get("updated_at"),
        "PR #91 review attestation must be unedited",
    )
    body_match = re.fullmatch(
        re.escape(EXTERNAL_REVIEW_ATTESTATION_TAG)
        + r"\n```json\n(.+)\n```",
        str(comment.get("body", "")),
        re.DOTALL,
    )
    require(body_match is not None, "PR #91 review attestation body format mismatch")
    attestation = unique_json_object(
        body_match.group(1),
        "PR #91 review attestation",
    )
    expected_keys = {
        "schema",
        "repository",
        "pull_request",
        "head_sha",
        "head_tree_sha",
        "verdict",
        "provider",
        "fresh_context",
        "reviewer_run_ids",
    }
    require(
        set(attestation) == expected_keys,
        "PR #91 review attestation schema keys mismatch",
    )
    run_ids = attestation["reviewer_run_ids"]
    require(
        attestation["schema"] == EXTERNAL_REVIEW_ATTESTATION_SCHEMA
        and attestation["repository"] == PLAN_REPOSITORY
        and attestation["pull_request"] == AMENDMENT_PR_NUMBER
        and type(attestation["pull_request"]) is int
        and attestation["head_sha"] == head_sha
        and attestation["head_tree_sha"] == head_tree
        and attestation["verdict"] == "NO_FINDINGS"
        and attestation["provider"] == "openai"
        and attestation["fresh_context"] is True,
        "PR #91 review attestation does not bind the exact reviewed head/tree and NO_FINDINGS",
    )
    require(
        isinstance(run_ids, list)
        and len(run_ids) >= 2
        and len(run_ids) == len(set(run_ids))
        and all(
            isinstance(run_id, str)
            and re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                run_id,
            )
            is not None
            for run_id in run_ids
        ),
        "PR #91 review attestation requires at least two unique full OpenAI reviewer run IDs",
    )
    head_commit_time = head_commit.get("committer", {}).get("date")
    created_at = parse_github_time(comment.get("created_at"), "attestation created_at")
    require(
        created_at > parse_github_time(head_commit_time, "PR #91 head commit time")
        and created_at < parse_github_time(pr.get("merged_at"), "PR #91 merged_at"),
        "PR #91 review attestation must be created after the head commit and before mergedAt",
    )


def require_authorization_pr_merged(
    anchor: dict[str, Any],
    plan_head_sha: str,
) -> None:
    pr_url = anchor.get("authorization_pr")
    require(pr_url == AMENDMENT_PR_URL, "authorization requires the exact merged PR #91 URL")
    pr_number = AMENDMENT_PR_NUMBER
    pr = github_api(
        f"repos/Project-Helianthus/helianthus-execution-plans/pulls/{pr_number}"
    )
    identity = anchor["pull_request_identity"]
    require(identity == EXPECTED_PR_IDENTITY, "authorization PR identity contract mismatch")
    require(isinstance(pr, dict), "authorization PR #91 response is invalid")
    require(
        pr.get("number") == identity["number"]
        and pr.get("html_url") == pr_url
        and pr.get("base", {}).get("sha") == identity["base_sha"]
        and pr.get("base", {}).get("ref") == identity["base_ref"]
        and pr.get("base", {}).get("repo", {}).get("full_name") == identity["base_repo"]
        and pr.get("head", {}).get("ref") == identity["head_ref"]
        and pr.get("head", {}).get("repo", {}).get("full_name") == identity["head_repo"],
        "authorization PR #91 base/head identity mismatch",
    )
    require(
        pr.get("state") == "closed"
        and pr.get("merged") is True
        and pr.get("merged_at") is not None
        and pr.get("merge_commit_sha") == plan_head_sha,
        "authorization PR #91 is not merged at the plan authorization SHA",
    )
    require(
        pr.get("user", {}).get("login") == anchor["authorized_issuer"],
        "authorization PR #91 issuer mismatch",
    )
    require(
        pr.get("author_association") in anchor["allowed_author_associations"],
        "authorization PR #91 author association is not allowed",
    )
    require(
        pr.get("merged_by", {}).get("login") == anchor["authorized_issuer"],
        "authorization PR #91 merger is not the authorized issuer",
    )
    head_sha = pr.get("head", {}).get("sha")
    require(
        isinstance(head_sha, str) and re.fullmatch(r"[0-9a-f]{40}", head_sha) is not None,
        "authorization PR #91 head SHA is missing or invalid",
    )
    head_commit = github_api(
        f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{head_sha}"
    )
    merge_commit = github_api(
        f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{plan_head_sha}"
    )
    head_tree = head_commit.get("tree", {}).get("sha") if isinstance(head_commit, dict) else None
    merge_tree = merge_commit.get("tree", {}).get("sha") if isinstance(merge_commit, dict) else None
    merge_parents = merge_commit.get("parents") if isinstance(merge_commit, dict) else None
    require(
        isinstance(head_tree, str)
        and re.fullmatch(r"[0-9a-f]{40}", head_tree) is not None
        and isinstance(merge_tree, str)
        and re.fullmatch(r"[0-9a-f]{40}", merge_tree) is not None,
        "authorization PR #91 commit tree evidence is invalid",
    )
    require_external_review_attestation(
        anchor,
        pr,
        head_commit,
        head_sha,
        head_tree,
    )
    require(
        merge_tree == head_tree,
        "squash merge tree differs from the attested PR #91 head tree",
    )
    require(
        isinstance(merge_parents, list)
        and len(merge_parents) == 1
        and isinstance(merge_parents[0], dict)
        and merge_parents[0].get("sha") == identity["base_sha"],
        "PR #91 squash merge must have exactly the expected original base SHA as parent",
    )


def require_docs_candidate_pr_merged(
    anchor: dict[str, Any],
) -> None:
    binding = anchor["docs_candidate_binding"]
    identity = binding["pull_request_identity"]
    pr = github_api(f"repos/{DOCS_REPOSITORY}/pulls/{binding['pr']}")
    require(isinstance(pr, dict), "docs PR #386 response is invalid")
    require(
        pr.get("number") == identity["number"]
        and pr.get("html_url") == binding["pr_url"]
        and pr.get("base", {}).get("sha") == identity["base_sha"]
        and pr.get("base", {}).get("ref") == identity["base_ref"]
        and pr.get("base", {}).get("repo", {}).get("full_name")
        == identity["base_repo"]
        and pr.get("head", {}).get("sha") == binding["commit_sha"]
        and pr.get("head", {}).get("ref") == identity["head_ref"]
        and pr.get("head", {}).get("repo", {}).get("full_name")
        == identity["head_repo"],
        "docs PR #386 base/head identity mismatch",
    )
    require(
        pr.get("state") == "closed"
        and pr.get("merged") is True
        and isinstance(pr.get("merged_at"), str)
        and isinstance(pr.get("merge_commit_sha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", pr["merge_commit_sha"]) is not None,
        "FMV3-M1-06 requires merged docs PR #386",
    )
    require(
        pr.get("user", {}).get("login") == anchor["authorized_issuer"]
        and pr.get("author_association") in anchor["allowed_author_associations"]
        and pr.get("merged_by", {}).get("login") == anchor["authorized_issuer"],
        "docs PR #386 issuer, association, or merger is not authorized",
    )
    head_commit = github_api(
        f"repos/{DOCS_REPOSITORY}/git/commits/{binding['commit_sha']}"
    )
    merge_commit = github_api(
        f"repos/{DOCS_REPOSITORY}/git/commits/{pr['merge_commit_sha']}"
    )
    require(
        isinstance(head_commit, dict)
        and head_commit.get("tree", {}).get("sha") == binding["commit_tree_sha"],
        "docs PR #386 bound candidate head tree mismatch",
    )
    require(
        isinstance(merge_commit, dict)
        and merge_commit.get("tree", {}).get("sha") == binding["commit_tree_sha"]
        and isinstance(merge_commit.get("parents"), list)
        and len(merge_commit["parents"]) == 1
        and merge_commit["parents"][0].get("sha") == identity["base_sha"],
        "docs PR #386 squash merge topology or tree mismatch",
    )


def load_issue_authorization_evidence(
    path_value: str | None,
    issue_id: str,
) -> dict[str, Any] | None:
    if issue_id != "FMV3-M2-01":
        require(
            path_value is None,
            "--authorization-evidence is accepted only for FMV3-M2-01",
        )
        return None
    require(
        isinstance(path_value, str) and path_value,
        "FMV3-M2-01 requires --authorization-evidence <external-json-file>",
    )
    path = Path(path_value)
    require(
        path.is_absolute() and path.is_file() and not path.is_symlink(),
        "authorization evidence must be an absolute regular non-symlink file",
    )
    evidence_bytes = path.read_bytes()
    require(
        0 < len(evidence_bytes) <= 65536,
        "authorization evidence size is outside the fail-closed bound",
    )
    evidence = unique_json_object(
        evidence_bytes.decode("utf-8"),
        "authorization evidence",
    )
    require(
        set(evidence) == {"schema", "authorization_issue", "producer"}
        and evidence.get("schema") == AUTHORIZATION_EVIDENCE_SCHEMA
        and evidence.get("authorization_issue") == "FMV3-M2-01",
        "authorization evidence envelope mismatch",
    )
    producer = evidence.get("producer")
    require(
        isinstance(producer, dict)
        and set(producer)
        == {
            "plan_issue",
            "repository",
            "github_issue_number",
            "github_pull_request_number",
            "merge_sha",
        }
        and producer.get("plan_issue") == "FMV3-M1-06"
        and producer.get("repository") == MODBUS_REPOSITORY
        and type(producer.get("github_issue_number")) is int
        and producer["github_issue_number"] > 0
        and type(producer.get("github_pull_request_number")) is int
        and producer["github_pull_request_number"] > 0
        and isinstance(producer.get("merge_sha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", producer["merge_sha"]) is not None,
        "FMV3-M2-01 producer evidence schema mismatch",
    )
    return producer


def require_m1_06_producer_evidence(producer: dict[str, Any]) -> None:
    merge_sha = producer["merge_sha"]
    issue_number = producer["github_issue_number"]
    pr_number = producer["github_pull_request_number"]
    main_sha = canonical_main_sha(MODBUS_REPOSITORY)
    issue = github_api(f"repos/{MODBUS_REPOSITORY}/issues/{issue_number}")
    pr = github_api(f"repos/{MODBUS_REPOSITORY}/pulls/{pr_number}")
    merge_commit = github_api(f"repos/{MODBUS_REPOSITORY}/git/commits/{merge_sha}")
    compare = github_api(
        f"repos/{MODBUS_REPOSITORY}/compare/{merge_sha}...{main_sha}"
    )
    timeline = github_api(
        f"repos/{MODBUS_REPOSITORY}/issues/{issue_number}/timeline?per_page=100"
    )
    require(
        isinstance(issue, dict)
        and issue.get("number") == issue_number
        and issue.get("repository_url")
        == f"https://api.github.com/repos/{MODBUS_REPOSITORY}"
        and issue.get("state") == "closed"
        and not issue.get("pull_request")
        and isinstance(issue.get("title"), str)
        and issue["title"].startswith("FMV3-M1-06"),
        "M1-06 producer issue identity or closure mismatch",
    )
    require(
        isinstance(pr, dict)
        and pr.get("number") == pr_number
        and pr.get("state") == "closed"
        and pr.get("merged") is True
        and pr.get("merge_commit_sha") == merge_sha
        and pr.get("base", {}).get("ref") == "main"
        and pr.get("base", {}).get("repo", {}).get("full_name")
        == MODBUS_REPOSITORY
        and pr.get("head", {}).get("repo", {}).get("full_name")
        == MODBUS_REPOSITORY,
        "M1-06 producer PR identity or merge SHA mismatch",
    )
    require(
        isinstance(pr.get("body"), str)
        and re.search(
            rf"(?im)^\s*(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#{issue_number}\s*[.]?\s*$",
            pr["body"],
        )
        is not None,
        "M1-06 producer PR does not close the supplied issue",
    )
    require(
        parse_github_time(issue.get("closed_at"), "M1-06 issue closed_at")
        >= parse_github_time(pr.get("merged_at"), "M1-06 PR merged_at"),
        "M1-06 producer issue closed before the supplied PR merged",
    )
    require(
        isinstance(merge_commit, dict)
        and merge_commit.get("sha") == merge_sha
        and isinstance(merge_commit.get("parents"), list)
        and len(merge_commit["parents"]) == 1,
        "M1-06 producer merge commit is not one exact squash commit",
    )
    require(
        isinstance(compare, dict)
        and compare.get("status") in {"ahead", "identical"}
        and compare.get("merge_base_commit", {}).get("sha") == merge_sha,
        "M1-06 producer merge SHA is not on canonical helianthus-modbus main",
    )
    require(isinstance(timeline, list), "M1-06 producer issue timeline is invalid")
    require(
        any(
            isinstance(event, dict)
            and event.get("event") == "cross-referenced"
            and event.get("source", {}).get("issue", {}).get("number") == pr_number
            and event.get("source", {})
            .get("issue", {})
            .get("pull_request", {})
            .get("url")
            == f"https://api.github.com/repos/{MODBUS_REPOSITORY}/pulls/{pr_number}"
            for event in timeline
        ),
        "M1-06 producer PR/issue cross-reference is absent",
    )


def require_issue_authorization_dependencies(
    issue_id: str,
    anchor: dict[str, Any],
    evidence_path: str | None,
) -> None:
    require(
        anchor.get("issue_evidence_policy") == EXPECTED_ISSUE_EVIDENCE_POLICY,
        "issue authorization evidence policy mismatch",
    )
    producer = load_issue_authorization_evidence(evidence_path, issue_id)
    if issue_id in {"FMV3-M1-06", "FMV3-M2-01"}:
        require_docs_candidate_pr_merged(anchor)
    if producer is not None:
        require_m1_06_producer_evidence(producer)
    r2_rebind = anchor["docs_candidate_binding"]["r2_rebind"]
    require(
        r2_rebind["status"] == "BOUND_DOCS_R2"
        and issue_id not in r2_rebind["blocks_authorization_for"],
        "authorization blocked: exact docs R2 binding is incomplete",
    )
def require_m1_admission_open(repo_root: Path, origin_main: str) -> None:
    gate_path = repo_root / M1_ADMISSION_GATE
    require(gate_path.is_file() and not gate_path.is_symlink(), "Modbus M1 admission gate is missing")
    committed_gate = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"HEAD:{M1_ADMISSION_GATE.as_posix()}"],
        check=True,
        capture_output=True,
    ).stdout
    require(gate_path.read_bytes() == committed_gate, "Modbus M1 admission gate differs from committed HEAD")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    require(isinstance(gate, dict) and set(gate) == M1_ADMISSION_KEYS, "Modbus M1 admission gate schema mismatch")
    require(gate["schema"] == "helianthus.execution.modbus-m1-admission" and gate["version"] == 1 and type(gate["version"]) is int, "Modbus M1 admission gate identity mismatch")
    require(gate["state"] == "OPEN", "Modbus M1 admission gate is not OPEN")
    require(gate["docs_repository"] == "Project-Helianthus/helianthus-docs-ebus" and gate["docs_pr"] == M1_DOCS_PR and type(gate["docs_pr"]) is int, "Modbus M1 admission docs identity mismatch")
    require(gate["trust_anchor_repository"] == "Project-Helianthus/helianthus-execution-plans", "Modbus M1 trust anchor repository mismatch")
    require(gate["required_check"] == "Modbus Trusted Revision", "Modbus M1 required check mismatch")
    for key in ("docs_merge_sha", "trust_anchor_commit"):
        require(isinstance(gate[key], str) and re.fullmatch(r"[0-9a-f]{40}", gate[key]) is not None, f"Modbus M1 gate {key} must be a full lowercase SHA")
    require(gate["branch_protection_evidence_url"] == "https://api.github.com/repos/Project-Helianthus/helianthus-docs-ebus/branches/main/protection/required_status_checks", "Modbus M1 branch-protection evidence URL mismatch")
    require(isinstance(gate["required_check_verified_at"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", gate["required_check_verified_at"]) is not None, "Modbus M1 gate verification timestamp is invalid")
    require(isinstance(gate["verification_pr"], int) and type(gate["verification_pr"]) is int and gate["verification_pr"] > M1_DOCS_PR, "Modbus M1 gate verification PR is invalid")
    require(isinstance(gate["verification_head_sha"], str) and re.fullmatch(r"[0-9a-f]{40}", gate["verification_head_sha"]) is not None, "Modbus M1 verification head SHA is invalid")
    require(isinstance(gate["required_check_run_url"], str) and gate["required_check_run_url"].startswith("https://github.com/Project-Helianthus/helianthus-docs-ebus/actions/runs/"), "Modbus M1 required-check run URL is invalid")
    anchor_is_merged = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", gate["trust_anchor_commit"], origin_main],
        check=False,
    ).returncode == 0
    require(anchor_is_merged, "Modbus trust anchor commit is not merged on execution-plans main")
    anchor_script = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{gate['trust_anchor_commit']}:scripts/validate_modbus_docs_trust.py"],
        check=False,
        capture_output=True,
    )
    require(anchor_script.returncode == 0 and anchor_script.stdout, "Modbus trust anchor script is absent from its merged commit")
    require(
        hashlib.sha256(anchor_script.stdout).hexdigest()
        == M1_TRUST_ANCHOR_VALIDATOR_SHA256,
        "Modbus trust anchor script is not the independently frozen M1 anchor",
    )

    docs_pr = github_api(
        f"repos/Project-Helianthus/helianthus-docs-ebus/pulls/{M1_DOCS_PR}"
    )
    require(docs_pr.get("merged") is True and docs_pr.get("merge_commit_sha") == gate["docs_merge_sha"], f"docs PR #{M1_DOCS_PR} merge evidence mismatch")
    verification_pr = github_api(f"repos/Project-Helianthus/helianthus-docs-ebus/pulls/{gate['verification_pr']}")
    require(
        verification_pr.get("merged") is True
        and verification_pr.get("base", {}).get("ref") == "main"
        and verification_pr.get("head", {}).get("sha") == gate["verification_head_sha"],
        "required-check verification PR evidence mismatch",
    )
    protection = github_api("repos/Project-Helianthus/helianthus-docs-ebus/branches/main/protection/required_status_checks")
    contexts = protection.get("contexts", [])
    checks = protection.get("checks", [])
    require(
        gate["required_check"] in contexts
        or any(isinstance(check, dict) and check.get("context") == gate["required_check"] for check in checks),
        "Modbus Trusted Revision is not a required main check",
    )
    check_runs = github_api(f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{gate['verification_head_sha']}/check-runs")
    runs = check_runs.get("check_runs", [])
    require(
        any(
            isinstance(run, dict)
            and run.get("name") == gate["required_check"]
            and run.get("conclusion") == "success"
            and run.get("details_url") == gate["required_check_run_url"]
            for run in runs
        ),
        "successful required-check run evidence mismatch",
    )
    workflow_api = github_api(
        "repos/Project-Helianthus/helianthus-docs-ebus/contents/"
        f".github/workflows/modbus-trusted-revision.yml?ref={gate['docs_merge_sha']}"
    )
    require(workflow_api.get("encoding") == "base64" and isinstance(workflow_api.get("content"), str), "docs workflow content evidence is invalid")
    workflow_text = base64.b64decode(workflow_api["content"]).decode("utf-8")
    try:
        workflow_value = json.loads(workflow_text)
        anchor_namespace: dict[str, Any] = {"__name__": "modbus_trust_anchor"}
        exec(
            compile(
                anchor_script.stdout.decode("utf-8"),
                "merged-modbus-trust-anchor",
                "exec",
            ),
            anchor_namespace,
        )
        expected_workflow = anchor_namespace["expected_workflow"](
            gate["trust_anchor_commit"]
        )
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValidationError(f"docs trusted workflow evidence is invalid: {exc}") from exc
    require(workflow_value == expected_workflow, "docs workflow does not exactly match the merged trust anchor contract")
def require_unique_metadata(text: str, key: str, expected: str, label: str) -> None:
    values = re.findall(rf"^{re.escape(key)}: (.+)$", text, re.MULTILINE)
    require(len(values) == 1, f"{label} must contain exactly one {key} field")
    require(values[0] == expected, f"{label} {key} mismatch")
def render_issue_map_gates(issue: dict[str, Any]) -> str:
    values = list(issue["gates"])
    if issue.get("companion_issue"):
        values.append(f"companion {issue['companion_issue']}")
    if issue.get("corrective_companion_issue"):
        values.append(f"corrective companion {issue['corrective_companion_issue']}")
    return ", ".join(values)
def load_plan(path: Path) -> dict[str, Any]:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)
    require(isinstance(value, dict), "plan.yaml root must be a mapping")
    return value
def require_fields(item: Any, fields: set[str], label: str) -> None:
    require(isinstance(item, dict), f"{label} must be a mapping")
    missing = fields - set(item)
    require(not missing, f"{label} missing fields: {sorted(missing)}")
def require_nonempty_text(value: Any, label: str) -> None:
    require(isinstance(value, str) and value.strip(), f"{label} must be non-empty text")
def validate_dag(nodes: set[str], dependencies: dict[str, list[str]], label: str) -> None:
    for node, deps in dependencies.items():
        require(isinstance(deps, list) and all(isinstance(dep, str) for dep in deps), f"{label} {node} depends_on must be a string list")
        require(len(deps) == len(set(deps)), f"{label} {node} has duplicate dependencies")
        require(node not in deps, f"{label} {node} depends on itself")
        unknown = set(deps) - nodes
        require(not unknown, f"{label} {node} has unknown dependencies: {sorted(unknown)}")
    state: dict[str, int] = {}
    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 1:
            raise ValidationError(f"{label} cycle: {' -> '.join(trail + [node])}")
        if state.get(node) == 2: return
        state[node] = 1
        for dep in dependencies[node]:
            visit(dep, trail + [node])
        state[node] = 2
    for node in sorted(nodes):
        visit(node, [])
def ancestors(node: str, dependencies: dict[str, list[str]]) -> set[str]:
    result: set[str] = set()
    stack = list(dependencies[node])
    while stack:
        dep = stack.pop()
        if dep not in result:
            result.add(dep)
            stack.extend(dependencies[dep])
    return result
def parse_issue_map(text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("| FMV3-"): continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        require(len(cells) == 8, f"issue-map row must have 8 cells: {line}")
        require(cells[0] not in rows, f"duplicate issue-map row: {cells[0]}")
        rows[cells[0]] = cells
    return rows
def parse_exact_markdown_table(
    text: str,
    header: str,
    separator: str,
    label: str,
) -> list[list[str]]:
    lines = text.splitlines()
    require(lines.count(header) == 1, f"{label} must contain one exact header")
    index = lines.index(header)
    require(index + 1 < len(lines) and lines[index + 1] == separator,
            f"{label} separator mismatch")
    rows: list[list[str]] = []
    for line in lines[index + 2:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    require(rows, f"{label} must contain rows")
    return rows
def validate_authorization_schema(plan: dict[str, Any]) -> dict[str, Any]:
    authorization = plan.get("execution_authorization")
    require(isinstance(authorization, dict), "execution_authorization must be a mapping")
    anchor = authorization.get("authorization_anchor")
    require(isinstance(anchor, dict), "authorization_anchor must be a mapping")
    require(
        anchor.get("authorization_pr") == AMENDMENT_PR_URL,
        "current authorization PR mismatch",
    )
    require(
        not ({"issue", "meta_issue", "marker"} & set(anchor))
        and "authorization_amendment" not in authorization,
        "authorization schema must not contain unverified GitHub issue or marker authority",
    )
    surface_digest = anchor.get("amendment_surfaces_sha256")
    require(
        isinstance(surface_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", surface_digest) is not None,
        "authorization amendment surface digest must be lowercase SHA-256",
    )
    expected = {
        "authorized_on": "2026-07-30",
        "availability_mode": "openai_only",
        "scope": "pre_gateway_transport_docs_registry",
        "scope_authority": "authorized_issues_only",
        "selection_policy": "fail_closed",
        "preflight_enforcement": "materialize authorization_anchor.tooling_binding.validator_path from --plan-head-sha, verify its anchored SHA-256, then execute it with --materialized-anchor-validator --authorize-issue <ID>",
        "milestone_labels_non_authoritative": ["M0", "M1", "M2", "M3"],
        "authorized_issues": AUTHORIZED_ISSUES,
        "authorized_issue_contract_sha256": authorization.get(
            "authorized_issue_contract_sha256"
        ),
        "authorization_anchor": {
            "required": True,
            "record_type": "github_merged_pr_v1",
            "authorization_pr": AMENDMENT_PR_URL,
            "predecessor_authorization_pr": PREDECESSOR_AUTHORIZATION_PR_URL,
            "predecessor_role": "provenance_only",
            "plan_repo": "Project-Helianthus/helianthus-execution-plans",
            "plan_path": "fronius-modbus-multivendor-v3-w29-26.implementing/plan.yaml",
            "authorized_issuer": "d3vi1",
            "allowed_author_associations": ["MEMBER", "OWNER"],
            "merge_requirement": "exact_pr_merge_commit_is_anchor_and_ancestor_of_origin_main",
            "bind": [
                "plan_head_sha",
                "authorized_issue_contract_sha256",
                "amendment_surfaces_sha256",
                "authorized_issue",
                "docs_candidate_binding",
                "tooling_binding",
                "pull_request_identity",
                "external_review_attestation",
                "issue_evidence_policy",
                "accepted_decision_d13",
                "m2_exit_gate",
            ],
            "corrected_issues": ["FMV3-M1-05", "FMV3-M1-06", "FMV3-M2-01"],
            "docs_candidate_binding": EXPECTED_DOCS_CANDIDATE_BINDING,
            "tooling_binding": anchor.get("tooling_binding"),
            "pull_request_identity": EXPECTED_PR_IDENTITY,
            "external_review_attestation": EXPECTED_EXTERNAL_REVIEW_ATTESTATION,
            "issue_evidence_policy": EXPECTED_ISSUE_EVIDENCE_POLICY,
            "stop_before_issue": "FMV3-M4-01",
            "gateway_work_authorized": False,
            "amendment_surfaces_sha256": surface_digest,
        },
        "repository_creation_authorized": True,
        "repository_creation_targets": {
            "public": ["helianthus-modbus", "helianthus-modbusreg"],
            "private": [],
        },
        "private_repository_creation": "deferred_requires_future_explicit_authorization",
        "implementation_authorized": True,
        "issue_commit_push_authorized": True,
        "deferred_issues": ["FMV3-M0-04", "FMV3-M0-05", "FMV3-M0-07"],
        "stop_before_issue": "FMV3-M4-01",
        "gateway_work_authorized": False,
    }
    require(authorization == expected, "execution authorization mismatch")
    require(
        isinstance(anchor["tooling_binding"], dict),
        "authorization tooling binding must be a mapping",
    )
    return authorization
def extract_canonical_authorization_block(text: str) -> str:
    matches = re.findall(
        r"^## Execution authorization\n\n(.*?)\n\n^## Claim discipline$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    require(len(matches) == 1, "canonical authorization block must occur exactly once")
    require(
        normalize_semantic_whitespace(matches[0])
        == normalize_semantic_whitespace(CANONICAL_AUTHORIZATION_BLOCK),
        "canonical authorization and hard-stop block mismatch",
    )
    return normalize_semantic_whitespace(matches[0])


def normalize_semantic_whitespace(text: str) -> str:
    """Collapse non-normative prose whitespace before authorization comparison."""
    return " ".join(text.split())


def replace_exact_lifecycle_line(
    text: str,
    pattern: str,
    replacement: str,
    label: str,
) -> str:
    replaced, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    require(count == 1, f"{label} lifecycle line must occur exactly once")
    return replaced


def normalized_surface_content(name: str, text: str) -> str:
    """Normalize a complete normative surface with an explicit mutation allowlist."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    canonical_hash_files = {
        "01-index.md",
        "10-architecture-and-repo-boundaries.md",
        "11-fronius-readonly-and-semantic-lock.md",
        "12-vendor-expansion-and-private-bindings.md",
        "13-roadmap-gates-and-risks.md",
        "99-status.md",
    }
    if name in canonical_hash_files:
        normalized = replace_exact_lifecycle_line(
            normalized,
            r"^Canonical-SHA256: `[0-9a-f]{64}`$",
            "Canonical-SHA256: `<canonical>`",
            f"{name} canonical hash",
        )
    if name == "00-canonical.md":
        normalized = replace_exact_lifecycle_line(
            normalized,
            r"^State: `(locked|implementing|maintenance)`$",
            "State: `<lifecycle-state>`",
            "canonical state",
        )
    elif name == "01-index.md":
        normalized = replace_exact_lifecycle_line(
            normalized,
            r"^# (Locked|Implementing|Maintenance) package index$",
            "# <Lifecycle-state> package index",
            "index heading",
        )
        normalized = replace_exact_lifecycle_line(
            normalized,
            r"^\| `99-status\.md` \| Current (locked|implementing|maintenance) and authorization state \|$",
            "| `99-status.md` | Current <lifecycle-state> and authorization state |",
            "index status description",
        )
    elif name == "99-status.md":
        normalized = replace_exact_lifecycle_line(
            normalized,
            r"^# (Locked|Implementing|Maintenance) status$",
            "# <Lifecycle-state> status",
            "status heading",
        )
        lifecycle_patterns = {
            "State": r"^(?:locked|implementing|maintenance)$",
            "Current milestone": r"^M[0-8]$",
            "Review epoch": r"^[1-9][0-9]*$",
            "Review state": r"^(?:IN_PROGRESS|FAILED|PASSED)$",
            "Accepted adversarial rounds": r"^[0-5]/5$",
            "Review target": r"^(?:R[1-5]|ARCHIVED|TERMINAL_NO_FINDINGS)$",
        }
        for key in AMENDMENT_STATUS_MUTABLE_FIELDS:
            normalized = replace_exact_lifecycle_line(
                normalized,
                rf"^{re.escape(key)}: {lifecycle_patterns[key][1:-1]}$",
                f"{key}: `<lifecycle>`",
                f"status {key}",
            )
    return normalize_semantic_whitespace(normalized)


def normalized_canonical_semantics(text: str) -> str:
    return normalized_surface_content("00-canonical.md", text)


def amendment_status_projection(status: str) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    for key in AMENDMENT_STATUS_IMMUTABLE_FIELDS:
        values = re.findall(rf"^{re.escape(key)}: (.+)$", status, re.MULTILINE)
        require(len(values) == 1, f"status must contain exactly one {key} field")
        metadata[key] = values[0]
    state_values = re.findall(r"^State: (.+)$", status, re.MULTILINE)
    require(len(state_values) == 1, "status must contain exactly one State field")
    hard_stop = re.fullmatch(
        r"no; stop before (FMV3-M[0-8]-\d{2})",
        metadata["Gateway work authorized"],
    )
    gateway_work_authorized = hard_stop is None
    return {
        "state": "<lifecycle-state>",
        "actual_state": state_values[0],
        "authorization_scope": metadata["Authorization scope authority"],
        "authorization_anchor": metadata["Authorization anchor"],
        "canonical_main_authority": metadata["Canonical main authority"],
        "external_review_attestation": metadata["External review attestation"],
        "docs_r2_rebind": metadata["Docs R2 rebind"],
        "gateway_work_authorized": gateway_work_authorized,
        "hard_stop_issue": hard_stop.group(1) if hard_stop is not None else None,
    }


def corrective_phase_gates(phase_gates: list[Any]) -> list[dict[str, Any]]:
    return [
        gate
        for gate in phase_gates
        if isinstance(gate, dict)
        and gate.get("id") in EXPECTED_CORRECTIVE_PHASE_GATE_IDS
    ]


def validate_corrective_phase_gates(phase_gates: list[Any]) -> None:
    gate_ids = [gate.get("id") for gate in phase_gates if isinstance(gate, dict)]
    require(len(gate_ids) == len(set(gate_ids)), "duplicate phase gate ID")
    gates = corrective_phase_gates(phase_gates)
    require(
        [gate["id"] for gate in gates] == EXPECTED_CORRECTIVE_PHASE_GATE_IDS,
        "corrective phase gate order mismatch",
    )
    require(
        gates == EXPECTED_CORRECTIVE_PHASE_GATES,
        "corrective docs-to-M1-to-M2 phase gate projection mismatch",
    )


def require_matching_amendment_snapshots(
    anchored_projection: dict[str, Any],
    current_projection: dict[str, Any],
) -> None:
    anchored_status = anchored_projection["status"]
    current_status = current_projection["status"]
    require(
        current_status["gateway_work_authorized"]
        == anchored_status["gateway_work_authorized"],
        "status Gateway work authorized mismatch",
    )
    require(
        current_projection == anchored_projection,
        "current main amendment surface digest differs from merged PR #91 anchor",
    )


def require_no_gateway_authorization_contradiction(
    plan: dict[str, Any],
    texts: dict[str, str],
) -> None:
    authorization = plan.get("execution_authorization", {})
    anchor = authorization.get("authorization_anchor", {})
    require(
        authorization.get("gateway_work_authorized") is False
        and anchor.get("gateway_work_authorized") is False
        and authorization.get("stop_before_issue") == "FMV3-M4-01"
        and anchor.get("stop_before_issue") == "FMV3-M4-01",
        "gateway authorization machine contradiction",
    )
    forbidden = (
        r"\bgateway(?:\s+work)?\s+(?:is\s+)?authorized\s*:\s*(?:yes|true)\b",
        r"\bgateway\s+work\s+is\s+authorized\b",
        r"\bgateway\s+(?:execution|implementation|development)\s+is\s+authorized\b",
        r"\bgateway(?:\s+work)?\s+authorization\s+is\s+granted\b",
        r"\bFMV3-M4-01\s+is\s+authorized\b",
        r"\bgateway_work_authorized\s*:\s*true\b",
    )
    searchable = {"plan.yaml": json.dumps(plan, ensure_ascii=True), **texts}
    for name, text in searchable.items():
        require(
            not any(re.search(pattern, text, re.IGNORECASE) for pattern in forbidden),
            f"contradictory gateway authorization in {name}",
        )


def amendment_surface_projection(
    plan: dict[str, Any],
    texts: dict[str, str],
) -> dict[str, Any]:
    require(
        set(texts) == set(AMENDMENT_SURFACE_FILES),
        "amendment surface file set mismatch",
    )
    require_no_gateway_authorization_contradiction(plan, texts)
    authorization = validate_authorization_schema(plan)
    anchor = authorization["authorization_anchor"]
    issues = plan.get("issues")
    require(isinstance(issues, list), "issues must be a list")
    issue_sequence = [
        issue.get("id")
        for issue in issues
        if isinstance(issue, dict) and issue.get("id") in AMENDMENT_ISSUE_IDS
    ]
    require(
        issue_sequence == list(AMENDMENT_ISSUE_IDS),
        "corrective issue sequence mismatch",
    )
    issues_by_id = {
        issue.get("id"): issue
        for issue in issues
        if isinstance(issue, dict) and issue.get("id") in AMENDMENT_ISSUE_IDS
    }
    require(
        list(issues_by_id) == list(AMENDMENT_ISSUE_IDS),
        "corrective issue rows missing or duplicated",
    )
    phase_gates = plan.get("phase_gates")
    require(isinstance(phase_gates, list), "phase_gates must be a list")
    corrective_gates = corrective_phase_gates(phase_gates)
    issue_map_rows = parse_issue_map(texts["90-issue-map.md"])
    require(
        all(issue_map_rows.get(issue_id) is not None for issue_id in AMENDMENT_ISSUE_IDS),
        "issue-map corrective rows missing",
    )
    milestone_rows = parse_exact_markdown_table(
        texts["91-milestone-map.md"],
        "| Milestone | Depends on | Entry | Exit | Parallelism |",
        "|---|---|---|---|---|",
        "milestone map",
    )
    require(
        [row[0] for row in milestone_rows] == [f"M{number}" for number in range(9)]
        and all(len(row) == 5 for row in milestone_rows),
        "milestone-map row order or shape mismatch",
    )
    milestone_by_id = {row[0]: row for row in milestone_rows}
    require(
        {key: milestone_by_id.get(key) for key in EXPECTED_MILESTONE_ROWS}
        == EXPECTED_MILESTONE_ROWS,
        "milestone-map M1/M2 projection mismatch",
    )
    corrective_gate_rows = parse_exact_markdown_table(
        texts["91-milestone-map.md"],
        "| Gate | Required predecessor | Blocked issue |",
        "|---|---|---|",
        "milestone-map corrective gate",
    )
    require(
        corrective_gate_rows == EXPECTED_CORRECTIVE_GATE_ROWS,
        "milestone-map corrective gate projection mismatch",
    )
    status = texts["99-status.md"]
    status_projection = amendment_status_projection(status)
    status_states = [status_projection["actual_state"]]
    require(
        status_states == [str(plan.get("state"))],
        "status state projection mismatch",
    )
    status_issue_counts = re.findall(
        r"^- ([0-9]+)-issue one-repository DAG and nine milestone groupings authored;$",
        status,
        re.MULTILINE,
    )
    require(
        status_issue_counts == [str(EXPECTED_ISSUE_COUNT)],
        "status issue-count projection mismatch",
    )
    canonical_block = extract_canonical_authorization_block(texts["00-canonical.md"])
    decisions = plan.get("decisions")
    require(isinstance(decisions, list), "decisions must be a list")
    decision_d13 = [row for row in decisions if isinstance(row, dict) and row.get("id") == "D13"]
    require(len(decision_d13) == 1, "accepted decision D13 must occur exactly once")
    require(
        decision_d13[0]
        == {"id": "D13", "status": "accepted", "decision": EXPECTED_D13_DECISION},
        "accepted decision D13 mismatch",
    )
    milestones = plan.get("milestones")
    require(isinstance(milestones, list), "milestones must be a list")
    milestone_m2 = [row for row in milestones if isinstance(row, dict) and row.get("id") == "M2"]
    require(len(milestone_m2) == 1, "milestone M2 must occur exactly once")
    require(
        milestone_m2[0].get("exit_gate") == EXPECTED_M2_EXIT_GATE,
        "M2 exit gate mismatch",
    )
    return {
        "schema": "helianthus.fmv3-amendment-surfaces.v1",
        "execution_authorization": {
            "authorized_issues": authorization["authorized_issues"],
            "authorization_pr": anchor["authorization_pr"],
            "predecessor_authorization_pr": anchor[
                "predecessor_authorization_pr"
            ],
            "predecessor_role": anchor["predecessor_role"],
            "corrected_issues": anchor["corrected_issues"],
            "docs_candidate_binding": anchor["docs_candidate_binding"],
            "tooling_binding": anchor["tooling_binding"],
            "pull_request_identity": anchor["pull_request_identity"],
            "external_review_attestation": anchor[
                "external_review_attestation"
            ],
            "issue_evidence_policy": anchor["issue_evidence_policy"],
            "stop_before_issue": authorization["stop_before_issue"],
            "gateway_work_authorized": authorization["gateway_work_authorized"],
        },
        "accepted_decision_d13": decision_d13[0],
        "m2_exit_gate": milestone_m2[0].get("exit_gate"),
        "issue_sequence": issue_sequence,
        "issue_rows": [issues_by_id[issue_id] for issue_id in AMENDMENT_ISSUE_IDS],
        "issue_map_rows": [
            issue_map_rows[issue_id] for issue_id in AMENDMENT_ISSUE_IDS
        ],
        "phase_gates": [
            *corrective_gates,
        ],
        "canonical_authorization_block": canonical_block,
        "canonical_semantics_sha256": hashlib.sha256(
            normalized_canonical_semantics(texts["00-canonical.md"]).encode("utf-8")
        ).hexdigest(),
        "milestone_rows": [
            milestone_by_id["M1"],
            milestone_by_id["M2"],
        ],
        "milestone_corrective_gate_rows": corrective_gate_rows,
        "status": {
            "issue_count": int(status_issue_counts[0]),
            **{
                key: value
                for key, value in status_projection.items()
                if key != "actual_state"
            },
        },
        "normalized_full_markdown_sha256": {
            name: hashlib.sha256(
                normalized_surface_content(name, texts[name]).encode("utf-8")
            ).hexdigest()
            for name in AMENDMENT_SURFACE_FILES
        },
    }
def amendment_projection_digest(projection: dict[str, Any]) -> str:
    encoded = json.dumps(
        projection,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def amendment_surface_digest(plan: dict[str, Any], texts: dict[str, str]) -> str:
    return amendment_projection_digest(amendment_surface_projection(plan, texts))
def load_amendment_surface_texts(root: Path) -> dict[str, str]:
    return {
        name: (root / name).read_text(encoding="utf-8")
        for name in AMENDMENT_SURFACE_FILES
    }
def validate_content_hygiene(root: Path) -> None:
    path_patterns = {"macOS absolute path": re.compile(r"/Users/"), "Unix home path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
                     "Windows absolute path": re.compile(r"[A-Za-z]:\\\\"), "file URI": re.compile(r"file://", re.IGNORECASE)}
    secret_patterns = {"GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
                       "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
                       "assigned credential": re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{12,}")}
    for path in sorted(root.iterdir()):
        if path.suffix not in {".md", ".yaml"}: continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in {**path_patterns, **secret_patterns}.items():
            require(not pattern.search(text), f"{path.name} contains prohibited {label}")


def require_materialized_validator_context() -> None:
    validator_value = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}VALIDATOR")
    digest = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}SHA256")
    token_value = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}TOKEN")
    token_path_value = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}TOKEN_FILE")
    require(
        all((validator_value, digest, token_value, token_path_value)),
        "direct use of --materialized-anchor-validator is forbidden",
    )
    validator_path = Path(str(validator_value)).resolve()
    token_path = Path(str(token_path_value)).resolve()
    require(
        Path(__file__).resolve() == validator_path
        and validator_path.is_file()
        and not validator_path.is_symlink()
        and token_path.is_file()
        and not token_path.is_symlink()
        and validator_path.parent == token_path.parent
        and validator_path.parent.stat().st_mode & 0o077 == 0
        and validator_path.stat().st_mode & 0o077 == 0
        and token_path.stat().st_mode & 0o077 == 0,
        "materialized anchor validator context is not private and exact",
    )
    require(
        isinstance(digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and hashlib.sha256(validator_path.read_bytes()).hexdigest() == digest,
        "materialized anchor validator SHA-256 mismatch",
    )
    require(
        secrets.compare_digest(token_path.read_text(encoding="ascii"), str(token_value)),
        "materialized anchor validator one-use token mismatch",
    )
    token_path.unlink()


def materialize_and_reexec_anchor_validator(
    root: Path,
    args: argparse.Namespace,
) -> int:
    require(
        args.plan_head_sha is not None
        and re.fullmatch(r"[0-9a-f]{40}", args.plan_head_sha) is not None,
        "--plan-head-sha with a full lowercase 40-character SHA is mandatory",
    )
    repo_root = Path(
        git_command(
            root,
            ["rev-parse", "--show-toplevel"],
            "plan repository toplevel lookup",
        ).strip()
    ).resolve()
    anchored_plan_path = Path(
        "fronius-modbus-multivendor-v3-w29-26.implementing/plan.yaml"
    )
    anchored_plan_bytes = committed_regular_blob(
        repo_root,
        args.plan_head_sha,
        anchored_plan_path.as_posix(),
        "authorization anchor plan",
    )
    anchored_plan = yaml.load(anchored_plan_bytes, Loader=UniqueLoader)
    require(isinstance(anchored_plan, dict), "anchored plan.yaml must be a mapping")
    anchored_authorization = anchored_plan.get("execution_authorization")
    require(
        isinstance(anchored_authorization, dict),
        "anchored execution authorization must be a mapping",
    )
    anchored_anchor = anchored_authorization.get("authorization_anchor")
    require(
        isinstance(anchored_anchor, dict),
        "authorization record is absent from the supplied plan anchor",
    )
    tooling = anchored_anchor.get("tooling_binding")
    require(
        isinstance(tooling, dict)
        and tooling.get("authorization_execution")
        == "materialized_from_pr91_anchor"
        and tooling.get("validator_path") == EXPECTED_TOOLING_PATHS["validator_path"],
        "anchored validator materialization binding mismatch",
    )
    expected_digest = tooling.get("validator_sha256")
    require(
        isinstance(expected_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", expected_digest) is not None,
        "anchored validator SHA-256 is invalid",
    )
    validator_bytes = committed_regular_blob(
        repo_root,
        args.plan_head_sha,
        tooling["validator_path"],
        "authorization anchor validator",
    )
    require(
        hashlib.sha256(validator_bytes).hexdigest() == expected_digest,
        "authorization anchor validator SHA-256 mismatch",
    )
    with tempfile.TemporaryDirectory(prefix="fmv3-anchor-validator-") as temporary:
        temporary_path = Path(temporary)
        temporary_path.chmod(0o700)
        validator_path = temporary_path / "validate_plan.py"
        token_path = temporary_path / "one-use-token"
        token = secrets.token_hex(32)
        validator_path.write_bytes(validator_bytes)
        validator_path.chmod(0o500)
        token_path.write_text(token, encoding="ascii")
        token_path.chmod(0o400)
        environment = os.environ.copy()
        environment[f"{MATERIALIZATION_ENV_PREFIX}VALIDATOR"] = str(validator_path)
        environment[f"{MATERIALIZATION_ENV_PREFIX}SHA256"] = expected_digest
        environment[f"{MATERIALIZATION_ENV_PREFIX}TOKEN"] = token
        environment[f"{MATERIALIZATION_ENV_PREFIX}TOKEN_FILE"] = str(token_path)
        command = [
            sys.executable,
            str(validator_path),
            *sys.argv[1:],
            "--materialized-anchor-validator",
        ]
        result = subprocess.run(command, check=False, env=environment)
        return result.returncode


def prepare_plan_authorization_checkout(root: Path) -> tuple[Path, str]:
    repo_root = Path(
        git_command(
            root,
            ["rev-parse", "--show-toplevel"],
            "plan repository toplevel lookup",
        ).strip()
    ).resolve()
    require(root.parent == repo_root, "authorization plan root must be directly under the git toplevel")
    require_canonical_remote(repo_root, PLAN_REPOSITORY, "authorization checkout")
    branch = git_command(
        repo_root,
        ["symbolic-ref", "--short", "HEAD"],
        "authorization checkout branch lookup",
    ).strip()
    require(branch == "main", "authorization requires the canonical main branch checkout")
    actual_head = git_command(
        repo_root,
        ["rev-parse", "HEAD"],
        "authorization checkout HEAD lookup",
    ).strip()
    authoritative_main = canonical_main_sha(PLAN_REPOSITORY)
    require(
        actual_head == authoritative_main,
        "authorization requires a checkout exactly at canonical GitHub main",
    )
    require_clean_checkout(repo_root, "authorization")
    return repo_root, authoritative_main


def validate(root: Path) -> tuple[int, int]:
    require(root.is_dir(), f"not a directory: {root}")
    actual_files = {path.name for path in root.iterdir() if path.is_file()}
    require(actual_files == REQUIRED_FILES, f"package files differ: missing={sorted(REQUIRED_FILES - actual_files)} extra={sorted(actual_files - REQUIRED_FILES)}")
    plan = load_plan(root / "plan.yaml")
    missing_keys = REQUIRED_KEYS - set(plan)
    require(not missing_keys, f"plan.yaml missing keys: {sorted(missing_keys)}")
    require(plan["slug"] == "fronius-modbus-multivendor-v3-w29-26", "slug mismatch")
    supported_states = {"locked", "implementing", "maintenance"}
    require(plan["state"] in supported_states, "state must be locked, implementing, or maintenance")
    require(root.name == f"{plan['slug']}.{plan['state']}", "directory suffix/state mismatch")
    require(plan["lock_authorized"] is True, "lock_authorized must be true")
    authorization = validate_authorization_schema(plan)
    repo_result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    repo_root = (
        Path(repo_result.stdout.strip())
        if repo_result.returncode == 0
        else Path(__file__).resolve().parent.parent
    )
    require_current_tooling(
        repo_root,
        root,
        authorization["authorization_anchor"]["tooling_binding"],
    )
    require(plan["started_on"] == "2026-07-14", "started_on mismatch")
    if plan["state"] == "locked":
        require(plan["current_milestone"] == "M0", "locked plan current_milestone must be M0")
    elif plan["state"] == "implementing":
        authorized_milestone_numbers = {
            int(re.fullmatch(r"FMV3-M([0-8])-\d{2}", issue_id).group(1))
            for issue_id in plan["execution_authorization"]["authorized_issues"]
        }
        maximum = max(authorized_milestone_numbers)
        current_match = re.fullmatch(r"M([0-8])", str(plan["current_milestone"]))
        require(current_match is not None, "implementing current_milestone must be M0..M8")
        current = int(current_match.group(1))
        require(current <= maximum, f"implementing current_milestone exceeds authorized M{maximum} boundary")
    else:
        require(plan["execution_authorization"]["gateway_work_authorized"] is True, "maintenance is forbidden by the pre-gateway authorization")
        require(plan["current_milestone"] == "M8", "maintenance current_milestone must be M8")
    require(plan["supersedes"] == "fronius-modbus-eebus-bridge-w28-26.draft", "supersedes mismatch")
    require(plan["availability_mode"] == "openai_only", "availability_mode must be openai_only")
    require(plan["repository_mutex"] == {"scope": "per_repository", "owners": ["cruise-topology", "cruise-preflight"], "max_active_issues": 1, "max_active_prs": 1, "validation": "structural_contract_only"}, "repository mutex contract mismatch")
    accepted_rounds = plan["accepted_adversarial_rounds"]
    require(isinstance(accepted_rounds, int) and not isinstance(accepted_rounds, bool) and 0 <= accepted_rounds <= 5, "accepted_adversarial_rounds must be an integer from 0 through 5")
    epoch_policy = plan["review_epoch"]
    require_fields(epoch_policy, {"rounds_per_epoch", "current_epoch", "states", "terminal_condition", "terminal_target", "r5_findings_action", "passed_contract", "finding_id_policy", "history_contract", "epochs"}, "review_epoch")
    require(epoch_policy["rounds_per_epoch"] == 5 and epoch_policy["states"] == ["IN_PROGRESS", "FAILED", "PASSED"] and epoch_policy["terminal_condition"] == "R5_NO_FINDINGS" and epoch_policy["terminal_target"] == "TERMINAL_NO_FINDINGS", "review epoch state/terminal policy mismatch")
    require(epoch_policy["r5_findings_action"] == "CLOSE_FAILED_ARCHIVE_AND_OPEN_NEXT_R1", "review epoch R5 findings action mismatch")
    passed_contract = {"accepted_rounds": 5, "accepted_round_numbers": [1, 2, 3, 4, 5], "r5_reviewer_verdict": "NO_FINDINGS", "r5_integration_state": "NOT_REQUIRED", "r5_finding_ids": [], "current_target": "TERMINAL_NO_FINDINGS", "zero_in_progress_allowed": True, "requires_highest_current_epoch": True, "lock_requires_separate_operator_action": True}
    require(epoch_policy["passed_contract"] == passed_contract, "review PASSED contract mismatch")
    history_contract = epoch_policy["history_contract"]
    require(history_contract == {"maximum_in_progress": 1, "in_progress_required_unless_passed": True, "passed_allows_zero_in_progress": True, "exactly_one_passed_if_terminal": True, "current_is_highest": True, "closed_epochs_immutable": True, "preserve_rounds_and_findings": True}, "review history contract mismatch")
    require(epoch_policy["finding_id_policy"] == {"comparison": "exact_review_table_order", "uniqueness": "global", "no_findings": []}, "review finding-ID policy mismatch")
    epochs = epoch_policy["epochs"]
    require(isinstance(epochs, list) and epochs, "review epochs must be a non-empty list")
    epoch_numbers = [item.get("number") for item in epochs if isinstance(item, dict)]
    require(epoch_numbers == list(range(1, len(epochs) + 1)), "review epochs must be ordered and consecutive")
    all_finding_ids: list[str] = []
    for item in epochs:
        require_fields(item, {"number", "state", "accepted_rounds", "current_target", "rounds"}, f"review epoch {item.get('number')}")
        require(item["state"] in set(epoch_policy["states"]), f"invalid review epoch state: {item['state']}")
        require(isinstance(item["accepted_rounds"], int) and 0 <= item["accepted_rounds"] <= 5, f"invalid accepted rounds for epoch {item['number']}")
        if item["state"] == "FAILED":
            require_fields(item, {"archive", "snapshot", "summary", "evidence"}, f"failed epoch {item['number']}")
            require(item["accepted_rounds"] == 5 and item["current_target"] == "ARCHIVED" and item["archive"] == "IMMUTABLE" and isinstance(item["snapshot"], str) and re.fullmatch(r"[0-9a-f]{64}", item["snapshot"]), f"failed epoch {item['number']} archive mismatch")
            require_nonempty_text(item["summary"], f"failed epoch {item['number']}.summary")
            require(isinstance(item["evidence"], list) and item["evidence"], f"failed epoch {item['number']} needs evidence")
        elif item["state"] == "IN_PROGRESS":
            require(item["accepted_rounds"] < 5 and item["current_target"] == f"R{item['accepted_rounds'] + 1}", f"in-progress epoch {item['number']} target mismatch")
        else:
            require(item["accepted_rounds"] == 5 and item["current_target"] == passed_contract["current_target"], f"passed epoch {item['number']} terminal mismatch")
        rounds = item["rounds"]
        require(isinstance(rounds, list) and [entry.get("number") for entry in rounds if isinstance(entry, dict)] == [1, 2, 3, 4, 5], f"review epoch {item['number']} round metadata mismatch")
        for entry in rounds:
            number = entry["number"]
            require_fields(entry, {"number", "reviewer_verdict", "integration_state", "finding_ids"}, f"review epoch {item['number']} R{number}")
            verdict, integration, finding_ids = entry["reviewer_verdict"], entry["integration_state"], entry["finding_ids"]
            require(isinstance(finding_ids, list) and all(isinstance(value, str) for value in finding_ids), f"review epoch {item['number']} R{number} finding_ids must be a string list")
            if number <= item["accepted_rounds"]:
                require(verdict in {"FINDINGS", "NO_FINDINGS"} and integration == ("CLOSED" if verdict == "FINDINGS" else "NOT_REQUIRED"), f"review epoch {item['number']} R{number} accepted metadata mismatch")
                prefix = f"R{number}" if item["number"] == 1 else f"E{item['number']}-R{number}"
                expected = [f"{prefix}-F{index:02d}" for index in range(1, len(finding_ids) + 1)]
                require(finding_ids == expected and (bool(finding_ids) == (verdict == "FINDINGS")), f"review epoch {item['number']} R{number} finding IDs are omitted, duplicated, or renumbered")
                all_finding_ids.extend(finding_ids)
            else:
                require(item["state"] == "IN_PROGRESS" and verdict == integration == "PENDING" and finding_ids == [], f"review epoch {item['number']} R{number} pending metadata mismatch")
        if item["state"] in {"FAILED", "PASSED"}:
            r5 = rounds[-1]
            expected_r5 = ("FINDINGS", "CLOSED", None) if item["state"] == "FAILED" else ("NO_FINDINGS", "NOT_REQUIRED", [])
            require((r5["reviewer_verdict"], r5["integration_state"], r5["finding_ids"] if item["state"] == "PASSED" else None) == expected_r5, f"review epoch {item['number']} terminal R5 mismatch")
    require(len(all_finding_ids) == len(set(all_finding_ids)), "review finding IDs must be globally unique")
    epoch = epochs[-1]
    require(all(item["state"] == "FAILED" for item in epochs[:-1]) and epoch["state"] in {"IN_PROGRESS", "PASSED"}, "only the highest/current epoch may be in progress or passed")
    in_progress = [item for item in epochs if item["state"] == "IN_PROGRESS"]
    passed = [item for item in epochs if item["state"] == "PASSED"]
    require(len(in_progress) == (1 if epoch["state"] == "IN_PROGRESS" else 0) and len(passed) == (1 if epoch["state"] == "PASSED" else 0), "review terminal/active epoch cardinality mismatch")
    require(epoch_policy["current_epoch"] == epoch["number"], "current review epoch pointer mismatch")
    require(epoch["accepted_rounds"] == accepted_rounds, "current epoch accepted-round mismatch")
    require(plan["canonical_file"] == "00-canonical.md", "canonical_file mismatch")
    require(plan["split_index"] == "01-index.md", "split_index mismatch")
    require(plan["knowledge_repo"] == "Project-Helianthus/helianthus-docs-ebus", "knowledge_repo mismatch")
    require(isinstance(plan["target_repos"], list), "target_repos must be a list")
    require(len(plan["target_repos"]) == len(set(plan["target_repos"])), "duplicate target repo")
    require(set(plan["target_repos"]) == TARGET_REPOS, "target_repos set mismatch")
    require(set(plan["review_scope"]) == REVIEW_SCOPE, "review_scope mismatch")
    decisions = plan["decisions"]
    require(isinstance(decisions, list) and decisions, "decisions must be a non-empty list")
    for index, decision in enumerate(decisions):
        require_fields(decision, {"id", "status", "decision"}, f"decision[{index}]")
        require_nonempty_text(decision["id"], f"decision[{index}].id")
        require(decision["status"] == "accepted", f"decision {decision['id']} status must be accepted")
        require_nonempty_text(decision["decision"], f"decision {decision['id']}.decision")
    decision_ids = [item["id"] for item in decisions]
    require(len(decision_ids) == len(set(decision_ids)), "duplicate decision ID")
    milestones = plan["milestones"]
    require(isinstance(milestones, list), "milestones must be a list")
    milestone_ids = [item.get("id") for item in milestones if isinstance(item, dict)]
    require(len(milestone_ids) == len(milestones), "invalid milestone row")
    require(set(milestone_ids) == {f"M{i}" for i in range(9)}, "milestones must be exactly M0..M8")
    require(len(milestone_ids) == len(set(milestone_ids)), "duplicate milestone ID")
    milestone_deps: dict[str, list[str]] = {}
    for item in milestones:
        require_fields(item, {"id", "title", "depends_on", "exit_gate"}, f"milestone {item['id']}")
        require_nonempty_text(item["title"], f"milestone {item['id']}.title")
        require_nonempty_text(item["exit_gate"], f"milestone {item['id']}.exit_gate")
        milestone_deps[item["id"]] = item["depends_on"]
    validate_dag(set(milestone_ids), milestone_deps, "milestone")
    issues = plan["issues"]
    require(isinstance(issues, list) and issues, "issues must be a non-empty list")
    issue_fields = {"id", "milestone", "repo", "depends_on", "what", "acceptance", "gates", "rollback"}
    issue_ids: list[str] = []
    issue_deps: dict[str, list[str]] = {}
    issues_by_id: dict[str, dict[str, Any]] = {}
    repo_owners: dict[str, str] = {}
    for index, issue in enumerate(issues):
        require_fields(issue, issue_fields, f"issue[{index}]")
        issue_id = issue["id"]
        require(isinstance(issue_id, str) and re.fullmatch(r"FMV3-M[0-8]-\d{2}", issue_id) is not None, f"invalid issue ID: {issue_id}")
        require(issue["milestone"] in milestone_ids, f"issue {issue_id} has unknown milestone")
        require(issue_id.startswith(f"FMV3-{issue['milestone']}-"), f"issue {issue_id} milestone prefix mismatch")
        require(isinstance(issue["repo"], str) and issue["repo"] in TARGET_REPOS, f"issue {issue_id} must have exactly one target repo string")
        require(issue_id not in repo_owners, f"issue {issue_id} has multiple owners")
        repo_owners[issue_id] = issue["repo"]
        require_nonempty_text(issue["what"], f"issue {issue_id}.what")
        require_nonempty_text(issue["acceptance"], f"issue {issue_id}.acceptance")
        require(isinstance(issue["gates"], list) and issue["gates"] and all(isinstance(gate, str) and gate for gate in issue["gates"]), f"issue {issue_id} must have gates")
        require_nonempty_text(issue["rollback"], f"issue {issue_id}.rollback")
        issue_ids.append(issue_id)
        issue_deps[issue_id] = issue["depends_on"]
        issues_by_id[issue_id] = issue
    require(len(issue_ids) == len(set(issue_ids)), "duplicate issue ID")
    require(len(issue_ids) == EXPECTED_ISSUE_COUNT, f"expected {EXPECTED_ISSUE_COUNT} issues")
    validate_dag(set(issue_ids), issue_deps, "issue")
    authorization = plan["execution_authorization"]
    authorized_set = set(authorization["authorized_issues"])
    deferred_set = set(authorization["deferred_issues"])
    require(authorized_set <= set(issue_ids), "execution authorization references unknown issues")
    require(deferred_set <= set(issue_ids), "execution deferral references unknown issues")
    require(not (authorized_set & deferred_set), "authorized and deferred issue sets overlap")
    require(
        {issues_by_id[issue_id]["milestone"] for issue_id in authorized_set} <= {"M0", "M1", "M2", "M3"},
        "authorized issue falls outside the pre-gateway M0-M3 labels",
    )
    require(
        all(issue_id not in authorized_set for issue_id in ("FMV3-M0-04", "FMV3-M0-05", "FMV3-M0-07", "FMV3-M4-01")),
        "private bootstrap or gateway issue entered the execution allowlist",
    )
    authorized_repo_map = {
        "FMV3-M0-01": "Project-Helianthus/.github",
        "FMV3-M0-02": "Project-Helianthus/helianthus-modbus",
        "FMV3-M0-03": "Project-Helianthus/helianthus-modbusreg",
        "FMV3-M0-06": "Project-Helianthus/helianthus-docs-ebus",
        "FMV3-M1-00": "Project-Helianthus/helianthus-docs-ebus",
        "FMV3-M1-01": "Project-Helianthus/helianthus-modbus",
        "FMV3-M1-02": "Project-Helianthus/helianthus-modbus",
        "FMV3-M1-03": "Project-Helianthus/helianthus-modbus",
        "FMV3-M1-04": "Project-Helianthus/helianthus-modbus",
        "FMV3-M1-05": "Project-Helianthus/helianthus-docs-ebus",
        "FMV3-M1-06": "Project-Helianthus/helianthus-modbus",
        "FMV3-M2-01": "Project-Helianthus/helianthus-modbusreg",
        "FMV3-M2-02": "Project-Helianthus/helianthus-modbusreg",
        "FMV3-M2-03": "Project-Helianthus/helianthus-modbusreg",
        "FMV3-M3-01": "Project-Helianthus/helianthus-docs-ebus",
        "FMV3-M3-02": "Project-Helianthus/helianthus-modbusreg",
        "FMV3-M3-03": "Project-Helianthus/helianthus-modbusreg",
    }
    require(set(authorized_repo_map) == authorized_set, "authorized issue/repository map is incomplete")
    require(
        all(issues_by_id[issue_id]["repo"] == repo for issue_id, repo in authorized_repo_map.items()),
        "authorized issue ownership differs from the exact execution map",
    )
    require(
        all(repo != "Project-Helianthus/helianthus-ebusgateway" for repo in authorized_repo_map.values()),
        "gateway-owned issue entered the authorized execution map",
    )
    m0_public = issues_by_id["FMV3-M0-01"]
    require(
        m0_public["acceptance"]
        == "Governance creates empty public helianthus-modbus and helianthus-modbusreg repositories with no Git objects, default branch, bootstrap content, or product code; private governance creation remains deferred to FMV3-M0-04 under future explicit authorization.",
        "M0-01 public create-empty acceptance mismatch",
    )
    contract_rows = [issues_by_id[issue_id] for issue_id in authorization["authorized_issues"]]
    contract_digest = hashlib.sha256(
        json.dumps(contract_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    require(
        authorization["authorized_issue_contract_sha256"] == contract_digest,
        "authorized issue action contract digest mismatch",
    )
    require(set(repo_owners.values()) == TARGET_REPOS, "every target repo must own at least one issue")
    companion = issues_by_id["FMV3-M1-00"]
    require(companion["repo"] == "Project-Helianthus/helianthus-docs-ebus" and companion.get("doc_gate") == "companion" and set(companion.get("companion_for", [])) == COMPANION_IDS, "M1 docs companion metadata mismatch")
    abnormal_results = ["provable_zero", "partial_write", "indeterminate_error", "cancellation_race", "ambiguous_completion"]
    tcp_wait = {"triggers": ["timeout", "cancellation"], "transaction_id_action": "tombstone", "late_response": "drop", "same_socket_reuse": "forbidden_until_normal_tombstone_rollover"}
    rtu_wait = {"triggers": ["timeout", "cancellation"], "action": "quarantine_resynchronize_or_recover_before_successor"}
    tcp_action = ["tombstone_transaction_id", "close_connection_prevent_stream_desync", "reconnect_increment_generation", "reject_old_generation"]
    write_contract = {"boundary": "transport_write_invoked", "abnormal_results": abnormal_results, "no_abandonment_only_if": "provable_zero", "possibly_transmitted": abnormal_results[1:], "full_transmit_success_transition": "response_wait", "tcp_possibly_transmitted_action": tcp_action, "tcp_response_wait_abandonment": tcp_wait, "rtu_possibly_transmitted_action": "quarantine_resynchronize_or_recover_before_successor", "rtu_response_wait_abandonment": rtu_wait}
    require(companion.get("transport_abandonment_docs") == ["write_linearization", "full_transmit_response_wait", "tcp_socket_lifetime_tombstones", "tcp_close_on_possibly_transmitted", "tcp_generation_rollover", "rtu_response_latency_bus_idle_quarantine"] and companion.get("transport_write_linearization") == write_contract, "M1 transport-write docs mismatch")
    coalescing = {"wire_response_id_bound_to": ["physical_request_id", "endpoint", "unit_id", "function_code", "logical_table", "physical_zero_based_pdu_offset", "physical_word_count", "transport_generation_id"], "logical_view_fields": ["logical_view_id", "wire_response_id", "logical_zero_based_pdu_offset", "logical_word_count", "slice_offset_within_wire", "slice_word_count"], "logical_view_per_dependent_observation": "required", "replay": "exact_words_and_provenance", "success_case": "unequal_overlapping_reads", "incompatible_dimensions": ["unit_id", "logical_table", "authorization_scope", "poll_generation_id", "operation_deadline"]}
    require(companion.get("coalescing_identity_contract") == coalescing and issues_by_id["FMV3-M1-02"].get("coalescing_identity_contract") == coalescing, "wire-response/logical-view coalescing contract mismatch")
    require(issues_by_id["FMV3-M2-01"].get("observation_view_fields") == coalescing["logical_view_fields"] and issues_by_id["FMV3-M2-03"].get("coalescing_mutation_matrix") == ["unequal_overlapping_reads_each_logical_view_replays_exact_words_and_provenance", "cross_unit_rejected", "cross_table_rejected", "cross_authorization_rejected", "cross_generation_rejected", "deadline_incompatible_rejected"], "M2 logical-view/mutation contract mismatch")
    for issue_id in COMPANION_IDS:
        issue = issues_by_id[issue_id]
        require(issue.get("doc_gate") == "required" and issue.get("companion_issue") == "FMV3-M1-00", f"{issue_id} docs companion metadata mismatch")
        require("FMV3-M1-00" in ancestors(issue_id, issue_deps), f"{issue_id} lacks docs companion ancestry")
    require(all("FMV3-M1-00" in issues_by_id[issue_id]["depends_on"] for issue_id in M2_IMPLEMENTATION_IDS), "M2 implementation must directly depend on the reused docs companion")
    tcp_contract = {"scope": "per_connection_socket", "allocator_count": "one", "inflight_map_count": "one", "shared_unit_ids": "all", "match_fields": ["active_connection_generation", "transaction_id", "echoed_unit_id", "echoed_function_code", "applicable_response_byte_count"], "request_offset_role": "provenance_only", "response_echoes_request_offset": False, "abandoned_id": "tombstone_for_socket_lifetime", "same_socket_tombstone_reuse": "forbidden", "tombstone_exhaustion": "controlled_close_reconnect", "generation_increment": "before_tombstoned_id_reuse", "old_socket_generation_frames": "reject", "successful_non_abandoned_correlation": "bounded", "full_transmit_success_transition": "response_wait", "response_wait_abandonment": tcp_wait, "unit_profile_state": "isolated", "endpoint_scheduling": "shared", "profile_semantics": "forbidden"}
    require(issues_by_id["FMV3-M1-02"].get("tcp_correlation_contract") == tcp_contract, "FMV3-M1-02 TCP correlation contract mismatch")
    rtu_contract = {"scope": "abnormal_or_response_wait_abandonment", "triggers": abnormal_results[1:], "full_transmit_success_transition": "response_wait", "response_wait_abandonment": ["timeout", "cancellation"], "response_latency": "bounded_endpoint_declared", "bus_idle_resynchronization": "required", "frames_during_quarantine": "discard", "successor_transmit": "after_quarantine_only", "quiescence_failure": "disable_and_recover_endpoint", "late_same_shape_delivery": "forbidden"}
    require(issues_by_id["FMV3-M1-03"].get("rtu_abandonment_contract") == rtu_contract, "FMV3-M1-03 RTU abandonment contract mismatch")
    rtu_physical = {"gate": "RTU_PHYSICAL_QUALIFICATION_V1", "dispositions": ["PHYSICALLY_QUALIFIED", "FIXTURE_ONLY_NO_HARDWARE"], "fixture_only": {"default": "disabled", "enabled_claim": "forbidden", "maturity": "experimental"}, "required_evidence": ["adapter_transceiver_identity", "baud_and_topology", "measured_physical_silent_intervals", "timeout_cancellation_quarantine_trace"], "no_hardware": {"supported_claim": "forbidden", "enabled_claim": "forbidden", "blocks_tcp_fronius": False, "blocks_tcp_sufficient_m1_m7": False}}
    require(companion.get("rtu_physical_qualification_contract") == rtu_physical and issues_by_id["FMV3-M1-03"].get("rtu_physical_qualification_contract") == rtu_physical, "RTU physical qualification/disposition mismatch")
    require(all(issues_by_id[issue_id].get("abnormal_write_results") == abnormal_results for issue_id in ("FMV3-M1-02", "FMV3-M1-03", "FMV3-M1-04")), "M1 deterministic abnormal-result cases mismatch")
    require(issues_by_id["FMV3-M1-02"].get("possibly_transmitted_action") == tcp_action and issues_by_id["FMV3-M1-03"].get("possibly_transmitted_action") == write_contract["rtu_possibly_transmitted_action"] and issues_by_id["FMV3-M1-03"]["depends_on"] == ["FMV3-M1-02"], "transport recovery/serialization mismatch")
    recovery_matrix = ["tcp_provable_zero_no_abandonment", "tcp_partial_write_close_reconnect", "tcp_indeterminate_error_close_reconnect", "tcp_cancellation_race_close_reconnect", "tcp_ambiguous_completion_close_reconnect", "tcp_full_transmit_timeout_tombstone", "tcp_full_transmit_cancellation_tombstone", "tcp_same_socket_tombstone_reuse_rejected", "tcp_tombstone_exhaustion_controlled_rollover", "tcp_old_generation_late_frame_rejected", "rtu_provable_zero_no_abandonment", "rtu_partial_write_quarantine", "rtu_indeterminate_error_quarantine", "rtu_cancellation_race_quarantine", "rtu_ambiguous_completion_quarantine", "rtu_full_transmit_timeout_quarantine", "rtu_full_transmit_cancellation_quarantine", "rtu_late_same_shape_discarded", "rtu_quiescence_failure_endpoint_recovery"]
    require(issues_by_id["FMV3-M1-04"].get("full_transmit_success_transition") == "response_wait" and issues_by_id["FMV3-M1-04"].get("transport_recovery_matrix") == recovery_matrix, "FMV3-M1-04 transport recovery matrix mismatch")
    docs_projection = load_docs_candidate(
        authorization["authorization_anchor"]["docs_candidate_binding"]
    )
    require_docs_r2_semantics(docs_projection)
    source_kind_contract = docs_projection["source_kind"]
    opaque_contract = docs_projection["opaque_capability"]
    attempt_ledger_contract = docs_projection["m2_ledger"]
    normalization_contract = docs_projection["normalization_record"]
    bounded_values_contract = docs_projection["bounded_values"]
    strict_tdd = {
        "red_commit": "test_only",
        "hosted_red": "fails_for_missing_behavior",
        "implementation_before_hosted_red": "forbidden",
        "hosted_green": "required_on_implementation_head",
    }
    fresh_docs_review = {
        "provider": "openai",
        "context": "fresh_independent",
        "reviewed_revision": "exact_docs_head_full_sha",
        "findings": "resolve_all_or_no_findings",
        "merge_blocker": True,
    }
    fresh_code_review = {
        "provider": "openai",
        "context": "fresh_independent",
        "reviewed_revisions": ["red_commit_full_sha", "implementation_head_full_sha"],
        "findings": "resolve_all_or_no_findings",
        "merge_blocker": True,
    }
    opaque_docs = issues_by_id["FMV3-M1-05"]
    opaque_runtime = issues_by_id["FMV3-M1-06"]
    m2_contract = issues_by_id["FMV3-M2-01"]
    require(
        [
            issue_id
            for issue_id in issue_ids
            if issue_id in AMENDMENT_ISSUE_IDS
        ]
        == list(AMENDMENT_ISSUE_IDS),
        "corrective issue sequence mismatch",
    )
    expected_corrective_issue_fields = {
        "FMV3-M1-05": issue_fields | {
            "companion_for", "contract_sections", "doc_gate",
            "documents_contract", "fresh_adversarial_contract",
            "normalization_round_trip_contract",
            "opaque_runtime_acquisition_contract", "source_kind_contract",
            "bounded_values_contract",
        },
        "FMV3-M1-06": issue_fields | {
            "companion_issue", "doc_gate", "fresh_adversarial_contract",
            "implements_contract", "opaque_runtime_acquisition_contract",
            "source_kind_contract", "strict_tdd_contract",
            "bounded_values_contract",
        },
        "FMV3-M2-01": issue_fields | {
            "attempt_ledger_contract", "companion_issue",
            "consumes_contract", "corrective_companion_issue",
            "doc_gate", "fresh_adversarial_contract",
            "normalization_round_trip_contract", "observation_view_fields",
            "producer_pin_contract", "source_trust_contract",
            "strict_tdd_contract", "bounded_values_contract",
        },
    }
    require(
        all(
            set(issues_by_id[issue_id]) == expected_fields
            for issue_id, expected_fields in expected_corrective_issue_fields.items()
        ),
        "corrective issue field projection mismatch",
    )
    require(
        opaque_docs["repo"] == "Project-Helianthus/helianthus-docs-ebus"
        and opaque_docs["depends_on"] == ["FMV3-M1-04"]
        and opaque_docs.get("doc_gate") == "companion"
        and opaque_docs.get("companion_for") == ["FMV3-M1-06", "FMV3-M2-01"]
        and opaque_docs.get("documents_contract") == "OPAQUE_RUNTIME_ACQUISITION_V1"
        and opaque_docs.get("contract_sections") == [
            "opaque_single_use_runtime_acquisition_capability",
            "source_kind_runtime_vs_offline_fixture",
            "source_issued_deliverability",
            "attempt_lifecycle_and_bounds",
            "copied_view_and_endpoint_recreation_cas",
            "per_coalesced_dependent_capability",
            "lossless_normalization",
        ]
        and opaque_docs.get("source_kind_contract") == source_kind_contract
        and opaque_docs.get("opaque_runtime_acquisition_contract") == opaque_contract
        and opaque_docs.get("normalization_round_trip_contract") == normalization_contract
        and opaque_docs.get("bounded_values_contract") == bounded_values_contract
        and opaque_docs.get("fresh_adversarial_contract") == fresh_docs_review
        and opaque_docs["gates"] == [
            "doc_gate", "licensing", "data_integrity", "fresh_adversarial_review"
        ],
        "FMV3-M1-05 opaque acquisition docs contract mismatch",
    )
    require(
        opaque_runtime["repo"] == "Project-Helianthus/helianthus-modbus"
        and opaque_runtime["depends_on"] == ["FMV3-M1-04", "FMV3-M1-05"]
        and opaque_runtime.get("doc_gate") == "required"
        and opaque_runtime.get("companion_issue") == "FMV3-M1-05"
        and opaque_runtime.get("implements_contract") == "OPAQUE_RUNTIME_ACQUISITION_V1"
        and opaque_runtime.get("source_kind_contract") == source_kind_contract
        and opaque_runtime.get("opaque_runtime_acquisition_contract") == opaque_contract
        and opaque_runtime.get("bounded_values_contract") == bounded_values_contract
        and opaque_runtime.get("strict_tdd_contract") == strict_tdd
        and opaque_runtime.get("fresh_adversarial_contract") == fresh_code_review
        and opaque_runtime["gates"] == [
            "TDD_RED", "CI", "doc_gate", "data_integrity",
            "concurrency", "fresh_adversarial_review",
        ],
        "FMV3-M1-06 opaque acquisition implementation contract mismatch",
    )
    require(
        m2_contract["depends_on"] == ["FMV3-M0-03", "FMV3-M1-00", "FMV3-M1-01", "FMV3-M1-06"]
        and m2_contract.get("corrective_companion_issue") == "FMV3-M1-05"
        and m2_contract.get("consumes_contract") == "OPAQUE_RUNTIME_ACQUISITION_V1"
        and m2_contract.get("producer_pin_contract")
        == EXPECTED_M1_06_PRODUCER_PIN_CONTRACT
        and m2_contract.get("source_trust_contract") == source_kind_contract
        and m2_contract.get("attempt_ledger_contract") == attempt_ledger_contract
        and m2_contract.get("normalization_round_trip_contract") == normalization_contract
        and m2_contract.get("bounded_values_contract") == bounded_values_contract
        and m2_contract.get("strict_tdd_contract") == strict_tdd
        and m2_contract.get("fresh_adversarial_contract") == fresh_code_review
        and "FMV3-M1-05" in ancestors("FMV3-M2-01", issue_deps)
        and m2_contract["gates"] == [
            "TDD_RED", "CI", "doc_gate", "data_integrity",
            "concurrency", "fresh_adversarial_review",
        ],
        "FMV3-M2-01 opaque capability consumer contract mismatch",
    )
    profile_companions = {"FMV3-M3-01": ["FMV3-M3-02", "FMV3-M3-03"], "FMV3-M7-01": ["FMV3-M7-02", "FMV3-M7-03", "FMV3-M7-04"], "FMV3-M6-00": ["FMV3-M6-01"], "FMV3-M8-00": ["FMV3-M8-01"]}
    for docs_id, consumers in profile_companions.items():
        require(issues_by_id[docs_id].get("doc_gate") == "companion" and issues_by_id[docs_id].get("companion_for") == consumers, f"{docs_id} companion metadata mismatch")
        for consumer_id in consumers:
            consumer = issues_by_id[consumer_id]
            require(consumer.get("doc_gate") == "required" and consumer.get("companion_issue") == docs_id and docs_id in ancestors(consumer_id, issue_deps), f"{consumer_id} companion metadata/ancestry mismatch")
    m3_disposition = issues_by_id["FMV3-M3-03"]
    require(m3_disposition.get("tdd_condition") == "OVERLAY_REQUIRED" and m3_disposition.get("standard_only_contract") == {"evidence_and_disposition": "public", "conformance_ci": "green", "implementation_commit": "forbidden", "empty_overlay": "forbidden"} and "TDD_RED_IF_OVERLAY_REQUIRED" in m3_disposition["gates"] and "TDD_RED" not in m3_disposition["gates"], "FMV3-M3-03 conditional overlay TDD mismatch")
    m7_disposition = issues_by_id["FMV3-M7-03"]
    growatt_sections = ["complete_candidate_contract", "complete_admission_contract", "qualified_candidate_facts", "admission_criteria", "provenance", "licensing", "unsupported_disposition", "exact_code_doc_mapping"]
    require(issues_by_id["FMV3-M7-01"].get("growatt_contract_sections") == growatt_sections and issues_by_id["FMV3-M7-01"].get("growatt_contract_completion") == "published_and_merged_before_close", "FMV3-M7-01 Growatt contract mismatch")
    require(set(m7_disposition) == issue_fields | {"doc_gate", "companion_issue", "tdd_condition", "profile_admitted_contract", "no_admissible_profile_contract", "disposition_contract"} and m7_disposition.get("tdd_condition") == "PROFILE_ADMITTED" and m7_disposition.get("profile_admitted_contract") == {"red_first_fixtures_and_code": "required", "later_companion_docs_change": "forbidden"} and m7_disposition.get("no_admissible_profile_contract") == {"prepublished_public_evidence_and_unsupported_disposition": "preserved", "implementation_commit": "forbidden", "catalog_entry": "forbidden", "support_claim": "forbidden", "later_companion_docs_change": "forbidden"} and set(m7_disposition["gates"]) == {"CI", "licensing", "protocol_interop", "hardware_conditional", "doc_gate", "TDD_RED_IF_PROFILE_ADMITTED"}, "FMV3-M7-03 prepublished profile gates mismatch")
    modbusreg_order = ["FMV3-M3-02", "FMV3-M3-03", "FMV3-M7-02", "FMV3-M7-03", "FMV3-M7-04", "FMV3-M7-05"]
    require("FMV3-M5-09" in issues_by_id["FMV3-M7-01"]["depends_on"] and "FMV3-M7-01" in issues_by_id["FMV3-M7-02"]["depends_on"] and all(first in ancestors(second, issue_deps) for first, second in zip(modbusreg_order, modbusreg_order[1:])), "critical docs or modbusreg serialization mismatch")
    emma_negative = {"inputs": ["emma_endpoint", "insufficiently_distinguished_endpoint"], "allowed_outcomes": ["no_match", "insufficient_evidence"], "forbidden_activation": ["huawei_smartlogger", "huawei_s_dongle"], "automatic_eligibility_without_reliable_discrimination": "blocked"}
    huawei_sections = ["register_map", "codec", "gateway_applicability", "branch_applicability", "version_applicability", "detection", "provenance", "licensing", "exact_code_doc_mapping"]
    huawei_admission = {"per_candidate_disposition": ["PROFILE_ADMITTED", "NO_ADMISSIBLE_PROFILE"], "admitted_requires": ["published_packet", "red_first_fixtures_and_code", "positive_gateway_branch_version_detection_codec_fixtures"], "non_admitted_forbids": ["implementation_commit", "catalog_entry", "support_claim"]}
    runtime_ops = ["fc03_read_holding_registers", "fc04_read_input_registers", "fc2b_mei0e_read_device_identification"]
    require(all(issues_by_id[i].get("phase1_read_only_operations") == runtime_ops for i in ("FMV3-M1-00", "FMV3-M1-01")) and issues_by_id["FMV3-M1-04"].get("identity_operation_matrix") == ["tcp_fc2b_mei0e_device_identification", "rtu_fc2b_mei0e_device_identification"] and issues_by_id["FMV3-M7-01"].get("detector_runtime_operation_contract") == {"enumeration": "per_candidate", "required_runtime_allowlist": runtime_ops, "unsupported_operation_disposition": "NO_ADMISSIBLE_PROFILE", "modbusreg_protocol_framing": "forbidden"} and issues_by_id["FMV3-M7-01"].get("emma_discriminator_inventory") == {"required": ["gateway", "model", "software", "version"], "unavailable_disposition": "mark_each_unavailable", "semantics": "deferred"} and issues_by_id["FMV3-M7-01"].get("huawei_candidate_contract_sections") == huawei_sections and issues_by_id["FMV3-M7-01"].get("huawei_candidate_dispositions") == ["PROFILE_ADMITTED", "NO_ADMISSIBLE_PROFILE"] and issues_by_id["FMV3-M7-01"].get("huawei_contract_completion") == "published_and_merged_before_close" and issues_by_id["FMV3-M7-04"].get("huawei_admission_contract") == huawei_admission and "TDD_RED_IF_PROFILE_ADMITTED" in issues_by_id["FMV3-M7-04"]["gates"] and "TDD_RED" not in issues_by_id["FMV3-M7-04"]["gates"] and all(issues_by_id[i].get("emma_negative_fixture_contract") == emma_negative for i in ("FMV3-M7-04", "FMV3-M7-05")), "Runtime-owned detector operations, Huawei admission, or EMMA discrimination mismatch")
    base_outcome = {"allowed": ["GO", "NO_GO", "STOP"], "progress": "GO", "completion_is_progress": False}
    for issue_id in ("FMV3-M4-04", "FMV3-M5-03"):
        require(issues_by_id[issue_id].get("outcome_contract") == base_outcome, f"{issue_id} outcome contract mismatch")
    myvaillant = issues_by_id["FMV3-M6-02"]
    go_evidence = {"minimum_locked_pv_capabilities": 1, "live_fronius_endpoint": {"enabled_during_run": "required", "qualification": "qualified", "availability_during_run": "required"}, "traced_observation": {"availability": "available", "freshness": "non_stale", "generated_after": "recorded_lab_run_start"}, "disallowed_inputs": ["replayed", "synthetic", "retained_cache_only", "fixture_only", "simulator_only"], "capability_value_result": "accepted_and_exposed", "myvaillant_side_observable": "required", "path": ["PUBLIC_GRAPHQL_M2M_V1", "eebus", "myvaillant"], "traversal_requirement": "same_observation_identity_and_value", "matching_fields": ["canonical_identity", "source_identity", "value", "unit", "value_semantics", "quality", "source_observation_timestamp", "receipt_timestamp"], "public_schema_field_change": "none_use_existing_identity_time_quality_contract", "handshake_or_packet_observation_only": "insufficient"}
    require(myvaillant.get("outcome_contract") == {**base_outcome, "success": "GO"} and myvaillant.get("go_evidence_contract") == go_evidence and issues_by_id["FMV3-M6-03"].get("packages_outcome_of") == "FMV3-M6-02" and issues_by_id["FMV3-M6-03"].get("publication_contract") == {"publishable_result": "sanitized_public_artifact", "unpublishable_result": "STOP", "private_only_success_claim": "forbidden"}, "FMV3-M6-02 GO/publication contract mismatch")
    require(issues_by_id["FMV3-M4-05"].get("packages_outcome_of") == "FMV3-M4-04", "M4 evidence issue must package the M4 gate outcome")
    disposition_contracts = {"FMV3-M3-03": ["STANDARD_ONLY", "OVERLAY_REQUIRED"], "FMV3-M7-03": ["PROFILE_ADMITTED", "NO_ADMISSIBLE_PROFILE"]}
    for issue_id, allowed in disposition_contracts.items():
        require(issues_by_id[issue_id].get("disposition_contract") == {"allowed": allowed, "completion_is_progress": True}, f"{issue_id} disposition contract mismatch")
        require("outcome_contract" not in issues_by_id[issue_id], f"{issue_id} disposition must not become a conditional GO gate")
    require({"FMV3-M3-01", "FMV3-M3-02"} <= ancestors("FMV3-M3-03", issue_deps) and "FMV3-M3-03" in ancestors("FMV3-M4-01", issue_deps), "Fronius disposition lacks ancestry or M4 release")
    require(issues_by_id["FMV3-M5-01"]["depends_on"] == ["FMV3-M5-02"] and set(issues_by_id["FMV3-M5-04"]["depends_on"]) == {"FMV3-M5-01", "FMV3-M5-02"} and issues_by_id["FMV3-M5-03"]["depends_on"] == ["FMV3-M5-04"], "M5 candidate semantic implementation/lock ordering mismatch")
    graphql_docs = issues_by_id["FMV3-M5-09"]
    contract_id = issues_by_id["FMV3-M5-05"].get("publishes_contract")
    require(contract_id == "PUBLIC_GRAPHQL_M2M_V1" and graphql_docs.get("documents_contract") == contract_id and issues_by_id["FMV3-M5-08"].get("packages_contract") == contract_id and all(issues_by_id[i].get("consumes_contract") == contract_id for i in ("FMV3-M6-01", "FMV3-M8-01")), "public GraphQL identity mismatch")
    channel_contract = {"scope": "credential_bearing_external", "authentication": "required", "confidentiality": "required", "server_identity": "verified", "plaintext_external": "reject", "untrusted_server_identity": "reject", "mechanism": "unspecified", "raw_registers_in_graphql": "forbidden"}
    require(graphql_docs.get("external_channel_contract") == channel_contract and issues_by_id["FMV3-M5-05"].get("external_channel_contract") == channel_contract and all(issues_by_id[issue_id].get("tests_external_channel") == contract_id for issue_id in ("FMV3-M5-08", "FMV3-M6-01")), "external GraphQL channel mismatch")
    require(graphql_docs["repo"] == "Project-Helianthus/helianthus-docs-ebus" and graphql_docs["depends_on"] == ["FMV3-M5-03"] and graphql_docs.get("doc_gate") == "companion" and graphql_docs.get("companion_for") == ["FMV3-M5-05"] and graphql_docs.get("contract_sections") == ["schema_projection", "external_access_security_channel", "compatibility_versioning", "credential_lifecycle", "recovery"] and graphql_docs.get("semantic_lock_ancestor") == "FMV3-M5-03", "FMV3-M5-09 docs mismatch")
    require(issues_by_id["FMV3-M5-05"]["depends_on"] == ["FMV3-M5-09"] and issues_by_id["FMV3-M5-05"].get("doc_gate") == "required" and issues_by_id["FMV3-M5-05"].get("companion_issue") == "FMV3-M5-09", "FMV3-M5-05 docs mismatch")
    require("FMV3-M5-02" in ancestors("FMV3-M5-09", issue_deps) and "FMV3-M5-03" in ancestors("FMV3-M5-09", issue_deps) and sum(issue.get("documents_contract") == contract_id for issue in issues) == 1, "GraphQL docs ancestry mismatch")
    require("FMV3-M5-05" in ancestors("FMV3-M5-08", issue_deps) and all("FMV3-M5-08" in ancestors(i, issue_deps) for i in ("FMV3-M6-01", "FMV3-M8-01")) and "FMV3-M6-02" in ancestors("FMV3-M6-03", issue_deps), "GraphQL/private-doc rollout ancestry mismatch")
    private_ingress = {"access_mechanism": "authenticated_bounded_query_polling", "version_compatibility": "reject_incompatible_contract_versions", "authentication": "noninteractive_least_privilege", "confidential_channel": "required", "server_identity": "verified", "credential_lifecycle_recovery": ["provision", "rotate", "revoke", "disable", "recover"], "ingress_recovery": ["bounded_reconnect_backoff", "explicit_disable", "stale_unavailable_propagation"], "forbidden_ingress_sources": ["helianthus-modbus", "helianthus-modbusreg", "gateway_internals", "undocumented_network_paths"], "tests_external_channel": contract_id}
    require(all(all(issues_by_id[i].get(k) == v for k, v in private_ingress.items()) for i in ("FMV3-M6-01", "FMV3-M8-01")) and sum("consumes_contract" in issue for issue in issues if issue["milestone"] == "M8") == 1 and "FMV3-M5-08" in ancestors("FMV3-M8-01", issue_deps) and "security" in issues_by_id["FMV3-M8-01"]["gates"], "Matter must have exactly one packaged, secured public ingress matching eeBUS")
    require(issues_by_id["FMV3-M7-04"]["depends_on"] == ["FMV3-M7-03"], "Growatt disposition must release Huawei")
    gates = plan["phase_gates"]
    require(isinstance(gates, list) and gates, "phase_gates must be a non-empty list")
    gate_ids: list[str] = []
    for index, gate in enumerate(gates):
        require_fields(gate, {"id", "kind", "after_issues", "before_issues", "requirement"},
                       f"phase_gate[{index}]")
        gate_ids.append(gate["id"])
        require(gate["kind"] in {"dependency", "conditional", "policy"},
                f"invalid phase gate kind: {gate['id']}")
        require_nonempty_text(gate["requirement"], f"phase gate {gate['id']}.requirement")
        after = gate["after_issues"]
        before = gate["before_issues"]
        require(isinstance(after, list) and isinstance(before, list), f"phase gate {gate['id']} issue refs must be lists")
        require(not ((set(after) | set(before)) - set(issue_ids)), f"phase gate {gate['id']} has unknown issue refs")
        if gate["kind"] == "policy":
            require(not after and not before, f"policy gate {gate['id']} must not encode fake dependencies")
        else:
            require(after and before, f"ordered gate {gate['id']} needs after and before issues")
            for later in before:
                missing = set(after) - ancestors(later, issue_deps)
                require(not missing, f"phase gate {gate['id']} is not enforced before {later}: {sorted(missing)}")
            if gate["kind"] == "conditional":
                require(gate.get("conditional_gate") in CONDITIONAL_GATE_IDS,
                        f"phase gate {gate['id']} lacks conditional-gate reference")
    require(len(gate_ids) == len(set(gate_ids)), "duplicate phase gate ID")
    require(set(gate_ids) == REQUIRED_PHASE_GATES, "phase gate set mismatch")
    validate_corrective_phase_gates(gates)
    conditional_gates = plan["conditional_gates"]
    require(isinstance(conditional_gates, list), "conditional_gates must be a list")
    conditional_ids = [item.get("id") for item in conditional_gates if isinstance(item, dict)]
    require(set(conditional_ids) == CONDITIONAL_GATE_IDS and len(conditional_ids) == len(CONDITIONAL_GATE_IDS),
            "conditional gate set mismatch")
    semantic_go = next(item for item in conditional_gates if item["id"] == "CG-M5-SEMANTIC-GO")
    require("FMV3-M5-04" in ancestors("FMV3-M5-03", issue_deps) and "FMV3-M5-03" in ancestors("FMV3-M5-09", issue_deps) and "FMV3-M5-04" not in semantic_go["before_issues"], "semantic MCP/lock/GraphQL ordering mismatch")
    conditional_fields = {"id", "gate_issue", "allowed_outcomes", "progress_outcome",
                          "non_progress_outcomes", "issue_completion_satisfies_gate",
                          "required_completion_issues", "before_issues", "requirement"}
    for item in conditional_gates:
        require_fields(item, conditional_fields, f"conditional gate {item.get('id')}")
        require(item["allowed_outcomes"] == ["GO", "NO_GO", "STOP"] and
                item["progress_outcome"] == "GO" and item["non_progress_outcomes"] == ["NO_GO", "STOP"],
                f"conditional gate {item['id']} outcome vocabulary mismatch")
        require(item["issue_completion_satisfies_gate"] is False,
                f"conditional gate {item['id']} must reject completion as success")
        refs = [item["gate_issue"], *item["required_completion_issues"], *item["before_issues"]]
        require(all(ref in issues_by_id for ref in refs), f"conditional gate {item['id']} has unknown issue ref")
        for later in item["before_issues"]:
            required = {item["gate_issue"], *item["required_completion_issues"]}
            require(required <= ancestors(later, issue_deps),
                    f"conditional gate {item['id']} lacks structural ancestry before {later}")
        require_nonempty_text(item["requirement"], f"conditional gate {item['id']}.requirement")
    phase_conditionals = {gate.get("conditional_gate") for gate in gates if gate["kind"] == "conditional"}
    require(phase_conditionals == CONDITIONAL_GATE_IDS, "conditional phase-gate references mismatch")
    risks = plan["risks"]
    require(isinstance(risks, list) and risks, "risks must be a non-empty list")
    risk_ids: list[str] = []
    for index, risk in enumerate(risks):
        require_fields(risk, {"id", "statement", "mitigation", "stop_trigger"}, f"risk[{index}]")
        for field in ("id", "statement", "mitigation", "stop_trigger"):
            require_nonempty_text(risk[field], f"risk[{index}].{field}")
        risk_ids.append(risk["id"])
    require(len(risk_ids) == len(set(risk_ids)), "duplicate risk ID")
    issue_map_text = (root / "90-issue-map.md").read_text(encoding="utf-8")
    issue_rows = parse_issue_map(issue_map_text)
    require(set(issue_rows) == set(issue_ids), "issue-map IDs do not mirror plan.yaml")
    for issue_id, row in issue_rows.items():
        issue = issues_by_id[issue_id]
        require(row[1] == issue["milestone"], f"issue-map milestone mismatch: {issue_id}")
        require(row[2] == issue["repo"], f"issue-map repo mismatch: {issue_id}")
        mapped_deps = [] if row[3] == "-" else [item.strip() for item in row[3].split(",")]
        require(mapped_deps == issue["depends_on"], f"issue-map dependency mismatch: {issue_id}")
        require(row[4] == issue["what"], f"issue-map action mismatch: {issue_id}")
        require(row[5] == issue["acceptance"], f"issue-map acceptance mismatch: {issue_id}")
        require(row[6] == render_issue_map_gates(issue), f"issue-map gates mismatch: {issue_id}")
        require(row[7] == issue["rollback"], f"issue-map rollback mismatch: {issue_id}")
    require(all(gate_id in issue_map_text for gate_id in CONDITIONAL_GATE_IDS),
            "issue map missing conditional gate mirror")
    for issue_id in COMPANION_IDS:
        require("FMV3-M1-00" in issue_rows[issue_id][6], f"issue map companion metadata missing: {issue_id}")
    for docs_id, consumers in profile_companions.items():
        require(all(docs_id in issue_rows[consumer_id][6] for consumer_id in consumers), f"issue map {docs_id} companion mirror missing")
    require("FMV3-M5-09" in issue_rows["FMV3-M5-05"][6], "issue map GraphQL companion metadata missing")
    milestone_map = (root / "91-milestone-map.md").read_text(encoding="utf-8")
    require(all(gate_id in milestone_map for gate_id in CONDITIONAL_GATE_IDS),
            "milestone map missing conditional gate mirror")
    require(
        "FMV3-M5-09" in milestone_map
        and "FMV3-M1-05" in milestone_map
        and "FMV3-M1-06" in milestone_map
        and "PG-OPAQUE-ACQUISITION-DOC-GATE" in milestone_map
        and "PG-OPAQUE-ACQUISITION-CONSUMER-PIN" in milestone_map
        and "46 issues" in issue_map_text
        and "repository mutex" in issue_map_text,
            "issue/milestone maps missing docs, mutex, or issue-count mirror")
    require(
        "corrective companion FMV3-M1-05" in issue_rows["FMV3-M2-01"][6],
        "issue map corrective companion metadata missing: FMV3-M2-01",
    )
    for chunk_name in CHUNKS:
        text = (root / chunk_name).read_text(encoding="utf-8")
        for heading in ("Depends on:", "Scope:", "Idempotence contract:",
                        "Falsifiability gate:", "Coverage:"):
            require(heading in text, f"{chunk_name} missing {heading}")
        for claim in ("**Proven**", "**Hypothesis**", "**Unknown**"):
            require(claim in text, f"{chunk_name} missing claim class {claim}")
    review = (root / "92-adversarial-review.md").read_text(encoding="utf-8")
    epoch_matches = list(re.finditer(r"^## Epoch ([1-9]\d*)\s*$", review, re.MULTILINE))
    require([int(match.group(1)) for match in epoch_matches] == epoch_numbers, "review epoch sections do not mirror plan.yaml")
    for epoch_index, epoch_match in enumerate(epoch_matches):
        end = epoch_matches[epoch_index + 1].start() if epoch_index + 1 < len(epoch_matches) else len(review)
        epoch_section = review[epoch_match.end():end]
        epoch_item = epochs[epoch_index]
        metadata = [re.search(pattern, epoch_section, re.MULTILINE) for pattern in
                    (r"^State: (IN_PROGRESS|FAILED|PASSED)[ \t]*$", r"^Accepted rounds: (\d+)[ \t]*$",
                     r"^Current target: (R[1-5]|ARCHIVED|TERMINAL_NO_FINDINGS)[ \t]*$", r"^Archive: (ACTIVE|IMMUTABLE|TERMINAL)[ \t]*$")]
        archive_snapshot = re.search(r"^Archive snapshot: `([0-9a-f]{64})`[ \t]*$", epoch_section, re.MULTILINE)
        require(all(metadata), f"epoch {epoch_item['number']} review metadata missing")
        expected_archive = {"FAILED": "IMMUTABLE", "IN_PROGRESS": "ACTIVE", "PASSED": "TERMINAL"}[epoch_item["state"]]
        require([metadata[0].group(1), int(metadata[1].group(1)), metadata[2].group(1), metadata[3].group(1)] ==
                [epoch_item["state"], epoch_item["accepted_rounds"], epoch_item["current_target"], expected_archive],
                f"epoch {epoch_item['number']} review metadata mismatch")
        if epoch_item["state"] == "FAILED":
            require(archive_snapshot is not None and archive_snapshot.group(1) == epoch_item["snapshot"] and
                    re.search(r"^Summary: .+", epoch_section, re.MULTILINE) is not None and
                    re.search(r"^Evidence: .+", epoch_section, re.MULTILINE) is not None, f"failed epoch {epoch_item['number']} archive mismatch")
        round_matches = list(re.finditer(r"^### R([1-5])\s*$", epoch_section, re.MULTILINE))
        require([int(match.group(1)) for match in round_matches] == [1, 2, 3, 4, 5], f"epoch {epoch_item['number']} must contain R1..R5")
        for round_index, round_match in enumerate(round_matches):
            round_end = round_matches[round_index + 1].start() if round_index < 4 else len(epoch_section)
            section = epoch_section[round_match.end():round_end]
            round_number = round_index + 1
            round_meta = epoch_item["rounds"][round_index]
            expected_state = "ACCEPTED" if round_number <= epoch_item["accepted_rounds"] else "PENDING"
            state = re.search(r"^State: (ACCEPTED|PENDING)[ \t]*$", section, re.MULTILINE)
            verdict = re.search(r"^Reviewer verdict: (FINDINGS|NO_FINDINGS|PENDING)[ \t]*$", section, re.MULTILINE)
            integration = re.search(r"^Integration: (CLOSED|NOT_REQUIRED|PENDING)[ \t]*$", section, re.MULTILINE)
            snapshot = re.search(r"^Snapshot: `([0-9a-f]{64})`[ \t]*$", section, re.MULTILINE)
            rows = re.findall(r"^\| ([A-Z0-9-]+) \| ([A-Z_]+) \|", section, re.MULTILINE)
            require(state and verdict and integration and state.group(1) == expected_state and
                    verdict.group(1) == round_meta["reviewer_verdict"] and integration.group(1) == round_meta["integration_state"] and
                    [row[0] for row in rows] == round_meta["finding_ids"], f"epoch {epoch_item['number']} R{round_number} review-row mismatch")
            accepted = expected_state == "ACCEPTED"
            require((accepted and snapshot is not None and all(row[1] == "CLOSED" for row in rows)) or
                    (not accepted and snapshot is None and not rows), f"epoch {epoch_item['number']} R{round_number} closure mismatch")
            if round_number == 5 and accepted:
                required_verdict = "FINDINGS" if epoch_item["state"] == "FAILED" else "NO_FINDINGS"
                require(verdict.group(1) == required_verdict, f"epoch {epoch_item['number']} R5 verdict mismatch")
    review_target = epoch["current_target"]
    require(epoch["rounds"][0].get("snapshot") == "d0e23922b27030b241688dec85d5e79f28de4d6730e6964511e71b6ff10b1c36", "epoch 3 R1 reviewed snapshot mismatch")
    require(f"Current epoch: `{epoch['number']}`" in review and f"Review state: `{epoch['state']}`" in review and f"Accepted rounds: `{accepted_rounds}`" in review and
            f"Current target: `{review_target}`" in review and all((int(a), b) == (accepted_rounds, review_target) for a, b in re.findall(r"at `(\d)/5`, targeting (R[1-5])", review)), "current review epoch mirror mismatch")
    require("archived intact" in review and "next numbered epoch at R1" in review and "there is no R6" in review and "TERMINAL_NO_FINDINGS" in review,
            "review epoch history/restart contract missing")
    require(
        "Issue #90 capability/ledger reconciliation gate" in review
        and "FMV3-M1-05" in review
        and "FMV3-M1-06" in review
        and "FMV3-M2-01" in review
        and re.search(r"does not\s+retroactively place the amendment inside epoch 3 R5", review) is not None,
        "issue #90 fresh adversarial amendment gate mirror missing",
    )
    for category in REVIEW_SCOPE:
        require(category in review, f"review contract missing category: {category}")
    canonical_bytes = (root / "00-canonical.md").read_bytes()
    canonical_text = canonical_bytes.decode("utf-8")
    require_unique_metadata(canonical_text, "State", f"`{plan['state']}`", "canonical")
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    require(plan["canonical_sha256"] == digest, "plan.yaml canonical_sha256 mismatch")
    for mirror_name in ("01-index.md", "99-status.md"):
        mirror = (root / mirror_name).read_text(encoding="utf-8")
        require(f"Canonical-SHA256: `{digest}`" in mirror, f"{mirror_name} canonical hash mirror mismatch")
    status = (root / "99-status.md").read_text(encoding="utf-8")
    require(
        status.startswith(f"# {plan['state'].capitalize()} status\n"),
        "status heading/state mirror mismatch",
    )
    status_fields = {
        "State": str(plan["state"]),
        "Current milestone": str(plan["current_milestone"]),
        "Review epoch": str(epoch["number"]),
        "Review state": str(epoch["state"]),
        "Accepted adversarial rounds": f"{accepted_rounds}/5",
        "Review target": str(review_target),
        "Lock authorized": "yes, for plan publication only",
        "Implementation authorized": "yes, for the pre-gateway M0-M3 issue allowlist only",
        "Authorization scope authority": "exact authorized_issues allowlist; milestone labels are non-authoritative",
        "Authorization anchor": "PR #91 exact squash merge plus external review attestation required; PR #89 is predecessor provenance only; issue #90 is tracking only",
        "Canonical main authority": "fixed GitHub API for Project-Helianthus/helianthus-execution-plans; origin is identity-only",
        "External review attestation": "one unique unedited authorized-issuer tag binding exact live PR #91 head/tree, NO_FINDINGS, and at least two fresh OpenAI reviewer run IDs",
        "Docs R2 rebind": "complete; exact docs PR #386 head/tree and expanded bounded_values projection bound",
        "Repository creation authorized": "yes, through FMV3-M0-01",
        "Private repository action": "deferred; creation requires future explicit authorization",
        "Commit/push authorized": "yes, for the plan package and authorized pre-gateway issues only",
        "Gateway work authorized": "no; stop before FMV3-M4-01",
        "Private creation/bootstrap authorized": "no; FMV3-M0-04, FMV3-M0-05, and FMV3-M0-07 deferred",
    }
    for key, expected in status_fields.items():
        require_unique_metadata(status, key, expected, "status")
    surface_texts = load_amendment_surface_texts(root)
    derived_surface_digest = amendment_surface_digest(plan, surface_texts)
    require(
        plan["execution_authorization"]["authorization_anchor"][
            "amendment_surfaces_sha256"
        ]
        == derived_surface_digest,
        "current amendment surface digest mismatch",
    )
    validate_content_hygiene(root)
    return len(issues), len(milestones)
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path)
    parser.add_argument("--authorize-issue")
    parser.add_argument("--plan-head-sha")
    parser.add_argument("--authorization-contract-sha256")
    parser.add_argument("--authorization-evidence")
    parser.add_argument("--materialized-anchor-validator", action="store_true")
    parser.add_argument("--print-amendment-surfaces-sha256", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve() if args.root is not None else Path(__file__).resolve().parent
    try:
        if args.authorize_issue is not None and not args.materialized_anchor_validator:
            return materialize_and_reexec_anchor_validator(root, args)
        if args.materialized_anchor_validator:
            require(
                args.authorize_issue is not None,
                "--materialized-anchor-validator is internal to issue authorization",
            )
            require_materialized_validator_context()
        if args.print_amendment_surfaces_sha256:
            plan = load_plan(root / "plan.yaml")
            print(amendment_surface_digest(plan, load_amendment_surface_texts(root)))
            return 0
        authorization_repo_root: Path | None = None
        authoritative_main: str | None = None
        if args.authorize_issue is not None:
            authorization_repo_root, authoritative_main = prepare_plan_authorization_checkout(
                root
            )
        issue_count, milestone_count = validate(root)
        if args.authorize_issue is not None:
            plan = load_plan(root / "plan.yaml")
            authorization = plan["execution_authorization"]
            require(
                args.plan_head_sha is not None and re.fullmatch(r"[0-9a-f]{40}", args.plan_head_sha) is not None,
                "--plan-head-sha with a full lowercase 40-character SHA is mandatory",
            )
            require(
                authorization_repo_root is not None and authoritative_main is not None,
                "authorization checkout context is absent",
            )
            anchor_is_merged = subprocess.run(
                [
                    "git",
                    "-C",
                    str(authorization_repo_root),
                    "merge-base",
                    "--is-ancestor",
                    args.plan_head_sha,
                    authoritative_main,
                ],
                check=False,
            ).returncode == 0
            require(
                anchor_is_merged,
                "authorization anchor is not reachable from authoritative canonical main",
            )
            repo_root = authorization_repo_root
            require(
                args.authorization_contract_sha256 == authorization["authorized_issue_contract_sha256"],
                "authorization contract digest does not match the plan",
            )
            anchor_relpath = authorization["authorization_anchor"]["plan_path"]
            require(
                isinstance(anchor_relpath, str)
                and not Path(anchor_relpath).is_absolute()
                and ".." not in Path(anchor_relpath).parts
                and Path(anchor_relpath).name == "plan.yaml",
                "authorization anchor plan_path must be a safe repository-relative plan.yaml path",
            )
            anchored_plan_result = subprocess.run(
                ["git", "-C", str(root), "show", f"{args.plan_head_sha}:{anchor_relpath}"],
                check=False,
                capture_output=True,
                text=True,
            )
            require(
                anchored_plan_result.returncode == 0,
                "authorization anchor plan_path is absent from the merged anchor",
            )
            anchored_plan_text = anchored_plan_result.stdout
            anchored_plan = yaml.load(anchored_plan_text, Loader=UniqueLoader)
            require(isinstance(anchored_plan, dict), "anchored plan.yaml must be a mapping")
            anchored_phase_gates = anchored_plan.get("phase_gates")
            require(
                isinstance(anchored_phase_gates, list),
                "anchored phase_gates must be a list",
            )
            validate_corrective_phase_gates(anchored_phase_gates)
            anchored_authorization = anchored_plan.get("execution_authorization", {})
            require(
                isinstance(anchored_authorization, dict),
                "anchored execution authorization must be a mapping",
            )
            anchored_anchor = anchored_authorization.get("authorization_anchor")
            require(
                isinstance(anchored_anchor, dict),
                "authorization record is absent from the merged PR #91 anchor",
            )
            anchored_tooling = anchored_anchor.get("tooling_binding")
            require(
                isinstance(anchored_tooling, dict)
                and anchored_tooling == authorization["authorization_anchor"]["tooling_binding"],
                "current tooling binding differs from merged PR #91 anchor",
            )
            for path_key, hash_key in (
                ("validator_path", "validator_sha256"),
                ("workflow_path", "workflow_sha256"),
            ):
                relative = safe_repository_path(anchored_tooling[path_key], path_key)
                anchored_blob = subprocess.run(
                    ["git", "-C", str(repo_root), "show", f"{args.plan_head_sha}:{relative.as_posix()}"],
                    check=False,
                    capture_output=True,
                )
                require(
                    anchored_blob.returncode == 0,
                    f"anchored tooling blob is absent: {path_key}",
                )
                require(
                    hashlib.sha256(anchored_blob.stdout).hexdigest()
                    == anchored_tooling[hash_key],
                    f"anchored {path_key} blob SHA-256 mismatch",
                )
                current_blob_path = current_tooling_path(
                    repo_root, root, path_key, relative
                )
                require(
                    current_blob_path.read_bytes() == anchored_blob.stdout,
                    f"current {path_key} blob differs from merged PR #91 anchor",
                )
                if path_key == "validator_path":
                    require(
                        Path(__file__).resolve().read_bytes() == anchored_blob.stdout,
                        "preflight is not executing the validator materialized from PR #91 anchor",
                    )
            require(
                anchored_authorization.get("authorized_issue_contract_sha256")
                == args.authorization_contract_sha256,
                "authorization contract digest is absent from the merged anchor",
            )
            require(
                args.authorize_issue in anchored_authorization.get("authorized_issues", []),
                "issue is absent from the merged authorization anchor",
            )
            require(
                args.authorize_issue in authorization["authorized_issues"],
                f"issue {args.authorize_issue} is outside the fail-closed execution allowlist",
            )
            require(
                args.authorize_issue != authorization["stop_before_issue"],
                f"issue {args.authorize_issue} reaches the hard stop",
            )
            require_authorization_pr_merged(
                anchored_anchor,
                args.plan_head_sha,
            )
            require_issue_authorization_dependencies(
                args.authorize_issue,
                anchored_anchor,
                args.authorization_evidence,
            )
            anchor_directory = Path(anchor_relpath).parent
            anchored_surface_texts: dict[str, str] = {}
            for name in AMENDMENT_SURFACE_FILES:
                relative = (anchor_directory / name).as_posix()
                result = subprocess.run(
                    ["git", "-C", str(repo_root), "show", f"{args.plan_head_sha}:{relative}"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                require(
                    result.returncode == 0,
                    f"amendment surface {name} is absent from merged PR #91 anchor",
                )
                anchored_surface_texts[name] = result.stdout
            anchored_projection = amendment_surface_projection(
                anchored_plan,
                anchored_surface_texts,
            )
            current_projection = amendment_surface_projection(
                plan,
                load_amendment_surface_texts(root),
            )
            require_matching_amendment_snapshots(
                anchored_projection,
                current_projection,
            )
            anchored_surface_digest = amendment_projection_digest(anchored_projection)
            current_surface_digest = amendment_projection_digest(current_projection)
            require(
                anchored_anchor.get("amendment_surfaces_sha256")
                == anchored_surface_digest,
                "anchor amendment surface digest mismatch",
            )
            require(
                authorization["authorization_anchor"]["amendment_surfaces_sha256"]
                == current_surface_digest,
                "current amendment surface digest mismatch",
            )
            require(
                current_surface_digest == anchored_surface_digest,
                "current main amendment surface digest differs from merged PR #91 anchor",
            )
            if (
                re.fullmatch(r"FMV3-M[123]-\d{2}", args.authorize_issue)
                is not None
                and args.authorize_issue not in {"FMV3-M1-00", "FMV3-M1-05"}
            ):
                require_m1_admission_open(repo_root, authoritative_main)
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if args.authorize_issue is not None:
        print(
            f"PASS: {args.authorize_issue} is inside the fail-closed execution allowlist "
            f"at {args.plan_head_sha} with contract {args.authorization_contract_sha256}"
        )
    else:
        print(f"PASS: {root.name}; {issue_count} issues; {milestone_count} milestones; lifecycle consistent")
    return 0
if __name__ == "__main__": raise SystemExit(main())
