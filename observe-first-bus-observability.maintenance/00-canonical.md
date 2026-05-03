# Observe-First eBUS Watch Registry + Bus Observability

Revision: `v1.0-maintenance-reconciled`
Date: `2026-03-09`
Status: `Maintenance`
Maintenance since: `2026-03-29`

Lifecycle note: all non-deferred milestones are complete. M8/tinyebus was
re-homed to `common-firmware-rewrite.locked`; record-only remains the canonical
default after the GW-16 non-promotion/default-state decision.

## Summary

- This feature is an architecture change, not a metrics add-on.
- It changes:
  - how Helianthus observes eBUS traffic
  - how it decides whether to poll
  - how it updates semantic state from observed traffic
  - how it exposes bus evidence to Prometheus, MCP, GraphQL, Portal, and later HA
- The target operating model is `observe-first, query-on-gap`:
  - observe bus traffic passively where transport permits
  - correlate request/response pairs conservatively
  - update a bounded `ShadowCache` only when confidence tier is sufficient
  - let `SemanticReadScheduler` avoid active reads when a watcher already has a fresh eligible value
  - surface both bus telemetry and watch efficiency
- `query-on-gap` means the active read path executes only when no eligible scheduler/shadow value exists for the caller's bounded freshness policy, or when invalidation/policy rules have explicitly disqualified the cached evidence.
- In other words, `observe-first` is the overall architecture, while `query-on-gap` is the concrete read-path behavior inside that architecture.
- Lettered subsections in this document (`3A`, `3B`, etc.) are used only where a numbered section is split into independently referenced contracts and the extra label materially improves navigation; unlettered sections may still contain multiple rule clusters, and the mixed numbering is intentional.
- Delivery order is strict:
  1. `helianthus-docs-ebus`
  2. `helianthus-ebusgo`
  3. pin bump in `helianthus-ebusgateway`
  4. `helianthus-ebusgateway`
  5. optional `helianthus-ha-integration` consumer rollout
- `helianthus-tinyebus` T0 raw-observability work is a post-M1 parallel track once the shared metric contract is stable, which in this plan means after `ISSUE-GW-03` and `ISSUE-DOC-05` have frozen the initial gateway metric names/semantics; it is not gated on the M7 default-flip proof because it only ships raw collector/exporter surfaces, not gateway observe-first semantics.

## Adversarially Locked Decisions

### 1. Source model

- `active` means traffic initiated by Helianthus on the primary connection.
- `passive` means traffic observed from a separate passive feed.
- `ebusd-tcp` is `active-only`.
- No synthetic `passive` estimates are allowed.

### 2. Passive architecture

- There will be exactly two gateway bus connections in passive-capable mode:
  - one primary active connection for Helianthus bus I/O
  - one passive tap connection for observation
- There will not be a third dedicated broadcast-only connection.
- `BroadcastListener` is not kept as an independent connection owner.
- The passive pipeline is explicitly two-level:
  - `PassiveBusTap` owns the passive connection and emits logical bus symbols plus lifecycle/reset signals
  - `PassiveTransactionReconstructor` is the single raw-stream consumer and emits classified passive events
- `BroadcastListener` will be refactored into a consumer/facade over the classified passive event bus:
  - `BroadcastListener` subscribes to classified passive events and filters broadcast frames
  - observability and shadow-cache correlation also subscribe to classified passive events

### 3. Passive decoding model

- The current passive parser in gateway is insufficient for observe-first cache updates because it only parses master telegrams with full headers.
- The new passive path must decode full direct-mode transactions from logical bus symbols, not just broadcast frames.
- B524 `dual-namespace` groups in this document mean the documented B524 group ranges where the same selector shape can resolve to more than one decoder/register namespace, so passive decoder selection may remain ambiguous without matching active watch-descriptor context.
- `PassiveBusTap` emits logical bus symbols and lifecycle/reset events, not domain-classified transactions.
- Logical bus symbols are post-transport, post-eBUS-escape-decoding symbols; CRC and length validation operate on these decoded symbols.
- The tap/reconstructor interface is a typed stream of:
  - `LogicalBusSymbol { byte_value, observed_at_monotonic }`
  - lifecycle/reset/discontinuity events carried out-of-band from the symbol stream
- `observed_at_monotonic` is the gateway-local monotonic receive/completion timestamp at which the decoded symbol became available to the passive pipeline; it is the authoritative ordering timestamp for shadow write-ordering unless a transport contract explicitly upgrades that source.
- `observed_at_monotonic` is process-local ordering metadata only; it may not be serialized, persisted, or used as a public/API timestamp. Any exported/public timestamp uses a separate wall-clock field.
- Architecturally, eBUS escape decoding is a dedicated passive-pipeline sublayer between transport byte framing and `LogicalBusSymbol` emission; target-byte classification must never consume undecoded escape prefixes.
- `PassiveTransactionReconstructor` must emit at least four classified event classes:
  - `PassiveMasterFrame`
  - `PassiveBroadcastFrame`
  - `PassiveTransaction`
  - `PassiveAbandonedTransaction`
- `PassiveMasterFrame` is the successful classified terminal for master-master exchanges that end after master telegram + ACK + delimiter and have no slave-response phase.
- The `PassiveMasterFrame` name is reserved only for that successful master-master terminal shape; broadcasts always use the distinct `PassiveBroadcastFrame` class.
- `PassiveTransaction` must reconstruct the frame-type-applicable protocol phases:
  - initiator request frame
  - target ACK/NACK
  - target response payload
  - final initiator ACK
  - timing markers needed for busy-time accounting
- The required timing markers are:
  - request start
  - request end / delimiter
  - response start when a response phase exists
  - response end or terminal delimiter
  - final terminal/delimiter timestamp for the classified event
- Reconstructor control flow must dispatch on the parsed master-telegram target/frame type as soon as the request header is available:
  - broadcast target: `request -> terminal-on-delimiter`, with no ACK/response expectation
  - master-master target: `request -> wait-ack -> terminal-on-delimiter`, with no slave response expectation and no `wait-response` phase
  - master-target/slave target: `request -> wait-ack -> wait-response -> wait-final-ack -> terminal` path applies
- Frame-type classification is derived from the raw target byte using the shared eBUS address classification rules (`broadcast`, `initiator-capable`, `target/slave`) and does not require device-registry lookup.
- Those shared eBUS address classification rules are owned by the exported protocol-layer classifier in `helianthus-ebusgo`; gateway passive code must reuse that authority rather than re-implementing divergent address-class logic.
- Reserved or invalid target-byte values such as `0x00`, `0xFF`, or delimiter/reserved symbols in target position must be classified as corrupted/abandoned input, never as a successful terminal frame type.
- `unexpected SYN` is only an error/reset boundary when it is illegal for the current frame-type-specific phase, not when it is the valid terminal delimiter for broadcast or master-master traffic
- Partial request/header corruption before a valid header is complete must be classified explicitly as abandoned partial-header state, never as a successful frame and never as a direct-apply candidate.

### 3A. Passive tap lifecycle

- `PassiveBusTap` is a long-lived service, not a fire-once goroutine.
- Loss of the passive socket must not permanently disable passive observability until gateway restart.
- On ENH/ENS enhanced transports, the passive tap must not send `INIT` during connect or reconnect.
- Passive ENH/ENS operation relies on passive byte streaming without triggering adapter-wide `RESETTED` side effects.
- Adapter capability discovery and any control-plane init/handshake remain owned by the primary connection, not the passive tap.
- Required lifecycle behavior:
  - detect transport closure and passive connection loss
  - detect transport-level reset signals such as ENH/ENS `RESETTED` that may be triggered by the primary connection
  - enable TCP keepalive where the transport exposes a TCP socket
  - use a configurable idle/absence threshold so a half-open passive connection can be treated as suspected-dead and reconnected
  - transition passive capability to unavailable during outage
  - retry connection with bounded exponential backoff
  - reset `PassiveTransactionReconstructor` state on reconnect
  - reset `PassiveTransactionReconstructor` state immediately on an observed transport reset signal before any further symbol processing
  - resume downstream fan-out only after the passive feed is healthy again
- Passive absence is defined as no logical bus symbols received for the threshold window.
- Whether a transport may be `legally fully silent` is a documented per-transport-family capability flag established by protocol/transport docs and mirrored into runtime capability data; it is not guessed from transient idleness alone.
- For transports that emit idle/delimiter symbols during a healthy quiet bus, those symbols count as ingress and prevent absence-triggered reconnect.
- For transports that may be legally fully silent, the absence threshold is only a dead-peer suspicion signal; reconnect requires either transport keepalive failure, explicit socket/read failure, or a longer hard-silence timeout confirming the session is not merely observing an idle bus.
- Default passive absence threshold is `10s`, configurable in the range `5s..30s`.
- Default hard-silence timeout for legally silent transports is `60s`, configurable in the range `30s..5m`.
- If passive absence threshold and hard-silence timeout would fire at the same instant, hard-silence timeout wins as the stronger dead-peer confirmation and collapses the absence suspicion into the same single reconnect sequence rather than double-firing reconnect logic.
- More generally, once hard-silence has already fired for a given passive episode, the weaker absence-threshold path may not later fire a second independent reconnect for that same episode.
- Default passive reconnect backoff is exponential with full jitter:
  - initial delay `1s`
  - multiplier `2x`
  - max delay `30s`
  - retries continue until shutdown while endpoint state is not `unsupported_or_misconfigured`
- Passive endpoint states must distinguish:
  - `unsupported_or_misconfigured`: second connection never established or capability probe disproved support
  - `temporarily_disconnected`: endpoint previously worked and is under reconnect
- Endpoint state and passive capability state are separate trackers in v1:
  - endpoint state answers whether the passive endpoint exists and is connectable
  - passive capability state answers whether the passive pipeline is currently trustworthy/usable for observe-first semantics
  - `passive_capability_unavailable_reason` is derived from these trackers and from warmup/degradation logic; it does not replace endpoint state internally
- Passive no-`INIT` streaming on ENH/ENS is a transport capability to be proven per adapter family in M1, not an unconditional assumption across all enhanced adapters.
- The proof split is explicit:
  - M1 lab validation proves whether a given adapter family supports passive no-`INIT` streaming at all
  - runtime capability probing only determines whether the current adapter instance is healthy/usable within that already-documented family capability, and may not treat simple bus idleness as proof of `unsupported_or_misconfigured`
- If an adapter family is proven incapable of passive no-`INIT` streaming in lab validation, that family is `unsupported_or_misconfigured` for this feature in runtime and passive retries do not continue for it.
- Runtime passive activation must also watch for active-path degradation plausibly introduced by the passive connection itself; repeated primary-path degradation temporally correlated with passive connect/probe is grounds to withdraw passive capability for that adapter instance and record an explicit reason.
- For this probe logic, `temporally correlated` means the primary-path degradation event occurs while the passive tap is connected/probing or within `5s` after a passive connect/re-probe transition for that adapter instance.
- The runtime passive capability probe is explicit:
  - it begins on first successful passive connect for an adapter instance and on any later explicit re-probe after capability withdrawal clearance
  - the probe window closes only after both `30s` have elapsed and `3` successful active logical requests have completed, or when the governing outer `5m` startup/reconnect window expires, whichever happens first
  - during that window the gateway tracks primary-path disconnects, transport resets, or request-complete failures temporally correlated with passive tap presence
  - `repeated primary-path degradation` means either `>= 2` primary-path degradation events in one probe window or the same pattern across `2` consecutive probe windows
  - passive capability withdrawal requires both the repeated-correlation threshold above and one confirmatory A/B signal that the degradation disappears when the passive tap is disabled for a control window or immediate re-probe
  - if disabling the passive tap removes the correlated active-path degradation, passive capability is withdrawn for that adapter instance with reason `capability_withdrawn`
- probing is not a fourth capability state in v1; it is a sub-phase of `warming_up`
- the probe window and the Section 12A warmup window start on the same successful passive connect and run in parallel; they are not sequential gates
- Shutdown behavior:
  - `PassiveBusTap.Close()` stops new reads, drains or terminates subscriber delivery in a defined order, then closes the transport
  - shutdown drain/termination is bounded; default drain timeout is `5s`, after which remaining subscribers are terminated explicitly
  - subscribers must observe channel closure or an explicit terminal event, not an undefined cancellation race
  - passive-derived state may expire naturally by TTL during shutdown; no new writes start after close begins
- All observe-first-owned shutdown budgets in v1 share one parent `5s` shutdown deadline; sub-budgets such as compactor `1s` and reconstructor/subscriber drain budgets are carved out inside that single parent deadline, not stacked sequentially beyond it.
- The compactor sub-budget runs concurrently with the passive pipeline drain under that same parent deadline; it may not serialize ahead of or after the `PassiveBusTap`/reconstructor shutdown path in a way that exceeds the parent `5s` limit.
- Positive shutdown semantics are explicit: on gateway shutdown, compactor stop, tap stop, and reconstructor/subscriber drain all begin under the same parent deadline immediately; components that overrun their sub-budget are terminated by the shared parent timeout rather than queued sequentially.

### 3B. Passive timing and fan-out semantics

- Passive timing markers are application receive-time estimates unless the transport provides wire-time timestamps.
- ENH/ENS TCP buffering means busy-time and periodicity are estimated, not ground-truth bus wire timing.
- No API or metric may claim exact wire-time precision unless adapter-provided timestamps exist.
- Mid-transaction abandon sources are explicit:
  - unexpected `SYN`
  - transport reset signal
  - transaction no-progress watchdog expiry
  - transport `ReadByte()` timeout while mid-transaction, treated as an abandon/no-progress signal rather than a valid idle delimiter
- Default transaction no-progress watchdog is `1s` since last protocol-progress symbol, configurable in the range `250ms..5s`.
- `protocol-progress symbol` means any decoded bus symbol that advances or legally completes the current frame-type-specific state machine, including request bytes, ACK/NACK, response bytes, and the legal terminal delimiter for that frame type.
- ACK and NACK symbols therefore do satisfy the progress watchdog while the reconstructor is still in a phase that expects them; once an `ack_only` transaction terminates successfully, the watchdog no longer applies because the state machine has already reached terminal state.
- A symbol that is structurally accepted by the current reconstructor phase counts as progress even if a later CRC/decode check causes the transaction to be classified abandoned or ambiguous.
- If both transaction no-progress watchdog and passive absence threshold would fire around the same moment, the transaction watchdog wins first, resets the in-flight transaction state, and only then may connection-level absence handling escalate.
- For timeout-precedence rules in this document, `the same instant` means the two deadlines fall in the same monotonic timer-evaluation cycle or within `1ms`, whichever is stricter in the implementation.
- A final-ACK NACK / slave retransmit pattern is treated as an explicit ambiguous retransmission episode in v1 and is not eligible for direct-apply unless later promoted with proof.
- For ambiguous retransmission episodes, the retained observability payload is bounded to the last-seen response plus episode metadata/counters; v1 does not retain an unbounded chain of retransmitted payload copies.
- The classified-event bus is the fan-out point, not the raw tap.
- Fan-out rules:
  - timing markers are stamped before classified events are dispatched to subscribers
  - classified event payloads are immutable to subscribers
  - per-subscriber delivery uses bounded buffers
  - slow critical subscribers must not silently stall the raw read loop or silently drop correctness-critical events
  - critical-subscriber overflow is treated as an explicit passive-pipeline fault rather than hidden loss
  - this explicit-fault rule also applies to preserved downstream critical paths such as broadcast delivery into the semantic router; correctness-critical broadcast loss may not remain a silent cap-and-drop queue behavior
  - overflow fault handling is explicit:
    - the affected subscriber must receive or be associated with a discontinuity/degraded signal rather than silently resuming as if its stream were lossless
    - subscriber-local state that depends on contiguous event history must be reset or invalidated before normal processing resumes
    - recovery requires explicit resubscription, local-state reset, or equivalent subscriber resync step driven by the subscriber owner/component; silent best-effort continuation is not sufficient for correctness-critical consumers
    - for built-in gateway subscribers, that recovery is triggered by the passive-pipeline supervisor owned by the reconstructor/fan-out component; it must issue the reset/resubscribe action rather than leaving recovery to an unspecified external actor
- In v1 the `passive-pipeline supervisor` is the bounded lifecycle/control loop inside the reconstructor/fan-out owner; it is not a third independent pipeline layer and it owns degraded-state observation plus built-in subscriber restart/resubscribe triggers.
  - the passive-pipeline supervisor is itself supervised: panic, repeated restart failure, or watchdog deadlock must surface explicit degraded/error metrics and either restart the supervisor or force the passive pipeline into a visible degraded state rather than failing silently
  - if all critical subscribers are simultaneously degraded/unsubscribed, the passive classified-event pipeline is globally degraded: normal downstream delivery pauses, only lifecycle/discontinuity signals remain authoritative, and normal classified delivery resumes only after at least one critical subscriber is healthy again
  - for this global passive-pipeline recovery rule, a critical subscriber is considered `healthy again` only after it has resubscribed and either processed at least one post-reset classified event without fault or remained fault-free for `5s`, whichever comes first
  - this global passive-pipeline recovery rule is distinct from the dedup-specific degraded-state recovery in Section 4; the former governs reconstructor/fan-out health, the latter governs trust in active/passive match evidence
  - correctness-critical broadcast overflow must propagate back to this passive-pipeline supervisor as an explicit degraded signal; the supervisor then resets/resubscribes the broadcast path before normal classified delivery resumes
- Default classified-event subscriber buffers:
  - critical consumers: `128`
  - non-critical consumers: `32`
- Subscriber criticality is explicit in v1:
  - critical:
    - `BroadcastListener` / semantic-router energy path
    - dedup consumer
  - non-critical:
    - `BusObservabilityStore`
    - bounded debug/live-summary helpers
