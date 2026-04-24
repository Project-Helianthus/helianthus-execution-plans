# 12 — Locked Decisions AD01..AD23

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `9e4b32d2b2b382ed9bad7f4098c63488c7b0e9da7fbec2a22ea10a76124eaee7`

Depends on: [10-scope-and-problem.md](./10-scope-and-problem.md) and
[11-milestones-and-coordination.md](./11-milestones-and-coordination.md).
Scope, normative anchors, and milestone structure must be understood
before the locked decisions make sense; several ADs reference
specific milestones and configuration surfaces.

Scope: All 23 locked decisions from the adversarial planning cycle
(R1..R5). AD01..AD07 were frozen at R1 or absorbed from operator
intent. AD08..AD13 resolved R1 escalations E1..E5. AD14..AD18 resolved
R2 escalations E6..E9. AD17 appended in R3/R4 with escalation +
cumulative + latch semantics. AD19 relocated in R3. AD20..AD23 added
in R3/R4/R5.

Idempotence contract: Declarative-only. Reapplying this chunk must
not rewrite any AD resolution, remove any AD entry, renumber
existing AD IDs, or downgrade any decision from resolution to open
question. Additions are only permitted via plan amendment with
explicit operator authorization.

Falsifiability gate: Review fails this chunk if it (a) introduces an
AD without a concrete resolution, (b) softens any resolution into
guidance rather than a gate, (c) reopens a frozen resolution, or (d)
permits an implementation choice that contradicts any AD.

Coverage: AD01..AD23 with full resolutions; cross-references to
milestones, configuration surfaces, and acceptance criteria where
applicable.

## AD01 — JoinBus event forwarding: abandoned transactions

Not forwarded; only broadcast/master/i2i request frames and
initiator-target request-plus-response pairs enter Joiner observation.
(Analog of `nm-participant-policy.md` L287-307 timer-reset rule;
decode faults and discontinuity events do not produce evidence.)

## AD02 — `InquiryExistence` semantics when `InquiryEnabled=false`

Return a concrete explicit not-supported sentinel consistently; nil is
forbidden. Returning nil implies a successful `07 FE` emission and
would silently corrupt Joiner's inquiry-followup accounting if
`InquiryEnabled` is ever flipped on.

## AD03 — Evidence promotion threshold

Promote a suspect after at least two observations or any single
strong evidence signal. Evidence classification:

- CRC-valid `07 04` request+response pair = strong for BOTH
- Request-only `07 04` = weak for requester; does not confirm target
- Passive `FF 00`/`FF 01` broadcasts = strong for originator
- New-source CRC-valid sender-attributed cyclic traffic = strong
- Inferred target responses from reconstructed initiator/target
  transactions (target inferred per ebus-overview.md:114-116) =
  strong for target

## AD04 — Joiner-fail handling: probe and semantic polling

While Joiner is unsuccessful on join-capable direct transports and no
override is configured, `probe_count=0` and active semantic polling
request `count=0`; runtime remains in degraded rejoin mode.

## AD05 — Full-range retry on non-ebusd-tcp

Disabled by default. Re-enabled only behind an explicit operator
diagnostic flag AND only after the evidence buffer has produced at
least one Vaillant root candidate.

## AD06 — `helianthus-ebusgo` `JoinMetrics` extension

Defer unless gateway-local evidence fusion cannot produce required
per-address counts. If needed, add only minimal count maps to
`JoinMetrics` with no new public type and no Joiner selection-logic
changes, in a narrow follow-up plan. This plan creates no milestone
or PR against `helianthus-ebusgo`.

## AD07 — Merge order under doc-gate

`helianthus-ebusreg` merges before `helianthus-ebusgateway`.
`helianthus-docs-ebus` may iterate in parallel but must satisfy the
active doc-gate tier before any gateway PR is mergeable (per AD18).

## AD08 — `bus_admission` field scope in envelope hash

