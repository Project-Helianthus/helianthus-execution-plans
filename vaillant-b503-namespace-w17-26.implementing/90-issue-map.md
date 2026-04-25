# Issue Map — vaillant/b503

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`

Depends on: [91-milestone-map.md](./91-milestone-map.md) for milestone status.

Scope: Maps each milestone to its tracking issue and merged PR once cruise-preflight / cruise-dev-supervise open them. Populated incrementally; empty rows expected for unstarted milestones.

Idempotence contract: Append-only. Past entries never rewritten except to add merged-squash references.

Falsifiability gate: Review fails if an entry claims merged-status without a squash hash and PR number, or if two milestones reference the same issue.

Coverage: One row per milestone (11 total: 7 v1.0 baseline + 4 v1.1 amendment-1).

| Milestone | Repo | Issue | PR | Squash hash | State |
|---|---|---|---|---|---|
| M0_DOC_GATE | helianthus-docs-ebus | — | docs-ebus#283 | b4cb1c7 | merged 2026-04-22 |
| M1_DECODER | helianthus-ebusgo | — | ebusgo#142 | 5491494d | merged 2026-04-22 |
| M2a_GATEWAY_MCP | helianthus-ebusgateway | — | ebusgateway#516 | d74dc89b | merged 2026-04-22 |
| M5_TRANSPORT_MATRIX | helianthus-ebusgateway | — | ebusgateway#518 | 2b8fcd1c | merged 2026-04-23 |
| M2b_GATEWAY_GRAPHQL | helianthus-ebusgateway | — | ebusgateway#520 | 07385b01 | merged 2026-04-23 |
| M3_PORTAL | helianthus-ebusgateway | — | ebusgateway#522 | 45846270 | merged 2026-04-23 |
| M4_HA | helianthus-ha-integration | — | ha-integration#188 | d9355e5f | merged 2026-04-23 |
| M0b_DOC_DISPATCHER_BRIDGE | helianthus-docs-ebus | — | — | — | not started (amendment-1) |
| M6_DISPATCHER_BRIDGE | helianthus-ebusgateway | — | — | — | not started (amendment-1) |
| M7_BENCH_REPLACE | helianthus-ebusgateway | — | — | — | not started (amendment-1) |
| M8_PORTAL_UX_GAPS | helianthus-ebusgateway | — | — | — | not started (amendment-1) |
