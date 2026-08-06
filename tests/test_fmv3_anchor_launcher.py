from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


LAUNCHER = Path(__file__).resolve().parents[1] / "scripts" / "fmv3_anchor_validator.py"
GIT = Path("/usr/bin/git")


def load_launcher():
    spec = importlib.util.spec_from_file_location("fmv3_anchor_launcher", LAUNCHER)
    if spec is None or spec.loader is None:
        raise RuntimeError("FMV3 anchor launcher is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        [str(GIT), "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class FMV3AnchorLauncherTests(unittest.TestCase):
    def test_canonical_checkout_retains_anchor_ancestor_after_main_advances(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            run_git(source, "init", "-b", "main")
            run_git(source, "config", "user.name", "FMV3 test")
            run_git(source, "config", "user.email", "fmv3@example.invalid")
            (source / "anchor").write_text("anchor\n", encoding="ascii")
            run_git(source, "add", "anchor")
            run_git(source, "commit", "-m", "anchor")
            anchor_sha = run_git(source, "rev-parse", "HEAD")
            (source / "later").write_text("later\n", encoding="ascii")
            run_git(source, "add", "later")
            run_git(source, "commit", "-m", "later")
            main_sha = run_git(source, "rev-parse", "HEAD")
            destination = root / "checkout"
            tools = launcher.TrustedTools(
                (GIT, "1" * 64), (Path("/trusted/gh"), "2" * 64),
            )
            original_fetch = launcher.CANONICAL_FETCH_URL
            launcher.CANONICAL_FETCH_URL = str(source)
            try:
                with mock.patch.object(
                    launcher, "github_api",
                    return_value={"object": {"sha": main_sha}},
                ):
                    launcher.materialize_canonical_checkout(tools, destination)
            finally:
                launcher.CANONICAL_FETCH_URL = original_fetch
            self.assertEqual(run_git(destination, "rev-parse", "HEAD"), main_sha)
            self.assertEqual(
                run_git(destination, "merge-base", "--is-ancestor", anchor_sha, main_sha),
                "",
            )

    def test_routing_receipt_never_assumes_max_override_support(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_dir = root / "plan"
            plan_dir.mkdir()
            (plan_dir / "plan.yaml").write_text(json.dumps({
                "issues": [{
                    "id": "FMV3-M2-01",
                    "repo": "Project-Helianthus/helianthus-modbusreg",
                    "complexity": 10,
                    "gates": ["security"],
                }]
            }), encoding="utf-8")
            router = root / "model_route.py"
            router.write_text(
                "import json, sys\n"
                "print(json.dumps({'saw_max': '--max-override-supported' in sys.argv}))\n",
                encoding="ascii",
            )
            router.chmod(0o500)
            policy = root / "model-routing-policy.json"
            policy.write_text("{}\n", encoding="ascii")
            policy.chmod(0o400)
            old_router = launcher.MODEL_ROUTER_SHA256
            old_policy = launcher.MODEL_ROUTING_POLICY_SHA256
            launcher.MODEL_ROUTER_SHA256 = hashlib.sha256(router.read_bytes()).hexdigest()
            launcher.MODEL_ROUTING_POLICY_SHA256 = hashlib.sha256(policy.read_bytes()).hexdigest()
            try:
                encoded, _ = launcher.build_routing_receipt(
                    plan_dir, "FMV3-M2-01", "a" * 40,
                    router, policy, root / "route",
                )
                receipt = json.loads(base64.b64decode(encoded))
                self.assertNotIn("max_override_supported", receipt)
                self.assertFalse(receipt["route"]["saw_max"])
            finally:
                launcher.MODEL_ROUTER_SHA256 = old_router
                launcher.MODEL_ROUTING_POLICY_SHA256 = old_policy

    def test_issue_mutation_capability_allowlist_binds_endpoint_and_payload(self) -> None:
        launcher = load_launcher()
        issue = {
            "id": "FMV3-M2-02",
            "repo": "Project-Helianthus/helianthus-modbusreg",
            "what": "Implement profile contract",
        }
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "payload.json"
            cases = [
                ("selected-issue-comment", "POST", "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments", {
                    "body": "FMV3 status",
                }),
                ("selected-issue-labels", "POST", "repos/Project-Helianthus/helianthus-modbusreg/issues/50/labels", {
                    "labels": ["in-progress"],
                }),
                ("issue-pull-create", "POST", "repos/Project-Helianthus/helianthus-modbusreg/pulls", {
                    "title": "FMV3-M2-02: Implement profile contract",
                    "base": "main", "head": "issue/50-profile-contract",
                    "body": "Closes #50",
                }),
            ]
            for capability, method, endpoint, value in cases:
                with self.subTest(capability=capability):
                    input_path = None
                    if value is not None:
                        payload.write_text(json.dumps(value), encoding="utf-8")
                        input_path = payload
                    launcher.require_mutation_capability(
                        issue, 50, capability, method, endpoint, input_path,
                    )
            payload.write_text(json.dumps({
                "title": "Unrelated", "base": "main",
                "head": "issue/999-unrelated", "body": "Closes #999",
            }), encoding="utf-8")
            with self.assertRaisesRegex(
                launcher.LauncherError, "outside the selected issue capability"
            ):
                launcher.require_mutation_capability(
                    issue, 50, "issue-pull-create", "POST",
                    "repos/Project-Helianthus/helianthus-modbusreg/pulls", payload,
                )
            payload.write_text(json.dumps({
                "title": "Unrelated", "base": "main",
                "head": "issue/50-profile-contract", "body": "Closes #50",
            }), encoding="utf-8")
            with self.assertRaisesRegex(
                launcher.LauncherError, "outside the selected issue capability"
            ):
                launcher.require_mutation_capability(
                    issue, 50, "issue-pull-create", "POST",
                    "repos/Project-Helianthus/helianthus-modbusreg/pulls", payload,
                )
            payload.write_text(json.dumps({
                "title": "FMV3-M2-02: Implement profile contract", "base": "main",
                "head": "issue/50-profile-contract",
                "body": "Closes #50\n\nCloses #999",
            }), encoding="utf-8")
            with self.assertRaisesRegex(
                launcher.LauncherError, "outside the selected issue capability"
            ):
                launcher.require_mutation_capability(
                    issue, 50, "issue-pull-create", "POST",
                    "repos/Project-Helianthus/helianthus-modbusreg/pulls", payload,
                )
            with self.assertRaisesRegex(
                launcher.LauncherError, "outside the selected issue capability"
            ):
                launcher.require_mutation_capability(
                    issue, 50, "issue-workflow-dispatch", "POST",
                    "repos/Project-Helianthus/helianthus-modbusreg/actions/workflows/ci.yml/dispatches",
                    payload,
                )
            payload.write_text(json.dumps({
                "title": "FMV3-M2-02: Implement profile contract", "base": "main",
                "head": "issue/50-profile-contract", "body": "Closes #50",
                "head_repo": "attacker/fork",
            }), encoding="utf-8")
            with self.assertRaisesRegex(
                launcher.LauncherError, "outside the selected issue capability"
            ):
                launcher.require_mutation_capability(
                    issue, 50, "issue-pull-create", "POST",
                    "repos/Project-Helianthus/helianthus-modbusreg/pulls", payload,
                )
            with self.assertRaisesRegex(
                launcher.LauncherError, "outside the selected issue capability"
            ):
                launcher.require_mutation_capability(
                    issue, 50, "issue-branch-create", "POST",
                    "repos/Project-Helianthus/helianthus-modbusreg/git/refs", payload,
                )
            payload.write_text(
                '{"title":"x","head":"issue/50-x","base":"dev",'
                '"base":"main","body":"Fixes #50"}', encoding="utf-8",
            )
            with self.assertRaisesRegex(
                launcher.LauncherError, "duplicate JSON key 'base'"
            ):
                launcher.require_mutation_capability(
                    issue, 50, "issue-pull-create", "POST",
                    "repos/Project-Helianthus/helianthus-modbusreg/pulls", payload,
                )

    def test_materialized_validator_uses_fresh_one_shot_directory_per_invocation(self) -> None:
        launcher = load_launcher()
        validator = (
            "import os\n"
            "from pathlib import Path\n"
            f"prefix = {launcher.MATERIALIZATION_ENV_PREFIX!r}\n"
            "Path(os.environ[prefix + 'TOKEN_FILE']).unlink()\n"
            "Path(os.environ[prefix + 'CLAIM_OWNER_SECRET_FILE']).unlink()\n"
        ).encode("ascii")
        digest = hashlib.sha256(validator).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            root.chmod(0o700)
            for _ in range(2):
                self.assertEqual(launcher.execute_materialized_validator(
                    validator, digest, [],
                    (Path("/trusted/git"), "1" * 64),
                    (Path("/trusted/gh"), "2" * 64),
                    root, "ab" * 32,
                ), 0)
            invocations = list(root.glob("validator-*"))
            self.assertEqual(len(invocations), 2)
            self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o700
                                for path in invocations))

    def test_real_materialized_validator_fences_real_shim_mutation_pre_and_post(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            root.chmod(0o700)
            events = root / "events.json"
            state = root / "claim-state"
            events.write_text("[]", encoding="ascii")
            state.write_text("HELD\n", encoding="ascii")
            git_shim = root / "git-shim"
            gh_shim = root / "gh-shim"
            git_shim.write_text(
                f"#!{sys.executable}\nimport sys\n"
                "assert sys.argv[1:] == ['--version']\nprint('git version fixture')\n",
                encoding="ascii",
            )
            gh_shim.write_text(
                f"#!{sys.executable}\nimport json\nfrom pathlib import Path\nimport sys\n"
                f"events = Path({str(events)!r})\n"
                "if sys.argv[1:] == ['--version']:\n"
                "    print('gh version fixture')\n"
                "else:\n"
                "    assert sys.argv[1:7] == ['api', '--hostname', 'github.com', "
                "'--method', 'POST', 'repos/Project-Helianthus/helianthus-modbusreg/"
                "issues/50/comments']\n"
                "    rows = json.loads(events.read_text())\n"
                "    rows.append('mutation')\n"
                "    events.write_text(json.dumps(rows))\n"
                "    print('{\"id\":1}')\n",
                encoding="ascii",
            )
            git_shim.chmod(0o500)
            gh_shim.chmod(0o500)
            validator = (
                "import hashlib\nimport json\nimport os\nfrom pathlib import Path\n"
                "import subprocess\n"
                f"events = Path({str(events)!r})\nstate = Path({str(state)!r})\n"
                f"prefix = {launcher.MATERIALIZATION_ENV_PREFIX!r}\n"
                "assert state.read_text() == 'HELD\\n'\n"
                "for kind in ('GIT', 'GH'):\n"
                "    path = Path(os.environ[prefix + kind])\n"
                "    assert hashlib.sha256(path.read_bytes()).hexdigest() == "
                "os.environ[prefix + kind + '_SHA256']\n"
                "    subprocess.run([str(path), '--version'], check=True, "
                "capture_output=True, text=True)\n"
                "rows = json.loads(events.read_text())\nrows.append('verify')\n"
                "events.write_text(json.dumps(rows))\n"
                "Path(os.environ[prefix + 'TOKEN_FILE']).unlink()\n"
                "Path(os.environ[prefix + 'CLAIM_OWNER_SECRET_FILE']).unlink()\n"
            ).encode("ascii")
            digest = hashlib.sha256(validator).hexdigest()
            tools = launcher.TrustedTools(
                (git_shim, hashlib.sha256(git_shim.read_bytes()).hexdigest()),
                (gh_shim, hashlib.sha256(gh_shim.read_bytes()).hexdigest()),
            )
            arguments: list[str] = []
            self.assertEqual(launcher.execute_materialized_validator(
                validator, digest, arguments, tools.git, tools.gh,
                root, "ab" * 32,
            ), 0)
            command = [
                str(gh_shim), "api", "--hostname", "github.com", "--method", "POST",
                "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            ]
            self.assertEqual(launcher.execute_fenced_github_operation(
                command, {}, validator, digest, arguments, tools, root, "ab" * 32,
                None,
            ), 0)
            self.assertEqual(json.loads(events.read_text()), [
                "verify", "mutation", "verify",
            ])
            self.assertEqual(len(list(root.glob("validator-*"))), 2)

    def test_main_materializes_private_tools_and_binds_the_anchored_validator(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repo = workspace / "canonical-plan-repo"
            sources = workspace / "fixed-sources"
            attacker_path = workspace / "hostile-path"
            audit_path = workspace / "validator-audit.json"
            responses_path = workspace / "github-responses.json"
            owner_secret_path = workspace / "claim-owner-secret"
            git_config_canary = workspace / "git-config-executed"
            repo.mkdir()
            sources.mkdir()
            attacker_path.mkdir()
            run_git(repo, "init", "-b", "main")
            run_git(repo, "config", "user.name", "FMV3 launcher test")
            run_git(repo, "config", "user.email", "fmv3@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="ascii")
            run_git(repo, "add", ".")
            run_git(repo, "commit", "-m", "base")
            base_sha = run_git(repo, "rev-parse", "HEAD")

            run_git(repo, "checkout", "-b", launcher.EXPECTED_HEAD_REF)
            plan_dir = repo / Path(launcher.PLAN_PATH).parent
            plan_dir.mkdir()
            validator = '''import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

prefix = "FMV3_ANCHOR_MATERIALIZATION_"
validator_path = Path(os.environ[prefix + "VALIDATOR"])
root = validator_path.parent
token_path = Path(os.environ[prefix + "TOKEN_FILE"])
claim_secret_path = Path(os.environ[prefix + "CLAIM_OWNER_SECRET_FILE"])
assert "PYTHONPATH" not in os.environ
assert os.environ.get("PYTHONNOUSERSITE") == "1"
assert sys.flags.isolated == 1
assert sys.flags.no_user_site == 1
assert "LD_PRELOAD" not in os.environ
assert "DYLD_INSERT_LIBRARIES" not in os.environ
audit_path = Path(__AUDIT_PATH__)
prior = json.loads(audit_path.read_text()) if audit_path.exists() else {"events": []}
audit = {"validator": str(validator_path), "root_mode": stat.S_IMODE(root.stat().st_mode), "token_before": token_path.exists(), "claim_secret_before": claim_secret_path.exists(), "events": prior["events"] + ["verify"]}
for kind, expected in (("GIT", "git version"), ("GH", "trusted-gh")):
    path = Path(os.environ[prefix + kind])
    digest = os.environ[prefix + kind + "_SHA256"]
    assert path.parent == root.parent / "tools"
    assert stat.S_IMODE(path.stat().st_mode) == 0o500
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    output = subprocess.check_output([str(path), "--version"], text=True).strip()
    assert output.startswith(expected)
    audit[kind.lower()] = {"path": str(path), "digest": digest, "mode": stat.S_IMODE(path.stat().st_mode), "output": output}
token_path.unlink()
claim_secret_path.unlink()
audit["token_consumed"] = not token_path.exists()
audit["claim_secret_consumed"] = not claim_secret_path.exists()
audit_path.write_text(json.dumps(audit), encoding="utf-8")
'''.replace("__AUDIT_PATH__", repr(str(audit_path))).encode("utf-8")
            validator_path = repo / launcher.VALIDATOR_PATH
            validator_path.write_bytes(validator)
            plan = {
                "issues": [{
                    "id": "FMV3-M1-00",
                    "repo": "Project-Helianthus/helianthus-docs-ebus",
                    "what": "Publish the M1 contract documentation",
                    "complexity": 8,
                    "gates": ["doc_gate", "protocol_interop"],
                }],
                "execution_authorization": {
                    "authorization_anchor": {
                        "plan_path": launcher.PLAN_PATH,
                        "tooling_binding": {
                            "authorization_execution": "materialized_from_pr91_anchor",
                            "validator_path": launcher.VALIDATOR_PATH,
                            "validator_sha256": hashlib.sha256(validator).hexdigest(),
                        },
                    }
                }
            }
            (repo / launcher.PLAN_PATH).write_text(
                json.dumps(plan), encoding="utf-8"
            )
            run_git(repo, "add", ".")
            run_git(repo, "commit", "-m", "fixture PR head")
            head_sha = run_git(repo, "rev-parse", "HEAD")
            head_tree = run_git(repo, "rev-parse", "HEAD^{tree}")
            run_git(repo, "checkout", "main")
            run_git(repo, "merge", "--squash", launcher.EXPECTED_HEAD_REF)
            run_git(repo, "commit", "-m", "fixture squash merge")
            merge_sha = run_git(repo, "rev-parse", "HEAD")
            self.assertEqual(head_tree, run_git(repo, "rev-parse", "HEAD^{tree}"))
            self.assertEqual(base_sha, run_git(repo, "rev-parse", "HEAD^"))
            canonical_source = workspace / "canonical.git"
            subprocess.run(
                [str(GIT), "clone", "--bare", str(repo), str(canonical_source)],
                check=True, capture_output=True, text=True,
            )
            fsmonitor = workspace / "hostile-fsmonitor"
            fsmonitor.write_text(
                f"#!/bin/sh\nprintf executed > {git_config_canary}\n",
                encoding="ascii",
            )
            fsmonitor.chmod(0o700)
            run_git(repo, "config", "core.fsmonitor", str(fsmonitor))
            canonical_remote = next(iter(launcher.CANONICAL_REMOTES))
            run_git(repo, "remote", "add", "origin", canonical_remote)
            run_git(repo, "remote", "set-url", "--push", "origin", canonical_remote)

            gh_source = sources / "gh"
            gh_source.write_text(
                f"#!{sys.executable}\n"
                "import json\n"
                "import os\n"
                "from pathlib import Path\n"
                "import sys\n"
                "args = sys.argv[1:]\n"
                "assert 'PYTHONPATH' not in os.environ\n"
                "assert 'LD_PRELOAD' not in os.environ\n"
                "assert 'DYLD_INSERT_LIBRARIES' not in os.environ\n"
                "if args == ['--version']:\n"
                "    print('trusted-gh fixture')\n"
                "    raise SystemExit(0)\n"
                "if args[:3] != ['api', '--hostname', 'github.com']:\n"
                "    raise SystemExit(2)\n"
                "if '--method' in args:\n"
                "    method_index = args.index('--method')\n"
                "    assert args[method_index + 1] == 'POST'\n"
                "    endpoint = args[method_index + 2]\n"
                "    assert endpoint == 'repos/Project-Helianthus/helianthus-docs-ebus/issues/373/comments'\n"
                f"    audit_path = Path({str(audit_path)!r})\n"
                "    audit = json.loads(audit_path.read_text())\n"
                "    audit['events'].append('mutation')\n"
                "    audit_path.write_text(json.dumps(audit))\n"
                "    print('{\"id\":1}')\n"
                "    raise SystemExit(0)\n"
                "endpoint = args[3]\n"
                f"responses = json.loads(Path({str(responses_path)!r}).read_text())\n"
                "if endpoint.endswith('/pulls/91'):\n"
                f"    source = Path({str(gh_source)!r})\n"
                "    source.write_text('#!/bin/sh\\nexit 97\\n', encoding='ascii')\n"
                "    source.chmod(0o700)\n"
                "print(json.dumps(responses[endpoint]))\n",
                encoding="utf-8",
            )
            gh_source.chmod(0o700)
            for name in ("git", "gh"):
                attacker = attacker_path / name
                attacker.write_text("#!/bin/sh\nexit 97\n", encoding="ascii")
                attacker.chmod(0o500)
            responses = {
                f"repos/{launcher.PLAN_REPOSITORY}/git/ref/heads/main": {
                    "object": {"type": "commit", "sha": merge_sha}
                },
                f"repos/{launcher.PLAN_REPOSITORY}/pulls/{launcher.AMENDMENT_PR_NUMBER}": {
                    "number": launcher.AMENDMENT_PR_NUMBER,
                    "html_url": launcher.AMENDMENT_PR_URL,
                    "state": "closed",
                    "merged": True,
                    "merge_commit_sha": merge_sha,
                    "base": {"sha": base_sha, "ref": "main", "repo": {"full_name": launcher.PLAN_REPOSITORY}},
                    "head": {"sha": head_sha, "ref": launcher.EXPECTED_HEAD_REF, "repo": {"full_name": launcher.PLAN_REPOSITORY}},
                },
                f"repos/{launcher.PLAN_REPOSITORY}/git/commits/{head_sha}": {"tree": {"sha": head_tree}},
                f"repos/{launcher.PLAN_REPOSITORY}/git/commits/{merge_sha}": {"tree": {"sha": head_tree}, "parents": [{"sha": base_sha}]},
                f"repos/{launcher.PLAN_REPOSITORY}/compare/{merge_sha}...{merge_sha}": {"status": "identical", "merge_base_commit": {"sha": merge_sha}},
            }
            responses_path.write_text(json.dumps(responses), encoding="utf-8")
            owner_secret_path.write_text("ab" * 32, encoding="ascii")
            owner_secret_path.chmod(0o400)
            mutation_input = workspace / "mutation.json"
            mutation_input.write_text(
                json.dumps({"body": "FMV3 integration status"}), encoding="utf-8"
            )
            mutation_input.chmod(0o400)
            router_source = sources / "model_route.py"
            router_source.write_text(
                "import json\nprint(json.dumps({'primary_profile':'docs_architecture'}))\n",
                encoding="ascii",
            )
            router_source.chmod(0o500)
            policy_source = sources / "model-routing-policy.json"
            policy_source.write_text("{}\n", encoding="ascii")
            policy_source.chmod(0o400)

            original_base = launcher.EXPECTED_BASE_SHA
            original_fetch_url = launcher.CANONICAL_FETCH_URL
            original_canonical_remotes = launcher.CANONICAL_REMOTES
            original_gh_sources = launcher.GH_SOURCE_CANDIDATES
            original_digests = launcher.TRUSTED_EXECUTABLE_SHA256
            original_router_digest = launcher.MODEL_ROUTER_SHA256
            original_policy_digest = launcher.MODEL_ROUTING_POLICY_SHA256
            original_argv = sys.argv
            original_environment = os.environ.copy()
            launcher.EXPECTED_BASE_SHA = base_sha
            launcher.CANONICAL_FETCH_URL = str(canonical_source)
            launcher.CANONICAL_REMOTES = {str(canonical_source)}
            launcher.GH_SOURCE_CANDIDATES = (gh_source,)
            launcher.TRUSTED_EXECUTABLE_SHA256 = {
                "Git": {
                    hashlib.sha256(candidate.resolve().read_bytes()).hexdigest()
                    for candidate in launcher.GIT_SOURCE_CANDIDATES if candidate.exists()
                },
                "GitHub CLI": {hashlib.sha256(gh_source.read_bytes()).hexdigest()},
            }
            launcher.MODEL_ROUTER_SHA256 = hashlib.sha256(
                router_source.read_bytes()
            ).hexdigest()
            launcher.MODEL_ROUTING_POLICY_SHA256 = hashlib.sha256(
                policy_source.read_bytes()
            ).hexdigest()
            os.environ.update({
                "PATH": str(attacker_path),
                "PYTHONPATH": str(attacker_path),
                "LD_PRELOAD": str(attacker_path / "loader.so"),
                "DYLD_INSERT_LIBRARIES": str(attacker_path / "loader.dylib"),
            })
            sys.argv = [
                str(LAUNCHER), str(repo), str(plan_dir), "--fenced-gh-api", "FMV3-M1-00",
                "--github-issue-number", "373",
                "--claim-run-id", "019fbe20-0000-7000-8000-000000000001",
                "--claim-sha", "a" * 40,
                "--claim-owner-secret-file", str(owner_secret_path),
                "--plan-head-sha", merge_sha, "--authorization-contract-sha256", "0" * 64,
                "--mutation-capability", "selected-issue-comment",
                "--mutation-method", "POST",
                "--mutation-endpoint",
                "repos/Project-Helianthus/helianthus-docs-ebus/issues/373/comments",
                "--mutation-input", str(mutation_input),
            ]
            try:
                launcher_bytes = LAUNCHER.read_bytes()
                launcher_digest = hashlib.sha256(launcher_bytes).hexdigest()
                with (
                    mock.patch.object(
                        launcher, "consume_canonical_reexec_marker",
                        return_value=launcher_digest,
                    ),
                    mock.patch.object(
                        launcher, "load_anchored_launcher",
                        return_value=(launcher_bytes, launcher_digest),
                    ),
                ):
                    self.assertEqual(launcher.main(), 0)
            finally:
                launcher.EXPECTED_BASE_SHA = original_base
                launcher.CANONICAL_FETCH_URL = original_fetch_url
                launcher.CANONICAL_REMOTES = original_canonical_remotes
                launcher.GH_SOURCE_CANDIDATES = original_gh_sources
                launcher.TRUSTED_EXECUTABLE_SHA256 = original_digests
                launcher.MODEL_ROUTER_SHA256 = original_router_digest
                launcher.MODEL_ROUTING_POLICY_SHA256 = original_policy_digest
                sys.argv = original_argv
                os.environ.clear()
                os.environ.update(original_environment)

            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(audit["root_mode"], 0o700)
            self.assertTrue(audit["token_before"])
            self.assertTrue(audit["token_consumed"])
            self.assertTrue(audit["claim_secret_before"])
            self.assertTrue(audit["claim_secret_consumed"])
            self.assertEqual(audit["events"], ["verify", "mutation", "verify"])
            for kind in ("git", "gh"):
                self.assertEqual(audit[kind]["mode"], 0o500)
                self.assertIn("/tools/", audit[kind]["path"])
                self.assertEqual(len(audit[kind]["digest"]), 64)
            self.assertIn("exit 97", gh_source.read_text(encoding="ascii"))
            self.assertFalse(git_config_canary.exists())

    def run_fenced_mutation_case(
        self,
        endpoint: str,
        verifier_results: tuple[object, ...],
        *,
        hold_process_lock_and_replace_secret: bool = False,
        capability: str = "selected-issue-comment",
        method: str = "POST",
        mutation_returncode: int = 0,
        mutation_exception: BaseException | None = None,
        interrupt_after_mutation_return: bool = False,
        replace_materialized_after_preflight: bool = False,
        issue_id: str = "FMV3-M2-02",
        repository: str = "Project-Helianthus/helianthus-modbusreg",
        issue_number: int = 50,
        mutation_payload: dict[str, object] | None = None,
    ):
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "checkout"
            plan_dir = checkout / Path(launcher.PLAN_PATH).parent
            plan_dir.mkdir(parents=True)
            (plan_dir / "plan.yaml").write_text(json.dumps({
                "issues": [{
                    "id": issue_id,
                    "repo": repository,
                    "what": "Implement profile contract",
                }]
            }), encoding="utf-8")
            secret = Path(temporary) / "owner-secret"
            secret.write_text("ab" * 32, encoding="ascii")
            secret.chmod(0o400)
            tools = launcher.TrustedTools(
                (Path("/trusted/git"), "1" * 64),
                (Path("/trusted/gh"), "2" * 64),
            )
            executed = subprocess.CompletedProcess(
                args=[], returncode=mutation_returncode,
                stdout=b'{"id":1}\n', stderr=b""
            )
            if mutation_payload is None and capability == "selected-issue-comment":
                mutation_payload = {"body": "FMV3 status"}
            mutation_input = None
            if mutation_payload is not None:
                mutation_input = Path(temporary) / "mutation.json"
                mutation_input.write_text(json.dumps(mutation_payload), encoding="utf-8")
                mutation_input.chmod(0o400)
            held_process_lock = None
            if hold_process_lock_and_replace_secret:
                held_process_lock = launcher.acquire_claim_process_lock()
                replacement = Path(temporary) / "replacement-secret"
                replacement.write_text("ab" * 32, encoding="ascii")
                replacement.chmod(0o400)
                os.replace(replacement, secret)
            original_argv = sys.argv
            sys.argv = [
                str(LAUNCHER), str(checkout), str(plan_dir),
                "--fenced-gh-api", issue_id,
                "--github-issue-number", str(issue_number),
                "--claim-run-id", "019fbe20-0000-7000-8000-000000000001",
                "--claim-sha", "a" * 40,
                "--claim-owner-secret-file", str(secret),
                "--plan-head-sha", "b" * 40,
                "--authorization-contract-sha256", "c" * 64,
                "--mutation-capability", capability,
                "--mutation-method", method,
                "--mutation-endpoint", endpoint,
            ]
            if mutation_input is not None:
                sys.argv.extend(["--mutation-input", str(mutation_input)])
            stdout = io.StringIO()
            stderr = io.StringIO()
            real_materialize = launcher.materialize_mutation_input
            materialized: dict[str, Path] = {}
            verifier_iterator = iter(verifier_results)

            def capture_materialized(source: Path | None, destination: Path) -> Path | None:
                result = real_materialize(source, destination)
                if result is not None:
                    materialized["path"] = result
                return result

            def verify(*_args, **_kwargs):
                result = next(verifier_iterator)
                if replace_materialized_after_preflight and "path" in materialized:
                    replacement = Path(temporary) / "replacement-payload.json"
                    replacement.write_text('{"body":"replaced"}', encoding="utf-8")
                    replacement.chmod(0o400)
                    os.replace(replacement, materialized["path"])
                if isinstance(result, BaseException):
                    raise result
                return result

            def execute_mutation(*_args, **_kwargs):
                if mutation_exception is not None:
                    raise mutation_exception
                if interrupt_after_mutation_return:
                    caller = sys._getframe(1)

                    def interrupt_on_next_opcode(frame, event, _arg):
                        if frame is caller and event == "opcode":
                            frame.f_trace_opcodes = False
                            frame.f_trace = None
                            sys.settrace(None)
                            raise KeyboardInterrupt()
                        return interrupt_on_next_opcode

                    caller.f_trace = interrupt_on_next_opcode
                    caller.f_trace_opcodes = True
                    sys.settrace(
                        lambda frame, _event, _arg: (
                            interrupt_on_next_opcode if frame is caller else None
                        )
                    )
                return executed
            try:
                with (
                    mock.patch.object(
                        launcher, "consume_canonical_reexec_marker",
                        return_value="f" * 64,
                    ),
                    mock.patch.object(
                        launcher, "materialize_trusted_tools", return_value=tools
                    ),
                    mock.patch.object(
                        launcher, "materialize_canonical_checkout",
                        return_value=checkout,
                    ),
                    mock.patch.object(
                        launcher, "require_canonical_checkout",
                        return_value="d" * 40,
                    ),
                    mock.patch.object(launcher, "authenticate_anchor"),
                    mock.patch.object(launcher, "git"),
                    mock.patch.object(
                        launcher, "materialize_mutation_input",
                        side_effect=capture_materialized,
                    ),
                    mock.patch.object(
                        launcher, "load_anchored_validator",
                        return_value=(b"validator", "e" * 64),
                    ),
                    mock.patch.object(
                        launcher, "load_anchored_launcher",
                        return_value=(LAUNCHER.read_bytes(), "f" * 64),
                    ),
                    mock.patch.object(
                        launcher, "execute_materialized_validator",
                        side_effect=verify,
                    ) as validate,
                    mock.patch.object(
                        launcher, "run_mutation_process", side_effect=execute_mutation
                    ) as mutate,
                    mock.patch.object(sys, "stdout", stdout),
                    mock.patch.object(sys, "stderr", stderr),
                ):
                    result = launcher.main()
            finally:
                sys.settrace(None)
                sys.argv = original_argv
                if held_process_lock is not None:
                    held_process_lock.close()
            return result, validate, mutate, stdout.getvalue(), stderr.getvalue()

    def test_fenced_github_mutation_verifies_before_and_after_exact_operation(self) -> None:
        endpoint = (
            "repos/Project-Helianthus/helianthus-modbusreg/"
            "issues/50/comments"
        )
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            endpoint, (0, 0)
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(validate.call_count, 2)
        for phase, call in zip(("preflight", "postflight"), validate.call_args_list):
            arguments = call.args[2]
            self.assertIn("--verify-claim", arguments)
            self.assertIn("a" * 40, arguments)
            self.assertEqual(
                arguments[arguments.index("--fenced-mutation-phase") + 1], phase,
            )
            self.assertEqual(
                arguments[arguments.index("--fenced-mutation-capability") + 1],
                "selected-issue-comment",
            )
            self.assertNotIn("--fenced-mutation-head", arguments)
        command = mutate.call_args.args[0]
        self.assertEqual(command[:6], [
            "/trusted/gh", "api", "--hostname", "github.com",
            "--method", "POST",
        ])
        self.assertEqual(command[6], endpoint)
        self.assertEqual(command[-2:], ["--input", "-"])
        self.assertEqual(mutate.call_args.args[2], b'{"body": "FMV3 status"}')

    def test_fenced_mutation_uses_validated_bytes_after_payload_path_replacement(self) -> None:
        endpoint = (
            "repos/Project-Helianthus/helianthus-modbusreg/"
            "issues/50/comments"
        )
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            endpoint, (0, 0), replace_materialized_after_preflight=True,
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        self.assertEqual(mutate.call_args.args[0][-2:], ["--input", "-"])
        self.assertEqual(mutate.call_args.args[2], b'{"body": "FMV3 status"}')

    def test_fenced_github_mutation_rejects_foreign_or_traversal_endpoint(self) -> None:
        for endpoint in (
            "repos/Project-Helianthus/helianthus-modbus/issues/1/comments",
            "repos/Project-Helianthus/helianthus-modbusreg/issues/999/comments",
            "repos/Project-Helianthus/helianthus-modbusreg/../helianthus-modbus/issues",
            "repos/Project-Helianthus/helianthus-modbusreg/%2e%2e/issues",
        ):
            with self.subTest(endpoint=endpoint):
                result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
                    endpoint, (0,)
                )
                self.assertEqual(result, 1)
                validate.assert_not_called()
                mutate.assert_not_called()
                self.assertIn("fenced mutation", stderr)

    def test_fenced_pull_creation_rechecks_exact_head_before_and_after(self) -> None:
        endpoint = "repos/Project-Helianthus/helianthus-modbusreg/pulls"
        payload = {
            "title": "FMV3-M2-02: Implement profile contract",
            "base": "main",
            "head": "issue/50-profile-contract",
            "body": "Closes #50",
        }
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            endpoint, (0, 0), capability="issue-pull-create",
            mutation_payload=payload,
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(validate.call_count, 2)
        for phase, call in zip(("preflight", "postflight"), validate.call_args_list):
            arguments = call.args[2]
            self.assertEqual(
                arguments[arguments.index("--fenced-mutation-phase") + 1], phase,
            )
            self.assertEqual(
                arguments[arguments.index("--fenced-mutation-capability") + 1],
                "issue-pull-create",
            )
            self.assertEqual(
                arguments[arguments.index("--fenced-mutation-head") + 1],
                "issue/50-profile-contract",
            )
        mutate.assert_called_once()

    def test_fenced_public_repository_creation_is_exact_and_issue_bound(self) -> None:
        endpoint = "orgs/Project-Helianthus/repos"
        payload = {
            "name": "helianthus-modbus", "private": False,
            "visibility": "public", "auto_init": False,
            "has_issues": True, "has_projects": False, "has_wiki": False,
            "has_downloads": False, "has_discussions": False,
            "is_template": False,
        }
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            endpoint, (0, 0), capability="create-public-repository",
            issue_id="FMV3-M0-01", repository="Project-Helianthus/.github",
            issue_number=90, mutation_payload=payload,
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        payload["name"] = "unrelated-repository"
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            endpoint, (0,), capability="create-public-repository",
            issue_id="FMV3-M0-01", repository="Project-Helianthus/.github",
            issue_number=90, mutation_payload=payload,
        )
        self.assertEqual(result, 1)
        validate.assert_not_called()
        mutate.assert_not_called()
        self.assertIn("empty-public allowlist", stderr)
        payload["name"] = "helianthus-modbus"
        payload["team_id"] = 123456
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            endpoint, (0,), capability="create-public-repository",
            issue_id="FMV3-M0-01", repository="Project-Helianthus/.github",
            issue_number=90, mutation_payload=payload,
        )
        self.assertEqual(result, 1)
        validate.assert_not_called()
        mutate.assert_not_called()
        self.assertIn("empty-public allowlist", stderr)

    def test_fenced_mutation_stable_lock_survives_atomic_secret_replacement(self) -> None:
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            (),
            hold_process_lock_and_replace_secret=True,
        )
        self.assertEqual(result, 1)
        validate.assert_not_called()
        mutate.assert_not_called()
        self.assertIn("stable process lock", stderr)

    def test_fenced_github_mutation_failed_postflight_forces_stop(self) -> None:
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            (0, 1),
        )
        self.assertEqual(result, 1)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        self.assertIn("mutation may have completed", stderr)
        self.assertIn("must STOP", stderr)

    def test_fenced_github_mutation_exceptional_postflight_forces_stop(self) -> None:
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            (0, OSError("postflight unavailable")),
        )
        self.assertEqual(result, 1)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        self.assertIn("mutation may have completed", stderr)
        self.assertIn("STOP without retry", stderr)
        self.assertIn("reconciliation", stderr)

    def test_fenced_github_mutation_nonzero_result_is_ambiguous_and_forces_stop(self) -> None:
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            (0, 0), mutation_returncode=1,
        )
        self.assertEqual(result, 1)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        self.assertIn("mutation may have completed", stderr)
        self.assertIn("STOP without retry", stderr)

    def test_fenced_github_mutation_interrupt_still_runs_postflight(self) -> None:
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            (0, 0), mutation_exception=KeyboardInterrupt(),
        )
        self.assertEqual(result, 1)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        self.assertIn("postflight reconciliation completed", stderr)
        self.assertIn("STOP without retry", stderr)

    def test_failed_postflight_precedes_simultaneous_mutation_interrupt(self) -> None:
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            (0, 1), mutation_exception=KeyboardInterrupt(),
        )
        self.assertEqual(result, 1)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        self.assertIn("postflight reconciliation failed", stderr)
        self.assertIn("mutation may have completed", stderr)
        self.assertIn("must STOP", stderr)
        self.assertNotIn("reconciliation completed", stderr)

    def test_fenced_github_interrupt_after_child_return_still_runs_postflight(self) -> None:
        result, validate, mutate, _, stderr = self.run_fenced_mutation_case(
            "repos/Project-Helianthus/helianthus-modbusreg/issues/50/comments",
            (0, 0), interrupt_after_mutation_return=True,
        )
        self.assertEqual(result, 1)
        self.assertEqual(validate.call_count, 2)
        mutate.assert_called_once()
        self.assertIn("postflight reconciliation completed", stderr)
        self.assertIn("STOP without retry", stderr)

    def test_process_group_actions_finish_before_session_leader_reap(self) -> None:
        script = f"""
import importlib.util
import json
import os
import subprocess
import sys

spec = importlib.util.spec_from_file_location("launcher_pgid_order", {str(LAUNCHER)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
events = []
reaped = False
real_killpg = module.os.killpg
real_poll = module.subprocess.Popen.poll
real_communicate = module.subprocess.Popen.communicate
real_wait = module.subprocess.Popen.wait

def record_reap(event, result):
    global reaped
    if result is not None:
        reaped = True
        events.append(event)
    return result

def traced_killpg(pgid, signum):
    if reaped:
        raise RuntimeError("process-group action followed leader reap")
    events.append(f"killpg:{{signum}}")
    return real_killpg(pgid, signum)

def traced_poll(process):
    return record_reap("poll-reaped", real_poll(process))

def traced_communicate(process, *args, **kwargs):
    result = real_communicate(process, *args, **kwargs)
    record_reap("communicate-reaped", process.returncode)
    return result

def traced_wait(process, *args, **kwargs):
    result = real_wait(process, *args, **kwargs)
    return record_reap("wait-reaped", result)

module.os.killpg = traced_killpg
module.subprocess.Popen.poll = traced_poll
module.subprocess.Popen.communicate = traced_communicate
module.subprocess.Popen.wait = traced_wait
try:
    result = module.run_mutation_process(
        [sys.executable, "-c", "pass"], os.environ.copy(), None,
        lambda _process: None, lambda: False,
    )
except BaseException as error:
    print(f"{{type(error).__name__}}: {{error}}", file=sys.stderr)
    raise SystemExit(31)
if result.returncode != 0 or not reaped:
    raise SystemExit(32)
print(json.dumps(events))
"""
        completed = subprocess.run(
            [sys.executable, "-I", "-s", "-c", script],
            check=False, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        events = json.loads(completed.stdout.strip().splitlines()[-1])
        reap_index = next(
            index for index, event in enumerate(events) if event.endswith("-reaped")
        )
        self.assertTrue(any(event.startswith("killpg:") for event in events))
        self.assertFalse(any(
            event.startswith("killpg:") for event in events[reap_index + 1:]
        ))

    def test_mutation_process_pumps_one_mib_input_and_output_without_deadlock(self) -> None:
        child_program = (
            "import os\n"
            "import sys\n"
            "os.write(1, b'o' * (1024 * 1024))\n"
            "payload = sys.stdin.buffer.read()\n"
            "os.write(2, str(len(payload)).encode('ascii'))\n"
        )
        script = f"""
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location("launcher_pipe_pump", {str(LAUNCHER)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.run_mutation_process(
    [sys.executable, "-c", {child_program!r}], os.environ.copy(), b"i" * (1024 * 1024),
    lambda _process: None, lambda: False,
)
if result.returncode != 0:
    raise SystemExit(41)
if result.stdout != b"o" * (1024 * 1024):
    raise SystemExit(42)
if result.stderr != b"1048576":
    raise SystemExit(43)
"""
        completed = subprocess.run(
            [sys.executable, "-I", "-s", "-c", script],
            check=False, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def assert_successful_child_fences_descendant_before_postflight(
        self, *, inherit_pipes: bool,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child_pid = root / "child-pid"
            child_exited = root / "child-exited"
            descendant_pid = root / "descendant-pid"
            descendant_started = root / "descendant-started"
            descendant_exited = root / "descendant-exited"
            postflight_completed = root / "postflight-completed"
            descendant_program = (
                "from pathlib import Path\n"
                "import os\n"
                "import signal\n"
                "import time\n"
                f"pid = Path({str(descendant_pid)!r})\n"
                f"started = Path({str(descendant_started)!r})\n"
                f"exited = Path({str(descendant_exited)!r})\n"
                "def stop(*_args):\n"
                "    exited.write_text('exited', encoding='ascii')\n"
                "    signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "    time.sleep(60)\n"
                "signal.signal(signal.SIGTERM, stop)\n"
                "pid.write_text(str(os.getpid()), encoding='ascii')\n"
                "started.write_text('started', encoding='ascii')\n"
                "time.sleep(60)\n"
            )
            stdio = "" if inherit_pipes else (
                ", stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, "
                "stderr=subprocess.DEVNULL"
            )
            child_program = (
                "from pathlib import Path\n"
                "import os\n"
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                f"child_pid = Path({str(child_pid)!r})\n"
                f"child_exited = Path({str(child_exited)!r})\n"
                f"descendant_started = Path({str(descendant_started)!r})\n"
                "child_pid.write_text(str(os.getpid()), encoding='ascii')\n"
                f"subprocess.Popen([sys.executable, '-c', {descendant_program!r}]{stdio})\n"
                "while not descendant_started.is_file():\n"
                "    time.sleep(0.01)\n"
                "child_exited.write_text('exited', encoding='ascii')\n"
            )
            script = f"""
import importlib.util
import os
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("launcher_after_child_exit", {str(LAUNCHER)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
child_pid = Path({str(child_pid)!r})
child_exited = Path({str(child_exited)!r})
descendant_pid = Path({str(descendant_pid)!r})
descendant_exited = Path({str(descendant_exited)!r})
postflight = Path({str(postflight_completed)!r})
def process_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True
def verify_postflight(*_args, **_kwargs):
    direct_pid = int(child_pid.read_text(encoding="ascii"))
    residual_pid = int(descendant_pid.read_text(encoding="ascii"))
    if not child_exited.is_file() or process_exists(direct_pid):
        raise RuntimeError("postflight started before direct child was gone")
    if not descendant_exited.is_file() or process_exists(residual_pid):
        raise RuntimeError("postflight started before descendant was gone")
    try:
        os.killpg(direct_pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError("postflight started before process group was absent")
    postflight.write_text("done", encoding="ascii")
    return 0
module.execute_materialized_validator = verify_postflight
tools = module.TrustedTools((Path("/usr/bin/true"), "1" * 64), (Path("/usr/bin/true"), "2" * 64))
command = [sys.executable, "-c", {child_program!r}]
try:
    result = module.execute_fenced_github_operation(command, {{}}, b"validator", "a" * 64, [], tools, Path({str(root)!r}), "secret", None)
except module.LauncherError as error:
    print(error, file=sys.stderr)
    raise SystemExit(23)
raise SystemExit(result)
"""
            process = subprocess.Popen(
                [sys.executable, "-I", "-s", "-c", script],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            timed_out = False
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                stdout, stderr = process.communicate(timeout=5)
            finally:
                if child_pid.is_file():
                    group_id = int(child_pid.read_text(encoding="ascii"))
                    try:
                        os.killpg(group_id, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    deadline = time.monotonic() + 1
                    while time.monotonic() < deadline:
                        try:
                            os.killpg(group_id, 0)
                        except ProcessLookupError:
                            break
                        time.sleep(0.02)
                    else:
                        try:
                            os.killpg(group_id, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
            self.assertFalse(timed_out, (stdout, stderr))
            self.assertEqual(process.returncode, 0, (stdout, stderr))
            self.assertTrue(child_exited.is_file())
            self.assertTrue(descendant_exited.is_file())
            self.assertTrue(postflight_completed.is_file())

    def test_successful_child_exit_fences_devnull_descendant(self) -> None:
        self.assert_successful_child_fences_descendant_before_postflight(
            inherit_pipes=False,
        )

    def test_successful_child_exit_fences_pipe_inheriting_descendant(self) -> None:
        self.assert_successful_child_fences_descendant_before_postflight(
            inherit_pipes=True,
        )

    def assert_real_termination_signal_fences_child_before_postflight(
        self, signum: int,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child_started = root / "child-started"
            child_exited = root / "child-exited"
            descendant_started = root / "descendant-started"
            descendant_exited = root / "descendant-exited"
            postflight_completed = root / "postflight-completed"
            descendant_program = (
                "from pathlib import Path\n"
                "import signal\n"
                "import sys\n"
                "import time\n"
                f"started = Path({str(descendant_started)!r})\n"
                f"exited = Path({str(descendant_exited)!r})\n"
                "def stop(*_args):\n"
                "    exited.write_text('exited', encoding='ascii')\n"
                "    raise SystemExit(0)\n"
                "signal.signal(signal.SIGTERM, stop)\n"
                "started.write_text('started', encoding='ascii')\n"
                "time.sleep(60)\n"
            )
            child_program = (
                "from pathlib import Path\n"
                "import signal\n"
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                f"started = Path({str(child_started)!r})\n"
                f"descendant_started = Path({str(descendant_started)!r})\n"
                f"exited = Path({str(child_exited)!r})\n"
                f"subprocess.Popen([sys.executable, '-c', {descendant_program!r}])\n"
                "def stop(*_args):\n"
                "    exited.write_text('exited', encoding='ascii')\n"
                "    raise SystemExit(0)\n"
                "signal.signal(signal.SIGTERM, stop)\n"
                "while not descendant_started.is_file():\n"
                "    time.sleep(0.01)\n"
                "started.write_text('started', encoding='ascii')\n"
                "time.sleep(60)\n"
            )
            script = f"""
import importlib.util
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("launcher_under_signal", {str(LAUNCHER)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
postflight = Path({str(postflight_completed)!r})
child_exited = Path({str(child_exited)!r})
descendant_exited = Path({str(descendant_exited)!r})
def verify_postflight(*_args, **_kwargs):
    if not child_exited.is_file():
        raise RuntimeError("postflight started before mutation child exited")
    if not descendant_exited.is_file():
        raise RuntimeError("postflight started before mutation descendant exited")
    postflight.write_text("done", encoding="ascii")
    return 0
module.execute_materialized_validator = verify_postflight
tools = module.TrustedTools((Path("/usr/bin/true"), "1" * 64), (Path("/usr/bin/true"), "2" * 64))
child = [sys.executable, "-c", {child_program!r}]
try:
    module.execute_fenced_github_operation(child, {{}}, b"validator", "a" * 64, [], tools, Path({str(root)!r}), "secret", None)
except module.LauncherError as error:
    print(error, file=sys.stderr)
    raise SystemExit(23)
raise SystemExit(0)
"""
            process = subprocess.Popen(
                [sys.executable, "-I", "-s", "-c", script],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            deadline = time.monotonic() + 10
            while not child_started.exists() and process.poll() is None:
                if time.monotonic() >= deadline:
                    process.kill()
                    self.fail("signal regression child did not start")
                time.sleep(0.02)
            process.send_signal(signum)
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 23, (stdout, stderr))
            self.assertTrue(child_exited.is_file())
            self.assertTrue(descendant_exited.is_file())
            self.assertTrue(postflight_completed.is_file())
            self.assertIn("postflight reconciliation completed", stderr)
            self.assertIn("STOP without retry", stderr)

    def test_real_sigterm_during_mutation_still_runs_postflight(self) -> None:
        self.assert_real_termination_signal_fences_child_before_postflight(signal.SIGTERM)

    def test_real_sigint_during_mutation_still_runs_postflight(self) -> None:
        self.assert_real_termination_signal_fences_child_before_postflight(signal.SIGINT)

    @unittest.skipUnless(hasattr(signal, "SIGQUIT"), "SIGQUIT is unavailable")
    def test_real_sigquit_during_mutation_still_runs_postflight(self) -> None:
        self.assert_real_termination_signal_fences_child_before_postflight(signal.SIGQUIT)

    def test_mutation_input_is_materialized_into_private_launcher_storage(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "request.json"
            destination = root / "private" / "mutation-input.json"
            source.write_text('{"body":"exact"}\n', encoding="utf-8")
            source.chmod(0o400)
            materialized = launcher.materialize_mutation_input(
                source.resolve(), destination
            )
            self.assertEqual(materialized, destination)
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o400)

    def test_trusted_executable_rejects_source_replacement_during_read(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "gh"
            replacement = root / "replacement"
            source.write_bytes(b"trusted executable bytes")
            source.chmod(0o500)
            replacement.write_bytes(b"attacker executable bytes")
            replacement.chmod(0o500)
            real_open = launcher.os.open
            launcher.TRUSTED_EXECUTABLE_SHA256 = {
                **launcher.TRUSTED_EXECUTABLE_SHA256,
                "GitHub CLI": {hashlib.sha256(source.read_bytes()).hexdigest()},
            }

            def replace_after_open(path, flags):
                descriptor = real_open(path, flags)
                os.replace(replacement, source)
                return descriptor

            with mock.patch.object(launcher.os, "open", side_effect=replace_after_open):
                with self.assertRaisesRegex(
                    launcher.LauncherError, "changed during materialization"
                ):
                    launcher.trusted_executable((source,), "GitHub CLI")

    def test_trusted_executable_rejects_unpinned_symlink_target(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "malicious-gh"
            candidate = root / "gh"
            target.write_bytes(b"malicious executable bytes")
            target.chmod(0o500)
            candidate.symlink_to(target.name)
            launcher.TRUSTED_EXECUTABLE_SHA256 = {
                **launcher.TRUSTED_EXECUTABLE_SHA256,
                "GitHub CLI": {hashlib.sha256(b"different trusted bytes").hexdigest()},
            }
            with self.assertRaisesRegex(launcher.LauncherError, "digest is not pinned"):
                launcher.trusted_executable((candidate,), "GitHub CLI")

    def test_runtime_contract_forbids_external_launcher_copy(self) -> None:
        canonical = (
            LAUNCHER.parents[1]
            / "fronius-modbus-multivendor-v3-w29-26.implementing"
            / "00-canonical.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(canonical.split())
        self.assertIn(
            "accepts its initial bootstrap only at that repo-owned path in the "
            "owner-private canonical-main checkout and requires byte equality with "
            "the authenticated anchor",
            normalized,
        )
        self.assertIn("isolatedly re-executes the authenticated canonical launcher", normalized)
        self.assertNotIn("installed external copy must remain byte-identical", normalized)

    def test_initial_launcher_rejects_a_copied_external_entrypoint(self) -> None:
        launcher = load_launcher()
        contents = LAUNCHER.read_bytes()
        digest = hashlib.sha256(contents).hexdigest()
        launcher.require_initial_launcher_source(LAUNCHER.parents[1], contents, digest)
        with tempfile.TemporaryDirectory() as temporary:
            external_checkout = Path(temporary)
            (external_checkout / "scripts").mkdir()
            copied = external_checkout / launcher.LAUNCHER_PATH
            copied.write_bytes(contents)
            with self.assertRaisesRegex(
                launcher.LauncherError,
                "not the repo-owned canonical-checkout entrypoint",
            ):
                launcher.require_initial_launcher_source(
                    external_checkout, contents, digest,
                )

    def test_canonical_reexec_marker_rejects_modified_materialization(self) -> None:
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            root.chmod(0o700)
            source = root / "launcher.py"
            token_path = root / "token"
            source.write_bytes(b"canonical launcher")
            source.chmod(0o500)
            token_path.write_text("one-use", encoding="ascii")
            token_path.chmod(0o400)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            prefix = launcher.CANONICAL_REEXEC_ENV_PREFIX
            marker = {
                f"{prefix}PATH": str(source),
                f"{prefix}SHA256": digest,
                f"{prefix}TOKEN": "one-use",
                f"{prefix}TOKEN_FILE": str(token_path),
            }
            original_file = launcher.__file__
            try:
                launcher.__file__ = str(source)
                with mock.patch.dict(os.environ, marker, clear=False):
                    source.chmod(0o600)
                    source.write_bytes(b"modified launcher")
                    source.chmod(0o500)
                    with self.assertRaisesRegex(
                        launcher.LauncherError, "re-exec digest mismatch"
                    ):
                        launcher.consume_canonical_reexec_marker()
                source.chmod(0o600)
                source.write_bytes(b"canonical launcher")
                source.chmod(0o500)
                token_path.chmod(0o600)
                token_path.write_text("one-use", encoding="ascii")
                token_path.chmod(0o400)
                with mock.patch.dict(os.environ, marker, clear=False):
                    self.assertEqual(
                        launcher.consume_canonical_reexec_marker(), digest
                    )
                    self.assertFalse(token_path.exists())
            finally:
                launcher.__file__ = original_file


if __name__ == "__main__":
    unittest.main()
