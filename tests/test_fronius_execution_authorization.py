from __future__ import annotations

import base64
from collections.abc import Callable
import contextlib
import hashlib
import io
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
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
VALIDATOR_GLOBALS = runpy.run_path(str(VALIDATOR))
STATIC_DEPENDENCIES = VALIDATOR_GLOBALS["COMPLETED_FMV3_DEPENDENCIES"]
M1_06_ISSUE_TITLE = VALIDATOR_GLOBALS["M1_06_PRODUCER_ISSUE_TITLE"]
M1_06_PR_TITLE = VALIDATOR_GLOBALS["M1_06_PRODUCER_PULL_REQUEST_TITLE"]
M1_06_ISSUE_MARKER = VALIDATOR_GLOBALS["M1_06_PRODUCER_ISSUE_MARKER"]
M1_06_REPORT_PATH = VALIDATOR_GLOBALS["M1_06_CONFORMANCE_REPORT_PATH"]
M1_06_REPORT_SCHEMA = VALIDATOR_GLOBALS["M1_06_CONFORMANCE_REPORT_SCHEMA"]
M1_06_CASES = VALIDATOR_GLOBALS["M1_06_CONFORMANCE_CASES"]
M1_06_CASE_DIGEST = VALIDATOR_GLOBALS["M1_06_CONFORMANCE_CASE_DIGEST"]
M1_06_MUTATION_CASES = VALIDATOR_GLOBALS["M1_06_MUTATION_CASES"]
M1_06_MUTATION_COMPILE_STEP_NAME = VALIDATOR_GLOBALS[
    "M1_06_MUTATION_COMPILE_STEP_NAME"
]
M1_06_MUTATION_WORKFLOW_PATH = VALIDATOR_GLOBALS["M1_06_MUTATION_WORKFLOW_PATH"]
M1_06_MUTATION_GUARD_PATH = VALIDATOR_GLOBALS["M1_06_MUTATION_GUARD_PATH"]
M1_06_DOCS_LOCK_VALIDATOR_PATH = VALIDATOR_GLOBALS["M1_06_DOCS_LOCK_VALIDATOR_PATH"]
M1_06_DOCS_LOCK_PATH = VALIDATOR_GLOBALS["M1_06_DOCS_LOCK_PATH"]
M1_06_MUTATION_AST_STEP_NAME = VALIDATOR_GLOBALS["M1_06_MUTATION_AST_STEP_NAME"]
M1_06_CI_JOB_NAME = VALIDATOR_GLOBALS["M1_06_CI_JOB_NAME"]
M1_06_CI_STEP_NAME = VALIDATOR_GLOBALS["M1_06_CI_STEP_NAME"]
M1_06_RED_GUARD_STEP_NAME = VALIDATOR_GLOBALS["M1_06_RED_GUARD_STEP_NAME"]
M1_06_RED_COMPILE_STEP_NAME = VALIDATOR_GLOBALS["M1_06_RED_COMPILE_STEP_NAME"]
M1_06_RED_TEST_STEP_NAME = VALIDATOR_GLOBALS["M1_06_RED_TEST_STEP_NAME"]
M1_06_RED_COMMIT_SUBJECT = VALIDATOR_GLOBALS["M1_06_RED_COMMIT_SUBJECT"]
M1_06_SETUP_STEP_NAME = VALIDATOR_GLOBALS["M1_06_SETUP_STEP_NAME"]
M1_06_DOCS_LOCK_STEP_NAME = VALIDATOR_GLOBALS["M1_06_DOCS_LOCK_STEP_NAME"]
M1_06_RED_GUARD_JOB_NAME = VALIDATOR_GLOBALS.get(
    "M1_06_RED_GUARD_JOB_NAME", "red-diff guard"
)
M1_06_CONFORMANCE_JOB_NAME = VALIDATOR_GLOBALS.get(
    "M1_06_CONFORMANCE_JOB_NAME", "conformance"
)
M1_06_PRODUCTION_SYMBOLS = VALIDATOR_GLOBALS["M1_06_PRODUCTION_SYMBOLS"]
GITHUB_ACTIONS_APP_ID = VALIDATOR_GLOBALS["GITHUB_ACTIONS_APP_ID"]
ISSUE_SPEC_DIGEST = VALIDATOR_GLOBALS["issue_spec_digest"]
ISSUE_SPEC_MARKER = VALIDATOR_GLOBALS["issue_spec_marker"]
ISSUE_SPEC_TITLE = VALIDATOR_GLOBALS["issue_spec_title"]
M1_06_REVIEW_SCHEMA = VALIDATOR_GLOBALS["M1_06_OWNER_REVIEW_SCHEMA"]
CODEX_REVIEW_BODY = VALIDATOR_GLOBALS["canonical_codex_review_body"]
PLAN_DATA = yaml.safe_load((PLAN / "plan.yaml").read_text(encoding="utf-8"))
AMENDMENT_PR_URL = (
    "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/91"
)
PR_HEAD_SHA = "1" * 40
PR_TREE_SHA = "2" * 40
PR_HEAD_COMMITTED_AT = "2026-07-30T10:00:00Z"
PR_ATTESTED_AT = "2026-07-30T10:30:00Z"
PR_MERGED_AT = "2026-07-30T10:20:00Z"
REVIEW_RUN_IDS = [
    "019f5d80-1111-7222-8333-444444444444",
    "019f5d80-5555-7666-8777-888888888888",
]
OFFICIAL_REVIEW_ID = 700
REVIEW_IDS = [701, 702]
WORKFLOW_RUN_ID = 700
M1_06_RED_SHA = "9" * 40
M1_06_RED_RUN_ID = 900
M1_06_GREEN_RUN_ID = 904
M1_06_OFFICIAL_REVIEW_ID = 901
M1_06_OWNER_REVIEW_IDS = [902, 903]
M1_06_MUTATION_RUN_IDS = list(range(9200, 9200 + len(M1_06_MUTATION_CASES)))
M1_06_MUTATION_SHAS = [format(index + 1, "x") * 40 for index in range(len(M1_06_MUTATION_CASES))]
M1_06_HARNESS_PR = 41
M1_06_HARNESS_HEAD_SHA = "61" * 20
M1_06_HARNESS_TREE_SHA = "71" * 20
M1_06_HARNESS_MERGE_SHA = "51" * 20
M1_06_HARNESS_BASE_SHA = "41" * 20
M1_06_HARNESS_BASE_TREE_SHA = "31" * 20
M1_06_HARNESS_WORKFLOW_ID = 123456
PLAN_REPOSITORY = "Project-Helianthus/helianthus-execution-plans"
PLAN_CANONICAL_REMOTE = (
    "https://github.com/Project-Helianthus/helianthus-execution-plans.git"
)
TEST_PUBLISH_REMOTE = "test-publish"
CLAIM_RUN_ID = "019fbe20-0000-7000-8000-000000000001"
CLAIM_OWNER_SECRET = "ab" * 32


def claim_event(
    *, repository: str = "Project-Helianthus/helianthus-modbusreg",
    issue_id: str = "FMV3-M2-02", issue_number: int = 50,
    plan_anchor: str = "1" * 40, run_id: str = CLAIM_RUN_ID,
    event: str = "ACQUIRE", state: str = "HELD", generation: int = 1,
    previous_sha: str | None = None, authoritative_main_sha: str = "2" * 40,
    event_at: str = "2026-08-01T00:00:00Z",
    expires_at: str = "2026-08-01T06:00:00Z",
    secret: str = CLAIM_OWNER_SECRET,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": VALIDATOR_GLOBALS["REPOSITORY_CLAIM_SCHEMA"],
        "ledger_id": VALIDATOR_GLOBALS["REPOSITORY_CLAIM_LEDGER_ID"],
        "owner_epoch": VALIDATOR_GLOBALS["REPOSITORY_CLAIM_OWNER_EPOCH"],
        "repository": repository,
        "ref": VALIDATOR_GLOBALS["repository_claim_ref"](repository),
        "event": event,
        "state": state,
        "issue_id": issue_id,
        "issue_number": issue_number,
        "plan_anchor": plan_anchor,
        "run_id": run_id,
        "owner_login": VALIDATOR_GLOBALS["REPOSITORY_CLAIM_OWNER_LOGIN"],
        "owner_actor_id": VALIDATOR_GLOBALS["REPOSITORY_CLAIM_OWNER_ACTOR_ID"],
        "owner_commitment": VALIDATOR_GLOBALS[
            "REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT"
        ],
        "generation": generation,
        "previous_sha": previous_sha,
        "authoritative_main_sha": authoritative_main_sha,
        "event_at": event_at,
        "expires_at": expires_at,
    }
    payload["event_mac"] = VALIDATOR_GLOBALS["repository_claim_event_mac"](
        payload, secret
    )
    return payload


def routing_receipt(
    issue: dict[str, object], plan_anchor: str,
) -> tuple[str, str]:
    risks, route = VALIDATOR_GLOBALS["expected_issue_route"](issue)
    payload = {
        "schema": VALIDATOR_GLOBALS["ROUTING_RECEIPT_SCHEMA"],
        "issue_id": issue["id"],
        "repository": issue["repo"],
        "complexity": issue["complexity"],
        "risks": risks,
        "plan_anchor": plan_anchor,
        "router_sha256": VALIDATOR_GLOBALS["MODEL_ROUTER_SHA256"],
        "policy_sha256": VALIDATOR_GLOBALS["MODEL_ROUTING_POLICY_SHA256"],
        "route": route,
    }
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return base64.b64encode(raw).decode("ascii"), hashlib.sha256(raw).hexdigest()


def m1_06_mutation_patch(case_id: str) -> str:
    return f"@@ -1 +1 @@\n-{case_id}:baseline\n+{case_id}:mutated\n"