- Dedup owns the second-stage adjudicated passive-output stream used by:
  - shadow-correlation / external-write invalidation consumer
  - watch-efficiency accounting
  These consumers do not subscribe to the pre-dedup classified-event bus directly.
- Non-critical subscriber overflow may drop oldest/newest per consumer contract, but must emit a metric.

### 4. Active/passive deduplication

- Passive tap must not filter out Helianthus-originated traffic globally.
- Whole-bus observability must still count Helianthus traffic for:
  - busy ratio
  - whole-bus frame totals
  - source/destination traffic distribution
- In this document, `Helianthus traffic` means any transaction where Helianthus is a participant, whether initiator or local responder; only the shadow/write-efficiency treatment distinguishes those roles.
- A dedicated dedup stage is required for shadow-cache and watch-efficiency consumers.
- Dedup rule:
  - active path emits a recent `ActiveTransactionFingerprint`
- `ActiveTransactionFingerprint` and `PassiveTransactionFingerprint` are typed gateway-side structs with exactly these logical identity fields plus the captured passive/active epoch id used for match scoping; they are not free-form maps or implementation-defined blobs
  - in this document, `frame type` and `transaction class` refer to the same bounded fingerprinting enum
  - the bounded `frame type / transaction class` enum used by fingerprinting is:
    - `master_target`
    - `master_master`
    - `broadcast`
    - `local_participant_inbound`
    - `abandoned_partial`
  - `outcome class` in fingerprinting and `outcome` labels in metrics reuse the same bounded domain unless a metric explicitly narrows it
  - the bounded `outcome class` enum used by fingerprinting is:
    - `success`
    - `nack`
    - `timeout`
    - `collision`
    - `transport_reset`
    - `decode_reset`
    - `abandoned`
  - fingerprint identity is a deterministic transaction hash over exactly:
    - frame type / transaction class
    - initiator/source address
    - target address
    - normalized request bytes after CRC/escape handling
    - response class
    - normalized response bytes when present
    - outcome class
    Timestamp is not part of fingerprint identity; time only bounds retention/matching windows.
  - the stable fingerprint wire/byte encoding used for hashing is the ordered length-prefixed concatenation of:
    - frame type / transaction class enum
    - initiator/source address
    - target address
    - response class enum
    - outcome class enum
    - normalized request bytes
    - normalized response bytes when present
    Implementations may optimize the in-memory representation, but the logical field order and content are fixed by this contract.
  - `normalized request/response bytes` means the full canonical decoded protocol frame bytes from header through CRC inclusive when present, after transport framing and eBUS escaping are removed, excluding ACK/NACK/SYN control symbols and any timing metadata
  - the fingerprint `response class` is the same bounded gateway-side response-shape enum defined in Section 5A, derived from the raw attempt-complete event before hashing; `helianthus-ebusgo` does not need to own a second divergent response-class taxonomy
  - no implementation-defined extra fields may participate in fingerprint identity unless the shared contract and cross-repo tests are updated together
  - active fingerprint retention is explicitly bounded but must be sized against the worst-case passive delivery delay on supported passive transports
- successful active-attempt fingerprints are emitted from inside `sendTransaction` before control returns to outer request-handling layers
- active fingerprint publication is keyed to the successful attempt-complete event itself; `active_publish_budget` measures from logical request start to active fingerprint publication, not to later scheduler return or semantic publish
  - only successful attempt-complete events enter the active dedup match table; failed/NACK/collision/timeout attempts contribute observability and retry accounting but do not create suppressing dedup fingerprints
  - `ActiveTransactionFingerprint` is produced from a structured attempt-complete observer event, not reconstructed heuristically from separate tx/rx callbacks
- if active fingerprint emission fails or its observer path panics, the failure must surface as an explicit fault/degraded signal; dedup may not silently continue as if active matching were fully reliable
  - dedup uses the family policy engine's `response_class` classifier for fingerprint construction; it may not maintain a parallel independent response-class derivation path
  - passive path computes a matching `PassiveTransactionFingerprint`
- if a passive transaction matches a recent active fingerprint, it is treated as a passive copy of Helianthus-originated traffic
  - active fingerprints remain valid for dedup suppression even if a later invalidation epoch disqualifies the corresponding fetch result from shadow/scheduler use; dedup identity and shadow eligibility are intentionally separate decisions
  - dedup maintains a short pending buffer for unmatched passive events so near-simultaneous passive-first arrival can still match a just-late active fingerprint
- the pending-passive grace buffer is explicitly bounded by both entry count and grace timeout
  - pending-buffer internal ordering is explicit:
    - each entry carries `inserted_at`, `release_at`, and dedup epoch id
    - `oldest releasable` means the entry with the earliest `release_at`, tie-broken by FIFO insertion order
  - the grace timeout must be sized against the configured worst-case active fingerprint publication delay, including bounded retry/collision handling, not only passive-first arrival jitter
  - active fingerprint retention and pending-passive grace sizing must be coordinated so either arrival order remains matchable within the supported delay envelope
  - unmatched passive entries older than the grace timeout are released as unmatched third-party traffic and may not be retained indefinitely
  - if such an unmatched passive entry exits grace without a matching active fingerprint and its initiator equals the current known local bus address, it is Helianthus-originated observability-only traffic rather than trustworthy third-party traffic and may not seed generic shadow admission or watch-efficiency counters
  - if the pending buffer reaches capacity, the oldest releasable entry whose grace has already expired may be flushed as unmatched before accepting more; if no entry is yet releasable, dedup enters degraded mode and the overflowing passive event may not be promoted as trustworthy third-party traffic
  - passive connection epoch boundaries such as reconnect, transport reset, or explicit discontinuity flush the pending-passive buffer and invalidate the active dedup match table for cross-epoch matching; pre-epoch pending entries may not cross-match with post-epoch active fingerprints, and post-epoch passive events may not match pre-epoch active fingerprints
  - invalidating the active dedup match table means clearing all retained pre-epoch active fingerprints from the match table; they may not remain matchable after the epoch boundary
  - epoch-boundary flush discards pre-epoch pending entries; they may not be released as trustworthy third-party traffic
  - dedup epoch transition is atomic at contract level: pending entries and active fingerprints are match-eligible only when their stored epoch id equals the current dedup epoch id captured at match time
- Dedup degraded-mode recovery is explicit:
  - dedup starts in `degraded` until the first healthy epoch or successful active fingerprint emission proves the active/passive match path initialized correctly
  - degraded mode begins on known fingerprint-emission failure, observer panic, explicit discontinuity, passive epoch reset, or dedup-consumer critical overflow/reset
  - degraded mode ends only after:
    - a fresh healthy epoch boundary, or
    - a successful active fingerprint emission proves the active path healthy again and the passive side is healthy enough to accept matching under the same hysteresis window
  - a healthy epoch boundary means a new passive epoch where reconstructor state has been reset, the passive socket/feed is healthy, and at least one successful classified passive event has been delivered post-epoch without another discontinuity intervening
  - while degraded, passive copies that would normally depend on active-match suppression may contribute to whole-bus observability but may not be treated as trustworthy third-party inputs for shadow/write-efficiency purposes
  - ambiguous passive retransmission/NACK episodes are observability-only while degraded or healthy; they may not be released as trustworthy third-party shadow candidates
  - dedup-consumer critical overflow/reset forces the same contiguous-history reset as an epoch boundary: pending passive state is flushed, active match retention for matching is invalidated, and the stage remains degraded until recovery criteria are met
  - any exit from degraded mode is gated by the same hysteresis: both `5s` of healthy subscriber state and `10` post-reset classified events must have been satisfied, and exit occurs only when the later of those two conditions completes
  - equivalently, dedup state machine is:

| state | enters on | exits on |
|---|---|---|
| `healthy` | startup after first healthy epoch or successful recovery | fingerprint emission failure, observer panic, explicit discontinuity, passive epoch reset, critical overflow/reset |
| `degraded` | any of the entry conditions above | fresh healthy epoch or successful active fingerprint emission proving the path healthy again, plus the documented hysteresis |
- Default dedup sizing:
  - `active_publish_budget` is derived from the configured logical request-complete retry envelope plus publication allowance, not a magic constant
  - the derivation must be enforced by code or test against the exported retry/backoff envelope from `helianthus-ebusgo`; a pure prose reminder is insufficient
  - the enforcement assertion is explicit: configured `active_publish_budget` must be greater than or equal to the exported worst-case logical request-complete retry envelope plus the documented publication/jitter allowance, and validation fails if the exported envelope grows beyond that budget
  - the v1 arithmetic is explicit: `active_publish_budget = exported logical request-complete retry envelope + 250ms publication/jitter allowance`
  - under the current documented envelope frozen by `ISSUE-EG-01` and consumed after `ISSUE-GW-17`, the exported logical request-complete retry envelope is `1250ms`; therefore `1250ms + 250ms = 1500ms`
  - under the current v1 retry policy the derived default is `1500ms`
  - if retry counts, retry timing, or collision/backoff semantics change, `active_publish_budget` must be recomputed from that envelope rather than left at a stale constant
  - `passive_delivery_budget = 500ms`
    This is the current validated default for supported passive-capable topologies and must be re-validated by `ISSUE-GW-18` / `ISSUE-GW-15`; if a topology cannot satisfy it, the default flip may not apply to that topology until the budget is revised and re-proven.
  - `pending_grace_timeout = max(active_publish_budget, passive_delivery_budget) + 250ms match-slack allowance = 1750ms`
  - the first `250ms` is the publication/jitter allowance inside `active_publish_budget`; the second `250ms` is the separate match-slack allowance between published active fingerprints and passive pending-buffer release, not a duplicate unnamed constant
  - `1750ms` is only the current derived default; it is not an independent hard-coded constant and must be recomputed from the formula if any underlying budget changes
  - `active_fingerprint_retention = pending_grace_timeout + passive_delivery_budget = 2250ms`
  - any change to the exported retry envelope or to `passive_delivery_budget` requires recomputing `pending_grace_timeout` and `active_fingerprint_retention` in the same change set and invalidates any previously captured proof/matrix evidence that depended on the older values
  - `pending_passive_capacity = 256`
- When active and passive copies of the same transaction both exist, passive timing markers are authoritative for bus-level timing metrics; active timing remains authoritative only for gateway-local transaction metrics.
- Dedup scope is explicit:
  - active-initiated Helianthus transactions use the normal active/passive dedup path
    This includes Helianthus-initiated write-confirm read-back requests and their passive copies.
- successful active writes also emit dedup fingerprints for duplicate suppression, but they remain observability-only for read-avoidance accounting and may not create generic shadow-eligibility by themselves
  - those successful active-write fingerprints do enter the active match table, but only for duplicate suppression of their passive copies; they never count as passive-hit/read-avoidance evidence
  - transactions where Helianthus is a local target/responder in a master-master exchange are tagged as `local_participant_inbound`; they are counted for whole-bus observability totals and busy accounting, but they are not counted as third-party passive hits or read-avoidance events, they are not eligible for generic shadow direct-apply in v1, and they also are not suppressed as active-initiated duplicates
  - `local_participant_inbound` classification uses the adapter-scoped current local bus address exported by the active transport/session runtime through a dedicated local-address snapshot interface
  - that snapshot interface exposes at least:
    - `address byte`
    - `known bool`
    - `epoch uint64`
    It must be readable without blocking the hot dedup path on active transport internals.
  - address changes invalidate active dedup match retention and local-participant classification state by advancing the dedup epoch for the new address epoch
  - when the local address first becomes established for an epoch (`known=false -> true`), dedup advances epoch and any pre-establishment observability-only events remain non-promotable
  - if the local bus address is not yet known for the current epoch, potential local-target inbound master-master traffic is treated as observability-only and may not be promoted to third-party shadow/write-efficiency input until the address is established
- For matched active/passive duplicates:
  - keep the passive event for whole-bus observability totals
  - keep passive timing markers for whole-bus busy/periodicity tracking
  - suppress passive shadow-cache writes
  - suppress passive watch-efficiency counters such as `passive_hits` and `active_reads_avoided`
  - do not suppress active-confirmed shadow-cache writes
  - matched-duplicate suppression takes precedence over generic passive-vs-active shadow timestamp ordering: a passive duplicate that matches an active fingerprint is retained only for bus-level observability/timing, not as competing shadow evidence
- The dedup/output interface is explicit:
  - the classified-event bus carries raw classified passive events to `BroadcastListener`, `BusObservabilityStore`, debug helpers, and the dedup stage
- the dedup stage alone produces the adjudicated passive stream used by shadow-correlation and watch-efficiency consumers
- shadow-correlation and watch-efficiency logic may not independently subscribe to pre-dedup classified events and re-derive match state out of band
- `dedup_pending_flush_total{reason=capacity}` increments only when capacity pressure is the primary cause; if an entry is already grace-expired at flush time, `reason=grace_expiry` wins and capacity does not double-count that flush
  - flush-reason precedence is explicit:
  - `epoch_reset`
  - `critical_overflow`
  - `grace_expiry`
  - `capacity`
  The highest-precedence simultaneously true reason is the only emitted label value for a given flushed entry; this metric records the emitted entry reason, not merely the outer trigger that caused the flush loop to run.
- output overflow on the adjudicated dedup stream for `shadow_correlation` or `watch_efficiency` is treated as a dedup degraded-mode fault and triggers the same contiguous-history reset as an epoch boundary before normal output resumes
- Dedup identity must not rely on a hard-coded initiator address like `0x71`.
- Dedup must use transaction identity plus a bounded recent-time window because the initiator address may change after join/rejoin.

### 5. Cache update rule

- `CRC valid` is necessary but never sufficient.
- Confidence is categorical, not a floating score:
  - `high_confidence`: eligible for direct-apply if all other policy gates pass
  - `limited_confidence`: record/invalidate only
  - `no_confidence`: discard
- Confidence mapping is explicit:
  - `high_confidence` requires valid transaction reconstruction, the required family-specific correlation rule, successful family decoder selection/parse, an accepted `response class`, and an accepted semantic/direct-apply policy outcome
  - `limited_confidence` applies when reconstruction is valid but the evidence is incomplete or policy-limited for direct-apply, such as record/invalidate-only families, externally observed writes under conservative policy, or otherwise decodable-but-non-direct-apply observations
  - `no_confidence` applies when reconstruction, correlation, decoder selection, or payload shape is invalid/ambiguous enough that even record/invalidate handling is unsafe
- A passive cache update requires:
  - valid passive transaction reconstruction
  - request/response correlation, or a documented broadcast-family carve-out correlation rule
  - family-specific decode
  - response class accepted by policy
  - watcher semantic class accepted by policy

### 5A. Policy vocabulary

- `response class` means one of:
  - `value_bearing`
  - `ack_only`
  - `header_only`
  - `error_or_ambiguous`
- `response class` mapping is explicit:
  - `ack_only`: the transaction terminates successfully with positive ACK semantics and no response frame carrying value/header payload bytes
    This includes successful master-master transactions that end after ACK plus delimiter with no slave-response frame.
  - NACK terminals with no response payload are `error_or_ambiguous`, not `ack_only`
  - any transaction that actually carries a response frame, even if that frame is only one byte or otherwise undersized, is never `ack_only`; it becomes `header_only` or `error_or_ambiguous` according to decoder/shape validity
  - `header_only`: a response frame exists with structurally valid framing/selectors/status metadata but not enough decoder-valid bytes to be value-bearing
  - `value_bearing`: a response frame exists and satisfies the addressed decoder's minimum value-bearing length and shape
  - `error_or_ambiguous`: malformed framing, conflicting retransmission episode, invalid selector context, decoder ambiguity, oversized/truncated decoder shape, or any other case that is unsafe even for header-only handling
- Response-class classification is owned by the family policy engine as an explicit pre-policy step over reconstructed request/response shapes; the reconstructor emits raw transaction outcomes and payloads, not final `response class` labels.
- The raw/policy boundary is explicit:
  - `PassiveTransactionReconstructor` emits reconstructed request/response frames, ACK/NACK presence, terminal outcome, frame type, and phase/timing markers
  - the family policy engine alone maps that raw shape into the bounded `response class` enum used by cache/direct-apply policy and dedup fingerprinting
- `watcher semantic class` is exactly the watch descriptor semantic class:
  - `state`
  - `config`
  - `discovery`
  - `debug`
- There is no second distinct notion of “watcher class” beyond the semantic class above.

### 6. Family policies

- In this document, `family` means the bounded eBUS command/message family bucket used by the protocol and observability layers, such as `B509`, `B516`, `B524`, or `B555`.

- `B516`
  - first-class passive `direct-apply` candidate only through the dedicated energy merge path
  - the canonical B516 selector key dimensions for freshness/provenance tracking are exactly `(family=B516, target, period, source, usage)`
  - selector echo in response is part of the correlation proof
  - it is not a generic `ShadowCache` + scheduler key in v1
  - precedence for B516-derived energy remains owned by `energyMergeStore`, not by the generic shadow precedence rules
  - the B516 energy-merge precedence rule in v1 is explicit:
    - register-backed active energy values outrank broadcast-derived values at the merge layer
    - within the same source class, newer ingest time wins
    - a broadcast may refresh broadcast-derived freshness/provenance state without overriding a newer or stronger register-backed semantic value
