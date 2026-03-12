# Status

State: `implementing`

## Current Position

- Bootstrap import complete: the observability workstream now lives in the
  canonical plan layout used by `helianthus-execution-plans`.
- Current milestone focus: `M0 docs canonical linkage (DOC-03/04 remaining); M1 merged on main`
- Current slug state: `observe-first-bus-observability.implementing`
- Anchored implementation has moved past the import seed and the `GW-18`
  merge/proof lane is now settled on repo `main`:
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
  - `ISSUE-GW-18` merged in `helianthus-ebusgateway` via issue `#351`, PR
    `#354`, merge commit `ef4e64eec876975246aba102475de079211d05e2`
  - The supporting proxy merge is issue
    `Project-Helianthus/helianthus-ebus-adapter-proxy#80`, PR `#81`, merge
    commit `a141fe056cbf6a3e212f850b501a893f922f41f6`
  - The supporting docs merge is issue
    `Project-Helianthus/helianthus-docs-ebus#206`, PR `#207`, merge commit
    `4323a4c281dc6cdc776805bc82acf81b4cad3e76`
  - `ISSUE-DOC-02` is now merged in `helianthus-docs-ebus` via issue `#211`,
    PR `#212`, merge commit `577ac0d37cde1ec95dec277bcba0a35fa32648f8`
  - Final parent proof artifact:
    `results-matrix-ha/20260312T094435Z-pr354-parent-passive-p01-p06/index.json`
  - Fresh merged-head passive rerun:
    `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json`
  - The parent artifact records `P01..P06` all `pass`, and the merged-head
    rerun records `P03..P06` all `pass` on gateway `ef4e64e` plus proxy
    `a141fe0`
  - `P01` / `P02` now prove the corrected direct-adapter contract with
    `passive_mode=unsupported_or_misconfigured`
  - `P03` / `P04` / `P05` prove the required passive-capable proxy paths
  - `P06` proves the `ebusd-tcp` negative-path contract with
    `passive_mode=unsupported_or_misconfigured`
  - Focused `P03` proof also exists in
    `results-matrix-ha/20260312T091947Z-proxy81-acb894c-gateway373-97da9f9-p03-rerun/index.json`,
    which passed before the parent full-suite rerun

## Active Focus

- No `GW-18` code, proof, or gateway-family issue blocker remains on merged
  `main`; the merged-head rerun reconfirms `P03..P06` on final gateway/proxy
  heads.
- Gateway follow-up slices `ISSUE-GW-18A` through `ISSUE-GW-18L`, plus the
  harness slice `ISSUE-GW-18M`, are now merged into the parent `GW-18` lane and
  proven by the focused `P03` rerun, the final parent artifact, and the merged-head
  rerun.
- No `GW-18`-family gateway issue and no related proxy/docs issue remains
  open; gateway issue `Project-Helianthus/helianthus-ebusgateway#374`, proxy
  issue `Project-Helianthus/helianthus-ebus-adapter-proxy#80`, and docs issue
  `Project-Helianthus/helianthus-docs-ebus#206` are all closed.
- `ISSUE-DOC-05` is merged on docs `main`; the same-cycle passive transport
  contract is no longer a pending doc-gate item.
- The overall workstream still stays in `implementing` because the remaining
  docs-canonicalization items `ISSUE-DOC-03..04` are not yet linked/merged on
  `helianthus-docs-ebus` `main`; `ISSUE-DOC-01` is exhausted via docs issue
  `Project-Helianthus/helianthus-docs-ebus#208` and PRs `#209` / `#210`,
  `ISSUE-DOC-02` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#211`, PR `#212`, and `M2` has not
  started yet.

## Blockers

- The imported seed still does not have a historical Discussion archive; it
  uses `bootstrap-seed-import-no-discussion-yet` as the source marker in
  `plan.yaml`.
- Documentation-side canonical linkage is still incomplete in
  `helianthus-docs-ebus` `main`; `ISSUE-DOC-03..04` remain unlinked/unmerged.
- `M2` and later milestones are still blocked on that earlier docs
  canonicalization plus fresh issue creation from the merged `M1` baseline.

## Next Actions

1. backfill or merge the pending `ISSUE-DOC-03..04` docs-canonicalization work
   onto `helianthus-docs-ebus` `main`
2. open the next `M2` MCP-first execution lane from the merged `M1` baseline
3. open a bootstrap Discussion in `helianthus-execution-plans` to retro-link
   the imported workstream
