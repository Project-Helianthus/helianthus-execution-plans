from __future__ import annotations

import base64
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / "fronius-modbus-multivendor-v3-w29-26.implementing"
    / "validate_plan.py"
)
SPEC = importlib.util.spec_from_file_location("fronius_validate_plan", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
GATE_REL = pathlib.Path("runtime-gates/fronius-modbus-m1-admission.json")


class ModbusM1LiveGateTests(unittest.TestCase):
    def git(self, repo: pathlib.Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            text=True,
        ).strip()

    def repository(self, temp: str) -> tuple[pathlib.Path, dict[str, object], str]:
        repo = pathlib.Path(temp) / "repo"
        (repo / "scripts").mkdir(parents=True)
        (repo / "scripts/validate_modbus_docs_trust.py").write_text(
            "trusted\n",
            encoding="utf-8",
        )
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Gate Test")
        self.git(repo, "config", "user.email", "gate-test@example.invalid")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "anchor")
        anchor = self.git(repo, "rev-parse", "HEAD")

        gate = {
            "branch_protection_evidence_url": (
                "https://api.github.com/repos/Project-Helianthus/"
                "helianthus-docs-ebus/branches/main/protection/"
                "required_status_checks"
            ),
            "docs_merge_sha": "a" * 40,
            "docs_pr": 374,
            "docs_repository": "Project-Helianthus/helianthus-docs-ebus",
            "required_check": "Modbus Trusted Revision",
            "required_check_run_url": (
                "https://github.com/Project-Helianthus/"
                "helianthus-docs-ebus/actions/runs/1/job/2"
            ),
            "required_check_verified_at": "2026-07-26T22:00:00Z",
            "schema": "helianthus.execution.modbus-m1-admission",
            "state": "OPEN",
            "trust_anchor_commit": anchor,
            "trust_anchor_repository": (
                "Project-Helianthus/helianthus-execution-plans"
            ),
            "verification_head_sha": "b" * 40,
            "verification_pr": 375,
            "version": 1,
        }
        gate_path = repo / GATE_REL
        gate_path.parent.mkdir(parents=True)
        gate_path.write_text(
            json.dumps(gate, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "open gate")
        head = self.git(repo, "rev-parse", "HEAD")
        return repo, gate, head

    def api(self, gate: dict[str, object]):
        def response(endpoint: str):
            if endpoint.endswith("/pulls/374"):
                return {
                    "merged": True,
                    "merge_commit_sha": gate["docs_merge_sha"],
                }
            if endpoint.endswith(f"/pulls/{gate['verification_pr']}"):
                return {
                    "merged": True,
                    "base": {"ref": "main"},
                    "head": {"sha": gate["verification_head_sha"]},
                }
            if endpoint.endswith("/protection/required_status_checks"):
                return {
                    "contexts": [gate["required_check"]],
                    "checks": [],
                }
            if endpoint.endswith("/check-runs"):
                return {
                    "check_runs": [
                        {
                            "name": gate["required_check"],
                            "conclusion": "success",
                            "details_url": gate["required_check_run_url"],
                        }
                    ]
                }
            if "/contents/" in endpoint:
                workflow = (
                    f"ref: {gate['trust_anchor_commit']}\n"
                    "python3 anchor/scripts/validate_modbus_docs_trust.py\n"
                )
                return {
                    "encoding": "base64",
                    "content": base64.b64encode(workflow.encode()).decode(),
                }
            raise AssertionError(f"unexpected endpoint: {endpoint}")

        return response

    def test_open_gate_requires_matching_live_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, gate, head = self.repository(temp)
            with mock.patch.object(VALIDATOR, "github_api", self.api(gate)):
                VALIDATOR.require_m1_admission_open(repo, head)

    def test_open_gate_rejects_docs_merge_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, gate, head = self.repository(temp)
            api = self.api(gate)

            def mismatch(endpoint: str):
                value = api(endpoint)
                if endpoint.endswith("/pulls/374"):
                    value["merge_commit_sha"] = "f" * 40
                return value

            with mock.patch.object(VALIDATOR, "github_api", mismatch):
                with self.assertRaisesRegex(
                    VALIDATOR.ValidationError,
                    "docs PR #374 merge evidence mismatch",
                ):
                    VALIDATOR.require_m1_admission_open(repo, head)


if __name__ == "__main__":
    unittest.main()
