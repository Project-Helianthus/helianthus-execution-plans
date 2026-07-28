#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_MANIFEST = pathlib.Path(
    "runtime-gates/fronius-modbus-m1-02-release.json"
)
VALIDATOR_PATH = pathlib.Path("scripts/validate_modbus_m1_02_release.py")
SHA_RE = re.compile(r"[0-9a-f]{40}")
HASH_RE = re.compile(r"[0-9a-f]{64}")
ALLOWED_MODES = {"100644", "100755"}


def _git(
    root: pathlib.Path,
    *args: str,
    binary: bool = False,
) -> bytes | str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(args)} failed: {detail}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", errors="strict").strip()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_regular_root(root: pathlib.Path) -> bool:
    try:
        lexical = root.absolute()
        return (
            lexical.is_dir()
            and not lexical.is_symlink()
            and lexical == lexical.resolve(strict=True)
        )
    except OSError:
        return False


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
        if kind != "blob" or mode not in ALLOWED_MODES:
            raise ValueError(
                f"{revision}: unsupported tree entry {mode} {kind} {path}"
            )
        entries[path] = (mode, object_id)
    return entries


def _blob(root: pathlib.Path, revision: str, path: str) -> bytes:
    value = _git(root, "show", f"{revision}:{path}", binary=True)
    assert isinstance(value, bytes)
    return value


def _validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(manifest) != {
        "attestation",
        "files",
        "post_merge",
        "repository",
        "reviewed_sha",
        "schema",
        "version",
    }:
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
    if manifest.get("attestation") != {
        "anchor_base_ref": "main",
        "anchor_head_ref": "issue/71-m1-02-external-trust",
        "anchor_pull_request": 84,
        "anchor_repository": (
            "Project-Helianthus/helianthus-execution-plans"
        ),
        "context": "adversarial-review",
        "creator_id": 16434603,
        "creator_login": "d3vi1",
        "description_prefix": (
            "OpenAI-only fresh adversarial consensus: NO_FINDINGS"
        ),
        "target": "pull_request_head",
        "target_url": (
            "https://github.com/Project-Helianthus/"
            "helianthus-execution-plans/pull/84"
        ),
    }:
        errors.append("release attestation contract is not exact")
    if manifest.get("post_merge") != {
        "base_ref": "main",
        "head_ref": "issue/5-owned-modbus-tcp-runtime",
        "pull_request": 6,
        "strategy": "squash",
        "target_ref": "refs/remotes/origin/main",
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
        ):
            errors.append(f"unsafe manifest path: {path}")
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


def validate_anchor(
    anchor_root: pathlib.Path,
    manifest_path: pathlib.Path,
) -> tuple[str | None, str | None, list[str]]:
    errors: list[str] = []
    if not _strict_regular_root(anchor_root):
        return None, None, ["anchor root must be a regular directory"]
    try:
        anchor_sha = str(_git(anchor_root, "rev-parse", "HEAD"))
        if SHA_RE.fullmatch(anchor_sha) is None:
            errors.append("anchor HEAD must be lowercase 40-hex SHA")
            return None, None, errors
        anchor_tree = str(
            _git(anchor_root, "rev-parse", f"{anchor_sha}^{{tree}}")
        )
        if _git(anchor_root, "status", "--porcelain", "--untracked-files=all"):
            errors.append("anchor checkout is dirty")
        ignored = _git(
            anchor_root,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
        )
        if ignored:
            errors.append("anchor checkout contains ignored files")
        relative_manifest = manifest_path.resolve(strict=True).relative_to(
            anchor_root.resolve(strict=True)
        )
        for relative in (VALIDATOR_PATH, relative_manifest):
            current = anchor_root / relative
            if not current.is_file() or current.is_symlink():
                errors.append(f"anchor protected path is not regular: {relative}")
                continue
            if current.read_bytes() != _blob(
                anchor_root,
                anchor_sha,
                relative.as_posix(),
            ):
                errors.append(f"anchor protected path differs from HEAD: {relative}")
        return anchor_sha, anchor_tree, errors
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        return None, None, errors


