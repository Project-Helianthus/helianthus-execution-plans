from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "scripts" / "aggregate_completion_token.py"
PROCESS_ATTESTATION = (
    ROOT
    / "multi-runtime-semantic-platform.locked"
    / "109-msp-docs-e2r-aggregate-process-attestation.json"
)


def load_implementation() -> object:
    spec = importlib.util.spec_from_file_location(
        "aggregate_completion_token", IMPLEMENTATION
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load AGGREGATE implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureObservations:
    def __init__(
        self,
        error: type[Exception],
        *,
        comments: dict[tuple[str, int, int], dict[str, object]] | None = None,
        pulls: dict[tuple[str, int], dict[str, object]] | None = None,
        refs: dict[tuple[str, str], str] | None = None,
    ) -> None:
        self.error = error
        self.comments = comments or {}
        self.pulls = pulls or {}
        self.refs = refs or {}
        self.fetched: list[tuple[str, str]] = []

    def issue_comment(
        self, repository: str, issue: int, comment_id: int
    ) -> dict[str, object]:
        try:
            return copy.deepcopy(self.comments[(repository, issue, comment_id)])
        except KeyError as exc:
            raise self.error("fixture-comment-offline") from exc

    def pull_request(self, repository: str, pr: int) -> dict[str, object]:
        try:
            return copy.deepcopy(self.pulls[(repository, pr)])
        except KeyError as exc:
            raise self.error("fixture-pr-offline") from exc

    def fetch_ref(self, root: Path, repository: str, remote_ref: str) -> str:
        del root
        self.fetched.append((repository, remote_ref))
        try:
            return self.refs[(repository, remote_ref)]
        except KeyError as exc:
            raise self.error("fixture-ref-offline") from exc


class AggregateDefenseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aggregate = load_implementation()

    def test_canonical_loader_rejects_duplicate_noncanonical_and_nonfinite_json(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            path.write_bytes(b'{"a":1}\n')
            self.assertEqual(self.aggregate.load_canonical_json(path), {"a": 1})
            for raw in (
                b'{"a":1,"a":1}\n',
                b'{ "a": 1 }\n',
                b'{"a":NaN}\n',
                b'{"a":1}',
            ):
                with self.subTest(raw=raw):
                    path.write_bytes(raw)
                    with self.assertRaises(self.aggregate.AggregateError):
                        self.aggregate.load_canonical_json(path)

    def test_review_and_attestation_shapes_are_fail_closed(self) -> None:
        review = {
            "evidence_sha256": "5" * 64,
            "p0_p2_findings": [],
            "result": "pass",
        }
        self.assertEqual(self.aggregate.validate_architecture_review(review), review)
        for invalid in (
            {**review, "extra": True},
            {**review, "result": "PASS"},
            {**review, "p0_p2_findings": ["P2"]},
            {**review, "evidence_sha256": "5" * 63},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(self.aggregate.AggregateError):
                    self.aggregate.validate_architecture_review(invalid)

        attestation = self.aggregate.build_process_attestation(
            milestone="MSP-DOCS-E2R-AGGREGATE",
            restricted_corpus_accessed=False,
        )
        self.assertEqual(
            self.aggregate.validate_process_attestation(attestation), attestation
        )
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.validate_process_attestation({**attestation, "extra": True})
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.build_process_attestation(
                milestone="MSP-DOCS-E2R-AGGREGATE",
                restricted_corpus_accessed=True,
            )

    def test_review_basis_is_neutral_and_binds_exact_public_files(self) -> None:
        basis = self.aggregate.architecture_review_evidence_core(ROOT)
        self.assertNotIn("result", basis)
        self.assertNotIn("p0_p2_findings", basis)
        self.assertNotIn("reviewer_context", basis)
        self.assertEqual(
            basis["reviewed_commit_oid"],
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
        )
        self.assertEqual(
            basis["reviewed_tree_oid"],
            subprocess.check_output(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
            ).strip(),
        )
        self.assertEqual(
            set(basis["reviewed_files"]), set(self.aggregate.REVIEWED_PATHS)
        )
        self.assertTrue(
            {
                "multi-runtime-semantic-platform.locked/00-canonical.md",
                "multi-runtime-semantic-platform.locked/14-execution-roadmap-issues-and-gates.md",
                "multi-runtime-semantic-platform.locked/90-issue-map.md",
                "multi-runtime-semantic-platform.locked/91-milestone-map.md",
                "multi-runtime-semantic-platform.locked/92-m0-issue-matrix.yaml",
                "multi-runtime-semantic-platform.locked/99-status.md",
                "multi-runtime-semantic-platform.locked/105-ad-docs-02-amendment.md",
                "multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md",
                "scripts/validate_ad_docs_02.py",
                "tests/test_validate_ad_docs_02.py",
            }.issubset(basis["reviewed_files"])
        )
        self.assertGreater(
            basis["tracked_tree"]["entry_count"], len(basis["reviewed_files"])
        )
        self.assertRegex(basis["tracked_tree"]["manifest_sha256"], r"^[0-9a-f]{64}$")
        attestation = self.aggregate.load_canonical_json(PROCESS_ATTESTATION)
        self.assertEqual(
            self.aggregate.validate_process_attestation(attestation), attestation
        )

    def test_review_basis_binds_changes_outside_visible_reviewed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Fixture"], cwd=root, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.invalid"],
                cwd=root,
                check=True,
            )
            (root / "selected.txt").write_text("selected\n", encoding="utf-8")
            (root / "unselected.txt").write_text("first\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "first"], cwd=root, check=True)
            first = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            (root / "unselected.txt").write_text("second\n", encoding="utf-8")
            subprocess.run(["git", "commit", "-qam", "second"], cwd=root, check=True)
            second = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            with mock.patch.object(self.aggregate, "REVIEWED_PATHS", ("selected.txt",)):
                first_basis = self.aggregate.architecture_review_evidence_core(
                    root, first
                )
                second_basis = self.aggregate.architecture_review_evidence_core(
                    root, second
                )
            self.assertEqual(
                first_basis["reviewed_files"], second_basis["reviewed_files"]
            )
            self.assertNotEqual(
                first_basis["reviewed_tree_oid"], second_basis["reviewed_tree_oid"]
            )
            self.assertNotEqual(
                first_basis["tracked_tree"]["manifest_sha256"],
                second_basis["tracked_tree"]["manifest_sha256"],
            )

    def _fixture_repository(self, root: Path) -> str:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "fixture@example.invalid"],
            cwd=root,
            check=True,
        )
        (root / "tracked.txt").write_text("committed\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()

    def test_worktree_verifier_rejects_extra_tracked_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            commit = self._fixture_repository(root)
            (root / "extra.txt").write_text("staged only\n", encoding="utf-8")
            subprocess.run(["git", "add", "extra.txt"], cwd=root, check=True)
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate.verify_worktree_matches_tree(root, commit)

    def test_worktree_verifier_rejects_mode_only_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            commit = self._fixture_repository(root)
            (root / "tracked.txt").chmod(0o755)
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate.verify_worktree_matches_tree(root, commit)

    def test_worktree_verifier_rejects_all_untracked_paths(self) -> None:
        for relative, ignored in (("extra.txt", False), ("ignored.tmp", True)):
            with self.subTest(relative=relative, ignored=ignored):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary) / "repo"
                    root.mkdir()
                    commit = self._fixture_repository(root)
                    if ignored:
                        (root / ".git" / "info" / "exclude").write_text(
                            "ignored.tmp\n", encoding="utf-8"
                        )
                    (root / relative).write_text("untracked\n", encoding="utf-8")
                    with self.assertRaises(self.aggregate.AggregateError):
                        self.aggregate.verify_worktree_matches_tree(root, commit)

    def test_cli_hardens_import_path_against_untracked_stdlib_shadows(self) -> None:
        for shadow in ("json.py", "hashlib.py"):
            with self.subTest(shadow=shadow):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    scripts = root / "scripts"
                    scripts.mkdir()
                    implementation = scripts / IMPLEMENTATION.name
                    implementation.write_bytes(IMPLEMENTATION.read_bytes())
                    (scripts / shadow).write_text(
                        "raise RuntimeError('untracked shadow imported')\n",
                        encoding="utf-8",
                    )
                    completed = subprocess.run(
                        [sys.executable, str(implementation), "--help"],
                        cwd=root,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_mint_cli_always_constructs_live_observations(self) -> None:
        live = object()
        argv = [
            "mint",
            "--platform-envelope",
            "platform.json",
            "--publish-envelope",
            "publish.json",
            "--architecture-review",
            "review.json",
            "--process-attestation",
            "attestation.json",
            "--clean-repository",
            self.aggregate.CLEAN_REPOSITORY,
            "--clean-base",
            self.aggregate.CLEAN_BASE,
            "--clean-root",
            ".",
            "--platform-root",
            ".",
            "--publish-root",
            ".",
            "--root",
            ".",
            "--repository",
            self.aggregate.AGGREGATE_REPOSITORY,
            "--pr",
            "64",
            "--base-oid",
            "0" * 40,
            "--head-oid",
            "1" * 40,
            "--merge-oid",
            "2" * 40,
            "--tree-oid",
            "3" * 40,
            "--observation-source",
            "github.pull-request.merged-at",
        ]
        with (
            mock.patch.object(self.aggregate, "_reject_untracked_files"),
            mock.patch.object(
                self.aggregate, "GitHubLiveObservations", return_value=live
            ) as factory,
            mock.patch.object(
                self.aggregate,
                "_validated_cli_inputs",
                side_effect=self.aggregate.AggregateError("stop"),
            ) as validate,
        ):
            with self.assertRaisesRegex(self.aggregate.AggregateError, "stop"):
                self.aggregate.main(argv)
        factory.assert_called_once_with()
        self.assertIs(validate.call_args.args[1], live)

    def test_canonical_json_never_serializes_nonfinite_numbers(self) -> None:
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.completion_token({"invalid": float("nan")})
        encoded = json.dumps({"ascii": "ok"}, separators=(",", ":"), sort_keys=True)
        self.assertEqual(encoded.encode("ascii"), b'{"ascii":"ok"}')


class AggregateLiveDefenseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aggregate = load_implementation()

    def _git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    def _fixture_squash_repository(
        self, root: Path, repository: str
    ) -> tuple[dict[str, object], str]:
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "fixture@example.invalid"],
            cwd=root,
            check=True,
        )
        tracked = root / "tracked.txt"
        tracked.write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
        base_oid = self._git(root, "rev-parse", "HEAD")
        base_tree = self._git(root, "rev-parse", "HEAD^{tree}")

        subprocess.run(["git", "checkout", "-qb", "feature"], cwd=root, check=True)
        tracked.write_text("squashed feature\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-qam", "feature"], cwd=root, check=True)
        head_oid = self._git(root, "rev-parse", "HEAD")
        tree_oid = self._git(root, "rev-parse", "HEAD^{tree}")
        subprocess.run(["git", "checkout", "-q", "main"], cwd=root, check=True)
        merge_oid = self._git(
            root, "commit-tree", tree_oid, "-p", base_oid, "-m", "squash"
        )
        subprocess.run(
            ["git", "reset", "--hard", "-q", merge_oid], cwd=root, check=True
        )
        subprocess.run(
            ["git", "remote", "add", "origin", f"https://github.com/{repository}.git"],
            cwd=root,
            check=True,
        )
        return {
            "base_oid": base_oid,
            "head_oid": head_oid,
            "merge_oid": merge_oid,
            "pr": 7,
            "repository": repository,
            "tree_oid": tree_oid,
        }, base_tree

    def _pull(self, identity: dict[str, object]) -> dict[str, object]:
        repository = identity["repository"]
        pr = identity["pr"]
        return {
            "base": {
                "ref": "main",
                "repo": {"full_name": repository},
                "sha": identity["base_oid"],
            },
            "head": {
                "ref": "feature",
                "repo": {"full_name": repository},
                "sha": identity["head_oid"],
            },
            "merge_commit_sha": identity["merge_oid"],
            "merged": True,
            "merged_at": "2026-07-13T20:00:00Z",
            "number": pr,
            "state": "closed",
            "url": f"https://api.github.com/repos/{repository}/pulls/{pr}",
        }

    def _pull_observations(self, identity: dict[str, object]) -> FixtureObservations:
        repository = str(identity["repository"])
        pr = int(identity["pr"])
        return FixtureObservations(
            self.aggregate.AggregateError,
            pulls={(repository, pr): self._pull(identity)},
            refs={
                (repository, f"refs/pull/{pr}/head"): str(identity["head_oid"]),
                (repository, "refs/heads/main"): str(identity["merge_oid"]),
            },
        )

    def _review_record(self) -> tuple[dict[str, object], str]:
        basis = self.aggregate.architecture_review_evidence_core(ROOT)
        basis_sha256 = self.aggregate._digest(basis)
        output = {"p0_p2_findings": [], "result": "pass"}
        body = json.dumps(
            {"review_basis_sha256": basis_sha256, "review_output": output},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        output_sha256 = hashlib.sha256(body.encode("ascii")).hexdigest()
        return {
            "review_basis": basis,
            "review_basis_sha256": basis_sha256,
            "review_comment": {
                "author": "d3vi1",
                "body_sha256": output_sha256,
                "comment_id": 12345,
                "issue": 64,
                "repository": "Project-Helianthus/helianthus-execution-plans",
            },
            "review_output": output,
            "review_output_sha256": self.aggregate._digest(output),
            "schema": "helianthus.aggregate-architecture-review",
            "version": 4,
        }, body

    def test_review_record_recomputes_output_and_rejects_asserted_reviewer_metadata(
        self,
    ) -> None:
        record, _ = self._review_record()
        projection = self.aggregate.validate_architecture_review_record(record, ROOT)
        self.assertEqual(projection["result"], "pass")
        self.assertNotIn("reviewer_model", record)
        self.assertNotIn("reviewer_agent_id", record)
        for invalid in (
            {**record, "review_output_sha256": "0" * 64},
            {**record, "reviewer_model": "asserted-model"},
            {
                **record,
                "review_comment": {**record["review_comment"], "body_sha256": "0" * 64},
            },
            {
                **record,
                "review_comment": {**record["review_comment"], "author": "review-bot"},
            },
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(self.aggregate.AggregateError):
                    self.aggregate.validate_architecture_review_record(invalid, ROOT)

    def test_mint_review_binding_requires_live_comment_identity_author_and_body(
        self,
    ) -> None:
        record, body = self._review_record()
        binding = record["review_comment"]
        key = (binding["repository"], binding["issue"], binding["comment_id"])
        comment = {
            "body": body,
            "id": binding["comment_id"],
            "issue_url": f"https://api.github.com/repos/{binding['repository']}/issues/{binding['issue']}",
            "url": f"https://api.github.com/repos/{binding['repository']}/issues/comments/{binding['comment_id']}",
            "author_association": "OWNER",
            "user": {"login": binding["author"]},
        }
        observations = FixtureObservations(
            self.aggregate.AggregateError, comments={key: comment}
        )
        self.assertEqual(
            self.aggregate.verify_architecture_review_comment(
                record, ROOT, observations
            )["result"],
            "pass",
        )
        mutations = (
            lambda item: item.__setitem__("body", body + "\n"),
            lambda item: item.__setitem__("id", binding["comment_id"] + 1),
            lambda item: item["user"].__setitem__("login", "different-reviewer"),
            lambda item: item.__setitem__("author_association", "COLLABORATOR"),
            lambda item: item.__setitem__("issue_url", item["issue_url"] + "0"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                changed = copy.deepcopy(comment)
                mutate(changed)
                invalid = FixtureObservations(
                    self.aggregate.AggregateError, comments={key: changed}
                )
                with self.assertRaises(self.aggregate.AggregateError):
                    self.aggregate.verify_architecture_review_comment(
                        record, ROOT, invalid
                    )
        member = copy.deepcopy(comment)
        member["author_association"] = "MEMBER"
        self.assertEqual(
            self.aggregate.verify_architecture_review_comment(
                record,
                ROOT,
                FixtureObservations(
                    self.aggregate.AggregateError, comments={key: member}
                ),
            )["result"],
            "pass",
        )
        wrong_basis_body = json.dumps(
            {"review_basis_sha256": "0" * 64, "review_output": record["review_output"]},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        wrong_basis = copy.deepcopy(comment)
        wrong_basis["body"] = wrong_basis_body
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.verify_architecture_review_comment(
                record,
                ROOT,
                FixtureObservations(
                    self.aggregate.AggregateError, comments={key: wrong_basis}
                ),
            )
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.verify_architecture_review_comment(
                record, ROOT, FixtureObservations(self.aggregate.AggregateError)
            )

    def test_reviewed_commit_must_be_ancestor_with_exact_record_only_delta(
        self,
    ) -> None:
        review_path = self.aggregate.ARCHITECTURE_REVIEW_PATH
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "feature"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Fixture"], cwd=root, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.invalid"],
                cwd=root,
                check=True,
            )
            (root / "tracked.txt").write_text("reviewed\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "reviewed"], cwd=root, check=True)
            reviewed_commit = self._git(root, "rev-parse", "HEAD")
            with mock.patch.object(self.aggregate, "REVIEWED_PATHS", ("tracked.txt",)):
                basis = self.aggregate.architecture_review_evidence_core(
                    root, reviewed_commit
                )

            record = root / review_path
            record.parent.mkdir(parents=True)
            record.write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "add", review_path], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "review record"], cwd=root, check=True
            )
            head = self._git(root, "rev-parse", "HEAD")
            self.aggregate._verify_reviewed_tree_delta(root, basis, head)

            (root / "tracked.txt").write_text(
                "changed after review\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "commit", "-qam", "unreviewed change"], cwd=root, check=True
            )
            extra_delta = self._git(root, "rev-parse", "HEAD")
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate._verify_reviewed_tree_delta(root, basis, extra_delta)

            reviewed_tree = self._git(root, "rev-parse", f"{reviewed_commit}^{{tree}}")
            unrelated = self._git(
                root,
                "commit-tree",
                reviewed_tree,
                "-m",
                "same tree without reviewed ancestry",
            )
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate._verify_reviewed_tree_delta(root, basis, unrelated)

    def test_live_pull_replay_rejects_nonexistent_or_fabricated_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            identity, _ = self._fixture_squash_repository(
                root, "Project-Helianthus/fixture-repository"
            )
            observations = self._pull_observations(identity)
            self.assertEqual(
                self.aggregate._verify_live_pull_objects(
                    root, identity, observations, category="fixture-live-pr"
                ),
                identity["merge_oid"],
            )
            for field, value in (
                ("state", "open"),
                ("merged", False),
                ("merge_commit_sha", "f" * 40),
                ("number", 8),
            ):
                with self.subTest(field=field):
                    pull = self._pull(identity)
                    pull[field] = value
                    invalid = self._pull_observations(identity)
                    invalid.pulls[
                        (str(identity["repository"]), int(identity["pr"]))
                    ] = pull
                    with self.assertRaises(self.aggregate.AggregateError):
                        self.aggregate._verify_live_pull_objects(
                            root, identity, invalid, category="fixture-live-pr"
                        )
            for side in ("base", "head"):
                with self.subTest(side=side):
                    pull = self._pull(identity)
                    pull[side]["sha"] = "f" * 40
                    invalid = self._pull_observations(identity)
                    invalid.pulls[
                        (str(identity["repository"]), int(identity["pr"]))
                    ] = pull
                    with self.assertRaises(self.aggregate.AggregateError):
                        self.aggregate._verify_live_pull_objects(
                            root, identity, invalid, category="fixture-live-pr"
                        )
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate._verify_live_pull_objects(
                    root,
                    identity,
                    FixtureObservations(self.aggregate.AggregateError),
                    category="fixture-live-pr",
                )

    def test_live_pull_replay_enforces_exact_head_ref_and_squash_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            identity, base_tree = self._fixture_squash_repository(
                root, "Project-Helianthus/fixture-repository"
            )
            wrong_head = self._pull_observations(identity)
            wrong_head.refs[(str(identity["repository"]), "refs/pull/7/head")] = str(
                identity["base_oid"]
            )
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate._verify_live_pull_objects(
                    root, identity, wrong_head, category="fixture-live-pr"
                )

            two_parent = self._git(
                root,
                "commit-tree",
                str(identity["tree_oid"]),
                "-p",
                str(identity["base_oid"]),
                "-p",
                str(identity["head_oid"]),
                "-m",
                "not a squash",
            )
            non_squash = {**identity, "merge_oid": two_parent}
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate._verify_live_pull_objects(
                    root,
                    non_squash,
                    self._pull_observations(non_squash),
                    category="fixture-live-pr",
                )

            wrong_tree_merge = self._git(
                root,
                "commit-tree",
                base_tree,
                "-p",
                str(identity["base_oid"]),
                "-m",
                "wrong tree",
            )
            wrong_tree = {
                **identity,
                "merge_oid": wrong_tree_merge,
                "tree_oid": base_tree,
            }
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate._verify_live_pull_objects(
                    root,
                    wrong_tree,
                    self._pull_observations(wrong_tree),
                    category="fixture-live-pr",
                )

    def test_clean_base_uses_live_main_and_fails_offline_or_stale(self) -> None:
        repository = "Project-Helianthus/fixture-repository"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            identity, _ = self._fixture_squash_repository(root, repository)
            subprocess.run(
                [
                    "git",
                    "update-ref",
                    "refs/remotes/origin/main",
                    str(identity["head_oid"]),
                ],
                cwd=root,
                check=True,
            )
            with (
                mock.patch.object(self.aggregate, "CLEAN_REPOSITORY", repository),
                mock.patch.object(self.aggregate, "CLEAN_BASE", identity["merge_oid"]),
            ):
                live = FixtureObservations(
                    self.aggregate.AggregateError,
                    refs={(repository, "refs/heads/main"): str(identity["merge_oid"])},
                )
                self.aggregate.verify_clean_base(
                    root, repository, str(identity["merge_oid"]), live
                )
                stale = FixtureObservations(
                    self.aggregate.AggregateError,
                    refs={(repository, "refs/heads/main"): str(identity["head_oid"])},
                )
                with self.assertRaises(self.aggregate.AggregateError):
                    self.aggregate.verify_clean_base(
                        root, repository, str(identity["merge_oid"]), stale
                    )
                with self.assertRaises(self.aggregate.AggregateError):
                    self.aggregate.verify_clean_base(
                        root,
                        repository,
                        str(identity["merge_oid"]),
                        FixtureObservations(self.aggregate.AggregateError),
                    )
            missing_oid = "f" * 40
            with (
                mock.patch.object(self.aggregate, "CLEAN_REPOSITORY", repository),
                mock.patch.object(self.aggregate, "CLEAN_BASE", missing_oid),
            ):
                missing = FixtureObservations(
                    self.aggregate.AggregateError,
                    refs={(repository, "refs/heads/main"): missing_oid},
                )
                with self.assertRaises(self.aggregate.AggregateError):
                    self.aggregate.verify_clean_base(
                        root, repository, missing_oid, missing
                    )

    def test_aggregate_mint_verifier_requires_live_merged_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            identity, _ = self._fixture_squash_repository(
                root, "Project-Helianthus/helianthus-execution-plans"
            )
            reviewed_commit = str(identity["head_oid"])
            with mock.patch.object(self.aggregate, "REVIEWED_PATHS", ("tracked.txt",)):
                review_basis = self.aggregate.architecture_review_evidence_core(
                    root, reviewed_commit
                )
            subprocess.run(["git", "checkout", "-q", "feature"], cwd=root, check=True)
            review_record = root / self.aggregate.ARCHITECTURE_REVIEW_PATH
            review_record.parent.mkdir(parents=True)
            review_record.write_text("{}\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", self.aggregate.ARCHITECTURE_REVIEW_PATH],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-qm", "review record"], cwd=root, check=True
            )
            head_oid = self._git(root, "rev-parse", "HEAD")
            tree_oid = self._git(root, "rev-parse", "HEAD^{tree}")
            merge_oid = self._git(
                root,
                "commit-tree",
                tree_oid,
                "-p",
                str(identity["base_oid"]),
                "-m",
                "squash with review record",
            )
            subprocess.run(["git", "checkout", "-q", "main"], cwd=root, check=True)
            subprocess.run(
                ["git", "reset", "--hard", "-q", merge_oid], cwd=root, check=True
            )
            identity = {
                **identity,
                "head_oid": head_oid,
                "merge_oid": merge_oid,
                "tree_oid": tree_oid,
            }
            arguments = {
                **identity,
                "observation_source": "github.pull-request.merged-at",
                "review_basis": review_basis,
            }
            self.aggregate.verify_aggregate_repository(
                root,
                **arguments,
                observations=self._pull_observations(identity),
            )
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate.verify_aggregate_repository(
                    root,
                    **arguments,
                    observations=FixtureObservations(self.aggregate.AggregateError),
                )
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate.verify_aggregate_repository(
                    root,
                    **{**arguments, "observation_source": "local.fixture"},
                    observations=self._pull_observations(identity),
                )


if __name__ == "__main__":
    unittest.main()