`bus_admission` is a normal field in the
`ebus.v1.bus_observability.data` body. `data_hash` is computed over
the full body including this field. No separate `admission_hash`
sub-field. Admission state transitions that survive the stability
window naturally flip `data_hash`, triggering HA-side re-emit via
the existing envelope dedup contract. `data_hash stable when
unchanged` is trivially true: the field does not change, so the hash
does not change. No new HA integration surface.

Flapping mitigation: `bus_admission` field changes are reflected into
the envelope body only after the new state is stable for at least
`state_min_stability_s` (default 30s, tunable [5, 60] subject to
AD22 invariant); transient flaps are logged via degraded-mode
counters but do not flip `bus_admission` in the envelope nor flip
`data_hash`.

## AD09 — `StartupSource.Override` semantics (c2 + i)

(c2) soft short-circuit with opt-in validate, plus (i) config-only
persistence.

- **Unset**: Joiner warmup gates all Helianthus-originated active
  traffic; warmup-before-active-frame invariant in force.
- **Set + `Validate=false`**: Joiner does NOT run; warmup does NOT
  gate; companion-target heuristic is vacuous (no `JoinMetrics`);
  log `startup admission override source=0xXX confidence=low` before
  first active frame; expvar
  `startup_admission_override_active=1`.
- **Set + `Validate=true`**: Joiner runs advisory-only in parallel,
  populates `JoinMetrics`; warmup does NOT gate; companion-target
  heuristic runs against override address, warns on conflict but
  never blocks; retrospective conflict detection at t≈5s warmup end
  sets `startup_admission_override_conflict_detected=1` and emits
  one structured WARN; active traffic emitted during t=0..5s is NOT
  retroactively invalidated.
- **Persistence**: config-only (option i); no auto-lift on later
  Joiner success. Override remains until operator edits config and
  restarts.

## AD10 — Directed-scan target validity contract

Explicit-target scan rejects nil or empty target lists and
consistently filters non-target-capable addresses, including
initiator-capable addresses and unknown symbols such as SYN or ESC,
before sending probes.

## AD11 — Transport-gate granularity and admission artifact scope

The matrix must include ENH, ENS, ebusd-tcp, UDP-plain, and TCP-plain
with explicit rows for "Join wired?" and "Static-source fallback?".

The admission artifact emitted by M7 is scoped to non-ebusd-tcp
adapter-direct validation only; ebusd-tcp does not emit
`admission_path_selected` in this plan.

Legacy term "startup scan pass" is retired for adapter-direct
transports; replaced by `startup_directed_probe_phase` (see
glossary). The directed-probe phase has zero intersection with the
legacy full-range `0x01..0xFD` scan (removed for adapter-direct per
M4/M6).

## AD12 — Acceptance authority for runtime validation

The machine-readable startup admission + discovery summary artifact
is the source of truth for M7 acceptance; raw log counts are
supporting evidence only.

## AD13 — ebusd-tcp behaviour preservation boundary

ebusd-tcp keeps configured static-source fallback and sanctioned
bounded-retry behaviour; no Joiner-based admission path is
introduced there in this run.

## AD14 — One-issue-per-repo invariant vs six ebusgateway PRs

Operator-blessed multi-PR exception: stacked PRs M2..M7 land in
dependency order and `merge_depends_on` uses transitive closure over
the full stack, not only direct predecessors. Each PR is squash-
merged on approval before the next is rebased. Docs-ebus doc-gate
tiers block gateway merges per AD18. M2a is merge-blocking for M3
and any bugs discovered by M2a after M2 merge are addressed by a
follow-up fix on main plus downstream rebase cascade under AD21.
Rationale persisted in `coordination.pr_strategy_rationale`. The
exception does not generalise to other cruise runs.

## AD15 — Bus-load budget class for startup discovery

Startup discovery (60s window) is burst-class, not sustained-class.
Ceiling: 2.0% burst over the 60s startup window (`probe_count ≤ 15`
satisfies this at approximately 5 B/s; 2.08% rounds to 2.0% per
operator ruling). Post-startup steady-state returns to NM-class
sustained behaviour with rate limit of 1 probe per 15s. NM-class
0.5% and 2% numbers remain frozen. Discovery-class burst band is
new and ratified in M0 doc-gate.

