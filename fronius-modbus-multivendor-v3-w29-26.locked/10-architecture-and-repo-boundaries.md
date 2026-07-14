# Architecture and repository boundaries

Canonical-SHA256: `d01dcf33f46878f30c3a627e7e037a69660d55ab8d23ee8294923261b3979ee6`

Depends on: Operator brief dated 2026-07-14 and root/repository `AGENTS.md` contracts.
Scope: Public layer ownership, endpoint/runtime behavior, standard and vendor profile ownership, canonical metadata, and public/private dependency direction.
Idempotence contract: Reapplying these boundaries creates no additional repository, owner, scheduler, profile catalog, semantic ID, or binding direction.
Falsifiability gate: Reject this chunk if any required behavior has two owners, an import points upward/private-to-public, a profile owns endpoint lifecycle, or a decoded value cannot be traced to bounded raw evidence.
Coverage: Decisions D01-D05, D07-D08, D11-D12; issues M0, M1, M2; risks R01-R03, R05, R07-R08.

## Claim register

**Proven**

- `Project-Helianthus/.github` is the existing governance repository that can own
  organization-level repository creation.
- The two planned public Modbus repositories and two planned private binding
  repositories have no local checkout at draft time.
- Existing public gateway, registry, docs, HA integration, and add-on checkouts are
  available for later issue-specific work.

**Hypothesis**

- The transport/profile split remains sufficient when more vendors and both TCP and
  RTU are active concurrently.

**Unknown**

- Final module paths, initial maintainers, and repository settings until the M0
  bootstrap issues execute.

## Normative boundaries

| Layer | Owner | Owns | Must not own |
|---|---|---|---|
| Transport/runtime | `Project-Helianthus/helianthus-modbus` | TCP, RTU, endpoint owner, queues, fairness, coalescing, deadlines, cancellation, backoff, reconnect, limits, metrics | Vendor detection, register meaning, PV semantics, private bindings |
| Modbus protocol | `Project-Helianthus/helianthus-modbus` | ADU/PDU types, FC03/FC04 register reads, FC2B/MEI0E Device Identification, exceptions, uninterpreted words/bytes, correlation | Signedness, scale, units, source validity, canonical values, writes in this plan |
| Profile registry | `Project-Helianthus/helianthus-modbusreg` | Catalog, profile API, signedness/scale codecs, source-observation validity/timestamps, detector, fixtures, standard families, vendor overlays | Sockets, serial ownership, retries, canonical quality/freshness/IDs, consumers |
| Canonical semantics | `Project-Helianthus/helianthus-ebusreg` | Protocol-independent identity, quantities, quality, freshness, counters, versions, compatibility | Modbus addresses, vendor probes, endpoint lifecycle |
| Gateway protocol adapter | `Project-Helianthus/helianthus-ebusgateway/internal/modbusadapter` | Implements the existing protocol-agnostic adapter interface, composes Modbus runtime/profile registry, converts to neutral gateway DTOs | Any second gateway Modbus importer, canonical policy, or new repository |
| Public composition/API | Gateway core outside the local Modbus adapter | Configuration, adapter interface, raw MCP service, projection, semantic MCP, externally routable machine-to-machine GraphQL contract, Portal | Direct `modbus`/`modbusreg` imports, defining profile facts, canonical meaning locally, or raw registers in GraphQL |
| Public consumers | HA integration and add-on | Stable public API consumption, packaging, configuration, recovery | Raw register interpretation or profile selection |
| Private output bindings | Private eeBUS and Matter repos | Mapping locked canonical device classes from exactly packaged `PUBLIC_GRAPHQL_M2M_V1` to licensed output protocols | Modbus/modbusreg/gateway internals, undocumented ingress, or upstream public ownership |

The import graph is acyclic. `modbusreg` may import `modbus`. Inside the gateway, exactly
only `internal/modbusadapter` may import `modbus` and `modbusreg`; it implements the
existing protocol-agnostic adapter interface. Gateway core, semantic, MCP, GraphQL, and
Portal packages import that interface or neutral gateway DTOs only and are tested with a
fake adapter. Adapter integration tests exercise the real modules. No new repository is
created for this boundary. Private bindings may import or consume published public
contracts. Public packages, CI, fixtures, docs, and release artifacts must build without
private access. A private discovery must be restated as sanitized, independently
reviewable public evidence before it can affect a public profile or semantic contract.

