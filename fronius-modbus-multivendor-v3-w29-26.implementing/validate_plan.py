#!/usr/bin/env python3
"""Validate only the structural contract of this locked execution-plan package."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
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
AMENDMENT_PR_URL = "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/89"
AMENDMENT_SURFACE_FILES = (
    "00-canonical.md",
    "90-issue-map.md",
    "91-milestone-map.md",
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
CANONICAL_AUTHORIZATION_BLOCK = """Execution activates only after PR #89 merges. Its exact merge commit is the sole immutable
authorization anchor. Issue #88 is tracking metadata only and is not cryptographic or
authorization evidence.

The ordered `authorized_issues` list in `plan.yaml` is the sole normative execution scope:
FMV3-M0-01, FMV3-M0-02, FMV3-M0-03, FMV3-M0-06, FMV3-M1-00, FMV3-M1-01,
FMV3-M1-02, FMV3-M1-03, FMV3-M1-04, FMV3-M1-05, FMV3-M1-06, FMV3-M2-01,
FMV3-M2-02, FMV3-M2-03, FMV3-M3-01, FMV3-M3-02, and FMV3-M3-03. Milestone names
are non-authoritative grouping labels. The amendment adds FMV3-M1-05 and FMV3-M1-06
and amends FMV3-M2-01.

FMV3-M0-01 creates only the two empty public repositories `helianthus-modbus` and
`helianthus-modbusreg`. FMV3-M1-05 publishes the public
`OPAQUE_RUNTIME_ACQUISITION_V1` companion, FMV3-M1-06 implements it after M1-05, and
FMV3-M2-01 consumes the merged M1-06 producer by exact full-SHA pin. Private governance
creation FMV3-M0-04 and destination bootstraps FMV3-M0-05/FMV3-M0-07 remain deferred.

