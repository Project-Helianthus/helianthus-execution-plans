# vaillant/b503 11: Execution Safety, Session Model, and Public Contract

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `896a82e720b33eefb449ea532570e0a962bfa76504519996825f13d92ec9bb28`

Depends on: [10-scope-decisions.md](./10-scope-decisions.md) for AD04, AD09, AD11, AD14, AD15.

Scope: Invoke-safety classification for the 7 locked selectors; live-monitor session state machine with epoch semantics; BUSY/EXPIRED/UNAVAILABLE error model; GraphQL capability signal contract; MCP→GraphQL→consumer rollout gating; HA entity lifecycle rules; portal tab lifecycle.

Idempotence contract: Re-reading this chunk must not alter the published public contract shape, the forbidden EXPIRED exposure rule, the 3-poll hysteresis for entity destruction, or the M5-blocks-M2b ordering.

Falsifiability gate: Review fails if this chunk permits EXPIRED in the public enum, removes the 3-poll hysteresis, collapses `TRANSPORT_DOWN` or `UNKNOWN` into `SESSION_BUSY`, shares the live-monitor mutex with B524 `readMu`, or allows consumer rollout (portal/HA) before GraphQL parity lands.

Coverage: §Invoke safety, §Live-monitor FSM, §Public contract + capability signal, §HA entity lifecycle, §Portal tab lifecycle, §Cross-cutting bus contention rules.

## Invoke-safety classification

Every B503 selector has an invoke-safety class. The `helianthus-ebusgo` package exports this as an enum and the gateway applies it at the invoke boundary.

| Selector | Class | Notes |
|---|---|---|
| `00 01` Currenterror | READ | passive-safe, idempotent |
| `01 01` Errorhistory | READ | indexed read |
| `02 01` Clearerrorhistory | INSTALL_WRITE | **NOT exposed v1** |
| `00 02` Currentservice | READ | passive-safe |
| `01 02` Servicehistory | READ | indexed read |
| `02 02` Clearservicehistory | INSTALL_WRITE | **NOT exposed v1** |
| `00 03` HMU LiveMonitor | SERVICE_WRITE | stateful: enable → read → disable |

Rules:
- READ → gateway may invoke without special session.
- SERVICE_WRITE → gated by the live-monitor session model (AD04).
- INSTALL_WRITE → never invoked through any public surface in v1. A negative test in M2a asserts MCP returns no tool for these selectors.

## Live-monitor FSM (AD04)

Gateway internal state machine for the `00 03` session:

```text
IDLE
  └─ (enable request from MCP)──────▶ ENABLING
                                       │
                  (enable ACK on bus)──┘
                                       ▼
                                    ACTIVE  ◀─┐
                                       │      │ (periodic reads during session)
                     (30s idle timer)──┘      │
                                       │      │
                    (explicit disable) │      │
                                       ▼      │
                                    DISABLED ─┘
                                       │
          (reconnect / restart / epoch mismatch detected)
                                       ▼
                                    EXPIRED (internal only)
                                       │
                         (resolver refresh + retry once)
                                       │
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                 ▼
                  success          TRANSPORT_DOWN    SESSION_BUSY
                (back to ACTIVE)   (surface literal) (public)
```

Invariants:
- `ownership_key = (adapter_instance_id, transport_incarnation_epoch)`. A second claimant with a different key gets `BUSY`; a first-claimant handle whose epoch has advanced gets `EXPIRED` (internal) and is auto-refreshed once per AD14.
- 30s idle auto-disable fires from ACTIVE if no read requests arrive. Gateway emits the disable frame with poll-quiesce.
- Poll-quiesce window bounds documented in M0_DOC_GATE; upper bound enforced by the transport layer.
- Write-class mutex is a DISTINCT `sync.Mutex` from B524 `readMu`. Acquisition order: `liveMonitorMu` → (optional) `readMu`. Never reversed.
- On transport disconnect, gateway MUST release `liveMonitorMu` and transition to DISABLED with owner cleanup.

## Public contract — GraphQL capability signal (AD09, AD14)

```graphql
type VaillantCapabilities {
  b503: B503Capability!
}

type B503Capability {
  available: Boolean!         # true only when availability == AVAILABLE
  reason: B503Availability!
}

enum B503Availability {
  AVAILABLE
  NOT_SUPPORTED    # device class does not implement B503
  TRANSPORT_DOWN   # transport currently disconnected
  SESSION_BUSY     # live-monitor session owned by another client
  UNKNOWN          # gateway has not yet determined availability
}
```

Rules:
- `EXPIRED` never appears in this enum (AD14 invariant).
- After the internal 1-retry policy, resolver surfaces:
  - `AVAILABLE` if retry succeeded;
  - `TRANSPORT_DOWN` or `UNKNOWN` if the refresh revealed either (R4 R2 — never collapsed);
  - `SESSION_BUSY` only for true lifecycle/contention ambiguity, not transport loss.
- `NOT_SUPPORTED` is a durable state determined by device class.

## HA entity lifecycle (AD11, AD15)

```text
Capability read                 Entity action
───────────────────────────     ──────────────────────────────────────
(initial) NOT_SUPPORTED         → entity NOT created
(initial) AVAILABLE             → entity created, state=<decimal>
(initial) TRANSPORT_DOWN        → entity created, state=unavailable
(initial) SESSION_BUSY/UNKNOWN  → entity created, state=unavailable

(runtime) AVAILABLE → TRANSPORT_DOWN / SESSION_BUSY / UNKNOWN
                                → entity stays, state=unavailable
(runtime) any ↔ AVAILABLE       → entity stays, state=<decimal>
(runtime) non-NOT_SUPPORTED → NOT_SUPPORTED (1st poll)
                                → entity stays, state=unavailable
(runtime) NOT_SUPPORTED for 3 consecutive polls
                                → entity destroyed
(runtime) if any non-NOT_SUPPORTED arrives during window
                                → counter resets; entity preserved
```

Poll source: HA integration's standard DataUpdateCoordinator tick. Cadence pinned in M4 acceptance (default 30s coordinator; hysteresis window therefore ≥90s). M4 acceptance MUST include explicit tests for cold-start, reconnect, and degraded-transport scenarios to prove deterministic entity-removal timing (R4 R3).

## Portal tab lifecycle (AD06)

- Errors / Service tabs: GraphQL query-driven, render on capability=`AVAILABLE`; render empty-state placeholder otherwise.
- Live-monitor tab: on tab enter → GraphQL `liveMonitor` query starts session; on tab leave or component unmount → GraphQL issues explicit disable.
- No install-write buttons, no feature flag, no hidden DOM. M3 acceptance includes a DOM audit test scanning for any element referencing `clear`, `delete`, `reset`.

## Cross-cutting bus contention (AD04, AD12)

The gateway's existing finding (writes via router path fail under heavy semantic polling) constrains the session model:
- Live-monitor enable/disable frames serialize via the dedicated `liveMonitorMu`.
- Heavy B524 polling MAY proceed concurrently with B503 READ selectors (`00 01`, `01 01`, `00 02`, `01 02`).
- M5 acceptance (AD12) requires a regression scenario proving B524 baseline throughput is unchanged with the new mutex in place.
