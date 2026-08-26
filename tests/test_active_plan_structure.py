from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_active_plan_structure.py"
SPEC = importlib.util.spec_from_file_location("active_plan_structure", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ActivePlanStructureTests(unittest.TestCase):
    def copied_plan_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "plans"
        shutil.copytree(ROOT / "adapter-hardware-telemetry.maintenance", root / "adapter-hardware-telemetry.maintenance")
        return temporary, root

    def test_current_active_plan_directories_are_valid(self) -> None:
        expected = sum(
            1
            for state in VALIDATOR.ACTIVE_STATES
            for _ in ROOT.glob(f"*.{state}/plan.yaml")
        )
        self.assertEqual(expected, VALIDATOR.validate_active_plan_structure(ROOT))

    def test_rejects_directory_state_mismatch(self) -> None:
        temporary, root = self.copied_plan_root()
        self.addCleanup(temporary.cleanup)
        plan = root / "adapter-hardware-telemetry.maintenance" / "plan.yaml"
        document = yaml.safe_load(plan.read_text(encoding="utf-8"))
        document["state"] = "locked"
        plan.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

        with self.assertRaisesRegex(VALIDATOR.ValidationError, "state does not match directory suffix"):
            VALIDATOR.validate_active_plan_structure(root)

    def test_rejects_directory_slug_mismatch_and_missing_common_file(self) -> None:
        temporary, root = self.copied_plan_root()
        self.addCleanup(temporary.cleanup)
        plan = root / "adapter-hardware-telemetry.maintenance" / "plan.yaml"
        document = yaml.safe_load(plan.read_text(encoding="utf-8"))
        document["slug"] = "wrong-slug"
        plan.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

        with self.assertRaisesRegex(VALIDATOR.ValidationError, "slug does not match directory name"):
            VALIDATOR.validate_active_plan_structure(root)

        document["slug"] = "adapter-hardware-telemetry"
        plan.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        (root / "adapter-hardware-telemetry.maintenance" / "99-status.md").unlink()

        with self.assertRaisesRegex(VALIDATOR.ValidationError, "missing common active-plan files: 99-status.md"):
            VALIDATOR.validate_active_plan_structure(root)


if __name__ == "__main__":
    unittest.main()
