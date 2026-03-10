# Energy v1: Split-Source Today, Daily History, and HA Backfill

Revision: `v1.0-lock-import`
Date: `2026-03-10`
Status: `Locked bootstrap import`

## Summary

- This plan is a cross-repo energy correction and rollout plan.
- It fixes same-day local energy behavior, adds bounded local daily history, and
  backfills Home Assistant from validated `B516` daily totals.
- It does not promise local historical hourly energy or instantaneous power
  draw.
- The source model is intentionally split by period:
  - `B516 day/current-year` owns `today so far` and completed daily history.
  - `B524` aggregate registers own `this month`, `last month`, and the
    lifetime/all-time anchor.
- The plan explicitly rejects `B516 primary for everything with B524 fallback`
  because the sources are not equivalent.
- The plan distinguishes two workstreams:
  1. correction of existing `energyTotals.today` behavior
  2. introduction of a new local daily-history capability
- Existing-surface correction may ship as gateway semantic work once docs are
  aligned.
- The new daily-history capability must follow
  `MCP prototype -> GraphQL parity -> Portal validation -> HA rollout`.
- Delivery order across repos is strict:
  1. `helianthus-docs-ebus`
  2. `helianthus-ebusgateway`
  3. `helianthus-ha-integration`
- Transport-gate applicability is not pre-judged here. Each concrete gateway
  issue must decide it in the pre-execution checklist once the exact active
  `B516` read path is fixed.

## 1. Evidence and Uncertainty

### 1.1 Proven

- `B516` exposes day/month/year/system selectors and returns energy values in
  `Wh` as `float32`.
- `B524` exposes register-backed cumulative energy counters in `kWh` for month
  and lifetime-style aggregate views.
- The current local rollout behaves like a previous-day-only experience because
  `today` is not being refreshed from the day-level source that can move
  intraday.
- Home Assistant Energy Dashboard fundamentally needs cumulative energy in
  `kWh`, plus recorder/statistics continuity for backfill. It does not require
  a live `W` or `kW` register to accept energy history.

### 1.2 Hypothesis

- The hourly history visible in myVaillant is not yet proven to map to a
  validated local eBUS source available to Helianthus today.
- Bounded active `B516 day` reads are sufficient to restore same-day local
  behavior without destabilizing normal semantic polling, provided they remain
  below the explicit history budget in this plan.

### 1.3 Unknown

- A validated local instantaneous power register in `W` or `kW`.
- Whether previous-year `B516 day` reads are valid on the target hardware.
- Whether the gateway can rely on a bus-idle or backlog heuristic for history
  pacing on every transport/profile combination.
- The minimum Home Assistant version floor that must be written into rollout
  docs for the statistics-import path.
- The exact anchor mismatch tolerance value to enforce at implementation time.
  That value must be derived from live cross-source coherence measurement rather
  than chosen arbitrarily.

## 2. Adversarially Locked Decisions

### 2.1 Source Ownership and Precedence

- `B516 day/current-year` is the source of truth for:
  - `today so far`
  - completed daily history
  - prospective hourly Home Assistant statistics after rollout
- `B524` is the source of truth for:
  - `this month`
  - `last month`
  - lifetime/all-time anchor
- `B524` must not suppress, zero-lock, or overwrite the `B516` day-owned
  `today` surface.
- Consumers must not treat `B516` and `B524` as interchangeable fallback
  sources across periods.
- `B524` remains in scope for Energy v1. It is not removed from the energy
  stack in this plan.

### 2.2 Same-Day and Hourly Boundary

- Energy v1 promises same-day local energy updates and prospective hourly Home
  Assistant statistics after rollout.
- Energy v1 does not promise historical hourly backfill because no validated
  local hourly source exists in the current proof set.
- Current-day values remain live/intraday data, not completed history.

### 2.3 Daily History Contract

- Daily history is a completed-day surface only.
- The current day must not appear in the daily-history API.
- The current day remains exclusively on `energyTotals.today`.
- The current year is in scope immediately.
- Previous-year daily history is hard-disabled until hardware proof is merged
  into `helianthus-docs-ebus`.

### 2.4 Backfill Contract

- The backfill importer is one-shot at startup, idempotent, and imports only
  missing completed days.
- It does not rewrite sensor state history.
- It imports long-term statistics, not synthetic hourly rows.
- If recorder statistics already exist, the importer resumes from the last
  recorder `sum`.
- If recorder statistics do not exist, the importer derives the base cumulative
  value as:
  - `live_total_now - today_so_far - sum(imported_completed_days)`
- `live_total_now` is the `B524` lifetime/all-time cumulative anchor.
- `today_so_far` is the `B516 day/current-year` intraday value.
- `live_total_now` and `today_so_far` must come from the same atomic gateway
  snapshot or the same GraphQL payload.
