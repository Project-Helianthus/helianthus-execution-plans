# Fronius-first Modbus runtime, multi-profile registry, and private output bindings

Date: `2026-07-14`
State: `locked`
Availability: `openai_only`, `gpt-5.6-sol`, reasoning `max`
Supersedes: `fronius-modbus-eebus-bridge-w28-26.draft`

This locked plan replaces the W28 package as execution intent. The W28 directory remains
unchanged as forensic history. The operator action on 2026-07-14 authorizes this plan lock
and publication only; it authorizes no product implementation, target-repository creation,
or implementation issue creation.

## Claim discipline

**Proven**

- `Project-Helianthus/.github` is the existing organization-governance repository and is
  the only issue host that can create all four planned repositories before destination
  bootstrap work exists.
- The four planned repositories `helianthus-modbus`, `helianthus-modbusreg`,
  `helianthus-eebus-binding-private`, and `helianthus-matter-binding-private` do not
  have local checkouts at drafting time.
- Existing local checkouts include the gateway, registry, documentation, Home
  Assistant integration, and Home Assistant add-on repositories.
- The operator's Huawei corpus distinguishes SmartLogger material from S-Dongle
  material and documents v49 and v52 as parallel firmware branches rather than a
  monotonic sequence.

**Hypothesis**

- One transport/runtime library and one multi-profile registry can serve Fronius,
  SunSpec, Growatt, and Huawei without coupling endpoint behavior to register meaning.
- A generic private eeBUS binding can expose locked PV semantics in a form accepted by
  myVaillant.

**Unknown**

- The exact Fronius models, firmware variants, unit topology, exposed blocks, and
  optional devices that will pass the phase-1 lab gate.
- Which Growatt and Huawei combinations will meet evidence and hardware support gates.
- Actual myVaillant interoperability until the M6 lab test passes.
- EMMA register and gateway applicability. EMMA remains out of scope.

Normative statements below are plan decisions, not empirical claims.

## Objective

Deliver a public, reusable Modbus stack with a Fronius-first read-only vertical:

1. `helianthus-modbus` owns Modbus protocol operations, TCP and RTU transports,
   endpoint scheduling, limits, cancellation, reconnect, runtime observability, and the
   single MBAP transaction allocator/correlation map on each TCP connection, including
   the exact ordered abnormal transport-write result set `provable_zero`, `partial_write`,
   `indeterminate_error`, `cancellation_race`, `ambiguous_completion`, where only
   `provable_zero` avoids abandonment and all other abnormal results force TCP
   close/reconnect handling and RTU quarantine/resynchronization or endpoint recovery.
   Separate `full_transmit_success` enters `response_wait` for both transports.
   RTU remains default-disabled and experimental until `RTU_PHYSICAL_QUALIFICATION_V1`
   records adapter/transceiver, baud/topology, physical silent intervals, and
   timeout/cancellation quarantine evidence; absent hardware creates no support claim and
   blocks no TCP-sufficient work.
2. `helianthus-modbusreg` owns one catalog of standard and vendor profiles, codecs,
   detector rules, fixtures, and profile conformance. M3 implements the minimal SunSpec
   standard family needed by Fronius before an evidence-dependent Fronius disposition;
   only qualified vendor-specific facts create an overlay. M7 later expands SunSpec, then
   evaluates Growatt and adds Huawei SmartLogger and Huawei S-Dongle packages.
3. The gateway-local `helianthus-ebusgateway/internal/modbusadapter` package implements
   the gateway's existing protocol-agnostic adapter interface and is the only gateway
   package permitted to import `helianthus-modbus` or `helianthus-modbusreg`; gateway core tests use the
   interface and a fake adapter. No additional repository is created for this boundary.
4. Existing public platform repositories own canonical semantics and public APIs.
5. Generic private eeBUS and Matter bindings consume exactly the same locked
   `PUBLIC_GRAPHQL_M2M_V1` contract and start implementation only after public consumers
   and packaged rollout complete. Both use authenticated bounded query/polling, compatible
   versions, noninteractive least privilege, a confidential channel with verified server
   identity, and credential lifecycle/recovery. The eeBUS binding uses the packaged machine-to-machine
   access contract documented publicly before GraphQL implementation for authenticated
   bounded polling of the stable versioned API over a confidential channel with verified
   server identity, fails closed for plaintext or untrusted identity, and invents no
   subscription. PV is their first vertical, not their repository identity.

The critical delivery path is M0 -> M1 TCP slice -> M2 -> M3 -> M4 -> M5 packaged
public rollout -> M6.
RTU completion, vendor expansion, and Matter remain explicit work but do not gate the
Fronius-to-eeBUS lab result unless an issue dependency says otherwise.

## Layer and ownership boundaries

```text
transport/runtime
  helianthus-modbus: TCP, RTU, endpoint owner, scheduler, deadlines, reconnect
        |
Modbus protocol
  helianthus-modbus: ADU/PDU, read functions, exceptions, uninterpreted 16-bit words/bytes
        |
profile registry
  helianthus-modbusreg: detection, signedness/scale codecs, standard profiles, overlays
        |
gateway protocol adapter
  helianthus-ebusgateway/internal/modbusadapter: sole gateway importer of modbus/modbusreg
        |
canonical semantics
  helianthus-ebusreg: protocol-independent identity, quantities, quality, versions
        |
public APIs and consumers
  helianthus-ebusgateway semantic MCP -> public GraphQL docs -> GraphQL -> Portal -> HA integration/add-on
        |
private output bindings
  helianthus-eebus-binding-private via public GraphQL query/polling; matter binding via public contract
```

