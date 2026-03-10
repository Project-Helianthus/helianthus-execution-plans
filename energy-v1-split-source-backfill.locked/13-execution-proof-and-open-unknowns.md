# Energy v1 Execution Plan 04: Execution, Proof, and Open Unknowns

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `17af2e502f3e5588be52f7b0355743cd0840834d434b810de76f97471c3a58f3`

Depends on:
- [10-source-ownership-and-doc-gates.md](./10-source-ownership-and-doc-gates.md)
- [11-gateway-live-today-and-history.md](./11-gateway-live-today-and-history.md)
- [12-mcp-graphql-portal-ha.md](./12-mcp-graphql-portal-ha.md)

Scope: Milestone order, proof gates, execution sequencing, and residual unknowns
that must remain explicit during implementation.

Idempotence contract: Reapplying this chunk must preserve the same milestone
order, the same proof gates, and the same explicit unknowns rather than letting
them collapse into silent assumptions.

Falsifiability gate: A review fails this chunk if it allows HA rollout before
MCP/GraphQL/Portal stages, hides unresolved proof dependencies, or treats
current-year-only shipment as a failure when previous-year proof is absent.

Coverage: Sections 7-9 from the source plan.

## Milestone Order

- `M0`: documentation and ADR lock, issue creation, source-ownership freeze
- `M1`: gateway semantic correction for `today` plus bounded `B516` collector
  groundwork
- `M2`: MCP prototype for daily history and capability surfacing
- `M3`: GraphQL parity plus Portal validation surface
- `M4`: Home Assistant rollout and startup backfill importer
- `M5`: previous-year proof gate decision, final validation, and maintenance

Default order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.

Additional sequencing rule:

- `ISSUE-DOC-ENERGY-03` must publish the coherence measurement and tolerance
  before `ISSUE-GW-ENERGY-04` begins GraphQL parity work.

## Proof Gates

### Docs and Semantics

- Docs agree on period ownership before code merges.
- `architecture/decisions.md` and `architecture/energy-merge.md` say the same
  thing about `B516` versus `B524`.
- `B516` docs distinguish current-year support from previous-year gated support.

### Gateway

- `B524` refresh no longer forces `today=0`.
- `B516 today` survives later `B524` refreshes.
- Named precedence test:
  - establish a nonzero `B516 today`
  - trigger or wait for a `B524` refresh cycle
  - assert the `today` surface remains on the `B516` value afterward
- History reads obey pacing and priority rules.
- Unsupported pairs are pruned after one negative probe per run.
- Valid `0 kWh` days remain valid data.
- Previous-year reads stay disabled until doc proof lands.
- Cross-source coherence is proven on live hardware before first-install
  backfill is enabled:
  - `B524_month_current ~= sum(B516_completed_days_this_month) + B516_today`
  - measured drift sets the anchor tolerance

### Home Assistant

- Startup backfill imports only missing completed days.
- Re-running startup backfill is a no-op.
- Imported cumulative history stays continuous with the live total.
- First-install anchoring reads `live_total_now` and `today_so_far` from the
  same payload.
- Current day is excluded from completed-history import.
- Same-day usage reaches the HA energy sensor state within one full semantic
  poll cycle after the gateway applies the updated `B516 day` reading.
- HA hourly long-term statistics pick up that intraday movement in the next
  hourly rollup.

## Residual Unknowns That Stay Explicit

- If atomic `live_total_now` plus `today_so_far` reads cannot be produced, first
  install backfill must stop rather than continue with split reads.
- If no bus-idle heuristic exists, fixed pacing remains mandatory.
- If previous-year `B516` proof fails, current-year-only backfill still ships.
- The minimum supported Home Assistant version floor still needs to be written.
- The anchor mismatch tolerance constant still needs to be chosen explicitly.
