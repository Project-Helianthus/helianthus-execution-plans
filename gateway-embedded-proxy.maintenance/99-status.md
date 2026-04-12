# Status

State: `maintenance`

## Current Position

- M1-M3 merged on gateway main via PR #472 (6abc083)
- PR #473 merged (Init consumer + P0 fixes)
- PR #474 merged (P3 observer continuity)
- PR #481 merged (INFO cache + ArbitrationSendsSource for active path)
- Final fix merged (proxy listener startup + ReadByte timeout) — fd296cf
- M4 merged on ha-addon main via PR #117
- ebusgo PRs #126 + #127 merged (Init return + StreamEvent)
- M0 doc-gate closed: docs-ebus `architecture/adapter-direct-multiplexer.md`
  and `architecture/overview.md` updated with v0.4.0 transport modes
- M5 live validation complete: v0.4.0 running live on production hardware
  with verified results (scan=4, B524=coherent, zones=2, dhw=true, INFO=7)

## Closure Note

All milestones (M0-M5) are now complete. The gateway-embedded adapter
multiplexer is deployed and running on production hardware. The plan
transitions to `.maintenance` as of 2026-04-11.

Key outcomes:
- Passive path corruption eliminated (was ~40%, now 0%)
- Self-echo noise removed by design (byte-level echo suppression)
- Proxy escape encoding bug eliminated by design (ENH logical bytes)
- Proxy listener preserved for ebusd/VRC Explorer compatibility
- Standalone proxy remains available for non-gateway deployments
- Dual-transport pattern (2s INIT/INFO + 50ms readLoop) proven stable
- INFO cache: all 7 non-reserved IDs cached at startup

## Blockers

None. All milestones complete.

## Next Actions

None. Plan is in maintenance.
