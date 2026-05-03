# Observe-First Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `956d6ad2957f09906a4eee3f3be733059c0a24d34af4d56ebf61c0553aaeac86`

This directory contains the canonical observability plan plus a lossless
execution-oriented split into sub-10k-token chunks. The split exists so agents
and reviewers can work on bounded, attackable pieces without losing the source
contract.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk must stay below `10000` tokens on both the GPT-5-family tokenizer
  and the Claude tokenizer.
- Each chunk must be reviewable in isolation and repeat:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is lossless: source content is mapped once to a chunk, except for
  intentional dependency repetition needed for isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical
  hash of `00-canonical.md`.
- Repo-local verification runs through
  [`scripts/validate_plans_repo.sh`](../scripts/validate_plans_repo.sh).

## Sequencing Rules

- The default milestone order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M9`.
- `M8` tinyebus is the explicit parallel-track carve-out.
- Locked decisions in the canonical plan override milestone shorthand if drift
  appears between this split and the canonical source.

## Chunk Map

1. [`10-foundations-passive-pipeline.md`](./10-foundations-passive-pipeline.md)
   Covers the architectural foundations and passive pipeline model.
2. [`11-cache-family-policy-scheduler.md`](./11-cache-family-policy-scheduler.md)
   Covers cache rules, family policy, and scheduler integration.
3. [`12-watch-memory-metrics.md`](./12-watch-memory-metrics.md)
   Covers watch catalog, memory budgets, and metrics/query surfaces.
4. [`13-degraded-lifecycle-rollback-doc-gate.md`](./13-degraded-lifecycle-rollback-doc-gate.md)
   Covers degraded behavior, lifecycle semantics, rollback, and doc-gate.
5. [`14-execution-m0-m1.md`](./14-execution-m0-m1.md)
   Covers milestone execution for `M0-M1`.
6. [`15-execution-m2-m5.md`](./15-execution-m2-m5.md)
   Covers milestone execution for `M2-M5`.
7. [`16-execution-m6-m9-validation.md`](./16-execution-m6-m9-validation.md)
   Covers milestone execution for `M6-M9`, final validation, and rollout gates.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Sections 1-4 | `10-foundations-passive-pipeline.md` |
| Sections 5-8B | `11-cache-family-policy-scheduler.md` |
| Sections 9-11B | `12-watch-memory-metrics.md` |
| Sections 12-14; Mega Doc-Gate | `13-degraded-lifecycle-rollback-doc-gate.md` |
| M0-M1 | `14-execution-m0-m1.md` |
| M2-M5 | `15-execution-m2-m5.md` |
| M6-M9; validation gates; assumptions/defaults | `16-execution-m6-m9-validation.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
