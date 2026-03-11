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
  with seven commits on
  top of `main`:
  - `e322770` `Add passive topology smoke suite and gates`
  - `8174de1` `Degrade passive ebusd-tcp startup cleanly`
  - `2397cea` `Prefer compatible ebusd matrix config fallback`
  - `28fad8b` `GW-18A: recover B524 root after partial preload`
  - `41b35b0` `GW-18: fix passive script review findings`
  - `d5e4011` squash-merge of stacked PR `#357` (`ISSUE-GW-18D`) into
    `issue/351-passive-topology-smoke`
  - `acad9a09` squash-merge of stacked PR `#359` (`ISSUE-GW-18E`) into
    `issue/351-passive-topology-smoke`
- Commit `41b35b0` addresses Codex review findings in the passive gate/wrapper
  script slice; it does not change the plan status that PR `#354` remains
  draft and not merge-ready while `#352`, `#353`, and `#355` stay open.
- The latest incremental branch validation passed local `./scripts/ci_local.sh`
  only with explicit `TRANSPORT_GATE_OWNER_OVERRIDE` and
  `PASSIVE_SMOKE_GATE_OWNER_OVERRIDE`; this is sufficient to record branch
  progress, not to claim the passive proof lane is green or the PR is
  merge-ready.
- Commit `28fad8b` has now also been validated live through a full HA
  addon-image rebuild and restart, not via `/data` binary override.
- The passive proof lane remains red and is still tracked through
  `ISSUE-GW-18A` / `#352`, `ISSUE-GW-18B` / `#353`, and `ISSUE-GW-18C` / `#355`.
- Targeted `P01` / `P02` reruns have now isolated a shared contract problem:
  - the common blocker is the direct-adapter passive support/proof contract,
    not two separate product failures
  - that slice is now being worked as `ISSUE-GW-18D` in
    `helianthus-ebusgateway` via issue `#356` and stacked PR `#357` on top of
    `#354`
  - stacked PR `#357` received a fresh clean Codex result and was then
    squash-merged into `issue/351-passive-topology-smoke` as `d5e4011`
  - the parent proof lane remains PR `#354`, still draft and still not
    merge-ready because passive proof is not closed yet
- A second stacked slice is now merged behind the same parent proof lane:
  - `ISSUE-GW-18E` (`Project-Helianthus/helianthus-ebusgateway#358`) required
    active confirmation before imported-only startup success
  - stacked PR `#359` was squash-merged into `issue/351-passive-topology-smoke`
    as `acad9a09`
  - the next active proof step on the updated parent branch is a resumed
    `GW-18` rerun starting with `P03`
- A third stacked slice is now open for the resumed `P03` proof path:
  - `ISSUE-GW-18F` (`Project-Helianthus/helianthus-ebusgateway#360`) targets
    the `P03` proxy-single startup discovery timeout
  - stacked PR `#361` from branch `issue/360-p03-proxy-single-startup-timeout`
    is open against parent branch `issue/351-passive-topology-smoke`
  - latest stacked head is `8529569`
  - this is still proof-remediation work behind parent PR `#354`; it does not
    claim proof success or milestone closure
- A fourth stacked slice is now open for the same `P03` proof path:
  - `ISSUE-GW-18G` (`Project-Helianthus/helianthus-ebusgateway#362`) targets
    active startup discovery through proxy-single `ENS`
  - stacked PR `#363` from branch
    `issue/362-p03-active-startup-through-proxy-single` is open against
    stacked branch `issue/360-p03-proxy-single-startup-timeout`
  - latest stacked head is `916bc455a8de11bb6be4c0e2e524478ef758cdd1`
  - parent PR `#354` remains open/draft, `#361` remains open and not
    merge-ready, and this is still proof-remediation work rather than proof
    success
- A fifth stacked slice is now open for the same `P03` proof path:
  - `ISSUE-GW-18H` (`Project-Helianthus/helianthus-ebusgateway#364`) targets
    the startup source-address contract on proxy-single `ENS`
  - stacked PR `#365` from branch
    `issue/364-p03-startup-source-addr-contract` is open against
    stacked branch `issue/362-p03-active-startup-through-proxy-single`
  - latest stacked head is `78eacdb239f11654861eb829f37e0ec4fc36aa6a`
  - `#363` remains open and not merge-ready, parent PR `#354` remains
    open/draft, and this is still proof-remediation work rather than proof
    success
- A sixth stacked slice is now active for the same `P03` proof path:
  - `ISSUE-GW-18I` (`Project-Helianthus/helianthus-ebusgateway#366`) targets
    the passive proxy-session contract on proxy-single `ENS`
  - stacked PR `#373` is now the active blocked lane on top of `#371`
  - latest stacked head is `0b5292e`
  - rerun artifact
    `results-matrix-ha/20260312T000413Z-issue373-p03-rerun` is `FAIL`
  - `P03` still showed all four devices present (`NETX3`, `BAI00`, `BASV2`,
    `VR_71`) and `semantic_startup_phase_transition ... to=LIVE_READY`
  - the passive tap final snapshot still ended at connected (`1`),
    `available=0`, and `completed_transactions=0`
  - current blocker reason is `completed_transactions`, and passive
    `decode_fault` request errors still accumulate
  - `#373` remains the active blocked lane and is not ready to fold upward
    into `#371` / `#369` / `#367` / parent PR `#354`
