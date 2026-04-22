# Vaillant B503 Namespace (`vaillant`)

State: `locked`
Slug: `vaillant-b503-namespace-w17-26`
Locked on: `2026-04-22`
Canonical revision: `v1.0-locked`

## Summary

`vaillant` is a new L7 provider namespace for Helianthus that carries Vaillant-proprietary diagnostic/service/live-monitor services under `PB=0xB5`. It runs parallel to `ebus_standard` and does not reuse or contaminate the cross-vendor standard surface. This plan implements the first subfamily: `SB=0x03` (B503) covering current/historical errors, service tickets, and HMU live-monitor.

`vaillant/b503` sits strictly above `protocol.Frame`. Framing, CRC, escaping and bus-transaction behaviour are unchanged. B503 request encoding is the observed two-byte selector `(family, selector)` pair (see §Wire Shape). Selector catalog is catalog-driven in `helianthus-ebusgo`, not hand-coded in gateway paths.

The sibling plan `ebus-standard-l7-services-w16-26` (COMPLETED 2026-04-20) establishes precedent for the MCP → GraphQL → consumer rollout ordering, transport-gate artefact, and per-milestone routing table conventions. This plan adopts those conventions directly.

## Scope

B503 selectors locked into first delivery:

| Request payload | Direction | Name | Response shape |
|---|---:|---|---|
| `00 01` | read | `Currenterror` | five LE uint16 slots (0xFFFF = empty) |
| `01 01` | read | `Errorhistory` | index + errorhistory payload |
| `02 01` | install write | `Clearerrorhistory` | ACK + side effect |
| `00 02` | read | `Currentservice` | five LE uint16 slots |
| `01 02` | read | `Servicehistory` | index + history payload |
| `02 02` | install write | `Clearservicehistory` | ACK + side effect |
| `00 03` | service write/read | HMU live-monitor enable + status | status + function + reserved |

First-delivery MCP surfaces (required):

- `ebus.v1.vaillant.errors.get` (current 5-slot read)
- `ebus.v1.vaillant.errors.history.get` (indexed)
- `ebus.v1.vaillant.service.current.get`
- `ebus.v1.vaillant.service.history.get`
- `ebus.v1.vaillant.live_monitor.get` (enable → read → idle-disable session)

Install writes (`Clearerrorhistory`, `Clearservicehistory`) are NOT exposed on any surface in v1 — not MCP, not GraphQL, not portal. A post-v1 installer-gated plan may revisit.

Live invocation for reads routes through the existing `ebus.v1.rpc.invoke` substrate. A new write-class session gate is introduced (see §Execution Safety) solely for the live-monitor enable/disable pair, which is side-effectful.

Portal first-delivery scope: read-only Vaillant pane with errors/service/live-monitor tabs consuming GraphQL. No install-write UI affordance present at any feature flag.

Home Assistant first-delivery scope: diagnostic sensor `boiler_active_error` (decimal) + attribute `error_history` (5-slot). Keyed off GraphQL capability signal `vaillantCapabilities.b503.available`. No F.xxx translation in entity state. No service-history entity in v1.

Transport-gate: B503 read decode and live-monitor session validated across `adapter-direct` and `ebusd_tcp` families (plus `ebusd_serial` if lab-available; escalation note otherwise). Matrix artefact `matrix/M6a-vaillant-b503.md`.

Explicitly out of first delivery:

- Install writes (`02 01` / `02 02`) on any surface.
- Cross-device F.xxx normalization table in public contract.
- SCAN_ID sweep of B503 selectors across all device classes (separate RE plan).
- Wireshark dissector parity update (separate docs-ebus task).
- HA service-history entity.
- GraphQL mutations for B503.

## Evidence snapshot (2026-04-22)

- `helianthus-docs-ebus/protocols/vaillant/ebus-vaillant-B503.md` — RE notes with 7 selectors and wire vectors (LOCAL_TYPESPEC + LOCAL_CAPTURE).
- LOCAL_CAPTURE: `REQ: f1 08 b5 03 02 00 01` → `RESP: 0a 19 01 ff ff ff ff ff ff ff ff` (first slot 0x0119 = 281 decimal; operator UI reported `F.281`).
- LOCAL_TYPESPEC: vendored john30 `ebusd-configuration` `errors_inc.tsp`, `service_inc.tsp`, `08.hmu.tsp`.
- No cross-device F.xxx table exists with sufficient provenance to publish in a stable public contract.
- Existing gateway surfaces B524 and B505 have mature decoders (`cmd/gateway/semantic_vaillant.go`, `mcp/server.go`, `graphql/mutations.go`, `portal/web/src/app.js`) — proven patterns are reused but NOT namespace-shared.

