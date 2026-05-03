# 11 — Milestones M0..M7 and Coordination

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `c3b2fb00c75c8ebc02de12ba6c7526b216f714f2be4a38d77890e4776c5f4fcf`

Depends on: [10-scope-and-problem.md](./10-scope-and-problem.md).
Scope, out-of-scope guards, and normative anchors are prerequisite
context for the milestone definitions and coordination rules.

Scope: Milestone definitions M0_DOC_GATE, M1_EBUSREG_DIRECTED_SCAN,
M2_GATEWAY_JOINBUS_ADAPTER, M2a_GATEWAY_OFFLINE_HARNESS,
M3_GATEWAY_STARTUP_ORDER_FLIP, M4_GATEWAY_EVIDENCE_PIPELINE,
M5_GATEWAY_DEGRADED_MODE_AND_ENVELOPE,
M6_GATEWAY_OVERRIDE_AND_FULL_RANGE_GUARD,
M7_GATEWAY_INTEGRATION_ACCEPTANCE with objective, acceptance, and
dependency specifications; plus coordination.parallel_iteration,
merge_order, merge_blockers (two-tier doc-gate), pr_strategy (AD14
multi-PR exception), rebase_protocol (trivial definition,
operator_unavailability, iteration_vs_merge_gap,
m2a_post_merge_cascade), and deferred_repos (helianthus-ebusgo per
AD06).

Idempotence contract: Declarative-only. Reapplying this chunk must
not alter the locked milestone ID set, remove any acceptance
criterion, weaken any merge blocker, collapse the transitive closure
of `merge_depends_on`, or generalise the one-PR-per-repo exception to
repos other than `helianthus-ebusgateway`. Rebase protocol
machine-checkable definitions remain binding.

Falsifiability gate: Review fails this chunk if it (a) removes or
renames a milestone, (b) weakens any acceptance criterion below the
frozen level, (c) permits a gateway PR merge without satisfying the
active doc-gate tier, (d) allows merged PRs to be reopened for M2a
cascade fixes, (e) drops the different-AI-identity requirement in the
>48h operator-unavailable fallback, or (f) permits a rebase to carry
CI-green status without re-run.

Coverage: Milestone Plan (all 9 milestones including M2a);
Coordination and PR Strategy; Rebase protocol sub-clauses; Deferred
repos.

## Milestone Dependency Order (merge)

`M0 → M1 → M2 → M2a → M3 → M4 → M5 → M6 → M7`

`merge_depends_on` is transitive closure per AD14.
`iteration_depends_on` is narrower to permit parallel iteration.

## M0_DOC_GATE — `helianthus-docs-ebus`

Objective: Ratify and document the startup admission + passive-first
discovery pipeline including direct-transport `JoinResult` authority,
startup ordering, degraded mode, operator override, evidence buffer
retention, rejoin backoff, and the discovery-class startup burst
budget. Author the admission-artifact JSON schema's normative
key-path listing (schema file itself lives in
`helianthus-ebusgateway` under AD23).

Acceptance has two tiers:

- **M0-DRAFT** — docs PR open-for-review with full drafted sections;
  unblocks M2..M6 merge per AD18.
- **M0-APPROVED** — docs PR merged to main; `markdown-link-check`
  (or equivalent) run locally with zero broken internal cross-links;
  `link_checker_infrastructure_deadline: YYYY-MM-DD` recorded in the
  M0 PR body and `_cruise_state/plan-doc-gate.yaml` with ≤90-day
  manual-audit fallback; beyond deadline, downstream merges block
  administratively.

iteration_depends_on: `[]`. merge_depends_on: `[]`.
Transport-gate: REQUIRED. Doc-gate trigger: yes. Complexity: 4.

## M1_EBUSREG_DIRECTED_SCAN — `helianthus-ebusreg`

Objective: Add directed scan API for explicit bounded targets while
preserving existing `Scan(ctx, bus, reg, source, nil)` for ebusd-tcp
sanctioned retry and external tooling.

