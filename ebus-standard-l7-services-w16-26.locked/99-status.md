# Status

State: `locked`

## Current Position

- Plan locked on `2026-04-18`
- Current milestone: `M0_DOC_GATE` (ready)
- Plan slug: `ebus-standard-l7-services-w16-26.locked`
- Canonical revision: `v1.0-locked`
- Canonical-SHA256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`

## Adversarial Review Summary

- R1: 9 attacks, 3 concessions, 9 PLAN_FIX, 2 ESCALATE_TO_OPERATOR (E1
  mutating invocation policy, E2 NM-plan ownership boundary).
- Operator resolutions: E1=(c) mixed safety-class default-deny keeping
  mutating/destructive/broadcast/memory-write denied in first delivery;
  E2=(c) `ebus_standard` subsumes locked NM plan via adopt-and-extend
  (operator clarification: the deprecated plan's R&D is used for
  enrichment, not discarded).
- R2: 9 attacks, 3 concessions, 9 PLAN_FIX, 1 ESCALATE (E3 on whether
  system-owned NM broadcasts may execute despite default-deny).
- Operator resolution: E3=(a) runtime-context exception with
  compile-time whitelist keyed by full catalog identity, structured
  audit log, and no runtime widening.
- R3: 3 lock-blocker attacks, 3 concessions, 3 PLAN_FIX, 0 escalations.
- R4: PLAN_STABLE, 0 attacks, 4 concessions, 0 recommended fixes, 0
  escalations.

## Deprecation Obligation

- `ebus-good-citizen-network-management.locked` is superseded by this
  plan via adopt-and-extend (see canonical §7).
- Merged NM docs `helianthus-docs-ebus#251/#253/#256` remain
  authoritative and are adopted as subchapters with attribution under
  `M0_DOC_GATE`.
- The superseded plan transitions to `.maintenance` only after `M6b`
  reconciles cross-links and issue map.

## Active Focus

- Create GitHub issues for `M0_DOC_GATE` in `helianthus-docs-ebus`
  (`ISSUE-DOC-EBS-00`, `ISSUE-DOC-EBS-01`, `ISSUE-DOC-EBS-02`).
- `M4b1` may begin as a parallel spike in `helianthus-ebusgo` once
  `M1_TYPES` starts.

## Blockers

- None. `M0_DOC_GATE` is ready to begin.

## Next Actions

1. Hand off to `cruise-preflight` with the registered meta-issue.
2. `cruise-preflight` routes `M0_DOC_GATE` and files any doc-gate /
   transport-gate checklist items required by the per-repo AGENTS.md.
3. Rename plan directory `.locked` → `.implementing` at the first code
   PR merged in any target repo.
