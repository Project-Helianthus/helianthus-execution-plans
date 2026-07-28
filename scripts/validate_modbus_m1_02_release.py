#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any


DEFAULT_MANIFEST = pathlib.Path(
    "runtime-gates/fronius-modbus-m1-02-release.json"
)
HOOK_PATH = "scripts/validate_external_m1_02.sh"
CI_PATH = "scripts/ci_local.sh"
SHA_RE = re.compile(r"[0-9a-f]{40}")
HASH_RE = re.compile(r"[0-9a-f]{64}")
ALLOWED_MODES = {"100644", "100755"}


def _git(
    root: pathlib.Path,
    *args: str,
    binary: bool = False,
    check: bool = True,
) -> bytes | str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(args)} failed: {detail}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", errors="strict").strip()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_manifest(path: pathlib.Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("release manifest root must be an object")
    canonical = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if raw != canonical:
        raise ValueError("release manifest must use canonical sorted JSON")
    return value


def _tree(root: pathlib.Path, revision: str) -> dict[str, tuple[str, str]]:
    raw = _git(root, "ls-tree", "-r", "-z", revision, binary=True)
    assert isinstance(raw, bytes)
    entries: dict[str, tuple[str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8", errors="strict")
        if kind != "blob":
            raise ValueError(f"{revision}: non-blob tree entry: {path}")
        entries[path] = (mode, object_id)
    return entries


def _blob(root: pathlib.Path, revision: str, path: str) -> bytes:
    value = _git(
        root,
        "show",
        f"{revision}:{path}",
        binary=True,
    )
    assert isinstance(value, bytes)
    return value


def _expected_hook(trust_anchor_sha: str) -> bytes:
    return f"""#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/.." && pwd)"
TRUST_REPOSITORY="https://github.com/Project-Helianthus/helianthus-execution-plans.git"
TRUST_SHA="{trust_anchor_sha}"
ANCHOR_DIR="$(mktemp -d)"
trap 'rm -rf "$ANCHOR_DIR"' EXIT

git init -q "$ANCHOR_DIR"
git -C "$ANCHOR_DIR" fetch --quiet --depth=1 "$TRUST_REPOSITORY" "$TRUST_SHA"
git -C "$ANCHOR_DIR" checkout --quiet --detach FETCH_HEAD
test "$(git -C "$ANCHOR_DIR" rev-parse HEAD)" = "$TRUST_SHA"
python3 "$ANCHOR_DIR/scripts/validate_modbus_m1_02_release.py" \
  --candidate-root "$ROOT" \
  --anchor-root "$ANCHOR_DIR" \
  --trust-anchor-sha "$TRUST_SHA"
""".encode("utf-8")


def _expected_ci(reviewed_ci: bytes) -> bytes:
    marker = b"export PYTHONDONTWRITEBYTECODE=1\n"
    if reviewed_ci.count(marker) != 1:
        raise ValueError("reviewed ci_local.sh has no unique insertion marker")
    addition = marker + b'"$ROOT/scripts/validate_external_m1_02.sh"\n'
    return reviewed_ci.replace(marker, addition, 1)


def _validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_keys = {
        "allowed_child_changes",
        "attestation",
        "files",
        "post_merge",
        "repository",
        "reviewed_sha",
        "schema",
        "version",
    }
    if set(manifest) != required_keys:
        errors.append("release manifest keys are not closed")
    if manifest.get("schema") != "helianthus.modbus.m1-02-release":
        errors.append("release manifest schema is invalid")
    if manifest.get("version") != 1:
        errors.append("release manifest version is invalid")
    if manifest.get("repository") != "Project-Helianthus/helianthus-modbus":
        errors.append("release manifest repository is invalid")
    reviewed_sha = manifest.get("reviewed_sha")
    if not isinstance(reviewed_sha, str) or SHA_RE.fullmatch(reviewed_sha) is None:
        errors.append("reviewed_sha must be lowercase 40-hex")
    if manifest.get("allowed_child_changes") != {
        CI_PATH: "modified",
        HOOK_PATH: "added",
    }:
        errors.append("allowed child changes are not exact")
    if manifest.get("attestation") != {
        "required_context": "adversarial-review",
        "target": "pull_request_head",
        "workflow_permissions": "contents:read",
    }:
        errors.append("release attestation contract is not exact")
    if manifest.get("post_merge") != {
        "strategy": "squash",
        "tree_must_equal_attested_pr_head": True,
    }:
        errors.append("post-merge tree attestation contract is not exact")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        errors.append("release manifest files must be a non-empty object")
        return errors
    for path, descriptor in files.items():
        pure = pathlib.PurePosixPath(path)
        if (
            not isinstance(path, str)
            or pure.is_absolute()
            or ".." in pure.parts
            or path == HOOK_PATH
        ):
            errors.append(f"unsafe or reserved manifest path: {path}")
            continue
        if not isinstance(descriptor, dict) or set(descriptor) != {
            "mode",
            "sha256",
        }:
            errors.append(f"invalid descriptor for {path}")
            continue
        if descriptor.get("mode") not in ALLOWED_MODES:
            errors.append(f"invalid mode for {path}")
        digest = descriptor.get("sha256")
        if not isinstance(digest, str) or HASH_RE.fullmatch(digest) is None:
            errors.append(f"invalid sha256 for {path}")
    return errors


def _validate_anchor(
    anchor_root: pathlib.Path,
    trust_anchor_sha: str,
    manifest_path: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    try:
        if anchor_root.is_symlink() or not anchor_root.is_dir():
            return ["anchor root must be a regular directory"]
        if _git(anchor_root, "rev-parse", "HEAD") != trust_anchor_sha:
            errors.append("anchor checkout HEAD does not equal trust anchor")
        if _git(anchor_root, "status", "--porcelain", "--untracked-files=all"):
            errors.append("anchor checkout is dirty")
        relative_manifest = manifest_path.resolve().relative_to(
            anchor_root.resolve()
        )
        protected = (
            pathlib.Path("scripts/validate_modbus_m1_02_release.py"),
            relative_manifest,
        )
        for relative in protected:
            path = anchor_root / relative
            if not path.is_file() or path.is_symlink():
                errors.append(f"anchor protected path is not regular: {relative}")
                continue
            committed = _blob(
                anchor_root,
                trust_anchor_sha,
                relative.as_posix(),
            )
            if path.read_bytes() != committed:
                errors.append(f"anchor protected path differs from commit: {relative}")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def validate_post_merge_tree(
    repository_root: pathlib.Path,
    merged_sha: str,
    attested_pr_head: str,
) -> list[str]:
    errors: list[str] = []
    if repository_root.is_symlink() or not repository_root.is_dir():
        return ["repository root must be a regular directory"]
    if SHA_RE.fullmatch(merged_sha) is None:
        errors.append("post-merge SHA must be lowercase 40-hex")
    if SHA_RE.fullmatch(attested_pr_head) is None:
        errors.append("attested PR head must be lowercase 40-hex")
    if errors:
        return errors
    try:
        merged_type = _git(repository_root, "cat-file", "-t", merged_sha)
        attested_type = _git(
            repository_root,
            "cat-file",
            "-t",
            attested_pr_head,
        )
        if merged_type != "commit" or attested_type != "commit":
            errors.append("post-merge comparison requires two commit objects")
            return errors
        merged_tree = _git(
            repository_root,
            "rev-parse",
            f"{merged_sha}^{{tree}}",
        )
        attested_tree = _git(
            repository_root,
            "rev-parse",
            f"{attested_pr_head}^{{tree}}",
        )
        if merged_tree != attested_tree:
            errors.append(
                "post-squash main tree does not equal attested PR-head tree"
            )
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def validate_release(
    candidate_root: pathlib.Path,
    manifest: dict[str, Any],
    trust_anchor_sha: str | None,
    allow_reviewed: bool,
) -> list[str]:
    errors = _validate_manifest(manifest)
    if errors:
        return errors
    reviewed_sha = manifest["reviewed_sha"]
    files = manifest["files"]
    try:
        if candidate_root.is_symlink() or not candidate_root.is_dir():
            return ["candidate root must be a regular directory"]
        head = _git(candidate_root, "rev-parse", "HEAD")
        if _git(
            candidate_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        ):
            errors.append("candidate worktree is dirty")
        ignored = _git(
            candidate_root,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
        )
        if ignored:
            errors.append("candidate worktree contains ignored files")
        ancestor = subprocess.run(
            [
                "git",
                "-C",
                str(candidate_root),
                "merge-base",
                "--is-ancestor",
                reviewed_sha,
                head,
            ],
            check=False,
        )
        if ancestor.returncode != 0:
            errors.append("reviewed SHA is not an ancestor of candidate HEAD")

        reviewed_tree = _tree(candidate_root, reviewed_sha)
        if set(reviewed_tree) != set(files):
            missing = sorted(set(files) - set(reviewed_tree))
            extra = sorted(set(reviewed_tree) - set(files))
            errors.append(
                f"reviewed tree inventory mismatch: missing={missing} extra={extra}"
            )
        for path, descriptor in files.items():
            entry = reviewed_tree.get(path)
            if entry is None:
                continue
            mode, _ = entry
            if mode != descriptor["mode"]:
                errors.append(f"reviewed mode mismatch: {path}")
            if _sha256(_blob(candidate_root, reviewed_sha, path)) != descriptor[
                "sha256"
            ]:
                errors.append(f"reviewed content mismatch: {path}")

        current_tree = _tree(candidate_root, head)
        if head == reviewed_sha:
            if not allow_reviewed:
                errors.append("release candidate must be the exact permitted child")
            expected_paths = set(files)
        else:
            parents = str(_git(candidate_root, "rev-list", "--parents", "-n", "1", head)).split()
            if parents != [head, reviewed_sha]:
                errors.append("release candidate must be a direct single-parent child")
            diff_raw = _git(
                candidate_root,
                "diff",
                "--name-status",
                "--no-renames",
                reviewed_sha,
                head,
            )
            actual_changes: dict[str, str] = {}
            status_names = {"A": "added", "M": "modified"}
            for line in str(diff_raw).splitlines():
                status, path = line.split("\t", 1)
                actual_changes[path] = status_names.get(status, status)
            if actual_changes != manifest["allowed_child_changes"]:
                errors.append(
                    f"candidate changes are not exact: {actual_changes}"
                )
            expected_paths = set(files) | {HOOK_PATH}

        if set(current_tree) != expected_paths:
            missing = sorted(expected_paths - set(current_tree))
            extra = sorted(set(current_tree) - expected_paths)
            errors.append(
                f"candidate tree inventory mismatch: missing={missing} extra={extra}"
            )
        for path, descriptor in files.items():
            if path in {CI_PATH, HOOK_PATH}:
                continue
            entry = current_tree.get(path)
            if entry is None:
                continue
            if entry[0] != descriptor["mode"]:
                errors.append(f"candidate mode mismatch: {path}")
            if _sha256(_blob(candidate_root, head, path)) != descriptor["sha256"]:
                errors.append(f"candidate content mismatch: {path}")

        if head != reviewed_sha:
            if trust_anchor_sha is None or SHA_RE.fullmatch(trust_anchor_sha) is None:
                errors.append("exact trust anchor SHA is required for child validation")
            else:
                hook = current_tree.get(HOOK_PATH)
                ci_entry = current_tree.get(CI_PATH)
                if hook is None or hook[0] != "100755":
                    errors.append("external release hook must be executable")
                elif _blob(candidate_root, head, HOOK_PATH) != _expected_hook(
                    trust_anchor_sha
                ):
                    errors.append("external release hook bytes are not exact")
                if ci_entry is None or ci_entry[0] != files[CI_PATH]["mode"]:
                    errors.append("ci_local.sh mode is not preserved")
                elif _blob(candidate_root, head, CI_PATH) != _expected_ci(
                    _blob(candidate_root, reviewed_sha, CI_PATH)
                ):
                    errors.append("ci_local.sh external hook insertion is not exact")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True, type=pathlib.Path)
    parser.add_argument("--anchor-root", type=pathlib.Path)
    parser.add_argument("--trust-anchor-sha")
    parser.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument("--allow-reviewed", action="store_true")
    parser.add_argument("--post-merge-sha")
    parser.add_argument("--attested-pr-head")
    args = parser.parse_args()

    script_root = pathlib.Path(__file__).resolve().parents[1]
    manifest_path = (args.manifest or script_root / DEFAULT_MANIFEST).resolve()
    try:
        manifest = _load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"modbus_m1_02_release_invalid: {exc}", file=sys.stderr)
        return 1

    if (args.post_merge_sha is None) != (args.attested_pr_head is None):
        print(
            "modbus_m1_02_release_invalid: post-merge arguments must be paired",
            file=sys.stderr,
        )
        return 1
    if args.post_merge_sha is not None:
        errors = validate_post_merge_tree(
            args.candidate_root.absolute(),
            args.post_merge_sha,
            args.attested_pr_head,
        )
        if errors:
            for error in errors:
                print(
                    f"modbus_m1_02_release_invalid: {error}",
                    file=sys.stderr,
                )
            return 1
        print(
            "modbus_m1_02_post_merge_ok "
            f"merged_sha={args.post_merge_sha} "
            f"attested_pr_head={args.attested_pr_head}"
        )
        return 0

    errors: list[str] = []
    if args.anchor_root is not None:
        if (
            args.trust_anchor_sha is None
            or SHA_RE.fullmatch(args.trust_anchor_sha) is None
        ):
            errors.append("anchor validation requires lowercase 40-hex SHA")
        else:
            errors.extend(
                _validate_anchor(
                    args.anchor_root.absolute(),
                    args.trust_anchor_sha,
                    manifest_path,
                )
            )
    errors.extend(
        validate_release(
            args.candidate_root.absolute(),
            manifest,
            args.trust_anchor_sha,
            args.allow_reviewed,
        )
    )
    if errors:
        for error in errors:
            print(f"modbus_m1_02_release_invalid: {error}", file=sys.stderr)
        return 1
    print(
        "modbus_m1_02_release_ok "
        f"reviewed_sha={manifest['reviewed_sha']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
