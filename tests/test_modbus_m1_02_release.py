from __future__ import annotations

import hashlib
import pathlib
import subprocess
import tempfile
import unittest

from scripts import validate_modbus_m1_02_release as release


TRUST_SHA = "a" * 40


def run(root: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class ModbusM102ReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        run(self.root, "init", "-q")
        run(self.root, "config", "user.name", "Test")
        run(self.root, "config", "user.email", "test@example.invalid")
        self.primary_branch = run(self.root, "branch", "--show-current")
        (self.root / "scripts").mkdir()
        (self.root / "product.go").write_text("package product\n", encoding="utf-8")
        ci = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"\n'
            "export PYTHONDONTWRITEBYTECODE=1\n"
            'echo "$ROOT"\n'
        )
        (self.root / release.CI_PATH).write_text(ci, encoding="utf-8")
        (self.root / release.CI_PATH).chmod(0o755)
        run(self.root, "add", ".")
        run(self.root, "commit", "-qm", "reviewed")
        self.reviewed = run(self.root, "rev-parse", "HEAD")
        self.manifest = self.make_manifest()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_manifest(self) -> dict:
        files = {}
        tracked = run(self.root, "ls-tree", "-r", "--name-only", "HEAD")
        for path in tracked.splitlines():
            mode = run(self.root, "ls-tree", "HEAD", "--", path).split()[0]
            data = (self.root / path).read_bytes()
            files[path] = {
                "mode": mode,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        return {
            "allowed_child_changes": {
                release.CI_PATH: "modified",
                release.HOOK_PATH: "added",
            },
            "attestation": {
                "required_context": "adversarial-review",
                "target": "pull_request_head",
                "workflow_permissions": "contents:read",
            },
            "files": files,
            "post_merge": {
                "strategy": "squash",
                "tree_must_equal_attested_pr_head": True,
            },
            "repository": "Project-Helianthus/helianthus-modbus",
            "reviewed_sha": self.reviewed,
            "schema": "helianthus.modbus.m1-02-release",
            "version": 1,
        }

    def make_child(self) -> str:
        reviewed_ci = (self.root / release.CI_PATH).read_bytes()
        (self.root / release.CI_PATH).write_bytes(
            release._expected_ci(reviewed_ci)
        )
        hook = self.root / release.HOOK_PATH
        hook.write_bytes(release._expected_hook(TRUST_SHA))
        hook.chmod(0o755)
        run(self.root, "add", ".")
        run(self.root, "commit", "-qm", "external gate")
        return run(self.root, "rev-parse", "HEAD")

    def validate(self, allow_reviewed: bool = False) -> list[str]:
        return release.validate_release(
            self.root,
            self.manifest,
            TRUST_SHA,
            allow_reviewed,
        )

    def test_reviewed_commit_passes_only_for_anchor_creation(self) -> None:
        self.assertEqual(self.validate(allow_reviewed=True), [])
        self.assertIn(
            "release candidate must be the exact permitted child",
            self.validate(),
        )

    def test_exact_single_child_passes(self) -> None:
        self.make_child()
        self.assertEqual(self.validate(), [])

    def test_product_mutation_is_rejected(self) -> None:
        self.make_child()
        (self.root / "product.go").write_text("package changed\n", encoding="utf-8")
        run(self.root, "add", ".")
        run(self.root, "commit", "-qm", "mutate product")
        errors = self.validate()
        self.assertIn(
            "release candidate must be a direct single-parent child",
            errors,
        )
        self.assertTrue(
            any("candidate content mismatch: product.go" in item for item in errors)
        )

    def test_extra_file_is_rejected(self) -> None:
        self.make_child()
        (self.root / "backdoor.go").write_text("package product\n", encoding="utf-8")
        run(self.root, "add", ".")
        run(self.root, "commit", "--amend", "-qm", "external gate plus file")
        errors = self.validate()
        self.assertTrue(
            any("candidate tree inventory mismatch" in item for item in errors)
        )
        self.assertTrue(any("candidate changes are not exact" in item for item in errors))

    def test_hook_byte_change_is_rejected(self) -> None:
        self.make_child()
        hook = self.root / release.HOOK_PATH
        hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        run(self.root, "add", ".")
        run(self.root, "commit", "--amend", "-qm", "weaken hook")
        self.assertIn(
            "external release hook bytes are not exact",
            self.validate(),
        )

    def test_ci_hook_omission_is_rejected(self) -> None:
        self.make_child()
        original = release._blob(self.root, self.reviewed, release.CI_PATH)
        (self.root / release.CI_PATH).write_bytes(original + b"# changed\n")
        run(self.root, "add", ".")
        run(self.root, "commit", "--amend", "-qm", "weaken ci")
        self.assertIn(
            "ci_local.sh external hook insertion is not exact",
            self.validate(),
        )

    def test_dirty_worktree_is_rejected(self) -> None:
        self.make_child()
        (self.root / "product.go").write_text("package dirty\n", encoding="utf-8")
        self.assertIn("candidate worktree is dirty", self.validate())

    def test_ignored_worktree_file_is_rejected(self) -> None:
        run(self.root, "checkout", "-q", self.reviewed)
        (self.root / ".gitignore").write_text("ignored.go\n", encoding="utf-8")
        run(self.root, "add", ".gitignore")
        run(self.root, "commit", "--amend", "--no-edit", "-q")
        self.reviewed = run(self.root, "rev-parse", "HEAD")
        self.manifest = self.make_manifest()
        self.make_child()
        (self.root / "ignored.go").write_text("package hidden\n", encoding="utf-8")
        self.assertIn(
            "candidate worktree contains ignored files",
            self.validate(),
        )

    def test_symlink_replacement_is_rejected(self) -> None:
        self.make_child()
        (self.root / "product.go").unlink()
        (self.root / "product.go").symlink_to("scripts/ci_local.sh")
        run(self.root, "add", ".")
        run(self.root, "commit", "--amend", "-qm", "symlink replacement")
        errors = self.validate()
        self.assertTrue(any("candidate mode mismatch: product.go" in e for e in errors))
        self.assertTrue(any("candidate changes are not exact" in e for e in errors))

    def test_merge_child_is_rejected(self) -> None:
        self.make_child()
        child = run(self.root, "rev-parse", "HEAD")
        run(self.root, "checkout", "-qb", "side", self.reviewed)
        (self.root / "side.txt").write_text("side\n", encoding="utf-8")
        run(self.root, "add", ".")
        run(self.root, "commit", "-qm", "side")
        run(self.root, "checkout", "-q", self.primary_branch)
        run(self.root, "merge", "--no-ff", "-qm", "merge", "side")
        self.assertNotEqual(run(self.root, "rev-parse", "HEAD"), child)
        self.assertIn(
            "release candidate must be a direct single-parent child",
            self.validate(),
        )


if __name__ == "__main__":
    unittest.main()
