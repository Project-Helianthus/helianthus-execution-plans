# Writable Installer/Maintenance Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `34d2c8b70b8852a694fb09916744fe3670f3f386016de83d65c1f239b85213b7`

This directory contains the canonical writable installer/maintenance plan plus a
lossless execution-oriented split into sub-10k-token chunks. The split exists so
agents and reviewers can work on bounded, attackable pieces without losing the
source contract.

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

- The default milestone order is `M0 -> M1 -> M2 -> M3 -> M4`.
- M1A (B524 probes) and M1B (B509 probes) are independent parallel tracks.
- M4 splits into M4a (B524 HA entities after M2) and M4b (B509 HA entities
  after M3).
- Locked decisions in the canonical plan override milestone shorthand if drift
  appears between this split and the canonical source.

## Chunk Map

1. [`10-source-inventory-probes.md`](./10-source-inventory-probes.md)
   Covers dual-source register inventory, source-ownership rules, Phase 0 live
   bus validation probes, and the degraded-mode contract.
2. [`11-gateway-semantic-graphql.md`](./11-gateway-semantic-graphql.md)
   Covers gateway semantic types (Phase 1), semantic poller reads and
   write-through cache (Phase 2), GraphQL schema, mutations, and B509 pipeline
   type generalization (Phase 3).
3. [`12-mcp-ha-integration.md`](./12-mcp-ha-integration.md)
   Covers MCP server write tools (Phase 4), HA integration coordinator queries,
   entity platforms, backward-compat contract, and data merge strategy (Phase 5).
4. [`13-tests-deployment-verification.md`](./13-tests-deployment-verification.md)
   Covers complete test matrix for gateway and HA, degraded-mode test strategy,
   and end-to-end deployment verification (Phases 6-7).

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Context; Source-Ownership; Source Inventory; Phase 0 (Probes + Degraded-Mode) | `10-source-inventory-probes.md` |
| Phases 1-3 (Semantic Types, Poller, GraphQL) | `11-gateway-semantic-graphql.md` |
| Phases 4-5 (MCP Server, HA Integration) | `12-mcp-ha-integration.md` |
| Phases 6-7 (Tests, Deployment Verification) | `13-tests-deployment-verification.md` |
| Milestone Map, PR Strategy, Proof Matrix, Risks | `91-milestone-map.md` |
| Issue Map | `90-issue-map.md` |
| Status | `99-status.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
