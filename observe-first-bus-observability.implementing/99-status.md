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
  - `ISSUE-GW-03` reached transport validation with the successful `T01..T88`
    artifact `20260310T121708Z-gw03-recovery-full88-v3`, but the merge lane is
    now held by post-matrix dual-review follow-ups
    `Project-Helianthus/helianthus-ebusgateway#344` and `#345`

## Active Focus

- `M1` implementation remains in progress.
- `ISSUE-GW-03` is blocked in review on
  `Project-Helianthus/helianthus-ebusgateway#343`.
- The current follow-up lane is `ISSUE-GW-03A` as
  `Project-Helianthus/helianthus-ebusgateway#344`, with `ISSUE-GW-03B` queued
  immediately behind it as `#345`.
- `90-issue-map.md` is now being used as the canonical backfill surface for
  merged code-repo execution references.
- Documentation-side canonical IDs `ISSUE-DOC-01..05` still need explicit
  linkage and reconciliation against the current code-repo reality.

## Blockers

- The imported seed does not yet have a historical Discussion archive; it uses
  `bootstrap-seed-import-no-discussion-yet` as the source marker in `plan.yaml`.
- Documentation-side canonical issues are not yet linked in
  `helianthus-docs-ebus`.
- `ISSUE-GW-03` is not merge-ready after the competitive review cycle:
  `#344` tracks the missed passive-warmup bootstrap when the store attaches
  after the tap is already connected, and `#345` tracks the dead
  `local_participant_inbound` wiring path.
- A separate live-lab adapter hang was observed during the same validation
  window, but it is treated as runtime/lab health rather than as the code
  readiness blocker for `GW-03`.

## Next Actions

1. open a bootstrap Discussion in `helianthus-execution-plans` to retro-link the
   imported workstream
2. implement `ISSUE-GW-03A`, then immediately settle whether `ISSUE-GW-03B`
   lands in the same repair cycle or as the next M1 follow-up
3. finish `ISSUE-GW-03` and backfill its merge into `90-issue-map.md`
4. create or link the remaining documentation-side canonical issues and update
   status tracking accordingly
5. close `M1` only after the post-matrix follow-ups and `ISSUE-DOC-05` settle
