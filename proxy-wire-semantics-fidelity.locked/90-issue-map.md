# Issue Map

This plan is anchored on one EPIC and a fixed cross-repo issue set.

Status legend:
- `planned`: defined and linked
- `active`: current execution focus
- `blocked`: depends on prior milestone
- `deferred`: intentionally postponed and non-blocking

## EPIC Root

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `EPIC-PROXY-WIRE-SEMANTICS` | `helianthus-execution-plans` | `Project-Helianthus/helianthus-execution-plans#5` | active |

## M0

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PLAN-01` | `helianthus-execution-plans` | `#6` | Canonical execution-plan package | active |
| `DOC-01` | `helianthus-docs-ebus` | `#238` | Wire-semantics decision doc | active |

## M1

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-01` | `helianthus-ebus-adapter-proxy` | `#85` | Stale `STARTED` absorb | blocked |
| `PROXY-02` | `helianthus-ebus-adapter-proxy` | `#86` | `SYN-while-waiting` timeout boundary | blocked |

## M2

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-03` | `helianthus-ebus-adapter-proxy` | `#87` | Arbitration rounds at boundaries | blocked |

## M3

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-04` | `helianthus-ebus-adapter-proxy` | `#88` | Minimal direct-mode phase tracker | blocked |

## M4

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `PROXY-05` | `helianthus-ebus-adapter-proxy` | `#89` | Session initiator learning | blocked |
| `DOC-02` | `helianthus-docs-ebus` | `#239` | Local target timing contract | blocked |
| `PROXY-06` | `helianthus-ebus-adapter-proxy` | `#90` | Local target responder window | blocked |

## M5

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `TEST-01-DOCS` | `helianthus-docs-ebus` | `#240` | Matrix docs and proof contract updates | blocked |
| `TEST-01-PROXY` | `helianthus-ebus-adapter-proxy` | `#91` | Proxy matrix/smoke implementation updates | blocked |

## M6 (deferred)

| Canonical ID | Repo | GitHub issue | Summary | Status |
| --- | --- | --- | --- | --- |
| `FOLLOWUP-01-DOCS` | `helianthus-docs-ebus` | `#241` | ESERA passive validation package (docs lane) | deferred |
| `FOLLOWUP-01-PLAN` | `helianthus-execution-plans` | `#7` | ESERA passive validation package (plan lane) | deferred |

## Ordering Rules

- `M0` must complete before any `M1` execution.
- `M1` (`PROXY-01`, `PROXY-02`) may run in sequence under one-repo lane rules.
- `M2` depends on both `PROXY-01` and `PROXY-02`.
- `M3` depends on `M2`.
- `M4` depends on `M3`.
- `M5` depends on `M4`.
- `M6` is non-blocking for `M0-M5`.
