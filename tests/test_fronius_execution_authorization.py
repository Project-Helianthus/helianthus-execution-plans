from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "fronius-modbus-multivendor-v3-w29-26.locked"
VALIDATOR = PLAN / "validate_plan.py"


class FroniusExecutionAuthorizationTests(unittest.TestCase):
    def authorize(self, issue_id: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(VALIDATOR), "--authorize-issue", issue_id],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_last_pre_gateway_issue_is_authorized(self) -> None:
        result = self.authorize("FMV3-M3-03")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fail-closed execution allowlist", result.stdout)

    def test_gateway_boundary_is_rejected(self) -> None:
        result = self.authorize("FMV3-M4-01")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the fail-closed execution allowlist", result.stderr)

    def test_deferred_private_governance_is_rejected(self) -> None:
        result = self.authorize("FMV3-M0-04")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the fail-closed execution allowlist", result.stderr)

    def test_authorized_action_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / PLAN.name
            shutil.copytree(PLAN, copied)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            issue = next(row for row in plan["issues"] if row["id"] == "FMV3-M3-03")
            issue["what"] = "Drifted authorized action"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), str(copied)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("action contract digest mismatch", result.stderr)

    def test_implementing_lifecycle_state_is_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / PLAN.name.replace(".locked", ".implementing")
            shutil.copytree(PLAN, copied)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            old_digest = plan["canonical_sha256"]
            plan["state"] = "implementing"

            canonical_path = copied / "00-canonical.md"
            canonical = canonical_path.read_text(encoding="utf-8").replace(
                "State: `locked`", "State: `implementing`", 1
            )
            canonical_path.write_text(canonical, encoding="utf-8")
            new_digest = hashlib.sha256(canonical_path.read_bytes()).hexdigest()
            plan["canonical_sha256"] = new_digest
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")

            for path in copied.glob("*.md"):
                if path == canonical_path:
                    continue
                text = path.read_text(encoding="utf-8").replace(old_digest, new_digest)
                if path.name == "99-status.md":
                    text = text.replace("# Locked status", "# Implementing status", 1)
                    text = text.replace("State: locked", "State: implementing", 1)
                path.write_text(text, encoding="utf-8")

            result = subprocess.run(
                ["python3", str(VALIDATOR), str(copied)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
