# Observe-First Execution Plan 05: M0-M1 Foundational Execution

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `415745ffb6cd371c55f10fe486de24a355e6e140c0645e20b78f783f57b6cd20`

Depends on: Execution Plans 01-04. This chunk is the first implementation tranche and must not begin before the architecture/doc-gate chunks are accepted.

Scope: M0 documentation corpus work and M1 low-level instrumentation/passive tap execution ordering.

Idempotence contract: Reapplying this chunk must converge on one replay corpus, one observer interface, one passive tap stack, and one bounded observability store.

Falsifiability gate: A review fails this chunk if repo ordering is ambiguous, CI artifacts are not reproducible, or passive instrumentation can merge without the paired docs and replay evidence.

Coverage: Milestones M0-M1 from the source plan.

---

## Milestones and Issues

- Milestones are sequentially gated `M0 -> M1 -> M2 -> ... -> M9` unless a milestone is explicitly marked optional or parallel-track.
- `M8` tinyebus is the only parallel-track carve-out in this plan; all gateway/doc milestones before it remain ordered.
- Locked Decisions remain the authoritative source of intent. Milestone issue acceptance criteria intentionally restate the relevant subset for traceability, and on drift the Locked Decisions section wins until the issue text is updated in the same revision.
- Issue numbering is historical and not itself a sequencing signal; only the milestone placement and explicit execution-order lists define order.

### M0. Documentation skeletons and replay corpus

- Execution order inside M0 is explicit:
  1. `ISSUE-DOC-01`
  2. `ISSUE-DOC-02`
  3. `ISSUE-DOC-03`
  4. `ISSUE-DOC-04`
  5. `ISSUE-EG-00`
  6. `ISSUE-GW-00`

`ISSUE-DOC-01` `helianthus-docs-ebus`
- Create `DOC-01`, `DOC-02`, `DOC-03` as skeleton docs with locked decisions and milestone-owned placeholders
- Acceptance:
  - no critical architecture choice remains implicit
  - placeholder sections are clearly marked and owned by later milestones

`ISSUE-DOC-02` `helianthus-docs-ebus`
- Create `DOC-04`, `DOC-05`, `DOC-06`, and `DOC-09` as draft contracts
- Acceptance:
  - MCP/GraphQL/Portal split is fixed
  - watch-summary skeleton contract exists before M5
  - freeze markers are clearly deferred to later milestones

`ISSUE-DOC-03` `helianthus-docs-ebus`
- Create `DOC-07`, `DOC-08`
- Acceptance:
  - protocol caveats and validation runbooks exist before implementation starts

`ISSUE-DOC-04` `helianthus-docs-ebus`
- Rename/migrate all B555 references to `protocols/ebus-vaillant-b555-timer-protocol.md`
- Acceptance:
  - no stale links or old filename references remain

`ISSUE-EG-00` `helianthus-ebusgo`
- Add protocol-level replay/testdata fixtures for future observer-hook tests
- Acceptance:
  - fixtures exist under repo-local testdata for core request/response and error scenarios
  - the real B524 proof corpus required for CI is mirrored into repo-local `testdata`, not referenced only from a workspace-private path
  - fixture manifests identify the real captured B524 proof cases mirrored from `_work_register_mapping/B524/proof_2026-03-05/` that later M1/M4 parser/correlation tests must validate against; M0 does not claim parser correctness before the parser-owning milestones land

`ISSUE-GW-00` `helianthus-ebusgateway`
- Build gateway replay corpus for passive tap and shadow-cache scenarios
- Acceptance:
  - ENH/ENS-style replay fixtures cover B509, B516, B524, B555, short replies, ack-only replies, collisions, timeouts, delayed replies
  - `ebusd-tcp` degraded mode is covered by negative-path fixtures asserting zero passive events and unavailable passive/broadcast capabilities, not by synthetic passive replay traffic
  - the real proof-scan wire corpus required for CI is mirrored into repo-local `testdata`, not referenced only from a workspace-private path
  - replay corpus manifests include the real proof-scan wire cases mirrored from `_work_register_mapping/B524/proof_2026-03-05/`; parser/correlation correctness against those cases is proven in the later parser-owning gateway milestones, not claimed as complete in M0

### M1. Low-level instrumentation and passive tap

