# Energy v1 Locked-Plan Review Log

This file captures adversarial review for the execution-plan repo version of the
Energy v1 plan.

Process:

1. Opus reviews the locked-plan artifacts adversarially.
2. Codex updates the locked-plan files.
3. Codex records each substantive plan delta in `98-changelog.md`.
4. Sonnet validates that the requested deltas were implemented.
5. Repeat until convergence.

## Bootstrap State

- Source material imported from:
  - `/Users/razvan/Desktop/Helianthus Project/Energy v1.md`
  - `/Users/razvan/Desktop/Helianthus Project/Energy v1 changelog.md`
  - `/Users/razvan/Desktop/Helianthus Project/Energy v1 review log.md`
- New canonical home:
  - `energy-v1-split-source-backfill.locked/`
- Initial review status:
  - pending first Opus pass on the locked-plan artifact set

## Round 1 - Opus Review

### Findings

- `P2` The pacing rule exposed two equivalent limits without precedence.
- `P2` The backfill anchor formula assumed arithmetic coherence between `B524`
  lifetime totals and `B516` daily sums without a proof gate.
- `P2` The M1 issue map did not declare that the history collector depends on
  the `today` source-fix issue.
- `P2` The gateway precedence proof was not described as a concrete test
  procedure.
- `P3` Portal validation existed as a stage but not as a falsifiable gate.
- `P3` The milestone map listed gateway as a primary M4 repo without a matching
  M4 gateway issue.
- `P3` The importer did not declare whether partial newest-first history windows
  are importable.

### Changes Applied

- Added pacing precedence and lower-rate-wins language.
- Added a cross-source coherence proof gate and tied tolerance selection to the
  measured drift.
- Added the explicit `ISSUE-GW-ENERGY-02 -> ISSUE-GW-ENERGY-01` ordering rule.
- Added a named precedence test for nonzero `B516 today` surviving a `B524`
  refresh.
- Added a falsifiable Portal validation minimum.
- Declared that HA backfill waits for the full contiguous completed-day window
  of the enabled target instead of importing partial newest-only windows.
- Removed gateway from the M4 primary repo list in `91-milestone-map.md`.

## Round 1 - Sonnet Validation

- Verdict: `PASS`

## Round 2 - Opus Review

### Findings

- `P2` The `147 minutes` value was really a theoretical floor, not a true
  worst-case ceiling, because the collector yields to live polling.
- `P2` The importer needed an explicit completion signal instead of inferring a
  full contiguous window from day rows alone.
- `P2` The cross-source coherence gate still needed explicit ownership in the
  issue map and an explicit dependency from `ISSUE-HA-ENERGY-02`.
- `P3` The base anchor needed to be described as an intentional residual and
  guarded against negative values.
- `P3` The HA same-day proof gate needed an explicit latency target and
  measurement rule.

### Changes Applied

- Reframed `147 minutes` as the theoretical minimum full-surface sweep time and
  made the lack of a hard upper bound explicit.
- Added `energyHistoryDailyStatus` and made the importer wait on
  `scanComplete` plus the reported coverage window.
- Assigned coherence-proof publication and tolerance ownership to
  `ISSUE-DOC-ENERGY-03` and kept `ISSUE-HA-ENERGY-02` blocked on it.
- Declared the base anchor to be an intentional opaque residual and required it
  to be non-negative.
- Replaced the vague HA same-day proof with a one-poll-cycle sensor-state rule
  plus next-hourly-rollup statistics rule.

## Round 2 - Sonnet Validation

- Verdict: `PASS`

## Round 3 - Opus Review

### Findings

- `P3` The sweep-volume sentence was duplicated in the canonical and gateway
  chunks.
- `P2` The plan still needed the explicit register/source mapping for
  `live_total_now` and `today_so_far`.
- `P2` The coherence-proof sequencing rule needed to block GraphQL parity until
  publication completed.
- `P2` The issue-map blocking rule for `ISSUE-HA-ENERGY-02` needed to live in
  the M4 section where implementers would actually look for it.
- `P3` Portal "match" semantics needed to be made exact.

### Changes Applied

- Removed the duplicate sweep-volume lines.
- Declared `live_total_now` as the `B524` lifetime/all-time anchor and
  `today_so_far` as the `B516 day/current-year` intraday value.
- Added the sequencing rule that `ISSUE-DOC-ENERGY-03` must publish the
  coherence measurement and tolerance before `ISSUE-GW-ENERGY-04` begins.
- Moved the `ISSUE-HA-ENERGY-02` blocking rule to the M4 section and tied it to
  the coherence and GraphQL/Portal gates.
- Tightened Portal validation so "match" now means aligned date ranges and
  source-precision `valueKwh` equality.

## Round 3 - Sonnet Validation

- Verdict: `PASS`

## Round 4 - Opus Review

