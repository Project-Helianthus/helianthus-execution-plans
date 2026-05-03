# Milestone Map

Lifecycle state: `maintenance`. All primary milestones are complete; open
evidence packaging remains maintenance follow-up.

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | Spec lock, architecture doc, AD01..AD12 definitions | `helianthus-execution-plans`, `helianthus-docs-ebus` | none | active |
| `M1` | Adapter multiplexer core: connection, arbitration, echo suppression, wire phase | `helianthus-ebusgateway` | `M0` | merged-main |
| `M2` | Gateway active + passive path integration, config flag, transport resolution | `helianthus-ebusgateway` | `M1` | merged-main |
| `M3` | External proxy endpoint: TCP listener, full master, session management | `helianthus-ebusgateway` | `M1` | merged-main |
| `M4` | HA addon config, migration documentation, rollback contract | `helianthus-ha-addon`, `helianthus-docs-ebus` | `M2`, `M3` | merged-main |
| `M5` | Matrix validation (AD01..AD12), E2E evidence, regression (T01..T88) | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M2`, `M3`, `M4` | active |

## Ordering Rules

- Hard execution order: `M0 -> M1 -> {M2, M3} -> M4 -> M5`.
- M2 and M3 are independent of each other but both depend on M1. They may
  execute in parallel if one-issue-per-repo is satisfied (both target
  `helianthus-ebusgateway`, so they must be sequential in practice unless
  split into separate issues that can be interleaved).
- One issue per repo at a time remains the lane rule.
- Doc-gate applies to every transport/protocol behavior change.
- Transport-gate: T01..T88 regression for any transport-affecting PR.
- AD01..AD12 gate for adapter-direct PRs.
