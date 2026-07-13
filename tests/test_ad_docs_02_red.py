from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "multi-runtime-semantic-platform.locked"
MATRIX_PATH = PLAN_DIR / "92-m0-issue-matrix.yaml"
E2_MERGES = {
    "62e4c2f2022c22f5129db923079268aafdc5617b",
    "6476e39811677041ba11911457baab4c602ac557",
}


class AdDocs02RedTests(unittest.TestCase):
    """Desired AD-DOCS-02 behavior; absent amendment surfaces are intentional RED."""

    def _one_artifact(self, prefix: str) -> Path:
        matches = sorted(PLAN_DIR.glob(f"{prefix}-*"))
        if not matches:
            self.fail(f"AD-DOCS-02 implementation missing: expected {prefix}-* artifact")
        self.assertEqual(matches[1:], [], f"AD-DOCS-02 must have one {prefix}-* artifact")
        return matches[0]

    def _surfaces(self) -> tuple[dict[str, object], str, str]:
        amendment = self._one_artifact("105")
        contract = self._one_artifact("106")
        audit = self._one_artifact("107")
        self.assertTrue(amendment.is_file(), "105-* must be an AD-DOCS-02 amendment file")
        self.assertTrue(contract.is_file(), "106-* must be the publication-contract v2 surface")
        self.assertTrue(audit.is_file(), "107-* must be the live topology audit")
        data = yaml.safe_load(contract.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict, "publication-contract v2 must be a YAML mapping")
        return data, amendment.read_text(encoding="utf-8"), audit.read_text(encoding="utf-8")

    def _rows(self) -> dict[str, dict[str, object]]:
        data = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)
        rows = data.get("issues")
        self.assertIsInstance(rows, list)
        self.assertTrue(all(isinstance(row, dict) for row in rows))
        return {str(row["id"]): row for row in rows}

    def test_requires_append_only_ad_docs_02_artifacts(self) -> None:
        contract, amendment, audit = self._surfaces()
        self.assertEqual(contract.get("schema_version"), 2)
        self.assertIn("AD-DOCS-02", amendment)
        self.assertIn("AD-DOCS-02", audit)

    def test_requires_exact_46_row_acyclic_serial_dag(self) -> None:
        self._surfaces()
        rows = self._rows()
        self.assertEqual(len(rows), 46)
        required = {
            "MSP-DOCS-E2R-PLATFORM",
            "MSP-DOCS-E2R-PUBLISH",
            "MSP-DOCS-E2R-AGGREGATE",
            "MSP-DOCS-CLEAN",
        }
        self.assertTrue(required.issubset(rows))
        self.assertEqual(
            rows["MSP-DOCS-E2R-PUBLISH"].get("requires_completion_tokens"),
            ["MSP-DOCS-E2R-PLATFORM"],
        )
        self.assertEqual(
            rows["MSP-DOCS-E2R-AGGREGATE"].get("requires_completion_tokens"),
            ["MSP-DOCS-E2R-PUBLISH"],
        )
        self.assertEqual(
            rows["MSP-DOCS-CLEAN"].get("requires_completion_tokens"),
            ["MSP-DOCS-E2R-AGGREGATE"],
        )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(row_id: str) -> None:
            self.assertNotIn(row_id, visiting, f"cycle at {row_id}")
            if row_id in visited:
                return
            visiting.add(row_id)
            for predecessor in rows[row_id].get("requires_completion_tokens", []):
                self.assertIn(predecessor, rows)
                visit(predecessor)
            visiting.remove(row_id)
            visited.add(row_id)

        for row_id in rows:
            visit(row_id)

    def test_requires_e2_composite_evidence_and_token_roots(self) -> None:
        contract, _, _ = self._surfaces()
        roots = set(contract.get("e2_merge_roots", []))
        self.assertEqual(roots, E2_MERGES)
        self.assertEqual(contract.get("completion_token_roots"), sorted(E2_MERGES))
        evidence = contract.get("evidence_inputs")
        self.assertIsInstance(evidence, dict)
        self.assertEqual(set(evidence.get("MSP-R00", [])), {"Project-Helianthus/helianthus-eebusreg#14"})
        self.assertEqual(set(evidence.get("MSP-03D-G01", [])), {"MSP-03D-G01"})

    def test_separates_completion_tokens_from_evidence_inputs(self) -> None:
        _, _, audit = self._surfaces()
        rows = self._rows()
        for row_id, row in rows.items():
            self.assertNotIn("predecessors", row, f"{row_id} must not use generic predecessors")
            self.assertNotIn("model_lane", row, f"{row_id} must not retain model_lane")
            self.assertFalse(
                set(row.get("requires_completion_tokens", []))
                & {"MSP-R00", "MSP-03D-G01"},
                f"{row_id} must not accept evidence-only work as a completion token",
            )
        self.assertIn("evidence_inputs", audit)
        self.assertIn("requires_completion_tokens", audit)

    def test_replay_and_identity_rejection_cases_are_documented(self) -> None:
        _, amendment, _ = self._surfaces()
        for rejection in (
            "token replay",
            "wrong repository",
            "wrong base",
            "wrong head",
            "wrong merge",
            "wrong tree",
            "moving ref",
            "base drift",
        ):
            self.assertIn(rejection, amendment.lower())

    def test_requires_routing_contract_or_observed_routing_evidence_exclusively(self) -> None:
        self._surfaces()
        for row_id, row in self._rows().items():
            has_contract = "routing_contract" in row
            has_evidence = "routing_evidence" in row
            self.assertNotEqual(has_contract, has_evidence, f"{row_id} routing surface is ambiguous")
            self.assertNotIn("model_lane", row)

    def test_rejects_ultra_from_routing_contracts(self) -> None:
        contract, _, _ = self._surfaces()
        encoded = json.dumps(contract).lower()
        self.assertIn('"forbidden_tier": "Ultra"', json.dumps(contract))
        self.assertIn("policy_digest", encoded)
        self.assertIn("resolver", encoded)

    def test_distinguishes_snapshot_logical_dispatch_and_selected_readiness(self) -> None:
        _, _, audit = self._surfaces()
        for label in (
            "readiness snapshot",
            "logical-ready",
            "dispatchable",
            "selected-batch",
        ):
            self.assertIn(label, audit.lower())

    def test_distinguishes_planned_expiry_from_candidate_cleanup(self) -> None:
        contract, _, _ = self._surfaces()
        expiry = contract.get("planned_expiry")
        cleanup = contract.get("candidate_cleanup")
        self.assertIsInstance(expiry, dict)
        self.assertIsInstance(cleanup, dict)
        self.assertNotEqual(expiry, cleanup)
        self.assertTrue(cleanup.get("fail_closed"))
        self.assertEqual(cleanup.get("post_consumption_rollback"), "forward_fix_only")

    def test_requires_publication_contract_v2_schema_floor_and_entry_kinds(self) -> None:
        contract, _, _ = self._surfaces()
        self.assertEqual(contract.get("schema_version"), 2)
        self.assertEqual(
            set(contract.get("entry_kinds", [])),
            {"eligibility", "exact_membership", "channel_registry", "absence_constraint"},
        )
        self.assertIn("absence_constraints", contract)
        self.assertIn("exact_memberships", contract)
        self.assertIn("channel_registry", contract)

    def test_requires_exact_publication_memberships_and_absence_constraints(self) -> None:
        contract, _, _ = self._surfaces()
        memberships = contract.get("exact_memberships")
        absence = contract.get("absence_constraints")
        self.assertIsInstance(memberships, dict)
        self.assertIsInstance(absence, list)
        self.assertTrue(memberships)
        self.assertTrue(absence)
        self.assertIn("hermetic_git_object_evidence", contract)

    def test_requires_protected_history_anchor_and_mutable_allowlist(self) -> None:
        _, amendment, _ = self._surfaces()
        self.assertIn("f25d9ac7d3f25f0f45821cdff27ff968a0ef5cfb", amendment)
        self.assertIn("byte-for-byte", amendment)
        self.assertIn("mutable allowlist", amendment)
        self.assertIn("100-topology-audit.md", amendment)

    def test_requires_legacy_audit_anchor_binding_and_live_107_audit(self) -> None:
        _, _, audit = self._surfaces()
        historical = PLAN_DIR / "100-topology-audit.md"
        self.assertTrue(historical.is_file())
        self.assertIn("anchor", audit.lower())
        self.assertIn("107", audit)
        self.assertEqual(
            hashlib.sha256(historical.read_bytes()).hexdigest(),
            "b84c74551e839a3869a775c2f94c1f0121f2cfe477fe58a076e53bd57568f4d2",
        )

    def test_retargeted_ledger_validator_preserves_unittest_discovery(self) -> None:
        self._surfaces()
        validator = ROOT / "scripts" / "validate_msp_r00_l_ledger.py"
        source = validator.read_text(encoding="utf-8")
        self.assertIn("100-topology-audit.md", source)
        self.assertIn("107", source)
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
        self.assertGreater(suite.countTestCases(), 40)


if __name__ == "__main__":
    unittest.main()
