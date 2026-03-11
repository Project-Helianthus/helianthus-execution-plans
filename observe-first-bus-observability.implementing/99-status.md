# Status

State: `implementing`

## Current Position

- Bootstrap import complete: the observability workstream now lives in the
  canonical plan layout used by `helianthus-execution-plans`.
- Current milestone focus: `M0-M1 foundations`
- Current slug state: `observe-first-bus-observability.implementing`
- Anchored implementation has moved past the import seed:
  - `ISSUE-EG-00..03` merged in `helianthus-ebusgo` via
    `Project-Helianthus/helianthus-ebusgo#116`
  - `ISSUE-GW-00` and `ISSUE-GW-17` merged in `helianthus-ebusgateway` via
    `Project-Helianthus/helianthus-ebusgateway#334`
  - `ISSUE-GW-01`, `ISSUE-GW-01B`, `ISSUE-GW-01C`, and `ISSUE-GW-02` merged in
    `helianthus-ebusgateway` via `#335`, `#337`, `#338` plus follow-up `#340`,
    and `#341`
  - `ISSUE-GW-03` merged in `helianthus-ebusgateway` via
    `Project-Helianthus/helianthus-ebusgateway#343`, after the post-matrix
    dual-review follow-ups from issues `#344` and `#345` landed through the
    repair cycle and final branch merge

## Active Focus

- `M1` implementation remains in progress.
- `GW-03` and its `GW-03A/B` review follow-ups are settled and merged.
- The remaining code-side blocker inside `M1` is `ISSUE-GW-18`, now linked as
  `Project-Helianthus/helianthus-ebusgateway#351`.
- `ISSUE-GW-18` now has a repo-owned passive suite and a first clean full
  artifact: `results-matrix-ha/20260311T062516Z-gw18-passive-smoke-v4`.
- That artifact exposed two explicit follow-up blockers:
  - `ISSUE-GW-18A` -> `Project-Helianthus/helianthus-ebusgateway#352`
  - `ISSUE-GW-18B` -> `Project-Helianthus/helianthus-ebusgateway#353`
- `90-issue-map.md` is now being used as the canonical backfill surface for
  merged code-repo execution references.
- Documentation-side canonical IDs `ISSUE-DOC-01..05` still need explicit
  linkage and reconciliation against the current code-repo reality.

## Blockers

- The imported seed does not yet have a historical Discussion archive; it uses
  `bootstrap-seed-import-no-discussion-yet` as the source marker in `plan.yaml`.
- Documentation-side canonical issues are not yet linked in
  `helianthus-docs-ebus`.
- `ISSUE-GW-18` is now linked as
  `Project-Helianthus/helianthus-ebusgateway#351`, and the passive-topology
  smoke lane now exists as repo-owned code plus runtime artifacts, but the
  first clean suite run failed all six cases.
- `ISSUE-GW-18A` blocks supported passive-capable topologies (`P01..P05`) from
  being treated as proven in `M1`.
- `ISSUE-GW-18B` blocks the negative-path `ebusd-tcp` degraded contract from
  being treated as proven in `M1`.
- `ISSUE-DOC-05` is still required before `M1` can close, even though the
  gateway-side metric contract is now merged.

## Next Actions

1. open a bootstrap Discussion in `helianthus-execution-plans` to retro-link the
   imported workstream
2. settle `ISSUE-GW-18A` and `ISSUE-GW-18B`, then rerun the passive suite until
   the `GW-18` proof lane is green again
3. create or link the remaining documentation-side canonical issues and update
   status tracking accordingly
4. settle `ISSUE-DOC-05` and then close `M1`