## AD16 — Semantic polling gate: not a poller refactor

The gate is a signal-source change at the existing `semanticBarrier`
closure goroutine in `cmd/gateway/main.go` (lines 194-202). The
poller's internal wait-on-channel mechanism already exists. We
change only the predicate under which the outer goroutine closes
the barrier. Strictly additive. No carve-out from the "semantic
polling refactor" out-of-scope clause is required. Classification:
main.go-only change.

## AD17 — Degraded-mode escalation threshold

Permit indefinite degraded mode (retries continue on backoff) but
emit a single-shot escalation signal to force operator visibility.

- **Threshold**: K=5 consecutive rejoin failures OR T=5min
  cumulative degraded duration within a 15-min rolling window;
  whichever fires first.
- **Signal**: `startup_admission_degraded_escalated=1` expvar +
  one-shot WARN log
  `startup admission degraded escalated threshold=<failures|duration> value=<N>`.
- **Latch clear**: escalation clears only after
  `state_min_stability_s` (30s) of continuous active state. WARN is
  emitted exactly once on unlatched→latched transition; no WARN on
  latched→unlatched. Integration test in M4: flap-flap-flap-recover
  cycle produces exactly 1 WARN per latched episode.
- **Runtime behaviour unchanged**: backoff schedule, passive
  observation, barrier-closed state continue regardless of latch.
- **Persistence**: cumulative accumulator is in-process only; does
  NOT survive restart. WARN log
  `startup admission escalation accumulator zeroed reason=process_start`
  is emitted on every process start.

## AD18 — Two-tier doc-gate strictness

- **Tier 1 (M2..M6)**: docs-ebus companion PR in open-for-review
  state with complete drafted `sections_to_add_or_extend` unblocks
  M2..M6 merge.
- **Tier 2 (M7)**: docs-ebus companion PR fully merged to main
  unblocks `M7_GATEWAY_INTEGRATION_ACCEPTANCE` merge.

Rationale: docs review latency can be multi-day; a strict "merged
before any code merges" gate would serialize the full six-PR
gateway stack behind a single docs PR and defeat the AD14 multi-PR
exception's value. M7 remains the final gate and enforces
normative-doc-merged discipline.

## AD19 — Parent-plan back-reference

The parent-plan back-reference edit lives in the
`helianthus-execution-plans` repo, not in docs-ebus M0. It is
performed as part of the plan-lock commit in
`helianthus-execution-plans` (when `<slug>.draft/` transitions to
`<slug>.locked/`) and includes a one-line addition under
ISSUE-GW-JOIN-01 in
`ebus-good-citizen-network-management.maintenance/11-runtime-discovery-and-policy.md`:

> "Extracted and superseded by `startup-admission-discovery-w17-26`;
> see `helianthus-execution-plans/startup-admission-discovery-w17-26.locked/`."

Parent plan state stays `.maintenance`. This is a single-repo edit in
`helianthus-execution-plans` and does not cross the one-issue/one-
PR-per-repo invariant (cruise-plan's lock-commit is the mechanism,
not a new milestone). M0 (docs-ebus) is unaffected.

## AD20 — Trivial-rebase definition + operator unavailability

Machine-checkable trivial-rebase: all three must be TRUE:

