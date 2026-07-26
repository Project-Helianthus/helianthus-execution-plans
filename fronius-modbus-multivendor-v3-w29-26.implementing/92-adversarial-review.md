# Adversarial review contract

Mode: `openai_only`
Required rounds: `5`
Current epoch: `3`
Review state: `PASSED`
Accepted rounds: `5`
Current target: `TERMINAL_NO_FINDINGS`

Each round uses a fresh independent OpenAI planner-adversary context routed to
`gpt-5.6-sol` with reasoning `max`. No Claude context participates.

A valid finding must identify a concrete blocker in at least one allowed category:

- implementability
- correctness/data integrity
- protocol interoperability
- security/safety
- licensing/IP boundary
- operability/recovery
- testability
- dependency/DAG feasibility

Each finding names the affected file/contract/issue, explains the failure mode, and gives
a bounded correction or operator escalation. Reviewers may not demand implementation-level
cryptographic proof systems, convert speculative improvements into blockers, or expand
`validate_plan.py` into a simulation of the product, release system, or rollback runtime.

Raw reviewer verdict and integration state are separate. A completed review records exactly
`FINDINGS` or `NO_FINDINGS`. `FINDINGS` requires integration `CLOSED` and preserves every
closed finding row; `NO_FINDINGS` requires integration `NOT_REQUIRED` and no invented
finding. Rejected findings receive a category/scope reason. R1-R4 may honestly use either
verdict and count as accepted once the matching integration state is present. A pending
placeholder is not accepted.
For each epoch and round, `plan.yaml` records the reviewer verdict, integration state, and
exact ordered globally unique `finding_ids`. Validation compares that list to the review
table, rejects duplicates, omissions, and renumbering, and requires `[]` for `NO_FINDINGS`.

Each epoch is `IN_PROGRESS`, `FAILED`, or `PASSED`. A nonterminal package has exactly one
highest/current `IN_PROGRESS` R1-R5 set. Closed epochs remain immutable summaries and
evidence: their round sections and finding rows are never deleted or relabeled. `PASSED`
requires accepted rounds 5, accepted R1-R5, R5 reviewer verdict `NO_FINDINGS`, integration
`NOT_REQUIRED`, `finding_ids: []`, and target `TERMINAL_NO_FINDINGS`; that exactly one
highest/current terminal epoch permits zero `IN_PROGRESS` epochs. If active R5 returns
`FINDINGS`, integration must first become `CLOSED`; the epoch then closes `FAILED` and is
archived intact before the revised unlocked package opens the next numbered epoch at R1.
No finding is invented to force closure, and there is no R6. Even `PASSED` leaves the plan
unlocked until a separate operator action; that action was provided on 2026-07-14 for plan
publication only.

## Epoch 1

State: FAILED
Accepted rounds: 5
Current target: ARCHIVED
Archive: IMMUTABLE
Archive snapshot: `467616a20c8527e71b3cd57e8f9fa2fa47f30f64ef00a0e71b233bbde6c22355`
Summary: Epoch 1 R5 returned FINDINGS and transitioned to FAILED only after R5-F01 integration closed.
Evidence: The R1-R5 verdicts, finding rows, and concessions remain below; R5 is bound to the archived snapshot.

### R1

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `55942929023f07b7b85776b519d8e7cab16c92d2465b63c2363bc862a423a87c`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| R1-F01 | CLOSED | `.github` creates four repos; destination bootstraps wait for creation |
| R1-F02 | CLOSED | M3 minimal SunSpec issue precedes the Fronius overlay |
| R1-F03 | CLOSED | M7 modbusreg lane is SunSpec -> Growatt -> Huawei -> catalog |
| R1-F04 | CLOSED | GraphQL and Portal are separate; Portal gates HA |
| R1-F05 | CLOSED | eeBUS/Matter implementation waits for packaged public rollout |
| R1-F06 | CLOSED | Schema docs derive from M4 and are independent of schema code |
| R1-F07 | CLOSED | Poll generation and complete dependency-set identity propagate end to end |
| R1-F08 | CLOSED | Protocol emits uninterpreted words/bytes; codecs own signedness |
| R1-F09 | CLOSED | Source validity/time is separate from ebusreg-owned canonical freshness |
| R1-F10 | CLOSED | Post-publication recovery retains schema/IDs and uses unavailable |
| R1-F11 | CLOSED | M6-01 owns RED/simulator scope; M6-02 is real-lab only |

