# vaillant/b503 10: Scope, Evidence, and Locked Decisions AD01..AD15

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `896a82e720b33eefb449ea532570e0a962bfa76504519996825f13d92ec9bb28`

Depends on: None. This chunk establishes scope, evidence, and the full decision matrix.

Scope: Defines IN/OUT bounds for first delivery; enumerates the 7 B503 selectors locked for v1; identifies target repos, forbidden surfaces (install writes everywhere, cross-device F.xxx normalization), and the evidence base (LOCAL_TYPESPEC + LOCAL_CAPTURE). Records AD01..AD15 with adversarial provenance from R1..R4.

Idempotence contract: Declarative-only. Reapplying this chunk must not broaden the selector set, reintroduce install writes into v1, contaminate `helianthus-ebusreg` with Vaillant-specific knowledge, or downgrade MCP→GraphQL→consumer ordering.

Falsifiability gate: Review fails this chunk if it exposes install writes on any surface in v1, places Vaillant protocol knowledge in `helianthus-ebusreg`, publishes a cross-device F.xxx lookup table in the stable public contract, or permits HA/Portal to consume MCP without GraphQL parity first.

Coverage: §Scope bounds, §Evidence, §Forbidden surfaces, §AD01..AD15, §Adversarial round log.

## Scope bounds

IN (v1):
- Decoder package `helianthus-ebusgo/protocol/vaillant/b503` with 7-selector coverage.
- MCP surfaces `ebus.v1.vaillant.errors.get`, `.errors.history.get`, `.service.current.get`, `.service.history.get`, `.live_monitor.get`.
- GraphQL read-only parity for those surfaces + `vaillantCapabilities.b503` signal.
- Portal Vaillant pane (errors/service/live-monitor tabs, read-only).
- HA diagnostic sensor `boiler_active_error` + `error_history` attribute, capability-signal-gated.
- Transport-matrix artefact across adapter-direct, ebusd_tcp (+ ebusd_serial if available).
- Live-monitor session model with epoch semantics and BUSY/EXPIRED/UNAVAILABLE error model (EXPIRED is gateway-internal only).

OUT (deferred post-v1 or separate plan):
- Install writes `Clearerrorhistory` (`02 01`), `Clearservicehistory` (`02 02`) on any surface (MCP, GraphQL, portal).
- Cross-device F.xxx lookup table in stable public contract.
- GraphQL mutations for B503.
- HA service-history entity.
- SCAN_ID sweep of B503 selectors across device classes (separate RE plan).
- Wireshark dissector parity update (separate docs-ebus task).

## Evidence

| Source | Reference |
|---|---|
| LOCAL_TYPESPEC | vendored john30 `ebusd-configuration`: `errors_inc.tsp`, `service_inc.tsp`, `08.hmu.tsp` |
| LOCAL_CAPTURE | operator-provided BAI00 read: `REQ: f1 08 b5 03 02 00 01` → `RESP: 0a 19 01 ff ff ff ff ff ff ff ff` (first slot decimal 281, operator UI reported F.281) |
| PUBLIC_CONFIG | john30 `ebusd-configuration` @ `23a460b8` |
| Helianthus prior RE | `helianthus-docs-ebus/protocols/vaillant/ebus-vaillant-B503.md` |
| Sibling plan precedent | `ebus-standard-l7-services-w16-26.locked` |

## Forbidden surfaces (v1 invariant)

1. NO install-write MCP tool exists for B503 in v1. Asserted by a negative test in M2a.
2. NO install-write GraphQL mutation exists for B503 in v1. Asserted by schema introspection diff in M2b.
3. NO install-write UI affordance (including hidden/feature-flagged) in v1 portal. Asserted by DOM audit in M3.
4. NO public enum value EXPIRED on `B503Availability`. Asserted by GraphQL schema tests in M2b.
5. NO protocol-specific B503 knowledge in `helianthus-ebusreg` (ownership lives in `helianthus-ebusgo`). Asserted by M1 review.

## Locked Decisions

### AD01 — Namespace placement

Parallel top-level package `helianthus-ebusgo/protocol/vaillant/b503`. Does not share code with `protocol/ebus_standard/*`. RESOLUTION: APPROVED. Provenance: R1 A1 + R1 C1.

### AD02 — Install writes v1 policy

`Clearerrorhistory`, `Clearservicehistory` NEVER exposed in v1 on any surface. Post-v1 requires separate plan + bench + installer-mode gating. RESOLUTION: APPROVED. Provenance: R1 C2.

### AD03 — Request encoding

Request modelled as `(family: byte, selector: byte)` pair matching observed wire shape. Not per-selector monolithic. RESOLUTION: APPROVED. Provenance: R1 baseline.

### AD04 — Live-monitor session model

