from __future__ import annotations

import hashlib
import pathlib
import subprocess
import tempfile
import unittest

from scripts import validate_modbus_m1_02_release as release


ANCHOR_SHA = "a" * 40


def run(root: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class ModbusM102ReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        strict_temp_root = pathlib.Path(tempfile.gettempdir()).resolve(strict=True)
        self.temp = tempfile.TemporaryDirectory(dir=strict_temp_root)
        self.root = pathlib.Path(self.temp.name)
        run(self.root, "init", "-q")
        run(self.root, "config", "user.name", "Test")
        run(self.root, "config", "user.email", "test@example.invalid")
        (self.root / "product.go").write_text("package product\n", encoding="utf-8")
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
            "attestation": {
                "context": "adversarial-review",
                "creator_id": 16434603,
                "creator_login": "d3vi1",
                "description": (
                    "OpenAI-only fresh adversarial consensus: NO_FINDINGS"
                ),
                "target": "pull_request_head",
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

    def test_exact_reviewed_commit_passes(self) -> None:
        self.assertEqual(
            release.validate_release(self.root, self.manifest),
            [],
        )

    def test_other_head_is_rejected(self) -> None:
        run(self.root, "commit", "--allow-empty", "-qm", "other head")
        self.assertTrue(
            any(
                "candidate HEAD is not exact reviewed SHA" in error
                for error in release.validate_release(self.root, self.manifest)
            )
        )

    def test_dirty_and_ignored_files_are_rejected(self) -> None:
        (self.root / "product.go").write_text("package dirty\n", encoding="utf-8")
        self.assertIn(
            "candidate worktree is dirty",
            release.validate_release(self.root, self.manifest),
        )
        run(self.root, "checkout", "--", "product.go")
        (self.root / ".gitignore").write_text("ignored.go\n", encoding="utf-8")
        run(self.root, "add", ".gitignore")
        run(self.root, "commit", "-qm", "ignore fixture")
        self.reviewed = run(self.root, "rev-parse", "HEAD")
        self.manifest = self.make_manifest()
        (self.root / "ignored.go").write_text("package hidden\n", encoding="utf-8")
        self.assertIn(
            "candidate worktree contains ignored files",
            release.validate_release(self.root, self.manifest),
        )

    def test_manifest_hash_mutation_is_rejected(self) -> None:
        self.manifest["files"]["product.go"]["sha256"] = "0" * 64
        self.assertIn(
            "reviewed content mismatch: product.go",
            release.validate_release(self.root, self.manifest),
        )

    def test_symlink_root_and_ancestor_are_rejected(self) -> None:
        direct = self.root.parent / f"{self.root.name}-link"
        ancestor = self.root.parent / f"{self.root.name}-ancestor"
        direct.symlink_to(self.root, target_is_directory=True)
        ancestor.symlink_to(self.root.parent, target_is_directory=True)
        try:
            for candidate in (direct, ancestor / self.root.name):
                self.assertEqual(
                    release.validate_release(candidate, self.manifest),
                    ["candidate root must be a regular directory"],
                )
                self.assertEqual(
                    release.validate_post_merge_tree(
                        candidate,
                        self.reviewed,
                        self.reviewed,
                    ),
                    ["repository root must be a regular directory"],
                )
        finally:
            direct.unlink()
            ancestor.unlink()

    def status(self, **overrides: object) -> dict:
        value = {
            "context": "adversarial-review",
            "creator": {"id": 16434603, "login": "d3vi1"},
            "description": (
                "OpenAI-only fresh adversarial consensus: NO_FINDINGS"
            ),
            "state": "success",
            "target_url": (
                "https://github.com/Project-Helianthus/"
                f"helianthus-execution-plans/commit/{ANCHOR_SHA}"
            ),
        }
        value.update(overrides)
        return value

    def test_exact_attestation_passes(self) -> None:
        self.assertEqual(
            release.validate_attestation_payload(
                [self.status()],
                self.manifest,
                ANCHOR_SHA,
            ),
            [],
        )

    def test_attestation_rejects_wrong_state_creator_description_and_url(
        self,
    ) -> None:
        mutations = (
            ({"state": "pending"}, "status is not success"),
            ({"creator": {"id": 1, "login": "other"}}, "creator identity"),
            ({"description": "NO_FINDINGS"}, "description is not exact"),
            ({"target_url": "https://example.invalid"}, "target URL"),
        )
        for override, expected in mutations:
            with self.subTest(override=override):
                errors = release.validate_attestation_payload(
                    [self.status(**override)],
                    self.manifest,
                    ANCHOR_SHA,
                )
                self.assertTrue(any(expected in error for error in errors))

    def test_latest_matching_attestation_wins(self) -> None:
        errors = release.validate_attestation_payload(
            [
                self.status(state="failure"),
                self.status(),
            ],
            self.manifest,
            ANCHOR_SHA,
        )
        self.assertIn(
            "latest adversarial-review status is not success",
            errors,
        )

    def test_post_merge_requires_exact_attested_tree(self) -> None:
        run(self.root, "checkout", "-qb", "matching")
        run(self.root, "commit", "--allow-empty", "-qm", "squash identity")
        matching = run(self.root, "rev-parse", "HEAD")
        self.assertEqual(
            release.validate_post_merge_tree(
                self.root,
                matching,
                self.reviewed,
            ),
            [],
        )
        (self.root / "product.go").write_text("package changed\n", encoding="utf-8")
        run(self.root, "add", ".")
        run(self.root, "commit", "-qm", "different tree")
        different = run(self.root, "rev-parse", "HEAD")
        self.assertIn(
            "post-squash main tree does not equal attested PR-head tree",
            release.validate_post_merge_tree(
                self.root,
                different,
                self.reviewed,
            ),
        )


if __name__ == "__main__":
    unittest.main()
