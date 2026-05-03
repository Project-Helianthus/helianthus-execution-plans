# Observe-First Execution Plan 06: M2-M5 APIs, Shadowing, and Scheduler Rollout

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `956d6ad2957f09906a4eee3f3be733059c0a24d34af4d56ebf61c0553aaeac86`

Depends on: Execution Plans 01-05.

Scope: M2 MCP, M3 GraphQL, M4 watch/shadow/flags, and M5 observe-first scheduler integration.

Idempotence contract: Reapplying this chunk must converge on one API surface per layer, one shared key model, and one flag-governed shadow/scheduler rollout.

Falsifiability gate: A review fails this chunk if MCP and GraphQL drift, feature flags are under-specified, or scheduler rollout can violate the upstream architecture chunks.

Coverage: Milestones M2-M5 from the source plan.

Sequencing supplement:
- Milestones in this chunk are sequentially gated `M2 -> M3 -> M4 -> M5`.
- Locked Decisions from the canonical plan override any issue text drift in this chunk.

---

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