Acceptance: new directed API rejects nil/empty target lists; filters
non-target-capable addresses (initiator-capable, unknown, SYN, ESC)
consistent with `registry/scan.go:64-67`; existing `Scan(..., nil)`
semantics unchanged; tests cover empty-target rejection, invalid-
target filtering, compatibility preservation. Snapshot/golden pins
`Scan(ctx, bus, reg, source, nil)` output on a fixed input set. The
ebusd-tcp sanctioned bounded-retry path is explicitly exercised in
the ebusreg test suite.

iteration_depends_on: `[M0_DOC_GATE]`.
merge_depends_on: `[M0_DOC_GATE]`.
Transport-gate: not-required. Doc-gate trigger: no. Complexity: 3.

## M2_GATEWAY_JOINBUS_ADAPTER — `helianthus-ebusgateway`

Objective: Implement `JoinBus` adapter for ENH, ENS, UDP-plain, and
TCP-plain by subscribing to `PassiveTransactionReconstructor` and
feeding `protocol.NewJoiner` with default `JoinConfig`, keeping
ebusd-tcp outside the Joiner path.

Acceptance:

- `JoinBus.Listen` subscribes to
  `PassiveTransactionReconstructor.Subscribe` and forwards only
  allowed events (broadcast/master-only/i2i = request-only;
  initiator/target-with-response = request + inferred response);
  abandoned transactions and discontinuities are NOT forwarded.
- `InquiryExistence` returns explicit not-supported sentinel when
  `InquiryEnabled=false`; never nil.
- Default `JoinConfig` = 5s warmup, inquiry disabled, persist-last-
  good enabled. ebusd-tcp does NOT instantiate or run Joiner.
- Transport classifier unit-tested against all 5 transports
  {ENH, ENS, ebusd-tcp, UDP-plain, TCP-plain}; any misclassification
  (join-capable routed to static fallback, or ebusd-tcp routed to
  Joiner) is a test failure.
- Integration test: `JoinBus.Listen` observes ≥1
  `PassiveClassifiedEvent` within 5s warmup on a bus with synthesized
  passive traffic; silent-bus yields 0 warmup events and transitions
  to degraded mode with `reason=transport_blind`.
- Config-load validation unit-test: `state_min_stability_s=120` with
  default `continuous_threshold_s=300` triggers FATAL startup error
  (AD22 5:1 invariant violation).

iteration_depends_on: `[M0_DOC_GATE]`.
merge_depends_on: `[M0_DOC_GATE]`.
Transport-gate: REQUIRED. Doc-gate trigger: yes. Complexity: 5.

## M2a_GATEWAY_OFFLINE_HARNESS — `helianthus-ebusgateway`

Objective: Offline test harness for admission + discovery that
exercises all paths without live adapter hardware.

Acceptance: `./scripts/ci_local.sh` in `helianthus-ebusgateway`
exercises the admission FSM, degraded-mode transitions, evidence
promotion, override paths (`Validate=true` and `Validate=false`), and
the transport classifier against recorded or synthesized
`PassiveTransactionReconstructor` event streams. Coverage includes
Joiner-success, Joiner-fail-no-free-initiator, transport_blind,
override short-circuit (both Validate branches), and the
`semanticBarrier` closure predicate. Override-path stubs reference M6
as source-of-truth; CI check at M2a-PR merge verifies stubs match
M6's finalized spec. Harness artifact emissions validate against the
M0-frozen `docs/schemas/admission-artifact.schema.json`; drift is a
test failure. M7 live-bus remains the final integration gate.

iteration_depends_on: `[M0, M2]` (adjusted per AD24; see 12-decision-matrix.md for cycle-break rationale). Override-spec alignment with M6 is enforced at merge time via the `iteration_vs_merge_gap` rule in `coordination.pr_strategy.rebase_protocol`; M2a's merge_depends_on is unchanged.
merge_depends_on: `[M0, M2]`.
Transport-gate: REQUIRED. Doc-gate trigger: no. Complexity: 4.

## M3_GATEWAY_STARTUP_ORDER_FLIP — `helianthus-ebusgateway`

Objective: Flip startup ordering on join-capable direct transports so
reconstructor + admission selection complete before any non-override
Helianthus-originated active traffic or semantic polling.

Acceptance:

- When `StartupSource.Override` is unset: order "passive reconstructor
  started" before "joiner warmup begin" before
  `startup_directed_probe_phase` (glossary).
