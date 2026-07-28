#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/runtime-gates/fronius-modbus-m1-02-release.json"
POST_MERGE_SHA="${1:-}"
export PYTHONDONTWRITEBYTECODE=1

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required for the Modbus M1-02 remote release gate." >&2
  exit 1
fi
if [ -z "${GH_TOKEN:-}" ]; then
  GH_TOKEN="$(gh auth token)"
  export GH_TOKEN
fi

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

canonical_tmp="$(
  python3 - <<'PY'
import tempfile
from pathlib import Path

print(Path(tempfile.gettempdir()).resolve(strict=True))
PY
)"
candidate_root="$(mktemp -d "$canonical_tmp/modbus-m1-02-release.XXXXXX")"
cleanup() {
  rm -rf "$candidate_root"
}
trap cleanup EXIT

git init -q "$candidate_root"
git -C "$candidate_root" fetch --quiet --depth=1 \
  "https://github.com/Project-Helianthus/helianthus-modbus.git" \
  "$reviewed_sha"
git -C "$candidate_root" checkout --quiet --detach FETCH_HEAD

args=(
  --candidate-root "$candidate_root"
  --anchor-root "$ROOT"
)
if [ -n "$POST_MERGE_SHA" ]; then
  git -C "$candidate_root" fetch --quiet \
    "https://github.com/Project-Helianthus/helianthus-modbus.git" \
    "+refs/heads/main:refs/remotes/origin/main"
  args+=(--post-merge-sha "$POST_MERGE_SHA")
fi

python3 "$ROOT/scripts/validate_modbus_m1_02_release.py" "${args[@]}"
