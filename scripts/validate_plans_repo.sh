#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TOKEN_VENV="${TMPDIR:-/tmp}/helianthus-plans-tokenenv"
if [ ! -x "$TOKEN_VENV/bin/python" ]; then
  python3 -m venv "$TOKEN_VENV"
  "$TOKEN_VENV/bin/pip" install -q pyyaml tiktoken >/dev/null
fi

NODE_DIR="${TMPDIR:-/tmp}/helianthus-plans-node"
if [ ! -d "$NODE_DIR/node_modules/@anthropic-ai/tokenizer" ]; then
  mkdir -p "$NODE_DIR"
  (
    cd "$NODE_DIR"
    npm init -y >/dev/null 2>&1
    npm install --silent @anthropic-ai/tokenizer >/dev/null 2>&1
  )
fi

ROOT="$ROOT" NODE_PATH="$NODE_DIR/node_modules" "$TOKEN_VENV/bin/python" - <<'PY'
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import tiktoken
import yaml

ROOT = Path(os.environ["ROOT"])
NODE_PATH = os.environ["NODE_PATH"]
STATE_RE = re.compile(r"^(?P<slug>.+)\.(?P<state>locked|implementing|maintenance)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_KEYS = [
    "slug",
    "title",
    "state",
    "source_discussion",
    "target_repos",
    "knowledge_repo",
    "canonical_file",
    "split_index",
    "started_on",
    "current_milestone",
]
REQUIRED_HEADERS = [
    "Depends on:",
    "Scope:",
    "Idempotence contract:",
    "Falsifiability gate:",
    "Coverage:",
]
GPT_LIMIT = 10000
CLAUDE_LIMIT = 10000
enc = tiktoken.get_encoding("o200k_base")


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def claude_tokens(path: Path) -> int:
    js = """
const fs = require('fs');
const { countTokens } = require('@anthropic-ai/tokenizer');
const txt = fs.readFileSync(process.argv[1], 'utf8');
process.stdout.write(String(countTokens(txt)));
"""
    result = subprocess.run(
        ["node", "-e", js, str(path)],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "NODE_PATH": NODE_PATH},
    )
    return int(result.stdout.strip())


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"{path}: plan.yaml must contain a mapping")
    return data


plan_dirs = sorted(p for p in ROOT.iterdir() if p.is_dir() and STATE_RE.match(p.name))
if not plan_dirs:
    fail("no plan directories found")

slug_to_dir = {}
for plan_dir in plan_dirs:
    match = STATE_RE.match(plan_dir.name)
    assert match is not None
    slug = match.group("slug")
    state = match.group("state")
    if slug in slug_to_dir:
        fail(f"multiple active plan directories found for slug '{slug}'")
    slug_to_dir[slug] = plan_dir

    required_files = [
        "plan.yaml",
        "00-canonical.md",
        "01-index.md",
        "90-issue-map.md",
        "91-milestone-map.md",
        "99-status.md",
    ]
    for rel in required_files:
        if not (plan_dir / rel).is_file():
            fail(f"{plan_dir.name}: missing required file {rel}")

    chunk_files = sorted(plan_dir.glob("1[0-9]-*.md"))
    if not chunk_files:
        fail(f"{plan_dir.name}: missing chunk files matching 1[0-9]-*.md")

    meta = load_yaml(plan_dir / "plan.yaml")
    for key in REQUIRED_KEYS:
        if key not in meta:
            fail(f"{plan_dir.name}: plan.yaml missing key '{key}'")

    if meta["slug"] != slug:
        fail(f"{plan_dir.name}: plan.yaml slug '{meta['slug']}' does not match directory slug '{slug}'")
    if meta["state"] != state:
        fail(f"{plan_dir.name}: plan.yaml state '{meta['state']}' does not match directory state '{state}'")
    if not isinstance(meta["target_repos"], list) or not meta["target_repos"]:
        fail(f"{plan_dir.name}: target_repos must be a non-empty list")
    if not DATE_RE.match(str(meta["started_on"])):
        fail(f"{plan_dir.name}: started_on must use YYYY-MM-DD")

    canonical = plan_dir / str(meta["canonical_file"])
    index = plan_dir / str(meta["split_index"])
    if canonical.name != "00-canonical.md":
        fail(f"{plan_dir.name}: canonical_file must be 00-canonical.md")
    if index.name != "01-index.md":
        fail(f"{plan_dir.name}: split_index must be 01-index.md")
    if not canonical.is_file():
        fail(f"{plan_dir.name}: canonical file not found: {canonical.name}")
    if not index.is_file():
        fail(f"{plan_dir.name}: split index not found: {index.name}")

    canonical_hash = sha256(canonical)
    expected_hash_line = f"Canonical-SHA256: `{canonical_hash}`"

    index_text = index.read_text(encoding="utf-8")
    if expected_hash_line not in index_text:
        fail(f"{plan_dir.name}: index hash mismatch")

    for chunk in chunk_files:
        text = chunk.read_text(encoding="utf-8")
        if expected_hash_line not in text:
            fail(f"{plan_dir.name}: chunk hash mismatch in {chunk.name}")
        for header in REQUIRED_HEADERS:
            if re.search(rf"^{re.escape(header)}", text, re.MULTILINE) is None:
                fail(f"{plan_dir.name}: missing header '{header}' in {chunk.name}")
        if chunk.name not in index_text:
            fail(f"{plan_dir.name}: index does not reference {chunk.name}")

        gpt_tokens = len(enc.encode(text))
        if gpt_tokens >= GPT_LIMIT:
            fail(f"{plan_dir.name}: GPT token budget exceeded in {chunk.name} ({gpt_tokens})")

        claude = claude_tokens(chunk)
        if claude >= CLAUDE_LIMIT:
            fail(f"{plan_dir.name}: Claude token budget exceeded in {chunk.name} ({claude})")

        print(f"{plan_dir.name}\t{chunk.name}\tGPT={gpt_tokens}\tClaude={claude}")

print(f"validated {len(plan_dirs)} plan(s)")
PY