- Joiner success establishes active initiator before first non-
  override `07 04`/B524/B509.
- Semantic polling gate: extend the existing `semanticBarrier`
  closure predicate in `cmd/gateway/main.go` (lines 194-202) so it
  closes only when BOTH `startupScanSignals.semanticBootstrapReady`
  fires AND admission is `{Joiner-success with valid JoinResult}` or
  `{Override-set}`. On admission-degraded-without-override, the
  barrier is never closed and the existing internal wait in
  `startVaillantSemanticPolling` blocks all emissions. No semantic
  poller internals change. `active semantic polling request count=0`
  is asserted against emission counters while the barrier remains
  open.
- Warmup-before-active-frame invariant applies only when override is
  unset. Under override, active frames are emitted using override
  Initiator immediately after INIT/INFO; Validate=true runs Joiner in
  parallel advisory-only and populates JoinMetrics, but does not
  gate emissions. Override path always emits
  `startup admission override source=0xXX confidence=low` log before
  first active frame.

iteration_depends_on: `[M0, M1, M2, M2a]`.
merge_depends_on: `[M0, M1, M2, M2a]`.
Transport-gate: REQUIRED. Doc-gate trigger: yes. Complexity: 6.

## M4_GATEWAY_EVIDENCE_PIPELINE — `helianthus-ebusgateway`

Objective: Replace full-range startup scanning with a passive-first
evidence buffer, suspect promotion, bounded directed `07 04`
confirmation, and explicit retention/recovery/escalation rules.

Acceptance:

- Evidence semantics match the frozen promotion policy.
- Directed confirmation uses the explicit-target ebusreg API; never
  calls `registry.Scan` with nil/empty on non-ebusd-tcp. Full-range
  `0x01..0xFD` probing removed on non-ebusd-tcp.
- Evidence buffer: `max_entries=128`, LRU + baseline-topology
  protection. Baseline seed configurable at
  `startup_admission.baseline_topology_seed`; Vaillant default
  `[0x08, 0x15, 0x26, 0x04, 0xF6, 0xEC]`. Two flood-test variants
  (default seed and non-default operator seed): 1000 distinct fake-
  source CRC-valid frames; baseline-protected entries survive;
  buffer length stays ≤128.
- Rejoin backoff `Base=5s`, `Max=60s` (aligned with ebusgo
  `defaultRejoinBackoffBase/Max`); exponential schedule capped at
  Max; cap persists until rejoin success.
- Degraded-mode recovery path testable end-to-end.
- Degraded-mode escalation: after 5 consecutive rejoin failures OR
  5 min cumulative degraded time within a 15-min rolling window
  (whichever fires first), emit one-shot WARN log and set
  `startup_admission_degraded_escalated=1`. Latch clears only after
  `state_min_stability_s=30` of continuous active state.
- `cumulative_window_algorithm: fixed_bucket_1s` — 900-slot ring
  buffer of 1-second buckets. Memory bound 3.6 KB per instance.
  Deterministic. Restart-reset per AD17.
- Integration test: flap-flap-flap-recover produces exactly 1 WARN
  per latched episode.

iteration_depends_on: `[M0, M1, M3]`.
merge_depends_on: `[M0, M1, M2, M2a, M3]`.
Transport-gate: REQUIRED. Doc-gate trigger: yes. Complexity: 6.

## M5_GATEWAY_DEGRADED_MODE_AND_ENVELOPE — `helianthus-ebusgateway`

Objective: Surface admission state via logs, expvar, and additive
`bus_observability` admission metadata without expanding HA-facing
API surface.

Acceptance:

- Degraded-reason log lines; full expvar set (see 13-
  configuration-and-acceptance.md for the complete list).
- `bus_observability` envelope adds additive `ebus.v1.*
  bus_admission` field `{state, source, companion_target, reason}`
  inside the data body. `data_hash` unchanged algorithm; new input
  field. No separate `admission_hash`. No new HA surface.
- State stability window: `bus_admission` reflected to envelope only
  after new state stable for `state_min_stability_s` (30 default;
  tunable [5, 60] subject to AD22). Integration test: rapid Joiner-
  fail/rejoin oscillation asserts envelope does not flip during
  transient window.
