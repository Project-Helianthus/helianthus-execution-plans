# Issue Map — vaillant/b503

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `896a82e720b33eefb449ea532570e0a962bfa76504519996825f13d92ec9bb28`

Depends on: [91-milestone-map.md](./91-milestone-map.md) for milestone status.

Scope: Maps each milestone to its tracking issue and merged PR once cruise-preflight / cruise-dev-supervise open them. Populated incrementally; empty at lock time.

Idempotence contract: Append-only. Past entries never rewritten except to add merged-squash references.

Falsifiability gate: Review fails if an entry claims merged-status without a squash hash and PR number, or if two milestones reference the same issue.

Coverage: One row per milestone; empty rows are the expected initial state.

| Milestone | Repo | Issue | PR | Squash hash | State |
|---|---|---|---|---|---|
| M0_DOC_GATE | helianthus-docs-ebus | — | — | — | not started |
| M1_DECODER | helianthus-ebusgo | — | — | — | not started |
| M2a_GATEWAY_MCP | helianthus-ebusgateway | — | — | — | not started |
| M5_TRANSPORT_MATRIX | helianthus-ebusgateway | — | — | — | not started |
| M2b_GATEWAY_GRAPHQL | helianthus-ebusgateway | — | — | — | not started |
| M3_PORTAL | helianthus-ebusgateway | — | — | — | not started |
| M4_HA | helianthus-ha-integration | — | — | — | not started |
