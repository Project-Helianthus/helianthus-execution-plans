# Observe-First Execution Plan 03: Watch, Memory, and Metrics

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `415745ffb6cd371c55f10fe486de24a355e6e140c0645e20b78f783f57b6cd20`

Depends on: Execution Plans 01-04. This chunk mirrors imported defaults only
when needed for isolated review.

Scope: Watch catalog shape, runtime activation, memory budgeting, metrics,
query surfaces, and bounded observability state.

Idempotence contract: Reapplying this chunk must not create duplicate keys,
parallel budget models, or unbounded shadow state.

Falsifiability gate: A review fails this chunk if activation rules, memory
budgets, or query surfaces remain ambiguous, unbounded, or unfalsifiable.

Coverage: Sections 9-11B from the source plan.

Imports:
- Plan 02 owns breaker defaults and B516 transitions. Plan 04 owns passive warmup semantics.
- Residual steady-state budget below the `<512` target is fixed as: watch-efficiency `<=80`, shadow/breaker/tombstone `<=40`, dedup/warmup/pipeline `<=24`, feature-flag/rollback/budget `<=16`.
- `active_read_saved_seconds{family,freshness_profile}` uses the last `32` successful request-complete samples in the same bucket, emits after `4` samples, and drops samples older than `30m`.
- `rollback_events_total` counts only adapter-scoped effective-runtime observe-first epoch changes, and `shadow_notification_overflow_total` applies to observability/debug/live-summary subscribers.

---

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
