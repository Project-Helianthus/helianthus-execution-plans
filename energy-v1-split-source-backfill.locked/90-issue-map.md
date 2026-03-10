# Issue Map

This plan uses canonical issue identifiers inside the split chunks. GitHub
issue numbers may be created later in the target repositories, but the
canonical IDs below remain the stable mapping surface for the plan itself.

Status legend:
- `planned`: defined in the plan, GitHub issue not yet linked here
- `active`: current execution focus
- `blocked`: depends on earlier milestone completion

Gateway pre-execution rule:
- Every `ISSUE-GW-ENERGY-*` checklist must resolve transport-gate applicability
  before implementation begins.
- At minimum, `ISSUE-GW-ENERGY-01` and `ISSUE-GW-ENERGY-02` must do this when
  they lock the active `B516` read path.

## M0

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-DOC-ENERGY-01` | `helianthus-docs-ebus` | Add energy source-ownership ADR and update `energy-merge.md` | active |
| `ISSUE-DOC-ENERGY-02` | `helianthus-docs-ebus` | Update `B516`, `B524`, and GraphQL docs with current-year and previous-year gates | active |

## M1

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-01` | `helianthus-ebusgateway` | Remove `B524` day zero-lock and restore `energyTotals.today` from `B516 day/current-year` | blocked |
| `ISSUE-GW-ENERGY-02` | `helianthus-ebusgateway` | Add bounded `B516` daily-history collector with runtime pair pruning, pacing limits, and restart-safe scan progress | blocked |
| `ISSUE-HA-ENERGY-01` | `helianthus-ha-integration` | Align HA live energy behavior with corrected gateway `today` semantics | blocked |

Ordering rule:
- `ISSUE-GW-ENERGY-02` depends on `ISSUE-GW-ENERGY-01` merging first, unless
  both land in one atomic PR on the same code path.
- `ISSUE-HA-ENERGY-01` depends only on `ISSUE-GW-ENERGY-01` and may begin as
  soon as that gateway correction merges; it is not blocked by the new
  daily-history pipeline.

## M2

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-03` | `helianthus-ebusgateway` | Ship the MCP daily-history prototype and the same-poll-cycle coherence-measurement read path as one hard-deliverable gateway issue | blocked |
| `ISSUE-DOC-ENERGY-03` | `helianthus-docs-ebus` | Freeze MCP contract, own live coherence measurement results, document the measured tolerance, and publish `daily_round_trip_quantum` for `epsilon_seed` | blocked |

Ownership rule:
- `ISSUE-DOC-ENERGY-03` depends on `ISSUE-GW-ENERGY-03` merging first because
  the coherence measurement must use the production same-poll-cycle read path.
- `ISSUE-DOC-ENERGY-03` owns publication of the live
  `B524_month_current ~= sum(B516_completed_days_this_month) + B516_today`
  measurement, the resulting tolerance constant, and
  `daily_round_trip_quantum`.
- `ISSUE-GW-ENERGY-04` stays blocked until that publication is complete.
- `ISSUE-GW-ENERGY-03` merging alone does not unblock `ISSUE-GW-ENERGY-04`.
  Only `ISSUE-DOC-ENERGY-03` publication does.

## M3

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-04` | `helianthus-ebusgateway` | Add GraphQL `energyHistoryDaily` parity and atomic anchor-read contract | blocked |
| `ISSUE-GW-ENERGY-05` | `helianthus-ebusgateway` | Add Portal or gateway-owned internal validation surface for daily history | blocked |
| `ISSUE-DOC-ENERGY-04` | `helianthus-docs-ebus` | Freeze GraphQL and Portal validation contract | blocked |

Ordering rule:
- `ISSUE-GW-ENERGY-05` depends on `ISSUE-GW-ENERGY-04` merging first.
- `ISSUE-GW-ENERGY-04` remains blocked until `ISSUE-DOC-ENERGY-03` publishes
  the coherence measurement and tolerance.
- `ISSUE-DOC-ENERGY-04` depends on `ISSUE-GW-ENERGY-05` completing Portal
  validation first so the frozen contract reflects the validated surface.

## M4

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-HA-ENERGY-02` | `helianthus-ha-integration` | Add one-shot startup backfill importer using long-term statistics import | blocked |
| `ISSUE-DOC-ENERGY-05` | `helianthus-docs-ebus` | Publish HA rollout, backfill, and proof expectations | blocked |

Blocking rule:
- `ISSUE-HA-ENERGY-02` stays blocked until both of these are complete:
  - `ISSUE-DOC-ENERGY-03` publishes the coherence measurement and tolerance
  - `ISSUE-GW-ENERGY-04` and `ISSUE-GW-ENERGY-05` complete GraphQL parity and
    Portal validation
- If previous-year enablement later expands the backfill target behind an
  existing current-year-only seed, `ISSUE-HA-ENERGY-02` must perform the
  controlled full reseed defined in the canonical importer contract.

## M5

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-06` | `helianthus-ebusgateway` | Enforce previous-year hard gate and maintenance cleanup after proof decision | blocked |
| `ISSUE-DOC-ENERGY-06` | `helianthus-docs-ebus` | Publish previous-year validation evidence or current-year-only maintenance note | blocked |