- Dual enum enforcement (AD23): runtime FATAL on out-of-range
  `admission_path_selected`; CI-side JSON-schema validation against
  `docs/schemas/admission-artifact.schema.json`.
- `startup_admission_degraded_cumulative_ms` is in-process only,
  does NOT persist across restart. WARN on process start:
  `startup admission escalation accumulator zeroed reason=process_start`.

iteration_depends_on: `[M0, M3, M4]`.
merge_depends_on: `[M0, M1, M2, M2a, M3, M4]`.
Transport-gate: REQUIRED. Doc-gate trigger: yes. Complexity: 4.

## M6_GATEWAY_OVERRIDE_AND_FULL_RANGE_GUARD — `helianthus-ebusgateway`

Objective: Finalize operator override wiring + persistence
semantics; hard-guard full-range retry on non-ebusd-tcp.

Acceptance:

- `StartupSource.Override` + `.Validate` wired per
  `configuration_surfaces` with config-only persistence and no auto-
  lift on later Joiner success.
- Low-confidence override log line + persistent expvar flag on both
  branches.
- Under `Validate=true`, retrospective conflict detection at end of
  5s advisory warmup sets
  `startup_admission_override_conflict_detected=1` expvar and emits
  one structured WARN; detection does not retroactively invalidate
  active frames emitted during warmup.
- ebusd-tcp preserves static-source fallback outside artifact scope.
- Non-ebusd-tcp full-range retry disabled by default; re-enabled
  only behind diagnostic flag AND after ≥1 Vaillant root candidate
  in evidence buffer.
- Regression coverage fails any non-ebusd-tcp startup path that
  calls `registry.Scan` with nil/empty targets.

iteration_depends_on: `[M0, M4, M5]`.
merge_depends_on: `[M0, M1, M2, M2a, M3, M4, M5]`.
Transport-gate: REQUIRED. Doc-gate trigger: yes. Complexity: 5.

## M7_GATEWAY_INTEGRATION_ACCEPTANCE — `helianthus-ebusgateway`

Objective: Emit the startup admission + discovery machine-readable
summary artifact and validate the full frozen acceptance set on the
live ENS adapter-direct topology.

Acceptance:

- End-of-window summary artifact: admission schema (`state, source,
  companion_target, warmup_duration_s, reason_if_degraded,
  transport_kind`, plus `admission_path_selected` enum ∈
  `{join, override, degraded_transport_blind, degraded_no_events}`;
  any other value or unset = failure). Scope: non-ebusd-tcp adapter-
  direct only.
- Discovery schema: `wire_bytes, window_s, startup_burst_pct,
  post_startup_sustained_rate_probes_per_15s, probe_count,
  promoted_suspects_without_identity,
  per_baseline_address_evidence_counts`.
- All startup_order_criteria, admission_criteria, and
  discovery_criteria (see 13-*) pass on ScanOnStart=true over 60s
  live-bus window.
- `startup_burst_pct ≤ 2.0` over `startup_window_s=60`.
- `post_startup_sustained_rate_probes_per_15s ≤ 1` in steady-state.
- `probe_count ≤ promoted_suspects_without_identity` AND
  `probe_count ≤ 15` (hard; any value >15 = failure).
- `echo_only_timeout ≤ 2` per pass (fail >5).
- `candidate_no_parse = 0` (fail >1).
- Each baseline address: in registry within 60s OR zero CRC-valid
  evidence; nonzero evidence with absence = failure.
- Local CI green on `helianthus-ebusreg` and `helianthus-ebusgateway`.
- Transport-gate evidence YAML at
  `docs/transport-gate-evidence/<ISO8601-date>-<transport>.yaml` in
  `helianthus-ebusgateway`; required fields: `transport`,
  `adapter_hw_id`, `admission_path_selected`,
  `warmup_events_observed`, `degraded_escalations`,
  `passive_event_count_5min`, `hash_of_gateway_binary_sha256`,
  `operator_signoff_gh_handle`, `timestamp_utc`,
  `deployment_seed_exercised_in_ci`, `ci_tested_seeds`. M7 PR
  description must link to this file; any missing/empty field =
  acceptance failure.
