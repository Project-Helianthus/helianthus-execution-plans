# Roadmap gates and risks

Canonical-SHA256: `d01dcf33f46878f30c3a627e7e037a69660d55ab8d23ee8294923261b3979ee6`

Depends on: Chunks 10-12 and the issue DAG in `plan.yaml`.
Scope: Milestone grouping, critical path, TDD, documentation and transport gates, hardware classes, rollback/recovery, review, and stop/go decisions.
Idempotence contract: Re-evaluating readiness from unchanged issue and gate states yields the same ready set and does not create work, accept a review, or lock the plan.
Falsifiability gate: Reject the roadmap if an issue has multiple repository owners, a dependency is missing/cyclic, GraphQL or a downstream consumer can precede lock of the tested semantic MCP, a required gate has no evidence, or rollback crosses ownership boundaries.
Coverage: Decisions D05-D07, D10-D12; milestones M0-M8; all phase and conditional gates and risks R01-R08.

## Claim register

**Proven**

- Epoch 1 R1 closed eleven valid findings and records reviewer verdict `FINDINGS` with
  integration `CLOSED`.
- Epoch 1 R2 closed seven valid findings and records reviewer verdict `FINDINGS` with
  integration `CLOSED`.
- Epoch 1 R3 closed R3-F01 through R3-F05 and records reviewer verdict `FINDINGS` with
  integration `CLOSED`.
- Epoch 1 R4 closed R4-F01 through R4-F05 and records reviewer verdict `FINDINGS` with
  integration `CLOSED`.
- Epoch 1 R5 closed R5-F01 and records reviewer verdict `FINDINGS` with integration
  `CLOSED`; epoch 1 then transitioned to `FAILED` and was archived immutably.
- Epoch 2 R1 closed E2-R1-F01 through E2-R1-F03 and records reviewer verdict `FINDINGS`
  with integration `CLOSED`.
- Epoch 2 R2 closed E2-R2-F01 through E2-R2-F03 and records reviewer verdict `FINDINGS`
  with integration `CLOSED`.
- Epoch 2 R3 closed E2-R3-F01 through E2-R3-F06 and records reviewer verdict `FINDINGS`
  with integration `CLOSED`.
- Epoch 2 R4 closed E2-R4-F01 through E2-R4-F03 and records reviewer verdict `FINDINGS`
  with integration `CLOSED`.
- Epoch 2 R5 closed E2-R5-F01 through E2-R5-F03 and records reviewer verdict `FINDINGS`
  with integration `CLOSED`; epoch 2 then transitioned to `FAILED` and was archived
  immutably at snapshot `987d594f721af943fc65f6f47e5f48d8d3b72011b656fd2db79dd13adceb4796`.
- Epoch 3 R1 closed E3-R1-F01 through E3-R1-F05 against snapshot
  `d0e23922b27030b241688dec85d5e79f28de4d6730e6964511e71b6ff10b1c36` and records
  reviewer verdict `FINDINGS` with integration `CLOSED`.
- Epoch 3 R2 closed E3-R2-F01 against snapshot
  `19f83175eaffc54e6e6ea5bb0f8282d0c6400e9c440ceacc80cbf5b75725f07b` and records
  reviewer verdict `FINDINGS` with integration `CLOSED`.
- Epoch 3 R3 closed E3-R3-F01 and E3-R3-F02 against snapshot
  `3dcfab8e8c094d8be6010caa50015100163741e460ce109c5b32ab6154eccf30` and records
  reviewer verdict `FINDINGS` with integration `CLOSED`.
- Epoch 3 R4 closed E3-R4-F01 against snapshot
  `ddc3962b53f4ce8d5d29a737c501cd4eab2e30ccd2e3e4bab12a16113c95a58e` and records
  reviewer verdict `FINDINGS` with integration `CLOSED`.
- Epoch 3 R5 returned `NO_FINDINGS` against snapshot
  `320f9383d26b640a423ad5902cad90643dc42e18d2c76544f6293d46253866ea`, with no findings and
  integration `NOT_REQUIRED`.
