#!/usr/bin/env python3
"""Verify E2R remediation proofs and mint the sole CLEAN completion token."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any


AGGREGATE_REPOSITORY = "Project-Helianthus/helianthus-execution-plans"
AGGREGATE_ISSUE = 64
CLEAN_REPOSITORY = "Project-Helianthus/helianthus-eebusreg"
CLEAN_BASE = "0e58327dfdb86ef243a19e18d590564813feaa00"
PRODUCER_ID = "MSP-DOCS-E2R-AGGREGATE"
CONSUMER_ID = "MSP-DOCS-CLEAN"
PLATFORM_TOKEN = "0b695b603f19dff35b857ddf47e03fe0ae02ac39ca89c353de8482872fd8c3de"
PUBLISH_TOKEN = "681cace127dcfc7359ca811624503c395bfb68c227e1fdc5b2608bae61735d91"
OID = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
OBSERVATION_SOURCE = re.compile(r"[a-z0-9][a-z0-9._+-]*\Z")
GITHUB_LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\[bot\])?\Z")
GITHUB_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
GITHUB_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
GITHUB_API_ROOT = "https://api.github.com"
GITHUB_REMOTE_ROOT = "https://github.com"
GITHUB_RESPONSE_LIMIT = 2 * 1024 * 1024
REVIEWED_PATHS = (
    "scripts/aggregate_completion_token.py",
    "scripts/validate_plans_repo.sh",
    "tests/fixtures/msp_docs_e2r_aggregate/platform_b_completion_envelope.json",
    "tests/fixtures/msp_docs_e2r_aggregate/publish_completion_envelope.json",
    "tests/test_aggregate_completion_token.py",
    "tests/test_msp_docs_e2r_aggregate_red.py",
    "multi-runtime-semantic-platform.locked/109-msp-docs-e2r-aggregate-process-attestation.json",
)
REVIEW_SCOPE = (
    "producer_identity_and_prior_chain",
    "publication_v2_membership_and_candidate_isolation",
    "hermetic_git_object_replay",
    "aggregate_merge_tree_and_clean_base",
    "sole_clean_consumer_and_process_separation",
)

EXACT_MEMBERS = (
    "cross-runtime-platform-contracts",
    "eebus-api-v1",
    "eebus-architecture",
    "eebus-protocol",
    "platform-cross-runtime-envelope",
    "platform-hash-auth-binding",
    "platform-ownership-validation",
    "platform-promotion-consumer-contract",
    "platform-shared-registry-boundary",
)
PLATFORM_PUBLISHER_BLOBS = frozenset(
    {
        "cross-runtime-platform-contracts",
        "platform-cross-runtime-envelope",
        "platform-hash-auth-binding",
        "platform-ownership-validation",
        "platform-promotion-consumer-contract",
        "platform-shared-registry-boundary",
    }
)
PUBLIC_MEMBER_PATHS = (
    "api/api-surface-v1.md",
    "architecture/README.md",
    "protocols/ship-spine-overview.md",
)
EXPECTED_CHANNELS = {
    member: ["canonical"]
    for member in EXACT_MEMBERS
}
EXPECTED_CHANNEL_REGISTRY = {
    "canonical": {"owner": "canonical_documentation_owner", "visibility": "stable"}
}
EXPECTED_IDENTITIES: dict[str, dict[str, Any]] = {
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
ENVELOPE_KEYS = frozenset(
    {
        "base_oid",
        "consumer_id",
        "evidence_core",
        "evidence_core_sha256",
        "head_oid",
        "merge_oid",
        "observation_source",
        "pr",
        "prior_token_digest",
        "producer_id",
        "repository",
        "schema_version",
        "tree_oid",
    }
)
IDENTITY_FIELDS = (
    "producer_id",
    "consumer_id",
    "repository",
    "pr",
    "base_oid",
    "head_oid",
    "merge_oid",
    "tree_oid",
    "prior_token_digest",
    "observation_source",
)


class AggregateError(Exception):
    """Fail-closed aggregate validation error."""


class GitHubLiveObservations:
    """Read immutable review identities and exact Git refs from GitHub."""

    def _api_json(self, repository: str, suffix: str) -> dict[str, Any]:
        if GITHUB_REPOSITORY.fullmatch(repository) is None or not suffix.startswith("/"):
            raise AggregateError("aggregate-token.github-api")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "helianthus-aggregate-completion-token",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            f"{GITHUB_API_ROOT}/repos/{repository}{suffix}", headers=headers
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status != 200:
                    raise AggregateError("aggregate-token.github-api")
                raw = response.read(GITHUB_RESPONSE_LIMIT + 1)
        except AggregateError:
            raise
        except (OSError, TimeoutError, urllib.error.URLError) as exc:
            raise AggregateError("aggregate-token.github-api") from exc
        if len(raw) > GITHUB_RESPONSE_LIMIT:
            raise AggregateError("aggregate-token.github-api")
        try:
            document = json.loads(raw.decode("utf-8", errors="strict"))
        except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
            raise AggregateError("aggregate-token.github-api") from exc
        return _object(document, "aggregate-token.github-api")

    def pull_request(self, repository: str, pr: int) -> dict[str, Any]:
        if type(pr) is not int or pr <= 0:
            raise AggregateError("aggregate-token.github-pull-request")
        return self._api_json(repository, f"/pulls/{pr}")

    def issue_comment(
        self, repository: str, issue: int, comment_id: int
    ) -> dict[str, Any]:
        if type(issue) is not int or issue <= 0 or type(comment_id) is not int or comment_id <= 0:
            raise AggregateError("aggregate-token.github-review-comment")
        return self._api_json(repository, f"/issues/comments/{comment_id}")

    def fetch_ref(self, root: Path, repository: str, remote_ref: str) -> str:
        """Observe then fetch one exact canonical GitHub ref, rejecting races."""
        if (
            GITHUB_REPOSITORY.fullmatch(repository) is None
            or not remote_ref.startswith("refs/")
            or any(character.isspace() for character in remote_ref)
            or not _directory_without_symlinks(root)
            or _github_repository(str(_git(root, "remote", "get-url", "origin")))
            != repository.casefold()
        ):
            raise AggregateError("aggregate-token.github-git-ref")
        remote = f"{GITHUB_REMOTE_ROOT}/{repository}.git"
        environment = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
        observed = subprocess.run(
            ["git", "ls-remote", "--exit-code", remote, remote_ref],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        if observed.returncode != 0:
            raise AggregateError("aggregate-token.github-git-ref")
        records = [line.split("\t") for line in observed.stdout.splitlines() if line]
        if (
            len(records) != 1
            or len(records[0]) != 2
            or records[0][1] != remote_ref
            or OID.fullmatch(records[0][0]) is None
        ):
            raise AggregateError("aggregate-token.github-git-ref")
        observed_oid = records[0][0]
        fetched = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "fetch",
                "--no-tags",
                "--force",
                remote,
                remote_ref,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        if fetched.returncode != 0 or _git(root, "rev-parse", "FETCH_HEAD") != observed_oid:
            raise AggregateError("aggregate-token.github-git-ref")
        return observed_oid


def _live_observations(observations: Any | None) -> Any:
    return GitHubLiveObservations() if observations is None else observations


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise AggregateError("aggregate-token.json") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _output_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value) + b"\n").hexdigest()


def completion_token(envelope: dict[str, Any]) -> str:
    """Return the canonical newline-terminated aggregate envelope digest."""
    if not isinstance(envelope, dict):
        raise AggregateError("aggregate-token.envelope")
    return _output_digest(envelope)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise AggregateError("aggregate-token.duplicate-key")
        document[key] = value
    return document


def _reject_constant(_: str) -> None:
    raise AggregateError("aggregate-token.json-constant")


def load_canonical_json(path: Path) -> dict[str, Any]:
    """Load one unique-key JSON object whose bytes are canonical plus LF."""
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except AggregateError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise AggregateError("aggregate-token.input") from exc
    if not isinstance(document, dict) or raw != _canonical_json(document) + b"\n":
        raise AggregateError("aggregate-token.noncanonical-input")
    return document


def _object(value: Any, category: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AggregateError(category)
    return value


def _exact_keys(value: dict[str, Any], expected: frozenset[str], category: str) -> None:
    if set(value) != expected or any(not isinstance(key, str) for key in value):
        raise AggregateError(category)


def _validate_frozen_identity(name: str, envelope: dict[str, Any]) -> None:
    expected = EXPECTED_IDENTITIES[name]
    _exact_keys(envelope, ENVELOPE_KEYS, f"aggregate-token.{name}-schema")
    if type(envelope.get("schema_version")) is not int or envelope["schema_version"] != 2:
        raise AggregateError(f"aggregate-token.{name}-schema")
    for field, exact in expected.items():
        if envelope.get(field) != exact or type(envelope.get(field)) is not type(exact):
            raise AggregateError(f"aggregate-token.{name}-identity")
    for field in ("base_oid", "head_oid", "merge_oid", "tree_oid"):
        if OID.fullmatch(envelope[field]) is None:
            raise AggregateError(f"aggregate-token.{name}-object")
    if len({envelope[field] for field in ("base_oid", "head_oid", "merge_oid", "tree_oid")}) != 4:
        raise AggregateError(f"aggregate-token.{name}-replay")
    core = _object(envelope.get("evidence_core"), f"aggregate-token.{name}-evidence")
    for field in IDENTITY_FIELDS:
        if core.get(field) != envelope[field] or type(core.get(field)) is not type(envelope[field]):
            raise AggregateError(f"aggregate-token.{name}-identity")
    if core.get("result") != "pass" or type(core.get("result")) is not str:
        raise AggregateError(f"aggregate-token.{name}-result")
    if _digest(core) != envelope["evidence_core_sha256"]:
        raise AggregateError(f"aggregate-token.{name}-evidence-digest")


def verify_publication_contract(
    platform_envelope: dict[str, Any],
    publish_envelope: dict[str, Any],
) -> dict[str, Any]:
    """Verify publication-v2 membership, candidate isolation, and replay bindings."""
    platform = _object(platform_envelope, "aggregate-token.platform-envelope")
    publish = _object(publish_envelope, "aggregate-token.publish-envelope")
    _validate_frozen_identity("platform", platform)
    _validate_frozen_identity("publish", publish)

    platform_core = _object(platform["evidence_core"], "aggregate-token.platform-evidence")
    publish_core = _object(publish["evidence_core"], "aggregate-token.publish-evidence")
    manifest = _object(platform_core.get("manifest"), "aggregate-token.manifest")
    prior_manifest = _object(
        platform_core.get("prior_manifest"), "aggregate-token.prior-manifest"
    )
    if (
        manifest.get("version") != 2
        or prior_manifest.get("version") != 1
        or manifest.get("mode") != "100644"
        or prior_manifest.get("mode") != "100644"
    ):
        raise AggregateError("aggregate-token.manifest-version")
    if platform_core.get("candidate_inventory") != []:
        raise AggregateError("aggregate-token.platform-candidate")
    exact_memberships = {"canonical": list(EXACT_MEMBERS)}
    if platform_core.get("exact_memberships") != exact_memberships:
        raise AggregateError("aggregate-token.platform-membership")
    if platform_core.get("eligible_channels") != EXPECTED_CHANNELS:
        raise AggregateError("aggregate-token.platform-channels")
    if platform_core.get("channel_registry") != EXPECTED_CHANNEL_REGISTRY:
        raise AggregateError("aggregate-token.platform-registry")
    publisher_blobs = _object(
        platform_core.get("publisher_blobs"), "aggregate-token.publisher-blobs"
    )
    if set(publisher_blobs) != PLATFORM_PUBLISHER_BLOBS:
        raise AggregateError("aggregate-token.publisher-blobs")
    for blob in publisher_blobs.values():
        item = _object(blob, "aggregate-token.publisher-blob")
        if (
            set(item) != {"mode", "oid", "path", "sha256"}
            or item.get("mode") != "100644"
            or not isinstance(item.get("path"), str)
            or OID.fullmatch(str(item.get("oid"))) is None
            or DIGEST.fullmatch(str(item.get("sha256"))) is None
        ):
            raise AggregateError("aggregate-token.publisher-blob")

    publication = _object(
        publish_core.get("publication_evidence"), "aggregate-token.publication"
    )
    if _digest(publication) != publish_core.get("publication_evidence_sha256"):
        raise AggregateError("aggregate-token.publication-digest")
    expected_source = {
        "commit": EXPECTED_IDENTITIES["publish"]["merge_oid"],
        "repository": EXPECTED_IDENTITIES["publish"]["repository"],
        "verification": "git_object",
    }
    if publication.get("source") != expected_source:
        raise AggregateError("aggregate-token.publication-source")
    if (
        publication.get("schema") != "helianthus.docs-publication-evidence"
        or publication.get("version") != 1
        or publication.get("state") != "PUBLISH"
        or publication.get("milestone") != "MSP-DOCS-E2R-PUBLISH"
    ):
        raise AggregateError("aggregate-token.publication-schema")
    contract = _object(
        publication.get("platform_contract"), "aggregate-token.platform-contract"
    )
    if (
        contract.get("candidate_inventory") != []
        or contract.get("exact_memberships") != exact_memberships
        or contract.get("eligible_channels") != EXPECTED_CHANNELS
        or contract.get("channel_registry") != EXPECTED_CHANNEL_REGISTRY
        or contract.get("source_repository") != EXPECTED_IDENTITIES["platform"]["repository"]
        or contract.get("source_merge") != EXPECTED_IDENTITIES["platform"]["merge_oid"]
        or contract.get("source_manifest_path")
        != "docs/platform/manifests/eebus-doc-ownership.yaml"
        or contract.get("source_manifest_blob_mode") != manifest.get("mode")
        or contract.get("source_manifest_oid") != manifest.get("oid")
        or contract.get("source_manifest_sha256") != manifest.get("sha256")
        or contract.get("completion_proof_sha256") != PLATFORM_TOKEN
    ):
        raise AggregateError("aggregate-token.platform-contract")
    artifacts = publication.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 4:
        raise AggregateError("aggregate-token.publication-artifacts")
    expected_artifacts = {
        "release_bundle": "api/release-bundle.txt",
        "search": "api/search-index.json",
        "sitemap": "api/sitemap.xml",
        "versioned_bundle": "api/versioned-bundle.txt",
    }
    seen_channels: set[str] = set()
    for raw_artifact in artifacts:
        artifact = _object(raw_artifact, "aggregate-token.publication-artifact")
        if set(artifact) != {"channel", "member_paths", "path", "sha256"}:
            raise AggregateError("aggregate-token.publication-artifact")
        channel = artifact.get("channel")
        if (
            not isinstance(channel, str)
            or channel in seen_channels
            or expected_artifacts.get(channel) != artifact.get("path")
            or artifact.get("member_paths") != list(PUBLIC_MEMBER_PATHS)
            or DIGEST.fullmatch(str(artifact.get("sha256"))) is None
        ):
            raise AggregateError("aggregate-token.publication-artifact")
        seen_channels.add(channel)
    if seen_channels != set(expected_artifacts):
        raise AggregateError("aggregate-token.publication-artifacts")
    return {
        "candidate_inventory": [],
        "exact_memberships": exact_memberships,
        "manifest_version": 2,
        "publication_evidence_sha256": publish_core["publication_evidence_sha256"],
    }


def verify_completion_envelopes(
    platform_envelope: dict[str, Any],
    publish_envelope: dict[str, Any],
) -> dict[str, Any]:
    """Independently recompute and verify both accepted producer envelopes."""
    contract = verify_publication_contract(platform_envelope, publish_envelope)
    platform_token = _digest(platform_envelope)
    publish_token = _output_digest(publish_envelope)
    if platform_token != PLATFORM_TOKEN or publish_token != PUBLISH_TOKEN:
        raise AggregateError("aggregate-token.producer-token")
    if (
        publish_envelope.get("prior_token_digest") != platform_token
        or publish_envelope["evidence_core"].get("prior_token_digest") != platform_token
        or publish_envelope["evidence_core"]["publication_evidence"]
        ["platform_contract"].get("completion_proof_sha256") != platform_token
    ):
        raise AggregateError("aggregate-token.prior-chain")
    return {
        **contract,
        "platform_token_digest": platform_token,
        "prior_token_digest": publish_token,
        "publish_token_digest": publish_token,
    }


def validate_architecture_review(review: dict[str, Any]) -> dict[str, Any]:
    """Validate the minimal review projection embedded in technical evidence."""
    item = _object(review, "aggregate-token.architecture-review")
    _exact_keys(
        item,
        frozenset({"result", "p0_p2_findings", "evidence_sha256"}),
        "aggregate-token.architecture-review",
    )
    if (
        item.get("result") != "pass"
        or item.get("p0_p2_findings") != []
        or not isinstance(item.get("evidence_sha256"), str)
        or DIGEST.fullmatch(item["evidence_sha256"]) is None
    ):
        raise AggregateError("aggregate-token.architecture-review")
    return dict(item)


def _regular_file_identity(root: Path, relative: str) -> dict[str, str]:
    path = root / relative
    try:
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise AggregateError("aggregate-token.architecture-review-file")
        raw = path.read_bytes()
    except OSError as exc:
        raise AggregateError("aggregate-token.architecture-review-file") from exc
    return {
        "mode": "100755" if mode & 0o111 else "100644",
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def architecture_review_evidence_core(root: Path) -> dict[str, Any]:
    """Build the neutral public file/object basis a fresh review must cover."""
    return {
        "clean_base": CLEAN_BASE,
        "clean_repository": CLEAN_REPOSITORY,
        "milestone": PRODUCER_ID,
        "platform_token_digest": PLATFORM_TOKEN,
        "publish_token_digest": PUBLISH_TOKEN,
        "review_scope": list(REVIEW_SCOPE),
        "reviewed_files": {
            relative: _regular_file_identity(root, relative)
            for relative in REVIEWED_PATHS
        },
    }


def _architecture_review_record_parts(
    record: dict[str, Any], root: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Recompute a review output and its immutable comment binding."""
    item = _object(record, "aggregate-token.architecture-review-record")
    _exact_keys(
        item,
        frozenset(
            {
                "review_basis",
                "review_basis_sha256",
                "review_comment",
                "review_output",
                "review_output_sha256",
                "schema",
                "version",
            }
        ),
        "aggregate-token.architecture-review-record",
    )
    basis = _object(
        item.get("review_basis"), "aggregate-token.architecture-review-record"
    )
    review_output = _object(
        item.get("review_output"), "aggregate-token.architecture-review-record"
    )
    review_comment = _object(
        item.get("review_comment"), "aggregate-token.architecture-review-record"
    )
    expected_basis = architecture_review_evidence_core(root)
    output_sha256 = _digest(review_output)
    if (
        item.get("schema") != "helianthus.aggregate-architecture-review"
        or type(item.get("version")) is not int
        or item["version"] != 3
        or basis != expected_basis
        or not isinstance(item.get("review_basis_sha256"), str)
        or _digest(basis) != item["review_basis_sha256"]
        or set(review_output) != {"p0_p2_findings", "result"}
        or review_output.get("result") != "pass"
        or review_output.get("p0_p2_findings") != []
        or not isinstance(item.get("review_output_sha256"), str)
        or item["review_output_sha256"] != output_sha256
        or set(review_comment)
        != {"author", "body_sha256", "comment_id", "issue", "repository"}
        or review_comment.get("repository") != AGGREGATE_REPOSITORY
        or type(review_comment.get("issue")) is not int
        or review_comment["issue"] != AGGREGATE_ISSUE
        or type(review_comment.get("comment_id")) is not int
        or review_comment["comment_id"] <= 0
        or not isinstance(review_comment.get("author"), str)
        or GITHUB_LOGIN.fullmatch(review_comment["author"]) is None
        or review_comment.get("body_sha256") != output_sha256
    ):
        raise AggregateError("aggregate-token.architecture-review-record")
    projection = validate_architecture_review(
        {
            "evidence_sha256": _digest(item),
            "p0_p2_findings": review_output["p0_p2_findings"],
            "result": review_output["result"],
        }
    )
    return projection, dict(review_comment), _canonical_json(review_output).decode("ascii")


