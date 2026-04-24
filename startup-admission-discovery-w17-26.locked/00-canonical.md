# Startup Bus Admission + Discovery Remediation

State: `locked`
Slug: `startup-admission-discovery-w17-26`
Locked on: `2026-04-23`
Canonical revision: `v1.0-locked`
Parent plan: `ebus-good-citizen-network-management.maintenance` (adopted-and-extended; ISSUE-GW-JOIN-01 extracted as narrow-scope execution per `feedback_deprecation_enrichment.md`)

## Summary

Under `cfg.ScanOnStart=true` on adapter-direct ENS @ 192.168.100.2, the
Helianthus gateway emits a scan storm: over a 60s window observed
`scan_07_04=58`, `echo_only_timeout=61`, `candidate_no_parse=12`,
`writePrefix` contamination by concurrent B524/B509 passive traffic, and
adapter heap/signal instability under sustained initiator bursts. With
`-scan=false` all counters go to zero. Root cause splits cleanly in two:

- **Admission layer**: the gateway issues active frames using a static
  configured `ScanSource` (default `0xF0`, or `0xF7` when proxy-auto-
  resolved). The source is never validated against the live bus. There is
  no address-pair authority, no companion-target occupancy check, no
  observe-first warmup. See `config.go:152-160`,
  `startup_scan.go:216 (proxyObserveFirstStartupSource)` — neither is a
  `JoinResult`.
- **Discovery layer**: `cmd/gateway/startup_scan.go:554` invokes
  `registry.Scan(..., nil)` which falls through to `scan.go:181-188
  DefaultScanTargets()` and probes `0x01..0xFD` with `07 04`.

Additionally, startup ordering in `cmd/gateway/main.go` starts the
discovery scan (line 192) BEFORE the passive transaction reconstructor
(lines 235-239). This inversion blocks Joiner wiring because Joiner has
no frame source to listen on when the scan is already firing.

This plan fixes both layers in one PR set, because active probing from an
unvalidated source is the original defect regardless of how the targets
are chosen. On join-capable direct transports (ENH, ENS, UDP-plain,
TCP-plain) the gateway now wires a `JoinBus` adapter subscribed to
`PassiveTransactionReconstructor`, runs a `protocol.NewJoiner` warmup
(default `JoinConfig`: 5s warmup, inquiry disabled, persist-last-good
enabled), and only after a successful `JoinResult` lands does it emit
Helianthus-originated active frames using `JoinResult.Initiator`.
Discovery replaces the full-range scan with a passive-first evidence
pipeline: suspects are promoted from reconstructor events and confirmed
by directed `07 04` probes against explicit targets through a new
`helianthus-ebusreg` directed scan API.

`ebusd-tcp` does NOT run `Joiner`. It continues to use the configured
`ScanSource` as admission-fallback per
`nm-participant-policy.md:38-48`, and retains the sanctioned bounded
full-range retry per `b524-semantic-root-discovery.md:L68-78`. On
non-ebusd-tcp transports the full-range retry is disabled by default
and can only be re-enabled behind an explicit operator diagnostic flag
AND only after the evidence buffer has produced at least one Vaillant
root candidate.

The plan is companion-doc-gated. A docs-ebus PR ratifies the startup
ordering contract, the degraded-mode surface, the operator override
semantics, evidence buffer retention, rejoin backoff, and the
discovery-class startup burst budget (2.0% over the 60s startup window,
distinct from the frozen NM-class 0.5% sustained / 2.0% burst band).

This plan is the narrow-scope execution of ISSUE-GW-JOIN-01 from the
superseded plan `ebus-good-citizen-network-management.maintenance`. The
parent plan is treated as an enrichment source (per
`feedback_deprecation_enrichment.md`): its normative artifacts remain
authoritative where they apply; this plan's M0 adds a single back-
reference in the parent plan's
`11-runtime-discovery-and-policy.md` under ISSUE-GW-JOIN-01 pointing to
this plan's directory. Parent plan state stays `.maintenance`.

## Scope

In scope for this plan:

- **JoinBus adapter** for ENH, ENS, UDP-plain, TCP-plain: subscribes to
  `PassiveTransactionReconstructor.Subscribe(...)` and forwards only
  allowed `PassiveClassifiedEvent.Kind`s (broadcast/master-only/i2i =
  request-only; initiator/target-with-response = request then inferred
  response; abandoned transactions and discontinuity events are NOT
  forwarded). `InquiryExistence` returns explicit
  `ErrUnsupported`/`ErrNotImplemented` sentinel when
  `InquiryEnabled=false`. Uses `protocol.NewJoiner` with default
  `JoinConfig`.
- **Startup ordering flip** on join-capable direct transports:
  INIT/INFO → reconstructor start + JoinBus subscribe → Joiner 5s warmup
  → on success, active source = `JoinResult.Initiator` and companion
  target is recorded for future use → directed probes only to promoted
  suspects → semantic polling enabled last. On Joiner fail without
  override, `probe_count=0` and active semantic polling request
  `count=0` while unsuccessful.
- **Evidence pipeline** (passive-first with bounded directed
  confirmation): promotion on ≥2 observations OR any single strong
  evidence; directed `07 04` using the new `helianthus-ebusreg` directed
  scan API; evidence buffer with `max_entries=128` LRU + baseline-
  topology protection; rejoin backoff aligned with
  `defaultRejoinBackoffBase/Max` (5s/60s, exponential, capped).
- **Degraded-mode surfaces**: log lines, expvars (including
  `startup_admission_degraded_total`, `startup_admission_state`,
  `startup_admission_warmup_events_seen`, escalation counters, cumulative
  window accumulator), and additive `bus_admission` field in the
  `ebus.v1.bus_observability` envelope with state-stability window.
- **Operator override** `StartupSource.Override` with opt-in
  `Override.Validate` sub-flag. Soft short-circuit: when set without
  `Validate`, Joiner is bypassed and active frames use the override
  immediately. When set with `Validate=true`, Joiner runs advisory-only
  in parallel, populates `JoinMetrics`, and companion-target heuristic
  warns on conflict but never blocks. Persistence is config-only; no
  auto-lift on later Joiner success.
