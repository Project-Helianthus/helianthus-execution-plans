# Proxy Wire-Semantics Fidelity Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `da94a59d01b9ed187ceeaa28657b2ddd3cce0f8a699770b457d330c38d336bd3`

This directory contains the canonical EPIC lock and a lossless execution split
for orchestrator-driven implementation.

## Split Rules

- Canonical source of truth is [00-canonical.md](./00-canonical.md).
- The split is lossless except for deliberate repetition needed for isolated
  execution/review.
- Each chunk is independently reviewable and includes:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- Any drift between chunk content and canonical plan is resolved in favor of
  `00-canonical.md`.

## Sequencing Rules

- Milestone order is fixed: `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- `M6` is deferred and non-blocking for code milestones.
- One active issue per repo at a time is the execution default.
- Proxy behavior changes must not merge without matrix evidence (`T01..T88`
  plus `PX01..PX12`).

## Chunk Map

1. [10-execution-contract-and-matrix.md](./10-execution-contract-and-matrix.md)
   Covers milestone contract, issue split, matrix gate (`PX01..PX12`), and
   orchestrator execution assumptions/defaults.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Sections 2-7 | `10-execution-contract-and-matrix.md` |

## Review Target

The split is acceptable only if adversarial review can confirm:

- complete issue coverage (`#5`, `#6`, `#7`, `#238`-`#241`, `#85`-`#91`)
- exact milestone ordering with deferred `M6`
- explicit matrix subset definition (`PX01..PX12`)
- explicit assumptions/defaults preserved from the EPIC contract
