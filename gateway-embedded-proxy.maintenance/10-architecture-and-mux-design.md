# Gateway-Embedded Proxy 01: Architecture and Multiplexer Design

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `f600ff2254ab7a300399ff85496c41b9b8ff13a0149dc62b137735e13e84c011`

Depends on: [00-canonical.md](./00-canonical.md).

Scope: Architectural topology (current vs target), multiplexer design,
owner arbitration model, echo suppression model, wire phase tracker, and
RESETTED/reconnection handling.

Idempotence contract: Declarative-only. Reapplying this chunk must not create
new issues, mutate milestone order, or weaken architectural contracts.

Falsifiability gate: Review fails this chunk if any of the following are absent:
multiplexer topology diagram, owner arbitration description with
gateway-priority semantics, echo suppression model distinguishing internal
passive path from external observer sessions, wire phase state machine.

Coverage: Canonical Summary and Sections 1-2.

## 1. Problem Statement

The gateway's passive bus tap sees approximately 40% `corrupted_request` events
on a 3-master eBUS (0x71 gateway, 0x31 ebusd, 0x10 VRC700).

Root causes:
- Passive reconstruction from raw byte stream lacks echo matching and frame
  boundary knowledge (structural limitation of passive observation).
- Self-echo noise: ~70% of corrupted frames originate from the gateway
  reconstructing its own transmitted frames — traffic the active path already
  has with full fidelity.
- Proxy escape encoding bug: `ownerObserverSeen` accumulates wire-level bytes
  (0xA9 escape sequences), replayed to observers that expect logical bytes.

## 2. Epistemic Framing

### Proven

- Active path: 100% fidelity via ENH echo matching and arbitration awareness.
- Passive path: ~40% corrupted on multi-master bus.
- Proxy escape bug: wire-level bytes in `ownerObserverSeen`, logical bytes
  expected by observers with escape decoding disabled.
- Gateway already classifies endpoints as proxy-like vs direct adapter.
- Gateway opens two TCP connections (active + passive) to same proxy endpoint.
- HA addon already has proxy config knobs.

### Hypothesis

- Embedded multiplexer eliminates self-echo noise from passive path.
- Frame-level echo suppression eliminates escape bug by design.
- Simpler than standalone proxy: no UDP-plain, no lease management, no local
  target emulation, two-class owner model (gateway + ebusd).
- Gateway semantic knowledge enables intelligent bus arbitration.

### Unknown

- Performance delta until live E2E measurement.
- Whether ebusgo transport needs new interfaces.
- RESETTED propagation behavior through multiplexer.
- Optimal arbitration fairness window between gateway and ebusd.

## 3. Topology Transition

### Current (Proxy-Based)

Gateway opens two TCP connections to proxy. Proxy multiplexes one upstream
connection to adapter. Passive path reconstructs from observer stream.

### Target (Adapter-Direct)

Gateway embeds multiplexer. Single connection to adapter. Multiplexer demuxes:
- Active path: `RawTransport` wrapper for `gateway.Bus`
- Passive path: filtered symbols (third-party only)
- Proxy endpoint: TCP listener for ebusd (full master access)

## 4. Multiplexer Architecture

Package: `internal/adaptermux/`

### 4.1 Connection Manager

Single ENH/ENS TCP connection to adapter hardware:
- Dial with TCP_NODELAY + KeepAlive
- INIT handshake on connect
- Reconnection loop on disconnect (1s initial, 30s cap, exponential backoff)

### 4.2 Active Path

`RawTransport`-compatible interface:
- `ReadByte()`: returns next byte from adapter (blocks)
- `Write()`: sends bytes to adapter, records them for echo tracking
- `Close()`: tears down multiplexer

Active path has exclusive write access to the adapter connection during
gateway ownership periods.

### 4.3 Passive Path

Callback-based filtered symbol stream:
- Receives all `ENHResReceived` bytes from adapter
- Suppresses bytes that the gateway itself sent (per echo tracking)
- Delivers third-party bytes (ebusd, VRC700 traffic) to `PassiveBusTap`
  via `OnPassiveTapEvent` callback

No escape decoding needed: ENH protocol delivers logical bytes.

### 4.4 Owner Arbitration

Two-class gateway-priority model:

At SYN boundary:
1. If gateway has pending START request → gateway wins
2. Else if external session has pending START → external wins (FIFO order)
3. Else → bus idle, no owner

Gateway requests are never delayed by external contention. External sessions
are serviced fairly at next available boundary.

Arbitration triggered by: SYN received from adapter, or owner release
(transaction complete, timeout, explicit release).

### 4.5 Echo Suppression

**Internal passive path**: byte-by-byte tracking. Every byte sent via active
path `Write()` is recorded. When adapter echoes it back as `ENHResReceived`,
the byte is suppressed from the passive stream. Mismatch resets tracking and
flushes accumulated bytes.

**External observer sessions**: frame-level tracking. The multiplexer knows
the complete frame each external session sent and suppresses the corresponding
echo from that session's observer stream. Other sessions see the traffic.
This eliminates byte-level `ownerObserverSeen` accumulation — no escape bug
possible.

### 4.6 Wire Phase Tracker

Adapted from proxy M3 minimal direct-mode phase tracker:

```
Idle → CollectRequest → WaitCmdAck → WaitResponseLen →
  WaitResponseBody → WaitResponseAck → Idle
```

- SYN at any phase → reset to Idle, open arbitration window
- Phase transitions drive: echo suppression boundaries, arbitration window
  detection, external session broadcast timing
- Byte-level tracking: SRC, DST, PB, SB, LEN, request/response body length

### 4.7 RESETTED Handling

When adapter sends ENHResResetted:
1. Active path: transport reset event, clear pending operations
2. Passive path: emit `PassiveTapEventDiscontinuity`
3. External sessions: broadcast ENHResResetted frame
4. Wire phase tracker: reset to Idle
5. Re-INIT after 200ms stabilization delay