def validate_release(
    candidate_root: pathlib.Path,
    manifest: dict[str, Any],
) -> list[str]:
    errors = _validate_manifest(manifest)
    if errors:
        return errors
    if not _strict_regular_root(candidate_root):
        return ["candidate root must be a regular directory"]
    reviewed_sha = manifest["reviewed_sha"]
    files = manifest["files"]
    try:
        head = str(_git(candidate_root, "rev-parse", "HEAD"))
        if head != reviewed_sha:
            errors.append(
                f"candidate HEAD is not exact reviewed SHA: {head}"
            )
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
        tree = _tree(candidate_root, reviewed_sha)
        if set(tree) != set(files):
            missing = sorted(set(files) - set(tree))
            extra = sorted(set(tree) - set(files))
            errors.append(
                f"reviewed tree inventory mismatch: missing={missing} extra={extra}"
            )
        for path, descriptor in files.items():
            entry = tree.get(path)
            if entry is None:
                continue
            if entry[0] != descriptor["mode"]:
                errors.append(f"reviewed mode mismatch: {path}")
            if _sha256(_blob(candidate_root, reviewed_sha, path)) != descriptor[
                "sha256"
            ]:
                errors.append(f"reviewed content mismatch: {path}")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def validate_attestation_payload(
    statuses: object,
    manifest: dict[str, Any],
    anchor_head: str,
    anchor_tree: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(statuses, list):
        return ["commit statuses payload must be a list"]
    contract = manifest["attestation"]
    matching = [
        status
        for status in statuses
        if isinstance(status, dict)
        and status.get("context") == contract["context"]
    ]
    if not matching:
        return ["required adversarial-review status is missing"]
    latest = matching[0]
    creator = latest.get("creator")
    expected_description = (
        f"{contract['description_prefix']} h={anchor_head} t={anchor_tree}"
    )
    if latest.get("state") != "success":
        errors.append("latest adversarial-review status is not success")
    if latest.get("description") != expected_description:
        errors.append("adversarial-review description is not exact")
    if latest.get("target_url") != contract["target_url"]:
        errors.append("adversarial-review target URL is not exact")
    if not isinstance(creator, dict):
        errors.append("adversarial-review creator is missing")
    elif (
        creator.get("login") != contract["creator_login"]
        or creator.get("id") != contract["creator_id"]
    ):
        errors.append("adversarial-review creator identity is not exact")
    return errors


def _github_json_pages(url: str, token: str) -> list[object]:
    values: list[object] = []
    expected = urllib.parse.urlparse(url)
    while url:
        parsed = urllib.parse.urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "api.github.com"
            or parsed.path != expected.path
        ):
            raise ValueError("GitHub pagination URL escaped the expected endpoint")
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
            if not isinstance(payload, list):
                raise ValueError("paginated GitHub response must be a list")
            values.extend(payload)
            link = response.headers.get("Link", "")
        url = ""
        for part in link.split(","):
            match = re.fullmatch(
                r'\s*<([^>]+)>;\s*rel="([^"]+)"\s*',
                part,
            )
            if match is not None and match.group(2) == "next":
                url = match.group(1)
                break
    return values


def _fetch_statuses(manifest: dict[str, Any], token: str) -> list[object]:
    repository = manifest["repository"]
    reviewed_sha = manifest["reviewed_sha"]
    return _github_json_pages(
        (
            f"https://api.github.com/repos/{repository}/commits/"
            f"{reviewed_sha}/statuses?per_page=100"
        ),
        token,
    )


