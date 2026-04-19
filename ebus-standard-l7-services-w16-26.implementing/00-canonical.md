# eBUS Standard L7 Services Namespace (`ebus_standard`)

State: `locked`
Slug: `ebus-standard-l7-services-w16-26`
Locked on: `2026-04-18`
Canonical revision: `v1.0-locked`

## Summary

`ebus_standard` is a new L7 provider namespace for Helianthus that carries the
official eBUS Application Layer standard services. It is a cross-vendor,
catalog-driven surface applicable to any eBUS-conformant device. It runs in
parallel with the existing Vaillant `0xB5` provider namespace and does not
reuse Vaillant-specific logic.

`ebus_standard` sits strictly above `protocol.Frame`. Framing, CRC, escaping,
and bus-transaction behaviour are unchanged. Device identification
(`0x07 0x04`) is a catalog entry in this namespace, not a hand-coded path in
scan/identity code.

`ebus_standard` subsumes the locked plan
`ebus-good-citizen-network-management`. That plan's R&D remains authoritative
as enrichment: its merged normative docs in `helianthus-docs-ebus` (PRs
`#251`, `#253`, `#256`) and its issue map stay canonical. They are adopted
and extended under this plan's ownership rather than rewritten. The
superseded plan transitions to `.maintenance` only after this plan's M6b
reconciles cross-links and issue states.

## Scope

Services in `ebus_standard` first lock baseline:

- `0x03` Service Data
- `0x05` Burner Control
- `0x07` System Data (includes `0x04` Identification and optional `0x03` /
  `0x05` capability discovery)
- `0x08` Controller-to-Controller
- `0x09` Memory Server
- `0x0F` Test Commands
- `0xFE` General Broadcast
- `0xFF` Network Management (including `FF 00`, `FF 01`, `FF 02`, `FF 03`,
  `FF 04`, `FF 05`, `FF 06`)

L7 primitive types ebus_standard must decode and (where relevant) encode:

- `BYTE`
- `CHAR` (explicit byte handling and padding rules)
- `DATA1c` (explicit signedness, replacement-value sentinels)
- variable-length raw payload
- composite BCD (nibble order, invalid-nibble policy)
- length-dependent selector (strict length validation and branch
  disambiguation)

First-delivery MCP surfaces (required):

- `ebus.v1.ebus_standard.services.list`
- `ebus.v1.ebus_standard.commands.list`
- `ebus.v1.ebus_standard.command.get` (includes `safety_class`)
- `ebus.v1.ebus_standard.decode`
  - input: PB, SB, direction, frame_type, payload hex
  - output: decoded fields, validity, replacement-value status, raw bytes

Live invocation routes through the existing `ebus.v1.rpc.invoke`. No new
execution path is introduced. The invocation path enforces a safety-class
default-deny policy (see Locked Decisions §9).

Portal (vrc-explorer) first-delivery scope: read/list/decode UI only.
Invocation UI for methods with `safety_class in {mutating, destructive,
broadcast, memory_write}` is NOT shipped in first delivery.

Home Assistant integration: first delivery is a compatibility checkpoint
only. No new HA entities, no new GraphQL fields, no consumer rollout. This
plan must prove identity-provenance changes do not alter HA-visible
contracts.

Explicitly out of first delivery:

- Framing/CRC/escaping/bus-transaction changes.
- GraphQL parity for `ebus_standard`. GraphQL waits on MCP semantic lock.
- GraphQL exposure of `mutating|destructive|broadcast|memory_write`
  methods (never first delivery).
- Non-optional capability discovery. `capability=unknown` is a valid
  terminal state.

## Evidence Snapshot

### Proven

- `0x07 0x04` Identification works through `ebusctl hex -n` on the live
  Vaillant topology (BAI00, NETX3, BASV2, VR_71).
- The gateway already carries a catalog-driven Vaillant `0xB5` provider and
  an `ebus.v1.rpc.invoke` path that can be reused for routing without
  re-implementing transport.