Concessions:

- The one-public-runtime/one-public-profile-registry ownership split was sound.
- The read-only boundary, Huawei parallel-branch caution, and EMMA deferral were sound.

### R2

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `c6a3043660bd72114e4f451533a08b631ae2ab648ab68a300d4fd14f124410e5`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| R2-F01 | CLOSED | Gateway `internal/modbusadapter` implements the existing adapter interface, is the sole gateway modbus/modbusreg importer, and leaves gateway core fake-testable; no repo added |
| R2-F02 | CLOSED | Raw identity now binds endpoint, unit, function/table, zero-based PDU offset, count, and recorded one-based documentary normalization, with FC03/FC04 and address-origin fixtures |
| R2-F03 | CLOSED | Response/sample identity and profile-declared one-response or bounded validated multi-response coherence reject torn reads or emit no observation |
| R2-F04 | CLOSED | FMV3-M7-02 and PG-VENDOR-EXPANSION retain prior dependencies and additionally wait for FMV3-M3-03 |
| R2-F05 | CLOSED | FMV3-M5-06 adds authenticated bounded raw Portal exploration while semantic Portal remains GraphQL-only; M5-08 proves both surfaces |
| R2-F06 | CLOSED | FMV3-M6-01 owns minimum SHIP/SPINE discovery and trust lifecycle simulation; M6-02 verifies it in the real lab; no public eeBUS repo added |
| R2-F07 | CLOSED | Fixture-only profiles are default-disabled experimental opt-in, hardware-record matching gates auto-eligibility, and FMV3-M7-05 tests lifecycle transitions |

Concessions:

- The existing repository split, read-only boundary, and one-issue-per-repository lanes
  remain unchanged.
- The corrections strengthen issue acceptance and ordering without expanding the planned
  repository or issue inventory.

### R3

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `5d2319c0a97cd7959e04d8a691612a856d142a03221407d6729c40d84e36d7ac`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| R3-F01 | CLOSED | Added machine-readable M4/M5 conditional outcome gates: completion is not success, only GO progresses, M4-05 packages evidence, and NO_GO/STOP blocks descendants |
| R3-F02 | CLOSED | Split reviewer verdict from integration state, preserved R1/R2 findings, defined honest R1-R4 NO_FINDINGS handling and R5 FINDINGS epoch restart without relabeling or R6 |
| R3-F03 | CLOSED | Selected authenticated bounded polling of the stable versioned public GraphQL API and required deployment, lifecycle, and live M5 Fronius-to-myVaillant trace evidence |
| R3-F04 | CLOSED | Added bounded FMV3-M1-00 public Modbus companion docs after bootstrap and before all M1 implementation, with doc-gate metadata and acyclic ancestry |
| R3-F05 | CLOSED | Versioned modbusreg codec/provenance now owns word order, applicable intra-word byte order, string packing/padding, and opposing fixture/profile cases |

Concessions:

- The public runtime/profile repository split, read-only boundary, and raw-first delivery
  order remain sound.
- The corrections refine conditional progress, evidence, and interpretation ownership
  without adding a runtime repository or moving codec policy into transport.