Stateful single-owner session per transport incarnation:
- ownership key = `(adapter_instance_id, transport_incarnation_epoch)`
- states: IDLE → ENABLING → ACTIVE → DISABLED (internal EXPIRED sub-state for stale-epoch handles)
- 30s idle auto-disable
- poll-quiesce window on enable/disable with documented bounds
- write-class mutex SEPARATE from B524 `readMu`
- guaranteed quiesce release on disconnect/restart
- explicit BUSY / EXPIRED / UNAVAILABLE outcomes; EXPIRED is gateway-internal only

RESOLUTION: APPROVED. Provenance: R1 A4 + R2 A3.

### AD05 — F.xxx mapping

Public contract publishes decimal as-is. NO cross-device lookup table. Optional LOCAL_CAPTURE annotation MAY appear in decoder metadata with `provenance=LOCAL_CAPTURE`. RESOLUTION: APPROVED. Provenance: R1 A3 + R1 E3.

### AD06 — Portal exposure

Read-only. No install-write UI affordance exists at any feature flag in v1. RESOLUTION: APPROVED. Provenance: R1 baseline.

### AD07 — HA scope v1

Active error + 5-slot history ONLY. Service-history entity deferred. No F.xxx translation in entity state. RESOLUTION: APPROVED. Provenance: R1 baseline + R1 A3.

### AD08 — Adapter-direct compatibility

Live-monitor enable is a write-class frame on the adapter-direct path; M5 verifies session enable/read/disable succeeds on adapter-direct. RESOLUTION: verified during M5. Provenance: R1 baseline.

### AD09 — MCP→GraphQL→Consumer ordering

M2b (GraphQL) blocks M3 (portal) and M4 (HA). HA consumes GraphQL, not MCP directly. Additionally M5 (transport matrix) BLOCKS M2b. Full DAG: `M0 → M1 → M2a → M5 → M2b → {M3, M4}`. RESOLUTION: APPROVED. Provenance: R1 A2 + R2 A1.

### AD10 — LOCAL_CAPTURE-only F.xxx data surface

Never appears in stable public contract. Diagnostic annotation only, with explicit provenance flag. RESOLUTION: APPROVED. Provenance: R1 E3.

### AD11 — HA capability-signal-driven entity lifecycle

Distinguish permanent-absence from transient unavailability:
- `NOT_SUPPORTED` → entity absent (permanent) — BUT only after 3-poll hysteresis following prior non-NOT_SUPPORTED state (AD15 guard)
- `TRANSPORT_DOWN` / `UNKNOWN` / `SESSION_BUSY` → entity present, state=unavailable
- During the 3-poll confirmation window on a NOT_SUPPORTED flip, entity remains present with state=unavailable, then is destroyed after 3 consecutive confirmations (R4 residual R1 fix)

RESOLUTION: APPROVED. Provenance: R2 A2 + R3 A14 + R4 R1.

### AD12 — B524 regression evidence in M5

M5 acceptance requires explicit regression rows: at least one B524 read/poll scenario under concurrent B503 live-monitor activity, with angry-tester commands, logs, PASS/FAIL verdicts. RESOLUTION: APPROVED. Provenance: R2 A5.

### AD13 — Per-milestone routing table locked

Routing annotations on every milestone (docs-researcher / codex-dev / claude-dev). M2a and M5 flagged as mandatory adversarial review + consultant escalation after 2 fail loops. RESOLUTION: APPROVED. Provenance: R2 A6.

### AD14 — EXPIRED normalization

`EXPIRED` is gateway-internal only, never in public enum `B503Availability`. Resolver rule: on EXPIRED, auto-refresh session state and retry read ONCE; on second EXPIRED/inconsistency, surface `SESSION_BUSY` publicly. Bounded retry prevents reconnect loops. If refresh reveals `TRANSPORT_DOWN` or `UNKNOWN`, surface those literally (NOT collapsed into `SESSION_BUSY`) — R4 residual R2 fix. RESOLUTION: APPROVED. Provenance: R3 A15 + R4 R2.

### AD15 — Entity lifecycle hysteresis

3-poll confirmation required before destroying entity on NOT_SUPPORTED flip. Poll source = HA integration's standard coordinator tick; M4 acceptance pins poll cadence explicitly (R4 residual R3 fix). RESOLUTION: APPROVED. Provenance: R3 A14 + R4 R3.

## Adversarial round log

| Round | Attacks (H/M/L) | Outcome |
|---|---|---|
| R1 | 6 (4/1/0) | all integrated into v1 |
| R2 | 6 (3/3/0) | all integrated into v2; DAG tightened, session epoch, doc-gate widened |
| R3 | 2 (1/1/0) | both integrated into v3 |
| R4 | 0 blocker; 3 residual (0/1/2) | CONSENSUS; residuals folded into plan |

No ESCALATE_TO_OPERATOR.
