# 13 — Configuration Surfaces, Falsifiable Acceptance, Bus-Load Budget, Transport Matrix, Glossary

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `c3b2fb00c75c8ebc02de12ba6c7526b216f714f2be4a38d77890e4776c5f4fcf`

Depends on: [10-scope-and-problem.md](./10-scope-and-problem.md),
[11-milestones-and-coordination.md](./11-milestones-and-coordination.md),
and [12-decision-matrix.md](./12-decision-matrix.md). Several
acceptance criteria and configuration surfaces trace back to specific
ADs; several artifact schema fields are tied to specific milestones.

Scope: All machine-readable configuration surfaces
(`startup_source_override`, `evidence_buffer`, `rejoin_backoff`,
`admission_envelope`, `admission_escalation`); the full falsifiable
acceptance schema (artifact_schema.admission + discovery,
startup_order_criteria, admission_criteria, discovery_criteria);
bus_load_budget numeric classes; the 5-row transport matrix; the
normative glossary (defining `startup_directed_probe_phase`); the
non-normative commentary (`probe_count_typical`).

Idempotence contract: Declarative-only. Reapplying this chunk must
not loosen any tunability bound, remove any acceptance criterion,
alter the transport matrix rows, rewrite a normative glossary
definition into non-normative prose, or promote commentary into
acceptance. Frozen (non-tunable) numbers remain frozen.

Falsifiability gate: Review fails this chunk if it (a) softens any
numeric acceptance threshold, (b) widens a tunable range beyond its
`[min, max]`, (c) removes any expvar from the M5 surface list, (d)
weakens the AD22 load-time invariant, (e) promotes a commentary item
into a gate, or (f) diverges the transport matrix from the 5-row
{ENH, ENS, ebusd-tcp, UDP-plain, TCP-plain} × {Join wired, Static-
source fallback} structure.

Coverage: Configuration Surfaces; Falsifiable Acceptance (artifact
schema, startup_order_criteria, admission_criteria,
discovery_criteria); Bus-Load Budget numeric classes; Transport
Matrix; Glossary (normative); Commentary (non-normative).

## Configuration Surfaces

### `startup_source_override` (AD09)

- `field`: `StartupSource.Override`
- `type`: optional uint8 or structured
- `default`: unset
- `operator_tunable`: yes
- `runtime_reloadable`: no
- `persistence`: config-only persistent (option i); no auto-lift;
  reset only by operator editing config and restart
- `validate_subflag`: `StartupSource.Override.Validate`
- `validate_default`: false

Behaviour branches:

- **Unset**: Joiner warmup gates all Helianthus-originated active
  traffic; warmup-before-active-frame invariant in force.
- **Set + `Validate=false`**: Joiner does NOT run; warmup-before-
  active-frame invariant bypassed on this path only;
  companion-target heuristic does NOT run (vacuous; no
  `JoinMetrics`); log
  `startup admission override source=0xXX confidence=low` before
  first active frame; expvar
  `startup_admission_override_active=1`.
- **Set + `Validate=true`**: Joiner runs in advisory-only mode in
  parallel, populates `JoinMetrics`; warmup does NOT gate active
  traffic (override Initiator used immediately); companion-target
  conflict heuristic runs against override when `JoinMetrics`
  populated, warns on conflict, never blocks; retrospective
  conflict detection at t≈5s warmup end sets
  `startup_admission_override_conflict_detected=1` and emits
  `startup admission override conflict_detected=1
  override_source=0xXX joiner_preferred=0xYY` WARN log; active
  traffic emitted during t=0..5s using override is NOT
  retroactively invalidated; operator-action-on-conflict is
  out-of-scope for this plan (advisory only).

### `evidence_buffer` (M4, AD05)

- `max_entries`: 128
- `max_entries_operator_tunable`: yes
- `max_entries_min`: 32
- `max_entries_max`: 1024
- `eviction_policy`: `lru-with-baseline-protection`
- `runtime_reloadable`: no

`baseline_topology_seed`:
- `source`: gateway YAML config under
  `startup_admission.baseline_topology_seed`
- `vaillant_default`: `[0x08, 0x15, 0x26, 0x04, 0xF6, 0xEC]`
- `validation`: each address must be in eBUS slave range
  `[0x03, 0xFE]` excluding broadcast `0xFE` and SYN `0xAA`
- `validation_failure_behavior`: reject at config-load with
  explicit error; gateway refuses to start
- `operator_tunable`: yes
- `runtime_reloadable`: no

M4 regression flood-tests cover both the default seed and a
non-default operator-configured seed; both assert baseline-protected
entries survive 1000 distinct fake-source CRC-valid frames while
buffer length stays ≤ `max_entries`.

### `rejoin_backoff` (M4)

- `base_seconds`: 5 (aligned with ebusgo `defaultRejoinBackoffBase`)
- `base_seconds_operator_tunable`: yes
- `base_seconds_min`: 1
- `base_seconds_max`: 30
- `max_seconds`: 60 (aligned with ebusgo
  `defaultRejoinBackoffMax`)
