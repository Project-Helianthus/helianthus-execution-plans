# Energy v1 Execution Plan 03: MCP, GraphQL, Portal, and Home Assistant

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `17af2e502f3e5588be52f7b0355743cd0840834d434b810de76f97471c3a58f3`

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
  - `coverageStart`
  - `coverageEnd`
  - `scanComplete`
- Contract rules:
  - `energyHistoryDaily` contains completed days only
  - `energyTotals.today` is the only surface that carries current-day energy
  - the first-install backfill path must be able to read `live_total_now` and
    `today_so_far` from the same GraphQL payload
  - the coverage window for a `(channel, usage, year)` query runs from
    `January 1` of that year to the last completed day in that year
  - for the current year, the last completed day is yesterday
  - for a completed previous year, the last completed day is December 31
  - `scanComplete` becomes true only when every day in that coverage window has
    been read or confirmed unsupported
  - the importer must key off `energyHistoryDailyStatus.scanComplete` and the
    reported coverage window rather than infer completeness from returned day
    rows

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
  - is idempotent on re-run

## Backfill Anchor Rules

- If recorder statistics already exist, resume from the last recorder `sum`.
- If recorder statistics do not exist, derive the base cumulative value as:
  - `live_total_now - today_so_far - sum(imported_completed_days)`
- `live_total_now` is the `B524` lifetime/all-time cumulative anchor.
- `today_so_far` is the `B516 day/current-year` intraday value.
- That base is an intentional opaque residual representing all energy before the
  oldest imported day.
- The computed base must be non-negative or the importer aborts with a
  diagnostic.
- `live_total_now` and `today_so_far` must come from the same atomic gateway
  snapshot or the same GraphQL response payload.
- The first-install path is valid only after the M2/M3 coherence proof confirms
  that `B524_month_current` and the current-month `B516` daily sums agree
  within the documented drift budget.
- Chain imported daily deltas into cumulative sums in chronological order.
- Abort and log on continuity mismatch rather than inventing a best-effort
  anchor.
- The importer does not start from a partial newest-only suffix. It waits until
  `energyHistoryDailyStatus.scanComplete` confirms the full coverage
  window for the enabled backfill target, then sorts that window
  chronologically and imports it as one coherent seed.
- Do not import synthetic hourly history for past days.
- After rollout, Home Assistant generates hourly long-term statistics
  prospectively because the live cumulative sensor now moves intraday from
  `B516`.
