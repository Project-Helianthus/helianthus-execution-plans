from __future__ import annotations

import ast
import copy
import importlib.util
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "fronius-modbus-multivendor-v3-w29-26.implementing"
VALIDATOR_PATH = PLAN_DIR / "validate_plan.py"
SPEC = importlib.util.spec_from_file_location("fronius_plan_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

ACCEPTED_ISSUE_GRAPH = tuple(
    (
        cells[0],
        cells[1],
        cells[2],
        tuple(cells[3].split(",")) if cells[3] else (),
    )
    for cells in (
        line.split("|")
        for line in """
FMV3-M0-01|M0|Project-Helianthus/.github|
FMV3-M0-02|M0|Project-Helianthus/helianthus-modbus|FMV3-M0-01
FMV3-M0-03|M0|Project-Helianthus/helianthus-modbusreg|FMV3-M0-01
FMV3-M0-04|M0|Project-Helianthus/.github|FMV3-M0-01
FMV3-M0-05|M0|Project-Helianthus/helianthus-eebus-binding-private|FMV3-M0-04
FMV3-M0-07|M0|Project-Helianthus/helianthus-matter-binding-private|FMV3-M0-04
FMV3-M0-06|M0|Project-Helianthus/helianthus-docs-ebus|
FMV3-M1-00|M1|Project-Helianthus/helianthus-docs-ebus|FMV3-M0-02,FMV3-M0-06
FMV3-M1-01|M1|Project-Helianthus/helianthus-modbus|FMV3-M0-02,FMV3-M1-00
FMV3-M1-02|M1|Project-Helianthus/helianthus-modbus|FMV3-M1-01
FMV3-M1-03|M1|Project-Helianthus/helianthus-modbus|FMV3-M1-02
FMV3-M1-04|M1|Project-Helianthus/helianthus-modbus|FMV3-M1-02,FMV3-M1-03
FMV3-M1-05|M1|Project-Helianthus/helianthus-docs-ebus|FMV3-M1-04
FMV3-M1-06|M1|Project-Helianthus/helianthus-modbus|FMV3-M1-04,FMV3-M1-05
FMV3-M2-01|M2|Project-Helianthus/helianthus-modbusreg|FMV3-M0-03,FMV3-M1-00,FMV3-M1-01,FMV3-M1-06
FMV3-M2-02|M2|Project-Helianthus/helianthus-modbusreg|FMV3-M1-00,FMV3-M2-01
FMV3-M2-03|M2|Project-Helianthus/helianthus-modbusreg|FMV3-M1-00,FMV3-M2-01,FMV3-M2-02
FMV3-M3-01|M3|Project-Helianthus/helianthus-docs-ebus|FMV3-M0-06,FMV3-M2-01
FMV3-M3-02|M3|Project-Helianthus/helianthus-modbusreg|FMV3-M1-02,FMV3-M2-03,FMV3-M3-01
FMV3-M3-03|M3|Project-Helianthus/helianthus-modbusreg|FMV3-M3-02
FMV3-M4-01|M4|Project-Helianthus/helianthus-ebusgateway|FMV3-M0-06,FMV3-M1-02,FMV3-M3-03
FMV3-M4-02|M4|Project-Helianthus/helianthus-ebusgateway|FMV3-M4-01
FMV3-M4-03|M4|Project-Helianthus/helianthus-ha-addon|FMV3-M4-01
FMV3-M4-04|M4|Project-Helianthus/helianthus-ebusgateway|FMV3-M4-02,FMV3-M4-03
FMV3-M4-05|M4|Project-Helianthus/helianthus-docs-ebus|FMV3-M3-01,FMV3-M4-04
FMV3-M5-01|M5|Project-Helianthus/helianthus-ebusreg|FMV3-M5-02
FMV3-M5-02|M5|Project-Helianthus/helianthus-docs-ebus|FMV3-M4-05
FMV3-M5-03|M5|Project-Helianthus/helianthus-execution-plans|FMV3-M5-04
FMV3-M5-04|M5|Project-Helianthus/helianthus-ebusgateway|FMV3-M5-01,FMV3-M5-02
FMV3-M5-09|M5|Project-Helianthus/helianthus-docs-ebus|FMV3-M5-03
FMV3-M5-05|M5|Project-Helianthus/helianthus-ebusgateway|FMV3-M5-09
FMV3-M5-06|M5|Project-Helianthus/helianthus-ebusgateway|FMV3-M5-05
FMV3-M5-07|M5|Project-Helianthus/helianthus-ha-integration|FMV3-M5-06
FMV3-M5-08|M5|Project-Helianthus/helianthus-ha-addon|FMV3-M5-06,FMV3-M5-07
FMV3-M6-00|M6|Project-Helianthus/helianthus-docs-ebus|FMV3-M5-08
FMV3-M6-01|M6|Project-Helianthus/helianthus-eebus-binding-private|FMV3-M0-05,FMV3-M6-00
FMV3-M6-02|M6|Project-Helianthus/helianthus-eebus-binding-private|FMV3-M6-01
FMV3-M6-03|M6|Project-Helianthus/helianthus-docs-ebus|FMV3-M6-02
FMV3-M7-01|M7|Project-Helianthus/helianthus-docs-ebus|FMV3-M0-06,FMV3-M1-04,FMV3-M2-03,FMV3-M5-09
FMV3-M7-02|M7|Project-Helianthus/helianthus-modbusreg|FMV3-M1-04,FMV3-M2-03,FMV3-M3-03,FMV3-M7-01
FMV3-M7-03|M7|Project-Helianthus/helianthus-modbusreg|FMV3-M7-02
FMV3-M7-04|M7|Project-Helianthus/helianthus-modbusreg|FMV3-M7-03
FMV3-M7-05|M7|Project-Helianthus/helianthus-modbusreg|FMV3-M7-04
FMV3-M8-00|M8|Project-Helianthus/helianthus-docs-ebus|FMV3-M5-08
FMV3-M8-01|M8|Project-Helianthus/helianthus-matter-binding-private|FMV3-M0-07,FMV3-M8-00
FMV3-M8-02|M8|Project-Helianthus/helianthus-matter-binding-private|FMV3-M8-01
""".strip().splitlines()
    )
)


class FroniusPlanStructureTests(unittest.TestCase):
    def copy_plan(self, root: Path) -> Path:
        target = root / PLAN_DIR.name
        shutil.copytree(PLAN_DIR, target)
        return target

    def document(self, plan_dir: Path) -> dict[str, Any]:
        return yaml.safe_load((plan_dir / "plan.yaml").read_text(encoding="utf-8"))

    def write_document(self, plan_dir: Path, document: dict[str, Any]) -> None:
        (plan_dir / "plan.yaml").write_text(
            yaml.safe_dump(document, sort_keys=False),
            encoding="utf-8",
        )

    def assert_document_rejected(
        self,
        mutate: Callable[[dict[str, Any]], None],
        message: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            document = self.document(plan_dir)
            mutate(document)
            self.write_document(plan_dir, document)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, message):
                VALIDATOR.validate_plan(plan_dir)

    def issue(self, document: dict[str, Any], issue_id: str) -> dict[str, Any]:
        return next(row for row in document["issues"] if row["id"] == issue_id)

    def issue_graph(self, document: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
        return tuple(
            (
                row["id"],
                row["milestone"],
                row["repo"],
                tuple(row["depends_on"]),
            )
            for row in document["issues"]
        )

    def assert_issue_graph_locked(self, document: dict[str, Any]) -> None:
        self.assertEqual(
            self.issue_graph(document),
            ACCEPTED_ISSUE_GRAPH,
            "accepted issue graph changed",
        )

    def test_accepts_current_plan(self) -> None:
        self.assertEqual(
            VALIDATOR.validate_plan(PLAN_DIR),
            {"issues": 46, "milestones": 9, "contracts": 7},
        )

    def test_exact_accepted_issue_graph_is_locked(self) -> None:
        self.assert_issue_graph_locked(self.document(PLAN_DIR))

    def test_graph_lock_rejects_owner_drift(self) -> None:
        document = self.document(PLAN_DIR)
        self.issue(document, "FMV3-M4-03")["repo"] = "Project-Helianthus/helianthus-ebusgateway"
        with self.assertRaisesRegex(AssertionError, "accepted issue graph changed"):
            self.assert_issue_graph_locked(document)

    def test_graph_lock_rejects_required_edge_removal(self) -> None:
        document = self.document(PLAN_DIR)
        self.issue(document, "FMV3-M1-04")["depends_on"].remove("FMV3-M1-03")
        with self.assertRaisesRegex(AssertionError, "accepted issue graph changed"):
            self.assert_issue_graph_locked(document)

    def test_graph_lock_rejects_evidence_lane_bypass(self) -> None:
        document = self.document(PLAN_DIR)
        self.issue(document, "FMV3-M5-02")["depends_on"] = ["FMV3-M4-04"]
        with self.assertRaisesRegex(AssertionError, "accepted issue graph changed"):
            self.assert_issue_graph_locked(document)

    def test_rejects_plan_local_outcome_release_authority(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["outcome_gates"] = [{"release_outcome": "GO"}]

        self.assert_document_rejected(mutate, "plan.yaml root fields are invalid")

    def test_active_plan_has_no_outcome_release_language(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(PLAN_DIR.iterdir())
            if path.suffix in {".md", ".yaml"}
        )
        for forbidden in (
            "only `GO` satisfies",
            "Only `GO` releases",
            "releases its declared",
            "releases no M5 successor",
            "releases M7-04",
            "release_outcome:",
            "gated_successors:",
            "outcome_gates:",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_gateway_transport_and_raw_mcp_are_doc_gated(self) -> None:
        document = self.document(PLAN_DIR)
        by_id = {issue["id"]: issue for issue in document["issues"]}
        for issue_id in ("FMV3-M4-01", "FMV3-M4-02"):
            self.assertIn("doc_gate", by_id[issue_id]["gates"])
        self.assertIn("FMV3-M0-06", by_id["FMV3-M4-01"]["depends_on"])

    def test_rejects_missing_issue_acceptance(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M2-03")["acceptance"] = ""

        self.assert_document_rejected(mutate, "acceptance must be nonempty")

    def test_rejects_missing_issue_gates(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M2-03")["gates"] = []

        self.assert_document_rejected(mutate, "gates must be a nonempty list")

    def test_private_bootstraps_require_ci(self) -> None:
        document = self.document(PLAN_DIR)
        for issue_id in ("FMV3-M0-05", "FMV3-M0-07"):
            self.assertIn("CI", self.issue(document, issue_id)["gates"])

    def test_rejects_private_bootstrap_without_ci(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M0-05")["gates"].remove("CI")

        self.assert_document_rejected(mutate, "private bootstrap must retain its CI gate")

    def test_private_repository_creation_requires_operator_confirmation(self) -> None:
        document = self.document(PLAN_DIR)
        issue = self.issue(document, "FMV3-M0-04")
        self.assertIn("operator_confirmation", issue["gates"])
        self.assertIn("Only after explicit operator confirmation", issue["acceptance"])

    def test_rejects_private_repository_creation_without_confirmation(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            issue = self.issue(document, "FMV3-M0-04")
            issue["gates"].remove("operator_confirmation")

        self.assert_document_rejected(mutate, "requires explicit operator confirmation")

    def test_rejects_status_hard_stop_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            status = plan_dir / "99-status.md"
            status.write_text(
                status.read_text(encoding="utf-8").replace(
                    "- gateway work: blocked", "- gateway work: ready", 1
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "status does not mirror"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_canonical_hard_stop_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            canonical = plan_dir / "00-canonical.md"
            canonical.write_text(
                canonical.read_text(encoding="utf-8").replace(
                    "`FMV3-M4-01`. `FMV3-M4-01` and every gateway issue remain blocked.",
                    "`FMV3-M4-02`. `FMV3-M4-02` and every gateway issue remain blocked.",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "canonical prose does not mirror"):
                VALIDATOR.validate_plan(plan_dir)

    def test_matter_pv_slice_is_m6_independent_and_contract_bound(self) -> None:
        document = self.document(PLAN_DIR)
        issues = {row["id"]: row for row in document["issues"]}
        ancestors = VALIDATOR._ancestors("FMV3-M8-02", issues)
        self.assertFalse(any(issue_id.startswith("FMV3-M6-") for issue_id in ancestors))
        acceptance = issues["FMV3-M8-02"]["acceptance"]
        self.assertIn("PUBLIC_GRAPHQL_M2M_V1", acceptance)
        self.assertIn("sole ingress", acceptance)
        self.assertIn("cannot change or bypass the locked PV contract", acceptance)

    def test_rejects_matter_pv_slice_without_contract_boundary(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M8-02")["acceptance"] = (
                "Conformance tests preserve Matter PV values."
            )

        self.assert_document_rejected(
            mutate,
            "must retain sole public ingress and locked PV contract acceptance",
        )

    def test_rejects_missing_issue_rollback(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M2-03")["rollback"] = ""

        self.assert_document_rejected(mutate, "rollback must be nonempty")

    def test_validation_is_read_only(self) -> None:
        before = {
            path.relative_to(PLAN_DIR): path.read_bytes()
            for path in PLAN_DIR.rglob("*")
            if path.is_file()
        }
        VALIDATOR.validate_plan(PLAN_DIR)
        after = {
            path.relative_to(PLAN_DIR): path.read_bytes()
            for path in PLAN_DIR.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_rejects_duplicate_yaml_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            plan_path = plan_dir / "plan.yaml"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8") + "state: implementing\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "duplicate YAML key"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_non_mapping_yaml_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            (plan_dir / "plan.yaml").write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "root must be a mapping"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_missing_required_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            (plan_dir / "00-canonical.md").unlink()
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "missing required files"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_templates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            (plan_dir / "templates").mkdir()
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "templates directory"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_extra_root_field(self) -> None:
        self.assert_document_rejected(
            lambda document: document.update({"runtime_gate": {}}),
            "root fields",
        )

    def test_rejects_repository_set_drift(self) -> None:
        self.assert_document_rejected(
            lambda document: document["repositories"].pop("Project-Helianthus/.github"),
            "repository set",
        )

    def test_rejects_unknown_issue_repository(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["repo"] = "Project-Helianthus/unknown"

        self.assert_document_rejected(mutate, "unknown repository")

    def test_rejects_duplicate_contract_id(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["contracts"].append(copy.deepcopy(document["contracts"][0]))

        self.assert_document_rejected(mutate, "contract IDs must be unique")

    def test_rejects_contract_version_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["contracts"][0]["version"] = 2

        self.assert_document_rejected(mutate, "contract IDs or versions changed")

    def test_rejects_duplicate_milestone_id(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["milestones"][1]["id"] = "M0"

        self.assert_document_rejected(mutate, "milestone IDs must be unique")

    def test_rejects_milestone_set_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["milestones"][-1]["id"] = "M9"

        self.assert_document_rejected(mutate, "milestones M0 through M8")

    def test_rejects_duplicate_issue_id(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["issues"][1]["id"] = document["issues"][0]["id"]

        self.assert_document_rejected(mutate, "issue IDs must be unique")

    def test_rejects_retained_issue_set_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["issues"][-1]["id"] = "FMV3-M8-03"

        self.assert_document_rejected(mutate, "retained 46 issue IDs changed")

    def test_rejects_unknown_milestone_reference(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["milestone"] = "M9"

        self.assert_document_rejected(mutate, "unknown milestone")

    def test_rejects_issue_milestone_mirror_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["milestone"] = "M2"

        self.assert_document_rejected(mutate, "milestone mirror")

    def test_rejects_unknown_dependency(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["depends_on"] = ["FMV3-M9-99"]

        self.assert_document_rejected(mutate, "unknown dependency")

    def test_rejects_duplicate_dependency(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["depends_on"] *= 2

        self.assert_document_rejected(mutate, "duplicate dependencies")

    def test_rejects_self_dependency(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["depends_on"] = ["FMV3-M3-03"]

        self.assert_document_rejected(mutate, "cannot depend on itself")

    def test_rejects_dependency_cycle(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M0-01")["depends_on"] = ["FMV3-M3-03"]

        self.assert_document_rejected(mutate, "must be acyclic")

    def test_rejects_missing_ordering_declaration(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["ordering"].pop()

        self.assert_document_rejected(mutate, "ordering declarations are incomplete")

    def test_rejects_ordering_sequence_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["ordering"][0]["sequence"].pop()

        self.assert_document_rejected(mutate, "ordering declarations changed")

    def test_rejects_ordering_not_represented_in_dag(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M6-02")["depends_on"] = []

        self.assert_document_rejected(mutate, "eebus_binding ordering is not present")

    def test_rejects_issue_mirror_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            path = plan_dir / "90-issue-map.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "| FMV3-M0-01 | M0 | Project-Helianthus/.github | - |",
                    "| FMV3-M0-01 | M0 | Project-Helianthus/helianthus-modbus | - |",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "issue map does not mirror"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_milestone_mirror_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = self.copy_plan(Path(temp))
            path = plan_dir / "91-milestone-map.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "| M3 | Minimal SunSpec family and Fronius applicability |",
                    "| M3 | Changed title |",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "milestone map does not mirror"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_hard_stop_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["hard_stop"]["before_issue"] = "FMV3-M4-02"

        self.assert_document_rejected(mutate, "hard stop must remain")

    def test_rejects_gateway_unblocked_state(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["hard_stop"]["gateway_work"] = "ready"

        self.assert_document_rejected(mutate, "hard stop must remain")

    def test_rejects_later_issue_bypassing_hard_stop(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M4-03")["depends_on"] = []

        self.assert_document_rejected(mutate, "bypasses the hard stop")

    def test_rejects_transport_boundary_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["transport_neutral_boundary"]["production_scope"] = "TCP profile logic"

        self.assert_document_rejected(mutate, "transport-neutral boundary changed")

    def test_rejects_m3_03_repository_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["repo"] = "Project-Helianthus/helianthus-modbus"

        self.assert_document_rejected(mutate, "M3-03 repository")

    def test_rejects_m3_03_dependency_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["depends_on"].append("FMV3-M2-03")

        self.assert_document_rejected(mutate, "M3-03 dependency")

    def test_rejects_m3_03_title_losing_boundary(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            self.issue(document, "FMV3-M3-03")["title"] = "Implement a Fronius TCP overlay"

        self.assert_document_rejected(mutate, "title lost its boundary")

    def test_rejects_blocking_severity_policy_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["review_policy"]["blocking_severities"] = ["P0", "P1"]

        self.assert_document_rejected(mutate, "review policy changed")

    def test_rejects_merge_verdict_policy_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["review_policy"]["merge_verdict"] = "APPROVED"

        self.assert_document_rejected(mutate, "review policy changed")

    def test_rejects_p2_evidence_policy_drift(self) -> None:
        def mutate(document: dict[str, Any]) -> None:
            document["review_policy"]["p2_evidence"].pop()

        self.assert_document_rejected(mutate, "review policy changed")

    def test_validator_uses_only_local_read_only_modules(self) -> None:
        tree = ast.parse(VALIDATOR_PATH.read_text(encoding="utf-8"))
        imported = {
            node.names[0].name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
        }
        imported.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertTrue(imported.isdisjoint({"subprocess", "socket", "urllib", "http", "requests"}))

    def test_no_maximum_review_round_wording_remains(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in PLAN_DIR.rglob("*")
            if path.is_file() and path.suffix in {".md", ".yaml", ".py"}
        )
        self.assertIsNone(
            re.search(r"max(?:imum)?[_ -]+(?:normal[_ -]+)?(?:review[_ -]+)?rounds?", text, re.IGNORECASE)
        )


if __name__ == "__main__":
    unittest.main()
