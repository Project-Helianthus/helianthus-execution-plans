# eBUS Good-Citizen Network Management + Raw MCP — Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `eb11742d60722b1389dca6822b956c15ddee542aacf95901299fefcd1a27dfcf`

Revision: `v1.0-locked`

This directory contains the canonical eBUS good-citizen NM plan plus a
lossless execution-oriented split into reviewable chunks.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk stays below `10000` tokens on both the GPT-5-family tokenizer and
  the Claude tokenizer.
- Each chunk is reviewable in isolation and repeats:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is lossless: canonical content is mapped once to a chunk, except
  for the dependency repetition needed for isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical
  hash of `00-canonical.md`.

## Sequencing Rules

- The default milestone order is
  `M0 -> M1 -> M2a -> M2b -> M3 -> M4 -> M5 -> M6 -> M7a -> M7b -> M8 -> M9 -> M10`.
- `ISSUE-GW-JOIN-01` is a pre-`M4` gateway prerequisite.
- `M7a` may start as soon as `M1` exists and may run in parallel with `M2a`
  through `M5`, but it gates only `M7b`.
- `M6` is planned as gateway-only unless implementation falsifies that
  assumption.

## Chunk Map

1. [`10-evidence-decisions-and-wire-behaviour.md`](./10-evidence-decisions-and-wire-behaviour.md)
   Covers summary, evidence snapshot, problem statement, and locked decisions
   for the NM model, discovery relationship, identity model, gateway/runtime
   ownership, and wire-level behavior.
2. [`11-runtime-discovery-and-policy.md`](./11-runtime-discovery-and-policy.md)
   Covers runtime-selected local address authority, cycle-time policy, target
   configuration, self-monitoring, failure/error semantics, bus-load policy,
   target repositories, and delivery ordering.
3. [`12-milestones-issues-acceptance-and-risks.md`](./12-milestones-issues-acceptance-and-risks.md)
   Covers milestone plan, cross-repo ordering, canonical issues, acceptance
   criteria, and risk table.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Evidence Snapshot; Problem Statement; Locked Decisions 1-6B | `10-evidence-decisions-and-wire-behaviour.md` |
| Locked Decisions 6C-12; Target Repositories; Delivery Order | `11-runtime-discovery-and-policy.md` |
| Milestone Plan; Canonical Issues; Acceptance Criteria; Risks | `12-milestones-issues-acceptance-and-risks.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every
chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