- **Full-range retry guard**: sanctioned retry remains ebusd-tcp only;
  non-ebusd-tcp disabled by default, gated behind diagnostic flag + ≥1
  Vaillant root candidate in evidence buffer.
- **`helianthus-ebusreg` directed scan API**: new
  `ScanDirected`/`ScanOptions{Mode,Targets}` requiring explicit
  non-empty targets; filters non-target-capable addresses consistently
  with `scan.go:64-67` (initiator-capable and SYN/ESC excluded);
  existing `Scan(ctx, bus, reg, source, nil)` unchanged.
- **Doc-gate companion** in `helianthus-docs-ebus`: new "Startup
  Admission + Discovery Pipeline" section cross-linked from
  `nm-model.md`, `nm-discovery.md`, `nm-participant-policy.md`
  §Local Address-Pair Authority. Ratifies the discovery-class burst
  budget. Documents the admission-artifact JSON schema at
  `docs/schemas/admission-artifact.schema.json` in
  `helianthus-ebusgateway`.
- **Transport-gate matrix** over ENH, ENS, ebusd-tcp, UDP-plain,
  TCP-plain with explicit rows for "Join wired?" and "Static-source
  fallback?".

## Out of Scope (hard guard)

Verbatim from operator intent. Any PR touching these items fails
preflight:

- FF 00/01/02 emission
- 07 FF, 07 FE active
- NM state machine (NMInit → NMReset → NMNormal)
- Responder-lane 07 04 response, FF 03-06
- Peer NM interrogation
- ebusd-tcp path behavior changes beyond preserving static-source
  admission-fallback
- Semantic polling refactor
- Passive transaction reconstructor refactor
- Firmware / adapter-proxy changes
- HA integration changes beyond additive `bus_observability` fields

## Normative Anchors (frozen; do not re-debate)

- `helianthus-docs-ebus/architecture/nm-model.md` (L36-52, L132-218)
- `helianthus-docs-ebus/architecture/nm-discovery.md` (L39-196)
- `helianthus-docs-ebus/architecture/nm-participant-policy.md`
  §"Local Address-Pair Authority" (L18-59),
  §"Transport Capability Matrix" (L192-214),
  §"Bus-Load Policy" (L216-247),
  §"Cycle-Time Policy, Timer-Reset Event Sources" (L287-307)
- `helianthus-docs-ebus/architecture/b524-semantic-root-discovery.md`
  (L68-78)
- `helianthus-execution-plans/ebus-good-citizen-network-management.maintenance/10-evidence-decisions-and-wire-behaviour.md`
  (L88-111)
- `helianthus-execution-plans/ebus-good-citizen-network-management.maintenance/11-runtime-discovery-and-policy.md`
  (L149: ISSUE-GW-JOIN-01)
- `helianthus-docs-ebus/protocols/ebus-services/ebus-overview.md`
  (L52-62, L88-131, L114-116)
- `helianthus-ebusgo/protocol/join.go`
  (L29, L42-47, L129-199, L264-353, L401-415)
- `helianthus-ebusgateway/passive_transaction_reconstructor.go`
  (L24-31, L76-82)

## Locked Decisions (AD01 — AD23)

### AD01 — JoinBus event forwarding: abandoned transactions

Not forwarded; only broadcast/master/i2i request frames and
initiator-target request-plus-response pairs enter Joiner observation.

### AD02 — `InquiryExistence` semantics when `InquiryEnabled=false`

Return a concrete explicit not-supported sentinel consistently; nil is
forbidden.

### AD03 — Evidence promotion threshold

Promote a suspect after at least two observations or any single strong
evidence signal.

### AD04 — Joiner-fail handling for probe and semantic polling

While Joiner is unsuccessful on join-capable direct transports and no
override is configured, `probe_count=0` and active semantic polling
`count=0`; runtime remains in degraded rejoin mode.

### AD05 — Full-range retry on non-ebusd-tcp

Disabled by default; re-enabled only behind an explicit operator
diagnostic flag AND only after the evidence buffer has produced at
least one Vaillant root candidate.

### AD06 — `helianthus-ebusgo` `JoinMetrics` extension

Defer unless gateway-local evidence fusion cannot produce the required
per-address counts; if needed, add only minimal count maps to
`JoinMetrics` with no new public type and no Joiner selection-logic
changes, in a narrow follow-up plan.

### AD07 — Merge order under doc-gate

`helianthus-ebusreg` merges before `helianthus-ebusgateway`.
`helianthus-docs-ebus` may iterate in parallel but must satisfy the
active doc-gate tier before a gateway PR is mergeable.

### AD08 — `bus_admission` scope in the envelope hash

`bus_admission` is a normal field in the
`ebus.v1.bus_observability.data` body. `data_hash` is computed over the
full body including this field. No separate `admission_hash` sub-field.
Admission state transitions that survive the stability window naturally
flip `data_hash`, triggering HA-side re-emit via the existing envelope
dedup contract. `data_hash stable when unchanged` is trivially true:
the field does not change, so the hash does not change. No new HA
integration surface required. Flapping mitigation: `bus_admission`
field changes are reflected into the envelope body only after the new
state is stable for at least 30 seconds
(`admission_state_min_stability_s=30`); transient state flaps are
logged via degraded-mode counters but do not flip `bus_admission` in
the envelope nor flip `data_hash`.

### AD09 — `StartupSource.Override` semantics

(c2) soft short-circuit with opt-in validate. When Override is set and
`Validate=false`: Joiner does not run, warmup does not gate active
traffic, companion-target heuristic is vacuous (no `JoinMetrics` to
check). When Override is set and `Validate=true`: Joiner runs in
advisory-only mode in parallel, populates `JoinMetrics`, warmup does
not gate, companion-target heuristic warns on conflict but never
blocks. Both variants emit the `confidence=low` log line and set the
persistent expvar flag. Persistence is config-only (option i): no
auto-lift on later Joiner success; override remains until operator
edits config and restarts.

### AD10 — Directed-scan target validity contract

Explicit-target scan rejects nil or empty target lists and consistently
filters non-target-capable addresses, including initiator-capable
addresses and unknown symbols such as SYN or ESC, before sending probes.

### AD11 — Transport-gate granularity and admission artifact scope

