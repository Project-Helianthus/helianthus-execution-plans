# eBUS 0.4.0 Baseline And Profile Split

Canonical-SHA256: `f7c48073085d32dbe1de9e352f454a29fa60b6b7ac05954c5f253cb9593dccdc`

Depends on:
`10-platform-taxonomy-and-boundaries.md`.

Scope:
Defines how gateway `0.4.0` becomes the eBUS runtime baseline and how Vaillant
is separated from base/classic eBUS.

Idempotence contract:
The first implementation pass must be behavior-preserving. Existing `ebus.v1.*`,
GraphQL, Portal, and Home Assistant behavior must not change while boundaries
are introduced.

Falsifiability gate:
With Vaillant profile logic disabled, raw/classic eBUS discovery and evidence
must remain available. With the profile enabled, current Vaillant semantics must
match gateway `0.4.0` behavior.

Coverage:
Covers M0, M2, and M3 from the canonical milestone list.

## Baseline

Gateway `0.4.0` is the direct eBUS baseline without the external eBUS proxy.
The draft treats that version as the compatibility reference for:

- direct adapter runtime behavior;
- adapter ownership and arbitration behavior;
- active/passive observation boundaries;
- startup scan behavior;
- observe-first behavior;
- existing Vaillant semantic behavior;
- current MCP, GraphQL, Portal, and Home Assistant outputs.

## Runtime Boundary

Introduce `EBusRuntimeAdapter` as a conceptual boundary around the existing
direct eBUS implementation. The boundary owns:

- eBUS direct adapter lifecycle;
- base eBUS transport and framing;
- active and passive runtime paths;
- startup scan;
- observe-first stores;
- raw eBUS evidence surfaces;
- eBUS profile registry.

The boundary must not imply a rewrite. It is a containment step so future
runtime adapters can coexist beside eBUS.

## Base/Profile Split

`helianthus-ebusreg` must evolve toward:

```text
helianthus-ebusreg
  eBUS base registry
  classic eBUS discovery and raw evidence
  profile registry
    ClassicEBusProfile
    VaillantProfile
    future AristonProfile
    future BuderusProfile
    future WolfProfile
    future SaunierDuvalProfile
```

Vaillant-specific behavior belongs behind `VaillantProfile`. Base eBUS belongs
to the runtime and base protocol layers.

## Public Surface Rules

- `ebus.v1.*` remains backward-compatible.
- Raw eBUS tools must not silently mean Vaillant-only behavior.
- Vendor-specific MCP additions must be explicitly profile-scoped.
- Semantic facts from eBUS must carry `base_protocol=eBUS` and a profile value
  such as `classic-ebus` or `vaillant`.
- Consumer-visible GraphQL and Home Assistant behavior must not change during
  the boundary split.

## Acceptance

- Gateway `0.4.0` smoke behavior is documented as the eBUS baseline.
- eBUS runtime internals are contained behind a runtime adapter boundary.
- Vaillant behavior is identified as profile behavior.
- Raw/classic eBUS remains available independently of Vaillant semantics.
- No consumer API is broken by the split.
