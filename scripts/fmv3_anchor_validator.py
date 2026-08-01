#!/usr/bin/env python3
"""Materialize the FMV3 authorization validator only after PR #91 authentication."""

from __future__ import annotations

import argparse
import base64
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable

import yaml


PLAN_REPOSITORY = "Project-Helianthus/helianthus-execution-plans"
CANONICAL_REMOTES = {
    "https://github.com/Project-Helianthus/helianthus-execution-plans.git",
    "git@github.com:Project-Helianthus/helianthus-execution-plans.git",
}
CANONICAL_FETCH_URL = (
    "https://github.com/Project-Helianthus/helianthus-execution-plans.git"
)
AMENDMENT_PR_NUMBER = 91
AMENDMENT_PR_URL = (
    "https://github.com/Project-Helianthus/helianthus-execution-plans/pull/91"
)
EXPECTED_BASE_SHA = "6fd2b4a8d181f5133250a0f2f1380d057254db60"
EXPECTED_HEAD_REF = "issue/90-fmv3-capability-ledger-reconcile"
PLAN_PATH = "fronius-modbus-multivendor-v3-w29-26.implementing/plan.yaml"
VALIDATOR_PATH = (
    "fronius-modbus-multivendor-v3-w29-26.implementing/validate_plan.py"
)
MATERIALIZATION_ENV_PREFIX = "FMV3_ANCHOR_MATERIALIZATION_"
GIT_SOURCE_CANDIDATES = (
    Path("/Library/Developer/CommandLineTools/usr/bin/git"),
    Path("/Applications/Xcode.app/Contents/Developer/usr/bin/git"),
    Path("/usr/bin/git"),
)
GH_SOURCE_CANDIDATES = (
    Path("/opt/homebrew/bin/gh"),
    Path("/usr/local/bin/gh"),
    Path("/usr/bin/gh"),
)
TRUSTED_EXECUTABLE_SHA256 = {
    "Git": {
        "24d10c6f5ee9d5eb463273269d3bc30fa8dcbffda30841112480dea950d0c55a",
        "09b2e76b4a77c930755f0cf689babfe2b5f713b047636a6d264764567b395819",
        "f54a87f6253aab09ed7b522bd78ddeab509105b1043076209d89127e55877a48",
    },
    "GitHub CLI": {
        "582a40676acf1394fcaf1c8c8bc5bad21806bd8c864b209d37b185c2df45dc92",
        "56b8bbbb27b066ecb33dbef9a256dc9d1314adaeff0908a752feba6c34053b40",
    },
}
CLAIM_PROCESS_LOCK_ADDRESS = ("127.0.0.1", 45991)
MODEL_ROUTER_SHA256 = "e4e4658bc8252dc0354e2a04aaa74631098571ed0b00030e869760025a76e02b"
MODEL_ROUTING_POLICY_SHA256 = (
    "7c5fd44ba842c9da311f6211960b3151ed860245db41501efb9bfeec001c23c6"
)
ROUTING_RECEIPT_SCHEMA = "helianthus.fmv3-model-routing-receipt.v1"
ROUTING_GATE_RISK_MAP = {
    "security": "security",
    "data_integrity": "data_integrity",
    "concurrency": "concurrency",
    "recovery": "recovery",
    "protocol_interop": "wire_format",
    "transport_gate": "distributed_protocol",
}
DOCS_REPOSITORY = "Project-Helianthus/helianthus-docs-ebus"


class LauncherError(RuntimeError):
    pass


class MutationProcessGroupFenceError(LauncherError):
    pass


class TrustedTools:
    """Private executable copies bound to the launcher's lifetime."""

    def __init__(self, git: tuple[Path, str], gh: tuple[Path, str]) -> None:
        self.git = git
        self.gh = gh


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LauncherError(message)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    text: bool = True,
    env: dict[str, str] | None = None,
) -> str | bytes:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=text,
        env=env,
    )
    require(
        result.returncode == 0,
        f"command failed ({' '.join(map(str, command))}): "
        f"{result.stderr.strip() if text else result.stderr.decode(errors='replace').strip()}",
    )
    return result.stdout


def trusted_executable(candidates: tuple[Path, ...], label: str) -> tuple[Path, bytes, str]:
    for candidate in candidates:
        try:
            candidate_metadata = os.lstat(candidate)
        except FileNotFoundError:
            continue
        candidate_link = os.readlink(candidate) if stat.S_ISLNK(candidate_metadata.st_mode) else None
        resolved = candidate.resolve(strict=True)
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(resolved, flags)
        try:
            metadata = os.fstat(descriptor)
            require(
                stat.S_ISREG(metadata.st_mode)
                and metadata.st_uid in {0, os.getuid()}
                and metadata.st_mode & 0o022 == 0
                and (label != "Git" or metadata.st_uid == 0),
                f"{label} executable ownership or mode is untrusted",
            )
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            final_descriptor_metadata = os.fstat(descriptor)
            final_path_metadata = os.stat(resolved, follow_symlinks=False)
            final_candidate_metadata = os.lstat(candidate)
            final_candidate_link = (
                os.readlink(candidate) if stat.S_ISLNK(final_candidate_metadata.st_mode) else None
            )
            require(
                (metadata.st_dev, metadata.st_ino, metadata.st_size)
                == (
                    final_descriptor_metadata.st_dev,
                    final_descriptor_metadata.st_ino,
                    final_descriptor_metadata.st_size,
                )
                and (metadata.st_dev, metadata.st_ino)
                == (final_path_metadata.st_dev, final_path_metadata.st_ino),
                f"{label} executable changed during materialization",
            )
            require(
                (candidate_metadata.st_dev, candidate_metadata.st_ino, candidate_metadata.st_mode)
                == (final_candidate_metadata.st_dev, final_candidate_metadata.st_ino,
                    final_candidate_metadata.st_mode)
                and candidate_link == final_candidate_link,
                f"{label} executable candidate changed during materialization",
            )
            contents = b"".join(chunks)
            require(len(contents) == metadata.st_size, f"{label} executable read is incomplete")
        finally:
            os.close(descriptor)
        digest = hashlib.sha256(contents).hexdigest()
        require(digest in TRUSTED_EXECUTABLE_SHA256[label],
                f"{label} executable digest is not pinned")
        return resolved, contents, digest
    raise LauncherError(f"{label} executable is unavailable at a trusted fixed path")


