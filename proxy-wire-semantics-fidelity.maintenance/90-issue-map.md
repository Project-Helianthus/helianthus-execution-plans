# Issue Map

This plan is anchored on one EPIC and a fixed cross-repo issue set.

Status legend:
- `merged-main`: implementation lane landed in local `main` history
- `active`: current execution focus
- `reconciling`: implementation exists, but plan-layer closure/reconciliation is pending
- `deferred`: intentionally postponed and non-blocking

## EPIC Root

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `EPIC-PROXY-WIRE-SEMANTICS` | `helianthus-execution-plans` | `Project-Helianthus/helianthus-execution-plans#5` | active |

## M0

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PLAN-01` | `helianthus-execution-plans` | `#6` | Canonical execution-plan package | reconciling |
| `DOC-01` | `helianthus-docs-ebus` | `#238` | Wire-semantics decision doc | merged-main |

## M1

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-01` | `helianthus-ebus-adapter-proxy` | `#85` | Stale `STARTED` absorb | merged-main |
| `PROXY-02` | `helianthus-ebus-adapter-proxy` | `#86` | `SYN-while-waiting` timeout boundary | merged-main |

## M2

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-03` | `helianthus-ebus-adapter-proxy` | `#87` | Arbitration rounds at boundaries | merged-main |

## M3

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-04` | `helianthus-ebus-adapter-proxy` | `#88` | Minimal direct-mode phase tracker | merged-main |

## M4

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-05` | `helianthus-ebus-adapter-proxy` | `#89` | Session initiator learning | merged-main |
| `DOC-02` | `helianthus-docs-ebus` | `#239` | Local target timing contract | merged-main |
| `PROXY-06` | `helianthus-ebus-adapter-proxy` | `#90` | Local target responder window | merged-main |

## M5

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `TEST-01-DOCS` | `helianthus-docs-ebus` | `#240` | Matrix docs and proof contract updates | merged-main |
| `TEST-01-PROXY` | `helianthus-ebus-adapter-proxy` | `#91` | Proxy matrix/smoke implementation updates | merged-main |

## M6 (deferred)

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `FOLLOWUP-01-DOCS` | `helianthus-docs-ebus` | `#241` | ESERA passive validation package (docs lane) | deferred |
| `FOLLOWUP-01-PLAN` | `helianthus-execution-plans` | `#7` | ESERA passive validation package (plan lane) | deferred |

## Ordering Rules

- `M0` is partially complete: docs lane landed, plan lane still reconciling.
- `M1` (`PROXY-01`, `PROXY-02`) are completed implementation lanes.
- `M2` through `M5` are completed implementation lanes.
- `M6` remains non-blocking for `M0-M5`.