The matrix must include ENH, ENS, ebusd-tcp, UDP-plain, and TCP-plain
with explicit rows for "Join wired?" and "Static-source fallback?". The
admission artifact emitted by M7 is scoped to non-ebusd-tcp adapter-
direct validation only; ebusd-tcp does not emit
`admission_path_selected` in this plan. Legacy term "startup scan pass"
is retired for adapter-direct transports; replaced by
`startup_directed_probe_phase` (see glossary).

### AD12 — Acceptance authority

The machine-readable startup admission + discovery summary artifact is
the source of truth for M7 acceptance; raw log counts are supporting
evidence only.

### AD13 — ebusd-tcp behaviour preservation

ebusd-tcp keeps configured static-source fallback and sanctioned
bounded-retry behavior; no Joiner-based admission path is introduced
there in this run.

### AD14 — Multi-PR exception in `helianthus-ebusgateway`

Operator-blessed multi-PR exception: stacked PRs M2..M7 land in
dependency order and `merge_depends_on` uses transitive closure over
the full stack, not only direct predecessors. Each PR is squash-merged
on approval before the next is rebased; docs-ebus doc-gate tiers block
gateway merges as declared in `coordination.merge_blockers`. M2a is
merge-blocking for M3 and any bugs discovered by M2a after M2 merge are
addressed by a follow-up fix on main plus downstream rebase cascade
under the declared rebase protocol. The exception does not generalise
to other cruise runs.

### AD15 — Bus-load budget class for startup discovery

Startup discovery (60s window) is burst-class not sustained-class.
Ceiling: 2.0% burst over the 60s startup window (`probe_count ≤15`
satisfies this at approximately 5 B/s). Post-startup steady-state
returns to NM-class sustained behaviour with rate limit of 1 probe per
15s. NM-class 0.5% and 2% numbers remain frozen. Discovery-class burst
band is new and ratified in M0 doc-gate.

### AD16 — Semantic polling gate under Joiner-fail

Not a semantic-poller refactor. Implementation is a signal-source gate
at the existing `semanticBarrier` closure goroutine in
`cmd/gateway/main.go` (lines 194-202). The poller's internal wait-on-
channel mechanism already exists. We change only the predicate under
which the outer goroutine closes the barrier. Strictly additive. No
carve-out from the "semantic polling refactor" out-of-scope clause is
required. Classification: main.go-only change.

### AD17 — Degraded-mode escalation threshold

Permit indefinite degraded mode (retries continue on backoff) but emit
a single-shot escalation signal to force operator visibility.
Threshold: K=5 consecutive rejoin failures OR T=5min cumulative
degraded duration, whichever fires first. Escalation latches via
`startup_admission_degraded_escalated=1` expvar and a one-shot WARN log
line. Escalation clears only after `state_min_stability_s` (30s) of
continuous active state. Runtime behaviour (backoff schedule, passive
observation, barrier-closed state) is unchanged by escalation. WARN is
emitted exactly once on unlatched→latched transition. Persistence:
cumulative accumulator is in-process only; does NOT survive restart.
WARN log `startup admission escalation accumulator zeroed
reason=process_start` is emitted on every process start.

### AD18 — Two-tier doc-gate strictness

Two-tier: (1) docs-ebus open-for-review with complete drafted sections
unblocks M2..M6 merge; (2) docs-ebus merged-to-main gates M7 integration
acceptance. Rationale: docs review latency can be multi-day; strict
"merged before any code merges" would serialize the whole six-PR gateway
stack behind a single docs PR and defeat the AD14 multi-PR exception's
value. M7 remains the final gate and enforces normative-doc-merged
discipline.

### AD19 — Parent-plan back-reference

The parent-plan back-reference edit lives in the
`helianthus-execution-plans` repo, not in docs-ebus M0. It is performed
as part of the plan-lock commit in `helianthus-execution-plans` (when
`<slug>.draft/` transitions to `<slug>.locked/`) and includes a
one-line addition under ISSUE-GW-JOIN-01 in
`ebus-good-citizen-network-management.maintenance/11-runtime-discovery-and-policy.md`:
"Extracted and superseded by `startup-admission-discovery-w17-26`; see
`helianthus-execution-plans/startup-admission-discovery-w17-26.locked/`."
Parent plan state stays `.maintenance` (no promotion). This is a
single-repo edit in `helianthus-execution-plans` and does not cross the
one-issue/one-PR-per-repo invariant.

### AD20 — Machine-checkable trivial-rebase definition

Trivial = all three: zero conflict markers AND only line-number-shift
hunks in PR-touched files AND post-rebase local CI green. Non-trivial =
any condition false; reviewer re-approval required. If operator is
unavailable >48h and a non-trivial rebase blocks merge, proceed with
second-reviewer sign-off. CRITICAL: under role-inversion, Codex-bot
thumbs-up does NOT satisfy the >48h fallback when Codex is also the
primary developer. The second reviewer must be a different AI identity
(Claude-fresh-Opus via orchestrator-glued dispatch, or whichever vendor
is non-primary at run time). Machine-checkable via required PR trailer
fields `primary_developer_ai_identity` and
`second_reviewer_ai_identity`; values must differ.

### AD21 — M2a post-merge cascade

Class-(a) harness-internal fixes land via local PR with standard
rebase. Class-(b) contract-affecting fixes land via main, trigger
mandatory re-run of M3..M7 local CI against `main@<fixed-M2a-sha>`, and
archive YAML evidence at
`docs/m2a-cascade-evidence/<date>-<fix-sha>.yaml`. Merged PRs are NEVER
reopened; all follow-ups are additive new PRs. `ci_local.sh`
classifies (a) vs (b) deterministically from the diff. Developer
cannot edit the YAML or the classification by hand. Evidence YAML
includes a deterministic SHA-256 over the classified diff plus the
resulting classification verdict (`cascade_evidence_sha`). Reviewer
regenerates and diffs.

### AD22 — Cross-field config invariant

Load-time FATAL invariant:
`state_min_stability_s * 5 ≤ continuous_threshold_s`. With
`continuous_threshold_s` frozen at 300s, this bounds
`state_min_stability_s` at ≤60s. Tunable range narrowed to [5, 60].
Violation is a FATAL config-load error and the gateway refuses to
start. Rationale: sub-stability flaps must remain visible to the
cumulative accumulator; a stability window approaching the continuous
threshold defeats both escalation paths.

