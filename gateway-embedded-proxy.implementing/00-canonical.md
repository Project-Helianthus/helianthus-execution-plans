# Gateway-Embedded Adapter Multiplexer (Direct Connect)

Revision: `v1.0-locked`
Date: `2026-04-09`
Status: `Locked`

## Summary

This plan embeds the adapter multiplexing logic currently provided by the
standalone `helianthus-ebus-adapter-proxy` directly into the
`helianthus-ebusgateway`. The gateway connects to the eBUS adapter hardware
(ENH/ENS protocol) without an intermediate proxy TCP hop, eliminating self-echo
noise on the passive observation path and the proxy's escape encoding bug.

An optional TCP proxy endpoint inside the gateway allows external clients
(ebusd) to connect with full master access, preserving backward compatibility.

The standalone proxy remains an independent product for users who do not run the
gateway.

## 1. Proven / Hypothesis / Unknown

### 1.1 Proven

- The gateway's active path achieves 100% frame fidelity via ENH echo matching
  and protocol-level arbitration awareness.
- The passive path sees approximately 40% `corrupted_request` events on a
  3-master bus (0x71 gateway, 0x31 ebusd, 0x10 VRC700). Root cause: passive
  reconstruction from a raw byte stream lacks echo matching and frame boundary
  knowledge.
- The proxy's echo replay mechanism stores echoed bytes in
  `ownerObserverSeen` as wire-level values (including escape sequences
  0xA9+0x00 and 0xA9+0x01). When replayed at SYN boundaries via
  `appendObserverRequestSegmentFrames()`, these wire-level bytes are delivered
  to observer sessions that have escape decoding disabled (gateway's
  `passiveTapDecodesWireEscapes()` returns false for proxy-like endpoints).
  Result: extra bytes in stream, CRC mismatch on frames containing 0xA9 or
  0xAA in payload data.
- The gateway already classifies transport endpoints as proxy-like (localhost
  ports 19001-19999) or direct adapter (remote TCP port 9999 or Unix socket)
  via `passiveTapUsesProxyLikeObserverTransport()` in `passive_bus_tap.go`.
- The gateway opens two separate TCP connections to the same proxy endpoint:
  one for active bus operations, one for passive observation.
- The HA addon configuration already includes `adapter_proxy_enabled`,
  `adapter_proxy_upstream`, and `adapter_proxy_port` knobs.
- Proxy standalone wire-semantics improvements (M1-M5 of
  `proxy-wire-semantics-fidelity` plan) are landed on proxy `main`.
- The ENH transport interface (`transport.RawTransport`) is well-defined in
  `helianthus-ebusgo` with `ReadByte()`, `Write()`, `Close()`.

### 1.2 Hypothesis

- Embedding the multiplexer eliminates self-echo noise from the passive path.
  Approximately 70% of `corrupted_request` events originate from the gateway
  attempting to passively reconstruct its own transmitted frames — traffic that
  the active path already has with full fidelity.
- In-process active/passive correlation is faster and more reliable than
  cross-TCP correlation through the proxy.
- The embedded multiplexer is simpler than the standalone proxy: no UDP-plain
  transport support, no source policy lease management, no local target
  emulation, simpler session model (two owner classes: gateway internal +
  external ebusd, not N arbitrary clients).
- Frame-level echo suppression (tracking complete sent frames, not individual
  bytes) eliminates the escape encoding bug by design. No byte-level
  `ownerObserverExpected/Seen` accumulation.
- Gateway semantic knowledge enables intelligent bus arbitration: the gateway
  can yield bus access to ebusd during polling gaps and prioritize
  time-critical semantic reads.

### 1.3 Unknown

- Exact performance delta (latency, frame corruption rate, observe-first
  coverage) until live end-to-end measurement on a 3-master bus.
- Whether `ebusgo/transport` requires new interfaces or adapters for the
  multiplexed passive stream, or whether `RawTransport` plus internal
  channels suffice.
- Impact on transport matrix tests T01..T88. Expected: zero impact because
  adapter-direct is additive (existing transport modes are unchanged).
- RESETTED propagation behavior through the multiplexer to active, passive,
  and external sessions simultaneously.
