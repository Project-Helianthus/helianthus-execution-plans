# Status

State: `locked` as of 2026-04-23.

Plan directory: `startup-admission-discovery-w17-26.draft/` → will
rename to `.locked/` at plan-lock commit (per cruise-plan skill).

Adversarial rounds: 5 (fully converged on R5). Zero blockers.

Current milestone: `M0_DOC_GATE` (planned, not started).

Plan is internally consistent and mergeable against its own
dependency graph. No `helianthus-ebusgateway` PR can merge until at
least `M0-DRAFT` (docs-ebus PR open-for-review) exists per AD18
doc-gate Tier 1.

Next phase: `cruise-preflight` — routing and complexity classification
for each milestone.

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
