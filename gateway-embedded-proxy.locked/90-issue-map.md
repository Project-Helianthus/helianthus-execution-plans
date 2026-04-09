# Issue Map

This plan is anchored on one EPIC and a fixed cross-repo issue set.

Status legend:
- `planned`: issue not yet created on GitHub
- `active`: current execution focus
- `merged-main`: implementation lane landed in local `main` history
- `deferred`: intentionally postponed and non-blocking

## EPIC Root

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `EPIC-GATEWAY-EMBEDDED-PROXY` | `helianthus-execution-plans` | TBD | planned |

## M0

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PLAN-01` | `helianthus-execution-plans` | TBD | Canonical execution-plan package | planned |
| `DOC-01` | `helianthus-docs-ebus` | TBD | Architecture doc + AD01..AD12 definitions | planned |

## M1

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-01` | `helianthus-ebusgateway` | TBD | Adapter multiplexer core + arbitration + echo suppression | planned |

## M2

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-02` | `helianthus-ebusgateway` | TBD | Active + passive path integration | planned |

## M3

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-03` | `helianthus-ebusgateway` | TBD | External proxy endpoint with full master access | planned |

## M4

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `HA-01` | `helianthus-ha-addon` | TBD | Addon config + migration | planned |
| `DOC-02` | `helianthus-docs-ebus` | TBD | Migration + rollback documentation | planned |

## M5

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-04` | `helianthus-ebusgateway` | TBD | Matrix validation + E2E evidence | planned |
| `DOC-03` | `helianthus-docs-ebus` | TBD | AD01..AD12 evidence documentation | planned |

## Ordering Rules

- All issues are planned, none yet created on GitHub.
- Issue numbers (TBD) must be assigned before execution begins.
- M0 must complete before any code milestone.
- M2 and M3 depend on M1 but are independent of each other.
- M4 depends on M2 + M3.
- M5 depends on M2 + M3 + M4.
- One issue per repo at a time.
- Doc-gate applies to every transport/protocol behavior change.
