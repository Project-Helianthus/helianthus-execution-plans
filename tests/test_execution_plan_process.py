from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MSP = ROOT / "multi-runtime-semantic-platform.locked"


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
        plan = yaml.safe_load((MSP / "plan.yaml").read_text(encoding="utf-8"))
        self.assertEqual("guidance_only", plan["process_model"]["authority"])
        self.assertEqual("none", plan["process_model"]["post_merge_effects"])
        self.assertEqual("guidance_only", plan["successor_unlocks"])

    def test_msp_dependency_map_is_closed_and_acyclic(self) -> None:
        matrix = yaml.safe_load((MSP / "92-m0-issue-matrix.yaml").read_text(encoding="utf-8"))
        rows = matrix["issues"]
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(len(rows), len(by_id))
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


if __name__ == "__main__":
    unittest.main()