### R4

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `b5b4b6ebaf6579f5a507dc0fab26d00df1a17a814c34517597ff1f426f3a91e9`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| R4-F01 | CLOSED | FMV3-M5-05 publishes one externally routable machine-to-machine GraphQL contract, FMV3-M5-08 packages/tests it from a separate service context with least-privilege credential lifecycle and bounds, and M6 consumes exactly that contract without subscriptions or raw GraphQL |
| R4-F02 | CLOSED | FMV3-M3-03 records STANDARD_ONLY or qualified OVERLAY_REQUIRED; both preserve Fronius fixtures/live qualification and release M4, while standard-only creates no overlay |
| R4-F03 | CLOSED | FMV3-M5-01 now depends on merged FMV3-M5-02 documentation with retained M4 ancestry; the phase gate, maps, and validator enforce docs-before-code |
| R4-F04 | CLOSED | FMV3-M7-03 may close NO_ADMISSIBLE_PROFILE with retained evidence/unsupported status and no catalog/support claim, releasing Huawei without another conditional gate |
| R4-F05 | CLOSED | Review state now supports immutable epoch-qualified failed history, exactly one active R1-R5 set, and failed-R5 archive/restart semantics through generic structural validation |

Concessions:

- The 39-issue repository ownership and private/public dependency direction remain sound.
- The corrections reuse existing issues and preserve read-only, no-subscription, and
  no-raw-registers-in-GraphQL boundaries.

### R5

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `467616a20c8527e71b3cd57e8f9fa2fa47f30f64ef00a0e71b233bbde6c22355`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| R5-F01 | CLOSED | Added the missing `security` gate to authoritative FMV3-M5-05 so it matches the issue map and existing acceptance contract; PUBLIC_GRAPHQL_M2M_V1 design is unchanged |

Concessions:

- The externally routable machine-to-machine GraphQL design, acceptance contract, and
  publish/package/consume chain remain sound and unchanged.

## Epoch 2

State: FAILED
Accepted rounds: 5
Current target: ARCHIVED
Archive: IMMUTABLE
Archive snapshot: `987d594f721af943fc65f6f47e5f48d8d3b72011b656fd2db79dd13adceb4796`
Summary: Epoch 2 R5 returned FINDINGS and transitioned to FAILED only after E2-R5-F01 through E2-R5-F03 integration closed.
Evidence: The epoch 2 R1-R5 verdicts, exact finding rows, and concessions remain below; R5 is bound to the archived snapshot.

### R1

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `b7483351faf61cf27362f920ebc1ac04145e8ec6a701d24e1a4898c43d00be88`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E2-R1-F01 | CLOSED | Per TCP connection/socket, one MBAP transaction-ID allocator and one in-flight map correlate all units by expected unit/function/range; late cancellation/timeout responses are quarantined across reuse/wrap, unit/profile state stays isolated, scheduling stays shared, and FMV3-M1-02 owns the deterministic matrix without profile semantics in runtime |
| E2-R1-F02 | CLOSED | Existing FMV3-M1-00 now publishes complete M2 observation/provenance, detector activation, hardware qualification, coherence, and fixture/mutation contracts in the same docs issue as M1; M2-01..03 carry direct/explicit companion ancestry and doc-gate metadata without changing the 39-issue DAG |
| E2-R1-F03 | CLOSED | PUBLIC_GRAPHQL_M2M_V1 requires an authenticated confidential external channel with verified server identity; plaintext and untrusted identity fail closed, M5-08 and M6-01 test both without prescribing mechanism, and raw registers remain outside GraphQL |

Concessions:

- Connection-wide scheduling with isolated unit/profile state preserves the existing runtime/profile boundary.
- Reusing FMV3-M1-00 and the existing M5/M6 issues closes the gaps without adding issues,
  repositories, profile semantics to runtime, or raw GraphQL.

