# Platform Taxonomy And Boundaries

Canonical-SHA256: `f7c48073085d32dbe1de9e352f454a29fa60b6b7ac05954c5f253cb9593dccdc`

Depends on:
None. This is the vocabulary root for the draft.

Scope:
Defines the platform layering that every runtime, protocol family, and vendor
profile must use.

Idempotence contract:
Re-reading or re-applying this taxonomy must not imply code changes by itself.
Implementation issues must name the layer they change.

Falsifiability gate:
For any proposed future protocol, reviewers must be able to classify each
component as transport, base protocol, profile, runtime instance, native
registry, semantic projection, or semantic integration. If not, the taxonomy is
incomplete.

Coverage:
Covers the canonical platform model, architectural rules, and target gateway
shape.

## Model

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

## Decisions

- Transport is only the communication substrate. It does not own semantics.
- Base protocol owns common grammar: framing, addressing, checksums, generic
  reads/writes, discovery primitives, and raw evidence.
- Profile/dialect owns vendor language and model interpretation.
- Runtime instance owns endpoint lifecycle, health, trust, reconnects, caches,
  and runtime-local snapshots.
- Native registry preserves raw discoveries in native protocol terms.
- Semantic projection converts native facts into canonical facts with evidence.
- Semantic integration merges facts by identity, provenance, precedence, and
  conflict state.

## Non-Goals

- Do not generalize eBUS adapter internals into shared infrastructure for all
  protocols.
- Do not treat Modbus as SunSPEC.
- Do not treat eBUS as Vaillant.
- Do not treat eeBUS/SHIP/SPINE as a simple transport.
- Do not expose stable consumer semantics before raw MCP and semantic MCP have
  converged.

## Target Gateway Shape

```text
GatewayHost
  RuntimeManager
    EBusRuntimeAdapter
    EEBusRuntimeAdapter
    ModbusRuntimeAdapter
    future CAN/UART/KM-Bus runtime adapters
  NativeRegistryStore
  SemanticFactGraph
  MCPServer
  GraphQLServer
  Portal
  HomeAssistantConsumer
```

The shared contract starts above runtime-specific transport and base protocol
mechanics. Below that boundary, each runtime keeps its native behavior.
