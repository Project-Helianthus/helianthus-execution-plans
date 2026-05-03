# Status

State: `maintenance`

## Current Position

- `eBUS Good-Citizen Network Management + Raw MCP` is retained as a frozen
  enrichment source in `helianthus-execution-plans`.
- Current slug state: `ebus-good-citizen-network-management.maintenance`
- The plan converged through a multi-round adversarial review loop before
  promotion from `_drafts/`.
- The locked plan includes:
  - raw MCP capture-first delivery
  - gateway-owned spec-aligned NM runtime
  - discovery realignment
  - broadcast/responder wire-lane split
  - Joiner-aware local address authority
  - bus-load, cadence, and observability-loss policy

## Adversarial Review Summary

- Round 1: major structural corrections to the NM model, responder feasibility,
  raw contention, and alias/faces gap scoping
- Round 2: target configuration, self-monitoring, event bridge, cadence floor,
  and repo-ordering clarifications
- Round 3: Joiner integration and local address authority convergence
- Round 4: factual semantic closure for automatic `NMReset -> NMNormal`,
  payload-less `FF02`, cadence evidence, `MessageReceived` meaning,
  disconnect semantics, and `Init_NM` triggers

## Maintenance Position

- The plan is superseded/adopted, not actively implementing.
- `ebus-standard-l7-services-w16-26.maintenance` adopted the authoritative NM
  docs and runtime design.
- `startup-admission-discovery-w17-26.maintenance` extracted and completed the
  narrow `ISSUE-GW-JOIN-01` startup-admission lane.

## Blockers

- None. The plan is in maintenance.

## Next Actions

None. Future work should open a new narrow plan or attach to the superseding
maintenance plans above.
