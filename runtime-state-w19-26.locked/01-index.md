# Index — Runtime State File

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `5f723d7122dd24c81357dc7adb640cbdb805679a5d91c8b8dedcbe6ef60edede`

## Chunks

- [10-architecture-overview.md](./10-architecture-overview.md) — Objective, scope, non-goals, repo split, lifecycle.
- [11-decision-matrix.md](./11-decision-matrix.md) — AD01..AD27 (full decision matrix with cross-plan references).
- [12-milestones.md](./12-milestones.md) — M0_PLAN_LOCK..M8_TRANSPORT_VERIFY (12 milestones with depends_on, scope, acceptance).
- [13-acceptance-falsifiability-cross-plan.md](./13-acceptance-falsifiability-cross-plan.md) — Falsifiability gate (P1..P6 + N1..N4), cross-plan amendments, deferred-to-v2 list.

## Tracking

- [90-issue-map.md](./90-issue-map.md) — Per-repo issue ID map.
- [91-milestone-map.md](./91-milestone-map.md) — Milestone → repo + topology nodes.
- [99-status.md](./99-status.md) — Current execution position + timeline.

## Adversarial provenance

- Codex gpt-5.5 (high reasoning): 6 rounds (R1..R6), threadId
  `019e1235-62fd-7521-b551-eee8f7b6a94d`, ready_to_lock at R6.
- Claude consultant subagent: SECOND_OPINION per AGENTS.md §8.4, mandatory
  web research (HA add-on /data/ patterns, JSON Schema tooling, fsync
  overlayfs semantics, eBUS timing). Recommendation: GO with 3 MUST-FIX
  patches (MF-1 exit-code semantics; MF-2 fsync portability + EXDEV; MF-3
  Go-native validator pin). All integrated into v3..v5.