- Live-bus runtime evidence: ≥5-minute window on real adapter-
  direct transport (ens-tcp @ 192.168.100.2 baseline) demonstrates
  (a) `startup_admission_warmup_events_seen ≥ 1` during warmup,
  (b) ≥1 non-degraded admission envelope with
  `admission_path_selected=join`,
  (c) `startup_admission_degraded_escalated=0` throughout.
  `live_bus_evidence_scope: steady-state-warmup-only`.
- CI-side JSON-schema validation via
  `docs/schemas/admission-artifact.schema.json` (AD23-frozen at M0).

iteration_depends_on: `[M0, M1, M2a, M3, M4, M5, M6]`.
merge_depends_on: `[M0, M1, M2, M2a, M3, M4, M5, M6]`.
Transport-gate: REQUIRED. Doc-gate trigger: no. Complexity: 6.

## Coordination

### Parallel iteration

M0, M1, and the gateway stack M2..M7 may iterate concurrently using
draft-stage contracts; merge serialization remains explicit in
`merge_depends_on`. M2a begins once M2 draft exists and completes
before the final gateway integration gate.

### Merge order

`helianthus-ebusreg` → `helianthus-ebusgateway`.

### Merge blockers (two-tier per AD18)

- `helianthus-docs-ebus` companion PR in open-for-review state with
  complete drafted sections BEFORE any `helianthus-ebusgateway` PR
  merges.
- `helianthus-docs-ebus` companion PR FULLY MERGED into main BEFORE
  `M7_GATEWAY_INTEGRATION_ACCEPTANCE` merges.
- `helianthus-ebusreg` directed-scan support merged BEFORE any
  gateway PR from M3 onward.
- Each gateway PR requires green local CI before merge.

### PR strategy (AD14)

- `helianthus-ebusreg`: one-pr-one-issue
- `helianthus-docs-ebus`: one-pr-one-issue
- `helianthus-ebusgateway`: operator-blessed-multi-pr-exception —
  M2, M2a, M3, M4, M5, M6, M7 land as stacked PRs in dependency
  order. Each squash-merged on approval before next rebased. No PR
  merges until predecessors approved AND docs-ebus tier satisfied
  AND local CI green. Exception does not generalise.

### Rebase protocol

- **On predecessor merge**: next PR in stack MUST be rebased onto
  main before review resumes.
- **Post-rebase CI**: rebase MUST trigger fresh local CI run. Prior
  green does not carry.
- **Trivial rebase (AD20)**: machine-checkable = (1) zero conflict
  markers, (2) only line-shift hunks in PR-touched files, (3)
  post-rebase local CI green. Any FALSE = non-trivial; reviewer
  re-approval required.
- **Operator unavailability >48h (AD20)**: proceed with second-
  reviewer sign-off; under role-inversion, the second reviewer
  AI identity MUST differ from the primary developer AI identity.
  PR description MUST include trailer fields
  `primary_developer_ai_identity` and `second_reviewer_ai_identity`;
  values must differ. Codex-bot thumbs-up does NOT satisfy when Codex
  is the primary developer.
- **iteration_vs_merge_gap**: when `merge_depends_on` exceeds
  `iteration_depends_on`, the later-merging PR MUST rebase against
  each additional merge-blocker's merge commit and re-run full local
  CI before merge. PR description records blocker SHAs under
  `## Merge-blocker SHAs at rebase`.
- **m2a_post_merge_cascade (AD21)**: `ci_local.sh` classifies (a)
  harness-internal (local PR, standard rebase) or (b) contract-
  affecting (follow-up PR on main; mandatory re-run of M3..M7 local
  CI at `main@<fixed-M2a-sha>`). Evidence YAML at
  `docs/m2a-cascade-evidence/<date>-<fix-sha>.yaml` authored by
  `ci_local.sh` alone with deterministic SHA over classified diff +
  classification verdict. Developer cannot hand-author/edit.
  Reviewer regenerates and diffs. Merged PRs are NEVER reopened.

### Deferred repos

`helianthus-ebusgo`: no milestones. AD06 defers any ebusgo changes.
If gateway-local evidence fusion proves it cannot produce required
per-address counts without upstream Joiner metrics, a narrow
follow-up plan adds count maps to `JoinMetrics`. This plan creates
no milestone or PR against `helianthus-ebusgo`.
