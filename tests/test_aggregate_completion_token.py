from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "scripts" / "aggregate_completion_token.py"
REVIEW_RECORD = (
    ROOT
    / "multi-runtime-semantic-platform.locked"
    / "108-msp-docs-e2r-aggregate-architecture-review.json"
)
PROCESS_ATTESTATION = (
    ROOT
    / "multi-runtime-semantic-platform.locked"
    / "109-msp-docs-e2r-aggregate-process-attestation.json"
)


def load_implementation() -> object:
    spec = importlib.util.spec_from_file_location("aggregate_completion_token", IMPLEMENTATION)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load AGGREGATE implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AggregateDefenseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aggregate = load_implementation()

    def test_canonical_loader_rejects_duplicate_noncanonical_and_nonfinite_json(self) -> None:
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
        self.assertEqual(self.aggregate.validate_process_attestation(attestation), attestation)
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.validate_process_attestation({**attestation, "extra": True})
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.build_process_attestation(
                milestone="MSP-DOCS-E2R-AGGREGATE",
                restricted_corpus_accessed=True,
            )

    def test_repository_review_record_binds_exact_public_files(self) -> None:
        record = self.aggregate.load_canonical_json(REVIEW_RECORD)
        projection = self.aggregate.validate_architecture_review_record(record, ROOT)
        self.assertEqual(projection["result"], "pass")
        self.assertEqual(projection["p0_p2_findings"], [])
        self.assertEqual(projection["evidence_sha256"], record["evidence_core_sha256"])
        attestation = self.aggregate.load_canonical_json(PROCESS_ATTESTATION)
        self.assertEqual(self.aggregate.validate_process_attestation(attestation), attestation)

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

    def test_canonical_json_never_serializes_nonfinite_numbers(self) -> None:
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.completion_token({"invalid": float("nan")})
        encoded = json.dumps({"ascii": "ok"}, separators=(",", ":"), sort_keys=True)
        self.assertEqual(encoded.encode("ascii"), b'{"ascii":"ok"}')


if __name__ == "__main__":
    unittest.main()
