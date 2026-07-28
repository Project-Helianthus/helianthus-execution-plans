from __future__ import annotations

import hashlib
import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

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
                "anchor_base_ref": "main",
                "anchor_head_ref": "issue/71-m1-02-external-trust",
                "anchor_pull_request": 84,
                "anchor_repository": (
                    "Project-Helianthus/helianthus-execution-plans"
                ),
                "context": "adversarial-review",
                "creator_id": 16434603,
                "creator_login": "d3vi1",
                "description_prefix": (
                    "OpenAI-only fresh adversarial consensus: NO_FINDINGS"
                ),
                "target": "pull_request_head",
                "target_url": (
                    "https://github.com/Project-Helianthus/"
                    "helianthus-execution-plans/pull/84"
                ),
            },
            "files": files,
            "post_merge": {
                "base_ref": "main",
                "head_ref": "issue/5-owned-modbus-tcp-runtime",
                "pull_request": 6,
                "strategy": "squash",
                "target_ref": "refs/remotes/origin/main",
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
                        self.reviewed,
                        "refs/remotes/origin/main",
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
                "OpenAI-only fresh adversarial consensus: NO_FINDINGS "
                f"anchor-tree={ANCHOR_SHA}"
            ),
            "state": "success",
            "target_url": (
                "https://github.com/Project-Helianthus/"
                "helianthus-execution-plans/pull/84"
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

    def test_live_attestation_is_mandatory(self) -> None:
        self.assertEqual(
            release.validate_live_attestation(
                self.manifest,
                ANCHOR_SHA,
                "",
            ),
            ["GH_TOKEN is required to verify attestation"],
        )

    def test_status_fetch_follows_next_page(self) -> None:
        class Response(io.BytesIO):
            def __init__(self, payload: object, link: str = "") -> None:
                super().__init__(json.dumps(payload).encode("utf-8"))
                self.headers = {"Link": link}

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *args: object) -> None:
                self.close()

        first_url = (
            "https://api.github.com/repos/Project-Helianthus/"
            "helianthus-modbus/commits/abc/statuses?per_page=100"
        )
        next_url = first_url + "&page=2"
        responses = [
            Response(
                [{"context": "other"}],
                f'<{next_url}>; rel="next", <{next_url}>; rel="last"',
            ),
            Response([self.status()]),
        ]
        with mock.patch.object(
            release.urllib.request,
            "urlopen",
            side_effect=responses,
        ):
            self.assertEqual(
                release._github_json_pages(first_url, "token"),
                [{"context": "other"}, self.status()],
            )

    def test_merge_payload_binds_exact_pr_and_sha(self) -> None:
        valid = {
            "base": {
                "ref": "main",
                "repo": {"full_name": "Project-Helianthus/helianthus-modbus"},
            },
            "head": {
                "ref": "issue/5-owned-modbus-tcp-runtime",
                "repo": {"full_name": "Project-Helianthus/helianthus-modbus"},
                "sha": self.reviewed,
            },
            "merge_commit_sha": self.reviewed,
            "merged": True,
            "number": 6,
            "state": "closed",
        }
        self.assertEqual(
            release.validate_merge_payload(
                valid,
                self.manifest,
                self.reviewed,
            ),
            [],
        )
        invalid = dict(valid, merge_commit_sha="0" * 40)
        self.assertIn(
            "post-merge SHA is not the GitHub PR merge commit",
            release.validate_merge_payload(
                invalid,
                self.manifest,
                self.reviewed,
            ),
        )

    def test_live_modbus_pr_head_must_equal_reviewed_sha(self) -> None:
        payload = {
            "base": {
                "ref": "main",
                "repo": {"full_name": "Project-Helianthus/helianthus-modbus"},
            },
            "head": {
                "ref": "issue/5-owned-modbus-tcp-runtime",
                "repo": {"full_name": "Project-Helianthus/helianthus-modbus"},
                "sha": "0" * 40,
            },
            "number": 6,
        }
        self.assertIn(
            "live Modbus PR head is not the reviewed SHA",
            release.validate_pull_request_head_payload(payload, self.manifest),
        )

    def test_anchor_must_be_exact_reviewed_pr_tree(self) -> None:
        pull_request = {
            "base": {
                "ref": "main",
                "repo": {
                    "full_name": (
                        "Project-Helianthus/helianthus-execution-plans"
                    )
                },
            },
            "head": {
                "ref": "issue/71-m1-02-external-trust",
                "repo": {
                    "full_name": (
                        "Project-Helianthus/helianthus-execution-plans"
                    )
                },
                "sha": ANCHOR_SHA,
            },
            "number": 84,
        }
        commit = {"sha": ANCHOR_SHA, "tree": {"sha": self.reviewed}}
        self.assertEqual(
            release.validate_anchor_review_payload(
                pull_request,
                commit,
                self.manifest,
                self.reviewed,
            ),
            [],
        )
        commit["tree"]["sha"] = "0" * 40
        self.assertIn(
            "local anchor tree is not the reviewed PR-head tree",
            release.validate_anchor_review_payload(
                pull_request,
                commit,
                self.manifest,
                self.reviewed,
            ),
        )

    def test_post_merge_requires_exact_attested_tree(self) -> None:
        run(self.root, "checkout", "-qb", "matching")
        run(self.root, "commit", "--allow-empty", "-qm", "squash identity")
        matching = run(self.root, "rev-parse", "HEAD")
        run(
            self.root,
            "update-ref",
            "refs/remotes/origin/main",
            matching,
        )
        self.assertEqual(
            release.validate_post_merge_tree(
                self.root,
                matching,
                self.reviewed,
                self.reviewed,
                "refs/remotes/origin/main",
            ),
            [],
        )
        run(self.root, "commit", "--allow-empty", "-qm", "later main commit")
        later = run(self.root, "rev-parse", "HEAD")
        run(
            self.root,
            "update-ref",
            "refs/remotes/origin/main",
            later,
        )
        self.assertEqual(
            release.validate_post_merge_tree(
                self.root,
                matching,
                self.reviewed,
                self.reviewed,
                "refs/remotes/origin/main",
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
                self.reviewed,
                "refs/remotes/origin/main",
            ),
        )
        self.assertIn(
            "attested PR head is not the manifest reviewed SHA",
            release.validate_post_merge_tree(
                self.root,
                matching,
                matching,
                self.reviewed,
                "refs/remotes/origin/main",
            ),
        )
        reviewed_tree = run(self.root, "rev-parse", f"{matching}^{{tree}}")
        unrelated = run(
            self.root,
            "commit-tree",
            reviewed_tree,
            "-m",
            "unrelated same tree",
        )
        run(
            self.root,
            "update-ref",
            "refs/remotes/origin/main",
            unrelated,
        )
        self.assertIn(
            "post-merge SHA is not contained in target branch",
            release.validate_post_merge_tree(
                self.root,
                matching,
                self.reviewed,
                self.reviewed,
                "refs/remotes/origin/main",
            ),
        )


if __name__ == "__main__":
    unittest.main()
