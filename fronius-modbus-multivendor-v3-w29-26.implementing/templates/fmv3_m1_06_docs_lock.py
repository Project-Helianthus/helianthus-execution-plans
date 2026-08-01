#!/usr/bin/env python3
"""Verify the M1-06 consumer lock against the merged public docs revision."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
from urllib.request import Request, urlopen


LOCK_PATH = Path(".github/fmv3/opaque-runtime-acquisition-docs-lock.json")
LOCK_SCHEMA = "helianthus.opaque-runtime-acquisition-docs-lock.v1"
DOCS_REPOSITORY = "Project-Helianthus/helianthus-docs-ebus"
DOCS_REMOTE = f"https://github.com/{DOCS_REPOSITORY}.git"
DOCS_PR = 386
CONTRACT_ID = "OPAQUE_RUNTIME_ACQUISITION_V1"
CONTRACT_VERSION = 1
CONTENT_REVISION = 1
POLICY_PATH = "docs/platform/opaque-runtime-acquisition-v1.md"
POLICY_SHA256 = "a95e2ec593a6c06584c06f1486b167c917e756d0af48b83896c51f05e58742d8"
MANIFEST_PATH = "docs/platform/manifests/opaque-runtime-acquisition-v1.json"
MANIFEST_SHA256 = "f692b01c7747bea0a1db3e68440826918e826c0fcc0afac0cde8e580e9a7616c"
LOCK_KEYS = {
    "schema", "repository", "pull_request", "merged_docs_commit_sha",
    "contract_id", "contract_version", "content_revision", "policy_path",
    "policy_sha256", "manifest_path", "manifest_sha256",
}


class LockError(RuntimeError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LockError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LockError(message)


def run_git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_") and key not in {"GH_TOKEN", "GITHUB_TOKEN"}
    }
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1",
    })
    result = subprocess.run(
        [
            "/usr/bin/git", "--no-replace-objects",
            "-c", "credential.helper=", "-c", "core.hooksPath=/dev/null",
            "-C", str(repo), *args,
        ],
        check=False, capture_output=True, text=text, env=environment,
    )
    require(result.returncode == 0, f"git {' '.join(args)} failed")
    return result.stdout


def committed_blob(repo: Path, commit: str, relative: str) -> bytes:
    row = run_git(repo, "ls-tree", commit, "--", relative)
    require(isinstance(row, str) and row.count("\n") == 1, f"missing docs blob: {relative}")
    metadata, separator, observed_path = row.rstrip("\n").partition("\t")
    parts = metadata.split()
    require(
        separator == "\t" and observed_path == relative and len(parts) == 3
        and parts[0] in {"100644", "100755"} and parts[1] == "blob",
        f"docs path is not one regular blob: {relative}",
    )
    blob = run_git(repo, "show", f"{commit}:{relative}", text=False)
    require(isinstance(blob, bytes), f"docs blob read failed: {relative}")
    return blob


def load_lock(root: Path) -> dict[str, Any]:
    path = root / LOCK_PATH
    require(path.is_file() and not path.is_symlink(), "docs lock must be a regular file")
    lock = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(isinstance(lock, dict) and set(lock) == LOCK_KEYS, "docs lock schema is not closed")
    expected = {
        "schema": LOCK_SCHEMA,
        "repository": DOCS_REPOSITORY,
        "pull_request": DOCS_PR,
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "content_revision": CONTENT_REVISION,
        "policy_path": POLICY_PATH,
        "policy_sha256": POLICY_SHA256,
        "manifest_path": MANIFEST_PATH,
        "manifest_sha256": MANIFEST_SHA256,
    }
    require(all(lock.get(key) == value for key, value in expected.items()), "docs lock fields mismatch")
    require(
        isinstance(lock.get("merged_docs_commit_sha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", lock["merged_docs_commit_sha"]) is not None,
        "merged docs commit must be one full lowercase SHA",
    )
    return lock


def verify_github_merge(commit: str) -> None:
    request = Request(
        f"https://api.github.com/repos/{DOCS_REPOSITORY}/pulls/{DOCS_PR}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "helianthus-fmv3-docs-lock-v1"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.load(response, object_pairs_hook=unique_object)
    require(
        isinstance(payload, dict) and payload.get("merged") is True
        and payload.get("merge_commit_sha") == commit,
        "docs lock does not identify the live merged PR #386 commit",
    )


def verify_blobs(commit: str) -> None:
    with tempfile.TemporaryDirectory(prefix="fmv3-docs-lock-") as temporary:
        repo = Path(temporary)
        run_git(repo, "init", "--quiet")
        run_git(repo, "remote", "add", "origin", DOCS_REMOTE)
        run_git(repo, "fetch", "--quiet", "--no-tags", "--depth=1", "origin", commit)
        require(run_git(repo, "rev-parse", "FETCH_HEAD").strip() == commit, "docs fetch SHA mismatch")
        for relative, expected in (
            (POLICY_PATH, POLICY_SHA256), (MANIFEST_PATH, MANIFEST_SHA256),
        ):
            require(
                hashlib.sha256(committed_blob(repo, commit, relative)).hexdigest() == expected,
                f"docs lock SHA-256 mismatch: {relative}",
            )


def main() -> int:
    root = Path.cwd().resolve()
    lock = load_lock(root)
    commit = lock["merged_docs_commit_sha"]
    verify_github_merge(commit)
    verify_blobs(commit)
    print(f"PASS: merged docs lock {commit}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LockError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=__import__("sys").stderr)
        raise SystemExit(1)