def materialize_trusted_executable(
    candidates: tuple[Path, ...], label: str, destination: Path
) -> tuple[Path, str]:
    _, contents, digest = trusted_executable(candidates, label)
    path = destination / label.lower().replace(" ", "-")
    with path.open("xb") as output:
        output.write(contents)
        output.flush()
        os.fsync(output.fileno())
    path.chmod(0o500)
    metadata = path.stat()
    require(
        path.is_file()
        and not path.is_symlink()
        and stat.S_ISREG(metadata.st_mode)
        and stat.S_IMODE(metadata.st_mode) == 0o500
        and hashlib.sha256(path.read_bytes()).hexdigest() == digest,
        f"{label} executable materialization is not exact",
    )
    return path, digest


def materialize_trusted_tools(destination: Path) -> TrustedTools:
    destination.mkdir(mode=0o700)
    destination.chmod(0o700)
    metadata = destination.stat()
    require(
        destination.is_dir()
        and not destination.is_symlink()
        and stat.S_ISDIR(metadata.st_mode)
        and stat.S_IMODE(metadata.st_mode) == 0o700,
        "trusted tool directory is not private",
    )
    return TrustedTools(
        materialize_trusted_executable(GIT_SOURCE_CANDIDATES, "Git", destination),
        materialize_trusted_executable(GH_SOURCE_CANDIDATES, "GitHub CLI", destination),
    )


def git(
    tools: TrustedTools, checkout: Path, *arguments: str, text: bool = True
) -> str | bytes:
    executable, _ = tools.git
    environment = {
        name: os.environ[name]
        for name in ("HOME", "LANG", "LC_ALL")
        if os.environ.get(name)
    }
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name, None)
    environment.update({
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
    })
    return run(
        [
            str(executable), "--no-replace-objects",
            "-c", "core.hooksPath=/dev/null",
            "-c", "core.fsmonitor=false",
            "-c", "credential.helper=",
            "-C", str(checkout), *arguments,
        ],
        text=text,
        env=environment,
    )


def github_api(tools: TrustedTools, endpoint: str) -> Any:
    executable, _ = tools.gh
    environment = {
        name: os.environ[name]
        for name in ("HOME", "GH_TOKEN", "GITHUB_TOKEN", "LANG", "LC_ALL")
        if os.environ.get(name)
    }
    raw = run(
        [executable, "api", "--hostname", "github.com", endpoint],
        env=environment,
    )
    assert isinstance(raw, str)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise LauncherError(f"GitHub API returned invalid JSON for {endpoint}") from error


def committed_regular_blob(
    tools: TrustedTools, checkout: Path, commit: str, path: str
) -> bytes:
    tree = git(tools, checkout, "ls-tree", "-z", commit, "--", path, text=False)
    assert isinstance(tree, bytes)
    rows = [row for row in tree.split(b"\0") if row]
    require(len(rows) == 1, f"anchor path is absent or ambiguous: {path}")
    metadata, separator, encoded_path = rows[0].partition(b"\t")
    fields = metadata.split()
    require(
        separator == b"\t"
        and encoded_path.decode("utf-8") == path
        and len(fields) == 3
        and fields[0] in {b"100644", b"100755"}
        and fields[1] == b"blob",
        f"anchor path is not a regular committed blob: {path}",
    )
    blob = git(tools, checkout, "show", f"{commit}:{path}", text=False)
    assert isinstance(blob, bytes)
    return blob


def require_canonical_checkout(tools: TrustedTools, checkout: Path) -> str:
    require(checkout.is_dir() and not checkout.is_symlink(), "checkout is not a directory")
    toplevel = Path(str(git(tools, checkout, "rev-parse", "--show-toplevel")).strip()).resolve()
    require(toplevel == checkout.resolve(), "checkout must equal its git toplevel")
    git_dir = Path(str(git(tools, checkout, "rev-parse", "--absolute-git-dir")).strip())
    replacement_refs = str(
        git(tools, checkout, "for-each-ref", "--format=%(refname)", "refs/replace")
    ).strip()
    grafts = git_dir / "info" / "grafts"
    alternates = git_dir / "objects" / "info" / "alternates"
    require(
        not replacement_refs
        and (not grafts.exists() or grafts.stat().st_size == 0)
        and (not alternates.exists() or alternates.stat().st_size == 0),
        "authorization checkout rejects replacement refs, grafts, and alternate object stores",
    )
    require(
        str(git(tools, checkout, "symbolic-ref", "--short", "HEAD")).strip() == "main",
        "authorization checkout must be on main",
    )
    require(
        not str(git(tools, checkout, "status", "--porcelain=v1", "--untracked-files=all")).strip(),
        "authorization checkout must be fully clean",
    )
    fetch_url = str(git(tools, checkout, "remote", "get-url", "origin")).strip()
    push_url = str(git(tools, checkout, "remote", "get-url", "--push", "origin")).strip()
    require(
        fetch_url in CANONICAL_REMOTES and push_url in CANONICAL_REMOTES,
        "origin fetch/push URLs do not identify the canonical plan repository",
    )
    head = str(git(tools, checkout, "rev-parse", "HEAD")).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", head) is not None, "checkout HEAD is invalid")
    main_ref = github_api(tools, f"repos/{PLAN_REPOSITORY}/git/ref/heads/main")
    require(
        isinstance(main_ref, dict)
        and main_ref.get("object", {}).get("type") == "commit"
        and main_ref.get("object", {}).get("sha") == head,
        "checkout is not exactly at canonical GitHub main",
    )
    return head


def materialize_canonical_checkout(tools: TrustedTools, destination: Path) -> Path:
    """Build an owner-private checkout without consuming caller Git config or objects."""
    destination.mkdir(mode=0o700)
    main_ref = github_api(tools, f"repos/{PLAN_REPOSITORY}/git/ref/heads/main")
    main_sha = (
        main_ref.get("object", {}).get("sha") if isinstance(main_ref, dict) else None
    )
    require(isinstance(main_sha, str)
            and re.fullmatch(r"[0-9a-f]{40}", main_sha) is not None,
            "canonical GitHub main ref is invalid")
    git(tools, destination, "init", "-b", "main")
    git(tools, destination, "remote", "add", "origin", CANONICAL_FETCH_URL)
    git(tools, destination, "fetch", "--no-tags", "origin", main_sha)
    git(tools, destination, "checkout", "-B", "main", main_sha)
    return destination


