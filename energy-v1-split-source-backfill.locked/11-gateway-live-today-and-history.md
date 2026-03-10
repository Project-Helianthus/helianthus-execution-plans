# Energy v1 Execution Plan 02: Gateway Live Today and Daily History

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `17af2e502f3e5588be52f7b0355743cd0840834d434b810de76f97471c3a58f3`

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

## Pacing and Bus Budget

- Fixed pacing contract:
  - primary controlling limit: `1 request / 2s`
  - derived sanity-check cap at the current v1 setting: `30 requests / minute`
  - lower priority than the normal semantic poller
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
- This proof is month-scoped on purpose because the backfill window is bounded
  while the lifetime anchor is not.
- If the proof fails, same-day updates and daily history may still ship, but
  first-install backfill stays disabled until the mismatch is explained and
  documented.