### R2

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `65995df36c0af95196c1259a8a9e9c5396506e3238455818ed98241d6bc7bc2e`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E2-R2-F01 | CLOSED | A transmitted TCP transaction ID abandoned by cancellation/timeout is a socket-lifetime tombstone; same-socket reuse is forbidden, controlled close/reconnect increments generation before tombstoned reuse, and old socket/generation frames are rejected. FC03/FC04 offset stays request provenance because responses do not echo it; matching uses active generation and transaction ID plus echoed unit/function/applicable byte count. FMV3-M1-02 tests reuse attempts, exhaustion/rollover, old-generation late frames, and bounded successful non-abandoned correlation without profile semantics. |
| E2-R2-F02 | CLOSED | Added exactly one public docs issue FMV3-M5-09 after M5-04 and before M5-05 to publish PUBLIC_GRAPHQL_M2M_V1 schema projection, external access/security/channel, compatibility/versioning, credential lifecycle, and recovery. M5-05 depends on it with companion metadata, M5-09 retains M5-03 GO ancestry, and the M5-02 then M5-09 docs lane stays serialized in the 40-issue DAG. |
| E2-R2-F03 | CLOSED | After an RTU request is transmitted then abandoned, successors wait through bounded endpoint-declared response latency plus bus-idle resynchronization, every quarantine frame is discarded, and failed quiescence disables/recovers the endpoint. FMV3-M1-00 documents the rule and FMV3-M1-03/04 test timeout/cancel, late same-shape responses, quarantine, failed quiescence, and recovery. |

Concessions:

- Successful non-abandoned TCP correlation remains bounded and the runtime/profile ownership
  split remains unchanged.
- The GraphQL correction adds one docs issue without adding a repository, raw GraphQL,
  subscription semantics, or a second concurrent docs lane.

### R3

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `fbdc798570105c8a8daab2d1ae1208455db40411fde0b98f6a1b7dcb0486302e`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E2-R3-F01 | CLOSED | Defined TCP/RTU transport-write linearization: only proven zero-byte acceptance/sending avoids abandonment; partial, indeterminate, cancellation-race, or ambiguous completion is possibly transmitted, forcing TCP tombstone/close/new generation or RTU quarantine/resync/recovery before a successor; M1-02..04 cover the deterministic cases and M1-00 documents them. |
| E2-R3-F02 | CLOSED | FMV3-M3-01 is the exact public companion for M3-02/M3-03 and FMV3-M7-01 for M7-02/M7-03/M7-04, with structural metadata/ancestry; standard-only and no-admissible paths retain public evidence/disposition without inventing profile facts. |
| E2-R3-F03 | CLOSED | FMV3-M3-03 now uses TDD_RED_IF_OVERLAY_REQUIRED; STANDARD_ONLY requires public evidence and green conformance CI while forbidding an implementation commit or empty overlay. |
| E2-R3-F04 | CLOSED | FMV3-M1-03 follows M1-02; FMV3-M7-01 follows the critical docs lane through M5-09 before M7-02; the single modbusreg lane remains serialized, and topology/preflight own a structural one-active-issue/one-active-PR per-repository mutex. |
| E2-R3-F05 | CLOSED | FMV3-M6-02 records GO/NO_GO/STOP with completion not progress and GO as sole success; GO requires a locked PV capability/value in a matching myVaillant-side observable through GraphQL and eeBUS, while handshake/packet-only and NO_GO/STOP cannot satisfy the objective or distort public/vendor contracts. |
| E2-R3-F06 | CLOSED | Added generic per-epoch/per-round verdict, integration, and exact ordered unique finding_ids for every archived and active accepted round; validation compares them to review rows and requires an empty list for NO_FINDINGS. |

Concessions:

- The 40-issue, nine-milestone ownership split and read-only product boundary remain intact.
- All six corrections are structural contracts or existing-issue refinements; no runtime
  scheduler simulation, profile fact, repository, or public schema was added.

