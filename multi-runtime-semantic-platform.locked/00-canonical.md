# Helianthus Multi-Runtime Semantic Platform

Revision: `v1.1-locked-amended`
Date: `2026-07-10`
Status: `Locked`
Cruise phase: `RECOVERY_RECONCILIATION`
Current milestone: `RECOVERY_RECONCILIATION`
Amendment count: `1`
Amendment: `AD-DOCS-01 external-only-documentation`
Accepted through: `MSP-03C plus merged MSP-03D EEBUS-G01 fake-peer harness only`
Dirty rescue candidate: `true`
Successor unlocks: `false until MSP-R00-L and MSP-03D-R merge from clean main`
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

This locked plan records five accepted adversarial rounds plus the accepted
AD-DOCS-01 amendment. It preserves the true historical evidence through M0,
M1, M2, MSP-03A, MSP-03B, MSP-03C, and the merged MSP-03D EEBUS-G01 fake-peer
harness slice, but it does not claim dirty rescue code as accepted plan
evidence.

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

## Recovery Reconciliation Lock State

The plan is locked while runtime execution is paused in
`RECOVERY_RECONCILIATION`.

- `accepted_through` is exactly `MSP-03C plus merged MSP-03D EEBUS-G01
  fake-peer harness only`.
- M3 and MSP-03D remain open. The merged fake-peer harness is useful evidence,
  not completion of MSP-03D.
- `dirty_rescue_candidate=true` records that useful local rescue work may
  exist, but dirty code has no acceptance authority and unlocks no successors.
- `successor_unlocks=false` until the reconciliation gates merge from clean
  main.
- `MSP-R00` is completed locally with no code acceptance, no successor unlock,
  issue `Project-Helianthus/helianthus-eebusreg#14`, and architecture review
  `PASS`.
- Initial ready rows are limited to `MSP-R00-L` and `DOCS-VERIFY`.

`MSP-R00` is an `helianthus-eebusreg` recovery row with no predecessor. It
completed locally and produced only a candidate input for public ledger review.
It gives no code acceptance and unlocks no runtime successor. Public plan
artifacts must not publish the local commit SHA, private paths, raw HMAC
mapping, source-bundle details, packet captures, raw transcripts, keys, PEM
blocks, tokens, trust stores, raw SKI, raw SHIPID, raw IP/MAC address, raw
serial values, or raw hashes.

`MSP-R00-L` is the serialized `helianthus-execution-plans` publication row. It
depends on MSP-R00, reviews and publishes only the public-safe redacted ledger,
and must merge before documentation migration and MSP-03D-R can start. Public
evidence uses random nonsemantic per-publication opaque IDs only. The only
public classes are `public_redacted`, `private_restricted`, and `discarded`.
Public commitment covers opaque IDs, classes, dispositions, and redaction
metadata only. Raw HMACs and opaque-ID mappings stay private. No public ledger
may expose raw or identifying paths, volume, sizes, timestamps, byte counts,
deterministic IDs, raw hashes, rescue commits, source bundles, packet captures,
transcripts, credentials, trust stores, or device identities.

`DOCS-VERIFY` is a blocking `helianthus-docs-eebus` check. It verifies license,
canonical owners, issue template compliance, path layout, and cross-seeding
from `helianthus-docs-eebus` back to `helianthus-docs-ebus` where durable
cross-protocol facts exist.

## AD-DOCS-01 External-Only Documentation Invariant

`helianthus-eebusreg` and its clean-main branches must contain no `docs/`
directory and must own no substantive protocol, architecture, API, harness,
test, or user documentation. Only exact minimal README entry/status/build
pointers and concise Go package metadata comments may remain. Those pointers
may link only to manifest-state `active` pages or pre-existing stable landing
pages.

Documentation ownership is exclusive:

- `helianthus-docs-eebus/protocols/` owns eeBUS/SHIP/SPINE protocol behavior.
- `helianthus-docs-eebus/architecture/` owns eeBUS runtime, adapter, trust,
  persistence, and lifecycle architecture.