def validate_architecture_review_record(
    record: dict[str, Any], root: Path
) -> dict[str, Any]:
    """Recompute the supplied fresh-review output and token projection."""
    projection, _, _ = _architecture_review_record_parts(record, root)
    return projection


def verify_architecture_review_comment(
    record: dict[str, Any], root: Path, observations: Any | None = None
) -> dict[str, Any]:
    """Bind a valid review output to its live GitHub issue comment."""
    projection, binding, expected_body = _architecture_review_record_parts(record, root)
    live = _live_observations(observations).issue_comment(
        binding["repository"], binding["issue"], binding["comment_id"]
    )
    user = _object(live.get("user"), "aggregate-token.github-review-comment")
    body = live.get("body")
    if (
        live.get("id") != binding["comment_id"]
        or type(live.get("id")) is not int
        or live.get("url")
        != f"{GITHUB_API_ROOT}/repos/{binding['repository']}/issues/comments/{binding['comment_id']}"
        or live.get("issue_url")
        != f"{GITHUB_API_ROOT}/repos/{binding['repository']}/issues/{binding['issue']}"
        or user.get("login") != binding["author"]
        or not isinstance(body, str)
        or body != expected_body
        or hashlib.sha256(body.encode("utf-8")).hexdigest() != binding["body_sha256"]
    ):
        raise AggregateError("aggregate-token.github-review-comment")
    return projection