- Current live HA runtime on that rebuilt image confirms branch-slice recovery,
  but still should not be treated as proof-closed:
  - the reported regulator-loss defect recovered live: `BASV2` and `VR_71`
    reappeared after the rebuilt addon image was deployed
  - `system`, `dhw`, and `circuits` recovered live as well
  - startup reached `LIVE_READY`
  - this is branch validation for the `28fad8b` fix, not evidence that the
    passive proof lane is green or that PR `#354` is merge-ready
- `90-issue-map.md` is now being used as the canonical backfill surface for
  merged code-repo execution references.
- The same-cycle docs follow-up for the `GW-18A` startup/discovery fix is now
  active in `helianthus-docs-ebus`:
  - `ISSUE-DOC-05` -> issue `Project-Helianthus/helianthus-docs-ebus#206`
  - PR `Project-Helianthus/helianthus-docs-ebus#207` carries the current docs
    lane for that follow-up and was amended to document the passive transport
    contract discovered in the `P01` / `P02` proof work
  - PR `#207` also received a fresh clean Codex result and is ready from the
    review-watch perspective, but it has not been merged yet
- Documentation-side canonical IDs `ISSUE-DOC-01..04` still need explicit
  linkage and reconciliation against the current code-repo reality.

## Blockers

- The imported seed does not yet have a historical Discussion archive; it uses
  `bootstrap-seed-import-no-discussion-yet` as the source marker in `plan.yaml`.
- Documentation-side canonical linkage is still incomplete in
  `helianthus-docs-ebus`; `ISSUE-DOC-05` is now active via `#206` / PR `#207`,
  but `ISSUE-DOC-01..04` remain unlinked here.
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
- `ISSUE-GW-18D` is now the active slice for the shared `P01` / `P02`
  direct-adapter passive contract blocker; until that gateway/docs pair lands,
  those cases should be treated as contract-unproven rather than separately
  failing for unknown reasons.
- `ISSUE-GW-18E` is now merged into the parent `issue/351` branch, but only as
  branch evidence behind draft PR `#354`; it does not close the milestone until
  proof reruns on the updated branch succeed.
- `ISSUE-GW-18F` is now active as the next stacked remediation slice for `P03`;
  until it lands and the rerun succeeds, parent PR `#354` remains draft and the
  proof lane remains open.
- `ISSUE-GW-18G` is now active as a further stacked remediation slice for
  `P03`; until it lands and the rerun succeeds, parent PR `#354` remains draft,
  PR `#361` remains open, and the proof lane remains open.
- `ISSUE-GW-18H` is now active as a further stacked remediation slice for
  `P03`; until it lands and the rerun succeeds, PR `#363` remains open and not
  merge-ready, parent PR `#354` remains draft, and the proof lane remains
  open.
- `ISSUE-GW-18I` is now active as a further stacked remediation slice for
  `P03`, but rerun artifact
  `results-matrix-ha/20260312T000413Z-issue373-p03-rerun` still fails after
  showing all four devices present and
  `semantic_startup_phase_transition ... to=LIVE_READY`, with passive tap final
  snapshot connected (`1`), `available=0`, and `completed_transactions=0`; the
  current blocker reason is `completed_transactions`, passive `decode_fault`
  request errors still accumulate, and `#373` remains the active blocked lane
  and is not ready to fold upward into `#371` / `#369` / `#367` / parent PR
  `#354`.
- Live HA validation now shows the reported regulator/system-loss symptom
  recovered on the rebuilt addon image, but that recovery is still branch-only
  evidence and does not clear the red passive proof lane.
- Doc-gate is now explicitly `YES` for the active `GW-18A` branch state, so a
  same-cycle docs follow-up is required before the gateway work can be treated
  as merge-ready.
- `ISSUE-DOC-05` is now active on issue `#206` / PR `#207`; it is still
  required before `M1` can close and can no longer be treated as deferred
  cleanup after the gateway branch lands.

## Next Actions

1. open a bootstrap Discussion in `helianthus-execution-plans` to retro-link the
   imported workstream
2. settle `ISSUE-GW-18A`, `ISSUE-GW-18B`, and `ISSUE-GW-18C`, then rerun the
   passive suite until the `GW-18` proof lane is green again
3. keep the live rebuilt-image recovery result as branch evidence only until the
   passive suite reruns go green, and treat the current `P03` failure on
   stacked PR `#373` as the active product blocker rather than as a lab-only
   handoff artifact
4. settle `ISSUE-GW-18I` on stacked PR `#373` first, because it is still the
   active blocked lane for `P03` and is not ready to fold upward into `#371` /
   `#369` / `#367` / parent PR `#354`; only then continue folding the stacked
   `GW-18` remediation chain upward and resume the parent proof rerun
5. settle `ISSUE-DOC-05` and then close `M1`
