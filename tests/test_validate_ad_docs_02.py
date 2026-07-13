from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "validate_ad_docs_02.py"
PLAN = ROOT / "multi-runtime-semantic-platform.locked"
spec = importlib.util.spec_from_file_location("validate_ad_docs_02", MODULE)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class AdDocs02ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = yaml.safe_load((PLAN / validator.MATRIX).read_text(encoding="utf-8"))
        self.integrity = json.loads((PLAN / validator.INTEGRITY).read_text(encoding="utf-8"))

    def rejects_matrix(self, document: dict) -> None:
        with self.assertRaises(validator.ValidationError):
            validator.validate_matrix(document)

    def rejects_integrity(self, document: dict) -> None:
        with self.assertRaises(validator.ValidationError):
            validator.validate_integrity(document)

    def row(self, document: dict, row_id: str) -> dict:
        return next(row for row in document["issues"] if row["id"] == row_id)

    def test_accepts_live_typed_contract(self) -> None:
        validator.validate_matrix(self.matrix)
        validator.validate_integrity(self.integrity)

    def test_rejects_self_cycle(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2R-PLATFORM")["requires_completion_tokens"] = ["MSP-DOCS-E2R-PLATFORM"]
        self.rejects_matrix(document)

    def test_rejects_active_forbidden_tier_ultra(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2")["routing_contract"]["forbidden_tier"] = "ultra"
        self.rejects_matrix(document)

    def test_rejects_direct_e2_to_clean(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-CLEAN")["requires_completion_tokens"] = ["MSP-DOCS-E2"]
        self.rejects_matrix(document)

    def test_rejects_missing_required_serial_edge(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2R-PUBLISH")["requires_completion_tokens"] = []
        self.rejects_matrix(document)

    def test_rejects_unknown_completion_token(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2R-PLATFORM")["requires_completion_tokens"] = ["UNKNOWN"]
        self.rejects_matrix(document)

    def test_rejects_model_lane(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2")["model_lane"] = "historical-only"
        self.rejects_matrix(document)

    def test_rejects_exact_id_drift(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-09D")["id"] = "MSP-09X"
        self.rejects_matrix(document)

    def test_rejects_duplicate_integrity_key(self) -> None:
        raw = (PLAN / validator.INTEGRITY).read_text(encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            json.loads(raw[:-2] + ',"schema_version":2}', object_pairs_hook=validator._json_object)

    def test_rejects_token_root_drift(self) -> None:
        document = copy.deepcopy(self.integrity)
        document["completion_token_roots"] = document["completion_token_roots"][:1]
        self.rejects_integrity(document)

    def test_rejects_token_replay_or_drift_waiver(self) -> None:
        for field in ("replay_rejected", "drift_rejected"):
            with self.subTest(field=field):
                document = copy.deepcopy(self.integrity)
                document["token_envelope"][field] = False
                self.rejects_integrity(document)

    def test_rejects_readiness_or_cleanup_drift(self) -> None:
        document = copy.deepcopy(self.integrity)
        document["readiness_categories"] = ["selected_batch"]
        self.rejects_integrity(document)
        document = copy.deepcopy(self.integrity)
        document["candidate_cleanup"]["fail_closed"] = False
        self.rejects_integrity(document)

    def test_accepts_declared_mutable_path(self) -> None:
        present = mock.Mock(returncode=0)
        completed = mock.Mock(stdout="multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, completed]):
            validator.validate_changed_paths(ROOT)

    def test_rejects_nested_protected_issue_path(self) -> None:
        present = mock.Mock(returncode=0)
        completed = mock.Mock(stdout="multi-runtime-semantic-platform.locked/issues/MSP-00B-model-routing.md\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, completed]):
            with self.assertRaises(validator.ValidationError):
                validator.validate_changed_paths(ROOT)


if __name__ == "__main__":
    unittest.main()