- `helianthus-docs-eebus/api/` owns eeBUS-specific Go public API schema,
  reference, and examples.
- `helianthus-docs-eebus/devices/`, `evidence/`, and `re-notes/` remain valid
  native roots for device notes, public-safe evidence, and reverse-engineering
  notes.
- `helianthus-docs-ebus/docs/platform/` owns language-neutral cross-runtime
  envelopes, hash/auth binding, shared registry boundary, and
  promotion/consumer rules.

Every page has `canonical_source`. Duplication is forbidden.

The ownership manifest supports four states:

- `planned`: the path may be absent, is noncanonical and nonlinkable, records a
  source issue/PR, and expires after 14 days.
- `candidate`: the path exists only in a candidate area, is hidden from stable
  outputs, records source PR/head/hash, and expires after 30 days.
- `active`: the path exists and is approved/frozen.
- `withdrawn`: the path is excluded and mandatory cleanup removes artifacts.

PR CI uses combined refs across source and docs repos. Main CI enforces
expiry. Owner/source pairs are globally unique. Cross-repo checks use clean
clones, explicit refs, pinned tools, and no absolute paths. Platform pages
merge first without forward links; eeBUS pages link only merged active platform
pages. README links point only to active/stable targets.

Candidate API documentation uses an explicit handshake:

- only org-owned `Project-Helianthus` branches are valid; forks are rejected;
- after `MSP-036`, the single `MSP-055` source PR may be prepared and pinned at
  an immutable candidate-ready head, but it remains merge-blocked;
- no force-push may occur after docs preparation;
- `helianthus-eebusreg` CI produces a normalized manifest plus GitHub OIDC
  DSSE/in-toto attestation;
- predicate verification binds issuer, workflow identity, org repo, ref,
  immutable head SHA, run id, run attempt, extractor version, schema version,
  clean checkout, and manifest digest;
- `helianthus-docs-eebus` commits the candidate manifest copy plus provenance
  and merges first;
- `MSP-DOCS-API-CANDIDATE` must complete before `MSP-055`; the eebusreg merge
  gate requires an exact match to the current source head, and any source push
  invalidates the candidate and re-blocks the source PR;
- abandoned or expired candidates activate the cleanup row, move entries to
  `withdrawn`, remove candidate artifacts, and restore docs main green.

The extractor implementation lives in `helianthus-eebusreg/internal/apiboundary`.
Schema and specification docs live in `helianthus-docs-eebus/api`. The
manifest is a CI artifact, never code-local documentation. Version 1
normalization is deterministic over package, symbol, type, and signature, with
stable ordering and no formatting, internal, or unexported noise.

`MSP-DOCS-CLEAN` is mechanical and portable. It rejects tracked or untracked
`docs/**`, symlinks, absolute paths, traversal, casefold collisions, extra
Markdown beyond the allowlist, non-template README content, and substantive
package comments through AST allow/deny rules. It includes positive and
negative fixtures and runs on Linux plus macOS or portable casefold emulation.
Path-safety and `canonical_source` gates are mirrored in the docs-owned roots.

Rollback is forward-only. `docs/` is never restored to eebusreg main. Any
break-glass restoration needs explicit owner approval, blocks all successors,
and creates cleanup work.

Recovered dirty docs are not facts. Publishable evidence IDs are required; if
they are absent, material is only candidate or hypothesis with a falsifier.

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
black-box fake-peer plus revised live VR940f access gates. M3 uses only
disposable proof credentials and makes no production trust guarantee.

Gate: the facade compiles, MSP-03C remains accepted, EEBUS-G01 remains
accepted, and clean-main MSP-03D-R passes both revised G17 and G19 with owner
acceptance. Revised G17 proves configured local SHIP advertisement/discovery,
myVaillant trust visibility, and negative/TTL behavior; it is not evidence
that the VR940f advertises a server. G19 proves direct outbound VR940f
TCP/TLS/WebSocket/SHIP access completion plus first post-access SPINE data.
Feature graph completeness and reconnect durability belong to MSP-055/M6, not
G17.

