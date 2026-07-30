from __future__ import annotations

import base64
from collections.abc import Callable
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import validate_modbus_docs_trust as trust_validator


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
AMENDMENT_PR_URL = (
    "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/89"
)


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
        if PLAN_DATA["state"] == "locked":
            anchored = repo / PLAN.name
            shutil.copytree(PLAN, anchored)
        else:
            locked = self.copy_lifecycle(temp, "locked", "M0")
            anchored = repo / locked.name
            shutil.move(str(locked), anchored)
        shutil.copytree(ROOT / "runtime-gates", repo / "runtime-gates")
        (repo / "scripts").mkdir()
        (repo / "scripts/validate_modbus_docs_trust.py").write_bytes(
            (ROOT / "scripts/validate_modbus_docs_trust.py").read_bytes()
        )
        (repo / "repository-marker.txt").write_text("clean\n", encoding="utf-8")
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Authorization Test")
        self.git(repo, "config", "user.email", "authorization-test@example.invalid")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "publish authorization anchor")
        head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        gate_path = repo / "runtime-gates/fronius-modbus-m1-admission.json"
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        gate["trust_anchor_commit"] = head
        gate_path.write_text(
            json.dumps(gate, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.git(repo, "add", gate_path.relative_to(repo).as_posix())
        self.git(repo, "commit", "-m", "bind test M1 trust anchor")
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
        if PLAN_DATA["state"] != "locked":
            shutil.rmtree(anchored)
            copied = repo / PLAN.name
            shutil.copytree(PLAN, copied)
            self.git(repo, "add", "-A")
            self.git(repo, "commit", "-m", "enter current lifecycle")
            self.git(repo, "push", "origin", "main")
            head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        else:
            copied = anchored
        return copied, head

    def authorize(
        self,
        plan_root: Path,
        anchor_sha: str,
        issue_id: str,
        amendment_pr: dict[str, object] | None = None,
        github_responses: dict[str, object] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        plan = yaml.safe_load((plan_root / "plan.yaml").read_text(encoding="utf-8"))
        contract_digest = plan["execution_authorization"]["authorized_issue_contract_sha256"]
        command = [
            sys.executable,
            str(VALIDATOR),
            str(plan_root),
            "--authorize-issue",
            issue_id,
            "--plan-head-sha",
            anchor_sha,
            "--authorization-contract-sha256",
            contract_digest,
        ]
        if amendment_pr is None and github_responses is None:
            return subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        with tempfile.TemporaryDirectory() as fake_bin:
            gh = Path(fake_bin) / "gh"
            gh.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "if len(sys.argv) != 3 or sys.argv[1] != 'api':\n"
                "    raise SystemExit(2)\n"
                "responses = json.loads(os.environ['FAKE_GH_RESPONSES'])\n"
                "if sys.argv[2] not in responses:\n"
                "    raise SystemExit(2)\n"
                "print(json.dumps(responses[sys.argv[2]]))\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
            responses = dict(github_responses or {})
            if amendment_pr is not None:
                responses[
                    "repos/Project-Helianthus/helianthus-execution-plans/pulls/89"
                ] = amendment_pr
            env["FAKE_GH_RESPONSES"] = json.dumps(responses)
            return subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

    def publish_amendment_reference(
        self,
        plan_root: Path,
        value: str = AMENDMENT_PR_URL,
    ) -> str:
        repo = plan_root.parent
        plan_path = plan_root / "plan.yaml"
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        authorization = plan["execution_authorization"]
        record = authorization.get(
            "authorization_amendment",
            authorization["authorization_anchor"],
        )
        record["authorization_pr"] = value
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
        self.git(repo, "add", plan_path.relative_to(repo).as_posix())
        staged = subprocess.run(
            ["git", "-C", str(repo), "diff", "--cached", "--quiet"],
            check=False,
        )
        self.assertIn(staged.returncode, {0, 1})
        if staged.returncode == 1:
            self.git(repo, "commit", "-m", "publish amendment PR reference")
            self.git(repo, "push", "origin", "main")
        return self.git(repo, "rev-parse", "HEAD").stdout.strip()

    def amendment_pr(
        self,
        anchor_sha: str,
        **overrides: object,
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "number": 89,
            "html_url": AMENDMENT_PR_URL,
            "state": "closed",
            "merged": True,
            "merge_commit_sha": anchor_sha,
            "author_association": "OWNER",
            "user": {"login": "d3vi1"},
            "base": {
                "ref": "main",
                "repo": {"full_name": "Project-Helianthus/helianthus-execution-plans"},
            },
        }
        value.update(overrides)
        return value

    def m1_admission_responses(
        self,
        plan_root: Path,
        amendment_anchor: str,
    ) -> dict[str, object]:
        gate = json.loads(
            (plan_root.parent / "runtime-gates/fronius-modbus-m1-admission.json").read_text(
                encoding="utf-8"
            )
        )
        workflow = json.dumps(
            trust_validator.expected_workflow(gate["trust_anchor_commit"]),
            indent=2,
            sort_keys=True,
        ) + "\n"
        return {
            "repos/Project-Helianthus/helianthus-execution-plans/pulls/89": self.amendment_pr(
                amendment_anchor
            ),
            "repos/Project-Helianthus/helianthus-docs-ebus/pulls/376": {
                "merged": True,
                "merge_commit_sha": gate["docs_merge_sha"],
            },
            f"repos/Project-Helianthus/helianthus-docs-ebus/pulls/{gate['verification_pr']}": {
                "merged": True,
                "base": {"ref": "main"},
                "head": {"sha": gate["verification_head_sha"]},
            },
            "repos/Project-Helianthus/helianthus-docs-ebus/branches/main/protection/required_status_checks": {
                "contexts": [gate["required_check"]],
                "checks": [],
            },
            f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{gate['verification_head_sha']}/check-runs": {
                "check_runs": [
                    {
                        "name": gate["required_check"],
                        "conclusion": "success",
                        "details_url": gate["required_check_run_url"],
                    }
                ]
            },
            "repos/Project-Helianthus/helianthus-docs-ebus/contents/.github/workflows/modbus-trusted-revision.yml?ref="
            f"{gate['docs_merge_sha']}": {
                "encoding": "base64",
                "content": base64.b64encode(workflow.encode("utf-8")).decode("ascii"),
            },
        }

    def copied_plan(self, temp: str) -> Path:
        copied = Path(temp) / PLAN.name
        shutil.copytree(PLAN, copied)
        return copied

    def amendment_surface_digest(self, plan_root: Path) -> str:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(plan_root),
                "--print-amendment-surfaces-sha256",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def rewrite_amendment_surface_digest(self, plan_root: Path) -> None:
        plan_path = plan_root / "plan.yaml"
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        plan["execution_authorization"]["authorization_anchor"][
            "amendment_surfaces_sha256"
        ] = self.amendment_surface_digest(plan_root)
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")

    def set_gateway_status_authorization(
        self,
        plan_root: Path,
        authorized: bool,
    ) -> None:
        status_path = plan_root / "99-status.md"
        unauthorized = "Gateway work authorized: no; stop before FMV3-M4-01"
        authorized_status = "Gateway work authorized: yes; FMV3-M4-01 is authorized"
        old, new = (
            (unauthorized, authorized_status)
            if authorized
            else (authorized_status, unauthorized)
        )
        status = status_path.read_text(encoding="utf-8")
        self.assertEqual(status.count(old), 1)
        status_path.write_text(status.replace(old, new, 1), encoding="utf-8")

    def published_amendment_snapshots(
        self,
        temp: str,
        mutate_anchor: Callable[[Path], None],
        mutate_current: Callable[[Path], None],
    ) -> tuple[Path, str, str]:
        repo = Path(temp) / "repo"
        repo.mkdir()
        plan_root = repo / PLAN.name
        shutil.copytree(PLAN, plan_root)
        shutil.copytree(ROOT / "runtime-gates", repo / "runtime-gates")
        (repo / "repository-marker.txt").write_text("clean\n", encoding="utf-8")
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Authorization Test")
        self.git(repo, "config", "user.email", "authorization-test@example.invalid")

        mutate_anchor(plan_root)
        self.rewrite_amendment_surface_digest(plan_root)
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "publish amended authorization anchor")
        anchor = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        remote = Path(temp) / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.git(repo, "remote", "add", "origin", str(remote))
        self.git(repo, "push", "-u", "origin", "main")

        mutate_current(plan_root)
        self.rewrite_amendment_surface_digest(plan_root)
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "restore current authorization snapshot")
        self.git(repo, "push", "origin", "main")
        current = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        return plan_root, anchor, current

    def rewrite_canonical_hashes(self, plan_root: Path) -> None:
        digest = hashlib.sha256((plan_root / "00-canonical.md").read_bytes()).hexdigest()
        plan_path = plan_root / "plan.yaml"
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        plan["canonical_sha256"] = digest
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
        for name in (
            "01-index.md",
            "10-architecture-and-repo-boundaries.md",
            "11-fronius-readonly-and-semantic-lock.md",
            "12-vendor-expansion-and-private-bindings.md",
            "13-roadmap-gates-and-risks.md",
            "99-status.md",
        ):
            path = plan_root / name
            text = path.read_text(encoding="utf-8")
            replaced, count = re.subn(
                r"Canonical-SHA256: `[0-9a-f]{64}`",
                f"Canonical-SHA256: `{digest}`",
                text,
            )
            self.assertEqual(count, 1)
            path.write_text(replaced, encoding="utf-8")

    def publish_current_lifecycle_digest_drift(
        self,
        plan_root: Path,
    ) -> tuple[Path, str, str]:
        repo = plan_root.parent
        anchor = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        locked = self.copy_lifecycle(str(repo), "locked", "M0")
        shutil.rmtree(plan_root)
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-m", "regenerate current lifecycle digest")
        self.git(repo, "push", "origin", "main")
        current = self.git(repo, "rev-parse", "HEAD").stdout.strip()
        return locked, anchor, current

    def block_m1_admission(self, plan_root: Path) -> None:
        repo = plan_root.parent
        gate_path = repo / "runtime-gates/fronius-modbus-m1-admission.json"
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        gate["state"] = "BLOCKED_PENDING_DOCS_TRUST"
        for key in (
            "branch_protection_evidence_url",
            "docs_merge_sha",
            "required_check_run_url",
            "required_check_verified_at",
            "trust_anchor_commit",
            "verification_head_sha",
            "verification_pr",
        ):
            gate[key] = None
        gate_path.write_text(
            json.dumps(gate, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.git(repo, "add", gate_path.relative_to(repo).as_posix())
        self.git(repo, "commit", "-m", "keep Modbus M1 admission blocked")
        self.git(repo, "push", "origin", "main")

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
        digest_result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(copied),
                "--print-amendment-surfaces-sha256",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(digest_result.returncode, 0, digest_result.stderr)
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        plan["execution_authorization"]["authorization_anchor"][
            "amendment_surfaces_sha256"
        ] = digest_result.stdout.strip()
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
        return copied

    def test_last_pre_gateway_issue_is_blocked_until_docs_trust_opens(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(plan_root)
            self.block_m1_admission(plan_root)
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M3-03",
                self.amendment_pr(anchor),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Modbus M1 admission gate is not OPEN", result.stderr)

    def test_m1_implementation_is_blocked_until_docs_trust_opens(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(plan_root)
            self.block_m1_admission(plan_root)
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M1-01",
                self.amendment_pr(anchor),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Modbus M1 admission gate is not OPEN", result.stderr)

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
            self.assertIn("live origin main HEAD", result.stderr)

    def test_stale_local_origin_main_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            remote = Path(temp) / "remote.git"
            other = Path(temp) / "other"
            subprocess.run(
                ["git", "clone", str(remote), str(other)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.git(other, "checkout", "-b", "main", "origin/main")
            self.git(other, "config", "user.name", "Remote Advance")
            self.git(
                other,
                "config",
                "user.email",
                "remote-advance@example.invalid",
            )
            (other / "advance.txt").write_text("advanced\n", encoding="utf-8")
            self.git(other, "add", "advance.txt")
            self.git(other, "commit", "-m", "advance live main")
            self.git(other, "push", "origin", "main")
            result = self.authorize(plan_root, anchor, "FMV3-M0-02")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("live origin main HEAD", result.stderr)

    def test_untracked_file_outside_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            (plan_root.parent / "outside-plan.txt").write_text("dirty\n", encoding="utf-8")
            result = self.authorize(plan_root, anchor, "FMV3-M3-03")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("entire checkout", result.stderr)

    def test_modified_file_outside_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            (plan_root.parent / "repository-marker.txt").write_text("modified\n", encoding="utf-8")
            result = self.authorize(plan_root, anchor, "FMV3-M3-03")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("entire checkout", result.stderr)

    def test_assume_unchanged_gate_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            repo = plan_root.parent
            gate_rel = "runtime-gates/fronius-modbus-m1-admission.json"
            self.git(repo, "update-index", "--assume-unchanged", gate_rel)
            gate = repo / gate_rel
            gate.write_text(
                gate.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            result = self.authorize(plan_root, anchor, "FMV3-M1-01")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nonstandard index flags", result.stderr)

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

    def test_implementing_lifecycle_authorizes_against_active_amendment_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            self.assertTrue(implementing.name.endswith(".implementing"))
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M0-02",
                self.amendment_pr(anchor),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fail-closed execution allowlist", result.stdout)

    def test_corrective_docs_issue_authorizes_against_active_amendment_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fail-closed execution allowlist", result.stdout)

    def test_structural_validator_rejects_placeholder_amendment_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            authorization = plan["execution_authorization"]
            record = authorization.get(
                "authorization_amendment",
                authorization["authorization_anchor"],
            )
            record["authorization_pr"] = "PENDING_PR_URL"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exact merged PR #89 URL", result.stderr)

    def test_amendment_authorization_rejects_placeholder_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing, "PENDING_PR_URL")
            result = self.authorize(implementing, anchor, "FMV3-M1-05")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exact merged PR #89 URL", result.stderr)

    def test_authorization_rejects_recomputed_current_surface_digest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, _ = self.published_plan(temp)
            self.publish_amendment_reference(implementing)
            current, anchor, _ = self.publish_current_lifecycle_digest_drift(
                implementing
            )
            result = self.authorize(
                current,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "current main amendment surface digest differs from merged PR #89 anchor",
                result.stderr,
            )

    def test_reflowed_canonical_authorization_whitespace_preserves_surface_digest(
        self,
    ) -> None:
        """Canonical prose whitespace is mutable; authorization words and fields are not."""
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            original_digest = self.amendment_surface_digest(copied)
            canonical = copied / "00-canonical.md"
            original = "sole immutable\nauthorization anchor"
            reflowed = "sole\nimmutable authorization anchor"
            text = canonical.read_text(encoding="utf-8")
            self.assertEqual(text.count(original), 1)
            canonical.write_text(text.replace(original, reflowed, 1), encoding="utf-8")
            self.rewrite_canonical_hashes(copied)
            self.assertEqual(original_digest, self.amendment_surface_digest(copied))
            result = self.run_validator(copied)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_current_milestone_reanchor_preserves_amendment_authorization(
        self,
    ) -> None:
        """Lifecycle progress is mutable; issue count, state, hard stop, and gateway ban are not."""
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            original_digest = self.amendment_surface_digest(plan_root)
            plan_path = plan_root / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["current_milestone"], "M0")
            plan["current_milestone"] = "M1"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            status_path = plan_root / "99-status.md"
            status = status_path.read_text(encoding="utf-8")
            self.assertEqual(status.count("Current milestone: M0"), 1)
            status_path.write_text(
                status.replace("Current milestone: M0", "Current milestone: M1", 1),
                encoding="utf-8",
            )
            self.assertEqual(original_digest, self.amendment_surface_digest(plan_root))
            self.rewrite_amendment_surface_digest(plan_root)
            self.git(plan_root.parent, "add", ".")
            self.git(plan_root.parent, "commit", "-m", "advance current milestone")
            self.git(plan_root.parent, "push", "origin", "main")
            current = self.git(plan_root.parent, "rev-parse", "HEAD").stdout.strip()
            responses = self.m1_admission_responses(plan_root, anchor)
            for issue_id in ("FMV3-M1-05", "FMV3-M1-06"):
                result = self.authorize(
                    plan_root,
                    anchor,
                    issue_id,
                    github_responses=responses,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("fail-closed execution allowlist", result.stdout)
            self.assertEqual(
                self.git(plan_root.parent, "rev-parse", "HEAD").stdout.strip(),
                current,
            )

    def test_amendment_authorization_rejects_unmerged_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor, state="open", merged=False, merge_commit_sha=None),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not merged at the plan authorization SHA", result.stderr)

    def test_amendment_authorization_rejects_wrong_merge_sha(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor, merge_commit_sha="f" * 40),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not merged at the plan authorization SHA", result.stderr)

    def test_amendment_authorization_rejects_wrong_issuer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor, user={"login": "not-the-owner"}),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("issuer mismatch", result.stderr)

    def test_amendment_authorization_rejects_wrong_author_association(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor, author_association="CONTRIBUTOR"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("author association is not allowed", result.stderr)

    def test_implementing_gateway_milestone_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copy_lifecycle(temp, "implementing", "M4")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exceeds authorized M3 boundary", result.stderr)

    def test_issue_map_action_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
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

    def test_canonical_hard_stop_inversion_with_regenerated_hashes_is_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            canonical = copied / "00-canonical.md"
            text = canonical.read_text(encoding="utf-8")
            old = "The hard stop is immediately before FMV3-M4-01."
            self.assertEqual(text.count(old), 1)
            canonical.write_text(
                text.replace(
                    old,
                    "The hard stop is immediately after FMV3-M4-01.",
                    1,
                ),
                encoding="utf-8",
            )
            self.rewrite_canonical_hashes(copied)
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("canonical authorization and hard-stop block mismatch", result.stderr)

    def test_milestone_map_m2_01_target_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            milestone_map = copied / "91-milestone-map.md"
            text = milestone_map.read_text(encoding="utf-8")
            old = (
                "| PG-OPAQUE-ACQUISITION-CONSUMER-PIN | "
                "FMV3-M1-06 merged after hosted RED/GREEN and fresh review; "
                "consumer pins full merged SHA | FMV3-M2-01 |"
            )
            self.assertEqual(text.count(old), 1)
            milestone_map.write_text(
                text.replace(old, old.replace("FMV3-M2-01", "FMV3-M2-02"), 1),
                encoding="utf-8",
            )
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("milestone-map corrective gate projection mismatch", result.stderr)

    def test_status_issue_count_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            status = copied / "99-status.md"
            text = status.read_text(encoding="utf-8")
            self.assertEqual(text.count("46-issue one-repository DAG"), 1)
            status.write_text(
                text.replace(
                    "46-issue one-repository DAG",
                    "45-issue one-repository DAG",
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("status issue-count projection mismatch", result.stderr)

    def test_amendment_surface_digest_binds_gateway_authorization_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            original = self.amendment_surface_digest(copied)
            self.set_gateway_status_authorization(copied, authorized=True)
            self.assertNotEqual(original, self.amendment_surface_digest(copied))

    def test_amendment_surface_digest_binds_corrective_gate_cardinality_and_order(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            original = self.amendment_surface_digest(copied)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            gates = plan["phase_gates"]
            first = next(
                index
                for index, gate in enumerate(gates)
                if gate["id"] == "PG-OPAQUE-ACQUISITION-DOC-GATE"
            )
            duplicate = dict(gates[first])
            gates.insert(first + 1, duplicate)
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            self.assertNotEqual(original, self.amendment_surface_digest(copied))

            gates.pop(first + 1)
            second = next(
                index
                for index, gate in enumerate(gates)
                if gate["id"] == "PG-OPAQUE-ACQUISITION-CONSUMER-PIN"
            )
            gates[first], gates[second] = gates[second], gates[first]
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            self.assertNotEqual(original, self.amendment_surface_digest(copied))

    def test_structural_validator_rejects_reordered_corrective_phase_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            gates = plan["phase_gates"]
            first = next(
                index
                for index, gate in enumerate(gates)
                if gate["id"] == "PG-OPAQUE-ACQUISITION-DOC-GATE"
            )
            second = next(
                index
                for index, gate in enumerate(gates)
                if gate["id"] == "PG-OPAQUE-ACQUISITION-CONSUMER-PIN"
            )
            gates[first], gates[second] = gates[second], gates[first]
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("corrective phase gate order mismatch", result.stderr)

    def test_authorization_rejects_anchor_gateway_status_restored_on_current(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor, current = self.published_amendment_snapshots(
                temp,
                lambda root: self.set_gateway_status_authorization(root, authorized=True),
                lambda root: self.set_gateway_status_authorization(root, authorized=False),
            )
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("status Gateway work authorized mismatch", result.stderr)
            self.assertEqual(
                self.git(plan_root.parent, "rev-parse", "HEAD").stdout.strip(),
                current,
            )

    def test_authorization_rejects_duplicate_corrective_gate_in_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def add_duplicate(root: Path) -> None:
                plan_path = root / "plan.yaml"
                plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
                gate = next(
                    gate
                    for gate in plan["phase_gates"]
                    if gate["id"] == "PG-OPAQUE-ACQUISITION-DOC-GATE"
                )
                plan["phase_gates"].append(dict(gate))
                plan_path.write_text(
                    yaml.safe_dump(plan, sort_keys=False), encoding="utf-8"
                )

            def remove_duplicate(root: Path) -> None:
                plan_path = root / "plan.yaml"
                plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
                seen: set[str] = set()
                gates = []
                for gate in plan["phase_gates"]:
                    if gate["id"] not in seen:
                        seen.add(gate["id"])
                        gates.append(gate)
                plan["phase_gates"] = gates
                plan_path.write_text(
                    yaml.safe_dump(plan, sort_keys=False), encoding="utf-8"
                )

            plan_root, anchor, _ = self.published_amendment_snapshots(
                temp,
                add_duplicate,
                remove_duplicate,
            )
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate phase gate ID", result.stderr)

    def test_corrective_issue_removal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["issues"] = [
                issue for issue in plan["issues"] if issue["id"] != "FMV3-M1-05"
            ]
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)

    def test_corrective_issue_reorder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            positions = {
                issue["id"]: index
                for index, issue in enumerate(plan["issues"])
                if issue["id"] in {"FMV3-M1-05", "FMV3-M1-06"}
            }
            first = positions["FMV3-M1-05"]
            second = positions["FMV3-M1-06"]
            plan["issues"][first], plan["issues"][second] = (
                plan["issues"][second],
                plan["issues"][first],
            )
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("corrective issue sequence mismatch", result.stderr)

    def test_corrective_issue_dependency_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            issue = next(
                issue for issue in plan["issues"] if issue["id"] == "FMV3-M1-06"
            )
            issue["depends_on"] = ["FMV3-M1-04"]
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)

    def test_duplicate_status_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
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
