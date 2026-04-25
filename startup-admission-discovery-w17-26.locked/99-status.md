# Status

State: `locked` (TERMINAL) — all 9 milestones merged 2026-04-25.

Adversarial rounds: 5 (fully converged on R5). Zero blockers at lock.

Current milestone: null (plan complete).
Final milestone: `M7_GATEWAY_INTEGRATION_ACCEPTANCE` (squash `aa9263a`
via ebusgateway#545).

## Merged milestones (squash SHAs)

| Milestone | Repo | PR | Squash SHA |
|---|---|---|---|
| M0_DOC_GATE | docs-ebus | #287 | `9ceab29` |
| M1_EBUSREG_DIRECTED_SCAN | ebusreg | #127 | `7f699c1` |
| M2_GATEWAY_JOINBUS_ADAPTER | ebusgateway | #527 | `52133af` |
| M2a_GATEWAY_OFFLINE_HARNESS | ebusgateway | #540 | `7216d10` |
| M3_GATEWAY_STARTUP_ORDER_FLIP | ebusgateway | #541 | `26aa930` |
| M4_GATEWAY_EVIDENCE_PIPELINE | ebusgateway | #542 | `d4204a1` |
| M5_GATEWAY_DEGRADED_MODE_AND_ENVELOPE | ebusgateway | #543 | `967fa1d` |
| M6_GATEWAY_OVERRIDE_AND_FULL_RANGE_GUARD | ebusgateway | #544 | `e0135b1` |
| M7_GATEWAY_INTEGRATION_ACCEPTANCE | ebusgateway | #545 | `aa9263a` |
| (transport-gate evidence) | ebusgateway | #546 | merged |

Gateway PRs M2a..M7 have higher PR numbers than originally opened
(#529..#539) because GitHub auto-closed the original stacked PRs when
their base branches (M2..M6) were squash-merged + deleted. PRs were
re-created against `main` with the unique commits cherry-picked. The
original PR numbers are preserved in the squash commit messages and
in the per-milestone issue history.

## Live-bus evidence

`docs/transport-gate-evidence/2026-04-25-adapter-direct-enh.yaml` in
helianthus-ebusgateway captures the M7 acceptance runtime evidence
from the RPi4 deployment at 192.168.100.4 (gateway binary SHA256
`ddc34283fee7a72a7603d59b5aecdc550e42882fc4085c48e6892d1cd92b4001`,
adapter-direct ENH @ 192.168.100.2).

The evidence shows new admission code paths are alive (classifier
log line, AD17 restart-WARN, `startup_directed_probe_phase` log,
artifact emission at the 60s window). `admission_path_selected =
degraded_no_events` because the deployment uses adapter-direct
multiplexer mode which the classifier correctly rejects (AD11) and
routes to static-fallback (AD13). Joiner does NOT run in this
configuration.

## Follow-up tasks (carried into post-cruise plans)

1. **Adapter-direct unwrapping**: extend `ClassifyTransportAdmission`
   so adapter-direct mode classifies based on its underlying ENH/ENS
   adapter. Until then, M7 join-path runtime evidence requires
   reconfiguring the deployment to non-adapter-direct ENS or running
   on a dedicated test bench.
2. **Evidence-buffer wiring**: `evidenceHasVaillantRoot` is hardcoded
   `false` at production call sites of `scanWithFullRangeGuard` (M6
   review-flagged). Diagnostic flag is unreachable until evidence-
   buffer integration lands.

Both items are tracked under `plan.yaml.follow_up_tasks` and should
be addressed in a narrow follow-up plan.

## Adversarial Round Trajectory

| Round | Attacks (B/M/m) | Concessions | Escalations | Outcome |
| --- | --- | --- | --- | --- |
| R1 | 12 (2/7/3) | 3 | 5 | operator-resolved: E1..E5 |
| R2 | 13 (1/7/5) | 4 | 4 | operator-resolved: E6..E9 |
| R3 | 15 (0/7/8) | 12 | 4 | operator-lean-resolved |
| R4 | 12 (0/5/7) | 7 | 4 | operator-lean-resolved |
| R5 | 0 | 10 | 0 | **`converged: true`** |

Primary planner: **Codex (gpt-5.4 high reasoning)** — role-inversion
swap per operator directive; Codex drafted R1..R5 plans.

Adversary: **fresh Claude Opus** via orchestrator-glued dispatch —
Claude-fresh-Opus attacked Codex's drafts each round with narrow
context (draft + normative anchors + frozen resolutions only).

Orchestrator: Claude Code (this session) — FSM state, escalation
routing, operator liaison, plan-artifact authorship.

## Role-Inversion Summary

- **Dev**: 100% Codex (no Claude-side dev fallback).
- **Planning primary**: Codex.
- **Adversarial planning R1-R5**: Claude-fresh-Opus (red-team
  only; narrow context; never drafts primary artifact).
- **Orchestration**: Claude Code (main session) — state, doc-gate,
  merge-gate, meta-issue bookkeeping.
- **PR Code review (forthcoming)**: Codex primary; Claude-fresh
  second-opinion only when pairing required.

## Operator Escalation Log (all resolved at plan-lock time)

R1 escalations (5): E1 multi-PR exception, E2 burst-class budget
ratification, E3 override semantics (c2+i), E4 semantic polling gate
(signal-source), E5 bus_admission data-body hash coverage. All
resolved in operator conversation; frozen as AD14, AD15, AD09, AD16,
AD08.

R2 escalations (4): E6 transitive-closure `merge_depends_on`, E7
K=5/T=5min degraded-mode escalation, E8 enum without `static_fallback`,
E9 two-tier doc-gate. All resolved as AD14 addendum, AD17, AD11
addendum, AD18.

R3 escalations (4): cumulative+continuous escalation semantics;
parent back-ref repo ownership; M2a post-merge cascade scope;
live-bus coverage binding. All operator-lean-resolved; frozen as
AD17 update, AD19, AD21, and M7 live-bus acceptance clause.

R4 escalations (4): cumulative accumulator persistence; cross-field
config invariant; cascade evidence authorship; second-reviewer trust
root under inversion. All operator-lean-resolved; frozen as AD17
update, AD22, AD21 update, AD20.

R5: no escalations; converged.

## Parent-Plan Relationship

Extracts `ISSUE-GW-JOIN-01` from
`ebus-good-citizen-network-management.maintenance/11-runtime-discovery-and-policy.md`.
Parent plan state stays `.maintenance`. Per AD19, the parent-plan
back-reference edit is folded into the plan-lock commit in this
repo (`helianthus-execution-plans`) — NOT a separate PR; NOT a
docs-ebus M0 concern.

Per `feedback_deprecation_enrichment.md`, the parent is treated as
an enrichment source: its normative artifacts remain authoritative
where they apply; this plan does NOT rewrite them.
