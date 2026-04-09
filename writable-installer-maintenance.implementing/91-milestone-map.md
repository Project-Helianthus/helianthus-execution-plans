# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | Docs lane for B524 + B509 installer/maintenance registers | `helianthus-docs-ebus` | none | merged |
| `M1A` | B524 probe evidence lane (operator notebook) | -- | none | unarchived |
| `M1B` | B509 probe evidence lane (operator notebook) | -- | none | unarchived |
| `M2` | B524 gateway lane: aggregated fields + writer wiring + GraphQL/MCP | `helianthus-ebusgateway` | `M0`, `M1A` | merged |
| `M3` | B509 gateway lane: menu code/phone write + service read-only + GraphQL/MCP | `helianthus-ebusgateway` | `M0`, `M1B`, `M2` | merged |
| `M4a` | HA system lane: optional queries + text/date entities | `helianthus-ha-integration` | `M2` | merged |
| `M4b` | HA boiler lane: phone/menu code text + service sensor | `helianthus-ha-integration` | `M3`, `M4a` | merged |
| `M4r` | Plan reconciliation lane (canonical/status/issue-map sync) | `helianthus-execution-plans` | `M0..M4b` | active |

## Ordering Rules

- Default order remains `M0 -> M1 -> M2 -> M3 -> M4`.
- `M1A` and `M1B` are independent.
- M2 and M3 are merged in a single gateway execution commit (`c9c8f59`) but
  remain separate logical milestones for traceability.
- Canonical design corrections apply:
  - aggregated controller fields (`installerName`, `installerPhone`),
  - menu code entities in `text.py`,
  - boiler phone as digit-string UX with BCD wire encoding,
  - no required `internal/configwrite/` extraction milestone.

## PR / Execution Strategy

| Milestone | Repo | Execution anchor | Depends On |
| --- | --- | --- | --- |
| `M0` | `helianthus-docs-ebus` | commit `7c4fc5a` (`WIM-M0`) | -- |
| `M1A` | -- | probe artifact backfill pending | -- |
| `M1B` | -- | probe artifact backfill pending | -- |
| `M2` | `helianthus-ebusgateway` | commit `c9c8f59` (`WIM-M2+M3`) | `M0`, `M1A` |
| `M3` | `helianthus-ebusgateway` | commit `c9c8f59` (`WIM-M2+M3`) | `M0`, `M1B`, `M2` |
| `M4a` | `helianthus-ha-integration` | commit `7c818c6` (`WIM-M4`) | `M2` |
| `M4b` | `helianthus-ha-integration` | commit `7c818c6` (`WIM-M4`) | `M3`, `M4a` |
| `M4r` | `helianthus-execution-plans` | this reconciliation cycle | `M0..M4b` |

## Proof Matrix

| Claim | Status | Blocks |
| --- | --- | --- |
| Controller installer/maintenance GraphQL + mutation surface exists | Proven | -- |
| Boiler installer/service GraphQL surface exists | Proven | -- |
| MCP `system.set_config` exists with parity/classification coverage | Proven | -- |
| MCP `boiler_status.set_config` exists with parity/classification coverage | Proven | -- |
| HA optional-query backward-compat architecture exists | Proven | -- |
| `hoursTillService` is read-only in HA surface | Proven | -- |
| Probe artifacts (M1A/M1B) are archived in plan repo | Unarchived | close `M4r` |

## Risks

| # | Risk | Severity | Mitigation | Status |
| --- | --- | --- | --- | --- |
| 1 | Missing archived probe artifacts for M1A/M1B | HIGH | Backfill artifacts or record explicit waiver | OPEN |
| 2 | Residual docs wording drift vs aggregated controller field API | MEDIUM | Final doc consistency pass in reconciliation lane | OPEN |
| 3 | Plan metadata drift from merged code after further iterations | MEDIUM | Keep `M4r` active until maps/status stay aligned | OPEN |
| 4 | Sensitive menu code exposure | MEDIUM | Keep hidden+disabled defaults + separate sensitive queries | MITIGATED |
| 5 | Stale post-write values | MEDIUM | Writer path patch+publish already in merged gateway lane | MITIGATED |