- `energyMergeStore` or the downstream energy snapshot surface must carry broadcast last-seen / broadcast-health metadata so stale broadcast-derived values can be distinguished from fresh register-backed values after passive disruption
  - the generic request/response correlation rule in Section 5 does not apply to B516 broadcasts; B516 uses its dedicated broadcast selector-correlation rule
  - malformed, truncated, oversized, or decoder-inconsistent B516 payloads are `error_or_ambiguous` and may not update the energy merge path
  - `never_seen -> warming_up` is triggered by the first acceptable B516 broadcast observed while transport capability is `broadcast=true` and global passive capability is at least `warming_up`; the trigger is blocked while global passive capability is `unavailable`
  - `never_seen -> unavailable` occurs when transport capability becomes `broadcast=false` or global passive capability becomes `unavailable` before any acceptable broadcast has ever been observed for that selector
  - before the first acceptable broadcast has been observed on a broadcast-capable transport, broadcast freshness state is `never_seen`, not `stale`
  - on transports where `broadcast=false`, broadcast freshness state is `unavailable`, not `stale`
  - `never_seen` and `unavailable` are not mutually exclusive over the lifetime of one selector: `never_seen` is the pre-observation state while broadcast-capable passive coverage exists, and a later loss of that coverage legally transitions the selector to `unavailable`
  - `unsupported_or_misconfigured` passive capability has no in-process recovery path for B516 freshness in v1; recovery requires restart-level reconfiguration or later transport-family support change
  - the rolling observed period is not considered valid until at least `3` acceptable broadcasts have been observed for that selector
  - acceptable broadcasts observed during global passive `warming_up` still count toward that per-selector minimum-sample requirement; selector warmup may therefore advance in parallel with global warmup
  - per-selector B516 sample counting is per passive epoch: each selector maintains its own acceptable-broadcast count within the current passive epoch and restarts that count on passive epoch reset for that selector family
  - before that minimum sample count is reached, freshness uses the fixed `10m` floor and the selector remains period-estimate `warming_up`
  - if that fixed `10m` floor expires before the minimum sample count is reached, the selector transitions from `warming_up` to `stale`
  - if a selector is `stale` only because the fixed `10m` floor expired before the minimum sample count was reached, a later acceptable broadcast that still leaves the selector below the minimum sample threshold transitions `stale -> warming_up`, not directly `stale -> fresh`
  - once the minimum sample count exists and a rolling period estimate is valid, broadcast freshness is stale when no fresh broadcast has been seen for `max(2x rolling observed period, 10m)` capped at `30m`
  - `fresh -> fresh` on a newer acceptable broadcast refreshes last-seen time and recomputes the next stale deadline; it is not a pure no-op on freshness bookkeeping
  - stale broadcast-derived energy values remain queryable but must carry freshness/provenance metadata; they may not be silently presented as fresh
  - `never_seen` and `unavailable` do not expose a broadcast-derived value payload; MCP/GraphQL return no broadcast-derived value (null/absent by surface convention) together with the explicit freshness/provenance state
  - MCP and GraphQL must expose the same freshness fields for broadcast-derived energy: at least freshness state, last broadcast timestamp when known, and broadcast-health/provenance metadata
  - `broadcast-health/provenance metadata` means at least:
    - last acceptable broadcast timestamp when known
    - current passive epoch id
    - selector sample count in the current epoch
    - rolling observed period when valid
    - warmup reason when state is `warming_up`
  - when freshness state is `warming_up`, MCP and GraphQL must also expose a bounded `warmup_reason` enum with values:
    - `global_passive`
    - `selector_samples`
    If both conditions are simultaneously unmet, `warmup_reason=global_passive` wins because global passive readiness is the outer prerequisite.
  - this `warmup_reason` field is specific to B516 per-selector freshness surfaces; general passive capability warmup surfaces in Section 12A do not expose a second `warmup_reason` sub-field in v1
  - this does not prohibit the separate global diagnostic metric `passive_warmup_blocker_reason`; the two surfaces are intentionally distinct, with per-selector B516 freshness reasons on one side and gateway-global passive warmup blockers on the other
  - the closed broadcast freshness state set is:
    - `fresh`
    - `stale`
    - `warming_up`
    - `never_seen`
    - `unavailable`
  - valid broadcast freshness transitions in v1 are bounded to:
    - `never_seen -> warming_up`
    - `warming_up -> warming_up` on healthy-socket transport reset / passive epoch reset while selector/global freshness remains in warmup
    - `warming_up -> warming_up` on additional acceptable broadcasts while minimum-sample or global-passive prerequisites remain unmet
    - `fresh -> fresh` on a newer acceptable broadcast that preserves freshness
    - `warming_up -> fresh`
    - `warming_up -> stale`
    - `fresh -> stale`
    - `stale -> fresh`
    - `stale -> warming_up` when a new acceptable broadcast arrives but minimum-sample prerequisites remain unmet after a stale floor-expiry episode
    - `fresh -> warming_up` on healthy-socket transport reset / passive epoch reset
    - `stale -> warming_up` on healthy-socket transport reset / passive epoch reset
    - any state -> `unavailable` on loss of broadcast-capable passive coverage, startup timeout, reconnect timeout, capability withdrawal, transport-family change, or restart-level reconfiguration
    - `unavailable -> warming_up` when broadcast-capable passive coverage returns for the same static transport family after outage/reset recovery
    - `unavailable` does not transition back in-process only for transport-family-change or restart-level `unavailable` causes on static transport families
  - equivalently, the valid transition table is:

| from | valid to |
|---|---|
| `never_seen` | `warming_up`, `unavailable` |
| `warming_up` | `warming_up`, `fresh`, `stale`, `unavailable` |
| `fresh` | `fresh`, `stale`, `warming_up`, `unavailable` |
| `stale` | `fresh`, `warming_up`, `unavailable` |
| `unavailable` | `warming_up` after coverage returns for the same static transport family; otherwise none in-process for transport-family-change or restart-level causes |

  - Portal must render these same underlying states distinctly rather than collapsing `never_seen` and `unavailable` into one opaque UI state
  - B516 broadcasts may continue to update the energy merge path during global passive `warming_up`, but all resulting freshness/provenance state must continue to report `warming_up` until the relevant global/selector warmup criteria are met; no UI or API may silently present those values as fully warmed/fresh before that point
  - if a selector has met its own sample threshold while global passive capability is still `warming_up`, the effective exposed selector freshness remains `warming_up` with `warmup_reason=global_passive` until global capability becomes `available`
  - when global passive capability later becomes `available`, any selector that was blocked only by `warmup_reason=global_passive` auto-advances to its otherwise eligible state (`fresh` or `stale`) without needing a further broadcast
  - if selector sample sufficiency is still unmet at that moment, the auto-advanced state is `warming_up` with `warmup_reason=selector_samples`, not `fresh`
  - on healthy-socket transport reset / passive epoch reset, all previously seen B516 selectors, including those currently `stale`, re-enter `warming_up` and restart their per-selector minimum-sample counting from zero; previous sample history remains diagnostic only
  - passive epoch reset is global for the B516 selector family on that adapter instance; all B516 selectors share that family-level passive epoch boundary in v1
  - no new B516 broadcast evidence may update the energy merge path while global passive capability is `unavailable` or while transport capability reports `broadcast=false`; previously retained energy state may remain queryable only through its explicit freshness/provenance contract
- `B524`
  - passive `direct-apply` only for correlated read traffic
  - instance comes from the request context, not the response
  - if request context is missing or partial, the observation is `ambiguous` and may not direct-apply
  - if decoder selection remains ambiguous because multiple B524 namespaces/decoder candidates fit the observed request context, the observation is `ambiguous` and may not direct-apply
  - observed B524 write traffic follows the generic external-write policy from Section 7, not the correlated-read direct-apply policy
  - for B524 writes, the runtime `external_write_policy` fully governs write-side disposition in v1; the descriptor's read-side `correlation_policy=request_response` still governs only passive reads for that same key
  - short replies are defined by the addressed decoder's minimum value-bearing length, not a family-global byte threshold
  - any reply with payload bytes below the addressed decoder's minimum value-bearing length is `error_or_ambiguous`
  - oversized payloads beyond the addressed decoder's expected value-bearing shape are `error_or_ambiguous`, not truncated into a direct-apply value
  - header-only replies map to response class `header_only` and are not value-bearing
- `B509`
  - passive `direct-apply` only for payload-bearing reads
  - the canonical B509 key dimensions are exactly `(family=B509, target, register_address)`; selector wire-form variations do not change the semantic key
  - the classifier is the existing read parser rule:
    - `op+addr only` and `addr only` forms with no payload map to response class `header_only` and are not value-bearing
    - status-only responses map to response class `header_only` and do not update cache
  - truncated payloads are evaluated against the addressed decoder's minimum value-bearing length, not by a family-global byte threshold
  - any reply with payload bytes below the addressed decoder's minimum value-bearing length is `error_or_ambiguous`
  - oversized payloads beyond the addressed decoder's expected value-bearing shape are `error_or_ambiguous`, not truncated into a direct-apply value
- `B555`
  - v1 uses the generic conservative `record/invalidate` mode
  - no passive `direct-apply` by default
  - the canonical B555 key dimensions in v1 are `(family=B555, target, opcode, zone_or_circuit, day_selector, slot_selector)`
  - canonical doc path is `protocols/ebus-vaillant-b555-timer-protocol.md`

- Family-to-`direct_apply_policy` mapping in v1 is explicit:

| family / case | direct_apply_policy |
|---|---|
| `B516` broadcast-energy path | `energy_merge_only` |
| `B524` state reads with valid correlation | `state_default` |
| `B524` config reads explicitly whitelisted | `config_opt_in` |
| `B509` payload-bearing state reads | `state_default` |
| `B509` config reads explicitly whitelisted | `config_opt_in` |
| `B555` | `never` |
| `discovery` / `debug` descriptors | `never` |

### 7. State vs config policy

- `state`
  - passive `direct-apply` allowed
- `config`
  - passive `record/invalidate` by default
  - passive `direct-apply` only via explicit per-watcher opt-in
- external writes observed passively:
  - `invalidate-only` by default
  - the runtime effect of `external_write_policy` is subordinate to `observe_first_enabled`; when the master observe-first flag is off, Section 14 master-off semantics clamp `record_and_invalidate` to `record_only` and suppress invalidate-only side effects
  - this external-write policy applies to externally observed writes on matching keys regardless of whether the descriptor's read-side correlation mode is `request_response`, `broadcast_selector`, or one of the record/invalidate modes; the read-side correlation mode itself remains unchanged
  - when `observe_first_enabled=true`, the effective externally observed write behavior is exactly the runtime `external_write_policy`:
    - `record_only` => bounded audit record only
    - `invalidate_only` => invalidate-only
    - `record_and_invalidate` => bounded audit record plus invalidation
- Helianthus writes:
  - remain `write + read-back confirm`

### 7A. Invalidate-only semantics

- `invalidate-only` has an explicit operational meaning.
- `invalidate-only` means exactly the default external-write behavior defined below:
  - retain the already-cached pre-write shadow entry as bounded diagnostic/provenance state
  - do not record the newly observed external-write value as a scheduler-eligible replacement
  - invalidate scheduler/shadow eligibility for the old cached value until refreshed
- `record-only` has an explicit operational meaning:
  - retain the externally observed write as bounded diagnostic/audit evidence
  - do not alter scheduler freshness eligibility
  - do not create or refresh a scheduler-eligible shadow value from that external write
  - do not trigger an immediate provider write or immediate active fetch in v1
  - `record_and_invalidate` means the same bounded diagnostic/audit recording as `record-only`, plus the scheduler/shadow invalidation behavior defined below for `invalidate-only`.
- In v1, `bounded diagnostic/audit evidence` for external writes uses a per-adapter bounded ring with default capacity `256` records; it may not grow unboundedly with write traffic.
- That bounded ring evicts oldest-on-insert when full; eviction happens at write time before the new record is appended, never lazily at read time.
- Default behavior for an externally observed write is:
  - retain the current already-cached shadow entry for diagnostics/provenance
  - mark that entry invalidated/tombstoned for scheduler eligibility
  - clear or age out matching scheduler freshness so the next read cannot be satisfied from pre-write cached freshness
  - do not trigger an immediate provider write or immediate active fetch in v1
- Invalidated entries are not eligible shadow hits, even if they still carry a last-known value.
- Pinned entries may still be invalidated; pinning prevents capacity eviction, not semantic invalidation.
- Invalidated pinned entries must compact to tombstone metadata and may not retain full payload state indefinitely; the default rolling tombstone maintenance period is `15m` before compaction/refresh is required.
- The `15m` value is a rolling maintenance period before compaction, not a second independent hard deadline: successful refresh removes the tombstone entirely and therefore resets both the `15m` compaction period and the later `24h` hard tombstone horizon for the next tombstone lifecycle.
- Tombstone compaction is triggered by a bounded background sweep with default cadence `1m`, with optional opportunistic on-access compaction as a secondary optimization only.
- Default compactor batch size is `64` entries per critical section; larger batches require an explicit documented override because they weaken the bounded-locking guarantee.
- One compactor cadence tick means one whole-table sweep attempt broken into bounded `64`-entry critical sections; the compactor may not stop after a single batch and still claim the sweep complete.
- After compaction, a pinned tombstone still consumes pinned cardinality budget for that key, but only metadata budget, not retained payload memory; if refresh remains impossible it ages toward the hard `24h` tombstone lifespan from Section 10, after which it may be de-pinned from `ShadowCache` while the watch remains active in `WatchCatalog`.
- `successful refresh` means any accepted non-tombstone shadow write for that key (`active_confirmed` or eligible passive write) that recreates a normal shadow entry; scheduler-local `lastOK` updates alone do not count as tombstone refresh.
- The `15m` tombstone compaction clock starts at the first invalidation/tombstone timestamp for that entry, not at write-confirm activation creation or expiry.
- `compaction` means stripping retained payload/value bytes while keeping tombstone metadata: canonical key, invalidation reason, timestamps, pin metadata, and generation/epoch metadata required for correctness.
- `de-pin` is triggered when the `24h` hard tombstone lifespan expires without successful refresh; it is not an arbitrary opportunistic eviction.
- The next poller read re-establishes freshness through the normal active or eligible passive read path.
- Invalidation of a key uses one atomic key-local helper path that both advances the shared generation domain and clears scheduler freshness for that key before subsequent reads observe the new state.
- The background compactor is a supervised worker: panic or repeated failure must surface explicit fault metrics and the worker must be restarted or the cache marked degraded rather than silently stopping tombstone maintenance.
- The background compactor may not hold the `ShadowCache` lock across a full-cache sweep or across notification delivery; it uses bounded per-entry or per-batch critical sections so compaction cannot stall the read/write path indefinitely.
- The `bounded-locking guarantee` for the compactor means no reader/writer path waits behind more than one `64`-entry compactor batch critical section.
- On shutdown, the background compactor must observe the shutdown signal and finish or abandon its current batch within `1s`; it may not prolong gateway shutdown indefinitely.
- `shadow_tombstone_compactions_total` increments exactly once when an entry transitions from payload-retained tombstone to metadata-only tombstone.
- `shadow_tombstone_depins_total` increments exactly once when a metadata-only tombstone leaves the pinned set after the `24h` hard lifespan rule.

### 8. ShadowCache vs SemanticReadScheduler

- `ShadowCache` does not replace `SemanticReadScheduler`.
- `ShadowCache` sits upstream of the scheduler.
- Responsibility split:
  - `ShadowCache`
    - stores observed evidence
    - stores source, confidence, freshness, timestamps, precedence
    - accepts both passive and active-confirmed evidence
  - `SemanticReadScheduler`
    - remains the coalescing layer
    - remains the active read freshness cache
    - remains the circuit breaker owner
- In v1 the scheduler instance is adapter-scoped and paired with the adapter-scoped `ShadowCache` budget domain for that same adapter instance; there is no cross-adapter shared scheduler cache in this feature.

### 8A. Shadow eligibility checklist

- A shadow value is eligible only when all of the following are true:
  - matching active watch descriptor exists for the canonical key
  - `observe_first_enabled=true`
  - the descriptor/policy path allows shadow satisfaction for that semantic class
  - the entry is not invalidated/tombstoned for scheduler purposes
  - the entry is within `min(caller maxAge, resolved descriptor freshness_ttl)`
  - confidence tier and response class satisfy the family policy
  - post-lock scheduler/shadow revalidation still passes
- Read path:
  1. scheduler receives `Get(key, maxAge, fetch)`
  2. scheduler checks whether `ShadowCache` has an eligible value for that key
  3. if yes, scheduler returns that value and seeds/refreshes its own `lastOK`
  4. otherwise scheduler performs active fetch as today
  5. successful active fetch updates both scheduler cache and `ShadowCache` as `active_confirmed`
- `fetch` is the caller-supplied active-read closure for that key. It performs one active read attempt chain under current transport/protocol rules and returns the raw value bytes/result or an error.
- The 5-step list above is logical, not mutex-accurate pseudocode; implementation must follow the separate consult/revalidate/commit rules below.
- Shadow-read ordering rule:
  - `ShadowCache` consultation happens outside the scheduler mutex
  - once the scheduler mutex is acquired, both scheduler state and shadow-entry validity/version must be revalidated before committing to a shadow hit
  - that post-lock shadow revalidation uses a lock-free or atomically readable shadow generation/eligibility snapshot exported by `ShadowCache`; it may not reacquire the full `ShadowCache` mutex while holding the scheduler mutex
  - the abstract snapshot contract is:
    - `SnapshotEligibility(key) -> {present bool, eligible bool, generation uint64, state enum}`
    - the returned tuple must be atomically self-consistent for one instant, but need not freeze subsequent concurrent writes
    - v1 implements this as a versioned per-key atomic snapshot record (single atomic read or retry-until-stable equivalent); seqlock-style or packed-struct approaches are acceptable, but the exported semantics are one atomic logical snapshot
    - valid `state enum` values are:
      - `present`
      - `invalidated`
      - `tombstone`
      When `present=false`, `state` is ignored by callers.
    - here `eligible bool` is the full scheduler-facing answer after freshness/invalidation checks, while `state enum` is the bounded storage-state classification
    - this `state enum` is exactly the same bounded domain used by `shadow_entries{state}` metrics; runtime state and metric labels may not diverge
  - the start-generation/invalidation token captured for active fetches and the post-lock generation/eligibility snapshot are the same opaque per-key generation domain, viewed at different moments in the read lifecycle
  - if, when the scheduler mutex is acquired, coalescing has already completed, scheduler freshness is already newer, or shadow invalidation/newer generation has appeared since the earlier shadow observation, that earlier shadow observation is discarded and the decision is recomputed
  - this makes shadow consultation advisory until post-lock revalidation, and repeated shadow checks under contention are acceptable
  - repeated consult/revalidate cycles are bounded; per `Get()` call, implementation may perform at most two shadow consult/revalidate passes before the first active/coalesced/fail-closed decision, plus at most one immediate recompute cycle after an invalidation-race discard
  - if a post-lock shadow revalidation fails because the candidate became ineligible between outside-lock consult and inside-lock check, one more consult/revalidate pass may occur within that bound; after the bound is exhausted the call falls through to the documented active/coalesced/fail-closed path
  - the global per-`Get()` retry budget is bounded: consult/revalidate passes plus one allowed immediate recompute after an invalidation-race discard may not compose into an unbounded loop
  - after an invalidation-race discard, the architecture-level recompute priority is explicit: join an existing coalesced fetch if present; else start one active fetch if the breaker allows; else fail closed as unavailable/error
  - per `Get()` call, the caller-supplied `fetch` closure may be invoked at most twice total: one initial active fetch attempt chain and at most one immediate recompute fetch after an invalidation-race discard
