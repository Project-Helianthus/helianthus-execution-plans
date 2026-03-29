# Adapter Hardware Telemetry Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0f9d24008521a5cf918a0959cd2a30e1ee559092f149416c75b8e7ca545d7391`

This directory contains the canonical adapter hardware telemetry plan plus a
lossless execution-oriented split into sub-10k-token chunks.

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

## Sequencing Rules

- The default milestone order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- M0 (docs) and M1 (ebusgo) can be parallelized.
- M2 (proxy) depends on M1.
- M3 (gateway) depends on M1. Does NOT hard-depend on M2 (proxy is optimization).
- M2 and M3 can be parallelized after M1.
- M4 (portal) depends on M3.
- M5 (HA) depends on M3.

## Chunk Map

1. [`10-data-sources-transport.md`](./10-data-sources-transport.md)
   Covers enhanced protocol INFO data sources (wire-observable gating) and ebusgo transport API (exclusivity contract).
2. [`11-proxy-gateway-semantic.md`](./11-proxy-gateway-semantic.md)
   Covers proxy 4-state cache + singleflight, gateway semantic model, Prometheus (48 budget), MCP (envelope), GraphQL (non-null), Portal.
3. [`12-ha-docs-delivery-acceptance.md`](./12-ha-docs-delivery-acceptance.md)
   Covers HA adapter_info_coordinator + diagnostic sensors, docs, delivery order, 11 acceptance criteria (incl. fault injection), risks.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Sections 1-2 | `10-data-sources-transport.md` |
| Sections 3-4 | `11-proxy-gateway-semantic.md` |
| Sections 5-11 | `12-ha-docs-delivery-acceptance.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
