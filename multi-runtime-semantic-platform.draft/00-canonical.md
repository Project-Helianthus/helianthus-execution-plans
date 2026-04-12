# Helianthus Multi-Runtime Semantic Platform

Revision: `v0.1-draft`
Date: `2026-04-12`
Status: `Draft`
Baseline: `Gateway 0.4.0`

## Summary

Helianthus is a multi-runtime native protocol gateway. It is not an eBUS-only
gateway with incidental plugins. Every supported system keeps its native
transport, base protocol, profile language, raw evidence, and lifecycle. The
shared platform integrates those systems by projecting canonical semantic facts
with provenance.

Gateway `0.4.0` is the baseline for the direct eBUS runtime without the
external eBUS proxy. This plan starts from that baseline and generalizes the
architecture so that eBUS, eeBUS, Modbus, CAN, UART, and KM-Bus families can
coexist without forcing one protocol's assumptions into another.

The first extension target is eeBUS through a new `helianthus-eebusreg` repo
using `enbility/eebus-go`. The same architecture must later support Gree VRF
CAN-BUS, Gree VRF UART, Viessmann KM-Bus, SunSPEC over Modbus RTU/TCP, Huawei
SUN2000 over Modbus RTU/TCP, and Growatt over Modbus RTU/TCP.

## Proven / Hypothesis / Unknown

### Proven

- Gateway `0.4.0` provides the named direct eBUS baseline for future runtime
  work.
- The current Vaillant support is a vendor profile over eBUS, not the complete
  meaning of eBUS.
- eBUS must support base/classic eBUS plus vendor dialects such as Vaillant,
  Ariston, Buderus, Wolf, and Saunier Duval.
- Modbus RTU and Modbus TCP are base protocol transports for multiple dialects,
  including SunSPEC, Huawei SUN2000 private maps, and Growatt private maps.
- MCP is the first delivery surface for new runtime/profile work in Helianthus.

### Hypothesis

- A stable split between transport, base protocol, profile, runtime instance,
  native registry, semantic projection, and semantic integration will allow new
  protocol families to be added without destabilizing the eBUS baseline.
- Raw-first MCP surfaces will provide enough observability for reverse
  engineering and lab verification before semantic promotion.
- Cross-runtime semantic facts with provenance will scale better than direct
  protocol-to-protocol translation.

### Unknown

- The exact eeBUS/SPINE feature subset exposed by the Vaillant VR940f in the
  local lab until it is paired and inspected.
- The first non-Vaillant eBUS vendor profile to implement.
- The final precedence policy for conflicts between eBUS, eeBUS, and future
  Modbus-derived semantic facts.
- Whether all future Modbus vendor-private maps can share one registry package
  or need profile-specific repos.

## Platform Model

```text
Transport
  eBUS adapter direct, SHIP/TCP, CAN, UART, KM-Bus, Modbus RTU, Modbus TCP

BaseProtocol
  eBUS, eeBUS/SHIP/SPINE, Modbus, Gree VRF framing, KM-Bus

Profile/Dialect
  Classic eBUS, Vaillant eBUS, Ariston eBUS, Buderus eBUS,
  SunSPEC, Huawei SUN2000 private, Growatt private, Gree VRF CAN/UART

RuntimeInstance
  configured endpoint with lifecycle, health, trust, identity, cache

NativeRegistry
  raw topology, devices, services, registers, frames, evidence

SemanticProjection
  boiler, zones, DHW, circuits, solar, inverter, battery, meter, energy

SemanticIntegration
  identity linking, precedence, conflict detection, command routing
```

## Architectural Rules

1. Transport has no semantic ownership. It moves bytes, frames, or sessions.
2. Base protocol owns common grammar: framing, addressing, checksums, generic
   reads/writes, discovery primitives, and raw evidence.
3. Profile/dialect owns the real vendor language: Vaillant B524, classic eBUS
   messages, SunSPEC models, Huawei private registers, Growatt maps, or Gree
   VRF command sets.
4. Runtime instance owns lifecycle: configuration, endpoint health, trust,
   pairing, caches, reconnects, and runtime-local snapshots.
5. Native registry preserves what the runtime discovered in native terms.
6. Semantic projection produces canonical facts and never hides raw evidence.
7. Semantic integration joins facts across runtimes through identity,
   provenance, precedence, conflict detection, and command routing.
8. Cross-runtime integration happens through canonical intent and semantic
   facts, not raw protocol-to-protocol translation.
9. MCP is the first surface for new capabilities. GraphQL, Portal, and Home
   Assistant follow only after MCP behavior stabilizes.
10. Vendor-specific knowledge belongs behind explicit profiles. No base
    protocol namespace may silently mean "Vaillant" or "SunSPEC".

## Target Architecture

```text
GatewayHost
  RuntimeManager
    EBusRuntimeAdapter
      eBUS direct adapter runtime
      eBUS base protocol
      ProfileRegistry
        ClassicEBusProfile
        VaillantProfile
        future vendor profiles
    EEBusRuntimeAdapter
      SHIP/SPINE runtime through enbility/eebus-go
      pairing and trust store
      SPINE service graph
    ModbusRuntimeAdapter
      Modbus RTU/TCP base protocol
      ProfileRegistry
        SunSPECProfile
        HuaweiSUN2000Profile
        GrowattProfile
  NativeRegistryStore
  SemanticFactGraph
  MCPServer
  GraphQLServer
  Portal
  HomeAssistantConsumer
```

