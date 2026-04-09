# Gateway-Embedded Proxy Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0bc9965756418f65ae4c709b90ff08d152612e2c9894ca8e684e8ba36e0cd8a8`

This directory contains the canonical plan for embedding adapter multiplexing
logic into the gateway, plus a lossless execution-oriented split into
sub-10k-token chunks.

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

- The default milestone order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- M2 and M3 both depend on M1 but are independent of each other. Parallel
  execution is permitted if one-issue-per-repo is satisfied.
- One active issue per repo at a time is the execution default.
- Adapter-direct behavior changes must not merge without matrix evidence
  (`T01..T88` plus `AD01..AD12`).

## Chunk Map

1. [`10-architecture-and-mux-design.md`](./10-architecture-and-mux-design.md)
   Covers architectural topology, multiplexer design, owner arbitration,
   echo suppression, wire phase tracker, and RESETTED handling.

2. [`11-gateway-integration-paths.md`](./11-gateway-integration-paths.md)
   Covers gateway active and passive path integration, config flags,
   transport resolution, and observe-first semantics preservation.

3. [`12-external-proxy-endpoint.md`](./12-external-proxy-endpoint.md)
   Covers external TCP proxy endpoint, session management, full master
   access, ENH protocol handling, and backpressure.

4. [`13-migration-rollback-addon.md`](./13-migration-rollback-addon.md)
   Covers HA addon configuration, migration path, rollback contract,
   and scope coordination with the proxy plan.

5. [`14-matrix-validation-gates.md`](./14-matrix-validation-gates.md)
   Covers AD01..AD12 matrix definitions, gate policy, regression requirements,
   orchestrator contract, assumptions, and maintenance readiness.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Sections 1-2 | `10-architecture-and-mux-design.md` |
| Sections 3 (M0-M2) | `11-gateway-integration-paths.md` |
| Sections 3 (M3) | `12-external-proxy-endpoint.md` |
| Sections 3 (M4), 8-10 | `13-migration-rollback-addon.md` |
| Sections 3 (M5), 4-7, 11 | `14-matrix-validation-gates.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