def build_process_attestation(
    *, milestone: str, restricted_corpus_accessed: bool
) -> dict[str, Any]:
    """Build the separate, non-technical restricted-corpus process statement."""
    if milestone != PRODUCER_ID or restricted_corpus_accessed is not False:
        raise AggregateError("aggregate-token.process-attestation")
    return {
        "distinct_from": "technical_git_object_proof",
        "milestone": PRODUCER_ID,
        "restricted_corpus_accessed": False,
        "schema": "helianthus.restricted-corpus-process-attestation",
        "version": 1,
    }


def validate_process_attestation(attestation: dict[str, Any]) -> dict[str, Any]:
    expected = build_process_attestation(
        milestone=PRODUCER_ID, restricted_corpus_accessed=False
    )
    if attestation != expected or any(
        type(attestation.get(key)) is not type(value) for key, value in expected.items()
    ):
        raise AggregateError("aggregate-token.process-attestation")
    return dict(attestation)


def _producer_record(name: str, token_digest: str) -> dict[str, Any]:
    expected = EXPECTED_IDENTITIES[name]
    return {
        **expected,
        "schema_version": 2,
        "token_digest": token_digest,
    }


def build_completion_envelope(
    *,
    platform_envelope: dict[str, Any],
    publish_envelope: dict[str, Any],
    clean_repository: str,
    clean_base: str,
    architecture_review: dict[str, Any],
    repository: str,
    pr: int,
    base_oid: str,
    head_oid: str,
    merge_oid: str,
    tree_oid: str,
    observation_source: str,
) -> dict[str, Any]:
    """Build the deterministic technical envelope authorized only for CLEAN."""
    verified = verify_completion_envelopes(platform_envelope, publish_envelope)
    review = validate_architecture_review(architecture_review)
    oids = (base_oid, head_oid, merge_oid, tree_oid)
    if (
        repository != AGGREGATE_REPOSITORY
        or type(pr) is not int
        or pr <= 0
        or any(not isinstance(oid, str) or OID.fullmatch(oid) is None for oid in oids)
        or len(set(oids)) != 4
        or not isinstance(observation_source, str)
        or OBSERVATION_SOURCE.fullmatch(observation_source) is None
        or clean_repository != CLEAN_REPOSITORY
        or clean_base != CLEAN_BASE
    ):
        raise AggregateError("aggregate-token.identity")
    evidence_core = {
        "architecture_review": review,
        "base_oid": base_oid,
        "clean_base": CLEAN_BASE,
        "clean_repository": CLEAN_REPOSITORY,
        "consumer_id": CONSUMER_ID,
        "head_oid": head_oid,
        "merge_oid": merge_oid,
        "observation_source": observation_source,
        "pr": pr,
        "prior_token_digest": verified["publish_token_digest"],
        "producer_evidence": {
            "platform": _producer_record("platform", verified["platform_token_digest"]),
            "publish": _producer_record("publish", verified["publish_token_digest"]),
        },
        "producer_id": PRODUCER_ID,
        "repository": AGGREGATE_REPOSITORY,
        "result": "pass",
        "tree_oid": tree_oid,
    }
    return {
        "base_oid": base_oid,
        "consumer_id": CONSUMER_ID,
        "evidence_core": evidence_core,
        "evidence_core_sha256": _digest(evidence_core),
        "head_oid": head_oid,
        "merge_oid": merge_oid,
        "observation_source": observation_source,
        "pr": pr,
        "prior_token_digest": verified["publish_token_digest"],
        "producer_id": PRODUCER_ID,
        "repository": AGGREGATE_REPOSITORY,
        "schema_version": 2,
        "tree_oid": tree_oid,
    }


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=not binary,
    )
    if result.returncode != 0:
        raise AggregateError("aggregate-token.git-object")
    if binary:
        return result.stdout
    return result.stdout.strip()