- Optimal arbitration fairness window between gateway and ebusd. Too long
  risks ebusd starvation; too short risks gateway polling disruption from
  ebusd bus contention.

## 2. Architectural Design

### 2.1 Current Topology (Proxy-Based)

```
Gateway                  Proxy               Adapter
┌───────────────┐  TCP   ┌──────────┐  TCP   ┌──────────┐
│ Active  path ─┼───────→│ owner    │───────→│          │
│ Passive path ─┼───────→│ observer │←───────│ eBUS hw  │
└───────────────┘        └──────────┘        └──────────┘
                              ↑
ebusd ────────────────────────┘ (TCP session)
```

Problems:
- Two TCP hops between gateway and adapter.
- Gateway passive path reconstructs from raw stream (40% corrupted).
- Proxy echo replay has escape encoding bug.
- Self-echo noise dominates passive path (~70% of corrupted frames).

### 2.2 Target Topology (Adapter-Direct)

```
Gateway (with embedded multiplexer)              Adapter
┌──────────────────────────────────────┐  ENH   ┌──────────┐
│ ┌────────────┐                       │────────│          │
│ │ Adapter Mux│←──── single conn ────→│←───────│ eBUS hw  │
│ ├────────────┤                       │        └──────────┘
│ │ Active path: RawTransport wrapper  │
│ │ Passive path: filtered symbols     │
│ │ (third-party only, zero self-echo) │
│ ├────────────┤                       │
│ │ Proxy endpoint (:19001)            │
│ │ ← ebusd connects as full master   │
│ └────────────┘                       │
└──────────────────────────────────────┘
```

What this eliminates:
- Echo suppression/replay logic for the internal passive path.
- Self-echo noise on passive tap (zero own-traffic reconstruction).
- One TCP hop (latency, failure modes).
- Redundant passive reconstruction of the gateway's own traffic.

What this enables:
- Passive tap sees only third-party traffic (ebusd + VRC700 broadcasts).
- Active/passive correlation in-process without network latency.
- Gateway semantic knowledge at multiplexer level for bus arbitration.
- Protocol specimen store captures only third-party traffic.

### 2.3 Multiplexer Architecture

The adapter multiplexer (`internal/adaptermux/`) owns a single ENH/ENS
connection to the adapter hardware and exposes three interfaces:

1. **Active path** (`RawTransport`-compatible): bidirectional byte-level
   interface for `gateway.Bus`. Supports `ReadByte()`, `Write()`, `Close()`.
   START arbitration and SEND forwarding pass through to the adapter.

2. **Passive path** (callback or channel): unidirectional filtered symbol
   stream. Receives all bytes from the adapter except those that the gateway
   itself sent (self-echo suppression). Feeds into `PassiveBusTap` via the
   existing `OnPassiveTapEvent` callback pattern.

3. **External session manager**: optional TCP listener accepting ENH client
   connections. Each external session (ebusd) can participate in bus
   arbitration as a master (START/SEND) or observe broadcast traffic.

### 2.4 Owner Arbitration Model

The multiplexer supports two owner classes with gateway-priority scheduling:

- **Gateway (internal)**: always has first pick at SYN boundaries. Gateway
  requests are never delayed by external session contention.
- **External sessions (ebusd)**: serviced at the next SYN boundary when the
  gateway has no pending bus work. Fair access: ebusd requests are queued and
  serviced in FIFO order.

This is a simplification of the proxy's N-session boundary-based arbitration
(proxy M2). Key differences:

- Fixed two-class priority instead of lowest-address election.
- No source policy lease management (gateway has a fixed eBUS address 0x71).
- No UDP-plain START arbitration (ENH/ENS only).

### 2.5 Echo Suppression Model

**Internal passive path**: the multiplexer tracks every byte the gateway
sends via `Write()`. When the adapter echoes these bytes back as
`ENHResReceived`, the multiplexer suppresses them from the passive symbol
stream. The passive path sees only third-party bytes. No frame assembly or
escape decoding is involved — the suppression operates on the logical
bytes from the ENH RECEIVED response.

