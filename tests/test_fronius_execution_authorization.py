from __future__ import annotations

import base64
from collections.abc import Callable
import hashlib
import json
import os
import re
import runpy
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
PR_ATTESTED_AT = "2026-07-30T10:10:00Z"
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
PLAN_REPOSITORY = "Project-Helianthus/helianthus-execution-plans"
PLAN_CANONICAL_REMOTE = (
    "https://github.com/Project-Helianthus/helianthus-execution-plans.git"
)
TEST_PUBLISH_REMOTE = "test-publish"


def m1_06_mutation_patch(case_id: str) -> str:
    return f"@@ -1 +1 @@\n-{case_id}:baseline\n+{case_id}:mutated\n"


def m1_06_mutation_patch_digest(case_id: str) -> str:
    projection = [{
        "filename": "runtime/capability.go",
        "status": "modified",
        "patch": m1_06_mutation_patch(case_id),
    }]
    return hashlib.sha256(json.dumps(
        projection, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")).hexdigest()


class FroniusExecutionAuthorizationTests(unittest.TestCase):
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
            ["git", "clone", "--shared", str(source), str(candidate)],
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
        base_sha = "e" * 40
        main_sha = "f" * 40
        return {
            f"repos/{repository}/issues/{issue_number}": {
                "number": issue_number, "repository_url": f"https://api.github.com/repos/{repository}",
                "state": "closed", "closed_at": "2026-08-01T12:00:00Z",
                "title": issue_title, "body": issue_body,
            },
            f"repos/{repository}/pulls/{pr_number}": {
                "number": pr_number, "title": pull_request_title, "state": "closed", "merged": True,
                "merged_at": "2026-08-01T12:00:00Z", "merge_commit_sha": merge_sha,
                "body": f"Closes #{issue_number}.",
                "base": {"sha": base_sha, "ref": "main", "repo": {"full_name": repository}},
                "head": {"sha": head_sha, "repo": {"full_name": repository}},
            },
            f"repos/{repository}/git/commits/{head_sha}": {"sha": head_sha, "tree": {"sha": binding["head_tree_sha"]}},
            f"repos/{repository}/git/commits/{merge_sha}": {"sha": merge_sha, "tree": {"sha": binding["head_tree_sha"]}, "parents": [{"sha": base_sha}]},
            f"repos/{repository}/git/ref/heads/main": {"object": {"type": "commit", "sha": main_sha}},
            f"repos/{repository}/compare/{merge_sha}...{main_sha}": {"status": "ahead", "merge_base_commit": {"sha": merge_sha}},
            f"repos/{repository}/issues/{issue_number}/timeline?per_page=100": [{"event": "cross-referenced", "source": {"issue": {"number": pr_number, "pull_request": {"url": f"https://api.github.com/repos/{repository}/pulls/{pr_number}", "merged_at": "2026-08-01T12:00:00Z"}}}}],
            f"graphql/closing-issues/{repository}/{pr_number}/FIRST": self.closing_issues_response(
                repository, issue_number
            ),
            f"repos/{repository}/commits/{head_sha}/check-runs": {"check_runs": [{
                "id": 1000 + index,
                "name": check["context"] if isinstance(check, dict) else check,
                "head_sha": head_sha,
                "status": "completed",
                "conclusion": "success",
                **({"app": {"id": check["app_id"]}}
                   if isinstance(check, dict) else {}),
            } for index, check in enumerate(binding["required_checks"])]},
        }

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
                "--plan-head-sha",
                anchor_sha,
                "--authorization-contract-sha256",
                contract_digest,
                "--materialized-anchor-validator",
            ]
            if evidence_value:
                command.extend(["--authorization-evidence", evidence_value])
            gh = Path(fake_bin) / "gh"
            gh.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "if len(sys.argv) < 3 or sys.argv[1] != 'api':\n"
                "    raise SystemExit(2)\n"
                "responses = json.loads(os.environ['FAKE_GH_RESPONSES'])\n"
                "if sys.argv[2] == 'graphql':\n"
                "    fields = {}\n"
                "    index = 3\n"
                "    while index < len(sys.argv):\n"
                "        if sys.argv[index] in {'-f', '-F'} and index + 1 < len(sys.argv):\n"
                "            key, separator, value = sys.argv[index + 1].partition('=')\n"
                "            if separator:\n"
                "                fields[key] = value\n"
                "            index += 2\n"
                "        else:\n"
                "            index += 1\n"
                "    repository = fields.get('owner', '') + '/' + fields.get('name', '')\n"
                "    cursor = fields.get('cursor', 'FIRST')\n"
                "    endpoint = f\"graphql/closing-issues/{repository}/{fields.get('number', '')}/{cursor}\"\n"
                "elif len(sys.argv) == 3:\n"
                "    endpoint = sys.argv[2]\n"
                "else:\n"
                "    raise SystemExit(2)\n"
                "if endpoint not in responses:\n"
                "    raise SystemExit(2)\n"
                "print(json.dumps(responses[endpoint]))\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)
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
            responses = dict(github_responses or {})
            for binding in STATIC_DEPENDENCIES.values():
                for endpoint, value in self.completion_responses(binding).items():
                    responses.setdefault(endpoint, value)
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
                if binding.get("kind") in {
                    "manual_repository_creation",
                    "docs_candidate_completion",
                }:
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
            for endpoint, value in list(responses.items()):
                if endpoint.endswith("/check-runs") and isinstance(value, dict):
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
                if endpoint.endswith("/jobs?per_page=100") and isinstance(value, dict):
                    rows = value.get("jobs")
                    if isinstance(rows, list):
                        page = {**value, "total_count": len(rows)}
                        responses.setdefault(endpoint + "&page=1", page)
                        responses.setdefault(
                            endpoint + "&page=2",
                            {"total_count": len(rows), "jobs": []},
                        )
                if endpoint.endswith("?per_page=100") and isinstance(value, list):
                    responses.setdefault(endpoint + "&page=1", value)
                    responses.setdefault(endpoint + "&page=2", [])
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
        head_sha = pr.get("head", {}).get("sha", PR_HEAD_SHA)
        return {"id": WORKFLOW_RUN_ID, "workflow_id": 244018027, "event": "pull_request", "status": "completed", "conclusion": "success", "head_sha": head_sha, "path": ".github/workflows/ci.yml", "actor": {"login": "d3vi1"}, "head_repository": {"full_name": PLAN_REPOSITORY}, "updated_at": "2026-07-30T10:01:00Z", "pull_requests": [{"number": 91, "base": {"ref": "main", "repo": {"url": "https://api.github.com/repos/Project-Helianthus/helianthus-execution-plans"}}, "head": {"sha": head_sha, "ref": "issue/90-fmv3-capability-ledger-reconcile", "repo": {"url": "https://api.github.com/repos/Project-Helianthus/helianthus-execution-plans"}}}]}

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
            "merged_at": "2026-07-31T12:00:00Z" if merged else None,
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
                "closed_at": "2026-07-31T12:00:00Z" if merged else None,
            },
            "repos/Project-Helianthus/helianthus-docs-ebus/issues/385/timeline?per_page=100": [{
                "event": "cross-referenced",
                "source": {"issue": {"number": 386, "pull_request": {
                    "url": "https://api.github.com/repos/Project-Helianthus/helianthus-docs-ebus/pulls/386",
                    "merged_at": "2026-07-31T12:00:00Z",
                }}},
            }] if merged else [],
            "graphql/closing-issues/Project-Helianthus/helianthus-docs-ebus/386/FIRST": (
                self.closing_issues_response(
                    "Project-Helianthus/helianthus-docs-ebus", 385
                ) if merged else self.closing_issues_response(
                    "Project-Helianthus/helianthus-docs-ebus", 999
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
            responses["repos/Project-Helianthus/helianthus-docs-ebus/branches/main/protection/required_status_checks"] = {"contexts": ["Modbus Trusted Revision"], "checks": [{"context": "Modbus Trusted Revision", "app_id": GITHUB_ACTIONS_APP_ID}]}
            responses[f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{binding['commit_sha']}/check-runs"] = {"check_runs": [{"id": 780, "name": "Modbus Trusted Revision", "head_sha": binding["commit_sha"], "status": "completed", "conclusion": "success", "completed_at": "2026-08-01T12:00:01Z", "app": {"id": GITHUB_ACTIONS_APP_ID}}]}
            owner_reviews = []
            for index in range(2):
                body = {"schema": "helianthus.fmv3-pr91-external-review-attestation.v1", "repository": "Project-Helianthus/helianthus-docs-ebus", "pull_request": 386, "head_sha": binding["commit_sha"], "head_tree_sha": binding["commit_tree_sha"], "verdict": "NO_FINDINGS", "attestation_kind": "owner_process_attestation", "review_process": "fresh_openai_context", "reviewer_run_reference": REVIEW_RUN_IDS[index], "output_digest_sha256": str(index + 3) * 64}
                owner_reviews.append({"id": 801 + index, "user": {"login": "d3vi1"}, "author_association": "OWNER", "state": "COMMENTED", "commit_id": binding["commit_sha"], "submitted_at": f"2026-08-01T12:00:0{2 + index}Z", "body": json.dumps(body, sort_keys=True)})
            responses["repos/Project-Helianthus/helianthus-docs-ebus/pulls/386/reviews?per_page=100"] = [{"id": 800, "user": {"login": "chatgpt-codex-connector[bot]"}, "state": "COMMENTED", "commit_id": binding["commit_sha"], "body": CODEX_REVIEW_BODY(binding["commit_sha"])}, *owner_reviews]
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
            "schema": "helianthus.fmv3-issue-authorization-evidence.v1",
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
                "green_workflow_run_id": M1_06_GREEN_RUN_ID,
                "mutation_runs": [
                    {
                        "case_id": case_id,
                        "mutation_commit_sha": M1_06_MUTATION_SHAS[index],
                        "workflow_run_id": M1_06_MUTATION_RUN_IDS[index],
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
type TerminalOutcome int

func NewRuntimeAcquisition() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func (c *OpaqueRuntimeCapability) Claim() bool { return true }
func (c *OpaqueRuntimeCapability) CancelOpen() {}
func NewBoundedCapability() *OpaqueRuntimeCapability { return &OpaqueRuntimeCapability{} }
func ReserveTerminalSequence() uint64 { return 1 }
"""
        test_source = b"""package runtime

import "testing"

func TestDeliverabilityExclusions(t *testing.T) {
    if NewRuntimeAcquisition() == nil { t.Fatal("missing runtime acquisition") }
}
func TestCopiedCapabilityOneWinner(t *testing.T) {
    if !NewRuntimeAcquisition().Claim() { t.Fatal("expected one winner") }
}
func TestFreshAcquisitionNonAlias(t *testing.T) {
    if NewRuntimeAcquisition() == nil { t.Fatal("missing fresh acquisition") }
}
func TestTerminalOutcomes(t *testing.T) {
    if TerminalOutcome(0) != 0 { t.Fatal("unexpected terminal outcome") }
}
func TestCancelOpenDrainAndReclaim(t *testing.T) {
    capability := NewRuntimeAcquisition()
    capability.CancelOpen()
    if capability == nil { t.Fatal("missing cancelled capability") }
}
func TestBoundsAndOverflow(t *testing.T) {
    if NewBoundedCapability() == nil { t.Fatal("missing bounded capability") }
}
func TestTerminalSequenceExhaustion(t *testing.T) {
    if ReserveTerminalSequence() == 0 { t.Fatal("zero terminal sequence") }
}
func TestCoalescedDependentIsolation(t *testing.T) {
    if NewRuntimeAcquisition() == nil { t.Fatal("missing isolated acquisition") }
}
"""
        responses: dict[str, object] = {}
        production_sha, production_blob = self.github_blob(production_source)
        test_sha, test_blob = self.github_blob(test_source)
        responses[f"repos/{repository}/git/blobs/{production_sha}"] = production_blob
        responses[f"repos/{repository}/git/blobs/{test_sha}"] = test_blob
        production_path = "runtime/capability.go"
        test_path = "runtime/capability_conformance_test.go"
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
            "production": [{
                "path": production_path,
                "blob_sha": production_sha,
                "mode": "100644",
                "symbols": list(M1_06_PRODUCTION_SYMBOLS),
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
        issue_endpoint = f"repos/{repository}/issues/{issue_number}"
        pr_endpoint = f"repos/{repository}/pulls/{pull_request_number}"
        responses[issue_endpoint]["body"] = (
            f"{responses[issue_endpoint]['body']}\n{M1_06_ISSUE_MARKER}\n\n"
            "Implement the immutable plan-bound capability contract."
        )
        responses[issue_endpoint]["closed_at"] = "2026-08-01T12:00:10Z"
        responses[pr_endpoint]["head"]["ref"] = (
            f"issue/{issue_number}-opaque-runtime-acquisition"
        )
        responses[pr_endpoint]["merged_at"] = "2026-08-01T12:00:10Z"
        timeline_endpoint = f"repos/{repository}/issues/{issue_number}/timeline?per_page=100"
        responses[timeline_endpoint][0]["source"]["issue"]["pull_request"]["merged_at"] = (
            "2026-08-01T12:00:10Z"
        )
        responses[f"repos/{repository}/branches/main/protection/required_status_checks"] = {
            "contexts": [check["context"] for check in dependency["required_checks"]],
            "checks": list(dependency["required_checks"]),
        }
        responses[f"repos/{repository}/git/commits/{M1_06_RED_SHA}"] = {
            "sha": M1_06_RED_SHA,
            "tree": {"sha": "8" * 40},
            "parents": [{"sha": "e" * 40}],
        }
        responses[f"repos/{repository}/commits/{M1_06_RED_SHA}?per_page=65&page=1"] = {
            "sha": M1_06_RED_SHA,
            "files": [{
                "filename": "runtime/capability_lifecycle_test.go",
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
            "event": "pull_request",
            "status": "completed",
            "conclusion": "failure",
            "head_sha": M1_06_RED_SHA,
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
        responses[f"repos/{repository}/commits/{M1_06_RED_SHA}/check-runs"] = {
            "check_runs": [{
                "id": 910,
                "name": "checks",
                "head_sha": M1_06_RED_SHA,
                "status": "completed",
                "conclusion": "failure",
                "details_url": f"https://github.com/{repository}/actions/runs/{M1_06_RED_RUN_ID}",
                "app": {"id": GITHUB_ACTIONS_APP_ID},
                "pull_requests": [{
                    "number": pull_request_number,
                    "head": {"sha": M1_06_RED_SHA},
                }],
            }],
        }
        responses[f"repos/{repository}/actions/runs/{M1_06_RED_RUN_ID}/jobs?per_page=100"] = {
            "jobs": [{
                "id": 920,
                "name": "checks",
                "head_sha": M1_06_RED_SHA,
                "status": "completed",
                "conclusion": "failure",
                "steps": [
                    {"number": 1, "name": "Set up Go", "status": "completed", "conclusion": "success"},
                    {"number": 2, "name": "./scripts/ci_local.sh", "status": "completed", "conclusion": "failure"},
                ],
            }],
        }
        responses[f"repos/{repository}/commits/{dependency['head_sha']}/check-runs"] = {
            "check_runs": [{
                "id": 930 + index,
                "name": check["context"],
                "head_sha": dependency["head_sha"],
                "status": "completed",
                "conclusion": "success",
                "completed_at": f"2026-08-01T12:00:0{index + 1}Z",
                "details_url": (
                    f"https://github.com/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}"
                    if check["context"] == "checks" else
                    f"https://github.com/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}/jobs/{940 + index}"
                ),
                "app": {"id": check["app_id"]},
            } for index, check in enumerate(dependency["required_checks"])]
        }
        responses[f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}"] = {
            "id": M1_06_GREEN_RUN_ID,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
            "head_sha": dependency["head_sha"],
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
        responses[f"repos/{repository}/actions/runs/{M1_06_GREEN_RUN_ID}/jobs?per_page=100"] = {
            "jobs": [{
                "id": 950,
                "name": "checks",
                "head_sha": dependency["head_sha"],
                "status": "completed",
                "conclusion": "success",
                "steps": [
                    {"number": 1, "name": "Set up Go", "status": "completed", "conclusion": "success"},
                    {"number": 2, "name": "./scripts/ci_local.sh", "status": "completed", "conclusion": "success"},
                ],
            }],
        }
        conformance_responses, report_sha = self.m1_06_conformance_responses(
            repository, str(dependency["head_tree_sha"])
        )
        responses.update(conformance_responses)
        mutation_selectors = []
        for index, (case_id, test_step_name) in enumerate(M1_06_MUTATION_CASES.items()):
            mutation_sha = M1_06_MUTATION_SHAS[index]
            mutation_run_id = M1_06_MUTATION_RUN_IDS[index]
            mutation_selectors.append({
                "case_id": case_id,
                "mutation_commit_sha": mutation_sha,
                "workflow_run_id": mutation_run_id,
            })
            responses[f"repos/{repository}/git/commits/{mutation_sha}"] = {
                "sha": mutation_sha,
                "tree": {"sha": format(index + 9, "x") * 40},
                "parents": [{"sha": dependency["head_sha"]}],
            }
            responses[f"repos/{repository}/commits/{mutation_sha}?per_page=65&page=1"] = {
                "sha": mutation_sha,
                "files": [{
                    "filename": "runtime/capability.go",
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
                "event": "workflow_dispatch",
                "status": "completed",
                "conclusion": "failure",
                "head_sha": mutation_sha,
                "path": ".github/workflows/ci.yml",
                "actor": {"login": "d3vi1"},
                "head_repository": {"full_name": repository},
                "updated_at": f"2026-08-01T12:00:{20 + index:02d}Z",
            }
            responses[f"repos/{repository}/commits/{mutation_sha}/check-runs"] = {
                "check_runs": [{
                    "id": 9300 + index,
                    "name": check_name,
                    "head_sha": mutation_sha,
                    "status": "completed",
                    "conclusion": "failure",
                    "details_url": f"https://github.com/{repository}/actions/runs/{mutation_run_id}",
                    "app": {"id": GITHUB_ACTIONS_APP_ID},
                }],
            }
            responses[f"repos/{repository}/actions/runs/{mutation_run_id}/jobs?per_page=100"] = {
                "jobs": [{
                    "id": 9400 + index,
                    "name": check_name,
                    "head_sha": mutation_sha,
                    "status": "completed",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Set up Go", "status": "completed", "conclusion": "success"},
                        {"number": 2, "name": M1_06_MUTATION_COMPILE_STEP_NAME, "status": "completed", "conclusion": "success"},
                        {"number": 3, "name": test_step_name, "status": "completed", "conclusion": "failure"},
                    ],
                }],
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
                "submitted_at": f"2026-08-01T12:00:{30 + index:02d}Z",
                "body": json.dumps(body, sort_keys=True),
            })
        responses[f"repos/{repository}/pulls/{pull_request_number}/reviews?per_page=100"] = [{
            "id": M1_06_OFFICIAL_REVIEW_ID,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "state": "COMMENTED",
            "commit_id": dependency["head_sha"],
            "submitted_at": "2026-08-01T12:00:29Z",
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
            policy = "repos/Project-Helianthus/helianthus-docs-ebus/branches/main/protection/required_status_checks"
            responses[policy] = {
                "contexts": ["Modbus Trusted Revision"],
                "checks": [{"context": "Modbus Trusted Revision", "app_id": 1234}],
            }
            checks = responses[f"repos/Project-Helianthus/helianthus-docs-ebus/commits/{binding['commit_sha']}/check-runs"]
            checks["check_runs"][0]["app"] = {"id": 9999}
            result = self.authorize(implementing, anchor, "FMV3-M1-06", github_responses=responses)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Modbus Trusted Revision@1234", result.stderr)

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
            ]["closed_at"] = "2026-07-31T12:00:01Z"
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
            self.assertIn("fail-closed execution allowlist", result.stdout)

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
                    "filename": "runtime/capability.go",
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
                responses[endpoint]["check_runs"][0]["conclusion"] = "success"
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("failing exact-SHA exact-PR check", result.stderr)

    def test_m2_01_rejects_red_ci_local_job_not_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_RED_RUN_ID}/jobs?per_page=100"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["jobs"][0]["steps"][1]["conclusion"] = "success"
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("run ci_local after successful setup", result.stderr)

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

    def test_m2_01_rejects_green_ci_local_step_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/actions/runs/{M1_06_GREEN_RUN_ID}/jobs?per_page=100"
            def mutate(responses: dict[str, object]) -> None:
                responses[endpoint]["jobs"][0]["steps"][1]["conclusion"] = "failure"
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("run ci_local after successful setup", result.stderr)

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
                    if item["path"] != "runtime/capability_conformance_test.go"
                ]
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conformance case", result.stderr)

    def test_m2_01_rejects_fake_artifact_blob_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            endpoint = f"repos/Project-Helianthus/helianthus-modbus/git/trees/{'d' * 40}?recursive=1"
            def mutate(responses: dict[str, object]) -> None:
                artifact = next(
                    item for item in responses[endpoint]["tree"]
                    if item["path"] == "runtime/capability.go"
                )
                artifact["sha"] = "7" * 40
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("production source is missing or differs", result.stderr)

    def test_m2_01_rejects_semantic_no_op_conformance_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            no_op = b'''package runtime\n\nimport "testing"\n\n'''
            for _, (function_name, _) in M1_06_CASES.items():
                no_op += f"func {function_name}(t *testing.T) {{}}\n".encode()
            def mutate(responses: dict[str, object]) -> None:
                self.rewrite_m1_06_report(
                    responses,
                    replace_path="runtime/capability_conformance_test.go",
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
                lambda responses: responses[endpoint]["jobs"][0]["steps"][2].update(
                    {"name": "go test ./..."}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("did not compile before failing its exact mapped test", result.stderr)

    def test_m2_01_rejects_mutation_compile_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_id = M1_06_MUTATION_RUN_IDS[0]
            endpoint = (
                "repos/Project-Helianthus/helianthus-modbus/actions/runs/"
                f"{run_id}/jobs?per_page=100"
            )
            result = self.authorize_m2_01_producer_case(
                temp,
                lambda responses: responses[endpoint]["jobs"][0]["steps"][1].update(
                    {"conclusion": "failure"}
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("did not compile before failing its exact mapped test", result.stderr)

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
                    replace_path="runtime/capability.go",
                    replacement=source,
                )
            result = self.authorize_m2_01_producer_case(temp, mutate)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks declared contract symbol", result.stderr)

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
                responses[base + "?filter=latest&per_page=100&page=1"] = {
                    "total_count": 101,
                    "check_runs": [*rows, *padding],
                }
                duplicate = dict(rows[0])
                duplicate["id"] = 99999
                duplicate["conclusion"] = "failure"
                responses[base + "?filter=latest&per_page=100&page=2"] = {
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

    def test_dynamic_certificate_rejects_same_name_wrong_app(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            implementing, anchor = self.published_plan(temp)
            anchor = self.publish_amendment_reference(implementing)
            dependency = self.dependency_certificate(
                "FMV3-M2-01", "Project-Helianthus/helianthus-modbusreg", 50, 51, "1"
            )
            dependency["required_checks"][0]["app_id"] = 1234
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
                "FMV3-M1-06 merged after live exact issue/PR/topology, RED/GREEN "
                "ci_local jobs, canonical-template review, fixed conformance report, "
                "and canonical-main proof | FMV3-M2-01 |"
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

    def test_hosted_ci_pins_and_exports_exact_docs_candidate(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("repository: Project-Helianthus/helianthus-docs-ebus", workflow)
        binding = PLAN_DATA["execution_authorization"]["authorization_anchor"][
            "docs_candidate_binding"
        ]
        self.assertIn(f"ref: {binding['commit_sha']}", workflow)
        self.assertIn("FMV3_DOCS_CANDIDATE_ROOT:", workflow)

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
            self.assertIn("after the head commit and before mergedAt", result.stderr)

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

    def test_workflow_run_must_prove_exact_live_pr_head_before_reviews(self) -> None:
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
            self.assertIn("workflow run does not prove exact live canonical PR head", result.stderr)

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