def _git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def _validate_live_pull_identity(
    pull: dict[str, Any], identity: dict[str, Any], category: str
) -> None:
    base = _object(pull.get("base"), category)
    head = _object(pull.get("head"), category)
    base_repo = _object(base.get("repo"), category)
    head_repo = _object(head.get("repo"), category)
    repository = identity["repository"]
    pr = identity["pr"]
    merged_at = pull.get("merged_at")
    if (
        pull.get("url") != f"{GITHUB_API_ROOT}/repos/{repository}/pulls/{pr}"
        or type(pull.get("number")) is not int
        or pull["number"] != pr
        or pull.get("state") != "closed"
        or pull.get("merged") is not True
        or not isinstance(merged_at, str)
        or GITHUB_INSTANT.fullmatch(merged_at) is None
        or pull.get("merge_commit_sha") != identity["merge_oid"]
        or base.get("ref") != "main"
        or base.get("sha") != identity["base_oid"]
        or base_repo.get("full_name") != repository
        or head.get("sha") != identity["head_oid"]
        or head_repo.get("full_name") != repository
    ):
        raise AggregateError(category)


def _verify_live_pull_objects(
    root: Path,
    identity: dict[str, Any],
    observations: Any | None = None,
    *,
    category: str,
) -> str:
    """Fetch and verify one merged squash PR against GitHub's live identity."""
    repository = identity.get("repository")
    pr = identity.get("pr")
    base_oid = identity.get("base_oid")
    head_oid = identity.get("head_oid")
    merge_oid = identity.get("merge_oid")
    tree_oid = identity.get("tree_oid")
    if (
        not isinstance(repository, str)
        or GITHUB_REPOSITORY.fullmatch(repository) is None
        or type(pr) is not int
        or pr <= 0
        or any(
            not isinstance(oid, str) or OID.fullmatch(oid) is None
            for oid in (base_oid, head_oid, merge_oid, tree_oid)
        )
        or not _directory_without_symlinks(root)
        or _github_repository(str(_git(root, "remote", "get-url", "origin")))
        != repository.casefold()
    ):
        raise AggregateError(category)

    live = _live_observations(observations)
    pull = _object(live.pull_request(repository, pr), category)
    _validate_live_pull_identity(pull, identity, category)
    observed_head = live.fetch_ref(root, repository, f"refs/pull/{pr}/head")
    observed_main = live.fetch_ref(root, repository, "refs/heads/main")
    if (
        not isinstance(observed_head, str)
        or observed_head != head_oid
        or not isinstance(observed_main, str)
        or OID.fullmatch(observed_main) is None
    ):
        raise AggregateError(category)

    for oid in (base_oid, head_oid, merge_oid):
        if _git(root, "cat-file", "-t", oid) != "commit":
            raise AggregateError(category)
    if _git(root, "cat-file", "-t", tree_oid) != "tree":
        raise AggregateError(category)
    parents = str(_git(root, "rev-list", "--parents", "-n", "1", merge_oid)).split()
    if (
        parents != [merge_oid, base_oid]
        or not _git_is_ancestor(root, base_oid, head_oid)
        or not _git_is_ancestor(root, merge_oid, observed_main)
        or _git(root, "rev-parse", f"{head_oid}^{{tree}}") != tree_oid
        or _git(root, "rev-parse", f"{merge_oid}^{{tree}}") != tree_oid
    ):
        raise AggregateError(category)
    return observed_main


