# Gateway-Embedded Proxy 02: Gateway Integration Paths

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `f600ff2254ab7a300399ff85496c41b9b8ff13a0149dc62b137735e13e84c011`

Depends on: [00-canonical.md](./00-canonical.md),
[10-architecture-and-mux-design.md](./10-architecture-and-mux-design.md).

Scope: Gateway active and passive path wiring through the multiplexer,
configuration flags, transport resolution changes, observe-first semantics
preservation. Covers milestones M0 (docs), M1 (multiplexer core), and
M2 (gateway integration).

Idempotence contract: Declarative-only. Reapplying this chunk must not create
new issues, mutate transport resolution logic, or weaken existing transport
mode guarantees.

Falsifiability gate: Review fails this chunk if: M0 doc-gate outcome is not
specified, M1 does not include unit test requirements with 0xA9 payload
coverage, M2 does not describe `resolveTransport()` routing, or T01..T88
regression gate is missing.

Coverage: Canonical Section 3 (M0, M1, M2).

## 1. M0: Architecture Spec + Doc Gate

Repos: `helianthus-execution-plans`, `helianthus-docs-ebus`

### 1.1 Execution Plan Lock

- Create EPIC issue on `helianthus-execution-plans`
- Create PLAN-01 issue for canonical plan package
- Lock plan as `.locked` (no code changes in this milestone)

### 1.2 Architecture Doc Update

- Add embedded multiplexer section to ARCHITECTURE.md
- Cover: topology diagram, multiplexer package location, active/passive path
  interfaces, external proxy endpoint overview
- Doc lives in `helianthus-docs-ebus` (DOC-01)

### 1.3 Matrix Extension Definition

- Define AD01..AD12 test IDs in docs
- Specify gate policy: T01..T88 + AD01..AD12 for adapter-direct PRs
- Document evidence format (log excerpts, counter values, pass/fail criteria)

### 1.4 Falsifiability

Review fails if:
- Architecture doc does not cover multiplexer topology
- AD01..AD12 definitions are absent from docs
- Plan package does not pass `validate_plans_repo.sh`

## 2. M1: Adapter Multiplexer Core

Repo: `helianthus-ebusgateway`

### 2.1 Package Structure

```
internal/adaptermux/
  mux.go              # Multiplexer core: connection, demux, lifecycle
  active_path.go      # RawTransport wrapper for gateway.Bus
  passive_path.go     # Filtered symbol stream (callback)
  arbitration.go      # Owner arbitration: gateway-priority, external FIFO
  echo_tracker.go     # Per-session echo tracking (byte-level + frame-level)
  wire_phase.go       # eBUS transaction phase tracker
  session.go          # External session management (ENH reader/writer)
  mux_test.go         # Unit tests
```

### 2.2 Core Interface

```go
type Mux struct {
    // Single adapter connection
    // Active path: RawTransport for gateway.Bus
    // Passive path: filtered symbol callback
    // External sessions: managed via AddSession/RemoveSession
}

func New(cfg Config) *Mux
func (m *Mux) Start(ctx context.Context) error
func (m *Mux) ActiveTransport() transport.RawTransport
func (m *Mux) SetPassiveCallback(fn func(PassiveEvent))
func (m *Mux) AddSession(conn net.Conn) (sessionID uint64, err error)
func (m *Mux) RemoveSession(sessionID uint64)
func (m *Mux) Close() error
```

### 2.3 Required Unit Tests

- Echo suppression with 0xA9 payload: verify no escape corruption
- Echo suppression with 0xAA (SYN) in payload: verify correct handling
- Gateway + external contention: gateway wins at SYN boundary
- External FIFO: multiple external requests serviced in order
- RESETTED propagation: all consumers notified
- Wire phase transitions: full state machine coverage
- Adapter disconnect: reconnection loop fires, consumers notified
- Passive path filtering: self-echo suppressed, third-party delivered

### 2.4 Falsifiability

Review fails if:
- Any unit test listed in 2.3 is absent
- Active path does not implement `transport.RawTransport`
- Passive path does not deliver third-party bytes via callback

## 3. M2: Gateway Active + Passive Path Integration

Repo: `helianthus-ebusgateway`

### 3.1 Configuration

New transport endpoint mode activated by URI scheme:

```
--adapter-direct enh://boiler.local:9999
```

Alternatively with explicit flags:

```
--transport adapter-direct --network tcp --address boiler.local:9999
```

Both forms are accepted. Adapter-direct is additive: existing transport modes
(enh, ens, ebusd-tcp, udp-plain, tcp-plain) are unchanged.

### 3.2 Transport Resolution

In `gateway.go` `resolveTransport()`:

```
if config.Protocol == TransportAdapterDirect:
    mux := adaptermux.New(adaptermux.Config{...})
    mux.Start(ctx)
    return mux.ActiveTransport()   // active path
    // passive path wired via mux.SetPassiveCallback()
```

The multiplexer is created during transport resolution and persists for the
gateway lifetime. The passive path is wired to `PassiveBusTap` via the
existing `OnPassiveTapEvent` callback mechanism — no new transport
connection is dialed for passive observation.

### 3.3 Passive Tap Wiring

Current flow (proxy-based):
```
resolvePassiveTransport() → dial TCP to proxy → read bytes → decode escapes
  → emit PassiveTapEvent
```

Adapter-direct flow:
```
mux.SetPassiveCallback() → mux delivers filtered symbols directly
  → emit PassiveTapEvent (no escape decoding needed, bytes already logical)
```

The `passiveTapDecodesWireEscapes()` and `passiveTapUsesProxyLikeObserverTransport()`
heuristics are bypassed entirely in adapter-direct mode — the multiplexer
handles everything internally.

### 3.4 Observe-First Semantics

No changes to:
- `PassiveTransactionReconstructor` — receives symbols as before
- `BroadcastListener` — routes broadcasts to router as before
- Shadow cache and deduplicator — merges active/passive state as before

The only difference: passive symbols are third-party only (zero self-echo),
which should reduce `corrupted_request` events and improve observe-first
coverage.

### 3.5 Regression Gate

T01..T88 must pass for this PR. Existing transport modes are not modified.
The adapter-direct path is additive and requires `--adapter-direct` flag to
activate.

### 3.6 Falsifiability

Review fails if:
- `resolveTransport()` does not handle `TransportAdapterDirect` protocol
- Passive path is not wired to multiplexer output
- T01..T88 regression is not demonstrated
- Active polling does not function on live bus with adapter-direct
