# eBUS Good-Citizen NM 01: Evidence, Decisions, and Wire Behaviour

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `eb11742d60722b1389dca6822b956c15ddee542aacf95901299fefcd1a27dfcf`

Depends on: None. This chunk defines the evidence model, the problem statement,
and the locked architectural decisions for the NM model and wire behaviour.

Scope: Summary, evidence snapshot, problem statement, optional-NM rationale,
spec-aligned passive NM model, discovery adjacency, identity model, gateway
runtime ownership, and broadcast/responder lane split.

Idempotence contract: Declarative-only. Reapplying this chunk must not change
the NM model, broaden the wire promises, or reintroduce probe-centric NM.

Falsifiability gate: A review fails this chunk if it claims NM is active/probe-
driven, treats `FF03/04/05/06` as the monitoring mechanism, assumes peer NM is
present on the observed Vaillant topology, or promises responder behaviour
without a feasibility gate.

Coverage: Summary; Evidence Snapshot; Problem Statement; Locked Decisions 1-6B
from the canonical plan.

## Summary

- Helianthus will implement optional eBUS NM because it improves topology
  visibility, failure signaling, standards alignment, and MCP/RE ergonomics.
- The plan follows the actual eBUS NM model: indirect, passive, cycle-time
  based monitoring of ordinary traffic.
- `FF03/04/05/06` are optional interrogation surfaces over internal NM state.
- Wire behaviour is split into:
  - Lane A: broadcasts we can originate with initiator mode
  - Lane B: responder-grade interrogation support that requires slave-address
    receive/reply support

## Evidence Snapshot

### Proven

- Live topology evidence confirms the Vaillant faces `0x15`, `0xEC`, `0x04`,
  and `0xF6`, with `0xEC -> 0x15` and `0xF6 -> 0x04` as canonical aliases.
- `07 04` identification works through `ebusctl hex -n`.
- Peer `FF03/04/05/06` interrogation on the observed Vaillant installation did
  not return useful data.
- The gateway currently lacks target configuration, cycle-time monitoring,
  status chart, net status, start flag, and the `NMInit -> NMReset -> NMNormal`
  state machine.
- Passive observation infrastructure already exists.
- The active send path already handles `0xFE` broadcast frames without slave
  response waiting, which supports the gateway-only first broadcast milestone.
- The MCP alias/faces parity gap is specifically in `ebus.v1.registry.devices.*`
  serialization and snapshot lookup, not in portal/GraphQL.

### Hypothesis

- Vaillant peer NM is optional/best-effort input, not required truth.
- A gateway-owned NM runtime still has value without peer interrogation
  responses.
- Local responder support may require lower-layer, proxy, or firmware work.

### Unknown

- Whether the current transport/adapters can safely support full local
  responder mode on the slave address.
- Whether `ebusd-tcp` can ever support responder-grade local participant
  behaviour.
- Whether active raw transceive can coexist with the semantic poller without a
  new contention policy.

## Problem Statement

The stack currently lacks:

1. first-class raw-frame MCP inspection
2. discovery integrated with the NM model
3. a gateway NM runtime with target configuration, cycle times, status chart,
   net status, start flag, and `NMInit -> NMReset -> NMNormal`
4. standards-speaking local participant behaviour on the wire

## Locked Decisions

### Optional NM is deliberate

- Helianthus chooses to implement optional eBUS NM.
- Peer support remains optional and is never assumed.

### The NM model is passive and indirect

- NM is not a probe graph.
- The runtime model is:
  - target configuration
  - cycle-time monitoring
  - per-node `OK/NOK` status chart
  - net status
  - start flag
  - `NMInit -> NMReset -> NMNormal`
- Monitoring is driven by ordinary cyclic traffic.
- `NMReset -> NMNormal` is automatic after initialization.

### Discovery remains adjacent, not identical, to NM

- Discovery fuses:
  - passive `07 04`
  - passive `FF 00`
  - passive `FF 01`
  - new cyclic traffic from unseen addresses
  - bounded active `07 04` confirmation
  - bounded, indirect `07 FE` use when justified
- `07 FE` is never treated as a direct-answer discovery query.
- `07 FF` remains an optional-later good-citizen signal.

### Identity must preserve bus faces

- The model separates:
  - `PhysicalDevice`
  - `BusFace`
  - `CompanionPair`
  - `TargetConfigurationEntry`
  - `NMEdge`
- Alias resolution remains multi-source:
  - direct protocol alias evidence
  - serial number
  - MAC address
  - bounded fallback signature

### Synthetic NM runtime lives in the gateway

- `helianthus-ebusgateway` owns the NM state machine.
- `helianthus-ebusreg` remains an identity/projection layer.

### Wire-level behaviour is split into two lanes

#### Broadcast lane

- Mandatory-first:
  - `FF 00`
  - `FF 02`
- Optional-later:
  - `FF 01`
  - `07 FF`
- Broadcasts do not require responder-mode transport support.
- `FF 00` is emitted only after a valid active local master address exists.
- `FF 02` is payload-less, so before responder support exists it remains a
  standards-shaped but only partially interrogable failure signal.

#### Responder lane

- Gated on responder feasibility.
- Includes:
  - targeted local `07 04`
  - `FF 03`
  - `FF 04`
  - `FF 05`
  - `FF 06`
- The interrogation target is the active local slave derived from the active
  local master.
- `0x71 -> 0x76` remains only an installation example, not a constant.
