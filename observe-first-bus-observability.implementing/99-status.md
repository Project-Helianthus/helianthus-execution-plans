# Status

State: `implementing`

## Current Position

- Bootstrap import complete: the observability workstream now lives in the
  canonical plan layout used by `helianthus-execution-plans`.
- Current milestone focus: `M0/M1 merged on main; M2 active with ISSUE-GW-04 merged and ISSUE-DOC-06 next`
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
  - `ISSUE-DOC-03` is now merged in `helianthus-docs-ebus` via issue `#213`,
    PR `#214`, merge commit `7620102dec68f6a803739974a81e0e6d0366b4a4`
  - `ISSUE-DOC-04` is now merged in `helianthus-docs-ebus` via issue `#215`,
    PR `#216`, merge commit `0da202a4545bf522a6e866a93905e0aba234a551`
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
  - `ISSUE-GW-04` is now merged in `helianthus-ebusgateway` via issue `#376`,
    PR `#377`, merge commit `3daf4beed9d6406f7af52869eea1c53ef14f2f62`
  - Fresh `GW-04` passive proof artifact
    `results-matrix-ha/20260312T175648Z-pr377-gw04-26ee758-passive-p01-p06-recovery/index.json`
    records `P01..P06` all `pass`
  - The fresh standard exclusive-handoff recovery probe
    `results-matrix-ha/20260312T175250Z-pr377-gw04-26ee758-recovery/full88-probe-t01-after-adapter-reboot/index.json`
    remained `blocked-infra` with `infra_reason=adapter_no_signal` after one
    adapter reboot, so the merge used an owner override only after the artifact
    pair proved the official addon/runtime was restored cleanly afterward

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
- The original `M0` docs-canonicalization backlog is now fully merged on docs
  `main`; `ISSUE-DOC-01` is exhausted via docs issue
  `Project-Helianthus/helianthus-docs-ebus#208` and PRs `#209` / `#210`,
  `ISSUE-DOC-02` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#211`, PR `#212`,
  `ISSUE-DOC-03` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#213`, PR `#214`, and
  `ISSUE-DOC-04` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#215`, PR `#216`.
- The overall workstream stays in `implementing` because `M2` is now open but
  not yet complete: the gateway half is merged, while the docs freeze in
  `ISSUE-DOC-06` is now the active gate before `M3`.

## Blockers

- The imported seed still does not have a historical Discussion archive; it
  uses `bootstrap-seed-import-no-discussion-yet` as the source marker in
  `plan.yaml`.
- `ISSUE-DOC-06` is now the gating blocker for the rest of `M2`; until the
  merged MCP surface is frozen against real output, `ISSUE-GW-05` and all of
  `M3+` remain blocked.

## Next Actions

1. execute `ISSUE-DOC-06` to freeze the merged MCP contract against the
   `GW-04` merged head and proof artifacts
2. open `ISSUE-GW-05` only after `ISSUE-DOC-06` lands, keeping the `MCP ->
   GraphQL` sequencing intact
3. open a bootstrap Discussion in `helianthus-execution-plans` to retro-link
   the imported workstream