- The locked `ebus-good-citizen-network-management` plan produced merged
  normative docs in `helianthus-docs-ebus` PRs `#251`, `#253`, `#256`, and
  a gateway NM runtime design (NMInit/NMReset/NMNormal, target
  configuration, cycle-time monitoring, self-monitoring, status chart, net
  status, start flag). These artifacts remain authoritative and are
  adopted, not rewritten.
- Peer `FF 03/04/05/06` interrogation on the observed Vaillant installation
  did not return useful data, matching the locked NM plan's finding.
- Broadcast-capable send path already exists for `0xFE` targets in the
  existing send layer; `FF 00` / `FF 02` can be originated without
  responder-mode transport support.

### Hypothesis

- `ebusd-tcp` does not support responder-grade local participant behaviour
  (slave-address receive + reply). `M4b` spike confirms or refutes.
- The existing Vaillant `0xB5` provider and `ebus_standard` can share L7
  primitive types and MCP envelope helpers without namespace leakage, if
  namespace-isolation tests are explicit.
- Current gateway NM state-machine design can consume catalog-driven emit
  and responder paths for `0xFF` services without redefining its
  runtime-state shape.

### Unknown

- Whether `FF 03/04/05/06` responder support ships in first delivery or
  stays gated on `M4b` feasibility outcome.
- Whether any `0x09` Memory Server reads present on the live topology are
  safe enough to be `read_only_safe`, or whether they are always
  `read_only_bus_load` or stricter.
- Whether `0x08` Controller-to-Controller observed traffic carries
  information relevant to identity/provenance beyond what Identification
  `0x07 0x04` already provides.

## Problem Statement

The current stack has three gaps relative to eBUS standard L7 services:

1. There is no cross-vendor L7 provider. All semantic surface is bound to
   the Vaillant `0xB5` namespace. Non-Vaillant devices and standard
   services are inaccessible as first-class catalog methods.
2. Device identification (`0x07 0x04`) is treated as scan/identity
   plumbing rather than as a cataloged L7 method with a canonical
   descriptor.
3. The locked NM plan defined 0xFF wire behaviour as hand-coded handlers
   on top of a gateway runtime state machine, which leaves 0xFF outside a
   catalog-driven model and duplicates ownership if a standard-services
   namespace is added later.

Consequences without `ebus_standard`:

- Cross-vendor reverse engineering and validation stay ad-hoc.
- The canonical identification descriptor remains implicit and cannot be
  consumed by MCP clients as a first-class method.
- Adding the NM wire surface by hand re-introduces provider drift that
  the catalog-driven Vaillant provider already eliminated in its own
  namespace.

## Locked Decisions

### 1. `ebus_standard` is a separate provider namespace from Vaillant `0xB5`

- `ebus_standard` is cross-vendor and must not contain any
  Vaillant-specific logic.
- Vaillant `0xB5` remains a parallel, unchanged namespace.
- Shared L7 primitives, registry lookup, MCP envelope helpers, and method
  identifiers are namespace-isolated with explicit tests.

### 2. Catalog is the single source of truth for methods

- Every method in `ebus_standard` is generated from a catalog data file.
- No provider hard-codes per-device behaviour.
- Catalog is SHA-pinned and version-tagged.

### 3. Catalog identity key is explicit and collision-safe

The catalog identity key for each method is the full tuple:

- `namespace` (`ebus_standard`)
- `PB`
- `SB`
- `selector_path` (nullable)
- `telegram_class` (e.g. master-slave, master-master, broadcast)
- `direction` (request / response)
- `request_or_response_role`
- `broadcast_or_addressed`
- `answer_policy` (answer-required / no-answer)
- `length_prefix_mode`
- `selector_decoder` identifier
- `service_variant`
- `transport_capability_requirements`
- `version`

Generation fails on duplicate identity keys or on ambiguous
length-selector branches. Class-2 broadcast, master-slave broadcast-mode
telegrams, no-answer forms, and typed-payload selectors have explicit
fixtures.