### M3.5 - Raw Runtime Contract Freeze

After MSP-R00-L, DOCS-VERIFY, MSP-DOCS-API-SCHEMA, MSP-DOCS-PLATFORM,
MSP-DOCS-E2, MSP-DOCS-CLEAN, and MSP-03D-R merge from clean main, freeze only
raw identity, raw snapshot envelope, and evidence object shapes in MSP-035.
Trust, pairing, admin state, lifecycle authority, availability guarantees, and
final MCP v1 remain unfrozen until later rows.

Gate: raw snapshot and evidence fixtures replay deterministically.

### M4 - Store, Raw View, Lifecycle Facade, And Trust Security

The clean-main serialized eebusreg sequence is:

1. `MSP-DOCS-CLEAN`: delete any code-repo docs and install ownership/API gates.
2. `MSP-03D-R`: G17+G19 harness and canonical recovery evidence.
3. `MSP-035`: raw identity/snapshot/evidence freeze.
4. `MSP-04A`: internal persistent store/schema only.
5. `MSP-036`: public immutable raw view only.
6. `MSP-DOCS-API-CANDIDATE`: merge hidden candidate API docs and the exact-head
   manifest/provenance while the single `MSP-055` source PR remains unmerged.
7. `MSP-055`: merge the disabled-by-default read-only lifecycle facade only
   after its current head exactly matches the merged candidate.
8. `MSP-DOCS-API-FREEZE`: promote the exact public Go API docs from candidate
   to active.
9. `MSP-04B`: first-trust/OOB/admin-local gated flow.
10. `MSP-04C`: restore, revocation, quarantine, and repair.

`MSP-036` can export only versioned immutable raw snapshot/view fields. It
must not export semantic device IDs, lifecycle authority, trust/pairing
mutation, or an availability guarantee. It depends on the internal store schema
and migration/conformance tests.

`MSP-055` is disabled by default. Its public lifecycle facade is read-only.
Outbound sockets require explicit configuration plus pre-seeded trust or an
allowlist. Public trust and pairing mutations are forbidden. First-trust, OOB
confirmation, and admin mutation remain later admin-local gated work.

Gate: no production listener can open unless eeBUS is enabled, interface/subnet
are explicit, the store is valid, pre-seeded trust or allowlist permits the
operation, and the relevant later trust state permits listening.

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

Gate: gateway import is blocked until prior canonical docs and eebusreg
contracts merge. Disabled default opens no eeBUS sockets, creates no trust
files, and leaves existing eBUS MCP, GraphQL, Portal, HA, and transport-matrix
behavior unchanged.

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
- Keep only language-neutral platform contracts canonical in
  `helianthus-docs-ebus/docs/platform/`. eeBUS protocol, runtime architecture,
  trust/lifecycle, and public API knowledge is canonical in the corresponding
  `helianthus-docs-eebus/protocols/`, `architecture/`, or `api/` owner defined
  by the AD-DOCS-01 matrix.
- `helianthus-docs-ebus/docs/platform/` owns only language-neutral
  cross-runtime platform contracts.
- `helianthus-eebusreg` owns no substantive docs and must keep any README or
  package comments minimal and pointer-only.
- Every milestone ends with a complete architecture review. Final execution
  adds one extra code-structure review.

## Acceptance

The locked plan is acceptable when:

- The locked directory exists with standard plan layout.
- The canonical plan states gateway `0.4.0` as the baseline.
- The plan uses gateway `0.4.0` as the only baseline reference.
- Chunks are reviewable in isolation and include the required proof headers.
- Historical evidence remains preserved without claiming dirty rescue code is
  accepted.
- AD-DOCS-01 external-only documentation rules are encoded in canonical text,
  matrix rows, topology, and review artifacts.
- Recovery, docs verification, clean-main runtime reconciliation, trust,
  gateway, MCP, evidence, candidate, coexistence, promotion, and consumer rows
  are explicit and acyclic.
- Active plan validation remains green after the directory is renamed to
  `.locked/`.
