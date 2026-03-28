# Status

State: `implementing`

## Current Position

- Bootstrap import complete: the observability workstream now lives in the
  canonical plan layout used by `helianthus-execution-plans`.
- Current milestone focus: `M0/M1/M2/M3/M4/M5/M6 merged on main; M7 active with ISSUE-GW-15 next, family-proof-eligibility and family-scoped promotion-eligibility merged`
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
  - `ISSUE-DOC-06` is now merged/closed in `helianthus-docs-ebus` via PR
    `#218`, merge commit `f037e16131e0efddbd825e4c3f2462f6163eec16`
  - `ISSUE-GW-05` is now merged/closed in `helianthus-ebusgateway` via issue
    `#378`, PR `#379`, merge commit
    `83e9c7b1ba927a282d87599269e91be817ff3582`
  - `ISSUE-DOC-07` is now merged/closed in `helianthus-docs-ebus` via issue
    `#219`, PR `#220`, merge commit
    `cbdf89aa795083093631da7849df5e12e8d448c5`
  - `ISSUE-GW-06` is now merged/closed in `helianthus-ebusgateway` via issue
    `#380`, PR `#381`, merge commit
    `873c970459d1933ba50638df5e6fb349a6a9a3a2`
  - `ISSUE-GW-07` is now merged/closed in `helianthus-ebusgateway` via issue
    `#382`, PR `#385`, merge commit
    `9e9e6904e0337812ffa87591a83ad6f4a5c0ea44`
  - `ISSUE-GW-08` is now merged/closed in `helianthus-ebusgateway` via issue
    `#386`, PR `#387`, merge commit
    `23e46011f3c57d08148cf3cdd51acd6958303f90`
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
- `ISSUE-DOC-06` is also merged/closed on docs `main`; the MCP docs freeze is
  no longer a pending gate item.
- `ISSUE-GW-05` is now merged/closed on gateway `main`, so the `M3` gateway
  GraphQL parity slice is no longer pending.
- `ISSUE-DOC-07` is now merged/closed on docs `main`, so the `M3` doc-gate is
  no longer pending.
- `ISSUE-GW-06` is now merged/closed on gateway `main`, so the `WatchCatalog`
  slice no longer blocks `M4`.
- `ISSUE-GW-07` is now merged/closed on gateway `main`, so the bounded
  `ShadowCache` slice no longer blocks `M4`.
- `ISSUE-GW-08` is now merged/closed on gateway `main`, so the feature-flag
  layer no longer blocks `M4`.
- `M3` is now fully merged on `main`, and `M4` is also fully merged on `main`.
- `ISSUE-GW-09` is now merged/closed on gateway `main` via issue
  `#388`, PR `#389`, merge commit
  `db09bbae687912a16fbc9f0a2f3a5616b84931e8`.
- `ISSUE-DOC-08` is now merged/closed on docs `main` via issue `#221`,
  PR `#222`, merge commit `bf8587f41dedb3be8372b30cf7cd667abc1c0226`.
- `ISSUE-GW-10` is now merged/closed on gateway `main` via issue `#390`,
  PR `#391`, merge commit `75ee6aa639bb44e8e859835293ae3912dc4d7b48`.
- `ISSUE-GW-11` is now merged/closed on gateway `main` via issue `#392`,
  PR `#393`.
- `ISSUE-GW-12` is now merged/closed on gateway `main` via issue `#394`,
  PR `#395`.
- `ISSUE-DOC-09` is now merged/closed on docs `main` via PR `#224`.
- `M5` is now fully merged on `main`.
- `ISSUE-GW-13` is now merged/closed on gateway `main` via issue `#396`,
  PR `#397`, merge commit `9f4a1df2837cbf075c03e9dc65b7419dceb9ae47`,
  after the required HA smoke passed externally on 2026-03-14.
- `ISSUE-GW-14` is now merged/closed on gateway `main` via issue `#398`,
  PR `#399`, merge commit `858e0ec75ad7ba6004e7af62f9043d8304fbd362`,
  after required HA smoke passed on 2026-03-14.
- `ISSUE-DOC-10` is now merged/closed on docs `main` via issue `#225`,
  PR `#226`, merge commit `5ab82fb`.
- `M6` is now fully merged on `main`.
- `M7` is now active, with `ISSUE-GW-15` as the next canonical critical
  path item.
- `ISSUE-GW-15` is now linked to gateway issue
  `Project-Helianthus/helianthus-ebusgateway#400` with bounded slices merged
  via PR `#401` (`5409c216654500a7b822ab620eacf2be59ae9497`), PR `#402`
  (`GW-15: add P03 canary manifest and interval verifier`,
  `1596c9fc02a0f745996cc5c911b9b1fec2c7c22d`), PR `#403`
  (`GW-15: add P03 canary proof verdict gate`,
  `a4cb5fb82b3adea42c45912e4c8f0a2d3e2db5bb`), PR `#404`
  (`GW-15: add P03 proof window gate`,
  `977503bdab9a7bf6cb94b1b4a8243c86ed45e8b5`), PR `#426`
  (`GW-15: add family proof eligibility artifact`,
  `96d7010e9676b686ed3301712b9e9b6d71f7225f`), and PR `#427`
  (`GW-15: add family-scoped promotion eligibility artifact`), merged via
  squash merge.
