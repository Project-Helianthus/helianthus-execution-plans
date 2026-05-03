# Proxy Wire-Semantics Fidelity 01: Execution Contract and Matrix

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `5949a992c2a63ba4b8ba207d7e8b898dec8a135d6cb18973c4d623018a987cc4`

Depends on: [00-canonical.md](./00-canonical.md),
[90-issue-map.md](./90-issue-map.md), and
[91-milestone-map.md](./91-milestone-map.md).

Scope: Milestone execution contract, full issue split, matrix subset definition
(`PX01..PX12`), and orchestrator assumptions/defaults.

Idempotence contract: Declarative-only. Reapplying this chunk must not create
new issues, mutate milestone order, or weaken matrix gates.

Falsifiability gate: Review fails this chunk if any issue from the EPIC split
is missing, if milestone order is not strictly `M0 -> M5` with deferred `M6`,
or if any `PX01..PX12` definition is absent.

Coverage: Canonical Sections 2-6.

## 1. Milestone Contract

Execution order is hard-locked:

`M0 -> M1 -> M2 -> M3 -> M4 -> M5`

with:

- `M6` deferred and non-blocking for implementation lanes
- one active issue per repo at a time
- doc-gate required before behavior-change merges

## 2. Full Issue Set

The orchestrator must resolve work from this fixed set:

- EPIC root:
  - `Project-Helianthus/helianthus-execution-plans#5`
- execution-plans:
  - `#6` (`PLAN-01`)
  - `#7` (`FOLLOWUP-01` plan lane)
- docs:
  - `#238` (`DOC-01`)
  - `#239` (`DOC-02`)
  - `#240` (`TEST-01` docs lane)
  - `#241` (`FOLLOWUP-01` docs lane)
- proxy:
  - `#85` (`PROXY-01`)
  - `#86` (`PROXY-02`)
  - `#87` (`PROXY-03`)
  - `#88` (`PROXY-04`)
  - `#89` (`PROXY-05`)
  - `#90` (`PROXY-06`)
  - `#91` (`TEST-01` proxy lane)

## 3. Matrix Subset Gate

Required adjunct subset:

- `PX01`: stale `STARTED` absorb success
- `PX02`: stale `STARTED` bounded expiry
- `PX03`: `SYN` while waiting command `ACK` timeout boundary
- `PX04`: `SYN` while waiting target response timeout boundary
- `PX05`: lower initiator wins same boundary
- `PX06`: queued higher loses if lower arrives before round closes
- `PX07`: requeue-after-timeout contender resolution
- `PX08`: equal-initiator FIFO preservation
- `PX09`: echo-driven visibility only for local target request
- `PX10`: in-window local target response coherence
- `PX11`: late local target response rejected and counted
- `PX12`: non-owner/non-responder send rejected

Merge gate policy for proxy transport/protocol behavior:

- must pass `T01..T88`
- must pass `PX01..PX12`
- must not show unexpected `fail`
- must not show unexpected `xpass`

## 4. Assumptions and Defaults

- Wire-semantics fidelity is the target; electrical bit-level simultaneity is
  out of scope for this implementation wave.
- No manual ENS/ENH address-claim extension is introduced.
- Session-to-initiator learning is allowed.
- Generic target ownership learning is not universal authority.
- Local target service is initially for controlled emulation use cases.
- Hardware validation is deferred to `M6`, but evidence contract is mandatory
  in `M5`.

## 5. Execution Guardrails

- `PROXY-01` and `PROXY-02` may land before scheduler redesign.
- `PROXY-06` may ship behaviorally, but strict timing claims for generic
  child-backed responders are blocked until `FOLLOWUP-01` completes.
- If the issue graph changes in GitHub, canonical map files must be updated
  before any downstream execution handoff.
