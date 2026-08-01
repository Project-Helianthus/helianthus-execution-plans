# Architecture and repository boundaries

Canonical-SHA256: `6b6ec69cbfc38b80aef763b6df602d1d4ed169f8ee22866e0459e3246ef8751f`

Depends on: Operator brief dated 2026-07-14 and root/repository `AGENTS.md` contracts.
Scope: Public layer ownership, endpoint/runtime behavior, standard and vendor profile ownership, canonical metadata, and public/private dependency direction.
Idempotence contract: Reapplying these boundaries creates no additional repository, owner, scheduler, profile catalog, semantic ID, or binding direction.
Falsifiability gate: Reject this chunk if any required behavior has two owners, an import points upward/private-to-public, a profile owns endpoint lifecycle, or a decoded value cannot be traced to bounded raw evidence.
Coverage: Decisions D01-D05, D07-D08, D11-D13; issues M0, M1, M2; risks R01-R03, R05, R07-R08.

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
| Transport/runtime | `Project-Helianthus/helianthus-modbus` | TCP, RTU, endpoint owner, queues, fairness, coalescing, deadlines, cancellation, backoff, reconnect, limits, metrics, source-issued opaque one-shot acquisition capability | Vendor detection, register meaning, attempt publication, PV semantics, private bindings |
| Modbus protocol | `Project-Helianthus/helianthus-modbus` | ADU/PDU types, FC03/FC04 register reads, FC2B/MEI0E Device Identification, exceptions, uninterpreted words/bytes, correlation | Signedness, scale, units, source validity, canonical values, writes in this plan |
| Profile registry | `Project-Helianthus/helianthus-modbusreg` | Catalog, profile API, signedness/scale codecs, source-observation validity/timestamps, independently owned bounded attempt ledger, detector, fixtures, standard families, vendor overlays | Sockets, serial ownership, capability issuance, retries, canonical quality/freshness/IDs, consumers |
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

The `.github` M0 issue creates the two empty public Modbus repositories. Each destination then
uses one exact no-parent empty-tree root commit to establish `main` as the legal base for issue
#1 / PR #2. That root is the sole direct-push initialization exception per destination; the
bootstrap implementation itself is squash-merged from an issue branch. Private governance
creation remains deferred to `.github` issue FMV3-M0-04; only
after it creates both empty targets may destination bootstraps FMV3-M0-05/FMV3-M0-07 run.
All three require future explicit authorization.
Milestones group related issues but do not own code. Each issue row names exactly one
repository. Cross-repository behavior is joined by explicit dependencies and versioned
contracts, never by one issue editing multiple repositories.
Every executable issue carries an explicit integer `complexity` from 1 through 10. Preflight
materializes the plan-pinned model router and policy, executes the exact role/complexity/risk route
in OpenAI-only mode, and requires an issue/anchor-bound non-degraded prescription receipt before
claim acquisition. `max` support is never assumed: the launcher flag is supplied only after the
active owner-trusted orchestration mechanism confirms it can apply that effort. Public docs issues
route as `docs/architecture`; other authorized issues route as `developer`. Protocol, security,
concurrency, and recovery gates map to pinned risk overrides.

The machine-readable `repository_mutex` is enforced by `cruise-topology` and
`cruise-preflight`: one protected append-only v2 CAS ref exists per repository, and authorization
requires exactly the selected issue open with no open PR. A no-bypass integrity ruleset forbids
claim-ref deletion/non-fast-forward, while a separate writer ruleset restricts creation/update to
the administrator bypass. The anchored owner actor and HMAC commitment are verified before first
acquisition and on every signed event. Each acquisition renews or takes over by fast-forwarding
from the exact observed ref. Release appends a signed tombstone from the exact acquired SHA, so
history, generation, and ownership cannot reset through deletion. The returned ledger/generation/
SHA/expiry fence is checked through the 512-event authenticated chain to genesis. The final event
is reserved for release, after which a future anchored owner-epoch rotation is required. Claim-ref
mutation re-reads the exact remote ref after every push result: exact target is reconciled
success, while any other or unavailable result forces completion-ambiguous `STOP` without retry.
Standalone `--verify-claim` is read-only diagnostic; protected GitHub mutations use `--fenced-gh-api`, which
holds the stable host-local kernel process lock plus owner-secret inode lock and performs exact
pre/post verification around one declared issue-bound REST capability with payload checks, using a
fresh private one-shot validator directory for each check. Every check also re-observes the exact
selected issue and a capability-specific open-PR mutex: pull creation transitions from zero open
PRs to exactly one same-repository `main` PR from the selected issue branch with the exact anchored
issue title and exactly one closing reference; issue comments/labels permit at most that exact PR;
repository creation permits none. Any competing PR race forces
completion-ambiguous `STOP` and reconciliation. The fixed allowlist covers exact-schema
selected-issue comments/labels, exact-schema PR creation with exactly one selected-issue closing
reference, and the FMV3-M0-01-only exact minimal payload for either named public repository; issue
edits, extra fields/references, and all other endpoints fail closed. A long-running same-run owner
uses `--renew-claim` with the exact current SHA to
append one signed successor. Lease time comes from GitHub's authenticated API `Date` header and
expiry equality rejects verification. Cross-repository CAS is unavailable, so either a nonzero
mutation result or a post-check failure forces `STOP` without retry and reconciliation rather than
claiming that the mutation was atomically prevented.
Branch publication and deletion use ordinary Git push under the active repository claim; the REST
allowlist has no `git/refs` capability.
Mutation payloads are parsed once from retained bytes and supplied to `gh` over stdin, so replacing
the private pathname cannot alter the authorized request. Postflight executes after every attempted
mutation subprocess exit, including interrupts and exceptions. The canonical checkout fetches full
history reachable from the observed `main` SHA so the permanent PR #91 anchor survives later main
commits. Required-status legacy contexts must all map to app-bound checks, and the two docs owner
attestations require strict distinct lowercase UUIDs and independently distinct output digests.
The post-merge anchor job checks out and asserts the immutable push-event SHA rather than resolving
the moving `main` branch name.
The
M1-06 authorization additionally pages immutable GitHub PR history and rejects any PR
whose open interval overlaps either the harness or product PR interval.

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

