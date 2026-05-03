# ebus_standard 10: Scope, Evidence, and Locked Decisions 1-8

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0273627cc3e9a63cf5d4bda3b26e07a662e422b30e364f169ff18dd32a3bd85c`

Depends on: None. This chunk establishes the scope of the cross-vendor L7
namespace, the evidence snapshot used to justify the design, the problem
statement, and the first eight locked decisions.

Scope: Summary, explicit service set (`0x03/0x05/0x07/0x08/0x09/0x0F/0xFE/
0xFF`), L7 primitive type set, first-delivery MCP surfaces, portal and HA
scope, out-of-scope statements, evidence snapshot, problem statement, and
Locked Decisions 1-8 covering namespace separation, catalog authority,
catalog identity key, Identification/DeviceInfo policy, optional capability
discovery, L7 type primitives, NM adopt-and-extend, and NM runtime wiring.

Idempotence contract: Declarative-only. Reapplying this chunk must not
broaden the service set, reintroduce Vaillant-specific logic into
`ebus_standard`, reopen the catalog to per-device hard-coding, change
`DeviceInfo` semantics, or duplicate the superseded NM plan's normative
text.

Falsifiability gate: Review fails this chunk if it claims `ebus_standard`
shares semantic logic with the Vaillant `0xB5` provider, allows provider
hard-coding instead of catalog generation, promotes Identification results
into a `DeviceInfo` rewrite, treats capability discovery as mandatory, or
rewrites normative sections already merged as
`helianthus-docs-ebus#251/#253/#256`.

Coverage: Summary; Scope; Evidence Snapshot; Problem Statement; Locked
Decisions 1-8 from the canonical plan.

## Summary

- `ebus_standard` is a cross-vendor L7 namespace covering the official eBUS
  Application Layer standard services. It runs in parallel with the
  Vaillant `0xB5` namespace and contains no Vaillant-specific logic.
- The namespace sits above `protocol.Frame`. Framing, CRC, escaping, and
  bus-transaction behaviour are untouched.
- The deprecated plan `ebus-good-citizen-network-management` is adopted
  and extended. Its merged normative docs remain authoritative.
- First delivery is read/list/decode plus catalog-driven NM emit and
  (conditionally) responder. Mutating and destructive surfaces are gated
  by a safety-class model covered in `11-execution-safety-and-surfaces.md`.

## Scope

### Services

`ebus_standard` first lock baseline covers:

- `0x03` Service Data
- `0x05` Burner Control
- `0x07` System Data (includes `0x04` Identification and optional
  `0x03` / `0x05` capability discovery)
- `0x08` Controller-to-Controller
- `0x09` Memory Server
- `0x0F` Test Commands
- `0xFE` General Broadcast
- `0xFF` Network Management (`FF 00`, `FF 01`, `FF 02`, `FF 03`, `FF 04`,
  `FF 05`, `FF 06`)

### L7 primitive types

- `BYTE`
- `CHAR` (explicit byte handling and padding rules)
- `DATA1c` (explicit signedness, replacement-value sentinels)
- variable-length raw payload
- composite BCD (nibble order, invalid-nibble policy)
- length-dependent selector (strict length validation and disambiguation)

### MCP surfaces (first delivery)

- `ebus.v1.ebus_standard.services.list`
- `ebus.v1.ebus_standard.commands.list`
- `ebus.v1.ebus_standard.command.get` (returns `safety_class`)
- `ebus.v1.ebus_standard.decode`
  - input: PB, SB, direction, frame_type, payload hex
  - output: decoded fields, validity, replacement-value status, raw bytes

Live invocation uses `ebus.v1.rpc.invoke` with safety-class gating (see
`11-execution-safety-and-surfaces.md`).

### Portal

Read/list/decode UI only. No invocation UI for
`mutating|destructive|broadcast|memory_write` classes in first delivery.

### Home Assistant

Compatibility checkpoint only. No new entities, no new GraphQL fields.

### Out of first delivery

- Framing/CRC/escaping/bus-transaction changes.
- GraphQL parity.
- GraphQL exposure of mutating/destructive/broadcast/memory-write methods
  (never first delivery).
- Non-optional capability discovery.

## Evidence Snapshot

### Proven

- `0x07 0x04` Identification works through `ebusctl hex -n` on the live
  Vaillant topology (BAI00, NETX3, BASV2, VR_71).
- Gateway already carries a catalog-driven Vaillant `0xB5` provider and an
  `ebus.v1.rpc.invoke` path. Infrastructure can be reused at the
  namespace-isolated helper level.
- Deprecated NM plan produced merged normative docs in
  `helianthus-docs-ebus` PRs `#251`, `#253`, `#256` and a gateway NM
  runtime design. These artifacts are authoritative and are adopted.
- Peer `FF 03/04/05/06` interrogation on the observed Vaillant topology
  did not return useful data; the deprecated plan's finding stands.
- Broadcast-capable send path exists for `0xFE` targets in the existing
  send layer. `FF 00` / `FF 02` can be emitted without responder-mode
  transport support.

### Hypothesis

- `ebusd-tcp` does not support responder-grade local participant behaviour
  (slave-address receive + reply). `M4b2` spike confirms or refutes.
- Vaillant `0xB5` and `ebus_standard` can share L7 primitive types and MCP
  envelope helpers without namespace leakage, if namespace-isolation tests
  are explicit.
