from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_msp_r00_l_ledger.py"
LEDGER_PATH = (
    ROOT
    / "multi-runtime-semantic-platform.locked"
    / "104-msp-r00-l-public-redacted-ledger.json"
)

spec = importlib.util.spec_from_file_location("validate_msp_r00_l_ledger", MODULE_PATH)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class MspR00LLedgerValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    def assert_rejects(self, mutated: dict) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
            json.dump(mutated, handle)
            handle.flush()
            with self.assertRaises(validator.ValidationError):
                validator.validate_ledger(Path(handle.name))

    def test_accepts_public_redacted_ledger(self) -> None:
        validator.validate_ledger(LEDGER_PATH)

    def test_rejects_extra_root_key(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["unexpected"] = "redacted"
        self.assert_rejects(mutated)

    def test_rejects_non_v4_uuid(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["opaque_public_id"] = "845fdc27-ae1c-1989-9cd5-4139f989410d"
        self.assert_rejects(mutated)

    def test_rejects_wrong_issue_ref(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["clean_main_issue_ref"] = "Project-Helianthus/helianthus-eebusreg#15"
        self.assert_rejects(mutated)

    def test_rejects_unknown_enum(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["disposition"] = "accepted"
        self.assert_rejects(mutated)

    def test_rejects_forbidden_extra_key(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["local_hash"] = "redacted"
        self.assert_rejects(mutated)

    def test_rejects_forbidden_value_pattern(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["redaction_categories"]["origin_locator"] = "2026-01-01"
        self.assert_rejects(mutated)


if __name__ == "__main__":
    unittest.main()