The eBUS direct adapter internals remain private to `EBusRuntimeAdapter`.
They are not generalized into shared infrastructure for eeBUS, Modbus, CAN,
UART, or KM-Bus. The shared contract begins above runtime-specific transport
and protocol mechanics.

## MCP-First Delivery Contract

Every runtime/profile follows the same delivery order:

1. Raw MCP runtime status, topology, discovery, snapshots, and evidence.
2. Profile-specific MCP diagnostics when a dialect has extra state.
3. Candidate semantic MCP projections with explicit status and provenance.
4. Promoted semantic MCP projections after evidence is stable.
5. GraphQL parity for stable MCP contracts.
6. Portal workbench support for internal validation and reverse engineering.
7. Home Assistant integration only for stable, promoted semantics.

No consumer may drive API shape before raw MCP and semantic MCP have converged.

## Semantic Status Model

The draft keeps a conservative semantic status vocabulary:

- `RAW_ONLY`: native evidence exists but no semantic claim is made.
- `CANDIDATE`: a semantic projection is plausible but not stable.
- `PROMOTED`: the field is stable enough for GraphQL and consumers.
- `CONFLICTED`: multiple runtimes disagree and the conflict is represented.
- `WITHHELD`: the system has evidence but intentionally does not expose the
  field as semantic output.

Future locked plans may refine this vocabulary, but implementation work must
not collapse candidate, conflicted, and withheld facts into consumer-visible
stable values.

## Milestones

### M0 - Gateway 0.4.0 Baseline Lock

Freeze gateway `0.4.0` as the no-proxy direct eBUS baseline. Capture invariants
for the direct eBUS runtime, adapter ownership, active/passive behavior,
startup scan, observe-first behavior, and Vaillant semantic behavior.

Gate: gateway `0.4.0` can be built, deployed, and smoke-tested on the real
HA/RPi4 lab without the external eBUS proxy.

### M1 - Platform Vocabulary ADR

Document `Transport / BaseProtocol / Profile / RuntimeInstance /
NativeRegistry / SemanticProjection / SemanticIntegration` as the mandatory
classification vocabulary for future protocol work.

Gate: future protocol plans can classify every component without ambiguity.

### M2 - eBUS Runtime Boundary

Wrap the current direct eBUS implementation as `EBusRuntimeAdapter` with zero
public behavior change. Keep eBUS adapter and mux internals private to the
eBUS runtime.

Gate: existing `ebus.v1.*` MCP, GraphQL, Portal, and Home Assistant behavior
remain unchanged.

### M3 - eBUS Base/Profile Split

Split generic eBUS framing, discovery, and raw surfaces from Vaillant-specific
language. Move Vaillant behavior behind `VaillantProfile`.

Gate: raw/classic eBUS remains available even when no Vaillant profile is
active.

### M4 - Semantic Provenance v1

Every semantic fact must carry runtime, transport, base protocol, profile,
device profile, evidence reference, confidence, and status.

Gate: semantic consumers can distinguish facts from eBUS Vaillant, classic
eBUS, eeBUS, Modbus/SunSPEC, and vendor-private Modbus profiles.

### M5 - helianthus-eebusreg

Create the new eeBUS registry repo over `enbility/eebus-go`. It owns
SHIP/SPINE lifecycle, pairing, trust store, raw service graph, snapshots, and
VR940f discovery.

Gate: no GraphQL, Portal, or Home Assistant dependency is required for initial
eeBUS visibility.

### M6 - eeBUS MCP Raw First

Add raw MCP tools for runtime status, sessions, services, topology, discovery,
snapshots, and pairing diagnostics.

Gate: the operator can bind VR940f and see what was discovered before semantic
mapping exists.

### M7 - eeBUS Semantic Candidate

Add candidate projections for devices, system, zones, and DHW. Keep circuits,
energy totals, and command routing withheld until evidence is sufficient.

Gate: candidate, promoted, and withheld status is visible through MCP.

### M8 - Multi-Runtime Coexistence

Run direct eBUS and eeBUS concurrently in the gateway. Keep raw surfaces
separate.

Gate: semantic core can display multiple facts for the same physical concept
with explicit provenance and conflicts.

### M9 - GraphQL, Portal, HA

Add GraphQL only after MCP stabilizes. Extend Portal first as the internal
reverse-engineering workbench. Extend Home Assistant only after GraphQL
stability and semantic promotion.

Gate: Home Assistant never exposes entities for candidate, conflicted, or
withheld fields.

### M10 - Next Runtime Families

Add Modbus RTU/TCP profile stack, Gree VRF CAN/UART, and Viessmann KM-Bus using
the same runtime/profile/semantic contracts.

Gate: no new protocol is allowed to bypass MCP raw-first delivery.

## Execution Rules

- Work one repo issue at a time unless a milestone explicitly permits
  independent parallel tracks.
- Each issue must touch one layer: transport, base protocol, profile,
  native registry, semantic projection, MCP, GraphQL, Portal, or Home
  Assistant.
- If an issue needs two layers, split it.
- Do not promote any semantic field to consumers without raw evidence and
  provenance.
- Do not rename or generalize eBUS public API namespaces until compatibility
  and migration are explicitly planned.
- Capture durable protocol knowledge in `helianthus-docs-ebus`; this repo
  tracks execution intent.

## Acceptance

The draft is acceptable when:

- The draft directory exists with standard plan layout.
- The canonical plan states gateway `0.4.0` as the baseline.
- The plan uses gateway `0.4.0` as the only baseline reference.
- Chunks are reviewable in isolation and include the required proof headers.
- Existing active plan validation remains green.
- The `.draft` directory is intentionally ignored by the active-plan validator.
