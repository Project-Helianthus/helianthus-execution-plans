# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | Build pipeline: toolchain, static path, Lovelace resource, hello card | `helianthus-ha-integration` | none | locked-ready |
| `M1` | Card 1: Burner Hydraulics — full SVG, entity mapping, animations | `helianthus-ha-integration` | `M0` | queued |
| `M2` | Card 2: System Hydraulics — topology-adaptive rendering | `helianthus-ha-integration` | `M1` | queued |
| `M3` | Polish: visual refinement, picker preview, docs, bundle gate | `helianthus-ha-integration` | `M2` | queued |

## Ordering Rules

- The default order is `M0 -> M1 -> M2 -> M3`.
- M0 must prove the full artifact pipeline (build, serve, register, render)
  before any card implementation begins.
- M1 (Card 1) is simpler and proves the SVG rendering patterns and shared
  utilities. M2 (Card 2) builds on these.
- M3 is polish only — both cards must be functionally complete before M3.
- Locked decisions in [00-canonical.md](./00-canonical.md) override milestone
  shorthand if drift appears here.
