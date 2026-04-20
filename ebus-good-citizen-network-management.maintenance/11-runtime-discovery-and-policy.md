# eBUS Good-Citizen NM 02: Runtime, Discovery, and Policy

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `eb11742d60722b1389dca6822b956c15ddee542aacf95901299fefcd1a27dfcf`

Depends on: [`10-evidence-decisions-and-wire-behaviour.md`](./10-evidence-decisions-and-wire-behaviour.md)
for the evidence model, NM interpretation, and wire-lane split.

Scope: Local address-pair authority, `Init_NM` triggers, disconnect semantics,
raw MCP stance, cycle-time policy, target configuration, self-monitoring,
failure/error surfaces, bus-load policy, target repositories, and delivery
ordering.

Idempotence contract: Declarative-only. Reapplying this chunk must not change
the local-address authority model, the cycle-time defaults, the transport-gap
policy, or the raw-MCP capture-first gate.

Falsifiability gate: A review fails this chunk if it hardcodes the local
address pair, lets transport blindness masquerade as remote-node silence,
claims the `120s` default is empirically proven when it is not, or treats NM
`self` status as the only fast transport-health detector.

Coverage: Locked Decisions 6C-12; Target Repositories; Delivery Order from the
canonical plan.

## Local Address-Pair Authority

- The NM runtime consumes a canonical local address-pair source.
- Preferred source on supporting transports:
  - `JoinResult.Initiator`
  - `JoinResult.CompanionTarget`
- Fallback source on transports where gentle join is unavailable or disabled,
  notably current `ebusd-tcp`:
  - configured local initiator policy
  - derived companion target
- The local address pair is runtime state with provenance, not a literal
  constant baked into the plan.

## Join, Rejoin, and `Init_NM`

- A rejoin that changes the selected local address pair is NM-relevant:
  `NMInit -> NMReset -> NMNormal`.
- Joiner warmup observations seed evidence but do not promote devices directly.
- A transport disconnect without completed rejoin is not treated as a fake NM
  reset.
- During transport blindness:
  - `self -> NOK`
  - remote-node cycle-time advancement freezes
  - new NM-originated broadcasts needing a valid local address are suppressed
- Helianthus enters `NMInit` on:
  - process start
  - first successful acquisition of a valid local address pair
  - completed join or rejoin after transport recovery
  - explicit operator-triggered NM reset
  - configuration changes that invalidate the current target configuration

## Raw MCP Policy

- Raw MCP is capture-first.
- The first milestone ships:
  - capture
  - frame listing
  - replay/decode-friendly evidence
- Active read-only transceive is conditional on explicit contention proof.

## Cycle-Time Policy

- The lock-baseline default for dynamically enrolled monitored nodes is
  provisionally `120s`.
- This is a planning default, not a claim already proven for every live node
  class.
- Implementation must collect observed cadence artifacts for enrolled node
  classes and either:
  - justify the default
  - or attach explicit overrides
- `07 FF` has a locked minimum cadence floor of `>= 10s`.
- Locked planning assumption for NM-originated traffic:
  - `<= 0.5%` sustained outside reset/rejoin windows
  - `<= 2.0%` bounded burst during reset/rejoin windows

## Target Configuration

- The gateway target configuration is discovery-fed and self-inclusive.
- Population strategy:
  - always include `self`
  - dynamically enroll confirmed devices/faces that Helianthus actively polls,
    depends on semantically, or promotes through discovery
  - allow bounded operator/static seed entries where needed
- Joiner warmup handoff path:
  - Joiner warmup observation
  - gateway discovery evidence buffer / suspect seeding
  - normal discovery promotion
  - target-configuration enrollment
- Unconfirmed passive suspects do not enter target configuration directly.

## What Resets a Node Timer

- A monitored node timer resets on:
  - passive observation of a CRC-valid reconstructed sender-attributed
    application transaction
  - a successful addressed response to a Helianthus-originated query that
    proves the monitored node is alive
  - for `self`, a successful Helianthus-originated bus transaction such as a
    poll read, discovery probe, or NM broadcast
- Passive decode faults do not reset NM cycle timers.
- Passive disconnect/discontinuity events are fed into the NM runtime as
  observability-loss signals distinct from remote-node absence.

## Self-Monitoring

- `self` is mandatory in the NM status chart.
- `self` is keyed to the active local address pair.
- The first lock baseline uses the same provisional `120s` default for `self`
  unless earlier evidence proves a tighter safe override.
- NM `self` status is not the only or fastest transport-health detector.
- Existing transport and adapter health surfaces remain responsible for the
  low-latency path.

## Failure and Error Surfaces

- `FF 02` is the NM-specific failure surface in scope.
- `FE 01` general error broadcast remains out of the first lock baseline unless
  a later doc-gated issue defines Helianthus-wide semantics for it.

## Target Repositories

- `helianthus-docs-ebus`
- `helianthus-ebusgo`
- `helianthus-ebusreg`
- `helianthus-ebusgateway`
- `helianthus-ebus-adapter-proxy`
- `helianthus-ha-integration`

Conditional note:

- adapter firmware repos may join later if `M7a` proves a dependency outside
  these currently enumerated repos.

## Delivery Ordering

- Default repo order:
  1. `helianthus-docs-ebus`
  2. `helianthus-ebusgo`
  3. `helianthus-ebusreg`
  4. `helianthus-ebusgateway`
  5. conditional proxy / firmware work
  6. optional consumer rollout
- `ISSUE-GW-JOIN-01` lands before `M4`.
- `M7a` may start as soon as `M1` exists and may run in parallel with `M2a`
  through `M5`, but it gates only `M7b`.