- `max_seconds_operator_tunable`: yes
- `max_seconds_min`: 30
- `max_seconds_max`: 300
- `runtime_reloadable`: no
- `schedule`: `Base, 2*Base, 4*Base, ... capped at Max`; cap
  persists until rejoin success.

### `admission_envelope` (AD08, AD22)

- `state_min_stability_s`: 30
- `state_min_stability_s_operator_tunable`: yes
- `state_min_stability_s_min`: 5
- `state_min_stability_s_max`: 60 (narrowed from 120 to preserve
  5:1 ratio with frozen `continuous_threshold_s=300`)
- `runtime_reloadable`: no
- `load_time_invariant`:
  `state_min_stability_s × 5 ≤ admission_escalation.continuous_threshold_s`;
  violation is FATAL config-load error; gateway refuses to start.

### `admission_escalation` (AD17)

All three thresholds are FROZEN (not operator-tunable):

- `continuous_threshold_s`: 300 (5 min)
- `cumulative_threshold_s`: 300 (5 min within rolling window)
- `cumulative_window_s`: 900 (15 min rolling)
- `cumulative_window_algorithm`: `fixed_bucket_1s`
- `cumulative_persists_across_restart`: false

`cumulative_window_algorithm` description:
> The 900s rolling window is implemented as a ring buffer of 900
> fixed 1-second buckets. Each bucket stores the count of degraded-
> state millisecond-samples observed in that second (0..1000). Sum
> over the full 900-bucket buffer yields `cumulative_ms`. Bucket
> rotation occurs on the 1-second tick. Memory: 900 × 4 bytes =
> 3.6 KB per admission instance. Bounded-memory, deterministic,
> restart-reset.

On process start, gateway emits WARN log
`startup admission escalation accumulator zeroed reason=process_start`
and the accumulator is set to 0.

### M5 expvar surfaces (complete list)

- `startup_admission_degraded_total` — monotonic count of degraded
  transitions
- `startup_admission_state` ∈ `{0=pending, 1=active, 2=degraded}`
- `startup_admission_override_active` — 1 when override is
  configured
- `startup_admission_warmup_events_seen` — reset at each warmup
  interval start (including post-rejoin); holds final count when
  warmup ends
- `startup_admission_warmup_cycles_total` — monotonic since process
  start; increments once per Joiner warmup entered. Stays 0 under
  Override-set + Validate=false (Joiner bypassed)
- `startup_admission_override_bypass_total` — monotonic; increments
  per admission cycle that selected the Override path (regardless
  of Validate)
- `startup_admission_override_conflict_detected` — retrospective
  advisory conflict under Validate=true
- `startup_admission_degraded_escalated` — latched escalation flag
  (0 or 1)
- `startup_admission_degraded_since_ms` — unix-ms timestamp of entry
  into CURRENT envelope-visible degraded state; resets only when
  `state_min_stability_s` confirms recovery to active; 0 when not
  degraded
- `startup_admission_consecutive_rejoin_failures` — reset on rejoin
  success
- `startup_admission_degraded_cumulative_ms` — rolling 15-min
  accumulator via fixed-bucket-1s ring buffer; in-process only;
  does NOT persist across restart

## Falsifiable Acceptance

### Artifact schema

Scope: **non-ebusd-tcp adapter-direct only**. ebusd-tcp does not
emit this artifact.

`admission` fields:
- `state`
- `source`
- `companion_target`
- `warmup_duration_s`
- `reason_if_degraded`
- `transport_kind`
- `admission_path_selected` ∈ enum
  `{join, override, degraded_transport_blind, degraded_no_events}`

`discovery` fields:
- `wire_bytes`
- `window_s`
- `startup_burst_pct`
- `post_startup_sustained_rate_probes_per_15s`
- `probe_count`
- `promoted_suspects_without_identity`
- `per_baseline_address_evidence_counts`

### `startup_order_criteria`

1. "passive reconstructor started" occurs before "joiner warmup
   begin" when `StartupSource.Override` is unset.
2. "joiner warmup begin" occurs before `startup_directed_probe_phase`
   when `StartupSource.Override` is unset.
3. `JoinBus.Listen` receives at least one `PassiveClassifiedEvent`
   during the 5s warmup on a live or synthesized active bus; a
   silent bus yields zero warmup events and degraded
   `reason=transport_blind`.
4. `JoinBus.InquiryExistence` is never called when
   `InquiryEnabled=false`.
5. When `InquiryEnabled=false`, `InquiryExistence` returns an
   explicit not-supported sentinel.
6. Semantic polling barrier closes only when
   `startupScanSignals.semanticBootstrapReady` has fired AND
   admission state is `Joiner-success with valid JoinResult` OR
   `Override-set`.
