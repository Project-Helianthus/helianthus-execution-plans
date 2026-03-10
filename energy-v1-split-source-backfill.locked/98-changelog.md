# Energy v1 Locked-Plan Changelog

This file exists so Sonnet can validate that each review round changed the
locked-plan artifacts in a traceable way.

## Bootstrap Import

- Imported the converged root-level `Energy v1.md` plan into the canonical
  `helianthus-execution-plans` layout.
- Recast the old single-file plan into:
  - `00-canonical.md`
  - `01-index.md`
  - four reviewable `10-13` chunks
  - `90-issue-map.md`
  - `91-milestone-map.md`
  - `99-status.md`
- Moved the plan from the old direct-file flow to the new locked-plan flow.
- Added explicit `MCP -> GraphQL -> Portal -> HA` sequencing for the new daily
  history capability.
- Kept the converged semantic decisions from the prior review loop:
  - split-source ownership
  - bounded `B516` history budget
  - completed-days-only history contract
  - atomic first-install anchor rule
  - hard-disabled previous-year gate

## Locked-Plan Review Round 1

- Declared `1 request / 2s` as the primary history pacing limit and made
  `30 requests / minute` a derived sanity-check cap, with the lower effective
  rate winning if those ever diverge.
- Added an explicit cross-source coherence proof gate:
  - `B524_lifetime ~= sum(B516_completed_days) + B516_today`
  - the measured drift budget sets the anchor tolerance
  - first-install backfill remains disabled if that proof fails
- Added an explicit intra-M1 dependency:
  - `ISSUE-GW-ENERGY-02` depends on `ISSUE-GW-ENERGY-01` unless both land
    atomically in one PR
- Made the gateway source-precedence proof falsifiable with a named test
  procedure around nonzero `B516 today` surviving a `B524` refresh.
- Turned Portal validation into a concrete gate:
  - at least 7 completed daily values
  - exact match with MCP output for the same query
  - current day must not render as completed history
- Declared that HA backfill does not import partial newest-only history suffixes;
  it waits for the full contiguous completed-day coverage window for the enabled
  target before seeding stats.
- Aligned the milestone map by removing `helianthus-ebusgateway` from `M4`
  primary repos because no gateway-owned M4 issue exists.

## Locked-Plan Review Round 2

- Relabeled the `147 minutes` figure as a theoretical minimum sweep time at
  sustained max rate rather than a promised worst-case ceiling.
- Added explicit coverage completion signaling for history consumers:
  - MCP stabilization must prove it
  - GraphQL now adds `energyHistoryDailyStatus`
  - the importer waits on `scanComplete` plus the reported coverage window
- Made `ISSUE-DOC-ENERGY-03` the explicit owner of the live cross-source
  coherence measurement and the tolerance constant publication, and kept
  `ISSUE-HA-ENERGY-02` blocked on that result.
- Clarified that the first-install base anchor is an intentional opaque residual
  for pre-import history and must be non-negative.
- Replaced the fuzzy HA same-day proof line with an explicit latency contract:
  - sensor state within one semantic poll cycle
  - long-term statistics on the next hourly rollup

## Locked-Plan Review Round 3

- Removed duplicate sweep-volume lines from the canonical and gateway chunks.
- Declared the exact source mapping for the first-install anchor formula:
  - `live_total_now` comes from the `B524` lifetime/all-time anchor
  - `today_so_far` comes from the `B516 day/current-year` intraday value
- Tightened Portal validation so "match" means aligned `start`/`end` ranges plus
  `valueKwh` equality at the same source round-trip precision.
- Added an explicit sequencing rule that `ISSUE-DOC-ENERGY-03` must publish the
  coherence measurement and tolerance before `ISSUE-GW-ENERGY-04` begins.
- Moved the `ISSUE-HA-ENERGY-02` blocking rule to the `M4` section and tied it
  to both the coherence publication and the GraphQL/Portal completion gates.

## Locked-Plan Review Round 4

- Made `ISSUE-GW-ENERGY-03` explicitly own the same-poll-cycle read path needed
  for the live cross-source coherence measurement, so M2 does not depend on M3
  for its first trustworthy read coordination.
- Added the missing intra-M3 ordering rule:
  - `ISSUE-GW-ENERGY-05` depends on `ISSUE-GW-ENERGY-04` merging first

## Locked-Plan Review Round 5

