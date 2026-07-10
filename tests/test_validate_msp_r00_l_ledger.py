from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_msp_r00_l_ledger.py"
VALIDATE_REPO_SCRIPT = ROOT / "scripts" / "validate_plans_repo.sh"

spec = importlib.util.spec_from_file_location("validate_msp_r00_l_ledger", MODULE_PATH)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

LEDGER_PATH = validator.resolve_default_ledger(ROOT)


class MspR00LLedgerValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        self.ledger_bytes = LEDGER_PATH.read_bytes()

    def write_temp_ledger(self, root: Path, state: str) -> Path:
        plan_dir = root / f"{validator.PLAN_SLUG}.{state}"
        plan_dir.mkdir()
        ledger_path = plan_dir / validator.LEDGER_FILENAME
        ledger_path.write_bytes(self.ledger_bytes)
        return ledger_path

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

    def test_explicit_cli_path_validation_preserves_ledger_bytes(self) -> None:
        before = LEDGER_PATH.read_bytes()
        validator.validate_ledger(LEDGER_PATH)
        self.assertEqual(before, LEDGER_PATH.read_bytes())

    def test_repo_validator_disables_python_bytecode_before_python_invocations(self) -> None:
        lines = VALIDATE_REPO_SCRIPT.read_text(encoding="utf-8").splitlines()
        export_index = lines.index("export PYTHONDONTWRITEBYTECODE=1")
        python_invocations = [
            index
            for index, line in enumerate(lines)
            if line.startswith("python3 ") or '"$TOKEN_VENV/bin/python"' in line
        ]
        self.assertGreaterEqual(len(python_invocations), 2)
        self.assertLess(export_index, min(python_invocations))

    def test_discovers_default_locked_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self.write_temp_ledger(root, "locked")
            self.assertEqual(validator.resolve_default_ledger(root), expected)
            validator.validate_ledger(root=root)

    def test_discovers_default_implementing_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self.write_temp_ledger(root, "implementing")
            self.assertEqual(validator.resolve_default_ledger(root), expected)
            validator.validate_ledger(root=root)

    def test_discovers_default_maintenance_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self.write_temp_ledger(root, "maintenance")
            self.assertEqual(validator.resolve_default_ledger(root), expected)
            validator.validate_ledger(root=root)

    def test_temp_ledger_helper_supports_non_locked_lifecycle_states(self) -> None:
        for state in ("implementing", "maintenance"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                expected = self.write_temp_ledger(root, state)
                self.assertEqual(
                    expected,
                    root / f"{validator.PLAN_SLUG}.{state}" / validator.LEDGER_FILENAME,
                )
                self.assertEqual(validator.resolve_default_ledger(root), expected)
                validator.validate_ledger(root=root)

    def test_rejects_missing_default_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(validator.ValidationError):
                validator.resolve_default_ledger(Path(tmp))

    def test_rejects_active_directory_without_default_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / f"{validator.PLAN_SLUG}.locked").mkdir()
            with self.assertRaises(validator.ValidationError):
                validator.resolve_default_ledger(root)

    def test_rejects_ambiguous_default_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_temp_ledger(root, "locked")
            self.write_temp_ledger(root, "implementing")
            with self.assertRaises(validator.ValidationError):
                validator.resolve_default_ledger(root)

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