### 4. `DeviceInfo` contract unchanged; Identification is a method result

- `0x07 0x04` produces a canonical `Identification` descriptor with fields
  `manufacturer`, `device_id`, `software_version`, `hardware_version`.
- The descriptor is exposed as a method result with provenance metadata.
- It does NOT overwrite `DeviceInfo`. Disagreements between
  `ebus_standard` Identification and existing `DeviceInfo` values are
  retained with source labels. Consumers apply deterministic precedence
  with both sources visible.

### 5. Capability discovery is optional; `capability=unknown` is terminal

- `0x07 0x03` and `0x07 0x05` are opt-in discovery surfaces.
- Devices that do not answer remain `capability=unknown`, which is a
  valid terminal state. No synthetic capability is invented.

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
  remain authoritative. `ebus_standard` M0 inventories them, marks the
  kept-verbatim sections with attribution, adopts them as subchapters
  under `ebus_standard` ownership, and adds an ownership preface plus
  migration appendix.
- `ebus_standard` M0 does NOT duplicate or rewrite the normative text.
- The superseded plan transitions to `.maintenance` only after M6b
  reconciles cross-links, issue map, and canonical IDs.

### 8. NM runtime state machine stays in the gateway; wire services are cataloged

- `NMInit/NMReset/NMNormal`, target configuration, cycle-time monitoring,
  self-monitoring, status chart, net status, and start flag remain owned
  by the gateway runtime as designed in the locked NM plan.
- `0xFF 00/01/02/03/04/05/06` and `07 FF` are catalog entries in
  `ebus_standard`. The gateway NM runtime consumes catalog metadata to
  emit broadcasts and drive responder replies.
- After M4c2 merges, no hand-coded `FF` command handler survives in the
  gateway.

### 9. Execution-safety policy: safety classes and default-deny

Each catalog method declares a `safety_class`:

- `read_only_safe`
- `read_only_bus_load`
- `mutating`
- `destructive`
- `broadcast`
- `memory_write`

First-delivery execution policy:

- `rpc.invoke` accepts `read_only_safe` and `read_only_bus_load`.
- `rpc.invoke` default-denies `mutating`, `destructive`, `broadcast`,
  `memory_write`.
- Default-deny applies to any user-facing caller and to every internal
  caller EXCEPT a single named caller context
  `caller_context=system_nm_runtime` that carries a compile-time
  whitelist.

The `system_nm_runtime` whitelist is keyed by the full catalog identity
tuple (see §3). The whitelist in first delivery is exactly:

- `0xFF 00` broadcast (NM reset status on join/reset)
- `0xFF 02` broadcast (NM failure signal)
- `0xFF 03` responder (net status)
- `0xFF 04` responder (monitored participants)
- `0xFF 05` responder (failed nodes)
- `0xFF 06` responder (required services)
- `0x07 FF` broadcast (sign of life, cadence-floor gated)

Each entry is pinned to the exact variant by namespace, PB, SB,
telegram_class, direction, role, broadcast_or_addressed, answer_policy,
service_variant, and transport_capability_requirements. Adjacent variants
with the same PB/SB but a different axis remain denied. A test proves
deny-parity across adjacent variants.

The whitelist is a compile-time constant in first delivery. It cannot be
widened at runtime. Every invocation through it produces a structured
audit log. A general operator override path is out of scope for first
delivery.

### 10. Single execution-policy module

- One shared execution-policy module is consulted by `rpc.invoke`,
  generated provider methods, and the NM runtime.
- All three call the same policy function with the caller context.
- Tests prove denial parity: direct provider invocation and MCP
  `rpc.invoke` deny identical sets by default; the `system_nm_runtime`
  whitelist is honoured only from the NM runtime call site.

### 11. GraphQL parity is gated on MCP semantic lock