Dependencies flow downward only. `helianthus-modbus` has no profile, vendor, PV, or
private-binding imports. `helianthus-modbusreg` may import `helianthus-modbus`, but it
does not own sockets, serial ports, retry loops, canonical PV IDs, or consumers.
`helianthus-ebusreg` defines canonical meaning without importing Modbus or private
packages. Inside `helianthus-ebusgateway`, `internal/modbusadapter` composes
`helianthus-modbus` and `helianthus-modbusreg` behind the existing protocol-agnostic
adapter interface. It is the only gateway package allowed to import either module;
gateway core, semantic, MCP, GraphQL, and Portal packages depend on the interface or
gateway-owned neutral DTOs only. Private repositories may depend on published public
contracts; public source, CI, builds, fixtures, and documentation must never require a
private repository, path, secret, or generated private artifact.

`Project-Helianthus/.github` owns the M0 repository-creation issue. Destination bootstrap
issues depend on it and cannot start until each destination exists. Each executable issue
has exactly one repository owner. Cross-repository milestones are coordination groupings
only; issue dependencies determine readiness.

`plan.yaml` also declares a concise per-repository mutex owned by `cruise-topology` and
`cruise-preflight`: at most one active issue and one active PR per repository. Validation
checks this structural contract and the explicit serialization edges, not runtime scheduling.

## Standard profiles and vendor overlays

SunSpec is treated as a standard profile family: its model identities, model chains,
quantities, scale rules, and version applicability are represented without assuming one
manufacturer. A device may also expose behavior outside the applicable SunSpec family.
Fronius applicability is therefore evidence-dependent: M3 records `STANDARD_ONLY` when
the required Fronius slice is fully covered by qualified standard facts, or
`OVERLAY_REQUIRED` only when qualified model, firmware, gateway, access, and scale evidence
proves vendor-specific facts. FMV3-M3-01 is the public companion for M3-02/M3-03.
`STANDARD_ONLY` records public evidence/disposition, passes conformance CI, and creates no
implementation commit or empty overlay; only `OVERLAY_REQUIRED` invokes overlay TDD/code.
Growatt and Huawei packages follow the same evidence rule for any overlay they admit.

An overlay may add or refine raw profile facts. It may not silently override a standard
fact, invent canonical meaning, weaken detection, or create a vendor-specific transport.
Conflicting eligible interpretations are an ambiguity and block activation.

Every versioned profile codec declares how raw words become a value. Its descriptor records
multi-register composition order (`high_word_first`, `low_word_first`, or
`not_applicable`), applicable byte order within each word (`high_byte_first`,
`low_byte_first`, or `not_applicable`), and for strings the encoding, byte traversal,
fixed length, pad byte, pad side, and trim policy. The selected descriptor and codec version
are decode provenance. `helianthus-modbus` preserves received words/bytes in order and owns
none of these interpretation choices.

## Deterministic read-only detection

Detection is a pure, bounded decision over a declared endpoint and unit identity:

1. Read transport-neutral identity evidence allowed by the profile catalog.
2. Evaluate static gates such as vendor, model, profile family, firmware or software
   package, gateway type, and profile version.
3. Execute only the minimum ordered read probes needed to distinguish remaining
   candidates. Probe addresses, sizes, count, total words, and deadline are bounded.
4. Record every successful, failed, illegal-address, timeout, and malformed response as
   detector evidence.
5. Select exactly one primary profile and explicit compatible overlays, or fail closed.

No write probe is permitted. No match, multiple matches, missing required identity,
unsupported version, inconsistent gateway evidence, probe-budget exhaustion, timeout,
or partial dependency data leaves the endpoint inactive for that profile. Raw diagnostic
access may remain available within authorization and bounds. Explicit operator selection
may narrow candidates but cannot bypass compatibility or evidence gates.

Every catalog entry also carries an activation lifecycle state. A fixture-only profile is
`experimental_opt_in`, is disabled by default, and can run only after explicit operator
opt-in while all normal identity, compatibility, and read-only gates still pass. It is not
auto-eligible and creates no support claim. `auto_eligible` requires a matching hardware
qualification record bound to profile version, model, gateway, firmware/software branch,
and transport. A missing, mismatched, revoked, or disabled qualification record prevents
automatic activation and safely demotes an active profile on re-evaluation.

The selected identity record contains endpoint identity, unit identity, profile ID and
version, detector version, model and firmware evidence, probe transcript reference, and
selection reason. Reconnect does not silently retain selection when identity evidence has
changed; re-detection occurs under a bounded policy.

## Source observation, canonical value, and provenance contract

