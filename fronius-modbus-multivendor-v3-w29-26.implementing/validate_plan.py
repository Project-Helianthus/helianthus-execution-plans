#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import deque
from pathlib import Path
from typing import Any

import yaml


class ValidationError(ValueError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValidationError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_mapping,
)


ROOT_KEYS = {
    "schema_version",
    "slug",
    "title",
    "state",
    "repositories",
    "contracts",
    "review_policy",
    "transport_neutral_boundary",
    "ordering",
    "milestones",
    "issues",
}

KNOWN_REPOSITORIES = {
    "Project-Helianthus/.github",
    "Project-Helianthus/helianthus-modbus",
    "Project-Helianthus/helianthus-modbusreg",
    "Project-Helianthus/helianthus-ebusgateway",
    "Project-Helianthus/helianthus-ebusreg",
    "Project-Helianthus/helianthus-ha-integration",
    "Project-Helianthus/helianthus-ha-addon",
    "Project-Helianthus/helianthus-docs-ebus",
    "Project-Helianthus/helianthus-eebus-binding-private",
    "Project-Helianthus/helianthus-matter-binding-private",
    "Project-Helianthus/helianthus-execution-plans",
}

EXPECTED_CONTRACTS = {
    "OPAQUE_RUNTIME_ACQUISITION_V1": 1,
    "helianthus.modbus.opaque-runtime-acquisition": 1,
    "published_attempt_v1": 1,
    "helianthus.fmv3-m1-06-conformance-report.v3": 3,
    "helianthus.fmv3-m3-03-completion.v2": 2,
    "RTU_PHYSICAL_QUALIFICATION_V1": 1,
    "PUBLIC_GRAPHQL_M2M_V1": 1,
}

EXPECTED_MILESTONES = tuple(f"M{number}" for number in range(9))

EXPECTED_ISSUE_IDS = (
    "FMV3-M0-01", "FMV3-M0-02", "FMV3-M0-03", "FMV3-M0-04",
    "FMV3-M0-05", "FMV3-M0-07", "FMV3-M0-06", "FMV3-M1-00",
    "FMV3-M1-01", "FMV3-M1-02", "FMV3-M1-03", "FMV3-M1-04",
    "FMV3-M1-05", "FMV3-M1-06", "FMV3-M2-01", "FMV3-M2-02",
    "FMV3-M2-03", "FMV3-M3-01", "FMV3-M3-02", "FMV3-M3-03",
    "FMV3-M4-01", "FMV3-M4-02", "FMV3-M4-03", "FMV3-M4-04",
    "FMV3-M4-05", "FMV3-M5-01", "FMV3-M5-02", "FMV3-M5-03",
    "FMV3-M5-04", "FMV3-M5-09", "FMV3-M5-05", "FMV3-M5-06",
    "FMV3-M5-07", "FMV3-M5-08", "FMV3-M6-00", "FMV3-M6-01",
    "FMV3-M6-02", "FMV3-M6-03", "FMV3-M7-01", "FMV3-M7-02",
    "FMV3-M7-03", "FMV3-M7-04", "FMV3-M7-05", "FMV3-M8-00",
    "FMV3-M8-01", "FMV3-M8-02",
)

EXPECTED_ORDERING = {
    "modbus_foundation": (
        "FMV3-M1-00", "FMV3-M1-01", "FMV3-M1-02", "FMV3-M1-04",
    ),
    "runtime_contract_producer_consumer": (
        "FMV3-M1-05", "FMV3-M1-06", "FMV3-M2-01",
    ),
    "fronius_first": (
        "FMV3-M3-01", "FMV3-M3-02", "FMV3-M3-03", "FMV3-M4-01",
    ),
    "semantic_promotion": (
        "FMV3-M5-02", "FMV3-M5-01", "FMV3-M5-04", "FMV3-M5-03",
        "FMV3-M5-09", "FMV3-M5-05", "FMV3-M5-06", "FMV3-M5-07",
        "FMV3-M5-08",
    ),
    "eebus_binding": (
        "FMV3-M6-00", "FMV3-M6-01", "FMV3-M6-02", "FMV3-M6-03",
    ),
    "vendor_expansion": (
        "FMV3-M7-01", "FMV3-M7-02", "FMV3-M7-03", "FMV3-M7-04",
        "FMV3-M7-05",
    ),
    "matter_binding": ("FMV3-M8-00", "FMV3-M8-01", "FMV3-M8-02"),
}

