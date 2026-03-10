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
