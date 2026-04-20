# Status

State: `locked`

## Current Position

- `eBUS Good-Citizen Network Management + Raw MCP` now has a canonical locked
  home in `helianthus-execution-plans`.
- Current slug state: `ebus-good-citizen-network-management.locked`
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

## Active Focus

- Keep the plan in `locked` until the first implementation PR opens in a target
  repo.
- Translate canonical issue IDs into real GitHub issues in milestone order.
- Start with `M0` in `helianthus-docs-ebus`.

## Blockers

- None. The plan is converged and implementation-ready.

## Next Actions

1. Create GitHub issues for `M0` and `M1` in the primary repos.
2. Preserve `M7a` as a parallel feasibility spike, not as a blocker for the
   internal NM runtime.
3. Rename the plan to `.implementing` when the first code PR opens.