- Epoch 3 is the sole terminal `PASSED` epoch at `5/5`, targeting `TERMINAL_NO_FINDINGS`.
- The predecessor package remains separate forensic history.

**Hypothesis**

- The issue DAG allows useful parallel work without placing vendor expansion or Matter on
  the Fronius-to-eeBUS critical path.

**Unknown**

- Calendar dates, assignees, repository creation dates, and hardware windows until
  pre-execution planning.

## DAG interpretation

Milestones are groupings, not cross-repository issues and not automatic serial barriers.
The issue graph in `plan.yaml` and `90-issue-map.md` is authoritative. FMV3-M1-03 depends
on M1-02, serializing TCP before RTU. FMV3-M7-01 waits until the critical docs lane reaches
FMV3-M5-09 and closes only after the complete Growatt contract, a public qualified admission
packet or `NO_ADMISSIBLE_PROFILE` for every SmartLogger/S-Dongle candidate, plus an EMMA
gateway/model/software/version discriminator inventory or per-field unavailable markers are
public and merged; FMV3-M7-02 retains its M1/M2/Fronius dependencies plus M7-01 ancestry.
Only then does `helianthus-modbusreg` serialize SunSpec expansion, Growatt
disposition, Huawei, and mixed-catalog closure. Completed `NO_ADMISSIBLE_PROFILE` preserves
the pre-published Growatt evidence/unsupported status and releases Huawei without a
conditional GO gate or later docs change. Huawei RED/code and positive fixtures exist only
for admitted candidates; non-admission forbids code/catalog/support claims. Huawei and
mixed-catalog negative fixtures keep EMMA deferred and block automatic eligibility when
reliable discrimination is unavailable. M8 starts after packaged FMV3-M5-08, consumes exactly
`PUBLIC_GRAPHQL_M2M_V1` as its sole ingress, and has no M6 dependency. `91-milestone-map.md` shows
the coarse graph and critical path.

No executable issue edits more than one repository. The existing `.github` governance
issue creates four repositories; each destination bootstrap issue depends on creation and
runs only after its repository exists. A consumer issue depends on the producing repository
issue and consumes a versioned artifact or contract. This draft creates no repository.
The machine-readable per-repository mutex is owned by `cruise-topology` and
`cruise-preflight` and permits at most one active issue and one active PR in each repository.
The validator checks that declaration and required DAG edges without runtime scheduling simulation.

FMV3-M1-00 follows public Modbus bootstrap and M0 boundary documentation in the existing
public docs repo. One issue/PR merges the bounded M1 Modbus protocol, TCP/RTU,
scheduling/recovery, MBAP correlation, physical `wire_response_id` plus per-observation
`logical_view_id`/slice identity, unequal-overlap replay and incompatible-coalescing tests,
and the runtime-versus-codec contract plus the named `RTU_PHYSICAL_QUALIFICATION_V1`
dispositions/evidence and
complete M2 source-observation/provenance, detector activation lifecycle, hardware
qualification, coherence, and fixture/mutation contracts. FMV3-M1-01 through FMV3-M1-04
and FMV3-M2-01 through FMV3-M2-03 retain its `doc_gate` and `companion_issue` metadata and
direct or explicit acyclic ancestry, preserving one docs issue/PR at a time.
FMV3-M5-02 likewise retains M4 GO/evidence ancestry and merges the public canonical PV
contract before FMV3-M5-01 semantic implementation; the validator checks this ancestry.
FMV3-M5-04 then depends on M5-01/M5-02 and produces the candidate golden- and live-tested
semantic MCP before FMV3-M5-03 reviews and locks that exact version. Later in the same
serialized docs lane, FMV3-M5-09 depends on M5-03 `GO` ancestry and is the one public
`PUBLIC_GRAPHQL_M2M_V1` companion issue/PR before FMV3-M5-05 GraphQL implementation. The
current DAG contains 43 issues, and semantic GO never gates M5-04.
FMV3-M3-01 is separately the companion for M3-02/M3-03; FMV3-M7-01 is the companion for
M7-02/M7-03/M7-04, with exact companion metadata and ancestry in `plan.yaml`.

## Required gates

