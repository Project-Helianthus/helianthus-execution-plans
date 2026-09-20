from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_validator(plan_dir: Path):
    spec = importlib.util.spec_from_file_location(plan_dir.name, plan_dir / "validate_plan.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SoftwareReleaseSplitTests(unittest.TestCase):
    def copy_plan(self, name: str) -> Path:
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary)
        destination = temporary / name
        shutil.copytree(ROOT / name, destination)
        return destination

    def test_guides_are_valid_and_separate(self) -> None:
        guide_07 = ROOT / "software-stabilization-07.implementing"
        guide_08 = ROOT / "software-declarative-08.locked"
        self.assertEqual({"packages": 49, "repositories": 15}, load_validator(guide_07).validate_plan(guide_07))
        self.assertEqual({"packages": 4, "repositories": 3}, load_validator(guide_08).validate_plan(guide_08))

    def test_07_rejects_future_package(self) -> None:
        plan_dir = self.copy_plan("software-stabilization-07.implementing")
        plan = yaml.safe_load((plan_dir / "plan.yaml").read_text())
        plan["packages"][0]["id"] = "INT-18"
        (plan_dir / "plan.yaml").write_text(yaml.safe_dump(plan, sort_keys=False))
        validator = load_validator(plan_dir)
        with self.assertRaisesRegex(validator.ValidationError, "exclusively to 0.8"):
            validator.validate_plan(plan_dir)

    def test_08_rejects_wrong_prerequisite(self) -> None:
        plan_dir = self.copy_plan("software-declarative-08.locked")
        plan = yaml.safe_load((plan_dir / "plan.yaml").read_text())
        plan["release_prerequisite"] = "ready"
        (plan_dir / "plan.yaml").write_text(yaml.safe_dump(plan, sort_keys=False))
        validator = load_validator(plan_dir)
        with self.assertRaisesRegex(validator.ValidationError, "0.7 prerequisite"):
            validator.validate_plan(plan_dir)
