from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "software-stabilization-07-08.implementing"
VALIDATOR_PATH = PLAN_DIR / "validate_plan.py"
SPEC = importlib.util.spec_from_file_location("software_stabilization_plan", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SoftwareStabilizationPlanTests(unittest.TestCase):
    def copy_plan(self, destination: Path) -> Path:
        plan_dir = destination / PLAN_DIR.name
        shutil.copytree(PLAN_DIR, plan_dir)
        self.write_mirror(plan_dir, self.load_plan(plan_dir))
        return plan_dir

    def write_mirror(self, plan_dir: Path, plan: dict[str, object]) -> None:
        packages = plan["packages"]
        assert isinstance(packages, list)
        rows = [
            "| ID | Release | Owner | Outcome | Prerequisites |",
            "|---|---|---|---|---|",
        ]
        for package in packages:
            dependencies = ", ".join(package["depends_on"]) or "None"
            rows.append(
                f"| {package['id']} | {package['release']} | {package['owner']} | test | {dependencies} |"
            )
        path = plan_dir / "91-milestone-map.md"
        text = path.read_text(encoding="utf-8")
        start = text.index("| ID |")
        end = text.index("\n## ", start)
        path.write_text(text[:start] + "\n".join(rows) + text[end:], encoding="utf-8")

    def load_plan(self, plan_dir: Path) -> dict[str, object]:
        return yaml.safe_load((plan_dir / "plan.yaml").read_text(encoding="utf-8"))

    def write_plan(self, plan_dir: Path, plan: dict[str, object]) -> None:
        (plan_dir / "plan.yaml").write_text(
            yaml.safe_dump(plan, sort_keys=False), encoding="utf-8"
        )

    def package(self, plan: dict[str, object], package_id: str) -> dict[str, object]:
        packages = plan["packages"]
        assert isinstance(packages, list)
        return next(package for package in packages if package["id"] == package_id)

    def test_current_plan_is_valid(self) -> None:
        self.assertEqual(
            {"packages": 45, "repositories": 13},
            VALIDATOR.validate_plan(PLAN_DIR),
        )

    def test_rejects_unknown_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "INT-01")["owner"] = "Project-Helianthus/unknown"
            self.write_plan(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "unknown owner"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_coherent_repository_typo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            repositories = plan["repositories"]
            assert isinstance(repositories, dict)
            owner = "Project-Helianthus/helianthus-ebusgateway"
            typo = "Project-Helianthus/helianthus-ebusgateawy"
            repositories[typo] = repositories.pop(owner)
            packages = plan["packages"]
            assert isinstance(packages, list)
            for package in packages:
                if package["owner"] == owner:
                    package["owner"] = typo
            self.write_plan(plan_dir, plan)
            self.write_mirror(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "repository allowlist is invalid"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_dependency_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "GOV-01")["depends_on"] = ["INT-24"]
            self.package(plan, "INT-24")["depends_on"] = ["GOV-01"]
            self.write_plan(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "must be acyclic"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_semreg_implementation_without_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "INT-05")["depends_on"] = ["INT-04"]
            self.write_plan(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "downstream of SEMREG-BOOTSTRAP"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_renamed_gateway_before_int14(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "INT-17")["depends_on"].remove("INT-16")
            self.write_plan(plan_dir, plan)
            self.write_mirror(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "INT-17 must remain downstream of INT-14"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_post_rename_package_with_old_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "INT-19")["owner"] = "Project-Helianthus/helianthus-ebusgateway"
            self.write_plan(plan_dir, plan)
            self.write_mirror(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "INT-19 must be owned by the renamed gateway"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_release_without_daybreak_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "INT-20")["depends_on"] = [
                "LEGACY-PERSIST",
                "LEGACY-IDENTITY",
                "LEGACY-MUX",
            ]
            self.write_plan(plan_dir, plan)
            self.write_mirror(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "INT-20 must remain downstream of INT-19"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_release_without_hardware_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "INT-21")["depends_on"] = [
                "LEGACY-PERSIST",
                "LEGACY-IDENTITY",
                "LEGACY-MUX",
            ]
            self.write_plan(plan_dir, plan)
            self.write_mirror(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "INT-21 must remain downstream of INT-19, INT-20"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_08_release_without_08_hardware_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            plan = self.load_plan(plan_dir)
            self.package(plan, "INT-24")["depends_on"] = ["INT-22"]
            self.write_plan(plan_dir, plan)
            self.write_mirror(plan_dir, plan)
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "INT-24 must remain downstream of INT-22, INT-23"):
                VALIDATOR.validate_plan(plan_dir)

    def test_rejects_markdown_owner_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_dir = self.copy_plan(Path(temporary))
            path = plan_dir / "91-milestone-map.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "| GOV-01 | 0.7 | Project-Helianthus/.github |",
                    "| GOV-01 | 0.7 | Project-Helianthus/helianthus-ebusgateway |",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "does not mirror"):
                VALIDATOR.validate_plan(plan_dir)


if __name__ == "__main__":
    unittest.main()