`helianthus-modbus` returns uninterpreted 16-bit words/bytes plus transport identity and
timing. Every physical request/range response has a unique `wire_response_id`; every
dependent logical observation has a linked `logical_view_id` and exact slice identity. It does not assign signedness, units, scale, validity,
quality, or freshness.
`helianthus-modbusreg` codecs interpret signedness, scale, composition, and packing and emit
a source observation with:

- decoded value and source `validity`, distinct from canonical quality;
- source observation timestamp and receipt timestamp;
- endpoint, unit ID, source profile/version, detector version, engineering unit, scale
  rule, raw type, signedness, and access mode;
- codec version plus declared multi-register word order, applicable intra-word byte order,
  and string encoding/packing/padding fields or explicit `not_applicable` values;
- `sample_id`, `poll_generation_id`, `dependency_set_id`, and the complete
  identity/membership of every raw dependency used by the decode;
- for each raw dependency, endpoint, unit ID, function/table, logical zero-based PDU
  offset/count, `logical_view_id`, linked `wire_response_id`, and slice offset/count;
- raw provenance sufficient to reproduce the decode from a sanitized fixture or bounded
  raw reference, including source evidence identifier, the documentary notation, and the
  recorded normalization from documentary one-based register notation when applicable to
  the zero-based PDU offset.

`sample_id` binds the exact wire-response/logical-view set accepted for one decode; every bounded validation
or re-read response remains in its coherence transcript, and IDs are never reused across
attempts. All members of a dependency set must belong to one `poll_generation_id`;
mixed-generation input is rejected, not merged. Each profile declares a coherence rule.
Unequal overlapping reads share one wire response only when unit, table, authorization,
generation, and deadlines are compatible; each logical view replays exact words and
provenance. A multi-response sample must complete
inside a bounded profile-declared coherence window and pass its validation or bounded
re-read recipe; otherwise no source observation is emitted. A changed dependency during
validation is a torn read, not a partial value. The gateway propagates source
validity/timestamps and sample/generation/dependency/response identities unchanged.
Partial, incoherent, or torn reads do not create a new source observation.

Only `helianthus-ebusreg` maps source validity/timestamps to canonical quality and owns
freshness deadlines, last-good retention, stale/unavailable transitions, expiry, stable
IDs, meaning, compatibility, and schema versions. Counter rollover, reset, device restart,
and decreasing values are canonical state transitions, not codec guesses.

## Runtime contract

The shared scheduler belongs in `helianthus-modbus`, not in profile packages. One runtime
owner exists per physical endpoint. On each TCP connection/socket, exactly one MBAP
transaction-ID allocator and one in-flight correlation map own requests for every unit ID
using that socket. Endpoint scheduling and bounded connection resources are shared, while
unit and profile lifecycle/decode state remains isolated. Normal FC03/FC04 responses do not
echo the requested offset: the offset remains request provenance, while delivery matches the
active connection generation and transaction ID plus echoed unit/function and applicable
expected byte-count constraints. For RTU, serial timing and bus serialization use the same
request envelope, deadline, cancellation, fairness, and observability contracts plus the
abandonment quarantine below.

The runtime provides:

- bounded endpoint, request, word, response, queue, in-flight, retry, and memory limits;
- fair scheduling across units and profiles with starvation tests;
- coalescing only for compatible overlapping reads whose unit, table, authorization,
  generation, and operation deadlines can all be preserved, with one physical-range
  `wire_response_id` and an exact-slice `logical_view_id` per dependent observation;
- one absolute operation deadline across queue, connect, transmit, receive, retry, and
  backoff, with cancellation releasing waiters and resources;
- one exact ordered abnormal transport-write result set: `provable_zero`, `partial_write`,
  `indeterminate_error`, `cancellation_race`, `ambiguous_completion`; only `provable_zero`
  avoids abandonment after invocation, while the other four are possibly transmitted;
- a separate `full_transmit_success` transition to `response_wait` for TCP and RTU; normal
  full transmission is not `ambiguous_completion`;
- bounded exponential reconnect backoff with jitter, reset rules, and no tight loops;
- TCP correlation that checks the active socket generation and MBAP transaction ID plus the
  echoed unit/function and applicable byte-count response shape before delivery, with the
  requested zero-based PDU offset retained only as provenance;
- after full TCP transmission, response-wait timeout or cancellation tombstones the
  transaction ID, drops any late response, and forbids same-socket reuse until the normal
  tombstone rollover policy; successfully completed, non-abandoned IDs remain governed by
  the bounded allocator and no-in-flight-collision rules;
- controlled close/reconnect on tombstone exhaustion, incrementing connection generation
  before a tombstoned ID can be reused and rejecting every old-socket/generation frame;
- for every TCP possibly-transmitted write, tombstone the ID, close the connection to
  prevent stream desynchronization, reconnect with incremented generation, and reject the
  old generation;
- after `full_transmit_success` on RTU, response-wait timeout or cancellation admits no
  successor transmit until the bounded endpoint-declared response-latency
  interval and bus-idle resynchronization quarantine both complete; all quarantine frames
  are discarded, and failure to reach quiescence disables and recovers the endpoint;
- apply that same RTU quarantine/resynchronization or endpoint recovery before a successor
  for each possibly-transmitted write result: `partial_write`, `indeterminate_error`,
  `cancellation_race`, and `ambiguous_completion`;