- Execution order inside M1 is explicit:
  1. `ISSUE-EG-01`
  2. `ISSUE-EG-02`
  3. `ISSUE-EG-03`
  4. `ISSUE-GW-17`
  5. `ISSUE-GW-01`
  6. `ISSUE-GW-01B`
  7. `ISSUE-GW-01C`
  8. `ISSUE-GW-02`
  9. `ISSUE-GW-03`
  10. `ISSUE-GW-03A`
  11. `ISSUE-GW-03B`
  12. `ISSUE-GW-18`
  13. `ISSUE-DOC-05`

- The M1 lane gained a post-matrix review extension on 2026-03-10. After the
  successful `T01..T88` artifact
  `20260310T121708Z-gw03-recovery-full88-v3`, adversarial and competitive
  review surfaced two `GW-03` correctness gaps that must settle before M1 can
  be closed.

`ISSUE-EG-01` `helianthus-ebusgo`
- Design a TinyGo-safe observer interface and extend `BusConfig`
- Acceptance:
  - no reflection
  - scope applies to every new exported observer or passive-support public type introduced by this feature in `helianthus-ebusgo`; unrelated existing public APIs are unaffected
  - no maps in hot-path event structs
  - no `time.Time` in exported observer event payloads; use primitive durations/timestamps only
  - event structs use primitive fields / fixed enums / slices with explicit ownership rules
  - descriptor lookup or watch-catalog references stay out of exported hot-path observer event structs; gateway-side consumers resolve descriptors out-of-band
  - the exported transport/protocol retry envelope needed by gateway dedup-budget validation is exposed as a stable config/constant surface rather than requiring the gateway to duplicate retry/backoff assumptions
  - nil/no-op path is allocation-safe
  - callback/event set is decision-complete
  - observer panic-containment policy is explicit

`ISSUE-EG-02` `helianthus-ebusgo`
- Wire observer events into `protocol.Bus`
- Acceptance:
  - events for arbitration, tx/rx, ack/nack, timeout, CRC mismatch, echo mismatch, retry, transaction duration
  - event set includes an attempt-complete callback emitted from inside `sendTransaction` before the successful attempt returns, carrying enough request/response content for the gateway to derive a stable `ActiveTransactionFingerprint`
  - event set also includes a logical request-complete callback emitted by `sendWithRetries`, with total duration, retry count, and final outcome
  - references to current method names such as `sendTransaction` and `sendWithRetries` are explanatory only; the stable contract is per-attempt complete versus logical request-complete semantics
  - observer invocations are panic-contained so a callback panic cannot kill `Bus.Run`
  - panic containment is per invocation; the observer path remains registered for subsequent transactions unless explicitly disabled by configuration or feature rollback
  - fingerprint-emission failure or observer panic is surfaced as an explicit fault/metric so downstream dedup can enter a conservative degraded mode rather than silently losing active-match evidence
  - all bus consumers continue to compile
- Validation:
  - repo-local unit tests
  - tests prove observer panic does not terminate the bus loop or strand pending `Send` callers
  - tests prove fingerprint-emission failure is observable and does not silently masquerade as a correct dedup path
  - tests prove attempt-complete and request-complete duration semantics across retries are explicit and stable
  - no claim that `T01..T88` is an ebusgo unit suite

`ISSUE-EG-03` `helianthus-ebusgo`
- Surface transport reset events needed by passive consumers
- Acceptance:
  - ENH/ENS `RESETTED` can be detected by passive consumers instead of being silently swallowed as ordinary stream continuation
  - the passive stack can hard-reset reconstruction state immediately when the adapter resets due to primary-connection init/reconnect
  - primary connection behavior remains compatible with existing transport semantics
- Validation:
  - repo-local tests prove reset events are surfaced without corrupting subsequent byte reads

`ISSUE-GW-17` `helianthus-ebusgateway`
- Bump `helianthus-ebusgo` pin after the M1 ebusgo-side issues merge
- Acceptance:
  - `GOWORK=off go get github.com/Project-Helianthus/helianthus-ebusgo@<commit>`
  - `go mod tidy`
  - pin is committed before gateway work depending on new hooks

