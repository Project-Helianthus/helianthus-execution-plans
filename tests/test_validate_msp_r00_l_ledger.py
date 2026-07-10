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

    def assert_raw_rejects(self, raw_json: str) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
            handle.write(raw_json)
            handle.flush()
            with self.assertRaises(validator.ValidationError):
                validator.validate_ledger(Path(handle.name))

    def valid_entry_json(self) -> str:
        return json.dumps(self.ledger["entries"][0], indent=6)

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

    def test_rejects_class_disposition_mismatch(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["disposition"] = "private_restricted"
        self.assert_rejects(mutated)

    def test_rejects_forbidden_extra_key(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["local_hash"] = "redacted"
        self.assert_rejects(mutated)

    def test_rejects_forbidden_value_pattern(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["redaction_categories"]["origin_locator"] = "2026-01-01"
        self.assert_rejects(mutated)

    def test_rejects_duplicate_root_key_before_hidden_value_is_overwritten(self) -> None:
        self.assert_raw_rejects(
            f"""{{
  "artifact_kind": "msp_r00_l_public_redacted_recovery_ledger",
  "entries": "commit",
  "entries": [
    {self.valid_entry_json()}
  ]
}}"""
        )

    def test_rejects_duplicate_entry_key_before_hidden_value_is_overwritten(self) -> None:
        entry = self.ledger["entries"][0]
        redaction = json.dumps(entry["redaction_categories"], indent=6)
        self.assert_raw_rejects(
            f"""{{
  "artifact_kind": "msp_r00_l_public_redacted_recovery_ledger",
  "entries": [
    {{
      "opaque_public_id": "{entry["opaque_public_id"]}",
      "clean_main_issue_ref": "{entry["clean_main_issue_ref"]}",
      "public_class": "commit",
      "public_class": "{entry["public_class"]}",
      "disposition": "{entry["disposition"]}",
      "redaction_categories": {redaction}
    }}
  ]
}}"""
        )

    def test_rejects_duplicate_nested_key_before_hidden_value_is_overwritten(self) -> None:
        entry = self.ledger["entries"][0]
        self.assert_raw_rejects(
            f"""{{
  "artifact_kind": "msp_r00_l_public_redacted_recovery_ledger",
  "entries": [
    {{
      "opaque_public_id": "{entry["opaque_public_id"]}",
      "clean_main_issue_ref": "{entry["clean_main_issue_ref"]}",
      "public_class": "{entry["public_class"]}",
      "disposition": "{entry["disposition"]}",
      "redaction_categories": {{
        "origin_locator": "commit",
        "origin_locator": "redacted",
        "runtime_identity": "redacted",
        "evidence_payload": "redacted",
        "integrity_preimage": "redacted",
        "quantity_observation": "redacted",
        "temporal_observation": "redacted"
      }}
    }}
  ]
}}"""
        )


if __name__ == "__main__":
    unittest.main()
