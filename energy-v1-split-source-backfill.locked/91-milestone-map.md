# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | docs lock, ADR, and source-ownership freeze | `helianthus-docs-ebus` | none | locked-ready |
| `M1` | gateway semantic correction and bounded collector groundwork | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M0` | queued |
| `M2` | MCP-first daily-history prototype | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M1` | queued |
| `M3` | GraphQL parity and Portal validation | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M2` | queued |
| `M4` | HA rollout and startup backfill | `helianthus-ha-integration`, `helianthus-docs-ebus` | `M3` | queued |
| `M5` | previous-year gate decision, final validation, maintenance | `helianthus-docs-ebus`, `helianthus-ebusgateway`, `helianthus-ha-integration` | `M4` | queued |

## Ordering Rules

- The default order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- Existing-surface correction for `energyTotals.today` and the new daily-history
  capability are distinct tracks under the same plan.
- Daily history must still follow `MCP -> GraphQL -> Portal -> HA` before the HA
  consumer adopts the new API.
- Locked decisions in [00-canonical.md](./00-canonical.md) override milestone
  shorthand if drift appears here.