- Replaced the structurally invalid lifetime coherence formula with a
  month-scoped proof that is actually testable with current-year B516 data:
  - `B524_month_current ~= sum(B516_completed_days_this_month) + B516_today`
- Defined the `energyHistoryDailyStatus` coverage window explicitly:
  - January 1 through the last completed day in the requested year
  - `scanComplete` only after every day in that window is read or confirmed
    unsupported
- Kept the lifetime anchor only for the base-residual calculation, not for the
  coherence proof itself.

## Locked-Plan Review Round 6

- Added explicit importer patience behavior for `scanComplete`:
  - configurable wait window, default `6h`
  - no automatic partial seed
  - diagnostic with `daysScanned`, `daysExpected`, and coverage percentage on
    expiry
- Extended `EnergyHistoryDailyStatus` with `daysScanned` and `daysExpected` so
  the importer and diagnostics can reason about progress explicitly.
- Tightened the lifetime-anchor justification:
  - base must satisfy `0 <= base <= live_total_now`
  - month-scoped proof plus base bound plus continuity check are the trust chain
- Reframed the same-day latency gate to the gateway `energyTotals.today`
  surface; HA client-side latency now belongs to the HA rollout issues.
- Rewrote `ISSUE-GW-ENERGY-03` so its summary unambiguously includes the
  same-poll-cycle coherence-measurement read path as a hard deliverable.

## Locked-Plan Review Round 7

- Added a persistent importer cooldown after unchanged stalled scans so restart
  loops do not repeatedly burn the full patience window.
- Added `pairStatus` to `EnergyHistoryDailyStatus` so unsupported pairs have a
  concrete GraphQL representation.
- Made the `ISSUE-DOC-ENERGY-03 -> ISSUE-GW-ENERGY-04` gate explicit in both
  the M2 and M3 sections of the issue map.
- Defined the restart-safe collector cursor as
  `previous_run_newest_completed_day + oldest_scanned_day`, with explicit
  catch-up of newly completed days before resuming the backward walk.

## Locked-Plan Review Round 8

- Moved `ISSUE-HA-ENERGY-01` into the existing-surface M1 track so corrected
  live-`today` behavior no longer waits behind the new-capability pipeline.
- Added the explicit `ISSUE-DOC-ENERGY-04 -> ISSUE-GW-ENERGY-05` dependency so
  the GraphQL/Portal doc freeze happens after Portal validation.
- Made `daily_round_trip_quantum` an explicit required output of
  `ISSUE-DOC-ENERGY-03` so `epsilon_seed` is computable at HA rollout time.
- Added the explicit `ISSUE-DOC-ENERGY-03 -> ISSUE-GW-ENERGY-03` ordering rule
  in canonical plus split artifacts.
- Aligned the M1 milestone map with the revised issue placement.
- Clarified that `scanComplete` is non-interpretable for unsupported pairs and
  that the importer must check `pairStatus == supported` first.

## Locked-Plan Review Round 9

- Scoped importer idempotence to a fixed enabled backfill target window and
  added the controlled full-reseed rule for backward window expansion after an
  earlier seed.
- Added the ongoing collector freshness contract:
  - after a full sweep, reevaluate after each local-day rollover
  - use the same newest-first catch-up path and pacing rules
- Added the gateway transport-gate pre-execution rule directly to the issue map.
- Closed the stale review-log gap by recording Fresh Adversarial Round 3 Sonnet
  validation as `PASS`.

## Locked-Plan Review Round 10

- Replaced the tautological first-install continuity check with a post-import
  second-snapshot invariant:
  - `today_so_far_after_import`
  - `live_total_after_import`
- Added `yearStatus` to `EnergyHistoryDailyStatus` so software-disabled years
  are explicit and skipped immediately by the importer.
- Reproduced the full `epsilon_seed` invariant and derivation inside chunk 12 so
  the HA/backfill contract remains reviewable in isolation.

## Locked-Plan Review Round 11

- Reworked the end-of-seed continuity proof so it reads back
  `stored_cumulative_after_import` from HA recorder storage instead of
  reusing in-memory imported sums.
- Redefined `daily_round_trip_quantum` on the shared precision path:
  - `B516 float32 Wh`
  - `gateway internal kWh`
  - `serialized JSON float`
  - `HA statistics storage`
- Added the `>= 7 completed current-month days` precondition before the
  published month-scoped coherence tolerance is accepted as representative.