`ISSUE-GW-18` `helianthus-ebusgateway`
- Add passive-topology smoke coverage alongside the existing runtime matrix
- Acceptance:
  - `T01..T88` remains the active-topology gate
  - these passive-topology smoke cases are the concrete adapter/topology families that must be proven for M1; M1 may not pass with an empty passive-family proof set
  - a dedicated passive-mode smoke subset covers at least:
    - `P01` direct `ENS`
    - `P02` direct `ENH`
    - `P03` proxy-single `ENS`
    - `P04` proxy-dual `ENS`
    - `P05` proxy-dual `ENH`
    - `P06` negative-path `ebusd-tcp` degraded mode with no passive capability
  - the subset is fixed in docs and CI, not selected ad hoc per run
  - observer hooks and passive cohabitation are exercised at topology level, not only by replay tests
  - if this issue proves the current `passive_delivery_budget` or derived dedup timing defaults too small for a supported topology, this issue owns freezing revised timing constants and the corresponding doc update before M1 can close
  - any such timing-constant revision forces rerun of any later proof or replay evidence that depended on the older constants; M7 may not reuse pre-revision evidence silently
  - failure of this issue blocks M1 completion and any later default-flip work for the affected topology until the passive smoke evidence is green again
- Status note:
  - the first clean artifact from the repo-owned passive suite,
    `results-matrix-ha/20260311T062516Z-gw18-passive-smoke-v4/index.json`,
    landed with `0 pass / 6 fail / 0 blocked`.
  - harness-side false negatives discovered during bring-up were fixed inside the
    `ISSUE-GW-18` branch before this artifact (`signal-before-connect` preflight
    and canceled-context cleanup).
  - the remaining failures are tracked as `ISSUE-GW-18A` and `ISSUE-GW-18B`.

`ISSUE-GW-18A` `helianthus-ebusgateway`
- Investigate and fix supported passive smoke failures on `P01..P05`
- Trigger:
  - discovered by `ISSUE-GW-18` artifact
    `results-matrix-ha/20260311T062516Z-gw18-passive-smoke-v4/index.json`
- Acceptance:
  - supported passive-capable smoke topologies prove passive availability or are
    explicitly reclassified with doc/plan updates in the same cycle
  - `P01`/`P02` direct `ENS`/`ENH` no longer stall at
    `ebus_passive_warmup_state=warming_up` with `confirmed=0`
  - proxy smoke cases no longer keep `devices=[]` while passive warmup remains
    incomplete
  - rerun passive smoke artifact is attached

`ISSUE-GW-18B` `helianthus-ebusgateway`
- Make the `ebusd-tcp` passive smoke negative path degrade cleanly
- Trigger:
  - discovered by `ISSUE-GW-18` artifact
    `results-matrix-ha/20260311T062516Z-gw18-passive-smoke-v4/index.json`
- Acceptance:
  - `P06` keeps gateway startup alive
  - passive state degrades to `unsupported_or_misconfigured`
  - no false `available` or `timed_out` passive outcomes are emitted on
    `ebusd-tcp`
  - rerun passive smoke artifact is attached

`ISSUE-GW-01` `helianthus-ebusgateway`
- Introduce `PassiveBusTap`
- Acceptance:
  - owns the passive connection
  - exposes logical post-escape-decoded bus symbols and lifecycle/reset signals to exactly one reconstruction stage
  - does not yet own the full transaction reconstruction state machine
  - is the single passive source feeding the classified passive pipeline for broadcast routing, bus observability, and shadow-cache correlation
  - no third bus connection is introduced
  - passive ENH/ENS connections do not send `INIT` on connect or reconnect
  - adapter-family capability probing proves whether passive byte streaming without `INIT` works; passive mode is not reported as available until this is established
  - consumes transport reset signals so primary-connection `INIT` / adapter reset cannot silently poison the passive parser state
  - detects passive transport loss and retries with bounded exponential backoff
  - enables TCP keepalive or equivalent transport-level dead-peer detection where supported
  - enforces a configurable idle/absence threshold so half-open passive sessions are reconnected
  - exports passive connection-health state needed for degraded-mode reporting
  - distinguishes endpoint unsupported/misconfigured from transiently disconnected
  - after the initial `5m` startup downgrade to `unavailable`, retries continue in background at max backoff unless the endpoint is classified `unsupported_or_misconfigured`
  - reconnect resets downstream reconstruction state before event flow resumes
  - shutdown drain/termination budgets are coordinated:
    - tap-to-reconstructor handoff/close budget defaults to `1s`
    - reconstructor/subscriber drain budget defaults to `4s`
    - these budgets run concurrently under the same parent `5s` shutdown deadline rather than sequentially summing beyond it
  - shutdown drains or explicitly terminates subscriber channels before transport close completes
  - malformed or incomplete escape sequences are surfaced as explicit decode/discontinuity faults and may not be delivered to the classifier as target/header bytes
  - tests/validation prove the `5m` startup timeout path transitions passive capability to `unavailable` with reason while background retries continue for endpoints not classified `unsupported_or_misconfigured`