def m1_06_mutation_patch_digest(case_id: str) -> str:
    projection = [{
        "filename": "capability.go",
        "status": "modified",
        "patch": m1_06_mutation_patch(case_id),
    }]
    return hashlib.sha256(json.dumps(
        projection, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")).hexdigest()


class FroniusExecutionAuthorizationTests(unittest.TestCase):
    def test_m1_06_template_rejects_persisted_checkout_credentials(self) -> None:
        validate_templates = VALIDATOR_GLOBALS["validate_plan_templates"]
        template_hashes = validate_templates.__globals__["PLAN_TEMPLATE_SHA256"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(PLAN / "templates", root / "templates")
            workflow_path = root / "templates/fmv3-m1-06-mutation.yml"
            workflow = workflow_path.read_text(encoding="utf-8")
            workflow_path.write_text(
                workflow.replace("          persist-credentials: false\n", "", 1),
                encoding="utf-8",
            )
            mutated_hashes = dict(template_hashes)
            mutated_hashes[workflow_path.name] = hashlib.sha256(
                workflow_path.read_bytes()
            ).hexdigest()
            with mock.patch.dict(template_hashes, mutated_hashes, clear=True):
                with self.assertRaisesRegex(
                    VALIDATOR_GLOBALS["ValidationError"],
                    "disable persisted credentials",
                ):
                    validate_templates(root)

    def test_repository_claim_ref_is_repository_scoped(self) -> None:
        claim_ref = VALIDATOR_GLOBALS["repository_claim_ref"]
        repository = "Project-Helianthus/helianthus-modbusreg"
        self.assertEqual(
            claim_ref(repository),
            "refs/heads/fmv3-claims-v2/project-helianthus-helianthus-modbusreg",
        )

    def test_repository_claim_control_requires_exact_owner_and_split_rulesets(self) -> None:
        control = VALIDATOR_GLOBALS["require_repository_claim_control"]
        namespace = control.__globals__
        saved_api = namespace["github_api"]
        saved_commitment = namespace["REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT"]
        namespace["REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT"] = namespace[
            "repository_claim_owner_key_commitment"
        ](CLAIM_OWNER_SECRET)
        common = {
            "target": "branch",
            "source_type": "Repository",
            "source": PLAN_REPOSITORY,
            "enforcement": "active",
            "conditions": {
                "ref_name": {
                    "include": [
                        f"{namespace['REPOSITORY_CLAIM_REF_PREFIX']}/**"
                    ],
                    "exclude": [],
                }
            },
        }
        responses = {
            "user": {
                "id": namespace["REPOSITORY_CLAIM_OWNER_ACTOR_ID"],
                "login": namespace["REPOSITORY_CLAIM_OWNER_LOGIN"],
                "type": "User",
            },
            (
                f"repos/{PLAN_REPOSITORY}/rulesets/"
                f"{namespace['REPOSITORY_CLAIM_INTEGRITY_RULESET_ID']}"
            ): {
                **common,
                "id": namespace["REPOSITORY_CLAIM_INTEGRITY_RULESET_ID"],
                "name": "FMV3 v2 claim integrity",
                "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}],
                "bypass_actors": [],
            },
            (
                f"repos/{PLAN_REPOSITORY}/rulesets/"
                f"{namespace['REPOSITORY_CLAIM_WRITER_RULESET_ID']}"
            ): {
                **common,
                "id": namespace["REPOSITORY_CLAIM_WRITER_RULESET_ID"],
                "name": "FMV3 v2 claim writer",
                "rules": [{"type": "creation"}, {"type": "update"}],
                "bypass_actors": [{
                    "actor_id": 5,
                    "actor_type": "RepositoryRole",
                    "bypass_mode": "always",
                }],
            },
        }
        namespace["github_api"] = lambda endpoint: responses[endpoint]
        try:
            control(CLAIM_OWNER_SECRET)
            responses[next(
                key for key in responses
                if isinstance(key, str) and key.endswith(
                    str(namespace["REPOSITORY_CLAIM_WRITER_RULESET_ID"])
                )
            )]["enforcement"] = "disabled"
            with self.assertRaisesRegex(
                namespace["ValidationError"], "rulesets are absent or drifted"
            ):
                control(CLAIM_OWNER_SECRET)
        finally:
            namespace["github_api"] = saved_api
            namespace["REPOSITORY_CLAIM_OWNER_KEY_COMMITMENT"] = saved_commitment

    def test_repository_claim_control_rejects_foreign_secret_before_github(self) -> None:
        control = VALIDATOR_GLOBALS["require_repository_claim_control"]
        namespace = control.__globals__
        saved_api = namespace["github_api"]
        namespace["github_api"] = lambda *_: self.fail(
            "foreign secret must fail before GitHub lookup"
        )
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "secret is not anchor-pinned"
            ):
                control("cd" * 32)
        finally:
            namespace["github_api"] = saved_api

    def test_repository_claim_clock_uses_unique_github_date_header(self) -> None:
        clock = VALIDATOR_GLOBALS["github_server_time"]
        namespace = clock.__globals__
        original = namespace["trusted_gh_command"]
        namespace["trusted_gh_command"] = lambda arguments: subprocess.CompletedProcess(
            arguments, 0,
            stdout=(
                "HTTP/2.0 200 OK\n"
                "Date: Sat, 01 Aug 2026 12:34:56 GMT\n\n{}\n"
            ),
            stderr="",
        )
        try:
            observed = clock()
        finally:
            namespace["trusted_gh_command"] = original
        self.assertEqual(observed.isoformat(), "2026-08-01T12:34:56+00:00")

    def test_model_routing_receipt_is_exact_issue_bound_and_not_underpowered(self) -> None:
        require_receipt = VALIDATOR_GLOBALS["require_issue_routing_receipt"]
        namespace = require_receipt.__globals__
        issue = next(
            item for item in PLAN_DATA["issues"] if item["id"] == "FMV3-M2-01"
        )
        anchor = "1" * 40
        encoded, digest = routing_receipt(issue, anchor)
        receipt = require_receipt(encoded, digest, issue, anchor)
        self.assertEqual(receipt["route"]["primary_profile"], "developer_critical")
        self.assertEqual(receipt["route"]["reasoning_effort"], "max")
        raw = json.loads(base64.b64decode(encoded))
        raw["route"]["model"] = "gpt-5.6-terra"
        weakened = json.dumps(
            raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        with self.assertRaisesRegex(
            namespace["ValidationError"], "underpowered"
        ):
            require_receipt(
                base64.b64encode(weakened).decode("ascii"),
                hashlib.sha256(weakened).hexdigest(),
                issue,
                anchor,
            )
        raw = json.loads(base64.b64decode(encoded))
        raw["max_override_supported"] = True
        unsupported = json.dumps(
            raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        with self.assertRaisesRegex(
            namespace["ValidationError"], "envelope"
        ):
            require_receipt(
                base64.b64encode(unsupported).decode("ascii"),
                hashlib.sha256(unsupported).hexdigest(),
                issue,
                anchor,
            )

    def test_model_routing_receipt_is_mandatory(self) -> None:
        require_receipt = VALIDATOR_GLOBALS["require_issue_routing_receipt"]
        namespace = require_receipt.__globals__
        issue = next(
            item for item in PLAN_DATA["issues"] if item["id"] == "FMV3-M1-01"
        )
        with self.assertRaisesRegex(
            namespace["ValidationError"], "requires one bounded"
        ):
            require_receipt(None, None, issue, "1" * 40)

    def test_repository_snapshot_requires_exact_selected_issue_open(self) -> None:
        snapshot = VALIDATOR_GLOBALS["require_plan_owned_repository_snapshot"]
        namespace = snapshot.__globals__
        original = namespace["github_paginated_list"]
        namespace["github_paginated_list"] = lambda endpoint, *_: []
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "exactly one active repository issue"
            ):
                snapshot(
                    "Project-Helianthus/helianthus-modbusreg",
                    50,
                    "FMV3-M2-02: selected",
                    "marker",
                )
        finally:
            namespace["github_paginated_list"] = original

    def test_fenced_repository_snapshot_enforces_capability_specific_pr_mutex(self) -> None:
        snapshot = VALIDATOR_GLOBALS["require_fenced_repository_snapshot"]
        namespace = snapshot.__globals__
        original = namespace["github_paginated_list"]
        repository = "Project-Helianthus/helianthus-modbusreg"
        title = "FMV3-M2-02: selected"
        marker = "<!-- fmv3-issue-spec-sha256:" + "a" * 64 + " -->"
        selected_issue = {
            "number": 50, "title": title, "body": marker, "state": "open",
        }
        selected_pr = {
            "number": 51,
            "state": "open",
            "title": title,
            "body": "Closes #50",
            "head": {
                "ref": "issue/50-profile-contract",
                "repo": {"full_name": repository},
            },
            "base": {"ref": "main", "repo": {"full_name": repository}},
        }
        competing_pr = {
            "number": 52,
            "state": "open",
            "head": {
                "ref": "issue/999-competing",
                "repo": {"full_name": repository},
            },
            "base": {"ref": "main", "repo": {"full_name": repository}},
        }

        def responses(prs: list[dict[str, object]]) -> None:
            namespace["github_paginated_list"] = lambda endpoint, *_: (
                [selected_issue] if "/issues?" in endpoint else prs
            )

        try:
            responses([competing_pr])
            with self.assertRaisesRegex(
                namespace["ValidationError"], "before fenced PR creation"
            ):
                snapshot(
                    repository, 50, title, marker, "issue-pull-create",
                    "preflight", "issue/50-profile-contract",
                )

            responses([selected_pr])
            snapshot(
                repository, 50, title, marker, "issue-pull-create",
                "postflight", "issue/50-profile-contract",
            )
            snapshot(
                repository, 50, title, marker, "selected-issue-comment",
                "postflight", None,
            )

            wrong_title_pr = {**selected_pr, "title": "FMV3-M2-02: unrelated"}
            responses([wrong_title_pr])
            with self.assertRaisesRegex(
                namespace["ValidationError"], "exactly one selected pull request"
            ):
                snapshot(
                    repository, 50, title, marker, "issue-pull-create",
                    "postflight", "issue/50-profile-contract",
                )

            responses([selected_pr, competing_pr])
            with self.assertRaisesRegex(
                namespace["ValidationError"], "exactly one selected pull request"
            ):
                snapshot(
                    repository, 50, title, marker, "issue-pull-create",
                    "postflight", "issue/50-profile-contract",
                )
            with self.assertRaisesRegex(
                namespace["ValidationError"], "competing pull request"
            ):
                snapshot(
                    repository, 50, title, marker, "selected-issue-comment",
                    "postflight", None,
                )
        finally:
            namespace["github_paginated_list"] = original

    def test_materialized_validator_rejects_self_consistent_unpinned_gh(self) -> None:
        trusted = VALIDATOR_GLOBALS["trusted_materialized_executable"]
        namespace = trusted.__globals__
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canary = root / "executed"
            fake = root / "gh"
            fake.write_text(
                f"#!/bin/sh\nprintf ran > {canary}\n",
                encoding="ascii",
            )
            fake.chmod(0o500)
            digest = hashlib.sha256(fake.read_bytes()).hexdigest()
            old_path = os.environ.get("FMV3_ANCHOR_MATERIALIZATION_GH")
            old_digest = os.environ.get("FMV3_ANCHOR_MATERIALIZATION_GH_SHA256")
            os.environ["FMV3_ANCHOR_MATERIALIZATION_GH"] = str(fake)
            os.environ["FMV3_ANCHOR_MATERIALIZATION_GH_SHA256"] = digest
            try:
                with self.assertRaises(namespace["ValidationError"]):
                    trusted("GH")
            finally:
                if old_path is None:
                    os.environ.pop("FMV3_ANCHOR_MATERIALIZATION_GH", None)
                else:
                    os.environ["FMV3_ANCHOR_MATERIALIZATION_GH"] = old_path
                if old_digest is None:
                    os.environ.pop("FMV3_ANCHOR_MATERIALIZATION_GH_SHA256", None)
                else:
                    os.environ["FMV3_ANCHOR_MATERIALIZATION_GH_SHA256"] = old_digest
            self.assertFalse(canary.exists())

    def test_repository_claim_ref_cas_has_one_winner_and_stale_release_fails(self) -> None:
        push_cas = VALIDATOR_GLOBALS["push_repository_claim_cas"]
        namespace = push_cas.__globals__
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            materialized = root / "materialized"
            materialized.mkdir(mode=0o700)
            validator_path = materialized / "validate_plan.py"
            validator_path.write_text("# fixture\n", encoding="ascii")
            repo = root / "repo"
            remote = root / "remote.git"
            repo.mkdir()
            subprocess.run(
                ["git", "init", "--bare", str(remote)], check=True,
                capture_output=True, text=True,
            )
            self.git(repo, "init", "-b", "main")
            self.git(repo, "config", "user.name", "Claim CAS Test")
            self.git(repo, "config", "user.email", "claim-cas@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="ascii")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-m", "base")
            self.git(repo, "remote", "add", "origin", str(remote))
            self.git(repo, "push", "-u", "origin", "main")
            tree = self.git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
            parent = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            commits = [
                self.git(repo, "commit-tree", tree, "-p", parent, "-m", message)
                .stdout.strip()
                for message in ("claim one", "claim two")
            ]
            claim_ref = "refs/heads/fmv3-claims/test/repository-1"
            saved_file = namespace["__file__"]
            saved_git = namespace["TRUSTED_GIT_EXECUTABLE"]
            saved_token = os.environ.get("GH_TOKEN")
            namespace["__file__"] = str(validator_path)
            namespace["TRUSTED_GIT_EXECUTABLE"] = Path("/usr/bin/git")
            os.environ["GH_TOKEN"] = "test-token-not-used-by-file-remote"
            barrier = threading.Barrier(2)
            outcomes: list[str] = []

            def claimant(commit: str) -> None:
                barrier.wait()
                try:
                    push_cas(repo, claim_ref, None, commit)
                    outcomes.append("won")
                except namespace["ValidationError"]:
                    outcomes.append("lost")

            threads = [threading.Thread(target=claimant, args=(commit,)) for commit in commits]
            try:
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                self.assertCountEqual(outcomes, ["won", "lost"])
                winner = self.git(repo, "ls-remote", "--refs", "origin", claim_ref)
                winner_sha = winner.stdout.split()[0]
                stale = next(commit for commit in commits if commit != winner_sha)
                with self.assertRaises(namespace["ValidationError"]):
                    push_cas(repo, claim_ref, stale, None)
                self.assertEqual(
                    self.git(repo, "ls-remote", "--refs", "origin", claim_ref)
                    .stdout.split()[0],
                    winner_sha,
                )
                with self.assertRaisesRegex(
                    namespace["ValidationError"], "append-only commit"
                ):
                    push_cas(repo, claim_ref, winner_sha, None)
                self.assertEqual(
                    self.git(repo, "ls-remote", "--refs", "origin", claim_ref)
                    .stdout.split()[0],
                    winner_sha,
                )
            finally:
                namespace["__file__"] = saved_file
                namespace["TRUSTED_GIT_EXECUTABLE"] = saved_git
                if saved_token is None:
                    os.environ.pop("GH_TOKEN", None)
                else:
                    os.environ["GH_TOKEN"] = saved_token

    def test_repository_claim_cas_reconciles_nonzero_push_result(self) -> None:
        push_cas = VALIDATOR_GLOBALS["push_repository_claim_cas"]
        namespace = push_cas.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "__file__", "remote_ref_sha", "trusted_github_token",
                "trusted_git_executable", "subprocess",
            )
        }
        with tempfile.TemporaryDirectory() as temporary:
            materialized = Path(temporary) / "validator"
            materialized.mkdir(mode=0o700)
            validator_path = materialized / "validate_plan.py"
            validator_path.write_text("# fixture\n", encoding="ascii")
            expected = "a" * 40
            target = "b" * 40
            namespace["__file__"] = str(validator_path)
            namespace["trusted_github_token"] = lambda: "fixture-token"
            namespace["trusted_git_executable"] = lambda: Path("/trusted/git")
            namespace["subprocess"] = mock.Mock()
            namespace["subprocess"].run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="connection lost",
            )
            try:
                states = iter((expected, target))
                namespace["remote_ref_sha"] = lambda *_: next(states)
                push_cas(Path("/unused"), "refs/heads/fmv3-claims-v2/test", expected, target)

                states = iter((expected, expected))
                namespace["remote_ref_sha"] = lambda *_: next(states)
                with self.assertRaisesRegex(
                    namespace["ValidationError"],
                    "completion-ambiguous.*STOP without retry.*reconciliation",
                ):
                    push_cas(
                        Path("/unused"), "refs/heads/fmv3-claims-v2/test",
                        expected, target,
                    )

                namespace["subprocess"].run.side_effect = OSError(
                    "connection dropped after send"
                )
                states = iter((expected, target))
                namespace["remote_ref_sha"] = lambda *_: next(states)
                push_cas(
                    Path("/unused"), "refs/heads/fmv3-claims-v2/test",
                    expected, target,
                )

                states = iter((expected, expected))
                namespace["remote_ref_sha"] = lambda *_: next(states)
                with self.assertRaisesRegex(
                    namespace["ValidationError"],
                    "completion-ambiguous.*STOP without retry.*reconciliation",
                ):
                    push_cas(
                        Path("/unused"), "refs/heads/fmv3-claims-v2/test",
                        expected, target,
                    )
            finally:
                namespace.update(saved)

    def test_expired_repository_claim_is_taken_over_with_observed_cas(self) -> None:
        acquire = VALIDATOR_GLOBALS["acquire_repository_claim"]
        namespace = acquire.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "remote_ref_sha", "github_api", "git_command",
                "push_repository_claim_cas", "require_repository_claim_history",
            )
        }
        observed = "a" * 40
        replacement = "c" * 40
        lookups = iter((observed, replacement))
        pushes: list[tuple[str | None, str | None]] = []
        commit_arguments: list[str] = []

        namespace["remote_ref_sha"] = lambda *_: next(lookups)
        prior_payload = claim_event(
            issue_id="FMV3-M2-03", issue_number=51,
            run_id="019fbe20-0000-7000-8000-000000000009",
            event="TAKEOVER", state="HELD", generation=7,
            previous_sha="9" * 40,
        )
        namespace["github_api"] = lambda *_: {
            "message": json.dumps(prior_payload),
            "sha": observed,
            "tree": {"sha": "b" * 40},
            "parents": [{"sha": "9" * 40}],
        }
        namespace["require_repository_claim_history"] = (
            lambda *_args, **_kwargs: prior_payload
        )

        def fake_git(_repo: Path, arguments: list[str], _label: str, **_kwargs):
            if "commit-tree" in arguments:
                commit_arguments.extend(arguments)
                return replacement
            if arguments == ["rev-parse", "FETCH_HEAD^{commit}"]:
                return observed
            return "b" * 40

        namespace["git_command"] = fake_git
        namespace["push_repository_claim_cas"] = (
            lambda _repo, _ref, expected, target: pushes.append((expected, target))
        )
        try:
            result = acquire(
                Path("/unused"), "2" * 40,
                "Project-Helianthus/helianthus-modbusreg", "FMV3-M2-02", 50,
                "1" * 40, "019fbe20-0000-7000-8000-000000000001",
                CLAIM_OWNER_SECRET,
                now=namespace["datetime"](
                    2026, 8, 1, 6, tzinfo=namespace["timezone"].utc
                ),
            )
        finally:
            namespace.update(saved)

        self.assertEqual(result["claim_sha"], replacement)
        self.assertEqual(pushes, [(observed, replacement)])
        payload = json.loads(commit_arguments[commit_arguments.index("-m") + 1])
        self.assertEqual(payload["generation"], 8)
        self.assertEqual(
            commit_arguments[commit_arguments.index("-p") + 1], observed
        )

    def test_repository_claim_generation_exhaustion_rejects_before_commit(self) -> None:
        acquire = VALIDATOR_GLOBALS["acquire_repository_claim"]
        namespace = acquire.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "remote_ref_sha", "github_api", "git_command",
                "push_repository_claim_cas", "require_repository_claim_history",
            )
        }
        observed = "a" * 40
        prior_payload = claim_event(
            event="RENEW", state="HELD",
            generation=namespace["REPOSITORY_CLAIM_MAX_GENERATION"],
            previous_sha="9" * 40,
        )
        namespace["remote_ref_sha"] = lambda *_: observed
        namespace["github_api"] = lambda *_: {
            "message": json.dumps(prior_payload),
            "sha": observed,
            "tree": {"sha": "b" * 40},
            "parents": [{"sha": "9" * 40}],
        }
        namespace["require_repository_claim_history"] = (
            lambda *_args, **_kwargs: prior_payload
        )
        namespace["git_command"] = lambda *_args, **_kwargs: self.fail(
            "generation exhaustion must fail before Git history mutation"
        )
        namespace["push_repository_claim_cas"] = lambda *_: self.fail(
            "generation exhaustion must fail before push"
        )
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "generation is exhausted"
            ):
                acquire(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg",
                    "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                    CLAIM_OWNER_SECRET,
                    now=namespace["datetime"](
                        2026, 8, 1, 1, tzinfo=namespace["timezone"].utc
                    ),
                )
        finally:
            namespace.update(saved)

    def test_repository_claim_history_budget_reserves_final_release(self) -> None:
        acquire = VALIDATOR_GLOBALS["acquire_repository_claim"]
        namespace = acquire.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "remote_ref_sha", "github_api", "git_command",
                "push_repository_claim_cas", "require_repository_claim_history",
            )
        }
        prior = claim_event(
            event="RENEW", generation=(
                namespace["REPOSITORY_CLAIM_MAX_HISTORY_EVENTS"] - 1
            ),
            previous_sha="9" * 40,
        )
        namespace["remote_ref_sha"] = lambda *_: "a" * 40
        namespace["github_api"] = lambda *_: {}
        namespace["require_repository_claim_history"] = lambda *_args: prior
        namespace["git_command"] = lambda *_args, **_kwargs: self.fail(
            "history budget must fail before commit creation"
        )
        namespace["push_repository_claim_cas"] = lambda *_: self.fail(
            "history budget must fail before push"
        )
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "rotate before another held event"
            ):
                acquire(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg",
                    "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                    CLAIM_OWNER_SECRET,
                    now=namespace["datetime"](
                        2026, 8, 1, 1, tzinfo=namespace["timezone"].utc
                    ),
                )
        finally:
            namespace.update(saved)

    def test_live_repository_claim_blocks_a_different_issue(self) -> None:
        acquire = VALIDATOR_GLOBALS["acquire_repository_claim"]
        namespace = acquire.__globals__
        saved = {
            key: namespace[key]
            for key in ("remote_ref_sha", "github_api", "git_command",
                        "push_repository_claim_cas",
                        "require_repository_claim_history")
        }
        prior_secret = "cd" * 32
        namespace["remote_ref_sha"] = lambda *_: "a" * 40
        prior_payload = claim_event(
            run_id="019fbe20-0000-7000-8000-000000000009",
            event_at="2026-08-02T00:00:00Z",
            expires_at="2026-08-02T06:00:00Z",
        )
        namespace["github_api"] = lambda *_: {
            "message": json.dumps(prior_payload), "sha": "a" * 40,
            "tree": {"sha": "b" * 40}, "parents": [{"sha": "2" * 40}],
        }
        namespace["require_repository_claim_history"] = (
            lambda *_args, **_kwargs: prior_payload
        )
        namespace["git_command"] = lambda *_args, **_kwargs: self.fail(
            "blocked claimant must not create a commit"
        )
        namespace["push_repository_claim_cas"] = lambda *_: self.fail(
            "blocked claimant must not push"
        )
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "another live owner"
            ):
                acquire(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg", "FMV3-M2-03", 51,
                    "1" * 40, CLAIM_RUN_ID, CLAIM_OWNER_SECRET,
                    now=namespace["datetime"](
                        2026, 8, 2, 1, tzinfo=namespace["timezone"].utc
                    ),
                )
        finally:
            namespace.update(saved)

    def test_repository_claim_fence_requires_exact_live_unexpired_tip(self) -> None:
        verify = VALIDATOR_GLOBALS["require_repository_claim_fence"]
        namespace = verify.__globals__
        saved = {
            key: namespace[key]
            for key in ("remote_ref_sha", "github_api", "git_command")
        }
        observed = "a" * 40
        payload = claim_event()
        namespace["remote_ref_sha"] = lambda *_: observed
        namespace["github_api"] = lambda *_: {
            "sha": observed, "message": json.dumps(payload),
            "tree": {"sha": "b" * 40}, "parents": [{"sha": "2" * 40}],
        }
        namespace["git_command"] = lambda *_args, **_kwargs: self.fail(
            "unchanged authoritative main needs no ancestry command"
        )
        try:
            fence = verify(
                Path("/unused"), "2" * 40,
                "Project-Helianthus/helianthus-modbusreg",
                "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                CLAIM_OWNER_SECRET, observed,
                now=namespace["datetime"](
                    2026, 8, 1, 5, 59, 59,
                    tzinfo=namespace["timezone"].utc,
                ),
            )
            self.assertEqual(fence["claim_sha"], observed)
            self.assertEqual(fence["generation"], 1)
            with self.assertRaisesRegex(
                namespace["ValidationError"], "fence is expired"
            ):
                verify(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg",
                    "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                    CLAIM_OWNER_SECRET, observed,
                    now=namespace["datetime"](
                        2026, 8, 1, 6, 0, 0,
                        tzinfo=namespace["timezone"].utc,
                    ),
                )
        finally:
            namespace.update(saved)

    def test_repository_claim_fence_rejects_advanced_tip_before_payload_read(self) -> None:
        verify = VALIDATOR_GLOBALS["require_repository_claim_fence"]
        namespace = verify.__globals__
        saved = {
            key: namespace[key]
            for key in ("remote_ref_sha", "github_api", "git_command")
        }
        namespace["remote_ref_sha"] = lambda *_: "b" * 40
        namespace["github_api"] = lambda *_: self.fail(
            "advanced tip must fail before payload lookup"
        )
        namespace["git_command"] = lambda *_args, **_kwargs: self.fail(
            "advanced tip must fail before ancestry lookup"
        )
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "fence has advanced"
            ):
                verify(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg",
                    "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                    CLAIM_OWNER_SECRET, "a" * 40,
                )
        finally:
            namespace.update(saved)

    def test_repository_claim_renewal_is_fenced_by_exact_predecessor(self) -> None:
        renew = VALIDATOR_GLOBALS["renew_repository_claim"]
        namespace = renew.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "require_repository_claim_fence", "acquire_repository_claim",
            )
        }
        calls: list[tuple[str, tuple[object, ...]]] = []
        namespace["require_repository_claim_fence"] = (
            lambda *arguments, **kwargs: calls.append(
                ("verify", arguments + (kwargs["require_unexpired"],))
            ) or {}
        )
        namespace["acquire_repository_claim"] = (
            lambda *arguments, **_kwargs: calls.append(("acquire", arguments)) or {
                "ledger_id": "fmv3-pr91-v2", "generation": 4,
                "claim_sha": "c" * 40,
                "expires_at": "2026-08-01T12:00:00Z",
            }
        )
        try:
            fence = renew(
                Path("/unused"), "2" * 40,
                "Project-Helianthus/helianthus-modbusreg",
                "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                CLAIM_OWNER_SECRET, "a" * 40,
            )
        finally:
            namespace.update(saved)
        self.assertEqual([call[0] for call in calls], ["verify", "acquire"])
        self.assertFalse(calls[0][1][-1])
        self.assertEqual(calls[0][1][-2], "a" * 40)
        self.assertEqual(fence["generation"], 4)

    def test_repository_claim_renewal_rejects_tip_advanced_after_verification(self) -> None:
        renew = VALIDATOR_GLOBALS["renew_repository_claim"]
        namespace = renew.__globals__
        saved_verify = namespace["require_repository_claim_fence"]
        saved_remote = namespace["remote_ref_sha"]
        namespace["require_repository_claim_fence"] = lambda *_args, **_kwargs: {}
        namespace["remote_ref_sha"] = lambda *_: "b" * 40
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "renewal predecessor has advanced"
            ):
                renew(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg",
                    "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                    CLAIM_OWNER_SECRET, "a" * 40,
                )
        finally:
            namespace["require_repository_claim_fence"] = saved_verify
            namespace["remote_ref_sha"] = saved_remote

    def test_repository_claim_event_rejects_tampered_mac(self) -> None:
        require_event = VALIDATOR_GLOBALS["require_repository_claim_event"]
        namespace = require_event.__globals__
        observed = "a" * 40
        payload = claim_event()
        payload["issue_number"] = 51
        commit = {
            "sha": observed, "message": json.dumps(payload),
            "tree": {"sha": "b" * 40}, "parents": [{"sha": "2" * 40}],
        }
        with self.assertRaisesRegex(
            namespace["ValidationError"], "event MAC is invalid"
        ):
            require_event(
                commit, observed,
                "Project-Helianthus/helianthus-modbusreg",
                CLAIM_OWNER_SECRET,
            )

    def test_repository_claim_history_validates_release_and_reacquire_chain(self) -> None:
        require_history = VALIDATOR_GLOBALS["require_repository_claim_history"]
        namespace = require_history.__globals__
        original = namespace["github_api"]
        repository = "Project-Helianthus/helianthus-modbusreg"
        first_sha = "a" * 40
        release_sha = "b" * 40
        reacquire_sha = "c" * 40
        first = claim_event()
        released = claim_event(
            event="RELEASE", state="RELEASED", generation=2,
            previous_sha=first_sha, event_at="2026-08-01T03:00:00Z",
        )
        reacquired = claim_event(
            issue_id="FMV3-M2-03", issue_number=51,
            run_id="019fbe20-0000-7000-8000-000000000009",
            event="ACQUIRE", state="HELD", generation=3,
            previous_sha=release_sha, event_at="2026-08-01T04:00:00Z",
            expires_at="2026-08-01T10:00:00Z",
        )
        commits = {
            first_sha: {
                "sha": first_sha, "message": json.dumps(first),
                "tree": {"sha": "d" * 40},
                "parents": [{"sha": "2" * 40}],
            },
            release_sha: {
                "sha": release_sha, "message": json.dumps(released),
                "tree": {"sha": "d" * 40}, "parents": [{"sha": first_sha}],
            },
            reacquire_sha: {
                "sha": reacquire_sha, "message": json.dumps(reacquired),
                "tree": {"sha": "d" * 40},
                "parents": [{"sha": release_sha}],
            },
        }
        namespace["github_api"] = lambda endpoint: commits[endpoint.rsplit("/", 1)[1]]
        try:
            tip = require_history(
                commits[reacquire_sha], reacquire_sha, repository,
                CLAIM_OWNER_SECRET,
            )
        finally:
            namespace["github_api"] = original
        self.assertEqual(tip["generation"], 3)
        self.assertEqual(tip["event"], "ACQUIRE")

    def test_repository_claim_history_rejects_generation_gap(self) -> None:
        require_history = VALIDATOR_GLOBALS["require_repository_claim_history"]
        namespace = require_history.__globals__
        original = namespace["github_api"]
        repository = "Project-Helianthus/helianthus-modbusreg"
        first_sha = "a" * 40
        tip_sha = "c" * 40
        first = claim_event()
        skipped = claim_event(
            event="RENEW", generation=3, previous_sha=first_sha,
            event_at="2026-08-01T01:00:00Z",
            expires_at="2026-08-01T07:00:00Z",
        )
        first_commit = {
            "sha": first_sha, "message": json.dumps(first),
            "tree": {"sha": "d" * 40}, "parents": [{"sha": "2" * 40}],
        }
        tip_commit = {
            "sha": tip_sha, "message": json.dumps(skipped),
            "tree": {"sha": "d" * 40}, "parents": [{"sha": first_sha}],
        }
        namespace["github_api"] = lambda *_: first_commit
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "generation or tree continuity"
            ):
                require_history(
                    tip_commit, tip_sha, repository, CLAIM_OWNER_SECRET,
                )
        finally:
            namespace["github_api"] = original

    def test_repository_claim_event_rejects_noncanonical_ttl(self) -> None:
        require_event = VALIDATOR_GLOBALS["require_repository_claim_event"]
        namespace = require_event.__globals__
        observed = "a" * 40
        payload = claim_event(expires_at="2026-08-01T05:59:59Z")
        commit = {
            "sha": observed, "message": json.dumps(payload),
            "tree": {"sha": "b" * 40}, "parents": [{"sha": "2" * 40}],
        }
        with self.assertRaisesRegex(
            namespace["ValidationError"], "held-event TTL is invalid"
        ):
            require_event(
                commit, observed,
                "Project-Helianthus/helianthus-modbusreg",
                CLAIM_OWNER_SECRET,
            )

    def test_post_claim_repository_race_releases_exact_claim(self) -> None:
        preflight = VALIDATOR_GLOBALS["require_plan_owned_repository_preflight"]
        namespace = preflight.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "require_plan_owned_repository_snapshot", "acquire_repository_claim",
                "release_repository_claim", "require_repository_claim_control",
            )
        }
        calls = 0
        released: list[tuple[object, ...]] = []

        def snapshot(*_args) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise namespace["ValidationError"]("competing PR appeared")

        namespace["require_plan_owned_repository_snapshot"] = snapshot
        namespace["acquire_repository_claim"] = lambda *_args, **_kwargs: {
            "ledger_id": "fmv3-pr91-v2", "generation": 1,
            "claim_sha": "c" * 40, "expires_at": "2026-08-01T06:00:00Z",
        }
        namespace["require_repository_claim_control"] = lambda *_: None
        namespace["release_repository_claim"] = (
            lambda *arguments: released.append(arguments) or "d" * 40
        )
        try:
            with self.assertRaisesRegex(namespace["ValidationError"], "competing PR"):
                preflight(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg", "FMV3-M2-02",
                    50, "title", "marker", "1" * 40,
                    "019fbe20-0000-7000-8000-000000000001",
                    CLAIM_OWNER_SECRET,
                )
        finally:
            namespace.update(saved)
        self.assertEqual(len(released), 1)
        self.assertEqual(released[0][-1], "c" * 40)

    def test_repository_claim_release_requires_exact_anchor_and_run_owner(self) -> None:
        release = VALIDATOR_GLOBALS["release_repository_claim"]
        namespace = release.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "remote_ref_sha", "github_api", "git_command",
                "push_repository_claim_cas", "require_repository_claim_history",
            )
        }
        observed = "a" * 40
        release_sha = "c" * 40
        lookups = iter((observed, release_sha))
        pushes: list[tuple[str | None, str | None]] = []
        payload = claim_event(
            event="RENEW", state="HELD", generation=(
                namespace["REPOSITORY_CLAIM_MAX_HISTORY_EVENTS"] - 1
            ),
            previous_sha="9" * 40,
        )
        namespace["remote_ref_sha"] = lambda *_: next(lookups)
        namespace["github_api"] = lambda *_: {
            "sha": observed, "message": json.dumps(payload),
            "tree": {"sha": "b" * 40}, "parents": [{"sha": "9" * 40}],
        }
        namespace["require_repository_claim_history"] = (
            lambda *_args, **_kwargs: payload
        )
        def fake_git(_repo: Path, arguments: list[str], _label: str, **_kwargs):
            if arguments == ["rev-parse", "FETCH_HEAD^{commit}"]:
                return observed
            if "commit-tree" in arguments:
                self.assertEqual(arguments[arguments.index("-p") + 1], observed)
                release_payload = json.loads(arguments[arguments.index("-m") + 1])
                self.assertEqual(release_payload["state"], "RELEASED")
                self.assertEqual(
                    release_payload["generation"],
                    namespace["REPOSITORY_CLAIM_MAX_HISTORY_EVENTS"],
                )
                return release_sha
            return ""
        namespace["git_command"] = fake_git
        namespace["push_repository_claim_cas"] = (
            lambda _repo, _ref, expected, target: pushes.append((expected, target))
        )
        try:
            released = release(
                Path("/unused"), "2" * 40,
                "Project-Helianthus/helianthus-modbusreg",
                "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                CLAIM_OWNER_SECRET, observed,
                now=namespace["datetime"](
                    2026, 8, 1, 3, tzinfo=namespace["timezone"].utc
                ),
            )
        finally:
            namespace.update(saved)
        self.assertEqual(released, release_sha)
        self.assertEqual(pushes, [(observed, release_sha)])

        namespace = release.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "remote_ref_sha", "github_api", "git_command",
                "push_repository_claim_cas",
            )
        }
        namespace["remote_ref_sha"] = lambda *_: observed
        namespace["github_api"] = lambda *_: {
            "sha": observed, "message": json.dumps(payload),
            "tree": {"sha": "b" * 40}, "parents": [{"sha": "9" * 40}],
        }
        namespace["git_command"] = lambda *_args, **_kwargs: self.fail(
            "foreign claim must fail before history append"
        )
        namespace["push_repository_claim_cas"] = lambda *_: self.fail(
            "foreign claim must not be deleted"
        )
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "event MAC is invalid"
            ):
                release(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg",
                    "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                    "cd" * 32, observed,
                )
        finally:
            namespace.update(saved)

        namespace = release.__globals__
        saved = {
            key: namespace[key]
            for key in (
                "remote_ref_sha", "github_api", "git_command",
                "push_repository_claim_cas",
            )
        }
        namespace["remote_ref_sha"] = lambda *_: "b" * 40
        namespace["github_api"] = lambda *_: self.fail(
            "advanced claim must be rejected before payload lookup"
        )
        namespace["push_repository_claim_cas"] = lambda *_: self.fail(
            "advanced claim must not be deleted"
        )
        namespace["git_command"] = lambda *_args, **_kwargs: self.fail(
            "advanced claim must be rejected before history append"
        )
        try:
            with self.assertRaisesRegex(
                namespace["ValidationError"], "claim has advanced"
            ):
                release(
                    Path("/unused"), "2" * 40,
                    "Project-Helianthus/helianthus-modbusreg",
                    "FMV3-M2-02", 50, "1" * 40, CLAIM_RUN_ID,
                    CLAIM_OWNER_SECRET, observed,
                )
        finally:
            namespace.update(saved)

    def run_validator(
        self,
        root: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(root)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def clone_docs_candidate(self, directory: str) -> Path:
        source = Path(os.environ["FMV3_DOCS_CANDIDATE_ROOT"])
        candidate = Path(directory) / "docs-candidate"
        subprocess.run(
            ["git", "clone", str(source), str(candidate)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.git(
            candidate,
            "checkout",
            "--detach",
            PLAN_DATA["execution_authorization"]["authorization_anchor"][
                "docs_candidate_binding"
            ]["commit_sha"],
        )
        self.git(
            candidate,
            "remote",
            "set-url",
            "origin",
            "https://github.com/Project-Helianthus/helianthus-docs-ebus.git",
        )
        return candidate

    def git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def closing_issues_response(
        self, repository: str, issue_number: int
    ) -> dict[str, object]:
        return {
            "data": {
                "repository": {
                    "pullRequest": {
                        "closingIssuesReferences": {
                            "nodes": [{
                                "number": issue_number,
                                "repository": {"nameWithOwner": repository},
                            }],
                            "pageInfo": {
                                "hasNextPage": False,
                                "endCursor": None,
                            },
                        }
                    }
                }
            }
        }

    def closed_event_response(
        self,
        repository: str,
        issue_number: int,
        pull_request_number: int,
        merged_at: str,
        closed_at: str,
    ) -> dict[str, object]:
        return {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [{
                                "createdAt": closed_at,
                                "closer": {
                                    "__typename": "PullRequest",
                                    "number": pull_request_number,
                                    "mergedAt": merged_at,
                                    "repository": {"nameWithOwner": repository},
                                },
                            }],
                            "pageInfo": {
                                "hasNextPage": False,
                                "endCursor": None,
                            },
                        }
                    }
                }
            }
        }

    def completion_responses(self, binding: dict[str, object]) -> dict[str, object]:
        repository = str(binding["repository"])
        issue_number = int(binding["github_issue_number"])
        if binding.get("kind") == "manual_repository_creation":
            return {
                f"repos/{repository}/issues/{issue_number}": {
                    "number": issue_number, "repository_url": f"https://api.github.com/repos/{repository}",
                    "state": "closed", "closed_at": binding["closed_at"], "title": binding["issue_title"],
                },
                f"repos/{repository}/issues/{issue_number}/timeline?per_page=100": [
                    {"event": "closed", "created_at": binding["closed_at"], "actor": {"login": binding["closed_by"]}}
                ],
                f"repos/{repository}/issues/comments/{binding['completion_comment_id']}": {
                    "id": binding["completion_comment_id"], "user": {"login": binding["closed_by"]},
                    "created_at": "2026-07-26T15:23:55Z", "updated_at": "2026-07-26T15:23:55Z",
                    "body": "## Independent governance verification: PASS\n\nVerified read-only through authenticated GitHub REST and GraphQL APIs on 2026-07-26 15:08-15:11 UTC by a fresh OpenAI-only reviewer.\n\n- `Project-Helianthus/helianthus-modbus`: public, `isEmpty=true`, `diskUsage=0`, no default branch ref, zero refs, branches, commits, or contents.\n- `Project-Helianthus/helianthus-modbusreg`: public, `isEmpty=true`, `diskUsage=0`, no default branch ref, zero refs, branches, commits, or contents.\n- Git refs and commits endpoints return `409 Git Repository is empty` for both.\n- `helianthus-eebus-binding-private`: absent through admin-visible REST, GraphQL, and organization inventory.\n- `helianthus-matter-binding-private`: absent through admin-visible REST, GraphQL, and organization inventory.\n- Authorization PR Project-Helianthus/helianthus-execution-plans#72 is merged at `0576544bd8851c4e32da3ca7c401270eee43ef5c`; `origin/main` points to that exact commit.\n- CI: N/A because M0-01 intentionally created no Git objects or workflows.\n\nAcceptance gate: **PASS**. No blocking findings.",
                },
            }
        if binding.get("kind") == "docs_candidate_completion":
            return {}
        pr_number = int(binding["github_pull_request_number"])
        head_sha = str(binding["head_sha"])
        merge_sha = str(binding["merge_sha"])
        plan_issue = str(binding.get("plan_issue", ""))
        issue_spec = next(
            (item for item in PLAN_DATA["issues"] if item["id"] == plan_issue), None
        )
        issue_title = (
            str(binding["issue_title"])
            if "issue_title" in binding else ISSUE_SPEC_TITLE(issue_spec)
        )
        pull_request_title = (
            str(binding["pull_request_title"])
            if "pull_request_title" in binding else issue_title
        )
        issue_body = (
            ISSUE_SPEC_MARKER(ISSUE_SPEC_DIGEST(issue_spec))
            if issue_spec is not None else ""
        )
        seed = binding.get("bootstrap_seed")
        base_sha = (
            str(seed["commit_sha"]) if isinstance(seed, dict) else "e" * 40
        )
        main_sha = "f" * 40
        minute = issue_number % 60
        issue_created_at = f"2026-08-01T10:{minute:02d}:00Z"
        pr_created_at = f"2026-08-01T10:{minute:02d}:10Z"
        merged_at = f"2026-08-01T10:{minute:02d}:40Z"
        issue_closed_at = f"2026-08-01T10:{minute:02d}:50Z"
        responses = {
            f"repos/{repository}/issues/{issue_number}": {
                "number": issue_number, "repository_url": f"https://api.github.com/repos/{repository}",
                "state": "closed", "created_at": issue_created_at,
                "closed_at": issue_closed_at,
                "title": issue_title, "body": issue_body,
            },
            f"repos/{repository}/pulls/{pr_number}": {
                "number": pr_number, "title": pull_request_title, "state": "closed", "merged": True,
                "created_at": pr_created_at,
                "merged_at": merged_at, "merge_commit_sha": merge_sha,
                "body": f"Closes #{issue_number}.",
                "base": {"sha": base_sha, "ref": "main", "repo": {"full_name": repository}},
                "head": {
                    "sha": head_sha,
                    "ref": f"issue/{issue_number}-completion",
                    "repo": {"full_name": repository},
                },
            },
            f"repos/{repository}/git/commits/{head_sha}": {"sha": head_sha, "tree": {"sha": binding["head_tree_sha"]}},
            f"repos/{repository}/git/commits/{merge_sha}": {"sha": merge_sha, "tree": {"sha": binding["head_tree_sha"]}, "parents": [{"sha": base_sha}]},
            f"repos/{repository}/git/ref/heads/main": {"object": {"type": "commit", "sha": main_sha}},
            f"repos/{repository}/compare/{merge_sha}...{main_sha}": {"status": "ahead", "merge_base_commit": {"sha": merge_sha}},
            f"repos/{repository}/issues/{issue_number}/timeline?per_page=100": [{"event": "cross-referenced", "source": {"issue": {"number": pr_number, "pull_request": {"url": f"https://api.github.com/repos/{repository}/pulls/{pr_number}", "merged_at": merged_at}}}}],
            f"repos/{repository}/issues?state=all&sort=created&direction=asc&per_page=100&page=1": [{
                "number": issue_number, "title": issue_title, "state": "closed",
                "created_at": issue_created_at,
                "closed_at": issue_closed_at,
            }],
            f"repos/{repository}/pulls?state=all&sort=created&direction=asc&per_page=100&page=1": [{
                "number": pr_number, "created_at": pr_created_at,
                "closed_at": merged_at,
            }],
            f"graphql/closing-issues/{repository}/{pr_number}/FIRST": self.closing_issues_response(
                repository, issue_number
            ),
            f"graphql/closed-events/{repository}/{issue_number}/FIRST": self.closed_event_response(
                repository, issue_number, pr_number,
                merged_at, issue_closed_at,
            ),
            f"repos/{repository}/commits/{head_sha}/check-runs": {"check_runs": [{
                "id": (
                    binding["required_check_runs"][index]["check_run_id"]
                    if "required_check_runs" in binding else 1000 + index
                ),
                "name": check["context"] if isinstance(check, dict) else check,
                "head_sha": head_sha,
                "status": "completed",
                "conclusion": "success",
                "completed_at": f"2026-08-01T10:{minute:02d}:{15 + index:02d}Z",
                **({"app": {"id": check["app_id"]}}
                   if isinstance(check, dict) else {}),
            } for index, check in enumerate(binding["required_checks"])]},
        }
        if isinstance(seed, dict):
            responses[f"repos/{repository}/git/commits/{seed['commit_sha']}"] = {
                "sha": seed["commit_sha"],
                "tree": {"sha": seed["tree_sha"]},
                "parents": seed["parents"],
                "message": seed["message"],
            }
        return responses

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
        (repo / ".github/workflows").mkdir(parents=True)
        (repo / ".github/workflows/ci.yml").write_bytes(
            (ROOT / ".github/workflows/ci.yml").read_bytes()
        )
        (repo / "scripts").mkdir()
        (repo / "scripts/validate_modbus_docs_trust.py").write_bytes(
            (ROOT / "scripts/validate_modbus_docs_trust.py").read_bytes()
        )
        (repo / "scripts/fmv3_anchor_validator.py").write_bytes(
            (ROOT / "scripts/fmv3_anchor_validator.py").read_bytes()
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
        self.git(repo, "remote", "add", "origin", PLAN_CANONICAL_REMOTE)
        self.git(repo, "remote", "add", TEST_PUBLISH_REMOTE, str(remote))
        self.git(repo, "push", "-u", TEST_PUBLISH_REMOTE, "main")
        if PLAN_DATA["state"] != "locked":
            shutil.rmtree(anchored)
            copied = repo / PLAN.name
            shutil.copytree(PLAN, copied)
            self.git(repo, "add", "-A")
            self.git(repo, "commit", "-m", "enter current lifecycle")
            self.git(repo, "push", TEST_PUBLISH_REMOTE, "main")
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
        authorization_evidence: Path | None = None,
        selected_issue_number: int = 999999,
        claim_run_id: str = CLAIM_RUN_ID,
    ) -> subprocess.CompletedProcess[str]:
        plan = yaml.safe_load((plan_root / "plan.yaml").read_text(encoding="utf-8"))
        contract_digest = plan["execution_authorization"]["authorized_issue_contract_sha256"]
        repo = plan_root.parent
        with tempfile.TemporaryDirectory() as fake_bin:
            evidence_value = (
                str(authorization_evidence.resolve())
                if authorization_evidence is not None else ""
            )
            anchored_plan = yaml.safe_load(
                self.git(
                    repo,
                    "show",
                    f"{anchor_sha}:{PLAN.name}/plan.yaml",
                ).stdout
            )
            anchored_selected_spec = next(
                item for item in anchored_plan["issues"]
                if item["id"] == issue_id
            )
            route_receipt, route_receipt_sha256 = routing_receipt(
                anchored_selected_spec, anchor_sha
            )
            tooling = anchored_plan["execution_authorization"][
                "authorization_anchor"
            ]["tooling_binding"]
            validator_blob = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "show",
                    f"{anchor_sha}:{tooling['validator_path']}",
                ],
                check=True,
                capture_output=True,
            ).stdout
            self.assertEqual(
                hashlib.sha256(validator_blob).hexdigest(),
                tooling["validator_sha256"],
            )
            materialized_validator = Path(fake_bin) / "validate_plan.py"
            token_path = Path(fake_bin) / "one-use-token"
            token = "test-only-one-use-materialization-token"
            materialized_validator.write_bytes(validator_blob)
            materialized_validator.chmod(0o500)
            token_path.write_text(token, encoding="ascii")
            token_path.chmod(0o400)
            command = [
                sys.executable,
                str(materialized_validator),
                str(plan_root),
                "--authorize-issue",
                issue_id,
                "--github-issue-number",
                str(selected_issue_number),
                "--claim-run-id",
                claim_run_id,
                "--plan-head-sha",
                anchor_sha,
                "--authorization-contract-sha256",
                contract_digest,
                "--routing-receipt-base64",
                route_receipt,
                "--routing-receipt-sha256",
                route_receipt_sha256,
                "--materialized-anchor-validator",
            ]
            if evidence_value:
                command.extend(["--authorization-evidence", evidence_value])
            gh = Path(fake_bin) / "trusted-gh-fixture"
            gh.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "if os.environ.get('EXPECT_SANITIZED_GH_ENV') == '1' and any(\n"
                "    os.environ.get(name) for name in ('GH_HOST', 'GH_ENTERPRISE_TOKEN', 'GH_CONFIG_DIR', 'GH_REPO', 'GH_DEBUG')\n"
                "):\n"
                "    raise SystemExit(3)\n"
                "args = sys.argv[1:]\n"
                "if not args or args.pop(0) != 'api':\n"
                "    raise SystemExit(2)\n"
                "if args[:2] == ['--hostname', 'github.com']:\n"
                "    del args[:2]\n"
                "responses = json.loads(open(os.environ['FAKE_GH_RESPONSES_FILE'], encoding='utf-8').read())\n"
                "if args and args[0] == 'graphql':\n"
                "    fields = {}\n"
                "    index = 1\n"
                "    while index < len(args):\n"
                "        if args[index] in {'-f', '-F'} and index + 1 < len(args):\n"
                "            key, separator, value = args[index + 1].partition('=')\n"
                "            if separator:\n"
                "                fields[key] = value\n"
                "            index += 2\n"
                "        else:\n"
                "            index += 1\n"
                "    repository = fields.get('owner', '') + '/' + fields.get('name', '')\n"
                "    cursor = fields.get('cursor', 'FIRST')\n"
                "    kind = 'closed-events' if 'timelineItems' in fields.get('query', '') else 'closing-issues'\n"
                "    endpoint = f\"graphql/{kind}/{repository}/{fields.get('number', '')}/{cursor}\"\n"
                "elif len(args) == 1:\n"
                "    endpoint = args[0]\n"
                "else:\n"
                "    raise SystemExit(2)\n"
                "if endpoint not in responses:\n"
                "    raise SystemExit(2)\n"
                "print(json.dumps(responses[endpoint]))\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)
            for name in ("git", "gh"):
                attacker = Path(fake_bin) / name
                attacker.write_text("#!/bin/sh\nexit 97\n", encoding="ascii")
                attacker.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
            env["FMV3_ANCHOR_MATERIALIZATION_VALIDATOR"] = str(
                materialized_validator
            )
            env["FMV3_ANCHOR_MATERIALIZATION_SHA256"] = tooling[
                "validator_sha256"
            ]
            env["FMV3_ANCHOR_MATERIALIZATION_TOKEN"] = token
            env["FMV3_ANCHOR_MATERIALIZATION_TOKEN_FILE"] = str(token_path)
            trusted_git = Path("/usr/bin/git")
            env["FMV3_ANCHOR_MATERIALIZATION_GIT"] = str(trusted_git)
            env["FMV3_ANCHOR_MATERIALIZATION_GIT_SHA256"] = hashlib.sha256(
                trusted_git.read_bytes()
            ).hexdigest()
            env["FMV3_ANCHOR_MATERIALIZATION_GH"] = str(gh.resolve())
            env["FMV3_ANCHOR_MATERIALIZATION_GH_SHA256"] = hashlib.sha256(
                gh.read_bytes()
            ).hexdigest()
            responses = dict(github_responses or {})
            for binding in STATIC_DEPENDENCIES.values():
                for endpoint, value in self.completion_responses(binding).items():
                    responses.setdefault(endpoint, value)
            by_repository: dict[str, list[dict[str, object]]] = {}
            for binding in STATIC_DEPENDENCIES.values():
                if binding.get("kind") == "manual_repository_creation":
                    continue
                repository = str(binding["repository"])
                by_repository.setdefault(repository, []).append(binding)
            for repository, bindings in by_repository.items():
                issue_rows = []
                pr_rows = []
                for offset, binding in enumerate(bindings):
                    issue_rows.append({
                        "number": binding["github_issue_number"],
                        "title": binding["issue_title"], "state": "closed",
                        "created_at": f"2026-07-26T11:{offset:02d}:00Z",
                        "closed_at": f"2026-07-26T11:{offset:02d}:30Z",
                    })
                    pr_rows.append({
                        "number": binding["github_pull_request_number"],
                        "created_at": f"2026-07-26T11:{offset:02d}:10Z",
                        "closed_at": f"2026-07-26T11:{offset:02d}:20Z",
                    })
                issue_endpoint = (
                    f"repos/{repository}/issues?state=all&sort=created&direction=asc"
                    "&per_page=100&page=1"
                )
                existing_issues = responses.setdefault(issue_endpoint, [])
                assert isinstance(existing_issues, list)
                existing_issue_numbers = {
                    row.get("number")
                    for row in existing_issues
                    if isinstance(row, dict)
                }
                existing_issues.extend(
                    row for row in issue_rows
                    if row["number"] not in existing_issue_numbers
                )
                pr_endpoint = (
                    f"repos/{repository}/pulls?state=all&sort=created&direction=asc"
                    "&per_page=100&page=1"
                )
                existing_prs = responses.setdefault(pr_endpoint, [])
                assert isinstance(existing_prs, list)
                existing_pr_numbers = {
                    row.get("number")
                    for row in existing_prs
                    if isinstance(row, dict)
                }
                existing_prs.extend(
                    row for row in pr_rows
                    if row["number"] not in existing_pr_numbers
                )
            selected_spec = next(
                item for item in plan["issues"] if item["id"] == issue_id
            )
            selected_issue_endpoint = (
                f"repos/{selected_spec['repo']}/issues?state=all&sort=created"
                "&direction=asc&per_page=100&page=1"
            )
            selected_rows = responses.setdefault(selected_issue_endpoint, [])
            assert isinstance(selected_rows, list)
            if not any(
                isinstance(row, dict) and row.get("state") == "open"
                for row in selected_rows
            ):
                marker = (
                    ISSUE_SPEC_MARKER(ISSUE_SPEC_DIGEST(selected_spec))
                    if set(VALIDATOR_GLOBALS["ISSUE_SPEC_FIELDS"]) <= set(selected_spec)
                    else None
                )
                selected_rows.append({
                    "number": selected_issue_number,
                    "title": ISSUE_SPEC_TITLE(selected_spec),
                    "body": marker or "",
                    "state": "open",
                    "created_at": "2026-08-02T12:00:00Z",
                    "closed_at": None,
                })
            current_head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            responses.setdefault(
                f"repos/{PLAN_REPOSITORY}/git/ref/heads/main",
                {"object": {"type": "commit", "sha": current_head}},
            )
            responses.setdefault(
                "repos/Project-Helianthus/helianthus-execution-plans/pulls/91",
                amendment_pr or self.amendment_pr(anchor_sha),
            )
            live_pr = responses.get(
                "repos/Project-Helianthus/helianthus-execution-plans/pulls/91"
            )
            if isinstance(live_pr, dict):
                head_sha = live_pr.get("head", {}).get("sha", PR_HEAD_SHA)
                head_response = responses.setdefault(
                    f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{head_sha}",
                    {
                        "tree": {"sha": PR_TREE_SHA},
                        "committer": {"date": PR_HEAD_COMMITTED_AT},
                    },
                )
                if isinstance(head_response, dict):
                    head_response.setdefault(
                        "committer", {"date": PR_HEAD_COMMITTED_AT}
                    )
                merge_response = responses.setdefault(
                    f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{anchor_sha}",
                    {
                        "tree": {"sha": PR_TREE_SHA},
                        "parents": [
                            {
                                "sha": "6fd2b4a8d181f5133250a0f2f1380d057254db60"
                            }
                        ],
                    },
                )
                if isinstance(merge_response, dict):
                    merge_response.setdefault(
                        "parents",
                        [
                            {
                                "sha": "6fd2b4a8d181f5133250a0f2f1380d057254db60"
                            }
                        ],
                    )
                responses.setdefault(
                    f"repos/{PLAN_REPOSITORY}/compare/{anchor_sha}...{current_head}",
                    {"status": "ahead", "merge_base_commit": {"sha": anchor_sha}},
                )
                responses.setdefault(
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1",
                    [
                        self.review_attestation_comment(live_pr),
                    ],
                )
                responses.setdefault(
                    f"repos/{PLAN_REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}",
                    self.workflow_run(live_pr),
                )
                responses.setdefault(
                    f"repos/{PLAN_REPOSITORY}/pulls/91/reviews?per_page=100",
                    [self.official_review(live_pr), self.review_evidence(live_pr, 0), self.review_evidence(live_pr, 1)],
                )
                responses.setdefault(
                    f"repos/{PLAN_REPOSITORY}/pulls/91/reviews/{OFFICIAL_REVIEW_ID}/comments?per_page=100",
                    [],
                )
            for binding in STATIC_DEPENDENCIES.values():
                if binding.get("kind") in {"manual_repository_creation", "docs_candidate_completion"}:
                    continue
                repository = str(binding["repository"])
                ref = responses.get(f"repos/{repository}/git/ref/heads/main", {})
                main_sha = ref.get("object", {}).get("sha") if isinstance(ref, dict) else None
                if isinstance(main_sha, str):
                    responses.setdefault(
                        f"repos/{repository}/compare/{binding['merge_sha']}...{main_sha}",
                        {"status": "ahead", "merge_base_commit": {"sha": binding["merge_sha"]}},
                    )
            plan_ref = responses.get(f"repos/{PLAN_REPOSITORY}/git/ref/heads/main", {})
            live_plan_main = plan_ref.get("object", {}).get("sha") if isinstance(plan_ref, dict) else None
            if isinstance(live_plan_main, str):
                responses.setdefault(
                    f"repos/{PLAN_REPOSITORY}/compare/{anchor_sha}...{live_plan_main}",
                    {"status": "ahead", "merge_base_commit": {"sha": anchor_sha}},
                )
            # Completion validation now checks the complete PR interval history.
            # Keep the common fixture faithful when an individual test supplies a
            # dynamic certificate or docs completion response in addition to the
            # static dependency ledger: every selected PR must appear exactly once.
            pr_endpoints = re.compile(r"repos/([^/]+/[^/]+)/pulls/([1-9][0-9]*)$")
            selected_prs: dict[str, dict[int, dict[str, object]]] = {}
            for endpoint, value in responses.items():
                match = pr_endpoints.fullmatch(endpoint) if isinstance(endpoint, str) else None
                if (match is not None and isinstance(value, dict)
                        and value.get("number") == int(match.group(2))):
                    selected_prs.setdefault(match.group(1), {})[
                        int(match.group(2))
                    ] = value
            for repository, pull_requests in selected_prs.items():
                endpoint = (
                    f"repos/{repository}/pulls?state=all&sort=created&direction=asc"
                    "&per_page=100&page=1"
                )
                rows = responses.get(endpoint)
                if not isinstance(rows, list):
                    rows = []
                    responses[endpoint] = rows
                present = {
                    row.get("number") for row in rows if isinstance(row, dict)
                }
                for offset, number in enumerate(sorted(set(pull_requests) - present)):
                    minute = 10 + offset
                    direct = pull_requests[number]
                    rows.append({
                        "number": number,
                        "created_at": direct.get(
                            "created_at", f"2026-01-01T00:{minute:02d}:00Z"
                        ),
                        "closed_at": direct.get("closed_at", direct.get("merged_at")),
                    })
            issue_endpoints = re.compile(
                r"repos/([^/]+/[^/]+)/issues/([1-9][0-9]*)$"
            )
            selected_issues: dict[str, dict[int, dict[str, object]]] = {}
            for endpoint, value in responses.items():
                match = (
                    issue_endpoints.fullmatch(endpoint)
                    if isinstance(endpoint, str)
                    else None
                )
                if match is not None and isinstance(value, dict):
                    selected_issues.setdefault(match.group(1), {})[
                        int(match.group(2))
                    ] = value
            for repository, issues in selected_issues.items():
                endpoint = (
                    f"repos/{repository}/issues?state=all&sort=created&direction=asc"
                    "&per_page=100&page=1"
                )
                rows = responses.get(endpoint)
                if not isinstance(rows, list):
                    rows = []
                    responses[endpoint] = rows
                present = {
                    row.get("number") for row in rows if isinstance(row, dict)
                }
                for offset, number in enumerate(sorted(set(issues) - present)):
                    direct = issues[number]
                    minute = 10 + offset
                    state = direct.get("state", "closed")
                    row = {
                        "number": number,
                        "title": direct.get("title", ""),
                        "body": direct.get("body", ""),
                        "state": state,
                        "created_at": direct.get(
                            "created_at", f"2026-01-02T00:{minute:02d}:00Z"
                        ),
                        "closed_at": direct.get("closed_at"),
                    }
                    if state == "closed" and row["closed_at"] is None:
                        row["closed_at"] = (
                            f"2026-01-02T00:{minute:02d}:30Z"
                        )
                    rows.append(row)
            for endpoint, value in list(responses.items()):
                if (isinstance(endpoint, str) and "/issues?" in endpoint
                        and isinstance(value, list)):
                    for index, row in enumerate(value):
                        if not isinstance(row, dict) or row.get("pull_request"):
                            continue
                        minute = index % 60
                        row.setdefault(
                            "created_at", f"2026-01-01T00:{minute:02d}:00Z"
                        )
                        if row.get("state") == "closed":
                            row.setdefault(
                                "closed_at", f"2026-01-01T00:{minute:02d}:30Z"
                            )
                        else:
                            row.setdefault("closed_at", None)
                if isinstance(endpoint, str) and endpoint.endswith("/check-runs") and isinstance(value, dict):
                    rows = value.get("check_runs")
                    if isinstance(rows, list):
                        page = {**value, "total_count": len(rows)}
                        responses.setdefault(
                            endpoint + "?filter=latest&per_page=100&page=1", page
                        )
                        responses.setdefault(
                            endpoint + "?filter=latest&per_page=100&page=2",
                            {"total_count": len(rows), "check_runs": []},
                        )
                        responses.setdefault(
                            endpoint + "?filter=all&per_page=100&page=1", page
                        )
                        responses.setdefault(
                            endpoint + "?filter=all&per_page=100&page=2",
                            {"total_count": len(rows), "check_runs": []},
                        )
                if isinstance(endpoint, str) and endpoint.endswith("/jobs?per_page=100") and isinstance(value, dict):
                    rows = value.get("jobs")
                    if isinstance(rows, list):
                        page = {**value, "total_count": len(rows)}
                        responses.setdefault(endpoint + "&page=1", page)
                        responses.setdefault(
                            endpoint + "&page=2",
                            {"total_count": len(rows), "jobs": []},
                        )
                if isinstance(endpoint, str) and endpoint.endswith("?per_page=100") and isinstance(value, list):
                    responses.setdefault(endpoint + "&page=1", value)
                    responses.setdefault(endpoint + "&page=2", [])
            responses = {key: value for key, value in responses.items() if isinstance(key, str)}
            responses_file = Path(fake_bin) / "github-responses.json"
            responses_file.write_text(json.dumps(responses), encoding="utf-8")
            responses_file.chmod(0o600)
            env["FAKE_GH_RESPONSES_FILE"] = str(responses_file)
            namespace = VALIDATOR_GLOBALS["main"].__globals__
            saved = {
                key: namespace[key]
                for key in (
                    "require_materialized_validator_context",
                    "trusted_gh_command",
                    "TRUSTED_GIT_EXECUTABLE",
                    "TRUSTED_GH_EXECUTABLE",
                    "CLAIM_OWNER_SECRET",
                    "acquire_repository_claim",
                    "require_repository_claim_control",
                )
            }
            saved_argv = sys.argv
            saved_environment = os.environ.copy()
            saved_cwd = Path.cwd()

            def test_materialized_context() -> None:
                namespace["TRUSTED_GIT_EXECUTABLE"] = Path("/usr/bin/git")
                namespace["TRUSTED_GH_EXECUTABLE"] = Path("/test/pinned-gh")
                namespace["CLAIM_OWNER_SECRET"] = CLAIM_OWNER_SECRET

            def test_trusted_gh(arguments: list[str]) -> subprocess.CompletedProcess[str]:
                if arguments and arguments[0] == "graphql":
                    fields: dict[str, str] = {}
                    index = 1
                    while index < len(arguments):
                        if arguments[index] in {"-f", "-F"} and index + 1 < len(arguments):
                            key, separator, value = arguments[index + 1].partition("=")
                            if separator:
                                fields[key] = value
                            index += 2
                        else:
                            index += 1
                    repository = fields.get("owner", "") + "/" + fields.get("name", "")
                    cursor = fields.get("cursor", "FIRST")
                    kind = (
                        "closed-events"
                        if "timelineItems" in fields.get("query", "")
                        else "closing-issues"
                    )
                    endpoint = (
                        f"graphql/{kind}/{repository}/"
                        f"{fields.get('number', '')}/{cursor}"
                    )
                elif len(arguments) == 1:
                    endpoint = arguments[0]
                else:
                    raise AssertionError(f"unexpected trusted GH arguments: {arguments}")
                if endpoint not in responses:
                    raise AssertionError(f"missing GitHub fixture response: {endpoint}")
                return subprocess.CompletedProcess(
                    arguments, 0, json.dumps(responses[endpoint]), ""
                )

            stdout = io.StringIO()
            stderr = io.StringIO()
            namespace["require_materialized_validator_context"] = test_materialized_context
            namespace["trusted_gh_command"] = test_trusted_gh
            namespace["acquire_repository_claim"] = lambda *_args, **_kwargs: {
                "ledger_id": "fmv3-pr91-v2", "generation": 1,
                "claim_sha": "f" * 40, "expires_at": "2026-08-01T06:00:00Z",
            }
            namespace["require_repository_claim_control"] = lambda *_args: None
            namespace["TRUSTED_GIT_EXECUTABLE"] = Path("/usr/bin/git")
            try:
                sys.argv = command[1:]
                os.environ.clear()
                os.environ.update(env)
                os.chdir(ROOT)
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    returncode = namespace["main"]()
            finally:
                sys.argv = saved_argv
                os.environ.clear()
                os.environ.update(saved_environment)
                os.chdir(saved_cwd)
                namespace.update(saved)
            return subprocess.CompletedProcess(
                command, returncode, stdout.getvalue(), stderr.getvalue()
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
            self.git(repo, "push", TEST_PUBLISH_REMOTE, "main")
        return self.git(repo, "rev-parse", "HEAD").stdout.strip()

    def amendment_pr(
        self,
        anchor_sha: str,
        **overrides: object,
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "number": 91,
            "html_url": AMENDMENT_PR_URL,
            "state": "closed",
            "merged": True,
            "merge_commit_sha": anchor_sha,
            "merged_at": PR_MERGED_AT,
            "author_association": "OWNER",
            "user": {"login": "d3vi1"},
            "merged_by": {"login": "d3vi1"},
            "base": {
                "sha": "6fd2b4a8d181f5133250a0f2f1380d057254db60",
                "ref": "main",
                "repo": {"full_name": "Project-Helianthus/helianthus-execution-plans"},
            },
            "head": {
                "sha": anchor_sha,
                "ref": "issue/90-fmv3-capability-ledger-reconcile",
                "repo": {"full_name": "Project-Helianthus/helianthus-execution-plans"},
            },
        }
        value.update(overrides)
        return value

    def review_attestation_comment(
        self,
        pr: dict[str, object],
        **overrides: object,
    ) -> dict[str, object]:
        attestation: dict[str, object] = {
            "schema": "helianthus.fmv3-pr91-external-review-attestation.v1",
            "repository": PLAN_REPOSITORY,
            "pull_request": 91,
            "head_sha": pr.get("head", {}).get("sha", PR_HEAD_SHA),
            "head_tree_sha": PR_TREE_SHA,
            "verdict": "NO_FINDINGS",
            "review_process_attestation": "owner_attests_two_fresh_openai_contexts",
            "workflow_run_id": WORKFLOW_RUN_ID,
            "official_review_id": OFFICIAL_REVIEW_ID,
            "owner_review_ids": REVIEW_IDS,
            "trust_model": "owner_plus_authenticated_independent_review_v1",
            "post_merge_run_classification": "non_authoritative_same_change_set_execution",
        }
        comment: dict[str, object] = {
            "user": {"login": "d3vi1"},
            "author_association": "OWNER",
            "created_at": PR_ATTESTED_AT,
            "updated_at": PR_ATTESTED_AT,
        }
        attestation_overrides = overrides.pop("attestation", None)
        if isinstance(attestation_overrides, dict):
            attestation.update(attestation_overrides)
        comment.update(overrides)
        comment["body"] = (
            "<!-- helianthus-fmv3-pr91-external-review-attestation-v1 -->\n"
            "```json\n"
            f"{json.dumps(attestation, sort_keys=True)}\n"
            "```"
        )
        return comment

    def review_evidence(self, pr: dict[str, object], index: int) -> dict[str, object]:
        review = {
            "schema": "helianthus.fmv3-pr91-external-review-attestation.v1",
            "repository": PLAN_REPOSITORY,
            "pull_request": 91,
            "head_sha": pr.get("head", {}).get("sha", PR_HEAD_SHA),
            "head_tree_sha": PR_TREE_SHA,
            "verdict": "NO_FINDINGS",
            "attestation_kind": "owner_process_attestation",
            "review_process": "fresh_openai_context",
            "reviewer_run_reference": REVIEW_RUN_IDS[index],
            "output_digest_sha256": str(index + 3) * 64,
        }
        return {"id": REVIEW_IDS[index], "user": {"login": "d3vi1"}, "author_association": "OWNER", "state": "COMMENTED", "commit_id": pr.get("head", {}).get("sha", PR_HEAD_SHA), "submitted_at": "2026-07-30T10:0%s:00Z" % (2 + index), "body": json.dumps(review, sort_keys=True)}

    def official_review(self, pr: dict[str, object]) -> dict[str, object]:
        head_sha = pr.get("head", {}).get("sha", PR_HEAD_SHA)
        return {"id": OFFICIAL_REVIEW_ID, "user": {"login": "chatgpt-codex-connector[bot]"}, "state": "COMMENTED", "commit_id": head_sha, "submitted_at": "2026-07-30T10:02:30Z", "body": CODEX_REVIEW_BODY(head_sha)}

    def workflow_run(self, pr: dict[str, object]) -> dict[str, object]:
        merge_sha = pr.get("merge_commit_sha", "f" * 40)
        return {"id": WORKFLOW_RUN_ID, "workflow_id": 244018027, "event": "push", "status": "completed", "conclusion": "success", "head_sha": merge_sha, "head_branch": "main", "path": ".github/workflows/ci.yml", "actor": {"login": "d3vi1"}, "head_repository": {"full_name": PLAN_REPOSITORY}, "updated_at": "2026-07-30T10:25:00Z", "pull_requests": []}

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
            "repos/Project-Helianthus/helianthus-execution-plans/pulls/91": self.amendment_pr(
                amendment_anchor
            ),
            f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{PR_HEAD_SHA}": {
                "tree": {"sha": PR_TREE_SHA},
                "committer": {"date": PR_HEAD_COMMITTED_AT},
            },
            f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{amendment_anchor}": {
                "tree": {"sha": PR_TREE_SHA},
                "parents": [
                    {"sha": "6fd2b4a8d181f5133250a0f2f1380d057254db60"}
                ],
            },
            "repos/Project-Helianthus/helianthus-docs-ebus/pulls/376": {
                **self.completion_responses(STATIC_DEPENDENCIES["FMV3-M1-00"])[
                    "repos/Project-Helianthus/helianthus-docs-ebus/pulls/376"
                ],
                "merge_commit_sha": gate["docs_merge_sha"],
            },
            f"repos/Project-Helianthus/helianthus-docs-ebus/pulls/{gate['verification_pr']}": {
                "merged": True,
                "base": {"ref": "main"},
                "head": {"sha": gate["verification_head_sha"]},
            },
            "repos/Project-Helianthus/helianthus-docs-ebus/branches/main/protection/required_status_checks": {
                "contexts": [gate["required_check"]],
                "checks": [{
                    "context": gate["required_check"],
                    "app_id": GITHUB_ACTIONS_APP_ID,
                }],
            },
            f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{gate['verification_head_sha']}/check-runs": {
                "check_runs": [
                    {
                        "name": gate["required_check"],
                        "conclusion": "success",
                        "details_url": gate["required_check_run_url"],
                        "head_sha": gate["verification_head_sha"],
                        "status": "completed",
                        "app": {"id": GITHUB_ACTIONS_APP_ID},
                    }
                ]
            },
            "repos/Project-Helianthus/helianthus-docs-ebus/contents/.github/workflows/modbus-trusted-revision.yml?ref="
            f"{gate['docs_merge_sha']}": {
                "encoding": "base64",
                "content": base64.b64encode(workflow.encode("utf-8")).decode("ascii"),
            },
        }

    def docs_pr(self, *, merged: bool, **overrides: object) -> dict[str, object]:
        binding = PLAN_DATA["execution_authorization"]["authorization_anchor"][
            "docs_candidate_binding"
        ]
        identity = binding["pull_request_identity"]
        value: dict[str, object] = {
            "number": 386,
            "title": "FMV3-M1-05: define opaque runtime acquisition contract",
            "html_url": binding["pr_url"],
            "state": "closed" if merged else "open",
            "merged": merged,
            "merged_at": "2026-08-01T13:00:00Z" if merged else None,
            "merge_commit_sha": "a" * 40 if merged else None,
            "author_association": "MEMBER",
            "user": {"login": "d3vi1"},
            "merged_by": {"login": "d3vi1"} if merged else None,
            "body": "Documentation implementation.\n\nCloses #385",
            "base": {
                "sha": identity["base_sha"],
                "ref": identity["base_ref"],
                "repo": {"full_name": identity["base_repo"]},
            },
            "head": {
                "sha": binding["commit_sha"],
                "ref": identity["head_ref"],
                "repo": {"full_name": identity["head_repo"]},
            },
        }
        value.update(overrides)
        return value

    def docs_candidate_responses(self, *, merged: bool) -> dict[str, object]:
        binding = PLAN_DATA["execution_authorization"]["authorization_anchor"][
            "docs_candidate_binding"
        ]
        pr = self.docs_pr(merged=merged)
        responses: dict[str, object] = {
            "repos/Project-Helianthus/helianthus-docs-ebus/pulls/386": pr,
            "repos/Project-Helianthus/helianthus-docs-ebus/issues/385": {
                "number": 385,
                "repository_url": "https://api.github.com/repos/Project-Helianthus/helianthus-docs-ebus",
                "title": "FMV3-M1-05: define opaque runtime acquisition contract",
                "state": "closed" if merged else "open",
                "closed_at": "2026-08-01T13:00:00Z" if merged else None,
            },
            "repos/Project-Helianthus/helianthus-docs-ebus/issues/385/timeline?per_page=100": [{
                "event": "cross-referenced",
                "source": {"issue": {"number": 386, "pull_request": {
                    "url": "https://api.github.com/repos/Project-Helianthus/helianthus-docs-ebus/pulls/386",
                    "merged_at": "2026-08-01T13:00:00Z",
                }}},
            }] if merged else [],
            "graphql/closing-issues/Project-Helianthus/helianthus-docs-ebus/386/FIRST": (
                self.closing_issues_response(
                    "Project-Helianthus/helianthus-docs-ebus", 385
                ) if merged else self.closing_issues_response(
                    "Project-Helianthus/helianthus-docs-ebus", 999
                )
            ),
            "graphql/closed-events/Project-Helianthus/helianthus-docs-ebus/385/FIRST": (
                self.closed_event_response(
                    "Project-Helianthus/helianthus-docs-ebus", 385, 386,
                    "2026-08-01T13:00:00Z", "2026-08-01T13:00:00Z",
                ) if merged else self.closed_event_response(
                    "Project-Helianthus/helianthus-docs-ebus", 385, 999,
                    "2026-07-31T12:00:00Z", "2026-07-31T12:00:00Z",
                )
            ),
        }
        if merged:
            responses[
                f"repos/Project-Helianthus/helianthus-docs-ebus/git/commits/{binding['commit_sha']}"
            ] = {"tree": {"sha": binding["commit_tree_sha"]}}
            responses[
                f"repos/Project-Helianthus/helianthus-docs-ebus/git/commits/{pr['merge_commit_sha']}"
            ] = {
                "tree": {"sha": binding["commit_tree_sha"]},
                "parents": [{"sha": binding["pull_request_identity"]["base_sha"]}],
            }
            docs_main = "f" * 40
            responses["repos/Project-Helianthus/helianthus-docs-ebus/git/ref/heads/main"] = {"object": {"type": "commit", "sha": docs_main}}
            responses[f"repos/Project-Helianthus/helianthus-docs-ebus/compare/{pr['merge_commit_sha']}...{docs_main}"] = {"status": "ahead", "merge_base_commit": {"sha": pr["merge_commit_sha"]}}
            bound_checks = binding["required_check_runs"]
            responses["repos/Project-Helianthus/helianthus-docs-ebus/branches/main/protection/required_status_checks"] = {
                "contexts": [item["context"] for item in bound_checks],
                "checks": [
                    {"context": item["context"], "app_id": item["app_id"]}
                    for item in bound_checks
                ],
            }
            responses[f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{binding['commit_sha']}/check-runs"] = {
                "check_runs": [{
                    "id": item["check_run_id"], "name": item["context"],
                    "head_sha": binding["commit_sha"], "status": "completed",
                    "conclusion": "success",
                    "completed_at": f"2026-08-01T12:00:0{index + 1}Z",
                    "app": {"id": item["app_id"]},
                } for index, item in enumerate(bound_checks)]
            }
            owner_reviews = []
            for index in range(2):
                body = {"schema": "helianthus.fmv3-pr91-external-review-attestation.v1", "repository": "Project-Helianthus/helianthus-docs-ebus", "pull_request": 386, "head_sha": binding["commit_sha"], "head_tree_sha": binding["commit_tree_sha"], "verdict": "NO_FINDINGS", "attestation_kind": "owner_process_attestation", "review_process": "fresh_openai_context", "reviewer_run_reference": REVIEW_RUN_IDS[index], "output_digest_sha256": str(index + 3) * 64}
                owner_reviews.append({"id": 801 + index, "user": {"login": "d3vi1"}, "author_association": "OWNER", "state": "COMMENTED", "commit_id": binding["commit_sha"], "submitted_at": f"2026-08-01T12:00:0{4 + index}Z", "body": json.dumps(body, sort_keys=True)})
            responses["repos/Project-Helianthus/helianthus-docs-ebus/pulls/386/reviews?per_page=100"] = [{"id": 800, "user": {"login": "chatgpt-codex-connector[bot]"}, "state": "COMMENTED", "commit_id": binding["commit_sha"], "submitted_at": "2026-08-01T12:00:03Z", "body": CODEX_REVIEW_BODY(binding["commit_sha"])}, *owner_reviews]
            responses["repos/Project-Helianthus/helianthus-docs-ebus/pulls/386/reviews/800/comments?per_page=100"] = []
        return responses

    def dependency_certificate(
        self,
        plan_issue: str,
        repository: str,
        issue_number: int,
        pull_request_number: int,
        marker: str,
    ) -> dict[str, object]:
        issue_spec = next(item for item in PLAN_DATA["issues"] if item["id"] == plan_issue)
        certificate = {
            "plan_issue": plan_issue,
            "repository": repository,
            "github_issue_number": issue_number,
            "github_pull_request_number": pull_request_number,
            "issue_spec_sha256": ISSUE_SPEC_DIGEST(issue_spec),
            "head_sha": marker * 40,
            "head_tree_sha": chr(ord(marker) + 1) * 40,
            "merge_sha": chr(ord(marker) + 2) * 40,
            "required_checks": [
                {"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID},
                {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID},
            ],
            "required_check_runs": [
                {
                    "context": context,
                    "app_id": GITHUB_ACTIONS_APP_ID,
                    "check_run_id": 1000 + index,
                }
                for index, context in enumerate(("checks", "lint"))
            ],
        }
        return certificate

    def write_authorization_evidence(
        self,
        directory: str,
        authorization_issue: str,
        dependencies: list[dict[str, object]],
        *,
        include_producer: bool = False,
    ) -> Path:
        path = Path(directory) / f"{authorization_issue}-authorization-evidence.json"
        envelope: dict[str, object] = {
            "schema": "helianthus.fmv3-issue-authorization-evidence.v2",
            "authorization_issue": authorization_issue,
            "dependencies": dependencies,
        }
        if include_producer:
            dependency = next(item for item in dependencies if item["plan_issue"] == "FMV3-M1-06")
            envelope["producer"] = {
                key: dependency[key]
                for key in ("plan_issue", "repository", "github_issue_number", "github_pull_request_number", "merge_sha")
            }
            envelope["producer"].update({
                "red_commit_sha": M1_06_RED_SHA,
                "red_workflow_run_id": M1_06_RED_RUN_ID,
                "red_workflow_run_attempt": 1,
                "red_check_runs": [
                    {"context": M1_06_RED_GUARD_JOB_NAME, "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 910},
                    {"context": M1_06_CONFORMANCE_JOB_NAME, "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 911},
                ],
                "red_job_ids": [
                    {"name": M1_06_RED_GUARD_JOB_NAME, "job_id": 920},
                    {"name": M1_06_CONFORMANCE_JOB_NAME, "job_id": 921},
                ],
                "green_workflow_run_id": M1_06_GREEN_RUN_ID,
                "green_workflow_run_attempt": 1,
                "green_check_runs": [
                    {"context": M1_06_RED_GUARD_JOB_NAME, "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 960},
                    {"context": M1_06_CONFORMANCE_JOB_NAME, "app_id": GITHUB_ACTIONS_APP_ID, "check_run_id": 961},
                ],
                "green_job_ids": [
                    {"name": M1_06_RED_GUARD_JOB_NAME, "job_id": 950},
                    {"name": M1_06_CONFORMANCE_JOB_NAME, "job_id": 951},
                ],
                "harness_pull_request_number": M1_06_HARNESS_PR,
                "harness_merge_sha": M1_06_HARNESS_MERGE_SHA,
                "harness_workflow_id": M1_06_HARNESS_WORKFLOW_ID,
                "harness_required_check_runs": [
                    {
                        "context": check["context"],
                        "app_id": check["app_id"],
                        "check_run_id": 970 + index,
                    }
                    for index, check in enumerate(dependency["required_checks"])
                ],
                "harness_ci_run": {
                    "workflow_run_id": 8990,
                    "workflow_run_attempt": 1,
                    "job_id": 8990,
                    "check_run_id": 970,
                },
                "mutation_runs": [
                    {
                        "case_id": case_id,
                        "mutation_commit_sha": M1_06_MUTATION_SHAS[index],
                        "workflow_run_id": M1_06_MUTATION_RUN_IDS[index],
                        "workflow_run_attempt": 1,
                        "check_run_id": 9300 + index,
                        "job_id": 9400 + index,
                    }
                    for index, case_id in enumerate(M1_06_MUTATION_CASES)
                ],
                "official_review_id": M1_06_OFFICIAL_REVIEW_ID,
                "owner_review_ids": M1_06_OWNER_REVIEW_IDS,
            })
        path.write_text(
            json.dumps(envelope, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def write_m2_authorization_evidence(self, directory: str) -> Path:
        dependency = self.dependency_certificate(
            "FMV3-M1-06", "Project-Helianthus/helianthus-modbus", 42, 43, "a"
        )
        dependency["merge_sha"] = "b" * 40
        dependency["head_tree_sha"] = "d" * 40
        return self.write_authorization_evidence(
            directory, "FMV3-M2-01", [dependency], include_producer=True
        )

    def github_blob(self, content: bytes) -> tuple[str, dict[str, object]]:
        sha = hashlib.sha1(
            f"blob {len(content)}\0".encode("ascii") + content,
            usedforsecurity=False,
        ).hexdigest()
        return sha, {
            "sha": sha,
            "size": len(content),
            "encoding": "base64",
            "content": base64.b64encode(content).decode("ascii"),
        }

    def m1_06_conformance_responses(
        self, repository: str, head_tree_sha: str
    ) -> tuple[dict[str, object], str]:
        production_source = b"""package runtime

type OpaqueRuntimeCapability struct{}
type AttemptInstance struct{}
type TerminalOutcome int

func NewRuntimeAcquisition() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func (c *OpaqueRuntimeCapability) Claim() bool { return true }
func (a *AttemptInstance) CloseMembership() bool { return true }
func (a *AttemptInstance) CancelOpen() bool { return true }
func NewBoundedCapability() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func ReserveTerminalSequence() uint64 { return 1 }
func (outcome TerminalOutcome) IsTerminal() bool { return true }
"""
        test_source = b"""package runtime

import "testing"

func TestDeliverabilityExclusions(t *testing.T) {
	if NewRuntimeAcquisition() == nil { t.Fatal("missing runtime acquisition") }
}
func TestCopiedCapabilityOneWinner(t *testing.T) {
	if !NewRuntimeAcquisition().Claim() { t.Fatal("expected one winner") }
}
func TestStaleAttemptInstanceCancellationIsolation(t *testing.T) {
	if !(&AttemptInstance{}).CancelOpen() { t.Fatal("stale cancellation alias") }
}
func TestTerminalOutcomes(t *testing.T) {
	if !TerminalOutcome(0).IsTerminal() { t.Fatal("unexpected terminal outcome") }
}
func TestAttemptMembershipCloseRegistrationRace(t *testing.T) {
	if !(&AttemptInstance{}).CloseMembership() { t.Fatal("membership close race") }
}
func TestBoundsAndOverflow(t *testing.T) {
	if NewBoundedCapability() == nil { t.Fatal("missing bounded capability") }
}
func TestTerminalSequenceExhaustion(t *testing.T) {
	if ReserveTerminalSequence() == 0 { t.Fatal("zero terminal sequence") }
}
func TestCoalescedDependentIsolation(t *testing.T) {
	if NewRuntimeAcquisition() == NewRuntimeAcquisition() { t.Fatal("aliased isolated acquisition") }
}
"""
        responses: dict[str, object] = {}
        production_sha, production_blob = self.github_blob(production_source)
        test_sha, test_blob = self.github_blob(test_source)
        responses[f"repos/{repository}/git/blobs/{production_sha}"] = production_blob
        responses[f"repos/{repository}/git/blobs/{test_sha}"] = test_blob
        production_path = "capability.go"
        test_path = "capability_conformance_test.go"
        cases = [{
            "case_id": case_id,
            "test_function": specification[0],
            "source_path": test_path,
            "source_blob_sha": test_sha,
            "mode": "100644",
            "status": "PASS",
            "mutation_patch_sha256": m1_06_mutation_patch_digest(case_id),
        } for case_id, specification in M1_06_CASES.items()]
        report = {
            "schema": M1_06_REPORT_SCHEMA,
            "plan_issue": "FMV3-M1-06",
            "repository": repository,
            "contract_id": "OPAQUE_RUNTIME_ACQUISITION_V1",
            "case_digest": M1_06_CASE_DIGEST,
            "go_list": {
                "package_dir": ".",
                "package_query": ".",
                "package_name": "runtime",
                "import_path": "github.com/Project-Helianthus/helianthus-modbus",
                "goos": "linux",
                "goarch": "amd64",
                "cgo_enabled": "0",
                "gowork": "off",
                "go_files": [production_path],
                "compiled_go_files": [production_path],
                "test_go_files": [test_path],
                "ignored_go_files": [],
                "cgo_files": [],
                "c_files": [],
                "cxx_files": [],
                "m_files": [],
                "h_files": [],
                "f_files": [],
                "s_files": [],
                "swig_files": [],
                "swig_cxx_files": [],
                "syso_files": [],
                "x_test_go_files": [],
				"ignored_other_files": [],
				"embed_patterns": [],
				"embed_files": [],
				"test_embed_patterns": [],
				"test_embed_files": [],
				"x_test_embed_patterns": [],
				"x_test_embed_files": [],
            },
            "production": [{
                "path": production_path,
                "blob_sha": production_sha,
                "mode": "100644",
                "symbols": [
                    {**symbol, "signature": {
                        "OpaqueRuntimeCapability": "OpaqueRuntimeCapability",
                        "AttemptInstance": "AttemptInstance",
                        "TerminalOutcome": "TerminalOutcome",
                        "NewRuntimeAcquisition": "func() *OpaqueRuntimeCapability",
                        "Claim": "func() bool",
                        "CloseMembership": "func() bool",
                        "CancelOpen": "func() bool",
                        "NewBoundedCapability": "func() *OpaqueRuntimeCapability",
                        "ReserveTerminalSequence": "func() uint64",
                        "IsTerminal": "func() bool",
                    }[symbol["name"]]}
                    for symbol in M1_06_PRODUCTION_SYMBOLS
                ],
            }],
            "cases": cases,
        }
        report_bytes = (json.dumps(report, sort_keys=True) + "\n").encode("utf-8")
        report_sha, report_blob = self.github_blob(report_bytes)
        responses[f"repos/{repository}/git/blobs/{report_sha}"] = report_blob
        responses[f"repos/{repository}/git/trees/{head_tree_sha}?recursive=1"] = {
            "sha": head_tree_sha,
            "truncated": False,
            "tree": [
                {"path": "go.mod", "mode": "100644", "type": "blob", "sha": "0" * 40},
                {"path": production_path, "mode": "100644", "type": "blob", "sha": production_sha},
                {"path": test_path, "mode": "100644", "type": "blob", "sha": test_sha},
                {"path": M1_06_REPORT_PATH, "mode": "100644", "type": "blob", "sha": report_sha},
            ],
        }
        return responses, report_sha

    def m1_06_producer_responses(
        self,
        *,
        issue_number: int = 42,
        pull_request_number: int = 43,
        merge_sha: str = "b" * 40,
        main_sha: str = "c" * 40,
    ) -> dict[str, object]:
        repository = "Project-Helianthus/helianthus-modbus"
        dependency = self.dependency_certificate(
            "FMV3-M1-06", repository, issue_number, pull_request_number, "a"
        )
        dependency["merge_sha"] = merge_sha
        dependency["head_tree_sha"] = "d" * 40
        responses = self.completion_responses(dependency)
        responses[f"repos/{repository}/git/commits/{dependency['head_sha']}"][
            "message"
        ] = "feat: implement opaque runtime acquisition"
        issue_endpoint = f"repos/{repository}/issues/{issue_number}"
        pr_endpoint = f"repos/{repository}/pulls/{pull_request_number}"
        responses[issue_endpoint]["body"] = (
            f"{responses[issue_endpoint]['body']}\n{M1_06_ISSUE_MARKER}\n\n"
            "Implement the immutable plan-bound capability contract."
        )
        responses[issue_endpoint]["closed_at"] = "2026-08-01T13:00:00Z"
        issue_history_endpoint = (
            f"repos/{repository}/issues?state=all&sort=created&direction=asc"
            "&per_page=100&page=1"
        )
        responses[issue_history_endpoint][0]["closed_at"] = "2026-08-01T13:00:00Z"
        responses[pr_endpoint]["head"]["ref"] = (
            f"issue/{issue_number}-opaque-runtime-acquisition"
        )
        responses[pr_endpoint]["base"]["sha"] = M1_06_HARNESS_MERGE_SHA
        responses[pr_endpoint]["created_at"] = "2026-08-01T12:31:00Z"
        responses[pr_endpoint]["closed_at"] = "2026-08-01T13:00:00Z"
        responses[f"repos/{repository}/git/commits/{merge_sha}"]["parents"] = [
            {"sha": M1_06_HARNESS_MERGE_SHA}
        ]
        responses[pr_endpoint]["merged_at"] = "2026-08-01T13:00:00Z"
        timeline_endpoint = f"repos/{repository}/issues/{issue_number}/timeline?per_page=100"
        responses[timeline_endpoint][0]["source"]["issue"]["pull_request"]["merged_at"] = (
            "2026-08-01T13:00:00Z"
        )
        responses[
            f"graphql/closed-events/{repository}/{issue_number}/FIRST"
        ] = self.closed_event_response(
            repository, issue_number, pull_request_number,
            "2026-08-01T13:00:00Z", "2026-08-01T13:00:00Z",
        )
        responses[f"repos/{repository}/branches/main/protection/required_status_checks"] = {
            "contexts": [check["context"] for check in dependency["required_checks"]],
            "checks": list(dependency["required_checks"]),
        }
        responses[f"repos/{repository}/git/commits/{M1_06_RED_SHA}"] = {
            "sha": M1_06_RED_SHA,
            "message": M1_06_RED_COMMIT_SUBJECT,
            "tree": {"sha": "8" * 40},
            "parents": [{"sha": M1_06_HARNESS_MERGE_SHA}],
        }
        responses[f"repos/{repository}/commits/{M1_06_RED_SHA}?per_page=65&page=1"] = {
            "sha": M1_06_RED_SHA,
            "files": [{
                "filename": "capability_lifecycle_test.go",
                "status": "added",
                "changes": 120,
            }],
        }
        responses[f"repos/{repository}/commits/{M1_06_RED_SHA}?per_page=65&page=2"] = {
            "sha": M1_06_RED_SHA,
            "files": [],
        }
        responses[f"repos/{repository}/compare/{M1_06_RED_SHA}...{dependency['head_sha']}"] = {
            "status": "ahead",
            "merge_base_commit": {"sha": M1_06_RED_SHA},
        }
        pr_ref = f"issue/{issue_number}-opaque-runtime-acquisition"
        responses[f"repos/{repository}/actions/runs/{M1_06_RED_RUN_ID}"] = {
            "id": M1_06_RED_RUN_ID,
            "run_attempt": 1,
            "workflow_id": M1_06_HARNESS_WORKFLOW_ID,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "failure",
            "head_sha": M1_06_RED_SHA,
            "path": M1_06_MUTATION_WORKFLOW_PATH,
            "updated_at": "2026-08-01T12:40:00Z",
            "head_repository": {"full_name": repository},
            "pull_requests": [{
                "number": pull_request_number,
                "base": {"ref": "main", "repo": {"full_name": repository}},
                "head": {
                    "sha": M1_06_RED_SHA,
                    "ref": pr_ref,
                    "repo": {"full_name": repository},
                },
            }],
        }
        responses[
            f"repos/{repository}/actions/runs/{M1_06_RED_RUN_ID}/attempts/1"
        ] = responses[f"repos/{repository}/actions/runs/{M1_06_RED_RUN_ID}"]
        responses[f"repos/{repository}/commits/{M1_06_RED_SHA}/check-runs"] = {
            "check_runs": [{
                "id": 910,
                "name": M1_06_RED_GUARD_JOB_NAME,
                "head_sha": M1_06_RED_SHA,
                "status": "completed",
                "conclusion": "success",
                "completed_at": "2026-08-01T12:39:58Z",
                "details_url": f"https://github.com/{repository}/actions/runs/{M1_06_RED_RUN_ID}",
                "app": {"id": GITHUB_ACTIONS_APP_ID},
            }, {
                "id": 911,
                "name": M1_06_CONFORMANCE_JOB_NAME,
                "head_sha": M1_06_RED_SHA,
                "status": "completed",
                "conclusion": "failure",
                "completed_at": "2026-08-01T12:40:00Z",
                "details_url": f"https://github.com/{repository}/actions/runs/{M1_06_RED_RUN_ID}",
                "app": {"id": GITHUB_ACTIONS_APP_ID},
            }],
        }
        responses[f"repos/{repository}/actions/runs/{M1_06_RED_RUN_ID}/jobs?per_page=100"] = {
            "jobs": [{
                "id": 920,
                "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/910",
                "name": M1_06_RED_GUARD_JOB_NAME,
                "head_sha": M1_06_RED_SHA,
                "status": "completed",
                "conclusion": "success",
                "steps": [
                    {"number": 1, "name": M1_06_SETUP_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 2, "name": M1_06_RED_GUARD_STEP_NAME, "status": "completed", "conclusion": "success"},
                ],
            }, {
                "id": 921,
                "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/911",
                "name": M1_06_CONFORMANCE_JOB_NAME,
                "head_sha": M1_06_RED_SHA,
                "status": "completed",
                "conclusion": "failure",
                "steps": [
                    {"number": 1, "name": M1_06_DOCS_LOCK_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 2, "name": M1_06_SETUP_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 3, "name": M1_06_RED_COMPILE_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 4, "name": VALIDATOR_GLOBALS["M1_06_CONFORMANCE_GUARD_STEP_NAME"], "status": "completed", "conclusion": "success"},
                    {"number": 5, "name": M1_06_RED_TEST_STEP_NAME, "status": "completed", "conclusion": "failure"},
                ],
            }],
        }
        responses[
            f"repos/{repository}/actions/runs/{M1_06_RED_RUN_ID}/attempts/1/jobs?per_page=100"
        ] = responses[
            f"repos/{repository}/actions/runs/{M1_06_RED_RUN_ID}/jobs?per_page=100"
        ]
        responses[f"repos/{repository}/commits/{dependency['head_sha']}/check-runs"] = {
            "check_runs": [{
                "id": 1000 + index,
                "name": check["context"],
                "head_sha": dependency["head_sha"],
                "status": "completed",
                "conclusion": "success",
                "completed_at": f"2026-08-01T12:45:0{index + 1}Z",
                "details_url": (
                    f"https://github.com/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}"
                    if check["context"] == "checks" else
                    f"https://github.com/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}/jobs/{940 + index}"
                ),
                "app": {"id": check["app_id"]},
            } for index, check in enumerate(dependency["required_checks"])] + [{
                "id": 960,
                "name": M1_06_RED_GUARD_JOB_NAME,
                "head_sha": dependency["head_sha"],
                "status": "completed",
                "conclusion": "success",
                "completed_at": "2026-08-01T12:45:03Z",
                "details_url": f"https://github.com/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}",
                "app": {"id": GITHUB_ACTIONS_APP_ID},
            }, {
                "id": 961,
                "name": M1_06_CONFORMANCE_JOB_NAME,
                "head_sha": dependency["head_sha"],
                "status": "completed",
                "conclusion": "success",
                "completed_at": "2026-08-01T12:45:05Z",
                "details_url": f"https://github.com/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}",
                "app": {"id": GITHUB_ACTIONS_APP_ID},
            }]
        }
        responses[f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}"] = {
            "id": M1_06_GREEN_RUN_ID,
            "run_attempt": 1,
            "workflow_id": M1_06_HARNESS_WORKFLOW_ID,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
            "head_sha": dependency["head_sha"],
            "path": M1_06_MUTATION_WORKFLOW_PATH,
            "updated_at": "2026-08-01T12:45:05Z",
            "head_repository": {"full_name": repository},
            "pull_requests": [{
                "number": pull_request_number,
                "base": {"ref": "main", "repo": {"full_name": repository}},
                "head": {
                    "sha": dependency["head_sha"],
                    "ref": pr_ref,
                    "repo": {"full_name": repository},
                },
            }],
        }
        responses[
            f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}/attempts/1"
        ] = responses[f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}"]
        responses[f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}/jobs?per_page=100"] = {
            "jobs": [{
                "id": 950,
                "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/960",
                "name": M1_06_RED_GUARD_JOB_NAME,
                "head_sha": dependency["head_sha"],
                "status": "completed",
                "conclusion": "success",
                "steps": [
                    {"number": 1, "name": M1_06_SETUP_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 2, "name": M1_06_RED_GUARD_STEP_NAME, "status": "completed", "conclusion": "success"},
                ],
            }, {
                "id": 951,
                "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/961",
                "name": M1_06_CONFORMANCE_JOB_NAME,
                "head_sha": dependency["head_sha"],
                "status": "completed",
                "conclusion": "success",
                "steps": [
                    {"number": 1, "name": M1_06_DOCS_LOCK_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 2, "name": M1_06_SETUP_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 3, "name": M1_06_RED_COMPILE_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 4, "name": VALIDATOR_GLOBALS["M1_06_CONFORMANCE_GUARD_STEP_NAME"], "status": "completed", "conclusion": "success"},
                    {"number": 5, "name": M1_06_RED_TEST_STEP_NAME, "status": "completed", "conclusion": "success"},
                ],
            }],
        }
        responses[
            f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}/attempts/1/jobs?per_page=100"
        ] = responses[
            f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}/jobs?per_page=100"
        ]
        conformance_responses, report_sha = self.m1_06_conformance_responses(
            repository, str(dependency["head_tree_sha"])
        )
        responses.update(conformance_responses)
        workflow_bytes = (PLAN / "templates/fmv3-m1-06-mutation.yml").read_bytes()
        guard_bytes = (PLAN / "templates/fmv3_m1_06_mutation_guard.go").read_bytes()
        docs_lock_validator_bytes = (
            PLAN / "templates/fmv3_m1_06_docs_lock.py"
        ).read_bytes()
        docs_binding = PLAN_DATA["execution_authorization"]["authorization_anchor"][
            "docs_candidate_binding"
        ]
        docs_lock_bytes = (json.dumps({
            "schema": VALIDATOR_GLOBALS["M1_06_DOCS_LOCK_SCHEMA"],
            "repository": "Project-Helianthus/helianthus-docs-ebus",
            "pull_request": 386,
            "merged_docs_commit_sha": "a" * 40,
            "contract_id": "OPAQUE_RUNTIME_ACQUISITION_V1",
            "contract_version": 1,
            "content_revision": 1,
            "policy_path": docs_binding["policy_path"],
            "policy_sha256": docs_binding["policy_sha256"],
            "manifest_path": docs_binding["manifest_path"],
            "manifest_sha256": docs_binding["manifest_sha256"],
        }, sort_keys=True) + "\n").encode("utf-8")
        workflow_sha, workflow_blob = self.github_blob(workflow_bytes)
        guard_sha, guard_blob = self.github_blob(guard_bytes)
        docs_lock_validator_sha, docs_lock_validator_blob = self.github_blob(
            docs_lock_validator_bytes
        )
        docs_lock_sha, docs_lock_blob = self.github_blob(docs_lock_bytes)
        ci_sha, ci_blob = self.github_blob(b"name: CI\\n")
        ci_local_sha, ci_local_blob = self.github_blob(b"#!/bin/sh\\nexit 0\\n")
        responses.update({
            f"repos/{repository}/git/blobs/{workflow_sha}": workflow_blob,
            f"repos/{repository}/git/blobs/{guard_sha}": guard_blob,
            f"repos/{repository}/git/blobs/{docs_lock_validator_sha}": docs_lock_validator_blob,
            f"repos/{repository}/git/blobs/{docs_lock_sha}": docs_lock_blob,
            f"repos/{repository}/git/blobs/{ci_sha}": ci_blob,
            f"repos/{repository}/git/blobs/{ci_local_sha}": ci_local_blob,
        })
        base_tree_sha = M1_06_HARNESS_BASE_TREE_SHA
        harness_tree_sha = M1_06_HARNESS_TREE_SHA
        trusted_blobs = {
            ".github/workflows/ci.yml": ci_sha,
            "scripts/ci_local.sh": ci_local_sha,
            M1_06_MUTATION_WORKFLOW_PATH: workflow_sha,
            M1_06_MUTATION_GUARD_PATH: guard_sha,
            M1_06_DOCS_LOCK_VALIDATOR_PATH: docs_lock_validator_sha,
            M1_06_DOCS_LOCK_PATH: docs_lock_sha,
        }
        responses[f"repos/{repository}/git/commits/{M1_06_HARNESS_HEAD_SHA}"] = {
            "sha": M1_06_HARNESS_HEAD_SHA, "tree": {"sha": harness_tree_sha},
        }
        responses[f"repos/{repository}/git/commits/{M1_06_HARNESS_MERGE_SHA}"] = {
            "sha": M1_06_HARNESS_MERGE_SHA,
            "tree": {"sha": harness_tree_sha},
            "parents": [{"sha": M1_06_HARNESS_BASE_SHA}],
        }
        responses[f"repos/{repository}/git/commits/{M1_06_HARNESS_BASE_SHA}"] = {
            "sha": M1_06_HARNESS_BASE_SHA, "tree": {"sha": base_tree_sha},
        }
        responses[f"repos/{repository}/pulls/{M1_06_HARNESS_PR}"] = {
            "number": M1_06_HARNESS_PR,
            "title": "FMV3-M1-06: install trusted evidence harness",
            "state": "closed", "merged": True,
            "merge_commit_sha": M1_06_HARNESS_MERGE_SHA,
            "created_at": "2026-08-01T12:00:00Z",
            "closed_at": "2026-08-01T12:30:00Z",
            "merged_at": "2026-08-01T12:30:00Z",
            "author_association": "OWNER",
            "user": {"login": "d3vi1"}, "merged_by": {"login": "d3vi1"},
            "base": {"sha": M1_06_HARNESS_BASE_SHA, "ref": "main", "repo": {"full_name": repository}},
            "head": {
                "sha": M1_06_HARNESS_HEAD_SHA,
                "ref": f"issue/{issue_number}-evidence-harness",
                "repo": {"full_name": repository},
            },
        }
        responses[
            f"repos/{repository}/pulls?state=all&sort=created&direction=asc&per_page=100&page=1"
        ] = [
            {
                "number": M1_06_HARNESS_PR,
                "created_at": "2026-08-01T12:00:00Z",
                "closed_at": "2026-08-01T12:30:00Z",
            },
            {
                "number": pull_request_number,
                "created_at": "2026-08-01T12:31:00Z",
                "closed_at": "2026-08-01T13:00:00Z",
            },
        ]
        responses[f"repos/{repository}/commits/{M1_06_HARNESS_HEAD_SHA}/check-runs"] = {
            "check_runs": [{
                "id": 970 + index,
                "name": check["context"],
                "head_sha": M1_06_HARNESS_HEAD_SHA,
                "status": "completed",
                "conclusion": "success",
                "completed_at": f"2026-08-01T12:20:0{index + 1}Z",
                "details_url": f"https://github.com/{repository}/actions/runs/899{index}",
                "app": {"id": check["app_id"]},
            } for index, check in enumerate(dependency["required_checks"])]
        }
        responses[f"repos/{repository}/actions/runs/8990"] = {
            "id": 8990,
            "run_attempt": 1,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
            "head_sha": M1_06_HARNESS_HEAD_SHA,
            "head_repository": {"full_name": repository},
            "updated_at": "2026-08-01T12:20:01Z",
        }
        responses[f"repos/{repository}/actions/runs/8990/attempts/1"] = responses[
            f"repos/{repository}/actions/runs/8990"
        ]
        responses[f"repos/{repository}/actions/runs/8990/jobs?per_page=100"] = {
            "jobs": [{
                "id": 8990,
                "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/970",
                "name": M1_06_CI_JOB_NAME,
                "head_sha": M1_06_HARNESS_HEAD_SHA,
                "status": "completed",
                "conclusion": "success",
                "steps": [
                    {"number": 1, "name": M1_06_SETUP_STEP_NAME, "status": "completed", "conclusion": "success"},
                    {"number": 2, "name": M1_06_CI_STEP_NAME, "status": "completed", "conclusion": "success"},
                ],
            }],
        }
        responses[
            f"repos/{repository}/actions/runs/8990/attempts/1/jobs?per_page=100"
        ] = responses[f"repos/{repository}/actions/runs/8990/jobs?per_page=100"]
        harness_review_id = 979
        responses[f"repos/{repository}/pulls/{M1_06_HARNESS_PR}/reviews?per_page=100"] = [{
            "id": harness_review_id,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "state": "COMMENTED",
            "commit_id": M1_06_HARNESS_HEAD_SHA,
            "submitted_at": "2026-08-01T12:25:00Z",
            "body": CODEX_REVIEW_BODY(M1_06_HARNESS_HEAD_SHA),
        }]
        responses[
            f"repos/{repository}/pulls/{M1_06_HARNESS_PR}/reviews/"
            f"{harness_review_id}/comments?per_page=100"
        ] = []
        responses[f"repos/{repository}/pulls/{M1_06_HARNESS_PR}/files?per_page=100&page=1"] = [
            {"filename": M1_06_MUTATION_WORKFLOW_PATH, "status": "added"},
            {"filename": M1_06_MUTATION_GUARD_PATH, "status": "added"},
            {"filename": M1_06_DOCS_LOCK_VALIDATOR_PATH, "status": "added"},
            {"filename": M1_06_DOCS_LOCK_PATH, "status": "added"},
        ]
        responses[f"repos/{repository}/pulls/{M1_06_HARNESS_PR}/files?per_page=100&page=2"] = []
        def tree_rows(blobs: dict[str, str]) -> list[dict[str, str]]:
            return [
                {"path": path, "mode": "100644", "type": "blob", "sha": sha}
                for path, sha in blobs.items()
            ]
        responses[f"repos/{repository}/git/trees/{base_tree_sha}?recursive=1"] = {
            "sha": base_tree_sha, "truncated": False,
            "tree": tree_rows({key: trusted_blobs[key] for key in (
                ".github/workflows/ci.yml", "scripts/ci_local.sh",
            )}),
        }
        responses[f"repos/{repository}/git/trees/{harness_tree_sha}?recursive=1"] = {
            "sha": harness_tree_sha, "truncated": False, "tree": tree_rows(trusted_blobs),
        }
        product_tree = responses[
            f"repos/{repository}/git/trees/{dependency['head_tree_sha']}?recursive=1"
        ]
        product_tree["tree"].extend(tree_rows(trusted_blobs))
        responses[f"repos/{repository}/actions/workflows/{Path(M1_06_MUTATION_WORKFLOW_PATH).name}"] = {
            "id": M1_06_HARNESS_WORKFLOW_ID,
            "path": M1_06_MUTATION_WORKFLOW_PATH,
            "state": "active",
        }
        responses[f"repos/{repository}/compare/{M1_06_HARNESS_MERGE_SHA}...{main_sha}"] = {
            "status": "ahead", "merge_base_commit": {"sha": M1_06_HARNESS_MERGE_SHA},
        }
        mutation_selectors = []
        for index, (case_id, test_step_name) in enumerate(M1_06_MUTATION_CASES.items()):
            mutation_sha = M1_06_MUTATION_SHAS[index]
            mutation_run_id = M1_06_MUTATION_RUN_IDS[index]
            mutation_selectors.append({
                "case_id": case_id,
                "mutation_commit_sha": mutation_sha,
                "workflow_run_id": mutation_run_id,
                "workflow_run_attempt": 1,
                "check_run_id": 9300 + index,
                "job_id": 9400 + index,
            })
            responses[f"repos/{repository}/git/commits/{mutation_sha}"] = {
                "sha": mutation_sha,
                "tree": {"sha": f"{index + 1:02x}" * 20},
                "parents": [{"sha": dependency["head_sha"]}],
            }
            responses[f"repos/{repository}/commits/{mutation_sha}?per_page=65&page=1"] = {
                "sha": mutation_sha,
                "files": [{
                    "filename": "capability.go",
                    "status": "modified",
                    "changes": 2,
                    "patch": m1_06_mutation_patch(case_id),
                }],
            }
            responses[f"repos/{repository}/commits/{mutation_sha}?per_page=65&page=2"] = {
                "sha": mutation_sha,
                "files": [],
            }
            check_name = f"mutation/{case_id}"
            responses[f"repos/{repository}/actions/runs/{mutation_run_id}"] = {
                "id": mutation_run_id,
                "run_attempt": 1,
                "workflow_id": M1_06_HARNESS_WORKFLOW_ID,
                "event": "workflow_dispatch",
                "status": "completed",
                "conclusion": "failure",
                "head_sha": mutation_sha,
                "path": M1_06_MUTATION_WORKFLOW_PATH,
                "actor": {"login": "d3vi1"},
                "head_repository": {"full_name": repository},
                "updated_at": f"2026-08-01T12:46:{20 + index:02d}Z",
            }
            responses[
                f"repos/{repository}/actions/runs/{mutation_run_id}/attempts/1"
            ] = responses[f"repos/{repository}/actions/runs/{mutation_run_id}"]
            responses[f"repos/{repository}/commits/{mutation_sha}/check-runs"] = {
                "check_runs": [{
                    "id": 9300 + index,
                    "name": check_name,
                    "head_sha": mutation_sha,
                    "status": "completed",
                    "conclusion": "failure",
                    "completed_at": f"2026-08-01T12:46:{20 + index:02d}Z",
                    "details_url": f"https://github.com/{repository}/actions/runs/{mutation_run_id}",
                    "app": {"id": GITHUB_ACTIONS_APP_ID},
                }],
            }
            responses[f"repos/{repository}/actions/runs/{mutation_run_id}/jobs?per_page=100"] = {
                "jobs": [{
                    "id": 9400 + index,
                    "check_run_url": (
                        f"https://api.github.com/repos/{repository}/check-runs/"
                        f"{9300 + index}"
                    ),
                    "name": check_name,
                    "head_sha": mutation_sha,
                    "status": "completed",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": M1_06_DOCS_LOCK_STEP_NAME, "status": "completed", "conclusion": "success"},
                        {"number": 2, "name": M1_06_SETUP_STEP_NAME, "status": "completed", "conclusion": "success"},
                        {"number": 3, "name": M1_06_MUTATION_AST_STEP_NAME, "status": "completed", "conclusion": "success"},
                        {"number": 4, "name": f"baseline/{case_id}", "status": "completed", "conclusion": "success"},
                        {"number": 5, "name": M1_06_MUTATION_COMPILE_STEP_NAME, "status": "completed", "conclusion": "success"},
                        {"number": 6, "name": f"mutant/{case_id}", "status": "completed", "conclusion": "failure"},
                    ],
                }],
            }
            responses[
                f"repos/{repository}/actions/runs/{mutation_run_id}/attempts/1/jobs?per_page=100"
            ] = responses[
                f"repos/{repository}/actions/runs/{mutation_run_id}/jobs?per_page=100"
            ]
            mutation_tree_sha = f"{index + 1:02x}" * 20
            responses[f"repos/{repository}/git/trees/{mutation_tree_sha}?recursive=1"] = {
                "sha": mutation_tree_sha, "truncated": False,
                "tree": tree_rows(trusted_blobs),
            }
        mutation_digest = hashlib.sha256(json.dumps(
            mutation_selectors, sort_keys=True, separators=(",", ":")
        ).encode("ascii")).hexdigest()
        owner_reviews = []
        for index, review_id in enumerate(M1_06_OWNER_REVIEW_IDS):
            body = {
                "schema": M1_06_REVIEW_SCHEMA,
                "repository": repository,
                "pull_request": pull_request_number,
                "plan_issue": "FMV3-M1-06",
                "red_commit_sha": M1_06_RED_SHA,
                "head_sha": dependency["head_sha"],
                "head_tree_sha": dependency["head_tree_sha"],
                "verdict": "NO_FINDINGS",
                "attestation_kind": "owner_process_attestation",
                "review_process": "fresh_openai_context",
                "reviewer_run_reference": REVIEW_RUN_IDS[index],
                "output_digest_sha256": str(index + 5) * 64,
                "conformance_report_blob_sha": report_sha,
                "conformance_case_digest": M1_06_CASE_DIGEST,
                "mutation_evidence_sha256": mutation_digest,
            }
            owner_reviews.append({
                "id": review_id,
                "user": {"login": "d3vi1"},
                "author_association": "OWNER",
                "state": "COMMENTED",
                "commit_id": dependency["head_sha"],
                "submitted_at": f"2026-08-01T12:57:0{index}Z",
                "body": json.dumps(body, sort_keys=True),
            })
        responses[f"repos/{repository}/pulls/{pull_request_number}/reviews?per_page=100"] = [{
            "id": M1_06_OFFICIAL_REVIEW_ID,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "state": "COMMENTED",
            "commit_id": dependency["head_sha"],
            "submitted_at": "2026-08-01T12:56:00Z",
            "body": CODEX_REVIEW_BODY(str(dependency["head_sha"])),
        }, *owner_reviews]
        responses[
            f"repos/{repository}/pulls/{pull_request_number}/reviews/{M1_06_OFFICIAL_REVIEW_ID}/comments?per_page=100"
        ] = []
        if main_sha != "f" * 40:
            default_main = "f" * 40
            responses[f"repos/{repository}/git/ref/heads/main"] = {"object": {"type": "commit", "sha": main_sha}}
            responses[f"repos/{repository}/compare/{merge_sha}...{main_sha}"] = responses.pop(
                f"repos/{repository}/compare/{merge_sha}...{default_main}"
            )
        return responses

    def dynamic_dependency_responses(
        self, dependency: dict[str, object]
    ) -> dict[str, object]:
        responses = self.completion_responses(dependency)
        repository = str(dependency["repository"])
        responses[f"repos/{repository}/branches/main/protection/required_status_checks"] = {
            "contexts": [check["context"] for check in dependency["required_checks"]],
            "checks": list(dependency["required_checks"]),
        }
        return responses

    def authorize_m2_01_producer_case(
        self,
        temp: str,
        mutate: Callable[[dict[str, object]], None],
    ) -> subprocess.CompletedProcess[str]:
        implementing, anchor = self.published_plan(temp)
        anchor = self.publish_amendment_reference(implementing)
        evidence = self.write_m2_authorization_evidence(temp)
        responses = self.m1_admission_responses(implementing, anchor)
        responses.update(self.docs_candidate_responses(merged=True))
        producer_responses = self.m1_06_producer_responses()
        mutate(producer_responses)
        responses.update(producer_responses)
        return self.authorize(
            implementing,
            anchor,
            "FMV3-M2-01",
            github_responses=responses,
            authorization_evidence=evidence,
        )

    def rewrite_m1_06_report(
        self,
        responses: dict[str, object],
        *,
        replace_path: str | None = None,
        replacement: bytes | None = None,
        mutate_report: Callable[[dict[str, object]], None] | None = None,
    ) -> None:
        repository = "Project-Helianthus/helianthus-modbus"
        tree_endpoint = f"repos/{repository}/git/trees/{'d' * 40}?recursive=1"
        tree = responses[tree_endpoint]["tree"]
        report_entry = next(item for item in tree if item["path"] == M1_06_REPORT_PATH)
        report_response = responses[f"repos/{repository}/git/blobs/{report_entry['sha']}"]
        report = json.loads(base64.b64decode(report_response["content"]))
        if replace_path is not None:
            assert replacement is not None
            replacement_sha, replacement_blob = self.github_blob(replacement)
            responses[f"repos/{repository}/git/blobs/{replacement_sha}"] = replacement_blob
            next(item for item in tree if item["path"] == replace_path)["sha"] = replacement_sha
            for production in report["production"]:
                if production["path"] == replace_path:
                    production["blob_sha"] = replacement_sha
            for case in report["cases"]:
                if case["source_path"] == replace_path:
                    case["source_blob_sha"] = replacement_sha
        if mutate_report is not None:
            mutate_report(report)
        report_sha, report_blob = self.github_blob(
            (json.dumps(report, sort_keys=True) + "\n").encode("utf-8")
        )
        responses[f"repos/{repository}/git/blobs/{report_sha}"] = report_blob
        report_entry["sha"] = report_sha
        reviews_endpoint = f"repos/{repository}/pulls/43/reviews?per_page=100"
        for review in responses[reviews_endpoint][1:]:
            body = json.loads(review["body"])
            body["conformance_report_blob_sha"] = report_sha
            review["body"] = json.dumps(body, sort_keys=True)

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
        (repo / "scripts").mkdir()
        (repo / "scripts/fmv3_anchor_validator.py").write_bytes(
            (ROOT / "scripts/fmv3_anchor_validator.py").read_bytes()
        )
        (repo / ".github/workflows").mkdir(parents=True)
        (repo / ".github/workflows/ci.yml").write_bytes(
            (ROOT / ".github/workflows/ci.yml").read_bytes()
        )
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
        self.git(repo, "remote", "add", "origin", PLAN_CANONICAL_REMOTE)
        self.git(repo, "remote", "add", TEST_PUBLISH_REMOTE, str(remote))
        self.git(repo, "push", "-u", TEST_PUBLISH_REMOTE, "main")

        mutate_current(plan_root)
        self.rewrite_amendment_surface_digest(plan_root)
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "restore current authorization snapshot")
        self.git(repo, "push", TEST_PUBLISH_REMOTE, "main")
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
        self.git(repo, "push", TEST_PUBLISH_REMOTE, "main")
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
        self.git(repo, "push", TEST_PUBLISH_REMOTE, "main")

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
            dependency = self.dependency_certificate(
                "FMV3-M3-02", "Project-Helianthus/helianthus-modbusreg", 68, 69, "1"
            )
            evidence = self.write_authorization_evidence(temp, "FMV3-M3-03", [dependency])
            responses = self.dynamic_dependency_responses(dependency)
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M3-03",
                self.amendment_pr(anchor),
                responses,
                evidence,
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

    def test_m1_admission_rejects_mixed_legacy_required_check_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(plan_root)
            responses = self.m1_admission_responses(plan_root, anchor)
            policy = (
                "repos/Project-Helianthus/helianthus-docs-ebus/branches/main/"
                "protection/required_status_checks"
            )
            responses[policy]["contexts"].append("legacy-unbound")
            result = self.authorize(
                plan_root, anchor, "FMV3-M1-01",
                self.amendment_pr(anchor), responses,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "legacy context without an app-bound check", result.stderr,
            )

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

    def test_direct_internal_materialization_flag_is_rejected(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(PLAN),
                "--authorize-issue",
                "FMV3-M1-05",
                "--plan-head-sha",
                "1" * 40,
                "--authorization-contract-sha256",
                PLAN_DATA["execution_authorization"][
                    "authorized_issue_contract_sha256"
                ],
                "--materialized-anchor-validator",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "direct use of --materialized-anchor-validator is forbidden",
            result.stderr,
        )

    def test_direct_unmaterialized_authorization_is_rejected(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(PLAN),
                "--authorize-issue",
                "FMV3-M1-05",
                "--plan-head-sha",
                "1" * 40,
                "--authorization-contract-sha256",
                PLAN_DATA["execution_authorization"][
                    "authorized_issue_contract_sha256"
                ],
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "trusted cruise-preflight anchor materializer",
            result.stderr,
        )

    def test_authorization_rejects_noncanonical_origin_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            self.git(
                plan_root.parent,
                "remote",
                "set-url",
                "origin",
                "https://example.invalid/not-canonical.git",
            )
            result = self.authorize(plan_root, anchor, "FMV3-M1-05")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("origin is not the canonical", result.stderr)

    def test_authorization_rejects_noncanonical_origin_push_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            self.git(
                plan_root.parent,
                "remote",
                "set-url",
                "--push",
                "origin",
                "https://example.invalid/not-canonical.git",
            )
            result = self.authorize(plan_root, anchor, "FMV3-M1-05")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("origin is not the canonical", result.stderr)

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
            self.assertIn("canonical main branch checkout", result.stderr)

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
            advanced = self.git(other, "rev-parse", "HEAD").stdout.strip()
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M0-02",
                github_responses={
                    f"repos/{PLAN_REPOSITORY}/git/ref/heads/main": {
                        "object": {"type": "commit", "sha": advanced}
                    }
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly at canonical GitHub main", result.stderr)

    def test_untracked_file_outside_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            (plan_root.parent / "outside-plan.txt").write_text("dirty\n", encoding="utf-8")
            result = self.authorize(plan_root, anchor, "FMV3-M3-03")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("fully clean checkout", result.stderr)

    def test_modified_file_outside_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor = self.published_plan(temp)
            (plan_root.parent / "repository-marker.txt").write_text("modified\n", encoding="utf-8")
            result = self.authorize(plan_root, anchor, "FMV3-M3-03")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("fully clean checkout", result.stderr)

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

    def test_m1_06_requires_exact_merged_docs_r2_head_and_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses[
                "repos/Project-Helianthus/helianthus-docs-ebus/pulls/386"
            ].update(
                {
                    "state": "open",
                    "merged": False,
                    "merged_at": None,
                    "merge_commit_sha": None,
                    "merged_by": None,
                }
            )
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-06",
                github_responses=responses,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("docs closing PR #386 identity mismatch", result.stderr)

    def test_m1_06_authorizes_after_exact_docs_r2_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-06",
                github_responses=responses,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fail-closed execution allowlist", result.stdout)

    def test_m1_06_rejects_docs_required_check_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            binding = PLAN_DATA["execution_authorization"]["authorization_anchor"]["docs_candidate_binding"]
            checks = responses[f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{binding['commit_sha']}/check-runs"]
            checks["check_runs"][0]["conclusion"] = "failure"
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exact-head required check failed", result.stderr)

    def test_m1_06_rejects_docs_same_name_wrong_app(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            binding = PLAN_DATA["execution_authorization"]["authorization_anchor"]["docs_candidate_binding"]
            checks = responses[f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{binding['commit_sha']}/check-runs"]
            checks["check_runs"][0]["app"] = {"id": 9999}
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"{binding['required_check_runs'][0]['context']}@15368", result.stderr)

    def test_m1_06_docs_certificate_survives_later_same_name_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            binding = PLAN_DATA["execution_authorization"]["authorization_anchor"]["docs_candidate_binding"]
            endpoint = f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{binding['commit_sha']}/check-runs"
            original = responses[endpoint]["check_runs"][0]
            responses[endpoint]["check_runs"].append({
                **original, "id": original["id"] + 100000,
                "completed_at": "2026-08-01T14:00:00Z",
            })
            result = self.authorize(
                implementing, anchor, "FMV3-M1-06", github_responses=responses,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_m1_06_rejects_docs_codex_inline_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses["repos/Project-Helianthus/helianthus-docs-ebus/pulls/386/reviews/800/comments?per_page=100"] = [{"id": 1}]
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("official Codex review has inline findings", result.stderr)

    def test_m1_06_rejects_docs_malicious_codex_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            endpoint = "repos/Project-Helianthus/helianthus-docs-ebus/pulls/386/reviews?per_page=100"
            responses[endpoint][0]["body"] += "\nP2 arbitrary finding"
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires one official Codex", result.stderr)

    def test_m1_06_rejects_malformed_or_reused_docs_owner_review_identity(self) -> None:
        endpoint = (
            "repos/Project-Helianthus/helianthus-docs-ebus/"
            "pulls/386/reviews?per_page=100"
        )
        for mutation, expected in (
            ("malformed_run", "structured owner-attested"),
            ("duplicate_run", "independently distinct"),
            ("duplicate_digest", "independently distinct"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                implementing, anchor = self.published_plan(temp)
                anchor = self.publish_amendment_reference(implementing)
                responses = self.m1_admission_responses(implementing, anchor)
                responses.update(self.docs_candidate_responses(merged=True))
                first = json.loads(responses[endpoint][1]["body"])
                second = json.loads(responses[endpoint][2]["body"])
                if mutation == "malformed_run":
                    second["reviewer_run_reference"] = "-" * 36
                elif mutation == "duplicate_run":
                    second["reviewer_run_reference"] = first[
                        "reviewer_run_reference"
                    ]
                else:
                    second["output_digest_sha256"] = first[
                        "output_digest_sha256"
                    ]
                responses[endpoint][2]["body"] = json.dumps(
                    second, sort_keys=True,
                )
                result = self.authorize(
                    implementing, anchor, "FMV3-M1-06",
                    github_responses=responses,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)

    def test_m1_06_rejects_m1_05_wrong_issue_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses["repos/Project-Helianthus/helianthus-docs-ebus/issues/385"]["title"] = "FMV3-M1-05: lookalike"
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("issue #385 identity/title/closure mismatch", result.stderr)

    def test_m1_06_rejects_m1_05_missing_closes_relation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses["repos/Project-Helianthus/helianthus-docs-ebus/pulls/386"]["body"] = "No closing keyword"
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not close exact issue #385", result.stderr)

    def test_m1_06_rejects_m1_05_missing_timeline_relation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses["repos/Project-Helianthus/helianthus-docs-ebus/issues/385/timeline?per_page=100"] = []
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks exact PR #386 timeline relation", result.stderr)

    def test_m1_06_rejects_m1_05_issue_closed_before_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses["repos/Project-Helianthus/helianthus-docs-ebus/issues/385"]["closed_at"] = "2026-07-31T11:59:59Z"
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("closure is not within the bounded post-merge window", result.stderr)

    def test_m1_06_accepts_m1_05_one_second_auto_close_delay(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses[
                "repos/Project-Helianthus/helianthus-docs-ebus/issues/385"
            ]["closed_at"] = "2026-08-01T13:00:01Z"
            responses[
                "graphql/closed-events/Project-Helianthus/helianthus-docs-ebus/385/FIRST"
            ]["data"]["repository"]["issue"]["timelineItems"]["nodes"][0][
                "createdAt"
            ] = "2026-08-01T13:00:01Z"
            result = self.authorize(
                implementing, anchor, "FMV3-M1-06", github_responses=responses
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_m1_06_rejects_m1_05_close_outside_post_merge_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses[
                "repos/Project-Helianthus/helianthus-docs-ebus/issues/385"
            ]["closed_at"] = "2026-07-31T12:01:01Z"
            result = self.authorize(
                implementing, anchor, "FMV3-M1-06", github_responses=responses
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("closure is not within the bounded post-merge window", result.stderr)

    def test_m1_06_rejects_m1_05_missing_closing_issues_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            endpoint = (
                "graphql/closing-issues/Project-Helianthus/"
                "helianthus-docs-ebus/386/FIRST"
            )
            responses[endpoint]["data"]["repository"]["pullRequest"][
                "closingIssuesReferences"
            ]["nodes"] = []
            result = self.authorize(
                implementing, anchor, "FMV3-M1-06", github_responses=responses
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("absent from pull request closingIssuesReferences", result.stderr)

    def test_m2_01_requires_external_producer_merge_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M2-01",
                github_responses=responses,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must equal direct unresolved predecessors", result.stderr)

    def test_m2_01_authorizes_with_canonical_producer_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            evidence = self.write_m2_authorization_evidence(temp)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            responses.update(self.m1_06_producer_responses())
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M2-01",
                github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_m2_01_rejects_harness_without_exact_merged_docs_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/pulls/"
                f"{M1_06_HARNESS_PR}/files?per_page=100&page=1"
            )

            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint] = [
                    row for row in responses[endpoint]
                    if row["filename"] != M1_06_DOCS_LOCK_PATH
                ]

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "must add only the exact workflow, AST guard, docs-lock validator, and merged docs lock",
                result.stderr,
            )

    def test_m2_01_rejects_green_run_without_successful_docs_lock_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{M1_06_GREEN_RUN_ID}/jobs?per_page=100"
            )

            def mutate(responses: dict[str, object]) -> None:
                conformance = next(
                    job for job in responses[endpoint]["jobs"]
                    if job["name"] == M1_06_CONFORMANCE_JOB_NAME
                )
                docs_lock = next(
                    step for step in conformance["steps"]
                    if step["name"] == M1_06_DOCS_LOCK_STEP_NAME
                )
                docs_lock["conclusion"] = "failure"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "ordered docs-lock/guard/compile/exact-test evidence",
                result.stderr,
            )

    def test_authorization_forces_public_github_host_and_sanitizes_gh_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            previous = {
                name: os.environ.get(name)
                for name in (
                    "GH_HOST", "GH_ENTERPRISE_TOKEN", "GH_CONFIG_DIR", "GH_REPO",
                    "GH_DEBUG", "EXPECT_SANITIZED_GH_ENV",
                )
            }
            os.environ.update({
                "GH_HOST": "attacker.invalid",
                "GH_ENTERPRISE_TOKEN": "untrusted-token",
                "GH_CONFIG_DIR": str(Path(temp) / "attacker-gh-config"),
                "GH_REPO": "attacker.invalid/owner/repository",
                "GH_DEBUG": "api",
                "EXPECT_SANITIZED_GH_ENV": "1",
            })
            try:
                result = self.authorize_m2_01_producer_case(temp, lambda _: None)
            finally:
                for name, value in previous.items():
                    if value is None:
                        os.environ.pop(name, None)
                    else:
                        os.environ[name] = value
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_authorization_rejects_git_replacement_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            repo = implementing.parent
            parent = self.git(repo, "rev-parse", "HEAD^").stdout.strip()
            self.git(repo, "replace", anchor, parent)
            result = self.authorize(
                implementing, anchor, "FMV3-M1-05", self.amendment_pr(anchor)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("replacement refs, grafts, and alternate object stores", result.stderr)

    def test_authorization_rejects_git_grafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            repo = implementing.parent
            git_dir = Path(
                self.git(repo, "rev-parse", "--absolute-git-dir").stdout.strip()
            )
            parent = self.git(repo, "rev-parse", "HEAD^").stdout.strip()
            grafts = git_dir / "info" / "grafts"
            grafts.parent.mkdir(parents=True, exist_ok=True)
            grafts.write_text(f"{anchor} {parent}\n", encoding="ascii")
            result = self.authorize(
                implementing, anchor, "FMV3-M1-05", self.amendment_pr(anchor)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("replacement refs, grafts, and alternate object stores", result.stderr)

    def test_m2_01_rejects_lookalike_exact_title_no_op_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/issues/42"
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint].update({
                    "body": "<!-- helianthus-fmv3-m1-06-opaque-runtime-acquisition-v1-lookalike -->\nNo-op issue."
                }),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("issue identity/title/closure mismatch", result.stderr)

    def test_m2_01_rejects_producer_issue_missing_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/issues/42"
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint].update({"body": "Implementation issue without marker."}),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("issue identity/title/closure mismatch", result.stderr)

    def test_m2_01_rejects_non_test_red_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/commits/{M1_06_RED_SHA}?per_page=65&page=1"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["files"] = [{
                    "filename": "capability.go",
                    "status": "modified",
                    "changes": 1,
                }]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RED commit contains a non-test", result.stderr)

    def test_m2_01_rejects_unbounded_red_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/commits/{M1_06_RED_SHA}?per_page=65&page=1"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["files"] = [{
                    "filename": f"runtime/capability_{index}_test.go",
                    "status": "added",
                    "changes": 1,
                } for index in range(65)]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RED commit diff response is invalid or outside bounds", result.stderr)

    def test_m2_01_rejects_hidden_red_diff_page_two(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/commits/{M1_06_RED_SHA}?per_page=65&page=2"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["files"] = [{
                    "filename": "runtime/hidden_production.go",
                    "status": "added",
                    "changes": 1,
                }]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("diff page 2 must be empty", result.stderr)

    def test_m2_01_rejects_red_run_not_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_RED_RUN_ID}"
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint].update({"conclusion": "success"}),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hosted RED run did not fail", result.stderr)

    def test_m2_01_rejects_red_run_wrong_sha(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_RED_RUN_ID}"
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint].update({"head_sha": "7" * 40}),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hosted RED run did not fail", result.stderr)

    def test_m2_01_rejects_red_run_wrong_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_RED_RUN_ID}"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["pull_requests"][0]["number"] = 44
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hosted RED run did not fail", result.stderr)

    def test_m2_01_rejects_red_check_not_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/commits/{M1_06_RED_SHA}/check-runs"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["check_runs"][0]["conclusion"] = "failure"
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hosted RED checks", result.stderr)

    def test_m2_01_rejects_red_exact_conformance_test_not_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_RED_RUN_ID}/jobs?per_page=100"

            def mutate(responses: dict[str, object]) -> None:
                conformance = responses[endpoint]["jobs"][1]
                conformance["conclusion"] = "success"
                conformance["steps"][3]["conclusion"] = "success"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("trusted RED guard or conformance job", result.stderr)

    def test_m2_01_rejects_green_head_reusing_red_subject(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/git/commits/"
                f"{'a' * 40}"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint].update({
                    "message": M1_06_RED_COMMIT_SUBJECT,
                }),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reviewed implementation head", result.stderr)

    def test_m2_01_rejects_attempt_job_check_run_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{M1_06_GREEN_RUN_ID}/attempts/1/jobs?per_page=100"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint]["jobs"][1].update({
                    "check_run_url": (
                        "https://api.github.com/repos/Project-Helianthus/"
                        "helianthus-modbus/check-runs/999999"
                    ),
                }),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("job identity/outcome mismatch", result.stderr)

    def test_m2_01_rejects_harness_attempt_job_check_run_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                "8990/attempts/1/jobs?per_page=100"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint]["jobs"][0].update({
                    "check_run_url": (
                        "https://api.github.com/repos/Project-Helianthus/"
                        "helianthus-modbus/check-runs/999999"
                    ),
                }),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checks job identity", result.stderr)

    def test_m2_01_rejects_nonempty_embed_input_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                self.rewrite_m1_06_report(
                    responses,
                    mutate_report=lambda report: report["go_list"].update({
                        "embed_patterns": ["policy.json"],
                        "embed_files": ["policy.json"],
                    }),
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("production/case bounds mismatch", result.stderr)

    def test_m2_01_rejects_red_unrelated_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_RED_RUN_ID}/jobs?per_page=100"

            def mutate(responses: dict[str, object]) -> None:
                guard, conformance = responses[endpoint]["jobs"]
                guard["conclusion"] = "failure"
                guard["steps"][1]["conclusion"] = "failure"
                conformance["conclusion"] = "success"
                conformance["steps"][3]["conclusion"] = "success"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RED", result.stderr)

    def test_m2_01_rejects_mutation_ast_guard_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_id = M1_06_MUTATION_RUN_IDS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{run_id}/jobs?per_page=100"
            )

            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["jobs"][0]["steps"][1]["conclusion"] = "failure"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AST", result.stderr)

    def write_m1_06_local_guard_fixture(
        self,
        repo: Path,
        *,
        production_name: str = "capability.go",
        test_name: str = "capability_conformance_test.go",
        production_prefix: str = "",
        test_prefix: str = "",
        dynamic_claim_mask: bool = False,
    ) -> tuple[Path, Path, Path]:
        (repo / "go.mod").write_text(
            "module github.com/Project-Helianthus/helianthus-modbus\n\ngo 1.22\n",
            encoding="utf-8",
        )
        production = """package runtime

type OpaqueRuntimeCapability struct{}
type AttemptInstance struct{}
type TerminalOutcome int
func NewRuntimeAcquisition() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func (c *OpaqueRuntimeCapability) Claim() bool { return true }
func (a *AttemptInstance) CloseMembership() bool { return true }
func (a *AttemptInstance) CancelOpen() bool { return true }
func NewBoundedCapability() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func ReserveTerminalSequence() uint64 { return 1 }
func (outcome TerminalOutcome) IsTerminal() bool { return true }
"""
        tests = """package runtime
import "testing"
func TestDeliverabilityExclusions(t *testing.T) { if NewRuntimeAcquisition() == nil { t.Fatal("fail") } }
func TestCopiedCapabilityOneWinner(t *testing.T) { if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") } }
func TestStaleAttemptInstanceCancellationIsolation(t *testing.T) { if !(&AttemptInstance{}).CancelOpen() { t.Fatal("fail") } }
func TestTerminalOutcomes(t *testing.T) { if !TerminalOutcome(0).IsTerminal() { t.Fatal("fail") } }
func TestAttemptMembershipCloseRegistrationRace(t *testing.T) { if !(&AttemptInstance{}).CloseMembership() { t.Fatal("fail") } }
func TestBoundsAndOverflow(t *testing.T) { if NewBoundedCapability() == nil { t.Fatal("fail") } }
func TestTerminalSequenceExhaustion(t *testing.T) { if ReserveTerminalSequence() == 0 { t.Fatal("fail") } }
func TestCoalescedDependentIsolation(t *testing.T) { if NewRuntimeAcquisition() == NewRuntimeAcquisition() { t.Fatal("fail") } }
"""
        if dynamic_claim_mask:
            tests = tests.replace(
                'if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") }',
                'if !NewRuntimeAcquisition().Claim() && len([]bool{}) != 0 { t.Fatal("fail") }',
                1,
            )
        production_path = repo / production_name
        test_path = repo / test_name
        production_path.write_text(production_prefix + production, encoding="utf-8")
        test_path.write_text(test_prefix + tests, encoding="utf-8")
        signatures = {
            "OpaqueRuntimeCapability": "OpaqueRuntimeCapability",
            "AttemptInstance": "AttemptInstance",
            "TerminalOutcome": "TerminalOutcome",
            "NewRuntimeAcquisition": "func() *OpaqueRuntimeCapability",
            "Claim": "func() bool",
            "CloseMembership": "func() bool",
            "CancelOpen": "func() bool",
            "NewBoundedCapability": "func() *OpaqueRuntimeCapability",
            "ReserveTerminalSequence": "func() uint64",
            "IsTerminal": "func() bool",
        }
        report = {
            "go_list": {
                "package_dir": ".", "package_query": ".",
                "package_name": "runtime",
                "import_path": "github.com/Project-Helianthus/helianthus-modbus",
                "goos": "linux", "goarch": "amd64", "cgo_enabled": "0",
                "gowork": "off", "go_files": [production_name],
                "compiled_go_files": [production_name],
                "test_go_files": [test_name], "ignored_go_files": [],
                "cgo_files": [], "c_files": [], "cxx_files": [], "m_files": [],
                "h_files": [], "f_files": [], "s_files": [], "swig_files": [],
                "swig_cxx_files": [], "syso_files": [], "x_test_go_files": [],
                "ignored_other_files": [], "embed_patterns": [], "embed_files": [],
                "test_embed_patterns": [], "test_embed_files": [],
                "x_test_embed_patterns": [], "x_test_embed_files": [],
            },
            "production": [{
                "path": production_name,
                "symbols": [
                    {**symbol, "signature": signatures[symbol["name"]]}
                    for symbol in M1_06_PRODUCTION_SYMBOLS
                ],
            }],
            "cases": [
                {"case_id": case_id, "test_function": value[0]}
                for case_id, value in M1_06_CASES.items()
            ],
        }
        report_path = repo / M1_06_REPORT_PATH
        report_path.parent.mkdir(parents=True)
        report_path.write_text(json.dumps(report), encoding="utf-8")
        return production_path, test_path, report_path

    def test_m1_06_guard_rejects_selected_build_constraints_and_platform_suffixes(self) -> None:
        cases = (
            (
                "go-build-production", "capability.go", "capability_conformance_test.go",
                "//go:build linux\n\n", "", "explicit build constraint",
            ),
            (
                "legacy-build-test", "capability.go", "capability_conformance_test.go",
                "", "// +build linux\n\n", "explicit build constraint",
            ),
            (
                "goos-production", "capability_linux.go", "capability_conformance_test.go",
                "", "", "implicit GOOS/GOARCH filename constraint",
            ),
            (
                "goos-goarch-production", "capability_linux_amd64.go",
                "capability_conformance_test.go", "", "",
                "implicit GOOS/GOARCH filename constraint",
            ),
            (
                "goos-test", "capability.go", "capability_linux_test.go",
                "", "", "implicit GOOS/GOARCH filename constraint",
            ),
            (
                "goos-goarch-test", "capability.go", "capability_linux_amd64_test.go",
                "", "", "implicit GOOS/GOARCH filename constraint",
            ),
        )
        command = [
            "go", "run", str(PLAN / "templates/fmv3_m1_06_mutation_guard.go"),
            "--verify-conformance",
        ]
        for label, production_name, test_name, production_prefix, test_prefix, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                repo = Path(temp)
                _, _, report_path = self.write_m1_06_local_guard_fixture(
                    repo,
                    production_name=production_name,
                    test_name=test_name,
                    production_prefix=production_prefix,
                    test_prefix=test_prefix,
                )
                result = subprocess.run(
                    [*command, str(report_path)], cwd=repo,
                    capture_output=True, text=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(expected, result.stderr)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            _, _, report_path = self.write_m1_06_local_guard_fixture(
                repo,
                production_name="capability_runtime.go",
                test_name="capability_conformance_suite_test.go",
            )
            ordinary_underscores = subprocess.run(
                [*command, str(report_path)], cwd=repo,
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(
                ordinary_underscores.returncode, 0,
                "ordinary underscore-separated names must remain valid: "
                + ordinary_underscores.stderr,
            )

    def test_m1_06_complete_mutation_authorization_rejects_dynamic_mask_via_exact_mutant_failure_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            production_path, _, report_path = self.write_m1_06_local_guard_fixture(
                repo, dynamic_claim_mask=True,
            )
            production_path.write_text(
                """package runtime

type OpaqueRuntimeCapability struct{}
type AttemptInstance struct{}
type TerminalOutcome int
func NewRuntimeAcquisition() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
""",
                encoding="utf-8",
            )
            claim_path = repo / "claim.go"
            claim_path.write_text(
                "package runtime\n\n"
                "func (c *OpaqueRuntimeCapability) Claim() bool { return true }\n",
                encoding="utf-8",
            )
            rest_path = repo / "capability_rest.go"
            rest_path.write_text(
                """package runtime

func (a *AttemptInstance) CloseMembership() bool { return true }
func (a *AttemptInstance) CancelOpen() bool { return true }
func NewBoundedCapability() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func ReserveTerminalSequence() uint64 { return 1 }
func (outcome TerminalOutcome) IsTerminal() bool { return true }
""",
                encoding="utf-8",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            symbols = report["production"][0]["symbols"]
            claim_index = next(
                index for index, symbol in enumerate(symbols)
                if symbol["name"] == "Claim"
            )
            selected_sources = [production_path.name, rest_path.name, claim_path.name]
            report["go_list"]["go_files"] = selected_sources
            report["go_list"]["compiled_go_files"] = selected_sources
            report["production"] = [
                {"path": production_path.name, "symbols": symbols[:claim_index]},
                {"path": claim_path.name, "symbols": [symbols[claim_index]]},
                {"path": rest_path.name, "symbols": symbols[claim_index + 1:]},
            ]
            report_path.write_text(json.dumps(report), encoding="utf-8")
            guard = PLAN / "templates/fmv3_m1_06_mutation_guard.go"
            conformance = subprocess.run(
                ["go", "run", str(guard), "--verify-conformance", str(report_path)],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(conformance.returncode, 0, conformance.stderr)

            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Guard test")
            self.git(repo, "config", "user.email", "guard@example.invalid")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-m", "green dynamically masked conformance")
            green_sha = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            baseline = subprocess.run(
                ["go", "test", "-run", "^TestCopiedCapabilityOneWinner$", "."],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)

            claim_path.write_text(
                claim_path.read_text(encoding="utf-8").replace(
                    "func (c *OpaqueRuntimeCapability) Claim() bool { return true }",
                    "func (c *OpaqueRuntimeCapability) Claim() bool { return false }",
                    1,
                ),
                encoding="utf-8",
            )
            self.git(repo, "add", claim_path.name)
            self.git(repo, "commit", "-m", "exact Claim mutant")
            mutant_sha = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            exact_mutation = subprocess.run(
                [
                    "go", "run", str(guard), "--case", "M1-06-COPY-ONE-WINNER",
                    "--base", green_sha, "--mutant", mutant_sha,
                ],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(exact_mutation.returncode, 0, exact_mutation.stderr)
            mutant_test = subprocess.run(
                ["go", "test", "-run", "^TestCopiedCapabilityOneWinner$", "."],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(
                mutant_test.returncode, 0,
                "the dynamic mask must keep the exact mutant mapped test green so the "
                "system-level mutation-failure evidence gate, not static syntax, rejects it",
            )

            diff_lines = self.git(
                repo, "diff", "--unified=3", green_sha, mutant_sha, "--", claim_path.name,
            ).stdout.splitlines()
            patch = "\n".join(diff_lines[4:]) + "\n"
            patch_projection = [{
                "filename": claim_path.name,
                "status": "modified",
                "patch": patch,
            }]
            patch_digest = hashlib.sha256(json.dumps(
                patch_projection, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            ).encode("ascii")).hexdigest()
            expected_digests = {case_id: "0" * 64 for case_id in M1_06_MUTATION_CASES}
            expected_digests["M1-06-COPY-ONE-WINNER"] = patch_digest
            run_id = 12345
            workflow_id = 67890
            case_id = "M1-06-COPY-ONE-WINNER"

            def github_api(path: str) -> dict[str, object]:
                if path == f"repos/Project-Helianthus/helianthus-modbus/git/commits/{mutant_sha}":
                    return {
                        "sha": mutant_sha,
                        "parents": [{"sha": green_sha}],
                        "tree": {"sha": "a" * 40},
                    }
                if path == f"repos/Project-Helianthus/helianthus-modbus/commits/{mutant_sha}?per_page=65&page=1":
                    return {
                        "sha": mutant_sha,
                        "files": [{
                            "filename": claim_path.name,
                            "status": "modified",
                            "changes": 2,
                            "patch": patch,
                        }],
                    }
                if path == f"repos/Project-Helianthus/helianthus-modbus/commits/{mutant_sha}?per_page=65&page=2":
                    return {"sha": mutant_sha, "files": []}
                if path == f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{run_id}/attempts/1":
                    return {
                        "id": run_id,
                        "run_attempt": 1,
                        "workflow_id": workflow_id,
                        "event": "workflow_dispatch",
                        "status": "completed",
                        "conclusion": "success",
                        "head_sha": mutant_sha,
                        "path": M1_06_MUTATION_WORKFLOW_PATH,
                        "actor": {"login": "owner"},
                    }
                raise AssertionError(f"unexpected GitHub API path: {path}")

            evidence_gate = VALIDATOR_GLOBALS["require_m1_06_mutation_evidence"]
            validation_error = VALIDATOR_GLOBALS["ValidationError"]
            trusted_blobs = {"scripts/fmv3_m1_06_mutation_guard.go": "b" * 40}
            with mock.patch.dict(
                evidence_gate.__globals__,
                {
                    "github_api": github_api,
                    "github_tree_blob_map": lambda *_: {
                        **trusted_blobs,
                        claim_path.name: "c" * 40,
                    },
                },
            ):
                with self.assertRaisesRegex(
                    validation_error,
                    "run is not exact-SHA hosted failure",
                    msg=(
                        "complete authorization must reject a dynamically masked exact mutant "
                        "whose mapped test remains green"
                    ),
                ):
                    evidence_gate(
                        {"authorized_issuer": "owner"},
                        "Project-Helianthus/helianthus-modbus",
                        green_sha,
                        [{
                            "case_id": case_id,
                            "mutation_commit_sha": mutant_sha,
                            "workflow_run_id": run_id,
                            "workflow_run_attempt": 1,
                            "check_run_id": 1,
                            "job_id": 2,
                        }],
                        expected_digests,
                        {claim_path.name},
                        None,
                        None,
                        workflow_id,
                        trusted_blobs,
                    )

    def test_m1_06_mutation_guard_compiles_and_rejects_return_change_plus_panic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "guard-repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Guard test")
            self.git(repo, "config", "user.email", "guard@example.invalid")
            source = repo / "runtime.go"
            source.write_text(
                "package runtime\n\ntype OpaqueRuntimeCapability struct{}\n"
                "func unrelated() *OpaqueRuntimeCapability { return nil }\n"
                "func NewRuntimeAcquisition() *OpaqueRuntimeCapability {\n"
                "\treturn &OpaqueRuntimeCapability{}\n}\n",
                encoding="utf-8",
            )
            report_path = repo / M1_06_REPORT_PATH
            report_path.parent.mkdir(parents=True)
            report_path.write_text(json.dumps({
                "production": [{
                    "path": "runtime.go",
                    "symbols": [{
                        "name": "NewRuntimeAcquisition", "kind": "function",
                        "receiver": "",
                        "signature": "func() *OpaqueRuntimeCapability",
                    }],
                }],
            }), encoding="utf-8")
            self.git(repo, "add", "runtime.go", M1_06_REPORT_PATH)
            self.git(repo, "commit", "-m", "base")
            base = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            source.write_text(source.read_text(encoding="utf-8").replace(
                "return &OpaqueRuntimeCapability{}", "return nil"
            ), encoding="utf-8")
            self.git(repo, "add", "runtime.go")
            self.git(repo, "commit", "-m", "mutate return")
            mutation = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            command = ["go", "run", str(PLAN / "templates/fmv3_m1_06_mutation_guard.go"),
                       "--case", "M1-06-DELIVERABILITY-EXCLUSIONS", "--base", base, "--mutant", mutation]
            accepted = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.git(repo, "checkout", "--detach", base)
            source.write_text(source.read_text(encoding="utf-8").replace(
                "return &OpaqueRuntimeCapability{}", 'panic("unexpected")\n\treturn nil'
            ), encoding="utf-8")
            self.git(repo, "add", "runtime.go")
            self.git(repo, "commit", "-m", "invert plus panic")
            panic_mutant = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            rejected = subprocess.run(
                [*command[:-1], panic_mutant], cwd=repo, capture_output=True, text=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("exactly the case return replacement", rejected.stderr)

            self.git(repo, "checkout", "--detach", base)
            source.write_text(
                source.read_text(encoding="utf-8")
                .replace("func NewRuntimeAcquisition", "//go:noinline\nfunc NewRuntimeAcquisition")
                .replace("return &OpaqueRuntimeCapability{}", "return nil"),
                encoding="utf-8",
            )
            self.git(repo, "add", "runtime.go")
            self.git(repo, "commit", "-m", "mutate return plus compiler directive")
            directive_mutant = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            rejected_directive = subprocess.run(
                [*command[:-1], directive_mutant], cwd=repo, capture_output=True, text=True, check=False
            )
            self.assertNotEqual(rejected_directive.returncode, 0)
            self.assertIn("exactly the case return replacement", rejected_directive.stderr)

            self.git(repo, "checkout", "--detach", base)
            source.write_text(
                source.read_text(encoding="utf-8")
                .replace("func NewRuntimeAcquisition", "// unrelated comment\nfunc NewRuntimeAcquisition")
                .replace("return &OpaqueRuntimeCapability{}", "return nil"),
                encoding="utf-8",
            )
            self.git(repo, "add", "runtime.go")
            self.git(repo, "commit", "-m", "mutate return plus comment")
            comment_mutant = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            rejected_comment = subprocess.run(
                [*command[:-1], comment_mutant], cwd=repo, capture_output=True, text=True, check=False
            )
            self.assertNotEqual(rejected_comment.returncode, 0)
            self.assertIn("exactly the case return replacement", rejected_comment.stderr)

            self.git(repo, "checkout", "--detach", base)
            (repo / "policy.json").write_text("{}\n", encoding="utf-8")
            self.git(repo, "add", "policy.json")
            self.git(repo, "commit", "-m", "add preexisting embed input")
            embed_base = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            source.write_text(
                source.read_text(encoding="utf-8")
                .replace("package runtime\n", 'package runtime\n\nimport _ "embed"\n', 1)
                .replace("func NewRuntimeAcquisition", "//go:embed policy.json\nvar policy string\n\nfunc NewRuntimeAcquisition")
                .replace("return &OpaqueRuntimeCapability{}", "return nil"),
                encoding="utf-8",
            )
            self.git(repo, "add", "runtime.go")
            self.git(repo, "commit", "-m", "mutate return plus go embed directive")
            embed_mutant = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            rejected_embed_directive = subprocess.run(
                [
                    "go", "run", str(PLAN / "templates/fmv3_m1_06_mutation_guard.go"),
                    "--case", "M1-06-DELIVERABILITY-EXCLUSIONS", "--base", embed_base,
                    "--mutant", embed_mutant,
                ], cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_embed_directive.returncode, 0)
            self.assertIn("exactly the case return replacement", rejected_embed_directive.stderr)

            self.git(repo, "checkout", "--detach", base)
            source.write_text(source.read_text(encoding="utf-8").replace(
                "return &OpaqueRuntimeCapability{}", "return nil"
            ), encoding="utf-8")
            (repo / "unrelated.txt").write_text("must not be changed\n", encoding="utf-8")
            self.git(repo, "add", "runtime.go", "unrelated.txt")
            self.git(repo, "commit", "-m", "mutate return plus non go file")
            extra_file_mutant = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            rejected_extra_file = subprocess.run(
                [*command[:-1], extra_file_mutant], cwd=repo, capture_output=True, text=True, check=False
            )
            self.assertNotEqual(rejected_extra_file.returncode, 0)
            self.assertIn("exactly one file", rejected_extra_file.stderr)

    def test_m1_06_guard_accepts_root_package_and_rejects_local_api_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "go.mod").write_text(
                "module github.com/Project-Helianthus/helianthus-modbus\n\ngo 1.22\n",
                encoding="utf-8",
            )
            production = """package runtime

type OpaqueRuntimeCapability struct{}
type AttemptInstance struct{}
type TerminalOutcome int
func NewRuntimeAcquisition() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func (c *OpaqueRuntimeCapability) Claim() bool { return true }
func (a *AttemptInstance) CloseMembership() bool { return true }
func (a *AttemptInstance) CancelOpen() bool { return true }
func NewBoundedCapability() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func ReserveTerminalSequence() uint64 { return 1 }
func (outcome TerminalOutcome) IsTerminal() bool { return true }
"""
            tests = """package runtime
import "testing"
func TestDeliverabilityExclusions(t *testing.T) { if NewRuntimeAcquisition() == nil { t.Fatal("fail") } }
func TestCopiedCapabilityOneWinner(t *testing.T) { if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") } }
func TestStaleAttemptInstanceCancellationIsolation(t *testing.T) { if !(&AttemptInstance{}).CancelOpen() { t.Fatal("fail") } }
func TestTerminalOutcomes(t *testing.T) { if !TerminalOutcome(0).IsTerminal() { t.Fatal("fail") } }
func TestAttemptMembershipCloseRegistrationRace(t *testing.T) { if !(&AttemptInstance{}).CloseMembership() { t.Fatal("fail") } }
func TestBoundsAndOverflow(t *testing.T) { if NewBoundedCapability() == nil { t.Fatal("fail") } }
func TestTerminalSequenceExhaustion(t *testing.T) { if ReserveTerminalSequence() == 0 { t.Fatal("fail") } }
func TestCoalescedDependentIsolation(t *testing.T) { if NewRuntimeAcquisition() == NewRuntimeAcquisition() { t.Fatal("fail") } }
"""
            (repo / "capability.go").write_text(production, encoding="utf-8")
            test_path = repo / "capability_conformance_test.go"
            test_path.write_text(tests, encoding="utf-8")
            report = {
                "go_list": {
                    "package_dir": ".", "package_query": ".",
                    "package_name": "runtime",
                    "import_path": "github.com/Project-Helianthus/helianthus-modbus",
                    "goos": "linux", "goarch": "amd64", "cgo_enabled": "0",
                    "gowork": "off", "go_files": ["capability.go"],
                    "compiled_go_files": ["capability.go"],
                    "test_go_files": ["capability_conformance_test.go"],
                    "ignored_go_files": [], "cgo_files": [], "c_files": [],
                    "cxx_files": [], "m_files": [], "h_files": [], "f_files": [],
                    "s_files": [], "swig_files": [], "swig_cxx_files": [],
                    "syso_files": [], "x_test_go_files": [],
                    "ignored_other_files": [], "embed_patterns": [], "embed_files": [],
                    "test_embed_patterns": [], "test_embed_files": [],
                    "x_test_embed_patterns": [], "x_test_embed_files": [],
                },
                "production": [{
                    "path": "capability.go",
                    "symbols": [
                        {**symbol, "signature": {
                            "OpaqueRuntimeCapability": "OpaqueRuntimeCapability",
                            "AttemptInstance": "AttemptInstance",
                            "TerminalOutcome": "TerminalOutcome",
                            "NewRuntimeAcquisition": "func() *OpaqueRuntimeCapability",
                            "Claim": "func() bool", "CloseMembership": "func() bool",
                            "CancelOpen": "func() bool",
                            "NewBoundedCapability": "func() *OpaqueRuntimeCapability",
                            "ReserveTerminalSequence": "func() uint64",
                            "IsTerminal": "func() bool",
                        }[symbol["name"]]}
                        for symbol in M1_06_PRODUCTION_SYMBOLS
                    ],
                }],
                "cases": [
                    {"case_id": case_id, "test_function": value[0]}
                    for case_id, value in M1_06_CASES.items()
                ],
            }
            report_path = repo / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            command = [
                "go", "run", str(PLAN / "templates/fmv3_m1_06_mutation_guard.go"),
                "--verify-conformance", str(report_path),
            ]
            accepted = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            tampered_report = json.loads(json.dumps(report))
            claim_descriptor = next(
                symbol for symbol in tampered_report["production"][0]["symbols"]
                if symbol["name"] == "Claim"
            )
            claim_descriptor["signature"] = "func() int"
            report_path.write_text(json.dumps(tampered_report), encoding="utf-8")
            rejected_signature = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_signature.returncode, 0)
            self.assertIn("descriptor Claim does not resolve exactly once", rejected_signature.stderr)
            report_path.write_text(json.dumps(report), encoding="utf-8")
            test_path.write_text(tests.replace(
                "func TestDeliverabilityExclusions(t *testing.T) {",
                "func TestDeliverabilityExclusions(t *testing.T) {\n"
                "NewRuntimeAcquisition := func() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }\n",
                1,
            ), encoding="utf-8")
            rejected = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("shadows production contract name", rejected.stderr)

            decoy_production = production + """
type decoyCapability struct{}
func (decoyCapability) Claim() bool { return true }
"""
            (repo / "capability.go").write_text(decoy_production, encoding="utf-8")
            test_path.write_text(tests.replace(
                "if !NewRuntimeAcquisition().Claim() { t.Fatal(\"fail\") }",
                "if !(decoyCapability{}).Claim() { t.Fatal(\"fail\") }",
                1,
            ), encoding="utf-8")
            rejected_decoy = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_decoy.returncode, 0)
            self.assertIn("unexpected declaration", rejected_decoy.stderr)

            field_production = production + """
type fieldDecoy struct { Claim func() bool }
"""
            (repo / "capability.go").write_text(field_production, encoding="utf-8")
            test_path.write_text(tests.replace(
                "if !NewRuntimeAcquisition().Claim() { t.Fatal(\"fail\") }",
                "if !(fieldDecoy{Claim: func() bool { return true }}).Claim() { t.Fatal(\"fail\") }",
                1,
            ), encoding="utf-8")
            rejected_field = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_field.returncode, 0)
            self.assertIn("unexpected declaration", rejected_field.stderr)

            interface_production = production + """
type claimInterface interface { Claim() bool }
type interfaceDecoy struct{}
func (interfaceDecoy) Claim() bool { return true }
func interfaceClaim() claimInterface { return interfaceDecoy{} }
"""
            (repo / "capability.go").write_text(interface_production, encoding="utf-8")
            test_path.write_text(tests.replace(
                "if !NewRuntimeAcquisition().Claim() { t.Fatal(\"fail\") }",
                "if !interfaceClaim().Claim() { t.Fatal(\"fail\") }",
                1,
            ), encoding="utf-8")
            rejected_interface = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_interface.returncode, 0)
            self.assertIn("unexpected declaration", rejected_interface.stderr)

            (repo / "capability.go").write_text(production, encoding="utf-8")
            dead = tests.replace(
                'if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") }',
                'if false { if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") } }',
                1,
            )
            test_path.write_text(dead, encoding="utf-8")
            rejected_dead = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_dead.returncode, 0)
            self.assertIn("invalid closed failure-control shape", rejected_dead.stderr)

            ignored = tests.replace(
                'if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") }',
                'NewRuntimeAcquisition().Claim(); if false { t.Fatal("fail") }',
                1,
            )
            test_path.write_text(ignored, encoding="utf-8")
            rejected_ignored = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_ignored.returncode, 0)
            self.assertIn("invalid closed failure-control shape", rejected_ignored.stderr)

            masked = tests.replace(
                'if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") }',
                'if !NewRuntimeAcquisition().Claim() && false { t.Fatal("fail") }',
                1,
            )
            test_path.write_text(masked, encoding="utf-8")
            rejected_masked = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_masked.returncode, 0)
            self.assertIn("invalid closed failure-control shape", rejected_masked.stderr)

            after_return = tests.replace(
                "func TestCopiedCapabilityOneWinner(t *testing.T) { if !NewRuntimeAcquisition().Claim() { t.Fatal(\"fail\") } }",
                "func TestCopiedCapabilityOneWinner(t *testing.T) { return; if !NewRuntimeAcquisition().Claim() { t.Fatal(\"fail\") } }",
                1,
            )
            test_path.write_text(after_return, encoding="utf-8")
            rejected_after_return = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_after_return.returncode, 0)
            self.assertIn("invalid closed failure-control shape", rejected_after_return.stderr)

            constant_true_else = tests.replace(
                'if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") }',
                'if true { t.Fatal("fail") } else { if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") } }',
                1,
            )
            test_path.write_text(constant_true_else, encoding="utf-8")
            rejected_constant_true_else = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_constant_true_else.returncode, 0)
            self.assertIn("invalid closed failure-control shape", rejected_constant_true_else.stderr)

            foreign_testing_t = tests.replace(
                'if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") }',
                'if !NewRuntimeAcquisition().Claim() { (&testing.T{}).Fatal("fail") }',
                1,
            )
            test_path.write_text(foreign_testing_t, encoding="utf-8")
            rejected_foreign_testing_t = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_foreign_testing_t.returncode, 0)
            self.assertIn("invalid closed failure-control shape", rejected_foreign_testing_t.stderr)

            test_path.write_text(tests + "\nfunc helper() {}\n", encoding="utf-8")
            rejected_helper = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_helper.returncode, 0)
            self.assertIn("fixed conformance test declarations", rejected_helper.stderr)

            test_path.write_text(tests + "\nfunc init() {}\n", encoding="utf-8")
            rejected_test_init = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_test_init.returncode, 0)
            self.assertIn("fixed conformance test declarations", rejected_test_init.stderr)

            (repo / "capability.go").write_text(
                production + "\nvar unrelatedInitializer = 1\n", encoding="utf-8",
            )
            test_path.write_text(tests, encoding="utf-8")
            rejected_initializer = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_initializer.returncode, 0)
            self.assertIn("unexpected declaration", rejected_initializer.stderr)

            (repo / "capability.go").write_text(
                production + "\nfunc alwaysFalse(value bool) bool { return false }\n",
                encoding="utf-8",
            )
            argument_only = tests.replace(
                'if !NewRuntimeAcquisition().Claim() { t.Fatal("fail") }',
                'if alwaysFalse(NewRuntimeAcquisition().Claim()) { t.Fatal("fail") }',
                1,
            )
            test_path.write_text(argument_only, encoding="utf-8")
            rejected_argument = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_argument.returncode, 0)
            self.assertIn("unexpected declaration", rejected_argument.stderr)

            test_path.write_text(tests, encoding="utf-8")
            (repo / "policy.json").write_text("{}\n", encoding="utf-8")
            (repo / "capability.go").write_text(
                production.replace(
                    "package runtime\n",
                    'package runtime\n\nimport _ "embed"\n\n//go:embed policy.json\nvar policy string\n',
                    1,
                ),
                encoding="utf-8",
            )
            rejected_embed = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected_embed.returncode, 0)
            self.assertIn("EmbedPatterns", rejected_embed.stderr)

    def test_m2_01_rejects_mutation_parent_baseline_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_id = M1_06_MUTATION_RUN_IDS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{run_id}/jobs?per_page=100"
            )

            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["jobs"][0]["steps"][2]["conclusion"] = "failure"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("baseline", result.stderr)

    def test_m2_01_rejects_product_harness_blob_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/git/trees/"
                f"{'d' * 40}?recursive=1"
            )

            def mutate(responses: dict[str, object]) -> None:
                replacement_sha, replacement = self.github_blob(b"tampered workflow\n")
                responses[
                    f"repos/Project-Helianthus/helianthus-modbus/git/blobs/{replacement_sha}"
                ] = replacement
                entry = next(
                    item for item in responses[endpoint]["tree"]
                    if item["path"] == M1_06_MUTATION_WORKFLOW_PATH
                )
                entry["sha"] = replacement_sha

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("trusted harness blob", result.stderr)

    def test_m2_01_rejects_retargeted_harness_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/workflows/"
                f"{Path(M1_06_MUTATION_WORKFLOW_PATH).name}"
            )

            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["path"] = ".github/workflows/ci.yml"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("trusted mutation workflow identity", result.stderr)

    def test_m2_01_rejects_overlapping_repository_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/pulls?state=all&"
                "sort=created&direction=asc&per_page=100&page=1"
            )

            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint].append({
                    "number": 99,
                    "created_at": "2026-08-01T12:10:00Z",
                    "closed_at": "2026-08-01T12:15:00Z",
                })

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("repository mutex was violated by PR #99", result.stderr)

    def test_m2_01_rejects_harness_branch_not_bound_to_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/pulls/41"

            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["head"]["ref"] = "issue/999-evidence-harness"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("harness PR identity or authority mismatch", result.stderr)

    def test_m2_01_rejects_harness_created_before_selected_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/pulls/41"

            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["created_at"] = "2026-08-01T09:59:59Z"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("product PR must be created after", result.stderr)

    def test_m2_01_rejects_red_not_ancestor_of_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/compare/{M1_06_RED_SHA}...{'a' * 40}"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint] = {
                    "status": "diverged",
                    "merge_base_commit": {"sha": "7" * 40},
                }
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not an ancestor", result.stderr)

    def test_m2_01_rejects_green_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/commits/{'a' * 40}/check-runs"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["check_runs"][0]["conclusion"] = "failure"
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exact-head required check failed", result.stderr)

    def test_m2_01_rejects_green_exact_conformance_test_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_GREEN_RUN_ID}/jobs?per_page=100"

            def mutate(responses: dict[str, object]) -> None:
                conformance = responses[endpoint]["jobs"][1]
                conformance["conclusion"] = "failure"
                conformance["steps"][2]["conclusion"] = "failure"

            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("trusted RED guard or conformance job", result.stderr)

    def test_m2_01_rejects_stale_owner_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/pulls/43/reviews?per_page=100"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint][1]["submitted_at"] = "2026-08-01T12:00:01Z"
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("owner-attested exact-head NO_FINDINGS process evidence", result.stderr)

    def test_m2_01_rejects_missing_owner_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/pulls/43/reviews?per_page=100"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint] = responses[endpoint][:-1]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("owner review selector is missing", result.stderr)

    def test_m2_01_rejects_second_page_duplicate_owner_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = "repos/Project-Helianthus/helianthus-modbus/pulls/43/reviews"
            endpoint = base + "?per_page=100"
            def mutate(responses: dict[str, object]) -> None:
                reviews = responses[endpoint]
                padding = [{
                    "id": 60000 + index,
                    "user": {"login": f"unrelated-{index}"},
                    "state": "COMMENTED",
                    "commit_id": "a" * 40,
                    "body": "unrelated review",
                } for index in range(97)]
                responses[base + "?per_page=100&page=1"] = [*reviews, *padding]
                responses[base + "?per_page=100&page=2"] = [dict(reviews[1])]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("owner review selector is missing or ambiguous", result.stderr)

    def test_m2_01_rejects_owner_review_wrong_conformance_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/pulls/43/reviews?per_page=100"
            def mutate(responses: dict[str, object]) -> None:
                body = json.loads(responses[endpoint][1]["body"])
                body["conformance_report_blob_sha"] = "7" * 40
                responses[endpoint][1]["body"] = json.dumps(body, sort_keys=True)
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("owner-attested exact-head NO_FINDINGS process evidence", result.stderr)

    def test_m2_01_rejects_official_codex_inline_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/pulls/43/reviews/"
                f"{M1_06_OFFICIAL_REVIEW_ID}/comments?per_page=100"
            )
            result = self.authorize_m2_01_producer_case(
                temp, lambda responses: responses.update({endpoint: [{"id": 1}]})
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("official Codex exact-head review has inline findings", result.stderr)

    def test_m2_01_rejects_malicious_official_codex_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = "repos/Project-Helianthus/helianthus-modbus/pulls/43/reviews?per_page=100"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint][0]["body"] += "\n\nP1: arbitrary finding text"
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("official Codex exact-head review is missing", result.stderr)

    def test_m2_01_rejects_producer_head_merge_tree_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/git/commits/{'b' * 40}"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["tree"]["sha"] = "7" * 40
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("squash tree/topology mismatch", result.stderr)

    def test_m2_01_rejects_missing_conformance_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/git/trees/{'d' * 40}?recursive=1"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["tree"] = [
                    item for item in responses[endpoint]["tree"]
                    if item["path"] != M1_06_REPORT_PATH
                ]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conformance report is missing", result.stderr)

    def test_m2_01_rejects_missing_required_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/git/trees/{'d' * 40}?recursive=1"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["tree"] = [
                    item for item in responses[endpoint]["tree"]
                    if item["path"] != "capability_conformance_test.go"
                ]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("go-list GoFiles/TestGoFiles", result.stderr)

    def test_m2_01_rejects_fake_artifact_blob_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/git/trees/{'d' * 40}?recursive=1"
            def mutate(responses: dict[str, object]) -> None:
                artifact = next(
                    item for item in responses[endpoint]["tree"]
                    if item["path"] == "capability.go"
                )
                artifact["sha"] = "7" * 40
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reported package source differs", result.stderr)

    def test_m2_01_rejects_semantic_no_op_conformance_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            no_op = b'''package runtime\n\nimport "testing"\n\n'''
            for _, (function_name, _) in M1_06_CASES.items():
                no_op += f"func {function_name}(t *testing.T) {{}}\n".encode()
            def mutate(responses: dict[str, object]) -> None:
                self.rewrite_m1_06_report(
                    responses,
                    replace_path="capability_conformance_test.go",
                    replacement=no_op,
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("semantic no-op", result.stderr)

    def test_m2_01_rejects_mutation_run_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_id = M1_06_MUTATION_RUN_IDS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{run_id}"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint].update({"conclusion": "success"}),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("run is not exact-SHA hosted failure", result.stderr)

    def test_m2_01_certificates_survive_later_same_name_reruns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                repository = "Project-Helianthus/helianthus-modbus"
                endpoints = [
                    f"repos/{repository}/commits/{M1_06_HARNESS_HEAD_SHA}/check-runs",
                    f"repos/{repository}/commits/{M1_06_RED_SHA}/check-runs",
                    f"repos/{repository}/commits/{'a' * 40}/check-runs",
                    f"repos/{repository}/commits/{M1_06_MUTATION_SHAS[0]}/check-runs",
                ]
                for offset, endpoint in enumerate(endpoints, start=1):
                    original = responses[endpoint]["check_runs"][-1]
                    responses[endpoint]["check_runs"].append({
                        **original, "id": original["id"] + 100000 + offset,
                        "completed_at": "2026-08-01T14:00:00Z",
                    })
                for offset, run_id in enumerate((
                    8990,
                    M1_06_RED_RUN_ID,
                    M1_06_GREEN_RUN_ID,
                    M1_06_MUTATION_RUN_IDS[0],
                ), start=1):
                    root_run = f"repos/{repository}/actions/runs/{run_id}"
                    attempt_one = f"{root_run}/attempts/1"
                    responses[root_run] = {
                        **responses[attempt_one],
                        "run_attempt": 2,
                        "updated_at": "2026-08-01T14:00:00Z",
                    }
                    responses[f"{root_run}/jobs?per_page=100"] = {
                        "jobs": [{
                            "id": 99000 + offset,
                            "name": "later rerun",
                            "head_sha": responses[attempt_one]["head_sha"],
                            "status": "completed",
                            "conclusion": "success",
                            "check_run_url": (
                                f"https://api.github.com/repos/{repository}/check-runs/"
                                f"{99000 + offset}"
                            ),
                            "steps": [],
                        }],
                    }
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_m2_01_rejects_mutation_not_parented_by_green(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            mutation_sha = M1_06_MUTATION_SHAS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/git/commits/"
                f"{mutation_sha}"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint]["parents"][0].update(
                    {"sha": "f" * 40}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not an exact child of GREEN head", result.stderr)

    def test_m2_01_rejects_mutation_without_mapped_test_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_id = M1_06_MUTATION_RUN_IDS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{run_id}/jobs?per_page=100"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint]["jobs"][0]["steps"][4].update(
                    {"name": "go test ./..."}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AST/baseline/compile proof", result.stderr)

    def test_m2_01_rejects_mutation_compile_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_id = M1_06_MUTATION_RUN_IDS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{run_id}/jobs?per_page=100"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint]["jobs"][0]["steps"][3].update(
                    {"conclusion": "failure"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AST/baseline/compile proof", result.stderr)

    def test_m2_01_rejects_mutation_patch_not_bound_by_green_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            mutation_sha = M1_06_MUTATION_SHAS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/commits/"
                f"{mutation_sha}?per_page=65&page=1"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint]["files"][0].update(
                    {"patch": "@@ -1 +1 @@\n-valid\n+unbound\n"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("patch differs from closed GREEN report", result.stderr)

    def test_m2_01_rejects_fake_conformance_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                self.rewrite_m1_06_report(
                    responses,
                    mutate_report=lambda report: report["cases"][0].update({"status": "FAIL"}),
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("case ID or PASS status mismatch", result.stderr)

    def test_m2_01_rejects_missing_production_contract_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = b'''package runtime\n\ntype OpaqueRuntimeCapability struct{}\ntype TerminalOutcome int\n'''
            def mutate(responses: dict[str, object]) -> None:
                self.rewrite_m1_06_report(
                    responses,
                    replace_path="capability.go",
                    replacement=source,
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks declared contract symbol", result.stderr)

    def test_m2_01_rejects_build_excluded_production_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                repository = "Project-Helianthus/helianthus-modbus"
                tree = responses[
                    f"repos/{repository}/git/trees/{'d' * 40}?recursive=1"
                ]["tree"]
                entry = next(item for item in tree if item["path"] == "capability.go")
                blob = responses[f"repos/{repository}/git/blobs/{entry['sha']}"]
                source = base64.b64decode(blob["content"])
                self.rewrite_m1_06_report(
                    responses,
                    replace_path="capability.go",
                    replacement=b"//go:build never\n\n" + source,
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("build-excluded or package-mismatched", result.stderr)

    def test_m2_01_rejects_cgo_source_outside_compiled_go_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                repository = "Project-Helianthus/helianthus-modbus"
                tree = responses[
                    f"repos/{repository}/git/trees/{'d' * 40}?recursive=1"
                ]["tree"]
                entry = next(item for item in tree if item["path"] == "capability.go")
                blob = responses[f"repos/{repository}/git/blobs/{entry['sha']}"]
                source = base64.b64decode(blob["content"]).replace(
                    b"package runtime\n", b'package runtime\n\nimport "C"\n', 1,
                )
                self.rewrite_m1_06_report(
                    responses, replace_path="capability.go", replacement=source,
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported cgo input", result.stderr)

    def test_m2_01_rejects_root_non_go_compiled_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                endpoint = (
                    "repos/Project-Helianthus/helianthus-modbus/git/trees/"
                    f"{'d' * 40}?recursive=1"
                )
                responses[endpoint]["tree"].append({
                    "path": "runtime_support.c", "mode": "100644",
                    "type": "blob", "sha": "9" * 40,
                })
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported non-Go compiled inputs", result.stderr)

    def test_m2_01_rejects_nested_module_conformance_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                endpoint = (
                    "repos/Project-Helianthus/helianthus-modbus/git/trees/"
                    f"{'d' * 40}?recursive=1"
                )
                responses[endpoint]["tree"].append({
                    "path": "runtime/go.mod", "mode": "100644",
                    "type": "blob", "sha": "9" * 40,
                })
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exact root Go module", result.stderr)

    def test_m2_01_rejects_test_local_production_symbol_shim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                repository = "Project-Helianthus/helianthus-modbus"
                tree = responses[
                    f"repos/{repository}/git/trees/{'d' * 40}?recursive=1"
                ]["tree"]
                entry = next(
                    item for item in tree
                    if item["path"] == "capability_conformance_test.go"
                )
                blob = responses[f"repos/{repository}/git/blobs/{entry['sha']}"]
                source = base64.b64decode(blob["content"])
                self.rewrite_m1_06_report(
                    responses,
                    replace_path="capability_conformance_test.go",
                    replacement=source + b"\nfunc ReserveTerminalSequence() uint64 { return 1 }\n",
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("locally redeclares production symbol", result.stderr)

    def test_m2_01_rejects_conformance_package_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(responses: dict[str, object]) -> None:
                repository = "Project-Helianthus/helianthus-modbus"
                tree = responses[
                    f"repos/{repository}/git/trees/{'d' * 40}?recursive=1"
                ]["tree"]
                entry = next(
                    item for item in tree
                    if item["path"] == "capability_conformance_test.go"
                )
                blob = responses[f"repos/{repository}/git/blobs/{entry['sha']}"]
                source = base64.b64decode(blob["content"]).replace(
                    b"package runtime\n", b"package runtime_test\n", 1
                )
                self.rewrite_m1_06_report(
                    responses,
                    replace_path="capability_conformance_test.go",
                    replacement=source,
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("build-excluded or package-mismatched", result.stderr)

    def test_m2_01_rejects_producer_merge_not_on_canonical_main(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            evidence = self.write_m2_authorization_evidence(temp)
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.docs_candidate_responses(merged=True))
            producer_responses = self.m1_06_producer_responses()
            producer_responses[
                f"repos/Project-Helianthus/helianthus-modbus/compare/{'b' * 40}...{'c' * 40}"
            ] = {
                "status": "diverged",
                "merge_base_commit": {"sha": "e" * 40},
            }
            responses.update(producer_responses)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M2-01",
                github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("merge is not on canonical main", result.stderr)

    def test_m2_02_rejects_missing_m2_01_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = self.m1_admission_responses(implementing, anchor)
            result = self.authorize(
                implementing, anchor, "FMV3-M2-02", github_responses=responses
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must equal direct unresolved predecessors", result.stderr)

    def test_m2_02_authorizes_with_exact_m2_01_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [dependency])
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.dynamic_dependency_responses(dependency))
            result = self.authorize(
                implementing, anchor, "FMV3-M2-02", github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_m3_02_rejects_missing_m2_03_and_m3_01_certificates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-03", "Project-Helianthus/helianthus-modbusreg", 52, 53, "1"
            )
            evidence = self.write_authorization_evidence(
                temp, "FMV3-M3-02", [dependency]
            )
            responses = self.m1_admission_responses(implementing, anchor)
            result = self.authorize(
                implementing, anchor, "FMV3-M3-02", github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must equal direct unresolved predecessors", result.stderr)

    def test_m3_02_authorizes_with_exact_two_dependency_certificates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependencies = [
                self.dependency_certificate("FMV3-M2-03", "Project-Helianthus/helianthus-modbusreg", 52, 53, "1"),
                self.dependency_certificate("FMV3-M3-01", "Project-Helianthus/helianthus-docs-ebus", 54, 55, "4"),
            ]
            dependencies[1]["required_checks"] = [
                {"context": "checks", "app_id": GITHUB_ACTIONS_APP_ID},
                {"context": "lint", "app_id": GITHUB_ACTIONS_APP_ID},
                {"context": "Modbus Trusted Revision", "app_id": GITHUB_ACTIONS_APP_ID},
            ]
            dependencies[1]["required_check_runs"] = [
                {
                    "context": check["context"],
                    "app_id": check["app_id"],
                    "check_run_id": 1000 + index,
                }
                for index, check in enumerate(dependencies[1]["required_checks"])
            ]
            evidence = self.write_authorization_evidence(temp, "FMV3-M3-02", dependencies)
            responses = self.m1_admission_responses(implementing, anchor)
            for dependency in dependencies:
                responses.update(self.dynamic_dependency_responses(dependency))
            result = self.authorize(
                implementing, anchor, "FMV3-M3-02", github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_dynamic_certificate_rejects_extra_non_direct_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            direct = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            extra = self.dependency_certificate(
                "FMV3-M1-06", "Project-Helianthus/helianthus-modbus", 42, 43, "4"
            )
            evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [direct, extra])
            responses = self.m1_admission_responses(implementing, anchor)
            result = self.authorize(
                implementing, anchor, "FMV3-M2-02", github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must equal direct unresolved predecessors", result.stderr)

    def test_dynamic_certificate_rejects_duplicate_direct_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            direct = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [direct, direct])
            responses = self.m1_admission_responses(implementing, anchor)
            result = self.authorize(
                implementing, anchor, "FMV3-M2-02", github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate predecessors", result.stderr)

    def test_remaining_authorized_dynamic_dependency_shapes_can_pass(self) -> None:
        shapes = {
            "FMV3-M2-03": [
                ("FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 60, 61, "1"),
                ("FMV3-M2-02", "Project-Helianthus/helianthus-modbusreg", 62, 63, "4"),
            ],
            "FMV3-M3-01": [
                ("FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 64, 65, "7"),
            ],
            "FMV3-M3-03": [
                ("FMV3-M3-02", "Project-Helianthus/helianthus-modbusreg", 66, 67, "a"),
            ],
        }
        for authorization_issue, selectors in shapes.items():
            with self.subTest(authorization_issue=authorization_issue), tempfile.TemporaryDirectory() as temp:
                implementing, anchor = self.published_plan(temp)
                anchor = self.publish_amendment_reference(implementing)
                dependencies = [self.dependency_certificate(*selector) for selector in selectors]
                evidence = self.write_authorization_evidence(temp, authorization_issue, dependencies)
                responses = self.m1_admission_responses(implementing, anchor)
                for dependency in dependencies:
                    responses.update(self.dynamic_dependency_responses(dependency))
                result = self.authorize(
                    implementing, anchor, authorization_issue, github_responses=responses,
                    authorization_evidence=evidence,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def assert_m2_02_dynamic_mutation_rejected(
        self,
        temp: str,
        mutate: Callable[[dict[str, object], dict[str, object]], None],
        message: str,
    ) -> None:
        implementing, anchor = self.published_plan(temp)
        anchor = self.publish_amendment_reference(implementing)
        dependency = self.dependency_certificate(
            "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
        )
        evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [dependency])
        responses = self.m1_admission_responses(implementing, anchor)
        dynamic = self.dynamic_dependency_responses(dependency)
        mutate(dependency, dynamic)
        responses.update(dynamic)
        result = self.authorize(
            implementing, anchor, "FMV3-M2-02", github_responses=responses,
            authorization_evidence=evidence,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)

    def test_dynamic_completion_accepts_unrelated_historical_pr_overlap(self) -> None:
        namespace = VALIDATOR_GLOBALS["require_plan_owned_repository_mutex"].__globals__
        original = namespace["github_paginated_list"]
        try:
            namespace["github_paginated_list"] = lambda endpoint, *_: (
                [{"number": 50, "state": "closed",
                  "created_at": "2026-08-01T11:00:00Z",
                  "closed_at": "2026-08-01T13:00:00Z"}]
                if "/issues?" in endpoint else [
                    {"number": 700, "created_at": "2026-01-01T00:00:00Z", "closed_at": "2026-01-01T02:00:00Z"},
                    {"number": 701, "created_at": "2026-01-01T01:00:00Z", "closed_at": "2026-01-01T03:00:00Z"},
                    {"number": 51, "created_at": "2026-08-01T12:00:00Z", "closed_at": "2026-08-01T12:30:00Z"},
                ]
            )
            VALIDATOR_GLOBALS["require_plan_owned_repository_mutex"](
                "Project-Helianthus/helianthus-modbusreg", 50, 51, completion=True)
        finally:
            namespace["github_paginated_list"] = original

    def test_dynamic_completion_rejects_overlap_with_selected_pr(self) -> None:
        namespace = VALIDATOR_GLOBALS["require_plan_owned_repository_mutex"].__globals__
        original = namespace["github_paginated_list"]
        try:
            namespace["github_paginated_list"] = lambda endpoint, *_: (
                [{"number": 50, "state": "closed",
                  "created_at": "2026-08-01T11:00:00Z",
                  "closed_at": "2026-08-01T13:00:00Z"}]
                if "/issues?" in endpoint else [
                    {"number": 51, "created_at": "2026-08-01T12:00:00Z", "closed_at": "2026-08-01T12:30:00Z"},
                    {"number": 99, "created_at": "2026-08-01T12:10:00Z", "closed_at": "2026-08-01T12:15:00Z"},
                ]
            )
            with self.assertRaises(VALIDATOR_GLOBALS["ValidationError"]) as raised:
                VALIDATOR_GLOBALS["require_plan_owned_repository_mutex"](
                    "Project-Helianthus/helianthus-modbusreg", 50, 51, completion=True)
            self.assertIn("selected PR #51 overlaps PR #99", str(raised.exception))
        finally:
            namespace["github_paginated_list"] = original

    def test_dynamic_completion_rejects_closed_issue_interval_overlap(self) -> None:
        namespace = VALIDATOR_GLOBALS["require_plan_owned_repository_mutex"].__globals__
        original = namespace["github_paginated_list"]
        try:
            namespace["github_paginated_list"] = lambda endpoint, *_: (
                [
                    {"number": 50, "state": "closed",
                     "created_at": "2026-08-01T12:00:00Z",
                     "closed_at": "2026-08-01T13:00:00Z"},
                    {"number": 99, "state": "closed",
                     "created_at": "2026-08-01T12:10:00Z",
                     "closed_at": "2026-08-01T12:20:00Z"},
                ] if "/issues?" in endpoint else [
                    {"number": 51, "created_at": "2026-08-01T12:00:00Z",
                     "closed_at": "2026-08-01T12:30:00Z"},
                ]
            )
            with self.assertRaisesRegex(
                VALIDATOR_GLOBALS["ValidationError"],
                "selected issue #50 overlaps issue #99",
            ):
                VALIDATOR_GLOBALS["require_plan_owned_repository_mutex"](
                    "Project-Helianthus/helianthus-modbusreg", 50, 51,
                    completion=True,
                )
        finally:
            namespace["github_paginated_list"] = original

    def test_authorization_preflight_rejects_competing_plan_owned_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [dependency])
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.dynamic_dependency_responses(dependency))
            endpoint = ("repos/Project-Helianthus/helianthus-modbusreg/issues?state=all&"
                        "sort=created&direction=asc&per_page=100&page=1")
            responses[endpoint] = [
                {"number": 88, "title": "FMV3-M2-02: competing", "state": "open"},
                {"number": 89, "title": "FMV3-M2-99: competing", "state": "open"},
            ]
            result = self.authorize(implementing, anchor, "FMV3-M2-02",
                                    github_responses=responses, authorization_evidence=evidence)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("concurrent active repository issues", result.stderr)

    def test_authorization_preflight_rejects_unmarked_competing_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [dependency])
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.dynamic_dependency_responses(dependency))
            endpoint = ("repos/Project-Helianthus/helianthus-modbusreg/issues?state=all&"
                        "sort=created&direction=asc&per_page=100&page=1")
            responses[endpoint] = [
                {"number": 89, "title": "M2-02 duplicate implementation", "state": "open"},
            ]
            result = self.authorize(implementing, anchor, "FMV3-M2-02",
                                    github_responses=responses, authorization_evidence=evidence)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("active repository issue is not the exact anchored selected issue",
                          result.stderr)

    def test_authorization_preflight_rejects_cloned_selected_issue_identity(self) -> None:
        namespace = VALIDATOR_GLOBALS["require_plan_owned_repository_snapshot"].__globals__
        original = namespace["github_paginated_list"]
        selected = next(issue for issue in PLAN_DATA["issues"] if issue["id"] == "FMV3-M2-02")
        title = VALIDATOR_GLOBALS["issue_spec_title"](selected)
        marker = VALIDATOR_GLOBALS["issue_spec_marker"](
            VALIDATOR_GLOBALS["issue_spec_digest"](selected)
        )
        try:
            namespace["github_paginated_list"] = lambda endpoint, *_: (
                [{"number": 999, "title": title, "body": marker, "state": "open"}]
                if "/issues?" in endpoint else []
            )
            with self.assertRaises(VALIDATOR_GLOBALS["ValidationError"]):
                VALIDATOR_GLOBALS["require_plan_owned_repository_snapshot"](
                    "Project-Helianthus/helianthus-modbusreg", 50, title, marker
                )
        finally:
            namespace["github_paginated_list"] = original

    def test_authorization_preflight_accepts_exact_selected_issue_identity(self) -> None:
        namespace = VALIDATOR_GLOBALS["require_plan_owned_repository_snapshot"].__globals__
        original = namespace["github_paginated_list"]
        selected = next(issue for issue in PLAN_DATA["issues"] if issue["id"] == "FMV3-M2-02")
        title = VALIDATOR_GLOBALS["issue_spec_title"](selected)
        marker = VALIDATOR_GLOBALS["issue_spec_marker"](
            VALIDATOR_GLOBALS["issue_spec_digest"](selected)
        )
        try:
            namespace["github_paginated_list"] = lambda endpoint, *_: (
                [{"number": 50, "title": title, "body": marker, "state": "open"}]
                if "/issues?" in endpoint else []
            )
            VALIDATOR_GLOBALS["require_plan_owned_repository_snapshot"](
                "Project-Helianthus/helianthus-modbusreg", 50, title, marker
            )
        finally:
            namespace["github_paginated_list"] = original

    def test_authorization_preflight_rejects_open_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [dependency])
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.dynamic_dependency_responses(dependency))
            endpoint = ("repos/Project-Helianthus/helianthus-modbusreg/pulls?state=all&"
                        "sort=created&direction=asc&per_page=100&page=1")
            responses[endpoint] = [{
                "number": 88, "state": "open", "created_at": "2026-08-01T12:00:00Z",
                "closed_at": None,
            }]
            result = self.authorize(implementing, anchor, "FMV3-M2-02",
                                    github_responses=responses, authorization_evidence=evidence)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("open pull request before development starts", result.stderr)

    @staticmethod
    def m3_03_test_source(*, import_body: bytes | None = None,
                          activation_body: bytes | None = None) -> dict[str, bytes]:
        import_body = import_body or (
            b" packages, err := froniusOverlayProductionPackages()\n"
            b" if err != nil { t.Fatal(err) }\n"
            b" if offending := hasTCPConcreteImport(packages); offending != \"\" "
            b"{ t.Fatal(offending) }\n"
        )
        activation_body = activation_body or (
            b" runtime := neutralRuntimeNoTCP{}\n"
            b" err := activateFroniusProfile(&runtime)\n"
            b" if !errors.Is(err, neutralRuntimeProbeError) { t.Fatal(err) }\n"
        )
        return {"registry/fronius_overlay_test.go": (
            b"package registry\n"
            b"import (\n\"errors\"\n\"go/parser\"\n\"go/token\"\n\"os\"\n\"path/filepath\"\n\"runtime\"\n\"sort\"\n\"strconv\"\n\"strings\"\n\"testing\"\n)\n"
            b"type NeutralRuntime interface { Read() error }\n"
            b"func activateFroniusProfile(runtime NeutralRuntime) error { return runtime.Read() }\n"
            b"func froniusOverlayProductionPackages() ([]string, error) {\n"
            b" _, sourceFile, _, ok := runtime.Caller(0)\n if !ok || sourceFile == \"\" { return nil, errors.New(\"canonical source directory unavailable\") }\n directory := filepath.Dir(sourceFile)\n entries, err := os.ReadDir(directory)\n if err != nil { return nil, err }\n imports := make([]string, 0)\n scanned := 0\n"
            b" for _, entry := range entries {\n if entry.IsDir() || !strings.HasSuffix(entry.Name(), \".go\") || strings.HasSuffix(entry.Name(), \"_test.go\") { continue }\n"
            b" sourcePath := filepath.Join(directory, entry.Name())\n file, err := parser.ParseFile(token.NewFileSet(), sourcePath, nil, parser.ImportsOnly)\n if err != nil { return nil, err }\n scanned++\n for _, spec := range file.Imports {\n importPath, err := strconv.Unquote(spec.Path.Value)\n if err != nil { return nil, err }\n imports = append(imports, importPath)\n }\n }\n if scanned == 0 { return nil, errors.New(\"no direct production Go source scanned\") }\n sort.Strings(imports)\n return imports, nil\n}\n"
            b"func hasTCPConcreteImport(imports []string) string {\n for _, importPath := range imports {\n for _, part := range strings.Split(importPath, \"/\") {\n normalized := strings.ToLower(strings.ReplaceAll(part, \"-\", \"_\"))\n if normalized == \"net\" || strings.Contains(normalized, \"tcp\") || normalized == \"modbus_tcp\" || normalized == \"modbustcp\" { return importPath }\n }\n }\n return \"\"\n}\n"
            b"type neutralRuntimeNoTCP struct{}\n"
            b"var neutralRuntimeProbeError = errors.New(\"probe\")\n"
            b"func (*neutralRuntimeNoTCP) Read() error { return neutralRuntimeProbeError }\n"
            b"var _ NeutralRuntime = (*neutralRuntimeNoTCP)(nil)\n"
            b"func TestFroniusOverlayRejectsTCPConcreteImports(t *testing.T) {\n"
            + import_body
            + b"}\n"
            b"func TestFroniusOverlayActivatesThroughNeutralRuntime(t *testing.T) {\n"
            + activation_body
            + b"}\n"
        )}

    def m3_03_artifact(self, *, overlay_packages: list[str] | None = None,
                       source_texts: dict[str, bytes] | None = None,
                       disposition: str = "STANDARD_ONLY") -> tuple[dict[str, object], dict[str, object]]:
        head, tree = "a" * 40, "b" * 40
        workflow_contract = VALIDATOR_GLOBALS["M3_03_WORKFLOW_CONTRACT"][disposition]
        workflow_path = workflow_contract["workflow_path"]
        workflow_sha, workflow_blob = self.github_blob(
            (PLAN / workflow_contract["template_path"]).read_bytes()
        )
        test_path = (
            "registry/fronius_overlay_test.go"
            if disposition == "STANDARD_ONLY"
            else "profiles/fronius/fronius_overlay_test.go"
        )
        package_name = "registry" if disposition == "STANDARD_ONLY" else "fronius"
        default_sources = {
            test_path: (
                f"package {package_name}\n".encode("ascii")
                + b"import (\n\"errors\"\n\"go/parser\"\n\"go/token\"\n\"os\"\n\"path/filepath\"\n\"runtime\"\n\"sort\"\n\"strconv\"\n\"strings\"\n\"testing\"\n)\n"
                + (b"type NeutralRuntime interface { Read() error }\n"
                   b"func activateFroniusProfile(runtime NeutralRuntime) error { return runtime.Read() }\n"
                   if disposition == "STANDARD_ONLY" else b"")
                + b"func froniusOverlayProductionPackages() ([]string, error) {\n"
                b" _, sourceFile, _, ok := runtime.Caller(0)\n if !ok || sourceFile == \"\" { return nil, errors.New(\"canonical source directory unavailable\") }\n directory := filepath.Dir(sourceFile)\n entries, err := os.ReadDir(directory)\n if err != nil { return nil, err }\n imports := make([]string, 0)\n scanned := 0\n"
                b" for _, entry := range entries {\n if entry.IsDir() || !strings.HasSuffix(entry.Name(), \".go\") || strings.HasSuffix(entry.Name(), \"_test.go\") { continue }\n"
                b" sourcePath := filepath.Join(directory, entry.Name())\n file, err := parser.ParseFile(token.NewFileSet(), sourcePath, nil, parser.ImportsOnly)\n if err != nil { return nil, err }\n scanned++\n for _, spec := range file.Imports {\n importPath, err := strconv.Unquote(spec.Path.Value)\n if err != nil { return nil, err }\n imports = append(imports, importPath)\n }\n }\n if scanned == 0 { return nil, errors.New(\"no direct production Go source scanned\") }\n sort.Strings(imports)\n return imports, nil\n}\n"
                b"func hasTCPConcreteImport(imports []string) string {\n for _, importPath := range imports {\n for _, part := range strings.Split(importPath, \"/\") {\n normalized := strings.ToLower(strings.ReplaceAll(part, \"-\", \"_\"))\n if normalized == \"net\" || strings.Contains(normalized, \"tcp\") || normalized == \"modbus_tcp\" || normalized == \"modbustcp\" { return importPath }\n }\n }\n return \"\"\n}\n"
                + b"type neutralRuntimeNoTCP struct{}\n"
                b"var neutralRuntimeProbeError = errors.New(\"probe\")\n"
                b"func (*neutralRuntimeNoTCP) Read() error { return neutralRuntimeProbeError }\n"
                b"var _ NeutralRuntime = (*neutralRuntimeNoTCP)(nil)\n"
                b"func TestFroniusOverlayRejectsTCPConcreteImports(t *testing.T) {\n"
                b" packages, err := froniusOverlayProductionPackages()\n"
                b" if err != nil { t.Fatal(err) }\n"
                b" if offending := hasTCPConcreteImport(packages); offending != \"\" { t.Fatal(offending) }\n"
                b"}\n"
                b"func TestFroniusOverlayActivatesThroughNeutralRuntime(t *testing.T) {\n"
                b" runtime := neutralRuntimeNoTCP{}\n"
                b" err := activateFroniusProfile(&runtime)\n"
                b" if !errors.Is(err, neutralRuntimeProbeError) { t.Fatal(err) }\n"
                b"}\n"
            ),
        }
        source_texts = source_texts or default_sources
        if disposition == "STANDARD_ONLY" and b"type NeutralRuntime" not in source_texts[test_path]:
            source_texts = {
                **source_texts,
                test_path: source_texts[test_path].replace(
                    b"\n", b"\ntype NeutralRuntime interface { Read() error }\n"
                    b"func activateFroniusProfile(runtime NeutralRuntime) error { return runtime.Read() }\n",
                    1,
                ),
            }
        test_sha, test_blob = self.github_blob(source_texts[test_path])
        proof_path = (
            test_path
            if disposition == "STANDARD_ONLY"
            else "profiles/fronius/activation.go"
        )
        proof_sha, proof_blob = (
            (test_sha, test_blob)
            if disposition == "STANDARD_ONLY"
            else self.github_blob(
                f"package {package_name}\n".encode("ascii")
                + b"type NeutralRuntime interface { Read() error }\n"
                b"func activateFroniusProfile(runtime NeutralRuntime) error { return runtime.Read() }\n"
            )
        )
        blobs = {workflow_sha: workflow_blob, proof_sha: proof_blob, test_sha: test_blob}
        tests = []
        for name in ("TestFroniusOverlayRejectsTCPConcreteImports",
                     "TestFroniusOverlayActivatesThroughNeutralRuntime"):
            source_sha, source_blob = test_sha, test_blob
            tests.append({"name": name, "source_path": test_path,
                          "source_blob_sha": source_sha, "job_name": "verify",
                          "step_name": (
                              "Run Fronius neutral activation"
                              if name == "TestFroniusOverlayActivatesThroughNeutralRuntime"
                              else "Run Fronius import boundary"
                          )})
        packages = overlay_packages if overlay_packages is not None else []
        artifact = {"schema": "helianthus.fmv3-m3-03-completion.v2", "head_sha": head,
                    "head_tree_sha": tree, "disposition": disposition,
                    "overlay_packages": packages,
                    "package_scan": {"scope": "fixed_profiles_fronius_namespace", "result": packages},
                    "tests": tests, "neutral_runtime_proof": {
                        "source_path": proof_path, "source_blob_sha": proof_sha,
                        "interface_symbol": "NeutralRuntime",
                        "activation_symbol": "activateFroniusProfile",
                    }, "overlay_tdd": None, "workflow_path": workflow_path,
                    "workflow_blob_sha": workflow_sha, "workflow_id": 74,
                    "workflow_run_id": 73, "workflow_run_attempt": 1,
                    "workflow_job_id": 730, "workflow_check_run_id": 731}
        tree_map = {workflow_path: workflow_sha,
                    test_path: tests[0]["source_blob_sha"],
                    proof_path: proof_sha}
        base_tree = {workflow_path: workflow_sha}
        red_tree = {
            workflow_path: workflow_sha,
            test_path: tests[0]["source_blob_sha"],
        }
        red_parent_tree = dict(base_tree)
        repository = "Project-Helianthus/helianthus-modbusreg"
        return artifact, {"tree": tree_map, "blobs": blobs, "run": {
            "id": 73, "run_attempt": 1, "workflow_id": 74,
            "path": workflow_path,
            "event": "pull_request", "head_sha": "a" * 40,
            "head_repository": {"full_name": "Project-Helianthus/helianthus-modbusreg"},
            "status": "completed", "conclusion": "success", "pull_requests": [{
                "number": 67, "base": {"ref": "main", "repo": {"full_name": "Project-Helianthus/helianthus-modbusreg"}},
                "head": {"sha": "a" * 40, "repo": {"full_name": "Project-Helianthus/helianthus-modbusreg"}},
            }],
        }, "jobs": [{
            "id": 730, "name": "verify", "head_sha": "a" * 40,
            "status": "completed", "conclusion": "success",
            "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/731",
            "steps": [
                {"name": "Prepare isolated Fronius proof package", "conclusion": "success"},
                {"name": "Build Fronius proof package", "conclusion": "success"},
                {"name": "Run Fronius neutral activation", "conclusion": "success"},
                {"name": "Run Fronius import boundary", "conclusion": "success"},
            ],
        }], "api": {
            f"repos/{repository}/pulls/67": {
                "head": {"sha": head}, "base": {"sha": "f" * 40},
            },
            f"repos/{repository}/git/commits/{'f' * 40}": {
                "sha": "f" * 40, "tree": {"sha": "1" * 40},
            },
            f"repos/{repository}/git/commits/{'d' * 40}": {
                "sha": "d" * 40, "tree": {"sha": "2" * 40},
            },
        }, "api_calls": [], "job_page_calls": [], "job_pages": {},
            "red_jobs": [], "red_tree": red_tree,
            "red_parent_tree": red_parent_tree, "base_tree": base_tree}

    def assert_m3_03_artifact(self, artifact: dict[str, object], fixture: dict[str, object], message: str | None = None) -> None:
        namespace = VALIDATOR_GLOBALS["require_m3_03_completion_artifact"].__globals__
        saved = {key: namespace[key] for key in ("github_api", "github_tree_blob_map", "github_paginated_object_rows")}
        try:
            def github_api(endpoint: str) -> object:
                fixture["api_calls"].append(endpoint)
                if endpoint in fixture["api"]:
                    return fixture["api"][endpoint]
                if endpoint == (
                    "repos/Project-Helianthus/helianthus-modbusreg/"
                    "actions/runs/73/attempts/1"
                ):
                    return fixture["run"]
                return fixture["blobs"][endpoint.rsplit("/", 1)[-1]]
            namespace["github_api"] = github_api
            def tree_map(_repo: str, _tree: str, label: str):
                if "RED parent tree" in label:
                    return fixture["red_parent_tree"]
                if "RED tree" in label:
                    return fixture["red_tree"]
                if label.endswith("base tree"):
                    return fixture["base_tree"]
                return fixture["tree"]
            namespace["github_tree_blob_map"] = tree_map
            def paginated_rows(endpoint: str, *_: object) -> object:
                fixture["job_page_calls"].append(endpoint)
                if endpoint in fixture["job_pages"]:
                    return fixture["job_pages"][endpoint]
                if endpoint.endswith("/actions/runs/72/attempts/1/jobs"):
                    return fixture["red_jobs"]
                if endpoint.endswith("/actions/runs/73/attempts/1/jobs"):
                    return fixture["jobs"]
                raise AssertionError(f"unexpected paginated endpoint: {endpoint}")
            namespace["github_paginated_object_rows"] = paginated_rows
            binding = {"head_sha": "a" * 40, "head_tree_sha": "b" * 40,
                       "github_pull_request_number": 67,
                       "completion_artifact": artifact}
            if message is None:
                VALIDATOR_GLOBALS["require_m3_03_completion_artifact"](
                    "Project-Helianthus/helianthus-modbusreg", binding, PLAN)
            else:
                with self.assertRaises(VALIDATOR_GLOBALS["ValidationError"]) as raised:
                    VALIDATOR_GLOBALS["require_m3_03_completion_artifact"](
                        "Project-Helianthus/helianthus-modbusreg", binding, PLAN)
                self.assertIn(message, str(raised.exception))
        finally:
            namespace.update(saved)

    def bind_m3_03_overlay_red_evidence(
        self, artifact: dict[str, object], fixture: dict[str, object],
    ) -> None:
        repository = "Project-Helianthus/helianthus-modbusreg"
        artifact["overlay_tdd"] = {
            "red_commit_sha": "c" * 40,
            "red_workflow_run_id": 72,
            "red_workflow_run_attempt": 1,
            "red_job_id": 720,
            "red_check_run_id": 721,
            "red_test_name": "TestFroniusOverlayActivatesThroughNeutralRuntime",
        }
        source_sha, source_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        fixture["api"].update({
            f"repos/{repository}/commits/{'c' * 40}": {
                "sha": "c" * 40,
                "commit": {
                    "message": "test(fronius): RED transport-neutral overlay",
                    "tree": {"sha": "e" * 40},
                },
                "parents": [{"sha": "f" * 40}],
                "files": [{"filename": artifact["tests"][0]["source_path"]}],
            },
            f"repos/{repository}/compare/{'c' * 40}...{'a' * 40}": {
                "status": "ahead", "merge_base_commit": {"sha": "c" * 40},
            },
            f"repos/{repository}/actions/runs/72/attempts/1": {
                "id": 72, "run_attempt": 1, "workflow_id": 74,
                "path": artifact["workflow_path"],
                "event": "pull_request", "head_sha": "c" * 40,
                "head_repository": {"full_name": repository},
                "status": "completed", "conclusion": "failure",
                "pull_requests": [{
                    "number": 67,
                    "base": {"ref": "main", "repo": {"full_name": repository}},
                    "head": {"sha": "a" * 40, "repo": {"full_name": repository}},
                }],
            },
        })
        fixture["red_jobs"] = [{
            "id": 720, "name": "verify", "head_sha": "c" * 40,
            "status": "completed", "conclusion": "failure",
            "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/721",
            "steps": [
                {"name": "Prepare isolated Fronius proof package", "conclusion": "success"},
                {"name": "Build Fronius proof package", "conclusion": "success"},
                {"name": "Run Fronius neutral activation", "conclusion": "failure"},
            ],
        }]

    def test_m3_03_completion_artifact_binds_derived_scan_and_test_execution(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        self.assert_m3_03_artifact(artifact, fixture)

    def test_m3_03_green_later_rerun_cannot_replace_selected_attempt(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        repository = "Project-Helianthus/helianthus-modbusreg"
        root_run = f"repos/{repository}/actions/runs/73"
        root_jobs = f"repos/{repository}/actions/runs/73/jobs"
        fixture["api"][root_run] = {
            "id": 73, "run_attempt": 2, "head_sha": "f" * 40,
            "status": "completed", "conclusion": "failure",
        }
        fixture["job_pages"][root_jobs] = [{
            "id": 999, "name": "verify", "head_sha": "f" * 40,
            "status": "completed", "conclusion": "failure",
            "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/999",
            "steps": [],
        }]
        self.assert_m3_03_artifact(artifact, fixture)
        self.assertNotIn(root_run, fixture["api_calls"])
        self.assertNotIn(root_jobs, fixture["job_page_calls"])

    def test_m3_03_red_later_rerun_cannot_replace_selected_attempt(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        self.bind_m3_03_overlay_red_evidence(artifact, fixture)
        repository = "Project-Helianthus/helianthus-modbusreg"
        root_run = f"repos/{repository}/actions/runs/72"
        root_jobs = f"repos/{repository}/actions/runs/72/jobs"
        fixture["api"][root_run] = {
            "id": 72, "run_attempt": 2, "head_sha": "e" * 40,
            "status": "completed", "conclusion": "success",
        }
        fixture["job_pages"][root_jobs] = [{
            "id": 998, "name": "verify", "head_sha": "e" * 40,
            "status": "completed", "conclusion": "success",
            "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/998",
            "steps": [],
        }]
        self.assert_m3_03_artifact(artifact, fixture)
        self.assertNotIn(root_run, fixture["api_calls"])
        self.assertNotIn(root_jobs, fixture["job_page_calls"])

    def test_m3_03_rejects_mismatched_green_attempt_job_or_check(self) -> None:
        cases = {
            "attempt": lambda _artifact, fixture: fixture["run"].update({
                "run_attempt": 2,
            }),
            "job": lambda _artifact, fixture: fixture["jobs"][0].update({
                "id": 999,
            }),
            "check": lambda _artifact, fixture: fixture["jobs"][0].update({
                "check_run_url": (
                    "https://api.github.com/repos/Project-Helianthus/"
                    "helianthus-modbusreg/check-runs/999"
                ),
            }),
        }
        for case, mutate in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact()
                mutate(artifact, fixture)
                expected = (
                    "exact-head workflow evidence is invalid"
                    if case == "attempt"
                    else "exact-head workflow job identity or outcome mismatch"
                )
                self.assert_m3_03_artifact(artifact, fixture, expected)

    def test_m3_03_rejects_mismatched_red_attempt_job_or_check(self) -> None:
        cases = {
            "attempt": lambda _artifact, fixture: fixture["api"][
                "repos/Project-Helianthus/helianthus-modbusreg/"
                "actions/runs/72/attempts/1"
            ].update({"run_attempt": 2}),
            "job": lambda _artifact, fixture: fixture["red_jobs"][0].update({
                "id": 999,
            }),
            "check": lambda _artifact, fixture: fixture["red_jobs"][0].update({
                "check_run_url": (
                    "https://api.github.com/repos/Project-Helianthus/"
                    "helianthus-modbusreg/check-runs/999"
                ),
            }),
        }
        for case, mutate in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact(
                    overlay_packages=["profiles/fronius"],
                    disposition="OVERLAY_REQUIRED",
                )
                self.bind_m3_03_overlay_red_evidence(artifact, fixture)
                mutate(artifact, fixture)
                expected = (
                    "RED workflow evidence is invalid"
                    if case == "attempt"
                    else "RED workflow lacks the intended failing neutral activation test"
                )
                self.assert_m3_03_artifact(artifact, fixture, expected)

    def test_m3_03_completion_artifact_rejects_self_reported_stale_scan(self) -> None:
        artifact, fixture = self.m3_03_artifact(overlay_packages=["profiles/fronius"])
        self.assert_m3_03_artifact(artifact, fixture, "package scan does not equal")

    def test_m3_03_completion_artifact_rejects_spoofed_or_noop_test(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        workflow_sha, workflow_blob = self.github_blob(b"jobs: {verify: {steps: [{run: 'true'}]}}\n")
        fixture["blobs"][workflow_sha] = workflow_blob
        fixture["tree"][artifact["workflow_path"]] = workflow_sha
        artifact["workflow_blob_sha"] = workflow_sha
        self.assert_m3_03_artifact(
            artifact, fixture,
            "workflow blob does not match the plan-pinned canonical contract",
        )

    def test_m3_03_completion_artifact_rejects_missing_test_declaration(self) -> None:
        source = self.m3_03_test_source()["registry/fronius_overlay_test.go"].replace(
            b"func TestFroniusOverlayRejectsTCPConcreteImports(t *testing.T)",
            b"func harmless(t *testing.T)",
        )
        artifact, fixture = self.m3_03_artifact(source_texts={
            "registry/fronius_overlay_test.go": source,
        })
        self.assert_m3_03_artifact(artifact, fixture, "not a proper Go test declaration")

    def test_m3_03_completion_artifact_rejects_empty_named_tests(self) -> None:
        source = self.m3_03_test_source()["registry/fronius_overlay_test.go"]
        source = source.replace(
            b" packages, err := froniusOverlayProductionPackages()\n"
            b" if err != nil { t.Fatal(err) }\n"
            b" if offending := hasTCPConcreteImport(packages); offending != \"\" { t.Fatal(offending) }\n",
            b"",
        ).replace(
            b" runtime := neutralRuntimeNoTCP{}\n"
            b" err := activateFroniusProfile(&runtime)\n"
            b" if !errors.Is(err, neutralRuntimeProbeError) { t.Fatal(err) }\n",
            b"",
        )
        artifact, fixture = self.m3_03_artifact(source_texts={
            "registry/fronius_overlay_test.go": source,
        })
        self.assert_m3_03_artifact(artifact, fixture, "empty, assertion-free, or semantic no-op")

    def test_m3_03_completion_artifact_rejects_tcp_concrete_production_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        source_sha, source_blob = self.github_blob(
            b"package fronius\nimport \"net\"\nvar _ *net.TCPConn\n"
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        self.assert_m3_03_artifact(artifact, fixture, "imports a TCP-concrete dependency")

    def test_m3_03_completion_artifact_rejects_raw_string_tcp_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(overlay_packages=["profiles/fronius"])
        source_sha, source_blob = self.github_blob(
            b"package fronius\nimport `net`\nvar _ *net.TCPConn\n"
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        self.assert_m3_03_artifact(artifact, fixture, "imports a TCP-concrete dependency")

    def test_m3_03_completion_artifact_rejects_escaped_tcp_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"]
        )
        source_sha, source_blob = self.github_blob(
            br'''package fronius
import "n\x65t"
var _ *net.TCPConn
'''
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "imports a TCP-concrete dependency"
        )

    def test_m3_03_completion_artifact_rejects_unicode_alias_tcp_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"]
        )
        source_sha, source_blob = self.github_blob(
            'package fronius\nimport 网 "net"\nvar _ *网.TCPConn\n'.encode("utf-8")
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "imports a TCP-concrete dependency"
        )

    def test_m3_03_completion_artifact_rejects_same_line_semicolon_tcp_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        source_sha, source_blob = self.github_blob(
            b'package fronius; import "net"; var _ net.TCPConn\n'
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        implementation_sha, implementation_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/implementation.go"] = implementation_sha
        fixture["blobs"][implementation_sha] = implementation_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "same-line semicolon syntax"
        )

    def test_m3_03_completion_artifact_rejects_compact_grouped_tcp_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        source_sha, source_blob = self.github_blob(
            b'package fronius\nimport ("net")\nvar _ *net.TCPConn\n'
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        implementation_sha, implementation_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/implementation.go"] = implementation_sha
        fixture["blobs"][implementation_sha] = implementation_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "imports a TCP-concrete dependency"
        )

    def test_m3_03_completion_artifact_rejects_indirect_standard_net_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        source_sha, source_blob = self.github_blob(
            b'package fronius\nimport "net/http"\nvar _ = http.MethodGet\n'
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        implementation_sha, implementation_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/implementation.go"] = implementation_sha
        fixture["blobs"][implementation_sha] = implementation_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "imports a TCP-concrete dependency"
        )

    def test_m3_03_completion_artifact_rejects_disguised_tcp_package(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        source_sha, source_blob = self.github_blob(
            b'package fronius\nimport "example.com/modbus/transport/tcpclient"\n'
            b'var _ = tcpclient.Dial\n'
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        implementation_sha, implementation_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/implementation.go"] = implementation_sha
        fixture["blobs"][implementation_sha] = implementation_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "imports a TCP-concrete dependency"
        )

    def test_m3_03_completion_artifact_rejects_unsealed_third_party_import(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        source_sha, source_blob = self.github_blob(
            b'package fronius\nimport "example.com/semantic/helpers"\n'
            b'var _ = helpers.Normalize\n'
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        implementation_sha, implementation_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/implementation.go"] = implementation_sha
        fixture["blobs"][implementation_sha] = implementation_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "outside the sealed transport-neutral allowlist"
        )

    def test_m3_03_completion_artifact_rejects_build_excluded_production_adapter(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        proof_sha, proof_blob = self.github_blob(
            b"//go:build never\n\npackage fronius\n"
            b"type NeutralRuntime interface { Read() error }\n"
            b"func activateFroniusProfile(runtime NeutralRuntime) error { return runtime.Read() }\n"
        )
        proof_path = artifact["neutral_runtime_proof"]["source_path"]
        artifact["neutral_runtime_proof"]["source_blob_sha"] = proof_sha
        fixture["tree"][proof_path] = proof_sha
        fixture["blobs"][proof_sha] = proof_blob
        implementation_sha, implementation_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/implementation.go"] = implementation_sha
        fixture["blobs"][implementation_sha] = implementation_blob
        self.assert_m3_03_artifact(artifact, fixture, "is build-excluded")

    def test_m3_03_completion_artifact_rejects_tcp_in_neutral_proof_source(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        proof_sha, proof_blob = self.github_blob(
            b"package registry\nimport \"net\"\n"
            b"type NeutralRuntime interface { Read() error }\n"
            b"func activateFroniusProfile(runtime NeutralRuntime) error {\n"
            b" var _ *net.TCPConn\n return runtime.Read()\n}\n"
        )
        artifact["neutral_runtime_proof"]["source_blob_sha"] = proof_sha
        proof_path = artifact["neutral_runtime_proof"]["source_path"]
        fixture["tree"][proof_path] = proof_sha
        fixture["blobs"][proof_sha] = proof_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "not the exact minimal neutral adapter"
        )

    def test_m3_03_completion_artifact_rejects_fronius_source_outside_namespace(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        source_sha, source_blob = self.github_blob(
            b"package profiles\nconst froniusRegister = 40069\n"
        )
        fixture["tree"]["profiles/vendor.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "escapes profiles/fronius namespace"
        )

    def test_m3_03_completion_artifact_rejects_activation_that_ignores_runtime(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        proof_sha, proof_blob = self.github_blob(
            b"package registry\n"
            b"type NeutralRuntime interface { Read() error }\n"
            b"func activateFroniusProfile(runtime NeutralRuntime) error { return nil }\n"
        )
        artifact["neutral_runtime_proof"]["source_blob_sha"] = proof_sha
        proof_path = artifact["neutral_runtime_proof"]["source_path"]
        fixture["tree"][proof_path] = proof_sha
        fixture["blobs"][proof_sha] = proof_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "not the exact minimal neutral adapter"
        )

    def test_m3_03_completion_artifact_rejects_dead_assertion_control_flow(self) -> None:
        artifact, fixture = self.m3_03_artifact(source_texts=self.m3_03_test_source(
            import_body=(
                b" _ = froniusOverlayProductionPackages(); _ = hasTCPConcreteImport(nil)\n"
                b" if false { t.Fatal(\"dead\") }\n"
            ),
            activation_body=(
                b" runtime := neutralRuntimeNoTCP{}; _ = activateFroniusProfile(runtime)\n"
                b" if false { t.Fatal(\"dead\") }\n"
            ),
        ))
        self.assert_m3_03_artifact(artifact, fixture, "closed canonical proof")

    def test_m3_03_completion_artifact_rejects_closed_body_bypasses(self) -> None:
        canonical_import = (
            b" packages := froniusOverlayProductionPackages()\n"
            b" if offending := hasTCPConcreteImport(packages); offending != \"\" "
            b"{ t.Fatal(offending) }\n"
        )
        canonical_activation = (
            b" runtime := neutralRuntimeNoTCP{}\n"
            b" err := activateFroniusProfile(&runtime)\n"
            b" if !errors.Is(err, neutralRuntimeProbeError) { t.Fatal(err) }\n"
        )
        cases = {
            "import_early_return": self.m3_03_test_source(
                import_body=b" return\n" + canonical_import,
                activation_body=canonical_activation,
            ),
            "import_always_taken_branch": self.m3_03_test_source(
                import_body=b" if true { return }\n" + canonical_import,
                activation_body=canonical_activation,
            ),
            "import_extra_prelude": self.m3_03_test_source(
                import_body=b" _ = 1\n" + canonical_import,
                activation_body=canonical_activation,
            ),
            "activation_early_return": self.m3_03_test_source(
                import_body=canonical_import,
                activation_body=b" return\n" + canonical_activation,
            ),
            "activation_always_taken_branch": self.m3_03_test_source(
                import_body=canonical_import,
                activation_body=b" if true { return }\n" + canonical_activation,
            ),
            "activation_extra_prelude": self.m3_03_test_source(
                import_body=canonical_import,
                activation_body=b" _ = 1\n" + canonical_activation,
            ),
        }
        for case, source_texts in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact(source_texts=source_texts)
                self.assert_m3_03_artifact(
                    artifact, fixture, "closed canonical proof"
                )

    def test_m3_03_completion_artifact_rejects_runtime_scanner_stubs_and_omissions(self) -> None:
        source = self.m3_03_test_source()["registry/fronius_overlay_test.go"]
        scanner_start = source.index(b"func froniusOverlayProductionPackages")
        scanner_end = source.index(b"type neutralRuntimeNoTCP")
        prefix, suffix = source[:scanner_start], source[scanner_end:]
        cases = {
            "nil_empty_stubs": (
                b"func froniusOverlayProductionPackages() ([]string, error) { return nil, nil }\n"
                b"func hasTCPConcreteImport([]string) string { return \"\" }\n"
            ),
            "constant_package_list": (
                b"func froniusOverlayProductionPackages() ([]string, error) { return []string{\"net\"}, nil }\n"
                b"func hasTCPConcreteImport(imports []string) string { return \"\" }\n"
            ),
            "ignored_read_parse_or_unquote_errors": source[scanner_start:scanner_end].replace(
                b"if err != nil { return nil, err }", b"if err != nil { }",
            ),
            "cwd_relative_directory": source[scanner_start:scanner_end].replace(
                b"os.ReadDir(directory)", b"os.ReadDir(\".\")",
            ),
            "relative_parse_path": source[scanner_start:scanner_end].replace(
                b"parser.ParseFile(token.NewFileSet(), sourcePath, nil, parser.ImportsOnly)",
                b"parser.ParseFile(token.NewFileSet(), entry.Name(), nil, parser.ImportsOnly)",
            ),
            "zero_file_success": source[scanner_start:scanner_end].replace(
                b"if scanned == 0 { return nil, errors.New(\"no direct production Go source scanned\") }\n ",
                b"",
            ),
            "skips_build_suffixed_sources": source[scanner_start:scanner_end].replace(
                b"strings.HasSuffix(entry.Name(), \"_test.go\")",
                b"strings.HasSuffix(entry.Name(), \"_test.go\") || strings.HasSuffix(entry.Name(), \"_linux.go\")",
            ),
            "incomplete_tcp_predicate": source[scanner_start:scanner_end].replace(
                b" || normalized == \"modbus_tcp\" || normalized == \"modbustcp\"", b"",
            ),
        }
        for case, replacement in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact(source_texts={
                    "registry/fronius_overlay_test.go": prefix + replacement + suffix,
                })
                self.assert_m3_03_artifact(
                    artifact, fixture,
                    ("exact complete path-component scan"
                     if case == "incomplete_tcp_predicate"
                     else "exact fail-closed runtime scanner"),
                )

    @unittest.skipUnless(shutil.which("go"), "Go toolchain is required for runtime scanner proof")
    def test_m3_03_runtime_scanner_rejects_tcp_import_after_production_init_chdir(self) -> None:
        source = self.m3_03_test_source()["registry/fronius_overlay_test.go"]
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp)
            (package / "go.mod").write_text("module example.com/fronius-scanner\n\ngo 1.24\n", encoding="utf-8")
            (package / "fronius_overlay_test.go").write_bytes(source)
            (package / "transport_linux.go").write_text(
                "package registry\n\nimport (\n\t\"net\"\n\t\"os\"\n)\n\n"
                "var _ net.Conn\n\nfunc init() {\n\tdirectory, err := os.MkdirTemp(\"\", \"fmv3-empty-\")\n"
                "\tif err != nil { panic(err) }\n\tif err := os.Chdir(directory); err != nil { panic(err) }\n}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["go", "test", ".", "-run", "^TestFroniusOverlayRejectsTCPConcreteImports$"],
                cwd=package, text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("net", result.stdout + result.stderr)

    def test_m3_03_completion_artifact_rejects_fabricated_registry_test_package(self) -> None:
        source = self.m3_03_test_source()["registry/fronius_overlay_test.go"].replace(
            b"package registry\n", b"package registry_test\n", 1,
        )
        artifact, fixture = self.m3_03_artifact(source_texts={
            "registry/fronius_overlay_test.go": source,
        })
        self.assert_m3_03_artifact(
            artifact, fixture, "fixed proof package"
        )

    def test_m3_03_completion_artifact_rejects_build_excluded_named_test(self) -> None:
        artifact, fixture = self.m3_03_artifact(source_texts={
            "registry/fronius_overlay_test.go": (
                b"//go:build never\n\npackage registry\nimport \"errors\"\nimport \"testing\"\n"
                b"type neutralRuntimeNoTCP struct{}\n"
                b"var neutralRuntimeProbeError = errors.New(\"probe\")\n"
                b"func (*neutralRuntimeNoTCP) Read() error { return neutralRuntimeProbeError }\n"
                b"var _ NeutralRuntime = (*neutralRuntimeNoTCP)(nil)\n"
                b"func TestFroniusOverlayRejectsTCPConcreteImports(t *testing.T) {\n"
                b" packages := froniusOverlayProductionPackages()\n"
                b" if offending := hasTCPConcreteImport(packages); offending != \"\" { t.Fatal(offending) }\n}\n"
                b"func TestFroniusOverlayActivatesThroughNeutralRuntime(t *testing.T) {\n"
                b" runtime := neutralRuntimeNoTCP{}\n err := activateFroniusProfile(&runtime)\n"
                b" if !errors.Is(err, neutralRuntimeProbeError) { t.Fatal(err) }\n}\n"
            ),
        })
        self.assert_m3_03_artifact(
            artifact, fixture, "neutral runtime proof package is invalid"
        )

    def test_m3_03_completion_artifact_rejects_implicitly_excluded_named_test(self) -> None:
        for replacement in (
            "registry/fronius_overlay_windows_test.go",
            "registry/_fronius_overlay_test.go",
        ):
            with self.subTest(path=replacement):
                artifact, fixture = self.m3_03_artifact()
                original = artifact["tests"][0]["source_path"]
                for item in artifact["tests"]:
                    item["source_path"] = replacement
                fixture["tree"][replacement] = fixture["tree"].pop(original)
                fixture["red_tree"][replacement] = fixture["red_tree"].pop(original)
                self.assert_m3_03_artifact(
                    artifact, fixture, "fixed canonical proof source"
                )

    def test_m3_03_completion_artifact_rejects_implicitly_excluded_production_adapter(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        proof_path = artifact["neutral_runtime_proof"]["source_path"]
        replacement = "profiles/fronius/activation_windows.go"
        artifact["neutral_runtime_proof"]["source_path"] = replacement
        fixture["tree"][replacement] = fixture["tree"].pop(proof_path)
        implementation_sha, implementation_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/implementation.go"] = implementation_sha
        fixture["blobs"][implementation_sha] = implementation_blob
        self.assert_m3_03_artifact(artifact, fixture, "is build-excluded")

    def test_m3_03_sibling_init_github_path_shim_is_neutralized_by_preparation(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        sibling_sha, sibling_blob = self.github_blob(
            b"package registry\nfunc init() { _ = \"$GITHUB_PATH go shim\" }\n"
        )
        fixture["tree"]["registry/sibling_test.go"] = sibling_sha
        fixture["blobs"][sibling_sha] = sibling_blob
        self.assert_m3_03_artifact(artifact, fixture)

    def test_m3_03_sibling_testmain_is_neutralized_by_preparation(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        sibling_sha, sibling_blob = self.github_blob(
            b"package registry\nfunc TestMain() {}\n"
        )
        fixture["tree"]["registry/sibling_test.go"] = sibling_sha
        fixture["blobs"][sibling_sha] = sibling_blob
        self.assert_m3_03_artifact(artifact, fixture)

    def test_m3_03_unchanged_base_sibling_is_neutralized_by_preparation(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        base_sha, base_blob = self.github_blob(b"package registry\nconst baseline = 1\n")
        fixture["base_tree"]["registry/baseline_test.go"] = base_sha
        fixture["tree"]["registry/baseline_test.go"] = base_sha
        fixture["blobs"][base_sha] = base_blob
        self.assert_m3_03_artifact(artifact, fixture)

    def test_m3_03_standard_only_permits_unchanged_base_production_init(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        base_sha, base_blob = self.github_blob(b"package registry\nfunc init() {}\n")
        fixture["base_tree"]["registry/base.go"] = base_sha
        fixture["tree"]["registry/base.go"] = base_sha
        fixture["blobs"][base_sha] = base_blob
        self.assert_m3_03_artifact(artifact, fixture)

    def test_m3_03_added_unbound_sibling_test_is_neutralized_by_preparation(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        sibling_sha, sibling_blob = self.github_blob(
            b"package registry\nfunc TestUnboundSibling(t *testing.T) {}\n"
        )
        fixture["tree"]["registry/unbound_test.go"] = sibling_sha
        fixture["blobs"][sibling_sha] = sibling_blob
        self.assert_m3_03_artifact(artifact, fixture)

    def test_m3_03_templates_pin_readonly_permissions_and_isolated_build_then_tests(self) -> None:
        for disposition, contract in VALIDATOR_GLOBALS["M3_03_WORKFLOW_CONTRACT"].items():
            with self.subTest(disposition=disposition):
                template = (PLAN / contract["template_path"]).read_bytes()
                workflow = yaml.safe_load(template)
                self.assertEqual(workflow["permissions"], {"contents": "read"})
                self.assertEqual(template.count(b"go test "), 2)
                self.assertEqual(template.count(b"go build "), 1)
                expected_build = (
                    b"go build ./profiles/fronius/..."
                    if disposition == "OVERLAY_REQUIRED"
                    else b"go build ./registry"
                )
                self.assertIn(expected_build, template)
                if disposition == "OVERLAY_REQUIRED":
                    self.assertNotIn(b"go build ./profiles/fronius\n", template)
                self.assertIn(b"Prepare isolated Fronius proof package", template)
                self.assertIn(b"Run Fronius neutral activation", template)
                self.assertIn(b"Run Fronius import boundary", template)
                self.assertIn(b"^TestFroniusOverlayActivatesThroughNeutralRuntime$", template)
                self.assertIn(b"^TestFroniusOverlayRejectsTCPConcreteImports$", template)
                self.assertNotEqual(
                    hashlib.sha256(
                        template.replace(b"contents: read", b"contents: write")
                    ).hexdigest(),
                    contract["sha256"],
                )

    def test_m3_03_rendered_head_tree_assertion_executes_and_rejects_mutation(self) -> None:
        command = yaml.safe_load(
            (PLAN / VALIDATOR_GLOBALS["M3_03_WORKFLOW_CONTRACT"]["STANDARD_ONLY"]["template_path"])
            .read_text(encoding="utf-8")
        )["jobs"]["verify"]["steps"][1]["run"]
        expression = "${{ github.event.pull_request.head.sha }}"
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.git(repo, "init")
            self.git(repo, "config", "user.name", "M3 assertion test")
            self.git(repo, "config", "user.email", "m3-assertion@example.invalid")
            (repo / "proof.txt").write_text("one\n", encoding="utf-8")
            self.git(repo, "add", "proof.txt")
            self.git(repo, "commit", "-m", "first")
            head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            self.assertRegex(head, r"^[0-9a-f]{40}$")
            rendered = command.replace(expression, head)
            self.assertEqual(
                subprocess.run(rendered, cwd=repo, shell=True, text=True).returncode, 0
            )
            (repo / "proof.txt").write_text("two\n", encoding="utf-8")
            self.git(repo, "commit", "-am", "second")
            wrong = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            self.assertNotEqual(
                subprocess.run(rendered, cwd=repo, shell=True, text=True).returncode, 0
            )
            self.assertNotEqual(
                subprocess.run(rendered.replace(f"{head}^{{tree}}", f"{wrong}^{{tree}}"),
                               cwd=repo, shell=True, text=True).returncode, 0
            )

    def test_m3_03_rejects_cleanup_workflow_mutation(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        canonical = base64.b64decode(fixture["blobs"][artifact["workflow_blob_sha"]]["content"])
        mutated_sha, mutated_blob = self.github_blob(canonical.replace(
            b"! -name 'fronius_overlay_test.go' -delete",
            b"! -name 'fronius_overlay_test.go' -print",
        ))
        artifact["workflow_blob_sha"] = mutated_sha
        fixture["tree"][artifact["workflow_path"]] = mutated_sha
        fixture["blobs"][mutated_sha] = mutated_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "workflow blob does not match the plan-pinned canonical contract"
        )

    def test_m3_03_rejects_overlay_production_init_and_test_symbols(self) -> None:
        for source in (
            b"package fronius\nfunc init() {}\n",
            b"package fronius\nvar neutralRuntimeProbeError = 1\n",
            b"package fronius\ntype neutralRuntimeNoTCP struct{}\n",
        ):
            with self.subTest(source=source):
                artifact, fixture = self.m3_03_artifact(
                    overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
                )
                self.bind_m3_03_overlay_red_evidence(artifact, fixture)
                source_sha, source_blob = self.github_blob(source)
                fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
                fixture["blobs"][source_sha] = source_blob
                self.assert_m3_03_artifact(
                    artifact, fixture, "overlay production source profiles/fronius/overlay.go has test-only"
                )

    def test_m3_03_rejects_missing_or_failed_green_build_or_test_evidence(self) -> None:
        cases = {
            "build": "Build Fronius proof package",
            "activation": "Run Fronius neutral activation",
            "import": "Run Fronius import boundary",
        }
        for case, step_name in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact()
                fixture["jobs"][0]["steps"] = [
                    step for step in fixture["jobs"][0]["steps"]
                    if step["name"] != step_name
                ]
                self.assert_m3_03_artifact(
                    artifact, fixture, f"GREEN workflow lacks successful {step_name}"
                )

    def test_m3_03_rejects_red_build_failure_and_import_failure_after_activation(self) -> None:
        cases = {
            "build": [
                {"name": "Prepare isolated Fronius proof package", "conclusion": "success"},
                {"name": "Build Fronius proof package", "conclusion": "failure"},
            ],
            "import_after_activation": [
                {"name": "Prepare isolated Fronius proof package", "conclusion": "success"},
                {"name": "Build Fronius proof package", "conclusion": "success"},
                {"name": "Run Fronius neutral activation", "conclusion": "success"},
                {"name": "Run Fronius import boundary", "conclusion": "failure"},
            ],
        }
        for case, steps in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact(
                    overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
                )
                self.bind_m3_03_overlay_red_evidence(artifact, fixture)
                fixture["red_jobs"][0]["steps"] = steps
                self.assert_m3_03_artifact(
                    artifact, fixture, "RED workflow lacks the intended failing neutral activation test"
                )

    def test_m3_03_rejects_artifact_named_test_init(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        source_path = artifact["tests"][0]["source_path"]
        original_sha = fixture["tree"][source_path]
        source = base64.b64decode(fixture["blobs"][original_sha]["content"])
        source_sha, source_blob = self.github_blob(source + b"func init() {}\n")
        fixture["tree"][source_path] = source_sha
        fixture["blobs"][source_sha] = source_blob
        for item in artifact["tests"]:
            item["source_blob_sha"] = source_sha
        self.assert_m3_03_artifact(
            artifact, fixture, "neutral runtime proof is not the exact bound source"
        )

    def test_m3_03_completion_artifact_rejects_decoy_workflow_command(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        workflow_sha, workflow_blob = self.github_blob(
            b"jobs:\n"
            b"  decoy:\n    if: false\n    steps:\n"
            b"      - run: go test ./... -run '^TestFroniusOverlayActivatesThroughNeutralRuntime$'\n"
            b"  verify:\n    steps:\n"
            b"      - name: run TestFroniusOverlayRejectsTCPConcreteImports\n"
            b"        run: go test ./... -run '^TestFroniusOverlayRejectsTCPConcreteImports$'\n"
            b"      - name: run TestFroniusOverlayActivatesThroughNeutralRuntime\n"
            b"        run: 'true'\n"
        )
        artifact["workflow_blob_sha"] = workflow_sha
        fixture["tree"][".github/workflows/ci.yml"] = workflow_sha
        fixture["blobs"][workflow_sha] = workflow_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "workflow path is not bound to the plan-pinned"
        )

    def test_m3_03_workflow_contract_rejects_terminal_review_bypasses(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        canonical_blob = base64.b64decode(
            fixture["blobs"][artifact["workflow_blob_sha"]]["content"]
        )

        def replace(old: bytes, new: bytes) -> tuple[dict[str, object], dict[str, object]]:
            candidate = dict(artifact)
            candidate_fixture = {
                **fixture,
                "tree": dict(fixture["tree"]),
                "blobs": dict(fixture["blobs"]),
            }
            blob_sha, blob = self.github_blob(canonical_blob.replace(old, new, 1))
            candidate["workflow_blob_sha"] = blob_sha
            candidate_fixture["tree"][candidate["workflow_path"]] = blob_sha
            candidate_fixture["blobs"][blob_sha] = blob
            return candidate, candidate_fixture

        cases = {
            "alternate_blob": (b"ubuntu-24.04", b"ubuntu-22.04"),
            "checkout_main": (
                b"ref: ${{ github.event.pull_request.head.sha }}", b"ref: main",
            ),
            "checkout_action": (
                b"actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
                b"actions/checkout@main",
            ),
            "head_tree_assertion": (
                b"Assert bound head and tree", b"Assert bound head only",
            ),
            "self_hosted_runner": (b"runs-on: ubuntu-24.04", b"runs-on: self-hosted"),
            "preceding_path_wrapper": (
                b"    steps:\n", b"    steps:\n      - name: prepend PATH wrapper\n        run: echo /tmp/decoy >> $GITHUB_PATH\n",
            ),
            "extra_arbitrary_step": (
                b"      - name: Run Fronius import boundary\n",
                b"      - name: arbitrary wrapper\n        run: true\n      - name: Run Fronius import boundary\n",
            ),
        }
        for case, (old, new) in cases.items():
            with self.subTest(case=case):
                candidate, candidate_fixture = replace(old, new)
                self.assert_m3_03_artifact(
                    candidate, candidate_fixture,
                    "workflow blob does not match the plan-pinned canonical contract",
                )

        alternate = dict(artifact)
        alternate["workflow_path"] = ".github/workflows/alternate.yml"
        self.assert_m3_03_artifact(
            alternate, fixture,
            "workflow path is not bound to the plan-pinned",
        )

    def test_m3_03_completion_artifact_rejects_inherited_workflow_overrides(self) -> None:
        cases = {
            "workflow_default_shell": (
                b"defaults:\n  run:\n    shell: bash\n"
                b"jobs:\n  verify:\n    steps:\n"
            ),
            "workflow_default_working_directory": (
                b"defaults:\n  run:\n    working-directory: decoy\n"
                b"jobs:\n  verify:\n    steps:\n"
            ),
            "workflow_env": (
                b"env:\n  GOFLAGS: -tags=decoy\n"
                b"jobs:\n  verify:\n    steps:\n"
            ),
        }
        steps = (
            b"      - name: run TestFroniusOverlayRejectsTCPConcreteImports\n"
            b"        run: go test ./registry -run '^TestFroniusOverlayRejectsTCPConcreteImports$'\n"
            b"      - name: run TestFroniusOverlayActivatesThroughNeutralRuntime\n"
            b"        run: go test ./registry -run '^TestFroniusOverlayActivatesThroughNeutralRuntime$'\n"
        )
        for case, workflow_source in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact()
                workflow_sha, workflow_blob = self.github_blob(workflow_source + steps)
                artifact["workflow_blob_sha"] = workflow_sha
                fixture["tree"][".github/workflows/ci.yml"] = workflow_sha
                fixture["blobs"][workflow_sha] = workflow_blob
                self.assert_m3_03_artifact(
                    artifact, fixture, "workflow path is not bound to the plan-pinned"
                )

    def test_m3_03_completion_artifact_rejects_selected_job_overrides(self) -> None:
        cases = {
            "continue_on_error": b"    continue-on-error: true\n",
            "job_env": b"    env:\n      GOFLAGS: -tags=decoy\n",
            "container": b"    container: golang:latest\n",
        }
        steps = (
            b"    steps:\n"
            b"      - name: run TestFroniusOverlayRejectsTCPConcreteImports\n"
            b"        run: go test ./registry -run '^TestFroniusOverlayRejectsTCPConcreteImports$'\n"
            b"      - name: run TestFroniusOverlayActivatesThroughNeutralRuntime\n"
            b"        run: go test ./registry -run '^TestFroniusOverlayActivatesThroughNeutralRuntime$'\n"
        )
        for case, job_override in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact()
                workflow_sha, workflow_blob = self.github_blob(
                    b"jobs:\n  verify:\n" + job_override + steps
                )
                artifact["workflow_blob_sha"] = workflow_sha
                fixture["tree"][".github/workflows/ci.yml"] = workflow_sha
                fixture["blobs"][workflow_sha] = workflow_blob
                self.assert_m3_03_artifact(
                    artifact, fixture, "workflow path is not bound to the plan-pinned"
                )

    def test_m3_03_completion_artifact_rejects_selected_step_env_overrides(self) -> None:
        cases = {
            "path": b"        env:\n          PATH: /tmp/decoy\n",
            "goflags": b"        env:\n          GOFLAGS: -exec=/tmp/decoy\n",
        }
        for case, step_env in cases.items():
            with self.subTest(case=case):
                artifact, fixture = self.m3_03_artifact()
                workflow_sha, workflow_blob = self.github_blob(
                    b"jobs:\n  verify:\n    steps:\n"
                    b"      - name: run TestFroniusOverlayRejectsTCPConcreteImports\n"
                    + step_env
                    + b"        run: go test ./registry -run '^TestFroniusOverlayRejectsTCPConcreteImports$'\n"
                    b"      - name: run TestFroniusOverlayActivatesThroughNeutralRuntime\n"
                    b"        run: go test ./registry -run '^TestFroniusOverlayActivatesThroughNeutralRuntime$'\n"
                )
                artifact["workflow_blob_sha"] = workflow_sha
                fixture["tree"][".github/workflows/ci.yml"] = workflow_sha
                fixture["blobs"][workflow_sha] = workflow_blob
                self.assert_m3_03_artifact(
                    artifact, fixture, "workflow path is not bound to the plan-pinned"
                )

    def test_m3_03_completion_artifact_rejects_tcp_state_in_neutral_fake(self) -> None:
        artifact, fixture = self.m3_03_artifact(source_texts={
            "registry/fronius_overlay_test.go": (
                b"package registry\nimport `net`\nimport \"testing\"\n"
                b"type neutralRuntimeNoTCP struct{ conn *net.TCPConn }\n"
                b"func (*neutralRuntimeNoTCP) Read() {}\n"
                b"var _ NeutralRuntime = (*neutralRuntimeNoTCP)(nil)\n"
                b"func TestFroniusOverlayRejectsTCPConcreteImports(t *testing.T) {\n"
                b" packages := froniusOverlayProductionPackages()\n"
                b" if offending := hasTCPConcreteImport(packages); offending != \"\" { t.Fatal(offending) }\n}\n"
                b"func TestFroniusOverlayActivatesThroughNeutralRuntime(t *testing.T) {\n"
                b" runtime := neutralRuntimeNoTCP{}\n"
                b" if err := activateFroniusProfile(runtime); err != nil { t.Fatal(err) }\n}\n"
            ),
        })
        self.assert_m3_03_artifact(artifact, fixture, "imports a TCP-concrete dependency")

    def test_m3_03_completion_artifact_rejects_overlay_required_without_overlay(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        artifact["overlay_tdd"] = {
            "red_commit_sha": "c" * 40, "red_workflow_run_id": 72,
            "red_workflow_run_attempt": 1, "red_job_id": 720,
            "red_check_run_id": 721,
            "red_test_name": "TestFroniusOverlayActivatesThroughNeutralRuntime",
        }
        self.assert_m3_03_artifact(artifact, fixture, "lacks exact RED evidence or a production overlay")

    def test_m3_03_standard_only_rejects_production_change_outside_overlay(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        source_sha, source_blob = self.github_blob(
            b"package registry\nconst vendorImplementation = true\n"
        )
        fixture["tree"]["registry/vendor.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        self.assert_m3_03_artifact(
            artifact, fixture, "STANDARD_ONLY changes production implementation"
        )

    def test_m3_03_overlay_required_rejects_unrelated_production_change(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        self.bind_m3_03_overlay_red_evidence(artifact, fixture)
        source_sha, source_blob = self.github_blob(
            b"package registry\nconst unrelatedProductionChange = true\n"
        )
        fixture["tree"]["registry/unrelated.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        self.assert_m3_03_artifact(
            artifact,
            fixture,
            "OVERLAY_REQUIRED changes production outside profiles/fronius",
        )

    def test_m3_03_overlay_required_rejects_nested_module_skipped_by_go_wildcard(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius", "profiles/fronius/internal"],
            disposition="OVERLAY_REQUIRED",
        )
        self.bind_m3_03_overlay_red_evidence(artifact, fixture)
        source_sha, source_blob = self.github_blob(
            b"package internal\nconst nestedImplementation = true\n"
        )
        module_sha, module_blob = self.github_blob(
            b"module example.invalid/hidden\n\ngo 1.24\n"
        )
        fixture["tree"]["profiles/fronius/internal/impl.go"] = source_sha
        fixture["tree"]["profiles/fronius/internal/go.mod"] = module_sha
        fixture["blobs"][source_sha] = source_blob
        fixture["blobs"][module_sha] = module_blob
        self.assert_m3_03_artifact(
            artifact,
            fixture,
            "nested module or wildcard-excluded directory",
        )

    def test_m3_03_completion_artifact_accepts_overlay_with_live_red_evidence(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        artifact["overlay_tdd"] = {
            "red_commit_sha": "c" * 40, "red_workflow_run_id": 72,
            "red_workflow_run_attempt": 1, "red_job_id": 720,
            "red_check_run_id": 721,
            "red_test_name": "TestFroniusOverlayActivatesThroughNeutralRuntime",
        }
        source_sha, source_blob = self.github_blob(b"package fronius\nconst enabled = true\n")
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        repository = "Project-Helianthus/helianthus-modbusreg"
        fixture["api"].update({
            f"repos/{repository}/commits/{'c' * 40}": {
                "sha": "c" * 40,
                "commit": {
                    "message": "test(fronius): RED transport-neutral overlay",
                    "tree": {"sha": "e" * 40},
                },
                "parents": [{"sha": "f" * 40}],
                "files": [{"filename": artifact["tests"][0]["source_path"]}],
            },
            f"repos/{repository}/compare/{'c' * 40}...{'a' * 40}": {
                "status": "ahead", "merge_base_commit": {"sha": "c" * 40},
            },
            f"repos/{repository}/actions/runs/72/attempts/1": {
                "id": 72, "run_attempt": 1, "workflow_id": 74,
                "path": artifact["workflow_path"],
                "event": "pull_request", "head_sha": "c" * 40,
                "head_repository": {"full_name": repository},
                "status": "completed", "conclusion": "failure",
                "pull_requests": [{
                    "number": 67,
                    "base": {"ref": "main", "repo": {"full_name": repository}},
                    "head": {"sha": "a" * 40, "repo": {"full_name": repository}},
                }],
            },
        })
        fixture["red_jobs"] = [{
            "id": 720, "name": "verify", "head_sha": "c" * 40,
            "status": "completed", "conclusion": "failure",
            "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/721",
            "steps": [
                {"name": "Prepare isolated Fronius proof package", "conclusion": "success"},
                {"name": "Build Fronius proof package", "conclusion": "success"},
                {"name": "Run Fronius neutral activation", "conclusion": "failure"},
            ],
        }]
        self.assert_m3_03_artifact(artifact, fixture)

    def test_m3_03_overlay_red_rejects_testmain_or_compile_decoy_source(self) -> None:
        for label, decoy in {
            "testmain": b"package fronius\nfunc TestMain() {}\n",
            "compile_decoy": b"//go:build ignore\npackage fronius\n",
        }.items():
            with self.subTest(label=label):
                artifact, fixture = self.m3_03_artifact(
                    overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
                )
                self.bind_m3_03_overlay_red_evidence(artifact, fixture)
                decoy_sha, decoy_blob = self.github_blob(decoy)
                canonical = artifact["tests"][0]["source_path"]
                fixture["red_tree"][canonical] = decoy_sha
                fixture["blobs"][decoy_sha] = decoy_blob
                self.assert_m3_03_artifact(
                    artifact, fixture,
                    "RED canonical test source blob differs from the exact GREEN source",
                )

    def test_m3_03_overlay_red_rejects_production_overlay_before_red(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        self.bind_m3_03_overlay_red_evidence(artifact, fixture)
        repository = "Project-Helianthus/helianthus-modbusreg"
        fixture["api"][f"repos/{repository}/commits/{'c' * 40}"]["parents"] = [
            {"sha": "d" * 40}
        ]
        self.assert_m3_03_artifact(
            artifact, fixture, "RED parent SHA is not the exact PR base"
        )

    def test_m3_03_red_tree_diff_rejects_hidden_production_change(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        artifact["overlay_tdd"] = {
            "red_commit_sha": "c" * 40, "red_workflow_run_id": 72,
            "red_workflow_run_attempt": 1, "red_job_id": 720,
            "red_check_run_id": 721,
            "red_test_name": "TestFroniusOverlayActivatesThroughNeutralRuntime",
        }
        source_sha, source_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        fixture["red_tree"]["profiles/fronius/overlay.go"] = source_sha
        repository = "Project-Helianthus/helianthus-modbusreg"
        fixture["api"].update({
            f"repos/{repository}/commits/{'c' * 40}": {
                "sha": "c" * 40,
                "commit": {
                    "message": "test(fronius): RED transport-neutral overlay",
                    "tree": {"sha": "e" * 40},
                },
                "parents": [{"sha": "f" * 40}],
                "files": [{"filename": artifact["tests"][0]["source_path"]}],
            },
            f"repos/{repository}/compare/{'c' * 40}...{'a' * 40}": {
                "status": "ahead", "merge_base_commit": {"sha": "c" * 40},
            },
            f"repos/{repository}/actions/runs/72/attempts/1": {
                "id": 72, "run_attempt": 1, "workflow_id": 74,
                "path": ".github/workflows/ci.yml",
                "event": "pull_request", "head_sha": "c" * 40,
                "head_repository": {"full_name": repository},
                "status": "completed", "conclusion": "failure",
                "pull_requests": [{
                    "number": 67,
                    "base": {"ref": "main", "repo": {"full_name": repository}},
                    "head": {"sha": "a" * 40, "repo": {"full_name": repository}},
                }],
            },
        })
        fixture["red_jobs"] = [{
            "id": 720, "name": "verify", "head_sha": "c" * 40,
            "status": "completed", "conclusion": "failure",
            "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/721",
            "steps": [
                {"name": "Prepare isolated Fronius proof package", "conclusion": "success"},
                {"name": "Build Fronius proof package", "conclusion": "success"},
                {"name": "Run Fronius neutral activation", "conclusion": "failure"},
            ],
        }]
        self.assert_m3_03_artifact(
            artifact, fixture, "RED tree diff is not complete test-only evidence"
        )

    def test_m3_03_completion_artifact_rejects_red_workflow_blob_spoof(self) -> None:
        artifact, fixture = self.m3_03_artifact(
            overlay_packages=["profiles/fronius"], disposition="OVERLAY_REQUIRED"
        )
        artifact["overlay_tdd"] = {
            "red_commit_sha": "c" * 40,
            "red_workflow_run_id": 72,
            "red_workflow_run_attempt": 1,
            "red_job_id": 720,
            "red_check_run_id": 721,
            "red_test_name": "TestFroniusOverlayActivatesThroughNeutralRuntime",
        }
        source_sha, source_blob = self.github_blob(
            b"package fronius\nconst enabled = true\n"
        )
        fixture["tree"]["profiles/fronius/overlay.go"] = source_sha
        fixture["blobs"][source_sha] = source_blob
        repository = "Project-Helianthus/helianthus-modbusreg"
        fixture["api"].update({
            f"repos/{repository}/commits/{'c' * 40}": {
                "sha": "c" * 40,
                "commit": {
                    "message": "test(fronius): RED transport-neutral overlay",
                    "tree": {"sha": "e" * 40},
                },
                "parents": [{"sha": "f" * 40}],
                "files": [{"filename": artifact["tests"][0]["source_path"]}],
            },
            f"repos/{repository}/compare/{'c' * 40}...{'a' * 40}": {
                "status": "ahead", "merge_base_commit": {"sha": "c" * 40},
            },
            f"repos/{repository}/actions/runs/72/attempts/1": {
                "id": 72, "run_attempt": 1, "workflow_id": 74,
                "path": ".github/workflows/ci.yml",
                "event": "pull_request", "head_sha": "c" * 40,
                "head_repository": {"full_name": repository},
                "status": "completed", "conclusion": "failure",
                "pull_requests": [{
                    "number": 67,
                    "base": {"ref": "main", "repo": {"full_name": repository}},
                    "head": {"sha": "a" * 40, "repo": {"full_name": repository}},
                }],
            },
        })
        fixture["red_jobs"] = [{
            "id": 720, "name": "verify", "head_sha": "c" * 40,
            "status": "completed", "conclusion": "failure",
            "check_run_url": f"https://api.github.com/repos/{repository}/check-runs/721",
            "steps": [
                {"name": "Prepare isolated Fronius proof package", "conclusion": "success"},
                {"name": "Build Fronius proof package", "conclusion": "success"},
                {"name": "Run Fronius neutral activation", "conclusion": "failure"},
            ],
        }]
        fixture["red_tree"][artifact["workflow_path"]] = "f" * 40
        fixture["red_parent_tree"][artifact["workflow_path"]] = "f" * 40
        self.assert_m3_03_artifact(
            artifact, fixture, "RED workflow blob differs from the declared exact workflow"
        )

    def test_m3_03_completion_artifact_rejects_unrelated_successful_run(self) -> None:
        artifact, fixture = self.m3_03_artifact()
        fixture["run"]["path"] = ".github/workflows/unrelated.yml"
        fixture["run"]["pull_requests"][0]["number"] = 999
        self.assert_m3_03_artifact(artifact, fixture, "exact-head workflow evidence is invalid")

    def test_dynamic_certificate_rejects_stale_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = f"repos/{dependency['repository']}/issues/{dependency['github_issue_number']}"
                responses[endpoint]["title"] = "FMV3-M2-01: stale completion"
            self.assert_m2_02_dynamic_mutation_rejected(temp, mutate, "identity/title/closure mismatch")

    def test_dynamic_certificate_rejects_missing_anchored_issue_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = f"repos/{dependency['repository']}/issues/{dependency['github_issue_number']}"
                responses[endpoint]["body"] = "lookalike no-op dependency"
            self.assert_m2_02_dynamic_mutation_rejected(
                temp, mutate, "identity/title/closure mismatch"
            )

    def test_dynamic_certificate_rejects_unanchored_issue_spec_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            dependency["issue_spec_sha256"] = "f" * 64
            evidence = self.write_authorization_evidence(
                temp, "FMV3-M2-02", [dependency]
            )
            responses = self.m1_admission_responses(implementing, anchor)
            responses.update(self.dynamic_dependency_responses(dependency))
            result = self.authorize(
                implementing, anchor, "FMV3-M2-02",
                github_responses=responses, authorization_evidence=evidence,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("certificate issue spec digest differs from anchor", result.stderr)

    def test_dynamic_certificate_rejects_second_page_duplicate_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                base = f"repos/{dependency['repository']}/commits/{dependency['head_sha']}/check-runs"
                rows = responses[base]["check_runs"]
                padding = [{
                    "id": 50000 + index,
                    "name": f"unrelated-{index}",
                    "head_sha": dependency["head_sha"],
                    "status": "completed",
                    "conclusion": "success",
                    "app": {"id": GITHUB_ACTIONS_APP_ID},
                } for index in range(98)]
                responses[base + "?filter=all&per_page=100&page=1"] = {
                    "total_count": 101,
                    "check_runs": [*rows, *padding],
                }
                duplicate = dict(rows[0])
                duplicate["id"] = rows[0]["id"]
                duplicate["conclusion"] = "failure"
                responses[base + "?filter=all&per_page=100&page=2"] = {
                    "total_count": 101,
                    "check_runs": [duplicate],
                }
            self.assert_m2_02_dynamic_mutation_rejected(
                temp, mutate, "exact-head required check failed"
            )

    def test_dynamic_certificate_rejects_unmerged_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = f"repos/{dependency['repository']}/pulls/{dependency['github_pull_request_number']}"
                responses[endpoint]["merged"] = False
            self.assert_m2_02_dynamic_mutation_rejected(temp, mutate, "wrong or unmerged issue/PR")

    def test_dynamic_certificate_rejects_pr_branch_not_bound_to_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = (
                    f"repos/{dependency['repository']}/pulls/"
                    f"{dependency['github_pull_request_number']}"
                )
                responses[endpoint]["head"]["ref"] = "issue/999-unbound"
            self.assert_m2_02_dynamic_mutation_rejected(
                temp, mutate, "wrong or unmerged issue/PR"
            )

    def test_dynamic_certificate_rejects_pr_outside_issue_interval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = (
                    f"repos/{dependency['repository']}/pulls/"
                    f"{dependency['github_pull_request_number']}"
                )
                responses[endpoint]["created_at"] = "2026-08-01T09:59:59Z"
            self.assert_m2_02_dynamic_mutation_rejected(
                temp, mutate, "selected PR interval is outside the selected issue interval"
            )

    def test_dynamic_certificate_rejects_wrong_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = f"repos/{dependency['repository']}/git/commits/{dependency['merge_sha']}"
                responses[endpoint]["tree"]["sha"] = "9" * 40
            self.assert_m2_02_dynamic_mutation_rejected(temp, mutate, "squash tree/topology mismatch")

    def test_dynamic_certificate_rejects_failed_required_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = f"repos/{dependency['repository']}/commits/{dependency['head_sha']}/check-runs"
                responses[endpoint]["check_runs"][0]["conclusion"] = "failure"
            self.assert_m2_02_dynamic_mutation_rejected(temp, mutate, "exact-head required check failed")

    def test_dynamic_certificate_rejects_postmerge_rerun_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = (
                    f"repos/{dependency['repository']}/commits/"
                    f"{dependency['head_sha']}/check-runs"
                )
                bound = responses[endpoint]["check_runs"][0]
                bound["conclusion"] = "failure"
                responses[endpoint]["check_runs"].append({
                    **bound,
                    "id": 999999,
                    "conclusion": "success",
                    "completed_at": "2026-08-01T13:00:00Z",
                })
            self.assert_m2_02_dynamic_mutation_rejected(
                temp, mutate, "exact-head required check failed"
            )

    def test_dynamic_certificate_rejects_same_name_wrong_app(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            dependency["required_checks"][0]["app_id"] = 1234
            dependency["required_check_runs"][0]["app_id"] = 1234
            evidence = self.write_authorization_evidence(temp, "FMV3-M2-02", [dependency])
            responses = self.m1_admission_responses(implementing, anchor)
            dynamic = self.dynamic_dependency_responses(dependency)
            endpoint = f"repos/{dependency['repository']}/commits/{dependency['head_sha']}/check-runs"
            dynamic[endpoint]["check_runs"][0]["app"] = {"id": 9999}
            responses.update(dynamic)
            result = self.authorize(
                implementing, anchor, "FMV3-M2-02", github_responses=responses,
                authorization_evidence=evidence,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checks@1234", result.stderr)

    def test_dynamic_certificate_rejects_legacy_context_only_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = (
                    f"repos/{dependency['repository']}/branches/main/protection/"
                    "required_status_checks"
                )
                responses[endpoint]["checks"] = []
            self.assert_m2_02_dynamic_mutation_rejected(
                temp, mutate, "app-bound checks are unavailable"
            )

    def test_dynamic_certificate_rejects_mixed_legacy_required_check_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(dependency: dict[str, object], responses: dict[str, object]) -> None:
                endpoint = (
                    f"repos/{dependency['repository']}/branches/main/protection/"
                    "required_status_checks"
                )
                responses[endpoint]["contexts"].append("legacy-unbound")
            self.assert_m2_02_dynamic_mutation_rejected(
                temp, mutate, "legacy context without an app-bound check"
            )

    def test_static_m1_04_rejects_pr_issue_relation_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            binding = STATIC_DEPENDENCIES["FMV3-M1-04"]
            responses = {
                f"repos/{binding['repository']}/issues/{binding['github_issue_number']}/timeline?per_page=100": []
            }
            result = self.authorize(
                implementing, anchor, "FMV3-M1-05", self.amendment_pr(anchor), responses
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PR/issue timeline relation is absent", result.stderr)

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
            self.assertIn("current authorization PR mismatch", result.stderr)

    def test_amendment_authorization_rejects_placeholder_pr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing, "PENDING_PR_URL")
            result = self.authorize(implementing, anchor, "FMV3-M1-05")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("current authorization PR mismatch", result.stderr)

    def test_recomputed_lifecycle_only_surface_digest_preserves_authorization(self) -> None:
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
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fail-closed execution allowlist", result.stdout)

    def test_reflowed_canonical_authorization_whitespace_preserves_surface_digest(
        self,
    ) -> None:
        """Canonical prose whitespace is mutable; authorization words and fields are not."""
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            original_digest = self.amendment_surface_digest(copied)
            canonical = copied / "00-canonical.md"
            original = "sole current\nimmutable authorization anchor"
            reflowed = "sole\ncurrent immutable authorization anchor"
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
        """Milestone progress is mutable; issue count, hard stop, and gateway ban are not."""
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
            self.git(plan_root.parent, "push", TEST_PUBLISH_REMOTE, "main")
            current = self.git(plan_root.parent, "rev-parse", "HEAD").stdout.strip()
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M1-05",
                github_responses=self.m1_admission_responses(plan_root, anchor),
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
            self.assertIn(
                "authorization PR #91 is not merged at the plan authorization SHA",
                result.stderr,
            )

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
            self.assertIn(
                "authorization PR #91 is not merged at the plan authorization SHA",
                result.stderr,
            )

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
                    "Determine Fronius phase-1 applicability from Modbus TCP evidence and implement only any evidence-required transport-neutral read-only overlay.",
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
                "FMV3-M1-06 merged after sequential anchored harness/product PRs, "
                "trusted RED/GREEN/mutation proof, clean reviews, fixed conformance "
                "report, and canonical-main proof | FMV3-M2-01 |"
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

    def test_gateway_authorization_status_contradiction_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            self.set_gateway_status_authorization(copied, authorized=True)
            result = subprocess.run(
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "contradictory gateway authorization in 99-status.md", result.stderr
            )

    def test_amendment_surface_digest_binds_complete_canonical_prose(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            original = self.amendment_surface_digest(copied)
            canonical = copied / "00-canonical.md"
            text = canonical.read_text(encoding="utf-8")
            old = "This implementing plan replaces the W28 package as execution intent."
            self.assertEqual(text.count(old), 1)
            canonical.write_text(
                text.replace(old, "This plan weakens the W28 execution intent.", 1),
                encoding="utf-8",
            )
            self.assertNotEqual(original, self.amendment_surface_digest(copied))

    def test_amendment_surface_digest_binds_every_normative_prose_surface(self) -> None:
        for name in (
            "01-index.md",
            "10-architecture-and-repo-boundaries.md",
            "11-fronius-readonly-and-semantic-lock.md",
            "12-vendor-expansion-and-private-bindings.md",
            "13-roadmap-gates-and-risks.md",
            "90-issue-map.md",
            "91-milestone-map.md",
            "92-adversarial-review.md",
            "99-status.md",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                copied = self.copied_plan(temp)
                original = self.amendment_surface_digest(copied)
                surface = copied / name
                surface.write_text(
                    surface.read_text(encoding="utf-8")
                    + "\nNormative full-surface regression drift.\n",
                    encoding="utf-8",
                )
                self.assertNotEqual(original, self.amendment_surface_digest(copied))

    def test_contradictory_gateway_authorization_fails_on_any_surface(self) -> None:
        for name in (
            "00-canonical.md",
            "01-index.md",
            "10-architecture-and-repo-boundaries.md",
            "11-fronius-readonly-and-semantic-lock.md",
            "12-vendor-expansion-and-private-bindings.md",
            "13-roadmap-gates-and-risks.md",
            "90-issue-map.md",
            "91-milestone-map.md",
            "92-adversarial-review.md",
            "99-status.md",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                copied = self.copied_plan(temp)
                surface = copied / name
                surface.write_text(
                    surface.read_text(encoding="utf-8")
                    + "\nGateway execution is authorized.\n",
                    encoding="utf-8",
                )
                result = subprocess.run(
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
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"contradictory gateway authorization in {name}",
                    result.stderr,
                )

        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            issue = next(row for row in plan["issues"] if row["id"] == "FMV3-M3-03")
            issue["rollback"] = "Gateway implementation is authorized."
            plan_path.write_text(
                yaml.safe_dump(plan, sort_keys=False), encoding="utf-8"
            )
            result = subprocess.run(
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "contradictory gateway authorization in plan.yaml", result.stderr
            )

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

    def test_authorization_rejects_anchor_immutable_status_restored_on_current(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate_anchor_status(root: Path) -> None:
                status_path = root / "99-status.md"
                status = status_path.read_text(encoding="utf-8")
                old = (
                    "Canonical main authority: fixed GitHub API for "
                    "Project-Helianthus/helianthus-execution-plans; origin is identity-only"
                )
                new = "Canonical main authority: local origin/main"
                self.assertEqual(status.count(old), 1)
                status_path.write_text(
                    status.replace(old, new, 1), encoding="utf-8"
                )

            def restore_current_status(root: Path) -> None:
                status_path = root / "99-status.md"
                status = status_path.read_text(encoding="utf-8")
                old = "Canonical main authority: local origin/main"
                new = (
                    "Canonical main authority: fixed GitHub API for "
                    "Project-Helianthus/helianthus-execution-plans; origin is identity-only"
                )
                self.assertEqual(status.count(old), 1)
                status_path.write_text(
                    status.replace(old, new, 1), encoding="utf-8"
                )

            plan_root, anchor, current = self.published_amendment_snapshots(
                temp,
                mutate_anchor_status,
                restore_current_status,
            )
            result = self.authorize(
                plan_root,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "current main amendment surface digest differs from merged PR #91 anchor",
                result.stderr,
            )
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

    def mutate_issue_contract(
        self,
        plan_root: Path,
        issue_id: str,
        field: str,
        mutate: Callable[[dict[str, object]], None],
    ) -> subprocess.CompletedProcess[str]:
        plan_path = plan_root / "plan.yaml"
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        issue = next(issue for issue in plan["issues"] if issue["id"] == issue_id)
        mutate(issue[field])
        issues_by_id = {candidate["id"]: candidate for candidate in plan["issues"]}
        authorized = plan["execution_authorization"]["authorized_issues"]
        contract_rows = [issues_by_id[candidate] for candidate in authorized]
        plan["execution_authorization"][
            "authorized_issue_contract_sha256"
        ] = hashlib.sha256(
            json.dumps(
                contract_rows, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
        return self.run_validator(plan_root)

    def test_capability_state_is_source_private_and_not_a_ledger_pointer(self) -> None:
        contract = next(
            issue for issue in PLAN_DATA["issues"] if issue["id"] == "FMV3-M1-05"
        )["opaque_runtime_acquisition_contract"]
        self.assertEqual(contract["state_owner"], "source_owned_shared_capability_state")
        self.assertEqual(contract["value_copy_semantics"], "shared_state")
        self.assertEqual(contract["representation"], "opaque_non_serializable")

    def test_old_source_issued_shared_ledger_pointer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M1-05",
                "opaque_runtime_acquisition_contract",
                lambda contract: contract.update(
                    {"state_owner": "source_issued_shared_ledger_pointer"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FMV3-M1-05 opaque acquisition docs contract mismatch", result.stderr)

    def test_caller_controlled_deliverability_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M1-06",
                "source_kind_contract",
                lambda contract: contract["runtime"]["deliverability"].update(
                    {"authority": "caller_boolean", "caller_control": "allowed"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FMV3-M1-06 opaque acquisition implementation contract mismatch", result.stderr)

    def test_endpoint_recreation_aliasing_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M1-05",
                "opaque_runtime_acquisition_contract",
                lambda contract: contract["endpoint_recreation"].update(
                    {"eligible_new_acquisition": "alias_prior_visible_identity"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FMV3-M1-05 opaque acquisition docs contract mismatch", result.stderr)

    def test_open_only_attempt_bound_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract["bounds"].update(
                    {"covered_attempt_states": ["open"]}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FMV3-M2-01 opaque capability consumer contract mismatch", result.stderr)

    def test_undefined_claim_transition_or_outcome_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract["claim_entry_lifecycle"].update(
                    {"terminal": []}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FMV3-M2-01 opaque capability consumer contract mismatch", result.stderr)

    def test_claim_in_progress_and_cancelling_lifecycle_drift_is_rejected(self) -> None:
        mutations: tuple[Callable[[dict[str, object]], None], ...] = (
            lambda contract: contract["claim_entry_lifecycle"].update(
                {"nonterminal": ["unresolved"]}
            ),
            lambda contract: contract["attempt_lifecycle"].update(
                {
                    "legal_transitions": [
                        transition
                        for transition in contract["attempt_lifecycle"][
                            "legal_transitions"
                        ]
                        if "cancelling" not in transition
                    ]
                }
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as temp:
                copied = self.copied_plan(temp)
                result = self.mutate_issue_contract(
                    copied,
                    "FMV3-M2-01",
                    "attempt_ledger_contract",
                    mutate,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    "FMV3-M2-01 opaque capability consumer contract mismatch",
                    result.stderr,
                )

    def test_atomic_seal_and_cancel_open_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract["attempt_lifecycle"].update(
                    {"seal_condition": "all_claim_entries_terminal"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "FMV3-M2-01 opaque capability consumer contract mismatch",
                result.stderr,
            )
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M1-06",
                "opaque_runtime_acquisition_contract",
                lambda contract: contract["attempt_binding"].update(
                    {"source_operation": "caller_owned_CancelOpen"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "FMV3-M1-06 opaque acquisition implementation contract mismatch",
                result.stderr,
            )

    def test_r2_critical_invariant_drift_is_rejected_after_digest_regeneration(self) -> None:
        cases: tuple[
            tuple[str, str, Callable[[dict[str, object]], None], str], ...
        ] = (
            (
                "FMV3-M1-06",
                "opaque_runtime_acquisition_contract",
                lambda contract: contract["attempt_binding"].update(
                    {"lookup": "AttemptKey_only"}
                ),
                "FMV3-M1-06 opaque acquisition implementation contract mismatch",
            ),
            (
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract["dependency_set"].update(
                    {"order": "unordered_set"}
                ),
                "FMV3-M2-01 opaque capability consumer contract mismatch",
            ),
            (
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract["attempt_lifecycle"].update(
                    {"publish_commit_linearization": "effect_then_state_two_steps"}
                ),
                "FMV3-M2-01 opaque capability consumer contract mismatch",
            ),
            (
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract["published_projection"].update(
                    {"additional_fields": "allowed"}
                ),
                "FMV3-M2-01 opaque capability consumer contract mismatch",
            ),
            (
                "FMV3-M2-01",
                "downstream_conformance_contract",
                lambda contract: contract.update({"docs_lock": ["manifest_sha256"]}),
                "FMV3-M1-05 opaque acquisition docs contract mismatch",
            ),
        )
        for issue_id, field, mutate, expected_error in cases:
            with self.subTest(issue_id=issue_id, field=field), tempfile.TemporaryDirectory() as temp:
                copied = self.copied_plan(temp)
                result = self.mutate_issue_contract(
                    copied, issue_id, field, mutate
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected_error, result.stderr)

    def test_bounded_values_and_nonwrapping_sequences_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M2-01",
                "bounded_values_contract",
                lambda contract: contract["attempt_key"].update({"max": "unbounded"}),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "FMV3-M2-01 opaque capability consumer contract mismatch",
                result.stderr,
            )
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M1-06",
                "opaque_runtime_acquisition_contract",
                lambda contract: contract["bounded_state"]["terminal_sequence"].update(
                    {"wrap": "allowed"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "FMV3-M1-06 opaque acquisition implementation contract mismatch",
                result.stderr,
            )

    def test_retryable_or_mutable_publish_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract.update(
                    {
                        "publish": "retryable_mutable_dto",
                        "mutable_dto": "allowed",
                    }
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FMV3-M2-01 opaque capability consumer contract mismatch", result.stderr)

    def test_unbounded_terminal_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            result = self.mutate_issue_contract(
                copied,
                "FMV3-M2-01",
                "attempt_ledger_contract",
                lambda contract: contract["reclamation"]["audit_tombstone"].update(
                    {"count_bound": "unbounded"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FMV3-M2-01 opaque capability consumer contract mismatch", result.stderr)

    def test_exact_docs_candidate_machine_projection_matches_plan(self) -> None:
        docs_root = Path(os.environ["FMV3_DOCS_CANDIDATE_ROOT"])
        anchor = PLAN_DATA["execution_authorization"]["authorization_anchor"]
        binding = anchor["docs_candidate_binding"]
        manifest_path = docs_root / binding["manifest_path"]
        policy_path = docs_root / binding["policy_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            binding["manifest_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(policy_path.read_bytes()).hexdigest(),
            binding["policy_sha256"],
        )
        for relative, expected_sha256 in binding["normative_blobs"].items():
            blob = self.git(
                docs_root,
                "show",
                f"{binding['commit_sha']}:{relative}",
            ).stdout.encode("utf-8")
            self.assertEqual(hashlib.sha256(blob).hexdigest(), expected_sha256)
        projection = {
            field: manifest[field] for field in binding["machine_projection_fields"]
        }
        self.assertEqual(
            hashlib.sha256(
                json.dumps(
                    projection, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest(),
            binding["machine_projection_sha256"],
        )
        projection_without_bounded_values = {
            field: manifest[field]
            for field in binding["machine_projection_fields"]
            if field != "bounded_values"
        }
        self.assertEqual(
            hashlib.sha256(
                json.dumps(
                    projection_without_bounded_values,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            binding["machine_projection_without_bounded_values_sha256"],
        )
        issues = {issue["id"]: issue for issue in PLAN_DATA["issues"]}
        self.assertEqual(
            issues["FMV3-M1-05"]["source_kind_contract"],
            manifest["source_kind"],
        )
        self.assertEqual(
            issues["FMV3-M1-06"]["opaque_runtime_acquisition_contract"],
            manifest["opaque_capability"],
        )
        self.assertEqual(
            issues["FMV3-M2-01"]["attempt_ledger_contract"],
            manifest["m2_ledger"],
        )
        self.assertEqual(
            issues["FMV3-M2-01"]["normalization_round_trip_contract"],
            manifest["normalization_record"],
        )
        for issue_id in ("FMV3-M1-05", "FMV3-M1-06", "FMV3-M2-01"):
            self.assertEqual(
                issues[issue_id]["bounded_values_contract"],
                manifest["bounded_values"],
            )

    def test_pr91_bootstrap_rejects_coordinated_docs_semantic_weakening(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp) / "docs-candidate"
            subprocess.run(
                ["git", "clone", "--no-local", os.environ["FMV3_DOCS_CANDIDATE_ROOT"], str(docs)],
                check=True, capture_output=True, text=True,
            )
            self.git(docs, "checkout", "--detach", PLAN_DATA["execution_authorization"]
                     ["authorization_anchor"]["docs_candidate_binding"]["commit_sha"])
            self.git(docs, "remote", "set-url", "origin",
                     "https://github.com/Project-Helianthus/helianthus-docs-ebus.git")
            manifest_path = docs / "docs/platform/manifests/opaque-runtime-acquisition-v1.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source_kind"]["runtime"]["deliverability"]["caller_control"] = "allowed"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            policy_path = docs / "docs/platform/opaque-runtime-acquisition-v1.md"
            policy_path.write_text(policy_path.read_text(encoding="utf-8").replace(
                "Deliverability MUST NOT be caller-controlled",
                "Deliverability MAY be caller-controlled",
            ), encoding="utf-8")
            validator_path = docs / "scripts/validate_opaque_runtime_acquisition.py"
            validator_path.write_text(validator_path.read_text(encoding="utf-8").replace(
                '"caller_control": "forbidden"', '"caller_control": "allowed"', 1,
            ), encoding="utf-8")
            self.git(docs, "config", "user.name", "Bootstrap test")
            self.git(docs, "config", "user.email", "bootstrap@example.invalid")
            self.git(docs, "add", "docs/platform/manifests/opaque-runtime-acquisition-v1.json",
                     "docs/platform/opaque-runtime-acquisition-v1.md",
                     "scripts/validate_opaque_runtime_acquisition.py")
            self.git(docs, "commit", "-m", "weaken coordinated docs contract")
            head = self.git(docs, "rev-parse", "HEAD").stdout.strip()
            binding = json.loads(json.dumps(
                PLAN_DATA["execution_authorization"]["authorization_anchor"]["docs_candidate_binding"]
            ))
            binding["commit_sha"] = head
            binding["commit_tree_sha"] = self.git(docs, "rev-parse", "HEAD^{tree}").stdout.strip()
            for relative in binding["normative_blobs"]:
                binding["normative_blobs"][relative] = hashlib.sha256(
                    self.git(docs, "show", f"{head}:{relative}").stdout.encode("utf-8")
                ).hexdigest()
            binding["manifest_sha256"] = binding["normative_blobs"][binding["manifest_path"]]
            binding["policy_sha256"] = binding["normative_blobs"][binding["policy_path"]]
            projection = {field: manifest[field] for field in binding["machine_projection_fields"]}
            binding["machine_projection_sha256"] = hashlib.sha256(json.dumps(
                projection, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            without_bounds = {field: manifest[field] for field in binding["machine_projection_fields"]
                              if field != "bounded_values"}
            binding["machine_projection_without_bounded_values_sha256"] = hashlib.sha256(json.dumps(
                without_bounds, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            namespace = VALIDATOR_GLOBALS["load_docs_candidate"].__globals__
            saved_expected = namespace["EXPECTED_DOCS_CANDIDATE_BINDING"]
            old_root = os.environ.get("FMV3_DOCS_CANDIDATE_ROOT")
            try:
                namespace["EXPECTED_DOCS_CANDIDATE_BINDING"] = binding
                os.environ["FMV3_DOCS_CANDIDATE_ROOT"] = str(docs)
                with self.assertRaises(VALIDATOR_GLOBALS["ValidationError"]) as raised:
                    VALIDATOR_GLOBALS["load_docs_candidate"](binding)
                self.assertIn("PR #91 trust anchor", str(raised.exception))
            finally:
                namespace["EXPECTED_DOCS_CANDIDATE_BINDING"] = saved_expected
                if old_root is None:
                    os.environ.pop("FMV3_DOCS_CANDIDATE_ROOT", None)
                else:
                    os.environ["FMV3_DOCS_CANDIDATE_ROOT"] = old_root

    def test_pr91_bootstrap_rejects_top_level_and_nested_duplicate_manifest_keys(self) -> None:
        for label, needle in (
            ("top-level", '"content_revision": 1,'),
            ("nested", '"caller_control": "forbidden",'),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                docs = Path(temp) / "docs-candidate"
                subprocess.run(["git", "clone", "--no-local", os.environ["FMV3_DOCS_CANDIDATE_ROOT"], str(docs)],
                               check=True, capture_output=True, text=True)
                original = PLAN_DATA["execution_authorization"]["authorization_anchor"]["docs_candidate_binding"]
                self.git(docs, "checkout", "--detach", original["commit_sha"])
                self.git(docs, "remote", "set-url", "origin",
                         "https://github.com/Project-Helianthus/helianthus-docs-ebus.git")
                manifest_path = docs / original["manifest_path"]
                manifest_text = manifest_path.read_text(encoding="utf-8")
                self.assertIn(needle, manifest_text)
                manifest_path.write_text(manifest_text.replace(
                    needle, needle + "\n  " + needle, 1
                ), encoding="utf-8")
                policy_path = docs / original["policy_path"]
                policy_path.write_text(policy_path.read_text(encoding="utf-8") + "\n<!-- coordinated hash refresh -->\n", encoding="utf-8")
                validator_path = docs / "scripts/validate_opaque_runtime_acquisition.py"
                validator_path.write_text(validator_path.read_text(encoding="utf-8") + "\n# coordinated hash refresh\n", encoding="utf-8")
                self.git(docs, "config", "user.name", "Duplicate key test")
                self.git(docs, "config", "user.email", "duplicate@example.invalid")
                self.git(docs, "add", original["manifest_path"], original["policy_path"],
                         "scripts/validate_opaque_runtime_acquisition.py")
                self.git(docs, "commit", "-m", f"coordinate {label} duplicate")
                head = self.git(docs, "rev-parse", "HEAD").stdout.strip()
                binding = json.loads(json.dumps(original))
                binding["commit_sha"] = head
                binding["commit_tree_sha"] = self.git(docs, "rev-parse", "HEAD^{tree}").stdout.strip()
                for relative in binding["normative_blobs"]:
                    binding["normative_blobs"][relative] = hashlib.sha256(
                        self.git(docs, "show", f"{head}:{relative}").stdout.encode("utf-8")
                    ).hexdigest()
                binding["manifest_sha256"] = binding["normative_blobs"][binding["manifest_path"]]
                binding["policy_sha256"] = binding["normative_blobs"][binding["policy_path"]]
                namespace = VALIDATOR_GLOBALS["load_docs_candidate"].__globals__
                previous, old_root = namespace["EXPECTED_DOCS_CANDIDATE_BINDING"], os.environ.get("FMV3_DOCS_CANDIDATE_ROOT")
                try:
                    namespace["EXPECTED_DOCS_CANDIDATE_BINDING"] = binding
                    os.environ["FMV3_DOCS_CANDIDATE_ROOT"] = str(docs)
                    with self.assertRaises(VALIDATOR_GLOBALS["ValidationError"]) as raised:
                        VALIDATOR_GLOBALS["load_docs_candidate"](binding)
                    self.assertIn("duplicate JSON key", str(raised.exception))
                finally:
                    namespace["EXPECTED_DOCS_CANDIDATE_BINDING"] = previous
                    if old_root is None:
                        os.environ.pop("FMV3_DOCS_CANDIDATE_ROOT", None)
                    else:
                        os.environ["FMV3_DOCS_CANDIDATE_ROOT"] = old_root
    def test_hosted_ci_pins_and_exports_exact_docs_candidate(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn(
            "https://github.com/Project-Helianthus/helianthus-docs-ebus.git",
            workflow,
        )
        binding = PLAN_DATA["execution_authorization"]["authorization_anchor"][
            "docs_candidate_binding"
        ]
        self.assertIn(binding["commit_sha"], workflow)
        self.assertIn("FMV3_DOCS_CANDIDATE_ROOT:", workflow)
        post_merge = workflow.split("  fmv3-anchor-post-merge:", 1)[1]
        self.assertIn("ref: ${{ github.sha }}", post_merge)
        self.assertNotIn("ref: main", post_merge)
        self.assertIn(
            'test "$(git rev-parse HEAD)" = "${{ github.sha }}"',
            post_merge,
        )

    def test_pull_request_ci_jobs_receive_no_github_token(self) -> None:
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(workflow["permissions"], {})
        for job_name in ("fmv3-anchor-linux-bootstrap", "validate"):
            with self.subTest(job=job_name):
                job = workflow["jobs"][job_name]
                self.assertEqual(job["permissions"], {})
                serialized = json.dumps(job, sort_keys=True)
                self.assertNotIn("actions/checkout@", serialized)
                self.assertNotIn("github.token", serialized)
                self.assertIn("git fetch --no-tags", serialized)
                self.assertIn("git checkout --detach FETCH_HEAD", serialized)

    def test_validator_fails_closed_without_docs_candidate_root(self) -> None:
        env = os.environ.copy()
        env.pop("FMV3_DOCS_CANDIDATE_ROOT", None)
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(PLAN)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FMV3_DOCS_CANDIDATE_ROOT is mandatory", result.stderr)

    def test_validator_fails_closed_at_wrong_docs_candidate_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = self.clone_docs_candidate(temp)
            self.git(docs, "config", "user.name", "FMV3 Test")
            self.git(docs, "config", "user.email", "fmv3-test@example.invalid")
            self.git(docs, "commit", "--allow-empty", "-m", "wrong candidate head")
            env = os.environ.copy()
            env["FMV3_DOCS_CANDIDATE_ROOT"] = str(docs)
            result = self.run_validator(PLAN, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not at the exact bound commit", result.stderr)

    def test_docs_candidate_rejects_nested_untracked_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = self.clone_docs_candidate(temp)
            nested = docs / "untracked-root"
            nested.mkdir()
            env = os.environ.copy()
            env["FMV3_DOCS_CANDIDATE_ROOT"] = str(nested)
            result = self.run_validator(PLAN, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("root must equal the git toplevel", result.stderr)

    def test_docs_candidate_rejects_dirty_predecessor_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = self.clone_docs_candidate(temp)
            predecessor = docs / "docs/platform/modbus-foundation-profile-contract-v1.md"
            predecessor.write_text(
                predecessor.read_text(encoding="utf-8") + "\nunauthorized drift\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["FMV3_DOCS_CANDIDATE_ROOT"] = str(docs)
            result = self.run_validator(PLAN, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("docs candidate requires a fully clean checkout", result.stderr)

    def test_docs_candidate_rejects_wrong_remote(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = self.clone_docs_candidate(temp)
            self.git(docs, "remote", "set-url", "origin", "https://example.invalid/docs.git")
            env = os.environ.copy()
            env["FMV3_DOCS_CANDIDATE_ROOT"] = str(docs)
            result = self.run_validator(PLAN, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("origin is not the canonical", result.stderr)

    def test_docs_candidate_rejects_wrong_push_remote(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = self.clone_docs_candidate(temp)
            self.git(
                docs,
                "remote",
                "set-url",
                "--push",
                "origin",
                "https://example.invalid/docs.git",
            )
            env = os.environ.copy()
            env["FMV3_DOCS_CANDIDATE_ROOT"] = str(docs)
            result = self.run_validator(PLAN, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("origin is not the canonical", result.stderr)

    def test_predecessor_d13_substitution_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            decision = next(row for row in plan["decisions"] if row["id"] == "D13")
            decision["decision"] = "predecessor PR #89 capability and ledger semantics"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("accepted decision D13 mismatch", result.stderr)

    def test_predecessor_m2_exit_gate_substitution_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            milestone = next(row for row in plan["milestones"] if row["id"] == "M2")
            milestone["exit_gate"] = "predecessor PR #89 M2 exit gate"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("M2 exit gate mismatch", result.stderr)

    def test_current_validator_mutation_cannot_authorize(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor, _ = self.published_amendment_snapshots(
                temp,
                lambda _: None,
                lambda root: (root / "validate_plan.py").write_text(
                    (root / "validate_plan.py").read_text(encoding="utf-8")
                    + "\n# unauthorized mutation\n",
                    encoding="utf-8",
                ),
            )
            result = self.authorize(
                plan_root, anchor, "FMV3-M1-05", self.amendment_pr(anchor)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("current validator_path blob differs", result.stderr)

    def test_current_ci_workflow_mutation_cannot_authorize(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor, _ = self.published_amendment_snapshots(
                temp,
                lambda _: None,
                lambda root: (root.parent / ".github/workflows/ci.yml").write_text(
                    (root.parent / ".github/workflows/ci.yml").read_text(encoding="utf-8")
                    + "\n# unauthorized mutation\n",
                    encoding="utf-8",
                ),
            )
            result = self.authorize(
                plan_root, anchor, "FMV3-M1-05", self.amendment_pr(anchor)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("current workflow_path blob differs", result.stderr)

    def test_restoring_pr89_validator_cannot_authorize(self) -> None:
        predecessor_validator = subprocess.run(
            [
                "git", "-C", str(ROOT), "show",
                "6fd2b4a8d181f5133250a0f2f1380d057254db60:"
                "fronius-modbus-multivendor-v3-w29-26.implementing/validate_plan.py",
            ],
            check=True,
            capture_output=True,
        ).stdout
        with tempfile.TemporaryDirectory() as temp:
            plan_root, anchor, _ = self.published_amendment_snapshots(
                temp,
                lambda _: None,
                lambda root: (root / "validate_plan.py").write_bytes(
                    predecessor_validator
                ),
            )
            result = self.authorize(
                plan_root, anchor, "FMV3-M1-05", self.amendment_pr(anchor)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("current validator_path blob differs", result.stderr)

    def test_wrong_or_missing_pr_base_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            pr["base"] = {"ref": "main", "repo": pr["base"]["repo"]}
            result = self.authorize(implementing, anchor, "FMV3-M1-05", pr)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("authorization PR #91 base/head identity mismatch", result.stderr)

    def test_wrong_pr_head_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            pr["head"] = {
                **pr["head"],
                "ref": "issue/89-incorrect-predecessor",
            }
            result = self.authorize(implementing, anchor, "FMV3-M1-05", pr)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("authorization PR #91 base/head identity mismatch", result.stderr)

    def test_wrong_or_missing_merger_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor, merged_by={"login": "other"})
            result = self.authorize(implementing, anchor, "FMV3-M1-05", pr)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("merger is not the authorized issuer", result.stderr)

    def test_missing_external_review_attestation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor),
                {
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1": []
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly one external review attestation tag", result.stderr)

    def test_duplicate_external_review_attestation_tag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            comment = self.review_attestation_comment(pr)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1": [
                        comment,
                        comment,
                    ]
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly one external review attestation tag", result.stderr)

    def test_edited_external_review_attestation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1": [
                        self.review_attestation_comment(
                            pr,
                            updated_at="2026-07-30T10:11:00Z",
                        )
                    ]
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be unedited", result.stderr)

    def test_external_review_attestation_requires_trusted_association(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1": [
                        self.review_attestation_comment(
                            pr,
                            author_association="CONTRIBUTOR",
                        )
                    ]
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("association is not trusted", result.stderr)

    def test_external_review_attestation_timing_is_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1": [
                        self.review_attestation_comment(
                            pr,
                            created_at=PR_MERGED_AT,
                            updated_at=PR_MERGED_AT,
                        )
                    ]
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("aggregate must follow the exact canonical-main push run after merge", result.stderr)

    def test_attestation_requires_two_fresh_openai_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1": [
                        self.review_attestation_comment(
                            pr,
                            attestation={"reviewer_run_ids": REVIEW_RUN_IDS[:1]},
                        )
                    ]
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("review attestation schema keys mismatch", result.stderr)

    def test_attestation_must_bind_exact_live_head_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1": [
                        self.review_attestation_comment(
                            pr,
                            attestation={"head_tree_sha": "9" * 40},
                        )
                    ]
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "exact reviewed head/tree, verdict, and owner-attested process",
                result.stderr,
            )

    def test_workflow_run_must_prove_exact_canonical_main_merge_sha(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            workflow = self.workflow_run(pr)
            workflow["head_sha"] = "9" * 40
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {f"repos/{PLAN_REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}": workflow},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("workflow run does not prove the exact canonical-main merge SHA", result.stderr)

    def test_native_reviews_must_be_submitted_for_exact_live_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            review = self.review_evidence(pr, 0)
            review["commit_id"] = "9" * 40
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {f"repos/{PLAN_REPOSITORY}/pulls/91/reviews?per_page=100": [self.official_review(pr), review, self.review_evidence(pr, 1)]},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("native review is not submitted, trusted, and bound to the exact head", result.stderr)

    def test_pr91_rejects_malicious_official_codex_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            pr = self.amendment_pr(anchor)
            official = self.official_review(pr)
            official["body"] = CODEX_REVIEW_BODY(pr["head"]["sha"]) + "\n\nP2: hidden finding"
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                pr,
                {f"repos/{PLAN_REPOSITORY}/pulls/91/reviews?per_page=100": [
                    official,
                    self.review_evidence(pr, 0),
                    self.review_evidence(pr, 1),
                ]},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("official Codex review is not an exact-head", result.stderr)

    def test_squash_merge_requires_exact_original_base_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                self.amendment_pr(anchor),
                {
                    f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{anchor}": {
                        "tree": {"sha": PR_TREE_SHA},
                        "parents": [{"sha": "8" * 40}, {"sha": "7" * 40}],
                    }
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PR #91 squash merge must have exactly", result.stderr)

    def test_squash_merge_tree_must_equal_reviewed_head_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            responses = {
                "repos/Project-Helianthus/helianthus-execution-plans/pulls/91":
                    self.amendment_pr(anchor),
                f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{PR_HEAD_SHA}":
                    {"tree": {"sha": PR_TREE_SHA}},
                f"repos/Project-Helianthus/helianthus-execution-plans/git/commits/{anchor}":
                    {"tree": {"sha": "3" * 40}},
            }
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-05",
                github_responses=responses,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not bind the exact reviewed head/tree", result.stderr)

    def test_non_authorization_canonical_semantic_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def mutate(root: Path) -> None:
                canonical = root / "00-canonical.md"
                text = canonical.read_text(encoding="utf-8")
                canonical.write_text(
                    text.replace(
                        "Every coalesced dependent receives an\nindependent capability.",
                        "Every coalesced dependent may share a capability.",
                        1,
                    ),
                    encoding="utf-8",
                )
                self.rewrite_canonical_hashes(root)

            plan_root, anchor, _ = self.published_amendment_snapshots(
                temp, lambda _: None, mutate
            )
            result = self.authorize(
                plan_root, anchor, "FMV3-M1-05", self.amendment_pr(anchor)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "current main amendment surface digest differs from merged PR #91 anchor",
                result.stderr,
            )

    def test_pr89_cannot_remain_current_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copied = self.copied_plan(temp)
            plan_path = copied / "plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["execution_authorization"]["authorization_anchor"][
                "authorization_pr"
            ] = "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/89"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            result = self.run_validator(copied)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("current authorization PR mismatch", result.stderr)

    def test_scope_and_hard_stop_reconciliation_remain_exact(self) -> None:
        authorization = PLAN_DATA["execution_authorization"]
        anchor = authorization["authorization_anchor"]
        self.assertEqual(len(PLAN_DATA["issues"]), 46)
        self.assertEqual(len(PLAN_DATA["milestones"]), 9)
        self.assertEqual(anchor["stop_before_issue"], "FMV3-M4-01")
        self.assertFalse(anchor["gateway_work_authorized"])
        self.assertEqual(anchor["authorization_pr"], AMENDMENT_PR_URL)
        self.assertEqual(
            anchor["predecessor_authorization_pr"],
            "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/89",
        )
        self.assertEqual(anchor["predecessor_role"], "provenance_only")


if __name__ == "__main__":
    unittest.main()