**TDD:** Every implementation path starts with a test-only RED commit. CI must observe that exact
commit failing for the intended missing behavior before implementation is pushed. A test
that fails for syntax, environment, or unrelated reasons does not satisfy RED. Growatt
`NO_ADMISSIBLE_PROFILE` performs no implementation and creates no catalog entry; M7-01 has
already merged the public evidence/unsupported disposition and exact code/document mapping.
`PROFILE_ADMITTED` alone triggers M7-03 RED/code, with no later companion docs change.
Fronius M3-03 uses `TDD_RED_IF_OVERLAY_REQUIRED`; `STANDARD_ONLY`
requires public evidence and green conformance CI but no implementation commit or empty overlay. Docs,
evidence-only dispositions, governance, lab-only, and repository-bootstrap work use their
named non-code gates.

**CI:** Repository-local CI is green at issue head. Generated artifacts and fixtures are
deterministic. Failures in unrelated profiles do not get waived by narrowing test scope.

**Documentation:** Architecture, protocol/profile evidence, semantic behavior, state
transitions, and reverse-engineered knowledge trigger the docs gate in
`Project-Helianthus/helianthus-docs-ebus`. Documentation distinguishes Proven,
Hypothesis, and Unknown and names normative code/schema ownership. M1 implementation has
the bounded FMV3-M1-00 companion merged first. M2 implementation reuses the same merged
companion for its complete public contracts; issue completion without that ancestor,
`doc_gate`, and companion metadata is invalid. M5 canonical documentation in FMV3-M5-02
must merge before semantic implementation in FMV3-M5-01. FMV3-M5-04 then implements and
golden/live-tests candidate semantic MCP before FMV3-M5-03 can lock that exact version.
After M5-03 GO, FMV3-M5-09 must merge the GraphQL schema projection, external
access/security/channel, compatibility/versioning, credential lifecycle, and recovery
contract before companion-bearing FMV3-M5-05 implementation.
M3-02/M3-03 carry FMV3-M3-01 companion metadata and ancestry. M7-02/M7-04 carry required
FMV3-M7-01 metadata; M7-03 also requires and consumes that already-merged companion before
either disposition, while only `PROFILE_ADMITTED` conditionally triggers RED/code.

**Transport:** Changes to Modbus protocol, TCP, RTU, endpoint scheduling, or gateway
transport composition run the applicable transport matrix. Existing gateway transport
paths also run their repository-required regression gate. No unexpected failure or xpass
is accepted. Gateway composition also proves that only `internal/modbusadapter` imports
`helianthus-modbus`/`helianthus-modbusreg`, while gateway core passes against a fake of the
existing protocol-agnostic adapter interface. FMV3-M1-02 deterministically proves one MBAP
allocator/map per TCP connection across concurrent units, out-of-order response matching,
cancellation/timeout tombstones that cannot be reused on the same socket, controlled
generation-changing rollover at tombstone exhaustion, old-generation late-frame rejection,
and bounded successful non-abandoned correlation. FC03/FC04 matching uses active connection
generation and transaction ID plus echoed unit/function and applicable byte-count constraints;
requested offset is provenance, not a response match field. FMV3-M1-03/04 prove that an
abandoned transmitted RTU request blocks successors through bounded endpoint-declared
response latency plus bus-idle resynchronization, discards every quarantine frame, and
disables/recovers the endpoint if quiescence is not reached. Unit/profile state stays
isolated and runtime correlation owns no profile semantics. The exact ordered abnormal-result
set is `provable_zero`, `partial_write`, `indeterminate_error`, `cancellation_race`,
`ambiguous_completion`. Only `provable_zero` avoids abandonment after invocation; M1-02
through M1-04 cover all five in that order. TCP possibly-transmitted abnormal results tombstone
the ID, close to prevent stream desynchronization, reconnect with incremented generation,
and reject old-generation frames. Each of the other four results makes RTU enter the same
quarantine/resynchronization or endpoint recovery before any successor. Separate
`full_transmit_success` enters `response_wait` for both transports. TCP response-wait timeout
or cancellation tombstones the ID, drops late response, and forbids same-socket reuse until
normal tombstone rollover; RTU response-wait timeout or cancellation enters existing
quarantine/resynchronization. The matrix contains exact rows
`tcp_full_transmit_timeout_tombstone`, `tcp_full_transmit_cancellation_tombstone`,
`rtu_full_transmit_timeout_quarantine`, and `rtu_full_transmit_cancellation_quarantine`.
Coalescing binds one `wire_response_id` to the physical request/range and one linked
`logical_view_id` plus exact slice identity to each dependent observation. Unequal
overlapping compatible reads must replay each view's exact words and provenance; cross-unit,
cross-table, cross-authorization, cross-generation, and deadline-incompatible reads must
not coalesce. FMV3-M1-00/M1-02 and M2-01/M2-03 mirror and mutate this contract.

