# Proxy Wire-Semantics Fidelity and Local Target Emulation

Revision: `v1.2-maintenance-reconciled`
Date: `2026-04-09`
Status: `Maintenance`
Maintenance since: `2026-04-11`

Lifecycle note: M1-M5 are merged and the plan is in maintenance. M6 remains a
deferred, non-blocking ESERA passive validation follow-up.

## Summary

This plan operationalizes EPIC `Project-Helianthus/helianthus-execution-plans#5`
as an orchestrator-ready work package that can be executed from EPIC context
alone.

The intent is to move `helianthus-ebus-adapter-proxy` from token-style
scheduling to wire-semantics behavior for shared eBUS access, with explicit
sequencing:

- `M0`: lock docs and execution package (no functional proxy changes)
- `M1`: immediate correctness fixes
- `M2`: boundary-based arbitration
- `M3`: minimal direct-mode phase tracker
- `M4`: local target emulation core
- `M5`: matrix/proof integration
- `M6`: deferred passive hardware validation (non-blocking)

No transport/protocol behavior change is allowed to merge without matrix
evidence.

Execution-state note:

- Proxy/docs implementation lanes for `M1..M5` are already landed on local
  `main` histories.
- `M0` docs lane is landed, while the execution-plans lane remains in
  reconciliation.
- `M6` remains deferred and non-blocking.

## 1. Proven / Hypothesis / Unknown

### 1.1 Proven

- EPIC issue exists: `#5`.
- Required child issues exist across all three repos.
- Proxy implementation lanes `#85` to `#91` are landed in local `main` history.
- Docs lanes `#238`, `#239`, and `#240` are landed in local execution history.
- Milestone ordering contract is fixed: `M0 -> M1 -> M2 -> M3 -> M4 -> M5`,
  with `M6` deferred.

### 1.2 Hypothesis

- `PX01..PX12` can be integrated as a required adjunct proof subset without
  destabilizing the existing `T01..T88` gate.
- Controlled local target responder windows can be implemented in proxy without
  violating existing ownership guarantees.

### 1.3 Unknown

- Hardware-timing proof for strict local target response fidelity on production
  shared bus topology remains unknown until ESERA passive validation (`M6`).

## 2. Milestone Model and Current Execution State

### M0: Spec, docs, and harness scaffolding

Repos:
- `helianthus-execution-plans`
- `helianthus-docs-ebus`

Outcomes:
- freeze decisions, issue map, milestone map, matrix IDs
- define runtime evidence expectations
- no functional proxy behavior change

Current state:
- docs lane (`DOC-01`) landed
- execution-plans lane (`PLAN-01`) still reconciling

### M1: Immediate correctness fixes

Repo:
- `helianthus-ebus-adapter-proxy`

Outcomes:
- stale `STARTED` absorb on `pendingStart`
- `SYN-while-waiting` closes current transaction for scheduling
- add stable counters/logs
- keep scheduler model otherwise unchanged

Current state:
- completed on proxy `main`

### M2: Boundary-based initiator arbitration

Repo:
- `helianthus-ebus-adapter-proxy`

Outcomes:
- choose next writer at boundaries from ready contenders
- winner selection by lowest initiator address
- FIFO only within equal initiator
- same-round requeue is honored

Current state:
- completed on proxy `main`

### M3: Minimal direct-mode phase tracker

Repo:
- `helianthus-ebus-adapter-proxy`

Outcomes:
- byte-level tracker for `SRC`, `DST`, `PB`, `SB`, `LEN`, request length
- detect `ACK/NACK` and response phase transitions
- classify terminal vs timeout boundaries
- no L7 semantic parsing

Current state:
- completed on proxy `main`

### M4: Local target emulation core

Repos:
- `helianthus-ebus-adapter-proxy`
- `helianthus-docs-ebus`

Outcomes:
- session-to-initiator learning from real start/request activity
- controlled local target association
- responder window from echoed request
- reject and count late detached responses

Current state:
- completed on proxy/docs `main`

### M5: Matrix, smoke, and operator proof updates

Repos:
- `helianthus-ebus-adapter-proxy`
- `helianthus-docs-ebus`

Outcomes:
- add and document `PX01..PX12`
- keep `T01..T88` as primary transport gate
- require `PX01..PX12` as adjunct gate for proxy behavior work
- define deferred hardware-proof placeholders

Current state:
- completed on proxy/docs `main`