def _github_json(url: str, token: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _fetch_pull_request(manifest: dict[str, Any], token: str) -> object:
    repository = manifest["repository"]
    number = manifest["post_merge"]["pull_request"]
    return _github_json(
        f"https://api.github.com/repos/{repository}/pulls/{number}",
        token,
    )


def _fetch_anchor_pull_request(
    manifest: dict[str, Any],
    token: str,
) -> object:
    contract = manifest["attestation"]
    return _github_json(
        (
            f"https://api.github.com/repos/{contract['anchor_repository']}/"
            f"pulls/{contract['anchor_pull_request']}"
        ),
        token,
    )


def _fetch_commit(repository: str, sha: str, token: str) -> object:
    return _github_json(
        f"https://api.github.com/repos/{repository}/git/commits/{sha}",
        token,
    )


def validate_pull_request_head_payload(
    payload: object,
    manifest: dict[str, Any],
) -> list[str]:
    if not isinstance(payload, dict):
        return ["Modbus pull request payload must be an object"]
    errors: list[str] = []
    contract = manifest["post_merge"]
    head = payload.get("head")
    base = payload.get("base")
    if payload.get("number") != contract["pull_request"]:
        errors.append("Modbus pull request number is not exact")
    if not isinstance(head, dict):
        errors.append("Modbus pull request head is missing")
    else:
        if head.get("ref") != contract["head_ref"]:
            errors.append("Modbus pull request head ref is not exact")
        if head.get("sha") != manifest["reviewed_sha"]:
            errors.append("live Modbus PR head is not the reviewed SHA")
        head_repo = head.get("repo")
        if (
            not isinstance(head_repo, dict)
            or head_repo.get("full_name") != manifest["repository"]
        ):
            errors.append("Modbus pull request head repository is not exact")
    if not isinstance(base, dict):
        errors.append("Modbus pull request base is missing")
    else:
        if base.get("ref") != contract["base_ref"]:
            errors.append("Modbus pull request base ref is not exact")
        base_repo = base.get("repo")
        if (
            not isinstance(base_repo, dict)
            or base_repo.get("full_name") != manifest["repository"]
        ):
            errors.append("Modbus pull request base repository is not exact")
    return errors


def validate_anchor_review_payload(
    pull_request: object,
    commit: object,
    manifest: dict[str, Any],
    anchor_tree: str,
) -> list[str]:
    if not isinstance(pull_request, dict):
        return ["anchor pull request payload must be an object"]
    if not isinstance(commit, dict):
        return ["anchor commit payload must be an object"]
    errors: list[str] = []
    contract = manifest["attestation"]
    head = pull_request.get("head")
    base = pull_request.get("base")
    if pull_request.get("number") != contract["anchor_pull_request"]:
        errors.append("anchor pull request number is not exact")
    if not isinstance(head, dict):
        errors.append("anchor pull request head is missing")
        head_sha = None
    else:
        head_sha = head.get("sha")
        if head.get("ref") != contract["anchor_head_ref"]:
            errors.append("anchor pull request head ref is not exact")
        head_repo = head.get("repo")
        if (
            not isinstance(head_repo, dict)
            or head_repo.get("full_name") != contract["anchor_repository"]
        ):
            errors.append("anchor pull request head repository is not exact")
    if not isinstance(base, dict):
        errors.append("anchor pull request base is missing")
    else:
        if base.get("ref") != contract["anchor_base_ref"]:
            errors.append("anchor pull request base ref is not exact")
        base_repo = base.get("repo")
        if (
            not isinstance(base_repo, dict)
            or base_repo.get("full_name") != contract["anchor_repository"]
        ):
            errors.append("anchor pull request base repository is not exact")
    if commit.get("sha") != head_sha:
        errors.append("anchor commit is not the reviewed PR head")
    tree = commit.get("tree")
    if not isinstance(tree, dict) or tree.get("sha") != anchor_tree:
        errors.append("local anchor tree is not the reviewed PR-head tree")
    return errors


def validate_merge_payload(
    payload: object,
    manifest: dict[str, Any],
    merged_sha: str,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["pull request payload must be an object"]
    errors: list[str] = []
    contract = manifest["post_merge"]
    if payload.get("number") != contract["pull_request"]:
        errors.append("post-merge pull request number is not exact")
    if payload.get("state") != "closed" or payload.get("merged") is not True:
        errors.append("post-merge pull request is not merged and closed")
    if payload.get("merge_commit_sha") != merged_sha:
        errors.append("post-merge SHA is not the GitHub PR merge commit")
    errors.extend(validate_pull_request_head_payload(payload, manifest))
    return errors


def validate_live_attestation(
    manifest: dict[str, Any],
    anchor_tree: str | None,
    token: str,
    merged_sha: str | None = None,
) -> list[str]:
    if not token:
        return ["GH_TOKEN is required to verify attestation"]
    if anchor_tree is None:
        return ["verified external anchor tree is required for attestation"]
    errors: list[str] = []
    try:
        pull_request = _fetch_pull_request(manifest, token)
        errors.extend(
            validate_pull_request_head_payload(pull_request, manifest)
        )
        anchor_pull_request = _fetch_anchor_pull_request(manifest, token)
        anchor_head = (
            anchor_pull_request.get("head")
            if isinstance(anchor_pull_request, dict)
            else None
        )
        anchor_head_sha = (
            anchor_head.get("sha")
            if isinstance(anchor_head, dict)
            else ""
        )
        anchor_commit = _fetch_commit(
            manifest["attestation"]["anchor_repository"],
            anchor_head_sha,
            token,
        )
        errors.extend(
            validate_anchor_review_payload(
                anchor_pull_request,
                anchor_commit,
                manifest,
                anchor_tree,
            )
        )
        errors.extend(
            validate_attestation_payload(
                _fetch_statuses(manifest, token),
                manifest,
                anchor_head_sha,
                anchor_tree,
            )
        )
        if merged_sha is not None:
            errors.extend(
                validate_merge_payload(
                    pull_request,
                    manifest,
                    merged_sha,
                )
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"cannot fetch GitHub attestation: {exc}")
    return errors


def validate_post_merge_tree(
    repository_root: pathlib.Path,
    merged_sha: str,
    attested_pr_head: str,
    expected_attested_pr_head: str,
    target_ref: str,
) -> list[str]:
    errors: list[str] = []
    if not _strict_regular_root(repository_root):
        return ["repository root must be a regular directory"]
    if SHA_RE.fullmatch(merged_sha) is None:
        errors.append("post-merge SHA must be lowercase 40-hex")
    if SHA_RE.fullmatch(attested_pr_head) is None:
        errors.append("attested PR head must be lowercase 40-hex")
    elif attested_pr_head != expected_attested_pr_head:
        errors.append("attested PR head is not the manifest reviewed SHA")
    if errors:
        return errors
    try:
        if _git(repository_root, "cat-file", "-t", merged_sha) != "commit":
            errors.append("post-merge SHA is not a commit")
        if _git(repository_root, "cat-file", "-t", attested_pr_head) != "commit":
            errors.append("attested PR head is not a commit")
        if errors:
            return errors
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository_root),
                "merge-base",
                "--is-ancestor",
                merged_sha,
                target_ref,
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode == 1:
            errors.append("post-merge SHA is not contained in target branch")
        elif result.returncode != 0:
            detail = result.stderr.decode(
                "utf-8",
                errors="replace",
            ).strip()
            raise ValueError(
                f"git merge-base --is-ancestor failed: {detail}"
            )
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True, type=pathlib.Path)
    parser.add_argument("--anchor-root", required=True, type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument("--post-merge-sha")
    args = parser.parse_args()

    script_root = pathlib.Path(__file__).resolve().parents[1]
    manifest_path = (args.manifest or script_root / DEFAULT_MANIFEST).absolute()
    try:
        manifest = _load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"modbus_m1_02_release_invalid: {exc}", file=sys.stderr)
        return 1
    anchor_sha, anchor_tree, errors = validate_anchor(
        args.anchor_root.absolute(),
        manifest_path,
    )

    if args.post_merge_sha is not None:
        errors.extend(
            validate_post_merge_tree(
                args.candidate_root.absolute(),
                args.post_merge_sha,
                manifest["reviewed_sha"],
                manifest["reviewed_sha"],
                manifest["post_merge"]["target_ref"],
            )
        )
    else:
        errors.extend(
            validate_release(args.candidate_root.absolute(), manifest)
        )

    errors.extend(
        validate_live_attestation(
            manifest,
            anchor_tree,
            os.environ.get("GH_TOKEN", ""),
            args.post_merge_sha,
        )
    )

    if errors:
        for error in errors:
            print(f"modbus_m1_02_release_invalid: {error}", file=sys.stderr)
        return 1
    if args.post_merge_sha is not None:
        print(
            "modbus_m1_02_post_merge_ok "
            f"merged_sha={args.post_merge_sha} "
            f"attested_pr_head={manifest['reviewed_sha']}"
        )
    else:
        print(
            "modbus_m1_02_candidate_attestation_ok "
            f"reviewed_sha={manifest['reviewed_sha']} "
            f"anchor_sha={anchor_sha}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