def authenticate_anchor(
    tools: TrustedTools, plan_head_sha: str, canonical_main: str
) -> None:
    require(
        re.fullmatch(r"[0-9a-f]{40}", plan_head_sha) is not None,
        "--plan-head-sha must be a full lowercase 40-character SHA",
    )
    pr = github_api(tools, f"repos/{PLAN_REPOSITORY}/pulls/{AMENDMENT_PR_NUMBER}")
    require(isinstance(pr, dict), "PR #91 response is invalid")
    head_sha = pr.get("head", {}).get("sha")
    require(
        pr.get("number") == AMENDMENT_PR_NUMBER
        and pr.get("html_url") == AMENDMENT_PR_URL
        and pr.get("state") == "closed"
        and pr.get("merged") is True
        and pr.get("merge_commit_sha") == plan_head_sha
        and pr.get("base", {}).get("sha") == EXPECTED_BASE_SHA
        and pr.get("base", {}).get("ref") == "main"
        and pr.get("base", {}).get("repo", {}).get("full_name") == PLAN_REPOSITORY
        and pr.get("head", {}).get("ref") == EXPECTED_HEAD_REF
        and pr.get("head", {}).get("repo", {}).get("full_name") == PLAN_REPOSITORY
        and isinstance(head_sha, str)
        and re.fullmatch(r"[0-9a-f]{40}", head_sha) is not None,
        "PR #91 does not authenticate the supplied plan anchor",
    )
    head_commit = github_api(tools, f"repos/{PLAN_REPOSITORY}/git/commits/{head_sha}")
    merge_commit = github_api(tools, f"repos/{PLAN_REPOSITORY}/git/commits/{plan_head_sha}")
    comparison = github_api(tools,
        f"repos/{PLAN_REPOSITORY}/compare/{plan_head_sha}...{canonical_main}"
    )
    require(
        isinstance(head_commit, dict)
        and isinstance(merge_commit, dict)
        and head_commit.get("tree", {}).get("sha")
        == merge_commit.get("tree", {}).get("sha")
        and isinstance(merge_commit.get("parents"), list)
        and len(merge_commit["parents"]) == 1
        and merge_commit["parents"][0].get("sha") == EXPECTED_BASE_SHA
        and isinstance(comparison, dict)
        and comparison.get("status") in {"ahead", "identical"}
        and comparison.get("merge_base_commit", {}).get("sha") == plan_head_sha,
        "PR #91 squash topology or canonical-main ancestry is invalid",
    )


def load_anchored_validator(
    tools: TrustedTools, checkout: Path, plan_head_sha: str
) -> tuple[bytes, str]:
    plan_blob = committed_regular_blob(tools, checkout, plan_head_sha, PLAN_PATH)
    try:
        plan = yaml.safe_load(plan_blob)
    except yaml.YAMLError as error:
        raise LauncherError("anchored plan YAML is invalid") from error
    require(isinstance(plan, dict), "anchored plan is not a mapping")
    authorization = plan.get("execution_authorization")
    anchor = authorization.get("authorization_anchor") if isinstance(authorization, dict) else None
    tooling = anchor.get("tooling_binding") if isinstance(anchor, dict) else None
    require(
        isinstance(anchor, dict)
        and anchor.get("plan_path") == PLAN_PATH
        and isinstance(tooling, dict)
        and tooling.get("authorization_execution") == "materialized_from_pr91_anchor"
        and tooling.get("validator_path") == VALIDATOR_PATH,
        "anchored validator tooling binding is invalid",
    )
    digest = tooling.get("validator_sha256")
    require(
        isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
        "anchored validator digest is invalid",
    )
    validator = committed_regular_blob(tools, checkout, plan_head_sha, VALIDATOR_PATH)
    require(
        hashlib.sha256(validator).hexdigest() == digest,
        "anchored validator blob does not match its SHA-256",
    )
    return validator, digest


def execute_materialized_validator(
    validator: bytes,
    digest: str,
    arguments: list[str],
    git_binding: tuple[Path, str],
    gh_binding: tuple[Path, str],
    root: Path,
    claim_owner_secret: str,
) -> int:
    root_metadata = root.stat()
    require(
        root.is_dir()
        and not root.is_symlink()
        and stat.S_ISDIR(root_metadata.st_mode)
        and stat.S_IMODE(root_metadata.st_mode) == 0o700,
        "anchor materialization directory is not private",
    )
    invocation = root / f"validator-{secrets.token_hex(16)}"
    invocation.mkdir(mode=0o700)
    invocation.chmod(0o700)
    validator_path = invocation / "validate_plan.py"
    token_path = invocation / "one-use-token"
    claim_secret_path = invocation / "claim-owner-secret"
    token = secrets.token_hex(32)
    validator_path.write_bytes(validator)
    validator_path.chmod(0o500)
    token_path.write_text(token, encoding="ascii")
    token_path.chmod(0o400)
    claim_secret_path.write_text(claim_owner_secret, encoding="ascii")
    claim_secret_path.chmod(0o400)
    environment = {
        name: os.environ[name]
        for name in (
            "HOME", "GH_TOKEN", "GITHUB_TOKEN", "LANG", "LC_ALL",
            "FMV3_DOCS_CANDIDATE_ROOT", "HELIANTHUS_VALIDATION_CACHE_ROOT",
        )
        if os.environ.get(name)
    }
    environment["PYTHONNOUSERSITE"] = "1"
    environment[f"{MATERIALIZATION_ENV_PREFIX}VALIDATOR"] = str(validator_path)
    environment[f"{MATERIALIZATION_ENV_PREFIX}SHA256"] = digest
    environment[f"{MATERIALIZATION_ENV_PREFIX}TOKEN"] = token
    environment[f"{MATERIALIZATION_ENV_PREFIX}TOKEN_FILE"] = str(token_path)
    environment[f"{MATERIALIZATION_ENV_PREFIX}CLAIM_OWNER_SECRET_FILE"] = str(
        claim_secret_path
    )
    environment[f"{MATERIALIZATION_ENV_PREFIX}GIT"] = str(git_binding[0])
    environment[f"{MATERIALIZATION_ENV_PREFIX}GIT_SHA256"] = git_binding[1]
    environment[f"{MATERIALIZATION_ENV_PREFIX}GH"] = str(gh_binding[0])
    environment[f"{MATERIALIZATION_ENV_PREFIX}GH_SHA256"] = gh_binding[1]
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-s",
            str(validator_path),
            *arguments,
            "--materialized-anchor-validator",
        ],
        check=False,
        env=environment,
    )
    require(not token_path.exists(), "materialized validator did not consume its token")
    require(not claim_secret_path.exists(),
            "materialized validator did not consume its claim owner secret")
    return result.returncode


