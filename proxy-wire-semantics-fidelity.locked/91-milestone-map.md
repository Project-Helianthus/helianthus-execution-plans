# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | Spec lock, docs lock, harness scaffolding (no proxy behavior changes) | `helianthus-execution-plans`, `helianthus-docs-ebus` | none | active |
| `M1` | Immediate correctness fixes (`stale STARTED`, `SYN-while-waiting`) | `helianthus-ebus-adapter-proxy` | `M0` | queued |
| `M2` | Boundary-based initiator arbitration rounds | `helianthus-ebus-adapter-proxy` | `M1` | queued |
| `M3` | Minimal direct-mode phase tracker | `helianthus-ebus-adapter-proxy` | `M2` | queued |
| `M4` | Local target emulation core and timing contract | `helianthus-ebus-adapter-proxy`, `helianthus-docs-ebus` | `M3` | queued |
| `M5` | Matrix/smoke/proof updates (`PX01..PX12`) | `helianthus-ebus-adapter-proxy`, `helianthus-docs-ebus` | `M4` | queued |
| `M6` | ESERA passive validation follow-up | `helianthus-docs-ebus`, `helianthus-execution-plans` | `M5` (advisory only) | deferred |

## Ordering Rules

- Hard execution order: `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
- `M6` is explicitly deferred and non-blocking for code milestones.
- One issue per repo at a time remains the lane rule.
- Doc-gate applies to every transport/protocol behavior change.
- `PROXY-01` and `PROXY-02` are allowed to land before scheduler redesign.
- `PROXY-06` must not be marketed as strict timing proof for generic
  child-backed responders before `FOLLOWUP-01` evidence exists.
