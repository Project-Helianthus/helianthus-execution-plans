# Root cause and fix detail

Canonical-SHA256: `ddd1786c883f07395e417d63c71607b46f92b8968126363fd11c55b8e0d8de7d`

Depends on: 00-canonical.md (problem statement, outcomes, decision matrix).

Scope: detailed walk-through of the bug surface in `helianthus-ebusgateway/internal/adaptermux/mux.go:2315-2317` and the `helianthus-ebusgo/protocol/bus.go:1328-1378` classifier that the fix re-engages. Code-level reasoning that justifies AD01–AD10.

Idempotence contract: re-reading this chunk against the same checked-out gateway commit yields the same root-cause attribution; re-running the predicate evaluation against the same simulated byte stream yields the same routing decision modulo the fix being present or absent. The chunk does not mutate state; it documents the predicate.

Falsifiability gate: the gate predicate's truth table at `mux.go:2315-2317` is enumerable. For each of the 5 conjuncts in AD02, a unit test must demonstrate the gate's behaviour on both sides of the conjunction. If any conjunct cannot be exercised by a test (e.g., requires a real wire), the chunk's "5-conjunct rationale" is unfalsifiable and must be reduced.

Coverage: this chunk covers the WHERE (file:line locations of all touched code), the HOW (predicate construction, byte-forwarding mechanics, diagnostic flag plumbing), and the WHY-NOT (rejection rationale for directions A/B/D). It does NOT cover the WHEN (sequencing), which is in 91-milestone-map.md.

## Code surfaces touched (M3 implementation)

### 1. echoTracker accessors — `internal/adaptermux/echo_tracker.go`

Add public methods:

```go
// matchCount returns the cumulative number of echo matches consumed for the
// current gateway txn. Reset on markRequestStart, decremented on rollbackSent.
func (t *echoTracker) matchCount() uint64 { return t.totalSuppressed }  // already tracked

// writeCount returns the cumulative number of bytes the gateway has issued via
// recordSent / recordSentStructural / recordSentWithTime since the last
// markRequestStart. Distinct from len(expectedEchoes) which shrinks as matches
// consume.
func (t *echoTracker) writeCount() uint64 { return t.totalWritten }  // new field
```

Both fields are zeroed in `markRequestStart` to scope them per-txn. No lock change — already accessed under `stateMu` from the mux's classify path.

### 2. mux.go gate refinement — `internal/adaptermux/mux.go:2304-2330`

Insert BEFORE the existing P11 strict-drop branch:

```go
preMatchHead, hadPendingEcho := m.gatewayEcho.peekNextExpected()
matchWouldHit := !hadPendingEcho || (hadPendingEcho && symbol == preMatchHead)

// (existing matchEcho gated call — unchanged)

// F-NEW-29 (2026-05-23, plan fix-p11-midwrite-byte-routing-w21-26):
// First-byte arbitration revalidation. If we have not yet matched any echo
// for this gateway txn AND have written exactly one byte AND the wire byte
// is master-class AND it does not match our expected echo, treat this as
// a false arbitration win and forward the foreign byte to bus.go's
// existing first-byte-after-arbitration classifier (bus.go:1328-1378)
// which will raise ErrBusCollision and trigger sendWithRetries to retry.
firstByteSuspectArbLoss := false
if hadPendingEcho &&
    m.gatewayEcho.matchCount() == 0 &&
    m.gatewayEcho.writeCount() == 1 &&
    symbol != preMatchHead &&
    protocol.AddressClassOf(symbol) == protocol.AddressClassMaster {
    firstByteSuspectArbLoss = true
    m.activeTxn.firstByteSuspectArbLoss.Store(true)
}

activeExpects := m.gatewayTxnActive
if activeExpects && hadPendingEcho && !firstByteSuspectArbLoss {
    activeExpects = symbol == preMatchHead
}
```

The `firstByteSuspectArbLoss` flag short-circuits the strict P11 mid-write drop, allowing the byte to flow to `activeCh`. P11 strict drop remains active for all other mid-write mismatches.

### 3. diagnostic flag — `internal/adaptermux/diag.go`

Add to `activeTxnDiag`:

```go
firstByteSuspectArbLoss atomic.Bool  // F-NEW-29 — set when forward-not-drop fires
```

Add to the inactive-log format string:

```go
fmt.Printf("... firstByteSuspectArbLoss=%v ...", txn.firstByteSuspectArbLoss.Load())
```

### 4. bus.go side — no changes

The existing classifier at `bus.go:1356-1361` already handles foreign master-class echo as `ErrBusCollision`. The `sendWithRetries` collision retry path at `bus.go:374-396` already consumes that error with `collisionBackoffFloor` + `waitForSyn`. No ebusgo changes needed.

## Unit tests (M1)

See 00-canonical.md M1 section for test list. Tests live in `internal/adaptermux/mux_test.go` and `internal/adaptermux/echo_tracker_test.go`.

The four-test suite uses the existing P3 mock transport pattern (already used in `p3_test.go`); no new test-harness infrastructure required.