### AD23 — Admission-artifact JSON schema ordering

The schema at `docs/schemas/admission-artifact.schema.json` in
`helianthus-ebusgateway` is authored as a normative contract at
plan-lock time (M0 scope in the docs-ebus PR includes the schema's
key-path listing; the file itself is committed to
`helianthus-ebusgateway` as part of `M2a_GATEWAY_OFFLINE_HARNESS` which
REFERENCES but does not author the schema semantics). M5 and M7
consume the schema without modification. Schema drift requires a plan
amendment, not a milestone-local change.

## Milestone Plan

Dependency order (merge): M0 → M1 → M2 → M2a → M3 → M4 → M5 → M6 → M7.
`merge_depends_on` uses transitive closure per AD14.
`iteration_depends_on` is narrower to permit parallel iteration.

### M0_DOC_GATE — `helianthus-docs-ebus`

**Objective.** Ratify and document the startup admission +
passive-first discovery pipeline, including direct-transport
`JoinResult` authority, startup ordering, degraded mode, operator
override, evidence buffer retention, rejoin backoff schedule, and the
discovery-class startup burst budget. Author the admission-artifact
JSON schema's normative key-path listing (schema file itself lives in
`helianthus-ebusgateway` under AD23).

**Sections to add or extend.**

- "Startup Admission + Discovery Pipeline" — new top-level section
- Degraded-mode surface docs
- Operator override docs
- Startup ordering contract (reconstructor before Joiner warmup; Joiner
  warmup before first active probe when override is unset)
- "Discovery-Class Burst Budget" subsection under
  `nm-participant-policy.md` §Bus-Load Policy
- Evidence buffer retention and rejoin backoff schedule
- Admission-artifact JSON schema key-path listing (AD23)

**Acceptance.**

- **M0-DRAFT.** Docs PR is opened in open-for-review state with the
  full `sections_to_add_or_extend` drafted in reviewable form. It
  explicitly states direct-transport `JoinResult` authority,
  reconstructor-before-warmup ordering, warmup-before-first-active-
  probe when override is unset, override as low-confidence opt-in with
  Validate=false/true branches, degraded-mode surfaces, evidence buffer
  retention and eviction, rejoin backoff as Base→2x→…→Max capped, and
  discovery-class startup burst budget distinct from NM-class
  sustained. This state unblocks M2..M6 merge.
- **M0-APPROVED.** Docs PR is merged to main. `markdown-link-check`
  (or equivalent) is run locally as part of docs-ebus preflight with
  zero broken internal cross-links. If the tool is not yet
  infrastructure in docs-ebus, a narrow follow-up issue is filed with
  a milestone target ≤90 days. Manual-audit fallback is valid for ≤1
  calendar quarter from M0-APPROVED merge date; beyond that, downstream
  merges administratively block until the link-checker lands.
  `link_checker_infrastructure_deadline: YYYY-MM-DD` is recorded in the
  M0 PR body and in `_cruise_state/plan-doc-gate.yaml`. This state is
  required before M7 merges.

**iteration_depends_on:** `[]`
**merge_depends_on:** `[]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** yes
**complexity:** 4

### M1_EBUSREG_DIRECTED_SCAN — `helianthus-ebusreg`

**Objective.** Add a directed scan API for explicit bounded targets
while preserving existing `Scan(ctx, bus, reg, source, nil)` behaviour
for ebusd-tcp sanctioned retry and external tooling.

**Acceptance.** New directed API requires explicit non-empty targets
and returns an error on nil or empty input; deduplicates and rejects or
filters initiator-capable, unknown, SYN, and ESC targets using the same
target-capability rules as current `registry/scan.go` send-time
filtering; existing `Scan(..., nil)` semantics remain unchanged. Tests
cover empty-target rejection, invalid-target filtering, and
compatibility preservation. Snapshot / golden coverage pins
`Scan(ctx, bus, reg, source, nil)` output behaviour on a fixed input
set to assert behavioural equivalence pre/post refactor. The ebusd-tcp
sanctioned bounded-retry path is explicitly exercised in the ebusreg
test suite.

**iteration_depends_on:** `[M0_DOC_GATE]`
**merge_depends_on:** `[M0_DOC_GATE]`
**transport_gate:** not-required
**doc_gate_trigger:** no
**complexity:** 3

### M2_GATEWAY_JOINBUS_ADAPTER — `helianthus-ebusgateway`

**Objective.** Implement the `JoinBus` adapter for ENH, ENS, UDP-plain,
and TCP-plain by subscribing to `PassiveTransactionReconstructor` and
feeding `protocol.NewJoiner` with default `JoinConfig`, while keeping
ebusd-tcp outside the Joiner path.

**Acceptance.**

- `JoinBus.Listen` subscribes to
  `PassiveTransactionReconstructor.Subscribe` and forwards only
  allowed events.
- `InquiryExistence` returns an explicit not-supported sentinel when
  `InquiryEnabled=false` and never nil.
- Default `JoinConfig` uses 5s warmup, inquiry disabled, persist-last-
  good enabled. ebusd-tcp does not instantiate or run Joiner.
- Transport classifier is unit-tested against all five transports in
  the capability matrix; misclassification is a test failure.
- Integration coverage proves `JoinBus.Listen` observes ≥1
  `PassiveClassifiedEvent` within the 5s warmup on a bus with
  synthesized passive traffic; a silent bus yields zero observed
  events and transitions to degraded mode with
  `reason=transport_blind`.
- Config-load validation unit-test: `state_min_stability_s=120` with
  default `continuous_threshold_s=300` triggers FATAL startup error
  (ratio 5:2 violates AD22 5:1 invariant).

**iteration_depends_on:** `[M0_DOC_GATE]`
**merge_depends_on:** `[M0_DOC_GATE]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** yes
**complexity:** 5

### M2a_GATEWAY_OFFLINE_HARNESS — `helianthus-ebusgateway`

**Objective.** Offline test harness for admission and discovery that
exercises all paths without live adapter hardware.

