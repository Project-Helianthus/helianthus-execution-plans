#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POST_MERGE_SHA="${1:-}"
export PYTHONDONTWRITEBYTECODE=1

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required for the Modbus M1-02 remote attestation gate." >&2
  exit 1
fi
if [ -z "${GH_TOKEN:-}" ]; then
  GH_TOKEN="$(gh auth token)"
  export GH_TOKEN
fi

canonical_tmp="$(
  python3 - <<'PY'
import tempfile
from pathlib import Path

print(Path(tempfile.gettempdir()).resolve(strict=True))
PY
)"
anchor_root="$ROOT"
anchor_checkout=""
candidate_root=""
cleanup() {
  if [ -n "$candidate_root" ]; then
    rm -rf "$candidate_root"
  fi
  if [ -n "$anchor_checkout" ]; then
    rm -rf "$anchor_checkout"
  fi
}
trap cleanup EXIT

if [ -n "$POST_MERGE_SHA" ]; then
  anchor_merge_sha="$(
    gh api \
      repos/Project-Helianthus/helianthus-execution-plans/pulls/84 \
      --jq 'select(.state == "closed" and .merged == true) | .merge_commit_sha'
  )"
  if [ -z "$anchor_merge_sha" ]; then
    echo "Execution-plans PR #84 is not merged and closed." >&2
    exit 1
  fi
  anchor_checkout="$(
    mktemp -d "$canonical_tmp/modbus-m1-02-anchor.XXXXXX"
  )"
  git init -q "$anchor_checkout"
  git -C "$anchor_checkout" fetch --quiet --depth=1 \
    "https://github.com/Project-Helianthus/helianthus-execution-plans.git" \
    "$anchor_merge_sha"
  git -C "$anchor_checkout" checkout --quiet --detach FETCH_HEAD
  git -C "$anchor_checkout" fetch --quiet \
    "https://github.com/Project-Helianthus/helianthus-execution-plans.git" \
    "+refs/heads/main:refs/remotes/origin/main"
  anchor_root="$anchor_checkout"
fi

MANIFEST="$anchor_root/runtime-gates/fronius-modbus-m1-02-release.json"
reviewed_sha="$(
  python3 - "$MANIFEST" <<'PY'
import json
import sys
from pathlib import Path

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["reviewed_sha"])
PY
)"
live_pr_head="$(
  gh api repos/Project-Helianthus/helianthus-modbus/pulls/6 --jq .head.sha
)"
if [ "$live_pr_head" != "$reviewed_sha" ]; then
  echo "Live Modbus PR #6 head is not the manifest reviewed SHA." >&2
  exit 1
fi

candidate_root="$(mktemp -d "$canonical_tmp/modbus-m1-02-release.XXXXXX")"

git init -q "$candidate_root"
git -C "$candidate_root" fetch --quiet --depth=1 \
  "https://github.com/Project-Helianthus/helianthus-modbus.git" \
  "$reviewed_sha"
git -C "$candidate_root" checkout --quiet --detach FETCH_HEAD

args=(
  --candidate-root "$candidate_root"
  --anchor-root "$anchor_root"
)
if [ -n "$POST_MERGE_SHA" ]; then
  git -C "$candidate_root" fetch --quiet \
    "https://github.com/Project-Helianthus/helianthus-modbus.git" \
    "+refs/heads/main:refs/remotes/origin/main"
  args+=(--post-merge-sha "$POST_MERGE_SHA")
fi

python3 "$anchor_root/scripts/validate_modbus_m1_02_release.py" "${args[@]}"
