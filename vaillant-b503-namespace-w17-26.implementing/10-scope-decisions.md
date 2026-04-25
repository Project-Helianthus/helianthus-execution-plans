# vaillant/b503 10: Scope, Evidence, and Locked Decisions AD01..AD15

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`

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

### AD16 — Production raw-frame dispatcher contract (amendment-1)

The B503 MCP+GraphQL surface MUST route through the same adaptermux/router substrate as B524/B525 — no parallel transport path. `b503session.Manager` remains single-owner across MCP+GraphQL. On transport disconnect, `RawFrameDispatcher` MUST propagate the error to `b503session.Manager.OnTransportDisconnect()` so AD04 quiesce-release fires. Lock acquisition order `liveMonitorMu → readMu` is invariant; reversal is a defect class. Stub fallbacks are FORBIDDEN post-M6 — the only acceptable post-deploy state is production dispatch live. M6 acceptance MUST include mixed-traffic B503+B524/B525 concurrency tests with `-race` AND a deterministic test-only lock tracer that records acquisition order; deadlock-or-fail timeout is a secondary trip-wire, not the primary proof.

RESOLUTION: APPROVED. Provenance: amend1 R1 A2 + R2 A2 + R3 A1.

### AD17 — BENCH-REPLACE attestation contract (amendment-1)

Matrix `M6a-vaillant-b503.md` §9 rows transition `[bridge-PASS] → [bridge-LIVE-PASS]` only via three concurrent gates:

1. PR-head commit trailer `BENCH-REPLACE-SIGNOFF: <YYYY-MM-DD>` (immutable git history evidence — semantic proof);
2. GitHub PR label `bench-replace-signoff` (workflow-gate evidence; PR scaffold step adds it; merge-gate validates);
3. Capture-artefact appendix files under `helianthus-ebusgateway/matrix/captures/M7-<transport>-<date>.txt` (factual evidence).

`cruise-merge-gate` MUST classify M7 as user-visible-breaking (LANE A) and force `WAIT_OPERATOR`. Auto-merge of BENCH-REPLACE PRs is FORBIDDEN. `cruise-merge-gate` MUST verify trailer-on-HEAD AND label BEFORE permitting operator to lift `WAIT_OPERATOR`. Trailer + captures remain authoritative semantic proof; label is workflow-gate evidence with explicit remediation path when missing only. Plan transition `.implementing → .locked → .maintenance` is BLOCKED until M7 merged.

RESOLUTION: APPROVED. Provenance: amend1 R1 A4 + R2 A4 + R4 A4 (LANE A confirmation).

### AD18 — Capability-signal 8-state truth table + stale-epoch discipline (amendment-1)

`vaillantCapabilities.b503` transitions follow an 8-state truth table. Each state has a defined output and stale-frame rule:

| # | State | Capability output | Stale-frame discipline |
|---|---|---|---|
| 1 | cold-boot, no successful dispatch yet | `UNKNOWN` | n/a |
| 2 | post-first-success steady state | `AVAILABLE` | n/a |
| 3 | disconnect during ACTIVE session | `TRANSPORT_DOWN` (literal) | in-flight requests fail TRANSPORT_DOWN; no late mutation |
| 4 | reconnect, before first post-reconnect dispatch | `UNKNOWN` (NOT sticky AVAILABLE) | reset to UNKNOWN regardless of pre-disconnect state |
| 5 | reconnect, post-first-success-after-reconnect | `AVAILABLE` | n/a |
| 6 | timeout/NAK/CRC during dispatch | `UPSTREAM_RPC_FAILED` to caller; capability stays last-known | n/a |
| 7 | session-expiry detected | `EXPIRED` internal → AD14 1-retry → `AVAILABLE` OR `TRANSPORT_DOWN` literal | n/a |
| 8 | stale in-flight completion across epoch rollover | n/a — frame discarded | reply/NAK/timeout from epoch N arriving after reconnect to epoch N+1 MUST be discarded; MUST NOT mutate capability to AVAILABLE; MUST NOT satisfy any post-reconnect waiter |

Forbidden states: sticky `AVAILABLE` after transport loss; premature `AVAILABLE` before first real dispatch; silent fallback to `UNKNOWN` once `TRANSPORT_DOWN` is knowable. Implementation contract: every B503 dispatch request MUST capture the current `Manager.epoch` into an in-flight request record at issue-time. Reply/NAK/timeout completion paths MUST compare against the stored epoch BEFORE waking waiters or mutating capability state. Epoch comparison is request-side metadata, not derived from `Manager` at receive time. M6 acceptance MUST include one separate test per truth-table row; missing-coverage = automatic merge-gate block.

RESOLUTION: APPROVED. Provenance: amend1 R1 A3 + R2 A1 + R3 A2.

### AD19 — Portal device-centric topology (amendment-1)

B503 is a per-target capability surface, not a global pane. The portal Vaillant B503 surface MUST accept a per-target selector and render distinct `B503Availability` state per device. Section `section-projection` is the canonical device-centric entry point; per-protocol planes (B503, L7 Standard, etc.) MUST be discoverable via Projection plane cards when capability=`AVAILABLE` for the selected device. Cross-linking from plane cards to per-protocol panes preserves direct-access while making device topology the primary navigation axis. Threading target through every B503 GraphQL query is invariant; query/cache keys MUST include target address as a first-class component; in-flight responses with mismatched target ARE discarded by the result handler before state mutation. M8 acceptance MUST include target-switch in-flight invalidation tests (M8-TGT-01..04 — capability, ownership, history, and enable-handshake) and a 4-step composite epoch-rollover frontend test (active → transport-down → unknown-pre-success → available-after-success).

RESOLUTION: APPROVED. Provenance: amend1 R4 A2 + R4 A3 + R5 A1.

## Adversarial round log

### v1.0 baseline (2026-04-22)

| Round | Attacks (H/M/L) | Outcome |
|---|---|---|
| R1 | 6 (4/1/0) | all integrated into v1 |
| R2 | 6 (3/3/0) | all integrated into v2; DAG tightened, session epoch, doc-gate widened |
| R3 | 2 (1/1/0) | both integrated into v3 |
| R4 | 0 blocker; 3 residual (0/1/2) | CONSENSUS; residuals folded into plan |

No ESCALATE_TO_OPERATOR.

### v1.1 amendment-1 (2026-04-25)

| Round | Attacks (H/M/L) | Outcome |
|---|---|---|
| R1 | 5 (2/3/0) | all integrated; M0b added, 4-test concurrency split, truth-table introduced, BENCH-REPLACE dual gate, transport-gate row coverage |
| R2 | 5 (2/2/1) | all integrated; AD18 8th row (stale-epoch), per-timing concurrency cases, M0b scope trim, label ownership, lane subtype |
| R3 | 3 (0/2/1) | declared CONSENSUS; lock-tracer + epoch-as-metadata + M7-blocked-until-M6 invariant integrated inline |
| R4 | 3 (0/3/0) | testable rendering contract per state, target-switch invalidation, frontend epoch-rollover; M8 → LANE A |
| R5 | 1 (0/1/0) | CONSENSUS; M8-TGT-04 target-switch-during-enable added; amendment locked |

No ESCALATE_TO_OPERATOR.