def _verify_repository_object_root(
    root: Path, repository: str, merge_oid: str, tree_oid: str
) -> None:
    if (
        not _directory_without_symlinks(root)
        or _github_repository(str(_git(root, "remote", "get-url", "origin")))
        != repository.casefold()
        or _git(root, "cat-file", "-t", merge_oid) != "commit"
        or _git(root, "rev-parse", f"{merge_oid}^{{tree}}") != tree_oid
    ):
        raise AggregateError("aggregate-token.producer-git-object")


def _git_blob_identity(
    root: Path, commit: str, path: str
) -> tuple[dict[str, str], bytes]:
    listing = str(_git(root, "ls-tree", commit, "--", path))
    if "\n" in listing or "\t" not in listing:
        raise AggregateError("aggregate-token.producer-git-object")
    metadata, listed_path = listing.split("\t", 1)
    fields = metadata.split()
    if listed_path != path or len(fields) != 3:
        raise AggregateError("aggregate-token.producer-git-object")
    mode, object_type, oid = fields
    if mode not in {"100644", "100755"} or object_type != "blob" or OID.fullmatch(oid) is None:
        raise AggregateError("aggregate-token.producer-git-object")
    raw = _git(root, "cat-file", "blob", oid, binary=True)
    assert isinstance(raw, bytes)
    return {
        "mode": mode,
        "oid": oid,
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }, raw