- stable response identity, malformed-frame isolation, exception propagation, and no
  cross-unit or cross-request data reuse;
- health and metrics for queue depth, wait time, coalescing, retries, timeouts, reconnect,
  source-observation gaps, and per-endpoint resource use.

Profiles submit declarative read intents and decode complete responses. They do not own
connections, MBAP allocation/correlation, polling loops, retries, backoff, cancellation, or
endpoint locks. The runtime matches protocol identity only and never interprets profile
signedness, scale, word/byte order, strings, provenance, or canonical meaning.

`Transport write` above means sending a read request through socket/serial I/O; it does not
authorize a Modbus write function.
Write support is explicitly deferred to a separate safety plan. Phase 1 exposes no write
function, write probe, generic raw write MCP tool, semantic control, or configuration bit
that can enable writes.
The exact phase-1 operation allowlist is FC03 Read Holding Registers, FC04 Read Input
Registers, and FC2B/MEI0E Read Device Identification. `helianthus-modbus` owns MEI
conformity levels, object IDs, segmentation/more-follows, bounded aggregation, exceptions,
and malformed responses on TCP and RTU. `helianthus-modbusreg` may request these operations
but never owns PDU framing.

## Delivery phases

### M0: governance and bootstrap

The existing `Project-Helianthus/.github` governance repository owns one issue that creates
all four planned repositories with intended visibility. Each destination then owns a
separate bootstrap issue that depends on governance creation and runs only after that
repository exists. Destination work sets license, module identity, ownership, CI, and
dependency policy before product code. Documentation fixes layer/licensing boundaries.
After the public Modbus repository bootstrap and boundary-doc issue, the existing bounded
companion issue FMV3-M1-00 publishes both the M1 Modbus protocol/read-only, TCP/RTU,
scheduling/recovery, response-correct MBAP matching, socket-lifetime tombstone/generation
rollover, abnormal transport-write linearization, separate full-transmit response-wait
transitions, RTU response-latency plus bus-idle quarantine, and runtime-versus-codec contracts
and the complete M2 source-observation/provenance, detector activation lifecycle, hardware
qualification, coherence, and fixture/mutation contracts. It is one public docs issue/PR,
merged before any M1 or M2 implementation; FMV3-M1-01 through FMV3-M1-04 and FMV3-M2-01
through FMV3-M2-03 all depend on it directly or through explicit ancestry and carry its
doc-gate/companion metadata.

### M1-M3: shared stack and Fronius fixtures

M1 first merges FMV3-M1-00, then establishes protocol, TCP, RTU, scheduler, and transport
gates, with FMV3-M1-03 depending on M1-02. M1-02 through M1-04 deterministically cover the
exact abnormal results `provable_zero`, `partial_write`, `indeterminate_error`,
`cancellation_race`, and `ambiguous_completion` in that order, separately from
`full_transmit_success -> response_wait`. TCP tests also cover mandatory close/reconnect on
possibly-transmitted abnormal results, response-wait timeout/cancellation tombstones, late
response drop, forbidden same-socket reuse until normal tombstone rollover, generation
rollover, old-generation rejection, and bounded successful correlation. RTU tests apply
quarantine/resynchronization or recovery to all four possibly-transmitted abnormal results
and to timeout/cancellation after full-transmit response waiting. FMV3-M1-04 names the exact
rows `tcp_full_transmit_timeout_tombstone`, `tcp_full_transmit_cancellation_tombstone`,
`rtu_full_transmit_timeout_quarantine`, and `rtu_full_transmit_cancellation_quarantine`.
RTU fixture conformance may close as `FIXTURE_ONLY_NO_HARDWARE`, leaving it disabled and
experimental with no supported/enabled claim. Only `PHYSICALLY_QUALIFIED` from
`RTU_PHYSICAL_QUALIFICATION_V1` permits such a claim; absent hardware blocks neither the
TCP/Fronius path nor TCP-sufficient M1/M7 work.
Protocol
outputs remain uninterpreted words/bytes in received order. M2 starts only with the same
FMV3-M1-00 companion merged and establishes
versioned codec/source-observation/detector contracts and deterministic fixtures, including
physical `wire_response_id`, linked logical `logical_view_id`/slice provenance,
explicit word composition, applicable intra-word byte order, string packing/padding, and
mixed-generation rejection. M2 may start after the M1 protocol contract while the RTU lane
continues; the issue DAG records that safe overlap without a second docs issue.
M3-01 is the public companion for M3-02/M3-03. M3 builds that provenance-qualified evidence packet, implements the minimal standard SunSpec
family needed by phase 1, then records the Fronius TCP read-only disposition. M3-03 returns
`STANDARD_ONLY` when M3-01/M3-02 prove the required slice fully standard, or
`OVERLAY_REQUIRED` only for qualified vendor-specific facts. Both dispositions retain
Fronius fixtures and later live qualification, pass read-only conformance, and unblock M4;
the standard-only path records evidence publicly with green CI and creates neither an
implementation commit nor an overlay artifact. Only overlay-required uses
`TDD_RED_IF_OVERLAY_REQUIRED`.
M1 fixtures prove that the same numeric offset under FC03/holding-register and
FC04/input-register identities cannot alias. M2 fixtures prove documentary one-based to
zero-based PDU normalization and reject off-by-one mappings. The replay/mutation harness
pairs opposing word orders, applicable opposing intra-word byte orders, and string
packing/padding policies so an implicit default cannot pass. It also changes a dependency
between responses and proves that a torn multi-response sample is rejected or successfully
re-read under its bounded profile coherence rule. Minimal and expanded SunSpec, Fronius,
Growatt, and Huawei issues each exercise every applicable order/packing case declared by
their versioned profile.