- GraphQL parity begins only after `M4B_read_decode_lock` freezes the
  list/get/decode envelope shape and `M4D_responder_lock` freezes
  responder capability/status fields where relevant.
- `mutating|destructive|broadcast|memory_write` methods NEVER appear in
  GraphQL in first delivery.

### 12. Portal consumer rollout is gated on semantic lock and hardened

- Portal read/list/decode UI depends on `M4B_read_decode_lock`.
- Portal responder UI (if any) depends on `M4D_responder_lock`.
- Portal decode sandbox enforces: strict hex validation, max payload
  length, max decoded-field count, worker/timeout isolation, HTML
  escaping for CHAR/raw/catalog strings, no unsafe Markdown or HTML
  rendering. Tests cover malformed hex, huge input, invalid CHAR bytes,
  and replacement-value display.

### 13. Shared-infrastructure isolation between providers

- Namespace-isolation tests cover: shared codec, registry lookup,
  generated method identifiers, MCP envelope helpers, catalog
  versioning.
- A regression proves Vaillant `0xB5` quirks do not affect
  `ebus_standard` decode results and vice versa.

### 14. Responder feasibility is a dedicated spike

- The responder feasibility spike that existed as `M7a` in the deprecated
  NM plan moves into this plan as `M4b1` (transport primitives in
  `helianthus-ebusgo`) plus `M4b2` (gateway capability observation and
  go/no-go signal).
- If proxy or firmware changes prove necessary, new issues are opened in
  `helianthus-ebus-adapter-proxy` or firmware repositories with explicit
  dependency edges. They do NOT ride inside `M4b`.

## Execution Safety Policy (normative summary)

- User-facing `rpc.invoke`: accept `read_only_safe`,
  `read_only_bus_load`. Deny everything else.
- NM runtime (`caller_context=system_nm_runtime`): additionally accept
  the compile-time whitelist above, matched by full catalog identity.
- Any other caller context (`ebus_standard` direct provider invocation,
  future runtime callers): accept the user-facing set and nothing else
  unless a future locked plan names and scopes a new caller context.
- Audit: every allowed invocation in `system_nm_runtime` is logged with
  catalog identity, caller, timestamp, and outcome.
- Widening the whitelist, adding caller contexts, or exposing
  mutating/destructive/broadcast/memory-write surfaces via GraphQL is a
  new locked-plan decision, not a code change.

## Target Repositories

- `helianthus-docs-ebus` — normative catalog, type rules, safety policy,
  NM adopt-and-extend, transport matrix publication.
- `helianthus-ebusgo` — L7 type primitives, responder transport
  primitives.
- `helianthus-ebusreg` — catalog schema + data, generic provider.
- `helianthus-ebusgateway` — MCP surfaces, execution-policy module,
  `rpc.invoke` integration, NM runtime wiring to catalog, responder
  runtime, matrix artifact.
- `helianthus-vrc-explorer` — portal read/list/decode UI with hardening.
- `helianthus-ha-integration` — compatibility checkpoint only
  (`M5b_HA_NOOP_COMPAT`), no consumer rollout first delivery.

Conditional (not in target_repos; opened as new issues if `M4b`
requires):

- `helianthus-ebus-adapter-proxy`
- firmware repositories

## Delivery Order

1. `helianthus-docs-ebus` (`M0`).
2. `helianthus-ebusgo` (`M1`).
3. `helianthus-ebusreg` (`M2`, `M3`).
4. `helianthus-ebusgateway` (`M4`, `M4B`).
5. Responder lane: `M4b1` (ebusgo) → `M4b2` (gateway) → `M4c1` (ebusgo)
   → `M4c2` (gateway) → `M4D` (gateway).
6. `helianthus-vrc-explorer` (`M5`), `helianthus-ha-integration` (`M5b`).
7. `M6a` (gateway matrix artifact) → `M6b` (docs publication and NM plan
   deprecation close-out).

## Milestone Plan

