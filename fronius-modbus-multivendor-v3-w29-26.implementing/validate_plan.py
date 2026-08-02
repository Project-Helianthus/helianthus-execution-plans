#!/usr/bin/env python3
"""Validate only the structural contract of this locked execution-plan package."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
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
AUTHORIZATION_EVIDENCE_SCHEMA = "helianthus.fmv3-issue-authorization-evidence.v2"
ISSUE_SPEC_MARKER_PREFIX = "helianthus-fmv3-issue-spec-v1"
ISSUE_SPEC_FIELDS = (
    "id", "repo", "depends_on", "what", "acceptance", "gates", "doc_gate",
    "complexity",
)
DEPENDENCY_COMPLETION_CERTIFICATE_SCHEMA = (
    "helianthus.fmv3-direct-dependency-completion-certificate.v1"
)
M1_06_PRODUCER_ISSUE_TITLE = (
    "FMV3-M1-06: Implement the source-issued opaque single-use runtime acquisition capability."
)
M1_06_PRODUCER_PULL_REQUEST_TITLE = M1_06_PRODUCER_ISSUE_TITLE
M1_06_PRODUCER_ISSUE_MARKER = (
    "<!-- helianthus-fmv3-m1-06-opaque-runtime-acquisition-v1 -->"
)
M1_06_CONFORMANCE_REPORT_PATH = (
    ".github/fmv3/fmv3-m1-06-conformance-report.json"
)
M1_06_CONFORMANCE_REPORT_SCHEMA = (
    "helianthus.fmv3-m1-06-conformance-report.v3"
)
M1_06_OWNER_REVIEW_SCHEMA = "helianthus.fmv3-m1-06-owner-review.v1"
M1_06_RED_REQUIRED_CHECK = "checks"
GITHUB_ACTIONS_APP_ID = 15368
M1_06_CI_JOB_NAME = "checks"
M1_06_SETUP_STEP_NAME = "Set up Go"
M1_06_CI_STEP_NAME = "./scripts/ci_local.sh"
M1_06_HARNESS_PULL_REQUEST_TITLE = "FMV3-M1-06: install trusted evidence harness"
M1_06_RED_COMMIT_SUBJECT = "test: FMV3-M1-06 RED conformance"
M1_06_RED_GUARD_JOB_NAME = "FMV3 M1-06 RED guard"
M1_06_CONFORMANCE_JOB_NAME = "FMV3 M1-06 conformance"
M1_06_RED_GUARD_STEP_NAME = "Validate test-only RED diff"
M1_06_RED_COMPILE_STEP_NAME = "go test -run ^$ ."
M1_06_CONFORMANCE_GUARD_STEP_NAME = (
    "Validate GREEN root package and production API binding"
)
M1_06_RED_TEST_STEP_NAME = "Run exact M1-06 conformance tests"
M1_06_PRODUCTION_SYMBOLS = (
    {"name": "OpaqueRuntimeCapability", "kind": "type", "receiver": ""},
    {"name": "AttemptInstance", "kind": "type", "receiver": ""},
    {"name": "TerminalOutcome", "kind": "type", "receiver": ""},
    {"name": "NewRuntimeAcquisition", "kind": "function", "receiver": ""},
    {"name": "Claim", "kind": "method", "receiver": "*OpaqueRuntimeCapability"},
    {"name": "CloseMembership", "kind": "method", "receiver": "*AttemptInstance"},
    {"name": "CancelOpen", "kind": "method", "receiver": "*AttemptInstance"},
    {"name": "NewBoundedCapability", "kind": "function", "receiver": ""},
    {"name": "ReserveTerminalSequence", "kind": "function", "receiver": ""},
    {"name": "IsTerminal", "kind": "method", "receiver": "TerminalOutcome"},
)
M1_06_PRODUCTION_SYMBOL_NAMES = tuple(
    symbol["name"] for symbol in M1_06_PRODUCTION_SYMBOLS
)
M1_06_CONFORMANCE_CASES = {
    "M1-06-DELIVERABILITY-EXCLUSIONS": (
        "TestDeliverabilityExclusions", ("NewRuntimeAcquisition",)
    ),
    "M1-06-COPY-ONE-WINNER": (
        "TestCopiedCapabilityOneWinner", ("Claim",)
    ),
    "M1-06-STALE-INSTANCE-CANCEL-ISOLATION": (
        "TestStaleAttemptInstanceCancellationIsolation",
        ("CancelOpen",)
    ),
    "M1-06-TERMINAL-OUTCOMES": (
        "TestTerminalOutcomes", ("TerminalOutcome", "IsTerminal")
    ),
    "M1-06-MEMBERSHIP-CLOSE-RACE": (
        "TestAttemptMembershipCloseRegistrationRace",
        ("CloseMembership",)
    ),
    "M1-06-BOUNDS-OVERFLOW": (
        "TestBoundsAndOverflow", ("NewBoundedCapability",)
    ),
    "M1-06-SEQUENCE-EXHAUSTION": (
        "TestTerminalSequenceExhaustion", ("ReserveTerminalSequence",)
    ),
    "M1-06-COALESCED-ISOLATION": (
        "TestCoalescedDependentIsolation", ("NewRuntimeAcquisition",)
    ),
}
M1_06_CONFORMANCE_CASE_DIGEST = hashlib.sha256(
    json.dumps(
        list(M1_06_CONFORMANCE_CASES),
        sort_keys=False,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()
M1_06_MUTATION_WORKFLOW_PATH = ".github/workflows/fmv3-m1-06-mutation.yml"
M1_06_MUTATION_GUARD_PATH = "scripts/fmv3_m1_06_mutation_guard.go"
M1_06_DOCS_LOCK_VALIDATOR_PATH = "scripts/fmv3_m1_06_docs_lock.py"
M1_06_DOCS_LOCK_PATH = ".github/fmv3/opaque-runtime-acquisition-docs-lock.json"
M1_06_DOCS_LOCK_STEP_NAME = "Verify merged docs lock before build and tests"
M1_06_DOCS_LOCK_SCHEMA = "helianthus.opaque-runtime-acquisition-docs-lock.v1"
M1_06_MUTATION_WORKFLOW_SHA256 = "905642b3d2f994b8fb4871410c86a698715af876f51ab06755c557298ff65856"
M1_06_MUTATION_GUARD_SHA256 = "7090543997ebe7c5f822d71436f53e2f766f7fe7b5948208690a13101099ee73"
M1_06_DOCS_LOCK_VALIDATOR_SHA256 = "3b6a55cbdfada1b90d7271774ef7a864df78dc34b1a0087c34ceb14dce5ab1cc"
M1_06_TEMPLATE_SHA256 = {
    "fmv3-m1-06-mutation.yml": M1_06_MUTATION_WORKFLOW_SHA256,
    "fmv3_m1_06_mutation_guard.go": M1_06_MUTATION_GUARD_SHA256,
    "fmv3_m1_06_docs_lock.py": M1_06_DOCS_LOCK_VALIDATOR_SHA256,
}
M1_06_DOCS_LOCK_KEYS = {
    "schema", "repository", "pull_request", "merged_docs_commit_sha",
    "contract_id", "contract_version", "content_revision", "policy_path",
    "policy_sha256", "manifest_path", "manifest_sha256",
}
M3_03_WORKFLOW_CONTRACT = {
    "STANDARD_ONLY": {
        "workflow_path": ".github/workflows/fmv3-m3-03-conformance.yml",
        "template_path": "templates/fmv3-m3-03-conformance.yml",
        "sha256": "b74eb7d1c46c25c67c31e4ac796c03889018779412095b335d2f9d58e589e3ad",
    },
    "OVERLAY_REQUIRED": {
        "workflow_path": ".github/workflows/fmv3-m3-03-overlay-conformance.yml",
        "template_path": "templates/fmv3-m3-03-overlay-conformance.yml",
        "sha256": "f72fc7b1f3fadc78af5b8dd8dd1529936a040d01f456751ff4224d6b47ab2d85",
    },
}
M3_03_PROOF_CONTRACT = {
    "STANDARD_ONLY": {
        "directory": "registry",
        "source_path": "registry/fronius_overlay_test.go",
        "build_target": "./registry",
        "test_target": "./registry",
    },
    "OVERLAY_REQUIRED": {
        "directory": "profiles/fronius",
        "source_path": "profiles/fronius/fronius_overlay_test.go",
        "build_target": "./profiles/fronius/...",
        "test_target": "./profiles/fronius",
    },
}
M3_03_PREPARE_STEP_NAME = "Prepare isolated Fronius proof package"
M3_03_BUILD_STEP_NAME = "Build Fronius proof package"
M3_03_ACTIVATION_STEP_NAME = "Run Fronius neutral activation"
M3_03_IMPORT_STEP_NAME = "Run Fronius import boundary"
PLAN_TEMPLATE_SHA256 = {
    **M1_06_TEMPLATE_SHA256,
    "fmv3-m3-03-conformance.yml": M3_03_WORKFLOW_CONTRACT["STANDARD_ONLY"]["sha256"],
    "fmv3-m3-03-overlay-conformance.yml": M3_03_WORKFLOW_CONTRACT["OVERLAY_REQUIRED"]["sha256"],
}
M1_06_MUTATION_AST_STEP_NAME = "Validate executable AST mutation"
M1_06_MUTATION_COMPILE_STEP_NAME = "go test -run ^$ ."
M1_06_MUTATION_CASES = {
    case_id: f"go test -run ^{test_function}$ ."
    for case_id, (test_function, _) in M1_06_CONFORMANCE_CASES.items()
}
M1_05_COMPLETION_BINDING = {
    "kind": "docs_candidate_completion",
    "repository": DOCS_REPOSITORY,
    "github_issue_number": 385,
    "issue_title": "FMV3-M1-05: define opaque runtime acquisition contract",
    "github_pull_request_number": 386,
    "pull_request_title": "FMV3-M1-05: define opaque runtime acquisition contract",
}
CODEX_REVIEW_BODY_TEMPLATE = "".join((
    "\n### 💡 Codex Review\n\n",
    "Here are some automated review suggestions for this pull request.\n\n",
    "**Reviewed commit:** `{commit_prefix}`\n",
    "\x20\x20\x20\x20\n\n",
    "<details> <summary>ℹ️ About Codex in GitHub</summary>\n",
    "<br/>\n\n",
    "Codex has been enabled to automatically review pull requests in this repo. Reviews are triggered when you\n",
    "- Open a pull request for review\n",
    "- Mark a draft as ready\n",
    "- Comment \"@codex review\".\n\n",
    "If Codex has suggestions, it will comment; otherwise it will react with 👍.\n\n\n\n\n",
    "When you [sign up for Codex through ChatGPT](https://openai.com/codex), Codex can also answer questions or update the PR, like \"@codex address that feedback\".\n",
    "\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\n",
    "</details>",
))


def canonical_codex_review_body(commit_sha: str) -> str:
    require(re.fullmatch(r"[0-9a-f]{40}", commit_sha) is not None,
            "official Codex reviewed commit must be one full SHA")
    return CODEX_REVIEW_BODY_TEMPLATE.format(commit_prefix=commit_sha[:10])
EXTERNAL_REVIEW_ATTESTATION_TAG = (
    "<!-- helianthus-fmv3-pr91-external-review-attestation-v1 -->"
)
EXTERNAL_REVIEW_EVIDENCE_TAG = (
    "<!-- helianthus-fmv3-pr91-external-review-evidence-v1 -->"
)
EXTERNAL_REVIEW_ATTESTATION_SCHEMA = (
    "helianthus.fmv3-pr91-external-review-attestation.v1"
)
MATERIALIZATION_ENV_PREFIX = "FMV3_ANCHOR_MATERIALIZATION_"
TRUSTED_MATERIALIZED_EXECUTABLE_SHA256 = {
    "GIT": {
        "24d10c6f5ee9d5eb463273269d3bc30fa8dcbffda30841112480dea950d0c55a",
        "09b2e76b4a77c930755f0cf689babfe2b5f713b047636a6d264764567b395819",
        "f54a87f6253aab09ed7b522bd78ddeab509105b1043076209d89127e55877a48",
    },
    "GH": {
        "582a40676acf1394fcaf1c8c8bc5bad21806bd8c864b209d37b185c2df45dc92",
        "56b8bbbb27b066ecb33dbef9a256dc9d1314adaeff0908a752feba6c34053b40",
    },
}
EXPECTED_TRUSTED_TOOL_POLICY = {
    "schema": "helianthus.fmv3-trusted-tool-policy.v1",
    "fixed_paths": {
        "git": [
            "/Library/Developer/CommandLineTools/usr/bin/git",
            "/Applications/Xcode.app/Contents/Developer/usr/bin/git",
            "/usr/bin/git",
        ],
        "github_cli": ["/opt/homebrew/bin/gh", "/usr/local/bin/gh", "/usr/bin/gh"],
    },
    "sha256": {
        "git": sorted(TRUSTED_MATERIALIZED_EXECUTABLE_SHA256["GIT"]),
        "github_cli": sorted(TRUSTED_MATERIALIZED_EXECUTABLE_SHA256["GH"]),
    },
    "github_api_environment": [
        "HOME", "GH_TOKEN", "GITHUB_TOKEN", "LANG", "LC_ALL",
    ],
    "validator_environment": [
        "HOME", "GH_TOKEN", "GITHUB_TOKEN", "LANG", "LC_ALL",
        "FMV3_DOCS_CANDIDATE_ROOT", "HELIANTHUS_VALIDATION_CACHE_ROOT",
    ],
    "pull_request_tokens": "forbidden",
    "persisted_checkout_credentials": "forbidden",
    "linux_bootstrap": "unmodified_launcher_self_test",
    "post_merge_anchor_authentication": "required",
    "authorization_checkout": "owner_private_fresh_canonical_main_fetch",
    "git_environment": ["HOME", "LANG", "LC_ALL"],
    "caller_local_git_config": "forbidden",
}
REPOSITORY_CLAIM_SCHEMA = "helianthus.fmv3-repository-claim.v2"
REPOSITORY_CLAIM_TTL_SECONDS = 6 * 60 * 60
REPOSITORY_CLAIM_REF_PREFIX = "refs/heads/fmv3-claims-v2"
REPOSITORY_CLAIM_LEDGER_ID = "fmv3-pr91-v2"
REPOSITORY_CLAIM_OWNER_EPOCH = 1
REPOSITORY_CLAIM_INTEGRITY_RULESET_ID = 20195126
REPOSITORY_CLAIM_WRITER_RULESET_ID = 20195127
REPOSITORY_CLAIM_OWNER_LOGIN = "d3vi1"
REPOSITORY_CLAIM_OWNER_ACTOR_ID = 16434603
REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT = (
    "4734e2381a5adeb1ddfed6df81dc7c18c3284106c4c4a4d4b587180143de20b7"
)
MODEL_ROUTER_SHA256 = "e4e4658bc8252dc0354e2a04aaa74631098571ed0b00030e869760025a76e02b"
MODEL_ROUTING_POLICY_SHA256 = (
    "7c5fd44ba842c9da311f6211960b3151ed860245db41501efb9bfeec001c23c6"
)
ROUTING_RECEIPT_SCHEMA = "helianthus.fmv3-model-routing-receipt.v1"
ROUTING_GATE_RISK_MAP = {
    "security": "security",
    "data_integrity": "data_integrity",
    "concurrency": "concurrency",
    "recovery": "recovery",
    "protocol_interop": "wire_format",
    "transport_gate": "distributed_protocol",
}
DOCS_REPOSITORY = "Project-Helianthus/helianthus-docs-ebus"
TRUSTED_GIT_EXECUTABLE: Path | None = None
TRUSTED_GH_EXECUTABLE: Path | None = None
CLAIM_OWNER_SECRET: str | None = None
DOCS_MACHINE_FIELDS = (
    "schema", "version", "contract_id", "contract_version", "content_revision",
    "source_kind", "opaque_capability", "m2_ledger", "normalization_record",
    "bounded_values", "public_authorization", "zero_trust_boundary",
    "downstream_conformance",
)
DOCS_MACHINE_FIELDS_WITHOUT_BOUNDED_VALUES = tuple(
    field for field in DOCS_MACHINE_FIELDS if field != "bounded_values"
)
DOCS_BOOTSTRAP_SEMANTIC_FIELDS = (
    "source_kind", "opaque_capability", "m2_ledger", "normalization_record",
    "bounded_values", "public_authorization", "zero_trust_boundary",
    "downstream_conformance",
)
DOCS_BOOTSTRAP_CRITICAL_INVARIANTS = {
    "runtime_authority": "runtime_source_owned",
    "runtime_caller_control": "forbidden",
    "runtime_issuer": "runtime_source",
    "capability_consumption": "one_shot_compare_and_swap",
    "capability_serialization": "forbidden",
    "attempt_instance_identity": "opaque_unforgeable_nonserializable_per_attempt_incarnation",
    "attempt_membership_close": "ledger_admission_atomic_open_to_closing_blocks_new_registration",
    "cancel_owner": "runtime_source",
    "cancel_lookup": "exact_opaque_closed_AttemptInstance_frozen_membership_only",
    "ledger_seal_condition": "nonempty_all_runtime_data_bearing_exact_cardinality_all_claim_succeeded",
    "dependency_set_validation": "nonempty_unique_bounded_count_and_encoded_bytes_before_decode_allocation_sequence_reservation_or_cas",
    "publish_commit_linearization": "irreversible_external_effect_and_publishing_to_published_one_transactional_commit",
    "published_projection_schema": "published_attempt_v1",
    "ledger_publication_on_non_success": "cancellation_and_audit_only_publication_forbidden",
    "downstream_docs_lock": [
        "merged_docs_commit_sha_full_40", "policy_sha256", "manifest_sha256",
    ],
    "zero_trust_boundary": "no_gateway_vendor_semantic_write_authorization",
}
EXPECTED_DOCS_CANDIDATE_BINDING = {
    "repo": DOCS_REPOSITORY,
    "pr": 386,
    "pr_url": "https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/386",
    "commit_sha": "4a4c6f431ae0166e309bee71771c66aebe0d173a",
    "commit_tree_sha": "2cca03b13d3300fb0753a43e2ef48e28683c00c2",
    "pull_request_identity": {
        "number": 386,
        "base_sha": "777954d1dea586409827116f2a0eb887ee5cd4f4",
        "base_repo": DOCS_REPOSITORY,
        "base_ref": "main",
        "head_repo": DOCS_REPOSITORY,
        "head_ref": "issue/385-opaque-runtime-acquisition",
    },
    "required_check_runs": [
        {"context": "Modbus Trusted Revision", "app_id": GITHUB_ACTIONS_APP_ID,
         "check_run_id": 91495144438},
    ],
    "manifest_path": "docs/platform/manifests/opaque-runtime-acquisition-v1.json",
    "manifest_sha256": "f692b01c7747bea0a1db3e68440826918e826c0fcc0afac0cde8e580e9a7616c",
    "policy_path": "docs/platform/opaque-runtime-acquisition-v1.md",
    "policy_sha256": "a95e2ec593a6c06584c06f1486b167c917e756d0af48b83896c51f05e58742d8",
    "normative_blobs": {
        ".github/workflows/modbus-trusted-revision.yml": "229616e784d7735ff7bf2288a7986f170898b75a9fac5dffbfa1c499f6795b98",
        "docs/platform/manifests/modbus-foundation-profile-contract-v1.json": "c411e3e8a464e4b9d3a59d3f5a0c82b57e176e24dec9550b9bc0c8b3e4b28c70",
        "docs/platform/manifests/opaque-runtime-acquisition-v1.json": "f692b01c7747bea0a1db3e68440826918e826c0fcc0afac0cde8e580e9a7616c",
        "docs/platform/modbus-foundation-profile-contract-v1.md": "1a53f203eed42766ac2d91580c41f72674b5eaea374a1cf4fff650396f06b196",
        "docs/platform/modbus-multivendor-boundaries.md": "b7edf9fc6073a441a638b392d6dfc92ea5851e2cf0b2080e09a46c395788480c",
        "docs/platform/opaque-runtime-acquisition-v1.md": "a95e2ec593a6c06584c06f1486b167c917e756d0af48b83896c51f05e58742d8",
        "docs/platform/schemas/modbus-companion-consumer-lock-v1.schema.json": "369a724954d21614d71fd970c8b6224d8c892af8870819cbef159619acce4ad0",
        "protocols/modbus/modbus-phase-one-wire-v1.md": "b941a60b39409c570f904f8e6830787203f8041c2fee462164c4c50c7a8f4444",
        "scripts/validate_modbus_companion.py": "cad2fe98a6c144d43bb5207c99ea054779d0f843f84eec3c29e19872fd7864ff",
        "scripts/validate_modbus_revision_transition.py": "8a024501ecd3c9e89bec049c7bf7d0ffbbc143a8f0128aba56741b361ada6d3b",
        "scripts/validate_opaque_runtime_acquisition.py": "8174762ba5994cdbda138c85428318ab11eeb3f64d07b170a87efa25e101eef6",
        "tests/test_modbus_companion_contract.py": "2b71925833eb0fe71af84f845e1baf0e7d6ce245b9c94be5e060d1202ba7c837",
        "tests/test_modbus_trusted_revision.py": "5cf860e220cb75958099f1b1f5d90c53a1f3247241b80554f0fe3554ebcef3bd",
        "tests/test_opaque_runtime_acquisition_contract.py": "b17afcdae8a54f88823ceeeb872a2381fe5a0ea9ce8e1947b5125d58daeeed4f",
    },
    "machine_projection_fields": list(DOCS_MACHINE_FIELDS),
    "machine_projection_sha256": "8cf8c51def65e4d23f820577a53b5899feb2eb79b5049a30f4d3c42b8ad7218c",
    "machine_projection_without_bounded_values_sha256": "a0b43ab65ff9fefefffe7ed6fe771f653ab4c29c5faab2422265291325089ab9",
    "bootstrap_trust_anchor": {
        "schema": "helianthus.fmv3-pr91-docs-bootstrap-trust.v1",
        "authoritative_root": "pr91_exact_tree_owner_decision_merge_plus_official_codex_exact_head_review",
        "ordering": "pr91_immutable_merge_and_official_codex_review_before_docs_pr386_merge",
        "docs_internal_hashes": "same_change_set_not_independent",
        "semantic_projection_sha256": "6518315a3d38bf0498f2b1e89abdbcd17a55e6ecc1c487662147f7478054a262",
        "critical_semantic_invariants": DOCS_BOOTSTRAP_CRITICAL_INVARIANTS,
    },
    "r2_rebind": {
        "status": "BOUND_DOCS_R2",
        "blocks_authorization_for": [],
        "required_semantics": [
            "claim_in_progress",
            "cancelling",
            "closed_attempt_instance_membership_before_ledger_admission",
            "nonempty_exact_ordered_runtime_dependency_set_before_seal",
            "CancelOpen_closed_AttemptInstance_linearization",
            "atomic_publish_cancel_winner",
            "closed_published_projection",
            "downstream_docs_lock_and_behavioral_conformance",
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
    "trust_model": "owner_plus_authenticated_independent_review_v1",
    "authoritative_evidence": "exact_tree_owner_decision_merge_plus_official_codex_exact_head_review",
    "mandatory_non_authoritative_evidence": "same_change_set_post_merge_ci_execution_observation",
    "owner_threat_model": "repository_owner_trusted_malicious_or_compromised_owner_resistance_out_of_scope",
    "source": "github_pr_issue_comment",
    "tag": EXTERNAL_REVIEW_ATTESTATION_TAG,
    "schema": EXTERNAL_REVIEW_ATTESTATION_SCHEMA,
    "issuer": "authorized_issuer",
    "trusted_association": "allowed_author_associations",
    "edit_policy": "created_at_equals_updated_at",
    "timing": "reviews_before_merge_then_aggregate_after_canonical_main_push_run",
    "verdict": "NO_FINDINGS",
    "owner_process_attestations": 2,
    "evidence_reviews": "one_authenticated_official_codex_review_plus_two_owner_process_attestations",
    "aggregate_binds": ["repository", "pull_request", "head_sha", "head_tree_sha", "workflow_run_id", "official_review_id", "owner_review_ids"],
    "head_publication_evidence": "non_authoritative_same_change_set_execution",
}
EXPECTED_ISSUE_EVIDENCE_POLICY = {
    "FMV3-M1-05": {
        "completion_binding": "exact_docs_issue_385_and_closing_pr_386",
    },
    "FMV3-M1-06": {
        "requires": "docs_pr_386_merged_at_exact_bound_candidate_head_and_tree",
    },
    "FMV3-M2-01": {
        "cli": "--authorization-evidence <external-json-file>",
        "schema": AUTHORIZATION_EVIDENCE_SCHEMA,
        "dependencies": ["FMV3-M1-06"],
        "producer_issue": "FMV3-M1-06",
        "producer_repository": MODBUS_REPOSITORY,
        "requires": [
            "full_40_character_merge_sha",
            "canonical_main_ancestry",
            "immutable_issue_marker_and_title",
            "sequential_premerged_owner_harness_pr_with_clean_exact_head_review",
            "selected_issue_branch_and_pr_interval_containment",
            "premerge_exact_check_run_ids_and_app_bound_policy",
            "exact_anchored_dual_mode_workflow_ast_guard_docs_lock_validator_and_merged_docs_lock_blobs",
            "unchanged_inherited_ci_tooling",
            "exact_squash_product_pull_request_head_tree_and_harness_base_parent",
            "test_only_red_ancestor_with_exact_subject_and_anchored_pull_request_guard_compile_test_failure",
            "exact_implementation_head_green_required_checks_and_anchored_conformance_success",
            "official_codex_exact_head_zero_inline_findings",
            "two_owner_process_attestations_after_green_and_mutations",
            "fixed_path_closed_conformance_report_with_exact_source_blobs_and_mutation_patch_digests",
            "root_module_exact_go_list_files_same_package_no_test_shims",
            "eight_exact_parent_report_bound_mutants_with_unchanged_harness_ast_parent_baseline_compile_and_mapped_failure",
        ],
    },
    "FMV3-M2-02": {"schema": AUTHORIZATION_EVIDENCE_SCHEMA, "dependencies": ["FMV3-M2-01"]},
    "FMV3-M2-03": {"schema": AUTHORIZATION_EVIDENCE_SCHEMA, "dependencies": ["FMV3-M2-01", "FMV3-M2-02"]},
    "FMV3-M3-01": {"schema": AUTHORIZATION_EVIDENCE_SCHEMA, "dependencies": ["FMV3-M2-01"]},
    "FMV3-M3-02": {"schema": AUTHORIZATION_EVIDENCE_SCHEMA, "dependencies": ["FMV3-M2-03", "FMV3-M3-01"]},
    "FMV3-M3-03": {"schema": AUTHORIZATION_EVIDENCE_SCHEMA, "dependencies": ["FMV3-M3-02"]},
}
COMPLETED_FMV3_DEPENDENCIES = {
    "FMV3-M0-01": {
        "kind": "manual_repository_creation", "repository": "Project-Helianthus/.github",
        "github_issue_number": 2,
        "issue_title": "FMV3-M0-01: create public Modbus repositories",
        "closed_at": "2026-07-26T15:23:57Z", "closed_by": "d3vi1",
        "completion_comment_id": 5084116709,
        "completion_comment_sha256": "9f2a13dcaa5da76000bfad85e371dff9d1a3abc9aa1f62aa32f937e5d32f38b3",
    },
    "FMV3-M0-02": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 1,
        "issue_title": "FMV3-M0-02: bootstrap the public Modbus runtime repository",
        "github_pull_request_number": 2, "pull_request_title": "chore: bootstrap public Modbus runtime repository",
        "head_sha": "e938946cb332d64a5f8331abe6a6f1b39f67a00e", "head_tree_sha": "71355ffdc8d60b319797e94355705764ba679f0e",
        "merge_sha": "7e4b4c53a8b91751550222d6d98125e41d3db8c1", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89814625783}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89814625786}],
        "bootstrap_seed": {"commit_sha": "bd15e364a749adcca283570f027bfb826198952a", "tree_sha": "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "parents": [], "message": "chore: initialize repository for issue #1"},
    },
    "FMV3-M0-03": {
        "repository": "Project-Helianthus/helianthus-modbusreg", "github_issue_number": 1,
        "issue_title": "FMV3-M0-03: bootstrap the public multi-profile registry repository",
        "github_pull_request_number": 2, "pull_request_title": "chore: bootstrap public Modbus profile registry",
        "head_sha": "b8fa5b1b5f01e4776338f2b9ffaf2b99ee058d85", "head_tree_sha": "9dbf08e3681b8bf9bd9a71f516a7ee0318c5b16d",
        "merge_sha": "c6f26b33e38525cddc1c0ce19389ed19a8bb6844", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89814626133}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89814626113}],
        "bootstrap_seed": {"commit_sha": "bd15e364a749adcca283570f027bfb826198952a", "tree_sha": "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "parents": [], "message": "chore: initialize repository for issue #1"},
    },
    "FMV3-M0-06": {
        "repository": DOCS_REPOSITORY, "github_issue_number": 371,
        "issue_title": "FMV3-M0-06: publish Modbus ownership and licensing boundaries",
        "github_pull_request_number": 372, "pull_request_title": "docs(platform): define Modbus repository boundaries",
        "head_sha": "a0ba25ef445abd5d17f5df4ff386040c3f4ed8a7", "head_tree_sha": "600cf88f8e742f8412ba2ae8d91076a4c44fa389",
        "merge_sha": "7b0dd0abba8bc3420f1d8d2bae2db5bc229b75f3", "required_checks": [{"context": "Docs Checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "Platform Contracts Combined Ref / Validate Explicit Combined Refs", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "Docs Checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89811147700}, {"context": "Platform Contracts Combined Ref / Validate Explicit Combined Refs", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89811147766}],
    },
    "FMV3-M1-00": {
        "repository": DOCS_REPOSITORY, "github_issue_number": 373,
        "issue_title": "FMV3-M1-00: Define Modbus M1/M2 companion contract",
        "github_pull_request_number": 376, "pull_request_title": "docs(platform): define Modbus M1/M2 companion contract",
        "head_sha": "db88c05ad9f49a23fdd3fc9de0e5d9ea3ca99055", "head_tree_sha": "25d4cd89216f0d1f2f05261506316bd64f91483b",
        "merge_sha": "711a556fee344c6fe7f1ecf3253fcdb3f5f22d06", "required_checks": [{"context": "Docs Checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "Platform Contracts Combined Ref / Validate Explicit Combined Refs", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "Docs Checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89890610488}, {"context": "Platform Contracts Combined Ref / Validate Explicit Combined Refs", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89890610566}],
    },
    "FMV3-M1-01": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 3,
        "issue_title": "FMV3-M1-01: implement strict phase-one Modbus PDU codecs",
        "github_pull_request_number": 4, "pull_request_title": "feat: implement strict phase-one Modbus PDU codecs",
        "head_sha": "9a07587a6157c6f570b054fe2eb6bd60f009fc7f", "head_tree_sha": "b13d5be4f965b3b6f3aae796aa6281f0526ccfe4",
        "merge_sha": "c9b3281b5025fd3b1b714235493bd36d526f865f", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89898484344}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 89898484259}],
    },
    "FMV3-M1-02": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 5,
        "issue_title": "FMV3-M1-02: implement owned Modbus TCP runtime",
        "github_pull_request_number": 6, "pull_request_title": "FMV3-M1-02: implement owned Modbus TCP runtime",
        "head_sha": "0aac61ddad62f664b47900334c48803587183fa3", "head_tree_sha": "ac81a5294a84a1783cb84f56cfe1ba455291c1ee",
        "merge_sha": "467229104bfe34ca90aa653ca22ad79da4fa9a32", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 90289850077}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 90289849636}],
    },
    "FMV3-M1-03": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 9,
        "issue_title": "FMV3-M1-03: implement fixture-only Modbus RTU runtime",
        "github_pull_request_number": 10, "pull_request_title": "FMV3-M1-03: fixture-only Modbus RTU runtime",
        "head_sha": "4f8e69dad3c57c798f3eb3d74f7382f3ae9d685b", "head_tree_sha": "12717cdd6efc34dcc6560cc98690d9436fd59951",
        "merge_sha": "fd7524fee3d4ea808a67185341a3bf13f6d151cd", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 90339773059}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 90339773231}],
    },
    "FMV3-M1-04": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 13,
        "issue_title": "FMV3-M1-04: close offline transport conformance and recovery matrices",
        "github_pull_request_number": 14, "pull_request_title": "FMV3-M1-04: close offline transport conformance matrices",
        "head_sha": "ada08479e73ecf7c9f892558e577347bf2f16dd9", "head_tree_sha": "1c2a90e5637ab989d66b87de264fc555c25965d0",
        "merge_sha": "4f81cbeb6321e64fa51676ed6e375ce36b60d16d", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
        "required_check_runs": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 90360576732}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 90360576695}],
    },
    "FMV3-M1-05": M1_05_COMPLETION_BINDING,
}
EXPECTED_M1_06_PRODUCER_PIN_CONTRACT = {
    "producer_issue": "FMV3-M1-06",
    "repository": MODBUS_REPOSITORY,
    "evidence_interface": "external_json_file",
    "evidence_schema": AUTHORIZATION_EVIDENCE_SCHEMA,
    "merge_sha": "required_full_40_lowercase_hex",
    "github_issue_number": "required_positive_integer",
    "github_pull_request_number": "required_positive_integer",
    "red_commit_sha": "required_full_40_lowercase_hex_selector",
    "red_workflow_run_id": "required_positive_integer_selector",
    "red_workflow_run_attempt": "required_positive_integer_selector",
    "red_check_runs": "exact_app_check_run_id_selectors",
    "red_job_ids": "exact_workflow_job_id_selectors",
    "green_workflow_run_id": "required_positive_integer_selector",
    "green_workflow_run_attempt": "required_positive_integer_selector",
    "green_check_runs": "exact_app_check_run_id_selectors",
    "green_job_ids": "exact_workflow_job_id_selectors",
    "harness_pull_request_number": "required_positive_integer_selector",
    "harness_merge_sha": "required_full_40_lowercase_hex_selector",
    "harness_workflow_id": "required_positive_integer_selector",
    "harness_required_check_runs": "exact_ordered_policy_app_and_check_run_id_selectors",
    "harness_ci_run": "exact_attempt_job_and_check_run_selector",
    "mutation_runs": "eight_ordered_case_commit_run_attempt_check_and_job_selectors",
    "mutation_compile_step": M1_06_MUTATION_COMPILE_STEP_NAME,
    "mutation_report_binding": "canonical_github_patch_sha256_per_case",
    "official_review_id": "required_positive_integer_selector",
    "owner_review_ids": "exactly_two_distinct_positive_integer_selectors",
    "issue_title": M1_06_PRODUCER_ISSUE_TITLE,
    "pull_request_title": M1_06_PRODUCER_PULL_REQUEST_TITLE,
    "issue_marker": M1_06_PRODUCER_ISSUE_MARKER,
    "conformance_report_path": M1_06_CONFORMANCE_REPORT_PATH,
    "conformance_report_schema": M1_06_CONFORMANCE_REPORT_SCHEMA,
    "conformance_case_digest": M1_06_CONFORMANCE_CASE_DIGEST,
    "verification": [
        "fixed_github_api_canonical_main_ancestry",
        "exact_issue_marker_title_and_closing_pull_request",
        "squash_head_tree_and_single_base_parent",
        "sequential_owner_harness_pr_exact_product_base_and_clean_review",
        "selected_issue_branch_and_pr_interval_containment",
        "premerge_exact_check_run_ids_app_bound_policy_workflow_attempts_and_job_ids",
        "all_pull_request_intervals_no_overlap",
        "test_only_red_ancestor_exact_subject_and_anchored_pull_request_failure",
        "exact_head_required_checks_and_anchored_conformance_success",
        "official_codex_zero_inline_findings",
        "two_fresh_owner_no_findings_after_green",
        "fixed_path_closed_conformance_report_exact_regular_blobs_and_mutation_patch_digests",
        "root_package_fixed_go_environment_exact_compiled_inputs_go_types_production_binding_no_test_shims",
        "red_job_proves_test_only_guard_compile_and_exact_conformance_failure",
        "exact_premerged_dual_mode_workflow_ast_guard_docs_lock_validator_and_merged_docs_lock_blobs",
        "inherited_ci_and_ci_local_unchanged_across_harness_and_product",
        "eight_exact_parent_report_bound_mutants_retain_harness_and_pass_ast_parent_test_compile_before_mapped_failure",
    ],
    "consumer_resolution": "exact_sha_verified_before_red",
}
EXPECTED_TOOLING_PATHS = {
    "validator_path": "fronius-modbus-multivendor-v3-w29-26.implementing/validate_plan.py",
    "workflow_path": ".github/workflows/ci.yml",
    "launcher_reference_path": "scripts/fmv3_anchor_validator.py",
}
EXPECTED_D13_DECISION = "FMV3-M1-05 documents and FMV3-M1-06 implements OPAQUE_RUNTIME_ACQUISITION_V1 as an additive successor to M1-04 before M2-01. A runtime source privately owns and issues each non-serializable one-shot capability only after all post-correlation successful-dependent deliverability conditions; only copies of that same capability share its state, and M1 state is never an M2 ledger pointer. Endpoint recreation and every new acquisition create fresh independent state even when visible identity or data match. Capability state moves open to claimed, cancelled, failed, or expired and is synchronously reclaimed by a pre-reserved terminal sequence into a finite-positive, byte-bounded, non-reconstructing tombstone ring. M2-01 pins the merged M1-06 producer SHA, keeps runtime and fixture trust distinct, and owns a separately bounded attempt/claim ledger across every retained state. The exact docs R2 binding requires unresolved claims to enter claim_in_progress before one immutable terminal result, open or sealed attempts to enter cancelling before cancelled, an atomic seal predicate requiring a nonempty exact ordered all-runtime dependency set with exact cardinality and every claim_succeeded, runtime-source-owned CancelOpen linearized by the exact opaque closed AttemptInstance with frozen membership, explicit byte and field bounds validated before allocation, one-shot sealed-to-publishing Publish(), and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. Deterministic reclamation preserves only bounded non-reconstructing audit metadata and the complete normalization record round-trips losslessly within admitted bounds. Consumer CI locks the merged docs SHA and policy/manifest hashes, exercises the eight downstream race/membership/ordering/seal/projection rows, and permits publication only through the five-field published_attempt_v1 projection with one atomic publish/cancel winner."
EXPECTED_M2_EXIT_GATE = "The reused FMV3-M1-00 companion remains merged, and M2-01 starts only after M1-06 merges and external authorization evidence supplies bounded selectors whose live GitHub objects prove the exact immutable marked/title issue and exact closing product squash PR on canonical main. A preceding owner-authored harness PR under the same issue must be the sole active PR, merge first with required checks and one clean exact-head Codex review, add only the plan-anchored dual-mode workflow, AST guard, docs-lock validator, and exact merged-docs lock, leave inherited ci.yml and ci_local.sh unchanged, and become the exact product PR base. The RED commit has the exact validator-pinned subject and test-only diff; the anchored pull_request workflow proves its RED guard and compile/no-tests succeed before the exact conformance suite fails. The implementation head has app-bound required checks green and the same anchored workflow proves conformance success. Eight exact-parent production-only mutants retain the exact harness blobs, match canonical patch digests precommitted by the GREEN report, pass the AST guard and parent mapped test, compile, and only then fail the exact mutant mapped test. The product head then receives one official Codex canonical-template zero-inline review and two owner NO_FINDINGS process attestations after GREEN and mutations; the fixed-path closed conformance report binds every validator-pinned case to an exact Go test/source blob/PASS, exact mutation patch digest, and exact production contract symbols. The exact docs R2 head/tree binding requires claim_in_progress and cancelling states, a nonempty exact ordered all-runtime dependency-set seal predicate with exact cardinality and every claim succeeded, runtime-source-owned CancelOpen linearization by the exact opaque closed AttemptInstance with frozen membership, byte and field bounds validated before allocation, and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. Profile API, exact wire-response/logical-view/sample identity and provenance, runtime-versus-fixture trust, independently ledger-owned bounded attempt/claim state across all retained states, finite-positive limits with a checked retained-attempt-limit times claim-limit product, duplicate AttemptKey rejection, complete immutable-terminal lifecycles, one-shot sealed publication, deterministic synchronous terminal-sequence reclamation into a finite-positive byte-bounded non-reconstructing audit/tombstone ring, exact bounded normalization round-trip, detector lifecycle, merged-docs SHA plus policy/manifest consumer lock, all eight downstream behavioral rows, five-field published_attempt_v1 projection, and atomic publish/cancel winner are stable under strict hosted RED/GREEN and fresh independent review."
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
to the externally attested PR head tree. One submitted official
Codex bot `COMMENTED` review must equal the canonical Codex no-suggestions template for the
exact ten-character head prefix and have zero inline findings; no severity or arbitrary finding
text is accepted. Two separate submitted owner reviews then bind that head/tree, `NO_FINDINGS`,
and owner-attested fresh-process references/output digests; they are process attestations, not
independently authenticated OpenAI artifacts. One unedited aggregate binds the
immutable submitted review IDs and a mandatory, non-authoritative same-change-set post-merge
`push` workflow execution observation on canonical `main` at the exact squash SHA; the aggregate is created only after that run completes, and
the plan never self-embeds its own head SHA.

Trust model: `owner_plus_authenticated_independent_review_v1`. The authoritative decision is the
trusted repository owner's exact-tree squash decision plus the official Codex exact-head review;
owner process attestations are non-independent. The post-merge CI observation is mandatory but
non-authoritative. Resistance to a malicious or compromised repository owner is out of scope.

PR #91 is also the external bootstrap trust root for the V1 docs candidate: its immutable
exact-tree owner decision and official exact-head Codex review must precede docs PR #386's merge.
It anchors the candidate head/tree, normative manifest, policy, semantic-validator and test blobs,
the normalized V1 semantic projection, and critical invariants including runtime-source authority
and forbidden caller control. Refreshed same-change-set docs hashes or validator results are not
independent authority and cannot weaken that bootstrap semantic anchor; docs contain no reference
to an unknown PR #91 merge SHA.

The ordered `authorized_issues` list in `plan.yaml` is the sole normative execution scope:
FMV3-M0-01, FMV3-M0-02, FMV3-M0-03, FMV3-M0-06, FMV3-M1-00, FMV3-M1-01,
FMV3-M1-02, FMV3-M1-03, FMV3-M1-04, FMV3-M1-05, FMV3-M1-06, FMV3-M2-01,
FMV3-M2-02, FMV3-M2-03, FMV3-M3-01, FMV3-M3-02, and FMV3-M3-03. Milestone names
are non-authoritative grouping labels. This amendment corrects FMV3-M1-05, FMV3-M1-06,
and FMV3-M2-01 without changing the allowlist.

Authorization ignores caller Git configuration and objects after validating the supplied path shape.
The trusted launcher resolves canonical `Project-Helianthus/helianthus-execution-plans` main
through the fixed GitHub API, fetches that exact SHA from a hardcoded canonical URL into a new
owner-private checkout, and runs Git with system/global config, hooks, fsmonitor, credential
helpers, replacements, grafts, and alternates disabled. The launcher and anchored validator both
accept only the same plan-bound pinned Git and GitHub CLI executable digests, verify candidate
symlink and opened-inode stability, pass only the exact plan-bound child environment allowlists,
authenticate the PR #91 merge SHA first, materialize the validator blob directly from that
immutable commit, verify its anchored SHA-256, and only then execute the one-use blob. The claim owner supplies an
external owner-only mode-0400 256-bit secret; only its commitment enters the public claim. The
internal call binds the exact selected open GitHub issue number and one lowercase run UUID. A
self-consistent caller-supplied executable hash is never sufficient. PR-head validation receives
no GitHub token and no persisted checkout credential. Hosted Ubuntu exercises the unmodified
launcher against its platform allowlist before merge and authenticates the real PR91 anchor from
trusted canonical main after merge. The versioned launcher reference and SHA-256 are bound in the
PR91 tooling record. Preflight must execute that repo-owned launcher directly from the owner-private
canonical-main checkout; copied or separately installed launcher executables are forbidden. The
checked-out candidate validator is defense-in-depth and is never the bootstrap trust root.

FMV3-M0-01 creates only the two empty public repositories `helianthus-modbus` and
`helianthus-modbusreg`. M0-02 and M0-03 each then use their sole destination-initialization
exception: direct push of exact no-parent commit `bd15e364a749adcca283570f027bfb826198952a`
with the empty tree `4b825dc642cb6eb9a060e54bf8d69288fbee4904` and no content, solely to establish
`main` as the legal base for issue #1 / PR #2. All later changes use branch/PR/squash flow.
FMV3-M1-05 publishes the public
`OPAQUE_RUNTIME_ACQUISITION_V1` companion, FMV3-M1-06 implements it after M1-05, and
FMV3-M2-01 consumes the merged M1-06 producer by exact full-SHA pin. Private governance
creation FMV3-M0-04 and destination bootstraps FMV3-M0-05/FMV3-M0-07 remain deferred.

Every authorized issue must prove completion of exactly its direct `depends_on` predecessors.
Completed FMV3 predecessors use immutable exact live-GitHub bindings for repository, issue and PR
titles/numbers, closing body and timeline relation, closure time, base/head/merge/tree/topology,
canonical-main ancestry, exact selected-issue branch and issue-contained PR interval, and exact-head
required checks bound by immutable check-run ID and completed before merge. M0-01 binds the exact no-object repository
creation closure and unedited completion-attestation comment. M0-02/M0-03 additionally bind the
shared exact empty-tree root commit, no-parent topology, message, PR #2 base, and subsequent squash
completion. Those are the only destination-initialization exceptions. Every unresolved direct predecessor must appear exactly
once in the bounded external `dependencies` certificate array; exact set equality rejects missing,
duplicate, extra, and non-direct rows. Each row binds exact repository, issue/PR selectors,
an anchored issue-spec digest and marker, head/tree/merge SHAs, the complete dynamic main
required-check policy, and an ordered exact check-run ID for every policy row, all authenticated
live. Every authorization-relevant required check has a concrete positive GitHub App ID and must
have completed before the selected PR merge; legacy context-only, any-app, unbound, and post-merge
rerun evidence is rejected.
M2-01 retains its producer extension, which must equal its M1-06 dependency row. Stale, unmerged,
wrong issue/PR, failed-check, wrong-tree/topology, or non-main evidence fails closed.
M1-05 completion is the exact docs issue #385 with its immutable title and repository, closed by
docs PR #386 through an exact `Closes #385` body line, live timeline relation, and authoritative
GraphQL `closingIssuesReferences`, with issue closure inside a bounded 60-second post-merge window. FMV3-M1-06 requires docs PR #386 merged with the exact bound candidate
head and tree, dynamically ancestral to canonical docs main, with all exact-head required checks
successful under its concrete app-bound policy, one official Codex exact-head `COMMENTED` review using the
exact canonical no-suggestions template and zero inline findings, and two owner structured
`NO_FINDINGS` process attestations submitted after CI. FMV3-M2-01 additionally accepts only external selectors for the
M1-06 issue, sequential harness and closing product PRs, merge and RED commit SHAs, anchored
RED/GREEN/mutation runs, official Codex review, and exactly two owner reviews; selector values
are not trusted outcome claims. Live GitHub must prove the exact immutable issue title and
`<!-- helianthus-fmv3-m1-06-opaque-runtime-acquisition-v1 -->` marker. Under that issue, an
owner-authored harness PR uses the selected issue branch, opens after that issue, is the sole active PR, adds only the exact plan-anchored dual-mode
workflow, executable-AST guard, docs-lock validator, and exact merged-docs lock, leaves inherited `ci.yml` and `ci_local.sh` blobs unchanged,
passes the certificate-bound pre-merge required check runs, with the checks job bound to its exact workflow attempt, job, and check-run IDs, and one clean exact-head Codex review,
and merges before product work.
The product PR starts from exactly that harness merge and then proves canonical same-repo
main/base/head identity, exact issue closure, reviewed head-tree equality with the one-parent
squash merge tree and PR base, and canonical-main ancestry. The RED commit carries the exact
pinned subject and is an implementation-head ancestor whose bounded first diff page contains only
Go tests, fixtures, or the fixed conformance-report path; diff page two is empty. Its exact anchored
`pull_request` workflow passes the test-only guard and compile/no-tests before the exact M1-06 suite
fails. All dynamically required checks then succeed on the exact implementation head, and the same
anchored workflow proves conformance success. RED, GREEN, docs, and mutation completion evidence
binds immutable app/check-run IDs; harness checks, RED, GREEN, and mutation evidence also bind the exact workflow
attempt and job IDs, so a later same-name rerun cannot invalidate or replace the certificate. Eight ordered production-Go-only mutant commits are
direct children of GREEN and retain the exact harness blobs. The GREEN report precommits each
canonical GitHub patch digest; each anchored mutation run passes executable-AST validation, the
mapped test on the GREEN parent, and compile/no-tests before that mapped test fails on the mutant.
One official Codex exact-head review after those mutations must use the exact
canonical no-suggestions template and have zero inline findings. Two owner `COMMENTED` closed-schema
`NO_FINDINGS` process attestations after GREEN and mutations must bind the exact RED/head/tree,
fixed conformance-report blob, validator-pinned case digest, and mutation-evidence digest. The regular committed report
`.github/fmv3/fmv3-m1-06-conformance-report.json` must use
`helianthus.fmv3-m1-06-conformance-report.v3`; its closed fixed case set binds deliverability
exclusions, copy one-winner, stale same-key instance cancellation isolation, terminal outcomes,
membership close/registration race,
bounds/overflow, sequence exhaustion, and coalesced isolation to exact Go test declarations,
source blobs, regular modes, nonempty failure/assertion bodies, semantic calls, `PASS`, and the
exact per-case mutation patch digest. Its exact module-root package projection binds fixed
`GOOS=linux`, `GOARCH=amd64`, `CGO_ENABLED=0`, `GOWORK=off` and the complete sorted
`GoFiles`/`CompiledGoFiles`/`TestGoFiles` set while every cgo, ignored, external-test, C/C++/assembly,
SWIG, syso, embed pattern/file, or other non-Go compiled-input category is empty. The trusted premerged guard runs
`go list -compiled` and `go/types`, binds every symbol by declaration kind, receiver, signature, and exact object identity, and credits a required test call only when its result directly controls a live failing assertion condition.
Every bound source must be in the same package and root directory,
must have no explicit or implicit build exclusion, cgo import, or nested module, and test files may
not redeclare or locally shadow any production contract symbol; every named conformance test has exactly one declaration. Its
production Go blobs must declare every fixed contract symbol. Missing, stale, fake, failed,
semantic-no-op, non-direct, or mismatched producer proof fails closed.
The exact docs R2 commit/tree, complete predecessor-inclusive normative closure, and expanded
machine projection including `bounded_values` and `downstream_conformance` are bound. They require
an opaque per-incarnation `AttemptInstance`, atomic membership close and freeze before ledger
admission, claim-in-progress, cancelling, a nonempty exact ordered all-runtime dependency set,
source-owned `CancelOpen(AttemptInstance)`, one atomic publish/cancel winner, the closed five-field
`published_attempt_v1` projection, byte/field bounds, and pre-reserved non-wrapping, non-reused
terminal sequences. M1-06 and M2-01 CI must lock the merged docs full SHA plus policy and manifest
hashes and run the eight downstream behavioral rows. Both issues still fail authorization until
docs PR #386 is merged at that exact head and tree.

The hard stop is immediately before FMV3-M4-01. Gateway work is not authorized. No gateway
issue, branch, PR, import, or code change is authorized by this action. Repository creation,
implementation issues, commits, pushes, reviews, and merges are authorized only for the
ordered issue list above and remain subject to every direct dependency and gate."""
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
        "Modbusreg bootstrap, merged FMV3-M1-00 and M1-06, live selector-authenticated producer TDD/review/artifact closure, and exact docs R2 binding",
        "Independent ledger adds claim_in_progress/cancelling, nonempty exact ordered all-runtime dependency set and exact-cardinality success before seal, closed AttemptInstance CancelOpen linearization, byte/field bounds, reserved non-wrapping terminal sequences, finite-positive limits and checked product; one-shot immutable Publish(); non-reconstructing reclamation; runtime/fixture trust; exact normalization/provenance/conformance",
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
        "FMV3-M1-06 merged after sequential anchored harness/product PRs, trusted RED/GREEN/mutation proof, clean reviews, fixed conformance report, and canonical-main proof",
        "FMV3-M2-01",
    ],
]
EXPECTED_CORRECTIVE_PHASE_GATES = [
    {
        "id": "PG-OPAQUE-ACQUISITION-DOC-GATE",
        "kind": "dependency",
        "after_issues": ["FMV3-M1-05"],
        "before_issues": ["FMV3-M1-06"],
        "requirement": "The public OPAQUE_RUNTIME_ACQUISITION_V1 companion merges after M1-04 through docs PR #386 at the exact bound docs R2 head/tree before M1-06 code. That exact binding includes claim_in_progress and cancelling states, a nonempty exact ordered all-runtime dependency-set seal predicate with exact cardinality and every claim succeeded, runtime-source-owned CancelOpen linearization by the exact opaque closed AttemptInstance with frozen membership, byte and field bounds validated before allocation, and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. The source-kind, source-private capability, deliverability, copy sharing, fresh acquisition, bounded lifecycle, one-shot Publish, reclamation, coalescing, and normalization contract remains exact. Fresh independent OpenAI review blocks merge.",
    },
    {
        "id": "PG-OPAQUE-ACQUISITION-CONSUMER-PIN",
        "kind": "dependency",
        "after_issues": ["FMV3-M1-06"],
        "before_issues": ["FMV3-M2-01"],
        "requirement": "M2-01 cannot begin until M1-06 has merged and bounded external selectors resolve live to its immutable marked/title issue; a sequential owner harness PR with required checks, one clean exact-head Codex review, only the anchored workflow, AST guard, docs-lock validator, and exact merged-docs lock additions, unchanged inherited CI tooling, and canonical-main merge; the exact closing product squash PR based directly on that harness merge; a test-only RED ancestor with exact subject, empty second diff page, and anchored exact-PR guard/compile success followed by exact-suite failure; exact-head app-bound required checks and anchored conformance success; eight exact-parent production-only mutants retaining the harness blobs, matching report-bound patch digests, passing AST and parent-baseline guards plus compile, then failing only the mapped mutant test; one official Codex zero-inline review and two owner NO_FINDINGS attestations after GREEN and mutations; and the fixed report binding exact Go test/source blobs, PASS, mutation digests, and production symbols. The exact docs R2 binding must also verify through the merged docs SHA plus policy/manifest hash lock and all eight downstream behavioral conformance rows.",
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


def trusted_materialized_executable(kind: str) -> Path:
    path_value = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}{kind}")
    digest = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}{kind}_SHA256")
    require(path_value is not None and digest is not None,
            f"trusted {kind.lower()} executable binding is absent")
    path = Path(path_value)
    require(path.is_absolute(), f"trusted {kind.lower()} executable path is not absolute")
    resolved = path.resolve()
    metadata = resolved.stat()
    computed_digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    require(
        kind in TRUSTED_MATERIALIZED_EXECUTABLE_SHA256
        and
        resolved == path
        and not path.is_symlink()
        and stat.S_ISREG(metadata.st_mode)
        and stat.S_IMODE(metadata.st_mode) == 0o500
        and metadata.st_uid == os.getuid()
        and isinstance(digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and computed_digest == digest
        and computed_digest in TRUSTED_MATERIALIZED_EXECUTABLE_SHA256[kind],
        f"trusted {kind.lower()} executable binding is not exact",
    )
    return resolved


def trusted_git_executable() -> Path:
    global TRUSTED_GIT_EXECUTABLE
    if TRUSTED_GIT_EXECUTABLE is not None:
        return TRUSTED_GIT_EXECUTABLE
    system_git = Path("/usr/bin/git")
    require(system_git.is_file() and not system_git.is_symlink(),
            "system Git executable is absent")
    metadata = system_git.stat()
    require(metadata.st_uid == 0 and metadata.st_mode & 0o022 == 0,
            "system Git executable is not root-owned and immutable")
    return system_git


def git_command(
    repo: Path,
    args: list[str],
    label: str,
    *,
    text: bool = True,
) -> str | bytes:
    environment = {
        name: os.environ[name]
        for name in ("HOME", "LANG", "LC_ALL")
        if os.environ.get(name)
    }
    environment.update({
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
    })
    result = subprocess.run(
        [
            str(trusted_git_executable()), "--no-replace-objects",
            "-c", "core.hooksPath=/dev/null",
            "-c", "core.fsmonitor=false",
            "-c", "credential.helper=",
            "-C", str(repo), *args,
        ],
        check=False,
        capture_output=True,
        text=text,
        env=environment,
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
    replacement_refs = git_command(
        repo_root,
        ["for-each-ref", "--format=%(refname)", "refs/replace"],
        f"{label} replacement-ref inspection",
    ).strip()
    git_dir = Path(str(git_command(
        repo_root, ["rev-parse", "--absolute-git-dir"], f"{label} git-dir lookup",
    )).strip())
    grafts = git_dir / "info" / "grafts"
    alternates = git_dir / "objects" / "info" / "alternates"
    require(
        not replacement_refs
        and (not grafts.exists() or grafts.stat().st_size == 0)
        and (not alternates.exists() or alternates.stat().st_size == 0),
        f"{label} rejects replacement refs, grafts, and alternate object stores",
    )


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
    manifest = unique_json_object(
        manifest_bytes.decode("utf-8"), "docs candidate opaque manifest"
    )
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
    bootstrap = binding.get("bootstrap_trust_anchor")
    require(isinstance(bootstrap, dict)
            and bootstrap.get("critical_semantic_invariants")
            == DOCS_BOOTSTRAP_CRITICAL_INVARIANTS,
            "docs bootstrap critical semantic invariants mismatch")
    semantic_projection = {
        field: manifest[field] for field in DOCS_BOOTSTRAP_SEMANTIC_FIELDS
    }
    require(canonical_json_sha256(semantic_projection)
            == bootstrap.get("semantic_projection_sha256"),
            "docs bootstrap semantic projection differs from the PR #91 trust anchor")
    observed_invariants = {
        "runtime_authority": manifest["source_kind"]["runtime"]["deliverability"]["authority"],
        "runtime_caller_control": manifest["source_kind"]["runtime"]["deliverability"]["caller_control"],
        "runtime_issuer": manifest["source_kind"]["runtime"]["issuer"],
        "capability_consumption": manifest["opaque_capability"]["consumption"],
        "capability_serialization": manifest["source_kind"]["runtime"]["deliverability"]["serialization"],
        "attempt_instance_identity": manifest["opaque_capability"]["attempt_instance"]["identity"],
        "attempt_membership_close": manifest["opaque_capability"]["attempt_instance"]["membership"]["close"],
        "cancel_owner": manifest["opaque_capability"]["attempt_binding"]["cancel_open"]["owner"],
        "cancel_lookup": manifest["opaque_capability"]["attempt_binding"]["cancel_open"]["lookup"],
        "ledger_seal_condition": manifest["m2_ledger"]["attempt_lifecycle"]["seal_condition"],
        "dependency_set_validation": manifest["m2_ledger"]["dependency_set"]["validation"],
        "publish_commit_linearization": manifest["m2_ledger"]["attempt_lifecycle"]["publish_commit_linearization"],
        "published_projection_schema": manifest["m2_ledger"]["published_projection"]["schema"],
        "ledger_publication_on_non_success": manifest["m2_ledger"]["attempt_lifecycle"]["seal_non_success"],
        "downstream_docs_lock": manifest["downstream_conformance"]["docs_lock"],
        "zero_trust_boundary": manifest["zero_trust_boundary"],
    }
    require(observed_invariants == bootstrap["critical_semantic_invariants"],
            "docs bootstrap critical semantic invariant differs from the PR #91 trust anchor")
    predecessor_manifest_path = (
        "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
    )
    predecessor_manifest = unique_json_object(
        blobs[predecessor_manifest_path].decode("utf-8"),
        "docs candidate predecessor manifest",
    )
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
        opaque["attempt_binding"]["source_operation"] == "CancelOpen(AttemptInstance)"
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
        opaque["attempt_instance"]["identity"]
        == "opaque_unforgeable_nonserializable_per_attempt_incarnation"
        and opaque["attempt_instance"]["membership"]["close"]
        == "ledger_admission_atomic_open_to_closing_blocks_new_registration"
        and opaque["attempt_binding"]["cancel_open"]["lookup"]
        == "exact_opaque_closed_AttemptInstance_frozen_membership_only"
        and ledger["attempt_lifecycle"]["seal_condition"]
        == "nonempty_all_runtime_data_bearing_exact_cardinality_all_claim_succeeded"
        and ledger["attempt_lifecycle"]["seal_forbidden_sets"]
        == "empty_fixture_only_mixed_zero_runtime_duplicate_omitted_reordered"
        and ledger["attempt_lifecycle"]["seal_linearization"]
        == "success_predicate_and_open_to_sealed_atomic"
        and ledger["dependency_set"]["validation"]
        == "nonempty_unique_bounded_count_and_encoded_bytes_before_decode_allocation_sequence_reservation_or_cas"
        and "claim_in_progress"
        in ledger["claim_entry_lifecycle"]["nonterminal"]
        and "open_to_cancelling" in ledger["attempt_lifecycle"]["legal_transitions"]
        and ledger["cancellation_protocol"]["source_operation"]
        == "runtime_source_owned_CancelOpen_exact_closed_AttemptInstance"
        and ledger["cancellation_protocol"]["drain"]
        == "wait_for_all_claim_in_progress_finalization"
        and ledger["attempt_lifecycle"]["publish_commit_linearization"]
        == "irreversible_external_effect_and_publishing_to_published_one_transactional_commit"
        and ledger["published_projection"]["schema"] == "published_attempt_v1"
        and projection["downstream_conformance"]["docs_lock"]
        == ["merged_docs_commit_sha_full_40", "policy_sha256", "manifest_sha256"]
        and len(projection["downstream_conformance"]["required_behavioral_tests"]) == 8,
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
        ("launcher_reference_path", "launcher_reference_sha256"),
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
    require(
        binding.get("trusted_tool_policy") == EXPECTED_TRUSTED_TOOL_POLICY,
        "authorization trusted tool policy mismatch",
    )
def trusted_gh_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    require(TRUSTED_GH_EXECUTABLE is not None,
            "trusted GitHub CLI was not supplied by the anchor materializer")
    executable = TRUSTED_GH_EXECUTABLE
    environment = {
        name: os.environ[name]
        for name in ("HOME", "GH_TOKEN", "GITHUB_TOKEN", "LANG", "LC_ALL")
        if os.environ.get(name)
    }
    return subprocess.run(
        [str(executable), "api", "--hostname", "github.com", *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )


def github_api(endpoint: str) -> Any:
    result = trusted_gh_command([endpoint])
    value = json.loads(result.stdout)
    require(isinstance(value, (dict, list)), f"GitHub API returned invalid JSON for {endpoint}")
    return value


def github_server_time() -> datetime:
    """Read API response time through the pinned authenticated GitHub CLI."""
    result = trusted_gh_command(["--include", "rate_limit"])
    date_headers = [
        line.partition(":")[2].strip()
        for line in result.stdout.splitlines()
        if line.lower().startswith("date:")
    ]
    require(len(date_headers) == 1,
            "GitHub API response has no unique authenticated Date header")
    try:
        observed = parsedate_to_datetime(date_headers[0])
    except (TypeError, ValueError) as exc:
        raise ValidationError("GitHub API Date header is invalid") from exc
    require(observed.tzinfo is not None,
            "GitHub API Date header has no timezone")
    return observed.astimezone(timezone.utc).replace(microsecond=0)


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


def github_paginated_list(endpoint: str, label: str,
                          *, maximum_pages: int = 100) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    separator = "&" if "?" in endpoint else "?"
    for page in range(1, maximum_pages + 1):
        value = github_api(f"{endpoint}{separator}per_page=100&page={page}")
        require(isinstance(value, list), f"{label} response is invalid")
        require(all(isinstance(item, dict) for item in value),
                f"{label} contains an invalid row")
        rows.extend(value)
        if len(value) < 100:
            return rows
    raise ValidationError(f"{label} pagination exceeds the fail-closed bound")


def github_paginated_object_rows(endpoint: str, row_key: str, label: str,
                                 *, query: str = "",
                                 maximum_pages: int = 100) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    expected_total: int | None = None
    separator = "&" if "?" in endpoint else "?"
    prefix = f"{query}&" if query else ""
    for page in range(1, maximum_pages + 1):
        value = github_api(
            f"{endpoint}{separator}{prefix}per_page=100&page={page}"
        )
        page_rows = value.get(row_key) if isinstance(value, dict) else None
        total = value.get("total_count") if isinstance(value, dict) else None
        require(type(total) is int and total >= 0 and isinstance(page_rows, list),
                f"{label} response is invalid")
        require(all(isinstance(item, dict) for item in page_rows),
                f"{label} contains an invalid row")
        if expected_total is None:
            expected_total = total
            require(expected_total <= maximum_pages * 100,
                    f"{label} exceeds the fail-closed row bound")
        require(total == expected_total, f"{label} total_count changed during pagination")
        rows.extend(page_rows)
        require(len(rows) <= expected_total, f"{label} returned duplicate excess rows")
        if len(page_rows) < 100:
            require(len(rows) == expected_total,
                    f"{label} pagination omitted rows")
            return rows
    raise ValidationError(f"{label} pagination exceeds the fail-closed bound")


def github_all_check_runs(repository: str, head_sha: str,
                          label: str) -> list[dict[str, Any]]:
    return github_paginated_object_rows(
        f"repos/{repository}/commits/{head_sha}/check-runs",
        "check_runs",
        label,
        query="filter=all",
    )


def github_latest_check_runs(repository: str, head_sha: str,
                             label: str) -> list[dict[str, Any]]:
    return github_paginated_object_rows(
        f"repos/{repository}/commits/{head_sha}/check-runs",
        "check_runs",
        label,
        query="filter=latest",
    )


CLOSING_ISSUES_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      closingIssuesReferences(first: 100, after: $cursor) {
        nodes { number repository { nameWithOwner } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
""".strip()

CLOSED_EVENTS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      timelineItems(first: 100, after: $cursor, itemTypes: [CLOSED_EVENT]) {
        nodes {
          ... on ClosedEvent {
            createdAt
            closer {
              __typename
              ... on PullRequest { number mergedAt repository { nameWithOwner } }
            }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
""".strip()


def github_closing_issue_references(
    repository: str,
    pull_request_number: int,
) -> set[tuple[str, int]]:
    owner, name = repository.split("/", 1)
    references: set[tuple[str, int]] = set()
    cursor: str | None = None
    for _page in range(100):
        command = [
            "graphql",
            "-f", f"query={CLOSING_ISSUES_QUERY}",
            "-F", f"owner={owner}",
            "-F", f"name={name}",
            "-F", f"number={pull_request_number}",
        ]
        if cursor is not None:
            command.extend(["-f", f"cursor={cursor}"])
        result = trusted_gh_command(command)
        value = json.loads(result.stdout)
        connection = (
            value.get("data", {}).get("repository", {})
            .get("pullRequest", {}).get("closingIssuesReferences")
            if isinstance(value, dict) else None
        )
        nodes = connection.get("nodes") if isinstance(connection, dict) else None
        page_info = connection.get("pageInfo") if isinstance(connection, dict) else None
        require(isinstance(nodes, list) and len(nodes) <= 100
                and isinstance(page_info, dict)
                and type(page_info.get("hasNextPage")) is bool,
                "GitHub closingIssuesReferences response is invalid")
        for node in nodes:
            node_repository = (
                node.get("repository", {}).get("nameWithOwner")
                if isinstance(node, dict) else None
            )
            number = node.get("number") if isinstance(node, dict) else None
            require(isinstance(node_repository, str)
                    and type(number) is int and number > 0,
                    "GitHub closingIssuesReferences contains an invalid row")
            reference = (node_repository, number)
            require(reference not in references,
                    "GitHub closingIssuesReferences contains duplicate rows")
            references.add(reference)
        if not page_info["hasNextPage"]:
            require(page_info.get("endCursor") is None
                    or isinstance(page_info.get("endCursor"), str),
                    "GitHub closingIssuesReferences terminal cursor is invalid")
            return references
        next_cursor = page_info.get("endCursor")
        require(isinstance(next_cursor, str) and next_cursor
                and next_cursor != cursor,
                "GitHub closingIssuesReferences pagination cursor is invalid")
        cursor = next_cursor
    raise ValidationError(
        "GitHub closingIssuesReferences pagination exceeds the fail-closed bound"
    )


def github_issue_closed_events(
    repository: str,
    issue_number: int,
) -> list[dict[str, Any]]:
    owner, name = repository.split("/", 1)
    events: list[dict[str, Any]] = []
    cursor: str | None = None
    for _page in range(100):
        command = [
            "graphql",
            "-f", f"query={CLOSED_EVENTS_QUERY}",
            "-F", f"owner={owner}",
            "-F", f"name={name}",
            "-F", f"number={issue_number}",
        ]
        if cursor is not None:
            command.extend(["-f", f"cursor={cursor}"])
        result = trusted_gh_command(command)
        value = json.loads(result.stdout)
        connection = (
            value.get("data", {}).get("repository", {}).get("issue", {})
            .get("timelineItems") if isinstance(value, dict) else None
        )
        nodes = connection.get("nodes") if isinstance(connection, dict) else None
        page_info = connection.get("pageInfo") if isinstance(connection, dict) else None
        require(
            isinstance(nodes, list) and len(nodes) <= 100
            and all(isinstance(node, dict) for node in nodes)
            and isinstance(page_info, dict)
            and type(page_info.get("hasNextPage")) is bool,
            "GitHub ClosedEvent timeline response is invalid",
        )
        events.extend(nodes)
        require(len(events) <= 10000, "GitHub ClosedEvent timeline exceeds the bound")
        if not page_info["hasNextPage"]:
            return events
        next_cursor = page_info.get("endCursor")
        require(
            isinstance(next_cursor, str) and next_cursor and next_cursor != cursor,
            "GitHub ClosedEvent timeline pagination cursor is invalid",
        )
        cursor = next_cursor
    raise ValidationError("GitHub ClosedEvent timeline pagination exceeds the fail-closed bound")


def require_issue_closed_by_pull_request(
    repository: str,
    issue_number: int,
    issue: dict[str, Any],
    pull_request_number: int,
    pull_request: dict[str, Any],
    label: str,
) -> None:
    references = github_closing_issue_references(repository, pull_request_number)
    require((repository, issue_number) in references,
            f"{label} is absent from pull request closingIssuesReferences")
    closed_at = parse_github_time(issue.get("closed_at"), f"{label} issue closed_at")
    merged_at = parse_github_time(
        pull_request.get("merged_at"), f"{label} pull request merged_at"
    )
    require(merged_at <= closed_at <= merged_at + timedelta(seconds=60),
            f"{label} issue closure is not within the bounded post-merge window")
    matching_events = []
    for event in github_issue_closed_events(repository, issue_number):
        closer = event.get("closer")
        if not isinstance(closer, dict):
            continue
        if (
            closer.get("__typename") == "PullRequest"
            and closer.get("number") == pull_request_number
            and closer.get("repository", {}).get("nameWithOwner") == repository
            and parse_github_time(closer.get("mergedAt"), f"{label} closer mergedAt")
            == merged_at
            and parse_github_time(event.get("createdAt"), f"{label} ClosedEvent createdAt")
            == closed_at
        ):
            matching_events.append(event)
    require(
        len(matching_events) == 1,
        f"{label} current closure is not bound to one immutable PR ClosedEvent",
    )


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
    merge_sha: str,
) -> None:
    require(
        anchor.get("external_review_attestation")
        == EXPECTED_EXTERNAL_REVIEW_ATTESTATION,
        "external review attestation contract mismatch",
    )
    comments = github_issue_comments(PLAN_REPOSITORY, AMENDMENT_PR_NUMBER)
    tagged = [comment for comment in comments if EXTERNAL_REVIEW_ATTESTATION_TAG in str(comment.get("body", ""))]
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
        "review_process_attestation",
        "workflow_run_id",
        "official_review_id",
        "owner_review_ids",
        "trust_model",
        "post_merge_run_classification",
    }
    require(
        set(attestation) == expected_keys,
        "PR #91 review attestation schema keys mismatch",
    )
    workflow_run_id = attestation.get("workflow_run_id")
    official_review_id = attestation.get("official_review_id")
    owner_review_ids = attestation.get("owner_review_ids")
    require(
        attestation["schema"] == EXTERNAL_REVIEW_ATTESTATION_SCHEMA
        and attestation["repository"] == PLAN_REPOSITORY
        and attestation["pull_request"] == AMENDMENT_PR_NUMBER
        and type(attestation["pull_request"]) is int
        and attestation["head_sha"] == head_sha
        and attestation["head_tree_sha"] == head_tree
        and attestation["verdict"] == "NO_FINDINGS"
        and attestation["review_process_attestation"]
        == "owner_attests_two_fresh_openai_contexts",
        "PR #91 review attestation does not bind the exact reviewed head/tree, verdict, and owner-attested process",
    )
    require(
        attestation["trust_model"] == "owner_plus_authenticated_independent_review_v1"
        and attestation["post_merge_run_classification"]
        == "non_authoritative_same_change_set_execution",
        "PR #91 trust-model classification is invalid",
    )
    require(
        type(workflow_run_id) is int
        and workflow_run_id > 0
        and type(official_review_id) is int and official_review_id > 0
        and isinstance(owner_review_ids, list)
        and len(owner_review_ids) == 2
        and len(owner_review_ids) == len(set(owner_review_ids))
        and official_review_id not in owner_review_ids
        and all(type(review_id) is int and review_id > 0 for review_id in owner_review_ids),
        "PR #91 review aggregate requires one workflow run, one official review, and two distinct owner review IDs",
    )
    head_commit_time = head_commit.get("committer", {}).get("date")
    created_at = parse_github_time(comment.get("created_at"), "attestation created_at")
    head_time = parse_github_time(head_commit_time, "PR #91 head commit time")
    merged_time = parse_github_time(pr.get("merged_at"), "PR #91 merged_at")
    workflow = github_api(f"repos/{PLAN_REPOSITORY}/actions/runs/{workflow_run_id}")
    require(isinstance(workflow, dict), "PR #91 workflow run evidence is invalid")
    require(
        workflow.get("id") == workflow_run_id
        and workflow.get("workflow_id") == 244018027
        and workflow.get("event") == "push"
        and workflow.get("status") == "completed"
        and workflow.get("conclusion") == "success"
        and workflow.get("head_sha") == merge_sha
        and workflow.get("head_branch") == "main"
        and workflow.get("path") == ".github/workflows/ci.yml"
        and workflow.get("actor", {}).get("login") == anchor["authorized_issuer"]
        and workflow.get("head_repository", {}).get("full_name") == PLAN_REPOSITORY
        and workflow.get("pull_requests") == [],
        "PR #91 workflow run does not prove the exact canonical-main merge SHA",
    )
    workflow_time = parse_github_time(workflow.get("updated_at"), "PR #91 workflow updated_at")
    require(
        created_at > workflow_time > merged_time > head_time,
        "PR #91 aggregate must follow the exact canonical-main push run after merge",
    )
    reviews = github_paginated_list(
        f"repos/{PLAN_REPOSITORY}/pulls/{AMENDMENT_PR_NUMBER}/reviews",
        "PR #91 native reviews",
    )
    by_id = {review.get("id"): review for review in reviews if isinstance(review, dict) and type(review.get("id")) is int}
    require(len(by_id) == len({review.get("id") for review in reviews if isinstance(review, dict)}), "PR #91 native reviews have duplicate or invalid IDs")
    official_review = by_id.get(official_review_id)
    owner_reviews = [by_id.get(review_id) for review_id in owner_review_ids]
    exact_head_codex = [review for review in reviews if isinstance(review, dict)
                        and review.get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
                        and review.get("commit_id") == head_sha]
    require(len(exact_head_codex) == 1
            and exact_head_codex[0].get("id") == official_review_id
            and isinstance(official_review, dict)
            and all(isinstance(item, dict) for item in owner_reviews),
            "PR #91 must have exactly one selected official Codex review at the exact head")
    require(
        official_review.get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
        and official_review.get("state") == "COMMENTED"
        and official_review.get("commit_id") == head_sha
        and official_review.get("body") == canonical_codex_review_body(head_sha),
        "PR #91 official Codex review is not an exact-head submitted COMMENTED review",
    )
    inline = github_paginated_list(
        f"repos/{PLAN_REPOSITORY}/pulls/{AMENDMENT_PR_NUMBER}/reviews/{official_review_id}/comments",
        "PR #91 official Codex inline comments",
    )
    require(not inline, "PR #91 official Codex review has inline findings")
    official_time = parse_github_time(official_review.get("submitted_at"), "official native review submitted_at")
    require(
        head_time < official_time < merged_time and created_at > official_time,
        "PR #91 official Codex review timing is invalid",
    )
    owner_run_ids: list[str] = []
    owner_output_hashes: list[str] = []
    for evidence in owner_reviews:
        assert isinstance(evidence, dict)
        require(
            evidence.get("user", {}).get("login") == anchor["authorized_issuer"]
            and evidence.get("author_association") in anchor["allowed_author_associations"]
            and evidence.get("state") == "COMMENTED"
            and evidence.get("commit_id") == head_sha,
            "PR #91 native review is not submitted, trusted, and bound to the exact head",
        )
        review = unique_json_object(str(evidence.get("body", "")), "PR #91 native review body")
        require(
            set(review) == {"schema", "repository", "pull_request", "head_sha", "head_tree_sha", "verdict", "attestation_kind", "review_process", "reviewer_run_reference", "output_digest_sha256"}
            and review["schema"] == EXTERNAL_REVIEW_ATTESTATION_SCHEMA
            and review["repository"] == PLAN_REPOSITORY
            and review["pull_request"] == AMENDMENT_PR_NUMBER
            and review["head_sha"] == head_sha
            and review["head_tree_sha"] == head_tree
            and review["verdict"] == "NO_FINDINGS"
            and review["attestation_kind"] == "owner_process_attestation"
            and review["review_process"] == "fresh_openai_context"
            and isinstance(review["reviewer_run_reference"], str)
            and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", review["reviewer_run_reference"]) is not None
            and isinstance(review["output_digest_sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", review["output_digest_sha256"]) is not None,
            "PR #91 owner process attestation does not bind exact head/tree/process/NO_FINDINGS",
        )
        evidence_time = parse_github_time(evidence.get("submitted_at"), "native review submitted_at")
        require(
            head_time < evidence_time < merged_time and created_at > evidence_time,
            "PR #91 aggregate or native review timing is invalid",
        )
        owner_run_ids.append(review["reviewer_run_reference"])
        owner_output_hashes.append(review["output_digest_sha256"])
    require(len(owner_run_ids) == len(set(owner_run_ids)) and len(owner_output_hashes) == len(set(owner_output_hashes)), "PR #91 owner process references and output digests must be unique")


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
        plan_head_sha,
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
    bootstrap = binding["bootstrap_trust_anchor"]
    pr91 = github_api(f"repos/{PLAN_REPOSITORY}/pulls/{AMENDMENT_PR_NUMBER}")
    require(isinstance(pr91, dict) and pr91.get("state") == "closed"
            and pr91.get("merged") is True and isinstance(pr91.get("merged_at"), str)
            and bootstrap.get("ordering")
            == "pr91_immutable_merge_and_official_codex_review_before_docs_pr386_merge"
            and parse_github_time(pr91["merged_at"], "PR #91 merged_at")
            < parse_github_time(pr["merged_at"], "docs PR #386 merged_at"),
            "docs PR #386 must merge after the immutable PR #91 bootstrap trust root")
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
    docs_main = canonical_main_sha(DOCS_REPOSITORY)
    compare = github_api(
        f"repos/{DOCS_REPOSITORY}/compare/{pr['merge_commit_sha']}...{docs_main}"
    )
    require(
        isinstance(compare, dict)
        and compare.get("status") in {"ahead", "identical"}
        and compare.get("merge_base_commit", {}).get("sha") == pr["merge_commit_sha"],
        "docs PR #386 merge is not on dynamic canonical docs main",
    )
    protection = github_api(
        f"repos/{DOCS_REPOSITORY}/branches/main/protection/required_status_checks"
    )
    docs_check_specs = live_required_check_specs(
        protection, "docs PR #386 canonical main required-check policy"
    )
    check_runs = require_exact_head_checks(
        DOCS_REPOSITORY,
        binding["commit_sha"],
        [{"context": name, "app_id": app_id} for name, app_id in docs_check_specs],
        "docs PR #386",
        completed_before=parse_github_time(
            pr.get("merged_at"), "docs PR #386 merged_at"
        ),
        bound_runs=binding["required_check_runs"],
    )
    reviews = github_paginated_list(
        f"repos/{DOCS_REPOSITORY}/pulls/{binding['pr']}/reviews",
        "docs PR #386 reviews",
    )
    codex_reviews = [
        review for review in reviews if isinstance(review, dict)
        and review.get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
        and review.get("state") == "COMMENTED"
        and review.get("commit_id") == binding["commit_sha"]
        and review.get("body") == canonical_codex_review_body(binding["commit_sha"])
    ]
    require(len(codex_reviews) == 1, "docs PR #386 requires one official Codex exact-head COMMENTED review")
    codex_review = codex_reviews[0]
    inline = github_paginated_list(
        f"repos/{DOCS_REPOSITORY}/pulls/{binding['pr']}/reviews/{codex_review['id']}/comments",
        "docs PR #386 official Codex inline comments",
    )
    require(not inline, "docs PR #386 official Codex review has inline findings")
    checks_time = max(
        parse_github_time(item.get("completed_at"), "docs required check completed_at")
        for item in check_runs
    )
    docs_merged_at = parse_github_time(pr.get("merged_at"), "docs PR #386 merged_at")
    require(checks_time < docs_merged_at,
            "docs PR #386 required checks must complete before merge")
    exact_head_codex = [review for review in reviews if isinstance(review, dict)
                        and review.get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
                        and review.get("commit_id") == binding["commit_sha"]]
    require(len(exact_head_codex) == 1 and exact_head_codex[0].get("id") == codex_review.get("id"),
            "docs PR #386 must have exactly one official Codex review at the exact head")
    codex_time = parse_github_time(
        codex_review.get("submitted_at"), "docs official Codex submitted_at"
    )
    require(checks_time < codex_time < docs_merged_at,
            "docs PR #386 official Codex review must follow CI and precede merge")
    owner_reviews = []
    for review in reviews:
        if not isinstance(review, dict) or review.get("user", {}).get("login") != anchor["authorized_issuer"]:
            continue
        if review.get("author_association") not in anchor["allowed_author_associations"] or review.get("state") != "COMMENTED" or review.get("commit_id") != binding["commit_sha"]:
            continue
        body = unique_json_object(str(review.get("body", "")), "docs owner review body")
        require(
            set(body) == {"schema", "repository", "pull_request", "head_sha", "head_tree_sha", "verdict", "attestation_kind", "review_process", "reviewer_run_reference", "output_digest_sha256"}
            and body["schema"] == EXTERNAL_REVIEW_ATTESTATION_SCHEMA
            and body["repository"] == DOCS_REPOSITORY and body["pull_request"] == binding["pr"]
            and body["head_sha"] == binding["commit_sha"] and body["head_tree_sha"] == binding["commit_tree_sha"]
            and body["verdict"] == "NO_FINDINGS"
            and body["attestation_kind"] == "owner_process_attestation"
            and body["review_process"] == "fresh_openai_context"
            and isinstance(body["reviewer_run_reference"], str)
            and re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                body["reviewer_run_reference"],
            ) is not None
            and isinstance(body["output_digest_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", body["output_digest_sha256"]),
            "docs PR #386 owner review is not structured owner-attested exact-head NO_FINDINGS process evidence",
        )
        owner_time = parse_github_time(
            review.get("submitted_at"), "docs owner review submitted_at"
        )
        require(checks_time < owner_time < docs_merged_at,
                "docs PR #386 owner reviews must follow CI and precede merge")
        owner_reviews.append((body["reviewer_run_reference"], body["output_digest_sha256"]))
    require(
        len(owner_reviews) == 2
        and len({run for run, _ in owner_reviews}) == 2
        and len({digest for _, digest in owner_reviews}) == 2,
        "docs PR #386 requires two independently distinct owner COMMENTED process attestations",
    )


def load_issue_authorization_evidence(
    path_value: str | None,
    issue_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if path_value is None:
        return [], None
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
    expected_keys = {"schema", "authorization_issue", "dependencies"}
    if issue_id == "FMV3-M2-01":
        expected_keys.add("producer")
    require(set(evidence) == expected_keys
            and evidence.get("schema") == AUTHORIZATION_EVIDENCE_SCHEMA
            and evidence.get("authorization_issue") == issue_id,
            "authorization evidence envelope mismatch")
    dependencies = evidence.get("dependencies")
    require(isinstance(dependencies, list) and len(dependencies) <= 8,
            "authorization evidence dependencies must be a bounded array")
    certificate_keys = {
        "plan_issue", "repository", "github_issue_number",
        "github_pull_request_number", "issue_spec_sha256", "head_sha",
        "head_tree_sha", "merge_sha", "required_checks", "required_check_runs",
    }
    for dependency in dependencies:
        expected_certificate_keys = certificate_keys | (
            {"completion_artifact"}
            if dependency.get("plan_issue") == "FMV3-M3-03" else set()
        ) if isinstance(dependency, dict) else certificate_keys
        require(isinstance(dependency, dict) and set(dependency) == expected_certificate_keys,
                "dependency completion certificate schema mismatch")
        require(isinstance(dependency["plan_issue"], str)
                and re.fullmatch(r"FMV3-M[0-8]-\d{2}", dependency["plan_issue"])
                and isinstance(dependency["repository"], str)
                and dependency["repository"] in TARGET_REPOS
                and type(dependency["github_issue_number"]) is int
                and dependency["github_issue_number"] > 0
                and type(dependency["github_pull_request_number"]) is int
                and dependency["github_pull_request_number"] > 0,
                "dependency completion certificate selector mismatch")
        require(isinstance(dependency["issue_spec_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", dependency["issue_spec_sha256"]),
                "dependency completion certificate issue spec digest is invalid")
        for key in ("head_sha", "head_tree_sha", "merge_sha"):
            require(isinstance(dependency[key], str)
                    and re.fullmatch(r"[0-9a-f]{40}", dependency[key]),
                    f"dependency completion certificate {key} must be a full SHA")
        checks = dependency["required_checks"]
        require(isinstance(checks, list) and 0 < len(checks) <= 16
                and all(isinstance(check, dict) for check in checks),
                "dependency completion certificate required-check policy is invalid")
        check_policy = required_check_specs(
            checks, "dependency completion certificate required-check policy"
        )
        check_runs = dependency["required_check_runs"]
        require(isinstance(check_runs, list) and 0 < len(check_runs) <= 16,
                "dependency completion certificate required-check runs are invalid")
        run_specs = required_check_run_specs(
            check_runs, "dependency completion certificate required-check runs"
        )
        require(
            [(name, app_id) for name, app_id, _ in run_specs] == check_policy,
            "dependency completion certificate check runs differ from policy",
        )
    producer = evidence.get("producer")
    if issue_id == "FMV3-M2-01":
        producer_keys = {
            "plan_issue", "repository", "github_issue_number",
            "github_pull_request_number", "merge_sha", "red_commit_sha",
            "red_workflow_run_id", "red_workflow_run_attempt",
            "red_check_runs", "red_job_ids",
            "green_workflow_run_id", "green_workflow_run_attempt",
            "green_check_runs", "green_job_ids",
            "harness_pull_request_number", "harness_merge_sha",
            "harness_workflow_id", "harness_required_check_runs", "harness_ci_run",
            "mutation_runs", "official_review_id", "owner_review_ids",
        }
        require(isinstance(producer, dict)
                and set(producer) == producer_keys
                and producer.get("plan_issue") == "FMV3-M1-06"
                and producer.get("repository") == MODBUS_REPOSITORY
                and type(producer.get("github_issue_number")) is int and producer["github_issue_number"] > 0
                and type(producer.get("github_pull_request_number")) is int and producer["github_pull_request_number"] > 0
                and isinstance(producer.get("merge_sha"), str)
                and re.fullmatch(r"[0-9a-f]{40}", producer["merge_sha"])
                and isinstance(producer.get("red_commit_sha"), str)
                and re.fullmatch(r"[0-9a-f]{40}", producer["red_commit_sha"])
                and type(producer.get("red_workflow_run_id")) is int
                and producer["red_workflow_run_id"] > 0
                and type(producer.get("red_workflow_run_attempt")) is int
                and producer["red_workflow_run_attempt"] > 0
                and type(producer.get("green_workflow_run_id")) is int
                and producer["green_workflow_run_id"] > 0
                and type(producer.get("green_workflow_run_attempt")) is int
                and producer["green_workflow_run_attempt"] > 0
                and isinstance(producer.get("red_check_runs"), list)
                and isinstance(producer.get("red_job_ids"), list)
                and isinstance(producer.get("green_check_runs"), list)
                and isinstance(producer.get("green_job_ids"), list)
                and type(producer.get("harness_pull_request_number")) is int
                and producer["harness_pull_request_number"] > 0
                and isinstance(producer.get("harness_merge_sha"), str)
                and re.fullmatch(r"[0-9a-f]{40}", producer["harness_merge_sha"])
                and type(producer.get("harness_workflow_id")) is int
                and producer["harness_workflow_id"] > 0
                and isinstance(producer.get("harness_required_check_runs"), list)
                and 0 < len(producer["harness_required_check_runs"]) <= 16
                and isinstance(producer.get("harness_ci_run"), dict)
                and isinstance(producer.get("mutation_runs"), list)
                and len(producer["mutation_runs"]) == len(M1_06_MUTATION_CASES)
                and type(producer.get("official_review_id")) is int
                and producer["official_review_id"] > 0
                and isinstance(producer.get("owner_review_ids"), list)
                and len(producer["owner_review_ids"]) == 2
                and len(set(producer["owner_review_ids"])) == 2
                and all(type(review_id) is int and review_id > 0
                        for review_id in producer["owner_review_ids"]),
                "FMV3-M2-01 producer evidence schema mismatch")
        required_check_run_specs(
            producer["harness_required_check_runs"],
            "FMV3-M2-01 harness required-check runs",
        )
        harness_ci_run = producer["harness_ci_run"]
        require(
            set(harness_ci_run) == {
                "workflow_run_id", "workflow_run_attempt", "job_id", "check_run_id",
            }
            and all(
                type(harness_ci_run.get(key)) is int and harness_ci_run[key] > 0
                for key in harness_ci_run
            )
            and any(
                item.get("context") == M1_06_RED_REQUIRED_CHECK
                and item.get("check_run_id") == harness_ci_run["check_run_id"]
                for item in producer["harness_required_check_runs"]
            ),
            "FMV3-M2-01 harness CI run selector is invalid",
        )
        expected_conformance_names = [
            M1_06_RED_GUARD_JOB_NAME, M1_06_CONFORMANCE_JOB_NAME,
        ]
        for phase in ("red", "green"):
            check_specs = required_check_run_specs(
                producer[f"{phase}_check_runs"],
                f"FMV3-M2-01 {phase} check-run selectors",
            )
            require(
                [(name, app_id) for name, app_id, _ in check_specs]
                == [(name, GITHUB_ACTIONS_APP_ID) for name in expected_conformance_names],
                f"FMV3-M2-01 {phase} check-run selectors differ from trusted jobs",
            )
            job_specs = producer[f"{phase}_job_ids"]
            require(
                isinstance(job_specs, list) and len(job_specs) == 2
                and all(
                    isinstance(item, dict) and set(item) == {"name", "job_id"}
                    and item.get("name") == expected_conformance_names[index]
                    and type(item.get("job_id")) is int and item["job_id"] > 0
                    for index, item in enumerate(job_specs)
                )
                and len({item["job_id"] for item in job_specs}) == 2,
                f"FMV3-M2-01 {phase} job selectors are invalid",
            )
        mutation_keys = {
            "case_id", "mutation_commit_sha", "workflow_run_id",
            "workflow_run_attempt", "check_run_id", "job_id",
        }
        mutation_ids: list[str] = []
        mutation_commits: list[str] = []
        mutation_runs: list[int] = []
        mutation_checks: list[int] = []
        mutation_jobs: list[int] = []
        for mutation in producer["mutation_runs"]:
            require(isinstance(mutation, dict) and set(mutation) == mutation_keys
                    and mutation.get("case_id") in M1_06_MUTATION_CASES
                    and isinstance(mutation.get("mutation_commit_sha"), str)
                    and re.fullmatch(r"[0-9a-f]{40}", mutation["mutation_commit_sha"])
                    and type(mutation.get("workflow_run_id")) is int
                    and mutation["workflow_run_id"] > 0
                    and type(mutation.get("workflow_run_attempt")) is int
                    and mutation["workflow_run_attempt"] > 0
                    and type(mutation.get("check_run_id")) is int
                    and mutation["check_run_id"] > 0
                    and type(mutation.get("job_id")) is int
                    and mutation["job_id"] > 0,
                    "FMV3-M2-01 mutation evidence selector schema mismatch")
            mutation_ids.append(mutation["case_id"])
            mutation_commits.append(mutation["mutation_commit_sha"])
            mutation_runs.append(mutation["workflow_run_id"])
            mutation_checks.append(mutation["check_run_id"])
            mutation_jobs.append(mutation["job_id"])
        require(mutation_ids == list(M1_06_MUTATION_CASES)
                and len(set(mutation_commits)) == len(mutation_commits)
                and len(set(mutation_runs)) == len(mutation_runs)
                and len(set(mutation_checks)) == len(mutation_checks)
                and len(set(mutation_jobs)) == len(mutation_jobs),
                "FMV3-M2-01 mutation evidence must be ordered and unique")
    return dependencies, producer


def require_m3_03_completion_artifact(
    repository: str, binding: dict[str, Any],
) -> None:
    artifact = binding.get("completion_artifact")
    require(isinstance(artifact, dict) and set(artifact) == {
        "schema", "head_sha", "head_tree_sha", "disposition", "overlay_packages",
        "package_scan", "tests", "neutral_runtime_proof", "overlay_tdd",
        "workflow_path", "workflow_blob_sha", "workflow_id", "workflow_run_id",
        "workflow_run_attempt", "workflow_job_id", "workflow_check_run_id",
    }, "FMV3-M3-03 completion artifact schema mismatch")
    require(artifact["schema"] == "helianthus.fmv3-m3-03-completion.v2"
            and artifact["head_sha"] == binding["head_sha"]
            and artifact["head_tree_sha"] == binding["head_tree_sha"]
            and artifact["disposition"] in {"STANDARD_ONLY", "OVERLAY_REQUIRED"}
            and isinstance(artifact["overlay_packages"], list)
            and type(artifact["workflow_id"]) is int and artifact["workflow_id"] > 0
            and type(artifact["workflow_run_id"]) is int
            and artifact["workflow_run_id"] > 0
            and type(artifact["workflow_run_attempt"]) is int
            and artifact["workflow_run_attempt"] > 0
            and type(artifact["workflow_job_id"]) is int
            and artifact["workflow_job_id"] > 0
            and type(artifact["workflow_check_run_id"]) is int
            and artifact["workflow_check_run_id"] > 0,
            "FMV3-M3-03 completion artifact identity/disposition mismatch")
    scan = artifact["package_scan"]
    require(isinstance(scan, dict) and set(scan) == {"scope", "result"}
            and scan["scope"] == "fixed_profiles_fronius_namespace"
            and isinstance(scan["result"], list)
            and scan["result"] == artifact["overlay_packages"],
            "FMV3-M3-03 package scan is not exact")
    tests = artifact["tests"]
    expected_tests = {
        "TestFroniusOverlayRejectsTCPConcreteImports",
        "TestFroniusOverlayActivatesThroughNeutralRuntime",
    }
    require(isinstance(tests, list) and len(tests) == 2
            and {item.get("name") for item in tests if isinstance(item, dict)} == expected_tests,
            "FMV3-M3-03 named test evidence is incomplete")
    canonical_test_source = M3_03_PROOF_CONTRACT[artifact["disposition"]]["source_path"]
    require(all(isinstance(item, dict) and item.get("source_path") == canonical_test_source
                for item in tests),
            "FMV3-M3-03 named tests must use the fixed canonical proof source")
    activation_test = next(
        item for item in tests
        if isinstance(item, dict)
        and item.get("name") == "TestFroniusOverlayActivatesThroughNeutralRuntime"
    )
    tree = github_tree_blob_map(repository, binding["head_tree_sha"], "FMV3-M3-03 exact head")
    workflow_path = artifact["workflow_path"]
    workflow_blob_sha = artifact["workflow_blob_sha"]
    workflow_contract = M3_03_WORKFLOW_CONTRACT[artifact["disposition"]]
    require(workflow_path == workflow_contract["workflow_path"]
            and isinstance(workflow_blob_sha, str)
            and re.fullmatch(r"[0-9a-f]{40}", workflow_blob_sha) is not None
            and tree.get(workflow_path) == workflow_blob_sha,
            "FMV3-M3-03 workflow path is not bound to the plan-pinned exact head tree")
    workflow_blob = decode_exact_github_blob(
        github_api(f"repos/{repository}/git/blobs/{workflow_blob_sha}"), workflow_blob_sha,
        "FMV3-M3-03 workflow blob", 1_000_000,
    )
    template_path = Path(__file__).resolve().parent / workflow_contract["template_path"]
    require(template_path.is_file() and not template_path.is_symlink()
            and hashlib.sha256(template_path.read_bytes()).hexdigest()
            == workflow_contract["sha256"]
            and hashlib.sha256(workflow_blob).hexdigest() == workflow_contract["sha256"]
            and workflow_blob == template_path.read_bytes(),
            "FMV3-M3-03 workflow blob does not match the plan-pinned canonical contract")
    try:
        workflow = yaml.safe_load(workflow_blob.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValidationError("FMV3-M3-03 workflow YAML is invalid") from exc
    workflow_jobs = workflow.get("jobs") if isinstance(workflow, dict) else None
    require(isinstance(workflow_jobs, dict),
            "FMV3-M3-03 workflow YAML jobs are invalid")
    require(
        set(workflow) == {"name", True, "permissions", "jobs"}
        and workflow.get("permissions") == {"contents": "read"}
        and set(workflow_jobs) == {"verify"},
        "FMV3-M3-03 workflow top-level permissions or shape is not exact",
    )
    workflow_job = workflow_jobs["verify"]
    require(isinstance(workflow_job, dict)
            and set(workflow_job) == {"runs-on", "steps"}
            and workflow_job["runs-on"] == "ubuntu-24.04"
            and isinstance(workflow_job["steps"], list),
            "FMV3-M3-03 workflow job can skip, redirect, or use a non-hosted runner")
    proof_contract = M3_03_PROOF_CONTRACT[artifact["disposition"]]
    expected_steps = [
        {
            "name": "Checkout bound head",
            "uses": "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
            "with": {
                "ref": "${{ github.event.pull_request.head.sha }}",
                "fetch-depth": 1,
                "persist-credentials": False,
            },
        },
        {
            "name": "Assert bound head and tree",
            "run": 'test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}" && test "$(git rev-parse HEAD^{tree})" = "$(git rev-parse "${{ github.event.pull_request.head.sha }}^{tree}")"',
        },
        {
            "name": M3_03_PREPARE_STEP_NAME,
            "run": (
                f"find {proof_contract['directory']} -maxdepth 1 -type f -name '*_test.go' "
                f"! -name 'fronius_overlay_test.go' -delete && test -f {proof_contract['source_path']}"
            ),
        },
        {
            "name": M3_03_BUILD_STEP_NAME,
            "run": f"go build {proof_contract['build_target']}",
        },
        {
            "name": M3_03_ACTIVATION_STEP_NAME,
            "run": f"go test {proof_contract['test_target']} -run '^TestFroniusOverlayActivatesThroughNeutralRuntime$'",
        },
        {
            "name": M3_03_IMPORT_STEP_NAME,
            "run": f"go test {proof_contract['test_target']} -run '^TestFroniusOverlayRejectsTCPConcreteImports$'",
        },
    ]
    require(workflow_job["steps"] == expected_steps,
            "FMV3-M3-03 workflow step allowlist is not exact")
    overlay_prefix = ("profiles", "fronius")
    derived_packages = sorted({
        PurePosixPath(path).parent.as_posix()
        for path in tree
        if path.endswith(".go") and not path.endswith("_test.go")
        and PurePosixPath(path).parts[:2] == overlay_prefix
    })
    require(scan["result"] == derived_packages,
            "FMV3-M3-03 package scan does not equal the exact-head Fronius Go package set")
    proof_candidate = artifact.get("neutral_runtime_proof")
    proof_candidate_path = (
        proof_candidate.get("source_path") if isinstance(proof_candidate, dict) else None
    )
    require(isinstance(proof_candidate_path, str),
            "FMV3-M3-03 neutral adapter source path is invalid")
    proof_is_test_only = proof_candidate_path.endswith("_test.go")
    if artifact["disposition"] == "STANDARD_ONLY":
        require(proof_is_test_only and proof_candidate_path == proof_contract["source_path"],
                "FMV3-M3-03 STANDARD_ONLY neutral adapter must be test-only")
    else:
        require(not proof_is_test_only
                and PurePosixPath(proof_candidate_path).parts[:2] == overlay_prefix,
                "FMV3-M3-03 OVERLAY_REQUIRED neutral adapter must be production overlay source")
    overlay_implementation_paths = [
        path for path in tree
        if path.endswith(".go") and not path.endswith("_test.go")
        and PurePosixPath(path).parts[:2] == overlay_prefix
        and path != proof_candidate_path
    ]
    for path, blob_sha in tree.items():
        source_path = PurePosixPath(path)
        if not path.endswith(".go") or path.endswith("_test.go"):
            continue
        source_blob = decode_exact_github_blob(
            github_api(f"repos/{repository}/git/blobs/{blob_sha}"), blob_sha,
            f"FMV3-M3-03 production source {path}", 1_000_000,
        )
        try:
            imports = go_import_paths(source_blob.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ValidationError(f"FMV3-M3-03 production source {path} is not UTF-8") from exc
        source_text = source_blob.decode("utf-8")
        is_overlay_source = source_path.parts[:2] == overlay_prefix
        require(
            go_source_path_is_unconditionally_build_eligible(path)
            and not re.search(
                r"(?m)^\s*//\s*(?:go:build|\+build)\b", source_text,
            ),
            f"FMV3-M3-03 production source {path} is build-excluded",
        )
        require(
            is_overlay_source or "fronius" not in source_text.lower(),
            "FMV3-M3-03 Fronius production source escapes profiles/fronius namespace",
        )
        if is_overlay_source:
            require(
                imports_are_transport_neutral(imports, test_source=False)
                and not any(is_tcp_concrete_import(import_path) for import_path in imports),
                f"FMV3-M3-03 production source {path} imports a TCP-concrete dependency "
                "or a dependency outside the sealed transport-neutral allowlist",
            )
            production_code = go_code_projection(source_text)
            require(
                not re.search(r"(?m)^\s*func\s+(?:\([^\n]*\)\s*)?init\s*\(", production_code)
                and not re.search(r"\b(?:neutralRuntimeProbeError|neutralRuntimeNoTCP)\b", production_code),
                f"FMV3-M3-03 overlay production source {path} has test-only initialization or symbols",
            )
    pr = github_api(
        f"repos/{repository}/pulls/{binding['github_pull_request_number']}"
    )
    base_sha = pr.get("base", {}).get("sha") if isinstance(pr, dict) else None
    require(isinstance(pr, dict)
            and pr.get("head", {}).get("sha") == binding["head_sha"]
            and isinstance(base_sha, str)
            and re.fullmatch(r"[0-9a-f]{40}", base_sha) is not None,
            "FMV3-M3-03 pull-request base is invalid")
    base_commit = github_api(f"repos/{repository}/git/commits/{base_sha}")
    base_tree_sha = (
        base_commit.get("tree", {}).get("sha")
        if isinstance(base_commit, dict) else None
    )
    require(isinstance(base_tree_sha, str)
            and re.fullmatch(r"[0-9a-f]{40}", base_tree_sha) is not None,
            "FMV3-M3-03 base tree is invalid")
    base_tree = github_tree_blob_map(
        repository, base_tree_sha, "FMV3-M3-03 base tree"
    )
    changed_paths = {
        path for path in set(base_tree) | set(tree)
        if base_tree.get(path) != tree.get(path)
    }
    def m3_03_evidence_path(path: str) -> bool:
        parts = PurePosixPath(path).parts
        return (
            path == workflow_path
            or path.endswith("_test.go")
            or "testdata" in parts
            or "fixtures" in parts
            or parts[:1] == ("docs",)
            or parts[:2] == (".github", "fmv3")
        )
    if artifact["disposition"] == "STANDARD_ONLY":
        require(derived_packages == [] and artifact["overlay_tdd"] is None,
                "FMV3-M3-03 STANDARD_ONLY must prove an empty overlay and no overlay TDD evidence")
        require(all(m3_03_evidence_path(path) for path in changed_paths),
                "FMV3-M3-03 STANDARD_ONLY changes production implementation")
    else:
        overlay_changed_production = {
            path for path in changed_paths
            if PurePosixPath(path).parts[:2] == overlay_prefix
            and path.endswith(".go") and not path.endswith("_test.go")
        }
        require(
            overlay_changed_production
            and all(
                m3_03_evidence_path(path)
                or path in overlay_changed_production
                for path in changed_paths
            ),
            "FMV3-M3-03 OVERLAY_REQUIRED changes production outside profiles/fronius",
        )
        tdd = artifact["overlay_tdd"]
        require(derived_packages and overlay_implementation_paths
                and isinstance(tdd, dict) and set(tdd) == {
            "red_commit_sha", "red_workflow_run_id", "red_workflow_run_attempt",
            "red_job_id", "red_check_run_id", "red_test_name",
        } and re.fullmatch(r"[0-9a-f]{40}", str(tdd.get("red_commit_sha"))) is not None
            and tdd["red_commit_sha"] != binding["head_sha"]
            and type(tdd.get("red_workflow_run_id")) is int
            and tdd["red_workflow_run_id"] > 0
            and type(tdd.get("red_workflow_run_attempt")) is int
            and tdd["red_workflow_run_attempt"] > 0
            and type(tdd.get("red_job_id")) is int
            and tdd["red_job_id"] > 0
            and type(tdd.get("red_check_run_id")) is int
            and tdd["red_check_run_id"] > 0
            and tdd.get("red_test_name") == "TestFroniusOverlayActivatesThroughNeutralRuntime",
            "FMV3-M3-03 OVERLAY_REQUIRED lacks exact RED evidence or a production overlay")
        red_sha = tdd["red_commit_sha"]
        red_commit = github_api(f"repos/{repository}/commits/{red_sha}")
        red_compare = github_api(f"repos/{repository}/compare/{red_sha}...{binding['head_sha']}")
        red_run = github_api(
            f"repos/{repository}/actions/runs/{tdd['red_workflow_run_id']}"
            f"/attempts/{tdd['red_workflow_run_attempt']}"
        )
        red_prs = red_run.get("pull_requests") if isinstance(red_run, dict) else None
        red_tree_sha = (
            red_commit.get("commit", {}).get("tree", {}).get("sha")
            if isinstance(red_commit, dict) else None
        )
        require(isinstance(red_commit, dict) and red_commit.get("sha") == red_sha
                and red_commit.get("commit", {}).get("message")
                == "test(fronius): RED transport-neutral overlay"
                and isinstance(red_tree_sha, str)
                and re.fullmatch(r"[0-9a-f]{40}", red_tree_sha) is not None
                and isinstance(red_commit.get("parents"), list)
                and len(red_commit["parents"]) == 1
                and isinstance(red_commit.get("files"), list) and red_commit["files"]
                and all(isinstance(row, dict) and isinstance(row.get("filename"), str)
                        and (row["filename"].endswith("_test.go")
                             or "testdata" in PurePosixPath(row["filename"]).parts
                             or "fixtures" in PurePosixPath(row["filename"]).parts)
                        for row in red_commit["files"])
                and any(row["filename"].endswith("_test.go") for row in red_commit["files"]),
                "FMV3-M3-03 RED commit is not exact test-only evidence")
        red_tree = github_tree_blob_map(repository, red_tree_sha, "FMV3-M3-03 RED tree")
        red_parent_sha = red_commit["parents"][0].get("sha")
        require(isinstance(red_parent_sha, str)
                and re.fullmatch(r"[0-9a-f]{40}", red_parent_sha) is not None
                and red_parent_sha == base_sha,
                "FMV3-M3-03 RED parent SHA is not the exact PR base")
        red_parent_commit = github_api(
            f"repos/{repository}/git/commits/{red_parent_sha}"
        )
        red_parent_tree_sha = (
            red_parent_commit.get("tree", {}).get("sha")
            if isinstance(red_parent_commit, dict) else None
        )
        require(isinstance(red_parent_tree_sha, str)
                and re.fullmatch(r"[0-9a-f]{40}", red_parent_tree_sha) is not None
                and red_parent_tree_sha == base_tree_sha,
                "FMV3-M3-03 RED parent tree is not the exact PR base tree")
        red_parent_tree = github_tree_blob_map(
            repository, red_parent_tree_sha, "FMV3-M3-03 RED parent tree"
        )
        red_changed_paths = {
            path for path in set(red_parent_tree) | set(red_tree)
            if red_parent_tree.get(path) != red_tree.get(path)
        }
        require(red_changed_paths
                and all(path.endswith("_test.go")
                        or "testdata" in PurePosixPath(path).parts
                        or "fixtures" in PurePosixPath(path).parts
                        for path in red_changed_paths)
                and any(path.endswith("_test.go") for path in red_changed_paths),
                "FMV3-M3-03 RED tree diff is not complete test-only evidence")
        require(
            red_tree.get(artifact["workflow_path"]) == artifact["workflow_blob_sha"],
            "FMV3-M3-03 RED workflow blob differs from the declared exact workflow",
        )
        canonical_test_blob_sha = tree.get(canonical_test_source)
        require(
            isinstance(canonical_test_blob_sha, str)
            and red_tree.get(canonical_test_source) == canonical_test_blob_sha
            and all(item.get("source_blob_sha") == canonical_test_blob_sha for item in tests),
            "FMV3-M3-03 RED canonical test source blob differs from the exact GREEN source",
        )
        require(isinstance(red_compare, dict) and red_compare.get("status") == "ahead"
                and red_compare.get("merge_base_commit", {}).get("sha") == red_sha,
                "FMV3-M3-03 RED commit is not an ancestor of the implementation head")
        require(isinstance(red_run, dict) and red_run.get("id") == tdd["red_workflow_run_id"]
                and red_run.get("run_attempt") == tdd["red_workflow_run_attempt"]
                and red_run.get("workflow_id") == artifact["workflow_id"]
                and red_run.get("path") == artifact["workflow_path"]
                and red_run.get("event") == "pull_request" and red_run.get("head_sha") == red_sha
                and github_repository_identity(red_run.get("head_repository"), repository)
                and red_run.get("status") == "completed" and red_run.get("conclusion") == "failure"
                and isinstance(red_prs, list) and len(red_prs) == 1
                and red_prs[0].get("number") == binding["github_pull_request_number"]
                and red_prs[0].get("base", {}).get("ref") == "main"
                and github_repository_identity(red_prs[0].get("base", {}).get("repo"), repository)
                and github_repository_identity(red_prs[0].get("head", {}).get("repo"), repository),
                "FMV3-M3-03 RED workflow evidence is invalid")
        red_jobs = github_paginated_object_rows(
            f"repos/{repository}/actions/runs/{tdd['red_workflow_run_id']}"
            f"/attempts/{tdd['red_workflow_run_attempt']}/jobs", "jobs",
            "FMV3-M3-03 RED workflow jobs",
        )
        selected_red_jobs = [
            job for job in red_jobs
            if isinstance(job, dict)
            and job.get("id") == tdd["red_job_id"]
            and job.get("name") == activation_test.get("job_name")
        ]
        require(len(selected_red_jobs) == 1
                and selected_red_jobs[0].get("head_sha") == red_sha
                and selected_red_jobs[0].get("status") == "completed"
                and selected_red_jobs[0].get("conclusion") == "failure"
                and selected_red_jobs[0].get("check_run_url") == (
                    f"https://api.github.com/repos/{repository}/check-runs/"
                    f"{tdd['red_check_run_id']}"
                )
                and sum(
                    isinstance(step, dict)
                    and step.get("name") == M3_03_PREPARE_STEP_NAME
                    and step.get("conclusion") == "success"
                    for step in selected_red_jobs[0].get("steps", [])
                ) == 1
                and sum(
                    isinstance(step, dict)
                    and step.get("name") == M3_03_BUILD_STEP_NAME
                    and step.get("conclusion") == "success"
                    for step in selected_red_jobs[0].get("steps", [])
                ) == 1
                and sum(
                    isinstance(step, dict)
                    and step.get("name") == M3_03_ACTIVATION_STEP_NAME
                    and step.get("conclusion") == "failure"
                    for step in selected_red_jobs[0].get("steps", [])
                ) == 1
                and not any(
                    isinstance(step, dict)
                    and step.get("name") == M3_03_IMPORT_STEP_NAME
                    and step.get("conclusion") == "success"
                    for step in selected_red_jobs[0].get("steps", [])
                ),
                "FMV3-M3-03 RED workflow lacks the intended failing neutral activation test")

    proof = artifact["neutral_runtime_proof"]
    require(isinstance(proof, dict) and set(proof) == {
        "source_path", "source_blob_sha", "interface_symbol", "activation_symbol",
    } and proof["interface_symbol"] == "NeutralRuntime"
        and proof["activation_symbol"] == "activateFroniusProfile"
        and isinstance(proof["source_path"], str)
        and proof["source_path"].endswith(".go")
        and tree.get(proof["source_path"]) == proof["source_blob_sha"],
        "FMV3-M3-03 neutral runtime proof is not the exact bound source")
    proof_blob = decode_exact_github_blob(
        github_api(f"repos/{repository}/git/blobs/{proof['source_blob_sha']}"),
        proof["source_blob_sha"], "FMV3-M3-03 neutral runtime source", 1_000_000,
    )
    proof_code = go_code_projection(proof_blob.decode("utf-8"))
    normalized_proof = " ".join(proof_code.split())
    minimal_neutral_adapter = (
        r"package\s+[A-Za-z_][A-Za-z0-9_]*\s+"
        r"type\s+NeutralRuntime\s+interface\s*\{\s*"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*error\s*\}\s*"
        r"func\s+activateFroniusProfile\s*\(\s*runtime\s+NeutralRuntime\s*\)\s*error\s*\{\s*"
        r"return\s+runtime\.([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*\}"
    )
    proof_match = re.search(minimal_neutral_adapter, normalized_proof)
    if proof_is_test_only:
        interface_match = re.search(
            r"type\s+NeutralRuntime\s+interface\s*\{\s*"
            r"([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*error\s*\}",
            normalized_proof,
        )
        activation_match = re.search(
            r"func\s+activateFroniusProfile\s*\(\s*runtime\s+NeutralRuntime\s*\)\s*error\s*\{\s*"
            r"return\s+runtime\.([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*\}",
            normalized_proof,
        )
        require(interface_match is not None and activation_match is not None
                and interface_match.group(1) == activation_match.group(1),
                "FMV3-M3-03 test-only activation is not the exact minimal neutral adapter")
    else:
        require(proof_match is not None and proof_match.group(1) == proof_match.group(2)
                and re.fullmatch(minimal_neutral_adapter, normalized_proof) is not None
                and go_import_paths(proof_blob.decode("utf-8")) == set(),
                "FMV3-M3-03 production activation is not the exact minimal neutral adapter")
    proof_package_match = re.match(
        r"^\s*package\s+([A-Za-z_][A-Za-z0-9_]*)\b", proof_code,
    )
    require(proof_package_match is not None,
            "FMV3-M3-03 neutral runtime proof package is invalid")
    proof_package = proof_package_match.group(1)
    require(proof_package == ("fronius" if artifact["disposition"] == "OVERLAY_REQUIRED" else "registry"),
            "FMV3-M3-03 neutral runtime proof package is not the fixed proof package")
    proof_directory = PurePosixPath(proof["source_path"]).parent.as_posix()
    expected_command_target = proof_contract["test_target"]
    named_test_source_blobs: dict[str, str] = {}
    if proof_is_test_only:
        named_test_source_blobs[proof["source_path"]] = proof["source_blob_sha"]
        require(
            not re.search(r"(?m)^func\s+(?:\([^\n]*\)\s*)?init\s*\(", proof_code)
            and not re.search(r"(?m)^func\s+TestMain\s*\(", proof_code),
            "FMV3-M3-03 artifact-named test source declares init or TestMain",
        )
    run = github_api(
        f"repos/{repository}/actions/runs/{artifact['workflow_run_id']}"
        f"/attempts/{artifact['workflow_run_attempt']}"
    )
    run_prs = run.get("pull_requests") if isinstance(run, dict) else None
    require(isinstance(run, dict) and run.get("id") == artifact["workflow_run_id"]
            and run.get("run_attempt") == artifact["workflow_run_attempt"]
            and run.get("workflow_id") == artifact["workflow_id"]
            and run.get("path") == workflow_path and run.get("event") == "pull_request"
            and run.get("head_sha") == binding["head_sha"]
            and github_repository_identity(run.get("head_repository"), repository)
            and run.get("status") == "completed" and run.get("conclusion") == "success"
            and isinstance(run_prs, list) and len(run_prs) == 1
            and run_prs[0].get("number") == binding["github_pull_request_number"]
            and run_prs[0].get("base", {}).get("ref") == "main"
            and github_repository_identity(run_prs[0].get("base", {}).get("repo"), repository)
            and run_prs[0].get("head", {}).get("sha") == binding["head_sha"]
            and github_repository_identity(run_prs[0].get("head", {}).get("repo"), repository),
            "FMV3-M3-03 exact-head workflow evidence is invalid")
    jobs = github_paginated_object_rows(
        f"repos/{repository}/actions/runs/{artifact['workflow_run_id']}"
        f"/attempts/{artifact['workflow_run_attempt']}/jobs", "jobs",
        "FMV3-M3-03 exact-head workflow jobs",
    )
    selected_jobs = [
        job for job in jobs
        if isinstance(job, dict)
        and job.get("id") == artifact["workflow_job_id"]
        and job.get("name") == activation_test.get("job_name")
    ]
    require(len(selected_jobs) == 1
            and selected_jobs[0].get("head_sha") == binding["head_sha"]
            and selected_jobs[0].get("status") == "completed"
            and selected_jobs[0].get("conclusion") == "success"
            and selected_jobs[0].get("check_run_url") == (
                f"https://api.github.com/repos/{repository}/check-runs/"
                f"{artifact['workflow_check_run_id']}"
            ),
            "FMV3-M3-03 exact-head workflow job identity or outcome mismatch")
    for item in tests:
        require(isinstance(item, dict) and set(item) == {
            "name", "source_path", "source_blob_sha", "job_name", "step_name"},
            "FMV3-M3-03 named test schema mismatch")
        expected_step_name = (
            M3_03_ACTIVATION_STEP_NAME
            if item["name"] == "TestFroniusOverlayActivatesThroughNeutralRuntime"
            else M3_03_IMPORT_STEP_NAME
        )
        require(item["source_path"] == proof_contract["source_path"]
                and item["step_name"] == expected_step_name,
                "FMV3-M3-03 named test is not bound to its fixed canonical source and step")
        require(tree.get(item["source_path"]) == item["source_blob_sha"],
                "FMV3-M3-03 named test blob is not bound to the exact head tree")
        source_blob = decode_exact_github_blob(
            github_api(f"repos/{repository}/git/blobs/{item['source_blob_sha']}"),
            item["source_blob_sha"], f"FMV3-M3-03 source blob for {item['name']}", 1_000_000,
        )
        source_text = source_blob.decode("utf-8")
        source_code = go_code_projection(source_text)
        require(
            not re.search(r"(?m)^func\s+(?:\([^\n]*\)\s*)?init\s*\(", source_code)
            and not re.search(r"(?m)^func\s+TestMain\s*\(", source_code),
            "FMV3-M3-03 artifact-named test source declares init or TestMain",
        )
        previous_blob_sha = named_test_source_blobs.setdefault(
            item["source_path"], item["source_blob_sha"],
        )
        require(previous_blob_sha == item["source_blob_sha"],
                "FMV3-M3-03 artifact names one candidate test source with conflicting blobs")
        test_directory = PurePosixPath(item["source_path"]).parent.as_posix()
        test_package_match = re.match(
            r"^\s*package\s+([A-Za-z_][A-Za-z0-9_]*)\b",
            go_code_projection(source_text),
        )
        require(test_directory == proof_directory
                and test_package_match is not None
                and test_package_match.group(1) == proof_package,
                "FMV3-M3-03 named test is not in the exact neutral-proof package/directory")
        if item["source_path"] != proof["source_path"]:
            for symbol in (
                "NeutralRuntime", "activateFroniusProfile",
            ):
                require(re.search(
                    rf"(?m)^\s*(?:type|func|var|const)\s+{re.escape(symbol)}\b",
                    go_code_projection(source_text),
                ) is None,
                        f"FMV3-M3-03 named test locally redeclares bound symbol {symbol}")
        require(item["source_path"].endswith("_test.go")
                and go_source_path_is_unconditionally_build_eligible(item["source_path"])
                and not re.search(r"(?m)^\s*//\s*(?:go:build|\+build)\b", source_text)
                and not any(
                    f"{'/'.join(PurePosixPath(item['source_path']).parts[:index])}/go.mod"
                    in tree
                    for index in range(1, len(PurePosixPath(item["source_path"]).parts))
                ),
                "FMV3-M3-03 named test is excluded or outside the root module")
        test_imports = go_import_paths(source_text)
        require(
            imports_are_transport_neutral(test_imports, test_source=True)
            and not any(is_tcp_concrete_import(path) for path in test_imports),
            "FMV3-M3-03 named test source imports a TCP-concrete dependency "
            "or a dependency outside the sealed transport-neutral allowlist",
        )
        require_m3_03_runtime_import_scanner(source_text, test_imports)
        require(re.search(
            rf"(?m)^func\s+{re.escape(item['name'])}\s*\(\s*t\s+\*testing\.T\s*\)\s*\{{",
            go_source_without_comments(source_text),
        ) is not None, f"FMV3-M3-03 named test {item['name']} is not a proper Go test declaration")
        projected_source = go_code_projection(source_text)
        comment_free_source = go_source_without_comments(source_text)
        declaration = re.compile(
            rf"(?m)^func\s+{re.escape(item['name'])}\s*"
            r"\(\s*t\s+\*testing\.T\s*\)\s*\{"
        )
        declarations = list(declaration.finditer(projected_source))
        require(len(declarations) == 1,
                f"FMV3-M3-03 named test {item['name']} is not a unique proper Go test declaration")
        body_start = declarations[0].end() - 1
        depth = 0
        body_end = None
        for index in range(body_start, len(projected_source)):
            if projected_source[index] == "{":
                depth += 1
            elif projected_source[index] == "}":
                depth -= 1
                if depth == 0:
                    body_end = index
                    break
        require(body_end is not None,
                f"FMV3-M3-03 named test {item['name']} has no closing brace")
        body = comment_free_source[body_start + 1:body_end]
        require(body.strip()
                and re.search(r"\bt\.(?:Fatal|Fatalf|Error|Errorf|Fail|FailNow)\s*\(", body),
                f"FMV3-M3-03 named test {item['name']} is empty, assertion-free, or semantic no-op")
        normalized_body = " ".join(body.split())
        if item["name"] == "TestFroniusOverlayRejectsTCPConcreteImports":
            require(normalized_body == (
                "packages, err := froniusOverlayProductionPackages() "
                "if err != nil { t.Fatal(err) } "
                "if offending := hasTCPConcreteImport(packages); offending != \"\" "
                "{ t.Fatal(offending) }"
            ), "FMV3-M3-03 import-boundary test body is not the closed canonical proof")
        else:
            code = go_source_without_comments(source_text)
            require(re.search(r"(?m)^type\s+neutralRuntimeNoTCP\s+struct\s*\{\s*\}", code)
                    and re.search(
                        r"(?m)^var\s+neutralRuntimeProbeError\s*=\s*errors\.New\s*\(", code
                    )
                    and re.search(
                        r"(?ms)^func\s*\(\s*\*neutralRuntimeNoTCP\s*\)\s*"
                        r"[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)\s*error\s*\{"
                        r"\s*return\s+neutralRuntimeProbeError\s*\}", code
                    )
                    and re.search(
                        r"(?m)^var\s+_\s+NeutralRuntime\s*=\s*\(\*neutralRuntimeNoTCP\)\(nil\)",
                        code,
                    ) and normalized_body == (
                        "runtime := neutralRuntimeNoTCP{} "
                        "err := activateFroniusProfile(&runtime) "
                        "if !errors.Is(err, neutralRuntimeProbeError) { t.Fatal(err) }"
                    ), "FMV3-M3-03 activation test body is not the closed canonical proof")
    activation_command = (
        f"go test {expected_command_target} -run "
        "'^TestFroniusOverlayActivatesThroughNeutralRuntime$'"
    )
    import_command = (
        f"go test {expected_command_target} -run "
        "'^TestFroniusOverlayRejectsTCPConcreteImports$'"
    )
    require(
        all(item["job_name"] == "verify" for item in tests)
        and workflow_job["steps"][-2].get("name") == M3_03_ACTIVATION_STEP_NAME
        and workflow_job["steps"][-2].get("run", "").strip() == activation_command
        and workflow_job["steps"][-1].get("name") == M3_03_IMPORT_STEP_NAME
        and workflow_job["steps"][-1].get("run", "").strip() == import_command
        and all(not ({"if", "continue-on-error", "working-directory", "shell", "env"}
                     & set(step)) for step in workflow_job["steps"][2:]),
        "FMV3-M3-03 workflow must isolate, build, then execute activation before import",
    )
    green_steps = selected_jobs[0].get("steps", [])
    for step_name in (
        M3_03_PREPARE_STEP_NAME, M3_03_BUILD_STEP_NAME,
        M3_03_ACTIVATION_STEP_NAME, M3_03_IMPORT_STEP_NAME,
    ):
        require(sum(
            isinstance(step, dict) and step.get("name") == step_name
            and step.get("conclusion") == "success"
            for step in green_steps
        ) == 1, f"FMV3-M3-03 GREEN workflow lacks successful {step_name}")


def required_check_specs(value: Any, label: str) -> list[tuple[str, int]]:
    require(isinstance(value, list) and value, f"{label} must be a nonempty list")
    specs: list[tuple[str, int]] = []
    for item in value:
        require(isinstance(item, dict) and set(item) == {"context", "app_id"},
                f"{label} check entry schema mismatch")
        context, app_id = item.get("context"), item.get("app_id")
        require(isinstance(context, str) and 0 < len(context.encode("utf-8")) <= 256
                and type(app_id) is int and app_id > 0,
                f"{label} contains an invalid context or app_id")
        specs.append((context, app_id))
    require(len(specs) == len(set(specs)), f"{label} contains duplicate checks")
    return specs


def required_check_run_specs(value: Any, label: str) -> list[tuple[str, int, int]]:
    require(isinstance(value, list) and value, f"{label} must be a nonempty list")
    specs: list[tuple[str, int, int]] = []
    for item in value:
        require(
            isinstance(item, dict)
            and set(item) == {"context", "app_id", "check_run_id"},
            f"{label} check-run entry schema mismatch",
        )
        context, app_id, check_run_id = (
            item.get("context"), item.get("app_id"), item.get("check_run_id")
        )
        require(
            isinstance(context, str) and 0 < len(context.encode("utf-8")) <= 256
            and type(app_id) is int and app_id > 0
            and type(check_run_id) is int and check_run_id > 0,
            f"{label} contains an invalid context, app_id, or check_run_id",
        )
        specs.append((context, app_id, check_run_id))
    require(
        len(specs) == len(set(specs))
        and len({item[0:2] for item in specs}) == len(specs)
        and len({item[2] for item in specs}) == len(specs),
        f"{label} contains duplicate check identities",
    )
    return specs


def live_required_check_specs(protection: Any, label: str) -> list[tuple[str, int]]:
    require(isinstance(protection, dict), f"{label} response is invalid")
    checks = protection.get("checks")
    contexts = protection.get("contexts")
    require(isinstance(checks, list) and checks,
            f"{label} app-bound checks are unavailable")
    value: list[dict[str, Any]] = []
    for check in checks:
        require(isinstance(check, dict), f"{label} check entry is invalid")
        value.append({"context": check.get("context"), "app_id": check.get("app_id")})
    specs = required_check_specs(value, label)
    require(
        isinstance(contexts, list)
        and all(isinstance(context, str) for context in contexts)
        and len(contexts) == len(set(contexts))
        and set(contexts) <= {context for context, _ in specs},
        f"{label} contains a legacy context without an app-bound check",
    )
    return specs


def require_exact_head_checks(
    repository: str,
    head_sha: str,
    expected: list[Any],
    label: str,
    *,
    completed_before: datetime | None = None,
    bound_runs: list[Any] | None = None,
) -> list[dict[str, Any]]:
    rows = (
        github_all_check_runs(repository, head_sha, f"{label} exact-head check runs")
        if completed_before is not None or bound_runs is not None
        else github_latest_check_runs(repository, head_sha, f"{label} exact-head check runs")
    )
    policy = required_check_specs(expected, f"{label} required-check policy")
    run_specs = (
        required_check_run_specs(bound_runs, f"{label} bound required-check runs")
        if bound_runs is not None else None
    )
    if run_specs is not None:
        require(
            [(name, app_id) for name, app_id, _ in run_specs] == policy,
            f"{label} bound check runs differ from the required-check policy",
        )
    matched: list[dict[str, Any]] = []
    for index, (name, app_id) in enumerate(policy):
        check_run_id = run_specs[index][2] if run_specs is not None else None
        matching = [row for row in rows if isinstance(row, dict)
                    and row.get("name") == name
                    and row.get("head_sha") == head_sha
                    and isinstance(row.get("app"), dict)
                    and row["app"].get("id") == app_id
                    and (check_run_id is None or row.get("id") == check_run_id)]
        require(len(matching) == 1 and matching[0].get("status") == "completed"
                and matching[0].get("conclusion") == "success",
                f"{label} exact-head required check failed: {name}@{app_id}")
        if completed_before is not None:
            completed_at = parse_github_time(
                matching[0].get("completed_at"), f"{label} {name}@{app_id} completed_at"
            )
            require(
                completed_at < completed_before,
                f"{label} required check completed at or after merge: {name}@{app_id}",
            )
        matched.append(matching[0])
    return matched


def issue_spec_projection(issue: dict[str, Any]) -> dict[str, Any]:
    require(set(ISSUE_SPEC_FIELDS) <= set(issue),
            "anchored issue is missing issue-spec fields")
    return {key: issue[key] for key in ISSUE_SPEC_FIELDS}


def issue_spec_digest(issue: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        issue_spec_projection(issue), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")).hexdigest()


def issue_spec_marker(digest: str) -> str:
    return f"<!-- {ISSUE_SPEC_MARKER_PREFIX}:{digest} -->"


def issue_spec_title(issue: dict[str, Any]) -> str:
    title = f"{issue['id']}: {issue['what']}"
    require(len(title.encode("utf-8")) <= 256,
            f"{issue['id']} anchored issue title exceeds GitHub bound")
    return title


def pull_request_body_closing_refs(body: str) -> list[str]:
    return re.findall(
        r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+"
        r"((?:https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/\d+)"
        r"|(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+)|(?:#\d+))\b",
        body,
    )


def require_pull_request_completion(plan_issue: str, binding: dict[str, Any],
                                    *, dynamic_policy: bool,
                                    issue_spec: dict[str, Any] | None = None) -> None:
    repository = binding["repository"]
    issue_number = binding["github_issue_number"]
    pr_number = binding["github_pull_request_number"]
    merge_sha = binding["merge_sha"]
    issue = github_api(f"repos/{repository}/issues/{issue_number}")
    pr = github_api(f"repos/{repository}/pulls/{pr_number}")
    head_commit = github_api(f"repos/{repository}/git/commits/{binding['head_sha']}")
    merge_commit = github_api(f"repos/{repository}/git/commits/{merge_sha}")
    seed = binding.get("bootstrap_seed")
    seed_commit = (
        github_api(f"repos/{repository}/git/commits/{seed['commit_sha']}")
        if isinstance(seed, dict) else None
    )
    main_sha = canonical_main_sha(repository)
    compare = github_api(f"repos/{repository}/compare/{merge_sha}...{main_sha}")
    timeline = github_paginated_list(
        f"repos/{repository}/issues/{issue_number}/timeline",
        f"dependency {plan_issue} issue timeline",
    )
    label = f"dependency {plan_issue}"
    if dynamic_policy:
        require(isinstance(issue_spec, dict) and issue_spec.get("id") == plan_issue,
                f"{label} anchored issue spec is absent")
        expected_spec_digest = issue_spec_digest(issue_spec)
        expected_title = issue_spec_title(issue_spec)
        marker = issue_spec_marker(expected_spec_digest)
        require(binding.get("issue_spec_sha256") == expected_spec_digest,
                f"{label} certificate issue spec digest differs from anchor")
    else:
        expected_title = binding["issue_title"]
        marker = None
    require(isinstance(issue, dict) and issue.get("number") == issue_number
            and issue.get("repository_url") == f"https://api.github.com/repos/{repository}"
            and issue.get("state") == "closed" and not issue.get("pull_request")
            and issue.get("title") == expected_title
            and (marker is None or (
                isinstance(issue.get("body"), str)
                and issue["body"].count(marker) == 1
            )),
            f"{label} issue identity/title/closure mismatch")
    require(isinstance(pr, dict) and pr.get("number") == pr_number
            and pr.get("title") == (expected_title if dynamic_policy
                                    else binding["pull_request_title"])
            and pr.get("state") == "closed" and pr.get("merged") is True
            and pr.get("merge_commit_sha") == merge_sha
            and pr.get("head", {}).get("sha") == binding["head_sha"]
            and isinstance(pr.get("head", {}).get("ref"), str)
            and re.fullmatch(
                rf"issue/{issue_number}-[a-z0-9]+(?:-[a-z0-9]+)*",
                pr["head"]["ref"],
            ) is not None
            and pr.get("head", {}).get("repo", {}).get("full_name") == repository
            and pr.get("base", {}).get("ref") == "main"
            and pr.get("base", {}).get("repo", {}).get("full_name") == repository,
            f"{label} wrong or unmerged issue/PR binding")
    issue_created_at = parse_github_time(
        issue.get("created_at"), f"{label} issue created_at"
    )
    issue_closed_at = parse_github_time(
        issue.get("closed_at"), f"{label} issue closed_at"
    )
    pr_created_at = parse_github_time(pr.get("created_at"), f"{label} PR created_at")
    pr_merged_at = parse_github_time(pr.get("merged_at"), f"{label} PR merged_at")
    require(
        issue_created_at <= pr_created_at <= pr_merged_at <= issue_closed_at,
        f"{label} selected PR interval is outside the selected issue interval",
    )
    if isinstance(seed, dict):
        require(
            set(seed) == {"commit_sha", "tree_sha", "parents", "message"}
            and pr.get("base", {}).get("sha") == seed.get("commit_sha")
            and isinstance(seed_commit, dict)
            and seed_commit.get("sha") == seed.get("commit_sha")
            and seed_commit.get("tree", {}).get("sha") == seed.get("tree_sha")
            and seed_commit.get("parents") == seed.get("parents") == []
            and seed_commit.get("message") == seed.get("message"),
            f"{label} destination initialization seed is not the exact empty-tree root",
        )
    require(isinstance(pr.get("body"), str)
            and re.search(rf"(?im)^\s*(?:[-*]\s*)?(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#{issue_number}\s*[.]?\s*$", pr["body"]),
            f"{label} PR does not close the exact issue")
    require_issue_closed_by_pull_request(
        repository, issue_number, issue, pr_number, pr, label,
    )
    require(isinstance(head_commit, dict) and head_commit.get("sha") == binding["head_sha"]
            and head_commit.get("tree", {}).get("sha") == binding["head_tree_sha"],
            f"{label} head commit tree mismatch")
    require(isinstance(merge_commit, dict) and merge_commit.get("sha") == merge_sha
            and merge_commit.get("tree", {}).get("sha") == binding["head_tree_sha"]
            and isinstance(merge_commit.get("parents"), list)
            and len(merge_commit["parents"]) == 1
            and merge_commit["parents"][0].get("sha") == pr.get("base", {}).get("sha"),
            f"{label} squash tree/topology mismatch")
    require(isinstance(compare, dict) and compare.get("status") in {"ahead", "identical"}
            and compare.get("merge_base_commit", {}).get("sha") == merge_sha,
            f"{label} merge is not on canonical main")
    require(any(
        isinstance(event, dict) and event.get("event") == "cross-referenced"
        and event.get("source", {}).get("issue", {}).get("number") == pr_number
        and event.get("source", {}).get("issue", {}).get("pull_request", {}).get("url")
        == f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
        and event.get("source", {}).get("issue", {}).get("pull_request", {}).get("merged_at")
        == pr.get("merged_at")
        for event in timeline), f"{label} PR/issue timeline relation is absent")
    checks = binding["required_checks"]
    if dynamic_policy:
        policy = github_api(f"repos/{repository}/branches/main/protection/required_status_checks")
        live_policy = set(live_required_check_specs(policy, f"{label} live required-check policy"))
        expected_policy = set(required_check_specs(checks, f"{label} certificate required-check policy"))
        require(live_policy == expected_policy,
                f"{label} required-check policy is stale or incomplete")
    require_exact_head_checks(
        repository,
        binding["head_sha"],
        checks,
        label,
        completed_before=pr_merged_at,
        bound_runs=binding["required_check_runs"],
    )
    require_plan_owned_repository_mutex(
        repository, issue_number, pr_number, completion=True,
    )


def require_plan_owned_repository_mutex(
    repository: str,
    selected_issue_number: int,
    selected_pr_number: int,
    *,
    completion: bool,
    selected_issue_title: str | None = None,
    selected_issue_marker: str | None = None,
) -> None:
    """Fail closed on concurrent repository work, with bounded paginated history."""
    issues = github_paginated_list(
        f"repos/{repository}/issues?state=all&sort=created&direction=asc",
        f"{repository} issue history",
    )
    repository_issues = [
        row for row in issues
        if isinstance(row, dict)
        and not row.get("pull_request")
    ]
    active_issues = [row for row in repository_issues if row.get("state") == "open"]
    require(len(active_issues) <= 1, f"{repository} has concurrent active repository issues")
    if not completion:
        require(len(active_issues) == 1,
                f"{repository} exact selected issue is not open")
        selected_issue = active_issues[0]
        require(selected_issue.get("number") == selected_issue_number
                and selected_issue.get("title") == selected_issue_title
                and isinstance(selected_issue.get("body"), str)
                and selected_issue["body"].count(str(selected_issue_marker)) == 1,
                f"{repository} active repository issue is not the exact anchored selected issue")
    if completion:
        issue_intervals: list[tuple[int, datetime, datetime | None]] = []
        for row in repository_issues:
            require(type(row.get("number")) is int and row["number"] > 0,
                    f"{repository} issue history has an invalid row")
            start = parse_github_time(
                row.get("created_at"), f"{repository} issue #{row['number']} created_at",
            )
            closed_at = row.get("closed_at")
            require(closed_at is None or isinstance(closed_at, str),
                    f"{repository} issue #{row['number']} closed_at is invalid")
            end = (parse_github_time(
                closed_at, f"{repository} issue #{row['number']} closed_at",
            ) if closed_at is not None else None)
            require(end is None or start <= end,
                    f"{repository} issue #{row['number']} has an inverted interval")
            issue_intervals.append((row["number"], start, end))
        selected_issue_intervals = [
            row for row in issue_intervals if row[0] == selected_issue_number
        ]
        require(len(selected_issue_intervals) == 1,
                f"{repository} issue history omits the exact selected issue")
        _, selected_issue_start, selected_issue_end = selected_issue_intervals[0]
        require(selected_issue_end is not None,
                f"{repository} selected issue is not closed at completion")
        for number, start, end in issue_intervals:
            if number == selected_issue_number:
                continue
            if not (
                selected_issue_end < start
                or (end is not None and end < selected_issue_start)
            ):
                raise ValidationError(
                    f"{repository} selected issue #{selected_issue_number} "
                    f"overlaps issue #{number}"
                )

    rows = github_paginated_list(
        f"repos/{repository}/pulls?state=all&sort=created&direction=asc",
        f"{repository} pull request interval history",
    )
    intervals: list[tuple[int, datetime, datetime | None]] = []
    for row in rows:
        require(isinstance(row, dict) and type(row.get("number")) is int
                and row["number"] > 0,
                f"{repository} pull request history has an invalid row")
        start = parse_github_time(
            row.get("created_at"), f"{repository} PR #{row['number']} created_at"
        )
        closed_at = row.get("closed_at")
        require(closed_at is None or isinstance(closed_at, str),
                f"{repository} PR #{row['number']} closed_at is invalid")
        end = (parse_github_time(closed_at, f"{repository} PR #{row['number']} closed_at")
               if closed_at is not None else None)
        require(end is None or start <= end,
                f"{repository} PR #{row['number']} has an inverted interval")
        intervals.append((row["number"], start, end))
    selected = [row for row in intervals if row[0] == selected_pr_number]
    require(len(selected) == 1,
            f"{repository} pull request history omits the exact selected PR #{selected_pr_number}")
    active_prs = [row for row in intervals if row[2] is None]
    if completion:
        require(not active_prs, f"{repository} has an active pull request at completion")
    else:
        require(not active_prs, f"{repository} has an open pull request before development starts")
    if completion:
        _, selected_start, selected_end = selected[0]
        require(selected_end is not None, f"{repository} selected PR is not closed at completion")
        require(
            selected_issue_start <= selected_start <= selected_end <= selected_issue_end,
            f"{repository} selected PR interval is outside the selected issue history interval",
        )
        for number, start, end in intervals:
            if number == selected_pr_number:
                continue
            if end is None or not (selected_end < start or end < selected_start):
                raise ValidationError(
                    f"{repository} selected PR #{selected_pr_number} overlaps PR #{number}"
                )


def require_plan_owned_issue_snapshot(
    repository: str, selected_issue_number: int, selected_issue_title: str,
    selected_issue_marker: str | None,
) -> None:
    """Observe only the exact anchored issue."""
    issues = github_paginated_list(
        f"repos/{repository}/issues?state=all&sort=created&direction=asc",
        f"{repository} authorization preflight issue history",
    )
    active = [
        row for row in issues
        if isinstance(row, dict) and not row.get("pull_request")
        and row.get("state") == "open"
    ]
    require(len(active) <= 1,
            f"{repository} has concurrent active repository issues")
    require(len(active) == 1,
            f"{repository} must have exactly one active repository issue")
    row = active[0]
    require(row.get("number") == selected_issue_number
            and row.get("title") == selected_issue_title
            and (selected_issue_marker is None or (
                isinstance(row.get("body"), str)
                and row["body"].count(selected_issue_marker) == 1
            )),
            f"{repository} active repository issue is not the exact anchored selected issue")


def require_plan_owned_repository_snapshot(
    repository: str, selected_issue_number: int, selected_issue_title: str,
    selected_issue_marker: str | None,
) -> None:
    """Observe only the exact anchored issue and no open PR."""
    require_plan_owned_issue_snapshot(
        repository, selected_issue_number, selected_issue_title,
        selected_issue_marker,
    )
    prs = github_paginated_list(
        f"repos/{repository}/pulls?state=all&sort=created&direction=asc",
        f"{repository} authorization preflight pull request history",
    )
    require(not any(isinstance(row, dict) and row.get("state") == "open" for row in prs),
            f"{repository} has an open pull request before development starts")


def require_fenced_repository_snapshot(
    repository: str, selected_issue_number: int, selected_issue_title: str,
    selected_issue_marker: str | None, capability: str, phase: str,
    expected_head: str | None,
) -> None:
    """Recheck the exact issue/PR mutex around every fenced REST mutation."""
    require(
        capability in {
            "selected-issue-comment", "selected-issue-labels",
            "issue-pull-create", "create-public-repository",
        }
        and phase in {"preflight", "postflight"},
        "fenced repository snapshot mode is invalid",
    )
    require_plan_owned_issue_snapshot(
        repository, selected_issue_number, selected_issue_title,
        selected_issue_marker,
    )
    prs = github_paginated_list(
        f"repos/{repository}/pulls?state=all&sort=created&direction=asc",
        f"{repository} fenced mutation pull request history",
    )
    open_prs = [
        row for row in prs
        if isinstance(row, dict) and row.get("state") == "open"
    ]
    branch_pattern = rf"issue/{selected_issue_number}-[a-z0-9]+(?:-[a-z0-9]+)*"

    def selected_pull_request(row: dict[str, Any]) -> bool:
        head_ref = row.get("head", {}).get("ref")
        body = row.get("body")
        return (
            isinstance(head_ref, str)
            and re.fullmatch(branch_pattern, head_ref) is not None
            and (expected_head is None or head_ref == expected_head)
            and row.get("title") == selected_issue_title
            and isinstance(body, str)
            and pull_request_body_closing_refs(body) == [f"#{selected_issue_number}"]
            and row.get("head", {}).get("repo", {}).get("full_name") == repository
            and row.get("base", {}).get("ref") == "main"
            and row.get("base", {}).get("repo", {}).get("full_name") == repository
        )

    if capability == "issue-pull-create":
        require(
            isinstance(expected_head, str)
            and re.fullmatch(branch_pattern, expected_head) is not None,
            "fenced pull-request snapshot lacks the exact selected issue branch",
        )
        if phase == "preflight":
            require(not open_prs,
                    f"{repository} has an open pull request before fenced PR creation")
        else:
            require(
                len(open_prs) == 1 and selected_pull_request(open_prs[0]),
                f"{repository} fenced PR creation did not leave exactly one selected pull request",
            )
    elif capability == "create-public-repository":
        require(expected_head is None and not open_prs,
                f"{repository} public-repository creation overlaps an open pull request")
    else:
        require(
            expected_head is None and len(open_prs) <= 1
            and all(selected_pull_request(row) for row in open_prs),
            f"{repository} fenced issue mutation overlaps a competing pull request",
        )


def expected_issue_route(issue: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    complexity = issue.get("complexity")
    repository = issue.get("repo")
    gates = issue.get("gates")
    require(type(complexity) is int and 1 <= complexity <= 10
            and isinstance(repository, str)
            and isinstance(gates, list)
            and all(isinstance(gate, str) for gate in gates),
            "routing issue specification is invalid")
    risks = sorted({
        ROUTING_GATE_RISK_MAP[gate]
        for gate in gates if gate in ROUTING_GATE_RISK_MAP
    })
    role = "docs" if repository == DOCS_REPOSITORY else "developer"
    if role == "docs":
        profile = "docs_architecture"
    elif risks:
        critical_risks = {
            "recovery", "rollback", "irreversible", "safety",
            "brick_risk", "eeprom", "factory_reset", "boot",
        }
        profile = (
            "developer_critical"
            if complexity >= 9 or set(risks) & critical_risks
            else "developer_complex"
        )
    elif complexity <= 2:
        profile = "developer_standard"
    elif complexity <= 4:
        profile = "developer_standard"
    elif complexity <= 6:
        profile = "developer_restricted"
    elif complexity <= 8:
        profile = "developer_complex"
    else:
        profile = "developer_critical"
    profile_runtime = {
        "developer_standard": ("gpt-5.6-terra", "medium"),
        "developer_restricted": ("gpt-5.6-terra", "high"),
        "developer_complex": ("gpt-5.6-sol", "xhigh"),
        "developer_critical": ("gpt-5.6-sol", "max"),
        "docs_architecture": ("gpt-5.6-sol", "xhigh"),
    }
    model, effort = profile_runtime[profile]
    reviewer_profile = (
        "reviewer_max" if complexity >= 9
        else "reviewer_critical" if complexity >= 7 or risks
        else "reviewer_standard"
    )
    route = {
        "session_orchestrator_vendor": "openai",
        "availability_mode": "openai_only",
        "vendor_diversity": "single",
        "role": role,
        "complexity": complexity,
        "risk_overrides": risks,
        "primary_profile": profile,
        "adversary_profile": None,
        "reviewer_profile": reviewer_profile,
        "developer_profile": profile if role == "developer" else None,
        "vendor": "openai",
        "model": model,
        "reasoning_effort": effort,
        "fresh_context_required": False,
        "pre_review_required": role == "developer" and 5 <= complexity <= 6,
        "intermediate_review_required": role == "developer" and complexity >= 9,
        "max_override_required": effort == "max",
        "capability_degraded": False,
        "degradation_reason": None,
        "selection_reason": (
            f"openai_only:{role}:complexity-{complexity}:{profile}"
        ),
    }
    return risks, route


def require_issue_routing_receipt(
    encoded: str | None, digest: str | None, issue: dict[str, Any],
    plan_anchor: str,
) -> dict[str, Any]:
    require(isinstance(encoded, str) and 0 < len(encoded) <= 131072
            and isinstance(digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
            "authorization requires one bounded model-routing receipt")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValidationError("model-routing receipt base64 is invalid") from exc
    require(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == digest,
            "model-routing receipt digest or size is invalid")
    try:
        receipt = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("model-routing receipt JSON is invalid") from exc
    require(isinstance(receipt, dict) and set(receipt) == {
        "schema", "issue_id", "repository", "complexity", "risks",
        "plan_anchor", "router_sha256", "policy_sha256",
        "route",
    }, "model-routing receipt envelope is invalid")
    canonical = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    require(canonical == raw, "model-routing receipt is not canonical JSON")
    risks, expected_route = expected_issue_route(issue)
    require(
        receipt["schema"] == ROUTING_RECEIPT_SCHEMA
        and receipt["issue_id"] == issue.get("id")
        and receipt["repository"] == issue.get("repo")
        and receipt["complexity"] == issue.get("complexity")
        and receipt["risks"] == risks
        and receipt["plan_anchor"] == plan_anchor
        and receipt["router_sha256"] == MODEL_ROUTER_SHA256
        and receipt["policy_sha256"] == MODEL_ROUTING_POLICY_SHA256
        and receipt["route"] == expected_route,
        "model-routing receipt is missing, underpowered, or not issue-bound",
    )
    return receipt


def repository_claim_ref(repository: str) -> str:
    repository_slug = re.sub(r"[^a-z0-9]+", "-", repository.lower()).strip("-")
    require(repository_slug, "repository claim identity is invalid")
    return f"{REPOSITORY_CLAIM_REF_PREFIX}/{repository_slug}"


def repository_claim_owner_key_commitment(claim_owner_secret: str) -> str:
    require(re.fullmatch(r"[0-9a-f]{64}", claim_owner_secret) is not None,
            "repository claim owner secret is invalid")
    material = (
        b"helianthus.fmv3-claim-owner.v2\0"
        + REPOSITORY_CLAIM_LEDGER_ID.encode("ascii")
        + b"\0"
        + str(REPOSITORY_CLAIM_OWNER_EPOCH).encode("ascii")
    )
    return hmac.new(bytes.fromhex(claim_owner_secret), material, hashlib.sha256).hexdigest()


def require_repository_claim_control(claim_owner_secret: str) -> None:
    require(secrets.compare_digest(
        repository_claim_owner_key_commitment(claim_owner_secret),
        REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT,
    ), "repository claim owner secret is not anchor-pinned")
    principal = github_api("user")
    require(isinstance(principal, dict)
            and principal.get("id") == REPOSITORY_CLAIM_OWNER_ACTOR_ID
            and principal.get("login") == REPOSITORY_CLAIM_OWNER_LOGIN
            and principal.get("type") == "User",
            "repository claim credential is not the anchor-pinned owner")
    integrity = github_api(
        f"repos/{PLAN_REPOSITORY}/rulesets/{REPOSITORY_CLAIM_INTEGRITY_RULESET_ID}"
    )
    writer = github_api(
        f"repos/{PLAN_REPOSITORY}/rulesets/{REPOSITORY_CLAIM_WRITER_RULESET_ID}"
    )
    common = {
        "target": "branch",
        "source_type": "Repository",
        "source": PLAN_REPOSITORY,
        "enforcement": "active",
        "conditions": {
            "ref_name": {
                "include": [f"{REPOSITORY_CLAIM_REF_PREFIX}/**"],
                "exclude": [],
            }
        },
    }
    require(
        isinstance(integrity, dict)
        and all(integrity.get(key) == value for key, value in common.items())
        and integrity.get("id") == REPOSITORY_CLAIM_INTEGRITY_RULESET_ID
        and integrity.get("name") == "FMV3 v2 claim integrity"
        and integrity.get("rules") == [
            {"type": "deletion"}, {"type": "non_fast_forward"},
        ]
        and integrity.get("bypass_actors") == []
        and isinstance(writer, dict)
        and all(writer.get(key) == value for key, value in common.items())
        and writer.get("id") == REPOSITORY_CLAIM_WRITER_RULESET_ID
        and writer.get("name") == "FMV3 v2 claim writer"
        and writer.get("rules") == [
            {"type": "creation"}, {"type": "update"},
        ]
        and writer.get("bypass_actors") == [{
            "actor_id": 5,
            "actor_type": "RepositoryRole",
            "bypass_mode": "always",
        }],
        "repository claim namespace rulesets are absent or drifted",
    )


def repository_claim_event_mac(payload: dict[str, Any], claim_owner_secret: str) -> str:
    repository_claim_owner_key_commitment(claim_owner_secret)
    require("event_mac" not in payload,
            "repository claim MAC input contains an event_mac")
    material = (
        b"helianthus.fmv3-claim-transition.v2\0"
        + json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
    )
    return hmac.new(bytes.fromhex(claim_owner_secret), material, hashlib.sha256).hexdigest()


def remote_ref_sha(repo_root: Path, ref: str) -> str | None:
    output = str(git_command(
        repo_root,
        ["ls-remote", "--refs", "origin", ref],
        f"repository claim lookup for {ref}",
    )).strip()
    if not output:
        return None
    rows = output.splitlines()
    require(len(rows) == 1, "repository claim ref lookup is ambiguous")
    fields = rows[0].split("\t")
    require(len(fields) == 2 and fields[1] == ref
            and re.fullmatch(r"[0-9a-f]{40}", fields[0]) is not None,
            "repository claim ref lookup is invalid")
    return fields[0]


def trusted_github_token() -> str:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    require(TRUSTED_GH_EXECUTABLE is not None,
            "trusted GitHub CLI is absent for repository claim authentication")
    environment = {
        name: os.environ[name]
        for name in ("HOME", "LANG", "LC_ALL")
        if os.environ.get(name)
    }
    result = subprocess.run(
        [str(TRUSTED_GH_EXECUTABLE), "auth", "token", "--hostname", "github.com"],
        check=False, capture_output=True, text=True, env=environment,
    )
    require(result.returncode == 0 and result.stdout.strip(),
            "GitHub token is unavailable for repository claim CAS")
    return result.stdout.strip()


def push_repository_claim_cas(
    repo_root: Path, ref: str, expected_sha: str | None, target_sha: str | None,
) -> None:
    require(target_sha is not None
            and re.fullmatch(r"[0-9a-f]{40}", target_sha) is not None,
            "repository claim CAS target must be an append-only commit")
    require(remote_ref_sha(repo_root, ref) == expected_sha,
            "repository claim CAS lost to another claimant")
    token = trusted_github_token()
    materialization_root = Path(__file__).resolve().parent
    require(stat.S_IMODE(materialization_root.stat().st_mode) == 0o700,
            "repository claim CAS requires the private materialization directory")
    askpass = materialization_root / f"claim-askpass-{secrets.token_hex(12)}"
    askpass.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "  *Username*) printf '%s\\n' 'x-access-token' ;;\n"
        "  *) printf '%s\\n' \"$FMV3_GIT_TOKEN\" ;;\n"
        "esac\n",
        encoding="ascii",
    )
    askpass.chmod(0o500)
    environment = {
        "GIT_ASKPASS": str(askpass),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1",
        "FMV3_GIT_TOKEN": token,
    }
    refspec = f"{target_sha}:{ref}"
    push_error: BaseException | None = None
    cleanup_error: BaseException | None = None
    try:
        try:
            subprocess.run(
                [
                    str(trusted_git_executable()), "--no-replace-objects", "-C",
                    str(repo_root),
                    "-c", "core.hooksPath=/dev/null",
                    "-c", "core.fsmonitor=false",
                    "-c", "credential.helper=",
                    "-c", "http.proxy=",
                    "-c", "http.sslVerify=true",
                    "push", "--porcelain", "origin", refspec,
                ],
                check=False, capture_output=True, text=True, env=environment,
            )
        except BaseException as exc:
            push_error = exc
    finally:
        try:
            askpass.unlink(missing_ok=True)
        except BaseException as exc:
            cleanup_error = exc
    try:
        reconciled = remote_ref_sha(repo_root, ref)
    except BaseException as exc:
        raise ValidationError(
            "repository claim CAS result is completion-ambiguous; execution must "
            "STOP without retry pending exact remote-ref reconciliation"
        ) from (push_error or cleanup_error or exc)
    if reconciled == target_sha:
        return
    raise ValidationError(
        "repository claim CAS result is completion-ambiguous; execution must STOP "
        "without retry pending exact remote-ref reconciliation"
    ) from (push_error or cleanup_error)


REPOSITORY_CLAIM_MAX_GENERATION = (1 << 64) - 1
REPOSITORY_CLAIM_MAX_HISTORY_EVENTS = 512
REPOSITORY_CLAIM_EVENT_FIELDS = {
    "schema", "ledger_id", "owner_epoch", "repository", "ref", "event", "state",
    "issue_id", "issue_number", "plan_anchor", "run_id", "owner_login",
    "owner_actor_id", "owner_commitment", "generation", "previous_sha",
    "authoritative_main_sha", "event_at", "expires_at", "event_mac",
}


def require_repository_claim_event(
    commit: Any, observed: str, repository: str, claim_owner_secret: str,
) -> dict[str, Any]:
    message = commit.get("message") if isinstance(commit, dict) else None
    try:
        payload = json.loads(message) if isinstance(message, str) else None
    except json.JSONDecodeError as exc:
        raise ValidationError("repository claim payload is invalid") from exc
    require(isinstance(commit, dict) and commit.get("sha") == observed
            and isinstance(commit.get("tree", {}).get("sha"), str)
            and re.fullmatch(r"[0-9a-f]{40}", commit["tree"]["sha"])
            and isinstance(commit.get("parents"), list)
            and len(commit["parents"]) == 1
            and isinstance(payload, dict) and set(payload) == REPOSITORY_CLAIM_EVENT_FIELDS,
            "repository claim event envelope is invalid")
    require(payload.get("schema") == REPOSITORY_CLAIM_SCHEMA
            and payload.get("ledger_id") == REPOSITORY_CLAIM_LEDGER_ID
            and payload.get("owner_epoch") == REPOSITORY_CLAIM_OWNER_EPOCH
            and payload.get("repository") == repository
            and payload.get("ref") == repository_claim_ref(repository)
            and (payload.get("event"), payload.get("state")) in {
                ("ACQUIRE", "HELD"), ("RENEW", "HELD"),
                ("TAKEOVER", "HELD"), ("RELEASE", "RELEASED"),
            }
            and isinstance(payload.get("issue_id"), str) and payload["issue_id"]
            and type(payload.get("issue_number")) is int and payload["issue_number"] > 0
            and re.fullmatch(r"[0-9a-f]{40}", str(payload.get("plan_anchor")))
            and re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                str(payload.get("run_id")),
            )
            and payload.get("owner_login") == REPOSITORY_CLAIM_OWNER_LOGIN
            and payload.get("owner_actor_id") == REPOSITORY_CLAIM_OWNER_ACTOR_ID
            and payload.get("owner_commitment") == REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT
            and type(payload.get("generation")) is int
            and 1 <= payload["generation"] <= REPOSITORY_CLAIM_MAX_GENERATION
            and re.fullmatch(r"[0-9a-f]{40}", str(payload.get("authoritative_main_sha")))
            and re.fullmatch(r"[0-9a-f]{64}", str(payload.get("event_mac"))),
            "repository claim event payload is invalid")
    event_time = parse_github_time(
        payload.get("event_at"), "repository claim event_at",
    )
    expiry = parse_github_time(
        payload.get("expires_at"), "repository claim expires_at",
    )
    if payload["state"] == "HELD":
        require(
            expiry == event_time + timedelta(
                seconds=REPOSITORY_CLAIM_TTL_SECONDS
            ),
            "repository claim held-event TTL is invalid",
        )
    unsigned = {key: value for key, value in payload.items() if key != "event_mac"}
    require(secrets.compare_digest(
        payload["event_mac"], repository_claim_event_mac(unsigned, claim_owner_secret),
    ), "repository claim event MAC is invalid")
    parent_sha = commit["parents"][0].get("sha")
    if payload["generation"] == 1:
        require(payload["event"] == "ACQUIRE" and payload["previous_sha"] is None
                and parent_sha == payload["authoritative_main_sha"],
                "repository claim genesis predecessor is invalid")
    else:
        require(re.fullmatch(r"[0-9a-f]{40}", str(payload.get("previous_sha")))
                and parent_sha == payload["previous_sha"],
                "repository claim predecessor is invalid")
    return payload


def require_repository_claim_history(
    commit: Any, observed: str, repository: str, claim_owner_secret: str,
) -> dict[str, Any]:
    """Authenticate and validate the bounded append-only event chain to genesis."""
    tip = require_repository_claim_event(
        commit, observed, repository, claim_owner_secret,
    )
    child_commit = commit
    child = tip
    visited = {observed}
    depth = 1
    tuple_fields = (
        "issue_id", "issue_number", "plan_anchor", "run_id",
        "owner_login", "owner_actor_id", "owner_commitment",
    )
    while child["generation"] > 1:
        require(depth < REPOSITORY_CLAIM_MAX_HISTORY_EVENTS,
                "repository claim history exceeds the fail-closed bound")
        parent_sha = child["previous_sha"]
        require(parent_sha not in visited,
                "repository claim history contains a cycle")
        visited.add(parent_sha)
        parent_commit = github_api(
            f"repos/{PLAN_REPOSITORY}/git/commits/{parent_sha}"
        )
        parent = require_repository_claim_event(
            parent_commit, parent_sha, repository, claim_owner_secret,
        )
        require(
            child["generation"] == parent["generation"] + 1
            and child_commit["tree"]["sha"] == parent_commit["tree"]["sha"],
            "repository claim generation or tree continuity is invalid",
        )
        child_time = parse_github_time(
            child["event_at"], "repository claim event_at",
        )
        parent_time = parse_github_time(
            parent["event_at"], "repository claim predecessor event_at",
        )
        parent_expiry = parse_github_time(
            parent["expires_at"], "repository claim predecessor expires_at",
        )
        require(child_time >= parent_time,
                "repository claim event time regressed")
        same_tuple = all(child[field] == parent[field] for field in tuple_fields)
        if child["event"] == "RENEW":
            require(parent["state"] == "HELD" and same_tuple
                    and child_time < parent_expiry,
                    "repository claim RENEW transition is invalid")
        elif child["event"] == "TAKEOVER":
            require(parent["state"] == "HELD" and child_time >= parent_expiry,
                    "repository claim TAKEOVER transition is invalid")
        elif child["event"] == "RELEASE":
            require(parent["state"] == "HELD" and same_tuple
                    and child["expires_at"] == parent["expires_at"],
                    "repository claim RELEASE transition is invalid")
        else:
            require(child["event"] == "ACQUIRE"
                    and parent["state"] == "RELEASED",
                    "repository claim ACQUIRE transition is invalid")
        child_commit = parent_commit
        child = parent
        depth += 1
    require(child["event"] == "ACQUIRE" and child["state"] == "HELD",
            "repository claim history has no valid genesis")
    return tip


def require_repository_claim_fence(
    repo_root: Path, authoritative_main: str, repository: str, issue_id: str,
    issue_number: int, plan_anchor: str, claim_run_id: str,
    claim_owner_secret: str, expected_claim_sha: str,
    *, require_unexpired: bool = True, now: datetime | None = None,
) -> dict[str, Any]:
    """Verify one exact live-tip fencing token without changing the ledger."""
    require(re.fullmatch(r"[0-9a-f]{40}", expected_claim_sha) is not None,
            "repository claim fence SHA is invalid")
    claim_ref = repository_claim_ref(repository)
    observed = remote_ref_sha(repo_root, claim_ref)
    require(observed == expected_claim_sha,
            "repository claim fence has advanced or is absent")
    commit = github_api(f"repos/{PLAN_REPOSITORY}/git/commits/{observed}")
    prior = require_repository_claim_history(
        commit, observed, repository, claim_owner_secret,
    )
    require(prior["state"] == "HELD"
            and prior["issue_id"] == issue_id
            and prior["issue_number"] == issue_number
            and prior["plan_anchor"] == plan_anchor
            and prior["run_id"] == claim_run_id,
            "repository claim fence is not owned by this anchored run")
    if prior["authoritative_main_sha"] != authoritative_main:
        git_command(
            repo_root,
            [
                "merge-base", "--is-ancestor",
                prior["authoritative_main_sha"], authoritative_main,
            ],
            "repository claim authoritative-main ancestry check",
        )
    expiry = parse_github_time(
        prior["expires_at"], "repository claim expires_at",
    )
    current_time = (
        now if now is not None else github_server_time()
    ).astimezone(timezone.utc).replace(microsecond=0)
    if require_unexpired:
        require(current_time < expiry, "repository claim fence is expired")
    return {
        "ledger_id": prior["ledger_id"],
        "generation": prior["generation"],
        "claim_sha": observed,
        "expires_at": prior["expires_at"],
    }


def acquire_repository_claim(
    repo_root: Path, authoritative_main: str, repository: str, issue_id: str,
    issue_number: int, plan_anchor: str, claim_run_id: str,
    claim_owner_secret: str,
    *, now: datetime | None = None,
    expected_observed_sha: str | None = None,
) -> dict[str, Any]:
    require(re.fullmatch(r"[0-9a-f]{40}", authoritative_main) is not None
            and re.fullmatch(r"[0-9a-f]{40}", plan_anchor) is not None
            and re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                claim_run_id,
            ) is not None,
            "repository claim anchor or run identity is invalid")
    claim_ref = repository_claim_ref(repository)
    observed = remote_ref_sha(repo_root, claim_ref)
    if expected_observed_sha is not None:
        require(observed == expected_observed_sha,
                "repository claim renewal predecessor has advanced")
    current_time = (
        now if now is not None else github_server_time()
    ).astimezone(timezone.utc).replace(microsecond=0)
    generation = 1
    previous_sha: str | None = None
    parent = authoritative_main
    event = "ACQUIRE"
    if observed is not None:
        commit = github_api(f"repos/{PLAN_REPOSITORY}/git/commits/{observed}")
        prior = require_repository_claim_history(
            commit, observed, repository, claim_owner_secret,
        )
        require(prior["generation"] < REPOSITORY_CLAIM_MAX_GENERATION,
                "repository claim generation is exhausted")
        require(prior["generation"] < REPOSITORY_CLAIM_MAX_HISTORY_EVENTS - 1,
                "repository claim owner epoch must rotate before another held event")
        prior_expiry = parse_github_time(prior["expires_at"],
                                         "repository claim expires_at")
        same_run = (
            prior["state"] == "HELD"
            and prior["issue_id"] == issue_id
            and prior["issue_number"] == issue_number
            and prior["plan_anchor"] == plan_anchor
            and prior["run_id"] == claim_run_id
        )
        if prior["state"] == "RELEASED":
            event = "ACQUIRE"
        elif same_run and current_time < prior_expiry:
            event = "RENEW"
        elif current_time >= prior_expiry:
            event = "TAKEOVER"
        else:
            raise ValidationError("repository claim is held by another live owner")
        generation = prior["generation"] + 1
        previous_sha = observed
        parent = observed
        git_command(repo_root, ["fetch", "--no-tags", "origin", claim_ref],
                    "repository claim history fetch")
        fetched = str(git_command(
            repo_root, ["rev-parse", "FETCH_HEAD^{commit}"],
            "repository claim fetched commit lookup",
        )).strip()
        require(fetched == observed,
                "repository claim fetched history differs from observed ref")
        tree_sha = commit["tree"]["sha"]
    else:
        tree_sha = str(git_command(
            repo_root, ["rev-parse", f"{authoritative_main}^{{tree}}"],
            "repository claim genesis tree lookup",
        )).strip()
    expires_at = current_time + timedelta(seconds=REPOSITORY_CLAIM_TTL_SECONDS)
    payload: dict[str, Any] = {
        "schema": REPOSITORY_CLAIM_SCHEMA,
        "ledger_id": REPOSITORY_CLAIM_LEDGER_ID,
        "owner_epoch": REPOSITORY_CLAIM_OWNER_EPOCH,
        "repository": repository,
        "ref": claim_ref,
        "event": event,
        "state": "HELD",
        "issue_id": issue_id,
        "issue_number": issue_number,
        "plan_anchor": plan_anchor,
        "run_id": claim_run_id,
        "owner_login": REPOSITORY_CLAIM_OWNER_LOGIN,
        "owner_actor_id": REPOSITORY_CLAIM_OWNER_ACTOR_ID,
        "owner_commitment": REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT,
        "generation": generation,
        "previous_sha": previous_sha,
        "authoritative_main_sha": authoritative_main,
        "event_at": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    payload["event_mac"] = repository_claim_event_mac(payload, claim_owner_secret)
    claim_sha = str(git_command(
        repo_root,
        [
            "-c", "user.name=Helianthus Claim Gate",
            "-c", "user.email=claim-gate@users.noreply.github.com",
            "commit-tree", tree_sha, "-p", parent,
            "-m", json.dumps(payload, sort_keys=True, separators=(",", ":")),
        ],
        "repository claim commit creation",
    )).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", claim_sha) is not None,
            "repository claim commit creation failed")
    push_repository_claim_cas(repo_root, claim_ref, observed, claim_sha)
    return {
        "ledger_id": REPOSITORY_CLAIM_LEDGER_ID,
        "generation": generation,
        "claim_sha": claim_sha,
        "expires_at": payload["expires_at"],
    }


def renew_repository_claim(
    repo_root: Path, authoritative_main: str, repository: str, issue_id: str,
    issue_number: int, plan_anchor: str, claim_run_id: str,
    claim_owner_secret: str, expected_claim_sha: str,
    *, now: datetime | None = None,
) -> dict[str, Any]:
    """Append a same-run renewal/takeover from one exact observed fence."""
    require_repository_claim_fence(
        repo_root, authoritative_main, repository, issue_id, issue_number,
        plan_anchor, claim_run_id, claim_owner_secret, expected_claim_sha,
        require_unexpired=False, now=now,
    )
    return acquire_repository_claim(
        repo_root, authoritative_main, repository, issue_id, issue_number,
        plan_anchor, claim_run_id, claim_owner_secret, now=now,
        expected_observed_sha=expected_claim_sha,
    )


def release_repository_claim(
    repo_root: Path, authoritative_main: str, repository: str, issue_id: str,
    issue_number: int, plan_anchor: str, claim_run_id: str,
    claim_owner_secret: str, expected_claim_sha: str,
    *, now: datetime | None = None,
) -> str:
    """Append one authenticated release tombstone after the exact active claim."""
    require(re.fullmatch(r"[0-9a-f]{40}", expected_claim_sha) is not None,
            "repository claim release SHA is invalid")
    claim_ref = repository_claim_ref(repository)
    observed = remote_ref_sha(repo_root, claim_ref)
    require(observed == expected_claim_sha,
            "repository claim has advanced or is absent")
    commit = github_api(f"repos/{PLAN_REPOSITORY}/git/commits/{observed}")
    prior = require_repository_claim_history(
        commit, observed, repository, claim_owner_secret,
    )
    require(prior["state"] == "HELD"
            and prior["issue_id"] == issue_id
            and prior["issue_number"] == issue_number
            and prior["plan_anchor"] == plan_anchor
            and prior["run_id"] == claim_run_id,
            "repository claim is not owned by this anchored run")
    require(prior["generation"] < REPOSITORY_CLAIM_MAX_GENERATION,
            "repository claim generation is exhausted")
    require(prior["generation"] < REPOSITORY_CLAIM_MAX_HISTORY_EVENTS,
            "repository claim owner epoch transition budget is exhausted")
    git_command(repo_root, ["fetch", "--no-tags", "origin", claim_ref],
                "repository claim release history fetch")
    fetched = str(git_command(
        repo_root, ["rev-parse", "FETCH_HEAD^{commit}"],
        "repository claim release fetched commit lookup",
    )).strip()
    require(fetched == observed,
            "repository claim release history differs from observed ref")
    event_time = (
        now if now is not None else github_server_time()
    ).astimezone(timezone.utc).replace(microsecond=0)
    payload: dict[str, Any] = {
        **{key: value for key, value in prior.items() if key != "event_mac"},
        "event": "RELEASE",
        "state": "RELEASED",
        "generation": prior["generation"] + 1,
        "previous_sha": observed,
        "authoritative_main_sha": authoritative_main,
        "event_at": event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    payload["event_mac"] = repository_claim_event_mac(payload, claim_owner_secret)
    release_sha = str(git_command(
        repo_root,
        [
            "-c", "user.name=Helianthus Claim Gate",
            "-c", "user.email=claim-gate@users.noreply.github.com",
            "commit-tree", commit["tree"]["sha"], "-p", observed,
            "-m", json.dumps(payload, sort_keys=True, separators=(",", ":")),
        ],
        "repository claim release commit creation",
    )).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", release_sha) is not None,
            "repository claim release commit creation failed")
    push_repository_claim_cas(repo_root, claim_ref, observed, release_sha)
    return release_sha


def require_plan_owned_repository_preflight(
    repo_root: Path, authoritative_main: str, repository: str, issue_id: str,
    selected_issue_number: int, selected_issue_title: str,
    selected_issue_marker: str | None, plan_anchor: str, claim_run_id: str,
    claim_owner_secret: str,
) -> dict[str, Any]:
    """Acquire one durable claim and recheck exact issue/PR state after CAS."""
    require_repository_claim_control(claim_owner_secret)
    require_plan_owned_repository_snapshot(
        repository, selected_issue_number, selected_issue_title, selected_issue_marker
    )
    fence = acquire_repository_claim(
        repo_root, authoritative_main, repository, issue_id,
        selected_issue_number, plan_anchor, claim_run_id, claim_owner_secret,
    )
    try:
        require_plan_owned_repository_snapshot(
            repository, selected_issue_number, selected_issue_title,
            selected_issue_marker,
        )
    except Exception:
        release_repository_claim(
            repo_root, authoritative_main, repository, issue_id,
            selected_issue_number, plan_anchor, claim_run_id,
            claim_owner_secret, fence["claim_sha"],
        )
        raise
    return fence


def github_repository_identity(value: Any, repository: str) -> bool:
    return isinstance(value, dict) and (
        value.get("full_name") == repository
        or value.get("url") == f"https://api.github.com/repos/{repository}"
    )


def decode_exact_github_blob(value: Any, sha: str, label: str,
                             maximum_bytes: int) -> bytes:
    require(isinstance(value, dict) and value.get("sha") == sha
            and value.get("encoding") == "base64"
            and type(value.get("size")) is int
            and 0 < value["size"] <= maximum_bytes
            and isinstance(value.get("content"), str),
            f"{label} response is invalid")
    encoded = re.sub(r"\s+", "", value["content"])
    try:
        blob = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValidationError(f"{label} is not valid base64") from exc
    require(len(blob) == value["size"], f"{label} size mismatch")
    git_blob_sha = hashlib.sha1(
        f"blob {len(blob)}\0".encode("ascii") + blob,
        usedforsecurity=False,
    ).hexdigest()
    require(git_blob_sha == sha, f"{label} content does not match its Git blob SHA")
    return blob


def github_tree_blob_map(
    repository: str,
    tree_sha: str,
    label: str,
) -> dict[str, str]:
    value = github_api(f"repos/{repository}/git/trees/{tree_sha}?recursive=1")
    rows = value.get("tree") if isinstance(value, dict) else None
    require(
        isinstance(value, dict) and value.get("sha") == tree_sha
        and value.get("truncated") is False
        and isinstance(rows, list) and len(rows) <= 10000,
        f"{label} tree response is invalid, truncated, or unbounded",
    )
    blobs: dict[str, str] = {}
    for row in rows:
        path = row.get("path") if isinstance(row, dict) else None
        require(
            isinstance(path, str) and path not in blobs
            and row.get("type") in {"blob", "tree"},
            f"{label} tree contains an invalid or duplicate path",
        )
        if row.get("type") == "blob":
            require(
                row.get("mode") in {"100644", "100755"}
                and isinstance(row.get("sha"), str)
                and re.fullmatch(r"[0-9a-f]{40}", row["sha"]),
                f"{label} tree contains an invalid blob",
            )
            blobs[path] = row["sha"]
    return blobs


def require_repository_mutex_history(
    repository: str,
    harness_pr: dict[str, Any],
    product_pr: dict[str, Any],
) -> None:
    rows = github_paginated_list(
        f"repos/{repository}/pulls?state=all&sort=created&direction=asc",
        "M1-06 repository mutex history",
    )
    selected = {
        harness_pr["number"]: harness_pr,
        product_pr["number"]: product_pr,
    }
    by_number: dict[int, dict[str, Any]] = {}
    for row in rows:
        number = row.get("number")
        require(type(number) is int and number > 0 and number not in by_number,
                "M1-06 repository mutex history has an invalid or duplicate PR")
        parse_github_time(row.get("created_at"), f"M1-06 PR #{number} created_at")
        closed_at = row.get("closed_at")
        require(closed_at is None or isinstance(closed_at, str),
                f"M1-06 PR #{number} closed_at is invalid")
        if closed_at is not None:
            parse_github_time(closed_at, f"M1-06 PR #{number} closed_at")
        by_number[number] = row
    require(set(selected) <= set(by_number),
            "M1-06 repository mutex history omits the harness or product PR")
    intervals: list[tuple[int, datetime, datetime]] = []
    for number, expected in selected.items():
        observed = by_number[number]
        start = parse_github_time(expected.get("created_at"), f"M1-06 PR #{number} created_at")
        end = parse_github_time(expected.get("merged_at"), f"M1-06 PR #{number} merged_at")
        require(
            observed.get("created_at") == expected.get("created_at")
            and observed.get("closed_at") == expected.get("merged_at")
            and start <= end,
            f"M1-06 repository mutex history differs for PR #{number}",
        )
        intervals.append((number, start, end))
    for row in rows:
        number = row["number"]
        if number in selected:
            continue
        opened = parse_github_time(row["created_at"], f"M1-06 PR #{number} created_at")
        closed = (
            parse_github_time(row["closed_at"], f"M1-06 PR #{number} closed_at")
            if row.get("closed_at") is not None
            else None
        )
        for selected_number, start, end in intervals:
            require(
                opened > end or (closed is not None and closed < start),
                f"M1-06 repository mutex was violated by PR #{number} during PR #{selected_number}",
            )


def require_m1_06_docs_lock(
    repository: str,
    harness_blobs: dict[str, str],
    product_blobs: dict[str, str],
) -> str:
    blob_sha = harness_blobs.get(M1_06_DOCS_LOCK_PATH)
    require(
        isinstance(blob_sha, str) and product_blobs.get(M1_06_DOCS_LOCK_PATH) == blob_sha,
        "M1-06 product head changed the merged docs lock",
    )
    blob = decode_exact_github_blob(
        github_api(f"repos/{repository}/git/blobs/{blob_sha}"),
        blob_sha, "M1-06 merged docs lock", 4096,
    )
    lock = unique_json_object(blob.decode("utf-8"), "M1-06 merged docs lock")
    binding = EXPECTED_DOCS_CANDIDATE_BINDING
    expected = {
        "schema": M1_06_DOCS_LOCK_SCHEMA,
        "repository": DOCS_REPOSITORY,
        "pull_request": binding["pr"],
        "contract_id": "OPAQUE_RUNTIME_ACQUISITION_V1",
        "contract_version": 1,
        "content_revision": 1,
        "policy_path": binding["policy_path"],
        "policy_sha256": binding["policy_sha256"],
        "manifest_path": binding["manifest_path"],
        "manifest_sha256": binding["manifest_sha256"],
    }
    require(
        set(lock) == M1_06_DOCS_LOCK_KEYS
        and all(lock.get(key) == value for key, value in expected.items())
        and isinstance(lock.get("merged_docs_commit_sha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", lock["merged_docs_commit_sha"]) is not None,
        "M1-06 merged docs lock fields are not exact",
    )
    docs_pr = github_api(f"repos/{DOCS_REPOSITORY}/pulls/{binding['pr']}")
    merge_sha = lock["merged_docs_commit_sha"]
    require(
        isinstance(docs_pr, dict) and docs_pr.get("merged") is True
        and docs_pr.get("merge_commit_sha") == merge_sha,
        "M1-06 docs lock does not bind the live PR #386 merge commit",
    )
    docs_merge = github_api(f"repos/{DOCS_REPOSITORY}/git/commits/{merge_sha}")
    require(
        isinstance(docs_merge, dict)
        and docs_merge.get("tree", {}).get("sha") == binding["commit_tree_sha"],
        "M1-06 docs lock merge tree differs from the plan-bound docs tree",
    )
    return blob_sha


def require_m1_06_harness_evidence(
    anchor: dict[str, Any],
    producer: dict[str, Any],
    product_pr: dict[str, Any],
    product_head_tree_sha: str,
    required_checks: list[dict[str, Any]],
) -> tuple[int, dict[str, str], datetime]:
    repository = MODBUS_REPOSITORY
    harness_pr_number = producer["harness_pull_request_number"]
    harness_merge_sha = producer["harness_merge_sha"]
    workflow_id = producer["harness_workflow_id"]
    issue_number = producer["github_issue_number"]
    issue = github_api(f"repos/{repository}/issues/{issue_number}")
    harness_pr = github_api(f"repos/{repository}/pulls/{harness_pr_number}")
    require(
        isinstance(issue, dict)
        and issue.get("number") == issue_number
        and issue.get("repository_url") == f"https://api.github.com/repos/{repository}"
        and issue.get("title") == M1_06_PRODUCER_ISSUE_TITLE
        and issue.get("state") == "closed"
        and isinstance(harness_pr, dict)
        and harness_pr.get("number") == harness_pr_number
        and harness_pr.get("title") == M1_06_HARNESS_PULL_REQUEST_TITLE
        and harness_pr.get("state") == "closed"
        and harness_pr.get("merged") is True
        and harness_pr.get("merge_commit_sha") == harness_merge_sha
        and harness_pr.get("base", {}).get("ref") == "main"
        and github_repository_identity(harness_pr.get("base", {}).get("repo"), repository)
        and github_repository_identity(harness_pr.get("head", {}).get("repo"), repository)
        and isinstance(harness_pr.get("head", {}).get("ref"), str)
        and re.fullmatch(
            rf"issue/{issue_number}-[a-z0-9]+(?:-[a-z0-9]+)*",
            harness_pr["head"]["ref"],
        ) is not None
        and harness_pr.get("user", {}).get("login") == anchor["authorized_issuer"]
        and harness_pr.get("merged_by", {}).get("login") == anchor["authorized_issuer"]
        and harness_pr.get("author_association") in anchor["allowed_author_associations"],
        "M1-06 evidence harness PR identity or authority mismatch",
    )
    harness_merged_at = parse_github_time(
        harness_pr.get("merged_at"), "M1-06 harness merged_at"
    )
    issue_created_at = parse_github_time(
        issue.get("created_at"), "M1-06 producer issue created_at"
    )
    harness_created_at = parse_github_time(
        harness_pr.get("created_at"), "M1-06 harness created_at"
    )
    harness_head_sha = harness_pr.get("head", {}).get("sha")
    require(
        isinstance(harness_head_sha, str)
        and re.fullmatch(r"[0-9a-f]{40}", harness_head_sha)
        and issue_created_at <= harness_created_at <= harness_merged_at
        and product_pr.get("base", {}).get("sha") == harness_merge_sha
        and harness_merged_at
        < parse_github_time(product_pr.get("created_at"), "M1-06 product created_at")
        and harness_merged_at
        < parse_github_time(product_pr.get("merged_at"), "M1-06 producer merged_at"),
        "M1-06 product PR must be created after and start exactly from the harness merge",
    )
    require_repository_mutex_history(repository, harness_pr, product_pr)
    harness_head = github_api(f"repos/{repository}/git/commits/{harness_head_sha}")
    harness_merge = github_api(f"repos/{repository}/git/commits/{harness_merge_sha}")
    harness_base_sha = harness_pr.get("base", {}).get("sha")
    harness_base = github_api(f"repos/{repository}/git/commits/{harness_base_sha}")
    harness_tree_sha = harness_head.get("tree", {}).get("sha") if isinstance(harness_head, dict) else None
    base_tree_sha = harness_base.get("tree", {}).get("sha") if isinstance(harness_base, dict) else None
    require(
        isinstance(harness_tree_sha, str) and re.fullmatch(r"[0-9a-f]{40}", harness_tree_sha)
        and isinstance(base_tree_sha, str) and re.fullmatch(r"[0-9a-f]{40}", base_tree_sha)
        and isinstance(harness_merge, dict)
        and harness_merge.get("tree", {}).get("sha") == harness_tree_sha
        and isinstance(harness_merge.get("parents"), list)
        and len(harness_merge["parents"]) == 1
        and harness_merge["parents"][0].get("sha") == harness_base_sha,
        "M1-06 evidence harness squash topology mismatch",
    )
    harness_checks = require_exact_head_checks(
        repository,
        harness_head_sha,
        required_checks,
        "M1-06 evidence harness",
        completed_before=harness_merged_at,
        bound_runs=producer["harness_required_check_runs"],
    )
    harness_ci = [
        row for row in harness_checks
        if row.get("name") == M1_06_RED_REQUIRED_CHECK
        and row.get("head_sha") == harness_head_sha
        and isinstance(row.get("details_url"), str)
    ]
    require(len(harness_ci) == 1,
            "M1-06 evidence harness lacks the exact checks workflow run")
    harness_ci_selector = producer["harness_ci_run"]
    match = re.fullmatch(
        rf"https://github\.com/{re.escape(repository)}/actions/runs/(\d+)(?:/.*)?",
        harness_ci[0]["details_url"],
    )
    require(
        match is not None
        and int(match.group(1)) == harness_ci_selector["workflow_run_id"]
        and harness_ci[0].get("id") == harness_ci_selector["check_run_id"],
            "M1-06 evidence harness checks workflow URL is invalid")
    harness_run = github_api(
        f"repos/{repository}/actions/runs/{harness_ci_selector['workflow_run_id']}"
        f"/attempts/{harness_ci_selector['workflow_run_attempt']}"
    )
    require(
        isinstance(harness_run, dict)
        and harness_run.get("id") == harness_ci_selector["workflow_run_id"]
        and harness_run.get("run_attempt") == harness_ci_selector["workflow_run_attempt"]
        and harness_run.get("event") == "pull_request"
        and harness_run.get("status") == "completed"
        and harness_run.get("conclusion") == "success"
        and harness_run.get("head_sha") == harness_head_sha
        and github_repository_identity(harness_run.get("head_repository"), repository),
        "M1-06 evidence harness CI run identity or attempt mismatch",
    )
    require_m1_06_ci_local_job(
        repository,
        harness_ci_selector["workflow_run_id"],
        harness_ci_selector["workflow_run_attempt"],
        harness_ci_selector["job_id"],
        harness_ci_selector["check_run_id"],
        harness_head_sha,
        expected_job_conclusion="success", expected_ci_conclusion="success",
    )
    harness_reviews = github_paginated_list(
        f"repos/{repository}/pulls/{harness_pr_number}/reviews",
        "M1-06 evidence harness reviews",
    )
    exact_head_codex = [
        review for review in harness_reviews
        if isinstance(review, dict)
        and review.get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
        and review.get("commit_id") == harness_head_sha
    ]
    require(
        len(exact_head_codex) == 1
        and exact_head_codex[0].get("state") == "COMMENTED"
        and exact_head_codex[0].get("body")
        == canonical_codex_review_body(harness_head_sha)
        and parse_github_time(
            exact_head_codex[0].get("submitted_at"),
            "M1-06 harness Codex submitted_at",
        ) < harness_merged_at,
        "M1-06 evidence harness lacks one clean exact-head Codex review",
    )
    harness_inline = github_paginated_list(
        f"repos/{repository}/pulls/{harness_pr_number}/reviews/"
        f"{exact_head_codex[0].get('id')}/comments",
        "M1-06 evidence harness Codex comments",
    )
    require(
        not harness_inline,
        "M1-06 evidence harness Codex review has inline findings",
    )
    page_1 = github_api(
        f"repos/{repository}/pulls/{harness_pr_number}/files?per_page=100&page=1"
    )
    page_2 = github_api(
        f"repos/{repository}/pulls/{harness_pr_number}/files?per_page=100&page=2"
    )
    expected_paths = {
        M1_06_MUTATION_WORKFLOW_PATH,
        M1_06_MUTATION_GUARD_PATH,
        M1_06_DOCS_LOCK_VALIDATOR_PATH,
        M1_06_DOCS_LOCK_PATH,
    }
    require(
        isinstance(page_1, list) and isinstance(page_2, list) and page_2 == []
        and len(page_1) == 4
        and {row.get("filename") for row in page_1 if isinstance(row, dict)} == expected_paths
        and all(row.get("status") == "added" for row in page_1 if isinstance(row, dict)),
        "M1-06 harness PR must add only the exact workflow, AST guard, docs-lock validator, and merged docs lock",
    )
    base_blobs = github_tree_blob_map(repository, base_tree_sha, "M1-06 harness base")
    harness_blobs = github_tree_blob_map(repository, harness_tree_sha, "M1-06 harness head")
    product_blobs = github_tree_blob_map(
        repository, product_head_tree_sha, "M1-06 product head"
    )
    for inherited_path in (".github/workflows/ci.yml", "scripts/ci_local.sh"):
        require(
            inherited_path in base_blobs
            and harness_blobs.get(inherited_path) == base_blobs[inherited_path]
            and product_blobs.get(inherited_path) == base_blobs[inherited_path],
            f"M1-06 changed trusted inherited CI tooling: {inherited_path}",
        )
    expected_hashes = {
        M1_06_MUTATION_WORKFLOW_PATH: M1_06_MUTATION_WORKFLOW_SHA256,
        M1_06_MUTATION_GUARD_PATH: M1_06_MUTATION_GUARD_SHA256,
        M1_06_DOCS_LOCK_VALIDATOR_PATH: M1_06_DOCS_LOCK_VALIDATOR_SHA256,
    }
    for path, expected_sha256 in expected_hashes.items():
        blob_sha = harness_blobs.get(path)
        require(
            isinstance(blob_sha, str) and product_blobs.get(path) == blob_sha,
            f"M1-06 product head changed trusted harness blob: {path}",
        )
        blob = decode_exact_github_blob(
            github_api(f"repos/{repository}/git/blobs/{blob_sha}"),
            blob_sha,
            f"M1-06 harness {path}",
            65536,
        )
        require(
            hashlib.sha256(blob).hexdigest() == expected_sha256,
            f"M1-06 harness blob differs from the plan-anchored template: {path}",
        )
    workflow = github_api(
        f"repos/{repository}/actions/workflows/{Path(M1_06_MUTATION_WORKFLOW_PATH).name}"
    )
    require(
        isinstance(workflow, dict) and workflow.get("id") == workflow_id
        and workflow.get("path") == M1_06_MUTATION_WORKFLOW_PATH
        and workflow.get("state") == "active",
        "M1-06 trusted mutation workflow identity is invalid",
    )
    main_sha = canonical_main_sha(repository)
    comparison = github_api(f"repos/{repository}/compare/{harness_merge_sha}...{main_sha}")
    require(
        isinstance(comparison, dict)
        and comparison.get("status") in {"ahead", "identical"}
        and comparison.get("merge_base_commit", {}).get("sha") == harness_merge_sha,
        "M1-06 harness merge is not on canonical main",
    )
    docs_lock_blob = require_m1_06_docs_lock(
        repository, harness_blobs, product_blobs,
    )
    return (
        workflow_id,
        {
            **{path: harness_blobs[path] for path in expected_hashes},
            M1_06_DOCS_LOCK_PATH: docs_lock_blob,
        },
        harness_merged_at,
    )


def require_m1_06_red_path(path: str) -> bool:
    relative = safe_repository_path(path, "M1-06 RED diff path")
    parts = relative.parts
    return (
        path == M1_06_CONFORMANCE_REPORT_PATH
        or path.endswith("_test.go")
        or "testdata" in parts
        or "fixtures" in parts
    )


def go_code_projection(source: str) -> str:
    """Preserve Go code positions while blanking comments and literals."""
    projected = list(source)
    index = 0
    state = "normal"
    escaped = False
    while index < len(source):
        char = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "normal":
            if char == "/" and following == "/":
                projected[index] = projected[index + 1] = " "
                state = "line_comment"
                index += 2
                continue
            if char == "/" and following == "*":
                projected[index] = projected[index + 1] = " "
                state = "block_comment"
                index += 2
                continue
            if char in {'"', "'", "`"}:
                projected[index] = " "
                state = {"\"": "string", "'": "rune", "`": "raw"}[char]
                escaped = False
        elif state == "line_comment":
            if char == "\n":
                state = "normal"
            else:
                projected[index] = " "
        elif state == "block_comment":
            projected[index] = " " if char != "\n" else "\n"
            if char == "*" and following == "/":
                projected[index + 1] = " "
                state = "normal"
                index += 2
                continue
        elif state == "raw":
            projected[index] = " " if char != "\n" else "\n"
            if char == "`":
                state = "normal"
        else:
            projected[index] = " " if char != "\n" else "\n"
            quote = '"' if state == "string" else "'"
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                state = "normal"
        index += 1
    require(state in {"normal", "line_comment"},
            "M1-06 Go source contains an unterminated comment or literal")
    return "".join(projected)


def go_source_without_comments(source: str) -> str:
    """Blank Go comments while preserving quoted import paths."""
    projected = list(source)
    index = 0
    state = "normal"
    escaped = False
    while index < len(source):
        char = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "normal":
            if char == "/" and following == "/":
                projected[index] = projected[index + 1] = " "
                state = "line_comment"
                index += 2
                continue
            if char == "/" and following == "*":
                projected[index] = projected[index + 1] = " "
                state = "block_comment"
                index += 2
                continue
            if char in {'"', "'", "`"}:
                state = {'"': "string", "'": "rune", "`": "raw"}[char]
                escaped = False
        elif state == "line_comment":
            if char == "\n":
                state = "normal"
            else:
                projected[index] = " "
        elif state == "block_comment":
            projected[index] = " " if char != "\n" else "\n"
            if char == "*" and following == "/":
                projected[index + 1] = " "
                state = "normal"
                index += 2
                continue
        elif state == "raw":
            if char == "`":
                state = "normal"
        else:
            quote = '"' if state == "string" else "'"
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                state = "normal"
        index += 1
    require(state in {"normal", "line_comment"},
            "Go source contains an unterminated comment or literal")
    return "".join(projected)


def go_unquote_import_literal(literal: str) -> str:
    if literal.startswith("`"):
        require(literal.endswith("`") and "\r" not in literal,
                "Go raw import literal is invalid")
        return literal[1:-1]
    require(literal.startswith('"') and literal.endswith('"'),
            "Go interpreted import literal is invalid")
    payload = literal[1:-1]
    result: list[str] = []
    simple = {
        "a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r",
        "t": "\t", "v": "\v", "\\": "\\", '"': '"', "'": "'",
    }
    index = 0
    while index < len(payload):
        if payload[index] != "\\":
            result.append(payload[index])
            index += 1
            continue
        require(index + 1 < len(payload), "Go import literal has a trailing escape")
        marker = payload[index + 1]
        if marker in simple:
            result.append(simple[marker])
            index += 2
            continue
        if marker in "01234567":
            digits = payload[index + 1:index + 4]
            require(len(digits) == 3 and all(char in "01234567" for char in digits),
                    "Go import literal has an invalid octal escape")
            value = int(digits, 8)
            require(value <= 0xFF, "Go import literal octal escape exceeds one byte")
            result.append(chr(value))
            index += 4
            continue
        widths = {"x": 2, "u": 4, "U": 8}
        require(marker in widths, "Go import literal has an invalid escape")
        width = widths[marker]
        digits = payload[index + 2:index + 2 + width]
        require(len(digits) == width and re.fullmatch(r"[0-9A-Fa-f]+", digits) is not None,
                "Go import literal has an invalid hexadecimal escape")
        value = int(digits, 16)
        require(value <= 0x10FFFF and not 0xD800 <= value <= 0xDFFF,
                "Go import literal has an invalid Unicode code point")
        result.append(chr(value))
        index += 2 + width
    return "".join(result)


def go_import_paths(source: str) -> set[str]:
    projection = go_code_projection(source)
    require(
        re.search(r"(?m)^([^\n]*);\s*import\b", projection) is None,
        "Go import declarations must not use same-line semicolon syntax",
    )
    clean = go_source_without_comments(source)
    literal = r'("(?:\\.|[^"\\\r\n])*"|`[^`\r\n]*`)'
    paths: set[str] = set()
    declarations = list(re.finditer(r"(?m)^\s*import\b", projection))
    for declaration in declarations:
        cursor = declaration.end()
        while cursor < len(clean) and clean[cursor].isspace():
            cursor += 1
        require(cursor < len(clean), "Go import declaration is incomplete")
        if clean[cursor] == "(":
            close = projection.find(")", cursor + 1)
            require(close >= 0, "Go grouped import declaration is unterminated")
            require(";" not in projection[cursor + 1:close],
                    "Go import declarations must not use explicit semicolons")
            block = clean[cursor + 1:close]
            matches = list(re.finditer(literal, block))
            require(matches, "Go grouped import declaration has no import paths")
            for match in matches:
                paths.add(go_unquote_import_literal(match.group(1)))
        else:
            line_end = clean.find("\n", cursor)
            if line_end < 0:
                line_end = len(clean)
            match = re.fullmatch(
                rf"\s*(?:\S+\s+)?{literal}\s*", clean[cursor:line_end]
            )
            require(match is not None, "Go single import declaration is invalid")
            paths.add(go_unquote_import_literal(match.group(1)))
    return paths


def is_tcp_concrete_import(import_path: str) -> bool:
    parts = [part.lower().replace("-", "_") for part in import_path.split("/")]
    return any(
        part == "net" or "tcp" in part or part in {"modbus_tcp", "modbustcp"}
        for part in parts
    )


FMV3_M3_03_TRANSPORT_NEUTRAL_IMPORTS = {
    "bytes", "cmp", "context", "encoding", "encoding/base64", "encoding/binary",
    "encoding/hex", "encoding/json", "errors", "fmt", "hash", "hash/crc32",
    "hash/crc64", "io", "maps", "math", "math/bits", "reflect", "regexp",
    "slices", "sort", "strconv", "strings", "sync", "sync/atomic", "time",
    "unicode", "unicode/utf8",
}

FMV3_M3_03_RUNTIME_SCANNER_IMPORTS = {
    "errors", "go/parser", "go/token", "os", "path/filepath", "runtime", "sort", "strconv", "strings", "testing",
}


def go_named_function_body(source: str, function_name: str) -> str:
    clean = go_source_without_comments(source)
    declaration = re.compile(rf"(?m)^func\s+{re.escape(function_name)}\s*\(")
    matches = list(declaration.finditer(clean))
    require(len(matches) == 1,
            f"FMV3-M3-03 canonical test source must declare exact {function_name}")
    body_start = clean.find("{", matches[0].end())
    require(body_start >= 0,
            f"FMV3-M3-03 canonical helper {function_name} has no body")
    depth = 0
    for index in range(body_start, len(clean)):
        if clean[index] == "{":
            depth += 1
        elif clean[index] == "}":
            depth -= 1
            if depth == 0:
                return clean[body_start + 1:index]
    raise ValidationError(f"FMV3-M3-03 canonical helper {function_name} has no closing brace")


def require_m3_03_runtime_import_scanner(source: str, imports: set[str]) -> None:
    require(imports == FMV3_M3_03_RUNTIME_SCANNER_IMPORTS,
            "FMV3-M3-03 canonical test source scanner imports are not exact")
    scanner_body = " ".join(
        go_named_function_body(source, "froniusOverlayProductionPackages").split()
    )
    require(scanner_body == (
        "_, sourceFile, _, ok := runtime.Caller(0) "
        'if !ok || sourceFile == "" { return nil, errors.New("canonical source directory unavailable") } '
        "directory := filepath.Dir(sourceFile) "
        "entries, err := os.ReadDir(directory) if err != nil { return nil, err } "
        "imports := make([]string, 0) "
        "scanned := 0 "
        "for _, entry := range entries { "
        'if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".go") || '
        'strings.HasSuffix(entry.Name(), "_test.go") { continue } '
        "sourcePath := filepath.Join(directory, entry.Name()) "
        "file, err := parser.ParseFile(token.NewFileSet(), sourcePath, nil, parser.ImportsOnly) "
        "if err != nil { return nil, err } "
        "scanned++ "
        "for _, spec := range file.Imports { "
        "importPath, err := strconv.Unquote(spec.Path.Value) "
        "if err != nil { return nil, err } "
        "imports = append(imports, importPath) } } "
        'if scanned == 0 { return nil, errors.New("no direct production Go source scanned") } '
        "sort.Strings(imports) return imports, nil"
    ), "FMV3-M3-03 production-package scanner is not the exact fail-closed runtime scanner")
    predicate_body = " ".join(
        go_named_function_body(source, "hasTCPConcreteImport").split()
    )
    require(predicate_body == (
        "for _, importPath := range imports { "
        "for _, part := range strings.Split(importPath, \"/\") { "
        "normalized := strings.ToLower(strings.ReplaceAll(part, \"-\", \"_\")) "
        "if normalized == \"net\" || strings.Contains(normalized, \"tcp\") || "
        "normalized == \"modbus_tcp\" || normalized == \"modbustcp\" { "
        "return importPath } } } return \"\""
    ), "FMV3-M3-03 TCP import predicate is not the exact complete path-component scan")


def imports_are_transport_neutral(imports: set[str], *, test_source: bool) -> bool:
    allowed = FMV3_M3_03_TRANSPORT_NEUTRAL_IMPORTS | (
        {"go/parser", "go/token", "os", "path/filepath", "runtime", "testing"}
        if test_source else set()
    )
    return imports <= allowed


GO_IMPLICIT_BUILD_SUFFIXES = {
    "aix", "android", "darwin", "dragonfly", "freebsd", "hurd", "illumos",
    "ios", "js", "linux", "netbsd", "openbsd", "plan9", "solaris", "wasip1",
    "windows", "386", "amd64", "arm", "arm64", "loong64", "mips", "mips64",
    "mips64le", "mipsle", "ppc64", "ppc64le", "riscv64", "s390x", "wasm",
}


def go_source_path_is_unconditionally_build_eligible(path: str) -> bool:
    name = PurePosixPath(path).name
    if name.startswith((".", "_")) or not name.endswith(".go"):
        return False
    stem = name[:-3]
    if stem.endswith("_test"):
        stem = stem[:-5]
    return stem.rsplit("_", 1)[-1].lower() not in GO_IMPLICIT_BUILD_SUFFIXES


def go_function_body(source: str, function_name: str) -> str:
    projected = go_code_projection(source)
    declaration = re.compile(
        rf"(?m)^func {re.escape(function_name)}\(t \*testing\.T\) \{{"
    )
    matches = list(declaration.finditer(projected))
    require(len(matches) == 1,
            f"M1-06 conformance source must declare exact {function_name}(t *testing.T)")
    start = matches[0].end() - 1
    depth = 0
    index = start
    while index < len(projected):
        char = projected[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return projected[start + 1:index]
        index += 1
    raise ValidationError(f"M1-06 conformance test {function_name} has no closing brace")


def require_m1_06_conformance_report(
    repository: str,
    head_tree_sha: str,
) -> tuple[str, str, dict[str, str], set[str]]:
    tree_value = github_api(
        f"repos/{repository}/git/trees/{head_tree_sha}?recursive=1"
    )
    tree = tree_value.get("tree") if isinstance(tree_value, dict) else None
    require(isinstance(tree_value, dict) and tree_value.get("sha") == head_tree_sha
            and tree_value.get("truncated") is False and isinstance(tree, list)
            and len(tree) <= 4096,
            "M1-06 implementation tree response is invalid or truncated")
    entries: dict[str, dict[str, Any]] = {}
    for item in tree:
        require(isinstance(item, dict) and isinstance(item.get("path"), str)
                and item["path"] not in entries,
                "M1-06 implementation tree contains an invalid or duplicate path")
        entries[item["path"]] = item
    report_entry = entries.get(M1_06_CONFORMANCE_REPORT_PATH)
    require(isinstance(report_entry, dict)
            and report_entry.get("type") == "blob"
            and report_entry.get("mode") == "100644"
            and isinstance(report_entry.get("sha"), str)
            and re.fullmatch(r"[0-9a-f]{40}", report_entry["sha"]),
            "M1-06 required conformance report is missing or not a regular committed blob")
    report_blob = github_api(
        f"repos/{repository}/git/blobs/{report_entry['sha']}"
    )
    report_bytes = decode_exact_github_blob(
        report_blob, report_entry["sha"], "M1-06 conformance report", 65536
    )
    try:
        report = unique_json_object(
            report_bytes.decode("utf-8"), "M1-06 conformance report"
        )
    except UnicodeError as exc:
        raise ValidationError("M1-06 conformance report is not UTF-8") from exc
    require(set(report) == {
        "schema", "plan_issue", "repository", "contract_id",
        "case_digest", "go_list", "production", "cases",
    } and report.get("schema") == M1_06_CONFORMANCE_REPORT_SCHEMA
            and report.get("plan_issue") == "FMV3-M1-06"
            and report.get("repository") == repository
            and report.get("contract_id") == "OPAQUE_RUNTIME_ACQUISITION_V1"
            and report.get("case_digest") == M1_06_CONFORMANCE_CASE_DIGEST,
            "M1-06 conformance report identity, digest, or closed schema mismatch")
    production = report.get("production")
    cases = report.get("cases")
    go_list = report.get("go_list")
    require(isinstance(production, list) and 1 <= len(production) <= 8
            and isinstance(cases, list)
            and len(cases) == len(M1_06_CONFORMANCE_CASES)
            and isinstance(go_list, dict)
            and set(go_list) == {
                "package_dir", "package_query", "package_name", "import_path",
                "goos", "goarch", "cgo_enabled", "gowork", "go_files",
                "compiled_go_files", "test_go_files", "ignored_go_files",
                "cgo_files", "c_files", "cxx_files", "m_files", "h_files",
                "f_files", "s_files", "swig_files", "swig_cxx_files",
                "syso_files", "x_test_go_files", "ignored_other_files",
                "embed_patterns", "embed_files", "test_embed_patterns",
                "test_embed_files", "x_test_embed_patterns",
                "x_test_embed_files",
            }
            and isinstance(go_list.get("package_dir"), str)
            and go_list.get("package_query") == "."
            and isinstance(go_list.get("package_name"), str)
            and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", go_list["package_name"])
            and isinstance(go_list.get("import_path"), str)
            and re.fullmatch(r"[A-Za-z0-9._~/-]+", go_list["import_path"])
            and go_list.get("goos") == "linux"
            and go_list.get("goarch") == "amd64"
            and go_list.get("cgo_enabled") == "0"
            and go_list.get("gowork") == "off"
            and isinstance(go_list.get("go_files"), list)
            and isinstance(go_list.get("compiled_go_files"), list)
            and isinstance(go_list.get("test_go_files"), list)
            and all(
                go_list.get(field) == []
                for field in (
                    "ignored_go_files", "cgo_files", "c_files", "cxx_files",
                    "m_files", "h_files", "f_files", "s_files", "swig_files",
                    "swig_cxx_files", "syso_files", "x_test_go_files",
                    "ignored_other_files", "embed_patterns", "embed_files",
                    "test_embed_patterns", "test_embed_files",
                    "x_test_embed_patterns", "x_test_embed_files",
                )
            ),
            "M1-06 conformance report production/case bounds mismatch")
    blob_cache: dict[str, bytes] = {}
    total_blob_bytes = 0

    def source_blob(path: Any, blob_sha: Any, mode: Any, label: str) -> bytes:
        nonlocal total_blob_bytes
        require(isinstance(path, str) and 0 < len(path.encode("utf-8")) <= 256,
                f"{label} path is invalid")
        safe_repository_path(path, f"{label} path")
        require(isinstance(blob_sha, str) and re.fullmatch(r"[0-9a-f]{40}", blob_sha)
                and mode == "100644", f"{label} blob or mode is invalid")
        tree_entry = entries.get(path)
        require(isinstance(tree_entry, dict) and tree_entry.get("type") == "blob"
                and tree_entry.get("mode") == mode and tree_entry.get("sha") == blob_sha,
                f"{label} is missing or differs from the implementation tree")
        if blob_sha not in blob_cache:
            blob_cache[blob_sha] = decode_exact_github_blob(
                github_api(f"repos/{repository}/git/blobs/{blob_sha}"),
                blob_sha, label, 2 * 1024 * 1024,
            )
            total_blob_bytes += len(blob_cache[blob_sha])
            require(total_blob_bytes <= 8 * 1024 * 1024,
                    "M1-06 conformance source blobs exceed aggregate byte bound")
        return blob_cache[blob_sha]

    package_dir = go_list["package_dir"]
    package_path = safe_repository_path(
        package_dir, "M1-06 conformance go-list package directory"
    )
    package_dir = package_path.as_posix()
    require(
        package_dir == "."
        and entries.get("go.mod", {}).get("type") == "blob"
        and entries.get("go.mod", {}).get("mode") == "100644"
        and [path for path in entries if path == "go.mod" or path.endswith("/go.mod")]
        == ["go.mod"],
        "M1-06 conformance package is not in the exact root Go module",
    )
    package_go_paths = sorted(
        path for path, entry in entries.items()
        if PurePosixPath(path).parent.as_posix() == package_dir
        and path.endswith(".go")
        and isinstance(entry, dict)
        and entry.get("type") == "blob"
    )
    derived_go_files = [path for path in package_go_paths if not path.endswith("_test.go")]
    derived_test_go_files = [path for path in package_go_paths if path.endswith("_test.go")]
    require(
        go_list["go_files"] == derived_go_files
        and go_list["compiled_go_files"] == derived_go_files
        and go_list["test_go_files"] == derived_test_go_files
        and derived_go_files and derived_test_go_files,
        "M1-06 conformance go-list GoFiles/TestGoFiles differ from the exact package tree",
    )
    reported_package_blobs: dict[str, str] = {}
    for item in production:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            reported_package_blobs[item["path"]] = item.get("blob_sha")
    for item in cases:
        if isinstance(item, dict) and isinstance(item.get("source_path"), str):
            path = item["source_path"]
            blob_sha = item.get("source_blob_sha")
            require(
                path not in reported_package_blobs
                or reported_package_blobs[path] == blob_sha,
                "M1-06 conformance report gives one package path multiple blobs",
            )
            reported_package_blobs[path] = blob_sha
    for path, blob_sha in reported_package_blobs.items():
        require(
            isinstance(entries.get(path), dict)
            and entries[path].get("sha") == blob_sha,
            f"M1-06 reported package source differs from the implementation tree: {path}",
        )
    package_sources: dict[str, str] = {}
    for path in package_go_paths:
        entry = entries[path]
        source = source_blob(
            path, entry.get("sha"), entry.get("mode"), f"M1-06 package source {path}"
        )
        try:
            source_text = source.decode("utf-8")
        except UnicodeError as exc:
            raise ValidationError(f"M1-06 package source {path} is not UTF-8") from exc
        package_match = re.match(
            r"^\s*package\s+([A-Za-z_][A-Za-z0-9_]*)\b",
            go_code_projection(source_text),
        )
        require(
            go_source_path_is_unconditionally_build_eligible(path)
            and not re.search(
                r"(?m)^\s*//\s*(?:go:build|\+build)\b", source_text,
            )
            and package_match is not None
            and package_match.group(1) == go_list["package_name"],
            f"M1-06 package source {path} is build-excluded or package-mismatched",
        )
        require(
            "C" not in go_import_paths(source_text),
            f"M1-06 package source {path} uses unsupported cgo input",
        )
        package_sources[path] = source_text

    unsupported_suffixes = (
        ".c", ".cc", ".cpp", ".cxx", ".m", ".h", ".hh", ".hpp",
        ".f", ".F", ".for", ".f90", ".s", ".S", ".swig", ".swigcxx",
        ".syso",
    )
    require(
        not any(
            PurePosixPath(path).parent.as_posix() == package_dir
            and path.endswith(unsupported_suffixes)
            and isinstance(entry, dict) and entry.get("type") == "blob"
            for path, entry in entries.items()
        ),
        "M1-06 root package contains unsupported non-Go compiled inputs",
    )

    production_paths = [item.get("path") for item in production if isinstance(item, dict)]
    case_paths = [item.get("source_path") for item in cases if isinstance(item, dict)]
    require(
        all(path in derived_go_files for path in production_paths)
        and all(path in derived_test_go_files for path in case_paths),
        "M1-06 reported production/tests are outside exact go-list package files",
    )
    for path in derived_test_go_files:
        projection = go_code_projection(package_sources[path])
        for symbol in M1_06_PRODUCTION_SYMBOL_NAMES:
            declaration = (
                rf"(?m)^\s*type\s+{re.escape(symbol)}\b"
                if symbol in {"OpaqueRuntimeCapability", "TerminalOutcome"}
                else rf"(?m)^\s*func\s+(?:\([^\n)]*\)\s*)?{re.escape(symbol)}\s*\("
            )
            require(
                re.search(declaration, projection) is None,
                f"M1-06 test source locally redeclares production symbol {symbol}",
            )
    for test_function, _ in M1_06_CONFORMANCE_CASES.values():
        declarations = sum(
            len(re.findall(
                rf"(?m)^func\s+{re.escape(test_function)}\s*\(t\s+\*testing\.T\)\s*\{{",
                go_code_projection(package_sources[path]),
            ))
            for path in derived_test_go_files
        )
        require(
            declarations == 1,
            f"M1-06 conformance package must declare exactly one {test_function}",
        )

    bound_symbols: list[dict[str, str]] = []
    for item in production:
        require(isinstance(item, dict)
                and set(item) == {"path", "blob_sha", "mode", "symbols"}
                and isinstance(item.get("symbols"), list)
                and item["symbols"],
                "M1-06 conformance production entry schema mismatch")
        source = source_blob(item.get("path"), item.get("blob_sha"),
                             item.get("mode"), "M1-06 production source")
        try:
            text = source.decode("utf-8")
        except UnicodeError as exc:
            raise ValidationError("M1-06 production source is not UTF-8") from exc
        require(str(item["path"]).endswith(".go")
                and not str(item["path"]).endswith("_test.go")
                and item["path"] in package_sources,
                "M1-06 production source must be a production Go file")
        for symbol in item["symbols"]:
            require(
                isinstance(symbol, dict)
                and set(symbol) == {"name", "kind", "receiver", "signature"}
                and isinstance(symbol.get("name"), str)
                and isinstance(symbol.get("kind"), str)
                and isinstance(symbol.get("receiver"), str)
                and isinstance(symbol.get("signature"), str)
                and 0 < len(symbol["signature"].encode("utf-8")) <= 256,
                "M1-06 production symbol descriptor schema mismatch",
            )
            identity = {
                "name": symbol["name"],
                "kind": symbol["kind"],
                "receiver": symbol["receiver"],
            }
            require(identity in M1_06_PRODUCTION_SYMBOLS,
                    "M1-06 production source reports an unknown contract descriptor")
            projected = go_code_projection(text)
            if symbol["kind"] == "type":
                declaration = rf"(?m)^type\s+{re.escape(symbol['name'])}\b"
            elif symbol["kind"] == "function":
                declaration = rf"(?m)^func\s+{re.escape(symbol['name'])}\s*\("
            else:
                receiver = re.escape(symbol["receiver"]).replace(
                    r"\*", r"\s*\*\s*"
                )
                declaration = (
                    rf"(?m)^func\s*\(\s*(?:[A-Za-z_][A-Za-z0-9_]*\s+)?"
                    rf"{receiver}\s*\)\s*{re.escape(symbol['name'])}\s*\("
                )
            require(re.search(declaration, projected) is not None,
                    f"M1-06 production source lacks declared contract symbol: {identity}")
            bound_symbols.append(identity)
    require(tuple(bound_symbols) == M1_06_PRODUCTION_SYMBOLS,
            "M1-06 production contract descriptors are missing, reordered, or duplicated")

    case_ids: list[str] = []
    test_functions: set[str] = set()
    mutation_patch_digests: dict[str, str] = {}
    for item in cases:
        require(isinstance(item, dict) and set(item) == {
            "case_id", "test_function", "source_path", "source_blob_sha", "mode",
            "status", "mutation_patch_sha256",
        }, "M1-06 conformance case closed schema mismatch")
        case_id = item.get("case_id")
        mutation_patch_sha256 = item.get("mutation_patch_sha256")
        require(case_id in M1_06_CONFORMANCE_CASES and item.get("status") == "PASS"
                and isinstance(mutation_patch_sha256, str)
                and re.fullmatch(r"[0-9a-f]{64}", mutation_patch_sha256),
                "M1-06 conformance case ID or PASS status mismatch")
        test_function, required_calls = M1_06_CONFORMANCE_CASES[case_id]
        require(item.get("test_function") == test_function
                and test_function not in test_functions
                and isinstance(item.get("source_path"), str)
                and item["source_path"].endswith("_test.go")
                and item["source_path"] in package_sources,
                "M1-06 conformance case test function/path mismatch")
        source = source_blob(item.get("source_path"), item.get("source_blob_sha"),
                             item.get("mode"), f"M1-06 conformance case {case_id}")
        try:
            text = source.decode("utf-8")
        except UnicodeError as exc:
            raise ValidationError(f"M1-06 conformance case {case_id} source is not UTF-8") from exc
        body = go_function_body(text, test_function)
        require(body.strip()
                and re.search(r"\bt\.(?:Fatal|Fatalf|Error|Errorf|Fail|FailNow)\s*\(", body)
                and all(re.search(rf"\b{re.escape(call)}\s*\(", body)
                        for call in required_calls),
                f"M1-06 conformance case {case_id} is empty, assertion-free, or semantic no-op")
        case_ids.append(case_id)
        test_functions.add(test_function)
        mutation_patch_digests[case_id] = mutation_patch_sha256
    require(case_ids == list(M1_06_CONFORMANCE_CASES),
            "M1-06 conformance cases are missing, extra, or reordered")
    return (
        report_entry["sha"],
        M1_06_CONFORMANCE_CASE_DIGEST,
        mutation_patch_digests,
        set(production_paths),
    )


def require_m1_06_ci_local_job(repository: str, run_id: int, run_attempt: int,
                               job_id: int, check_run_id: int, head_sha: str,
                               *, expected_job_conclusion: str,
                               expected_ci_conclusion: str) -> None:
    jobs = github_paginated_object_rows(
        f"repos/{repository}/actions/runs/{run_id}/attempts/{run_attempt}/jobs",
        "jobs",
        "M1-06 workflow jobs",
    )
    matching = [job for job in jobs if isinstance(job, dict)
                and job.get("id") == job_id
                and job.get("name") == M1_06_CI_JOB_NAME]
    require(len(matching) == 1 and matching[0].get("head_sha") == head_sha
            and matching[0].get("status") == "completed"
            and matching[0].get("conclusion") == expected_job_conclusion
            and matching[0].get("check_run_url") == (
                f"https://api.github.com/repos/{repository}/check-runs/{check_run_id}"
            ),
            "M1-06 exact checks job identity, head, or conclusion mismatch")
    steps = matching[0].get("steps")
    require(isinstance(steps, list) and 2 <= len(steps) <= 64,
            "M1-06 checks job steps are invalid or unbounded")
    setup = [step for step in steps if isinstance(step, dict)
             and step.get("name") == M1_06_SETUP_STEP_NAME]
    ci_local = [step for step in steps if isinstance(step, dict)
                and step.get("name") == M1_06_CI_STEP_NAME]
    require(len(setup) == 1 and setup[0].get("status") == "completed"
            and setup[0].get("conclusion") == "success"
            and type(setup[0].get("number")) is int
            and len(ci_local) == 1 and ci_local[0].get("status") == "completed"
            and ci_local[0].get("conclusion") == expected_ci_conclusion
            and type(ci_local[0].get("number")) is int
            and setup[0]["number"] < ci_local[0]["number"],
            "M1-06 checks job must run ci_local after successful setup with exact outcome")


def require_m1_06_conformance_jobs(
    repository: str,
    run_id: int,
    run_attempt: int,
    head_sha: str,
    *,
    expected_test_conclusion: str,
    expected_job_ids: list[dict[str, Any]],
    expected_check_runs: list[dict[str, Any]],
) -> None:
    jobs = github_paginated_object_rows(
        f"repos/{repository}/actions/runs/{run_id}/attempts/{run_attempt}/jobs",
        "jobs",
        "M1-06 trusted conformance workflow jobs",
    )
    guard_jobs = [
        job for job in jobs
        if isinstance(job, dict)
        and job.get("id") == expected_job_ids[0]["job_id"]
        and job.get("name") == M1_06_RED_GUARD_JOB_NAME
    ]
    conformance_jobs = [
        job for job in jobs
        if isinstance(job, dict)
        and job.get("id") == expected_job_ids[1]["job_id"]
        and job.get("name") == M1_06_CONFORMANCE_JOB_NAME
    ]
    expected_job_conclusion = (
        "failure" if expected_test_conclusion == "failure" else "success"
    )
    require(
        len(guard_jobs) == 1
        and guard_jobs[0].get("head_sha") == head_sha
        and guard_jobs[0].get("status") == "completed"
        and guard_jobs[0].get("conclusion") == "success"
        and guard_jobs[0].get("check_run_url") == (
            f"https://api.github.com/repos/{repository}/check-runs/"
            f"{expected_check_runs[0]['check_run_id']}"
        )
        and len(conformance_jobs) == 1
        and conformance_jobs[0].get("head_sha") == head_sha
        and conformance_jobs[0].get("status") == "completed"
        and conformance_jobs[0].get("conclusion") == expected_job_conclusion
        and conformance_jobs[0].get("check_run_url") == (
            f"https://api.github.com/repos/{repository}/check-runs/"
            f"{expected_check_runs[1]['check_run_id']}"
        ),
        "M1-06 trusted RED guard or conformance job identity/outcome mismatch",
    )
    guard_steps = guard_jobs[0].get("steps")
    conformance_steps = conformance_jobs[0].get("steps")
    require(
        isinstance(guard_steps, list) and 1 <= len(guard_steps) <= 32
        and isinstance(conformance_steps, list) and 5 <= len(conformance_steps) <= 32,
        "M1-06 trusted conformance job steps are invalid or unbounded",
    )
    guard = [
        step for step in guard_steps
        if isinstance(step, dict) and step.get("name") == M1_06_RED_GUARD_STEP_NAME
    ]
    setup = [
        step for step in conformance_steps
        if isinstance(step, dict) and step.get("name") == M1_06_SETUP_STEP_NAME
    ]
    docs_lock = [
        step for step in conformance_steps
        if isinstance(step, dict) and step.get("name") == M1_06_DOCS_LOCK_STEP_NAME
    ]
    compile_step = [
        step for step in conformance_steps
        if isinstance(step, dict) and step.get("name") == M1_06_RED_COMPILE_STEP_NAME
    ]
    semantic_guard = [
        step for step in conformance_steps
        if isinstance(step, dict)
        and step.get("name") == M1_06_CONFORMANCE_GUARD_STEP_NAME
    ]
    test_step = [
        step for step in conformance_steps
        if isinstance(step, dict) and step.get("name") == M1_06_RED_TEST_STEP_NAME
    ]
    require(
        len(guard) == 1
        and guard[0].get("status") == "completed"
        and guard[0].get("conclusion") == "success"
        and len(docs_lock) == 1
        and docs_lock[0].get("status") == "completed"
        and docs_lock[0].get("conclusion") == "success"
        and len(setup) == 1
        and setup[0].get("status") == "completed"
        and setup[0].get("conclusion") == "success"
        and len(compile_step) == 1
        and compile_step[0].get("status") == "completed"
        and compile_step[0].get("conclusion") == "success"
        and len(semantic_guard) == 1
        and semantic_guard[0].get("status") == "completed"
        and semantic_guard[0].get("conclusion") == "success"
        and len(test_step) == 1
        and test_step[0].get("status") == "completed"
        and test_step[0].get("conclusion") == expected_test_conclusion
        and all(
            type(step[0].get("number")) is int
            for step in (guard, docs_lock, setup, compile_step, semantic_guard, test_step)
        )
        and docs_lock[0]["number"] < setup[0]["number"] < compile_step[0]["number"]
        < semantic_guard[0]["number"] < test_step[0]["number"],
        "M1-06 trusted workflow lacks ordered docs-lock/guard/compile/exact-test evidence",
    )


def require_m1_06_mutation_evidence(
    anchor: dict[str, Any],
    repository: str,
    head_sha: str,
    mutations: list[dict[str, Any]],
    expected_patch_digests: dict[str, str],
    production_paths: set[str],
    merged_at: datetime,
    not_before: datetime,
    trusted_workflow_id: int,
    trusted_harness_blobs: dict[str, str],
) -> tuple[str, datetime]:
    require(set(expected_patch_digests) == set(M1_06_MUTATION_CASES),
            "M1-06 mutation patch digest set differs from closed report")
    latest_time: datetime | None = None
    for mutation in mutations:
        case_id = mutation["case_id"]
        commit_sha = mutation["mutation_commit_sha"]
        run_id = mutation["workflow_run_id"]
        commit = github_api(f"repos/{repository}/git/commits/{commit_sha}")
        require(isinstance(commit, dict) and commit.get("sha") == commit_sha
                and isinstance(commit.get("parents"), list)
                and len(commit["parents"]) == 1
                and commit["parents"][0].get("sha") == head_sha,
                f"M1-06 mutation {case_id} is not an exact child of GREEN head")
        mutation_tree_sha = commit.get("tree", {}).get("sha")
        require(
            isinstance(mutation_tree_sha, str)
            and re.fullmatch(r"[0-9a-f]{40}", mutation_tree_sha),
            f"M1-06 mutation {case_id} tree identity is invalid",
        )
        mutation_blobs = github_tree_blob_map(
            repository, mutation_tree_sha, f"M1-06 mutation {case_id}"
        )
        require(
            all(
                mutation_blobs.get(path) == blob_sha
                for path, blob_sha in trusted_harness_blobs.items()
            ),
            f"M1-06 mutation {case_id} changed its trusted workflow or AST guard",
        )
        diff = github_api(f"repos/{repository}/commits/{commit_sha}?per_page=65&page=1")
        diff_page_2 = github_api(
            f"repos/{repository}/commits/{commit_sha}?per_page=65&page=2"
        )
        files = diff.get("files") if isinstance(diff, dict) else None
        require(isinstance(diff, dict) and diff.get("sha") == commit_sha
                and isinstance(files, list) and 0 < len(files) <= 8
                and isinstance(diff_page_2, dict)
                and diff_page_2.get("sha") == commit_sha
                and diff_page_2.get("files") == [],
                f"M1-06 mutation {case_id} diff is invalid or unbounded")
        paths: set[str] = set()
        patch_projection: list[dict[str, str]] = []
        for item in files:
            path = item.get("filename") if isinstance(item, dict) else None
            patch = item.get("patch") if isinstance(item, dict) else None
            require(isinstance(path, str) and path not in paths
                    and path.endswith(".go") and not path.endswith("_test.go")
                    and item.get("status") == "modified"
                    and type(item.get("changes")) is int
                    and 0 < item["changes"] <= 128
                    and isinstance(patch, str)
                    and 0 < len(patch.encode("utf-8")) <= 65536
                    and "\x00" not in patch,
                    f"M1-06 mutation {case_id} must be a bounded production-Go-only diff")
            paths.add(path)
            patch_projection.append({
                "filename": path,
                "status": "modified",
                "patch": patch,
            })
        patch_digest = hashlib.sha256(json.dumps(
            sorted(patch_projection, key=lambda item: item["filename"]),
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")).hexdigest()
        require(patch_digest == expected_patch_digests[case_id],
                f"M1-06 mutation {case_id} patch differs from closed GREEN report")
        require(
            paths <= production_paths,
            f"M1-06 mutation {case_id} changed a file outside report-bound production",
        )
        run_attempt = mutation["workflow_run_attempt"]
        run = github_api(
            f"repos/{repository}/actions/runs/{run_id}/attempts/{run_attempt}"
        )
        require(isinstance(run, dict) and run.get("id") == run_id
                and run.get("run_attempt") == mutation["workflow_run_attempt"]
                and run.get("workflow_id") == trusted_workflow_id
                and run.get("event") == "workflow_dispatch"
                and run.get("status") == "completed"
                and run.get("conclusion") == "failure"
                and run.get("head_sha") == commit_sha
                and run.get("path") == M1_06_MUTATION_WORKFLOW_PATH
                and run.get("actor", {}).get("login") == anchor["authorized_issuer"]
                and github_repository_identity(run.get("head_repository"), repository),
                f"M1-06 mutation {case_id} run is not exact-SHA hosted failure")
        run_url = f"https://github.com/{repository}/actions/runs/{run_id}"
        check_name = f"mutation/{case_id}"
        checks = github_all_check_runs(
            repository, commit_sha, f"M1-06 mutation {case_id} check runs"
        )
        selected_checks = [item for item in checks
                           if item.get("id") == mutation["check_run_id"]
                           if item.get("name") == check_name
                           and isinstance(item.get("app"), dict)
                           and item["app"].get("id") == GITHUB_ACTIONS_APP_ID]
        require(len(selected_checks) == 1
                and selected_checks[0].get("head_sha") == commit_sha
                and selected_checks[0].get("status") == "completed"
                and selected_checks[0].get("conclusion") == "failure"
                and isinstance(selected_checks[0].get("details_url"), str)
                and (selected_checks[0]["details_url"] == run_url
                     or selected_checks[0]["details_url"].startswith(run_url + "/")),
                f"M1-06 mutation {case_id} check is not exact-App exact-run failure")
        check_completed_at = parse_github_time(
            selected_checks[0].get("completed_at"),
            f"M1-06 mutation {case_id} check completed_at",
        )
        require(
            not_before < check_completed_at < merged_at,
            f"M1-06 mutation {case_id} check must complete before product merge",
        )
        jobs = github_paginated_object_rows(
            f"repos/{repository}/actions/runs/{run_id}/attempts/{run_attempt}/jobs",
            "jobs",
            f"M1-06 mutation {case_id} jobs",
        )
        selected_jobs = [job for job in jobs
                         if job.get("id") == mutation["job_id"]
                         and job.get("name") == check_name]
        require(len(selected_jobs) == 1
                and selected_jobs[0].get("head_sha") == commit_sha
                and selected_jobs[0].get("status") == "completed"
                and selected_jobs[0].get("conclusion") == "failure"
                and selected_jobs[0].get("check_run_url") == (
                    f"https://api.github.com/repos/{repository}/check-runs/"
                    f"{mutation['check_run_id']}"
                ),
                f"M1-06 mutation {case_id} job is not exact-SHA failure")
        steps = selected_jobs[0].get("steps")
        require(isinstance(steps, list) and 6 <= len(steps) <= 64,
                f"M1-06 mutation {case_id} job steps are invalid")
        docs_lock = [step for step in steps if isinstance(step, dict)
                     and step.get("name") == M1_06_DOCS_LOCK_STEP_NAME]
        setup = [step for step in steps if isinstance(step, dict)
                 and step.get("name") == M1_06_SETUP_STEP_NAME]
        ast_guard = [step for step in steps if isinstance(step, dict)
                     and step.get("name") == M1_06_MUTATION_AST_STEP_NAME]
        baseline = [step for step in steps if isinstance(step, dict)
                    and step.get("name") == f"baseline/{case_id}"]
        compile_step = [step for step in steps if isinstance(step, dict)
                        and step.get("name") == M1_06_MUTATION_COMPILE_STEP_NAME]
        test_step = [step for step in steps if isinstance(step, dict)
                     and step.get("name") == f"mutant/{case_id}"]
        require(len(docs_lock) == 1 and docs_lock[0].get("conclusion") == "success"
                and docs_lock[0].get("status") == "completed"
                and len(setup) == 1 and setup[0].get("conclusion") == "success"
                and setup[0].get("status") == "completed"
                and len(ast_guard) == 1
                and ast_guard[0].get("status") == "completed"
                and ast_guard[0].get("conclusion") == "success"
                and len(baseline) == 1
                and baseline[0].get("status") == "completed"
                and baseline[0].get("conclusion") == "success"
                and len(compile_step) == 1
                and compile_step[0].get("status") == "completed"
                and compile_step[0].get("conclusion") == "success"
                and len(test_step) == 1 and test_step[0].get("status") == "completed"
                and test_step[0].get("conclusion") == "failure"
                and type(docs_lock[0].get("number")) is int
                and type(setup[0].get("number")) is int
                and type(ast_guard[0].get("number")) is int
                and type(baseline[0].get("number")) is int
                and type(compile_step[0].get("number")) is int
                and type(test_step[0].get("number")) is int
                and docs_lock[0]["number"] < setup[0]["number"] < ast_guard[0]["number"]
                < baseline[0]["number"] < compile_step[0]["number"]
                < test_step[0]["number"],
                f"M1-06 mutation {case_id} lacked successful docs-lock/AST/baseline/compile proof before mapped failure")
        run_time = parse_github_time(run.get("updated_at"),
                                     f"M1-06 mutation {case_id} updated_at")
        require(not_before < run_time < merged_at,
                f"M1-06 mutation {case_id} evidence must follow harness merge and precede product merge")
        latest_time = run_time if latest_time is None else max(latest_time, run_time)
    digest = hashlib.sha256(json.dumps(
        mutations, sort_keys=True, separators=(",", ":"),
    ).encode("ascii")).hexdigest()
    assert latest_time is not None
    return digest, latest_time


def require_m1_06_producer_evidence(anchor: dict[str, Any],
                                    producer: dict[str, Any],
                                    dependency: dict[str, Any]) -> None:
    repository = MODBUS_REPOSITORY
    issue_number = producer["github_issue_number"]
    pr_number = producer["github_pull_request_number"]
    head_sha = dependency["head_sha"]
    head_tree_sha = dependency["head_tree_sha"]
    merge_sha = producer["merge_sha"]
    red_sha = producer["red_commit_sha"]
    issue = github_api(f"repos/{repository}/issues/{issue_number}")
    pr = github_api(f"repos/{repository}/pulls/{pr_number}")
    head_commit = github_api(f"repos/{repository}/git/commits/{head_sha}")
    merge_commit = github_api(f"repos/{repository}/git/commits/{merge_sha}")
    require(isinstance(issue, dict) and issue.get("number") == issue_number
            and issue.get("repository_url") == f"https://api.github.com/repos/{repository}"
            and issue.get("title") == M1_06_PRODUCER_ISSUE_TITLE
            and issue.get("state") == "closed" and not issue.get("pull_request")
            and isinstance(issue.get("body"), str)
            and issue["body"].count(M1_06_PRODUCER_ISSUE_MARKER) == 1,
            "M1-06 producer issue immutable marker/title/identity mismatch")
    require(isinstance(pr, dict) and pr.get("number") == pr_number
            and pr.get("title") == M1_06_PRODUCER_PULL_REQUEST_TITLE
            and pr.get("merged") is True and pr.get("state") == "closed"
            and pr.get("merge_commit_sha") == merge_sha
            and pr.get("head", {}).get("sha") == head_sha
            and github_repository_identity(pr.get("head", {}).get("repo"), repository)
            and isinstance(pr.get("head", {}).get("ref"), str)
            and re.fullmatch(rf"issue/{issue_number}-[a-z0-9]+(?:-[a-z0-9]+)*",
                             pr["head"]["ref"])
            and pr.get("base", {}).get("ref") == "main"
            and isinstance(pr.get("body"), str)
            and pull_request_body_closing_refs(pr["body"]) == [f"#{issue_number}"]
            and github_repository_identity(pr.get("base", {}).get("repo"), repository),
            "M1-06 producer exact closing PR or canonical base/head mismatch")
    issue_created_at = parse_github_time(
        issue.get("created_at"), "M1-06 producer issue created_at"
    )
    issue_closed_at = parse_github_time(
        issue.get("closed_at"), "M1-06 producer issue closed_at"
    )
    product_created_at = parse_github_time(
        pr.get("created_at"), "M1-06 producer PR created_at"
    )
    producer_merged_at = parse_github_time(
        pr.get("merged_at"), "M1-06 producer merged_at"
    )
    require(
        issue_created_at <= product_created_at <= producer_merged_at <= issue_closed_at,
        "M1-06 producer PR interval is outside the selected issue interval",
    )
    require_plan_owned_repository_mutex(
        repository, issue_number, pr_number, completion=True,
    )
    require(isinstance(head_commit, dict) and head_commit.get("sha") == head_sha
            and head_commit.get("tree", {}).get("sha") == head_tree_sha
            and head_commit.get("message") != M1_06_RED_COMMIT_SUBJECT
            and isinstance(merge_commit, dict) and merge_commit.get("sha") == merge_sha
            and merge_commit.get("tree", {}).get("sha") == head_tree_sha
            and isinstance(merge_commit.get("parents"), list)
            and len(merge_commit["parents"]) == 1
            and merge_commit["parents"][0].get("sha") == pr.get("base", {}).get("sha"),
            "M1-06 reviewed implementation head/squash tree or base topology mismatch")

    trusted_workflow_id, trusted_harness_blobs, harness_merged_at = (
        require_m1_06_harness_evidence(
        anchor,
        producer,
        pr,
        head_tree_sha,
        dependency["required_checks"],
        )
    )

    red_commit = github_api(f"repos/{repository}/git/commits/{red_sha}")
    red_diff = github_api(
        f"repos/{repository}/commits/{red_sha}?per_page=65&page=1"
    )
    red_diff_page_2 = github_api(
        f"repos/{repository}/commits/{red_sha}?per_page=65&page=2"
    )
    red_compare = github_api(f"repos/{repository}/compare/{red_sha}...{head_sha}")
    require(isinstance(red_commit, dict) and red_commit.get("sha") == red_sha
            and red_commit.get("message") == M1_06_RED_COMMIT_SUBJECT
            and isinstance(red_commit.get("parents"), list)
            and len(red_commit["parents"]) == 1
            and red_commit["parents"][0].get("sha") == producer["harness_merge_sha"],
            "M1-06 RED commit identity/topology mismatch")
    require(isinstance(red_compare, dict) and red_compare.get("status") == "ahead"
            and red_compare.get("merge_base_commit", {}).get("sha") == red_sha,
            "M1-06 test-only RED commit is not an ancestor of the implementation head")
    files = red_diff.get("files") if isinstance(red_diff, dict) else None
    require(isinstance(red_diff, dict) and red_diff.get("sha") == red_sha
            and isinstance(files, list) and 0 < len(files) <= 64,
            "M1-06 RED commit diff response is invalid or outside bounds")
    require(isinstance(red_diff_page_2, dict)
            and red_diff_page_2.get("sha") == red_sha
            and red_diff_page_2.get("files") == [],
            "M1-06 RED commit diff page 2 must be empty")
    red_paths: set[str] = set()
    has_test = False
    for item in files:
        require(isinstance(item, dict) and isinstance(item.get("filename"), str)
                and item["filename"] not in red_paths
                and item.get("status") in {"added", "modified"}
                and type(item.get("changes")) is int
                and 0 < item["changes"] <= 10000
                and require_m1_06_red_path(item["filename"]),
                "M1-06 RED commit contains a non-test, unbounded, or invalid diff path")
        red_paths.add(item["filename"])
        has_test = has_test or item["filename"].endswith("_test.go")
    require(has_test, "M1-06 RED commit must add or modify at least one Go test")

    red_run_id = producer["red_workflow_run_id"]
    red_attempt = producer["red_workflow_run_attempt"]
    red_run = github_api(
        f"repos/{repository}/actions/runs/{red_run_id}/attempts/{red_attempt}"
    )
    run_prs = red_run.get("pull_requests") if isinstance(red_run, dict) else None
    require(isinstance(red_run, dict) and red_run.get("id") == red_run_id
            and red_run.get("run_attempt") == producer["red_workflow_run_attempt"]
            and red_run.get("workflow_id") == trusted_workflow_id
            and red_run.get("path") == M1_06_MUTATION_WORKFLOW_PATH
            and red_run.get("event") == "pull_request"
            and red_run.get("status") == "completed"
            and red_run.get("conclusion") == "failure"
            and red_run.get("head_sha") == red_sha
            and github_repository_identity(red_run.get("head_repository"), repository)
            and isinstance(run_prs, list) and len(run_prs) == 1
            and run_prs[0].get("number") == pr_number
            and run_prs[0].get("base", {}).get("ref") == "main"
            and github_repository_identity(run_prs[0].get("base", {}).get("repo"), repository)
            and run_prs[0].get("head", {}).get("sha") == red_sha
            and run_prs[0].get("head", {}).get("ref") == pr.get("head", {}).get("ref")
            and github_repository_identity(run_prs[0].get("head", {}).get("repo"), repository),
            "M1-06 hosted RED run did not fail on the exact RED SHA and PR")
    red_completed_at = parse_github_time(
        red_run.get("updated_at"), "M1-06 RED run updated_at"
    )
    require(
        harness_merged_at < red_completed_at < producer_merged_at,
        "M1-06 RED proof must follow harness merge and precede product merge",
    )
    red_checks = github_all_check_runs(
        repository, red_sha, "M1-06 hosted RED check runs"
    )
    run_url = f"https://github.com/{repository}/actions/runs/{red_run_id}"
    red_selectors = {
        item["context"]: item for item in producer["red_check_runs"]
    }
    matching_red_checks = {
        name: matches[0]
        for name, selector in red_selectors.items()
        if len(matches := [
            item for item in red_checks if isinstance(item, dict)
            and item.get("id") == selector["check_run_id"]
            and item.get("name") == name
            and item.get("app", {}).get("id") == selector["app_id"]
        ]) == 1
    }
    require(
        set(matching_red_checks) == {
            M1_06_RED_GUARD_JOB_NAME, M1_06_CONFORMANCE_JOB_NAME,
        }
        and matching_red_checks[M1_06_RED_GUARD_JOB_NAME].get("conclusion") == "success"
        and matching_red_checks[M1_06_CONFORMANCE_JOB_NAME].get("conclusion") == "failure"
        and all(
            row.get("head_sha") == red_sha
            and row.get("status") == "completed"
            and isinstance(row.get("details_url"), str)
            and (row["details_url"] == run_url
                 or row["details_url"].startswith(run_url + "/"))
            for row in matching_red_checks.values()
        )
        and all(
            harness_merged_at < parse_github_time(
                row.get("completed_at"), f"M1-06 RED {name} completed_at"
            ) < producer_merged_at
            for name, row in matching_red_checks.items()
        ),
        "M1-06 hosted RED checks are not trusted exact-run guard/pass plus conformance/fail",
    )
    require_m1_06_conformance_jobs(
        repository, red_run_id, red_attempt, red_sha,
        expected_test_conclusion="failure",
        expected_job_ids=producer["red_job_ids"],
        expected_check_runs=producer["red_check_runs"],
    )

    green_rows = require_exact_head_checks(
        repository,
        head_sha,
        dependency["required_checks"],
        "M1-06 hosted GREEN",
        completed_before=producer_merged_at,
        bound_runs=dependency["required_check_runs"],
    )
    green_completed_at = max(parse_github_time(
        item.get("completed_at"), f"M1-06 GREEN {item.get('name')} completed_at"
    ) for item in green_rows)
    green_run_id = producer["green_workflow_run_id"]
    green_attempt = producer["green_workflow_run_attempt"]
    green_run = github_api(
        f"repos/{repository}/actions/runs/{green_run_id}/attempts/{green_attempt}"
    )
    green_prs = green_run.get("pull_requests") if isinstance(green_run, dict) else None
    require(isinstance(green_run, dict) and green_run.get("id") == green_run_id
            and green_run.get("run_attempt") == producer["green_workflow_run_attempt"]
            and green_run.get("workflow_id") == trusted_workflow_id
            and green_run.get("path") == M1_06_MUTATION_WORKFLOW_PATH
            and green_run.get("event") == "pull_request"
            and green_run.get("status") == "completed"
            and green_run.get("conclusion") == "success"
            and green_run.get("head_sha") == head_sha
            and github_repository_identity(green_run.get("head_repository"), repository)
            and isinstance(green_prs, list) and len(green_prs) == 1
            and green_prs[0].get("number") == pr_number
            and green_prs[0].get("base", {}).get("ref") == "main"
            and github_repository_identity(green_prs[0].get("base", {}).get("repo"), repository)
            and green_prs[0].get("head", {}).get("sha") == head_sha
            and green_prs[0].get("head", {}).get("ref") == pr.get("head", {}).get("ref")
            and github_repository_identity(green_prs[0].get("head", {}).get("repo"), repository),
            "M1-06 hosted GREEN run is not exact-head exact-PR success")
    green_run_completed_at = parse_github_time(
        green_run.get("updated_at"), "M1-06 GREEN run updated_at"
    )
    require(
        harness_merged_at < green_run_completed_at < producer_merged_at,
        "M1-06 GREEN workflow must follow harness merge and precede product merge",
    )
    green_run_url = f"https://github.com/{repository}/actions/runs/{green_run_id}"
    green_all_checks = github_all_check_runs(
        repository, head_sha, "M1-06 trusted GREEN check runs"
    )
    green_selectors = {
        item["context"]: item for item in producer["green_check_runs"]
    }
    green_conformance_checks = {
        name: matches[0]
        for name, selector in green_selectors.items()
        if len(matches := [
            item for item in green_all_checks if isinstance(item, dict)
            and item.get("id") == selector["check_run_id"]
            and item.get("name") == name
            and item.get("app", {}).get("id") == selector["app_id"]
        ]) == 1
    }
    require(
        set(green_conformance_checks) == {
            M1_06_RED_GUARD_JOB_NAME, M1_06_CONFORMANCE_JOB_NAME,
        }
        and all(
            row.get("head_sha") == head_sha
            and row.get("status") == "completed"
            and row.get("conclusion") == "success"
            and isinstance(row.get("details_url"), str)
            and (row["details_url"] == green_run_url
                 or row["details_url"].startswith(green_run_url + "/"))
            for row in green_conformance_checks.values()
        )
        and all(
            harness_merged_at < parse_github_time(
                row.get("completed_at"), f"M1-06 GREEN {name} completed_at"
            ) < producer_merged_at
            for name, row in green_conformance_checks.items()
        ),
        "M1-06 trusted GREEN checks are not exact-run successes",
    )
    require_m1_06_conformance_jobs(
        repository, green_run_id, green_attempt, head_sha,
        expected_test_conclusion="success",
        expected_job_ids=producer["green_job_ids"],
        expected_check_runs=producer["green_check_runs"],
    )
    report_blob_sha, case_digest, mutation_patch_digests, report_production_paths = (
        require_m1_06_conformance_report(
        repository, head_tree_sha
        )
    )
    mutation_digest, mutations_completed_at = require_m1_06_mutation_evidence(
        anchor, repository, head_sha, producer["mutation_runs"],
        mutation_patch_digests, report_production_paths, producer_merged_at,
        harness_merged_at,
        trusted_workflow_id, trusted_harness_blobs,
    )
    review_not_before = max(
        green_completed_at,
        green_run_completed_at,
        mutations_completed_at,
    )

    reviews = github_paginated_list(
        f"repos/{repository}/pulls/{pr_number}/reviews",
        "M1-06 producer reviews",
    )
    official = [review for review in reviews if isinstance(review, dict)
                and review.get("id") == producer["official_review_id"]]
    exact_head_codex = [review for review in reviews if isinstance(review, dict)
                        and review.get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
                        and review.get("commit_id") == head_sha]
    require(len(official) == 1
            and len(exact_head_codex) == 1
            and exact_head_codex[0].get("id") == producer["official_review_id"]
            and official[0].get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
            and official[0].get("state") == "COMMENTED"
            and official[0].get("commit_id") == head_sha
            and official[0].get("body") == canonical_codex_review_body(head_sha)
            and parse_github_time(official[0].get("submitted_at"),
                                  "M1-06 official Codex submitted_at") > review_not_before
            and parse_github_time(official[0].get("submitted_at"),
                                  "M1-06 official Codex submitted_at") < producer_merged_at,
            "M1-06 official Codex exact-head review is missing, stale, or not after GREEN and mutation evidence")
    inline = github_paginated_list(
        f"repos/{repository}/pulls/{pr_number}/reviews/{producer['official_review_id']}/comments",
        "M1-06 official Codex inline comments",
    )
    require(not inline, "M1-06 official Codex exact-head review has inline findings")
    owner_reviews: list[tuple[str, str]] = []
    for review_id in producer["owner_review_ids"]:
        selected = [review for review in reviews if isinstance(review, dict)
                    and review.get("id") == review_id]
        require(len(selected) == 1, "M1-06 owner review selector is missing or ambiguous")
        review = selected[0]
        body = unique_json_object(str(review.get("body", "")), "M1-06 owner review body")
        require(review.get("user", {}).get("login") == anchor["authorized_issuer"]
                and review.get("author_association") in anchor["allowed_author_associations"]
                and review.get("state") == "COMMENTED"
                and review.get("commit_id") == head_sha
                and parse_github_time(review.get("submitted_at"),
                                      "M1-06 owner review submitted_at") > review_not_before
                and parse_github_time(review.get("submitted_at"),
                                      "M1-06 owner review submitted_at") < producer_merged_at
                and set(body) == {
                    "schema", "repository", "pull_request", "plan_issue",
                    "red_commit_sha", "head_sha", "head_tree_sha", "verdict",
                    "attestation_kind", "review_process", "reviewer_run_reference",
                    "output_digest_sha256",
                    "conformance_report_blob_sha", "conformance_case_digest",
                    "mutation_evidence_sha256",
                }
                and body.get("schema") == M1_06_OWNER_REVIEW_SCHEMA
                and body.get("repository") == repository
                and body.get("pull_request") == pr_number
                and body.get("plan_issue") == "FMV3-M1-06"
                and body.get("red_commit_sha") == red_sha
                and body.get("head_sha") == head_sha
                and body.get("head_tree_sha") == head_tree_sha
                and body.get("conformance_report_blob_sha") == report_blob_sha
                and body.get("conformance_case_digest") == case_digest
                and body.get("mutation_evidence_sha256") == mutation_digest
                and body.get("verdict") == "NO_FINDINGS"
                and body.get("attestation_kind") == "owner_process_attestation"
                and body.get("review_process") == "fresh_openai_context"
                and isinstance(body.get("reviewer_run_reference"), str)
                and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", body["reviewer_run_reference"])
                and isinstance(body.get("output_digest_sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", body["output_digest_sha256"]),
                "M1-06 owner review is not structured owner-attested exact-head NO_FINDINGS process evidence after GREEN and mutations")
        owner_reviews.append((body["reviewer_run_reference"], body["output_digest_sha256"]))
    require(len({run_id for run_id, _ in owner_reviews}) == 2
            and len({output for _, output in owner_reviews}) == 2,
            "M1-06 requires two distinct owner fresh-review runs and outputs")


def require_static_dependency_completion(issue_id: str, binding: dict[str, Any]) -> None:
    if binding.get("kind") == "docs_candidate_completion":
        repository = binding["repository"]
        issue_number = binding["github_issue_number"]
        pr_number = binding["github_pull_request_number"]
        issue = github_api(f"repos/{repository}/issues/{issue_number}")
        pr = github_api(f"repos/{repository}/pulls/{pr_number}")
        timeline = github_paginated_list(
            f"repos/{repository}/issues/{issue_number}/timeline",
            "FMV3-M1-05 docs issue timeline",
        )
        require(isinstance(issue, dict) and issue.get("number") == issue_number
                and issue.get("repository_url") == f"https://api.github.com/repos/{repository}"
                and issue.get("title") == binding["issue_title"]
                and issue.get("state") == "closed" and not issue.get("pull_request"),
                "FMV3-M1-05 docs issue #385 identity/title/closure mismatch")
        require(isinstance(pr, dict) and pr.get("number") == pr_number
                and pr.get("title") == binding["pull_request_title"]
                and pr.get("state") == "closed" and pr.get("merged") is True
                and pr.get("base", {}).get("ref") == "main"
                and github_repository_identity(pr.get("base", {}).get("repo"), repository)
                and github_repository_identity(pr.get("head", {}).get("repo"), repository),
                "FMV3-M1-05 docs closing PR #386 identity mismatch")
        require(isinstance(pr.get("body"), str)
                and re.search(r"(?im)^\s*(?:[-*]\s*)?(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#385\s*[.]?\s*$", pr["body"]),
                "FMV3-M1-05 docs PR #386 does not close exact issue #385")
        require_issue_closed_by_pull_request(
            repository, issue_number, issue, pr_number, pr, "FMV3-M1-05",
        )
        require(any(
            isinstance(event, dict) and event.get("event") == "cross-referenced"
            and event.get("source", {}).get("issue", {}).get("number") == pr_number
            and event.get("source", {}).get("issue", {}).get("pull_request", {}).get("url")
            == f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
            and event.get("source", {}).get("issue", {}).get("pull_request", {}).get("merged_at")
            == pr.get("merged_at")
            for event in timeline),
            "FMV3-M1-05 docs issue #385 lacks exact PR #386 timeline relation")
        return
    if binding.get("kind") != "manual_repository_creation":
        require_pull_request_completion(issue_id, binding, dynamic_policy=False)
        return
    repository = binding["repository"]
    issue = github_api(f"repos/{repository}/issues/{binding['github_issue_number']}")
    timeline = github_api(f"repos/{repository}/issues/{binding['github_issue_number']}/timeline?per_page=100")
    comment = github_api(f"repos/{repository}/issues/comments/{binding['completion_comment_id']}")
    require(isinstance(issue, dict) and issue.get("repository_url") == f"https://api.github.com/repos/{repository}"
            and issue.get("number") == binding["github_issue_number"]
            and issue.get("title") == binding["issue_title"] and issue.get("state") == "closed"
            and issue.get("closed_at") == binding["closed_at"],
            f"static completion binding is stale or wrong for {issue_id}")
    require(isinstance(timeline, list) and sum(
        isinstance(event, dict) and event.get("event") == "closed"
        and event.get("created_at") == binding["closed_at"]
        and event.get("actor", {}).get("login") == binding["closed_by"]
        for event in timeline) == 1, f"{issue_id} exact manual closure event mismatch")
    require(isinstance(comment, dict) and comment.get("id") == binding["completion_comment_id"]
            and comment.get("user", {}).get("login") == binding["closed_by"]
            and comment.get("created_at") == comment.get("updated_at")
            and hashlib.sha256(str(comment.get("body", "")).encode()).hexdigest()
            == binding["completion_comment_sha256"],
            f"{issue_id} exact manual completion attestation mismatch")


def require_direct_dependency_completion(
    issue_id: str,
    issue_deps: dict[str, list[str]],
    issue_repos: dict[str, str],
    issue_specs: dict[str, dict[str, Any]],
    certificates: list[dict[str, Any]],
) -> None:
    direct = issue_deps[issue_id]
    static = [dependency for dependency in direct if dependency in COMPLETED_FMV3_DEPENDENCIES]
    future = [dependency for dependency in direct
              if dependency not in COMPLETED_FMV3_DEPENDENCIES]
    for dependency in static:
        require_static_dependency_completion(
            dependency, COMPLETED_FMV3_DEPENDENCIES[dependency]
        )
    certificate_ids = [item["plan_issue"] for item in certificates]
    require(len(certificate_ids) == len(set(certificate_ids)),
            "dependency completion certificate contains duplicate predecessors")
    require(set(certificate_ids) == set(future),
            f"dependency completion certificates must equal direct unresolved predecessors for {issue_id}")
    for certificate in certificates:
        require(certificate["repository"] == issue_repos[certificate["plan_issue"]],
                f"dependency {certificate['plan_issue']} repository differs from plan topology")
        require_pull_request_completion(certificate["plan_issue"], certificate,
                                        dynamic_policy=True,
                                        issue_spec=issue_specs[certificate["plan_issue"]])
        if certificate["plan_issue"] == "FMV3-M3-03":
            require_m3_03_completion_artifact(
                certificate["repository"], certificate,
            )


def require_issue_authorization_dependencies(
    issue_id: str,
    anchor: dict[str, Any],
    evidence_path: str | None,
    issue_deps: dict[str, list[str]],
    issue_repos: dict[str, str],
    issue_specs: dict[str, dict[str, Any]],
) -> None:
    require(
        anchor.get("issue_evidence_policy") == EXPECTED_ISSUE_EVIDENCE_POLICY,
        "issue authorization evidence policy mismatch",
    )
    certificates, producer = load_issue_authorization_evidence(evidence_path, issue_id)
    require_direct_dependency_completion(
        issue_id, issue_deps, issue_repos, issue_specs, certificates
    )
    if issue_id in {"FMV3-M1-06", "FMV3-M2-01"}:
        require_docs_candidate_pr_merged(anchor)
    if producer is not None:
        matching = [item for item in certificates if item["plan_issue"] == "FMV3-M1-06"]
        require(len(matching) == 1 and all(
            producer[key] == matching[0][key]
            for key in ("plan_issue", "repository", "github_issue_number",
                        "github_pull_request_number", "merge_sha")),
            "M1-06 producer extension differs from its dependency certificate")
        require_m1_06_producer_evidence(anchor, producer, matching[0])
    r2_rebind = anchor["docs_candidate_binding"]["r2_rebind"]
    require(
        r2_rebind["status"] == "BOUND_DOCS_R2"
        and issue_id not in r2_rebind["blocks_authorization_for"],
        "authorization blocked: exact docs R2 binding is incomplete",
    )
def require_m1_admission_open(repo_root: Path, origin_main: str) -> None:
    gate_path = repo_root / M1_ADMISSION_GATE
    require(gate_path.is_file() and not gate_path.is_symlink(), "Modbus M1 admission gate is missing")
    committed_gate = git_command(
        repo_root,
        ["show", f"HEAD:{M1_ADMISSION_GATE.as_posix()}"],
        "Modbus M1 admission gate blob read",
        text=False,
    )
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
    git_command(
        repo_root,
        ["merge-base", "--is-ancestor", gate["trust_anchor_commit"], origin_main],
        "Modbus trust anchor ancestry check",
    )
    anchor_script = git_command(
        repo_root,
        ["show", f"{gate['trust_anchor_commit']}:scripts/validate_modbus_docs_trust.py"],
        "Modbus trust anchor script read",
        text=False,
    )
    require(anchor_script, "Modbus trust anchor script is absent from its merged commit")
    require(
        hashlib.sha256(anchor_script).hexdigest()
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
    checks = live_required_check_specs(
        protection, "Modbus M1 required-check policy",
    )
    require(
        (gate["required_check"], GITHUB_ACTIONS_APP_ID) in checks,
        "Modbus Trusted Revision is not pinned to the GitHub Actions App",
    )
    runs = github_latest_check_runs(
        DOCS_REPOSITORY,
        gate["verification_head_sha"],
        "Modbus M1 verification check runs",
    )
    require(
        any(
            isinstance(run, dict)
            and run.get("name") == gate["required_check"]
            and run.get("conclusion") == "success"
            and isinstance(run.get("app"), dict)
            and run["app"].get("id") == GITHUB_ACTIONS_APP_ID
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
                anchor_script.decode("utf-8"),
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
        "preflight_enforcement": "fetch full history reachable from exact canonical main into an owner-private checkout without caller Git config, materialize authorization_anchor.tooling_binding.validator_path from --plan-head-sha, verify its anchored SHA-256 and pinned Git/GitHub CLI allowlist, then materialize and execute the exact-hash model router/policy in openai_only mode for the selected issue role, complexity, and mapped risks without any caller-asserted runtime-capability override; execute the validator with --materialized-anchor-validator --authorize-issue <ID> --github-issue-number <N> --claim-run-id <UUID> --claim-owner-secret-file <0400> plus the canonical issue/anchor-bound non-degraded routing prescription receipt; a max-required route therefore remains capability-degraded and authorization fails until a future anchored extension verifies provider-produced immutable execution evidence; the anchored owner login, owner-secret commitment, exact live integrity/writer claim-namespace rulesets, and routing receipt are mandatory; authorization PASS logs the resolved profile/model/effort and returns one repository-scoped protected append-only remote Git-ref CAS fence after the exact open issue and zero-open-PR recheck; standalone --verify-claim is diagnostic only, while protected GitHub REST mutation requires --fenced-gh-api with the exact current --claim-sha, one explicit issue-bound mutation capability, validation of retained in-memory payload bytes sent only via stdin, the stable host-local kernel process lock plus owner-secret inode lock, exact pre/post fence verification after every attempted mutation child exit including interruption, and an exact selected-issue plus capability-specific open-PR mutex snapshot in both phases; any nonzero mutation result, child interruption/exception, or post-verification failure is completion-ambiguous and forces STOP without retry plus reconciliation; all required-status contexts must map to positive-App-ID checks, every completion certificate must bind exact pre-merge check-run IDs, and docs review evidence requires two strict unique lowercase UUIDs plus independently unique output digests; --renew-claim appends a successor from the exact presented SHA and --release-claim appends a fast-forward tombstone",
        "routing_gate": {
            "schema": ROUTING_RECEIPT_SCHEMA,
            "router_sha256": MODEL_ROUTER_SHA256,
            "policy_sha256": MODEL_ROUTING_POLICY_SHA256,
            "availability_mode": "openai_only",
            "session_orchestrator_vendor": "openai",
            "availability": {"openai": True, "anthropic": False},
            "max_profile_policy": "caller_assertions_forbidden_provider_produced_immutable_execution_evidence_extension_required",
            "autonomous": True,
            "role_policy": {
                DOCS_REPOSITORY: "docs_architecture", "default": "developer",
            },
            "gate_risk_map": ROUTING_GATE_RISK_MAP,
            "receipt_binding": [
                "issue_id", "repository", "complexity", "risks",
                "plan_anchor", "router_sha256", "policy_sha256", "route",
            ],
            "runtime_scope": "routing_prescription_only_no_runtime_capability_or_model_identity_claim",
            "failure": "missing_mismatched_underpowered_or_capability_degraded_blocks_authorization",
        },
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
                "routing_gate",
                "docs_candidate_binding",
                "tooling_binding",
                "pull_request_identity",
                "external_review_attestation",
                "issue_evidence_policy",
                "direct_dependency_completion",
                "accepted_decision_d13",
                "m2_exit_gate",
            ],
            "corrected_issues": ["FMV3-M1-05", "FMV3-M1-06", "FMV3-M2-01"],
            "docs_candidate_binding": EXPECTED_DOCS_CANDIDATE_BINDING,
            "tooling_binding": anchor.get("tooling_binding"),
            "pull_request_identity": EXPECTED_PR_IDENTITY,
            "external_review_attestation": EXPECTED_EXTERNAL_REVIEW_ATTESTATION,
            "issue_evidence_policy": EXPECTED_ISSUE_EVIDENCE_POLICY,
            "direct_dependency_completion": "exact_static_live_github_bindings_for_completed_predecessors_plus_bounded_github_authenticated_certificate_bound_to_anchored_issue_spec_for_future_direct_predecessors",
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
        "m1_06_template_sha256": M1_06_TEMPLATE_SHA256,
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


def validate_review_repair_semantics(
    plan: dict[str, Any], texts: dict[str, str]
) -> None:
    lifecycle_fragments = (
        "unresolved -> claim_in_progress",
        "claim_succeeded",
        "capability_cancelled",
        "capability_failed",
        "capability_expired",
        "claim_rejected_terminal",
        "open -> sealed|cancelling",
        "sealed -> publishing|cancelling",
        "cancelling -> cancelled",
    )
    for name in ("00-canonical.md", "10-architecture-and-repo-boundaries.md"):
        text = texts[name]
        require(
            all(fragment in text for fragment in lifecycle_fragments),
            f"{name} omits the corrected claim/attempt lifecycle",
        )
        require(
            re.search(
                r"unresolved\s*(?:->|to)\s*(?:claim_succeeded|capability_(?:cancelled|failed|expired)|claim_rejected_terminal)",
                text,
            ) is None,
            f"{name} reintroduces a forbidden direct unresolved terminal transition",
        )
    architecture = texts["10-architecture-and-repo-boundaries.md"]
    require(
        "One official Codex" in architecture
        and "two owner `NO_FINDINGS` process attestations" in architecture,
        "architecture review cardinality no longer matches the authorization contract",
    )
    issues = {
        issue.get("id"): issue
        for issue in plan.get("issues", [])
        if isinstance(issue, dict)
    }
    m1_02_rollback = str(issues.get("FMV3-M1-02", {}).get("rollback", ""))
    require(
        m1_02_rollback
        == "Disable or revert the unpublished TCP runtime entry point and restore or pin the preceding helianthus-modbus revision; do not touch gateway artifacts or persisted gateway state.",
        "FMV3-M1-02 rollback crosses into the unauthorized gateway repository",
    )
    m3_03 = issues.get("FMV3-M3-03", {})
    m3_text = " ".join((str(m3_03.get("what", "")), str(m3_03.get("acceptance", ""))))
    require(
        "Modbus TCP is only the phase-1 evidence and acquisition path" in m3_text
        and "overlay code remains transport-neutral" in m3_text
        and "cannot import TCP types or gate activation on TCP" in m3_text
        and "fixed import-boundary test" in m3_text
        and "exact executable fail-closed runtime source scanner" in m3_text
        and "including build-constrained and implicitly excluded filenames" in m3_text
        and "returns directory/read/parse/unquote errors to t.Fatal" in m3_text
        and m3_03.get("transport_neutrality_gate", {}).get("runtime_scanner_contract")
        == "runtime_caller_filepath_dir_absolute_immutable_source_directory_scan"
        and "validator-pinned transport-neutral standard-library allowlist" in m3_text
        and "module-local, third-party, and every other import fail closed" in m3_text
        and "zero-field non-TCP fake with a compile-time assertion" in m3_text
        and m3_03.get("transport_neutrality_gate") == {
            "forbidden_import_test": "TestFroniusOverlayRejectsTCPConcreteImports",
            "neutral_activation_test": "TestFroniusOverlayActivatesThroughNeutralRuntime",
            "production_package_helper": "froniusOverlayProductionPackages",
            "tcp_import_predicate_helper": "hasTCPConcreteImport",
            "runtime_import_scanner": "exact_fail_closed_immutable_source_directory_production_go_source_scan",
            "runtime_scanner_contract": "runtime_caller_filepath_dir_absolute_immutable_source_directory_scan",
            "neutral_runtime_fake": "neutralRuntimeNoTCP",
            "neutral_activation_helper": "activateFroniusProfile",
            "required_for_dispositions": ["STANDARD_ONLY", "OVERLAY_REQUIRED"],
        },
        "FMV3-M3-03 no longer keeps the vendor overlay transport-neutral",
    )
    require(m3_03.get("completion_evidence_contract") == {
        "schema": "helianthus.fmv3-m3-03-completion.v2",
        "bind": ["head_sha", "head_tree_sha", "disposition", "fixed_profiles_fronius_namespace_scan", "canonical_disposition_bound_named_test_source_blob", "artifact_named_test_sources_no_init_or_testmain", "complete_go_import_literal_unquote_and_unicode_alias_scan", "executable_fail_closed_runtime_import_scanner", "sealed_transport_neutral_direct_import_allowlist", "semicolon_import_declaration_rejection", "disposition_bound_minimal_neutral_adapter", "overlay_separate_production_implementation_source_without_init_or_test_only_symbols_or_constraints", "zero_field_fake_compile_time_interface_assertion", "sentinel_result_control_flow", "closed_canonical_named_test_bodies", "exact_top_level_permissions_contents_read", "executable_head_and_tree_assertion", "exact_preparation_deletes_all_other_direct_test_sources", "exact_standalone_production_build_before_tests", "activation_first_and_import_second_exact_commands", "conditional_overlay_red_commit_and_same_workflow_blob_run", "overlay_red_matches_green_canonical_test_source_blob", "red_exact_pr_base_parent_and_tree", "red_exact_parent_tree_test_only_diff", "red_preparation_and_build_success_activation_failure_and_no_import_success", "workflow_path_and_blob", "workflow_run_attempt", "workflow_job_id", "workflow_check_run_id", "red_workflow_run_attempt", "red_job_id", "red_check_run_id", "green_preparation_build_activation_and_import_success"],
        "standard_only_requires_empty_fixed_overlay_namespace": True,
        "overlay_required_requires_nonempty_fixed_overlay_namespace": True,
        "overlay_required_requires_live_test_only_red_evidence": True,
    }, "FMV3-M3-03 completion evidence contract is incomplete")


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
    global TRUSTED_GIT_EXECUTABLE, TRUSTED_GH_EXECUTABLE, CLAIM_OWNER_SECRET
    validator_value = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}VALIDATOR")
    digest = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}SHA256")
    token_value = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}TOKEN")
    token_path_value = os.environ.get(f"{MATERIALIZATION_ENV_PREFIX}TOKEN_FILE")
    claim_secret_path_value = os.environ.get(
        f"{MATERIALIZATION_ENV_PREFIX}CLAIM_OWNER_SECRET_FILE"
    )
    require(
        all((validator_value, digest, token_value, token_path_value,
             claim_secret_path_value)),
        "direct use of --materialized-anchor-validator is forbidden",
    )
    validator_path = Path(str(validator_value)).resolve()
    token_path = Path(str(token_path_value)).resolve()
    claim_secret_path = Path(str(claim_secret_path_value)).resolve()
    require(
        Path(__file__).resolve() == validator_path
        and validator_path.is_file()
        and not validator_path.is_symlink()
        and token_path.is_file()
        and not token_path.is_symlink()
        and validator_path.parent == token_path.parent
        and validator_path.parent == claim_secret_path.parent
        and claim_secret_path.is_file()
        and not claim_secret_path.is_symlink()
        and validator_path.parent.stat().st_mode & 0o077 == 0
        and validator_path.stat().st_mode & 0o077 == 0
        and token_path.stat().st_mode & 0o077 == 0
        and claim_secret_path.stat().st_mode & 0o077 == 0
        and claim_secret_path.stat().st_uid == os.getuid(),
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
    TRUSTED_GIT_EXECUTABLE = trusted_materialized_executable("GIT")
    TRUSTED_GH_EXECUTABLE = trusted_materialized_executable("GH")
    CLAIM_OWNER_SECRET = claim_secret_path.read_text(encoding="ascii").strip()
    require(re.fullmatch(r"[0-9a-f]{64}", CLAIM_OWNER_SECRET) is not None,
            "materialized claim owner secret is invalid")
    token_path.unlink()
    claim_secret_path.unlink()


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


def validate_plan_templates(root: Path) -> None:
    template_root = root / "templates"
    require(
        template_root.is_dir() and not template_root.is_symlink(),
        "M1-06 template directory is missing or is a symlink",
    )
    entries = {path.name: path for path in template_root.iterdir()}
    require(
        set(entries) == set(PLAN_TEMPLATE_SHA256),
        "plan template file set differs from the anchored contract",
    )
    for name, expected_sha256 in PLAN_TEMPLATE_SHA256.items():
        path = entries[name]
        metadata = path.lstat()
        require(
            stat.S_ISREG(metadata.st_mode)
            and not path.is_symlink()
            and metadata.st_size <= 65536
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256,
            f"M1-06 template differs from the anchored bytes: {name}",
        )
    workflow = entries[Path(M1_06_MUTATION_WORKFLOW_PATH).name].read_text(
        encoding="utf-8"
    )
    try:
        workflow_data = yaml.safe_load(workflow)
    except yaml.YAMLError as exc:
        raise ValidationError("M1-06 mutation workflow YAML is invalid") from exc
    workflow_jobs = workflow_data.get("jobs") if isinstance(workflow_data, dict) else None
    checkout_steps = [
        step
        for job in workflow_jobs.values()
        if isinstance(workflow_jobs, dict) and isinstance(job, dict)
        for step in job.get("steps", [])
        if isinstance(step, dict) and str(step.get("uses", "")).startswith("actions/checkout@")
    ] if isinstance(workflow_jobs, dict) else []
    require(
        workflow.count("ref: ${{ github.event.pull_request.head.sha }}") == 2
        and workflow.count(
            'test "$(git rev-parse HEAD)" = "${{ github.event.pull_request.head.sha }}"'
        ) == 2
        and workflow.count(
            'test "$(git rev-parse HEAD^)" = "${{ github.event.pull_request.base.sha }}"'
        ) == 2,
        "M1-06 pull_request jobs do not execute the exact PR head",
    )
    require(
        len(checkout_steps) == 3
        and all(
            step.get("uses")
            == "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
            and isinstance(step.get("with"), dict)
            and step["with"].get("persist-credentials") is False
            for step in checkout_steps
        ),
        "M1-06 mutation workflow checkouts must be SHA-pinned and disable persisted credentials",
    )
    require(
        workflow.count(f"name: {M1_06_DOCS_LOCK_STEP_NAME}") == 2
        and workflow.count(f"run: python3 {M1_06_DOCS_LOCK_VALIDATOR_PATH}") == 2
        and all(
            [step.get("name") for step in workflow_jobs[job]["steps"]].index(
                M1_06_DOCS_LOCK_STEP_NAME
            ) < [step.get("name") for step in workflow_jobs[job]["steps"]].index(
                "Set up Go"
            )
            for job in ("conformance", "mutation")
        ),
        "M1-06 workflow does not verify the merged docs lock before build and tests",
    )
    guard = entries[Path(M1_06_MUTATION_GUARD_PATH).name].read_text(
        encoding="utf-8"
    )
    require(
        "len(paths) != 1" in guard
        and "len(names) != 1 || names[0] != targetKey" in guard
        and "mutationTargetPath(*base, contract.target)" in guard
        and "mutation must replace only the exact" in guard
        and "mutation must be exactly the case return replacement" in guard
        and "closedFailureControl" in guard
        and "exactTestingTParameter" in guard
        and "exactFailureCall" in guard
        and "conditionCallObjects" in guard
        and "constantTrue" in guard
        and "descriptor == symbol" in guard
        and "production source contains an unexpected declaration or package initializer" in guard
        and "must contain one non-constant if without else whose body directly fails through its test parameter" in guard
        and "declarationSpan(path, before, contract.target)" in guard
        and "beforeTarget := before[beforeStart:beforeEnd]" in guard
        and "bytes.Count(beforeTarget, []byte(contract.before))" in guard
        and "expected = append(expected, before[:beforeStart]...)" in guard
        and "bytes.Equal(after, expected)" in guard
        and "IgnoredOtherFiles" in guard
        and "XTestEmbedFiles" in guard
        and 'exec.Command("/usr/bin/git"' in guard
        and 'strings.HasPrefix(entry, "GIT_")' in guard
        and '"GIT_CONFIG_NOSYSTEM=1"' in guard
        and '"GIT_CONFIG_GLOBAL=/dev/null"' in guard,
        "M1-06 mutation guard does not enforce exact case-specific AST causality",
    )
    docs_lock_validator = entries[
        Path(M1_06_DOCS_LOCK_VALIDATOR_PATH).name
    ].read_text(encoding="utf-8")
    require(
        M1_06_DOCS_LOCK_SCHEMA in docs_lock_validator
        and DOCS_REPOSITORY in docs_lock_validator
        and EXPECTED_DOCS_CANDIDATE_BINDING["policy_sha256"] in docs_lock_validator
        and EXPECTED_DOCS_CANDIDATE_BINDING["manifest_sha256"] in docs_lock_validator
        and 'payload.get("merged") is True' in docs_lock_validator
        and 'payload.get("merge_commit_sha") == commit' in docs_lock_validator
        and '"/usr/bin/git", "--no-replace-objects"' in docs_lock_validator
        and 'key not in {"GH_TOKEN", "GITHUB_TOKEN"}' in docs_lock_validator,
        "M1-06 docs-lock validator is not fail-closed and tokenless",
    )


def validate(root: Path) -> tuple[int, int]:
    require(root.is_dir(), f"not a directory: {root}")
    actual_files = {path.name for path in root.iterdir() if path.is_file()}
    require(actual_files == REQUIRED_FILES, f"package files differ: missing={sorted(REQUIRED_FILES - actual_files)} extra={sorted(actual_files - REQUIRED_FILES)}")
    validate_plan_templates(root)
    plan = load_plan(root / "plan.yaml")
    missing_keys = REQUIRED_KEYS - set(plan)
    require(not missing_keys, f"plan.yaml missing keys: {sorted(missing_keys)}")
    require(plan["slug"] == "fronius-modbus-multivendor-v3-w29-26", "slug mismatch")
    supported_states = {"locked", "implementing", "maintenance"}
    require(plan["state"] in supported_states, "state must be locked, implementing, or maintenance")
    require(root.name == f"{plan['slug']}.{plan['state']}", "directory suffix/state mismatch")
    require(plan["lock_authorized"] is True, "lock_authorized must be true")
    authorization = validate_authorization_schema(plan)
    try:
        repo_root = Path(str(git_command(
            root, ["rev-parse", "--show-toplevel"], "plan repository root lookup",
        )).strip())
    except ValidationError:
        repo_root = Path(__file__).resolve().parent.parent
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
    require(plan["repository_mutex"] == {
        "scope": "per_repository",
        "owners": ["cruise-topology", "cruise-preflight"],
        "max_active_issues": 1,
        "max_active_prs": 1,
        "validation": "live_github_interval_history_plus_protected_append_only_remote_git_ref_cas",
        "claim": {
            "control_repo": PLAN_REPOSITORY,
            "ref_prefix": REPOSITORY_CLAIM_REF_PREFIX,
            "ref_identity": "repository_only",
            "schema": REPOSITORY_CLAIM_SCHEMA,
            "ledger_id": REPOSITORY_CLAIM_LEDGER_ID,
            "owner_epoch": REPOSITORY_CLAIM_OWNER_EPOCH,
            "identity": [
                "repository", "ref", "event", "state", "issue_id", "issue_number",
                "plan_anchor", "run_id", "owner_login", "owner_actor_id",
                "owner_commitment", "generation", "previous_sha",
                "authoritative_main_sha", "event_at", "expires_at", "event_mac",
            ],
            "ttl_seconds": REPOSITORY_CLAIM_TTL_SECONDS,
            "time_source": "authenticated_github_api_date_header",
            "max_history_events": REPOSITORY_CLAIM_MAX_HISTORY_EVENTS,
            "history_validation": "same_tree_hmac_chain_to_genesis_exact_generation_transition_and_ttl",
            "push_reconciliation": "reread_exact_remote_ref_after_every_push_result_exact_target_is_success_else_completion_ambiguous_stop_without_retry",
            "acquire": "create_or_fast_forward_from_exact_observed_ref",
            "renew_or_expired_takeover": "fast_forward_from_exact_observed_ref",
            "claim_commit_parent": "authoritative_main_initial_then_exact_prior_claim_append_only",
            "release": "fast_forward_tombstone_from_exact_owned_ref",
            "verify_entrypoint": "anchored_launcher_read_only_verify_exact_issue_number_run_plan_anchor_private_owner_secret_and_current_claim_sha",
            "renew_entrypoint": "anchored_launcher_append_only_renew_exact_issue_number_run_plan_anchor_private_owner_secret_and_current_claim_sha",
            "release_entrypoint": "anchored_launcher_release_claim_exact_issue_number_run_plan_anchor_private_owner_secret_and_acquired_claim_sha",
            "fenced_mutation_entrypoint": "anchored_launcher_fenced_gh_api_issue_capability_and_payload_bound_exact_pre_and_post_verification_with_stable_process_and_owner_secret_locks",
            "fenced_repository_snapshot": "exact_selected_issue_and_capability_specific_open_pr_mutex_pre_and_post",
            "canonical_checkout_history": "full_history_reachable_from_exact_observed_main_preserves_permanent_pr91_anchor",
            "mutation_payload_transport": "validate_retained_in_memory_bytes_then_send_exact_bytes_via_stdin_no_path_reopen",
            "mutation_interruption": "postflight_after_every_attempted_child_exit_including_base_exception_then_ambiguous_stop_without_retry",
            "required_check_policy": "every_context_app_bound_and_certificate_binds_exact_premerge_check_run_id",
            "docs_review_identity": "two_strict_lowercase_uuid_runs_and_independently_unique_output_digests",
            "post_merge_checkout": "exact_push_event_github_sha_checked_out_and_asserted_no_moving_main_ref",
            "mutation_capabilities": [
                "selected-issue-comment", "selected-issue-labels",
                "issue-pull-create",
                "create-public-repository",
            ],
            "branch_mutation": "ordinary_git_push_under_active_repository_claim_no_git_refs_rest_capability",
            "create_public_repository_scope": "FMV3-M0-01_only_exact_helianthus-modbus_or_helianthus-modbusreg_public_no_auto_init_issues_enabled_other_features_disabled_non_template_payload",
            "local_process_lock": "ipv4_loopback_127_0_0_1_port_45991_held_for_entire_claim_operation",
            "owner_secret": "external_owner_only_mode_0400_256_bit_hex_never_published",
            "owner_login": REPOSITORY_CLAIM_OWNER_LOGIN,
            "owner_actor_id": REPOSITORY_CLAIM_OWNER_ACTOR_ID,
            "owner_commitment": REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT,
            "integrity_ruleset_id": REPOSITORY_CLAIM_INTEGRITY_RULESET_ID,
            "writer_ruleset_id": REPOSITORY_CLAIM_WRITER_RULESET_ID,
            "rulesets": "active_exact_v2_claim_namespace_no_bypass_deletion_and_non_fast_forward_integrity_plus_repository_admin_bypass_creation_and_update_writer",
            "transitions": ["ACQUIRE", "RENEW", "TAKEOVER", "RELEASE"],
            "fencing": "standalone_verify_diagnostic_protected_github_rest_mutation_only_through_fenced_entrypoint",
            "cross_repository_atomicity": "unavailable_any_nonzero_mutation_result_or_post_verification_failure_means_mutation_may_have_completed_and_forces_stop_without_retry_reconciliation",
            "threat_model": {
                "ruleset_administrators": "trusted",
                "github_and_tls": "trusted",
                "owner_secret_possession": "owner_authority",
                "owner_secret_loss": "future_anchored_owner_epoch_rotation_required",
                "history_budget_exhaustion": "release_then_future_anchored_owner_epoch_rotation_required",
                "local_lock_prebind": "fail_closed_denial_only",
                "multi_host_owner_lock": "not_provided",
            },
            "post_claim_recheck": "exact_selected_open_issue_and_zero_open_prs",
        },
    }, "repository mutex contract mismatch")
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
    issue_fields = {
        "id", "milestone", "complexity", "repo", "depends_on", "what",
        "acceptance", "gates", "rollback",
    }
    issue_ids: list[str] = []
    issue_deps: dict[str, list[str]] = {}
    issues_by_id: dict[str, dict[str, Any]] = {}
    repo_owners: dict[str, str] = {}
    for index, issue in enumerate(issues):
        require_fields(issue, issue_fields, f"issue[{index}]")
        issue_id = issue["id"]
        require(isinstance(issue_id, str) and re.fullmatch(r"FMV3-M[0-8]-\d{2}", issue_id) is not None, f"invalid issue ID: {issue_id}")
        require(issue["milestone"] in milestone_ids, f"issue {issue_id} has unknown milestone")
        require(type(issue["complexity"]) is int and 1 <= issue["complexity"] <= 10,
                f"issue {issue_id} complexity must be an integer from 1 through 10")
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
    seed_contract = {
        "method": "direct_push_empty_tree_root_commit",
        "commit_sha": "bd15e364a749adcca283570f027bfb826198952a",
        "tree_sha": "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
        "parents": [],
        "subject": "chore: initialize repository for issue #1",
        "default_branch": "main",
        "issue_number": 1,
        "first_pull_request_number": 2,
        "sole_exception_before_legal_pr_base": True,
    }
    require(
        issues_by_id["FMV3-M0-02"].get("seed_contract") == seed_contract
        and issues_by_id["FMV3-M0-03"].get("seed_contract") == seed_contract,
        "M0 public destination seed contract mismatch",
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
    downstream_conformance_contract = docs_projection["downstream_conformance"]
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
            "bounded_values_contract", "downstream_conformance_contract",
        },
        "FMV3-M1-06": issue_fields | {
            "companion_issue", "doc_gate", "fresh_adversarial_contract",
            "implements_contract", "opaque_runtime_acquisition_contract",
            "repository_mutex_evidence",
            "source_kind_contract", "strict_tdd_contract",
            "bounded_values_contract", "downstream_conformance_contract",
        },
        "FMV3-M2-01": issue_fields | {
            "attempt_ledger_contract", "companion_issue",
            "consumes_contract", "corrective_companion_issue",
            "doc_gate", "fresh_adversarial_contract",
            "normalization_round_trip_contract", "observation_view_fields",
            "producer_pin_contract", "source_trust_contract",
            "strict_tdd_contract", "bounded_values_contract",
            "downstream_conformance_contract",
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
        and opaque_docs.get("downstream_conformance_contract")
        == downstream_conformance_contract
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
        and opaque_runtime.get("repository_mutex_evidence")
        == "all_pull_request_intervals_no_overlap"
        and opaque_runtime.get("source_kind_contract") == source_kind_contract
        and opaque_runtime.get("opaque_runtime_acquisition_contract") == opaque_contract
        and opaque_runtime.get("bounded_values_contract") == bounded_values_contract
        and opaque_runtime.get("downstream_conformance_contract")
        == downstream_conformance_contract
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
        and m2_contract.get("downstream_conformance_contract")
        == downstream_conformance_contract
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
    require(m3_disposition.get("m3_03_workflow_contract") == M3_03_WORKFLOW_CONTRACT, "FMV3-M3-03 canonical workflow contract mismatch")
    require(m3_disposition.get("completion_evidence_contract") == {"schema": "helianthus.fmv3-m3-03-completion.v2", "bind": ["head_sha", "head_tree_sha", "disposition", "fixed_profiles_fronius_namespace_scan", "canonical_disposition_bound_named_test_source_blob", "artifact_named_test_sources_no_init_or_testmain", "complete_go_import_literal_unquote_and_unicode_alias_scan", "executable_fail_closed_runtime_import_scanner", "sealed_transport_neutral_direct_import_allowlist", "semicolon_import_declaration_rejection", "disposition_bound_minimal_neutral_adapter", "overlay_separate_production_implementation_source_without_init_or_test_only_symbols_or_constraints", "zero_field_fake_compile_time_interface_assertion", "sentinel_result_control_flow", "closed_canonical_named_test_bodies", "exact_top_level_permissions_contents_read", "executable_head_and_tree_assertion", "exact_preparation_deletes_all_other_direct_test_sources", "exact_standalone_production_build_before_tests", "activation_first_and_import_second_exact_commands", "conditional_overlay_red_commit_and_same_workflow_blob_run", "overlay_red_matches_green_canonical_test_source_blob", "red_exact_pr_base_parent_and_tree", "red_exact_parent_tree_test_only_diff", "red_preparation_and_build_success_activation_failure_and_no_import_success", "workflow_path_and_blob", "workflow_run_attempt", "workflow_job_id", "workflow_check_run_id", "red_workflow_run_attempt", "red_job_id", "red_check_run_id", "green_preparation_build_activation_and_import_success"], "standard_only_requires_empty_fixed_overlay_namespace": True, "overlay_required_requires_nonempty_fixed_overlay_namespace": True, "overlay_required_requires_live_test_only_red_evidence": True}, "FMV3-M3-03 completion evidence contract mismatch")
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
        "External review attestation": "owner_plus_authenticated_independent_review_v1; authoritative owner exact-tree decision plus official Codex exact-head review; owner attestations non-independent; mandatory non-authoritative same-change-set post-merge CI observation",
        "Docs R2 rebind": "complete; PR #91 bootstrap precedes docs PR #386 merge and binds exact head/tree, blob closure, normalized V1 semantics, critical invariants, canonical-main ancestry, exact-head CI, and review chain",
        "Repository creation authorized": "yes, through FMV3-M0-01; M0-02/M0-03 bind the sole exact empty-tree root initialization exception per destination",
        "Private repository action": "deferred; creation requires future explicit authorization",
        "Commit/push authorized": "yes, for the plan package and authorized pre-gateway issues only",
        "Gateway work authorized": "no; stop before FMV3-M4-01",
        "Private creation/bootstrap authorized": "no; FMV3-M0-04, FMV3-M0-05, and FMV3-M0-07 deferred",
    }
    for key, expected in status_fields.items():
        require_unique_metadata(status, key, expected, "status")
    surface_texts = load_amendment_surface_texts(root)
    validate_review_repair_semantics(plan, surface_texts)
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
    parser.add_argument("--verify-claim")
    parser.add_argument("--renew-claim")
    parser.add_argument("--release-claim")
    parser.add_argument("--github-issue-number", type=int)
    parser.add_argument("--claim-run-id")
    parser.add_argument("--claim-sha")
    parser.add_argument("--plan-head-sha")
    parser.add_argument("--authorization-contract-sha256")
    parser.add_argument("--authorization-evidence")
    parser.add_argument("--routing-receipt-base64")
    parser.add_argument("--routing-receipt-sha256")
    parser.add_argument("--fenced-mutation-phase", choices=("preflight", "postflight"))
    parser.add_argument("--fenced-mutation-capability")
    parser.add_argument("--fenced-mutation-head")
    parser.add_argument("--materialized-anchor-validator", action="store_true")
    parser.add_argument("--print-amendment-surfaces-sha256", action="store_true")
    args = parser.parse_args()
    active_claim_fence: dict[str, Any] | None = None
    routing_receipt: dict[str, Any] | None = None
    root = args.root.resolve() if args.root is not None else Path(__file__).resolve().parent
    try:
        claim_modes = [
            value for value in (
                args.authorize_issue, args.verify_claim,
                args.renew_claim, args.release_claim,
            )
            if value is not None
        ]
        require(len(claim_modes) <= 1,
                "claim operation modes are mutually exclusive")
        selected_issue_id = claim_modes[0] if claim_modes else None
        if selected_issue_id is not None and not args.materialized_anchor_validator:
            raise ValidationError(
                "claim operations require the trusted cruise-preflight anchor materializer"
            )
        if args.materialized_anchor_validator:
            require(
                selected_issue_id is not None,
                "--materialized-anchor-validator is internal to claim operations",
            )
            require_materialized_validator_context()
            require(type(args.github_issue_number) is int and args.github_issue_number > 0,
                    "--github-issue-number must be a positive integer")
            require(isinstance(args.claim_run_id, str) and re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                args.claim_run_id,
            ) is not None, "--claim-run-id must be one lowercase UUID")
            if any(value is not None for value in (
                args.verify_claim, args.renew_claim, args.release_claim,
            )):
                require(isinstance(args.claim_sha, str)
                        and re.fullmatch(r"[0-9a-f]{40}", args.claim_sha) is not None,
                        "verify, renew, and release require the exact acquired --claim-sha")
            else:
                require(args.claim_sha is None,
                        "--claim-sha is valid only with verify, renew, or release")
            if args.authorize_issue is not None:
                require(args.routing_receipt_base64 is not None
                        and args.routing_receipt_sha256 is not None,
                        "--authorize-issue requires a model-routing receipt")
            else:
                require(args.routing_receipt_base64 is None
                        and args.routing_receipt_sha256 is None,
                        "model-routing receipt is valid only with --authorize-issue")
            if args.fenced_mutation_phase is None:
                require(
                    args.fenced_mutation_capability is None
                    and args.fenced_mutation_head is None,
                    "fenced mutation snapshot arguments require an exact phase",
                )
            else:
                require(
                    args.verify_claim is not None
                    and isinstance(args.fenced_mutation_capability, str),
                    "fenced mutation snapshot is valid only for claim verification",
                )
        if args.print_amendment_surfaces_sha256:
            plan = load_plan(root / "plan.yaml")
            print(amendment_surface_digest(plan, load_amendment_surface_texts(root)))
            return 0
        authorization_repo_root: Path | None = None
        authoritative_main: str | None = None
        if selected_issue_id is not None:
            authorization_repo_root, authoritative_main = prepare_plan_authorization_checkout(
                root
            )
        issue_count, milestone_count = validate(root)
        if selected_issue_id is not None:
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
            git_command(
                authorization_repo_root,
                ["merge-base", "--is-ancestor", args.plan_head_sha, authoritative_main],
                "authorization anchor canonical-main ancestry check",
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
            anchored_plan_text = str(git_command(
                repo_root,
                ["show", f"{args.plan_head_sha}:{anchor_relpath}"],
                "authorization anchor plan read",
            ))
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
                ("launcher_reference_path", "launcher_reference_sha256"),
            ):
                relative = safe_repository_path(anchored_tooling[path_key], path_key)
                anchored_blob = git_command(
                    repo_root,
                    ["show", f"{args.plan_head_sha}:{relative.as_posix()}"],
                    f"anchored tooling blob read: {path_key}",
                    text=False,
                )
                require(
                    hashlib.sha256(anchored_blob).hexdigest()
                    == anchored_tooling[hash_key],
                    f"anchored {path_key} blob SHA-256 mismatch",
                )
                current_blob_path = current_tooling_path(
                    repo_root, root, path_key, relative
                )
                require(
                    current_blob_path.read_bytes() == anchored_blob,
                    f"current {path_key} blob differs from merged PR #91 anchor",
                )
                if path_key == "validator_path":
                    require(
                        Path(__file__).resolve().read_bytes() == anchored_blob,
                        "preflight is not executing the validator materialized from PR #91 anchor",
                    )
            require(
                anchored_authorization.get("authorized_issue_contract_sha256")
                == args.authorization_contract_sha256,
                "authorization contract digest is absent from the merged anchor",
            )
            require(
                selected_issue_id in anchored_authorization.get("authorized_issues", []),
                "issue is absent from the merged authorization anchor",
            )
            require(
                selected_issue_id in authorization["authorized_issues"],
                f"issue {selected_issue_id} is outside the fail-closed execution allowlist",
            )
            require(
                selected_issue_id != authorization["stop_before_issue"],
                f"issue {selected_issue_id} reaches the hard stop",
            )
            require_authorization_pr_merged(
                anchored_anchor,
                args.plan_head_sha,
            )
            anchored_issues = anchored_plan.get("issues")
            require(isinstance(anchored_issues, list), "anchored issues must be a list")
            anchored_deps = {
                item.get("id"): item.get("depends_on")
                for item in anchored_issues
                if isinstance(item, dict)
            }
            anchored_repos = {
                item.get("id"): item.get("repo")
                for item in anchored_issues
                if isinstance(item, dict)
            }
            anchored_issue_specs = {
                item.get("id"): item
                for item in anchored_issues
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
            require(
                set(anchored_authorization["authorized_issues"]) <= set(anchored_deps)
                and all(
                    isinstance(anchored_deps[issue], list)
                    for issue in anchored_authorization["authorized_issues"]
                ),
                "anchored direct dependency graph is invalid",
            )
            selected_spec = anchored_issue_specs.get(selected_issue_id)
            require(isinstance(selected_spec, dict), "anchored selected issue spec is absent")
            require(
                isinstance(selected_spec.get("repo"), str)
                and isinstance(selected_spec.get("id"), str)
                and isinstance(selected_spec.get("what"), str),
                "anchored selected issue spec is invalid",
            )
            selected_marker = (
                issue_spec_marker(issue_spec_digest(selected_spec))
                if set(ISSUE_SPEC_FIELDS) <= set(selected_spec) else None
            )
            if args.authorize_issue is not None:
                routing_receipt = require_issue_routing_receipt(
                    args.routing_receipt_base64,
                    args.routing_receipt_sha256,
                    selected_spec,
                    args.plan_head_sha,
                )
            if args.authorize_issue is not None:
                require_plan_owned_repository_snapshot(
                    str(selected_spec["repo"]),
                    args.github_issue_number,
                    issue_spec_title(selected_spec),
                    selected_marker,
                )
            anchor_directory = Path(anchor_relpath).parent
            anchored_surface_texts: dict[str, str] = {}
            for name in AMENDMENT_SURFACE_FILES:
                relative = (anchor_directory / name).as_posix()
                anchored_surface_texts[name] = str(git_command(
                    repo_root,
                    ["show", f"{args.plan_head_sha}:{relative}"],
                    f"anchored amendment surface read: {name}",
                ))
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
            require(isinstance(CLAIM_OWNER_SECRET, str),
                    "materialized claim owner secret is unavailable")
            if args.release_claim is not None:
                require_repository_claim_control(CLAIM_OWNER_SECRET)
                release_repository_claim(
                    repo_root,
                    authoritative_main,
                    str(selected_spec["repo"]),
                    selected_issue_id,
                    args.github_issue_number,
                    args.plan_head_sha,
                    str(args.claim_run_id),
                    CLAIM_OWNER_SECRET,
                    str(args.claim_sha),
                )
            elif args.verify_claim is not None:
                require_repository_claim_control(CLAIM_OWNER_SECRET)
                active_claim_fence = require_repository_claim_fence(
                    repo_root,
                    authoritative_main,
                    str(selected_spec["repo"]),
                    selected_issue_id,
                    args.github_issue_number,
                    args.plan_head_sha,
                    str(args.claim_run_id),
                    CLAIM_OWNER_SECRET,
                    str(args.claim_sha),
                )
                if args.fenced_mutation_phase is not None:
                    require_fenced_repository_snapshot(
                        str(selected_spec["repo"]),
                        args.github_issue_number,
                        issue_spec_title(selected_spec),
                        selected_marker,
                        str(args.fenced_mutation_capability),
                        args.fenced_mutation_phase,
                        args.fenced_mutation_head,
                    )
            elif args.renew_claim is not None:
                require_repository_claim_control(CLAIM_OWNER_SECRET)
                active_claim_fence = renew_repository_claim(
                    repo_root,
                    authoritative_main,
                    str(selected_spec["repo"]),
                    selected_issue_id,
                    args.github_issue_number,
                    args.plan_head_sha,
                    str(args.claim_run_id),
                    CLAIM_OWNER_SECRET,
                    str(args.claim_sha),
                )
            else:
                require_issue_authorization_dependencies(
                    selected_issue_id,
                    anchored_anchor,
                    args.authorization_evidence,
                    anchored_deps,
                    anchored_repos,
                    anchored_issue_specs,
                )
            if args.authorize_issue is not None and (
                re.fullmatch(r"FMV3-M[123]-\d{2}", selected_issue_id)
                is not None
                and selected_issue_id not in {"FMV3-M1-00", "FMV3-M1-05"}
            ):
                require_m1_admission_open(repo_root, authoritative_main)
            if args.authorize_issue is not None:
                active_claim_fence = require_plan_owned_repository_preflight(
                    repo_root,
                    authoritative_main,
                    str(selected_spec["repo"]),
                    selected_issue_id,
                    args.github_issue_number,
                    issue_spec_title(selected_spec),
                    selected_marker,
                    args.plan_head_sha,
                    str(args.claim_run_id),
                    CLAIM_OWNER_SECRET,
                )
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if args.authorize_issue is not None:
        if not isinstance(active_claim_fence, dict) or not isinstance(
            routing_receipt, dict
        ):
            print(
                "FAIL: authorization claim fence or routing receipt is unavailable",
                file=sys.stderr,
            )
            return 1
        print(
            f"PASS: {args.authorize_issue} is inside the fail-closed execution allowlist "
            f"at {args.plan_head_sha} with contract {args.authorization_contract_sha256}; "
            f"route {routing_receipt['route']['primary_profile']} "
            f"{routing_receipt['route']['model']}/"
            f"{routing_receipt['route']['reasoning_effort']} receipt "
            f"{args.routing_receipt_sha256}; "
            f"claim {active_claim_fence['claim_sha']} ledger "
            f"{active_claim_fence['ledger_id']} generation "
            f"{active_claim_fence['generation']} expires "
            f"{active_claim_fence['expires_at']}"
        )
    elif args.verify_claim is not None or args.renew_claim is not None:
        if not isinstance(active_claim_fence, dict):
            print("FAIL: claim fence is unavailable", file=sys.stderr)
            return 1
        action = "verified" if args.verify_claim is not None else "renewed"
        print(
            f"PASS: {action} {selected_issue_id} claim "
            f"{active_claim_fence['claim_sha']} ledger "
            f"{active_claim_fence['ledger_id']} generation "
            f"{active_claim_fence['generation']} expires "
            f"{active_claim_fence['expires_at']}"
        )
    elif args.release_claim is not None:
        print(
            f"PASS: released {args.release_claim} claim owned by run "
            f"{args.claim_run_id} at {args.plan_head_sha}"
        )
    else:
        print(f"PASS: {root.name}; {issue_count} issues; {milestone_count} milestones; lifecycle consistent")
    return 0
if __name__ == "__main__": raise SystemExit(main())