### Findings

- `P2` The issue map still needed the explicit `ISSUE-GW-ENERGY-05 ->
  ISSUE-GW-ENERGY-04` ordering rule inside M3.
- `P2` The coherence measurement still lacked a clear M2 gateway owner for the
  same-poll-cycle read path that makes the measurement trustworthy.

### Changes Applied

- Added the explicit M3 ordering rule that Portal validation depends on GraphQL
  parity merging first.
- Expanded `ISSUE-GW-ENERGY-03` so M2 now owns the same-poll-cycle read path
  required for the live coherence measurement.

## Round 4 - Sonnet Validation

- Verdict: `PASS`

## Round 5 - Opus Review

### Findings

- `P1` The lifetime coherence formula was structurally invalid because the plan
  only backfills a bounded history window while the lifetime anchor includes all
  prior years.
- `P2` The plan still needed an explicit definition of the history coverage
  window and the condition that makes `scanComplete` true.

### Changes Applied

- Replaced the lifetime coherence formula with a month-scoped proof that is
  testable with current-year `B516` data and `B524` current-month totals.
- Defined the coverage window and `scanComplete` transition explicitly in the
  canonical plan and GraphQL contract.

## Round 5 - Sonnet Validation

- Verdict: `PASS`

## Round 6 - Opus Convergence Check

- Verdict: `NO_MATERIAL_FINDINGS`
- No further plan text changes were required.

## Fresh Migration Fidelity Check - Sonnet

- Verdict: `MIGRATION_PASS`

## Fresh Adversarial Round 1 - Opus Review

### Findings

- `P2` The importer needed explicit behavior when `scanComplete` never arrives.
- `P2` `ISSUE-GW-ENERGY-03` still needed a less ambiguous summary so the
  gateway coherence-measurement read path could not slip out of scope.
- `P2` The lifetime anchor needed a clearer trust chain because the coherence
  proof is only month-scoped.
- `P3` The gateway chunk needed to restate that the per-minute cap is derived at
  current values and must be recalculated if changed.
- `P3` The same-day latency gate needed to be phrased at the gateway surface,
  not as an HA visibility guarantee.

### Changes Applied

- Added a configurable `scanComplete` patience window with explicit diagnostic
  behavior and no implicit partial import.
- Extended `EnergyHistoryDailyStatus` with progress counters.
- Clarified the lifetime-anchor trust chain and tightened the base bound to
  `0 <= base <= live_total_now`.
- Rewrote the pacing note so the current equality and future recalculation rule
  are explicit.
- Reframed same-day latency to the gateway `energyTotals.today` surface.
- Rewrote `ISSUE-GW-ENERGY-03` to make the coherence-measurement read path a
  hard deliverable.

## Fresh Adversarial Round 1 - Sonnet Validation

- Verdict: `PASS`

## Fresh Adversarial Round 2 - Opus Review

### Findings

- `P2` The end-of-seed continuity check still needed an explicit numeric
  invariant and tolerance rule.
- `P2` The collector needed a restart-safe progress contract or the importer
  could starve forever under restarts.
- `P3` `daysExpected` still needed an exact definition for edge cases and
  unsupported pairs.

### Changes Applied

- Defined the end-of-seed continuity invariant and the derived `epsilon_seed`
  contract.
- Made collector progress restart-safe and tied it to the gateway collector
  issue scope.
- Defined `daysExpected`, January 1 semantics, and the unsupported-pair rule.

## Fresh Adversarial Round 2 - Sonnet Validation

- Verdict: `PASS`

## Fresh Adversarial Round 3 - Opus Review

### Findings

- `P2` The importer still needed a cooldown rule after repeated patience-window
  expiry on unchanged stalled scans.
- `P2` The M2 -> M3 gate from `ISSUE-DOC-ENERGY-03` to `ISSUE-GW-ENERGY-04`
  needed to be explicit in the issue map itself, not only in the plan prose.
- `P3` The restart-safe collector cursor still needed exact semantics so newly
  completed days are not skipped after restart.
- `P3` `EnergyHistoryDailyStatus` still needed a concrete GraphQL field to
  represent unsupported pairs.

### Changes Applied

- Added a persisted cooldown after unchanged stalled scans.
- Made the `ISSUE-DOC-ENERGY-03 -> ISSUE-GW-ENERGY-04` dependency explicit in
  the M2 and M3 issue-map rules.
- Defined the restart-safe collector cursor semantics.
- Added `pairStatus` to `EnergyHistoryDailyStatus`.

## Fresh Adversarial Round 3 - Sonnet Validation

- Verdict: `PASS`

## Fresh Adversarial Round 4 - Opus Review

### Findings

- `P2` `ISSUE-HA-ENERGY-01` was over-serialized behind the full
  `MCP -> GraphQL -> Portal -> HA` pipeline even though it only consumes the
  corrected existing `energyTotals.today` surface.