### R4

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `9cebd062800c3b125963c4f0541163122f3a38a5d80ed5f3a282ebe0a345c115`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E2-R4-F01 | CLOSED | Established one exact ordered write-result set everywhere: `provable_zero`, `partial_write`, `indeterminate_error`, `cancellation_race`, `ambiguous_completion`; only `provable_zero` avoids abandonment, all other results force TCP close/reconnect and RTU quarantine/recovery, both recovery matrices include ambiguous completion, and RTU timeout/cancellation is limited to post-full-transmit waiting. |
| E2-R4-F02 | CLOSED | FMV3-M7-01 must publish and merge the complete Growatt candidate/admission contract, qualified facts, criteria, provenance/licensing, unsupported disposition, and exact code/document mapping before closing; M7-03 consumes it, `PROFILE_ADMITTED` alone triggers RED/code, and `NO_ADMISSIBLE_PROFILE` preserves pre-published evidence without code/catalog/support claim or later docs change. |
| E2-R4-F03 | CLOSED | FMV3-M6-02 GO now requires an enabled qualified live Fronius endpoint and the same available non-stale post-run-start observation identity/value traced through PUBLIC_GRAPHQL_M2M_V1 and eeBUS to the accepted myVaillant observable; replay/cache/synthetic/fixture/simulator input cannot GO, existing identity/time/quality fields suffice, and NO_GO/STOP remains honest non-success evidence. |

Concessions:

- The 40-issue, nine-milestone DAG and repository ownership remain sound and unchanged.
- The corrections reuse existing transport, docs, and lab issues without adding a public
  schema field, repository, issue, conditional gate, or runtime simulation to validation.

### R5

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `987d594f721af943fc65f6f47e5f48d8d3b72011b656fd2db79dd13adceb4796`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E2-R5-F01 | CLOSED | Extended the generic review epoch model with terminal `PASSED`: accepted R1-R5, five accepted rounds, R5 `NO_FINDINGS`/`NOT_REQUIRED`/`[]`, target `TERMINAL_NO_FINDINGS`, no active epoch required, and draft/lock authorization unchanged pending separate operator action. |
| E2-R5-F02 | CLOSED | Preserved the exact five abnormal transport-write results and their handling while adding separate `full_transmit_success -> response_wait`; TCP wait timeout/cancellation tombstones and late-drops without same-socket reuse before normal rollover, RTU uses existing quarantine/resync, and M1-04 carries the four exact matrix rows. |
| E2-R5-F03 | CLOSED | Recorded epoch 2 R4 and R5 closure claims, removed the stale 3/5-R4 claim, archived epoch 2 with its exact R5 IDs/snapshot, and opened epoch 3 as the sole `IN_PROGRESS` R1 target with five pending entries. |

Concessions:

- Existing `FAILED` archive and `IN_PROGRESS` behavior, the 40-issue/nine-milestone DAG,
  and every product boundary remain unchanged.
- The five abnormal results remain exact and ordered; normal full transmission is now an
  explicit success transition rather than an ambiguous completion.

## Epoch 3

State: PASSED
Accepted rounds: 5
Current target: TERMINAL_NO_FINDINGS
Archive: TERMINAL

### R1

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `d0e23922b27030b241688dec85d5e79f28de4d6730e6964511e71b6ff10b1c36`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E3-R1-F01 | CLOSED | Semantic lock can pass before the semantic MCP behavior exists: M5-04 now depends on M5-01/M5-02 and produces the golden/live-tested candidate; M5-03 locks that exact version; semantic GO gates M5-09 and later consumers, never M5-04. |
| E3-R1-F02 | CLOSED | Coalescing lacks a reproducible identity model for one wire response serving different logical ranges: each physical request/range now has `wire_response_id`, each dependent observation has linked `logical_view_id` plus exact slice, unequal overlaps replay exact words/provenance, and incompatible unit/table/authorization/generation/deadline cases reject coalescing. |
| E3-R1-F03 | CLOSED | EMMA deferral omits the required fail-closed EMMA discrimination gate: M7-01 inventories gateway/model/software/version discriminators or marks each unavailable; M7-04/M7-05 negative fixtures allow only `no_match`/`insufficient_evidence`, never activate SmartLogger/S-Dongle, and block Huawei auto-eligibility without reliable discrimination. |
| E3-R1-F04 | CLOSED | The RTU hardware-conditional gate has no outcome or evidence contract: `RTU_PHYSICAL_QUALIFICATION_V1` now requires adapter/transceiver, baud/topology, measured physical silent intervals, and timeout/cancellation quarantine evidence; otherwise RTU remains default-disabled experimental fixture-only with no enabled/supported claim and blocks no TCP-sufficient work. |
| E3-R1-F05 | CLOSED | The Matter binding has no selected semantic ingress contract or trust model: M8-01 now depends on packaged M5-08, consumes exactly `PUBLIC_GRAPHQL_M2M_V1` through authenticated bounded polling with version, confidential verified-server, credential lifecycle/recovery, and security rejection of Modbus/modbusreg, internal, subscription, and undocumented ingress. |