| Milestone | Scope | Repo | Depends on | Result |
| --- | --- | --- | --- | --- |
| `M0_DOC_GATE` | Normative catalog, type rules, safety policy, NM adopt-and-extend preface + migration appendix | `helianthus-docs-ebus` | none | Normative source frozen; merged docs `#251/#253/#256` adopted in-place |
| `M1_TYPES` | L7 primitive types with positive and negative golden vectors | `helianthus-ebusgo` | `M0` | Type primitives locked |
| `M2_CATALOG` | Catalog schema, YAML data, identity key model (§3), collision test, SHA pinning | `helianthus-ebusreg` | `M0` | Catalog is a versioned artifact |
| `M3_PROVIDER` | Generic `ebus_standard` provider, catalog-driven method generation, identity/provenance policy, namespace-isolation tests, feature-flag disable switch | `helianthus-ebusreg` | `M2` | Provider plan stable in registry |
| `M4_GATEWAY_MCP` | MCP `services.list`/`commands.list`/`command.get`/`decode`, execution-policy module (§10), `rpc.invoke` safety gating, NM runtime wiring to catalog | `helianthus-ebusgateway` | `M1`, `M3` | MCP surfaces live; NM emit routed through catalog |
| `M4B_read_decode_lock` | Freeze envelope shape for `list/get/decode`, safety metadata names, error schema, replacement-value schema, catalog version reporting | `helianthus-ebusgateway` | `M4` | Semantic lock for read/decode consumers |
| `M4b1` | Transport feasibility primitives for slave-address receive/reply on ENH/ENS | `helianthus-ebusgo` | `M1` | Responder substrate available |
| `M4b2` | Gateway capability observation + go/no-go signal | `helianthus-ebusgateway` | `M4b1` | Responder feasibility answered |
| `M4c1` | Transport support for responder-mode frames on approved transports | `helianthus-ebusgo` | `M4b2=go` | Transport substrate for responder |
| `M4c2` | Responder runtime for `07 04` + `FF 03/04/05/06`, driven by catalog | `helianthus-ebusgateway` | `M4c1` | Responder lane live where supported |
| `M4D_responder_lock` | Freeze responder capability/status fields in MCP | `helianthus-ebusgateway` | `M4c2` | Semantic lock for responder consumers |
| `M5_PORTAL` | Portal read/list/decode UI with hardening; no invocation UI for denied classes | `helianthus-vrc-explorer` | `M4B` | Operator-visible inspection surface |
| `M5b_HA_NOOP_COMPAT` | HA compatibility checkpoint: no new entities or fields; identity/provenance regression | `helianthus-ha-integration` | `M4B` | HA-visible contracts unchanged |
| `M6a` | Live-bus matrix artifact: offline conformance vectors, Vaillant regression transcripts, NM wire regression, 07 FF cadence floor, rollback criteria | `helianthus-ebusgateway` | `M4B`, `M4D`, `M5`, `M5b` | Deployment-grade proof |
| `M6b` | Matrix publication in docs; NM plan deprecation close-out; issue map reconciliation | `helianthus-docs-ebus` | `M6a` | Superseded plan transitions to `.maintenance` |

## Canonical Issues