7. On admission-degraded-without-override, the semantic barrier
   remains open and active semantic polling request `count=0`.

### `admission_criteria`

1. A successful `JoinResult` with valid initiator and companion
   target exists before the first non-override Helianthus-
   originated `07 04`, `B524`, or `B509` active request.
2. All non-override active frames use `JoinResult.Initiator`.
3. If `StartupSource.Override` is set, the
   `startup admission override source=0xXX confidence=low` log
   line is emitted before the first active frame and
   `admission_path_selected=override`.
4. If Joiner fails without override, then `probe_count=0` and
   active semantic polling request `count=0`.
5. Admission artifact scope excludes ebusd-tcp and records
   `transport_kind` plus `admission_path_selected`, where
   `admission_path_selected` is one of
   `{join, override, degraded_transport_blind, degraded_no_events}`;
   any other value or unset is failure.

### `discovery_criteria`

1. `promoted_suspects_without_identity ≤ 15`.
2. `probe_count ≤ promoted_suspects_without_identity` AND
   `probe_count ≤ 15` (hard ceilings).
3. `startup_burst_pct ≤ 2.0` over `startup_window_s=60`.
4. `post_startup_sustained_rate_probes_per_15s ≤ 1` in steady-
   state, enforced by the rate limiter as an invariant.
5. `echo_only_timeout ≤ 2` per pass; fail if > 5.
6. `candidate_no_parse = 0`; fail if > 1.
7. Each baseline address is either present in the registry within
   60s OR had zero CRC-valid evidence frames during the window;
   nonzero evidence with absence is failure.
8. Zero `FF 00` emitted by this remediation work.
9. Zero `registry.Scan(nil/empty)` on non-ebusd-tcp, enforced by
   regression test.
10. Local CI (`./scripts/ci_local.sh`) is green on
    `helianthus-ebusreg` and `helianthus-ebusgateway`.

## Bus-Load Budget

Wire capacity at 2400 baud, 10 bits/byte: **240 bytes/s**.

Classes:

- `nm_class_sustained_pct_limit`: 0.5 (frozen, NM-class)
- `nm_class_burst_pct_limit`: 2.0 (frozen, NM-class)
- `discovery_class_startup_burst_pct_limit`: 2.0 over 60s startup
  window (NEW, discovery-class)
- `discovery_class_post_startup_rate`: "1 probe per 15s steady-
  state" (enforced as invariant, not as a percentage)

Full `07 04` transaction wire bytes: 18-22. `probe_count ≤ 15`
satisfies the 2.0% startup-burst ceiling at ~5 B/s.

## Transport Matrix

| Transport | Join wired | Static-source fallback |
|---|---|---|
| ENH | yes | only via `StartupSource.Override` (opt-in) |
| ENS | yes | only via `StartupSource.Override` (opt-in) |
| ebusd-tcp | no | yes (default configured fallback) |
| UDP-plain | yes | only via `StartupSource.Override` (opt-in) |
| TCP-plain | yes | only via `StartupSource.Override` (opt-in) |

## Glossary (normative; bindings to falsifiable_acceptance terms)

- **`startup_directed_probe_phase`**: the post-warmup interval
  during which directed probes (`07 04` `InquiryExistence`) are
  sent against promoted-suspect addresses using
  `JoinResult.Initiator` as SRC, rate-limited per
  `bus_load_budget.classes.discovery_class_startup_burst_pct_limit`.
  This phase has ZERO intersection with the legacy full-range
  `0x01..0xFD` scan (which is removed for adapter-direct transports
  per AD11).

## Commentary (non-normative editorial guidance; not gate material)

- **`probe_count_typical`**: on the observed baseline Vaillant
  topology (`0x08` BAI00, `0x15` BASV2, `0x26` VR_71,
  `0x04`/`0xF6` NETX3, `0xEC` SOL00), steady-state `probe_count`
  is typically ≤ 8 in a 60s window. This is guidance, not an
  acceptance gate. Acceptance gates are
  `probe_count ≤ promoted_suspects_without_identity` AND
  `probe_count ≤ 15` (hard).

## Link-Checker Deadline Mechanism (AD-absorbed from R3)

Format: `link_checker_infrastructure_deadline: YYYY-MM-DD` in
ISO-8601, recorded in the M0 PR body AND in
`_cruise_state/plan-doc-gate.yaml` pointer file.

Enforcement:

- A step in `./scripts/ci_local.sh` of both `helianthus-ebusgateway`
  and `helianthus-ebusreg` reads the deadline via `gh api
  repos/Project-Helianthus/helianthus-docs-ebus/pulls/<M0-PR-number>`
  from the committed pointer file.
- If today's date > deadline AND link-checker infrastructure is
  still absent, `ci_local.sh` FAILS with explicit error
  `link-checker infrastructure deadline expired; plan re-scoping
  required`.
- Merges are administratively blocked until infrastructure lands
  or the plan is explicitly re-scoped by operator.