- The merged `#401` lane closed the first bounded `P03` proof-plumbing slice;
  the merged `#402` lane closed the second bounded slice (fixed `P03` canary
  manifest, active direct-read canary verifier, interval verifier integration,
  and review hardening on baseline seeding, read-only method allowlist, first
  interval artifact scheduling, and semantic phase ordering); and the merged
  `#403` lane closed the third bounded slice (machine-readable canary verdict
  thresholds plus a fail-closed proof-mode gate on top of the
  artifact-production slices). The merged `#404` lane closed the fourth
  bounded slice by requiring an elapsed proof window before proof mode can
  succeed and resetting proof-window state on hard poll failures.
- The merged `#406` lane (`gateway: canonicalize P03 proof gating and
  canaries`) plus follow-up `#408` moved `GW-15` past the earlier
  start-phase-collision failure and into a canonical bounded proof shape on
  gateway `main`.
- The bounded canonical `P03` proof rerun now passes on 2026-03-15 at
  `results-matrix-ha/20260315T070147Z-gw15-proof-p03-canonical-rerun/index.json`.
  That artifact records `P03=pass`, emits the full proof artifact set, and
  includes a passing `canary_verdict.json`; this closes the narrower
  sub-objective “first bounded canonical `P03` proof artifact exists and
  passes” under parent issue `Project-Helianthus/helianthus-ebusgateway#400`.
- The passive follow-up gate also passes at
  `results-matrix-ha/20260315T073335Z-passive-suite-followup-gate/index.json`,
  giving a green bounded passive-suite checkpoint (`P01..P06`) on top of the
  canonicalized proof lane.
- The merged `#410` lane
  (`GW-15 child: add read-avoidance accounting to canonical proof artifacts`)
  replaced placeholder `read_avoidance_accounting` with fail-closed proof-window
  accounting derived from persisted metrics, and it rejects current-run
  mid-window counter regressions instead of trusting only start/end deltas.
- The merged `#412` lane
  (`GW-15: gate proof-window traffic minimums from transaction counters`)
  makes the proof traffic minimums fail closed against the current proof window:
  completed passive transactions now count transaction-classified events only,
  direct-apply candidate counts distinguish evaluated traffic from accepted
  direct applies, and the verifier rejects missing, non-finite, regressing, or
  threshold-missing counters instead of treating the requirement as advisory.
- The merged `#415` lane
  (`GW-15 child: add adversarial replay falsification gate`) replaces the
  earlier fake-green verifier path with a Go-produced observed replay behavior
  artifact, then compares that observed behavior fail-closed against the locked
  replay corpus expectations; garbled boundary cases and the B524 ambiguity case
  are now proven through the behavioral replay seam instead of through corpus
  metadata alone.
- The merged `#420` lane
  (`GW-15 child: fail proof on feature-flag drift`) makes proof-window
  feature-flag state immutability fail closed across start/sample/end snapshot
  artifacts, compares canonicalized GraphQL and bus-observability flag state in
  the proof summary/verdict path, and keeps the legitimate bus-side omitted
  `normalizations` case compatible without weakening GraphQL/canonical malformed
  snapshots.
- The merged `#422` lane
  (`GW-15: derive warmup behavior proof artifact`) replaces the earlier
  fake-green warmup artifact seam with structured `start` / `sample_*` / `end`
  bus-observability and GraphQL snapshots, and it hardens the fake-smoke test
  defaults so CI continues to fail closed on missing or malformed warmup
  transition evidence instead of silently passing on canary-phase labels.
- The family-proof-eligibility slice is now merged via PR `#426`
  (`GW-15: add family proof eligibility artifact`), merge commit
  `96d7010e9676b686ed3301712b9e9b6d71f7225f`, merged at
  `2026-03-28T14:10:16Z`; issue `Project-Helianthus/helianthus-ebusgateway#424`
  was closed by that merge.
- The family-scoped promotion-eligibility slice is now merged via PR `#427`
  (`GW-15: add family-scoped promotion eligibility artifact`) and closes issue
  `Project-Helianthus/helianthus-ebusgateway#425` without advancing the parent
  `GW-15` lane.
- The proof-surface freshness precursor is now merged via PR `#429`
  (`GW-15: expose proof-surface freshness clocks`), merge commit
  `46d1c5cffba6b844a38e07d51c3526d1da0af237`; issue
  `Project-Helianthus/helianthus-ebusgateway#428` is closed by that merge.
