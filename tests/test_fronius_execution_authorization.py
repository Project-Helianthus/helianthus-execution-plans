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
PLAN_REPOSITORY = "Project-Helianthus/helianthus-execution-plans"
PLAN_CANONICAL_REMOTE = (
    "https://github.com/Project-Helianthus/helianthus-execution-plans.git"
)
TEST_PUBLISH_REMOTE = "test-publish"


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
            if authorization_evidence is not None:
                command.extend(
                    ["--authorization-evidence", str(authorization_evidence.resolve())]
                )
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
            current_head = self.git(repo, "rev-parse", "HEAD").stdout.strip()
            responses.setdefault(
                f"repos/{PLAN_REPOSITORY}/git/ref/heads/main",
                {"object": {"type": "commit", "sha": current_head}},
            )
            if amendment_pr is not None:
                responses[
                    "repos/Project-Helianthus/helianthus-execution-plans/pulls/91"
                ] = amendment_pr
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
                    "repos/Project-Helianthus/helianthus-execution-plans/issues/91/comments?per_page=100&page=1",
                    [self.review_attestation_comment(live_pr)],
                )
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
                "sha": PR_HEAD_SHA,
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
            "provider": "openai",
            "fresh_context": True,
            "reviewer_run_ids": REVIEW_RUN_IDS,
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

    def docs_pr(self, *, merged: bool, **overrides: object) -> dict[str, object]:
        binding = PLAN_DATA["execution_authorization"]["authorization_anchor"][
            "docs_candidate_binding"
        ]
        identity = binding["pull_request_identity"]
        value: dict[str, object] = {
            "number": 386,
            "html_url": binding["pr_url"],
            "state": "closed" if merged else "open",
            "merged": merged,
            "merged_at": "2026-07-31T12:00:00Z" if merged else None,
            "merge_commit_sha": "a" * 40 if merged else None,
            "author_association": "MEMBER",
            "user": {"login": "d3vi1"},
            "merged_by": {"login": "d3vi1"} if merged else None,
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
        return responses

    def write_m2_authorization_evidence(
        self,
        directory: str,
        *,
        issue_number: int = 42,
        pull_request_number: int = 43,
        merge_sha: str = "b" * 40,
    ) -> Path:
        path = Path(directory) / "m2-authorization-evidence.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "helianthus.fmv3-issue-authorization-evidence.v1",
                    "authorization_issue": "FMV3-M2-01",
                    "producer": {
                        "plan_issue": "FMV3-M1-06",
                        "repository": "Project-Helianthus/helianthus-modbus",
                        "github_issue_number": issue_number,
                        "github_pull_request_number": pull_request_number,
                        "merge_sha": merge_sha,
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return path

    def m1_06_producer_responses(
        self,
        *,
        issue_number: int = 42,
        pull_request_number: int = 43,
        merge_sha: str = "b" * 40,
        main_sha: str = "c" * 40,
    ) -> dict[str, object]:
        repository = "Project-Helianthus/helianthus-modbus"
        return {
            f"repos/{repository}/git/ref/heads/main": {
                "object": {"type": "commit", "sha": main_sha}
            },
            f"repos/{repository}/issues/{issue_number}": {
                "number": issue_number,
                "repository_url": f"https://api.github.com/repos/{repository}",
                "state": "closed",
                "closed_at": "2026-08-01T12:00:01Z",
                "title": "FMV3-M1-06: implement opaque runtime acquisition",
            },
            f"repos/{repository}/pulls/{pull_request_number}": {
                "number": pull_request_number,
                "state": "closed",
                "merged": True,
                "merged_at": "2026-08-01T12:00:00Z",
                "merge_commit_sha": merge_sha,
                "body": f"## What\nImplement M1-06.\n\nCloses #{issue_number}.",
                "base": {
                    "ref": "main",
                    "repo": {"full_name": repository},
                },
                "head": {"repo": {"full_name": repository}},
            },
            f"repos/{repository}/git/commits/{merge_sha}": {
                "sha": merge_sha,
                "tree": {"sha": "d" * 40},
                "parents": [{"sha": "e" * 40}],
            },
            f"repos/{repository}/compare/{merge_sha}...{main_sha}": {
                "status": "ahead",
                "merge_base_commit": {"sha": merge_sha},
            },
            f"repos/{repository}/issues/{issue_number}/timeline?per_page=100": [
                {
                    "event": "cross-referenced",
                    "source": {
                        "issue": {
                            "number": pull_request_number,
                            "pull_request": {
                                "url": f"https://api.github.com/repos/{repository}/pulls/{pull_request_number}"
                            },
                        }
                    },
                }
            ],
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
            responses.update(self.docs_candidate_responses(merged=False))
            result = self.authorize(
                implementing,
                anchor,
                "FMV3-M1-06",
                github_responses=responses,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires merged docs PR #386", result.stderr)

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
            self.assertIn("requires --authorization-evidence", result.stderr)

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
            self.assertIn("not on canonical helianthus-modbus main", result.stderr)

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
                "external JSON proves full merge SHA on canonical main plus exact "
                "PR/issue relationship | FMV3-M2-01 |"
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
            base_sha = PLAN_DATA["execution_authorization"]["authorization_anchor"][
                "docs_candidate_binding"
            ]["pull_request_identity"]["base_sha"]
            self.git(docs, "checkout", "--detach", base_sha)
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
            self.assertIn("base/head identity mismatch", result.stderr)

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
            self.assertIn("base/head identity mismatch", result.stderr)

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
            self.assertIn("at least two unique full OpenAI reviewer run IDs", result.stderr)

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
            self.assertIn("exact reviewed head/tree and NO_FINDINGS", result.stderr)

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
            self.assertIn("exactly the expected original base SHA as parent", result.stderr)

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
            self.assertIn("squash merge tree differs", result.stderr)

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