All code issues follow strict TDD: a test-only RED commit must exist and be observed red by
CI before implementation is pushed. Conditional disposition issues invoke that rule only
when their declared implementation branch is selected. Transport changes require the applicable transport
matrix. Protocol, semantic, licensing, or reverse-engineered knowledge changes require the
documentation gate.

### M4: raw MCP and real-device proof

The gateway-local `internal/modbusadapter` package becomes the single owner of the
configured Fronius TCP endpoint and implements the existing protocol-agnostic adapter interface. Only that
package imports `helianthus-modbus` or `helianthus-modbusreg`; gateway core is tested
against a fake adapter/interface while adapter integration tests cover the real modules.
It exposes bounded raw reads and detector/profile observations through MCP before
canonical promotion.
The add-on provides validated configuration, secret-safe logging, a disable switch, health,
and restart recovery.

Fronius phase 1 has a `hardware_required` gate. Fixtures alone cannot claim support. The
lab starts from explicit experimental opt-in; a successful record qualifies only the exact
tested profile/hardware tuple for later automatic eligibility. The smoke test must prove
detection, bounded polling, raw MCP parity, coherent sample/response
identity, source observation stop/resume and generation integrity across
disconnect/reconnect, read-only traffic, resource bounds, and no regression to existing
gateway transport. FMV3-M4-04 records exactly `GO`, `NO_GO`, or `STOP`; issue completion
alone never satisfies the gate. FMV3-M4-05 packages the exact result and sanitized evidence
for any outcome. Only M4-04 `GO` plus completed M4-05 evidence packaging permits M5
raw/semantic work. `NO_GO` or `STOP` remains honest evidence, disables the endpoint, and
leaves all M5 work blocked; it does not block raw fixture work or require a public API
rollback.

### M5: semantic lock and public promotion

Only after M4 live evidence is sanitized does `helianthus-docs-ebus` publish the candidate
canonical PV contract. FMV3-M5-02 retains the M4 prerequisites and must merge before
`helianthus-ebusreg` semantic implementation starts in FMV3-M5-01. FMV3-M5-04 then creates
the candidate Fronius-to-canonical mapping and semantic MCP and runs that exact version
through golden and live Fronius tests, preserving wire-response/logical-view provenance.
A separate semantic-lock issue depends on M5-04 and reviews that tested MCP version,
schema, evidence, quality/freshness rules, and compatibility. FMV3-M5-03 records exactly
`GO`, `NO_GO`, or `STOP`; completion is not progress. `NO_GO` or `STOP` keeps raw and
candidate semantic MCP available for remediation and blocks M5-09 plus all later consumers.
FMV3-M5-04 is outside the semantic-GO before-set.

Promotion is strictly semantic MCP golden/live proof -> M5-03 lock GO -> public GraphQL companion docs -> GraphQL ->
Portal -> Home Assistant -> recoverable add-on packaging. FMV3-M5-09 is exactly one public
`helianthus-docs-ebus` issue/PR after FMV3-M5-03 and before FMV3-M5-05. It follows the earlier
FMV3-M5-02 docs work in the same serialized repository lane and publishes the exact
`PUBLIC_GRAPHQL_M2M_V1` schema projection, external access/security/channel contract,
compatibility/versioning, credential lifecycle, and recovery contract while retaining
M5-03 `GO` ancestry. FMV3-M5-05 carries that companion metadata and implements the documented
contract for a separately deployed service client. Any credential-bearing external use
requires an authenticated confidential channel with verified server identity before
credentials are sent. Plaintext external access and untrusted server identity fail closed.
It proves external-context reachability, noninteractive authentication and authorization,
least privilege, bounded polling/rate/resource behavior, and credential provisioning,
rotation, revocation, disable, and recovery without prescribing the channel or authentication
mechanism or weakening security. The
Portal issue contains two deliberately separate surfaces: its semantic PV view remains a
GraphQL-only consumer, while an authenticated raw diagnostics/register explorer reuses the
already-bounded raw service behind MCP with the same read allowlist,
endpoint/function/range and rate/resource budgets, secret redaction, and audit controls.
Raw registers are not added to semantic GraphQL and no subscription is introduced.
FMV3-M5-08 packages and repeats the public service-client test from an external service
context, including explicit plaintext rejection, untrusted-server-identity rejection, and
the same credential lifecycle and recovery contract.
Private implementation remains blocked until that packaged public rollout completes.

### M6: private eeBUS output and myVaillant

