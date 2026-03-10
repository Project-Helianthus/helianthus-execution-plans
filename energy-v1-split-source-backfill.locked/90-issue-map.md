# Issue Map

This plan uses canonical issue identifiers inside the split chunks. GitHub
issue numbers may be created later in the target repositories, but the
canonical IDs below remain the stable mapping surface for the plan itself.

Status legend:
- `planned`: defined in the plan, GitHub issue not yet linked here
- `active`: current execution focus
- `blocked`: depends on earlier milestone completion

## M0

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-DOC-ENERGY-01` | `helianthus-docs-ebus` | Add energy source-ownership ADR and update `energy-merge.md` | active |
| `ISSUE-DOC-ENERGY-02` | `helianthus-docs-ebus` | Update `B516`, `B524`, and GraphQL docs with current-year and previous-year gates | active |

## M1

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-01` | `helianthus-ebusgateway` | Remove `B524` day zero-lock and restore `energyTotals.today` from `B516 day/current-year` | blocked |
| `ISSUE-GW-ENERGY-02` | `helianthus-ebusgateway` | Add bounded `B516` daily-history collector with runtime pair pruning and pacing limits | blocked |

Ordering rule:
- `ISSUE-GW-ENERGY-02` depends on `ISSUE-GW-ENERGY-01` merging first, unless
  both land in one atomic PR on the same code path.

## M2

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-03` | `helianthus-ebusgateway` | Ship MCP daily-history prototype with capability, gating, and the same-poll-cycle read path needed for cross-source coherence measurement | blocked |
| `ISSUE-DOC-ENERGY-03` | `helianthus-docs-ebus` | Freeze MCP contract, own live coherence measurement results, and document the measured tolerance | blocked |

Ownership rule:
- `ISSUE-DOC-ENERGY-03` owns publication of the live
  `B524_month_current ~= sum(B516_completed_days_this_month) + B516_today`
  measurement and the resulting tolerance constant.
- `ISSUE-GW-ENERGY-04` stays blocked until that publication is complete.

## M3

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-04` | `helianthus-ebusgateway` | Add GraphQL `energyHistoryDaily` parity and atomic anchor-read contract | blocked |
| `ISSUE-GW-ENERGY-05` | `helianthus-ebusgateway` | Add Portal or gateway-owned internal validation surface for daily history | blocked |
| `ISSUE-DOC-ENERGY-04` | `helianthus-docs-ebus` | Freeze GraphQL and Portal validation contract | blocked |

Ordering rule:
- `ISSUE-GW-ENERGY-05` depends on `ISSUE-GW-ENERGY-04` merging first.

## M4

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-HA-ENERGY-01` | `helianthus-ha-integration` | Align HA live energy behavior with corrected gateway `today` semantics | blocked |
| `ISSUE-HA-ENERGY-02` | `helianthus-ha-integration` | Add one-shot startup backfill importer using long-term statistics import | blocked |
| `ISSUE-DOC-ENERGY-05` | `helianthus-docs-ebus` | Publish HA rollout, backfill, and proof expectations | blocked |

Blocking rule:
- `ISSUE-HA-ENERGY-02` stays blocked until both of these are complete:
  - `ISSUE-DOC-ENERGY-03` publishes the coherence measurement and tolerance
  - `ISSUE-GW-ENERGY-04` and `ISSUE-GW-ENERGY-05` complete GraphQL parity and
    Portal validation

## M5

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-ENERGY-06` | `helianthus-ebusgateway` | Enforce previous-year hard gate and maintenance cleanup after proof decision | blocked |
| `ISSUE-DOC-ENERGY-06` | `helianthus-docs-ebus` | Publish previous-year validation evidence or current-year-only maintenance note | blocked |