- Circuit-breaker rule:
  - freshness/maxAge eligibility is evaluated before breaker state is consulted; an expired or otherwise ineligible shadow entry may not bypass the breaker
  - eligible shadow hits bypass the active-read circuit breaker guard
  - the breaker protects only against active fetch attempts
  - a shadow hit while the breaker is open may refresh scheduler `lastOK`, but does not reset or heal the breaker's active-failure counters by itself
  - such a refresh is not considered a prohibited stale fallback, because only entries that already passed the freshness/maxAge eligibility checks may bypass the breaker
  - only successful active fetches affect breaker recovery semantics
- Freshness rule:
  - the upper bound for a shadow hit is always the caller's `maxAge`
  - descriptor `freshness_ttl` may further restrict eligibility, but may never widen it
  - effective shadow freshness limit is:
    - if `maxAge <= 0`: shadow hit not allowed and the call behaves as a shadow-bypass read
    - else `min(caller maxAge, descriptor freshness_ttl)`
  - descriptor `freshness_ttl` is still load-bearing even when default caller profiles are narrower: it becomes the binding constraint for family/key-specific tighter descriptors and for tooling or future callers that request a wider `maxAge` than policy allows
  - hierarchical `freshness_ttl` resolution order is explicit:
    - exact descriptor/key-specific `freshness_ttl` if present
    - otherwise family-generated descriptor default when one exists
    - otherwise the freshness-profile default
    When more than one documented default could apply, the tighter/smaller TTL wins.
- Observe-first caller freshness policy:
  - the current `500ms` scheduler call sites are treated as legacy active-read coalescing defaults, not as acceptable long-term shadow freshness ceilings
  - M5 must introduce per-key or per-freshness-profile caller `maxAge` profiles for observe-first paths
  - default caller `maxAge` profiles are:
    - `state_fast`: `5s`
    - `state_slow`: `15s`
    - `config`: `60s`
    - `discovery`: `5m`
    - `debug`: `0` unless tooling overrides explicitly
  - family- or key-specific callers may tighten these defaults, but may not widen beyond descriptor `freshness_ttl`
  - no observe-first B509/B524 state-read path may keep a hard-coded `500ms` freshness ceiling after M5 lands
- Breaker contention note:
  - v1 does not auto-tune breaker thresholds from passive-health signals
  - breaker oscillation under shared-bus contention is an accepted limitation in v1 as long as shadow hits continue to bypass active fetch suppression
- Default breaker parameters remain:
  - failure budget `2`
  - open cooldown `15s`
  - half-open probe limit `1`
- Breaker state progression is explicit:
  - `closed` on normal operation
  - `open` after failure budget exhausted
  - `half_open` after the `15s` cooldown when one probe attempt is permitted
  - successful half-open probe closes the breaker; failed half-open probe immediately reopens it
- If breaker is open and no eligible shadow value exists, the key is unavailable until the next allowed half-open probe.
- If a shadow invalidation race removes eligibility while the breaker is already open, the key is unavailable until the next allowed half-open probe; stale fallback is not permitted.
- Locking rule:
  - `SemanticReadScheduler` must never hold its own mutex while acquiring the `ShadowCache` lock
  - `ShadowCache` must never call back into `SemanticReadScheduler` while holding its own lock
  - active-confirmed writes to `ShadowCache` happen only after the scheduler mutex has been released
  - subscriber notifications from `ShadowCache` are out-of-lock
  - `ShadowCache` notifications are advisory only in v1; they use bounded non-blocking delivery with overflow metrics and may not stall the write path
  - `ShadowCache` notification consumers are limited to observability/debug/live-summary helpers in v1; the scheduler core path does not rely on notifications for correctness and consults shadow state only on read
- Write-order rule:
  - every shadow entry carries an observation timestamp from the evidence source
  - for passive evidence this timestamp is exactly the Section 3 `observed_at_monotonic` field
  - for `active_confirmed` evidence this timestamp is the successful attempt-complete monotonic timestamp from the active observer event
  - incoming writes are rejected if their observation timestamp is strictly older than the current entry
  - source precedence is a trust tie-breaker, not permission to overwrite newer evidence with older data
  - `active_confirmed` outranks passive evidence only when timestamps are equal or the active evidence is not older
  - if two passive writes arrive with the same source and the same observation timestamp but different payload content, the later write may not silently overwrite; the pair is treated as ambiguous/conflicting evidence and the existing accepted entry remains authoritative until a later strictly newer generation/timestamp resolves it
  - in that scenario, the first accepted write increments `shadow_writes_total` normally; the later conflicting candidate increments both `ambiguous_total{reason=same_timestamp_conflict}` and `shadow_write_rejections_total{reason=same_timestamp_conflict}` when it reached shadow admission
  - rejecting an older-timestamp write never clears or weakens any newer invalidation/tombstone state already present for that key; rejection affects only the incoming write candidate
- Active-fetch write-back rule:
  - when an active fetch starts, the scheduler must capture a generation/invalidation token for that key
  - the generation token is adapter-scoped, per-key, monotonic `uint64`, resets on process restart, and is not persisted across restarts
  - any state transition that changes shadow eligibility or tombstone/invalidation status for a key must advance that key's generation token
  - tombstone de-pin/eviction after the hard `24h` horizon is also a generation-advancing event for that key
  - if an external-write invalidation or newer shadow/scheduler generation occurs before that fetch completes, the completed fetch result may not reseed scheduler freshness as a fresh success
  - the same generation/invalidation rule applies to any subsequent `active_confirmed` shadow write derived from that fetch; a stale in-flight fetch may not overwrite any entry from a newer generation, whether that newer entry is a tombstone or a repopulated value, merely because its completion timestamp is newer
  - stale pre-invalidation active results may be discarded or forced through at most one immediate recompute attempt under a fresh generation token; after that they fail closed as `unavailable/error`, never as stale fallback
  - if that single allowed recompute fetch also completes stale against a newer generation, it fails closed immediately and may not trigger a second recompute
  - the same generation/order rules cover half-open probe versus concurrent `Get()` races for the same key: at most one accepted active result may commit, and a stale-completing probe or concurrent fetch may not overwrite a newer accepted result
  - for same-generation concurrent active completions, `newer accepted result` means the candidate with the later observation timestamp from the active observer event; if timestamps are equal, the existing accepted result remains authoritative and the later candidate is rejected as a same-timestamp conflict
  - the observation timestamp for an `active_confirmed` shadow write is the successful attempt-complete timestamp from the active observer event, not the later logical request-complete or scheduler-return timestamp
  - joining an existing coalesced fetch does not count as invoking the caller-supplied `fetch` closure; only actual closure invocations count toward the `max 2` fetch budget

### 8B. Passive evidence to semantic publish path

- `ShadowCache` does not write directly to `LiveSemanticProvider` in v1.
- Generic shadow/scheduler observe-first does not cover the existing B516 energy merge path.
- The existing semantic poller remains the sole owner of:
  - semantic field assembly
  - merge logic
  - provider writes
  - GraphQL subscription publish calls
- Passive evidence only seeds `ShadowCache` and the scheduler-facing read path.
- B516 energy broadcasts remain an explicit carve-out handled by the dedicated energy merge/provider path.
- The B516 routing chain in v1 is explicit:
  - `PassiveTransactionReconstructor`
  - `BroadcastListener`
  - semantic router
  - `energyMergeStore`
  - provider snapshot/export surfaces
- `BroadcastListener` consumes pre-dedup classified passive events, so the B516 broadcast/energy path is intentionally not suppressed by active/passive dedup logic.
- `BusObservabilityStore` also consumes pre-dedup classified passive events; dedup suppression applies only to the downstream shadow-correlation and watch-efficiency consumers, not to bus-level observability/timing accounting.
- Here `pre-dedup` means `BroadcastListener` is a parallel direct subscriber of the reconstructor classified-event fan-out, not a consumer of a second upstream tap or a downstream dedup-filtered stream.
- In v1 only the documented B516 broadcast-energy path is intentionally exempt from dedup suppression. Other passive broadcast families remain observability-only unless a later family policy explicitly promotes them.
- The next poller cycle may satisfy individual raw reads from eligible shadow entries, assemble semantic snapshots through the existing helpers, and then publish through the existing `publish*` path.
- There is no second out-of-band semantic publish path from passive tap events in v1.
- Result:
  - observe-first reduces active bus I/O first
  - GraphQL subscription latency remains bounded by the poller publish cadence, not raw passive event arrival time
  - merge semantics stay centralized in the existing poller/provider path
- Generic `ShadowCache` consultation does not rely on callbacks or notifications from `ShadowCache` to `SemanticReadScheduler`; scheduler/shadow synchronization uses the shared per-key generation domain plus explicit scheduler invalidation helpers on write-side events, while notification channels remain advisory-only for observability/debug tooling.
- The `shadow-correlation consumer` named elsewhere in this document is the bounded downstream component on the adjudicated dedup stream that decides whether a third-party passive event becomes a generic shadow write, an external-write invalidation, or observability-only output.
- External-write invalidation for third-party passive traffic is applied only on the adjudicated post-dedup passive stream, before generic shadow admission for that observation.

### 9. Watch catalog and runtime activation

- `WatchCatalog` is not “all documented keys always active”.
- `WatchCatalog` is the bounded static catalog of possible watch descriptors.
- Runtime activation is a separate bounded set.
- `WatchCatalog` access rules are explicit:
  - the static descriptor catalog is immutable after startup for one adapter instance
  - runtime activation records are a separate mutable bounded structure
  - hot-path readers may read immutable descriptors lock-free
  - activation updates use a bounded lock or atomic map-swap path and may not mutate the immutable descriptor catalog in place
- `WatchDescriptor` must include at least:
  - family
  - concrete key shape
  - semantic class: `state | config | discovery | debug`
  - freshness profile
  - decoder id
  - correlation policy
  - direct-apply policy
  - `freshness_ttl`
- Static `WatchDescriptor`s do not carry activation provenance; activation source belongs to runtime activation records.
- `semantic class` remains the coarse policy bucket used by Section 5 and Section 7.
- `freshness profile` is the finer-grained bounded enum used for TTL defaults and caller `maxAge` defaults:
  - `state_fast`
  - `state_slow`
  - `config`
  - `discovery`
  - `debug`
- Descriptor authors choose `state_fast` only for values whose semantic usefulness degrades on the order of seconds and that are normally polled or observed at high cadence, such as temperatures or fast operating state; `state_slow` is the default for stable state whose usefulness degrades on the order of tens of seconds rather than single-digit seconds.
- Semantic-class / freshness-profile pairings are validated:
  - `state` may use only `state_fast` or `state_slow`
  - `config` may use only `config`
  - `discovery` may use only `discovery`
  - `debug` may use only `debug`
  Invalid pairings are catalog-build/startup errors for that descriptor and may not silently fall through to runtime defaults.
- Default TTLs by freshness profile:
  - `state_fast`: `10s`
  - `state_slow`: `30s`
  - `config`: `5m`
  - `discovery`: `1h`
  - `debug`: `0` unless explicitly overridden by tooling
- Family- or key-specific descriptors may tighten these defaults but may not widen them without explicit documentation.
- `freshness_ttl` resolves hierarchically: if a descriptor sets an explicit TTL, it may only tighten the freshness-profile default; otherwise the profile default is the effective TTL.
- In-memory `WatchDescriptor` representation treats `freshness_ttl` as optional; unset/nil means "use the resolved default from profile/family rules", not zero-duration.
- `decoder id` is a stable string enum naming a concrete family decoder implementation.
- The `decoder id` registry is a closed shared table owned by the watch-catalog / family-policy layer in gateway code. It is the authority for:
  - stable decoder names
  - minimum value-bearing length
  - expected value-bearing shape
  - any family-specific decode metadata referenced by this spec
  - concretely, v1 stores this as a source-controlled compiled registry table in the shared watch-catalog/family-policy package; updates happen only via the same-cycle code+doc change that introduces the new decoder id
- the addressed decoder is selected from the canonical key / active watch-descriptor mapping; if no active descriptor selects a decoder for that observation, or if multiple decoder candidates remain after namespace resolution, the event may remain observable but is not a shadow direct-apply candidate
- the canonical in-memory B524 key builder uses typed fields, not raw selector byte slices:
  - `target byte`
  - `opcode byte`
  - `group byte`
  - `instance byte`
  - `register_address uint16`
  Derived serialization uses zero-padded hex rendering only for logs/metrics/debug.
- `correlation policy` is a stable enum with at least:
  - `request_response`
  - `broadcast_selector`
  - `record_and_invalidate`
  - `record_only`
  - `invalidate_only`
- The single `correlation policy` field intentionally covers both passive read-correlation mode and default externally observed write disposition for that descriptor, because both govern how passive evidence for the same descriptor is admitted into the policy engine.
- Descriptor-local `correlation policy` governs how passive evidence for that descriptor is interpreted by default.
- The runtime `external_write_policy` flag is a higher-level system override for externally observed writes:
  - for descriptors whose passive treatment is one of the `record_*` / `invalidate_*` modes, the runtime flag is the effective externally observed write policy in v1
  - for pure read-correlation descriptors (`request_response`, `broadcast_selector`), the runtime flag does not change their read-side correlation mode
  - descriptor-local `record_*` / `invalidate_*` values remain the documented per-descriptor default intent and are used for catalog documentation and future finer-grained policy work, but they do not outrank the runtime flag in v1
  - therefore v1 implementations may not branch on descriptor-local externally observed write disposition after the runtime override has been applied; the descriptor field is metadata/documentation unless a later milestone explicitly promotes finer-grained runtime enforcement
- `direct-apply policy` is a stable enum with at least:
  - `never`
  - `state_default`
  - `config_opt_in`
  - `energy_merge_only`
- `config_opt_in` is granted only by the static code-owned `WatchCatalog` descriptor for that key; there is no operator/runtime-created config direct-apply grant in v1.
- The runtime bridge is explicit:
  - if a descriptor is `config_opt_in` and `passive_config_direct_apply=true`, it may use config direct-apply
  - if a descriptor is `config_opt_in` and `passive_config_direct_apply=false`, it falls back to the normal conservative config behavior from Section 7, meaning record-only or record-and-invalidate according to the effective runtime `external_write_policy`, never config direct-apply
- Document shorthand such as `record/invalidate` refers to the single enum policy `record_and_invalidate`.
- Runtime `activation source` is provenance, not access control. It records who activated the watch:
  - `poller`
  - `write_confirm`
  - `tooling`
  - `operator`
- Runtime activation sources:
  - semantic poller read lists
  - write-confirm keys
  - explicitly requested tooling keys
  - optional operator/dev watch registrations later
- Multiple simultaneous activation sources for the same key use union semantics:
  - the key remains active while at least one activation source remains present
  - deactivation of one source does not remove the key if other sources are still active
  - runtime provenance is stored as the bounded active-source set for that key rather than a single winner-takes-all source
- `write_confirm` runtime activation is explicit:
  - it is created when a write path requires a follow-up read-back confirmation for a concrete key
  - while active, it contributes to pinned/runtime activation just like other write-confirm keys
  - it is removed when read-back confirm succeeds, when the write-confirm window expires, or when no remaining activation source keeps that key active
  - default write-confirm activation timeout is `15m` unless a narrower family/key-specific rule is documented
  - concurrent write-confirm activations are capped at `256` per adapter instance; beyond that cap, new write-confirm shadow pinning must fail closed and the write path must use direct active read-back without creating additional pinned shadow activations
  - if a write-confirm activation targets a key that is already pinned for another activation source, it adds runtime provenance only and does not consume a second pinned slot
- Activation is derived from explicit code-owned selector lists, not from “all docs”.
- `explicit code-owned selector lists` means:
  - static gateway watch-descriptor tables committed in code
  - semantic poller read lists derived from those tables
  - write-confirm runtime activations for concrete keys
  It does not mean ad-hoc operator-entered selectors by default.