**Acceptance.** `./scripts/ci_local.sh` in `helianthus-ebusgateway`
exercises the admission FSM, degraded-mode transitions, evidence
promotion, override paths (both `Validate=true` and `Validate=false`),
and the transport classifier against recorded or synthesized
`PassiveTransactionReconstructor` event streams. Coverage includes:
Joiner-success path, Joiner-fail-no-free-initiator path,
transport_blind (silent bus) path, override short-circuit paths
(Validate=false / Validate=true), and the `semanticBarrier` closure
predicate. No hardware required. Override-path stubs in M2a MUST
reference M6 as the source-of-truth for override semantics; a CI check
at M2a-PR merge time verifies the stubs match M6's finalized spec.
M2a harness artifact emissions validate against the M0-frozen
`docs/schemas/admission-artifact.schema.json`; drift is a test
failure. M7 live-bus remains the final integration gate.

**iteration_depends_on:** `[M0_DOC_GATE, M2_GATEWAY_JOINBUS_ADAPTER, M6_GATEWAY_OVERRIDE_AND_FULL_RANGE_GUARD]`
**merge_depends_on:** `[M0_DOC_GATE, M2_GATEWAY_JOINBUS_ADAPTER]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** no
**complexity:** 4

### M3_GATEWAY_STARTUP_ORDER_FLIP — `helianthus-ebusgateway`

**Objective.** Flip startup ordering on join-capable direct transports
so reconstructor and admission selection complete before any non-
override Helianthus-originated active traffic or semantic polling
begins, while preserving the operator override short-circuit path.

**Acceptance.**

- Direct-transport startup path proves the order "passive reconstructor
  started" before "joiner warmup begin" before
  `startup_directed_probe_phase` when `StartupSource.Override` is unset.
- Joiner success establishes the active initiator before the first non-
  override Helianthus-originated `07 04`, `B524`, or `B509` request.
- Semantic polling gate: the existing `semanticBarrier` closure
  predicate in `cmd/gateway/main.go` (currently lines 194-202) is
  extended so the barrier only closes when BOTH
  `startupScanSignals.semanticBootstrapReady` fires AND admission state
  is `{Joiner-success with valid JoinResult}` OR `{Override-set}`. On
  admission-degraded-without-override, the barrier is never closed and
  the pre-existing internal channel wait in
  `startVaillantSemanticPolling` blocks all emissions. No changes to
  semantic poller internals. `active semantic polling request count=0`
  is asserted against emission counters while the barrier remains open.
- Warmup-before-active-frame invariant applies only when
  `StartupSource.Override` is unset. Under override, active frames are
  emitted using the override Initiator immediately after INIT/INFO; if
  `Override.Validate=true`, Joiner warmup runs in parallel and populates
  `JoinMetrics` for the companion-target conflict heuristic but does
  not gate emissions. The override path always emits the
  `startup admission override source=0xXX confidence=low` log line
  before the first active frame.

**iteration_depends_on:** `[M0, M1, M2, M2a]`
**merge_depends_on:** `[M0, M1, M2, M2a]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** yes
**complexity:** 6

### M4_GATEWAY_EVIDENCE_PIPELINE — `helianthus-ebusgateway`

**Objective.** Replace full-range startup scanning with a passive-first
evidence buffer, suspect promotion, bounded directed `07 04`
confirmation, and explicit retention, recovery, and escalation rules.

**Acceptance.**

- Evidence semantics match the frozen promotion policy (CRC-valid
  request+response = strong both; request-only = weak requester;
  passive FF 00/01 = strong originator; new-source CRC-valid cyclic =
  strong; inferred target responses = strong target). Promotion = ≥2
  obs OR any 1 strong.
- Directed confirmation uses the explicit-target ebusreg API; never
  calls `registry.Scan` with nil or empty targets on non-ebusd-tcp.
  Full-range `0x01..0xFD` probing is removed for non-ebusd-tcp.
- Evidence buffer has `max_entries=128` with LRU eviction + baseline-
  topology protection. Baseline seed is configurable; Vaillant default
  `{0x08, 0x15, 0x26, 0x04, 0xF6, 0xEC}`. Regression flood-tests cover
  both the default seed and a non-default operator-configured seed
  `{e.g., 0x03, 0x10, 0x50}`; both assert baseline-protected entries
  survive 1000 distinct fake-source CRC-valid frames while buffer
  length stays ≤128.
- Rejoin backoff `Base=5s`, `Max=60s` (aligned with ebusgo
  `defaultRejoinBackoffBase/Max`); schedule Base→2×Base→4×Base→…
  capped at Max; cap persists until rejoin success.
- Degraded-mode recovery path is testable end-to-end: simulated
  transient silence → passive traffic resumes → rejoin succeeds →
  barrier closes → polling begins.
- Degraded-mode escalation: after 5 consecutive rejoin failures OR 5
  minutes cumulative degraded time within a 15-minute rolling window
  (whichever fires first), emit one-shot WARN log
  `startup admission degraded escalated threshold=<failures|duration> value=<N>`
  and set `startup_admission_degraded_escalated=1`. Latch is cleared
  only after `state_min_stability_s=30` of continuous active state.
- `cumulative_window_algorithm: fixed_bucket_1s` — 900-slot ring
  buffer of 1-second buckets. Memory bound 3.6 KB per instance.
  Deterministic. Restart-reset per AD17.
- Integration test: flap-flap-flap-recover cycle produces exactly 1
  WARN log per latched episode.