def verify_producer_git_objects(
    platform_root: Path,
    publish_root: Path,
    platform_envelope: dict[str, Any],
    publish_envelope: dict[str, Any],
    observations: Any | None = None,
) -> dict[str, Any]:
    """Replay both accepted proofs from live PR heads and immutable Git objects."""
    verified = verify_completion_envelopes(platform_envelope, publish_envelope)
    platform_identity = EXPECTED_IDENTITIES["platform"]
    publish_identity = EXPECTED_IDENTITIES["publish"]
    _verify_live_pull_objects(
        platform_root,
        platform_identity,
        observations,
        category="aggregate-token.platform-live-replay",
    )
    _verify_live_pull_objects(
        publish_root,
        publish_identity,
        observations,
        category="aggregate-token.publish-live-replay",
    )
    _verify_repository_object_root(
        platform_root,
        platform_identity["repository"],
        platform_identity["merge_oid"],
        platform_identity["tree_oid"],
    )
    _verify_repository_object_root(
        publish_root,
        publish_identity["repository"],
        publish_identity["merge_oid"],
        publish_identity["tree_oid"],
    )

    platform_core = platform_envelope["evidence_core"]
    publication = publish_envelope["evidence_core"]["publication_evidence"]
    contract = publication["platform_contract"]
    manifest_record, _ = _git_blob_identity(
        platform_root,
        platform_identity["merge_oid"],
        contract["source_manifest_path"],
    )
    if manifest_record != {
        "mode": platform_core["manifest"]["mode"],
        "oid": platform_core["manifest"]["oid"],
        "path": contract["source_manifest_path"],
        "sha256": platform_core["manifest"]["sha256"],
    }:
        raise AggregateError("aggregate-token.platform-git-replay")
    for expected_blob in platform_core["publisher_blobs"].values():
        measured, _ = _git_blob_identity(
            platform_root, platform_identity["merge_oid"], expected_blob["path"]
        )
        if measured != expected_blob:
            raise AggregateError("aggregate-token.platform-git-replay")

    for field in ("publisher",):
        expected_blob = publication[field]
        measured, _ = _git_blob_identity(
            publish_root, publish_identity["merge_oid"], expected_blob["path"]
        )
        if (
            expected_blob.get("repository") != publish_identity["repository"]
            or measured
            != {
                "mode": expected_blob["blob_mode"],
                "oid": expected_blob["oid"],
                "path": expected_blob["path"],
                "sha256": expected_blob["sha256"],
            }
        ):
            raise AggregateError("aggregate-token.publish-git-replay")
    token_producer = publish_envelope["evidence_core"]["token_producer"]
    measured_token_producer, _ = _git_blob_identity(
        publish_root, publish_identity["merge_oid"], token_producer["path"]
    )
    if measured_token_producer != token_producer:
        raise AggregateError("aggregate-token.publish-git-replay")

    candidate = b"api/_candidate/runtime-reference.md"
    for artifact in publication["artifacts"]:
        measured, raw = _git_blob_identity(
            publish_root, publish_identity["merge_oid"], artifact["path"]
        )
        if (
            measured["mode"] != "100644"
            or measured["sha256"] != artifact["sha256"]
            or candidate in raw
            or any(path.encode("ascii") not in raw for path in PUBLIC_MEMBER_PATHS)
        ):
            raise AggregateError("aggregate-token.publish-git-replay")
    for path in PUBLIC_MEMBER_PATHS:
        measured, _ = _git_blob_identity(
            publish_root, publish_identity["merge_oid"], path
        )
        if measured["mode"] != "100644":
            raise AggregateError("aggregate-token.publish-git-replay")
    return verified