After the M5 public rollout, FMV3-M6-00 first publishes a sanitized permissive companion
for GraphQL ingress, SHIP/SPINE discovery, TLS/pairing, trust lifecycle, identity, encoding,
capability negotiation, PV exchange, security, and the public-knowledge boundary. Only then
does the private eeBUS repository deploy a generic
canonical-to-eeBUS output binding for all future device classes. Its only semantic ingress
is exactly the machine-to-machine public GraphQL contract documented by FMV3-M5-09,
implemented by FMV3-M5-05, and packaged/tested by FMV3-M5-08, consumed with authenticated and
authorized queries at a bounded polling cadence over the same authenticated confidential
channel with verified server identity. M6-01 rejects plaintext external access and untrusted
server identity and does not prescribe the channel mechanism; no GraphQL subscription is
assumed or invented. Its
first enabled slice maps locked PV semantics. A CI-observed RED commit precedes
implementation. FMV3-M6-01 tests deployment/configuration, authn/authz, GraphQL
schema/contract compatibility, polling reconnect/backoff, explicit disable, and
unavailable/stale propagation, together with minimum eeBUS SHIP/SPINE discovery and trust
lifecycle: discovery, SHIP TLS and pairing, persisted trust, reconnect, revocation/reset,
disable recovery, capability negotiation, identity, encoding, and a complete PV exchange.
It contains no Modbus transport, register addresses, Fronius detector, raw profile codec,
or gateway-internal logic. This plan creates no public eeBUS implementation repository.

Actual myVaillant interoperability remains a hypothesis until FMV3-M6-02 records exactly
`GO`, `NO_GO`, or `STOP`; completion is not progress and `GO` is the sole objective success.
GO requires an enabled, qualified live Fronius endpoint throughout the run and at least one
traced observation that is available, non-stale, and generated after the recorded lab-run
start. That same observation identity and value must traverse `PUBLIC_GRAPHQL_M2M_V1` and
eeBUS to an accepted myVaillant-side observable with matching canonical/source identity,
value, unit/value semantics, quality, source observation time, and receipt time. Replayed,
synthetic, retained-cache-only, fixture-only, simulator-only, handshake-only, or packet-only
input cannot GO. The existing public identity/time/quality contract carries this proof; no
new public schema field is required. The required lab also
verifies discovery, SHIP TLS/pairing, trust persistence across restart/reconnect,
revocation/reset and repair, and disable recovery while recording reproducible `GO` or
`NO_GO`/`STOP` evidence. M6-02 is real-lab only and simulator qualification belongs to
M6-01. FMV3-M6-03 follows the lab and publishes reusable sanitized protocol/interoperability
findings with provenance and licensing. Knowledge that cannot be published permissively
forces `STOP`; a private-only success or support claim cannot satisfy M6. `NO_GO` or `STOP`
retains honest evidence but does not complete the plan objective or unlock success, and no
outcome adds vendor logic or distorts the public schema.

### M7: vendor expansion

FMV3-M7-01 waits until the critical docs lane reaches FMV3-M5-09 and is the public companion
for M7-02, M7-03, and M7-04; profile implementation also waits for FMV3-M3-03.
Before M7-01 closes, its merged public packet publishes the complete Growatt candidate and
admission contracts, qualified candidate facts, admission criteria, provenance/licensing,
explicit unsupported disposition, and exact code/document mapping for both dispositions.
For every vendor candidate M7-01 enumerates all detector operations and proves each belongs
to the versioned phase-1 runtime allowlist; an unsupported operation forces non-admission
rather than protocol framing in modbusreg. For every SmartLogger and S-Dongle candidate it likewise publishes a complete
provenance/licensing-qualified register, codec, gateway, branch, version, detection, and exact
code/document admission packet, or records `NO_ADMISSIBLE_PROFILE`.
The single `helianthus-modbusreg` lane is then serialized: expand the minimal SunSpec
family, evaluate Growatt, then Huawei, then mixed-catalog closure. FMV3-M7-03 may finish as
`NO_ADMISSIBLE_PROFILE` after bounded evidence and licensing analysis; that disposition
preserves the pre-published public evidence and explicit unsupported status, creates no
implementation commit, catalog entry, support claim, or later companion docs change, and
releases FMV3-M7-04 without an extra conditional GO gate. `PROFILE_ADMITTED` alone triggers
RED-first fixtures/code against the already-merged companion and likewise requires no later
companion docs change. M7 adds raw/profile support only.
New canonical fields or consumer claims require their own live evidence and semantic-lock
cycle.

Huawei intake starts from operator-authored analysis, converted Markdown, gate tables,
enrichment tables, live snapshots, and audits, but does not copy conclusions as truth.
Evidence is re-inventoried by source, license, model, gateway, software package, firmware
branch, access, and live confirmation. v49 and v52 are parallel branches; a register present
or typed one way in one branch is not inherited by the other. Model or MEI evidence,
software package identity, gateway detection, and bounded read-only probes are revalidated.
Unconfirmed live values remain Unknown. The plan contains no exact Huawei register claims.
SmartLogger and S-Dongle remain distinct profile scopes. EMMA has no implementation issue
and its semantics stay deferred. M7-01 inventories EMMA gateway/model/software/version
discriminators or marks each unavailable. M7-04/M7-05 negative fixtures require EMMA or
insufficiently distinguished endpoints to return only `no_match` or
`insufficient_evidence`, never activate SmartLogger/S-Dongle, and block Huawei automatic
eligibility whenever reliable discrimination is unavailable. M7-04 creates RED-first code and
positive gateway/branch/version/detection/codec fixtures only for a `PROFILE_ADMITTED`
candidate backed by the published packet. `NO_ADMISSIBLE_PROFILE` creates no implementation
commit, catalog entry, or support claim.