- The family-policy engine is the same gateway component family previously referred to as the `watch-catalog / family-policy layer`; this document uses `family-policy engine` as the preferred term.
- Passive observations for catalog-miss or inactive selectors do not create shadow entries in v1.
- Such observations still contribute to whole-bus observability but do not create scheduler-facing cache state in v1; any future `untracked_selector` debug surface is out of scope for M0-M9 unless a separate issue explicitly adds it, and only then may it introduce its own bounded storage contract.
- `debug` freshness-profile watches are observability/tooling-only in v1 and do not allocate shadow entries unless an explicit tooling override is documented later.
- If a tooling override later allows debug-profile shadow entries, those entries remain evictable/manual-budget entries and may not consume the pinned sub-budget in v1.
- When the last runtime activation source for a key is removed, any existing shadow entry for that key loses pinned status immediately, remains eligible only under its normal freshness/invalidation rules, and becomes evictable like any other non-pinned entry; deactivation does not force immediate deletion of still-fresh data.
- For B524 dual-namespace groups, decoder resolution attempts the active watch-descriptor mapping keyed by request selector dimensions; only an exact single matching descriptor selects a decoder, otherwise the observation remains ambiguous/non-direct-apply.
- Decoder ambiguity detection is explicit:
  - zero matching active descriptors for the canonical key => not direct-apply-eligible
  - exactly one matching active descriptor => select that decoder
  - more than one matching active descriptor => `multi_decoder` ambiguity
- The canonical B524 watch-key dimensions are exactly `(family=B524, target, opcode, group, instance, register_address)`.
- Decoder/namespace selection happens after key construction from the canonical B524 selector dimensions; if multiple decoder candidates still match the same canonical key, the observation remains ambiguous/non-direct-apply rather than extending the key with an ad-hoc decoder discriminator.

### 9A. Shared key contract

- Shadow correlation, watch activation, and scheduler lookups must use a shared canonical key-construction contract.
- Key construction may not be duplicated as ad-hoc `fmt.Sprintf` conventions across packages.
- The canonical in-memory key form is a typed struct, not an ad-hoc string:
  - canonical struct fields cover family plus the family-specific selector dimensions
  - string serialization exists only as a derived stable rendering for logs/metrics/debug
- The shared key builder/type must live outside `main` so both poller call sites and passive correlation code can use the same implementation.
- In v1 that canonical watch-key type is owned by a shared `helianthus-ebusgateway` package adjacent to watch-catalog/scheduler code; it does not live in `main`, and it is not pushed down into `helianthus-ebusgo`.
- The shared canonical key package must expose typed builders for at least:
  - `B524WatchKey{target, opcode, group, instance, register_address}`
  - `B509WatchKey{target, register_address}`
  - `B516WatchKey{target, period, source, usage}`
  - `B555WatchKey{target, opcode, zone_or_circuit, day_selector, slot_selector}`
- `B516WatchKey` is used for B516 freshness/provenance and energy-merge identity only; it is not a generic scheduler-facing `ShadowCache` key in v1.
- Round-trip and cross-package tests must prove that passive-derived keys and scheduler query keys are identical for the same semantic selector.

### 10. Memory model

- `ShadowCache` is memory-only in v1.
- Gateway hard limits:
  - `4096` total shadow entries max
  - semantic and write-confirm keys are pinned
  - pinned entries have their own bounded sub-budget and may not consume the entire cache
  - each adapter instance owns its own `ShadowCache` budget domain; current single-adapter gateway deployments therefore observe these limits per active/passive eBUS adapter instance
  - if code-owned pinned activation would exceed the pinned budget, observe-first shadowing for that adapter instance fails closed into degraded/disabled mode while the gateway process still starts; this is not a fatal process exit
  - in that degraded/disabled mode, passive tap ingest, whole-bus observability, and watch-catalog construction remain enabled, but shadow satisfaction/direct-apply for that adapter instance stay disabled until configuration or watch inventory returns within budget
  - in that degraded/disabled mode, watch-efficiency metrics that depend on generic shadow satisfaction/direct-apply remain zero or omitted for the affected adapter instance; they may not be repurposed to count budget-degraded misses as transport-limitation misses
  - tooling/manual watch entries are LRU-evicted first
- Default pinned sub-budget is `2048` entries.
- Of that pinned sub-budget, `256` entries are reserved for the documented write-confirm cap, leaving `1792` as the maximum static/runtime non-write-confirm pinned footprint before degraded-mode shadow disabling begins.
- Startup/config validation must therefore prove `static non-write-confirm pinned footprint <= 1792`; otherwise observe-first shadowing for that adapter instance starts in the documented pinned-budget degraded mode.
- After the `15m` compaction window elapses and the bounded compactor runs, pinned tombstones become metadata-only and then age toward a hard maximum tombstone lifespan of `24h`.
- Compaction is also a state transition for runtime/metric accounting: once a payload-retained invalidation is compacted, the entry leaves `shadow_entries{state="invalidated"}` and enters `shadow_entries{state="tombstone"}` exactly once for that lifecycle.
- After `24h` without successful refresh, a pinned tombstone may be de-pinned and evicted from `ShadowCache` while the watch remains active in `WatchCatalog`; the next eligible active/passive observation recreates the shadow entry.
- If even metadata-only tombstones would still exceed budget before that point, observe-first shadowing remains disabled for that adapter instance until revalidation or inventory/configuration change reduces the set.
- In v1, returning within budget typically requires restart-level config/watch-inventory change or later successful revalidation; no hot automatic recovery is implied beyond successful refresh of the affected keys.
- Tinyebus hard limit:
  - fixed-size table, hard limit `512` entries max in T0

### 11. Metrics model

- Existing `expvar` remains in place.
- There is no broad expvar migration in this feature.
- New bus/watch metrics are exposed through a dedicated Prometheus text exporter.
- Unless a metric name is already written in full elsewhere, metric identifiers in this document are expressed in logical suffix form and are emitted with the shared `ebus_` Prometheus namespace prefix on gateway and on the semantically aligned tinyebus T0 subset.
- The gateway keeps a custom text exporter rather than blindly adopting full client-library auto-registration because this feature requires strict bounded-series admission, overflow bucketing, and close alignment with the tinyebus text-exposition contract.
- Metric type conventions for this feature are explicit:
  - `metric family` in this document means one concrete Prometheus metric name, not the whole feature-wide set of metrics
  - metrics ending in `_total` are Counters
  - metrics ending in `_seconds_total` are cumulative-seconds Counters
  - metrics ending in `_state` are one-hot Gauges over a closed label domain unless otherwise stated
  - metrics ending in `_degraded_state` are `0|1` Gauges representing degraded/not-degraded for one bounded subsystem
  - metrics ending in `_enabled` are `0|1` Gauges for bounded config-flag state
  - metrics ending in `_connected` are `0|1` Gauges
  - metrics ending in `_reason` are one-hot Gauges over a closed bounded reason enum
  - metrics ending in `_elapsed_seconds` are Gauges of the current elapsed window
  - metrics ending in `_duration_seconds` are Gauges of the latest bounded-duration sample unless the metric is explicitly documented as a rolling estimate/mean or a milestone explicitly upgrades it to histogram form
  - metrics ending in `_saved_seconds` are Gauges whose value is a current saved-time estimate rather than a raw duration sample
  - metrics ending in `_transactions` are Gauges of current counted progress/threshold values, not counters
- Gateway serves `/metrics` on the main HTTP server mux.
- Tinyebus does not use `prometheus/client_golang`.
- Tinyebus uses the same metric names only where they are semantically meaningful to the firmware bootstrap runtime.
- Tinyebus T0 does not claim gateway-parity labels for shadow-cache, scheduler, or semantic-watch behavior that does not yet exist there.
- Passive tap lifecycle metrics must include connection-health signals such as reconnect attempts and connected state.
- Observer-fed observability events must carry transport-class and timing-capability metadata so the store can distinguish real bus-timed transports from relay/round-trip transports.
- Prometheus label policy:
  - family labels are a closed set:
    - `B509`
    - `B516`
    - `B524`
    - `B555`
    - `other`
  - source/target labels are bounded to known/normalized values plus an overflow bucket such as `other`
  - `src` and `dst` are each normalized to at most `8` explicit address buckets per adapter instance plus `other`; excess live addresses are folded into `other` for Prometheus while remaining visible in bounded MCP/GraphQL data
  - feature-scoped Prometheus series emitted by this observe-first/bus-observability feature must stay within an explicit bounded budget; no raw unbounded address fan-out is allowed
  - bounded label domains for the core bus metrics are:
    - `scope`: `active`, `passive`
    - `window`: `1m`, `5m`, `15m`, `1h`
    - `frame_type`: `master_target`, `master_master`, `broadcast`, `local_participant_inbound`, `abandoned_partial`
    - `phase`: `request`, `ack`, `response`, `final_ack`, `terminal`
    - `class`: `timeout`, `crc_mismatch`, `echo_mismatch`, `unexpected_syn`, `transport_reset`, `decode_fault`, `collision`, `nack`, `abandoned`
    - `src` / `dst`: the bounded normalized address buckets described above
- Default observability series budget is `1024`.
- The `1024` default budget applies to all new series emitted by this feature on the gateway exporter, including bus observability, shadow/watch, dedup, warmup, and feature-flag series, but not unrelated pre-existing gateway metrics outside this feature scope.
- The design target is to stay below `512` steady-state series for this feature under normal bounded address/family populations, leaving at least `50%` headroom before the `1024` hard budget is approached.
- The steady-state series envelope is explicitly budgeted as:
  - up to `256` series for `frames_observed_total`
  - up to `64` series for `errors_total`
  - up to `32` series for B516 freshness/update metrics
  - the remaining observe-first shadow/dedup/warmup/flag metrics together must stay within the residual headroom under the `<512` design target
- Series-budget enforcement is explicit:
  - the store tracks registered/emitted series against the budget
  - when a new series would exceed the budget, it is folded into an overflow bucket or omitted per-metric policy
  - overflow increments an explicit `observability_series_budget_overflow_total` metric and logs a degraded-state reason
  - implementations may not pre-register the full Cartesian product of all bounded label enums; only architecturally valid and actually observed label combinations may consume series budget
  - the `<512` design target assumes lazy observation-driven series creation plus pruning of impossible combinations such as invalid transition pairs or disabled freshness profiles
  - metric-specific admission caps are part of that budget discipline:
    - `frames_observed_total` may consume at most `384` series per adapter instance before new combinations are folded into that metric's overflow buckets
    - `errors_total` may consume at most `128` series per adapter instance before new combinations are folded into overflow buckets
    - the lower steady-state design targets are `256` and `64` respectively; exceeding those softer targets is allowed only until the hard per-metric caps are reached
  - overflow-bucket assignment is deterministic: when a metric exceeds its admissible series set, the excess label combination is folded by replacing the highest-cardinality offending label dimension(s) with that metric's documented `other` bucket rather than by hashing to arbitrary buckets
- Required metrics include invalidation and feature-flag visibility:
  - `frames_observed_total{scope,src,dst,family,frame_type}`
  - `errors_total{scope,class,phase}`
  - `bus_busy_seconds_total`
  - `bus_busy_ratio{window}`
    This is a GaugeVec over the closed `window` domain.
  - `observability_series_budget_overflow_total`
    This is a label-free per-adapter Counter.
  - `passive_tap_reconnect_attempts_total`
  - `passive_tap_reconnect_successes_total`
  - `passive_tap_reconnect_failures_total`
  - `passive_capability_probe_attempts_total`
  - `passive_capability_probe_outcomes_total{outcome}`
    Valid `outcome` values are bounded to:
    - `confirmed`
    - `withdrawn`
    - `timed_out`
    `timed_out` increments only when the governing outer probe/fallback window expires before either `confirmed` or `withdrawn`.
  - `passive_tap_connected`
  - `shadow_invalidations_total{family,reason,source}`
    Valid `reason` values are bounded to:
    - `external_write`
    - `rollback`
    - `manual`
    - `policy_reject`
    Valid `source` values are bounded to:
    - `passive`
    - `active`
    - `operator`
    - `system`
    Source semantics are explicit:
    - `passive`: invalidation triggered by passive external-write or passive-policy evidence
    - `active`: invalidation triggered by active-path generation advancement or active reconciliation logic
    - `operator`: explicit operator/manual invalidation action
    - `system`: automated system-initiated invalidation such as rollback or internal safety normalization
  - `feature_flag_normalizations_total{reason}`
    Valid `reason` values are bounded to:
    - `master_off_clamp`
    - `config_requires_state`
    - `config_requires_invalidation`
    - `state_disabled_forces_record_only`
    This Counter increments whenever runtime normalization changes the effective behavior away from the raw configured flag combination.
  - `feature_flag_enabled{flag}`
    Valid `flag` values are bounded to:
    - `observe_first_enabled`
    - `passive_state_direct_apply`
    - `passive_config_direct_apply`
  - `external_write_policy_state{policy}`
    Valid `policy` values are bounded to:
    - `invalidate_only`
    - `record_only`
    - `record_and_invalidate`
    Invalid flag combinations do not abort gateway startup; the feature starts in a safe normalized state with explicit diagnostics/metrics:
    - invalid observe-first sub-flags are clamped to their safe disabled equivalent
    - invalid `external_write_policy` combinations are clamped according to the master-off/runtime rules from Sections 7 and 14
    - `passive_config_direct_apply=true` with `external_write_policy=record_only` must be normalized to `record_and_invalidate`
    Per-descriptor correlation/default policy is intentionally not exported as a Prometheus label set in v1; operators inspect that bounded descriptor metadata through watch-summary/MCP/GraphQL surfaces rather than high-cardinality metrics.
  - `shadow_pinned_budget_degraded_state`
    This is a label-free per-adapter `0|1` Gauge.
  - `shadow_entries{state}`
    Valid `state` values are bounded to:
    - `present`
    - `invalidated`
    - `tombstone`
    This is a GaugeVec of current shadow entry counts by state.
  - `shadow_pinned_entries`
    This is a label-free per-adapter Gauge.
  - `shadow_evictable_entries`
    This is a label-free per-adapter Gauge.
    The metric invariant is explicit: `sum(shadow_entries{state=*}) == shadow_pinned_entries + shadow_evictable_entries`.
    This is a logical/state invariant, not a promise of scrape-atomic simultaneity across independently exported gauges.
  - `shadow_writes_total{source}`
    Valid `source` values are bounded to:
    - `passive`
    - `active_confirmed`
    This Counter counts accepted shadow writes only; rejected attempts are counted exclusively in `shadow_write_rejections_total`.
  - `shadow_write_rejections_total{reason}`
    Valid `reason` values are bounded to:
    - `stale_timestamp`
    - `same_timestamp_conflict`
    - `generation_advanced`
    - `policy_reject`
    - `capacity`
    This Counter increments only when a candidate write reached shadow admission and was rejected there; it may co-increment with `ambiguous_total{reason=same_timestamp_conflict}` for the same observation, but the two counters are not guaranteed to move together.
  - `shadow_revalidate_retries_total`
    This is a label-free per-adapter Counter for scheduler shadow consult/revalidate retries.
    It increments once for each consult/revalidate pass beyond the first pass of a `Get()` call.
  - `shadow_bypass_reads_total{reason}`
    Valid `reason` values are bounded to:
    - `caller_max_age_zero`
    - `observe_first_disabled`
    - `debug_profile`
    This is a Counter of reads that intentionally bypass shadow eligibility rather than missing an eligible entry.
  - `shadow_notification_overflow_total`
    This is a label-free per-adapter Counter.
  - `shadow_hits_total`
    This is a label-free per-adapter Counter for successful generic `ShadowCache` satisfactions only.
    It explicitly excludes the B516 `energy_merge_only` path.
    It counts successful generic shadow satisfactions regardless of whether the retained shadow value originated from passive evidence or from earlier `active_confirmed` writes.
  - `shadow_misses_total`
    This is a label-free per-adapter Counter for generic `ShadowCache` consults that did not yield a usable shadow value.
    It explicitly excludes the B516 `energy_merge_only` path.
  - `active_fetches_total{family,freshness_profile,outcome}`
    Valid `freshness_profile` values for this metric are the same bounded set used by watch-efficiency metrics:
    - `state_fast`
    - `state_slow`
    - `config`
    - `discovery`
    The `debug` profile is excluded from this observe-first comparison metric family.
    Valid `outcome` values are bounded to:
    - `success`
    - `error`
    - `breaker_blocked`
    `breaker_blocked` means the scheduler decided not to start any transport/protocol fetch attempt because the breaker was already open; it may co-occur with a shadow miss for the same `Get()` path.
  - `passive_hits_total{family,freshness_profile}`
    This Counter is the passive-origin subset of generic shadow satisfactions; it is not equal to `shadow_hits_total` because `shadow_hits_total` also includes satisfactions served from `active_confirmed` shadow state.
  - `direct_apply_total{family,freshness_profile}`
  - `active_reads_avoided_total{family,freshness_profile}`
  - `active_read_saved_seconds{family,freshness_profile}`
    This metric is a Gauge whose value is the current documented rolling-mean saved-duration estimate from `ISSUE-GW-12`, not a last-sample gauge.
    Valid `freshness_profile` values for watch-efficiency metrics are bounded to:
    - `state_fast`
    - `state_slow`
    - `config`
    - `discovery`
    The `debug` profile is excluded because generic shadow hits are disabled for `debug` in v1.
    These buckets include only watches whose descriptor `freshness_profile` exactly matches the label value; they are not broader semantic-class aggregates.
    The generic watch-efficiency metric family excludes the B516 `energy_merge_only` path in v1; broadcast-energy freshness/merge activity is surfaced through the dedicated B516 freshness metrics rather than counted as generic `ShadowCache` read avoidance.
  - `ambiguous_total{family,reason}`
    Valid `reason` values are bounded to:
    - `decode`
    - `missing_request_context`
    - `multi_decoder`
    - `retransmission`
    - `same_timestamp_conflict`
    - `policy_reject`
    This Counter increments at classification/policy time when the observation is recognized as ambiguous, regardless of whether it later reaches shadow admission.
  - `missed_due_to_transport_limitations_total{family,freshness_profile,limitation}`
    Valid `limitation` values are bounded to:
    - `passive_unavailable`
    - `broadcast_unavailable`
    - `other_capability_limit`
    This Counter increments once per observe-first-eligible read call that falls back to active behavior because the required passive/broadcast capability for that call is currently unavailable; it is not a persistent descriptor-count gauge.
  - `dedup_degraded_state`
    This is a label-free per-adapter `0|1` Gauge.
  - `dedup_degraded_total{reason}`
    Valid `reason` values are bounded to:
    - `fingerprint_emission_failure`
    - `observer_panic`
    - `epoch_reset`
    - `critical_overflow`
    - `explicit_discontinuity`
  - `dedup_pipeline_fault_total{stage}`
    Valid `stage` values are bounded to:
    - `input`
    - `output`
    This Counter increments on any end-to-end dedup pipeline fault that can cause loss of adjudication correctness, whether the fault originated on the input side or output side.
  - `dedup_epoch_resets_total`
  - `dedup_matched_total`
  - `dedup_unmatched_total`
  - `dedup_local_participant_inbound_total`
    This is a label-free per-adapter Counter.
  - `passive_pipeline_degraded_state`
    This is a label-free per-adapter `0|1` Gauge.
    It is `1` exactly when the passive-pipeline supervisor from Section 3B has declared the classified-event pipeline globally degraded because all critical subscribers are simultaneously degraded/unsubscribed or an equivalent supervisor-declared global passive-pipeline fault is active.
  - `passive_fanout_overflow_total{consumer,criticality}`
    Valid `consumer` values are bounded to:
    - `broadcast_listener`
    - `dedup`
    - `observability_store`
    - `debug_summary`
    Valid `criticality` values are bounded to:
    - `critical`
    - `noncritical`
  - `dedup_output_overflow_total{consumer}`
    Valid `consumer` values are bounded to:
    - `shadow_correlation`
    - `watch_efficiency`
  - `dedup_pending_flush_total{reason}`
    Valid `reason` values are bounded to:
    - `capacity`
    - `grace_expiry`
    - `epoch_reset`
    - `critical_overflow`
  - `dedup_pending_entries`
    This is a label-free per-adapter Gauge of current pending-passive buffer occupancy.
  - `passive_warmup_state{state}`
    Valid `state` values are bounded to:
    - `unavailable`
    - `warming_up`
    - `available`
    Probe sub-phase is represented as `warming_up`; no fourth probe-specific state label exists in v1.
  - `passive_capability_unavailable_reason{reason}`
    Valid `reason` values are bounded to:
    - `startup_timeout`
    - `reconnect_timeout`
    - `socket_loss`
    - `flap_dampened`
    - `unsupported_or_misconfigured`
    - `capability_withdrawn`
  - `passive_warmup_elapsed_seconds`
  - `passive_warmup_completed_transactions`
    This is a Gauge of current completed-transaction progress in the active warmup session.
  - `passive_warmup_required_transactions`
    This gauge is dynamic and always reflects the currently applicable threshold for the active warmup mode:
    - `20` during initial/reconnect warmup
    - `10` during post-reset settling warmup
    - `0` whenever no active warmup session exists, including before first connect and after fallback-path promotion to `available`
    Consumers must interpret `0` together with `passive_warmup_state{state}`; `0` alone does not distinguish "no session" from a just-completed transition edge.
  - `passive_warmup_completion_mode{mode}`
    Valid `mode` values are bounded to:
    - `thresholds_met`
    - `fallback_path`
    This one-hot Gauge reflects how the current or most recent successful warmup promotion to `available` was achieved.
    Before the first successful promotion, all `mode` values remain `0`.
    If both threshold satisfaction and fallback-path criteria become true on the same evaluation edge, `thresholds_met` wins and `fallback_path` remains `0`.
  - `passive_warmup_blocker_reason{reason}`
    Valid `reason` values are bounded to:
    - `connected_observation_window`
    - `completed_transactions`
    - `healthy_symbol_ingress`
    - `post_reset_settling`
    - `startup_outer_window`
    This one-hot Gauge exposes the dominant currently unsatisfied global passive warmup precondition when `passive_warmup_state{state="warming_up"}`.
    Outside `warming_up`, all `reason` values remain `0`.
    Dominance order is fixed:
    - `post_reset_settling`
    - `completed_transactions`
    - `connected_observation_window`
    - `healthy_symbol_ingress`
    - `startup_outer_window`
  - `passive_capability_transitions_total{from,to}`
    Valid `from` / `to` values use the closed passive capability state set:
    - `unavailable`
    - `warming_up`
    - `available`
  - `breaker_keys{state}`
    Valid `state` values are bounded to:
    - `closed`
    - `open`
    - `half_open`
    This is a Gauge of current scheduler breaker-key counts by state.
  - `periodicity_tuple_budget_overflow_total`
    This is a label-free per-adapter Counter for tuple-budget eviction/overflow events.
  - `energy_broadcast_selectors{state}`
    Valid `state` values are bounded to:
    - `fresh`
    - `stale`
    - `warming_up`
    - `never_seen`
    - `unavailable`
    This is a Gauge of the current number of B516 selector streams in each freshness state, aggregated across selectors rather than labeled per selector.
  - `energy_broadcast_updates_total{outcome}`
    Valid `outcome` values are bounded to:
    - `accepted`
    - `rejected`
    - `stale_refresh`
    `stale_refresh` means an acceptable broadcast arrived while the selector was currently in `stale` state and refreshed that selector's freshness/provenance tracking.
    This Counter tracks B516 broadcast-energy update activity for the dedicated `energy_merge_only` path and is separate from generic `shadow_hits_total` / `passive_hits_total`.
  - `energy_broadcast_freshness_transitions_total{from,to}`
    Valid `from` / `to` values use the same closed freshness-state set:
    - `fresh`
    - `stale`
    - `warming_up`
    - `never_seen`
    - `unavailable`
    Only architecturally valid transitions from the B516 freshness-state machine in Section 6 may be emitted; impossible pairs remain absent and may not consume series budget.
    Self-transitions driven only by no-op refreshes do not increment this counter.
    Reset-driven self-transitions that restart epoch/sample state, such as `warming_up -> warming_up` on passive reset, do increment this counter.
  - `shadow_tombstone_compactions_total`
  - `shadow_tombstone_depins_total`
  - `shadow_tombstones{stage}`
    Valid `stage` values are bounded to:
    - `payload_retained`
    - `metadata_only`
    Metric invariant: `shadow_tombstones{payload_retained} + shadow_tombstones{metadata_only} == shadow_entries{state="tombstone"}`.
    This is a logical/state invariant, not a promise of scrape-atomic simultaneity across independently exported gauges.
  - `shadow_compactor_sweep_duration_seconds`
    This is a label-free per-adapter Gauge of the last completed sweep duration.
  - `shadow_compactor_failures_total`
  - `shadow_compactor_degraded_state`
    This is a label-free per-adapter `0|1` Gauge.
  - `watch_runtime_activations_total{source,action}`
    Valid `source` values are bounded to:
    - `poller`
    - `write_confirm`
    - `tooling`
    - `operator`
    Valid `action` values are bounded to:
    - `activate`
    - `deactivate`
    - `expire`
    - `last_source_removed`
    In v1, `operator` remains zero/absent unless a later issue explicitly enables operator-managed watch activation.
  - `write_confirm_active`
    This is a label-free per-adapter Gauge of currently active write-confirm runtime activations.
  - `write_confirm_cap_rejections_total`
    This is a label-free per-adapter Counter.
  - `rollback_events_total`
    This is a label-free per-adapter Counter and increments once per adapter-scoped rollback epoch event.
    Partial rollback attempts that fail before the full adapter-scoped rollback sequence completes must surface separate error metrics/logs and may not increment this counter.

