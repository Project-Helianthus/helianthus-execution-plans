# Gateway-Embedded Proxy 03: External Proxy Endpoint

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0bc9965756418f65ae4c709b90ff08d152612e2c9894ca8e684e8ba36e0cd8a8`

Depends on: [00-canonical.md](./00-canonical.md),
[10-architecture-and-mux-design.md](./10-architecture-and-mux-design.md).

Scope: External TCP proxy endpoint for ebusd (and other ENH clients),
session management, full master access, ENH protocol handling, per-session
echo suppression, RESETTED propagation, and backpressure. Covers
milestone M3.

Idempotence contract: Declarative-only. Reapplying this chunk must not create
new issues, mutate session management contracts, or weaken echo suppression
guarantees.

Falsifiability gate: Review fails this chunk if: ebusd cannot connect and
execute a bus transaction through the proxy endpoint, per-session echo
suppression is not specified, or backpressure overflow behavior is undefined.

Coverage: Canonical Section 3 (M3).

## 1. M3: External Proxy Endpoint

Repo: `helianthus-ebusgateway`

### 1.1 Configuration

Optional TCP listener activated by flag:

```
--proxy-listen :19001
```

When specified, the gateway starts a TCP listener on the given address.
External ENH clients (ebusd) can connect and participate in bus operations.

When not specified, no listener is started. The gateway operates in
adapter-direct mode without external proxy capabilities.

### 1.2 Session Lifecycle

Each TCP connection creates a session:

1. **Connect**: accept TCP connection, assign unique session ID, start
   reader/writer goroutines.
2. **INIT exchange**: optional. If client sends ENHReqInit, respond with
   features byte and adapter INFO (cached from multiplexer).
3. **Active operation**: client sends ENHReqStart/ENHReqSend, receives
   ENHResStarted/ENHResFailed/ENHResReceived.
4. **Observer broadcast**: client receives third-party traffic as
   ENHResReceived frames.
5. **Disconnect**: client closes connection, or server closes on error/
   overflow. Session cleanup: release bus ownership if held, remove from
   session registry.

### 1.3 Full Master Access

External sessions can operate as bus masters:

**START arbitration**:
- Client sends ENHReqStart(initiator_address).
- Request is queued in the multiplexer's arbitration queue.
- At next SYN boundary (if gateway has no pending request), multiplexer
  forwards START to adapter.
- On ENHResStarted: multiplexer notifies winning session.
- On ENHResFailed: multiplexer notifies session of failure.
- Gateway-priority: if gateway and external session both have pending
  START, gateway always wins.

**SEND**:
- Client sends ENHReqSend(data_byte).
- Multiplexer forwards byte to adapter connection.
- Byte is recorded for echo tracking (this session's sent bytes).

**Transaction lifecycle**:
- Wire phase tracker monitors transaction progress.
- On transaction completion (final ACK or SYN timeout), ownership is
  released and next arbitration round begins.
- Maximum ownership duration: 2 seconds (from proxy convention).
- Idle release grace: 50ms after last SYN with no pending SEND.

### 1.4 Observer Broadcast

All connected sessions receive third-party bus traffic:

- Gateway's traffic: visible to external sessions (not their own).
- Other external sessions' traffic: visible (cross-session observation).
- Own session's traffic: suppressed via per-session echo tracking.

Broadcast is per-byte as `ENHResReceived` frames, matching the proxy's
observer frame format for ebusd compatibility.

### 1.5 Per-Session Echo Suppression

Each session has its own echo tracker:

- When a session sends a byte via SEND, the byte is recorded in that
  session's `expectedEchoes` queue.
- When the adapter returns `ENHResReceived` with a matching byte, the byte
  is consumed from `expectedEchoes` and suppressed from that session's
  observer stream.
- Non-matching bytes: flush remaining expected echoes, deliver as observer
  frames.
- SYN boundary: flush any accumulated echo bytes.

**Frame-level tracking** (not byte-level `ownerObserverSeen`):
- The multiplexer knows the wire phase and can correlate echo sequences
  with sent frames as complete units.
- No escape encoding is involved in the echo tracking path — ENH protocol
  delivers logical bytes.
- This eliminates the proxy's 0xA9/0xAA escape corruption bug by design.

### 1.6 RESETTED Propagation

When the adapter sends ENHResResetted:
- All external sessions receive ENHResResetted frame.
- Any pending START requests are cleared with failure notification.
- Wire phase tracker resets to Idle.
- Sessions that were mid-transaction see the reset and must re-arbitrate.

### 1.7 Adapter INFO

External sessions may request adapter INFO (hardware identity, firmware,
temperature, voltages):
- ENHReqInfo is forwarded to adapter through the multiplexer.
- ENHResInfo response is returned to requesting session.
- INFO is cached per multiplexer startup (from proxy pattern).

### 1.8 Backpressure

Session send buffer: 8KB default (configurable).
When buffer fills:
- Session is forcibly closed.
- Dropped/closed counters incremented.
- Ownership released if held.
- Log warning with session ID.

This matches the proxy's backpressure model for ebusd compatibility.

### 1.9 Differences from Standalone Proxy

| Feature | Standalone Proxy | Embedded Endpoint |
|---------|-----------------|-------------------|
| Owner classes | N sessions, lowest-address wins | 2 classes: gateway-priority + external FIFO |
| UDP-plain | Supported | Not supported |
| TCP-plain | Supported | Not supported (ENH only) |
| Source policy leases | Soft reservation, 30min | Not needed (fixed addresses) |
| Local target emulation | Supported (M4) | Not supported |
| Echo suppression | Byte-level ownerObserverSeen | Frame-level, no escape bug |
| Stale START absorb | 50ms window | Same (from proxy M1) |
| Session count | Unlimited | Practical limit: 2-3 |

### 1.10 Falsifiability

Review fails if:
- ebusd cannot connect and send a bus command
- Echo suppression does not correctly suppress 0xA9-containing frames
- RESETTED is not propagated to external sessions
- Backpressure overflow behavior is not implemented