Hardware classification for M7 is `hardware_conditional`: fixtures may publish an
`experimental_opt_in` profile that is disabled by default, but automatic eligibility and
a supported model/gateway/firmware claim require a matching real-device qualification
record. Mixed-catalog closure tests activation, explicit opt-in, qualification, demotion,
disable, and restart lifecycle without permitting a mismatched hardware record.

### M8: private Matter output

After the M5 public rollout, FMV3-M8-00 publishes the sanitized permissive Matter binding
companion for ingress, identity/capability/encoding, trust/credentials, compatibility,
unavailable behavior, recovery, and forbidden imports. Only then is the private Matter
repository generic across future
device classes and has exactly one ingress: packaged `PUBLIC_GRAPHQL_M2M_V1`, using the same
authenticated bounded query/polling, version compatibility, noninteractive least privilege,
confidential channel, verified server identity, and credential lifecycle/recovery contract
as eeBUS. M8-01 requires M8-00 ancestry, its companion metadata, and a security gate and rejects Modbus,
modbusreg, gateway internals, GraphQL subscriptions, and undocumented network paths. PV is the first test slice. M8
does not depend on M6 and is not on the M0-to-M6 critical path. Simulator conformance is
required; hardware is optional until a specific product-support claim is proposed.

## Recovery and stop/go rules

Every runtime/configuration issue includes an explicit disable or recovery action. Before a
public schema is published, rollback may remove the candidate and restore a pre-schema
binary. After publication, the schema and IDs remain: recovery uses a compatible forward
fix, deprecation, capability disable, or only a prior binary/image that still implements
that published schema. Disabled data becomes unavailable. A schema-less image may never
replace a published schema. Persisted state is versioned and may be ignored safely when
producer or schema compatibility fails.

GO requires all dependencies, explicit success outcomes for conditional gates, RED/CI
evidence for code issues, relevant documentation and transport gates, required hardware
classification, and zero unresolved blocker findings.
STOP or NO_GO applies when detection is ambiguous, provenance or licensing is unclear,
private material is required upstream, resource limits fail, a write path is reachable,
required hardware evidence is absent, or recovery cannot restore the prior service.
`NO_GO` and `STOP` are valid evidence outcomes but never progress; completing their issue
does not unlock a conditional edge.
For FMV3-M6-02 specifically, only GO completes the myVaillant plan objective; NO_GO/STOP
preserves the honest lab record without converting issue completion into success. GO cannot
be derived from replay, cache, fixtures, synthetic input, or simulation.

## Non-goals

- No Modbus writes, controls, write probes, or write-capable generic APIs.
- No repository per vendor and no separate SunSpec repository.
- No EMMA profile, register claim, or support promise.
- No private binding logic in public repositories and no public dependency on private CI.
- No automatic GraphQL, Portal, HA, eeBUS, or Matter promotion from raw profile availability.
- No claim that myVaillant interoperability is already proven.
- No implementation, repository creation, issue creation, commit, push, or plan lock in
  this drafting task.

## Review and lock state

Each review epoch contains exactly five bounded OpenAI-only adversarial rounds and has state
`IN_PROGRESS`, `FAILED`, or `PASSED`. A nonterminal package has exactly one highest/current
`IN_PROGRESS` R1-R5 set. Closed epochs remain immutable epoch-qualified summaries and
evidence; their rounds and findings are never deleted or relabeled. A finding is valid
only when it identifies a concrete blocker in implementability, correctness/data integrity,
protocol interoperability, security/safety, licensing/IP boundary, operability/recovery,
testability, or dependency/DAG feasibility. Reviewers may not demand implementation-level
cryptographic proof systems or a validator that emulates the product. Raw reviewer verdict
is recorded separately as `FINDINGS` or `NO_FINDINGS`; integration is `CLOSED` for findings
and `NOT_REQUIRED` for no findings. R1-R4 may honestly return either verdict and count once
their matching integration state is recorded. A `PASSED` epoch requires five accepted rounds,
accepted R1-R5, R5 `NO_FINDINGS`, integration `NOT_REQUIRED`, `finding_ids: []`, and target
`TERMINAL_NO_FINDINGS`. It is the exactly one highest/current review terminal and permits zero
`IN_PROGRESS` epochs. R5 `FINDINGS` may close an active epoch as `FAILED` only after integration
is `CLOSED`; that epoch is then archived without deletion or relabeling, and the revised
unlocked package opens the next epoch at R1, with no invented finding or R6.
For every epoch and round, `plan.yaml` records reviewer verdict, integration state, and the
exact ordered globally unique `finding_ids`; validation compares that order to the review
table and requires `[]` for `NO_FINDINGS`.
A terminal `PASSED` review does not itself lock the plan. The separate operator action on
2026-07-14 authorizes this package to enter `locked` state without changing the reviewed
technical execution contract.