- The merged `#429` lane exports provider-owned freshness clocks on the
  bounded proof surfaces, carries them through GraphQL / MCP / verifier
  sampling, and includes the follow-up fix from commit `1e06729` that keeps
  `watchSummary.lastUpdatedAt` stable on idempotent runtime bootstrap reads.
- The merged `#431` lane now publishes honest publisher cadence evidence on
  the runtime bus-observability surface, carries it through GraphQL / MCP,
  and wires the fail-closed publisher-cadence proof artifact that `#423`
  needed as its cross-plane-skew precursor.
- The cross-plane-skew slice is now merged via PR `#432`
  (`GW-15: add cross-plane skew proof artifact`), merge commit
  `fd034693f2ae2fcaeceb02c0b945ab91801925dd`; issue
  `Project-Helianthus/helianthus-ebusgateway#423` is closed by that merge.
- The merged `#432` lane derives `cross_plane_skew.json` only from same-run
  structured start/sample/end snapshots plus the merged publisher-cadence
  artifact, binds the skew threshold to
  `max(publisher_cadence_sec, configured_proof_sample_interval_sec)`, and
  fails closed on missing cadence evidence, missing same-phase timestamps, or
  skew above the bounded target.
- The merged `#421` lane
  (`GW-15 child: report cold-start vs post-warmup behavior in canonical proof
  artifacts`) is now closed on gateway `main` via PR `#422`
  (`f899cc0de1cfd91beb54cf70af96630977e0f950`), and it records the warmup-
  behavior proof artifact slice as merged while keeping `ISSUE-GW-15` active
  for the remaining default-flip evidence.
- `ISSUE-GW-15` still remains active and has not advanced to `ISSUE-GW-16`,
  because the parent gate now explicitly carries the remaining bounded proof
  evidence under issue `#400`: the independent timing-reference seam and the
  still-missing rollback execution proof seam.
- The attempted rollback-smoke child `#418` / PR `#419` was explicitly rerouted
  out of the active lane as a wrong seam: the current repo has no independent
  rollback execution/result primitive, so that artifact cannot yet prove real
  rollback execution instead of derived snapshot state.
- The timing-reference child `#416` remains open but is not part of the
  remaining active bounded proof evidence here; there is still no independent
  wire-derived timing reference source available to compare against busy /
  periodicity observability outputs.
- The tiny parallel lane is now explicitly de-emphasized from this plan's
  critical path: `ISSUE-TE-01` and `ISSUE-TE-02` are re-homed as deferred to
  `common-firmware-rewrite.locked`.
- `ISSUE-DOC-12` remains in observe-first as a deferred tail item; tinyebus
  documentation follows the firmware-rewrite workstream while final rollout
  documentation stays on this plan.
- The original `M0` docs-canonicalization backlog is now fully merged on docs
  `main`; `ISSUE-DOC-01` is exhausted via docs issue
  `Project-Helianthus/helianthus-docs-ebus#208` and PRs `#209` / `#210`,
  `ISSUE-DOC-02` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#211`, PR `#212`,
  `ISSUE-DOC-03` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#213`, PR `#214`, and
  `ISSUE-DOC-04` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#215`, PR `#216`.
- The overall workstream stays in `implementing` on a fully merged `M6`
  baseline, with `ISSUE-GW-15` now carrying the next active delivery lane in
  `M7`.
- `featureFlagsUpdatedAt` remains intentionally process-stable configuration
  metadata after `#429`; that is honest for the freshness precursor but it is
  not itself proof of live-mutating feature-flag skew semantics.

## Blockers

- The imported seed still does not have a historical Discussion archive; it
  uses `bootstrap-seed-import-no-discussion-yet` as the source marker in
  `plan.yaml`.
- `M8` remains intentionally deferred for this plan's critical path and is
  tracked in `common-firmware-rewrite.locked`.
- `M9` remains blocked behind the active `M7` implementation lane now led by
  `ISSUE-GW-15`.

## Next Actions

1. resume `Project-Helianthus/helianthus-ebusgateway#416` as the next bounded
   `GW-15` child slice only when an honest independent wire-derived timing
   reference source exists, keeping the implementation seam separate from the
   already-merged observability/proof surfaces
2. keep `ISSUE-GW-16` blocked until `ISSUE-GW-15` proof slices are complete
   and the `GW-15` safety/timing evidence gate is closed
3. keep `#416` explicitly blocked on an independent wire-derived timing
   reference source and keep `#418` explicitly deferred until a real rollback
   execution hook exists
4. keep `ISSUE-TE-01` / `ISSUE-TE-02` tracking in
   `common-firmware-rewrite.locked` and avoid reactivating tiny work on this
   plan until firmware bring-up milestones are ready
5. open a bootstrap Discussion in `helianthus-execution-plans` to retro-link
   the imported workstream
