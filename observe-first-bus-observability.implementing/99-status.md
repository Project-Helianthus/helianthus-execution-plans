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
- `ISSUE-GW-18A` now has an active branch-only regulator-loss recovery commit:
  - `28fad8b` `GW-18A: recover B524 root after partial preload`
  - this work is committed on `issue/351-passive-topology-smoke` / PR `#354`
    but is not merged, so `ISSUE-GW-18A` remains open until reruns prove the
    passive lane green again
- `ISSUE-GW-18B` no longer reproduces as a startup-fatal product bug on the
  active branch. Reruns `results-matrix-ha/20260311T064844Z-gw18b-p06-v1` and
  `results-matrix-ha/20260311T065409Z-gw18b-p06-v2` show the gateway staying
  alive and passive metrics degrading to `unsupported_or_misconfigured`
  correctly.
- Those reruns exposed a new harness-side blocker:
  - `ISSUE-GW-18C` -> `Project-Helianthus/helianthus-ebusgateway#355`
  - matrix `ebusd` config/image compatibility still prevents `P06` from
    proving non-empty active discovery cleanly
- Active branch state for `ISSUE-GW-18` is `Project-Helianthus/helianthus-ebusgateway#354`
  on `issue/351-passive-topology-smoke`, currently draft and not merge-ready
  with four commits on
  top of `main`:
  - `e322770` `Add passive topology smoke suite and gates`
  - `8174de1` `Degrade passive ebusd-tcp startup cleanly`
  - `2397cea` `Prefer compatible ebusd matrix config fallback`
  - `28fad8b` `GW-18A: recover B524 root after partial preload`
- The latest incremental branch validation passed local `./scripts/ci_local.sh`
  only with explicit `TRANSPORT_GATE_OWNER_OVERRIDE` and
  `PASSIVE_SMOKE_GATE_OWNER_OVERRIDE`; this is sufficient to record branch
  progress, not to claim the passive proof lane is green or the PR is
  merge-ready.
- The passive proof lane remains red and is still tracked through
  `ISSUE-GW-18A` / `#352`, `ISSUE-GW-18B` / `#353`, and `ISSUE-GW-18C` / `#355`.
- Current live HA runtime should not be treated as proof-closed:
  - GraphQL currently returns only `NETX3` and `BAI00` from `devices`
  - GraphQL `system` is currently `null`
  - the adapter status page still shows `eBUS signal: acquired` and `ebusd connected: yes`
  - recent `ebusd` logs still show live `BASV2` / `VR_71` traffic, so the bus
    is not dead; the runtime is only partially reconverged after the smoke lane
    experiments
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
- `ISSUE-GW-18A` still blocks supported passive-capable topologies (`P01..P05`)
  from being treated as proven in `M1`; commit `28fad8b` is an unmerged branch
  fix, not milestone-closing evidence.
- `ISSUE-GW-18B` is still open until the branch work lands, but its remaining
  proof gap is no longer a startup-fatal gateway bug.
- `ISSUE-GW-18C` blocks `P06` from being treated as fully proven in `M1`
  because the matrix `ebusd` side still fails config compatibility before it
  can provide clean active discovery evidence.
- Live HA runtime is currently below the pre-GW-18 validation baseline even
  though the adapter is healthy enough to show signal and active traffic. Until
  full device and semantic parity return, live observations must be treated as
  degraded runtime evidence, not as milestone-close evidence.
- Doc-gate is now explicitly `YES` for the active `GW-18A` branch state, so a
  same-cycle docs follow-up is required before the gateway work can be treated
  as merge-ready.
- `ISSUE-DOC-05` is still required before `M1` can close, and it can no longer
  be treated as deferred cleanup after the gateway branch lands.

## Next Actions

1. open a bootstrap Discussion in `helianthus-execution-plans` to retro-link the
   imported workstream
2. settle `ISSUE-GW-18A`, `ISSUE-GW-18B`, and `ISSUE-GW-18C`, then rerun the
   passive suite until the `GW-18` proof lane is green again
3. restore live HA runtime to full device and semantic parity before treating
   any new smoke evidence as operator-ready
4. create or link the remaining documentation-side canonical issues and update
   status tracking accordingly, with the `GW-18A` docs follow-up treated as a
   same-cycle requirement rather than post-merge cleanup
5. settle `ISSUE-DOC-05` and then close `M1`