PR #89 remains predecessor provenance for the successor lane. PR #91 becomes the sole
current authorization anchor only after the fixed GitHub API proves its original base/head
identity, one-parent squash topology, authorized merger, and tree equality with a successful
mandatory non-authoritative same-change-set post-merge canonical-main `push` workflow execution observation at the exact squash SHA, exactly one authenticated official Codex bot review,
two separate submitted authorized-issuer owner process attestations, and their unedited
aggregate. Every record binds its full SHA/tree and `NO_FINDINGS`; the owner attestations bind
fresh OpenAI contexts without masquerading as provider-authenticated artifacts, and the aggregate
binds the workflow run plus all three review IDs. Issue #90 tracks scope but is not evidence.
That immutable PR #91 decision/review is the external bootstrap root and must precede docs PR
#386's merge; it pins the candidate head/tree, normative manifest, policy, validator and tests,
normalized V1 semantics, and critical no-caller-control/runtime-source invariants. Refreshed docs
hashes and same-change-set validation are mandatory but not independent authority.

FMV3-M1-05 follows M1-04 and publishes `OPAQUE_RUNTIME_ACQUISITION_V1` through exact docs
issue #385 and closing PR #386 evidence. FMV3-M1-06 depends explicitly on both M1-04 and
M1-05 and requires docs PR #386 merged with the exact bound head and tree.
FMV3-M2-01 retains its M1-00 companion metadata, records M1-05 as its corrective companion,
depends on M1-06, and accepts the producer only through an external fail-closed JSON file
whose bounded issue/PR/commit/run/review IDs are selectors only. Live GitHub must prove the
immutable marked/title issue; a sequential owner-authored harness PR that alone adds the exact
plan-anchored dual-mode workflow, AST guard, docs-lock validator, and exact merged-docs lock, leaves inherited CI tooling unchanged, passes
required checks plus one clean exact-head Codex review, merges first, and becomes the exact base
of the same-repo closing product squash PR; product head/tree/base topology, issue closure, and
canonical-main ancestry; bounded test-only RED ancestry/diff with exact subject and empty page two;
anchored exact-PR RED guard/compile success followed by exact-suite failure; exact-head required-check
GREEN plus anchored conformance success; and eight exact-parent production-only mutants that retain
the harness blobs, match patch digests precommitted by the GREEN report, pass executable-AST and
parent-baseline guards, compile, and then fail only their mapped mutant tests. One official Codex
canonical-template zero-inline product review and two owner `NO_FINDINGS` process attestations follow
GREEN and all mutations; the fixed closed conformance report binds every pinned case to an exact
nonempty Go test/PASS, patch digest, and production contract symbol. The exact docs R2 commit/tree,
complete predecessor-inclusive
normative closure, and expanded `bounded_values` projection are bound. They require
claim-in-progress, cancelling, atomic all-success-before-seal, source-owned CancelOpen,
byte/field bounds, and pre-reserved non-wrapping, non-reused terminal sequences. M1-06 and
M2-01 still require docs PR #386 merged at that exact head/tree. Exact docs/code revisions
require fresh independent OpenAI review with every finding resolved.

## Profile families

