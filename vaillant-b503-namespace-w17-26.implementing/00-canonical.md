# Vaillant B503 Namespace (`vaillant`)

State: `implementing`
Slug: `vaillant-b503-namespace-w17-26`
Locked on: `2026-04-22` (v1.0)
Amendment-1 locked on: `2026-04-25` (v1.1)
Canonical revision: `v1.1-amend1`

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

Milestone summary (v1.0 baseline + v1.1 amendment-1):

| Milestone | Repo | Routing | Complexity | State |
|---|---|---|---|---|
| M0_DOC_GATE | helianthus-docs-ebus | docs-researcher (Claude) | 5 | merged 2026-04-22 |
| M1_DECODER | helianthus-ebusgo | codex-dev | 4 | merged 2026-04-22 |
| M2a_GATEWAY_MCP | helianthus-ebusgateway | claude-dev + adversarial | 8 | merged 2026-04-22 |
| M5_TRANSPORT_MATRIX | helianthus-ebusgateway | claude-dev + adversarial | 7 | merged 2026-04-23 |
| M2b_GATEWAY_GRAPHQL | helianthus-ebusgateway | codex-dev | 5 | merged 2026-04-23 |
| M3_PORTAL | helianthus-ebusgateway | codex-dev | 4 | merged 2026-04-23 |
| M4_HA | helianthus-ha-integration | codex-dev | 4 | merged 2026-04-23 |
| **M0b_DOC_DISPATCHER_BRIDGE** | helianthus-docs-ebus | docs-researcher (Claude) | 4 | not started (amendment-1) |
| **M6_DISPATCHER_BRIDGE** | helianthus-ebusgateway | claude-dev + adversarial | 8 | not started (amendment-1) |
| **M7_BENCH_REPLACE** | helianthus-ebusgateway | codex-dev + operator-attest | 5 | not started (amendment-1) |
| **M8_PORTAL_UX_GAPS** | helianthus-ebusgateway | codex-restricted (LANE A) | 6 | not started (amendment-1) |

Dependency DAG (v1.1):

```text
M0 → M1 → M2a → M5 → M2b → {M3, M4} → M6 → {M7, M8} → terminal
                                ▲
                                │
                              M0b (docs-gate companion to M6)
```

Mandatory adversarial-review milestones: `M2a`, `M5`, `M6` (consultant
escalation after 2 fail loops). `M7` is operator-attest (cruise-merge-gate
WAIT_OPERATOR). `M8` is LANE A user-visible-breaking (modifies existing
Vaillant pane semantics) — also WAIT_OPERATOR.

`M7` and `M8` are both `_blocks_terminal: true`. Plan transition
`.implementing → .locked → .maintenance` is gated on both being merged.

## Amendment-1 (v1.1) — Production dispatcher + portal UX gaps

Locked on `2026-04-25` after R1..R5 adversarial CONSENSUS with Codex
`gpt-5.4` reasoning=high.

**Trigger.** All 7 baseline milestones merged 2026-04-22..23, but
`cmd/gateway/vaillant_b503_wiring.go` installs `b503StubDispatcher{}`
which always returns `errB503DispatcherNotWired`. Live gateway probes
(192.168.100.4) confirmed `vaillantCapabilities.b503 = {available: false,
reason: UNKNOWN}` and `UPSTREAM_RPC_FAILED` on every read tool. Plan
was incorrectly transitioned to `.maintenance` on 2026-04-25; rolled
back to `.implementing` and amendment-1 codifies the production-wiring
+ live-bus + portal-UX gap closure as 4 new milestones.

**New decisions.** AD16 (dispatcher contract), AD17 (BENCH-REPLACE
attestation), AD18 (capability-signal 8-state truth table including
stale-epoch discipline), AD19 (portal device-centric topology). See
[10-scope-decisions.md](./10-scope-decisions.md) §AD16..AD19.

**Forbidden post-amendment.** Stub dispatcher fallback in production
wiring. Sticky AVAILABLE after transport loss. Premature AVAILABLE
before first real dispatch. Stale-epoch frame mutation of capability or
session state. Auto-merge of M7 BENCH-REPLACE PRs.

**Detail chunk:** [13-amendment-1-dispatcher-portal-ux.md](./13-amendment-1-dispatcher-portal-ux.md).

## Adversarial provenance

### v1.0 baseline (2026-04-22) — converged at R4

Codex `gpt-5.4`, reasoning=high. Rounds log:

- R1: 6 attacks (4 high, 1 med), 2 concessions — ebusreg-leak fix, MCP→GraphQL→consumer ordering, semantic-lock narrowing, live-monitor serialization, transport-gate expansion, acceptance criteria concreteness.
- R2: 6 attacks (3 high, 3 med) — DAG tightening (M5 blocks M2b), HA capability signal, session epoch semantics, doc-gate operational contract breadth, B524 regression rows, per-milestone routing table.
- R3: 2 attacks (1 high, 1 med) — HA permanent-vs-transient unavailability split, EXPIRED normalization rule.
- R4: CONSENSUS with 3 residual concerns (1 med, 2 low) folded into plan as clarifications (entity-unavailable-during-hysteresis, refresh-outcome non-collapse, poll cadence pinning).

No ESCALATE_TO_OPERATOR decisions outstanding for v1.0.

### v1.1 amendment-1 (2026-04-25) — converged at R5

Codex `gpt-5.4`, reasoning=high. Mode `AMENDMENT_REVIEW` (delta-bounded;
baseline plan attacks out of scope). Rounds log:

- R1: 5 attacks (2 high, 3 med), 2 concessions — missing doc-gate companion (→ M0b added), mixed-traffic concurrency under-specified (→ 4-test split), capability-signal truth table needed, BENCH-REPLACE-SIGNOFF placement ambiguity, transport-gate row coverage explicit.
- R2: 5 attacks (2 high, 2 med, 1 low), 2 concessions — stale-epoch in-flight completion (→ AD18 8th row added), per-timing concurrency case split (→ M6-CONC-01..04), M0b scope-creep trim, label ownership assignment, lane subtype clarification.
- R3: 3 attacks (0 high, 2 med, 1 low), 2 concessions, declared CONSENSUS — mechanical lock-order verification mechanism, explicit epoch-as-request-side-metadata, M7 PR topology invariant. Inline fixes integrated.
- R4: 3 attacks (0 high, 3 med), 3 concessions — actionable-copy non-falsifiable (→ data-testid contract per state), target-switch in-flight invalidation, frontend epoch-rollover acceptance. R4 also recommended classifying M8 as LANE A (accepted).
- R5: 1 attack (0 high, 1 med), 3 concessions, CONSENSUS — target-switch-during-enable contract added (M8-TGT-04). Amendment locked.

No ESCALATE_TO_OPERATOR decisions outstanding for v1.1.