EXPECTED_REVIEW_POLICY = {
    "blocking_severities": ["P0", "P1", "P2"],
    "merge_verdict": "NO_BLOCKING_FINDINGS",
    "exact_head_review": "required",
    "repeat_while_blocking_findings_exist": True,
    "prior_blocking_findings": "resolved_or_independently_validated_by_design",
    "nonblocking_severities": ["P3", "P4"],
    "nonblocking_triage": ["fix", "backlog", "by_design"],
    "nonblocking_requires_another_round": False,
    "duplicate_findings_reopen": False,
    "by_design_independent_opinions": 1,
    "scope": "acceptance_criteria_and_declared_threat_model",
    "p2_evidence": [
        "concrete_reachable_scenario",
        "wrong_behavior",
        "relevant_impact",
        "verifiable_fix_criterion",
    ],
    "theoretical_out_of_threat_model_is_p2": False,
}

REQUIRED_FILES = {
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
    "plan.yaml",
    "validate_plan.py",
}

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_plan(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValidationError(f"invalid YAML: {exc}") from exc
    _require(isinstance(value, dict), "plan.yaml root must be a mapping")
    return value


def _rows(value: Any, name: str, fields: set[str]) -> list[dict[str, Any]]:
    _require(isinstance(value, list), f"{name} must be a list")
    result: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        _require(isinstance(row, dict), f"{name}[{index}] must be a mapping")
        _require(set(row) == fields, f"{name}[{index}] fields are invalid")
        result.append(row)
    return result


def _unique_ids(rows: list[dict[str, Any]], name: str) -> list[str]:
    ids = [row.get("id") for row in rows]
    _require(all(isinstance(value, str) and value for value in ids), f"{name} IDs must be nonempty strings")
    _require(len(ids) == len(set(ids)), f"{name} IDs must be unique")
    return ids


def _ancestors(issue_id: str, issues: dict[str, dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    pending = list(issues[issue_id]["depends_on"])
    while pending:
        dependency = pending.pop()
        if dependency in result:
            continue
        result.add(dependency)
        pending.extend(issues[dependency]["depends_on"])
    return result


def _validate_graph(issues: dict[str, dict[str, Any]]) -> None:
    outgoing = {issue_id: [] for issue_id in issues}
    indegree = {issue_id: 0 for issue_id in issues}
    for issue_id, issue in issues.items():
        dependencies = issue["depends_on"]
        _require(isinstance(dependencies, list), f"{issue_id} depends_on must be a list")
        _require(len(dependencies) == len(set(dependencies)), f"{issue_id} has duplicate dependencies")
        for dependency in dependencies:
            _require(dependency in issues, f"{issue_id} has unknown dependency {dependency}")
            _require(dependency != issue_id, f"{issue_id} cannot depend on itself")
            outgoing[dependency].append(issue_id)
            indegree[issue_id] += 1
    ready = deque(sorted(key for key, count in indegree.items() if count == 0))
    visited = 0
    while ready:
        current = ready.popleft()
        visited += 1
        for successor in outgoing[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    _require(visited == len(issues), "issue dependency graph must be acyclic")


def _markdown_table(path: Path, header: tuple[str, ...]) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    found = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if found and rows:
                break
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if not found:
            if cells == header:
                found = True
            continue
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        _require(len(cells) == len(header), f"{path.name} has a malformed table row")
        rows.append(cells)
    _require(found, f"{path.name} is missing the expected table")
    return rows


def _validate_mirrors(
    plan_dir: Path,
    milestones: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    expected_issues = [
        (
            issue["id"],
            issue["milestone"],
            issue["repo"],
            ", ".join(issue["depends_on"]) if issue["depends_on"] else "-",
        )
        for issue in issues
    ]
    actual_issues = _markdown_table(
        plan_dir / "90-issue-map.md",
        ("ID", "Milestone", "Repository", "Depends on"),
    )
    _require(actual_issues == expected_issues, "issue map does not mirror plan.yaml")

    expected_milestones = [(row["id"], row["title"]) for row in milestones]
    actual_milestones = _markdown_table(
        plan_dir / "91-milestone-map.md",
        ("Milestone", "Title"),
    )
    _require(actual_milestones == expected_milestones, "milestone map does not mirror plan.yaml")

    status_text = (plan_dir / "99-status.md").read_text(encoding="utf-8")
    for expected_status in (
        f"- planned nodes: {len(issues)}",
        "- completed nodes: 36",
        "- remaining nodes: 10",
        "clean stop after `FMV3-M7-05`",
        "M0: `FMV3-M0-04`, `FMV3-M0-05`, and `FMV3-M0-07`",
        "M6: `FMV3-M6-00` through `FMV3-M6-03`",
        "M8: `FMV3-M8-00` through `FMV3-M8-02`",
    ):
        _require(expected_status in status_text, "reconciled status is incomplete or stale")

    canonical_text = " ".join(
        (plan_dir / "00-canonical.md").read_text(encoding="utf-8").split()
    )
    _require(
        "The original M0-M3 plan cycle ended after `FMV3-M3-03` and immediately before "
        "`FMV3-M4-01`." in canonical_text,
        "canonical historical boundary is incomplete or stale",
    )
    _require(
        "The reconciled public delivery stops after `FMV3-M7-05`." in canonical_text,
        "canonical reconciled boundary is incomplete or stale",
    )


def validate_plan(plan_dir: Path) -> dict[str, int]:
    plan_dir = plan_dir.resolve()
    missing = sorted(name for name in REQUIRED_FILES if not (plan_dir / name).is_file())
    _require(not missing, f"missing required files: {', '.join(missing)}")
    _require(not (plan_dir / "templates").exists(), "FMV3 templates directory must be removed")

    plan = load_plan(plan_dir / "plan.yaml")
    _require(set(plan) == ROOT_KEYS, "plan.yaml root fields are invalid")
    _require(plan["schema_version"] == 1, "schema_version must be 1")
    _require(plan["slug"] == "fronius-modbus-multivendor-v3-w29-26", "slug is invalid")
    _require(plan["state"] == "implementing", "state must be implementing")

    repositories = plan["repositories"]
    _require(isinstance(repositories, dict), "repositories must be a mapping")
    _require(set(repositories) == KNOWN_REPOSITORIES, "repository set is invalid")
    _require(all(isinstance(role, str) and role for role in repositories.values()), "repository roles must be nonempty strings")

    contracts = _rows(plan["contracts"], "contracts", {"id", "version"})
    contract_ids = _unique_ids(contracts, "contract")
    contract_map = {row["id"]: row["version"] for row in contracts}
    _require(contract_map == EXPECTED_CONTRACTS, "retained contract IDs or versions changed")
    _require(len(contract_ids) == 7, "expected 7 retained contracts")

    milestones = _rows(plan["milestones"], "milestones", {"id", "title"})
    milestone_ids = _unique_ids(milestones, "milestone")
    _require(tuple(milestone_ids) == EXPECTED_MILESTONES, "expected milestones M0 through M8")
    _require(all(isinstance(row["title"], str) and row["title"] for row in milestones), "milestone titles must be nonempty")

    issues = _rows(
        plan["issues"],
        "issues",
        {"id", "milestone", "repo", "depends_on", "title", "acceptance", "gates", "rollback"},
    )
    issue_ids = _unique_ids(issues, "issue")
    _require(tuple(issue_ids) == EXPECTED_ISSUE_IDS, "the retained 46 issue IDs changed")
    issue_map = {row["id"]: row for row in issues}
    for issue in issues:
        issue_id = issue["id"]
        _require(re.fullmatch(r"FMV3-M[0-8]-\d{2}", issue_id) is not None, f"invalid issue ID {issue_id}")
        _require(issue["milestone"] in milestone_ids, f"{issue_id} has unknown milestone")
        _require(issue["milestone"] == issue_id.split("-")[1], f"{issue_id} milestone mirror is invalid")
        _require(issue["repo"] in KNOWN_REPOSITORIES, f"{issue_id} has unknown repository")
        _require(isinstance(issue["title"], str) and issue["title"], f"{issue_id} title must be nonempty")
        _require(isinstance(issue["acceptance"], str) and issue["acceptance"], f"{issue_id} acceptance must be nonempty")
        _require(isinstance(issue["rollback"], str) and issue["rollback"], f"{issue_id} rollback must be nonempty")
        gates = issue["gates"]
        _require(isinstance(gates, list) and gates, f"{issue_id} gates must be a nonempty list")
        _require(all(isinstance(gate, str) and gate for gate in gates), f"{issue_id} gates must be nonempty strings")
        _require(len(gates) == len(set(gates)), f"{issue_id} has duplicate gates")
    _validate_graph(issue_map)

    for bootstrap_id in ("FMV3-M0-05", "FMV3-M0-07"):
        _require(
            "CI" in issue_map[bootstrap_id]["gates"],
            f"{bootstrap_id} private bootstrap must retain its CI gate",
        )

    private_creation = issue_map["FMV3-M0-04"]
    _require(
        "operator_confirmation" in private_creation["gates"]
        and "Only after explicit operator confirmation" in private_creation["acceptance"],
        "FMV3-M0-04 private repository creation requires explicit operator confirmation",
    )

    m8 = issue_map["FMV3-M8-02"]
    _require(
        not any(issue_id.startswith("FMV3-M6-") for issue_id in _ancestors(m8["id"], issue_map)),
        "FMV3-M8-02 must remain independent of M6",
    )
    m8_acceptance = m8["acceptance"]
    _require(
        "PUBLIC_GRAPHQL_M2M_V1" in m8_acceptance
        and "sole ingress" in m8_acceptance
        and "cannot change or bypass the locked PV contract" in m8_acceptance,
        "FMV3-M8-02 must retain sole public ingress and locked PV contract acceptance",
    )

    ordering_rows = _rows(plan["ordering"], "ordering", {"id", "sequence"})
    ordering_ids = _unique_ids(ordering_rows, "ordering")
    ordering = {row["id"]: tuple(row["sequence"]) for row in ordering_rows}
    _require(set(ordering_ids) == set(EXPECTED_ORDERING), "ordering declarations are incomplete")
    _require(ordering == EXPECTED_ORDERING, "ordering declarations changed")
    for name, sequence in ordering.items():
        for predecessor, successor in zip(sequence, sequence[1:]):
            _require(predecessor in _ancestors(successor, issue_map), f"{name} ordering is not present in the DAG")

    _require(plan["review_policy"] == EXPECTED_REVIEW_POLICY, "review policy changed")

    for issue_id in ("FMV3-M4-01", "FMV3-M4-02"):
        issue = issue_map[issue_id]
        _require("doc_gate" in issue["gates"], f"{issue_id} must retain doc_gate")
        _require(
            "FMV3-M0-06" in _ancestors(issue_id, issue_map),
            f"{issue_id} must remain downstream of the public gateway/MCP contract",
        )

    docs_acceptance = issue_map["FMV3-M0-06"]["acceptance"]
    for required_term in (
        "gateway Modbus endpoint ownership",
        "bounded read-only raw/profile MCP contract",
        "before gateway implementation",
    ):
        _require(
            required_term in docs_acceptance,
            f"FMV3-M0-06 must retain public gateway/MCP contract term: {required_term}",
        )

    _require(plan["transport_neutral_boundary"] == {
        "issue": "FMV3-M3-03",
        "evidence_transport": "Modbus TCP",
        "production_scope": "transport-neutral read-only profile logic",
        "allowed_dispositions": ["STANDARD_ONLY", "OVERLAY_REQUIRED"],
        "proof_owner": "Project-Helianthus/helianthus-modbusreg",
    }, "M3-03 transport-neutral boundary changed")
    m3 = issue_map["FMV3-M3-03"]
    _require(m3["repo"] == "Project-Helianthus/helianthus-modbusreg", "M3-03 repository is invalid")
    _require(m3["depends_on"] == ["FMV3-M3-02"], "M3-03 dependency is invalid")
    title = m3["title"].lower()
    _require("transport-neutral" in title and "read-only" in title, "M3-03 title lost its boundary")

    _validate_mirrors(plan_dir, milestones, issues)
    return {"issues": len(issues), "milestones": len(milestones), "contracts": len(contracts)}


def main(argv: list[str]) -> int:
    plan_dir = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent
    try:
        counts = validate_plan(plan_dir)
    except (OSError, ValidationError) as exc:
        print(f"FMV3 plan invalid: {exc}", file=sys.stderr)
        return 1
    print(
        "FMV3 plan valid: "
        f"{counts['issues']} issues, {counts['milestones']} milestones, "
        f"{counts['contracts']} contracts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