`ISSUE-GW-01B` `helianthus-ebusgateway`
- Implement `PassiveTransactionReconstructor`
- Acceptance:
  - reconstructs full or partial direct-mode transactions from logical post-escape-decoded bus symbols
  - dispatches transaction flow from the parsed request target/frame type before entering later phases, so broadcast and master-master traffic use their legal early terminal paths rather than falling through the slave-response path
  - explicit state machine phases:
    - idle
    - request
    - wait-ack
    - wait-response
    - wait-final-ack
    - terminal/abandoned
  - validates request CRC and response CRC where applicable
  - emits:
    - completed passive transactions
    - partial/abandoned transactions with classified reason
  - handles:
    - request with no target response
    - NACK
    - timeout/abandon
    - broadcast request
    - master-master request
    - delayed slave response
    - collision/garbled reset
    - unexpected `SYN` while mid-transaction
    - partial-header corruption
    - final-ACK NACK / retransmission episode as ambiguous/non-direct-apply in v1
  - produces timing markers for busy accounting
  - is the single consumer of `PassiveBusTap` logical-symbol/feed output rather than opening another connection
  - acts as the classified-event fan-out point for downstream passive consumers
  - common classify-and-reject path reuses buffers and targets `< 1 alloc/op` on the Go `1.22` repo benchmark gate for rejected/non-retained traffic
  - completed transactions may allocate only for the final retained frame/data copy needed downstream
  - retained completed-transaction path must remain bounded-allocation, targeting at most one retained payload copy plus O(1) metadata allocations rather than per-subscriber duplication, with a benchmark target of `<= 4 alloc/op`
  - that retained-path allocation target is end-to-end for one retained classified transaction up to fan-out bookkeeping, not multiplied per subscriber; subscriber delivery may not clone retained payloads per downstream consumer
  - unexpected `SYN` is a hard reset boundary for in-progress reconstruction
  - recovery by the second unexpected `SYN` is a requirement, not only an aspiration
  - transport reset signals trigger an immediate reconstruction reset before any further bytes are interpreted
  - transport `ReadByte()` timeout while mid-transaction is treated as an abandon/no-progress signal
  - a transaction-level progress watchdog exists in addition to raw transport timeout handling, default `1s`, configurable `250ms..5s`
  - classified events carry immutable payloads and pre-stamped timing markers
  - per-subscriber dispatch uses explicit default buffers of `128` for critical and `32` for non-critical consumers
  - critical-subscriber overflow produces an explicit discontinuity/degraded signal plus subscriber reset/resync semantics; correctness-critical consumers may not continue as if they had a contiguous stream after overflow
  - built-in gateway subscribers recover through subscriber-owner restart/resubscription driven by the passive-pipeline supervisor owned by this component; recovery may not depend on an unspecified external actor noticing the degraded flag
  - shutdown while mid-transaction emits an explicit shutdown/discontinuity boundary to subscribers if it can be delivered within the bounded drain timeout; otherwise the partial in-flight transaction is discarded rather than emitted as a normal successful/abandoned protocol event
- Validation:
  - replay tests per state-machine phase
  - replay tests prove broadcast and master-master requests are emitted as successful classified terminals rather than abandoned transactions
  - replay tests for partial transaction timeout and recovery
  - replay test injects garbled length/data and proves recovery by the configured unexpected-`SYN` reset rule
  - replay test injects garbled delimiters between adjacent transactions and proves the reconstructor abandons unsafe correlation rather than applying a wrong-key shadow update
  - replay tests prove malformed escape sequences are turned into decode/discontinuity faults before target/header classification
  - allocation-focused benchmark/test proves the common reject path does not introduce per-transaction heap churn
  - the `Go 1.22 repo benchmark gate` means a repo-local benchmark target added by this issue and run with `go test -run '^$' -bench . -benchmem` under the pinned Go `1.22` toolchain in local CI/validation
  - benchmark results are taken on the repo's canonical validation platform `linux/arm64`; if a secondary host architecture is used locally, the canonical gate still runs on the pinned `linux/arm64` environment before acceptance
  - benchmark op granularity is fixed by the benchmark harness: one op is one reconstructed transaction candidate on the reject path, or one retained completed transaction on the retained path, never one raw byte
  - tests cover critical-subscriber backpressure/overflow without silent loss or raw-loop stalls and prove degraded/discontinuity signaling plus recovery behavior

