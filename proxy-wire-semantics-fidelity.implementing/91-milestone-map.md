# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | Spec lock, docs lock, harness scaffolding (no proxy behavior changes) | `helianthus-execution-plans`, `helianthus-docs-ebus` | none | reconciling |
| `M1` | Immediate correctness fixes (`stale STARTED`, `SYN-while-waiting`) | `helianthus-ebus-adapter-proxy` | `M0` | merged-main |
| `M2` | Boundary-based initiator arbitration rounds | `helianthus-ebus-adapter-proxy` | `M1` | merged-main |
| `M3` | Minimal direct-mode phase tracker | `helianthus-ebus-adapter-proxy` | `M2` | merged-main |
| `M4` | Local target emulation core and timing contract | `helianthus-ebus-adapter-proxy`, `helianthus-docs-ebus` | `M3` | merged-main |
| `M5` | Matrix/smoke/proof updates (`PX01..PX12`) | `helianthus-ebus-adapter-proxy`, `helianthus-docs-ebus` | `M4` | merged-main |
| `M6` | ESERA passive validation follow-up | `helianthus-docs-ebus`, `helianthus-execution-plans` | `M5` (advisory only) | deferred |

## Ordering Rules

- Hard execution order remains: `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- `M6` is explicitly deferred and non-blocking for code milestones.
- `M0` remains open only for plan-lane reconciliation (`PLAN-01`).
- One issue per repo at a time remains the lane rule.
- Doc-gate applies to every transport/protocol behavior change.
- `PROXY-06` must not be marketed as strict timing proof for generic
  child-backed responders before `FOLLOWUP-01` evidence exists.
