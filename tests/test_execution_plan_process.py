from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MSP = ROOT / "multi-runtime-semantic-platform.locked"
MSP_GRAPH_GOLDEN = ROOT / "tests/golden/msp-dependency-graph.yaml"


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_mapping,
)


def load_unique_yaml(path: Path) -> object:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)


class ExecutionPlanProcessTests(unittest.TestCase):
    def test_retired_authorization_runtimes_are_absent(self) -> None:
        retired = (
            "scripts/aggregate_completion_token.py",
            "scripts/validate_ad_docs_02.py",
            "scripts/validate_msp_r00_l_ledger.py",
            "multi-runtime-semantic-platform.locked/106-ad-docs-02-integrity.json",
            "multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md",
            "multi-runtime-semantic-platform.locked/108-msp-docs-e2r-aggregate-architecture-review.json",
            "multi-runtime-semantic-platform.locked/109-msp-docs-e2r-aggregate-process-attestation.json",
        )
        self.assertEqual([], [path for path in retired if (ROOT / path).exists()])

    def test_msp_plan_declares_guidance_only_process(self) -> None:
        plan = load_unique_yaml(MSP / "plan.yaml")
        self.assertEqual("guidance_only", plan["process_model"]["authority"])
        self.assertEqual("none", plan["process_model"]["post_merge_effects"])
        self.assertNotIn("initial_ready_set", plan)
        self.assertNotIn("successor_unlocks", plan)
        self.assertNotIn("successor_unlock_condition", plan)

    def test_msp_dependency_map_is_closed_and_acyclic(self) -> None:
        matrix = load_unique_yaml(MSP / "92-m0-issue-matrix.yaml")
        rows = matrix["issues"]
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(len(rows), len(by_id))
        graph = [
            {"id": row["id"], "depends_on": row.get("depends_on", [])}
            for row in rows
        ]
        golden = load_unique_yaml(MSP_GRAPH_GOLDEN)
        self.assertEqual(75, len(graph))
        self.assertEqual(101, sum(len(row["depends_on"]) for row in graph))
        self.assertEqual(golden, graph)
        for row in rows:
            self.assertNotIn("requires_completion_tokens", row)
            self.assertTrue(set(row.get("depends_on", ())).issubset(by_id))

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(issue_id: str) -> None:
            if issue_id in visiting:
                self.fail(f"dependency cycle at {issue_id}")
            if issue_id in visited:
                return
            visiting.add(issue_id)
            for dependency in by_id[issue_id].get("depends_on", ()):
                visit(dependency)
            visiting.remove(issue_id)
            visited.add(issue_id)

        for issue_id in by_id:
            visit(issue_id)

    def test_msp_loader_rejects_duplicate_dependency_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate YAML key: depends_on"):
            yaml.load(
                "- id: MSP-X\n  depends_on: []\n  depends_on: [MSP-Y]\n",
                Loader=UniqueKeyLoader,
            )

    def test_msp_has_no_operative_dispatch_or_authorization_surface(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(MSP.iterdir())
            if path.suffix in {".md", ".yaml"}
        )
        for forbidden in (
            "required_at_dispatch",
            "routing_contract:",
            "routing_policy:",
            "unlock_predicate:",
            "initial_ready_set:",
            "successor_unlocks:",
            "successor_unlock_condition:",
            "## Current Ready Row",
            "authoritative for LAB acceptance and current dispatch",
            "generated control projection above is authoritative",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