The `.github` M0 issue creates the four planned repositories. Each destination bootstrap
issue depends on that governance issue and runs only after its repository exists.
Milestones group related issues but do not own code. Each issue row names exactly one
repository. Cross-repository behavior is joined by explicit dependencies and versioned
contracts, never by one issue editing multiple repositories.

The machine-readable `repository_mutex` is enforced by `cruise-topology` and
`cruise-preflight`: per repository, at most one issue and one PR may be active. The
validator checks only that structural ownership contract and does not simulate scheduling.

After the public Modbus bootstrap and M0 boundary documentation, bounded public docs issue
FMV3-M1-00 defines the M1 Modbus protocol/read-only, TCP/RTU, scheduling/recovery, MBAP
response matching without an echoed request offset, socket-lifetime tombstones and
generation-changing rollover, RTU response-latency plus bus-idle quarantine, and
transport-write linearization. Its exact ordered abnormal result set is `provable_zero`,
`partial_write`, `indeterminate_error`, `cancellation_race`, `ambiguous_completion`. Only
`provable_zero` avoids abandonment; the other four are possibly transmitted and force TCP
tombstone/close/reconnect/new-generation handling plus RTU quarantine/resynchronization or
endpoint recovery before a successor. Separate `full_transmit_success` enters `response_wait`.
TCP wait timeout/cancellation tombstones the ID, drops late response, and forbids same-socket
reuse until normal rollover; RTU wait timeout/cancellation enters existing quarantine/resync.
The same issue also publishes physical `wire_response_id` and per-observation linked
`logical_view_id`/slice identity, unequal-overlap replay and incompatible-coalescing
mutations, the named `RTU_PHYSICAL_QUALIFICATION_V1` evidence/dispositions, and the complete
M2 source-observation/provenance, detector activation lifecycle, hardware qualification,
coherence, and fixture/mutation contracts. It is one docs issue/PR merged before any M1 or
M2 implementation. FMV3-M1-01 through FMV3-M1-04 and FMV3-M2-01 through FMV3-M2-03 all
carry `doc_gate: required` and `companion_issue: FMV3-M1-00`; each has direct or explicit
acyclic dependency ancestry to the merged companion.

## Profile families

SunSpec is modeled as a standard family because its model identities and data meanings
are intended to apply across conforming manufacturers. FMV3-M3-03 records
`STANDARD_ONLY` when qualified Fronius evidence and the minimal standard implementation
cover the required slice; it creates an overlay only under `OVERLAY_REQUIRED` for qualified
vendor-specific facts. `STANDARD_ONLY` retains Fronius fixtures/live qualification and
unblocks M4 with public evidence, green conformance CI, and no implementation commit or
empty overlay. FMV3-M3-01 is the public companion for M3-02/M3-03. Later FMV3-M7-01 is the
public companion for M7-02/M7-03/M7-04 and closes only after the complete Growatt
candidate/admission contract, qualified facts, criteria, provenance/licensing, unsupported
disposition, and exact code/document mapping are public and merged. M7-03 consumes that
companion with no later docs change: `PROFILE_ADMITTED` alone triggers RED/code, while
`NO_ADMISSIBLE_PROFILE` preserves the pre-published evidence and unsupported disposition
without implementation, catalog entry, or support claim. Overlays remain isolated and versioned inside
`helianthus-modbusreg`, never separate repositories or transport code.

The registry permits one selected primary profile per identity domain plus overlays that
declare compatibility with that exact primary/profile version. If two candidates assign
different meanings to the same raw source, both remain inactive until evidence resolves
the ambiguity. Overlay precedence is explicit data; package import order is never a
selection rule.

Catalog activation is also explicit. `experimental_opt_in` is the only state available to
a fixture-only profile; it is disabled by default and requires operator opt-in while still
passing every detector and compatibility gate. `auto_eligible` requires a matching
hardware qualification record bound to the profile version and exact
model/gateway/firmware-or-software/transport tuple. Missing, mismatched, revoked, or
disabled qualification safely prevents or demotes automatic activation. Experimental
opt-in is not a support claim and cannot bypass semantic lock.

