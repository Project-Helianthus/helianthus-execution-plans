#!/usr/bin/env python3
"""Validate only the structural contract of this locked execution-plan package."""
from __future__ import annotations
import hashlib
import re
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
    slug title state lock_authorized source_discussion target_repos knowledge_repo canonical_file canonical_sha256
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
REQUIRED_PHASE_GATES = set("PG-REPOSITORY-CREATION PG-MODBUS-BOOT PG-MODBUS-DOC-GATE PG-MODBUSREG-BOOT PG-EEBUS-BOOT PG-MATTER-BOOT PG-RAW-FIRST PG-PV-DOC-GATE PG-SEMANTIC-LOCK PG-CONSUMER-PROMOTION PG-GRAPHQL-DOC-GATE PG-PUBLIC-ROLLOUT PG-EEBUS-DOC-GATE PG-MATTER-DOC-GATE PG-VENDOR-EXPANSION PG-READ-ONLY PG-RECOVERABLE-RELEASE".split())
EXPECTED_ISSUE_COUNT = 43
CONDITIONAL_GATE_IDS = {"CG-M4-LIVE-GO", "CG-M5-SEMANTIC-GO"}
M1_IMPLEMENTATION_IDS = {f"FMV3-M1-{number:02d}" for number in range(1, 5)}
M2_IMPLEMENTATION_IDS = {f"FMV3-M2-{number:02d}" for number in range(1, 4)}
COMPANION_IDS = M1_IMPLEMENTATION_IDS | M2_IMPLEMENTATION_IDS
CHUNKS = [f"{number}-{name}.md" for number, name in ((10, "architecture-and-repo-boundaries"), (11, "fronius-readonly-and-semantic-lock"), (12, "vendor-expansion-and-private-bindings"), (13, "roadmap-gates-and-risks"))]
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
    require(plan["state"] == "locked", "state must be locked")
    require(plan["lock_authorized"] is True, "lock_authorized must be true")
    require(plan["started_on"] == "2026-07-14", "started_on mismatch")
    require(plan["current_milestone"] == "M0", "current_milestone must remain M0")
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
        require(all(row[position] for position in range(4, 8)), f"issue-map missing acceptance/gate data: {issue_id}")
    require(all(gate_id in issue_map_text for gate_id in CONDITIONAL_GATE_IDS),
            "issue map missing conditional gate mirror")
    for issue_id in COMPANION_IDS:
        require("FMV3-M1-00" in issue_rows[issue_id][6], f"issue map companion metadata missing: {issue_id}")
    require(all(all(case in issue_rows[issue_id][5] for case in abnormal_results) for issue_id in ("FMV3-M1-00", "FMV3-M1-02", "FMV3-M1-03", "FMV3-M1-04")), "issue map abnormal-result mirror mismatch")
    require(all(all(term in issue_rows[issue_id][5] for term in ("full_transmit_success", "response_wait")) for issue_id in ("FMV3-M1-00", "FMV3-M1-02", "FMV3-M1-03", "FMV3-M1-04")) and all(row in issue_rows["FMV3-M1-04"][5] for row in recovery_matrix[5:7] + recovery_matrix[15:17]), "issue map full-transmit mirror mismatch")
    for docs_id, consumers in profile_companions.items():
        require(all(docs_id in issue_rows[consumer_id][6] for consumer_id in consumers), f"issue map {docs_id} companion mirror missing")
    require("FMV3-M5-09" in issue_rows["FMV3-M5-05"][6], "issue map GraphQL companion metadata missing")
    require(issue_rows["FMV3-M7-03"][6] == "CI, licensing, protocol_interop, hardware_conditional, doc_gate companion FMV3-M7-01, TDD_RED_IF_PROFILE_ADMITTED" and "already-merged M7-01" in issue_rows["FMV3-M7-03"][5], "issue map Growatt prepublication mismatch")
    require(all(term in issue_rows["FMV3-M6-02"][5] for term in ("live Fronius", "post-run-start", "same identity/value", "cannot GO")), "issue map myVaillant live evidence mismatch")
    milestone_map = (root / "91-milestone-map.md").read_text(encoding="utf-8")
    require(all(gate_id in milestone_map for gate_id in CONDITIONAL_GATE_IDS),
            "milestone map missing conditional gate mirror")
    require("FMV3-M5-09" in milestone_map and "43 issues" in issue_map_text and "repository mutex" in issue_map_text,
            "issue/milestone maps missing docs, mutex, or issue-count mirror")
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
    for category in REVIEW_SCOPE:
        require(category in review, f"review contract missing category: {category}")
    canonical_bytes = (root / "00-canonical.md").read_bytes()
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    require(plan["canonical_sha256"] == digest, "plan.yaml canonical_sha256 mismatch")
    for mirror_name in ("01-index.md", "99-status.md"):
        mirror = (root / mirror_name).read_text(encoding="utf-8")
        require(f"Canonical-SHA256: `{digest}`" in mirror, f"{mirror_name} canonical hash mirror mismatch")
    status = (root / "99-status.md").read_text(encoding="utf-8")
    for line in (
        "State: locked",
        "Current milestone: M0",
        f"Review epoch: {epoch['number']}",
        f"Review state: {epoch['state']}",
        f"Accepted adversarial rounds: {accepted_rounds}/5",
        f"Review target: {review_target}",
        "Lock authorized: yes, for plan publication only",
        "Implementation authorized: no",
        "Repository creation authorized: no",
        "Commit/push authorized: yes, for this plan package only",
    ):
        require(line in status, f"status mismatch: {line}")
    require(root.name == f"{plan['slug']}.locked", "directory suffix/state mismatch")
    validate_content_hygiene(root)
    return len(issues), len(milestones)
def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        issue_count, milestone_count = validate(root)
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {root.name}; {issue_count} issues; {milestone_count} milestones; locked consistent")
    return 0
if __name__ == "__main__": raise SystemExit(main())
