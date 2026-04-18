# Status

State: `locked`

## Current Position

- Plan locked on `2026-04-18`
- **M0_DOC_GATE COMPLETE** (2026-04-18) — merged via squash as `b85e7084` in `helianthus-docs-ebus`
- Current milestone: `M1_TYPES` (ready) + `M2_CATALOG` (ready, can run in parallel)
- Plan slug: `ebus-standard-l7-services-w16-26.locked`
- Canonical revision: `v1.0-locked`
- Canonical-SHA256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`

## M0_DOC_GATE Deliverables

| Issue | PR | Squash SHA | Files |
|---|---|---|---|
| [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) | [#267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) | `b85e7084` | 9 files under `architecture/ebus_standard/` |

Adopted NM docs (`nm-model.md`, `nm-discovery.md`, `nm-participant-policy.md`) UNMODIFIED — adopt-and-extend invariant honored per AD10.

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
  `M0_DOC_GATE` (delivered via PR #267).
- The superseded plan transitions to `.maintenance` only after `M6b`
  reconciles cross-links and issue map.

## Active Focus

- `M1_TYPES` in `helianthus-ebusgo` — L7 primitive types with positive
  and negative golden vectors. Now unblocked.
- `M2_CATALOG` in `helianthus-ebusreg` — catalog schema + YAML data +
  identity key + collision test + SHA pinning. Now unblocked (parallel
  with M1).
- `M4b1` parallel-spike in `helianthus-ebusgo` may begin once `M1_TYPES`
  starts.

## Blockers

- None.

## Next Actions

1. Re-enter `cruise-preflight` for wave 2 batch (M1_TYPES + M2_CATALOG).
2. Rename plan directory `.locked` → `.implementing` at the first CODE
   PR merged in any target repo (M0 was docs-only; rename trigger
   awaits first code merge in `helianthus-ebusgo` or `helianthus-ebusreg`).