`ISSUE-GW-01C` `helianthus-ebusgateway`
- Add active/passive deduplicator
- Acceptance:
  - active dedup inputs are derived from the successful attempt-complete observer event introduced in `ISSUE-EG-02`
  - active fingerprint retention is explicitly bounded and sized against worst-case supported passive delivery delay, default `2250ms`
  - the configured dedup timing budgets are validated against the retry/backoff envelope exported by `helianthus-ebusgo`; a pin bump that changes the envelope without updating the derived budget must fail validation
  - whole-bus observability keeps passive copies of Helianthus-originated traffic
  - dedup is the sole owner of the adjudicated passive-output stream consumed by shadow-correlation and watch-efficiency logic; those consumers may not subscribe to pre-dedup classified events directly
  - shadow-cache writes suppress passive duplicates of active-originated transactions
  - watch-efficiency counters suppress passive duplicates of active-originated transactions
  - successful-attempt dedup matching is explicit across retries: failed/NACK/collision attempts do not enter the suppressing match table, and ambiguous retransmission episodes are observability-only rather than trustworthy third-party candidates
  - dedup uses bounded recent transaction identity, not a hard-coded initiator address
  - dedup uses a short pending-passive grace window so passive-first arrival can still match a slightly later active fingerprint
  - pending-passive buffering is bounded by explicit capacity `256` and grace-time rules
  - grace-time sizing is derived from the configured worst-case active fingerprint publication horizon, including bounded retry/collision behavior, not only nominal passive-first jitter; default `1750ms`
  - unmatched pending passive events are released as unmatched traffic on grace expiry rather than retained indefinitely
  - pending-buffer overflow flushes the oldest releasable entry as unmatched traffic rather than silently dropping or unboundedly retaining events
  - passive reconnect, transport reset, or explicit discontinuity flushes pending dedup state and invalidates active match retention for cross-epoch matching so pre-epoch passive events cannot match post-epoch active fingerprints and post-epoch passive events cannot match pre-epoch active fingerprints
  - epoch-boundary flush discards stale pending entries rather than reclassifying them as trustworthy third-party traffic
  - if active fingerprint emission is known to have failed for a transaction/window, dedup enters a conservative degraded mode and may not silently reclassify passive copies as trustworthy third-party traffic for shadow/write-efficiency purposes
  - dedup degraded mode clears only after a healthy new epoch or successful fingerprint emission proves the active-match path healthy again
  - local-target master-master participation is tagged separately from third-party passive traffic and is excluded from `passive_hits` / `reads_avoided`
  - the dedup stage exports explicit `local_participant_inbound` accounting and uses the runtime local-address tracker rather than a fixed initiator/source address assumption
- Validation:
  - replay tests where the same active transaction is also seen on the passive feed
  - race-oriented tests prove no false passive apply when the passive event arrives before the active fingerprint is published
  - retry-heavy active cases prove the grace window still suppresses false third-party classification for Helianthus-originated traffic delayed by bounded retries
  - delayed-passive cases prove active retention remains long enough for supported passive delivery jitter
  - observer-failure cases prove missing active fingerprints surface degraded dedup behavior instead of silent passive misclassification
  - tests prove third-party traffic exits the grace buffer after timeout without requiring any active fingerprint
  - metrics prove no double counting of passive hits
  - dedup degraded-state and epoch-reset metrics are exported and exercised in tests

