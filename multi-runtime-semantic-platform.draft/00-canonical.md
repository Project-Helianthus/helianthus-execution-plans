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

The first extension target is raw eeBUS visibility for the
VR940f/myVaillant gateway through a new `helianthus-eebusreg` repo. The repo
bootstrap is raw runtime/evidence plumbing only; the M3 facade spike introduces
`enbility/eebus-go v0.7.0` behind internal packages. The repo name is accepted
only after an ADR states that it is raw runtime/evidence plumbing, not a
semantic registry fork. The same architecture must later support Gree VRF
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
  local lab until it is paired and inspected through raw MCP.
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

### M0 - Control Plane And Issue Matrix

Create the execution control plane before code. Every issue must record
complexity, model lane, repo, predecessor edges, doc owner, doc gate,
transport/security gate, rollback ledger, review ledger, and one-PR-per-repo
serialization.

Gate: no implementation issue may start until the issue matrix is complete and
the `eebus-transport-gate v0` definition exists.

### M1 - Documentation Grounding

Create the platform ownership ADR under `helianthus-docs-ebus/docs/platform/`
first, then bootstrap `helianthus-docs-eebus`, then add the eeBUS provenance
and publication policy.

Gate: eeBUS-native facts and cross-protocol platform contracts have one
canonical owner each, with summary-only non-owning pages.

### M2 - Raw Identity, Snapshot, Evidence, And Correlation Drafts

Bootstrap `helianthus-eebusreg` as a raw runtime/evidence repo, then draft raw
identity, snapshot envelope, evidence object, and raw correlation contracts.
This milestone does not freeze final MCP v1 and does not create semantic
parity.

Gate: the raw contracts are reviewable, versioned, and explicitly mark unknown
eeBUS/SPINE fields as unknown rather than silently normalizing them.

### M3 - eeBUS Runtime Feasibility

Spike `enbility/eebus-go v0.7.0` behind internal facades, prove toolchain and
module boundaries, prove HA runtime networking from a LAN peer, and run
black-box fake-peer plus live VR940f smoke. M3 uses only disposable proof
credentials and makes no production trust guarantee.

Gate: the facade compiles and the VR940f can be discovered, paired for proof,
inspected, and reconnected before any persistent gateway import is allowed.

### M3.5 - Raw Runtime Contract Freeze

Freeze only raw identity, raw snapshot envelope, and evidence object shapes.
Trust, pairing, admin state, and final MCP v1 remain unfrozen until M4/M6.

Gate: raw snapshot and evidence fixtures replay deterministically.

### M4 - Production Trust, First-Trust, And Security

Implement the production trust-state model, hardened `/data/eebus` store,
first-trust flow, admin-local boundary, backup/restore behavior, quarantine,
and repair flows.

Gate: no production listener can open unless eeBUS is enabled, interface/subnet
are explicit, the store is valid, and the trust state permits listening.

### M4.5 - Trust And Admin State Freeze

Freeze trust, pairing, admin-local, restore/clone, quarantine, and repair state
semantics after M4 tests pass.

Gate: MCP and gateway code can consume the state model without making security
decisions ad hoc.

### M5 - Gateway Sidecar Integration

Add isolated eeBUS configuration and a disabled-by-default
`EEBusRuntimeAdapter` sidecar. It is a sibling runtime and must not modify
`transportFromConn`, `protocol.Bus`, `router.BusEventRouter`, or eBUS registry
semantics.

Gate: disabled default opens no eeBUS sockets, creates no trust files, and
leaves existing eBUS MCP, GraphQL, Portal, HA, and transport-matrix behavior
unchanged.

### M6 - Read-Only eeBUS MCP v1

Freeze final read-only `eebus.v1.*` MCP after raw identity and trust/admin
state are composed. Stable tools expose runtime status, services, sessions,
topology, snapshots, and pairing status only.

Gate: snapshot, hash, auth/mask binding, error precedence, drop, evolution, and
anti-leak tests pass.

### M6.5 - Synchronized Evidence Recorder

Record synchronized eeBUS, eBUS, and myVaillant/myPyllant evidence using
existing read-only eBUS surfaces only. If exact B509/B524/B555 source identity
is absent, the result is `WITHHELD` or `NOT_TESTED`.

Gate: replay regenerates the same raw evidence, timestamps, redacted hashes,
and candidate inputs without live network or cloud access.

### M7 - Draft Candidate Fact Graph

Create draft candidate facts only. M7 cannot promote leaves and cannot drive
GraphQL, Portal, HA, or command routing.

Gate: candidate facts retain raw evidence, comparator drafts, negative result
states, and source identity.

### M8 - Multi-Runtime Coexistence

Run eBUS and eeBUS concurrently with separate raw surfaces. Promoted eBUS
leaves remain authoritative; eeBUS candidate or conflict facts never override
existing consumer-visible output.

Gate: coexistence fixtures prove no eBUS output drift and conflict visibility
is raw/debug only.

### M8.5 - Leaf Promotion Lock

Lock individual leaf promotions only after coexistence evidence is present.
Each dossier must include comparator results, source-family identity,
terminal negative states, replay regeneration, and redacted hashes.

Gate: no leaf can enter GraphQL, Portal, or HA without a locked dossier.

### M9 - GraphQL, Portal, And HA Consumers

Split consumer work by repo: gateway GraphQL first, Portal second, Home
Assistant third. Consumers expose only promoted leaves.

Gate: GraphQL schema/value snapshots, HA entity identity/class/unit/availability
snapshots, and MCP/debug compatibility prove no unapproved drift.

## Execution Rules

- Work one repo issue at a time unless a milestone explicitly permits
  independent parallel tracks.
- Each issue must touch one layer: transport, base protocol, profile,
  native registry, semantic projection, MCP, GraphQL, Portal, or Home
  Assistant.
- If an issue needs two layers, split it.
- Complexity/model routing is fixed for this plan:
  - complexity 1-2: `GPT-5.3-Codex-Spark` for fast smoke, checklist, and
    mechanical gap checks;
  - complexity 3-4: `gpt-5.4-mini` for small doc-gate, issue-splitting,
    acceptance-criteria, and consistency tasks;
  - complexity 5: `GPT-5.5 medium` owner, with Spark or `gpt-5.4-mini` review;
  - complexity 6-7: `GPT-5.5 high` owner with adversarial review;
  - complexity 8-10: `GPT-5.5 xhigh` owner and independent review before merge.
- Do not promote any semantic field to consumers without raw evidence and
  provenance.
- Do not rename or generalize eBUS public API namespaces until compatibility
  and migration are explicitly planned.
- Keep durable protocol knowledge canonical in `helianthus-docs-ebus`.
  `helianthus-docs-eebus` is the eeBUS-native workbench/docs repo and must
  cross-seed publishable conclusions back to `helianthus-docs-ebus`.
  Cross-protocol platform contracts remain in `helianthus-docs-ebus/docs/platform/`
  until a future docs-platform repo is created.

## Acceptance

The draft is acceptable when:

- The draft directory exists with standard plan layout.
- The canonical plan states gateway `0.4.0` as the baseline.
- The plan uses gateway `0.4.0` as the only baseline reference.
- Chunks are reviewable in isolation and include the required proof headers.
- Existing active plan validation remains green.
- The `.draft` directory is intentionally ignored by the active-plan validator.
