# Platform Taxonomy And Boundaries

Canonical-SHA256: `786f23ae2457c556df300005fcdabdc90b5a2fecb3e7bdb291326d4ba7a43286`

Depends on:
None. This is the vocabulary root for the draft.

Scope:
Defines the platform layering that every runtime, protocol family, and vendor
profile must use in the locked plan.

Idempotence contract:
Re-reading or re-applying this taxonomy must not imply code changes by itself.
Implementation issues must name the layer they change.

Falsifiability gate:
For any proposed future protocol, reviewers must be able to classify each
component as transport, base protocol, profile, runtime instance, native
registry, semantic projection, or semantic integration. If not, the taxonomy is
incomplete.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

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
- Language-neutral cross-runtime contracts live in
  `helianthus-docs-ebus/docs/platform/`; protocol-native eeBUS contracts live
  in `helianthus-docs-eebus` under the AD-DOCS-01 ownership matrix.

## Documentation Ownership Boundary

`helianthus-docs-ebus/docs/platform/` owns cross-runtime envelopes,
hash/auth binding, shared registry boundary, and promotion/consumer rules.
`helianthus-docs-eebus/protocols/` owns eeBUS/SHIP/SPINE protocol behavior.
`helianthus-docs-eebus/architecture/` owns eeBUS runtime, adapter, trust,
persistence, and lifecycle architecture. `helianthus-docs-eebus/api/` owns
eeBUS-specific Go public API schema, reference, and examples.

Every page declares `canonical_source`. Duplicated ownership is invalid.
`helianthus-eebusreg` owns no substantive protocol, architecture, API,
harness, test, or user documentation.

## Non-Goals

- Do not generalize eBUS adapter internals into shared infrastructure for all
  protocols.
- Do not treat Modbus as SunSPEC.
- Do not treat eBUS as Vaillant.
- Do not treat eeBUS/SHIP/SPINE as a simple transport.
- Do not expose stable consumer semantics before raw MCP and semantic MCP have
  converged.
- Do not restore a `docs/` directory to `helianthus-eebusreg` main, even as
  rollback. Documentation cleanup is forward-only.

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
