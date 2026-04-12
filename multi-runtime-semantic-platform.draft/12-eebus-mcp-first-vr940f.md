# eeBUS MCP-First VR940f Track

Canonical-SHA256: `f7c48073085d32dbe1de9e352f454a29fa60b6b7ac05954c5f253cb9593dccdc`

Depends on:
`10-platform-taxonomy-and-boundaries.md` and the gateway `0.4.0` baseline
described in `11-ebus-040-baseline-and-profile-split.md`.

Scope:
Defines the first eeBUS runtime track: new registry repo, raw MCP visibility,
VR940f binding, and candidate semantic reproduction.

Idempotence contract:
Initial eeBUS work must be additive. It must not change existing eBUS outputs
or require GraphQL, Portal, or Home Assistant changes.

Falsifiability gate:
The operator must be able to pair/bind the VR940f and inspect discovered
SHIP/SPINE sessions, services, topology, and raw evidence before any semantic
mapping is accepted.

Coverage:
Covers M5, M6, and M7 from the canonical milestone list.

## New Repo

Create `helianthus-eebusreg` as the eeBUS native registry repo over
`enbility/eebus-go`.

It owns:

- SHIP/SPINE lifecycle;
- pairing and trust store;
- runtime health;
- sessions;
- service graph;
- raw topology;
- snapshots;
- evidence references;
- VR940f discovery state.

It does not own GraphQL, Portal, Home Assistant, or cross-runtime semantic
precedence.

## Gateway Runtime

`EEBusRuntimeAdapter` is a sibling of `EBusRuntimeAdapter`.

It owns the configured eeBUS endpoint lifecycle and exposes raw state upward to
the gateway. It must not reuse eBUS adapter internals or eBUS-specific
assumptions.

## MCP Raw First

Initial MCP tools are raw/runtime oriented:

- runtime status;
- session list and session detail;
- service list and service detail;
- raw discovery state;
- raw topology state;
- snapshot capture and drop;
- pairing diagnostics.

Names are finalized during implementation, but the shape must remain
`eebus.v1.*` for stable raw tools and experimental namespaces for dangerous
pairing mutation.

## VR940f First Target

The first lab success condition is:

- gateway starts with eBUS direct runtime unchanged;
- eeBUS runtime can be configured;
- VR940f can be discovered;
- pairing/trust state is visible;
- services and topology are exposed through MCP;
- raw evidence survives restart through the chosen cache/trust model.

## Candidate Semantics

The first candidate semantic families are:

- devices;
- system;
- zones;
- DHW.

The initial withheld families are:

- circuits;
- energy totals;
- command routing.

Candidate semantic fields must remain marked as candidate until raw evidence,
field provenance, and repeated lab observations justify promotion.