## Problem statement

Helianthus currently lacks any stable public surface for Vaillant error/service diagnostics. Operator captures show LOCAL_CAPTURE evidence that B503 carries actionable F.xxx data on BAI00. Without this namespace:

- HA cannot present boiler error state beyond binary ignition flags.
- Portal offers no diagnostic pane for service tickets.
- Live-monitor (HMU subfamily) remains entirely unexposed despite TypeSpec documentation.

The plan introduces a narrowly-scoped read-only public contract with explicit provenance labelling, deferring cross-device semantic normalization until bench evidence exists.

## Wire shape

Request payload (all B503 selectors observed to date):

```text
family   : byte     # 0x00 (current) | 0x01 (history index) | 0x02 (clear)
selector : byte     # 0x01 (error) | 0x02 (service) | 0x03 (HMU live-monitor)
```

Response shape is selector-dependent; see §Scope table and the decoder package
per-selector structs in `helianthus-ebusgo/protocol/vaillant/b503`.

Sentinel rule: `0xFFFF` (LE uint16) denotes an empty slot in five-slot
composite payloads. `first_active_error` is the first non-sentinel slot
scanning from slot 0 upward.

## Locked decisions (AD01..AD15)

See [10-scope-decisions.md](./10-scope-decisions.md) for the full matrix with
R1..R4 adversarial-planning provenance.

## Execution safety and public contract

See [11-execution-safety-and-surfaces.md](./11-execution-safety-and-surfaces.md)
for invoke-safety classification, live-monitor session model, capability
signal contract, and MCP→GraphQL→consumer rollout gating.

## Milestone plan

See [12-milestones-issues-acceptance.md](./12-milestones-issues-acceptance.md)
for the per-milestone scope, routing, complexity annotation, dependency
ordering (including M5 blocking M2b), and acceptance criteria.

Milestone summary:

| Milestone | Repo | Routing | Complexity |
|---|---|---|---|
| M0_DOC_GATE | helianthus-docs-ebus | docs-researcher (Claude) | 5 |
| M1_DECODER | helianthus-ebusgo | codex-dev | 4 |
| M2a_GATEWAY_MCP | helianthus-ebusgateway | claude-dev + adversarial review | 8 |
| M5_TRANSPORT_MATRIX | helianthus-ebusgateway | claude-dev | 7 |
| M2b_GATEWAY_GRAPHQL | helianthus-ebusgateway | codex-dev | 5 |
| M3_PORTAL | helianthus-ebusgateway | codex-dev | 4 |
| M4_HA | helianthus-ha-integration | codex-dev | 4 |

Dependency DAG: `M0 → M1 → M2a → M5 → M2b → {M3, M4}`.
`M2a` and `M5` are mandatory adversarial-review milestones with consultant
escalation after 2 fail loops.

## Adversarial provenance

The plan converged at R4 (Codex `gpt-5.4`, reasoning=high). Rounds log:

- R1: 6 attacks (4 high, 1 med), 2 concessions — ebusreg-leak fix, MCP→GraphQL→consumer ordering, semantic-lock narrowing, live-monitor serialization, transport-gate expansion, acceptance criteria concreteness.
- R2: 6 attacks (3 high, 3 med) — DAG tightening (M5 blocks M2b), HA capability signal, session epoch semantics, doc-gate operational contract breadth, B524 regression rows, per-milestone routing table.
- R3: 2 attacks (1 high, 1 med) — HA permanent-vs-transient unavailability split, EXPIRED normalization rule.
- R4: CONSENSUS with 3 residual concerns (1 med, 2 low) folded into plan as clarifications (entity-unavailable-during-hysteresis, refresh-outcome non-collapse, poll cadence pinning).

No ESCALATE_TO_OPERATOR decisions outstanding.