1. `git rebase` completes with zero conflict markers in any file.
2. Post-rebase `git diff HEAD@{pre-rebase} -- <PR-touched-files>`
   shows only line-number-shift hunks (no semantic changes in the
   PR's own files).
3. Post-rebase local CI (`./scripts/ci_local.sh`) is green.

All three TRUE → trivial; prior reviewer approval retained. Any
FALSE → non-trivial; reviewer re-approval required.

**Operator unavailability >48h**: proceed with second-reviewer
sign-off recorded in the PR description. Under role-inversion,
the second reviewer AI identity MUST differ from the primary
developer AI identity. Machine-checkable: the PR description's
reviewer-sign-off trailer MUST include
`primary_developer_ai_identity: <name>` and
`second_reviewer_ai_identity: <name>`; values must differ.
Identical-AI-identity double-stamps are rejected at pre-merge
check. Codex-bot thumbs-up does NOT satisfy the fallback when Codex
is also the primary developer.

## AD21 — M2a post-merge cascade classification + CI re-run

Class-(a) **harness-internal** — no downstream test-contract impact;
fixed by a local PR to `helianthus-ebusgateway` without cascade.
Standard rebase_protocol applies.

Class-(b) **contract-affecting** — changes assertions, signatures,
or behavioural expectations used by M3..M7 tests. Require:

1. A new follow-up PR in `helianthus-ebusgateway` that lands the fix
   on main (not by reopening merged PRs).
2. Mandatory re-run of M3..M7 local CI against
   `main@<fixed-M2a-sha>`.
3. Evidence YAML at
   `docs/m2a-cascade-evidence/<ISO8601-date>-<fix-sha>.yaml`.
4. Any test failures from the re-run trigger further follow-up PRs
   per affected milestone — NOT reopening merged PRs.

**Evidence authorship**: `ci_local.sh` is the SOLE author of the
cascade-evidence YAML. The script emits a deterministic SHA-256 over
the classified diff (pre-fix vs post-fix of M2a test-contract
files) PLUS the resulting classification verdict, recorded in the
YAML as `cascade_evidence_sha`. Developer is NOT permitted to hand-
author or hand-edit the YAML. Reviewer regenerates the YAML by
re-running `ci_local.sh` at the fix SHA and diffs against the
committed artifact. Any diff in `cascade_evidence_sha` or
classification is a blocking review comment.

**Classification authority**: `ci_local.sh` classifies (a) vs (b)
deterministically from the diff. Operator can override
classification only by editing the M2a test-contract file-set
declaration; not by editing the YAML.

## AD22 — Cross-field config invariant

Load-time FATAL invariant:
`state_min_stability_s × 5 ≤ admission_escalation.continuous_threshold_s`.

With `continuous_threshold_s` frozen at 300s, this bounds
`state_min_stability_s` at ≤ 60s. Tunable range narrowed to
`[5, 60]`. Violation is a FATAL config-load error and the gateway
refuses to start.

Rationale: sub-stability flaps must remain visible to the cumulative
accumulator; a stability window approaching the continuous threshold
defeats both escalation paths (continuous never trips because
envelope never surfaces the degraded state; cumulative never
accumulates for any flap shorter than the window).

M2 acceptance includes a unit test:
`state_min_stability_s=120` with default `continuous_threshold_s=300`
triggers FATAL startup error (ratio 5:2 violates 5:1 invariant).

## AD23 — Admission-artifact JSON schema authorship and ordering

The schema at `docs/schemas/admission-artifact.schema.json` in
`helianthus-ebusgateway` is authored as a normative contract at
plan-lock time. M0 scope in the docs-ebus PR includes the schema's
key-path listing; the schema file itself is committed to
`helianthus-ebusgateway` as part of `M2a_GATEWAY_OFFLINE_HARNESS`
which REFERENCES but does not author the schema semantics. M5 and
M7 consume the schema without modification. Schema drift requires a
plan amendment, not a milestone-local change.

The schema enforces:
- `admission.admission_path_selected` ∈
  `{join, override, degraded_transport_blind, degraded_no_events}`
- Required admission fields: `state, source, companion_target,
  warmup_duration_s, reason_if_degraded, transport_kind,
  admission_path_selected`.
- Required discovery fields: `wire_bytes, window_s,
  startup_burst_pct, post_startup_sustained_rate_probes_per_15s,
  probe_count, promoted_suspects_without_identity,
  per_baseline_address_evidence_counts`.

Enforcement is dual (M5 + M7):
- **Runtime**: gateway emits FATAL log and refuses to start emitting
  artifacts if `admission_path_selected` would be outside the enum.
- **CI**: M7 acceptance script validates the emitted artifact
  against the schema; schema violations fail acceptance.