RTU records exactly `PHYSICALLY_QUALIFIED` or `FIXTURE_ONLY_NO_HARDWARE` against
`RTU_PHYSICAL_QUALIFICATION_V1`. Physical qualification requires adapter/transceiver
identity, baud and topology, measured physical silent intervals, and a physical
timeout/cancellation quarantine trace. Fixture-only RTU remains default-disabled and
experimental with no enabled or supported claim. Missing RTU hardware blocks neither
TCP/Fronius nor TCP-sufficient M1/M7 work.

**Hardware:**

- `hardware_required`: Fronius M4 live proof, public packaged M5 rollout, and M6
  myVaillant interoperability from an enabled, qualified live Fronius endpoint with a fresh
  observation generated after recorded lab-run start.
- `hardware_conditional`: RTU permits `FIXTURE_ONLY_NO_HARDWARE` closure as a default-disabled
  experimental capability with no enabled/supported claim; only exact
  `RTU_PHYSICAL_QUALIFICATION_V1` evidence yields `PHYSICALLY_QUALIFIED`. M7 fixture-only
  profiles remain default-disabled `experimental_opt_in`, while `auto_eligible` requires a
  matching profile-version and hardware-tuple qualification record. Lack of RTU hardware
  does not block TCP/Fronius or TCP-sufficient M1/M7.
- `hardware_optional`: M8 until a concrete Matter product-support claim is proposed.
- `not_applicable`: governance, pure contracts, deterministic fixtures, and docs, unless
  their issue acceptance says otherwise.

**Conditional outcomes:** Dependency completion never substitutes for an outcome gate.
FMV3-M4-04 records `GO`, `NO_GO`, or `STOP`, FMV3-M4-05 packages the exact outcome, and M5
work requires M4-04 `GO` plus completed M4-05. FMV3-M5-04 first implements and tests the
candidate semantic MCP after M5-01/M5-02. FMV3-M5-03 then records `GO`, `NO_GO`, or `STOP`
on that exact version; M5-09 and every later consumer descendant require its `GO`, while
M5-04 is outside the gate.
`NO_GO` and `STOP` remain honest evidence but unlock nothing. The validator checks only
these declared issue references, outcome values, and ancestry; it does not simulate
hardware or runtime behavior. M3 Fronius and M7 Growatt dispositions are ordinary completed
issue states, not conditional GO gates: either allowed M3 disposition releases M4, and
Growatt `NO_ADMISSIBLE_PROFILE` releases Huawei without a catalog entry or support claim.
FMV3-M6-02 independently records `GO`, `NO_GO`, or `STOP`; completion is not progress and
only GO satisfies the plan objective when the same available non-stale live Fronius
observation generated after run start traverses `PUBLIC_GRAPHQL_M2M_V1` and eeBUS to the
accepted myVaillant observable with matching identity, value, unit, semantics, quality, and
timestamps. Replay, synthetic input, retained-cache-only data, fixtures, and simulation
cannot GO; NO_GO/STOP remains honest evidence and no success.