**iteration_depends_on:** `[M0, M1, M3]`
**merge_depends_on:** `[M0, M1, M2, M2a, M3]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** yes
**complexity:** 6

### M5_GATEWAY_DEGRADED_MODE_AND_ENVELOPE — `helianthus-ebusgateway`

**Objective.** Surface admission state explicitly through logs,
expvar, and additive `bus_observability` admission metadata without
expanding HA-facing API surface.

**Expvar surfaces.**

- `startup_admission_degraded_total`
- `startup_admission_state` ∈ {0=pending, 1=active, 2=degraded}
- `startup_admission_override_active`
- `startup_admission_warmup_events_seen` — reset at each warmup
  interval start (including post-rejoin); holds final count when
  warmup ends
- `startup_admission_warmup_cycles_total` — monotonic since process
  start; increments once per Joiner warmup entered
- `startup_admission_override_bypass_total` — monotonic; increments
  per admission cycle that selected the Override path
- `startup_admission_override_conflict_detected` — retrospective
  advisory conflict under `Validate=true`
- `startup_admission_degraded_escalated` — latched escalation flag
- `startup_admission_degraded_since_ms` — unix-ms timestamp of entry
  into current envelope-visible degraded window (0 when not degraded)
- `startup_admission_consecutive_rejoin_failures` — reset on rejoin
  success
- `startup_admission_degraded_cumulative_ms` — rolling 15-min window
  sum of envelope-degraded time; in-process only, does NOT persist
  across restart

**Acceptance.**

- Join failure and blindness cases emit `startup admission degraded
  reason=<reason>` log lines.
- `bus_observability` envelope adds additive `ebus.v1.* bus_admission`
  field `{state, source, companion_target, reason}` inside the data
  body. `data_hash` is computed over the full data body with the
  unchanged algorithm and the new input field. No separate
  `admission_hash` sub-field. No new HA integration surface.
- State stability window: `bus_admission` is reflected into the
  envelope body only after the new state has remained stable for
  `state_min_stability_s` (default 30, tunable [5, 60] subject to
  AD22 invariant). Integration coverage simulates rapid
  Joiner-fail/rejoin oscillation and asserts `bus_admission` does not
  flip during the transient window.
- Dual enum enforcement: runtime FATAL on out-of-range
  `admission_path_selected` emission; CI-side JSON-schema validation
  uses `docs/schemas/admission-artifact.schema.json` (AD23-frozen at
  M0).

**iteration_depends_on:** `[M0, M3, M4]`
**merge_depends_on:** `[M0, M1, M2, M2a, M3, M4]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** yes
**complexity:** 4

### M6_GATEWAY_OVERRIDE_AND_FULL_RANGE_GUARD — `helianthus-ebusgateway`

**Objective.** Finalize operator override wiring and persistence
semantics while hard-guarding full-range retry so non-ebusd-tcp can
only re-enable it diagnostically after real evidence exists.

**Acceptance.**

- `StartupSource.Override` and `StartupSource.Override.Validate` are
  wired exactly per `configuration_surfaces` with config-only
  persistence and no auto-lift on later Joiner success.
- The low-confidence override log line and persistent expvar flag are
  emitted on both `Validate=false` and `Validate=true` branches.
- Under `Validate=true`, retrospective conflict detection at the end
  of the 5s advisory warmup sets
  `startup_admission_override_conflict_detected=1` expvar and emits a
  single structured WARN log. Detection does not alter or
  retroactively invalidate active frames emitted during warmup.
- ebusd-tcp preserves configured static-source fallback semantics
  outside the admission artifact scope.
- Non-ebusd-tcp full-range retry is disabled by default and can only
  be re-enabled behind an explicit diagnostic flag AND only after the
  evidence buffer has produced ≥1 Vaillant root candidate.
- Regression coverage fails any non-ebusd-tcp startup path that
  attempts `registry.Scan` with nil or empty targets.

**iteration_depends_on:** `[M0, M4, M5]`
**merge_depends_on:** `[M0, M1, M2, M2a, M3, M4, M5]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** yes
**complexity:** 5

### M7_GATEWAY_INTEGRATION_ACCEPTANCE — `helianthus-ebusgateway`

**Objective.** Emit the startup admission + discovery machine-readable
summary artifact and validate the full frozen acceptance set on the
live ENS adapter-direct topology.

**Acceptance.**

- End-of-window summary artifact contains the frozen admission and
  discovery schema for non-ebusd-tcp adapter-direct scope only,
  including `transport_kind` and `admission_path_selected`. Live-bus
  artifact asserts `transport_kind` and `admission_path_selected` are
  consistent with the transport capability matrix and
  `admission_path_selected` is one of
  `{join, override, degraded_transport_blind, degraded_no_events}`;
  any other value or unset is failure.
- `startup_order_criteria`, `admission_criteria`, and
  `discovery_criteria` all pass on `ScanOnStart=true` over the 60s
  live-bus window.
- `startup_burst_pct ≤ 2.0` over `startup_window_s=60`.
- `post_startup_sustained_rate_probes_per_15s ≤ 1` in steady-state,
  enforced by the rate limiter as an invariant.
- `probe_count ≤ promoted_suspects_without_identity` AND
  `probe_count ≤ 15`; any value above 15 is failure.
- `echo_only_timeout ≤ 2` per pass; fail above 5.
- `candidate_no_parse = 0`; fail above 1.
- Each baseline address is either in the registry within 60s or has
  zero CRC-valid evidence; nonzero evidence with absence is failure.
- Local CI is green in `helianthus-ebusreg` and
  `helianthus-ebusgateway`.
- Transport-gate evidence attached as a YAML file at
  `docs/transport-gate-evidence/<ISO8601-date>-<transport>.yaml` in
  `helianthus-ebusgateway` with required fields: `transport`,
  `adapter_hw_id`, `admission_path_selected`, `warmup_events_observed`,
  `degraded_escalations`, `passive_event_count_5min`,
  `hash_of_gateway_binary_sha256`, `operator_signoff_gh_handle`,
  `timestamp_utc`, `deployment_seed_exercised_in_ci`, `ci_tested_seeds`.
  M7 PR description must link to this file; any missing or empty
  field is acceptance failure.
- Live-bus runtime evidence: ≥5-minute runtime window on the real
  adapter-direct transport (ens-tcp @ 192.168.100.2 baseline)
  demonstrates (a) `startup_admission_warmup_events_seen ≥ 1` during
  warmup, (b) at least one non-degraded admission envelope emission
  with `admission_path_selected=join`, (c)
  `startup_admission_degraded_escalated=0` throughout.
  `live_bus_evidence_scope: steady-state-warmup-only`; the 5-min
  window validates warmup passive-event plumbing and non-degraded
  baseline but does not validate the 15-min rolling-window cumulative
  logic (that is covered by M2a offline harness synthesis).
- CI-side JSON-schema validation uses
  `docs/schemas/admission-artifact.schema.json` (AD23-frozen at M0).

**iteration_depends_on:** `[M0, M1, M2a, M3, M4, M5, M6]`
**merge_depends_on:** `[M0, M1, M2, M2a, M3, M4, M5, M6]`
**transport_gate:** REQUIRED
**doc_gate_trigger:** no
**complexity:** 6

## Coordination and PR Strategy

Parallel iteration is permitted: M0, M1, and the gateway stack M2..M7
may iterate concurrently using draft-stage contracts. Merge
serialization is explicit in `merge_depends_on`. M2a begins once M2
draft exists and completes before the final gateway integration gate.

Merge order: `helianthus-ebusreg` → `helianthus-ebusgateway`. Merge
blockers are two-tier per AD18:

- `helianthus-docs-ebus` companion PR must be in open-for-review state
  with a reviewable draft of the complete `sections_to_add_or_extend`
  before any `helianthus-ebusgateway` PR is mergeable.
- `helianthus-docs-ebus` companion PR must be fully merged into main
  before `M7_GATEWAY_INTEGRATION_ACCEPTANCE` is mergeable.
- `helianthus-ebusreg` directed-scan support must merge before any
  `helianthus-ebusgateway` PR from M3 onward.
- Each `helianthus-ebusgateway` PR requires green local CI before
  merge.

PR strategy per AD14:

- `helianthus-ebusreg`: one-pr-one-issue
- `helianthus-docs-ebus`: one-pr-one-issue
- `helianthus-ebusgateway`: operator-blessed-multi-pr-exception — M2,
  M2a, M3, M4, M5, M6, M7 land as stacked PRs in dependency order;
  each squash-merged on approval before the next is rebased; no PR
  merges until predecessors are approved AND docs-ebus doc-gate
  satisfies the active tier AND local CI is green. The exception does
  not generalise.

### Rebase protocol

- **On predecessor merge:** the next PR in the stack MUST be rebased
  onto main before review resumes.
- **Post-rebase CI:** rebase MUST trigger a fresh local CI run. Prior
  CI-green status does not carry across a rebase.
- **Trivial rebase (AD20).** All three machine-checkable conditions
  MUST be true: (1) `git rebase` completes with zero conflict markers,
  (2) post-rebase `git diff HEAD@{pre-rebase} -- <PR-touched-files>`
  shows only line-number-shift hunks, (3) post-rebase local CI is
  green. Any FALSE = non-trivial; reviewer re-approval required.
- **Operator unavailability >48h (AD20).** Proceed with second-
  reviewer sign-off recorded in the PR description. Under role-
  inversion, Codex-bot thumbs-up does NOT satisfy the fallback when
  Codex is also the primary developer. PR description MUST include
  trailer fields `primary_developer_ai_identity` and
  `second_reviewer_ai_identity`; values must differ.
- **iteration_vs_merge_gap.** When a milestone's `merge_depends_on`
  exceeds its `iteration_depends_on` (e.g., M4 iterates on M3 but
  merges on M2a+M3), the later-merging PR MUST rebase against each
  additional merge-blocker's merge commit and re-run full local CI
  before merge. The PR description MUST record the SHA of each merge-
  blocker at rebase time in a section
  `## Merge-blocker SHAs at rebase`.
