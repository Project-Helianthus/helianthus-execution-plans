# Status

State: `locked`

## Current Position

- Locked testing-first rewrite plan imported into `helianthus-execution-plans`.
- Current milestone focus: `T0`
- Current slug state: `common-firmware-rewrite.locked`
- The plan is structurally complete only after the issue map, milestone map, and
  status files exist alongside the canonical and split documents.

## Active Focus

- establish the T0 execution lane as the next actionable entry point
- backfill canonical issue IDs before implementation starts in any downstream
  repo
- keep the rewrite framed as a testing-first, proof-gated workstream rather
  than a direct implementation sprint

## Blockers

- no downstream canonical issues are linked yet for `T0` through `M9`
- family-specific hardware truth for v3.x and ESERA remains unresolved by design
  until `M0`
- per-repo structure assumptions called out in the doc-gate remain unconfirmed
  until T0 and M0 execution

## Next Actions

1. open and link the `T0` canonical issues from [90-issue-map.md](./90-issue-map.md)
2. execute the testing-first document and oracle-export work required to close
   `T0`
3. promote the plan from locked-only tracking to active execution once T0 work
   is formally opened
4. keep `91-milestone-map.md` and `90-issue-map.md` synchronized as real issues
   and PRs appear
