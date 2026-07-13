from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "scripts" / "aggregate_completion_token.py"
FIXTURES = ROOT / "tests" / "fixtures" / "msp_docs_e2r_aggregate"
PLATFORM_FIXTURE = FIXTURES / "platform_b_completion_envelope.json"
PUBLISH_FIXTURE = FIXTURES / "publish_completion_envelope.json"

PLATFORM_TOKEN = "0b695b603f19dff35b857ddf47e03fe0ae02ac39ca89c353de8482872fd8c3de"
PUBLISH_TOKEN = "681cace127dcfc7359ca811624503c395bfb68c227e1fdc5b2608bae61735d91"
CLEAN_BASE = "0e58327dfdb86ef243a19e18d590564813feaa00"
AGGREGATE_REPOSITORY = "Project-Helianthus/helianthus-execution-plans"
CLEAN_REPOSITORY = "Project-Helianthus/helianthus-eebusreg"

EXACT_MEMBERS = [
    "cross-runtime-platform-contracts",
    "eebus-api-v1",
    "eebus-architecture",
    "eebus-protocol",
    "platform-cross-runtime-envelope",
    "platform-hash-auth-binding",
    "platform-ownership-validation",
    "platform-promotion-consumer-contract",
    "platform-shared-registry-boundary",
]
EXPECTED_IDENTITIES = {
    "platform": {
        "producer_id": "MSP-DOCS-E2R-PLATFORM",
        "consumer_id": "MSP-DOCS-E2R-PUBLISH",
        "repository": "Project-Helianthus/helianthus-docs-ebus",
        "pr": 347,
        "base_oid": "b245469c30752f06a49bb567b9a4680431774d0d",
        "head_oid": "7b8d14b010da2d67ec79c65cad98b9951c106e7b",
        "merge_oid": "8872f65b888048db001bc640ae04a4f460ee8db1",
        "tree_oid": "093e5195a850273c4d57ffc68e13d0b7f9f76e5a",
        "evidence_core_sha256": "5a5a814ffb6280b145e571a2ef79a8986072afc8aab2c9500ac20b6b530ea0c5",
        "prior_token_digest": "cf6a48f670555d47da79c27fba55bd402eacfb7cc7eefdabe6410201de65c692",
        "observation_source": "github.pull-request.merged-at",
    },
    "publish": {
        "producer_id": "MSP-DOCS-E2R-PUBLISH",
        "consumer_id": "MSP-DOCS-E2R-AGGREGATE",
        "repository": "Project-Helianthus/helianthus-docs-eebus",
        "pr": 11,
        "base_oid": "62e4c2f2022c22f5129db923079268aafdc5617b",
        "head_oid": "7a618cd64361a65521e0fbe0e04ae23b315ca173",
        "merge_oid": "9fc4b2a86424ac00075cf3bd3510918c3f9cefaf",
        "tree_oid": "9fca9d8307e7d3d69a9ea7b746088f6abe9bd2e9",
        "evidence_core_sha256": "2168312730663707087486c5e52dc8c26181a6fb51a53eb2c8add9fb4747133a",
        "prior_token_digest": PLATFORM_TOKEN,
        "observation_source": "github.pull-request.merged-at",
    },
}
AGGREGATE_IDENTITY = {
    "repository": AGGREGATE_REPOSITORY,
    "pr": 999,
    "base_oid": "1" * 40,
    "head_oid": "2" * 40,
    "merge_oid": "3" * 40,
    "tree_oid": "4" * 40,
    "observation_source": "test.fixture",
}
REVIEW = {
    "result": "pass",
    "p0_p2_findings": [],
    "evidence_sha256": "5" * 64,
}


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def output_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value) + b"\n").hexdigest()


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_fixture(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(document, dict):
        raise TypeError(f"{path.name} must contain one JSON object")
    return document


def load_implementation() -> object:
    spec = importlib.util.spec_from_file_location("aggregate_completion_token", IMPLEMENTATION)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load AGGREGATE implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicAggregateFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = load_fixture(PLATFORM_FIXTURE)
        self.publish = load_fixture(PUBLISH_FIXTURE)

    def test_public_envelopes_are_byte_canonical_and_recompute_exact_tokens(self) -> None:
        # Preserve each producer's accepted public digest convention exactly.
        for path, envelope, expected_token, token_has_newline in (
            (PLATFORM_FIXTURE, self.platform, PLATFORM_TOKEN, False),
            (PUBLISH_FIXTURE, self.publish, PUBLISH_TOKEN, True),
        ):
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), canonical_json(envelope) + b"\n")
                measured = output_digest(envelope) if token_has_newline else digest(envelope)
                self.assertEqual(measured, expected_token)
                self.assertEqual(
                    digest(envelope["evidence_core"]),
                    envelope["evidence_core_sha256"],
                )

    def test_public_envelopes_bind_exact_identity_and_prior_token_chain(self) -> None:
        for name, envelope in (("platform", self.platform), ("publish", self.publish)):
            with self.subTest(envelope=name):
                self.assertEqual(envelope["schema_version"], 2)
                for field, expected in EXPECTED_IDENTITIES[name].items():
                    self.assertEqual(envelope[field], expected)
                    if field != "evidence_core_sha256":
                        self.assertEqual(envelope["evidence_core"][field], expected)
        self.assertEqual(self.publish["prior_token_digest"], digest(self.platform))
        self.assertEqual(
            self.publish["evidence_core"]["publication_evidence"]["platform_contract"]
            ["completion_proof_sha256"],
            digest(self.platform),
        )

    def test_publication_v2_membership_and_candidate_isolation_are_exact(self) -> None:
        platform_core = self.platform["evidence_core"]
        publication = self.publish["evidence_core"]["publication_evidence"]
        contract = publication["platform_contract"]
        self.assertEqual(platform_core["manifest"]["version"], 2)
        self.assertEqual(platform_core["candidate_inventory"], [])
        self.assertEqual(contract["candidate_inventory"], [])
        self.assertEqual(platform_core["exact_memberships"], {"canonical": EXACT_MEMBERS})
        self.assertEqual(contract["exact_memberships"], {"canonical": EXACT_MEMBERS})
        self.assertEqual(platform_core["eligible_channels"], contract["eligible_channels"])
        self.assertEqual(platform_core["channel_registry"], contract["channel_registry"])
        self.assertEqual(
            set(platform_core["publisher_blobs"]),
            {
                "cross-runtime-platform-contracts",
                "platform-cross-runtime-envelope",
                "platform-hash-auth-binding",
                "platform-ownership-validation",
                "platform-promotion-consumer-contract",
                "platform-shared-registry-boundary",
            },
        )

    def test_publication_evidence_is_hermetic_and_recomputes_exactly(self) -> None:
        publish_core = self.publish["evidence_core"]
        publication = publish_core["publication_evidence"]
        self.assertEqual(digest(publication), publish_core["publication_evidence_sha256"])
        self.assertEqual(
            publication["source"],
            {
                "commit": EXPECTED_IDENTITIES["publish"]["merge_oid"],
                "repository": EXPECTED_IDENTITIES["publish"]["repository"],
                "verification": "git_object",
            },
        )
        self.assertEqual(
            publication["platform_contract"]["source_merge"],
            EXPECTED_IDENTITIES["platform"]["merge_oid"],
        )
        self.assertEqual(
            publication["platform_contract"]["source_manifest_sha256"],
            self.platform["evidence_core"]["manifest"]["sha256"],
        )
        artifact_members = {tuple(item["member_paths"]) for item in publication["artifacts"]}
        self.assertEqual(
            artifact_members,
            {("api/api-surface-v1.md", "architecture/README.md", "protocols/ship-spine-overview.md")},
        )


class AggregateImplementationRedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = load_fixture(PLATFORM_FIXTURE)
        self.publish = load_fixture(PUBLISH_FIXTURE)
        if self._testMethodName != "test_aggregate_implementation_exists" and not IMPLEMENTATION.is_file():
            self.skipTest("AGGREGATE implementation not present yet")
        self.aggregate = load_implementation() if IMPLEMENTATION.is_file() else None

    def assert_rejected(self, platform: dict[str, object], publish: dict[str, object]) -> None:
        assert self.aggregate is not None
        with self.assertRaises(self.aggregate.AggregateError):
            self.aggregate.verify_completion_envelopes(platform, publish)

    def build_envelope(self, *, clean_base: str = CLEAN_BASE) -> dict[str, object]:
        assert self.aggregate is not None
        return self.aggregate.build_completion_envelope(
            platform_envelope=copy.deepcopy(self.platform),
            publish_envelope=copy.deepcopy(self.publish),
            clean_repository=CLEAN_REPOSITORY,
            clean_base=clean_base,
            architecture_review=copy.deepcopy(REVIEW),
            **AGGREGATE_IDENTITY,
        )

    def test_aggregate_implementation_exists(self) -> None:
        self.assertTrue(
            IMPLEMENTATION.is_file(),
            "MSP-DOCS-E2R-AGGREGATE implementation missing: expected scripts/aggregate_completion_token.py",
        )

    def test_accepts_and_independently_recomputes_only_the_exact_public_envelopes(self) -> None:
        assert self.aggregate is not None
        verified = self.aggregate.verify_completion_envelopes(self.platform, self.publish)
        self.assertEqual(verified["platform_token_digest"], PLATFORM_TOKEN)
        self.assertEqual(verified["publish_token_digest"], PUBLISH_TOKEN)
        self.assertEqual(verified["prior_token_digest"], PUBLISH_TOKEN)

    def test_rejects_identity_evidence_and_prior_chain_drift(self) -> None:
        identity_fields = (
            "producer_id",
            "consumer_id",
            "repository",
            "pr",
            "base_oid",
            "head_oid",
            "merge_oid",
            "tree_oid",
            "evidence_core_sha256",
            "prior_token_digest",
            "observation_source",
        )
        for name, original in (("platform", self.platform), ("publish", self.publish)):
            for field in identity_fields:
                with self.subTest(envelope=name, field=field):
                    platform = copy.deepcopy(self.platform)
                    publish = copy.deepcopy(self.publish)
                    envelope = platform if name == "platform" else publish
                    value = envelope[field]
                    envelope[field] = value + 1 if isinstance(value, int) else "f" * len(value)
                    self.assert_rejected(platform, publish)

    def test_rejects_replay_moving_refs_and_wrong_repositories(self) -> None:
        self.assert_rejected(copy.deepcopy(self.publish), copy.deepcopy(self.publish))
        self.assert_rejected(copy.deepcopy(self.platform), copy.deepcopy(self.platform))
        for name, field, value in (
            ("platform", "merge_oid", "refs/heads/main"),
            ("publish", "head_oid", "main"),
            ("platform", "repository", "Project-Helianthus/helianthus-docs-eebus"),
            ("publish", "repository", "Project-Helianthus/helianthus-docs-ebus"),
        ):
            with self.subTest(envelope=name, field=field):
                platform = copy.deepcopy(self.platform)
                publish = copy.deepcopy(self.publish)
                target = platform if name == "platform" else publish
                target[field] = value
                self.assert_rejected(platform, publish)

    def test_rejects_token_schema_membership_candidate_and_replay_drift(self) -> None:
        mutations = (
            lambda p, q: p.__setitem__("schema_version", 3),
            lambda p, q: q["evidence_core"].__setitem__("evaluated_at", "2026-07-13T18:40:04Z"),
            lambda p, q: p["evidence_core"]["exact_memberships"]["canonical"].pop(),
            lambda p, q: q["evidence_core"]["publication_evidence"]["platform_contract"]
            ["exact_memberships"]["canonical"].append("candidate-leak"),
            lambda p, q: p["evidence_core"]["candidate_inventory"].append("candidate-leak"),
            lambda p, q: q["evidence_core"]["publication_evidence"]["platform_contract"]
            ["candidate_inventory"].append("candidate-leak"),
            lambda p, q: q["evidence_core"]["publication_evidence"]["source"].__setitem__(
                "verification", "worktree"
            ),
            lambda p, q: q["evidence_core"]["publication_evidence"]["artifacts"][0]
            ["member_paths"].append("api/_candidate/runtime-reference.md"),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                platform = copy.deepcopy(self.platform)
                publish = copy.deepcopy(self.publish)
                mutate(platform, publish)
                self.assert_rejected(platform, publish)

    def test_semantic_publication_verification_rejects_rehashed_membership_or_candidate_drift(self) -> None:
        assert self.aggregate is not None
        for mutate in (
            lambda p, q: p["evidence_core"]["exact_memberships"]["canonical"].pop(),
            lambda p, q: p["evidence_core"]["candidate_inventory"].append("candidate-leak"),
            lambda p, q: q["evidence_core"]["publication_evidence"]["platform_contract"]
            ["eligible_channels"].pop("platform-hash-auth-binding"),
            lambda p, q: q["evidence_core"]["publication_evidence"]["source"].__setitem__(
                "verification", "ambient_checkout"
            ),
        ):
            with self.subTest(mutation=mutate):
                platform = copy.deepcopy(self.platform)
                publish = copy.deepcopy(self.publish)
                mutate(platform, publish)
                publish_core = publish["evidence_core"]
                publish_core["publication_evidence_sha256"] = digest(
                    publish_core["publication_evidence"]
                )
                platform["evidence_core_sha256"] = digest(platform["evidence_core"])
                publish["evidence_core_sha256"] = digest(publish_core)
                with self.assertRaises(self.aggregate.AggregateError):
                    self.aggregate.verify_publication_contract(platform, publish)

    def test_detects_hidden_tracked_worktree_drift_even_when_git_status_is_clean(self) -> None:
        assert self.aggregate is not None
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True
            )
            tracked = root / "tracked.txt"
            tracked.write_text("committed\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            self.aggregate.verify_worktree_matches_tree(root, commit)
            subprocess.run(
                ["git", "update-index", "--assume-unchanged", "tracked.txt"],
                cwd=root,
                check=True,
            )
            tracked.write_text("hidden drift\n", encoding="utf-8")
            status = subprocess.check_output(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=root,
                text=True,
            )
            self.assertEqual(status, "")
            with self.assertRaises(self.aggregate.AggregateError):
                self.aggregate.verify_worktree_matches_tree(root, commit)

    def test_freezes_clean_base_and_rejects_any_alternate_candidate(self) -> None:
        envelope = self.build_envelope()
        self.assertEqual(envelope["evidence_core"]["clean_repository"], CLEAN_REPOSITORY)
        self.assertEqual(envelope["evidence_core"]["clean_base"], CLEAN_BASE)
        for alternate in ("main", "0" * 40, CLEAN_BASE[:-1] + "1"):
            with self.subTest(clean_base=alternate):
                with self.assertRaises(self.aggregate.AggregateError):
                    self.build_envelope(clean_base=alternate)

    def test_restricted_corpus_process_attestation_stays_outside_technical_proof(self) -> None:
        assert self.aggregate is not None
        envelope = self.build_envelope()
        attestation = self.aggregate.build_process_attestation(
            milestone="MSP-DOCS-E2R-AGGREGATE",
            restricted_corpus_accessed=False,
        )
        self.assertEqual(
            attestation,
            {
                "distinct_from": "technical_git_object_proof",
                "milestone": "MSP-DOCS-E2R-AGGREGATE",
                "restricted_corpus_accessed": False,
                "schema": "helianthus.restricted-corpus-process-attestation",
                "version": 1,
            },
        )
        technical = canonical_json(envelope)
        self.assertNotIn(b"process_attestation", technical)
        self.assertNotIn(digest(attestation).encode("ascii"), technical)

    def test_emits_one_deterministic_completion_token_only_for_msp_docs_clean(self) -> None:
        assert self.aggregate is not None
        first = self.build_envelope()
        second = self.build_envelope()
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(first["schema_version"], 2)
        self.assertEqual(first["producer_id"], "MSP-DOCS-E2R-AGGREGATE")
        self.assertEqual(first["consumer_id"], "MSP-DOCS-CLEAN")
        self.assertEqual(first["prior_token_digest"], PUBLISH_TOKEN)
        self.assertEqual(first["evidence_core"]["architecture_review"], REVIEW)
        self.assertEqual(first["evidence_core_sha256"], digest(first["evidence_core"]))
        token = self.aggregate.completion_token(first)
        self.assertEqual(token, output_digest(first))
        self.assertEqual(token, self.aggregate.completion_token(second))
        self.assertNotIn("completion_tokens", first)
        self.assertNotIn("alternate_consumers", first)


if __name__ == "__main__":
    unittest.main()