def _directory_without_symlinks(path: Path) -> bool:
    absolute = path.absolute()
    temporary = Path(tempfile.gettempdir()).absolute()
    current = temporary if absolute == temporary or temporary in absolute.parents else Path(absolute.anchor)
    try:
        if stat.S_ISLNK(current.lstat().st_mode) or not current.is_dir():
            return False
        for part in absolute.relative_to(current).parts:
            current /= part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                return False
    except (OSError, ValueError):
        return False
    return True


def _github_repository(remote: str) -> str | None:
    scp = re.fullmatch(r"(?:git@)?github\.com:(?P<path>[^?#]+)", remote, re.I)
    if scp is not None:
        path = scp.group("path")
    else:
        try:
            parsed = urllib.parse.urlsplit(remote)
            port = parsed.port
        except ValueError:
            return None
        scheme = parsed.scheme.casefold()
        if (
            scheme not in {"https", "ssh", "git"}
            or (parsed.hostname or "").casefold() != "github.com"
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            return None
        if scheme == "https" and (parsed.username is not None or port is not None):
            return None
        if scheme == "ssh" and ((parsed.username or "git").casefold() != "git" or port not in {None, 22}):
            return None
        if scheme == "git" and (parsed.username is not None or port not in {None, 9418}):
            return None
        path = parsed.path
    normalized = path.strip("/")
    if normalized.casefold().endswith(".git"):
        normalized = normalized[:-4]
    parts = normalized.split("/")
    if len(parts) != 2 or any(re.fullmatch(r"[A-Za-z0-9_.-]+", part) is None for part in parts):
        return None
    return "/".join(parts).casefold()


def _decode_git_path(raw: bytes) -> str:
    try:
        path = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AggregateError("aggregate-token.worktree-drift") from exc
    relative = PurePosixPath(path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise AggregateError("aggregate-token.worktree-drift")
    return path


def _worktree_blob(root: Path, path: str, expected_mode: str) -> tuple[str, str]:
    relative = PurePosixPath(path)
    current = root
    for index, part in enumerate(relative.parts):
        current /= part
        try:
            item_mode = current.lstat().st_mode
        except OSError as exc:
            raise AggregateError("aggregate-token.worktree-drift") from exc
        if index < len(relative.parts) - 1:
            if stat.S_ISLNK(item_mode) or not stat.S_ISDIR(item_mode):
                raise AggregateError("aggregate-token.worktree-drift")
    if expected_mode == "120000":
        if not stat.S_ISLNK(item_mode):
            raise AggregateError("aggregate-token.worktree-drift")
        try:
            raw = os.fsencode(os.readlink(current))
        except OSError as exc:
            raise AggregateError("aggregate-token.worktree-drift") from exc
        measured_mode = "120000"
    else:
        if not stat.S_ISREG(item_mode) or stat.S_ISLNK(item_mode):
            raise AggregateError("aggregate-token.worktree-drift")
        try:
            before = current.lstat()
            descriptor = os.open(current, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except OSError as exc:
            raise AggregateError("aggregate-token.worktree-drift") from exc
        try:
            after = os.fstat(descriptor)
            if (
                not stat.S_ISREG(after.st_mode)
                or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                or stat.S_IMODE(before.st_mode) != stat.S_IMODE(after.st_mode)
            ):
                raise AggregateError("aggregate-token.worktree-drift")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
        finally:
            os.close(descriptor)
        measured_mode = "100755" if after.st_mode & 0o111 else "100644"
    oid = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
    return measured_mode, oid


def verify_worktree_matches_tree(root: Path, commit: str) -> None:
    """Compare every tracked path's bytes and mode to an immutable commit tree."""
    if OID.fullmatch(commit) is None or not _directory_without_symlinks(root):
        raise AggregateError("aggregate-token.git-object")
    if _git(root, "cat-file", "-t", commit) != "commit":
        raise AggregateError("aggregate-token.git-object")
    raw_tree = _git(root, "ls-tree", "-rz", "--full-tree", commit, binary=True)
    assert isinstance(raw_tree, bytes)
    expected: dict[str, tuple[str, str]] = {}
    for record in raw_tree.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_type, oid = metadata.decode("ascii").split()
        except (UnicodeDecodeError, ValueError) as exc:
            raise AggregateError("aggregate-token.worktree-drift") from exc
        path = _decode_git_path(raw_path)
        if (
            path in expected
            or mode not in {"100644", "100755", "120000"}
            or object_type != "blob"
            or OID.fullmatch(oid) is None
        ):
            raise AggregateError("aggregate-token.worktree-drift")
        expected[path] = (mode, oid)
    if _git(root, "ls-files", "--unmerged"):
        raise AggregateError("aggregate-token.worktree-drift")
    raw_index = _git(root, "ls-files", "-z", "--cached", binary=True)
    assert isinstance(raw_index, bytes)
    tracked = {_decode_git_path(raw) for raw in raw_index.split(b"\0") if raw}
    if tracked != set(expected):
        raise AggregateError("aggregate-token.worktree-drift")
    for path, (mode, oid) in expected.items():
        measured_mode, measured_oid = _worktree_blob(root, path, mode)
        if measured_mode != mode or measured_oid != oid:
            raise AggregateError("aggregate-token.worktree-drift")


def verify_clean_base(
    root: Path,
    repository: str,
    base_oid: str,
    observations: Any | None = None,
) -> None:
    """Verify the frozen CLEAN base against live GitHub main and the local object."""
    if (
        repository != CLEAN_REPOSITORY
        or base_oid != CLEAN_BASE
        or not _directory_without_symlinks(root)
        or _github_repository(str(_git(root, "remote", "get-url", "origin")))
        != CLEAN_REPOSITORY.casefold()
        or _git(root, "cat-file", "-t", base_oid) != "commit"
    ):
        raise AggregateError("aggregate-token.clean-base")
    try:
        live_main = _live_observations(observations).fetch_ref(
            root, repository, "refs/heads/main"
        )
    except AggregateError:
        raise
    except Exception as exc:
        raise AggregateError("aggregate-token.clean-base") from exc
    if live_main != base_oid or _git(root, "cat-file", "-t", base_oid) != "commit":
        raise AggregateError("aggregate-token.clean-base")


def verify_aggregate_repository(
    root: Path,
    *,
    repository: str,
    pr: int,
    base_oid: str,
    head_oid: str,
    merge_oid: str,
    tree_oid: str,
    observation_source: str,
    observations: Any | None = None,
) -> None:
    """Verify the live merged PR identity and exact checked-out squash tree."""
    if (
        repository != AGGREGATE_REPOSITORY
        or type(pr) is not int
        or pr <= 0
        or observation_source != "github.pull-request.merged-at"
        or not _directory_without_symlinks(root)
        or _github_repository(str(_git(root, "remote", "get-url", "origin")))
        != AGGREGATE_REPOSITORY.casefold()
        or _git(root, "rev-parse", "HEAD") != merge_oid
    ):
        raise AggregateError("aggregate-token.aggregate-identity")
    _verify_live_pull_objects(
        root,
        {
            "base_oid": base_oid,
            "head_oid": head_oid,
            "merge_oid": merge_oid,
            "pr": pr,
            "repository": repository,
            "tree_oid": tree_oid,
        },
        observations,
        category="aggregate-token.aggregate-live-replay",
    )
    verify_worktree_matches_tree(root, merge_oid)


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--platform-envelope", type=Path, required=True)
    parser.add_argument("--publish-envelope", type=Path, required=True)
    parser.add_argument("--architecture-review", type=Path, required=True)
    parser.add_argument("--process-attestation", type=Path, required=True)
    parser.add_argument("--clean-repository", required=True)
    parser.add_argument("--clean-base", required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    review_basis = commands.add_parser("review-basis")
    review_basis.add_argument("--root", type=Path, required=True)
    verify = commands.add_parser("verify-inputs")
    _common_arguments(verify)
    verify.add_argument("--root", type=Path, required=True)
    mint = commands.add_parser("mint")
    _common_arguments(mint)
    mint.add_argument("--clean-root", type=Path, required=True)
    mint.add_argument("--platform-root", type=Path, required=True)
    mint.add_argument("--publish-root", type=Path, required=True)
    mint.add_argument("--root", type=Path, required=True)
    mint.add_argument("--repository", required=True)
    mint.add_argument("--pr", type=int, required=True)
    mint.add_argument("--base-oid", required=True)
    mint.add_argument("--head-oid", required=True)
    mint.add_argument("--merge-oid", required=True)
    mint.add_argument("--tree-oid", required=True)
    mint.add_argument("--observation-source", required=True)
    return parser


def _validated_cli_inputs(
    args: argparse.Namespace, observations: Any | None = None
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    platform = load_canonical_json(args.platform_envelope)
    publish = load_canonical_json(args.publish_envelope)
    review_record = load_canonical_json(args.architecture_review)
    attestation = load_canonical_json(args.process_attestation)
    verified = verify_completion_envelopes(platform, publish)
    review = validate_architecture_review_record(review_record, args.root)
    validate_process_attestation(attestation)
    if args.clean_repository != CLEAN_REPOSITORY or args.clean_base != CLEAN_BASE:
        raise AggregateError("aggregate-token.clean-base")
    if args.command == "mint":
        review = verify_architecture_review_comment(
            review_record, args.root, observations
        )
        verify_clean_base(
            args.clean_root, args.clean_repository, args.clean_base, observations
        )
        verify_producer_git_objects(
            args.platform_root,
            args.publish_root,
            platform,
            publish,
            observations,
        )
    return platform, publish, {**verified, "architecture_review": review}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "review-basis":
        sys.stdout.buffer.write(
            _canonical_json(architecture_review_evidence_core(args.root)) + b"\n"
        )
        return 0
    observations = GitHubLiveObservations() if args.command == "mint" else None
    platform, publish, verified = _validated_cli_inputs(args, observations)
    if args.command == "verify-inputs":
        output = {
            "architecture_review": verified["architecture_review"],
            "clean_base": CLEAN_BASE,
            "clean_repository": CLEAN_REPOSITORY,
            "platform_token_digest": verified["platform_token_digest"],
            "publish_token_digest": verified["publish_token_digest"],
            "result": "pass",
        }
    else:
        verify_aggregate_repository(
            args.root,
            repository=args.repository,
            pr=args.pr,
            base_oid=args.base_oid,
            head_oid=args.head_oid,
            merge_oid=args.merge_oid,
            tree_oid=args.tree_oid,
            observation_source=args.observation_source,
            observations=observations,
        )
        output = build_completion_envelope(
            platform_envelope=platform,
            publish_envelope=publish,
            clean_repository=args.clean_repository,
            clean_base=args.clean_base,
            architecture_review=verified["architecture_review"],
            repository=args.repository,
            pr=args.pr,
            base_oid=args.base_oid,
            head_oid=args.head_oid,
            merge_oid=args.merge_oid,
            tree_oid=args.tree_oid,
            observation_source=args.observation_source,
        )
    sys.stdout.buffer.write(_canonical_json(output) + b"\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AggregateError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, UnicodeError, ValueError, RecursionError, MemoryError):
        print("aggregate-token.input", file=sys.stderr)
        raise SystemExit(1) from None