### 11A. Bus observability query data model

- `busSummary` exposes bounded aggregate counters and capability state.
- `busMessages` exposes recent reconstructed bus records from a bounded ring buffer, not unbounded history.
- `busPeriodicity` exposes bounded summary entries derived from a periodicity tracker, not raw event history.
- Store bounds:
  - recent-message ring buffer is bounded and configurable; default `1024`
  - periodicity tracker is bounded by a maximum tuple-entry budget; default `256`
  - periodicity entries stale-evict after `1h` without new observations
  - if the periodicity budget is full and no stale entries exist, the least-recently-seen tuple is evicted by LRU and `periodicity_tuple_budget_overflow_total` increments
  - busy/frame/error aggregates remain fixed-cost counters
- Record model:
  - `busMessages` records are reconstructed transactions or classified partial transactions with timestamps and outcome metadata
- `busPeriodicity` entries are keyed by normalized `(source, target, PB, SB)` tuple identity with sample count, last-seen, interval statistics, and capability/warmup state; `family` is a derived closed-set tag carried alongside, not part of tuple identity
- `PB` and `SB` here mean the eBUS primary-byte and secondary-byte command fields from the reconstructed master request header.
- `interval statistics` means a fixed-cost bounded summary per tuple:
  - `sample_count`
  - `last_interval`
  - rolling mean interval
  - `min_interval`
  - `max_interval`
  It does not imply percentiles, unbounded history retention, or per-entry histograms.
- In this section, `sample_count` means count of observed interval deltas, not count of raw transactions; therefore `3 observed intervals` requires `4` qualifying transactions for that tuple.
- Only successful classified terminal events contribute qualifying transactions for periodicity interval formation; abandoned, ambiguous, or decode-failed transactions do not.
- Per-tuple periodicity warmup requires at least `3` observed intervals before the tuple may leave `warming_up`; before that threshold the entry remains `warming_up` even if global passive capability is already `available`.
- Periodicity tuple readiness is independent of the global passive completed-transaction threshold, but an exported tuple may not present as fully ready until both its own `3`-interval threshold and the current global passive readiness conditions are satisfied.
- Periodicity budget is consumed by normalized raw `(source, target, PB, SB)` tuples, not by family buckets.
- MCP and GraphQL surfaces must return these bounded records directly; they must not infer or construct unbounded in-memory history on demand
- Timing quality for busy-time and periodicity must be exposed or documented as estimated unless the underlying transport supplies true wire timestamps
- `normalized` means source/target are bucketed to known addresses or `other` according to the bounded label policy.
- `known addresses` means the bounded union of:
  - addresses currently present in the live device registry for the adapter instance
  - the adapter's current local address when known
  - protocol-reserved addresses explicitly documented by this feature
- Even when a passive event is matched as an active/passive duplicate for shadow/write-efficiency purposes, its passive timing markers remain authoritative inputs to bus-level busy/periodicity tracking.
- `local_participant_inbound` traffic remains part of bus-level periodicity/busy tracking under its normalized `(source, target, PB, SB)` tuple identity; its exclusion applies only to shadow/write-efficiency semantics, not to bus observability.

### 11B. Logging conventions

- This feature requires structured logs for lifecycle and degraded-state transitions.
- At minimum, lifecycle/degraded logs must carry:
  - adapter instance identifier
  - component
  - old state / new state when applicable
  - reason enum
  - epoch / generation when applicable
  - key family / canonical key when applicable and bounded/safe to log
- Logging is complementary to metrics; it may not replace the required bounded metric surfaces.

### 12. Degraded transport behavior

- `ebusd-tcp` degraded mode contract:
  - `active=true`
  - `passive=false`
  - `broadcast=false`
  - busy-time aggregates are unavailable, not zero
  - passive efficiency aggregates are unavailable, not zero
  - broadcast-sourced passive updates are unavailable
  - broadcast-derived semantic surfaces must not claim live passive coverage on `ebusd-tcp`
  - energy semantics rely on active register reads only when available on this transport path
  - MCP/GraphQL must return `available=false` plus a reason
  - Portal must show an explicit degraded warning
  - Prometheus must expose capability info and omit unavailable aggregate series
- In this document, Prometheus `unavailable` means the value series itself is omitted while the corresponding capability/state gauge explicitly reports the unavailable state; sentinel numeric values are not used in v1.
- When true wire timestamps are unavailable, explicit `estimated` timing-quality markers on the relevant busy/periodicity MCP/GraphQL/API surfaces are mandatory in v1; mere silence about precision is not sufficient.
- Transport family is effectively static for a gateway process in v1. Switching transport family requires a restart-level reinitialization of capability and metric state; hot transport swaps are out of scope.

### 12A. Passive outage and reconnect semantics

- Passive outages do not reset monotonic counters.
- Initial passive connection enters the same `warming_up` state model as reconnects.
- Before the first successful passive connect, passive capability remains `unavailable`; `warming_up` begins only after a passive socket/feed has connected successfully.
- Warmup exit is explicit, not implicit:
  - global passive warmup exits only after both a minimum connected observation window and a minimum completed-transaction count are satisfied
  - per-periodicity entry warmup may remain until its own minimum sample threshold is met
  - outside B516 per-selector freshness and the global passive `passive_warmup_blocker_reason` surface, v1 does not expose additional warmup-reason enums for every downstream surface
  - Route A / Route B from this section are fallback-path exceptions only; they do not replace the primary `30s` / `20 transactions` warmup thresholds before the governing outer `5m` window is reached
- `completed transaction` for warmup counting means a successful classified passive terminal event, including successful broadcast and master-master terminals, but excluding abandoned/garbled/ambiguous partial transactions.
- `healthy symbol ingress` is satisfied only by the Route A / Route B rules in this section; the phrase does not mean arbitrary socket health or arbitrary byte presence outside those bounded rules
- Transport reset on a still-live passive connection is not treated identically to full passive socket loss.
- On ENH/ENS `RESETTED` or equivalent passive-epoch boundary without connection loss:
  - reconstructor state resets immediately
  - pending dedup state and other contiguous-history-dependent subscriber state reset immediately
  - passive capability need not transition all the way to `unavailable` if the socket remains healthy
  - timing/confidence-sensitive passive outputs such as busy-time and periodicity re-enter `warming_up` for a bounded post-reset settling period and fresh completed-transaction threshold
  - the long-lived connection-health window does not need to restart from zero solely because of adapter reset if the socket itself remained healthy
  - if reset/discontinuity occurs while already in `warming_up`, the state remains `warming_up`; the passive epoch bumps, post-reset settling counters restart from zero, the post-reset threshold set replaces the initial/reconnect `30s`/`20` thresholds for that settling episode, and the initial startup `5m` wall-clock deadline never resets merely because the passive socket reconnects
- Default warmup thresholds:
  - initial/reconnect connected observation window: `30s`
  - initial/reconnect completed transactions: `20`
  - post-reset settling window on healthy socket: `5s`
  - post-reset completed transactions: `10`
- Passive capability state machine is explicit:
  - `unavailable -> unavailable` on failed reconnect/probe attempt while retry/backoff continues
  - `unavailable -> warming_up` on successful passive connect
  - `warming_up -> available` when warmup thresholds are met
  - `warming_up -> warming_up` on transport reset / discontinuity while already warming up
  - `warming_up -> unavailable` on passive socket loss, endpoint unsupported/misconfigured determination, startup timeout, reconnect timeout, or explicit capability withdrawal reason
  - `available -> warming_up` on transport reset / discontinuity that preserves socket health
  - `available -> unavailable` on passive socket loss or explicit capability withdrawal
- If startup never establishes a healthy passive session within `5m`, or if the first connected passive session still never satisfies startup warmup criteria within that same `5m` startup window, passive transitions to `unavailable` with reason rather than remaining indefinitely in `warming_up`.
- The two outer `5m` windows are named explicitly:
  - `startup_outer_window`: one wall-clock `5m` budget from gateway startup
  - `reconnect_outer_window`: one per-episode `5m` budget after a post-startup reconnect or reset episode begins
- After the `5m` startup downgrade to `unavailable`, background reconnect/probe attempts continue at max backoff while endpoint state is not `unsupported_or_misconfigured`; only that explicit state stops retrying.
- The initial startup `5m` window is a wall-clock budget from gateway startup and does not roll forward on repeated passive socket reconnects.
- For the fallback rules below, the `fallback window` means the outer `5m` startup or reconnect/reset window, not the shorter `30s`/`5s` warmup counters.
- `healthy symbol ingress` for that fallback window is satisfied by one of:
  - route A: at least one successful classified passive terminal event in the fallback window, using the same success definition as `completed transaction` in this section
  - route B: at least `100` decoded logical bus symbols in the fallback window, where `decoded logical bus symbols` means Section 3 `LogicalBusSymbol` instances after eBUS escape decoding, with no disconnect/reset fault in that same window, plus reconstructor liveness proven by at least `1` classified passive event of any terminal kind (successful or explicit abandoned/error classification) in the same fallback window
    The Route B conditions may be satisfied in any order within the same fallback window; evaluation occurs whenever either counter changes and succeeds only when both predicates are simultaneously true for that window.
    Re-evaluation happens immediately on every relevant counter or fault-state change against the current window snapshot; it is not deferred until both counters change again.
- raw symbol ingress alone is insufficient to promote global passive capability to `available`
- Any transport reset or passive socket-loss event during the fallback window resets the Route A / Route B ingress counters for that startup/reconnect episode back to zero; only the outer `5m` fallback deadline survives the reset.
- Startup and post-startup reconnect episodes use the same Route A / Route B fallback thresholds; only the governing outer deadline differs between the startup wall-clock window and a post-startup reconnect episode.
- Reconnect/reset warmup after startup is also bounded per reconnect episode: if a healthy passive socket remains connected for `5m` after reconnect/reset without reaching the completed-transaction threshold, global passive capability may transition to `available` only if healthy symbol ingress has been observed during that reconnect window; otherwise it remains `warming_up` or degrades according to the outer state-machine rules
- when global passive capability is `warming_up`, operator-facing diagnosis uses the bounded `passive_warmup_blocker_reason` surface rather than requiring consumers to infer cause from raw counters alone
- Reconnect/reset flap dampening is explicit:
  - reconnect episodes continue to use the exponential backoff from Section 3A
  - if `3` reconnect/reset episodes occur within `10m` without reaching `available`, passive capability degrades to `unavailable` for that episode class until a fresh reconnect attempt begins after backoff
  - repeated reset flapping may therefore keep B516 selectors in `warming_up`, but it may not do so silently or without capability-state evidence
  - this dampening outcome remains `temporarily_disconnected`, not `unsupported_or_misconfigured`, and lasts for one full reconnect backoff interval at the current backoff tier before the next fresh reconnect attempt may promote capability again
  - one `dampened cycle` means one full dampen/backoff/retry attempt sequence after a flap-dampening trigger has fired
  - if `3` consecutive dampened cycles complete without ever reaching `available` and without satisfying Route A or Route B healthy symbol ingress, the endpoint escalates to `unsupported_or_misconfigured` for the remainder of the process lifetime