SunSpec is modeled as a standard family because its model identities and data meanings
are intended to apply across conforming manufacturers. FMV3-M3-03 records
`STANDARD_ONLY` when qualified Fronius evidence and the minimal standard implementation
cover the required slice; it creates an overlay only under `OVERLAY_REQUIRED` for qualified
vendor-specific facts. `STANDARD_ONLY` retains Fronius fixtures/live qualification and
unblocks M4 with public evidence, green conformance CI, and no implementation commit or
empty overlay. FMV3-M3-01 is the public companion for M3-02/M3-03. M3-03 CI rejects
TCP-concrete imports, including escaped Go import literals with arbitrary Unicode aliases and
same-line semicolon import declarations, and
activates the profile through a non-TCP fake that implements only the neutral runtime interface.
The bound neutral adapter has no imports or extra declarations: it is test-only for
`STANDARD_ONLY`, while `OVERLAY_REQUIRED` confines it to `profiles/fronius` and requires a
separate non-test implementation source. Named tests share the exact neutral-proof package and
directory, cannot locally redeclare the bound interface, activation, or scan helpers, have no build
constraints or nested module, and run in an exact unskippable YAML job/step pinned to
`./profiles/fronius` for `OVERLAY_REQUIRED` or the proof package path for `STANDARD_ONLY`. `STANDARD_ONLY`
proves a complete evidence-only base/head diff; `OVERLAY_REQUIRED` proves a complete nonempty
test-only parent/RED diff where the RED parent SHA and tree are exactly the fetched PR base SHA
and tree, and where RED retains the identical GREEN canonical test-source blob. The fixed
head/tree assertion is executable after GitHub expression substitution.
Later FMV3-M7-01 is the public companion for M7-02/M7-03/M7-04 and closes only after the complete Growatt
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

Runtime acquisition origin is carried by behavior, not by a forgeable serialized field or
caller boolean. Only the runtime source, after request-bound correlation proves successful
data, an attached dependent, exact logical-slice validation, and coherent production,
issues an opaque non-serializable capability. Private M1
state is shared only across copies of that same capability and is never an M2 ledger
pointer, so copied views racing it produce exactly one winner. Detached, cancelled,
exceptional, malformed, failed, late/abandoned, uncorrelated, torn/incoherent, and all
non-success acquisitions receive none. Coalescing never shares the capability itself:
every dependent logical view receives an independent capability. Endpoint recreation and every new acquisition create fresh
independent state even when visible identity or data match; no acquisition may alias,
remint, reset, or merge a prior state. Existing capability state follows only its own
acquisition/attempt lifecycle. Each capability moves once from `open` to `claimed`,
`cancelled`, `failed`, or `expired`; source-synchronous reclamation precedes terminal
return, uses source-assigned terminal sequence, and retains only finite-positive bounded,
non-reconstructing terminal metadata with lowest-sequence-first eviction. Offline fixtures
receive none.

The private M2 attempt ledger is independent of M1 capability state. Duplicate
`AttemptKey` is rejected. Every admitted claim moves `unresolved -> claim_in_progress` only
while its attempt is `open`, then moves exactly once to `claim_succeeded`,
`capability_cancelled`, `capability_failed`, `capability_expired`, or
`claim_rejected_terminal`; cancellation alone may move a still-`unresolved` claim to
`attempt_cancelled`. Attempts permit exactly `open -> sealed|cancelling`,
`sealed -> publishing|cancelling`, `cancelling -> cancelled`, and
`publishing -> published|publish_failed`. Cancellation blocks admission, seal, and publish,
drains every `claim_in_progress` operation, and closes only remaining `unresolved` claims.
Seal atomically requires every data-bearing runtime claim to be `claim_succeeded`. `Publish()` is the one-shot
`sealed -> publishing` transition, reads immutable sealed ledger state, and accepts no
mutable DTO. Finite-positive limits count all retained attempt and claim states, claims per
attempt, the checked retained-attempt-limit times claim-limit product, and the
audit/tombstone ring; zero, negative, overflow, or inconsistency fails before activation.
Reclamation is deterministic and synchronous on terminal/admission only for terminal state
with no operation in progress or retained nonterminal reference, ordered by ledger-assigned
terminal sequence. The ring stores non-reconstructing immutable terminal metadata and
evicts the lowest sequence first. Offline fixtures are explicitly
untrusted, execute zero capability CAS operations, and cannot mint a production
`sample_id`. The versioned normalization record round-trips exactly, including unknown
extension fields, rather than retaining only the normalized address.

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

M0 governance creates public repositories before public destination bootstrap; deferred
private issues create their repositories only under future explicit authorization and then
record private licenses before code. Evidence intake records source,
license/permission, transformation, applicability, and sanitization. Any unresolved IP
or provenance question blocks the affected profile without blocking unrelated profiles.