The hard stop is immediately before FMV3-M4-01. Gateway work is not authorized. No gateway
issue, branch, PR, import, or code change is authorized by this action. Repository creation,
implementation issues, commits, pushes, reviews, and merges are authorized only for the
ordered issue list above and remain subject to every dependency and gate."""
EXPECTED_MILESTONE_ROWS = {
    "M1": [
        "M1",
        "M0",
        "Modbus bootstrap and M0 boundary docs complete",
        "FMV3-M1-00 fixes existing operations/recovery/coalescing; after M1-04, M1-05 docs then M1-06 hosted RED/GREEN implement OPAQUE_RUNTIME_ACQUISITION_V1 with fresh review",
        "Original history stays intact; the corrective docs issue precedes code, and absent RTU hardware blocks no TCP work",
    ],
    "M2": [
        "M2",
        "M0",
        "Modbusreg bootstrap, merged FMV3-M1-00, merged M1-06, and exact full-SHA consumer pin",
        "Shared bounded attempt ledger, duplicate-key rejection, sealed immutable Publish(), runtime/fixture trust split, exact normalization round-trip, logical-view provenance, detector/qualification/coherence conformance",
        "M2-01 retains M1-00 and adds M1-05 corrective companion metadata; hosted RED/GREEN and fresh review are mandatory",
    ],
}
EXPECTED_CORRECTIVE_GATE_ROWS = [
    [
        "PG-OPAQUE-ACQUISITION-DOC-GATE",
        "FMV3-M1-05 merged after M1-04, exact docs head fresh-reviewed",
        "FMV3-M1-06",
    ],
    [
        "PG-OPAQUE-ACQUISITION-CONSUMER-PIN",
        "FMV3-M1-06 merged after hosted RED/GREEN and fresh review; consumer pins full merged SHA",
        "FMV3-M2-01",
    ],
]
EXPECTED_CORRECTIVE_PHASE_GATES = [
    {
        "id": "PG-OPAQUE-ACQUISITION-DOC-GATE",
        "kind": "dependency",
        "after_issues": ["FMV3-M1-05"],
        "before_issues": ["FMV3-M1-06"],
        "requirement": "The public OPAQUE_RUNTIME_ACQUISITION_V1 companion merges after M1-04 and before M1-06 code, defining source_kind runtime versus offline_fixture, source-issued non-serializable one-shot capability semantics, bounded attempt lifecycle, shared copy/recreation state, per-dependent coalesced capabilities, and lossless normalization. A fresh independent OpenAI review of the exact docs revision is a merge blocker.",
    },
    {
        "id": "PG-OPAQUE-ACQUISITION-CONSUMER-PIN",
        "kind": "dependency",
        "after_issues": ["FMV3-M1-06"],
        "before_issues": ["FMV3-M2-01"],
        "requirement": "M2-01 cannot begin until M1-06 has merged, its exact full 40-character merge SHA is pinned and verified by the consumer, and the M1 hosted RED/GREEN plus fresh independent review evidence is closed.",
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
def require_authorization_pr_merged(
    anchor: dict[str, Any],
    plan_head_sha: str,
) -> None:
    pr_url = anchor.get("authorization_pr")
    require(pr_url == AMENDMENT_PR_URL, "authorization requires the exact merged PR #89 URL")
    pr_number = 89
    pr = github_api(
        f"repos/Project-Helianthus/helianthus-execution-plans/pulls/{pr_number}"
    )
    require(
        isinstance(pr, dict)
        and pr.get("number") == pr_number
        and pr.get("html_url") == pr_url
        and pr.get("base", {}).get("ref") == "main"
        and pr.get("base", {}).get("repo", {}).get("full_name") == anchor["plan_repo"],
        "authorization PR #89 identity mismatch",
    )
    require(
        pr.get("state") == "closed"
        and pr.get("merged") is True
        and pr.get("merge_commit_sha") == plan_head_sha,
        "authorization PR #89 is not merged at the plan authorization SHA",
    )
    require(
        pr.get("user", {}).get("login") == anchor["authorized_issuer"],
        "authorization PR #89 issuer mismatch",
    )
    require(
        pr.get("author_association") in anchor["allowed_author_associations"],
        "authorization PR #89 author association is not allowed",
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
        "authorization requires the exact merged PR #89 URL",
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
        "preflight_enforcement": "validate_plan.py --authorize-issue <ID>",
        "milestone_labels_non_authoritative": ["M0", "M1", "M2", "M3"],
        "authorized_issues": AUTHORIZED_ISSUES,
        "authorized_issue_contract_sha256": authorization.get(
            "authorized_issue_contract_sha256"
        ),
        "authorization_anchor": {
            "required": True,
            "record_type": "github_merged_pr_v1",
            "authorization_pr": AMENDMENT_PR_URL,
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
            ],
            "added_issues": ["FMV3-M1-05", "FMV3-M1-06"],
            "amended_issues": ["FMV3-M2-01"],
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
    return authorization
def extract_canonical_authorization_block(text: str) -> str:
    matches = re.findall(
        r"^## Execution authorization\n\n(.*?)\n\n^## Claim discipline$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    require(len(matches) == 1, "canonical authorization block must occur exactly once")
    require(
        matches[0] == CANONICAL_AUTHORIZATION_BLOCK,
        "canonical authorization and hard-stop block mismatch",
    )
    return matches[0]


def amendment_status_metadata(status: str) -> dict[str, str]:
    keys = (
        "State",
        "Current milestone",
        "Review epoch",
        "Review state",
        "Accepted adversarial rounds",
        "Review target",
        "Lock authorized",
        "Implementation authorized",
        "Authorization scope authority",
        "Authorization anchor",
        "Repository creation authorized",
        "Private repository action",
        "Commit/push authorized",
        "Gateway work authorized",
        "Private creation/bootstrap authorized",
    )
    metadata: dict[str, str] = {}
    for key in keys:
        values = re.findall(rf"^{re.escape(key)}: (.+)$", status, re.MULTILINE)
        require(len(values) == 1, f"status must contain exactly one {key} field")
        metadata[key] = values[0]
    return metadata


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
    anchored_status = anchored_projection["status"]["metadata"]
    current_status = current_projection["status"]["metadata"]
    require(
        current_status.get("Gateway work authorized")
        == anchored_status["Gateway work authorized"],
        "status Gateway work authorized mismatch",
    )
    require(
        current_projection == anchored_projection,
        "current main amendment surface digest differs from merged PR #89 anchor",
    )


def amendment_surface_projection(
    plan: dict[str, Any],
    texts: dict[str, str],
) -> dict[str, Any]:
    require(
        set(texts) == set(AMENDMENT_SURFACE_FILES),
        "amendment surface file set mismatch",
    )
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
    status_metadata = amendment_status_metadata(status)
    status_states = [status_metadata["State"]]
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
    return {
        "schema": "helianthus.fmv3-amendment-surfaces.v1",
        "execution_authorization": {
            "authorized_issues": authorization["authorized_issues"],
            "added_issues": anchor["added_issues"],
            "amended_issues": anchor["amended_issues"],
            "stop_before_issue": authorization["stop_before_issue"],
            "gateway_work_authorized": authorization["gateway_work_authorized"],
        },
        "issue_sequence": issue_sequence,
        "issue_rows": [issues_by_id[issue_id] for issue_id in AMENDMENT_ISSUE_IDS],
        "issue_map_rows": [
            issue_map_rows[issue_id] for issue_id in AMENDMENT_ISSUE_IDS
        ],
        "phase_gates": [
            *corrective_gates,
        ],
        "canonical_authorization_block": canonical_block,
        "milestone_rows": [
            milestone_by_id["M1"],
            milestone_by_id["M2"],
        ],
        "milestone_corrective_gate_rows": corrective_gate_rows,
        "status": {
            "state": status_states[0],
            "issue_count": int(status_issue_counts[0]),
            "metadata": status_metadata,
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
    validate_authorization_schema(plan)
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
    opaque_contract = {
        "representation": "opaque_non_serializable",
        "issuer": "runtime_source",
        "issue_condition": "deliverable_runtime_acquisition_only",
        "forbidden_issue_conditions": ["non_deliverable_runtime_acquisition", "offline_fixture"],
        "consumption": "one_shot_compare_and_swap",
        "state_owner": "source_issued_shared_ledger_pointer",
        "value_copy_semantics": "shared_state",
        "endpoint_recreation_semantics": "shared_state",
        "coalesced_dependents": "independent_capability_per_dependent",
        "copied_view_race": "exactly_one_winner",
        "terminal_reuse": "forbidden",
        "bounded_state": {
            "capabilities": "endpoint_configured_hard_limit",
            "open_attempts": "consumer_configured_hard_limit",
            "claims_per_attempt": "dependency_set_hard_limit",
            "terminal_reclamation": "required",
        },
    }
    normalization_contract = {
        "schema": "versioned",
        "record_fields": [
            "schema_version", "source_kind", "source_evidence_id",
            "documentary_notation", "documentary_address",
            "documentary_address_base", "function_code", "logical_table",
            "normalized_zero_based_pdu_offset", "word_count",
        ],
        "unknown_extension_fields": "preserved_losslessly",
        "round_trip": "exact_record_equality",
    }
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
        },
        "FMV3-M1-06": issue_fields | {
            "companion_issue", "doc_gate", "fresh_adversarial_contract",
            "implements_contract", "opaque_runtime_acquisition_contract",
            "strict_tdd_contract",
        },
        "FMV3-M2-01": issue_fields | {
            "attempt_ledger_contract", "companion_issue",
            "consumes_contract", "corrective_companion_issue",
            "doc_gate", "fresh_adversarial_contract",
            "normalization_round_trip_contract", "observation_view_fields",
            "producer_pin_contract", "source_trust_contract",
            "strict_tdd_contract",
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
        and opaque_docs.get("source_kind_contract") == {
            "allowed": ["runtime", "offline_fixture"],
            "runtime_trust": "capability_required_for_delivery",
            "offline_fixture_trust": "untrusted_no_capability",
        }
        and opaque_docs.get("opaque_runtime_acquisition_contract") == opaque_contract
        and opaque_docs.get("normalization_round_trip_contract") == normalization_contract
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
        and opaque_runtime.get("opaque_runtime_acquisition_contract") == opaque_contract
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
        and m2_contract.get("producer_pin_contract") == {
            "producer_issue": "FMV3-M1-06",
            "merge_sha": "required_full_40_lowercase_hex",
            "consumer_resolution": "exact_sha_verified_before_red",
        }
        and m2_contract.get("source_trust_contract") == {
            "runtime": {
                "capability": "required",
                "delivery_trust": "successful_one_shot_cas",
            },
            "offline_fixture": {
                "capability": "forbidden",
                "capability_cas_calls": 0,
                "trust": "untrusted",
                "production_sample_id": "forbidden",
            },
        }
        and m2_contract.get("attempt_ledger_contract") == {
            "state_owner": "shared_ledger_owned_pointer",
            "attempt_key_uniqueness": "duplicate_rejected",
            "attempt_bound": "configured_hard_limit",
            "claims_per_attempt_bound": "dependency_set_hard_limit",
            "claim_capability": "one_shot_runtime_capability",
            "seal_transition": "open_to_sealed_once",
            "sealed_attempt_set": "immutable",
            "publish_signature": "Publish()",
            "publish_input": "sealed_ledger_state",
            "mutable_dto": "forbidden",
            "terminal_reclamation": "required",
        }
        and m2_contract.get("normalization_round_trip_contract") == normalization_contract
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
        "Issue #88 corrective amendment gate" in review
        and "FMV3-M1-05" in review
        and "FMV3-M1-06" in review
        and "FMV3-M2-01" in review
        and re.search(r"does not\s+retroactively place the amendment inside epoch 3 R5", review) is not None,
        "issue #88 fresh adversarial amendment gate mirror missing",
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
        "Authorization anchor": "PR #89 merge commit required; issue #88 is tracking only",
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
    parser.add_argument("--print-amendment-surfaces-sha256", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve() if args.root is not None else Path(__file__).resolve().parent
    try:
        if args.print_amendment_surfaces_sha256:
            plan = load_plan(root / "plan.yaml")
            print(amendment_surface_digest(plan, load_amendment_surface_texts(root)))
            return 0
        issue_count, milestone_count = validate(root)
        if args.authorize_issue is not None:
            plan = load_plan(root / "plan.yaml")
            authorization = plan["execution_authorization"]
            require(
                args.plan_head_sha is not None and re.fullmatch(r"[0-9a-f]{40}", args.plan_head_sha) is not None,
                "--plan-head-sha with a full lowercase 40-character SHA is mandatory",
            )
            actual_head = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            remote_main_result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "ls-remote",
                    "--exit-code",
                    "origin",
                    "refs/heads/main",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            remote_main_rows = remote_main_result.stdout.splitlines()
            require(
                len(remote_main_rows) == 1
                and re.fullmatch(
                    r"[0-9a-f]{40}\trefs/heads/main",
                    remote_main_rows[0],
                )
                is not None,
                "authorization requires one exact live origin main ref",
            )
            origin_main = remote_main_rows[0].split("\t", 1)[0]
            require(actual_head == origin_main, "authorization requires the checked-out live origin main HEAD")
            anchor_is_merged = subprocess.run(
                ["git", "-C", str(root), "merge-base", "--is-ancestor", args.plan_head_sha, origin_main],
                check=False,
            ).returncode == 0
            require(anchor_is_merged, "authorization anchor is not reachable from authoritative origin/main")
            repo_root = Path(
                subprocess.run(
                    ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
            )
            index_flags = subprocess.run(
                ["git", "-C", str(repo_root), "ls-files", "-v"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
            require(
                all(line.startswith("H ") for line in index_flags),
                "authorization rejects assume-unchanged, skip-worktree, or other nonstandard index flags",
            )
            plan_worktree_status = subprocess.run(
                ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            require(not plan_worktree_status, "authorization requires the entire checkout to match the committed main HEAD")
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
                "authorization record is absent from the merged PR #89 anchor",
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
                    f"amendment surface {name} is absent from merged PR #89 anchor",
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
                "current main amendment surface digest differs from merged PR #89 anchor",
            )
            if (
                re.fullmatch(r"FMV3-M[123]-\d{2}", args.authorize_issue)
                is not None
                and args.authorize_issue not in {"FMV3-M1-00", "FMV3-M1-05"}
            ):
                require_m1_admission_open(repo_root, origin_main)
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
