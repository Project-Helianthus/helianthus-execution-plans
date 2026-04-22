# Vaillant B503 Namespace — Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `896a82e720b33eefb449ea532570e0a962bfa76504519996825f13d92ec9bb28`

Revision: `v1.0-locked`

This directory contains the canonical `vaillant/b503` plan plus a lossless execution-oriented split into reviewable chunks.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk stays below `10000` tokens on both the GPT-5-family tokenizer and the Claude tokenizer.
- Each chunk repeats `Depends on`, `Scope`, `Idempotence contract`, `Falsifiability gate`, `Coverage`.
- The split is lossless: canonical content maps once to a chunk, except for the dependency repetition needed for isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical hash of `00-canonical.md`.

## Sequencing Rules

- Default review order: `10-scope-decisions.md` → `11-execution-safety-and-surfaces.md` → `12-milestones-issues-acceptance.md`.
- Chunks are NOT merge units; milestones (see `91-milestone-map.md`) drive PR ordering.

## Files

| File | Purpose |
|---|---|
| [00-canonical.md](./00-canonical.md) | Canonical plan (source of truth) |
| [01-index.md](./01-index.md) | This index |
| [10-scope-decisions.md](./10-scope-decisions.md) | Scope bounds + Locked Decisions AD01..AD15 + adversarial provenance |
| [11-execution-safety-and-surfaces.md](./11-execution-safety-and-surfaces.md) | Invoke safety classification, live-monitor session model, capability signal contract, MCP→GraphQL→consumer rollout gating |
| [12-milestones-issues-acceptance.md](./12-milestones-issues-acceptance.md) | Per-milestone scope, routing, complexity, dependencies, acceptance criteria |
| [90-issue-map.md](./90-issue-map.md) | Issue ↔ milestone map (populated as issues open) |
| [91-milestone-map.md](./91-milestone-map.md) | Milestone table with primary repo + status |
| [99-status.md](./99-status.md) | Live status tracker |
