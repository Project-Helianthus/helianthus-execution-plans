# Energy v1 Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `17af2e502f3e5588be52f7b0355743cd0840834d434b810de76f97471c3a58f3`

This directory contains the canonical Energy v1 plan plus a lossless
execution-oriented split into reviewable chunks. The split exists so Opus,
Sonnet, and implementation agents can attack bounded pieces without losing the
source contract.

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
- The split is lossless except for deliberate dependency repetition needed for
  isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical
  hash of `00-canonical.md`.

## Sequencing Rules

- The default milestone order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- Existing-surface correction and new-capability rollout are distinct:
  - `energyTotals.today` correction is existing-surface semantic work
  - daily history is a new capability and must follow
    `MCP -> GraphQL -> Portal -> HA`
- Locked decisions in the canonical plan override milestone shorthand if drift
  appears between this split and the canonical source.

## Chunk Map

1. [`10-source-ownership-and-doc-gates.md`](./10-source-ownership-and-doc-gates.md)
   Covers evidence, uncertainty, source ownership, doc-gates, and scope
   boundaries.
2. [`11-gateway-live-today-and-history.md`](./11-gateway-live-today-and-history.md)
   Covers gateway semantic correction, bounded `B516` history collection, and
   previous-year gating.
3. [`12-mcp-graphql-portal-ha.md`](./12-mcp-graphql-portal-ha.md)
   Covers the new-capability pipeline, GraphQL contract, Portal validation, and
   Home Assistant rollout/backfill.
4. [`13-execution-proof-and-open-unknowns.md`](./13-execution-proof-and-open-unknowns.md)
   Covers milestone order, issue/proof expectations, and residual unknowns that
   remain explicit.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Sections 1-3 | `10-source-ownership-and-doc-gates.md` |
| Section 4 | `11-gateway-live-today-and-history.md` |
| Sections 5-6 | `12-mcp-graphql-portal-ha.md` |
| Sections 7-9 | `13-execution-proof-and-open-unknowns.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every
chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