def lock_claim_owner_secret(path_value: Path | None) -> tuple[str, int]:
    require(path_value is not None and path_value.is_absolute(),
            "claim mode requires an absolute --claim-owner-secret-file")
    metadata = os.lstat(path_value)
    require(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
            and metadata.st_uid == os.getuid()
            and stat.S_IMODE(metadata.st_mode) == 0o400,
            "claim owner secret file must be owner-only mode 0400")
    descriptor = os.open(
        path_value,
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        opened = os.fstat(descriptor)
        require(
            (opened.st_dev, opened.st_ino, opened.st_uid, opened.st_mode)
            == (metadata.st_dev, metadata.st_ino, metadata.st_uid, metadata.st_mode),
            "claim owner secret changed while it was opened",
        )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LauncherError(
                "another local claim operation holds the owner-secret lock"
            ) from exc
        contents = os.read(descriptor, 1024)
        require(os.read(descriptor, 1) == b"",
                "claim owner secret file is oversized")
        secret = contents.decode("ascii").strip()
        require(re.fullmatch(r"[0-9a-f]{64}", secret) is not None,
                "claim owner secret must be 256-bit lowercase hex")
        return secret, descriptor
    except Exception:
        os.close(descriptor)
        raise


def acquire_claim_process_lock() -> socket.socket:
    """Serialize conforming owner operations on a kernel socket, not a replaceable inode."""
    claim_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        claim_lock.bind(CLAIM_PROCESS_LOCK_ADDRESS)
        claim_lock.listen(1)
    except OSError as exc:
        claim_lock.close()
        raise LauncherError(
            "another local claim operation holds the stable process lock"
        ) from exc
    return claim_lock


def materialize_mutation_input(
    path_value: Path | None, destination: Path,
) -> Path | None:
    if path_value is None:
        return None
    require(path_value.is_absolute(), "--mutation-input must be absolute")
    metadata = os.lstat(path_value)
    require(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
            and metadata.st_uid == os.getuid()
            and stat.S_IMODE(metadata.st_mode) == 0o400
            and metadata.st_size <= 1024 * 1024,
            "mutation input must be an owner-only 0400 regular file of at most 1 MiB")
    descriptor = os.open(
        path_value,
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        opened = os.fstat(descriptor)
        require(
            (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mode)
            == (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mode),
            "mutation input changed while it was opened",
        )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            total += len(chunk)
            require(total <= 1024 * 1024, "mutation input exceeded 1 MiB while read")
            chunks.append(chunk)
        final = os.fstat(descriptor)
        current = os.stat(path_value, follow_symlinks=False)
        require(
            (opened.st_dev, opened.st_ino, opened.st_size)
            == (final.st_dev, final.st_ino, final.st_size)
            == (current.st_dev, current.st_ino, current.st_size),
            "mutation input changed during materialization",
        )
    finally:
        os.close(descriptor)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with destination.open("xb") as output:
        output.write(b"".join(chunks))
        output.flush()
        os.fsync(output.fileno())
    destination.chmod(0o400)
    return destination


def mutation_payload(source: Path | bytes | None, label: str) -> dict[str, object]:
    require(source is not None, f"{label} requires a JSON mutation input")

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            require(key not in result, f"{label} mutation input has duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(
            source.decode("utf-8") if isinstance(source, bytes)
            else source.read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
        )
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise LauncherError(f"{label} mutation input is not valid UTF-8 JSON") from exc
    require(isinstance(value, dict), f"{label} mutation input must be one JSON object")
    return value


def github_closing_references(body: str) -> list[str]:
    return re.findall(
        r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+"
        r"((?:https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/\d+)"
        r"|(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+)|(?:#\d+))\b",
        body,
    )


def require_mutation_capability(
    issue: dict[str, object], issue_number: int, capability: str,
    method: str, endpoint: str, input_source: Path | bytes | None,
) -> None:
    """Bind each REST mutation to one issue-specific, payload-checked capability."""
    require(
        re.fullmatch(r"[A-Za-z0-9._~%/-]+", endpoint) is not None
        and "://" not in endpoint
        and ".." not in endpoint
        and "%2e" not in endpoint.lower()
        and "%2f" not in endpoint.lower()
        and "%5c" not in endpoint.lower(),
        "fenced mutation endpoint is not a safe relative GitHub API path",
    )
    issue_id = issue.get("id")
    repository = issue.get("repo")
    issue_what = issue.get("what")
    require(isinstance(issue_id, str) and isinstance(repository, str)
            and isinstance(issue_what, str),
            "fenced mutation issue identity is invalid")
    issue_title = f"{issue_id}: {issue_what}"
    require(len(issue_title.encode("utf-8")) <= 256,
            "fenced mutation selected issue title exceeds GitHub bound")

    if capability == "create-public-repository":
        require(
            issue_id == "FMV3-M0-01"
            and repository == "Project-Helianthus/.github"
            and method == "POST"
            and endpoint == "orgs/Project-Helianthus/repos",
            "public-repository creation is not authorized by the selected issue",
        )
        payload = mutation_payload(input_source, capability)
        require(
            set(payload) == {
                "name", "private", "visibility", "auto_init", "has_issues",
                "has_projects", "has_wiki", "has_downloads", "has_discussions",
                "is_template",
            }
            and payload.get("name") in {"helianthus-modbus", "helianthus-modbusreg"}
            and payload.get("private") is False
            and payload.get("visibility") == "public"
            and payload.get("auto_init") is False
            and payload.get("has_issues") is True
            and payload.get("has_projects") is False
            and payload.get("has_wiki") is False
            and payload.get("has_downloads") is False
            and payload.get("has_discussions") is False
            and payload.get("is_template") is False,
            "public-repository creation payload is outside the exact empty-public allowlist",
        )
        return

    repo_prefix = f"repos/{repository}"
    issue_prefix = f"{repo_prefix}/issues/{issue_number}"
    branch_pattern = rf"issue/{issue_number}-[a-z0-9]+(?:-[a-z0-9]+)*"
    if capability == "selected-issue-comment":
        payload = mutation_payload(input_source, capability)
        body = payload.get("body")
        allowed = (
            method == "POST" and endpoint == f"{issue_prefix}/comments"
            and set(payload) == {"body"} and isinstance(body, str)
            and 0 < len(body.encode("utf-8")) <= 65_536
        )
    elif capability == "selected-issue-labels":
        if method in {"POST", "PUT"}:
            payload = mutation_payload(input_source, capability)
            labels = payload.get("labels")
            allowed = (
                endpoint == f"{issue_prefix}/labels" and set(payload) == {"labels"}
                and isinstance(labels, list) and 0 < len(labels) <= 100
                and all(isinstance(label, str) and 0 < len(label.encode("utf-8")) <= 50
                        for label in labels)
            )
        else:
            allowed = (
                method == "DELETE" and input_source is None
                and re.fullmatch(
                    rf"{re.escape(issue_prefix)}/labels/[A-Za-z0-9._~%-]+", endpoint,
                ) is not None
            )
    elif capability == "issue-pull-create":
        payload = mutation_payload(input_source, capability)
        body = payload.get("body")
        title = payload.get("title")
        allowed = (
            method == "POST" and endpoint == f"{repo_prefix}/pulls"
            and set(payload) == {"title", "head", "base", "body"}
            and title == issue_title
            and payload.get("base") == "main"
            and isinstance(payload.get("head"), str)
            and re.fullmatch(branch_pattern, payload["head"]) is not None
            and isinstance(body, str) and len(body.encode("utf-8")) <= 65_536
            and github_closing_references(body) == [f"#{issue_number}"]
        )
    else:
        allowed = False
    require(allowed, "fenced mutation is outside the selected issue capability")


def read_pinned_routing_file(
    path: Path, expected_sha256: str, label: str,
) -> bytes:
    require(path.is_absolute(), f"{label} path must be absolute")
    metadata = os.lstat(path)
    require(
        stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        and metadata.st_uid in {0, os.getuid()}
        and metadata.st_mode & 0o022 == 0
        and metadata.st_size <= 1024 * 1024,
        f"{label} ownership, mode, or size is untrusted",
    )
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        final = os.fstat(descriptor)
        current = os.stat(path, follow_symlinks=False)
        require(
            (metadata.st_dev, metadata.st_ino, metadata.st_size)
            == (opened.st_dev, opened.st_ino, opened.st_size)
            == (final.st_dev, final.st_ino, final.st_size)
            == (current.st_dev, current.st_ino, current.st_size),
            f"{label} changed during materialization",
        )
    finally:
        os.close(descriptor)
    contents = b"".join(chunks)
    require(hashlib.sha256(contents).hexdigest() == expected_sha256,
            f"{label} digest is not plan-pinned")
    return contents


def build_routing_receipt(
    plan_dir: Path, issue_id: str, plan_anchor: str,
    router_source: Path, policy_source: Path, destination: Path,
) -> tuple[str, str]:
    router = read_pinned_routing_file(
        router_source, MODEL_ROUTER_SHA256, "model router"
    )
    policy = read_pinned_routing_file(
        policy_source, MODEL_ROUTING_POLICY_SHA256, "model routing policy"
    )
    scripts = destination / ".codex" / "scripts"
    scripts.mkdir(mode=0o700, parents=True)
    router_path = scripts / "model_route.py"
    policy_path = destination / ".codex" / "model-routing-policy.json"
    router_path.write_bytes(router)
    router_path.chmod(0o500)
    policy_path.write_bytes(policy)
    policy_path.chmod(0o400)
    plan = yaml.safe_load((plan_dir / "plan.yaml").read_text(encoding="utf-8"))
    matches = [
        issue for issue in plan.get("issues", [])
        if isinstance(issue, dict) and issue.get("id") == issue_id
    ] if isinstance(plan, dict) else []
    require(
        len(matches) == 1
        and isinstance(matches[0].get("repo"), str)
        and type(matches[0].get("complexity")) is int,
        "routing issue specification is absent or ambiguous",
    )
    issue = matches[0]
    gates = issue.get("gates")
    require(isinstance(gates, list) and all(isinstance(gate, str) for gate in gates),
            "routing issue gates are invalid")
    risks = sorted({
        ROUTING_GATE_RISK_MAP[gate]
        for gate in gates if gate in ROUTING_GATE_RISK_MAP
    })
    role = "docs" if issue["repo"] == DOCS_REPOSITORY else "developer"
    command = [
        sys.executable, "-I", "-s", str(router_path),
        "--availability-mode", "openai_only",
        "--session-orchestrator-vendor", "openai",
        "--role", role,
        "--complexity", str(issue["complexity"]),
        "--openai-available", "--no-anthropic-available", "--autonomous",
    ]
    if role == "docs":
        command.extend(["--docs-mode", "architecture"])
    for risk in risks:
        command.extend(["--risk", risk])
    environment = {
        name: os.environ[name]
        for name in ("HOME", "LANG", "LC_ALL")
        if os.environ.get(name)
    }
    environment["PYTHONNOUSERSITE"] = "1"
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, env=environment,
    )
    require(result.returncode == 0, "plan-pinned model router failed")
    try:
        route = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise LauncherError("plan-pinned model router returned invalid JSON") from exc
    require(isinstance(route, dict), "plan-pinned model router result is invalid")
    receipt = {
        "schema": ROUTING_RECEIPT_SCHEMA,
        "issue_id": issue_id,
        "repository": issue["repo"],
        "complexity": issue["complexity"],
        "risks": risks,
        "plan_anchor": plan_anchor,
        "router_sha256": MODEL_ROUTER_SHA256,
        "policy_sha256": MODEL_ROUTING_POLICY_SHA256,
        "route": route,
    }
    encoded = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return base64.b64encode(encoded).decode("ascii"), hashlib.sha256(encoded).hexdigest()


def execute_fenced_github_operation(
    command: list[str], environment: dict[str, str], validator: bytes,
    digest: str, postflight_arguments: list[str], tools: TrustedTools,
    root: Path, claim_owner_secret: str, mutation_input: bytes | None,
) -> int:
    """Execute one mutation, then prove the exact claim fence still holds."""
    mutation: subprocess.CompletedProcess[bytes] | None = None
    mutation_error: BaseException | None = None
    postflight: int | None = None
    postflight_error: BaseException | None = None

    termination_signals: list[int] = []
    mutation_process: subprocess.Popen[bytes] | None = None
    handled_signals = tuple(
        value for value in (
            getattr(signal, "SIGHUP", None),
            getattr(signal, "SIGINT", None),
            getattr(signal, "SIGQUIT", None),
            getattr(signal, "SIGTERM", None),
        )
        if value is not None
    )
    previous_handlers: dict[int, object] = {}

    def remember_termination(signum: int, _frame: object) -> None:
        if signum not in termination_signals:
            termination_signals.append(signum)

    def capture_process(process: subprocess.Popen[bytes]) -> None:
        nonlocal mutation_process
        mutation_process = process

    def mutate_with_mandatory_postflight() -> subprocess.CompletedProcess[bytes]:
        nonlocal mutation_process, postflight, postflight_error
        process_group_fenced = False
        try:
            try:
                mutation_result = run_mutation_process(
                    command, environment, mutation_input, capture_process,
                    lambda: bool(termination_signals),
                )
            except MutationProcessGroupFenceError:
                raise
            except BaseException:
                process_group_fenced = True
                raise
            process_group_fenced = True
            return mutation_result
        finally:
            if process_group_fenced:
                mutation_process = None
                try:
                    postflight = execute_materialized_validator(
                        validator, digest, postflight_arguments,
                        tools.git, tools.gh, root, claim_owner_secret,
                    )
                except BaseException as error:
                    postflight_error = error

    try:
        for signum in handled_signals:
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, remember_termination)
        try:
            mutation = mutate_with_mandatory_postflight()
        except BaseException as error:
            mutation_error = error
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    if termination_signals and mutation_error is None:
        names = ", ".join(signal.Signals(value).name for value in termination_signals)
        mutation_error = LauncherError(f"termination signal received during mutation: {names}")
    if isinstance(mutation_error, MutationProcessGroupFenceError):
        raise LauncherError(
            "the private mutation process group could not be proven absent; "
            "postflight reconciliation was not started and execution must STOP "
            "without retry"
        ) from mutation_error
    if postflight_error is not None:
        raise LauncherError(
            "postflight verification failed after the fenced GitHub mutation; "
            "the mutation may have completed and execution must STOP without "
            "retry pending reconciliation"
        ) from postflight_error
    if postflight is not None and postflight != 0:
        raise LauncherError(
            "postflight reconciliation failed after the fenced GitHub mutation; "
            "the mutation may have completed and execution must STOP without "
            "retry pending reconciliation"
        )
    if mutation_error is not None:
        raise LauncherError(
            "GitHub mutation execution was interrupted or failed ambiguously; "
            "postflight reconciliation completed but the mutation may have "
            "completed and execution must STOP without retry"
        ) from mutation_error
    require(
        mutation is not None and postflight is not None,
        "fenced GitHub mutation or postflight result is unavailable",
    )
    if mutation.stdout:
        print(mutation.stdout.decode("utf-8", errors="replace"), end="")
    if mutation.stderr:
        print(mutation.stderr.decode("utf-8", errors="replace"), end="", file=sys.stderr)
    require(
        postflight == 0,
        "claim advanced during fenced GitHub mutation; the mutation may have "
        "completed and execution must STOP",
    )
    require(
        mutation.returncode == 0,
        "GitHub returned an ambiguous failure after the fenced mutation; the "
        "mutation may have completed and execution must STOP without retry",
    )
    return 0