Each versioned profile codec explicitly declares `word_order` as high-word-first,
low-word-first, or not-applicable; applicable `byte_order_within_word` as high-byte-first,
low-byte-first, or not-applicable; and for strings the encoding, byte traversal, fixed
length, pad byte, pad side, and trim policy. The codec version and selected descriptor are
provenance fields. Opposing order and packing fixtures must fail when a profile omits or
misstates the applicable declaration.

## Detection contract

Detection inputs are endpoint/unit identity, catalog version, static applicability
metadata, and a bounded transcript of read-only probes. Candidate order and probe order
are deterministic. Each profile declares supported model identifiers, firmware/software
constraints, gateway constraints, required and discriminating reads, maximum ranges,
expected response classes, activation state, and required qualification-record match.

Outcomes are `selected`, `no_match`, `ambiguous`, `unsupported_version`,
`insufficient_evidence`, or `probe_failed`. Only `selected` activates decode. Timeout,
malformed response, illegal address, changed identity, budget exhaustion, and partial
required evidence cannot be interpreted as a positive match. No write operation can be
used for detection. Manual selection may remove candidates but still runs all required
version, gateway, and read-evidence checks.

## Source observation and canonical value contracts

The Modbus protocol output is uninterpreted 16-bit words/bytes in received order. It does
not compose registers, reorder bytes, unpack strings, or trim padding. Signedness, scale,
enum, unit, multi-register word composition, applicable intra-word byte order, and string
packing/padding interpretation belong only to `modbusreg` codecs. Their output is a source
observation envelope, not an unqualified scalar and not a canonical value. Required fields
are decoded value, source validity, observation/receipt timestamps, profile/detector/codec
versions, raw type, signedness, unit, scale, access, declared word/byte order and string
packing/padding or explicit not-applicable values, `sample_id`,
`poll_generation_id`, `dependency_set_id`, complete dependency membership, and raw
provenance. Every physical request/range response has a `wire_response_id`; every dependent
logical observation has a linked `logical_view_id`, logical offset/count, and exact slice
offset/count within that wire response.
Provenance records the documentary notation and the explicit one-based-to-zero-based
normalization when the source document uses one-based register numbers. FC03 holding and
FC04 input sources at the same numeric offset are never equal identities. `sample_id`
binds the exact response set admitted for one decode; validation/re-read responses remain
in its coherence transcript and response/sample IDs are not reused across attempts.

All members of a decode dependency set must carry one `poll_generation_id`; the harness
and gateway reject mixed generations. Profiles also declare coherence as one response
where possible or as a bounded multi-response window with a validation/bounded re-read
recipe. If a member is absent/invalid, the window expires, or validation detects mutation
and the bounded re-read cannot repair it, no new source observation is committed. The
gateway propagates source validity/timestamps and sample, generation, dependency, and
response identity unchanged. Torn-read mutation is a required fixture.

`ebusreg` alone maps source validity/timestamps to canonical quality and owns freshness
deadlines, last-good retention, stale/unavailable transitions, expiry, counter rollover,
reset, and canonical compatibility. Profiles and gateway code cannot define competing
canonical timers or quality transitions.

## Scheduler and endpoint ownership

One `helianthus-modbus` runtime owns each physical endpoint. TCP pool keys exclude unit ID
so units sharing a gateway also share bounded endpoint resources and endpoint scheduling.
On each individual TCP connection/socket, one MBAP transaction-ID allocator and one
in-flight correlation map own requests for every unit ID. Normal FC03/FC04 responses do not
echo the requested offset, so correlation matches active connection generation and
transaction ID plus echoed unit/function and applicable expected byte count; the requested
zero-based PDU offset remains provenance only. Unit/profile lifecycle and decode state
remains isolated even though the allocator/map is connection-wide. RTU serializes the bus
and honors its framing/timing rules under the same request envelope.

Scheduling requirements are:

- bounded endpoint, queue, in-flight, read-range, response, retry, and memory budgets;
- weighted or round-robin fairness with a stated starvation bound;
- coalescing only when unit, logical table, authorization scope, poll generation, and
  operation deadlines are compatible; unequal overlapping reads may share one physical
  wire response only when every dependent logical view replays its exact words/provenance;