- The first-install anchor formula is valid only if live hardware proves that
  the `B524` lifetime anchor and the `B516` day totals are arithmetically
  coherent within a documented drift budget.
- The importer must abort and log if reconstructed continuity does not match the
  live anchor within the configured tolerance.

### 2.5 Scope Boundary

- Discovery of a generic live power-draw register in `W` or `kW` is explicitly
  out of scope for this plan.
- Proving a native local hourly history source is also out of scope for Energy
  v1. If such a source is found later, it becomes Energy v2 or a follow-up
  track.

## 3. Documentation and ADR Contract

- This plan hits these doc-gates:
  - `architecture change`
  - `semantic behavior change`
  - `RE-derived protocol knowledge`
  - `GraphQL parity / consumer contract change`
- It does not require a new FSM document unless implementation introduces an
  explicit energy-history lifecycle state machine.
- `helianthus-docs-ebus` must gain an explicit architectural decision for
  energy source ownership and precedence. The rule is:
  - `B516 day` owns intraday and daily-history semantics
  - `B524` owns month/lifetime aggregate semantics
  - `B524` must not suppress `B516 today`
  - the two sources are complementary, not generic fallbacks
- The following docs must be updated before or alongside code:
  - `architecture/decisions.md`
  - `architecture/energy-merge.md`
  - `protocols/ebus-vaillant-B516-energy.md`
  - `protocols/ebus-vaillant-B524-register-map.md`
  - `api/graphql.md`

## 4. Gateway Contract

### 4.1 Existing-Surface Semantic Correction

- The gateway must remove the current `B524`-driven `day=0` lock behavior.
- `energyTotals.today` must be fed from active `B516 day/current-year` reads.
- Existing aggregate surfaces remain compatible:
  - `this month`
  - `last month`
  - lifetime/all-time anchor
- That compatibility layer exists to avoid breaking the current Home Assistant
  consumer while source ownership is corrected under it.

### 4.2 B516 Daily-History Collector

- The gateway adds a bounded daily-history collector for published energy pairs.
- Published pair count in scope is six:
  - `gas/climate`
  - `gas/dhw`
  - `electric/climate`
  - `electric/dhw`
  - `solar/climate`
  - `solar/dhw`
- The effective scan set is discovered at runtime:
  - each candidate pair is probed once at the start of a history run
  - pairs that return protocol-level unsupported or unavailable responses are
    pruned from the remainder of that run
  - valid `0 kWh` daily values remain in scope and are not treated as
    unsupported
- History collection is not part of the hot startup path.
- History collection starts only after semantic startup is complete and normal
  live polling is stable.
- Collector progress is restart-safe:
  - the gateway persists scan progress per `(channel, usage, year)` tuple
  - the persisted cursor is a pair:
    - `previous_run_newest_completed_day`
    - `oldest_scanned_day`
  - on restart, the collector first scans any newly completed days in
    `(previous_run_newest_completed_day, current_newest_completed_day]`
  - after catching up the newer suffix, the collector resumes the backward walk
    from the day immediately older than `oldest_scanned_day`
  - persisted progress is cleared only when the scan completes or the run is
    invalidated by a configuration/capability change
- After a full history sweep completes, the collector must schedule a periodic
  follow-up run so newly completed days enter `energyHistoryDaily` without
  requiring a gateway restart.
- The minimum v1 contract is one reevaluation after each local-day rollover for
  supported tuples, using the same newest-first catch-up path and pacing rules.
- Pacing contract:
  - primary controlling limit: `1 request / 2s`
  - derived sanity-check cap at the current v1 setting: `30 requests / minute`
  - scheduling priority below the normal semantic poller
  - if a bus-idle or backlog heuristic exists, the collector may use it
  - if no such heuristic exists, the fixed pacing above is the controlling limit
- If implementation later exposes separate pacing and per-minute caps, the lower
  effective rate wins.
- Worst-case two-year scan volume at full surface is:
  - `366 days x 2 years x 6 pairs = 4392 requests`
- That worst case applies only when all six published pairs are actually
  supported by the current hardware profile.
- Theoretical minimum full-surface sweep time at sustained maximum rate is
  about `147 minutes`.
- Because the collector is lower priority than live polling, the plan does not
  promise a hard upper bound on sweep completion time. Downstream consumers must
  tolerate longer collection windows.
- Read order is newest completed days first, then backward.

### 4.3 Previous-Year Gate

- Previous-year daily reads are guarded by a hard-disabled flag such as
  `b516PreviousYearEnabled = false`.
- That flag may be flipped only after validation evidence is merged into
  `protocols/ebus-vaillant-B516-energy.md`.

### 4.4 Cross-Source Coherence Gate