def require_nonreaping_waitid() -> int:
    """Return waitid flags that observe exit while retaining PID/PGID identity."""
    required = ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")
    missing = [name for name in required if not hasattr(os, name)]
    if missing:
        raise MutationProcessGroupFenceError(
            "non-reaping waitid support is unavailable: " + ", ".join(missing)
        )
    return os.WEXITED | os.WNOHANG | os.WNOWAIT


class MutationProcessController:
    """Pump one trusted command while its session-leader identity stays anchored."""

    def __init__(
        self, process: subprocess.Popen[bytes], selector: selectors.BaseSelector,
        mutation_input: bytes | None, waitid_options: int,
    ) -> None:
        self.process = process
        self.selector = selector
        self.waitid_options = waitid_options
        self.pending_input = memoryview(mutation_input or b"")
        self.input_offset = 0
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.streams: dict[str, Any] = {}
        self.leader_exit_observed = False
        self.group_actions_closed = False
        self.leader_reaped = False

    def configure_pipes(self) -> None:
        streams = {
            "stdin": self.process.stdin,
            "stdout": self.process.stdout,
            "stderr": self.process.stderr,
        }
        if any(stream is None for stream in streams.values()):
            raise MutationProcessGroupFenceError(
                "mutation child pipes were not created"
            )
        for name, stream in streams.items():
            assert stream is not None
            os.set_blocking(stream.fileno(), False)
            self.streams[name] = stream
            event = selectors.EVENT_WRITE if name == "stdin" else selectors.EVENT_READ
            self.selector.register(stream, event, name)
        if not self.pending_input:
            self.close_stream("stdin")

    def close_stream(self, name: str) -> None:
        stream = self.streams.pop(name, None)
        if stream is None:
            return
        try:
            self.selector.unregister(stream)
        except (KeyError, ValueError):
            pass
        try:
            stream.close()
        except BrokenPipeError:
            pass

    def close(self) -> None:
        for name in tuple(self.streams):
            self.close_stream(name)
        self.selector.close()

    def pump_pipes(self, timeout_seconds: float) -> None:
        if not self.selector.get_map():
            if timeout_seconds > 0:
                time.sleep(timeout_seconds)
            return
        try:
            events = self.selector.select(timeout_seconds)
        except InterruptedError:
            return
        for key, _mask in events:
            name = key.data
            stream = key.fileobj
            descriptor = stream.fileno()
            if name == "stdin":
                try:
                    written = os.write(
                        descriptor,
                        self.pending_input[self.input_offset:self.input_offset + 65536],
                    )
                except BrokenPipeError:
                    self.close_stream(name)
                    continue
                except OSError as exc:
                    if exc.errno == errno.EPIPE:
                        self.close_stream(name)
                        continue
                    raise
                self.input_offset += written
                if self.input_offset == len(self.pending_input):
                    self.close_stream(name)
                continue
            try:
                chunk = os.read(descriptor, 65536)
            except BlockingIOError:
                continue
            if not chunk:
                self.close_stream(name)
            elif name == "stdout":
                self.stdout.extend(chunk)
            else:
                self.stderr.extend(chunk)

    def observe_leader_exit(self) -> bool:
        if self.leader_exit_observed:
            return True
        if self.group_actions_closed or self.leader_reaped:
            raise MutationProcessGroupFenceError(
                "leader exit observation was attempted after group fencing closed"
            )
        if self.process.returncode is not None:
            raise MutationProcessGroupFenceError(
                "mutation session leader was reaped before process-group fencing"
            )
        try:
            result = os.waitid(
                os.P_PID, self.process.pid, self.waitid_options,
            )
        except InterruptedError:
            return False
        except ChildProcessError as exc:
            raise MutationProcessGroupFenceError(
                "mutation session leader lost its non-reaped identity anchor"
            ) from exc
        if result is None or result.si_pid == 0:
            return False
        if result.si_pid != self.process.pid:
            raise MutationProcessGroupFenceError(
                "waitid returned a foreign mutation process"
            )
        self.leader_exit_observed = True
        return True

    def signal_group(self, signum: int) -> None:
        if self.group_actions_closed or self.leader_reaped:
            raise MutationProcessGroupFenceError(
                "process-group action was attempted after leader reap began"
            )
        try:
            os.killpg(self.process.pid, signum)
        except ProcessLookupError:
            pass
        except PermissionError as exc:
            # macOS reports EPERM for a group containing only an owned zombie
            # leader. WNOWAIT still anchors that identity, so there is no live
            # same-group process left to signal in this trusted-command model.
            if not self.leader_exit_observed:
                raise MutationProcessGroupFenceError(
                    "private mutation process group cannot be signalled"
                ) from exc

    def pump_for(self, timeout_seconds: float) -> None:
        deadline = time.monotonic() + timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            self.pump_pipes(min(0.05, remaining))
            self.observe_leader_exit()

    def reap_leader(self) -> int:
        if not self.group_actions_closed:
            raise MutationProcessGroupFenceError(
                "mutation session leader reap preceded process-group fencing"
            )
        if self.leader_reaped:
            if self.process.returncode is None:
                raise MutationProcessGroupFenceError(
                    "mutation session leader return code is unavailable"
                )
            return self.process.returncode
        try:
            returncode = self.process.wait(timeout=1)
        except subprocess.TimeoutExpired as exc:
            raise MutationProcessGroupFenceError(
                "mutation session leader could not be reaped after SIGKILL"
            ) from exc
        except ChildProcessError as exc:
            raise MutationProcessGroupFenceError(
                "mutation session leader was reaped outside the controller"
            ) from exc
        self.leader_reaped = True
        return returncode

    def drain_after_reap(self, timeout_seconds: float = 1) -> None:
        deadline = time.monotonic() + timeout_seconds
        while "stdout" in self.streams or "stderr" in self.streams:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MutationProcessGroupFenceError(
                    "mutation child pipes remained open after group SIGKILL"
                )
            self.pump_pipes(min(0.05, remaining))

    def fence_and_reap(
        self, grace_seconds: float = 2, kill_grace_seconds: float = 2,
    ) -> tuple[int, bytes, bytes]:
        self.close_stream("stdin")
        if not self.group_actions_closed:
            self.signal_group(signal.SIGTERM)
            self.pump_for(grace_seconds)
            self.signal_group(signal.SIGKILL)
            deadline = time.monotonic() + kill_grace_seconds
            post_kill_cycle = False
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self.pump_pipes(min(0.05, remaining))
                post_kill_cycle = True
                self.observe_leader_exit()
                if (
                    post_kill_cycle
                    and self.leader_exit_observed
                    and "stdout" not in self.streams
                    and "stderr" not in self.streams
                ):
                    break
            if not self.leader_exit_observed:
                raise MutationProcessGroupFenceError(
                    "mutation session leader survived process-group SIGKILL"
                )
            self.group_actions_closed = True
        returncode = self.reap_leader()
        self.drain_after_reap()
        return returncode, bytes(self.stdout), bytes(self.stderr)