- `startup_timeout` applies only to the initial startup wall-clock `5m` window.
- `reconnect_timeout` applies only to post-startup reconnect episodes that exhaust their per-episode `5m` fallback window without meeting the documented fallback criteria.
- `passive_capability_unavailable_reason` maps to runtime endpoint/capability state as follows:
  - startup window expired before usable passive readiness -> `startup_timeout`
  - post-startup reconnect episode exhausted its fallback window -> `reconnect_timeout`
  - previously working endpoint lost socket/transport health -> `socket_loss`
  - reconnect/reset flap dampening temporarily suppressed new promotion attempts -> `flap_dampened`
  - endpoint disproved passive support or is misconfigured -> `unsupported_or_misconfigured`
  - operator/runtime explicitly withdrew passive capability -> `capability_withdrawn`
- the per-reconnect `5m` fallback window applies only after the initial startup window has already exited to either `available` or `unavailable`; during startup, the startup wall-clock window is the sole governing outer deadline
- Startup uses the same fallback semantics once a passive socket has connected successfully: if the first connected passive session has healthy symbol ingress for the full `5m` startup window but still misses the completed-transaction threshold, global capability may transition to `available` as a fallback-path exception while tuple-level/periodicity sample sufficiency remains in warmup/insufficient-samples state
- On a legitimately idle bus with no successful classified passive events and insufficient Route B symbol evidence, passive capability degrades to `unavailable` after the governing `5m` startup/reconnect window; this is expected behavior, not a hidden fault.
- During passive outage:
  - active-scoped counters may continue
  - whole-bus busy-time and periodicity are `unavailable`, not degraded into misleading active-only values
  - recent-message and periodicity views may retain prior bounded history, but must expose passive capability as unavailable
- After passive reconnect:
  - counters continue from their prior monotonic values
  - busy-time and periodicity enter an explicit warmup state before reporting normal values again
  - MCP/GraphQL capability state must distinguish `available`, `unavailable`, and `warming_up`

### 12B. Cold-start behavior

- On gateway cold start, `ShadowCache` and scheduler freshness start empty.
- Observe-first therefore begins in an active-only effective mode until passive warmup completes and relevant shadow entries accumulate.
- This startup phase is expected and must not be misreported as steady-state observe-first inefficiency.
- Watch-efficiency and capability surfaces must distinguish startup/warmup behavior from steady-state no-savings behavior.
- In v1 that distinction is surfaced by the passive warmup metrics/state:
  - `passive_warmup_state{state}`
  - `passive_warmup_completion_mode{mode}`
  - `passive_warmup_blocker_reason{reason}`
  - zero/omitted watch-efficiency counts while those warmup surfaces remain active are interpreted as startup/warmup, not steady-state inefficiency
- If `observe_first_enabled=true` but passive capability remains persistently `unavailable` for the adapter instance, the system behaves as active-only plus observability/audit overhead:
  - generic passive shadow satisfaction never becomes eligible
  - active-confirmed shadow writes and audit surfaces may still exist
  - watch-efficiency metrics remain zero or omitted for passive-assisted paths
  - operators should treat this as an active-only deployment for that adapter instance until passive capability is restored

### 13. Snapshot and notification semantics

- This feature does not make semantic snapshots globally atomic across planes.
- Snapshot reads remain composed from current provider state and may show cross-plane skew.
- Passive asynchronous updates can widen observed skew relative to poll-only operation.
- v1 contract:
  - this skew is accepted and must be documented explicitly
  - no API may claim strict cross-plane atomicity unless a real global snapshot mechanism exists
  - snapshot/meta docs must distinguish “stable snapshot id semantics” from “global multi-plane atomicity”
- Steady-state integration validation should keep observed cross-plane skew within `max(poller publish cadence, stream interval)`, but this is an operational target rather than an API guarantee.
- For this validation target, `observed cross-plane skew` means the wall-clock delta between the oldest and newest `last_updated_at` timestamps among the semantic surfaces included in the same snapshot/assertion.
- Any validation against that skew target must record the concrete configured poller publish cadence and stream interval used in the test run; the target is not falsifiable without those deployment values and those `last_updated_at` fields.
- Notification latency budget by surface:
  - GraphQL subscriptions: bounded by the next configured poller publish cycle that incorporates eligible shadow-backed reads
  - Portal SSE semantic stream: bounded by the configured stream interval after provider state changes
  - MCP and GraphQL query reads: return the current provider state at read time
- This spec does not set the numeric poller publish cadence or Portal stream interval; those remain runtime/configuration concerns owned by the existing gateway subsystems. The contract here is the ownership boundary, not the numeric interval value.

### 14. Rollback model

- Feature flags are introduced before any behavior-changing integration.
- In v1 these feature flags are runtime-mutable control-plane inputs; a change is applied as an adapter-scoped epoch-boundary event rather than requiring process restart.
- With `observe_first_enabled=false` in v1:
  - passive tap, reconstructor, passive bus observability, and the B516 broadcast-energy path remain enabled
  - `WatchCatalog` remains constructed and observable
  - runtime sub-flags such as `passive_state_direct_apply`, `passive_config_direct_apply`, and non-recording external-write observe-first effects are treated as inactive regardless of their configured values
  - generic passive shadow direct-apply, scheduler shadow satisfaction, and passive external-write invalidation of scheduler/shadow state are disabled
  - under this master-off state:
    - `record_only` continues as bounded audit/debug recording only
    - a raw `invalidate_only` setting is a no-op for scheduler/shadow semantics in this state until normalization is applied; after normalization it follows the effective `record_only` behavior, so the event is audit-recorded but never invalidates scheduler/shadow state
    - `record_and_invalidate` degrades to `record_only`
  - passive observations may still feed bounded audit/debug summaries, but not scheduler-eligible generic shadow state
  - this master-off suppression is broader than the Section 9 catalog-miss/inactive-selector rule: even active catalog hits may not produce generic scheduler-eligible passive shadow state while master-off is in effect
  - watch-efficiency metrics remain exported but should stay at zero or omitted for paths whose eligibility is disabled by the flag state
- Runtime flag normalization rules are exhaustive in v1:
  - if `observe_first_enabled=false`, then `passive_state_direct_apply=false` and `passive_config_direct_apply=false` for runtime behavior regardless of configured sub-flags
  - if `passive_state_direct_apply=false`, then `passive_config_direct_apply=false`
  - if `passive_state_direct_apply=false`, then `external_write_policy` is effectively clamped to `record_only` because no generic shadow/direct-apply path remains to invalidate safely for benefit
  - if `passive_config_direct_apply=true` and `external_write_policy=record_only`, runtime normalization clamps that combination to `record_and_invalidate`
  - normalization order is fixed:
    1. apply `observe_first_enabled` master-off clamp
    2. apply `passive_state_direct_apply=false` => `passive_config_direct_apply=false`
    3. apply the `passive_state_direct_apply=false` => `external_write_policy=record_only` clamp
    4. evaluate any remaining `passive_config_direct_apply` / `external_write_policy` consistency rules
  - no other hidden normalization paths exist in v1
  - this normalization sequence runs both at startup and after every runtime flag-change event before the new effective state is applied
- Forward-enable semantics are explicit:
  - changing `observe_first_enabled` from `false -> true` is an adapter-scoped epoch-boundary event
  - the runtime first bumps the relevant scheduler/shadow generation epoch, then allows new shadow eligibility under the enabled policy set
  - an in-flight `Get()` that started under the disabled epoch may not gain a new shadow hit mid-call merely because the flag flipped; only subsequent reads in the newer epoch may use the enabled observe-first path
  - setting any feature flag to the value it already has is a no-op and may not bump epoch, clear freshness, or emit rollback/transition side effects
  - any normalization that changes the effective runtime state away from the raw configured combination must emit diagnostics and increment `feature_flag_normalizations_total{reason}`
  - once a raw configuration is normalized, all runtime behavior follows the effective normalized state; for example a raw `invalidate_only` setting clamped to `record_only` under master-off or state-direct-disabled does produce bounded audit/debug recording because the effective policy is `record_only`
- If proof fails:
  - passive direct-apply stays disabled
  - system falls back to record-only observe mode plus active polling
  - observability remains enabled
- On rollback to record-only mode:
  - rollback is treated as an adapter-scoped epoch-boundary event for scheduler/shadow interaction
  - the runtime first disables new observe-first shadow satisfaction for that adapter instance, then bumps the relevant scheduler/shadow generation epoch; that rollback epoch bump is the same per-key generation/invalidation domain defined in Section 8A
  - after that epoch bump, the runtime invalidates passive-derived eligible shadow entries and clears scheduler freshness under that newer epoch
  - any in-flight or concurrent `Get()` observing an older epoch must fail closed to the non-observe-first path rather than committing a shadow hit across the rollback boundary
  - passive-derived eligible shadow entries are invalidated
  - scheduler freshness seeded from passive observe-first is cleared
  - record-only observability history may remain for diagnostics
  - rollback-driven invalidations must use `reason=rollback` in invalidation metrics and logs

## Mega Doc-Gate

### Rule

- Documentation is merge-blocking for this feature.
- M0 creates skeletons with locked decisions and milestone-owned sections.
- Contracts are frozen only when their milestone is implemented and validated.
- Each required doc must contain:
  - scope
  - invariants
  - degraded behavior
  - unsupported/unproven cases
  - evidence section
  - falsification cases
  - concrete examples
- `DOC-xx` artifact ids and `ISSUE-DOC-xx` issue ids are separate namespaces in this plan; equal numbers do not imply the same artifact.

### Required docs

`DOC-01` `architecture/observe-first-watch-registry.md`
- watch catalog
- runtime activation
- shadow cache
- scheduler integration
- precedence rules

`DOC-02` `architecture/bus-observability-v2.md`
- busy-time model
- error taxonomy
- periodicity model
- capability matrix by transport
- Prometheus/expvar coexistence

`DOC-03` `architecture/decisions.md`
- ADR: observe-first semantic reads
- ADR: active vs passive bus observability split
- ADR: passive tap replaces standalone broadcast connection ownership
- ADR: GraphQL for domain data, Portal API for portal-native surfaces

`DOC-04` `api/mcp.md`
- `ebus.v1.bus.summary.get`
- `ebus.v1.bus.messages.list`
- `ebus.v1.bus.periodicity.list`
- The `ebus.v1.bus.*` namespace is intentionally separate from semantic MCP tools because it exposes bus-observability/raw-traffic domain data rather than protocol-agnostic semantic state.

`DOC-05` `api/graphql.md`
- `busSummary`
- `busMessages`
- `busPeriodicity`

`DOC-06` `api/portal.md`
- GraphQL-fed bus/watch views
- portal-native stream/timeline/bootstrap
- degraded mode behavior
- optional `bus` stream layer

`DOC-07` protocol doc updates
- `protocols/ebus-vaillant-B516-energy.md`
- `protocols/ebus-vaillant-B524-register-map.md`
- `protocols/ebus-vaillant-B509-boiler-register-map.md`
- `protocols/ebus-vaillant-b555-timer-protocol.md`
- `protocols/ebusd-tcp.md`

`DOC-08` validation docs
- extend `architecture/adversarial-matrix.md`
- update `development/end-to-end-smoke.md`
- update `development/smoke-matrix.md` where this feature depends on matrix evidence
- add tiny observability notes

`DOC-09` watch-summary contracts
- MCP: `ebus.v1.watch.summary.get`
- GraphQL: `watchSummary`
- query-on-gap and watch-summary semantics

### Doc acceptance gate

- No `PROVEN` claim without evidence.
- No conservative rule may be silently upgraded later; promotion requires a doc update.
- All stale B555 filename references must be fixed in the doc milestone.

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
  10. `ISSUE-GW-18`
  11. `ISSUE-DOC-05`

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

### M2. MCP first

- Execution order inside M2 is explicit:
  1. `ISSUE-GW-04`
  2. `ISSUE-DOC-06`

`ISSUE-GW-04` `helianthus-ebusgateway`
- Implement MCP tools
- Acceptance:
  - `ebus.v1.bus.summary.get`
  - `ebus.v1.bus.messages.list`
  - `ebus.v1.bus.periodicity.list`
  - `bus.messages.list` returns bounded recent-message records from the store ring buffer
  - `bus.periodicity.list` returns bounded periodicity summaries with capability/warmup state
  - timing-quality metadata is explicit when busy/periodicity values are estimated rather than wire-timestamped
  - explicit capability fields and degraded reasons

`ISSUE-DOC-06` `helianthus-docs-ebus`
- Freeze MCP contract against real output
- Acceptance:
  - bounded `busMessages` and `busPeriodicity` response models are explicit
  - capability and warmup states are documented
  - timing-quality semantics for estimated metrics are documented

### M3. GraphQL parity

- Execution order inside M3 is explicit:
  1. `ISSUE-GW-05`
  2. `ISSUE-DOC-07`

`ISSUE-GW-05` `helianthus-ebusgateway`
- Implement GraphQL parity
- Acceptance:
  - `busSummary`
  - `busMessages`
  - `busPeriodicity`
  - GraphQL list fields expose the same bounded recent-message and periodicity-summary model as MCP
  - timing-quality semantics are preserved relative to MCP
  - unavailable states are explicit

`ISSUE-DOC-07` `helianthus-docs-ebus`
- Freeze GraphQL contract
- Acceptance:
  - bounded list-model parity with MCP is explicit
  - unavailable vs warming-up states are documented
  - estimated-timing semantics are documented

### M4. Watch catalog, shadow cache, feature flags

- Execution order inside M4 is explicit:
  1. `ISSUE-GW-06`
  2. `ISSUE-GW-08`
  3. `ISSUE-GW-07`
  4. `ISSUE-GW-09`
  5. `ISSUE-DOC-08`

`ISSUE-GW-06` `helianthus-ebusgateway`
- Implement `WatchCatalog`
- Acceptance:
  - concrete descriptor structure
  - descriptor structure separates coarse semantic class from freshness profile; `state_fast` / `state_slow` are freshness-profile values, not new semantic classes
  - activation derived from explicit code-owned selector lists
  - no wildcard unbounded activation
  - canonical shared key builders/types exist outside `main` and are used by both scheduler call sites and passive correlation code
  - activation source is recorded as provenance enum, not as access-control policy
  - watch-catalog construction is feature-flag agnostic; later feature flags gate runtime use of shadow/policy behavior, not catalog definition itself
  - catalog/inactive selector observations feed bounded observability/debug summaries but do not allocate shadow entries

`ISSUE-GW-07` `helianthus-ebusgateway`
- Implement bounded `ShadowCache`
- Acceptance:
  - hard capacity
  - pinned vs evictable entries
  - startup/config validation failure for pinned-budget overflow disables observe-first shadowing for that adapter instance without aborting gateway process startup
  - precedence model
  - observation timestamps prevent older active-confirmed writes from overwriting newer passive evidence
  - invalidation epoch participates in shadow acceptance, so an `active_confirmed` write from a fetch that started before the current invalidation epoch cannot overwrite any newer-generation shadow entry, whether tombstone or repopulated value, only because its completion timestamp is newer
  - invalidated entries remain retained for diagnostics but are tombstoned/ineligible for scheduler satisfaction
  - scheduler post-lock revalidation consumes a lock-free or atomically readable per-entry generation/eligibility snapshot exported by `ShadowCache`; it may not require reacquiring the full `ShadowCache` mutex while the scheduler mutex is held
  - pinned invalidated tombstones compact after the default `15m` retention window, are swept by the bounded background compactor, and after the hard `24h` tombstone lifespan may be de-pinned from `ShadowCache` while the watch remains active in `WatchCatalog`
  - pinning does not block semantic invalidation
  - invalidation-epoch bookkeeping is core `ShadowCache` state and is semantically independent of particular flag values
  - GW-07 still consumes the narrow immutable flag/config interface from GW-08, but only later policy code uses those values to decide when the already-present bookkeeping should be exercised

`ISSUE-GW-08` `helianthus-ebusgateway`
- Add feature flags before behavior changes
- Acceptance:
  - `observe_first_enabled`
  - `passive_state_direct_apply`
  - `passive_config_direct_apply`
  - `external_write_policy`
    Valid values are bounded to:
    - `invalidate_only`
    - `record_only`
    - `record_and_invalidate`
  - defaults conservative enough to disable behavior without removing observability
  - invalid flag combinations are normalized explicitly rather than silently becoming dead settings
  - `passive_state_direct_apply` and `passive_config_direct_apply` require `observe_first_enabled`
  - `passive_config_direct_apply` may not be enabled while `passive_state_direct_apply` is disabled
  - `passive_config_direct_apply=true` may not coexist with `external_write_policy=record_only`; startup validation normalizes that combination to an invalidating policy because config direct-apply without external-write invalidation is unsafe
  - `external_write_policy` values have explicit startup-validated semantics rather than symbolic names only; GW-08 validates admissible values/combinations and documented meaning against `DOC-01`, later finalized by `ISSUE-DOC-08`, while GW-07/GW-09 implement the runtime enforcement paths
  - GW-08 exposes only an immutable feature-flag config/state interface consumed by GW-07/GW-09; GW-07 may not import GW-08 implementation internals
  - feature-flag state is exported via metrics and diagnostics