**External observer sessions**: each external session's own sent bytes are
tracked and suppressed from that session's observer stream. Other sessions'
traffic (including the gateway's) is visible. Echo suppression operates at
frame-level granularity: the multiplexer knows the complete frame each session
sent and suppresses the corresponding echo as a unit. This eliminates the
byte-level `ownerObserverSeen` accumulation pattern that caused the escape
encoding bug in the proxy.

### 2.6 Wire Phase Tracker

The multiplexer includes a wire phase tracker adapted from the proxy's
minimal direct-mode phase tracker (proxy M3). The tracker follows byte-level
eBUS transaction structure:

- Phases: `Idle` → `CollectRequest` → `WaitCmdAck` → `WaitResponseLen` →
  `WaitResponseBody` → `WaitResponseAck` → `Idle`
- SYN (0xAA) at any point resets to `Idle` and opens an arbitration window.
- Phase transitions drive: echo suppression boundaries, arbitration window
  detection, external session broadcast timing.

### 2.7 RESETTED and Reconnection

- Adapter RESETTED events are propagated to all consumers: active path
  (transport reset), passive path (discontinuity event), and all external
  sessions (ENHResResetted frame).
- On adapter TCP disconnect, the multiplexer enters a reconnection loop
  (exponential backoff, 1s initial, 30s cap). Active path blocks until
  reconnection. Passive path emits disconnection event. External sessions
  receive RESETTED on reconnection.

## 3. Milestone Model

### M0: Architecture Spec + Doc Gate

Repos: `helianthus-execution-plans`, `helianthus-docs-ebus`

Outcomes:
- Architecture doc update: embedded multiplexer section in ARCHITECTURE.md
- ENH multiplexer design document in docs-ebus
- Transport matrix extension definition (AD01..AD12)
- Canonical plan lock
- No functional code changes

Falsifiability gate: review fails if architecture doc does not cover the
multiplexer topology, or if AD01..AD12 definitions are absent from docs.

### M1: Adapter Multiplexer Core

Repo: `helianthus-ebusgateway`

Outcomes:
- New `internal/adaptermux/` package with:
  - Single ENH/ENS connection manager (dial, INIT, reconnection)
  - Active path `RawTransport` wrapper
  - Passive path filtered symbol channel/callback
  - Per-session echo tracking (frame-level suppression)
  - Owner arbitration (gateway-priority, external FIFO at SYN boundary)
  - Wire phase tracker (byte-level SRC/DST/PB/SB/LEN)
  - RESETTED propagation to all consumers
- Comprehensive unit tests with loopback transport

Depends on: M0 (architecture doc landed)

Falsifiability gate: review fails if any of the following are absent: echo
suppression unit test with 0xA9 payload, arbitration unit test with
gateway+external contention, RESETTED propagation unit test, wire phase
transition unit test.

### M2: Gateway Active + Passive Path Integration

Repo: `helianthus-ebusgateway`

Outcomes:
- Config flag: `--adapter-direct enh://host:port`
- `resolveTransport()` routing: adapter-direct mode creates multiplexer,
  returns active `RawTransport` wrapper to `gateway.Bus`
- Passive tap wiring: multiplexer passive output feeds `PassiveBusTap` via
  callback (replaces separate TCP connection for passive observation)
- Observe-first semantics preserved: broadcast listener, shadow cache,
  deduplicator work unchanged
- Regression gate: T01..T88 pass (existing transport modes unmodified)

Depends on: M1 (multiplexer core)

Falsifiability gate: review fails if active path regression (T01..T88) is
not demonstrated, or if passive path integration does not receive third-party
traffic on a live bus.

### M3: External Proxy Endpoint

Repo: `helianthus-ebusgateway`

Outcomes:
- Optional TCP listener: `--proxy-listen :19001`
- ENH session management: connect, disconnect, cleanup, send buffer
  overflow protection
- Full master access: external sessions send ENHReqStart/ENHReqSend,
  receive ENHResStarted/ENHResFailed/ENHResReceived
- Observer broadcast: third-party traffic delivered to external sessions
- Per-session echo suppression (frame-level, no escape bug)
- RESETTED propagation to external sessions
- Backpressure: configurable send buffer (8KB default), overflow forces
  session close

Depends on: M1 (multiplexer core with arbitration)

Falsifiability gate: review fails if ebusd cannot connect, send a bus
command, and receive the response through the proxy endpoint.

### M4: HA Addon + Migration

Repos: `helianthus-ha-addon`, `helianthus-docs-ebus`

Outcomes:
- Addon config schema: `adapter_direct_enabled` (bool),
  `adapter_direct_address` (host:port)
- When enabled: gateway started with `--adapter-direct`, proxy process
  not spawned
- When disabled: existing proxy-based topology (backward compatible)
- If `adapter_proxy_port` is set alongside adapter-direct: gateway starts
  with `--proxy-listen` for ebusd coexistence
- Migration documentation: step-by-step for addon and standalone users
- Rollback contract documentation

Depends on: M2 (gateway integration functional), M3 (proxy endpoint functional)

Falsifiability gate: review fails if addon cannot start in both modes
(adapter-direct and proxy-based) from config alone, or if rollback
documentation is absent.

### M5: Matrix Validation + E2E

Repos: `helianthus-ebusgateway`, `helianthus-docs-ebus`

Outcomes:
- AD01..AD12 test definitions documented with evidence format
- Live bus validation on 3-master topology (0x71 + 0x31 + 0x10):
  - Active path transaction success rate
  - Passive path corrupted frame rate (comparison: proxy-based vs
    adapter-direct)
  - Observer broadcast delivery correctness
  - Arbitration fairness (gateway vs ebusd transaction distribution)
- Regression: T01..T88 pass, PX01..PX12 pass (standalone proxy unchanged)
- Performance metrics: latency, observe-first coverage percentage

Depends on: M2 + M3 + M4 (all functional paths available)

Falsifiability gate: review fails if any AD01..AD12 gate lacks documented
evidence, or if T01..T88 regression is not demonstrated.

## 4. Required Adapter-Direct Matrix Subset

| ID   | Description | Milestone |
|------|-------------|-----------|
| AD01 | Active path sends and receives eBUS transactions correctly | M2 |
| AD02 | Passive path sees zero self-echo frames in adapter-direct mode | M2 |
| AD03 | Passive path correctly reconstructs third-party traffic | M2 |
| AD04 | RESETTED propagates to active + passive + external sessions | M1, M3 |
| AD05 | External proxy endpoint: ebusd connects, receives broadcasts | M3 |
| AD06 | External proxy endpoint: ebusd sends START/SEND successfully | M3 |
| AD07 | Owner arbitration: gateway and ebusd compete fairly at SYN | M3 |
| AD08 | Per-session echo suppression: own bytes suppressed from own view | M1, M3 |
| AD09 | Adapter disconnect: reconnection recovers all paths | M1 |
| AD10 | Migration: proxy-based to adapter-direct preserves semantics | M4 |
| AD11 | Rollback: adapter-direct to proxy-based restores behavior | M4 |
| AD12 | No 0xA9/0xAA escape corruption in observer streams | M1, M3 |

Gate policy:
- Adapter-direct transport/protocol PRs must pass full `T01..T88` plus
  full `AD01..AD12`.
- No unexpected `fail`.
- No unexpected `xpass`.
- `PX01..PX12` remain as the standalone proxy gate (separate product).

## 5. Canonical Issue Split

### EPIC Root

- `Project-Helianthus/helianthus-execution-plans#TBD` (`EPIC-GATEWAY-EMBEDDED-PROXY`)

### M0

- `Project-Helianthus/helianthus-execution-plans#TBD` (`PLAN-01`)
- `Project-Helianthus/helianthus-docs-ebus#TBD` (`DOC-01`)

### M1

- `Project-Helianthus/helianthus-ebusgateway#TBD` (`GW-01`)

### M2

- `Project-Helianthus/helianthus-ebusgateway#TBD` (`GW-02`)

### M3

- `Project-Helianthus/helianthus-ebusgateway#TBD` (`GW-03`)

### M4

- `Project-Helianthus/helianthus-ha-addon#TBD` (`HA-01`)
- `Project-Helianthus/helianthus-docs-ebus#TBD` (`DOC-02`)

### M5

- `Project-Helianthus/helianthus-ebusgateway#TBD` (`GW-04`)
- `Project-Helianthus/helianthus-docs-ebus#TBD` (`DOC-03`)

Issue numbers will be assigned when issues are created on GitHub. The
canonical map files must be updated with real issue numbers before any
downstream execution handoff.

## 6. Orchestrator Contract

Execution rules for an orchestrator receiving this plan:

1. Resolve child issues from the canonical map; do not infer missing work.
2. Execute strictly `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
3. M2 and M3 both depend on M1 but are independent of each other. Parallel
   execution is permitted if one-issue-per-repo is satisfied.
4. Maintain one active issue per repo at a time.
5. Keep doc-gate ahead of behavior-change merge decisions.
6. Transport-gate: T01..T88 regression must pass for any transport-affecting PR.
7. AD01..AD12 gate must pass for adapter-direct PRs.
8. Do not modify standalone proxy code. This plan is additive to the gateway.
9. Do not modify existing transport modes (ENH, ENS, ebusd-tcp via proxy).

## 7. Assumptions and Defaults

- The eBUS adapter hardware supports only one simultaneous TCP connection.
  This is the fundamental reason the multiplexer is needed.
- The gateway is the primary bus owner (eBUS address 0x71). External clients
  via the proxy endpoint are secondary owners.
- ENH is the primary adapter protocol. ENS support is included but
  UDP-plain and TCP-plain are out of scope for the embedded multiplexer.
- Local target emulation (proxy M4) is out of scope. The embedded
  multiplexer does not emulate target devices.
- Source policy lease management is out of scope. The gateway has a fixed
  eBUS address; external sessions use their own configured addresses.
- Zero-downtime migration is not required. Addon restart is acceptable for
  switching between proxy-based and adapter-direct topologies.
- The standalone proxy remains a first-class product. It is not deprecated
  or modified by this plan.

## 8. Scope Coordination with Proxy Plan

The `proxy-wire-semantics-fidelity` plan covers standalone proxy improvements:
wire-semantics arbitration (M2), phase tracker (M3), local target emulation
(M4), and PX01..PX12 matrix (M5). All milestones are landed on proxy `main`.

This plan covers the gateway-embedded alternative. There is no scope overlap:

- Proxy plan's M1-M5 remain proxy-only code.
- This plan creates new code in `ebusgateway/internal/adaptermux/`.
- Proxy plan's PX01..PX12 matrix is the standalone proxy gate.
- This plan's AD01..AD12 is the adapter-direct gate.
- The wire phase tracker design in M1 is informed by proxy M3 but is a
  reimplementation, not a code extraction or shared library.

## 9. Migration Path

### Forward Migration (Proxy-Based to Adapter-Direct)

1. Set `adapter_direct_enabled: true` and
   `adapter_direct_address: "host:9999"` in HA addon config.
2. Optionally set `adapter_proxy_port: 19001` if ebusd coexistence is needed.
3. Restart addon. Gateway starts with `--adapter-direct`, proxy not spawned.
4. If ebusd is configured, it connects to gateway's proxy endpoint on
   port 19001 instead of the standalone proxy.

### Rollback (Adapter-Direct to Proxy-Based)

1. Set `adapter_direct_enabled: false` in HA addon config.
2. Restart addon. Gateway starts with `--transport enh://localhost:19001`,
   proxy process is spawned as before.
3. ebusd reconnects to standalone proxy on port 19001.

Rollback requires only a config change and restart. No code rollback is
needed because adapter-direct is additive — existing transport modes are
unchanged.

## 10. Rollback Contract

At any milestone boundary, the system can revert to proxy-based topology:

- **After M0**: no code changes to revert. Plan-only.
- **After M1**: multiplexer code exists but is not wired into gateway
  startup. Remove or leave dormant.
- **After M2**: gateway has `--adapter-direct` flag but defaults to
  existing transport mode. Config omission reverts.
- **After M3**: proxy endpoint exists but is optional (`--proxy-listen`).
  Config omission disables.
- **After M4**: addon config flag controls topology. Set
  `adapter_direct_enabled: false` to revert.
- **After M5**: matrix tests exist as documentation. No runtime impact.

## 11. Maintenance Readiness Definition

This plan transitions from `.locked` to `.implementing` when:
- M0 issues are created on GitHub with real issue numbers
- Architecture doc PR is opened

This plan transitions from `.implementing` to `.maintenance` when:
- All AD01..AD12 gates have documented evidence
- T01..T88 regression is demonstrated
- Migration and rollback documentation is complete
- No stale locked-state instructions remain in the split package
