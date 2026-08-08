from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "fronius-modbus-multivendor-v3-w29-26.implementing"
    / "validate_plan.py"
)


class ModbusM1PlanSeparationTests(unittest.TestCase):
    def test_fmv3_validator_does_not_import_legacy_live_gate(self) -> None:
        tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
        modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertNotIn("scripts.validate_modbus_docs_trust", modules)
        self.assertNotIn("scripts.validate_modbus_m1_02_release", modules)

    def test_fmv3_validator_has_no_remote_lookup_function(self) -> None:
        tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
        functions = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        self.assertTrue(functions.isdisjoint({"github_api", "fetch_docs", "checkout_docs"}))


if __name__ == "__main__":
    unittest.main()