| ID | Repo | Summary |
| --- | --- | --- |
| `ISSUE-DOC-EBS-00` | `helianthus-docs-ebus` | Normative ebus_standard catalog (services 0x03/0x05/0x07/0x08/0x09/0x0F/0xFE/0xFF) with adopt-and-extend of NM docs `#251/#253/#256` |
| `ISSUE-DOC-EBS-01` | `helianthus-docs-ebus` | L7 type rules: BYTE/CHAR/DATA1c/raw/BCD/length-selector exact semantics |
| `ISSUE-DOC-EBS-02` | `helianthus-docs-ebus` | Execution-safety policy: safety classes, default-deny, `system_nm_runtime` whitelist contract |
| `ISSUE-GO-EBS-01` | `helianthus-ebusgo` | Implement L7 type primitives with positive+negative golden vectors |
| `ISSUE-GO-EBS-02` | `helianthus-ebusgo` | Transport feasibility primitives for slave-address receive/reply (M4b1) |
| `ISSUE-GO-EBS-03` | `helianthus-ebusgo` | Transport support for responder-mode frames (M4c1) |
| `ISSUE-REG-EBS-01` | `helianthus-ebusreg` | Catalog schema + data file + identity key model + collision test + SHA pinning |
| `ISSUE-REG-EBS-02` | `helianthus-ebusreg` | Generic `ebus_standard` provider with catalog-driven method generation, identity provenance, disable switch |
| `ISSUE-REG-EBS-03` | `helianthus-ebusreg` | Namespace-isolation tests vs Vaillant 0xB5 (codec, registry lookup, envelope helpers) |
| `ISSUE-GW-EBS-01` | `helianthus-ebusgateway` | MCP surfaces: `services.list`, `commands.list`, `command.get`, `decode` |
| `ISSUE-GW-EBS-02` | `helianthus-ebusgateway` | Execution-policy module + `rpc.invoke` safety gating + `caller_context` enforcement |
| `ISSUE-GW-EBS-03` | `helianthus-ebusgateway` | NM runtime wiring to catalog-driven emit and responder paths |
| `ISSUE-GW-EBS-04` | `helianthus-ebusgateway` | Gateway capability observation + go/no-go for responder feasibility (M4b2) |
| `ISSUE-GW-EBS-05` | `helianthus-ebusgateway` | Responder runtime for `07 04` + `FF 03/04/05/06` (M4c2) |
| `ISSUE-GW-EBS-06` | `helianthus-ebusgateway` | `M4B_read_decode_lock` semantic-lock artifact |
| `ISSUE-GW-EBS-07` | `helianthus-ebusgateway` | `M4D_responder_lock` semantic-lock artifact |
| `ISSUE-GW-EBS-08` | `helianthus-ebusgateway` | Live-bus matrix artifact (M6a): offline vectors, Vaillant regression, NM regression, cadence enforcement, rollback criteria |
| `ISSUE-VRC-EBS-01` | `helianthus-vrc-explorer` | Portal read/list/decode UI with hardened decode sandbox |
| `ISSUE-HA-EBS-01` | `helianthus-ha-integration` | Compatibility checkpoint: prove no HA-visible contract changes from identity/provenance shifts |
| `ISSUE-DOC-EBS-03` | `helianthus-docs-ebus` | Matrix publication + NM plan `.maintenance` transition + issue map reconciliation (M6b) |

Conditional (opened only if `M4b2` requires):

| ID | Repo | Summary |
| --- | --- | --- |
| `ISSUE-PROXY-EBS-01` | `helianthus-ebus-adapter-proxy` | Conditional responder-path mediation, opened with explicit dependency edges only if `M4b` proves it needed |

## Acceptance Criteria

- Normative catalog and type rules are frozen in `helianthus-docs-ebus`
  with adopt-and-extend of merged PRs `#251/#253/#256`. No normative
  rewrite of adopted sections.
- L7 type primitives decode and encode correctly for positive and
  negative golden vectors. Validity and replacement-value status
  propagate to decode output.
- Catalog generation fails on duplicate identity keys and on ambiguous
  length-selector branches. Catalog carries a version and SHA.
- Generic `ebus_standard` provider is registered in the registry with a
  stable plan name and a feature-flag disable switch. `DeviceInfo`
  contract is unchanged. Identification descriptors never silently
  overwrite existing `DeviceInfo` values; disagreements retain both
  sources with labels.
- Namespace-isolation tests pass: Vaillant `0xB5` quirks do not affect
  `ebus_standard` decode results and vice versa. Shared codec, registry
  lookup, generated identifiers, and MCP envelope helpers are isolated.
