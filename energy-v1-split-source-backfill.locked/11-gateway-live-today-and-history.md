# Energy v1 Execution Plan 02: Gateway Live Today and Daily History

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6aa03bced178080e07cf3eb16c7345bece61e7f382069110f1ca8fc7d4f8ca4c`

Depends on: [10-source-ownership-and-doc-gates.md](./10-source-ownership-and-doc-gates.md).
Gateway behavior in this chunk is invalid unless the source-ownership and
doc-gate rules are accepted first.

Scope: Gateway semantic correction for `energyTotals.today`, bounded `B516`
daily-history collection, unsupported-pair pruning, and the previous-year gate.

Idempotence contract: Reapplying this chunk must preserve a single `today`
owner, a single bounded history collector, and one active previous-year gate.

Falsifiability gate: A review fails this chunk if `today` can still be forced to
zero by `B524`, if history reads are unbounded, if valid `0 kWh` days are
mistaken for unsupported pairs, or if previous-year enablement lacks a hard
gate.

Coverage: Section 4 from the source plan.

## Existing-Surface Semantic Correction

- Remove the current `B524`-driven `day=0` lock behavior.
- Feed `energyTotals.today` from active `B516 day/current-year` reads.
- Keep existing aggregate compatibility from `B524` for:
  - `this month`
  - `last month`
  - lifetime/all-time anchor
- This correction is existing-surface semantic work, not the new history
  capability itself.

## B516 Daily-History Collector

- Add a bounded daily-history collector for the six published channel/usage
  pairs:
  - `gas/climate`
  - `gas/dhw`
  - `electric/climate`
  - `electric/dhw`
  - `solar/climate`
  - `solar/dhw`
- Runtime scan-set discovery is mandatory:
  - probe each candidate pair once at the start of a history run
  - prune pairs that return protocol-level unsupported or unavailable responses
  - keep valid `0 kWh` daily values in scope
- History collection is background work only:
  - not part of the hot startup path
  - starts only after semantic startup is complete and live polling is stable
- Collector progress is restart-safe:
  - persist scan progress per `(channel, usage, year)` tuple
  - the persisted cursor is a pair:
    - `previous_run_newest_completed_day`
    - `oldest_scanned_day`
  - on restart, first scan any newly completed days in
    `(previous_run_newest_completed_day, current_newest_completed_day]`
  - after catching up the newer suffix, resume the backward walk from the day
    immediately older than `oldest_scanned_day`
  - clear persisted progress only when the scan completes or the run is
    invalidated by a configuration/capability change
- After a full history sweep completes, schedule a periodic follow-up run so
  newly completed days enter `energyHistoryDaily` without requiring restart.
- The minimum v1 contract is one reevaluation after each local-day rollover for
  supported tuples, using the same newest-first catch-up path and pacing rules.

## Pacing and Bus Budget

- Fixed pacing contract:
  - primary controlling limit: `1 request / 2s`
  - derived sanity-check cap at the current v1 setting: `30 requests / minute`
  - lower priority than the normal semantic poller
- At current values the two limits are the same rate; if either is changed, the
  other must be recalculated or the lower effective rate wins.
- If the gateway has a bus-idle or backlog heuristic, the collector may use it.
- If the gateway has no such heuristic, the fixed pacing above remains the
  controlling limit.
- If implementation later exposes separate pacing and per-minute caps, the
  lower effective rate wins.
- Worst-case full-surface scan volume is:
  - `366 days x 2 years x 6 pairs = 4392 requests`
- That figure applies only when all six published pairs are actually supported
  by the current hardware profile.
- Theoretical minimum full sweep time at sustained maximum rate is about
  `147 minutes`.
- Because the collector yields to live polling, the plan does not promise a
  hard upper bound on completion time.
- Read newest completed days first, then walk backward.

## Previous-Year Gate

- Previous-year daily history is hard-disabled by a flag such as
  `b516PreviousYearEnabled = false`.
- The flag may flip only after validation evidence is merged into
  `protocols/ebus-vaillant-B516-energy.md`.
- If previous-year proof never lands, Energy v1 still ships with current-year
  support only.

## Cross-Source Coherence Gate

- First-install HA backfill requires live hardware proof that:
  - `B524_month_current ~= sum(B516_completed_days_this_month) + B516_today`
- The measured drift budget from that proof becomes the backfill anchor
  tolerance.
- That proof is representative only after at least `7` completed days exist in
  the current month.
- If fewer than `7` completed days exist, the measurement may be exploratory,
  but it must not unlock first-install backfill or publish a final tolerance.
- This proof is month-scoped on purpose because the backfill window is bounded
  while the lifetime anchor is not.
- If the proof fails, same-day updates and daily history may still ship, but
  first-install backfill stays disabled until the mismatch is explained and
  documented.