def run_mutation_process(
    command: list[str], environment: dict[str, str], mutation_input: bytes | None,
    on_start: Callable[[subprocess.Popen[bytes]], None],
    termination_requested: Callable[[], bool],
) -> subprocess.CompletedProcess[bytes]:
    require(
        mutation_input is None or len(mutation_input) <= 1024 * 1024,
        "mutation input must not exceed 1 MiB",
    )
    waitid_options = require_nonreaping_waitid()
    selector = selectors.DefaultSelector()
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0, text=False, env=environment,
            start_new_session=True,
        )
    except BaseException:
        selector.close()
        raise
    controller = MutationProcessController(
        process, selector, mutation_input, waitid_options,
    )
    try:
        controller.configure_pipes()
        on_start(process)
        while not controller.observe_leader_exit() and not termination_requested():
            controller.pump_pipes(0.05)
        returncode, stdout, stderr = controller.fence_and_reap()
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)
    except BaseException as error:
        try:
            controller.fence_and_reap()
        except BaseException as cleanup_error:
            if isinstance(error, MutationProcessGroupFenceError):
                raise error
            if isinstance(cleanup_error, MutationProcessGroupFenceError):
                raise cleanup_error from error
            raise MutationProcessGroupFenceError(
                "mutation process cleanup was interrupted"
            ) from cleanup_error
        raise
    finally:
        controller.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkout", type=Path)
    parser.add_argument("plan_dir", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--authorize-issue")
    mode.add_argument("--verify-claim")
    mode.add_argument("--renew-claim")
    mode.add_argument("--release-claim")
    mode.add_argument("--fenced-gh-api")
    mode.add_argument("--verify-anchor-only", action="store_true")
    mode.add_argument("--self-test-trusted-tools", action="store_true")
    parser.add_argument("--github-issue-number", type=int)
    parser.add_argument("--claim-run-id")
    parser.add_argument("--claim-sha")
    parser.add_argument("--claim-owner-secret-file", type=Path)
    parser.add_argument("--plan-head-sha")
    parser.add_argument("--authorization-contract-sha256")
    parser.add_argument("--authorization-evidence", type=Path)
    parser.add_argument("--model-router", type=Path)
    parser.add_argument("--model-routing-policy", type=Path)
    parser.add_argument(
        "--mutation-method", choices=("POST", "PATCH", "PUT", "DELETE")
    )
    parser.add_argument("--mutation-endpoint")
    parser.add_argument("--mutation-input", type=Path)
    parser.add_argument("--mutation-capability", choices=(
        "selected-issue-comment", "selected-issue-labels", "issue-pull-create",
        "create-public-repository",
    ))
    args = parser.parse_args()
    try:
        checkout = args.checkout.resolve()
        caller_checkout = checkout
        plan_dir = args.plan_dir.resolve()
        with tempfile.TemporaryDirectory(prefix="fmv3-anchor-launcher-") as temporary:
            root = Path(temporary)
            root.chmod(0o700)
            tools = materialize_trusted_tools(root / "tools")
            if args.self_test_trusted_tools:
                print("PASS: trusted Git and GitHub CLI materialized from the platform allowlist")
                return 0
            require(
                plan_dir == checkout / Path(PLAN_PATH).parent,
                "plan_dir is not the canonical FMV3 lifecycle directory",
            )
            require(
                isinstance(args.plan_head_sha, str)
                and re.fullmatch(r"[0-9a-f]{40}", args.plan_head_sha) is not None,
                "--plan-head-sha is required for anchor authentication",
            )
            checkout = materialize_canonical_checkout(tools, root / "canonical-main")
            plan_dir = checkout / Path(PLAN_PATH).parent
            canonical_main = require_canonical_checkout(tools, checkout)
            authenticate_anchor(tools, args.plan_head_sha, canonical_main)
            git(
                tools,
                checkout,
                "merge-base",
                "--is-ancestor",
                args.plan_head_sha,
                canonical_main,
            )
            validator, digest = load_anchored_validator(
                tools, checkout, args.plan_head_sha
            )
            if args.verify_anchor_only:
                print(f"PASS: PR #91 anchor {args.plan_head_sha} authenticated on canonical main")
                return 0
            selected_issue = (
                args.authorize_issue or args.verify_claim
                or args.renew_claim or args.release_claim or args.fenced_gh_api
            )
            routing_arguments: list[str] = []
            if args.authorize_issue is not None:
                router_source = (
                    args.model_router.resolve()
                    if args.model_router is not None
                    else caller_checkout.parent / ".codex" / "scripts" / "model_route.py"
                )
                policy_source = (
                    args.model_routing_policy.resolve()
                    if args.model_routing_policy is not None
                    else caller_checkout.parent / ".codex" / "model-routing-policy.json"
                )
                receipt, receipt_sha256 = build_routing_receipt(
                    plan_dir, selected_issue, args.plan_head_sha,
                    router_source, policy_source, root / "model-routing",
                )
                routing_arguments = [
                    "--routing-receipt-base64", receipt,
                    "--routing-receipt-sha256", receipt_sha256,
                ]
            else:
                require(
                    args.model_router is None and args.model_routing_policy is None,
                    "model-routing paths are valid only with --authorize-issue",
                )
            process_lock = acquire_claim_process_lock()
            try:
                claim_owner_secret, secret_lock = lock_claim_owner_secret(
                    args.claim_owner_secret_file
                )
                try:
                    require(
                        isinstance(selected_issue, str) and selected_issue
                        and type(args.github_issue_number) is int
                        and args.github_issue_number > 0
                        and isinstance(args.claim_run_id, str)
                        and re.fullmatch(
                            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                            args.claim_run_id,
                        ) is not None
                        and isinstance(args.authorization_contract_sha256, str)
                        and re.fullmatch(
                            r"[0-9a-f]{64}", args.authorization_contract_sha256
                        ) is not None,
                        "claim mode requires exact issue, claim run, and contract arguments",
                    )
                    exact_fence_mode = any(value is not None for value in (
                        args.verify_claim, args.renew_claim,
                        args.release_claim, args.fenced_gh_api,
                    ))
                    if exact_fence_mode:
                        require(
                            isinstance(args.claim_sha, str)
                            and re.fullmatch(r"[0-9a-f]{40}", args.claim_sha)
                            is not None,
                            "verify, renew, release, and fenced mutation require "
                            "the exact acquired --claim-sha",
                        )
                    else:
                        require(
                            args.claim_sha is None,
                            "--claim-sha is valid only with verify, renew, release, "
                            "or fenced mutation",
                        )
                    if args.fenced_gh_api is None:
                        require(
                            args.mutation_method is None
                            and args.mutation_endpoint is None
                            and args.mutation_input is None
                            and args.mutation_capability is None,
                            "mutation arguments are valid only with --fenced-gh-api",
                        )
                    else:
                        require(
                            args.mutation_method is not None
                            and isinstance(args.mutation_endpoint, str)
                            and isinstance(args.mutation_capability, str),
                            "--fenced-gh-api requires capability, method, and endpoint",
                        )
                    validator_mode = (
                        "--authorize-issue" if args.authorize_issue
                        else "--verify-claim" if (
                            args.verify_claim or args.fenced_gh_api
                        )
                        else "--renew-claim" if args.renew_claim
                        else "--release-claim"
                    )
                    validator_arguments = [
                        str(plan_dir),
                        validator_mode,
                        selected_issue,
                        "--github-issue-number",
                        str(args.github_issue_number),
                        "--claim-run-id",
                        args.claim_run_id,
                        "--plan-head-sha",
                        args.plan_head_sha,
                        "--authorization-contract-sha256",
                        args.authorization_contract_sha256,
                    ]
                    if args.authorization_evidence is not None:
                        validator_arguments.extend([
                            "--authorization-evidence",
                            str(args.authorization_evidence.resolve()),
                        ])
                    if args.claim_sha is not None:
                        validator_arguments.extend(["--claim-sha", args.claim_sha])
                    validator_arguments.extend(routing_arguments)
                    if args.fenced_gh_api is None:
                        return execute_materialized_validator(
                            validator, digest, validator_arguments,
                            tools.git, tools.gh, root, claim_owner_secret,
                        )
                    plan = yaml.safe_load((plan_dir / "plan.yaml").read_text(
                        encoding="utf-8"
                    ))
                    matching = [
                        issue for issue in plan.get("issues", [])
                        if isinstance(issue, dict)
                        and issue.get("id") == selected_issue
                    ] if isinstance(plan, dict) else []
                    require(
                        len(matching) == 1
                        and isinstance(matching[0].get("repo"), str),
                        "fenced mutation issue repository is ambiguous",
                    )
                    endpoint = str(args.mutation_endpoint)
                    mutation_input = materialize_mutation_input(
                        args.mutation_input, root / "mutation-input.json"
                    )
                    mutation_input_bytes = (
                        mutation_input.read_bytes()
                        if mutation_input is not None else None
                    )
                    require_mutation_capability(
                        matching[0], args.github_issue_number,
                        args.mutation_capability, args.mutation_method,
                        endpoint, mutation_input_bytes,
                    )
                    fenced_head: str | None = None
                    if args.mutation_capability == "issue-pull-create":
                        payload = mutation_payload(
                            mutation_input_bytes, args.mutation_capability,
                        )
                        head = payload.get("head")
                        require(
                            isinstance(head, str),
                            "fenced pull-request mutation lacks an exact head",
                        )
                        fenced_head = head
                    fenced_snapshot_arguments = [
                        "--fenced-mutation-capability",
                        args.mutation_capability,
                    ]
                    if fenced_head is not None:
                        fenced_snapshot_arguments.extend([
                            "--fenced-mutation-head", fenced_head,
                        ])
                    preflight_arguments = validator_arguments + [
                        "--fenced-mutation-phase", "preflight",
                    ] + fenced_snapshot_arguments
                    preflight = execute_materialized_validator(
                        validator, digest, preflight_arguments,
                        tools.git, tools.gh, root, claim_owner_secret,
                    )
                    if preflight != 0:
                        return preflight
                    postflight_arguments = validator_arguments + [
                        "--fenced-mutation-phase", "postflight",
                    ] + fenced_snapshot_arguments
                    command = [
                        str(tools.gh[0]), "api", "--hostname", "github.com",
                        "--method", str(args.mutation_method), endpoint,
                    ]
                    if mutation_input_bytes is not None:
                        command.extend(["--input", "-"])
                    environment = {
                        name: os.environ[name]
                        for name in (
                            "HOME", "GH_TOKEN", "GITHUB_TOKEN", "LANG", "LC_ALL",
                        )
                        if os.environ.get(name)
                    }
                    return execute_fenced_github_operation(
                        command, environment, validator, digest,
                        postflight_arguments, tools, root, claim_owner_secret,
                        mutation_input_bytes,
                    )
                finally:
                    fcntl.flock(secret_lock, fcntl.LOCK_UN)
                    os.close(secret_lock)
            finally:
                process_lock.close()
    except (LauncherError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
