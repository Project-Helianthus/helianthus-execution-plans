# eBUS Standard L7 Services — Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `23d973c55172df381adbee0c12ace33482cacf1627b5dfed994ef3ec82084a89`

Revision: `v1.0-locked`

This directory contains the canonical `ebus_standard` plan plus a lossless
execution-oriented split into reviewable chunks.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk stays below `10000` tokens on both the GPT-5-family tokenizer
  and the Claude tokenizer.
- Each chunk is reviewable in isolation and repeats:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is lossless: canonical content maps once to a chunk, except for
  the dependency repetition needed for isolated review.
- Drift detection is explicit: every chunk and this index carry the
  canonical hash of `00-canonical.md`.

## Sequencing Rules

- Default order:
  `M0 -> M1 -> M2 -> M3 -> M4 -> M4B -> M4b1 -> M4b2 -> M4c1 -> M4c2 ->
   M4D -> M5 -> M5b -> M6a -> M6b`.
- `M4B_read_decode_lock` is a hard gate before `M5_PORTAL` and
  `M5b_HA_NOOP_COMPAT`.
- `M4D_responder_lock` is a hard gate before any portal responder UI.
- `M4b2` gates `M4c1`/`M4c2`; no responder work starts without a go-signal.
- `M6b` closes out the deprecated plan
  `ebus-good-citizen-network-management` via `.maintenance` transition.

## Chunk Map

1. [`10-scope-decisions.md`](./10-scope-decisions.md)
   Covers Summary, Scope, Evidence Snapshot, Problem Statement, and Locked
   Decisions 1-8 (namespace separation, catalog authority, catalog identity
   key, Identification/DeviceInfo policy, capability discovery, L7 type
   primitives, NM adopt-and-extend, NM runtime wiring).
2. [`11-execution-safety-and-surfaces.md`](./11-execution-safety-and-surfaces.md)
   Covers Locked Decisions 9-14 (safety classes and default-deny,
   `system_nm_runtime` whitelist, single execution-policy module, GraphQL
   gating, portal gating and hardening, shared-infrastructure isolation,
   responder feasibility spike), Execution Safety Policy normative summary,
   Target Repositories, and Delivery Order.
3. [`12-milestones-issues-acceptance.md`](./12-milestones-issues-acceptance.md)
   Covers Milestone Plan, Canonical Issues, Acceptance Criteria, and
   Risks.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Scope; Evidence Snapshot; Problem Statement; Locked Decisions 1-8 | `10-scope-decisions.md` |
| Locked Decisions 9-14; Execution Safety Policy; Target Repositories; Delivery Order | `11-execution-safety-and-surfaces.md` |
| Milestone Plan; Canonical Issues; Acceptance Criteria; Risks | `12-milestones-issues-acceptance.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every
chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