- Before Home Assistant first-install backfill is accepted, live hardware must
  validate:
  - `B524_month_current ~= sum(B516_completed_days_this_month) + B516_today`
- The measured drift budget from that proof becomes the anchor mismatch
  tolerance.
- That proof is representative only after at least `7` completed days exist in
  the current month.
- If fewer than `7` completed days exist, the measurement may be exploratory,
  but it must not unlock first-install backfill or publish a final tolerance.
- This proof is month-scoped on purpose. Energy v1 does not attempt a
  lifetime-versus-history equality check because the imported history window is
  intentionally bounded while the lifetime anchor is not.
- If the proof fails, the plan may still ship same-day updates and
  current-year-only history surfaces, but first-install backfill must remain
  disabled until the month-scoped mismatch is understood and documented.

## 5. New Capability Pipeline: MCP, GraphQL, Portal

### 5.1 MCP Prototype First

- The new daily-history capability must appear first as an MCP surface in the
  gateway.
- The MCP surface must expose ordered completed-day buckets for
  `(channel, usage, year)` plus enough capability status to explain rejected,
  unavailable, or not-yet-complete requests.
- MCP is the stabilization surface for:
  - completed-day-only semantics
  - unsupported-pair pruning behavior
  - current-year versus previous-year gating
  - proof that the history collector can coexist with live polling
  - explicit coverage completion signaling

### 5.2 GraphQL Parity

- After the MCP contract is frozen, the gateway adds GraphQL parity:
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
- For a `(channel, usage, year)` query, the coverage window is defined as:
  - `January 1` of the requested year through the last completed day in that
    year
  - for the current year, the last completed day is yesterday
  - for a completed previous year, the last completed day is December 31
- `scanComplete` becomes true only when every day in that coverage window has
  been read or confirmed unsupported for the active hardware/profile.
- `daysExpected` is the count of calendar days in the coverage window.
- For the current year on January 1, `daysExpected=0` and `scanComplete=true`
  trivially because there are no completed days yet.
- `pairStatus` is `supported | unsupported | temporarily_unavailable`.
- `yearStatus` is `enabled | disabled`.
- `yearStatus=disabled` means the requested year is blocked by a software gate
  such as previous-year support still being disabled.
- Unsupported pairs do not report `daysExpected=0`; they surface through
  `pairStatus` instead.
- When `pairStatus != supported` or `yearStatus != enabled`, `coverageStart`,
  `coverageEnd`, `daysExpected`, `daysScanned`, and `scanComplete` are not
  interpreted as coverage data.
- GraphQL must keep `energyTotals.today` and the daily-history surface
  semantically distinct:
  - `energyTotals.today` is the only place where current-day energy appears
  - `energyHistoryDaily` contains completed days only
- The GraphQL path used for first-install HA anchoring must let
  `live_total_now` and `today_so_far` be read from the same response payload.

### 5.3 Portal Validation

- Portal is the first consumer of the new GraphQL history capability.
- Energy v1 requires at least one internal validation surface in Portal or an
  equivalent gateway-owned internal consumer before Home Assistant adopts the
  new history API.
- The purpose of the Portal stage is not feature parity with myVaillant. Its job
  is to prove the new capability on the tightest feedback loop before the
  external HA rollout.
- Portal validation is not satisfied by an empty view. The minimum falsifiable
  acceptance rule is:
  - for at least one supported `(channel, usage, year)` query, Portal must show
    at least seven completed daily values whose `start`/`end` ranges align with
    MCP output for the same query and whose `valueKwh` values match at the same
    source round-trip precision
  - Portal must not render the current day as a completed-history bucket

## 6. Home Assistant Rollout

- The Home Assistant integration keeps the existing energy entity model and
  statistic IDs.
- Cumulative `total_increasing` sensors remain the public contract.
- Gateway correction of `energyTotals.today` restores same-day local behavior
  without requiring a new HA entity model.
- The integration adds a one-shot startup importer that:
  - reads recorder statistics state
  - fetches missing daily buckets from `energyHistoryDaily`
  - imports only completed days
  - is idempotent on re-run while the enabled backfill target window is fixed
- The importer rules are:
  - if statistics already exist, resume from the last recorder `sum`
  - if statistics do not exist, compute the base cumulative anchor from
    `live_total_now - today_so_far - sum(imported_completed_days)`
  - `live_total_now` is the `B524` lifetime/all-time cumulative anchor
  - `today_so_far` is the `B516 day/current-year` intraday value
  - that base is an intentional opaque residual representing all energy before
    the oldest imported day
  - the computed base must satisfy `0 <= base <= live_total_now` or the
    importer aborts with a diagnostic
  - chain imported day totals into cumulative sums in chronological order
  - abort and log on continuity mismatch