- **m2a_post_merge_cascade.** Post-merge M2a fixes classified by
  `ci_local.sh` as (a) harness-internal (local PR, standard rebase) or
  (b) contract-affecting. Class-(b) triggers mandatory re-run of
  M3..M7 local CI against `main@<fixed-M2a-sha>`; evidence YAML is
  authored by `ci_local.sh` alone with a deterministic SHA over the
  classified diff plus the classification verdict, written to
  `docs/m2a-cascade-evidence/<date>-<fix-sha>.yaml`. Developer cannot
  hand-author or hand-edit the YAML. Reviewer regenerates and diffs.

### `helianthus-ebusgo` is deferred

AD06 defers any ebusgo changes. If gateway-local evidence fusion
proves it cannot produce the required per-address counts without
upstream Joiner metrics, a narrow follow-up plan will add count maps
to `JoinMetrics`. This plan does NOT create a milestone or PR against
`helianthus-ebusgo`.

## Configuration Surfaces

See the Appendix YAML for machine-readable form. Summary:

- **`startup_source_override`** (AD09). Field
  `StartupSource.Override`, opt-in default-off; config-only
  persistence; `Validate` sub-flag default false; (c2) soft short-
  circuit semantics with retrospective conflict detection under
  `Validate=true`.
- **`evidence_buffer`** (AD03, AD05, M4). `max_entries=128` (tunable
  [32, 1024]); `eviction_policy: lru-with-baseline-protection`;
  baseline seed configurable at `startup_admission.baseline_topology_seed`;
  Vaillant default `[0x08, 0x15, 0x26, 0x04, 0xF6, 0xEC]`; validation
  rejects addresses outside eBUS slave range [0x03, 0xFE] excluding
  broadcast 0xFE and SYN 0xAA; FATAL at config-load on invalid entries.
- **`rejoin_backoff`** (M4). `base_seconds=5` (tunable [1, 30]),
  `max_seconds=60` (tunable [30, 300]); schedule Base→2×Base→…→Max
  capped.
- **`admission_envelope`** (AD08, AD22). `state_min_stability_s=30`
  (tunable [5, 60]); load-time invariant
  `state_min_stability_s × 5 ≤ continuous_threshold_s`; FATAL on
  violation.
- **`admission_escalation`** (AD17). `continuous_threshold_s=300`
  (frozen), `cumulative_threshold_s=300` (frozen),
  `cumulative_window_s=900` (frozen),
  `cumulative_window_algorithm: fixed_bucket_1s` (frozen, 900-slot
  ring buffer, 3.6 KB memory, deterministic),
  `cumulative_persists_across_restart: false` with startup WARN.

## Falsifiable Acceptance

See the Appendix YAML for the complete machine-readable schema.

- **artifact_schema.admission** fields: `state, source,
  companion_target, warmup_duration_s, reason_if_degraded,
  transport_kind`; plus `admission_path_selected` enum ∈ `{join,
  override, degraded_transport_blind, degraded_no_events}`. Scope:
  non-ebusd-tcp adapter-direct only.
- **artifact_schema.discovery** fields: `wire_bytes, window_s,
  startup_burst_pct, post_startup_sustained_rate_probes_per_15s,
  probe_count, promoted_suspects_without_identity,
  per_baseline_address_evidence_counts`.
