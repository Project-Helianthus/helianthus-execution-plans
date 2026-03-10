# Energy v1 Execution Plan 03: MCP, GraphQL, Portal, and Home Assistant

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6aa03bced178080e07cf3eb16c7345bece61e7f382069110f1ca8fc7d4f8ca4c`

Depends on:
- [10-source-ownership-and-doc-gates.md](./10-source-ownership-and-doc-gates.md)
- [11-gateway-live-today-and-history.md](./11-gateway-live-today-and-history.md)

Scope: New-capability rollout through `MCP -> GraphQL -> Portal -> HA`, the
daily-history API contract, and the Home Assistant backfill/importer rules.

Idempotence contract: Reapplying this chunk must preserve one completed-day
history contract, one GraphQL parity surface, and one startup backfill path
without duplicating imports or creating synthetic hourly history.

Falsifiability gate: A review fails this chunk if current-day energy leaks into
the history API, if GraphQL skips the MCP stabilization step, if Portal is
skipped as the first consumer, or if first-install backfill can anchor from
non-atomic reads.

Coverage: Sections 5-6 from the source plan.

## MCP Prototype First

- Daily history is a new capability and must appear first as an MCP surface in
  the gateway.
- MCP stabilization must prove:
  - completed-day-only semantics
  - unsupported-pair pruning behavior
  - current-year versus previous-year gating
  - coexistence with live polling under the bounded history budget
  - coverage completion signaling for importer/Portal consumers

## GraphQL Parity

- After MCP freezes, add GraphQL parity:
  - `energyHistoryDaily(channel, usage, year): [EnergyDayPoint!]!`
  - `energyHistoryDailyStatus(channel, usage, year): EnergyHistoryDailyStatus!`
- `EnergyDayPoint` contains:
  - `start`
  - `end`
  - `valueKwh`
- `EnergyHistoryDailyStatus` contains:
  - `pairStatus`
  - `yearStatus`
  - `coverageStart`
  - `coverageEnd`
  - `scanComplete`
  - `daysScanned`
  - `daysExpected`
- Contract rules:
  - `energyHistoryDaily` contains completed days only
  - `energyTotals.today` is the only surface that carries current-day energy
  - the first-install backfill path must be able to read `live_total_now` and
    `today_so_far` from the same GraphQL payload
  - the coverage window for a `(channel, usage, year)` query runs from
    `January 1` of that year to the last completed day in that year
  - for the current year, the last completed day is yesterday
  - for a completed previous year, the last completed day is December 31
  - `daysExpected` is the count of calendar days in that coverage window
  - on January 1 of the current year, `daysExpected=0` and `scanComplete=true`
    trivially because there are no completed days yet
  - `pairStatus` is `supported | unsupported | temporarily_unavailable`
  - `yearStatus` is `enabled | disabled`
  - `yearStatus=disabled` means the requested year is blocked by a software
    gate such as previous-year support still being disabled
  - unsupported pairs do not report `daysExpected=0`; they surface through
    `pairStatus` instead
  - when `pairStatus != supported` or `yearStatus != enabled`,
    `coverageStart`, `coverageEnd`, `daysExpected`, `daysScanned`, and
    `scanComplete` are not interpreted as coverage data
  - `scanComplete` becomes true only when every day in that coverage window has
    been read or confirmed unsupported
  - the importer must key off `energyHistoryDailyStatus.scanComplete` and the
    reported coverage window rather than infer completeness from returned day
    rows
  - the importer must check `pairStatus == supported` and
    `yearStatus == enabled` before evaluating `scanComplete`

## Portal Validation

- Portal is the first consumer of the new GraphQL history capability.
- Energy v1 requires at least one gateway-owned internal validation surface in
  Portal or an equivalent gateway-owned internal consumer before Home Assistant
  adopts the history API.
- The Portal stage exists to validate the capability on the tightest feedback
  loop before the external HA rollout.
- Portal validation passes only if:
  - for at least one supported `(channel, usage, year)` query, Portal shows at
    least seven completed daily values whose `start`/`end` ranges align with
    MCP output for the same query and whose `valueKwh` values match at the same
    source round-trip precision
  - Portal does not render the current day as a completed-history bucket

## Home Assistant Rollout

- Keep the existing energy entities and statistic IDs.
- Keep cumulative `total_increasing` sensors as the public contract.
- Restore same-day local behavior by consuming the corrected gateway
  `energyTotals.today`.
- Add a one-shot startup importer that:
  - reads recorder statistics state
  - fetches missing daily buckets from `energyHistoryDaily`
  - imports only completed days
  - is idempotent on re-run while the enabled backfill target window is fixed

## Backfill Anchor Rules

- If recorder statistics already exist, resume from the last recorder `sum`.
- If recorder statistics do not exist, derive the base cumulative value as:
  - `live_total_now - today_so_far - sum(imported_completed_days)`
- `live_total_now` is the `B524` lifetime/all-time cumulative anchor.
- `today_so_far` is the `B516 day/current-year` intraday value.
- That base is an intentional opaque residual representing all energy before the
  oldest imported day.
- The computed base must satisfy `0 <= base <= live_total_now` or the importer
  aborts with a diagnostic.
- `live_total_now` and `today_so_far` must come from the same atomic gateway
  snapshot or the same GraphQL response payload.
- The first-install path is valid only after the M2/M3 coherence proof confirms
  that `B524_month_current` and the current-month `B516` daily sums agree
  within the documented drift budget.
- The plan does not require a whole-window lifetime-equality proof for the
  imported history seed. The lifetime anchor is trusted through the
  month-scoped proof at the live boundary plus the bounded base invariant and
  end-of-seed continuity check against recorder-stored cumulative data and a
  second fresh live snapshot after import completion.
- The end-of-seed continuity invariant is:
  - `abs((stored_cumulative_after_import + today_so_far_after_import) - live_total_after_import) <= epsilon_seed`
- `epsilon_seed` is derived as:
  - `month_coherence_tolerance + imported_day_count * daily_round_trip_quantum`
- `daily_round_trip_quantum` is a required documented output from
  `ISSUE-DOC-ENERGY-03` alongside the month coherence tolerance, because
  `epsilon_seed` is not computable without it.
- `daily_round_trip_quantum` is defined over the common representation path
  `B516 float32 Wh -> gateway internal kWh -> serialized JSON float -> HA
  statistics storage`.
- Chain imported daily deltas into cumulative sums in chronological order.
- Abort and log on continuity mismatch rather than inventing a best-effort
  anchor.
- The importer does not start from a partial newest-only suffix. It waits until
  `energyHistoryDailyStatus.scanComplete` confirms the full coverage
  window for the enabled backfill target, then sorts that window
  chronologically and imports it as one coherent seed.
- If the enabled backfill target later expands backward after an earlier seed
  (for example when previous-year support is enabled after a current-year-only
  seed already exists), the importer must perform one controlled full reseed for
  the affected statistic IDs instead of attempting an append-only import.
- That full reseed recomputes the base against the expanded window and
  reimports the cumulative series from the oldest enabled completed day.
- After a first-install seed completes, the importer must read back the
  recorder-stored cumulative `sum` for the newest imported completed day before
  evaluating the end-of-seed continuity invariant.
- The importer waits up to a configurable patience window before giving up on
  `scanComplete`; default `6h`.
- For `yearStatus == disabled`, the importer must skip the tuple immediately
  rather than entering the patience-window path.
- If that patience window expires, the importer does not perform a partial seed.
  It logs a diagnostic including `daysScanned`, `daysExpected`, and derived
  coverage percentage, then exits cleanly so a later retry can continue.
- After a patience-window expiry, the importer persists:
  - expiry timestamp
  - observed `daysScanned`
  - observed `daysExpected`
- On a later startup, if the gateway reports the same `(daysScanned,
  daysExpected)` snapshot and less than the cooldown window has elapsed, the
  importer skips the wait entirely and re-emits the persisted diagnostic.
- Default cooldown window after an unchanged stalled scan is `24h`.
- Do not import synthetic hourly history for past days.
- After rollout, Home Assistant generates hourly long-term statistics
  prospectively because the live cumulative sensor now moves intraday from
  `B516`.