Epoch 1 R1 recorded reviewer verdict `FINDINGS`, integrated eleven valid findings as
`CLOSED`, and was accepted against snapshot
`55942929023f07b7b85776b519d8e7cab16c92d2465b63c2363bc862a423a87c`.
Epoch 1 R2 recorded reviewer verdict `FINDINGS`, integrated seven valid findings as
`CLOSED`, and was accepted against snapshot
`c6a3043660bd72114e4f451533a08b631ae2ab648ab68a300d4fd14f124410e5`.
Epoch 1 R3 recorded reviewer verdict `FINDINGS` against pre-repair snapshot
`5d2319c0a97cd7959e04d8a691612a856d142a03221407d6729c40d84e36d7ac`; R3-F01 through
R3-F05 are integrated `CLOSED` in this revision.
Epoch 1 R4 recorded reviewer verdict `FINDINGS` against pre-repair snapshot
`b5b4b6ebaf6579f5a507dc0fab26d00df1a17a814c34517597ff1f426f3a91e9`; R4-F01 through
R4-F05 are integrated `CLOSED` in this revision.
Epoch 1 R5 recorded reviewer verdict `FINDINGS` against snapshot
`467616a20c8527e71b3cd57e8f9fa2fa47f30f64ef00a0e71b233bbde6c22355`; R5-F01 added
the missing `security` gate to FMV3-M5-05 without changing its existing machine-to-machine
GraphQL design or acceptance contract. Integration reached `CLOSED` before epoch 1
transitioned to `FAILED`, and its R1-R5 history is archived immutably.

Epoch 2 R1 recorded reviewer verdict `FINDINGS` against snapshot
`b7483351faf61cf27362f920ebc1ac04145e8ec6a701d24e1a4898c43d00be88`; E2-R1-F01 through
E2-R1-F03 remain integrated `CLOSED`. Epoch 2 R2 recorded reviewer verdict `FINDINGS`
against pre-repair snapshot
`65995df36c0af95196c1259a8a9e9c5396506e3238455818ed98241d6bc7bc2e`; E2-R2-F01 through
E2-R2-F03 remain integrated `CLOSED`. Epoch 2 R3 recorded reviewer verdict `FINDINGS`
against pre-repair snapshot
`fbdc798570105c8a8daab2d1ae1208455db40411fde0b98f6a1b7dcb0486302e`; E2-R3-F01 through
E2-R3-F06 remain integrated `CLOSED`. Epoch 2 R4 recorded reviewer verdict `FINDINGS`
against pre-repair snapshot
`9cebd062800c3b125963c4f0541163122f3a38a5d80ed5f3a282ebe0a345c115`; E2-R4-F01 through
E2-R4-F03 remain integrated `CLOSED`. Epoch 2 R5 recorded reviewer verdict `FINDINGS`
against snapshot `987d594f721af943fc65f6f47e5f48d8d3b72011b656fd2db79dd13adceb4796`;
E2-R5-F01 through E2-R5-F03 are integrated `CLOSED` in this revision. They add the future
terminal `PASSED` model, separate full-transmit response-wait behavior from the five abnormal
write results, and repair the review claim register. Epoch 2 then transitioned to `FAILED`
and was archived immutably with its R1-R5 history preserved.

Epoch 3 R1 recorded reviewer verdict `FINDINGS` against snapshot
`d0e23922b27030b241688dec85d5e79f28de4d6730e6964511e71b6ff10b1c36`; E3-R1-F01 through
E3-R1-F05 are integrated `CLOSED` for semantic ordering, coalesced wire/view identity,
EMMA discrimination, RTU qualification, and Matter ingress. Epoch 3 R2 recorded reviewer
verdict `FINDINGS` against snapshot
`19f83175eaffc54e6e6ea5bb0f8282d0c6400e9c440ceacc80cbf5b75725f07b`; E3-R2-F01 is
integrated `CLOSED` by making Huawei positive admission public, licensed, conditional, and
fail-closed. Epoch 3 R3 recorded reviewer verdict `FINDINGS` against snapshot
`3dcfab8e8c094d8be6010caa50015100163741e460ce109c5b32ab6154eccf30`; E3-R3-F01 and
E3-R3-F02 are integrated `CLOSED` through public eeBUS/Matter companions, sanitized
post-lab publication or STOP, and consistent active-state validation. Epoch 3 R4 recorded
reviewer verdict `FINDINGS` against snapshot
`ddc3962b53f4ce8d5d29a737c501cd4eab2e30ccd2e3e4bab12a16113c95a58e`; E3-R4-F01 is
integrated `CLOSED` by assigning FC2B/MEI0E identity to the runtime and gating every M7
detector operation on its allowlist. Epoch 3 R5 recorded `NO_FINDINGS` against snapshot
`320f9383d26b640a423ad5902cad90643dc42e18d2c76544f6293d46253866ea`, with no findings and
integration `NOT_REQUIRED`. Epoch 3 is the sole highest/current terminal `PASSED` epoch.
Accepted rounds: `5/5`. Current target: `TERMINAL_NO_FINDINGS`.
Lock authorized: `yes`, for plan publication only.
