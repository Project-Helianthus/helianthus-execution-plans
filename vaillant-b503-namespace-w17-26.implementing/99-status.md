# Status — vaillant/b503

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`

Depends on: [91-milestone-map.md](./91-milestone-map.md).

Scope: Live execution tracker. Updated by cruise-preflight / cruise-dev-supervise / cruise-merge-gate as cruise run progresses.

Idempotence contract: Append-only timeline; past bullets not rewritten.

Falsifiability gate: Review fails if status claims milestones merged without matching entries in `90-issue-map.md` and `91-milestone-map.md`.

Coverage: Current position + timeline.

State: `implementing` (rolled back from incorrectly-set `maintenance` on 2026-04-25)
Plan v1.0 locked: `2026-04-22`
Plan v1.1 amendment-1 locked: `2026-04-25`
Implementation started: `2026-04-22` (M0_DOC_GATE merged that evening)

## Current Position

- All 7 v1.0 baseline milestones merged 2026-04-22..23.
- Live gateway probe (192.168.100.4) on 2026-04-25 revealed `b503StubDispatcher` still injected; `vaillantCapabilities.b503 = {available: false, reason: UNKNOWN}` and all MCP read tools surfacing `UPSTREAM_RPC_FAILED`.
- Plan rolled back from `.maintenance` to `.implementing` on 2026-04-25.
- Amendment-1 (M0b, M6, M7, M8) locked after R1..R5 adversarial CONSENSUS with Codex `gpt-5.4` reasoning=high — see `00-canonical.md::§Adversarial provenance` and `13-amendment-1-dispatcher-portal-ux.md::§Adversarial provenance`.
- Next action: cruise-preflight on `M0b_DOC_DISPATCHER_BRIDGE` and `M6_DISPATCHER_BRIDGE` (parallel where DAG permits — M0b has no upstream deps; M6 depends on M0b merged).
- Canonical SHA256: see `00-canonical.md` head; chunks bear matching hash.

## Timeline

- `2026-04-22` — Plan v1.0 drafted, adversarial R1..R4 (6 / 6 / 2 / 0 attacks, converged), CONSENSUS, written to `.locked/`. M0_DOC_GATE + M1_DECODER + M2a_GATEWAY_MCP merged.
- `2026-04-23` — M5_TRANSPORT_MATRIX + M2b_GATEWAY_GRAPHQL + M4_HA + M3_PORTAL merged. Plan transitioned `.implementing → .locked` and (incorrectly, not yet detected) `.locked → .maintenance`.
- `2026-04-25` — Operator-detected stub-completion gap. Plan rolled back `.maintenance → .implementing`. Amendment-1 adversarial R1..R5 (5 / 5 / 3 / 3 / 1 attacks, CONSENSUS at R5). Amendment-1 locked. M0b/M6/M7/M8 enter cruise-preflight queue.