### M6: Deferred hardware validation follow-up

Repos:
- `helianthus-docs-ebus`
- `helianthus-execution-plans`

Outcomes:
- ESERA passive capture procedure and pass/fail contract
- non-blocking for M0-M5
- required before production claims of strict timing fidelity

Current state:
- intentionally deferred; no closure claim

## 3. Canonical Issue Split

### EPIC root

- `Project-Helianthus/helianthus-execution-plans#5`

### M0

- `Project-Helianthus/helianthus-execution-plans#6` (`PLAN-01`)
- `Project-Helianthus/helianthus-docs-ebus#238` (`DOC-01`)

### M1

- `Project-Helianthus/helianthus-ebus-adapter-proxy#85` (`PROXY-01`)
- `Project-Helianthus/helianthus-ebus-adapter-proxy#86` (`PROXY-02`)

### M2

- `Project-Helianthus/helianthus-ebus-adapter-proxy#87` (`PROXY-03`)

### M3

- `Project-Helianthus/helianthus-ebus-adapter-proxy#88` (`PROXY-04`)

### M4

- `Project-Helianthus/helianthus-ebus-adapter-proxy#89` (`PROXY-05`)
- `Project-Helianthus/helianthus-docs-ebus#239` (`DOC-02`)
- `Project-Helianthus/helianthus-ebus-adapter-proxy#90` (`PROXY-06`)

### M5

- `Project-Helianthus/helianthus-docs-ebus#240` (`TEST-01 docs lane`)
- `Project-Helianthus/helianthus-ebus-adapter-proxy#91` (`TEST-01 proxy lane`)

### M6 (deferred)

- `Project-Helianthus/helianthus-docs-ebus#241` (`FOLLOWUP-01 docs lane`)
- `Project-Helianthus/helianthus-execution-plans#7` (`FOLLOWUP-01 plan lane`)

## 4. Required Proxy Semantics Matrix Subset

The new required subset is:

- `PX01`: stale `STARTED` absorb, matching result in absorb window
- `PX02`: stale `STARTED` absorb expires, bounded fail path
- `PX03`: `SYN` while waiting for command `ACK` reopens arbitration
- `PX04`: `SYN` while waiting for target response reopens arbitration
- `PX05`: lower initiator beats higher initiator at same boundary
- `PX06`: queued higher initiator loses if lower arrives before round closes
- `PX07`: requeue-after-timeout by former owner beats higher contender
- `PX08`: FIFO preserved for equal initiator
- `PX09`: local target sees request only after echoed `RECEIVED`
- `PX10`: local emulated target response inside responder window is coherent
- `PX11`: late local target response is rejected and counted
- `PX12`: non-owner/non-responder send is rejected during active transaction

Gate policy:

- transport/protocol proxy PRs must pass:
  - full `T01..T88`
  - full `PX01..PX12`
- no unexpected `fail`
- no unexpected `xpass`

## 5. Orchestrator Contract

Execution rules for an orchestrator receiving only EPIC `#5`:

1. Resolve child issues from this canonical map; do not infer missing work.
2. Execute strictly `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
3. Treat `M6` as deferred/non-blocking for implementation milestones.
4. Maintain one active issue per repo at a time.
5. Keep doc-gate ahead of behavior-change merge decisions.
6. Allow `PROXY-01` and `PROXY-02` to land before scheduler redesign.
7. Do not claim strict timing proof for generic child-backed responders before
   `FOLLOWUP-01` evidence is complete.

## 6. Assumptions and Defaults

- Goal is wire-semantics fidelity for shared eBUS access, not perfect
  electrical bit-level simultaneity.
- No ENS/ENH extension is introduced for manual target claims.
- Generic learning is allowed for `session -> initiator source`.
- Generic learning is not universal authority for arbitrary
  `target -> session`.
- Local target service is introduced for controlled emulation use cases first.
- Hardware validation is deferred in this wave, but the matrix/docs/proof
  contract must be implementation-ready now.

## 7. Maintenance Readiness Definition

This plan remains `implementing` until:

- `PLAN-01` (`#6`) is reconciled on `main` with status/issue/milestone maps
  aligned to landed implementation evidence,
- deferred follow-up ownership for `FOLLOWUP-01` (`#241`, `#7`) is explicitly
  reaffirmed in plan status, and
- no stale `locked`-state execution instructions remain in the split package.

After these are satisfied, the slug may transition to `.maintenance`.