Concessions:

- The runtime, profile, canonical-semantic, gateway-adapter, and private-binding ownership
  direction is otherwise coherent and keeps public artifacts independent of private
  repositories.
- The phase-1 read-only boundary explicitly excludes Modbus write functions and requires a
  separate safety plan for future writes.

### R2

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `19f83175eaffc54e6e6ea5bb0f8282d0c6400e9c440ceacc80cbf5b75725f07b`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E3-R2-F01 | CLOSED | Huawei positive profile knowledge lacked a complete public admission contract: M7-01 now requires a provenance/licensing-qualified register, codec, gateway, branch, version, detection, and exact code/doc packet or `NO_ADMISSIBLE_PROFILE` per SmartLogger/S-Dongle candidate; only admitted candidates trigger RED/code and positive fixtures, while non-admission forbids code, catalog entries, and support claims. |

Concession:

- The runtime, profile registry, canonical semantics, gateway adapter, and private binding
  ownership direction remains explicit and acyclic.

### R3

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `3dcfab8e8c094d8be6010caa50015100163741e460ce109c5b32ab6154eccf30`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E3-R3-F01 | CLOSED | Private eeBUS and Matter lanes lacked mandatory public companions: M6-00 and M8-00 now publish sanitized permissive protocol/binding contracts before private code, while M6-03 publishes reusable myVaillant findings or records STOP when publication is impossible; private-only protocol knowledge cannot satisfy the milestone. |
| E3-R3-F02 | CLOSED | The stale `1/5`/R2 active-epoch statement is corrected to the authoritative state, and structural validation rejects contradictory accepted-round/current-target summaries. |

Concession:

- The Huawei lane has public licensed positive admission packets and fail-closed EMMA
  discrimination.

### R4

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `ddc3962b53f4ce8d5d29a737c501cd4eab2e30ccd2e3e4bab12a16113c95a58e`
Reviewer verdict: FINDINGS
Integration: CLOSED

| Finding | Status | Integrated correction |
|---|---|---|
| E3-R4-F01 | CLOSED | Vendor admission could require an unowned Modbus PDU: phase 1 now explicitly includes FC2B/MEI0E Device Identification in `helianthus-modbus`, tests it on TCP/RTU, and requires every M7 detector operation to map to the runtime allowlist; unsupported operations force non-admission and modbusreg cannot frame PDUs. |

Concessions:

- EMMA remains fail-closed when discrimination is unavailable.
- Semantic MCP is tested before lock and private consumers follow packaged public GraphQL.

### R5

State: ACCEPTED
Reviewer route: fresh OpenAI planner adversary, Sol/max
Snapshot: `320f9383d26b640a423ad5902cad90643dc42e18d2c76544f6293d46253866ea`
Reviewer verdict: NO_FINDINGS
Integration: NOT_REQUIRED

Concessions:

- `helianthus-modbus` owns all phase-1 PDU framing and unsupported detector operations fail
  closed before profile admission.
- Semantic MCP is tested before lock, and private bindings follow packaged public GraphQL
  plus sanitized public companion contracts.

Epochs 1 and 2 are immutable `FAILED` archives after their R5 `FINDINGS` integrations
reached `CLOSED`. Epoch 3 R1-R4 `FINDINGS`, including E3-R1-F01 through E3-R4-F01, are
integrated `CLOSED`; R5 returned `NO_FINDINGS` with no integration required. Epoch 3 is the
sole highest/current terminal `PASSED` epoch at `5/5`, targeting `TERMINAL_NO_FINDINGS`.
