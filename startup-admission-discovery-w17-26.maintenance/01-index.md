# Startup Admission + Discovery — Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `c3b2fb00c75c8ebc02de12ba6c7526b216f714f2be4a38d77890e4776c5f4fcf`

Revision: `v1.0-locked`

This directory contains the canonical plan plus a lossless execution-oriented split into reviewable chunks.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk stays below 10000 tokens on both the GPT-5-family tokenizer and the Claude tokenizer.
- Each chunk is reviewable in isolation and repeats: `Depends on`, `Scope`, `Idempotence contract`, `Falsifiability gate`, `Coverage`.
- The split is lossless: canonical content maps once to a chunk, except for the dependency repetition needed for isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical hash of `00-canonical.md`.

## Sequencing Rules

- Default dependency order (merge): `M0 → M1 → M2 → M2a → M3 → M4 → M5 → M6 → M7`.
- `merge_depends_on` uses transitive closure across the stacked PR set per AD14.
- `M2a_GATEWAY_OFFLINE_HARNESS` is merge-blocking for `M3_GATEWAY_STARTUP_ORDER_FLIP` and all downstream gateway milestones.
- Doc-gate tier 1 (`docs-ebus` open-for-review) blocks M2..M6 merge; tier 2 (`docs-ebus` merged) blocks M7 merge.

## Chunk Map

| Chunk | Focus |
|---|---|
| [10-scope-and-problem.md](./10-scope-and-problem.md) | Summary, scope, hard out-of-scope, normative anchors |
| [11-milestones-and-coordination.md](./11-milestones-and-coordination.md) | Milestones M0..M7 (incl. M2a), coordination, PR strategy, rebase protocol |
| [12-decision-matrix.md](./12-decision-matrix.md) | Locked decisions AD01..AD23 |
| [13-configuration-and-acceptance.md](./13-configuration-and-acceptance.md) | Configuration surfaces, falsifiable acceptance, bus-load budget, transport matrix, glossary, commentary |