- MCP surfaces `ebus.v1.ebus_standard.services.list` /
  `.commands.list` / `.command.get` / `.decode` ship with declared
  envelope shapes. `command.get` includes `safety_class`. `decode`
  accepts PB, SB, direction, frame_type, payload hex and returns
  decoded fields, validity, replacement-value status, and raw bytes.
- `rpc.invoke` default-denies `mutating|destructive|broadcast|memory_write`
  methods for every caller context except `system_nm_runtime`, which is
  restricted to the compile-time whitelist keyed by full catalog
  identity. Deny-parity tests pass across adjacent variants.
- NM runtime emits `FF 00`, `FF 02`, and (optionally) `07 FF` through
  catalog-driven paths after `M4c2`. Responder replies to
  `FF 03/04/05/06` ship only on transports approved by `M4b2` and after
  `M4c2`; `ebusd-tcp` documents the no-responder outcome if confirmed.
- `M4B_read_decode_lock` and `M4D_responder_lock` artifacts freeze
  envelope and responder-field shapes before portal and HA checkpoint
  milestones start.
- Portal decode sandbox enforces hex validation, size caps, worker
  timeout isolation, HTML escaping, and no unsafe Markdown/HTML
  rendering. Tests cover malformed hex, oversized input, invalid CHAR
  bytes, and replacement-value display.
- HA integration carries no new entities, no new GraphQL fields, and no
  change to HA-visible contracts. Regression tests cover identity and
  provenance paths.
- `M6a` publishes offline conformance vectors plus Vaillant live-bus
  regression transcripts across transports. Rollback criteria are
  documented per repo: catalog version pinning, provider disable
  switch, MCP surface back-compat policy, documented revert path.
- `M6b` transitions `ebus-good-citizen-network-management` to
  `.maintenance` with cross-links and issue map reconciled. Merged docs
  `#251/#253/#256` remain authoritative; this plan's canonical carries
  the ownership preface and migration appendix.

## Risks

| # | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| 1 | Catalog identity key still misses an eBUS dispatch axis (service-specific length prefix, class-2 broadcast, typed-payload selector) | HIGH | explicit fixtures per axis in `M2`; generation collision test; §3 identity tuple enumerated |
| 2 | Execution-safety whitelist drift lets adjacent variants execute under `system_nm_runtime` | HIGH | whitelist keyed by full catalog identity tuple; deny-parity tests across adjacent variants; single execution-policy module |
| 3 | Responder lane requires proxy or firmware changes not visible from gateway code | HIGH | `M4b1`+`M4b2` dedicated feasibility spike; out-of-scope repos get new issues with explicit dependency edges |
| 4 | Portal decode sandbox becomes an XSS/size-bomb/UI-lockup vector | MEDIUM | hardening acceptance in `M5` (hex validation, size caps, worker timeout, HTML escape, no unsafe markup) |
| 5 | NM plan deprecation breaks traceability of merged docs `#251/#253/#256` | MEDIUM | adopt-and-extend; no rewrite; ownership preface + migration appendix; `.maintenance` transition only after reconciliation in `M6b` |
| 6 | Shared infrastructure lets Vaillant `0xB5` quirks leak into `ebus_standard` decode | MEDIUM | namespace-isolation tests in `M3`; regression fixtures independent of Vaillant |
| 7 | `M4B` semantic lock premature relative to responder fields added by `M4c2` | MEDIUM | split into `M4B_read_decode_lock` and `M4D_responder_lock`; portal responder UI (if any) gates on `M4D` |
| 8 | HA-visible contracts change silently through identity/provenance shifts | MEDIUM | `M5b_HA_NOOP_COMPAT` compatibility checkpoint; identity regression tests |
| 9 | `rpc.invoke` gating and provider-direct invocation diverge in denial policy | MEDIUM | single execution-policy module; denial-parity tests across entry points |
| 10 | Operator override deferral blocks legitimate maintenance execution | LOW | `system_nm_runtime` whitelist covers required NM emit/responder; operator override is an explicit future locked-plan decision, not a silent code change |