- **startup_order_criteria**: reconstructor-before-warmup-before-
  directed-probe-phase when override unset; ≥1 warmup event on active
  bus OR zero events on silent bus with `reason=transport_blind`;
  `InquiryExistence` never called with `InquiryEnabled=false`; sentinel
  return; barrier closure predicate respects admission state; barrier
  stays open + polling=0 on admission-degraded-without-override.
- **admission_criteria**: JoinResult exists before first non-override
  active request; all non-override frames use `JoinResult.Initiator`;
  override path logs `confidence=low` and sets
  `admission_path_selected=override`; Joiner-fail-without-override →
  `probe_count=0` AND polling=0; artifact scope excludes ebusd-tcp;
  enum enforcement.
- **discovery_criteria**: `promoted ≤ 15`; `probe_count ≤ promoted AND
  ≤ 15` (hard ceiling); `startup_burst_pct ≤ 2.0` over 60s;
  `post_startup_sustained_rate ≤ 1/15s` in steady-state;
  `echo_only_timeout ≤ 2` (fail >5); `candidate_no_parse = 0` (fail
  >1); per-baseline-address registry-presence OR zero-evidence;
  zero FF 00; zero `registry.Scan(nil/empty)` on non-ebusd-tcp; local
  CI green.

## Bus-Load Budget

Wire capacity at 2400 baud, 10 bits/byte: 240 bytes/s.

Classes (AD15):

- **NM-class sustained** 0.5% (frozen)
- **NM-class burst** 2.0% (frozen)
- **Discovery-class startup burst** 2.0% over the 60s startup window
  (NEW; ratified in M0 doc-gate)
- **Discovery-class post-startup** 1 probe per 15s steady-state
  (enforced by rate limiter as an invariant)

Full `07 04` transaction on the wire: 18–22 bytes. `probe_count ≤ 15`
satisfies the 2.0% startup-burst ceiling at ~5 B/s (2.08% rounds to
2.0% per operator ruling).

## Transport Matrix

| Transport | Join wired | Static-source fallback |
|---|---|---|
| ENH | yes | only via `StartupSource.Override` (opt-in) |
| ENS | yes | only via `StartupSource.Override` (opt-in) |
| ebusd-tcp | no | yes (default configured fallback) |
| UDP-plain | yes | only via `StartupSource.Override` (opt-in) |
| TCP-plain | yes | only via `StartupSource.Override` (opt-in) |

## Doc-Gate Sections

In `helianthus-docs-ebus` companion PR (M0):

- Startup Admission + Discovery Pipeline (new top-level)
- Degraded-mode surface docs
- Operator override docs
- Startup ordering contract
- Discovery-Class Burst Budget subsection under
  `nm-participant-policy.md` §Bus-Load Policy
- Evidence buffer retention and rejoin backoff schedule
- Admission-artifact JSON schema key-path listing (AD23)

## Glossary (normative)

- **`startup_directed_probe_phase`**: the post-warmup interval during
  which directed probes (`07 04` `InquiryExistence`) are sent against
  promoted-suspect addresses using `JoinResult.Initiator` as SRC,
  rate-limited per
  `bus_load_budget.classes.discovery_class_startup_burst_pct_limit`.
  This phase has ZERO intersection with the legacy full-range
  `0x01..0xFD` scan (which is removed for adapter-direct transports
  per AD11).

## Commentary (non-normative editorial guidance; not gate material)

- **`probe_count_typical`**: on the observed baseline Vaillant
  topology, steady-state `probe_count` is typically ≤ 8 in a 60s
  window. Guidance only. Acceptance gates are `probe_count ≤
  promoted` AND `probe_count ≤ 15` (hard).

## References

### Normative sources

- `helianthus-docs-ebus/architecture/nm-model.md#L36-52,L132-218`
- `helianthus-docs-ebus/architecture/nm-discovery.md#L39-196`
- `helianthus-docs-ebus/architecture/nm-participant-policy.md`
  (§Local Address-Pair Authority, §Transport Capability Matrix,
  §Bus-Load Policy, §Cycle-Time Policy)
- `helianthus-docs-ebus/architecture/b524-semantic-root-discovery.md#L68-78`
- `helianthus-execution-plans/ebus-good-citizen-network-management.maintenance/10-evidence-decisions-and-wire-behaviour.md#L88-111`
- `helianthus-execution-plans/ebus-good-citizen-network-management.maintenance/11-runtime-discovery-and-policy.md#L149`
- `helianthus-docs-ebus/protocols/ebus-services/ebus-overview.md#L52-62,L88-131,L114-116`
- `helianthus-ebusgo/protocol/join.go#L29,L42-47,L129-199,L264-353,L401-415`
- `helianthus-ebusgateway/passive_transaction_reconstructor.go#L24-31,L76-82`
- `helianthus-ebusgateway/docs/transport-gate-evidence/` (directory
  convention for M7 acceptance evidence)
- `helianthus-ebusgateway/docs/schemas/admission-artifact.schema.json`
  (AD23-frozen contract)

### Parent plan

- Slug: `ebus-good-citizen-network-management`
- State: `.maintenance`
- Relationship: extracts ISSUE-GW-JOIN-01 as narrow-scope execution;
  parent treated as enrichment source per
  `feedback_deprecation_enrichment.md`. Plan-lock commit adds one-line
  back-reference in parent's
  `11-runtime-discovery-and-policy.md` under ISSUE-GW-JOIN-01.

### Adversarial round history

5 rounds, fully converged on R5. Zero blockers. Trajectory:

| Round | Attacks | Blockers | Majors | Minors | Concessions | Escalations |
|---|---|---|---|---|---|---|
| R1 | 12 | 2 | 7 | 3 | 3 | 5 (all operator-resolved) |
| R2 | 13 | 1 | 7 | 5 | 4 | 4 (all operator-resolved) |
| R3 | 15 | 0 | 7 | 8 | 12 | 4 (operator-lean-resolved) |
| R4 | 12 | 0 | 5 | 7 | 7 | 4 (operator-lean-resolved) |
| R5 | 0 | 0 | 0 | 0 | 10 | 0 (`converged: true`) |

Primary planner: Codex (gpt-5.4 high reasoning). Adversary: fresh
Claude Opus via orchestrator-glued dispatch per role-inversion.
