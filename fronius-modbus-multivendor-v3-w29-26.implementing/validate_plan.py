#!/usr/bin/env python3
"""Validate only the structural contract of this locked execution-plan package."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timedelta
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
ISSUE_SPEC_MARKER_PREFIX = "helianthus-fmv3-issue-spec-v1"
ISSUE_SPEC_FIELDS = (
    "id", "repo", "depends_on", "what", "acceptance", "gates", "doc_gate",
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
    "helianthus.fmv3-m1-06-conformance-report.v1"
)
M1_06_OWNER_REVIEW_SCHEMA = "helianthus.fmv3-m1-06-owner-review.v1"
M1_06_RED_REQUIRED_CHECK = "checks"
GITHUB_ACTIONS_APP_ID = 15368
M1_06_CI_JOB_NAME = "checks"
M1_06_SETUP_STEP_NAME = "Set up Go"
M1_06_CI_STEP_NAME = "./scripts/ci_local.sh"
M1_06_PRODUCTION_SYMBOLS = (
    "OpaqueRuntimeCapability",
    "NewRuntimeAcquisition",
    "Claim",
    "CancelOpen",
    "NewBoundedCapability",
    "ReserveTerminalSequence",
    "TerminalOutcome",
)
M1_06_CONFORMANCE_CASES = {
    "M1-06-DELIVERABILITY-EXCLUSIONS": (
        "TestDeliverabilityExclusions", ("NewRuntimeAcquisition",)
    ),
    "M1-06-COPY-ONE-WINNER": (
        "TestCopiedCapabilityOneWinner", ("Claim",)
    ),
    "M1-06-FRESH-NON-ALIAS": (
        "TestFreshAcquisitionNonAlias", ("NewRuntimeAcquisition",)
    ),
    "M1-06-TERMINAL-OUTCOMES": (
        "TestTerminalOutcomes", ("TerminalOutcome",)
    ),
    "M1-06-CANCEL-OPEN-DRAIN-RECLAIM": (
        "TestCancelOpenDrainAndReclaim", ("CancelOpen",)
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
M1_06_MUTATION_WORKFLOW_PATH = ".github/workflows/ci.yml"
M1_06_MUTATION_COMPILE_STEP_NAME = "go test -run ^$ ./..."
M1_06_MUTATION_CASES = {
    case_id: f"go test -run ^{test_function}$ ./..."
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
    "owner_process_attestations": 2,
    "evidence_reviews": "one_authenticated_official_codex_review_plus_two_owner_process_attestations",
    "aggregate_binds": ["repository", "pull_request", "head_sha", "head_tree_sha", "workflow_run_id", "official_review_id", "owner_review_ids"],
    "head_publication_evidence": "successful_pull_request_workflow_run_before_reviews",
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
            "exact_squash_pull_request_head_tree_and_base_parent",
            "test_only_red_ancestor_with_exact_pull_request_hosted_failure",
            "exact_implementation_head_green_required_checks",
            "official_codex_exact_head_zero_inline_findings",
            "two_owner_process_attestations_after_green_and_mutations",
            "fixed_path_closed_conformance_report_with_exact_source_blobs_and_mutation_patch_digests",
            "exact_red_and_green_ci_local_jobs",
            "eight_exact_parent_report_bound_mutants_compile_before_mapped_test_failure",
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
    },
    "FMV3-M0-03": {
        "repository": "Project-Helianthus/helianthus-modbusreg", "github_issue_number": 1,
        "issue_title": "FMV3-M0-03: bootstrap the public multi-profile registry repository",
        "github_pull_request_number": 2, "pull_request_title": "chore: bootstrap public Modbus profile registry",
        "head_sha": "b8fa5b1b5f01e4776338f2b9ffaf2b99ee058d85", "head_tree_sha": "9dbf08e3681b8bf9bd9a71f516a7ee0318c5b16d",
        "merge_sha": "c6f26b33e38525cddc1c0ce19389ed19a8bb6844", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
    },
    "FMV3-M0-06": {
        "repository": DOCS_REPOSITORY, "github_issue_number": 371,
        "issue_title": "FMV3-M0-06: publish Modbus ownership and licensing boundaries",
        "github_pull_request_number": 372, "pull_request_title": "docs(platform): define Modbus repository boundaries",
        "head_sha": "a0ba25ef445abd5d17f5df4ff386040c3f4ed8a7", "head_tree_sha": "600cf88f8e742f8412ba2ae8d91076a4c44fa389",
        "merge_sha": "7b0dd0abba8bc3420f1d8d2bae2db5bc229b75f3", "required_checks": [{"context": "Docs Checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "Platform Contracts Combined Ref / Validate Explicit Combined Refs", "app_id": GITHUB_ACTIONS_APP_ID}],
    },
    "FMV3-M1-00": {
        "repository": DOCS_REPOSITORY, "github_issue_number": 373,
        "issue_title": "FMV3-M1-00: Define Modbus M1/M2 companion contract",
        "github_pull_request_number": 376, "pull_request_title": "docs(platform): define Modbus M1/M2 companion contract",
        "head_sha": "db88c05ad9f49a23fdd3fc9de0e5d9ea3ca99055", "head_tree_sha": "25d4cd89216f0d1f2f05261506316bd64f91483b",
        "merge_sha": "711a556fee344c6fe7f1ecf3253fcdb3f5f22d06", "required_checks": [{"context": "Docs Checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "Platform Contracts Combined Ref / Validate Explicit Combined Refs", "app_id": GITHUB_ACTIONS_APP_ID}],
    },
    "FMV3-M1-01": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 3,
        "issue_title": "FMV3-M1-01: implement strict phase-one Modbus PDU codecs",
        "github_pull_request_number": 4, "pull_request_title": "feat: implement strict phase-one Modbus PDU codecs",
        "head_sha": "9a07587a6157c6f570b054fe2eb6bd60f009fc7f", "head_tree_sha": "b13d5be4f965b3b6f3aae796aa6281f0526ccfe4",
        "merge_sha": "c9b3281b5025fd3b1b714235493bd36d526f865f", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
    },
    "FMV3-M1-02": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 5,
        "issue_title": "FMV3-M1-02: implement owned Modbus TCP runtime",
        "github_pull_request_number": 6, "pull_request_title": "FMV3-M1-02: implement owned Modbus TCP runtime",
        "head_sha": "0aac61ddad62f664b47900334c48803587183fa3", "head_tree_sha": "ac81a5294a84a1783cb84f56cfe1ba455291c1ee",
        "merge_sha": "467229104bfe34ca90aa653ca22ad79da4fa9a32", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
    },
    "FMV3-M1-03": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 9,
        "issue_title": "FMV3-M1-03: implement fixture-only Modbus RTU runtime",
        "github_pull_request_number": 10, "pull_request_title": "FMV3-M1-03: fixture-only Modbus RTU runtime",
        "head_sha": "4f8e69dad3c57c798f3eb3d74f7382f3ae9d685b", "head_tree_sha": "12717cdd6efc34dcc6560cc98690d9436fd59951",
        "merge_sha": "fd7524fee3d4ea808a67185341a3bf13f6d151cd", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
    },
    "FMV3-M1-04": {
        "repository": MODBUS_REPOSITORY, "github_issue_number": 13,
        "issue_title": "FMV3-M1-04: close offline transport conformance and recovery matrices",
        "github_pull_request_number": 14, "pull_request_title": "FMV3-M1-04: close offline transport conformance matrices",
        "head_sha": "ada08479e73ecf7c9f892558e577347bf2f16dd9", "head_tree_sha": "1c2a90e5637ab989d66b87de264fc555c25965d0",
        "merge_sha": "4f81cbeb6321e64fa51676ed6e375ce36b60d16d", "required_checks": [{"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID}, {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID}],
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
    "green_workflow_run_id": "required_positive_integer_selector",
    "mutation_runs": "eight_ordered_case_commit_and_workflow_selectors",
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
        "test_only_red_ancestor_and_exact_pull_request_failure",
        "exact_head_required_checks_success",
        "official_codex_zero_inline_findings",
        "two_fresh_owner_no_findings_after_green",
        "fixed_path_closed_conformance_report_exact_regular_blobs_and_mutation_patch_digests",
        "red_and_green_jobs_execute_ci_local",
        "eight_exact_parent_report_bound_mutants_compile_before_mapped_test_failure",
    ],
    "consumer_resolution": "exact_sha_verified_before_red",
}
EXPECTED_TOOLING_PATHS = {
    "validator_path": "fronius-modbus-multivendor-v3-w29-26.implementing/validate_plan.py",
    "workflow_path": ".github/workflows/ci.yml",
}
EXPECTED_D13_DECISION = "FMV3-M1-05 documents and FMV3-M1-06 implements OPAQUE_RUNTIME_ACQUISITION_V1 as an additive successor to M1-04 before M2-01. A runtime source privately owns and issues each non-serializable one-shot capability only after all post-correlation successful-dependent deliverability conditions; only copies of that same capability share its state, and M1 state is never an M2 ledger pointer. Endpoint recreation and every new acquisition create fresh independent state even when visible identity or data match. Capability state moves open to claimed, cancelled, failed, or expired and is synchronously reclaimed by a pre-reserved terminal sequence into a finite-positive, byte-bounded, non-reconstructing tombstone ring. M2-01 pins the merged M1-06 producer SHA, keeps runtime and fixture trust distinct, and owns a separately bounded attempt/claim ledger across every retained state. The exact docs R2 binding requires unresolved claims to enter claim_in_progress before one immutable terminal result, open or sealed attempts to enter cancelling before cancelled, an atomic seal predicate in which every data-bearing runtime claim is claim_succeeded, runtime-source-owned CancelOpen linearized by exact bounded AttemptKey, explicit byte and field bounds validated before allocation, one-shot sealed-to-publishing Publish(), and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. Deterministic reclamation preserves only bounded non-reconstructing audit metadata and the complete normalization record round-trips losslessly within admitted bounds."
EXPECTED_M2_EXIT_GATE = "The reused FMV3-M1-00 companion remains merged, and M2-01 starts only after M1-06 merges and external authorization evidence supplies bounded selectors whose live GitHub objects prove the exact immutable marked/title issue, exact closing same-repo squash PR and canonical-main topology, test-only RED ancestor with an exact-PR hosted run/check failure at ./scripts/ci_local.sh after successful setup, exact-head GREEN app-bound required checks and successful ./scripts/ci_local.sh job, eight exact-parent production-only mutants whose canonical patch digests are precommitted in the GREEN report and whose mapped tests fail only after same-SHA compile/no-tests success, official Codex canonical-template zero-inline exact-head review after mutations, two owner NO_FINDINGS process attestations after GREEN and mutations, and the fixed-path closed conformance report binding every validator-pinned case to an exact Go test/source blob/PASS, exact mutation patch digest, and exact production contract symbols. The exact docs R2 head/tree binding requires claim_in_progress and cancelling states, an atomic all-data-bearing-runtime-claims-succeeded seal predicate, runtime-source-owned CancelOpen linearization by exact bounded AttemptKey, byte and field bounds validated before allocation, and pre-reserved nonzero uint64 terminal sequences that never wrap or reuse. Profile API, exact wire-response/logical-view/sample identity and provenance, runtime-versus-fixture trust, independently ledger-owned bounded attempt/claim state across all retained states, finite-positive limits with a checked retained-attempt-limit times claim-limit product, duplicate AttemptKey rejection, complete immutable-terminal lifecycles, one-shot sealed publication, deterministic synchronous terminal-sequence reclamation into a finite-positive byte-bounded non-reconstructing audit/tombstone ring, exact bounded normalization round-trip, detector lifecycle, and conformance harness are stable under strict hosted RED/GREEN and fresh independent review."
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
to the externally attested PR head tree. Before review, a successful canonical `pull_request`
workflow run must bind the exact live head and PR base/head identity. One submitted official
Codex bot `COMMENTED` review must equal the canonical Codex no-suggestions template for the
exact ten-character head prefix and have zero inline findings; no severity or arbitrary finding
text is accepted. Two separate submitted owner reviews then bind that head/tree, `NO_FINDINGS`,
and owner-attested fresh-process references/output digests; they are process attestations, not
independently authenticated OpenAI artifacts. One unedited aggregate binds the
workflow-run ID and immutable submitted review IDs;
the plan never self-embeds its own head SHA.

The ordered `authorized_issues` list in `plan.yaml` is the sole normative execution scope:
FMV3-M0-01, FMV3-M0-02, FMV3-M0-03, FMV3-M0-06, FMV3-M1-00, FMV3-M1-01,
FMV3-M1-02, FMV3-M1-03, FMV3-M1-04, FMV3-M1-05, FMV3-M1-06, FMV3-M2-01,
FMV3-M2-02, FMV3-M2-03, FMV3-M3-01, FMV3-M3-02, and FMV3-M3-03. Milestone names
are non-authoritative grouping labels. This amendment corrects FMV3-M1-05, FMV3-M1-06,
and FMV3-M2-01 without changing the allowlist.

Authorization runs only from a fully clean canonical
`Project-Helianthus/helianthus-execution-plans` main checkout resolved through the fixed
GitHub API. A configured remote named `origin` is never main authority and must identify
the canonical repository exactly. The trusted cruise-preflight launcher authenticates the
PR #91 merge SHA first, materializes the validator blob directly from that immutable commit,
verifies its anchored SHA-256, and only then executes the one-use blob with the internal flag.
The checked-out candidate validator is defense-in-depth and is never the bootstrap trust root.

FMV3-M0-01 creates only the two empty public repositories `helianthus-modbus` and
`helianthus-modbusreg`. FMV3-M1-05 publishes the public
`OPAQUE_RUNTIME_ACQUISITION_V1` companion, FMV3-M1-06 implements it after M1-05, and
FMV3-M2-01 consumes the merged M1-06 producer by exact full-SHA pin. Private governance
creation FMV3-M0-04 and destination bootstraps FMV3-M0-05/FMV3-M0-07 remain deferred.

Every authorized issue must prove completion of exactly its direct `depends_on` predecessors.
Completed FMV3 predecessors use immutable exact live-GitHub bindings for repository, issue and PR
titles/numbers, closing body and timeline relation, closure time, base/head/merge/tree/topology,
canonical-main ancestry, and exact-head required checks. M0-01 is the sole no-PR exception because
repository creation produced no Git object; it instead binds the exact issue closure event and
unedited completion-attestation comment. Every unresolved direct predecessor must appear exactly
once in the bounded external `dependencies` certificate array; exact set equality rejects missing,
duplicate, extra, and non-direct rows. Each row binds exact repository, issue/PR selectors,
an anchored issue-spec digest and marker, head/tree/merge SHAs, and the complete dynamic main
required-check policy, all authenticated live. Every authorization-relevant required check has a
concrete positive GitHub App ID; legacy context-only and any-app evidence is rejected.
M2-01 retains its producer extension, which must equal its M1-06 dependency row. Stale, unmerged,
wrong issue/PR, failed-check, wrong-tree/topology, or non-main evidence fails closed.
M1-05 completion is the exact docs issue #385 with its immutable title and repository, closed by
docs PR #386 through an exact `Closes #385` body line, live timeline relation, and authoritative
GraphQL `closingIssuesReferences`, with issue closure inside a bounded 60-second post-merge window. FMV3-M1-06 requires docs PR #386 merged with the exact bound candidate
head and tree, dynamically ancestral to canonical docs main, with all exact-head required checks
successful under its concrete app-bound policy, one official Codex exact-head `COMMENTED` review using the
exact canonical no-suggestions template and zero inline findings, and two owner structured
`NO_FINDINGS` process attestations submitted after CI. FMV3-M2-01 additionally accepts only external selectors for the
M1-06 issue, closing PR, merge and RED commit SHAs, failed RED workflow run, official Codex
review, and exactly two owner reviews; those selector values are not trusted outcome claims.
Live GitHub must prove the exact immutable issue title and
`<!-- helianthus-fmv3-m1-06-opaque-runtime-acquisition-v1 -->` marker, canonical same-repo
main/base/head PR identity, exact issue closure by that PR, reviewed head-tree equality with
the one-parent squash merge tree and PR base, and canonical-main ancestry. The test-only RED
commit must be an implementation-head ancestor whose bounded first diff page contains only Go
tests, fixtures, or the fixed conformance-report path and no production path; diff page two must be
empty. Its exact `pull_request` run and `checks` check must fail on that RED SHA and PR, and the
exact `checks` job must fail at `./scripts/ci_local.sh` after successful setup. All dynamically
required checks must then succeed on the exact implementation head, with the selected GREEN run's
exact `checks` job succeeding at `./scripts/ci_local.sh`. Eight ordered, production-Go-only mutant
commits must each be a direct child of GREEN. The GREEN conformance report precommits each
canonical GitHub patch digest; every selected run must then pass `go test -run ^$ ./...` on the
mutant before the validator-mapped test fails. One official Codex exact-head review after those mutations must use the exact
canonical no-suggestions template and have zero inline findings. Two owner `COMMENTED` closed-schema
`NO_FINDINGS` process attestations after GREEN and mutations must bind the exact RED/head/tree,
fixed conformance-report blob, validator-pinned case digest, and mutation-evidence digest. The regular committed report
`.github/fmv3/fmv3-m1-06-conformance-report.json` must use
`helianthus.fmv3-m1-06-conformance-report.v1`; its closed fixed case set binds deliverability
exclusions, copy one-winner, fresh non-alias, terminal outcomes, CancelOpen drain/reclaim,
bounds/overflow, sequence exhaustion, and coalesced isolation to exact Go test declarations,
source blobs, regular modes, nonempty failure/assertion bodies, semantic calls, `PASS`, and the
exact per-case mutation patch digest. Its
production Go blobs must declare every fixed contract symbol. Missing, stale, fake, failed,
semantic-no-op, non-direct, or mismatched producer proof fails closed.
The exact docs R2 commit/tree, complete predecessor-inclusive normative closure, and expanded
machine projection including `bounded_values` are bound. They require claim-in-progress,
cancelling, atomic all-success-before-seal, source-owned CancelOpen, byte/field bounds, and
pre-reserved non-wrapping, non-reused terminal sequences. M1-06 and M2-01 still fail
authorization until docs PR #386 is merged at that exact head and tree.

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
        "FMV3-M1-06 merged after live exact issue/PR/topology, RED/GREEN ci_local jobs, canonical-template review, fixed conformance report, and canonical-main proof",
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
        "requirement": "M2-01 cannot begin until M1-06 has merged and bounded external selectors resolve live to its immutable marked/title issue, exact closing same-repository squash PR and canonical-main topology, bounded test-only RED ancestor with empty second diff page and exact-PR hosted checks-job failure at ./scripts/ci_local.sh after successful setup, exact-head GREEN app-bound required checks and checks-job success at ./scripts/ci_local.sh, eight exact-parent production-only mutants whose canonical patch digests are precommitted in the GREEN report and whose mapped tests fail only after same-SHA compile/no-tests success, official Codex canonical-template zero-inline review after mutations, two owner NO_FINDINGS process attestations after GREEN and mutations binding the fixed report blob/case/mutation digests, and the fixed-path closed conformance report binding every validator-pinned case to exact Go test/source blob/PASS, exact mutation patch digest, and exact production contract symbols. The exact docs R2 binding must also verify.",
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


def github_closing_issue_references(
    repository: str,
    pull_request_number: int,
) -> set[tuple[str, int]]:
    owner, name = repository.split("/", 1)
    references: set[tuple[str, int]] = set()
    cursor: str | None = None
    for _page in range(100):
        command = [
            "gh", "api", "graphql",
            "-f", f"query={CLOSING_ISSUES_QUERY}",
            "-F", f"owner={owner}",
            "-F", f"name={name}",
            "-F", f"number={pull_request_number}",
        ]
        if cursor is not None:
            command.extend(["-f", f"cursor={cursor}"])
        result = subprocess.run(
            command, check=True, capture_output=True, text=True,
        )
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
    require(
        created_at > parse_github_time(head_commit_time, "PR #91 head commit time")
        and created_at < parse_github_time(pr.get("merged_at"), "PR #91 merged_at"),
        "PR #91 review attestation must be created after the head commit and before mergedAt",
    )
    workflow = github_api(f"repos/{PLAN_REPOSITORY}/actions/runs/{workflow_run_id}")
    require(isinstance(workflow, dict), "PR #91 workflow run evidence is invalid")
    pull_requests = workflow.get("pull_requests")
    require(
        workflow.get("id") == workflow_run_id
        and workflow.get("workflow_id") == 244018027
        and workflow.get("event") == "pull_request"
        and workflow.get("status") == "completed"
        and workflow.get("conclusion") == "success"
        and workflow.get("head_sha") == head_sha
        and workflow.get("path") == ".github/workflows/ci.yml"
        and workflow.get("actor", {}).get("login") == anchor["authorized_issuer"]
        and workflow.get("head_repository", {}).get("full_name") == PLAN_REPOSITORY
        and isinstance(pull_requests, list)
        and len(pull_requests) == 1
        and isinstance(pull_requests[0], dict)
        and pull_requests[0].get("number") == AMENDMENT_PR_NUMBER
        and pull_requests[0].get("base", {}).get("repo", {}).get("url") == f"https://api.github.com/repos/{EXPECTED_PR_IDENTITY['base_repo']}"
        and pull_requests[0].get("base", {}).get("ref") == EXPECTED_PR_IDENTITY["base_ref"]
        and pull_requests[0].get("head", {}).get("repo", {}).get("url") == f"https://api.github.com/repos/{EXPECTED_PR_IDENTITY['head_repo']}"
        and pull_requests[0].get("head", {}).get("ref") == EXPECTED_PR_IDENTITY["head_ref"]
        and pull_requests[0].get("head", {}).get("sha") == head_sha,
        "PR #91 workflow run does not prove exact live canonical PR head",
    )
    workflow_time = parse_github_time(workflow.get("updated_at"), "PR #91 workflow updated_at")
    reviews = github_paginated_list(
        f"repos/{PLAN_REPOSITORY}/pulls/{AMENDMENT_PR_NUMBER}/reviews",
        "PR #91 native reviews",
    )
    by_id = {review.get("id"): review for review in reviews if isinstance(review, dict) and type(review.get("id")) is int}
    require(len(by_id) == len({review.get("id") for review in reviews if isinstance(review, dict)}), "PR #91 native reviews have duplicate or invalid IDs")
    official_review = by_id.get(official_review_id)
    owner_reviews = [by_id.get(review_id) for review_id in owner_review_ids]
    require(isinstance(official_review, dict) and all(isinstance(item, dict) for item in owner_reviews), "PR #91 aggregate references absent native reviews")
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
    require(official_time > workflow_time and created_at >= official_time, "PR #91 official Codex review timing is invalid")
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
        require(created_at >= evidence_time > workflow_time, "PR #91 aggregate or native review timing is invalid")
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
            and isinstance(body["reviewer_run_reference"], str) and re.fullmatch(r"[0-9a-f-]{36}", body["reviewer_run_reference"])
            and isinstance(body["output_digest_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", body["output_digest_sha256"]),
            "docs PR #386 owner review is not structured owner-attested exact-head NO_FINDINGS process evidence",
        )
        require(parse_github_time(review.get("submitted_at"), "docs owner review submitted_at") > checks_time, "docs PR #386 owner reviews must follow successful CI")
        owner_reviews.append((body["reviewer_run_reference"], body["output_digest_sha256"]))
    require(len(owner_reviews) == 2 and len(set(owner_reviews)) == 2, "docs PR #386 requires two distinct owner COMMENTED process attestations")


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
        "head_tree_sha", "merge_sha", "required_checks",
    }
    for dependency in dependencies:
        require(isinstance(dependency, dict) and set(dependency) == certificate_keys,
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
        required_check_specs(checks, "dependency completion certificate required-check policy")
    producer = evidence.get("producer")
    if issue_id == "FMV3-M2-01":
        producer_keys = {
            "plan_issue", "repository", "github_issue_number",
            "github_pull_request_number", "merge_sha", "red_commit_sha",
            "red_workflow_run_id", "green_workflow_run_id",
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
                and type(producer.get("green_workflow_run_id")) is int
                and producer["green_workflow_run_id"] > 0
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
        mutation_keys = {"case_id", "mutation_commit_sha", "workflow_run_id"}
        mutation_ids: list[str] = []
        mutation_commits: list[str] = []
        mutation_runs: list[int] = []
        for mutation in producer["mutation_runs"]:
            require(isinstance(mutation, dict) and set(mutation) == mutation_keys
                    and mutation.get("case_id") in M1_06_MUTATION_CASES
                    and isinstance(mutation.get("mutation_commit_sha"), str)
                    and re.fullmatch(r"[0-9a-f]{40}", mutation["mutation_commit_sha"])
                    and type(mutation.get("workflow_run_id")) is int
                    and mutation["workflow_run_id"] > 0,
                    "FMV3-M2-01 mutation evidence selector schema mismatch")
            mutation_ids.append(mutation["case_id"])
            mutation_commits.append(mutation["mutation_commit_sha"])
            mutation_runs.append(mutation["workflow_run_id"])
        require(mutation_ids == list(M1_06_MUTATION_CASES)
                and len(set(mutation_commits)) == len(mutation_commits)
                and len(set(mutation_runs)) == len(mutation_runs),
                "FMV3-M2-01 mutation evidence must be ordered and unique")
    return dependencies, producer


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


def live_required_check_specs(protection: Any, label: str) -> list[tuple[str, int]]:
    require(isinstance(protection, dict), f"{label} response is invalid")
    checks = protection.get("checks")
    require(isinstance(checks, list) and checks,
            f"{label} app-bound checks are unavailable")
    value: list[dict[str, Any]] = []
    for check in checks:
        require(isinstance(check, dict), f"{label} check entry is invalid")
        value.append({"context": check.get("context"), "app_id": check.get("app_id")})
    return required_check_specs(value, label)


def require_exact_head_checks(repository: str, head_sha: str,
                              expected: list[Any], label: str) -> list[dict[str, Any]]:
    rows = github_latest_check_runs(repository, head_sha,
                                    f"{label} exact-head check runs")
    matched: list[dict[str, Any]] = []
    for name, app_id in required_check_specs(expected, f"{label} required-check policy"):
        matching = [row for row in rows if isinstance(row, dict)
                    and row.get("name") == name
                    and row.get("head_sha") == head_sha
                    and isinstance(row.get("app"), dict)
                    and row["app"].get("id") == app_id]
        require(len(matching) == 1 and matching[0].get("status") == "completed"
                and matching[0].get("conclusion") == "success",
                f"{label} exact-head required check failed: {name}@{app_id}")
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
            and pr.get("head", {}).get("repo", {}).get("full_name") == repository
            and pr.get("base", {}).get("ref") == "main"
            and pr.get("base", {}).get("repo", {}).get("full_name") == repository,
            f"{label} wrong or unmerged issue/PR binding")
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
    require_exact_head_checks(repository, binding["head_sha"], checks, label)


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


def require_m1_06_red_path(path: str) -> bool:
    relative = safe_repository_path(path, "M1-06 RED diff path")
    parts = relative.parts
    return (
        path in {"go.mod", "go.sum", M1_06_CONFORMANCE_REPORT_PATH}
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
) -> tuple[str, str, dict[str, str]]:
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
        "case_digest", "production", "cases",
    } and report.get("schema") == M1_06_CONFORMANCE_REPORT_SCHEMA
            and report.get("plan_issue") == "FMV3-M1-06"
            and report.get("repository") == repository
            and report.get("contract_id") == "OPAQUE_RUNTIME_ACQUISITION_V1"
            and report.get("case_digest") == M1_06_CONFORMANCE_CASE_DIGEST,
            "M1-06 conformance report identity, digest, or closed schema mismatch")
    production = report.get("production")
    cases = report.get("cases")
    require(isinstance(production, list) and 1 <= len(production) <= 8
            and isinstance(cases, list)
            and len(cases) == len(M1_06_CONFORMANCE_CASES),
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

    bound_symbols: list[str] = []
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
                and not str(item["path"]).endswith("_test.go"),
                "M1-06 production source must be a production Go file")
        for symbol in item["symbols"]:
            require(symbol in M1_06_PRODUCTION_SYMBOLS,
                    "M1-06 production source reports an unknown contract symbol")
            projected = go_code_projection(text)
            declaration = (rf"(?m)^type\s+{re.escape(symbol)}\b"
                           if symbol in {"OpaqueRuntimeCapability", "TerminalOutcome"}
                           else rf"(?m)^func\s+(?:\([^\n)]*\)\s*)?{re.escape(symbol)}\s*\(")
            require(re.search(declaration, projected) is not None,
                    f"M1-06 production source lacks declared contract symbol: {symbol}")
            bound_symbols.append(symbol)
    require(tuple(bound_symbols) == M1_06_PRODUCTION_SYMBOLS,
            "M1-06 production contract symbols are missing, reordered, or duplicated")

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
                and item["source_path"].endswith("_test.go"),
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
    )


def require_m1_06_ci_local_job(repository: str, run_id: int, head_sha: str,
                               *, expected_job_conclusion: str,
                               expected_ci_conclusion: str) -> None:
    jobs = github_paginated_object_rows(
        f"repos/{repository}/actions/runs/{run_id}/jobs",
        "jobs",
        "M1-06 workflow jobs",
    )
    matching = [job for job in jobs if isinstance(job, dict)
                and job.get("name") == M1_06_CI_JOB_NAME]
    require(len(matching) == 1 and matching[0].get("head_sha") == head_sha
            and matching[0].get("status") == "completed"
            and matching[0].get("conclusion") == expected_job_conclusion,
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


def require_m1_06_mutation_evidence(
    anchor: dict[str, Any],
    repository: str,
    head_sha: str,
    mutations: list[dict[str, Any]],
    expected_patch_digests: dict[str, str],
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
        run = github_api(f"repos/{repository}/actions/runs/{run_id}")
        require(isinstance(run, dict) and run.get("id") == run_id
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
        checks = github_latest_check_runs(
            repository, commit_sha, f"M1-06 mutation {case_id} check runs"
        )
        selected_checks = [item for item in checks
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
        jobs = github_paginated_object_rows(
            f"repos/{repository}/actions/runs/{run_id}/jobs",
            "jobs",
            f"M1-06 mutation {case_id} jobs",
        )
        selected_jobs = [job for job in jobs if job.get("name") == check_name]
        require(len(selected_jobs) == 1
                and selected_jobs[0].get("head_sha") == commit_sha
                and selected_jobs[0].get("status") == "completed"
                and selected_jobs[0].get("conclusion") == "failure",
                f"M1-06 mutation {case_id} job is not exact-SHA failure")
        steps = selected_jobs[0].get("steps")
        require(isinstance(steps, list) and 3 <= len(steps) <= 64,
                f"M1-06 mutation {case_id} job steps are invalid")
        setup = [step for step in steps if isinstance(step, dict)
                 and step.get("name") == M1_06_SETUP_STEP_NAME]
        compile_step = [step for step in steps if isinstance(step, dict)
                        and step.get("name") == M1_06_MUTATION_COMPILE_STEP_NAME]
        test_step = [step for step in steps if isinstance(step, dict)
                     and step.get("name") == M1_06_MUTATION_CASES[case_id]]
        require(len(setup) == 1 and setup[0].get("conclusion") == "success"
                and len(compile_step) == 1
                and compile_step[0].get("status") == "completed"
                and compile_step[0].get("conclusion") == "success"
                and len(test_step) == 1 and test_step[0].get("status") == "completed"
                and test_step[0].get("conclusion") == "failure"
                and type(setup[0].get("number")) is int
                and type(compile_step[0].get("number")) is int
                and type(test_step[0].get("number")) is int
                and setup[0]["number"] < compile_step[0]["number"]
                < test_step[0]["number"],
                f"M1-06 mutation {case_id} did not compile before failing its exact mapped test")
        run_time = parse_github_time(run.get("updated_at"),
                                     f"M1-06 mutation {case_id} updated_at")
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
            and github_repository_identity(pr.get("base", {}).get("repo"), repository),
            "M1-06 producer exact closing PR or canonical base/head mismatch")
    require(isinstance(head_commit, dict) and head_commit.get("sha") == head_sha
            and head_commit.get("tree", {}).get("sha") == head_tree_sha
            and isinstance(merge_commit, dict) and merge_commit.get("sha") == merge_sha
            and merge_commit.get("tree", {}).get("sha") == head_tree_sha
            and isinstance(merge_commit.get("parents"), list)
            and len(merge_commit["parents"]) == 1
            and merge_commit["parents"][0].get("sha") == pr.get("base", {}).get("sha"),
            "M1-06 reviewed implementation head/squash tree or base topology mismatch")

    red_commit = github_api(f"repos/{repository}/git/commits/{red_sha}")
    red_diff = github_api(
        f"repos/{repository}/commits/{red_sha}?per_page=65&page=1"
    )
    red_diff_page_2 = github_api(
        f"repos/{repository}/commits/{red_sha}?per_page=65&page=2"
    )
    red_compare = github_api(f"repos/{repository}/compare/{red_sha}...{head_sha}")
    require(isinstance(red_commit, dict) and red_commit.get("sha") == red_sha
            and isinstance(red_commit.get("parents"), list)
            and len(red_commit["parents"]) == 1,
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
    red_run = github_api(f"repos/{repository}/actions/runs/{red_run_id}")
    run_prs = red_run.get("pull_requests") if isinstance(red_run, dict) else None
    require(isinstance(red_run, dict) and red_run.get("id") == red_run_id
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
    red_checks = github_latest_check_runs(
        repository, red_sha, "M1-06 hosted RED check runs"
    )
    matching_red_checks = [item for item in red_checks if isinstance(item, dict)
                           and item.get("name") == M1_06_RED_REQUIRED_CHECK]
    require(len(matching_red_checks) == 1, "M1-06 exact RED required check is missing or ambiguous")
    red_check = matching_red_checks[0]
    red_check_prs = red_check.get("pull_requests")
    run_url = f"https://github.com/{repository}/actions/runs/{red_run_id}"
    require(red_check.get("head_sha") == red_sha
            and red_check.get("status") == "completed"
            and red_check.get("conclusion") == "failure"
            and isinstance(red_check.get("details_url"), str)
            and (red_check["details_url"] == run_url
                 or red_check["details_url"].startswith(run_url + "/"))
            and isinstance(red_check_prs, list) and len(red_check_prs) == 1
            and red_check_prs[0].get("number") == pr_number
            and red_check_prs[0].get("head", {}).get("sha") == red_sha,
            "M1-06 hosted RED check is not a failing exact-SHA exact-PR check")
    require_m1_06_ci_local_job(
        repository, red_run_id, red_sha,
        expected_job_conclusion="failure", expected_ci_conclusion="failure",
    )

    green_rows = require_exact_head_checks(
        repository, head_sha, dependency["required_checks"], "M1-06 hosted GREEN"
    )
    green_completed_at = max(parse_github_time(
        item.get("completed_at"), f"M1-06 GREEN {item.get('name')} completed_at"
    ) for item in green_rows)
    green_run_id = producer["green_workflow_run_id"]
    green_run = github_api(f"repos/{repository}/actions/runs/{green_run_id}")
    green_prs = green_run.get("pull_requests") if isinstance(green_run, dict) else None
    require(isinstance(green_run, dict) and green_run.get("id") == green_run_id
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
    green_run_url = f"https://github.com/{repository}/actions/runs/{green_run_id}"
    green_check_rows = {
        item.get("id"): item for item in green_rows
        if item.get("name") == M1_06_RED_REQUIRED_CHECK
        and type(item.get("id")) is int
    }
    require(len(green_check_rows) == 1
            and isinstance(next(iter(green_check_rows.values())).get("details_url"), str)
            and (next(iter(green_check_rows.values()))["details_url"] == green_run_url
                 or next(iter(green_check_rows.values()))["details_url"].startswith(green_run_url + "/")),
            "M1-06 GREEN checks check-run is not bound to the selected GREEN run")
    require_m1_06_ci_local_job(
        repository, green_run_id, head_sha,
        expected_job_conclusion="success", expected_ci_conclusion="success",
    )
    report_blob_sha, case_digest, mutation_patch_digests = (
        require_m1_06_conformance_report(
        repository, head_tree_sha
        )
    )
    mutation_digest, mutations_completed_at = require_m1_06_mutation_evidence(
        anchor, repository, head_sha, producer["mutation_runs"],
        mutation_patch_digests,
    )
    review_not_before = max(green_completed_at, mutations_completed_at)

    reviews = github_paginated_list(
        f"repos/{repository}/pulls/{pr_number}/reviews",
        "M1-06 producer reviews",
    )
    official = [review for review in reviews if isinstance(review, dict)
                and review.get("id") == producer["official_review_id"]]
    require(len(official) == 1
            and official[0].get("user", {}).get("login") == "chatgpt-codex-connector[bot]"
            and official[0].get("state") == "COMMENTED"
            and official[0].get("commit_id") == head_sha
            and official[0].get("body") == canonical_codex_review_body(head_sha)
            and parse_github_time(official[0].get("submitted_at"),
                                  "M1-06 official Codex submitted_at") > review_not_before,
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
    checks = protection.get("checks", [])
    require(
        isinstance(checks, list)
        and any(
            isinstance(check, dict)
            and check.get("context") == gate["required_check"]
            and check.get("app_id") == GITHUB_ACTIONS_APP_ID
            for check in checks
        ),
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
        "External review attestation": "successful exact-head canonical pull_request workflow run, one authenticated official Codex review, two owner process attestations, and unedited aggregate binding workflow-run and review IDs",
        "Docs R2 rebind": "complete; exact docs PR #386 head/tree, canonical-main ancestry, exact-head CI, and review chain bound",
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
            raise ValidationError(
                "issue authorization requires the trusted cruise-preflight anchor materializer"
            )
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
            require_issue_authorization_dependencies(
                args.authorize_issue,
                anchored_anchor,
                args.authorization_evidence,
                anchored_deps,
                anchored_repos,
                anchored_issue_specs,
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
