# Observe-First Execution Plan 07: M6-M9 Consumers, Proof, Tinyebus, and Final Validation

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `415745ffb6cd371c55f10fe486de24a355e6e140c0645e20b78f783f57b6cd20`

Depends on: Execution Plans 01-06 for `M6`, `M7`, and `M9`. `M8` is the explicit parallel-track carve-out and may start after the shared metric contract freezes at `ISSUE-GW-03` + `ISSUE-DOC-05`.

Scope: M6 semantic publish and Portal, M7 proof and default-flip, M8 tinyebus, M9 HA consumer rollout, and the final validation/adversarial gates.

Idempotence contract: Reapplying this chunk must converge on one proof gate, one rollout decision, and one final validation envelope. It must not duplicate consumer contracts or proof surfaces.

Falsifiability gate: A review fails this chunk if proof claims are unfalsifiable, consumer rollouts outrun API stability, or final validation gates can be passed vacuously.

Coverage: Milestones M6-M9, validation gates, and assumptions/defaults from the source plan.

Sequencing supplement:
- `M6 -> M7 -> M9` remain sequential.
- `M8` is parallel by exception only; it does not wait for `M7`.
- Locked Decisions from the canonical plan override any issue text drift in this chunk.

---

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
