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
