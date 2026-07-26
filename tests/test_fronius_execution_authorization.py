from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLAN_CANDIDATES = [
    ROOT / f"fronius-modbus-multivendor-v3-w29-26.{state}"
    for state in ("locked", "implementing", "maintenance")
    if (ROOT / f"fronius-modbus-multivendor-v3-w29-26.{state}").is_dir()
]
if len(PLAN_CANDIDATES) != 1:
    raise RuntimeError("expected exactly one active Fronius Modbus lifecycle directory")
PLAN = PLAN_CANDIDATES[0]
VALIDATOR = PLAN / "validate_plan.py"
PLAN_DATA = yaml.safe_load((PLAN / "plan.yaml").read_text(encoding="utf-8"))


class FroniusExecutionAuthorizationTests(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def published_plan(self, temp: str) -> tuple[Path, str]:
        repo = Path(temp) / "repo"
        repo.mkdir()
        copied = repo / PLAN.name
        shutil.copytree(PLAN, copied)
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Authorization Test")
        self.git(repo, "config", "user.email", "authorization-test@example.invalid")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "publish plan")
        head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        remote = Path(temp) / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.git(repo, "remote", "add", "origin", str(remote))
        self.git(repo, "push", "-u", "origin", "main")
        return copied, head

    def authorize(
        self, plan_root: Path, anchor_sha: str, issue_id: str
    ) -> subprocess.CompletedProcess[str]:
        plan = yaml.safe_load((plan_root / "plan.yaml").read_text(encoding="utf-8"))
        contract_digest = plan["execution_authorization"]["authorized_issue_contract_sha256"]
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(plan_root),
                "--authorize-issue",
                issue_id,
                "--plan-head-sha",
                anchor_sha,
                "--authorization-contract-sha256",
                contract_digest,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def copy_lifecycle(self, temp: str, state: str, milestone: str) -> Path:
        copied = Path(temp) / f"fronius-modbus-multivendor-v3-w29-26.{state}"
        shutil.copytree(PLAN, copied)
        plan_path = copied / "plan.yaml"
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        old_state = plan["state"]
        old_digest = plan["canonical_sha256"]
        plan["state"] = state
        plan["current_milestone"] = milestone

        canonical_path = copied / "00-canonical.md"
        canonical = canonical_path.read_text(encoding="utf-8").replace(
            f"State: `{old_state}`", f"State: `{state}`", 1
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
                text = text.replace(
                    f"# {old_state.capitalize()} status", f"# {state.capitalize()} status", 1
                )
                text = text.replace(f"State: {old_state}", f"State: {state}", 1)
                text = text.replace(
                    f"Current milestone: {PLAN_DATA['current_milestone']}",
                    f"Current milestone: {milestone}",
                    1,
                )
            path.write_text(text, encoding="utf-8")
        return copied

    def test_last_pre_gateway_issue_is_authorized(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            result = self.authorize(plan_root, anchor, "FMV3-M3-03")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fail-closed execution allowlist", result.stdout)

    def test_gateway_boundary_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            result = self.authorize(plan_root, anchor, "FMV3-M4-01")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("absent from the merged authorization anchor", result.stderr)

    def test_deferred_private_governance_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            result = self.authorize(plan_root, anchor, "FMV3-M0-04")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("absent from the merged authorization anchor", result.stderr)

    def test_unmerged_feature_head_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            repo = plan_root.parent
            self.git(repo, "checkout", "-b", "unmerged")
            marker = repo / "unmerged.txt"
            marker.write_text("unmerged\n", encoding="utf-8")
            self.git(repo, "add", "unmerged.txt")
            self.git(repo, "commit", "-m", "unmerged branch")
            result = self.authorize(plan_root, anchor, "FMV3-M3-03")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("authoritative origin/main HEAD", result.stderr)

    def test_authorized_action_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / PLAN.name
            shutil.copytree(PLAN, copied)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            issue = next(row for row in plan["issues"] if row["id"] == "FMV3-M3-03")
            issue["what"] = "Drifted authorized action"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("action contract digest mismatch", result.stderr)

    def test_implementing_lifecycle_state_is_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copy_lifecycle(temp, "implementing", "M0")
            result = self.run_validator(copied)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_implementing_gateway_milestone_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copy_lifecycle(temp, "implementing", "M4")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exceeds authorized M3 boundary", result.stderr)

    def test_issue_map_action_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / PLAN.name
            shutil.copytree(PLAN, copied)
            issue_map = copied / "90-issue-map.md"
            issue_map.write_text(
                issue_map.read_text(encoding="utf-8").replace(
                    "Determine Fronius phase-1 applicability and implement only any evidence-required TCP read-only overlay.",
                    "Broadened map-only action",
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("issue-map action mismatch", result.stderr)

    def test_duplicate_status_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / PLAN.name
            shutil.copytree(PLAN, copied)
            status = copied / "99-status.md"
            status.write_text(
                status.read_text(encoding="utf-8") + f"\nState: {PLAN_DATA['state']}\n",
                encoding="utf-8",
            )
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly one State field", result.stderr)


if __name__ == "__main__":
    unittest.main()
