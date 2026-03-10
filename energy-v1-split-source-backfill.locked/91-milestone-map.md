# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | docs lock, ADR, and source-ownership freeze | `helianthus-docs-ebus` | none | locked-ready |
| `M1` | gateway semantic correction, HA live-`today` alignment, and bounded collector groundwork | `helianthus-ebusgateway`, `helianthus-ha-integration` | `M0` | queued |
| `M2` | MCP-first daily-history prototype | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M1` | queued |
| `M3` | GraphQL parity and Portal validation | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M2` | queued |
| `M4` | HA new-capability rollout and startup backfill | `helianthus-ha-integration`, `helianthus-docs-ebus` | `M3` | queued |
| `M5` | previous-year gate decision, final validation, maintenance | `helianthus-docs-ebus`, `helianthus-ebusgateway`, `helianthus-ha-integration` | `M4` | queued |

## Ordering Rules

- The default order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- Existing-surface correction for `energyTotals.today` and the new daily-history
  capability are distinct tracks under the same plan.
- `ISSUE-HA-ENERGY-01` belongs to the existing-surface track and may begin after
  `ISSUE-GW-ENERGY-01`; only `ISSUE-HA-ENERGY-02` is blocked on the full
  `MCP -> GraphQL -> Portal -> HA` new-capability pipeline.
- Daily history must still follow `MCP -> GraphQL -> Portal -> HA` before the HA
  consumer adopts the new API.
- Locked decisions in [00-canonical.md](./00-canonical.md) override milestone
  shorthand if drift appears here.
