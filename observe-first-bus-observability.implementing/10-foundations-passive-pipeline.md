# Observe-First Execution Plan 01: Foundations and Passive Pipeline

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `415745ffb6cd371c55f10fe486de24a355e6e140c0645e20b78f783f57b6cd20`

Depends on: None. This chunk defines the source model, passive pipeline, and active/passive dedup invariants that all later chunks import.

Scope: Architectural contracts for source separation, passive tap lifecycle, reconstructor behavior, timing/fan-out rules, and deduplication.

Idempotence contract: Declarative-only. Reapplying this chunk must not introduce additional APIs, duplicate buffers, parallel passive readers, or alternate dedup models.

Falsifiability gate: A review fails this chunk if it permits two passive architectures, ambiguous frame reconstruction, duplicate counting of Helianthus traffic, or undefined degraded-state behavior.

Coverage: Summary; Sections 1-4 from the source plan.

Supplements:
- Section 4 fingerprinting uses the bounded `response_class` enum `value_bearing | ack_only | header_only | error_or_ambiguous`; Execution Plan 02 owns the full mapping rules, but these four values are the complete enum here.
- `ack_only` in this chunk means exactly `response_class=ack_only`.
- If an unmatched passive event exits dedup grace without a matching active fingerprint and its initiator equals the current local bus address, it is Helianthus-originated observability-only traffic rather than trustworthy third-party traffic and may not seed shadow admission or watch-efficiency counters.
- The closed passive capability state set is `unavailable | warming_up | available`; Execution Plan 04 owns the full state machine and transition rules.
- `compactor` here means the ShadowCache tombstone-sweep worker from Execution Plan 02. Its `1s` shutdown budget sits under this chunk's shared `5s` parent shutdown deadline.
- The Execution Plan 04 warmup window starts on the same successful passive connect as the probe window, but it governs when passive evidence becomes read-avoidance-eligible rather than capability/probe confirmation.

---

# Observe-First eBUS Watch Registry + Bus Observability

Revision: `v0.20-hardening-draft`
Date: `2026-03-09`
Status: `Draft (convergence hardening)`

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
