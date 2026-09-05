# Semantic draft reconciliation for software 0.7 and 0.8

Planning decision, 5 September 2026. This document reconciles [issue #93](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/93)
and [draft PR #94](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/94)
with the [current software program](00-canonical.md). The source draft is fixed at
[`6b5e74340d52c7ac2e8e8a10ccd808198a4022a8`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/6b5e74340d52c7ac2e8e8a10ccd808198a4022a8/semantic-bridge-ir-w34-26/00-canonical.md).
Its section and criterion numbers below are historical references, not new test IDs.

This is planning intent. It does not implement a contract, certify a product,
change live systems, or cause work in another repository when merged. Issue #93
retains the unfinished INT-04 design; reconciling its draft does not complete that
design or satisfy STD-01. Repository implementation evidence stays with its owner.

## Release and ownership decisions

**0.7 owns the typed semantic model and its working product integration.** Identity,
exact quantities, time, source bindings, evidence, capability packs, operations,
projections and lifecycle contracts are necessary now. Calling that interchange
model HSIR does not require a descriptive language or generation framework.

**0.8 owns the descriptive migration and measured code reduction after 0.7
acceptance.** Inventories, language/IR design, generation and migration comparators
belong to INT-18. Runtime I/O, concurrency, protocol state machines and safety
behavior remain explicitly owned code unless that later design proves otherwise.
The old draft's post-0.7 cleanup is retained in this program; it is no longer an
unspecified 0.7.x wave with 0.8 outside scope. Necessary architectural refactoring
and behavioral test names still belong in the 0.7 changes that need them.

The public semantic contract destination is **Project-Helianthus/helianthus-semreg**.
It owns the protocol-neutral kernel, versioned capability packs and their public
architecture/API documentation. SEMREG-BOOTSTRAP establishes the actual repository,
license, self-contained instructions and independent build before implementation.
This ownership choice does not assert that bootstrap or the complete INT-04
design is finished. The eBUS-specific registry and its PV contracts are migration
donors and compatibility comparators, not the universal semantic owner.

The gateway owns runtime composition and its driver/provider SPI. Native transport
and registry owners retain framing, protocol lifecycle, qualification, decoding
and native evidence. Durable contracts and fixtures live with their producer and
consumer repositories. Cross-protocol documentation must not be routed into the
eBUS documentation repository merely because the old draft did so.

## Retained architecture direction

The kernel is a typed superset of qualified domain facts, with no import of a
transport, protocol, vendor, gateway or consumer package. A small kernel and
versioned capability packs cover thermal/HVAC, PV/inverter, storage/BMS, EVSE and
infrastructure. Public values have explicit types; unrestricted `any` is not a
substitute for an extension contract. Unknown enums/extensions remain representable
without becoming supported capabilities.

One physical asset may have several native bindings and perspectives. Opaque
resource identity, compatibility aliases and evidence-qualified links keep those
bindings distinct. B524, B509 and standard eBUS observations may coexist; similar
values or addresses do not prove shared identity. Relations and purpose-specific
views are derived from one graph, with exact quantities and separate phenomenon,
source, cache and receipt times. Missing source time stays absent. Presentation
selection exposes alternatives and conflicts and never invents a control policy.

Upward flow is native observation → qualification → facts/capabilities → target
projection. Raw frames, register words and protocol objects remain available under
the native owner's access contract. Canonical facts retain source and transformation
lineage without publishing private endpoint data. Projections have a target version,
explicit loss/withholding dispositions and revision-consistent snapshots.

Downward flow is intent → capability, authority, preconditions and deadline checks
→ one exact native binding and generation → native operation → acknowledgement,
readback and outcome. Ambiguous routes, withdrawn capabilities and stale generations
fail closed. An indeterminate result cannot retry on another route. Loop/echo
suppression is bounded and tested. Observation does not authorize a command.

Desired driver state is persistent and separate from observed state. Start, stop
and restart require expected-revision/idempotency behavior and generation-fenced
withdrawal/republication. Driver startup failure must not prevent gateway API/health
availability or terminate unrelated drivers. INT-06 reconciles and extends existing
ownership instead of introducing a second manager or retry loop.

Portal drivers contribute versioned values, groups, relationships, diagnostics,
actions and bounded components where needed. Portal owns navigation, search,
accessibility and visual coherence. A fixture driver must demonstrate extension
without a central vendor switch. GraphQL, native and semantic MCP, HA through
GraphQL, Prometheus, eeBUS output and Matter output consume the promoted contracts;
none becomes the upstream semantic owner.

## Corrections to the old draft

| Old assumption | Current disposition |
|---|---|
| Only eBUS, eeBUS and Modbus form the first release; CAN is a later fixture | 0.7 includes every already-started native family in the current work map, including Gree/Growatt CAN, vendor Modbus/BMS and Tesla profiles. Evidence-blocked candidates remain visible without fabricated support. |
| All current Modbus/eeBUS completion and historical live checks must finish before any semantic work | Conceptual design and independent native fixes can proceed. A mapping freezes only when its exact normative/evidence dependencies are verified. Integration consumes merged provider contracts; physical acceptance remains a release gate. |
| DriverManager exists only in a future runtime and must be newly implemented | INT-06 begins from the actual current manager and owned acquisition seams. Existing eBUS lifecycle behavior is a reuse baseline, not proof that every family already implements the new SPI. |
| Matter starts from the 1.6.1 data-model snapshot | The source is draft 1.7 ballot 0.9 at `29b4768a513cf566011ab8cd60df1bc495204953`, as recorded in the canonical guide. Draft support is not final-standard conformance. |
| SPINE 1.3 counts 32/143/48/36 establish current completeness | Those numbers identify the old draft's inventory. STD-01 verifies exact current component/use-case sources and deltas. Every element in the selected corpus needs a disposition; device materialization remains limited to advertised/observed evidence. |
| Universal semantic documentation belongs in docs-ebus | Semreg owns its public semantic contract; each protocol docs repository owns its native evidence and protocol contract. |
| One big-bang rewrite dictates all development sequencing | Repository-local delivery follows the current dependency map. Production replacement and rollback still use a coherent, exact release BOM and separately authorized operations; mixed incompatible semantic state is not a fallback. |
| Rename is excluded from the architecture program | INT-14 explicitly owns the coordinated gateway rename after its stated dependencies, including consumer, module, image, documentation and pin migration. |
| Old parallel-lane notices and historical ownership reservations remain mandatory | Current issue/PR write sets and dependency order govern delivery. Disjoint worktrees, fresh bases and exact-HEAD review preserve the useful coordination invariant. Historical comments do not reserve current work. |
| Additional protocol/consumer concepts are implicit release work | Keep extensible boundaries. Do not add unstarted protocols or future consumer products to 0.7, and do not republish private product strategy. |

The existing PV and UI tuples in draft sections 19.4–19.5 remain dated comparator
references. Reconcile the actual baseline in owning issues before migration;
never relabel a historical SHA as current HEAD. Preserve PV envelope accounting,
strict asset/profile identity grammar, stable public identities and the separation
of Pairing, SHIP and SPINE, including trusted/offline behavior. Disconnected
hardware supplies neither a software PASS nor an automatic software defect.

INT-06 reconciles the current gateway's lifecycle and acquisition ownership in
the gateway repository's normal workflow. It records the exact implementation
baseline, existing internal operations, missing public surfaces and additional
families there. Its acceptance preserves generation fencing, admission,
withdrawal, bounded retry and quarantine. This guide records that dependency
and acceptance intent; it does not validate or store implementation proof.

## Retention of all 36 original acceptance clauses

Every clause in draft section 21 has a disposition below. A mapping to a package
retains work; it does not assert that the clause has passed. Current package IDs
and owners are defined in [the milestone map](91-milestone-map.md).

| Draft clause(s) | Retained acceptance or explicit correction | Owning package(s) |
|---|---|---|
| 1 | Reconcile current native/runtime baselines and frozen comparator behavior. Historical SHAs and physical checks are dated evidence, not a universal precondition for independent work. | INT-00, native packages, INT-17, INT-20 |
| 2 | Exact complete 0.7 BOM, reviewed and physically accepted before release. | INT-16, INT-19, INT-20, INT-21 |
| 3 | Public semreg ownership, protocol-free imports and migration of canonical PV types/catalog/lifecycle/counters/registry. | SEMREG-BOOTSTRAP, INT-04, INT-05 |
| 4 | Explicit public types and versioned extensions; no unrestricted untyped public values. | INT-04, INT-05 |
| 5 | Opaque resource identities with tested public compatibility aliases. | INT-05, INT-08, LEGACY-IDENTITY |
| 6 | Shared driver/provider contract without protocol branches in common lifecycle logic; include all started native families. | INT-06, INT-07 |
| 7 | Distinct B524/B509/standard bindings with qualified identity and lineage. | NATIVE-01, INT-05, INT-07 |
| 8 | Complete typed dispositions for the exact selected eeBUS corpus; historical counts are not a current source claim. | STD-01, INT-04, INT-05, INT-12 |
| 9 | Catalog completeness never fabricates device capabilities or operations. | INT-05, INT-07, INT-12 |
| 10 | Real eeBUS output feature/use-case discovery, read, subscribe and gated-command conformance. | INT-12, INT-17 |
| 11 | Exact SunSpec model/revision catalog inventory and explicit profile dispositions, with unsupported and unknown kept distinct. | NATIVE-03, INT-04, INT-05 |
| 12 | Native SPINE, frames and register words remain separate from canonical facts with protected provenance. | Native packages, INT-05, INT-07, INT-08 |
| 13 | Existing GraphQL/MCP/Portal/HA parity alongside the new contracts. | INT-08, INT-10, INT-15, INT-17 |
| 14 | Typed list/get/start/stop/restart surfaces with persistent desired state, separate observation, expected revision and idempotency; HA uses GraphQL. | INT-06, INT-08, INT-10, INT-15 |
| 15 | Replay the existing promoted eeBUS leaves against the frozen comparator; a historical count is not the final capability target. | INT-05, INT-07, INT-17 |
| 16–17 | Generation-fenced capability withdrawal/republication, per-driver failure isolation, API/health independent of driver startup. | INT-06, INT-07, LEGACY-PERSIST, INT-17 |
| 18 | Versioned projection manifests and golden loss reports for each applicable output. | INT-08, INT-12, INT-13, INT-17 |
| 19–20 | Exactly-one operation route; ACK/readback distinction; no fallback after indeterminate outcomes; bounded multi-output loop suppression. | INT-06, INT-08, INT-12, INT-13, INT-17 |
| 21–22 | Consumer-independent contracts and explicit exclusion of autonomous optimization and future consumer products. No new business-product reference implementation is required by this reconciliation. | INT-04, INT-06, INT-08 |
| 23 | Extensibility is proved using existing CAN families and a fixture driver, without redesigning the kernel or adding vendor switches. | NATIVE-05, NATIVE-06, INT-06, INT-07, INT-09, INT-10 |
| 24–25 | Coherent release and state migration, whole-release rollback and no mixed incompatible state. Supersede the false future-only DriverManager premise; reuse existing lifecycle behavior. | LEGACY-PERSIST, INT-06, INT-14, INT-16, INT-17, INT-20 |
| 26–27 | Disjoint writes, dependency-aware integration and fresh review after relevant predecessor changes. Historical mandatory lane notices are superseded by current repository workflow. | All affected owning issues under workspace policy |
| 28 | Endpoint-free Modbus provider errors; at most one owner-gated reconnect/retry within one total context/quota, immutable original PDU, atomic concurrent callers and no healthy-generation teardown. Reuse the existing native seam. | INT-06, INT-07, INT-17 |
| 29 | Preserve the prior complete release and untouched compatible state; test rollback against the exact final candidate. | LEGACY-PERSIST, INT-14, INT-16, INT-17, INT-20 |
| 30 | Inventory oversized/mixed responsibilities and redundant transformations; perform the planned descriptive migration and behavior-preserving cleanup after accepted 0.7. | INT-18 |
| 31–32 | Descriptive behavioral test names, exact normative case references where applicable, redistributable tests, and preserved/improved coverage. Historical IDs remain traceability metadata. | Every affected repository; INT-17, INT-18 |
| 33–34 | Applicable CI and fresh exact-HEAD review; internal readiness is distinct from external certification. Daybreak and physical acceptance are additional release gates. | All owning repositories, INT-17, INT-19, INT-20, INT-21 |
| 35 | Complete canonical PV envelope accounting including mixed-origin partial updates, and exact asset/profile identity grammar with malformed-input rejection. | INT-05, INT-08, INT-17 |
| 36 | Pairing/SHIP/SPINE and trusted/offline UI parity. Physical topology is tested on the final candidate and does not pass from offline fixtures. | INT-03, INT-10, INT-15, INT-17, INT-20 |

## Old issue families and their successors

| Draft section 19 ID | Current successor |
|---|---|
| DOC-IR-01 | INT-04 and semreg-owned public architecture contract after SEMREG-BOOTSTRAP |
| ORG-IR-01 | SEMREG-BOOTSTRAP |
| SEM-IR-01 | INT-04 design and INT-05 typed kernel |
| SEM-IR-02 | INT-05 provenance, perspectives, selection and conflict |
| SEM-IR-03 | INT-05 capability/operation types; INT-06/08 routing; INT-12/13 projections |
| SEM-IR-PV-01 | INT-05 PV migration and INT-08/17 compatibility accounting |
| GW-IR-01 | INT-06 adaptation of current lifecycle ownership and INT-07 composition |
| EBUS-IR-01 | Native eBUS owner plus INT-05/06/07; no universal semantic ownership in ebusreg |
| GW-IR-02 | INT-07 eBUS integration and INT-17 comparator |
| EEBUS-IR-01 | STD-01, native eeBUS owner, INT-05/07/12 |
| MODBUS-IR-01 | NATIVE-03/04/07 provider results, INT-05 mappings and INT-07 composition |
| GW-IR-03 | INT-07 across every already-started native family |
| GW-IR-04 | INT-08 and INT-09/10 Portal design/implementation |
| NB-IR-REQ | INT-08/11/12/13; explicit target contracts and loss dispositions |
| HA-IR-01 | INT-03 and INT-15 |
| CUT-IR-01 | INT-14/16/17/19/20/21, with action-time confirmation for live replacement |
| DOC-IR-02 | Public semantic, protocol and operator contracts in their actual owning repositories |
| CLEAN-IR-* | INT-18 after 0.7 acceptance, with final 0.8 Daybreak/hardware gates |

## Remaining design and validation boundary

INT-04 still owes the concrete versioned schema/package contract, every 0.7
capability-pack catalog, source/version dispositions, compatibility migration
and cross-protocol identity rules. STD-01 must provide verified normative sources
before affected mappings freeze. Unknown source revisions cannot pass by omission.
INT-06 and INT-09 then finalize the runtime SPI/north-south and Portal contracts.

Product validation retains deterministic serialization, exact quantity/time
properties, unknown preservation, provenance cycle rejection, false-identity and
ambiguous-route rejection, partial failure, revision consistency, restart/withdrawal,
stop timeout and degraded-driver fixtures. Native-to-same-native round trips are
claimed only for explicitly exact mappings; projection loss stays visible elsewhere.
Transport and normative conformance apply through each owning repository's declared
contract, not a universal eBUS matrix. Private or restricted test vectors are not
published. Physical and sensitive operations require their concrete approval.

This document's own validation is the repository's local read-only plan check.
It adds no checker, executable state or downstream action. Draft supersession
belongs to the owner's separate issue/PR workflow, outside this guide. Issue #93
and the current work packages retain the unimplemented design and delivery acceptance.
