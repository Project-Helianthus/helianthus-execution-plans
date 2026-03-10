# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | locked-plan import, docs-repo sanitation, and downstream issue scaffolding | `helianthus-execution-plans`, `helianthus-docs-ebus` | none | active |
| `M1` | entrypoints, naming, and navigation | `helianthus-docs-ebus` | `M0` | queued |
| `M2` | protocol-boundary surgery | `helianthus-docs-ebus` | `M1` | queued |
| `M3` | API, timer, and terminology alignment | `helianthus-docs-ebus` | `M2` | queued |
| `M4` | proof sweep and maintenance handoff | `helianthus-docs-ebus` | `M3` | queued |

## Ordering Rules

- The default order is `M0 -> M1 -> M2 -> M3 -> M4`.
- `M0` ends only when the locked import merges and the canonical plan URL can be
  referenced from downstream issues and PRs.
- `M0` also requires the sanitation pass to reconcile and remove the stale and
  objective-equivalent remote branches named in `ISSUE-DOC-00`.
- Locked decisions in `00-canonical.md` override milestone shorthand in this
  file if drift appears.
