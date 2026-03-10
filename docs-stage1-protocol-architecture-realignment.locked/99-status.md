# Status

State: `locked`

## Current Position

- Locked bootstrap import prepared for the `helianthus-execution-plans`
  repository.
- Current milestone focus: `M0`
- Current slug state:
  `docs-stage1-protocol-architecture-realignment.locked`
- This import packages the Stage 1 realignment contract before any downstream
  `helianthus-docs-ebus` execution issues or PRs are opened.

## Active Focus

- land the locked import cleanly in the execution-plans repository
- define and complete the docs-repo sanitation lane before downstream content
  edits start
- establish the canonical issue IDs and milestone ordering for the downstream
  docs workstream
- require canonical-plan linkage in all related downstream issues and PRs once
  the import merges

## Blockers

- no Discussion thread exists yet for this workstream, so `plan.yaml` uses the
  bootstrap marker `bootstrap-docs-realignment-2026-03-10-no-discussion-yet`
- the canonical plan URL does not exist until the import PR merges
- downstream docs issues and PRs cannot reference the canonical plan URL until
  that merge happens
- the docs repo still exposes the two sanitation targets as remote branches
  until `ISSUE-DOC-00` is executed

## Next Actions

1. merge the locked import PR in `helianthus-execution-plans`
2. execute `ISSUE-DOC-00` and remove the stale and objective-equivalent remote
   branches from `helianthus-docs-ebus`
3. open downstream `helianthus-docs-ebus` issues for `ISSUE-DOC-01` through
   `ISSUE-DOC-06`
4. require the canonical plan URL in every related issue and PR
5. move from `M0` to `M1` only after the plan URL is stable, linked, and the
   sanitation pass is complete
