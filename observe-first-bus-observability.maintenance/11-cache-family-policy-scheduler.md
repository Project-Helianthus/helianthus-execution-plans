# Observe-First Execution Plan 02: Cache Rules, Family Policy, and Scheduler Integration

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `415745ffb6cd371c55f10fe486de24a355e6e140c0645e20b78f783f57b6cd20`

Depends on: Execution Plan 01 for pipeline/dedup invariants. This chunk also mirrors the fixed descriptor/freshness constants from Execution Plan 03 and the passive-capability constants from Execution Plan 04 for isolated review.

Scope: Cache update rules, policy vocabulary, family-specific behavior, invalidate-only semantics, and ShadowCache/SemanticReadScheduler interaction.

Idempotence contract: Reapplying this chunk must converge on one cache-precedence model, one invalidation model, and one scheduler read path. It must not create parallel freshness rules.

Falsifiability gate: A review fails this chunk if stale results can overwrite newer invalidations, if family policies conflict, or if scheduler/shadow coordination is under-specified.

Coverage: Sections 5-8B from the source plan.

Supplements:
- Imported descriptor subset used by this chunk: canonical key, semantic class, freshness profile, decoder id, correlation policy, direct-apply policy, resolved `freshness_ttl`, and runtime activation state. Execution Plan 03 owns the full static catalog schema, but these fields are the complete subset this chunk may rely on.
- `freshness_profile` here is exactly `state_fast | state_slow | config | discovery | debug`.
- Minimum `ShadowEntry` contract for this chunk: canonical key, source, confidence tier, state (`present | invalidated | tombstone`), stored value/payload, observation timestamp, last-write generation, invalidation generation/epoch, invalidation reason, pin bit, and eligibility/expiry metadata.
- `family=other` has `direct_apply_policy=never` in v1.
- `energyMergeStore` is a pre-existing gateway path, separate from generic `ShadowCache` in storage, memory budget, and locking. The B516 carve-out in this chunk does not imply shared data structures.
- The ShadowCache compactor `1s` budget is a child budget inside Execution Plan 01's shared `5s` shutdown parent.
- Imported passive capability states for B516 predicates are exactly `unavailable | warming_up | available`; Execution Plan 04 owns their transition triggers.
- Imported runtime normalization summary from Execution Plan 04: observe-first master-off disables both direct-apply flags; state-direct-off disables config-direct and clamps `external_write_policy=record_only`; `passive_config_direct_apply + record_only` normalizes to `record_and_invalidate`.

---

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