**Semantic lock:** Raw MCP and sanitized live evidence precede merged canonical docs,
semantic code, candidate semantic MCP golden/live proof, and then a separate GO/NO_GO/STOP
decision on that exact tested version. Promotion is candidate semantic MCP -> M5-03 lock GO
-> one public GraphQL companion-doc issue -> one externally routable
machine-to-machine GraphQL implementation -> GraphQL-only semantic Portal plus separately
authenticated bounded raw Portal diagnostics -> HA -> packaged external-service-context
proof. Public sanitized eeBUS and Matter binding companions merge after rollout and before
private protocol code. Private eeBUS consumes exactly that tested contract and publishes
reusable post-lab findings through M6-03 or records STOP; private-only protocol knowledge
cannot satisfy M6. Credential-bearing external GraphQL uses an authenticated confidential
channel with verified server identity; plaintext external access and untrusted identity fail
closed without prescribing the mechanism. M5-08 and M6-01 test both rejection paths. Raw
registers remain outside GraphQL. Private Matter independently starts only after M5-08 plus
its public companion and
uses the same packaged `PUBLIC_GRAPHQL_M2M_V1` as its sole authenticated bounded-polling
ingress, with compatible versions, confidential verified-server transport, credential
lifecycle/recovery, and security rejection of private/internal/undocumented alternatives.

**Write safety:** The transport-write completion contract describes socket/serial I/O for
read requests and does not authorize a Modbus write function. The read-only allowlist is a phase gate. Discovery, raw MCP, profiles,
semantic APIs, and private bindings expose no write path. Any proposed write starts a
separate plan.

## Recovery contract

Before activation, configuration is validated atomically. Each endpoint and profile has
an explicit disable. TCP `partial_write`, `indeterminate_error`, `cancellation_race`, or
`ambiguous_completion` retains a socket-lifetime tombstone and forces close/reconnect; the
same four RTU triggers delay successors until response-latency plus bus-idle quarantine
completes and disable/recover a nonquiescent endpoint. Separate `full_transmit_success`
enters `response_wait`: TCP timeout/cancellation tombstones the ID and drops late response
under normal rollover, while RTU timeout/cancellation enters the same quarantine path.
Cancellation and shutdown release
other endpoint ownership/resources. Source
observations preserve validity/timestamps and sample/generation/dependency plus physical
wire-response and per-observation logical-view/slice identity; only `ebusreg` applies
canonical quality/freshness transitions. Reconnect is
bounded and revalidates changed identity. Qualification mismatch or revocation demotes
automatic profile eligibility and emits no synthetic replacement observation.

Pre-publication candidates can be removed and a schema-less image restored. After
publication, schemas and IDs remain; recovery uses a compatible image/forward fix or
deprecation, and disabled data is reported unavailable. A schema-less image may not replace
a published schema. Add-on rollout proves both phases plus GraphQL service credential
provisioning, rotation, revocation, disable, and recovery from an external service context.
That external proof also rejects plaintext and untrusted server identity before credential
use without prescribing the confidential-channel mechanism.
Private binding failure disables
only that output; eeBUS disable/recovery also preserves or explicitly resets trust according
to the tested SHIP lifecycle. Vendor profile failure disables only that catalog entry unless
the shared runtime gate also fails.

## Risk decisions

| Risk | Blocking evidence | Required response |
|---|---|---|
| Wrong profile or ambiguity | More than one eligible interpretation or incomplete identity | Fail closed; add evidence/fixture; do not promote |
| Data corruption | FC03/FC04 alias, documentary off-by-one mapping, physical wire/logical slice alias, incompatible coalescing, wrong word/byte order or string packing/padding, mixed generation, torn multi-response sample, or conflated source/canonical state | Reject observation; repair wire-response/logical-view identity and mutation coverage, normalization/coherence, versioned modbusreg codec/provenance, or ebusreg transition |
| Endpoint starvation/correlation | Queue, fairness, deadline, same-socket tombstone reuse, tombstone exhaustion rollover, old-generation TCP frame, RTU late same-shape frame, failed bus-idle resynchronization, or reconnect failure | Disable endpoint; fix the shared scheduler, per-connection allocator/generation, or RTU quarantine/recovery before profile work |
| Huawei branch drift, unowned detector operation, unlicensed admission, or EMMA collision | Candidate needs a PDU outside FC03/FC04/FC2B-MEI0E, lacks public applicability, or EMMA could activate a profile | Enumerate every probe against the runtime allowlist; unsupported operations force non-admission, modbusreg cannot frame PDUs, packets stay public/licensed, and missing discrimination blocks auto-eligibility |
| IP boundary breach | Public artifact needs restricted/private source | Quarantine artifact; rebuild clean evidence or stop profile |
| External GraphQL or myVaillant incompatibility | Plaintext credential path, untrusted server identity, or the exact packaged GraphQL/eeBUS path cannot carry the same fresh post-run-start observation from an enabled qualified live Fronius endpoint to the accepted myVaillant observable | Fail closed; replay/cache/fixture/synthetic/simulator input cannot GO; disable private output and preserve the public contract and sanitized honest evidence |
| Accidental write surface | Reachable write request or control | Immediate STOP; remove surface; require separate safety plan |
| Matter ingress/trust violation | M8 uses anything except packaged PUBLIC_GRAPHQL_M2M_V1, lacks compatible authenticated/confidential verified-server access or credential lifecycle, or imports private/internal/undocumented ingress | Fail closed; reject the import/path in security tests and disable Matter without changing the public contract |
| Fixture-only support claim | RTU lacks RTU_PHYSICAL_QUALIFICATION_V1 or a profile lacks its matching hardware record | Keep RTU/profile default-disabled experimental with no enabled/support claim; block profile auto-eligibility while allowing TCP-sufficient work |

