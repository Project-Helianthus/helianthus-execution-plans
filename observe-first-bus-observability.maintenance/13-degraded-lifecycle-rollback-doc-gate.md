# Observe-First Execution Plan 04: Degraded Modes, Lifecycle Semantics, Rollback, and Doc-Gate

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `956d6ad2957f09906a4eee3f3be733059c0a24d34af4d56ebf61c0553aaeac86`

Depends on: Execution Plans 01-03.

Scope: Transport degradation, passive outage/reconnect behavior, cold start, snapshot semantics, rollback semantics, and the mega doc-gate.

Idempotence contract: Reapplying this chunk must converge on one capability state machine, one rollback contract, and one documentation gate. It must not create alternative lifecycle semantics.

Falsifiability gate: A review fails this chunk if capability states are ambiguous, rollback can leave stale trust in place, or doc-gate requirements can be bypassed.

Coverage: Sections 12-14 and Mega Doc-Gate from the source plan.

---

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