- `P2` `ISSUE-DOC-ENERGY-04` needed an explicit dependency on
  `ISSUE-GW-ENERGY-05` so the doc freeze happens after Portal validation.
- `P2` `daily_round_trip_quantum` needed explicit ownership as a required output
  so `epsilon_seed` is computable.
- `P3` `ISSUE-DOC-ENERGY-03` needed an explicit dependency on
  `ISSUE-GW-ENERGY-03` merging first.
- `P3` The M1 milestone map needed to be consistent with the new placement of
  `ISSUE-HA-ENERGY-01`.
- `P3` The `pairStatus != supported` contract still needed to make
  `scanComplete` non-interpretable and to require the importer to check
  `pairStatus == supported` first.

### Changes Applied

- Moved `ISSUE-HA-ENERGY-01` into the existing-surface M1 track and clarified
  that only `ISSUE-HA-ENERGY-02` is blocked on the full new-capability
  pipeline.
- Added the `ISSUE-DOC-ENERGY-04 -> ISSUE-GW-ENERGY-05` ordering rule.
- Assigned `daily_round_trip_quantum` explicitly to `ISSUE-DOC-ENERGY-03`.
- Added the `ISSUE-DOC-ENERGY-03 -> ISSUE-GW-ENERGY-03` dependency.
- Aligned the M1 milestone map with the issue map.
- Clarified that `scanComplete` is non-interpretable when
  `pairStatus != supported` and that the importer checks `pairStatus` first.

## Fresh Adversarial Round 4 - Sonnet Validation

- Verdict: `PASS`

## Fresh Adversarial Round 5 - Opus Review

### Findings

- `P2` The importer needed an explicit backward-range-expansion contract for the
  case where previous-year enablement widens the backfill window after an
  earlier current-year-only seed.
- `P2` The issue map needed to carry the transport-gate pre-execution
  obligation for the gateway issues, not only the plan prose.
- `P3` The locked review log still left Fresh Adversarial Round 3 Sonnet
  validation pending.
- `P3` The collector still needed an explicit ongoing freshness trigger so newly
  completed days enter `energyHistoryDaily` without restart.

### Changes Applied

- Scoped importer idempotence to a fixed enabled target window and added the
  controlled full-reseed rule for backward range expansion.
- Added a gateway pre-execution transport-gate rule to the issue map.
- Marked Fresh Adversarial Round 3 Sonnet validation as `PASS`.
- Added the post-sweep daily rollover reevaluation rule for the history
  collector in canonical plus gateway chunk.

## Fresh Adversarial Round 5 - Sonnet Validation

- Verdict: `PASS`

## Fresh Adversarial Round 6 - Opus Review

### Findings

- `P1` The first-install end-of-seed continuity check was tautological because
  it reused the same snapshot from which `base` was derived.
- `P2` `EnergyHistoryDailyStatus` lacked a year-level software-gate signal, so a
  disabled previous year could look like a stalled scan.
- `P2` Chunk 12 referenced `epsilon_seed` without reproducing the invariant and
  derivation needed for isolated review.

### Changes Applied

- Moved the continuity check onto a second fresh post-import snapshot and
  updated the trust chain accordingly.
- Added `yearStatus` to `EnergyHistoryDailyStatus` and required the importer to
  skip disabled years instead of entering the patience loop.
- Reproduced the full `epsilon_seed` invariant and derivation in chunk 12.

## Fresh Adversarial Round 6 - Sonnet Validation

- Verdict: `PASS`

## Fresh Adversarial Round 7 - Opus Review

### Findings

- `P1` The end-of-seed continuity check still had algebraic cancellation, so the
  `imported_day_count * daily_round_trip_quantum` tolerance term had no real
  error source.
- `P2` `daily_round_trip_quantum` still referenced GraphQL even though the value
  must be published before the GraphQL milestone exists.
- `P3` The month-scoped coherence measurement still lacked a minimum completed
  day count before a final tolerance could be accepted as representative.

### Changes Applied

- Moved the continuity check onto recorder-stored cumulative data read back from
  HA plus a second fresh live snapshot after import completion.
- Redefined `daily_round_trip_quantum` on the common representation path
  `B516 float32 Wh -> gateway internal kWh -> serialized JSON float -> HA
  statistics storage`.
- Added the `>= 7 completed current-month days` minimum before the published
  coherence tolerance is accepted as representative.

## Fresh Adversarial Round 7 - Sonnet Validation

- Verdict: `PASS`

## Fresh Adversarial Round 8 - Opus Convergence Check

- Verdict: `NO_MATERIAL_FINDINGS`

## Fresh Adversarial Round 8 - Sonnet Convergence Validation

- Verdict: `PASS`
- No remaining implementation deltas found.