- one absolute deadline covering queue, connect, I/O, retry, and backoff;
- transport-write linearization with exactly the ordered abnormal `provable_zero`, `partial_write`,
  `indeterminate_error`, `cancellation_race`, `ambiguous_completion` results; only
  `provable_zero` avoids abandonment and the other four are possibly transmitted;
- separate `full_transmit_success` transition to `response_wait` for TCP and RTU, never
  classified as `ambiguous_completion`;
- cancellation/timeout during TCP response wait that releases waiters, tombstones the
  transaction ID, drops late response, and forbids same-socket reuse until normal rollover;
- TCP possibly-transmitted completion that tombstones the ID, closes the connection to
  prevent stream desynchronization, increments generation on reconnect, and rejects the
  old generation;
- controlled close/reconnect at tombstone exhaustion, with generation increment before any
  tombstoned ID reuse and rejection of every old-socket/generation frame; successful
  non-abandoned correlation remains under the bounded allocator/no-in-flight-collision rules;
- timeout/cancellation during RTU response wait after full transmit that blocks every successor
  until a bounded endpoint-declared response-latency interval plus bus-idle resynchronization
  quarantine completes, discards every quarantine frame, and disables/recovers a
  nonquiescent endpoint;
- each RTU possibly-transmitted result, `partial_write`, `indeterminate_error`,
  `cancellation_race`, and `ambiguous_completion`, entering that same quarantine/resynchronization
  or endpoint recovery before any successor;
- bounded exponential reconnect with jitter and observable reset conditions;
- one `wire_response_id` bound to physical request ID, endpoint, unit, function/table,
  physical zero-based PDU range/count, and transport generation, plus one linked
  `logical_view_id`, logical range/count, and exact slice offset/count for every dependent
  observation;
- metrics for wait, queue, coalescing, response classes, timeout, retry, reconnect,
  cancellation, source-observation gaps, and endpoint resource use.

FMV3-M1-02 through FMV3-M1-04 deterministically cover the exact abnormal results
`provable_zero`, `partial_write`, `indeterminate_error`, `cancellation_race`, and
`ambiguous_completion` in that order, separately from `full_transmit_success -> response_wait`.
TCP tests also cover concurrent units, same-socket tombstone reuse, late response drop,
close/reconnect rollover, and old-generation rejection; FMV3-M1-03 follows M1-02 and RTU
tests cover all four possibly-transmitted triggers, full-transmit timeout/cancellation,
late same-shape discard,
quarantine completion, failed quiescence, and endpoint recovery before a successor. Profiles submit read intents
and decode complete results. They never dial, open serial ports, allocate/correlate MBAP IDs,
schedule recurring work, retry, sleep, reconnect, or lock endpoints. Runtime correlation uses
protocol identity only and owns no profile semantics.

RTU conformance records exactly `PHYSICALLY_QUALIFIED` or
`FIXTURE_ONLY_NO_HARDWARE` against `RTU_PHYSICAL_QUALIFICATION_V1`. The physical disposition
requires adapter/transceiver identity, baud and topology, measured physical silent
intervals, and timeout/cancellation quarantine traces. Without that evidence, RTU remains
default-disabled and experimental with no enabled or supported claim; fixture conformance
may close, and no missing RTU hardware blocks TCP/Fronius or TCP-sufficient M1/M7 work.

## Safety and licensing boundary

Phase 1 allowlists exactly FC03 Read Holding Registers, FC04 Read Input Registers, and
FC2B/MEI0E Read Device Identification. The protocol runtime owns MEI conformity, object,
segmentation/more-follows, bounds, exception, and malformed-response behavior on TCP/RTU;
profile code may request these operations but cannot frame them. No generic write primitive is hidden for later
use. Write support requires a separate plan covering authorization, interlocks, device
capability, value validation, confirmation, audit, timeout uncertainty, and recovery.

M0 governance creates repositories before destination bootstrap; bootstraps record public
and private licenses before code. Evidence intake records source,
license/permission, transformation, applicability, and sanitization. Any unresolved IP
or provenance question blocks the affected profile without blocking unrelated profiles.
