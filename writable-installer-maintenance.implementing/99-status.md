# Status

State: `implementing`

## Current Position

- Slug moved from `writable-installer-maintenance.locked` to
  `writable-installer-maintenance.implementing`.
- Canonical contract reconciled on `2026-04-09` to match implemented behavior
  and explicit post-implementation design corrections.
- Main implementation lanes are merged on target repos:
  - docs: `7c4fc5a` (`WIM-M0`)
  - gateway: `c9c8f59` (`WIM-M2+M3`)
  - HA integration: `7c818c6` (`WIM-M4`)
- Tracking files are now aligned to merged evidence and corrected design.

## Convergence History (pre-implementation lock phase)

| Round | Engine | P0 | P1 | P2 | Key Fixes |
| --- | --- | --- | --- | --- | --- |
| 8 | Codex gpt-5.4 | 0 | 2 | 2 | Field-additive degradation, write-through cache |
| 9 | Codex gpt-5.4 | 0 | 4 | 1 | Removed M1-pre, parity hash scope |
| 10 | Codex gpt-5.4 | 0 | 5 | 5 | Probe params, writer wiring, HA availability gates |
| 11 | Claude Opus | 0 | 5 | 6 | Pipeline and data-merge refinements |
| 12 | Claude Opus | 0 | 0 | 2 | Converged lock baseline |

## Active Focus

- Keep this plan in `implementing` until reconciliation lane `M4r` is closed.
- Preserve canonical alignment with merged code for:
  - aggregated controller installer fields,
  - menu code in text entities,
  - boiler phone digit-string/BCD semantics,
  - read-only `hoursTillService`.

## Remaining Blockers

- Probe evidence artifacts for `M1A/M1B` are not archived in this plan
  directory (`unarchived` state).
- Final consistency pass may still be needed if any docs wording outside this
  plan references superseded split-field assumptions.

## Next Actions

1. Backfill probe artifacts (`M1A/M1B`) in this plan repository or record
   explicit waiver rationale.
2. Complete final wording consistency pass between canonical and docs snapshots.
3. If no residual drift remains, promote plan from `.implementing` to
   `.maintenance`.