`ISSUE-GW-09` `helianthus-ebusgateway`
- Implement family policy engine
- Acceptance:
  - response-class classification is a first-class pre-policy stage owned by this engine; downstream policy checks consume the bounded response-class enum rather than re-deriving ad hoc labels elsewhere
  - B516 direct-apply candidate only through the dedicated energy merge path
  - B524 direct-apply candidate only for correlated state reads
  - B524 observed writes route to the generic external-write invalidation policy, not the correlated-read direct-apply path
  - B509 direct-apply candidate only for payload-bearing reads
  - B555 uses the generic conservative `record/invalidate` mode
- Validation:
  - replay tests prove B509/B524 response-shape mapping into the Section 5A `response_class` enum
  - replay tests cover decoder-selection ambiguity and prove ambiguous cases are rejected from direct-apply
  - replay tests cover externally observed writes under each runtime `external_write_policy`
  - falsification tests prove wrong-family or wrong-policy application is rejected rather than silently reclassified

`ISSUE-DOC-08` `helianthus-docs-ebus`
- Update architecture docs with actual watch catalog, memory budget, flags, and family rules
- Acceptance:
  - B516 energy carve-out and passive pipeline fan-out architecture are explicit
  - shared key-construction contract is explicit
  - invalidate-only semantics are explicit
  - energy broadcast freshness / provenance semantics are explicit

### M5. Observe-first scheduler integration

- Execution order inside M5 is explicit:
  1. `ISSUE-GW-10`
  2. `ISSUE-GW-12`
  3. `ISSUE-GW-11`
  4. `ISSUE-DOC-09`
- Rationale:
  - `ISSUE-GW-10` lands the scheduler/shadow semantics first
  - `ISSUE-GW-12` depends on that runtime eligibility behavior for meaningful efficiency metrics
  - `ISSUE-GW-11` can then expose stable watch-summary/query surfaces over the now-defined scheduler/watch behavior

`ISSUE-GW-10` `helianthus-ebusgateway`
- Integrate `ShadowCache` into `SemanticReadScheduler`
- Acceptance:
  - scheduler remains intact as coalescer + breaker
  - shadow cache is consulted before active fetch
  - shadow consultation happens outside the scheduler mutex and any candidate shadow hit is revalidated after scheduler-lock acquisition before commit
  - post-lock revalidation includes shadow generation/invalidation state, not only scheduler-local freshness/coalescing state, so an intervening external-write invalidation cannot seed a fresh scheduler `lastOK`
  - eligible shadow hits refresh scheduler cache
  - eligible shadow hits bypass the active-read breaker guard
  - shadow hits do not reset breaker failure counters or alter active transport health state
  - active fetch completion carries a start-generation/invalidation token and may not reseed scheduler `lastOK` or `lastOKAt` if an intervening invalidation/newer generation occurred while the fetch was in flight
  - observe-first call sites use per-key or per-freshness-profile caller `maxAge` profiles rather than the current hard-coded `500ms` ceiling on B509/B524 state reads
  - the default caller `maxAge` profile table is implemented exactly as documented unless a narrower key-specific override exists
  - the effective shadow freshness limit remains `min(caller maxAge, watcher TTL)`
  - at most one immediate recompute attempt is allowed after an invalidation-race discard; repeated invalidation races fail closed instead of looping indefinitely
  - post-revalidation decision priority is explicit: join an existing coalesced fetch if present; else start one active fetch if the breaker allows; else fail closed as unavailable/error
  - repeated shadow consult/revalidate retries are bounded to the documented maximum per `Get()` call and may not spin indefinitely under contention
  - total retry composition per `Get()` call is globally capped: two consult/revalidate passes before the first active decision, plus at most one immediate recompute cycle after an invalidation-race discard
  - v1 keeps breaker thresholds static even when passive health indicates shared-bus contention rather than transport death
  - external-write invalidation clears or ages out matching scheduler freshness so pre-write cached values are not served as eligible reads
  - concurrent active-fetch races for the same key are resolved by generation/order rules: an older or stale-completing fetch may not overwrite a newer-generation result, and same-generation concurrent completions use the newer accepted result only

`ISSUE-GW-11` `helianthus-ebusgateway`
- Add watch-summary surfaces after the watch system exists
- Acceptance:
  - MCP: `ebus.v1.watch.summary.get`
  - GraphQL: `watchSummary`
  - outputs include activation counts, freshness classes, direct-apply eligibility classes, degraded capability markers

`ISSUE-GW-12` `helianthus-ebusgateway`
- Add watch-efficiency metrics
- Acceptance:
  - metrics are computed strictly over the GW-10-defined generic observe-first shadow/scheduler eligibility path; they may not backfill missing semantics by inferring their own eligibility model
  - `passive_hits`
  - `direct_apply`
  - `active_reads_avoided`
  - `active_read_saved_seconds`
  - `ambiguous`
  - `missed_due_to_transport_limitations`
  - `missed_due_to_transport_limitations` counts observe-first-eligible reads in a `(family, freshness_profile)` bucket that could not use passive assistance because the current transport capability for that path is explicitly `passive=false`, `broadcast=false`, or equivalent transport-level limitation documented by the capability model
  - duration-saved estimation uses the rolling mean of the last `32` successful logical request-complete durations for the same `(family, freshness_profile)` bucket, including retries where appropriate; the series is omitted until at least `5` samples exist
  - duration-saved rolling means stale out after `15m` without new successful samples for that bucket; stale estimates are omitted until refreshed
  - documentation and UI text must describe duration-saved as a bucket-level estimate, not a per-key guaranteed saving
  - cold-start and passive warmup periods are identified so zero savings during startup is not misreported as steady-state inefficiency

`ISSUE-DOC-09` `helianthus-docs-ebus`
- Freeze watch-summary MCP/GraphQL contracts and document query-on-gap truth table plus scheduler/shadow-cache interaction
- Document observe-first freshness profiles and the fact that legacy `500ms` read windows are not the v1 shadow policy
- Document snapshot skew semantics and notification latency budgets for GraphQL subscriptions vs Portal SSE vs query reads
- Document shadow write-order semantics and breaker-bypass semantics explicitly
- Document invalidation-epoch interaction for both scheduler write-back and `active_confirmed` shadow writes explicitly
- Document breaker-contention limitation and feature-flag validity rules explicitly
- Document cold-start observe-first behavior and invalidation semantics explicitly

### M6. Semantic publish and Portal

- Execution order inside M6 is explicit:
  1. `ISSUE-GW-13`
  2. `ISSUE-GW-14`
  3. `ISSUE-DOC-10`

`ISSUE-GW-13` `helianthus-ebusgateway`
- Publish shadow-derived semantic updates through the existing poller/provider path
- Acceptance:
  - `ShadowCache` does not write directly to `LiveSemanticProvider`
  - B516 energy remains an explicit carve-out using the existing energy merge/provider path and is not double-written into generic shadow-backed state
  - energy merge/provider outputs expose broadcast freshness or broadcast-health metadata sufficient to distinguish stale broadcast-derived values from fresh register-backed values after passive pipeline disruption
  - gateway Prometheus exposition for energy freshness state and transitions is implemented here, including `energy_broadcast_selectors{state}` and `energy_broadcast_freshness_transitions_total{from,to}`
  - stale broadcast-derived values remain queryable with timestamp/provenance metadata rather than being silently dropped or silently presented as fresh
  - `never_seen/unavailable` broadcast freshness is distinct from `stale`, and the same freshness-state contract is used by MCP, GraphQL, and Portal
  - existing semantic merge helpers remain the single place that assembles zone/DHW/energy/boiler/circuits/radio snapshots
  - provider writes and GraphQL subscription publishes remain poller-owned
  - passive-derived values can appear in provider state only after the poller consumes eligible shadow-backed reads
  - zone/DHW/energy/boiler/circuits/radio updates can flow without schema churn
  - GraphQL subscriptions receive passive-derived updates through the existing publish path, not a second out-of-band publisher

`ISSUE-GW-14` `helianthus-ebusgateway`
- Add Portal bus observability UI
- Acceptance:
  - GraphQL for domain aggregates
  - Portal API only for bootstrap/stream/timeline/snapshots
  - any required `bus` bootstrap or stream/timeline layer wiring from `DOC-06` is implemented explicitly rather than implied
  - bootstrap/stream wiring must at minimum expose passive capability state, warmup state, and degraded banners needed by the bus observability view
  - if a bus SSE/timeline layer is implemented, its event types and warmup/degraded visibility rules are fixed in this issue rather than deferred entirely to docs
  - degraded mode banner on `ebusd-tcp`
  - `warming_up` is visually distinct from `degraded/unavailable`

`ISSUE-DOC-10` `helianthus-docs-ebus`
- Update `api/portal.md` and overview after the real Portal wiring lands
- Document the notification-latency split between GraphQL subscriptions and Portal SSE stream surfaces
- Document energy freshness/provenance surfaces for broadcast-derived values

### M7. Proof, rollback decision, default flip

- Execution order inside M7 is explicit:
  1. `ISSUE-GW-15`
  2. `ISSUE-GW-16`
  3. `ISSUE-DOC-11`

`ISSUE-GW-15` `helianthus-ebusgateway`
- Run lab proof
- Acceptance:
  - proof verdict is split explicitly:
    - safety gate for observe-first/default-flip: wrong-key detection, canary validation, replay falsification, and read-avoidance correctness
    - timing-quality gate for busy/periodicity metric maturity: tolerance checks for estimated timing metrics
  - 24h run with no wrong-key apply
  - "no wrong-key apply" is backed by an explicit detection mechanism rather than absence of observed mismatches; required evidence includes structured passive-apply audit traces and stable-register canary validation, not only ad-hoc value comparison
  - stable-register canaries are defined in advance in the proof plan as a fixed committed set of config/discovery registers expected not to change during the proof window; they are actively re-verified at least hourly, and any passive/apply mismatch is a proof failure
  - canary re-verification is independent of the shadow path under test: it uses explicit active direct reads on the live protocol path and those reads are excluded from read-avoidance accounting
  - canary re-verification read failures are handled explicitly:
    - each scheduled canary verification may retry up to `3` times within the verification window
    - if all retries fail, that canary interval is marked `inconclusive`, not silently passed
    - the overall proof requires at least `90%` of scheduled canary intervals to be conclusive
    - each canary must independently achieve at least `75%` conclusive scheduled intervals; healthy canaries may not mask one systematically failing canary
    - if either the overall or per-canary threshold fails, the proof run is failed and must be restarted as a full new proof window after remediation; partial reuse of the old window is not allowed
  - operator-initiated changes to canary registers invalidate the affected canary interval unless they were pre-declared in the proof plan; proof may not silently treat expected operator mutations as either a clean pass or a protocol bug
  - feature-flag state participating in the proof is immutable for the duration of the proof run; any mid-proof flag change invalidates the run
  - proof traffic minimums are explicit:
    - at least `1000` completed passive transactions observed
    - at least `100` passive direct-apply candidates evaluated
  - canary set minimums are explicit:
    - at least `6` canary registers total
    - at least `2` from B524 direct-apply-enabled state/config surfaces
    - at least `2` from B509 direct-apply-enabled state/config surfaces
    - any family later promoted to direct-apply must contribute at least `2` canaries before proof can pass for that family
  - periodicity and busy metrics are validated against wire evidence with explicit tolerances, not exact-equality language:
    - the `wire-derived reference` must come from an independent timestamped reference capture such as a lab wire logger, external analyzer, or proxy-side timestamped mirror; the gateway's own estimated timing path may not serve as its own proof reference
    - busy ratio over windows `>= 5m` stays within `15%` relative error of wire-derived reference on passive-capable transports without true wire timestamps
    - periodicity rolling-mean interval for stable tuples with at least `10` samples stays within `max(20%, 2s)` of wire-derived reference
  - timing-quality tolerance failures keep busy/periodicity metrics in estimated/experimental status and require doc/metric follow-up, but do not by themselves fail the safety gate for `passive_state_direct_apply` if the safety criteria above pass
  - read avoidance is measurable under real shared-bus traffic
  - adversarial replay proof covers garbled transaction boundaries and demonstrates that unsafe passive B524 correlation is abandoned rather than applied
  - adversarial replay proof explicitly includes a B524 dual-namespace ambiguity case and demonstrates that multi-decoder matches are classified `ambiguous` and rejected from direct-apply
  - proof artifact reports both avoided-read counts and estimated active-read duration saved
  - proof reports cold-start and post-warmup behavior separately
  - proof records the configured poller publish cadence and stream interval and measures cross-plane skew using the Section 13 `last_updated_at` delta definition
  - the safety gate and any resulting default flip apply only to the passive-capable transport/topology families that individually pass the proof and replay matrix; proof on one passive transport family may not silently authorize the flip on another unproven family
  - gateway crash, restart, or proof-run interruption invalidates the in-progress 24h proof window; partial runs do not count as completed proof evidence
  - proof includes a rollback smoke step that flips observe-first from enabled to disabled, proves shadow satisfaction stops immediately, proves concurrent readers fail closed across the rollback epoch, and proves rollback invalidation metrics emit `reason=rollback`

`ISSUE-GW-16` `helianthus-ebusgateway`
- Decide feature-flag default state
- Acceptance:
  - if the GW-15 safety gate passes, enable `passive_state_direct_apply` only on the passive-capable transport/topology families individually proven by GW-15
  - timing-quality gate failures from GW-15 may defer promotion of busy/periodicity metrics from estimated/experimental to stable, but do not by themselves block the observe-first default flip once the safety gate passes
  - if proof fails, keep record-only mode and document rollback

`ISSUE-DOC-11` `helianthus-docs-ebus`
- Promote only evidence-backed claims from `candidate` to `proven`

### M8. Tinyebus

- `M8` numbering is historical only. Earliest start is immediately after the shared metric contract freezes at `ISSUE-GW-03` + `ISSUE-DOC-05`; it does not wait for M7.
- Execution order inside M8 is explicit:
  1. `ISSUE-TE-01`
  2. `ISSUE-TE-02`
  3. `ISSUE-DOC-12`

`ISSUE-TE-01` `helianthus-tinyebus`
- Add fixed-memory collector + custom Prometheus text encoder
- Acceptance:
  - metric scope is explicitly limited to raw firmware-observable counters in T0, such as frame counts, error counts, and bus-active duration/counter surfaces
  - metric-name alignment with gateway is explicit for the T0 subset:
    - `ebus_frames_observed_total`
    - `ebus_errors_total`
    - `ebus_bus_busy_seconds_total`
  - no dependency on `prometheus/client_golang`
  - hard limit `512` entries max in the fixed-size collector table
  - T0 label admission must be bounded so `frames_observed_total` alone cannot exhaust the `512`-entry collector table; any excess combinations fold into bounded overflow buckets before starving error/busy metrics
  - TinyGo-safe
  - Go tests verify the text exposition format for deterministic sample collector snapshots

`ISSUE-TE-02` `helianthus-tinyebus`
- Integrate observability into emulation and bus stubs
- Acceptance:
  - deterministic emulation scenarios drive non-zero collector outputs for the limited T0 metric set
  - bootstrap runtime can export those deterministic collector snapshots
  - explicit note that device-side `/metrics` requires later networking/runtime work

`ISSUE-DOC-12` `helianthus-docs-ebus`
- Document tiny observability contract and limits

### M9. Optional HA consumer rollout

`ISSUE-HA-01` `helianthus-ha-integration`
- Optional rollout of observability/watch diagnostics after GraphQL parity is stable
- Acceptance:
  - no core behavior dependency
  - if implemented, expose diagnostics only, not new control paths
  - diagnostics are read-only and derived from already-stable GraphQL/MCP surfaces
  - no new write/control entities or automation side effects
  - if skipped, no earlier milestone contract changes

## Validation and Adversarial Gates

### Repo-local tests

- `helianthus-ebusgo`
  - unit tests for observer interface and bus hook wiring
  - retry/error path tests
  - no false reference to `T01..T88` as a local test suite
- `helianthus-ebusgateway`
  - replay tests for passive correlation
  - shadow cache precedence tests
  - scheduler integration tests
  - Prometheus exposition tests
  - MCP/GraphQL parity tests
  - Portal degraded-mode tests

### Runtime matrix gate

- `T01..T88` is the gateway runtime topology matrix from `helianthus-ebusgateway/internal/matrix` and `cmd/matrix-runner`, documented in `helianthus-docs-ebus/development/smoke-matrix.md`.
- It is not an `ebusgo` unit suite.
- Requirement:
  - any change that affects transport/protocol behavior must pass the full 88-case runtime matrix after the gateway pin bump
  - passive-mode behavior is additionally validated by a dedicated passive-topology smoke subset; the active matrix alone is not considered sufficient evidence for the passive pipeline

### Lab validation

- ENH/ENS/proxy passive mode
- `ebusd-tcp` degraded mode
- shared-bus traffic from VR940/myVaillant
- idle and bursty periods
- proof that B524 passive correlation works from the passive raw symbol feed, not from broadcast-only parsing
- proof includes initial passive-connect warmup behavior, not only reconnect warmup

### Hard blockers

- any wrong-key cache apply
- any direct config apply without explicit proof
- any mismatch between MCP and GraphQL semantics
- any unavailable aggregate encoded as zero
- any hidden degraded-mode state in Portal
- any unbounded label growth
- any unbounded shadow-cache growth

## Assumptions and Defaults

- Portal domain data remains GraphQL-backed.
- Portal API remains reserved for portal-native tooling and transport surfaces.
- Existing expvar metrics remain; new feature metrics are Prometheus-exported separately.
- Passive shadow cache is memory-only in v1.
- “All documented” means full catalog coverage, not full runtime activation.
- Default target behavior:
  - `state = passive direct-apply`, but feature-flagged and proof-gated
  - `config = record/invalidate`
  - `external writes = invalidate-only`
- Canonical B555 documentation path is `protocols/ebus-vaillant-b555-timer-protocol.md`.