- Current gateway NM state-machine design can consume catalog-driven emit
  and responder paths for `0xFF` services without redefining runtime
  state shape.

### Unknown

- Whether `FF 03/04/05/06` responder support ships in first delivery or
  stays gated on `M4b2` outcome.
- Whether `0x09` Memory Server reads available on the live topology are
  safe enough to be `read_only_safe`, or whether they are always
  `read_only_bus_load` or stricter.
- Whether `0x08` Controller-to-Controller observed traffic carries
  identity/provenance information beyond Identification `0x07 0x04`.

## Problem Statement

1. There is no cross-vendor L7 provider. All semantic surface is bound to
   Vaillant `0xB5`. Non-Vaillant devices and standard services are not
   first-class catalog methods.
2. Device identification (`0x07 0x04`) is treated as scan/identity
   plumbing rather than as a cataloged L7 method with a canonical
   descriptor.
3. The deprecated NM plan defined `0xFF` wire behaviour as hand-coded
   handlers on top of a gateway runtime state machine. That leaves `0xFF`
   outside a catalog-driven model and duplicates ownership if a
   standard-services namespace is added later.

Consequences without `ebus_standard`:

- Cross-vendor reverse engineering and validation stay ad-hoc.
- The canonical Identification descriptor remains implicit and cannot be
  consumed by MCP clients as a first-class method.
- Adding the NM wire surface by hand re-introduces provider drift that
  the catalog-driven Vaillant provider already eliminated in its own
  namespace.

## Locked Decisions 1-8

### 1. Separate provider namespace

- `ebus_standard` is cross-vendor and carries no Vaillant-specific logic.
- Vaillant `0xB5` remains a parallel, unchanged namespace.
- Shared L7 primitives, registry lookup, MCP envelope helpers, and method
  identifiers are namespace-isolated with explicit tests.

### 2. Catalog is the single source of truth

- Every `ebus_standard` method is generated from a catalog data file.
- No provider hard-codes per-device behaviour.
- Catalog is SHA-pinned and version-tagged.

### 3. Catalog identity key is explicit and collision-safe

The catalog identity key for each method is the full tuple:

- `namespace` (`ebus_standard`)
- `PB`
- `SB`
- `selector_path` (nullable)
- `telegram_class` (master-slave, master-master, broadcast)
- `direction` (request / response)
- `request_or_response_role`
- `broadcast_or_addressed`
- `answer_policy` (answer-required / no-answer)
- `length_prefix_mode`
- `selector_decoder` identifier
- `service_variant`
- `transport_capability_requirements`
- `version`

Generation MUST fail on duplicate identity keys or ambiguous
length-selector branches. Class-2 broadcast, master-slave broadcast-mode
telegrams, no-answer forms, and typed-payload selectors have explicit
fixtures in `M2`.

### 4. DeviceInfo contract unchanged; Identification is a method result

- `0x07 0x04` produces a canonical `Identification` descriptor with
  fields `manufacturer`, `device_id`, `software_version`,
  `hardware_version`.
- The descriptor is exposed as a method result with provenance metadata.
- It does NOT overwrite `DeviceInfo`. Disagreements with existing
  `DeviceInfo` values are retained with source labels; deterministic
  precedence applies with both sources visible.

### 5. Capability discovery is optional; `capability=unknown` is terminal

- `0x07 0x03` and `0x07 0x05` are opt-in discovery surfaces.
- Devices that do not answer remain `capability=unknown`, a valid terminal
  state. No synthetic capability is invented.

### 6. L7 type primitives are strictly specified

- `BYTE`, `CHAR`, `DATA1c`, variable-length raw, composite BCD, and
  length-dependent selector each have exact byte handling, signedness,
  replacement-value sentinels, nibble ordering, invalid-nibble policy,
  selector length validation, truncated/overlong payload error paths, and
  validity propagation to decode output.
- Golden vectors are required for each primitive and cover positive AND
  negative cases.

### 7. `ebus_standard` subsumes the locked NM plan via adopt-and-extend

- `ebus-good-citizen-network-management` is superseded by `ebus_standard`.
- Merged normative docs `#251`, `#253`, `#256` in `helianthus-docs-ebus`
  remain authoritative. M0 inventories them, marks kept-verbatim sections
  with attribution, adopts them as subchapters under `ebus_standard`
  ownership, and adds an ownership preface plus migration appendix.
- M0 does NOT duplicate or rewrite the normative text.
- The superseded plan transitions to `.maintenance` only after `M6b`
  reconciles cross-links, issue map, and canonical IDs.

### 8. NM runtime state stays in gateway; wire services are catalog-driven

- `NMInit/NMReset/NMNormal`, target configuration, cycle-time monitoring,
  self-monitoring, status chart, net status, and start flag remain owned
  by the gateway runtime as designed in the deprecated NM plan.
- `0xFF 00/01/02/03/04/05/06` and `07 FF` are catalog entries in
  `ebus_standard`. The gateway NM runtime consumes catalog metadata to
  emit broadcasts and drive responder replies.
- After `M4c2` merges, no hand-coded `FF` command handler survives in the
  gateway. `M4_GATEWAY_MCP` landing completes wiring for the broadcast
  subset; the responder subset lands only if `M4b2` signals go.
