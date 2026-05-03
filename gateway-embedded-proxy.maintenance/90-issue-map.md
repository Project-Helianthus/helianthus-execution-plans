# Issue Map

Lifecycle state: `maintenance`. Execution-plan issue #11 is closed; remaining
formal evidence packaging is tracked as maintenance follow-up, not active
implementation.

This plan is anchored on one EPIC and a fixed cross-repo issue set.

Status legend:
- `planned`: issue not yet created on GitHub
- `active`: current execution focus
- `reconciling`: plan/doc reconciliation in progress
- `merged-main`: implementation lane landed in local `main` history
- `deferred`: intentionally postponed and non-blocking

## EPIC Root

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `EPIC-GATEWAY-EMBEDDED-PROXY` | `helianthus-execution-plans` | [#11](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/11) | planned |

## M0

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PLAN-01` | `helianthus-execution-plans` | [#11](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/11) | Canonical execution-plan package | reconciling |
| `DOC-01` | `helianthus-docs-ebus` | [#248](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/248) | Architecture doc + AD01..AD12 definitions | active |

## M1

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-01` | `helianthus-ebusgateway` | [#472](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/472) (merged) | Adapter multiplexer core + arbitration + echo suppression | merged-main (PR #472) |

## M2

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-02` | `helianthus-ebusgateway` | [#472](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/472) (merged) | Active + passive path integration | merged-main (PR #472) |

## M3

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-03` | `helianthus-ebusgateway` | [#472](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/472) (merged) | External proxy endpoint with full master access | merged-main (PR #472) |

## M4

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `HA-01` | `helianthus-ha-addon` | [#117](https://github.com/Project-Helianthus/helianthus-ha-addon/issues/117) (merged) | Addon config + migration | merged-main (PR #117) |
| `DOC-02` | `helianthus-docs-ebus` | [#249](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/249) | Migration + rollback documentation | active |

## M5

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `GW-04` | `helianthus-ebusgateway` | [#476](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/476) | Matrix validation + E2E evidence | active |
| `DOC-03` | `helianthus-docs-ebus` | [#250](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/250) | AD01..AD12 evidence documentation | active |

## Ordering Rules

- M0 must complete before M5 can be declared done.
- M2 and M3 depend on M1 but are independent of each other.
- M4 depends on M2 + M3.
- M5 depends on M2 + M3 + M4.
- One issue per repo at a time.
- Doc-gate applies to every transport/protocol behavior change.
