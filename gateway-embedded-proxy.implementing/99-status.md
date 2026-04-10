# Status

State: `implementing`

## Current Position

- M1-M3 merged on gateway main via PR #472 (6abc083)
- PR #473 merged (Init consumer + P0 fixes)
- PR #474 merged (P3 observer continuity)
- M4 merged on ha-addon main via PR #117
- ebusgo PRs #126 + #127 merged (Init return + StreamEvent)
- M0 doc-gate still open (ARCHITECTURE.md + docs-ebus pending)
- M5 in progress (AD gate exists, live validation pending)

## Active Focus

- M0 doc closure: ARCHITECTURE.md update + docs-ebus landing
- M5 live validation: AD01..AD12 evidence collection against production hardware

## Blockers

- M0 doc-gate must close before M5 can be declared complete.

## Next Actions

1. Land ARCHITECTURE.md update for adapter-direct transport
2. Land docs-ebus AD01..AD12 definitions
3. Complete M5 live validation matrix
4. Collect E2E evidence for AD gate closure
5. Close M0 + M5, transition plan to `.done`