## Review process

Each epoch has five bounded OpenAI-only adversarial rounds and state `IN_PROGRESS`, `FAILED`,
or `PASSED`. A nonterminal package has exactly one highest/current `IN_PROGRESS` R1-R5 set.
Closed epochs remain immutable epoch-qualified summaries/evidence; their rounds and findings
are neither deleted nor relabeled. A valid finding names a concrete
blocker in one allowed review category and points to the affected contract, issue, gate,
or dependency. Findings outside scope, requests for implementation-level cryptographic
proof systems, and demands that the validator emulate product behavior are rejected as
invalid review expansion. Raw reviewer verdict is `FINDINGS` or `NO_FINDINGS`; integration
is recorded separately as `CLOSED` or `NOT_REQUIRED`, respectively. R1-R4 may honestly be
`NO_FINDINGS` and still count. `PASSED` requires accepted rounds 5, accepted R1-R5, R5
`NO_FINDINGS`, integration `NOT_REQUIRED`, `finding_ids: []`, and target
`TERMINAL_NO_FINDINGS`; it is the exactly one highest/current review terminal and permits
zero `IN_PROGRESS` epochs. R5 `FINDINGS` may close an active epoch as `FAILED` only after
integration is `CLOSED`; it is archived intact, then the revised unlocked package opens the
next numbered epoch at R1 without relabeling, inventing findings, or adding R6. Epochs 1 and
2 followed that transition after their R5 integrations closed. Epoch 3 R1-R4 returned
`FINDINGS`; E3-R1-F01 through E3-R1-F05, E3-R2-F01, E3-R3-F01/F02, and E3-R4-F01 are integrated
`CLOSED` against their snapshots. Epoch 3 R5 returned `NO_FINDINGS` with `NOT_REQUIRED` and
no finding IDs, so epoch 3 is the sole terminal `PASSED` R1-R5 set at `5/5`, targeting
`TERMINAL_NO_FINDINGS`. Machine-readable
round metadata records verdict, integration state, and exact ordered unique finding IDs;
the validator compares those lists to every accepted review table and requires `[]` for
`NO_FINDINGS`.

Even a terminal `PASSED` review leaves the plan unlocked until the canonical hash mirrors
validate, status is consistent, and the operator separately authorizes lock. The operator
provided that authorization on 2026-07-14. This publication performs no semantic lock or
product implementation.

## Stop/go summary

An issue is ready only when every dependency exists and is complete, its repository exists,
and entry gates are green. Conditional descendants additionally require the declared GO,
not just gate-issue completion. GO requires acceptance and all named gates. NO_GO or STOP is a
valid deliverable for detector ambiguity, unsupported hardware, semantic lock, or private
interoperability; it preserves evidence, is not progress, and prevents unsafe downstream work. No schedule
pressure overrides licensing, write safety, semantic lock, required hardware, recovery, or
public/private direction.