- The plan does not require a whole-window lifetime-equality proof for the
  imported history seed. The lifetime anchor is trusted through:
  - the month-scoped coherence proof at the live boundary
  - the bounded base invariant `0 <= base <= live_total_now`
  - the end-of-seed continuity check against recorder-stored cumulative data and
    a second fresh live snapshot after import completion
- The end-of-seed continuity invariant is:
  - `abs((stored_cumulative_after_import + today_so_far_after_import) - live_total_after_import) <= epsilon_seed`
- `epsilon_seed` is derived as:
  - `month_coherence_tolerance + imported_day_count * daily_round_trip_quantum`
- `daily_round_trip_quantum` is the maximum single-day error introduced by the
  common representation path `B516 float32 Wh -> gateway internal kWh ->
  serialized JSON float -> HA statistics storage` and must be documented when
  the tolerance is published.
- The integration does not create synthetic past-hour rows.
- The importer does not seed from a partial newest-only history suffix. It waits
  until `energyHistoryDailyStatus.scanComplete` confirms the full coverage
  window for the enabled backfill target, then sorts that window
  chronologically and imports it as one coherent seed.
- The importer evaluates `scanComplete` only for tuples where
  `pairStatus == supported` and `yearStatus == enabled`.
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
- For `yearStatus == disabled`, the importer must skip the tuple immediately
  rather than entering the patience-window path.
- Home Assistant creates hourly long-term statistics prospectively after rollout
  because the live cumulative sensor now moves intraday from `B516`.

## 7. Validation and Proof Gates

### 7.1 Docs and Semantics

- Docs must agree on period ownership before code is merged.
- The energy ADR and `energy-merge.md` must say the same thing about `B516`
  versus `B524`.
- `B516` docs must distinguish current-year daily support from previous-year
  gated support.

### 7.2 Gateway

- `B524` refreshes no longer force `today=0`.
- `B516 today` survives later `B524` refreshes.
- A named gateway acceptance test must prove source precedence:
  - establish a nonzero `B516 today`
  - trigger or wait for a `B524` refresh cycle
  - assert that the `today` surface still reports the `B516`-owned value
- The history collector obeys its pacing and priority rules.
- Unsupported pairs are pruned after their first negative capability probe in a
  run.
- Valid `0 kWh` days remain valid data.
- Previous-year reads stay disabled until the doc proof gate is satisfied.
- Cross-source coherence is proven before first-install backfill is enabled:
  - `B524_month_current ~= sum(B516_completed_days_this_month) + B516_today`
  - measured drift sets the anchor tolerance

### 7.3 Home Assistant

- Startup backfill imports only missing completed days.
- A second startup pass is a no-op.
- The imported cumulative series remains continuous with the live total.
- First-install anchoring uses one atomic gateway payload for `live_total_now`
  and `today_so_far`.
- Current day is not imported as completed history.
- After rollout, the gateway `energyTotals.today` surface reflects the updated
  `B516 day` value within one semantic poll cycle.
- HA-side observability then follows the integration's own refresh cadence; the
  consumer rollout issues own that exact client-side latency rather than this
  plan's gateway contract.

## 8. Milestone Order

- `M0`: documentation and ADR lock, issue creation, source-ownership freeze
- `M1`: gateway semantic correction for `today` plus bounded `B516` collector
  groundwork, plus the HA live-`today` alignment on the existing
  `energyTotals.today` surface
- `M2`: MCP prototype for daily history and capability surfacing
- `M3`: GraphQL parity plus Portal validation surface
- `M4`: Home Assistant new-capability rollout and startup backfill importer
- `M5`: previous-year proof gate decision, final validation, and maintenance

The default order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.

Additional sequencing rule:

- `ISSUE-HA-ENERGY-01` may begin after `ISSUE-GW-ENERGY-01` because it consumes
  the corrected existing `energyTotals.today` surface rather than the new
  daily-history API.
- `ISSUE-DOC-ENERGY-03` depends on `ISSUE-GW-ENERGY-03` merging first because
  the coherence measurement must exercise the production same-poll-cycle read
  path.
- `ISSUE-DOC-ENERGY-03` must publish the coherence measurement and tolerance
  before `ISSUE-GW-ENERGY-04` begins GraphQL parity work.

## 9. Residual Unknowns That Must Stay Visible

- If implementation cannot produce atomic `live_total_now` plus `today_so_far`
  reads from one payload, first-install backfill must stop rather than invent a
  best-effort anchor.
- If the gateway has no bus-idle heuristic, the fixed pacing contract remains
  mandatory rather than advisory.
- If previous-year `B516` proof fails, Energy v1 still ships with current-year
  backfill only.
- If a local hourly source is later proven, that becomes a new plan rather than
  an implicit extension of this one.