`ISSUE-GW-02` `helianthus-ebusgateway`
- Refactor `BroadcastListener` to consume classified passive events
- Acceptance:
  - old broadcast behavior preserved
  - implementation no longer owns a separate connection
  - implementation consumes pre-dedup classified passive events from `PassiveTransactionReconstructor`, not raw tap symbols
  - B516 broadcast delivery to the energy path remains intentionally pre-dedup and may not be suppressed by active/passive dedup filtering
  - downstream router delivery for correctness-critical broadcast events must not remain a silent drop-on-full queue; overflow must surface as an explicit fault/metric and degraded-state signal
  - any router/subscriber infrastructure changes required to satisfy that no-silent-drop rule are in scope of this issue rather than left implicit in unrelated follow-up work

`ISSUE-GW-03` `helianthus-ebusgateway`
- Add `BusObservabilityStore` and gateway Prometheus exporter
- Acceptance:
  - frame/error/family/length/busy/periodicity metrics
  - bounded recent-message ring buffer backs `busMessages`, default `1024`
  - bounded periodicity tracker backs `busPeriodicity`, default `256` tuples with `1h` stale eviction
  - all aggregate counters stay fixed-cost and do not depend on retaining unbounded message history
  - `BusObservabilityStore` overflow policy preserves aggregate-counter correctness: if recent-message buffering must evict under pressure, it evicts oldest retained records while still ingesting and counting the new event
  - Prometheus labels use bounded family/address buckets and remain within the explicit default series budget `1024`
  - reconstructor health/error metrics include garbled-reset recovery counts and classified-fan-out overflow/fault counts
  - M1 exports only the observability metrics whose backing state exists by M1; later shadow lifecycle, feature-flag, and write-confirm activation metrics are introduced by their owning M4/M5 issues rather than claimed as meaningful in M1
  - observability ingest is transport-aware and records transport-class/timing-capability metadata for active and passive event sources
  - passive tap lifecycle metrics include reconnect attempt counters and connected-state gauge/signal
  - passive outage/reconnect behavior preserves monotonic counters and exposes busy/periodicity warmup state
  - warmup progress is exported, including elapsed warmup window and completed-transaction progress toward readiness thresholds
  - adapter-reset/passive-epoch-boundary behavior is distinguished from full socket-loss outage in capability and warmup reporting
  - dedup degraded-state and epoch-reset metrics are exported
  - active timing-derived metrics that do not represent real bus timing on relay transports such as `ebusd-tcp` are suppressed or marked unavailable at the store layer rather than emitted as misleading values
  - busy/periodicity timing quality is documented or exposed as estimated unless the transport supplies true wire timestamps
  - custom Prometheus text exposition
  - expvar remains untouched

`ISSUE-GW-03A` `helianthus-ebusgateway`
- Bootstrap passive warmup from the current reconstructor snapshot when the
  observability store attaches after the passive tap has already emitted the
  initial `connected` discontinuity
- Acceptance:
  - the observability store checks current reconstructor/tap connectivity on
    attach and enters passive warmup without waiting for a future reconnect or
    reset boundary
  - a clean boot with passive traffic available does not remain stuck in
    `unavailable` or degrade to `startup_timeout` solely because the initial
    `connected` discontinuity was emitted before subscription
  - regression coverage exists for the "already connected before attach" path
  - the fix is documented as a `GW-03` follow-up discovered during the
    successful `T01..T88` matrix validation and immediately following dual
    review cycle on 2026-03-10

`ISSUE-GW-03B` `helianthus-ebusgateway`
- Wire the runtime local-address snapshotter into `BusObservabilityStore` so
  `local_participant_inbound` accounting is live in the gateway binary rather
  than falling back to the generic master bucket
- Acceptance:
  - `run()` wires `cfg.LocalAddressSnapshotter` from the active/passive
    deduplicator into `BusObservabilityStore`
  - frames attributable to the local participant are exported under the
    intended `local_participant_inbound` path
  - regression coverage exists for the runtime wiring path
  - the fix is documented as a `GW-03` follow-up discovered during the
    successful `T01..T88` matrix validation and immediately following dual
    review cycle on 2026-03-10

`ISSUE-DOC-05` `helianthus-docs-ebus`
- Update docs after M1 implementation
- Acceptance:
  - observer interface
  - attempt-complete vs request-complete observer semantics
  - passive tap architecture
  - escape-decoding layer assignment is explicit
  - passive reconnect, outage, and warmup semantics
  - Prometheus/expvar coexistence
  - `ARCHITECTURE.md` and related architecture diagrams are updated in the same milestone before M1 passive-pipeline code PRs can merge
