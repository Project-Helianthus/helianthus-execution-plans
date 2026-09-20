# Semantic-draft reconciliation for 0.7

This current reconciliation retains the acceptance of [issue #93](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/93)
and the early semantic draft at
[`6b5e74340d52c7ac2e8e8a10ccd808198a4022a8`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/6b5e74340d52c7ac2e8e8a10ccd808198a4022a8/semantic-bridge-ir-w34-26/00-canonical.md).
Its section and clause numbers are historical traceability references, not a claim
that historical SHAs, issue state or tests are current. This document is planning
intent; it creates no repository work, contract or live-system action.

## Current ownership and architecture

0.7 owns the typed semantic model and its product integration: identity, exact
quantities, source bindings, evidence, capability packs, operations, projections
and lifecycle. `helianthus-semreg` and `helianthus-docs-semantic` are existing
public owners of, respectively, protocol-neutral interfaces/types/fixtures and
reusable semantic architecture/API knowledge. The retained `SEMREG-BOOTSTRAP` ID
is historical ownership traceability, not a pending repository creation.

The semantic kernel imports no transport, protocol, vendor, gateway or consumer
package. Public values have explicit types and versioned extensions; unknown values
remain representable without becoming supported capabilities. One physical asset
may have multiple native bindings and perspectives. Opaque identity and qualified
links preserve those distinctions, while quantities retain phenomenon, source,
cache and receipt times. Presentation exposes alternatives and conflicts without
inventing a control policy.

Native owners retain framing, protocol lifecycle, qualification, decoders, FSMs
and raw evidence. The gateway owns generic north/south composition and versioned
extension hooks for Portal, MCP, GraphQL, metrics and other bindings. It dispatches
one exact qualified native route; ambiguity, withdrawn capability, stale generation
and indeterminate outcomes fail closed. ACK, readback and outcome remain distinct.
`helianthus-ebusreg` stays eBUS-native rather than becoming a universal semantic
owner. Portal drivers contribute descriptions and bounded components, while Portal
owns navigation, search, accessibility and visual coherence.

The later descriptive IR/code-generation transformation is exclusively in the
[locked 0.8 guide](../software-declarative-08.locked/00-canonical.md). Accepted 0.7
is its external prerequisite. The 0.8 transformation, Daybreak and hardware work
are not 0.7 deliverables or packages; all applicable non-declarative clauses below
remain 0.7 acceptance.

## Corrections retained from the early draft

| Historical assumption | Current 0.7 disposition |
|---|---|
| A future DriverManager must be created before integration | INT-06 begins with the actual current manager and acquisition seams; reuse is not proof that each family already satisfies the new contract. |
| Universal semantic documentation belongs in docs-ebus | SemReg/docs-semantic own public semantic contracts; protocol documentation keeps native evidence. |
| Only eBUS, eeBUS and Modbus are first-release work | Every already-started native family remains visible, including CAN and vendor profiles; unknown support remains unknown. |
| Historical normative counts prove current completeness | `STD-01` pins the applicable corpus before mappings freeze; every selected source receives a disposition. |
| A big-bang rewrite controls delivery | Repository-local dependency order applies; the exact release BOM, rollback and public-boundary rules remain. |
| Portal or consumers define upstream behavior | Bindings consume promoted contracts and disclose projection loss; they do not own semantic decisions. |

## Retention of all 36 original acceptance clauses

Every clause in draft section 21 has a successor below. A package mapping retains
acceptance; it does not assert a PASS. Package owner and dependency detail are in
[the 0.7 map](91-milestone-map.md). The one declarative clause has its explicit
external successor in the 0.8 guide and is not inserted into the 0.7 package map.

| Draft clause(s) | Retained acceptance or explicit correction | 0.7 successor / external boundary |
|---|---|---|
| 1 | Reconcile current native/runtime baselines and frozen comparator behavior; historical SHAs and physical checks are dated evidence. | INT-00, native packages, INT-17, INT-20 |
| 2 | Exact complete 0.7 BOM is reviewed and physically accepted before release. | INT-16, INT-19, INT-20, INT-21 |
| 3 | Public SemReg and docs-semantic ownership, protocol-free imports, and migration of canonical PV types/catalog/lifecycle/counters/registry. | SEMREG-BOOTSTRAP, INT-04, INT-05 |
| 4 | Explicit public types and versioned extensions; no unrestricted untyped public values. | INT-04, INT-05 |
| 5 | Opaque resource identities with tested public compatibility aliases. | INT-05, INT-08, LEGACY-IDENTITY |
| 6 | Shared driver/provider contract without protocol branches in common lifecycle logic; all started families included. | INT-06, INT-07 |
| 7 | Distinct B524/B509/standard bindings with qualified identity and lineage. | NATIVE-01, INT-05, INT-07 |
| 8 | Typed dispositions for the selected eeBUS corpus; historical counts are not current-source claims. | STD-01, INT-04, INT-05, INT-12 |
| 9 | Catalog completeness never fabricates capabilities or operations. | INT-05, INT-07, INT-12 |
| 10 | eeBUS output discovery/read/subscribe/gated-command conformance. | INT-12, INT-17 |
| 11 | Exact SunSpec model/revision inventory and explicit supported, unsupported and unknown dispositions. | NATIVE-03, INT-04, INT-05 |
| 12 | Native SPINE, frames and register words remain separate from canonical facts with protected provenance. | Native packages, INT-05, INT-07, INT-08 |
| 13 | GraphQL, MCP, Portal and HA parity alongside the semantic contracts. | INT-08, INT-10, INT-15, INT-17 |
| 14 | Typed list/get/start/stop/restart with desired versus observed state, revision and idempotency; HA uses GraphQL. | INT-06, INT-08, INT-10, INT-15 |
| 15 | Replay existing promoted eeBUS leaves against a frozen comparator; counts do not define final capability. | INT-05, INT-07, INT-17 |
| 16-17 | Generation-fenced withdrawal/republication, per-driver failure isolation and API/health independent of driver startup. | INT-06, INT-07, LEGACY-PERSIST, INT-17 |
| 18 | Versioned projection manifests and golden loss reports for every applicable output. | INT-08, INT-12, INT-13, INT-17 |
| 19-20 | Exactly one operation route; distinct ACK/readback; no indeterminate fallback; bounded loop suppression. | INT-06, INT-08, INT-12, INT-13, INT-17 |
| 21-22 | Consumer-independent contracts; no autonomous optimization or unstarted consumer products. | INT-04, INT-06, INT-08 |
| 23 | Extensibility proof with existing CAN families and a fixture driver, without kernel redesign or vendor switches. | NATIVE-05, NATIVE-06, INT-06, INT-07, INT-09, INT-10 |
| 24-25 | Coherent state migration/rollback and no mixed incompatible state; reuse existing lifecycle behavior. | LEGACY-PERSIST, INT-06, INT-14, INT-16, INT-17, INT-20 |
| 26-27 | Disjoint writes, dependency-aware integration and fresh review after relevant predecessor changes. | Owning repository workflow |
| 28 | Endpoint-free Modbus errors, one bounded owner-gated retry, immutable PDU, atomic callers and no healthy-generation teardown. | INT-06, INT-07, INT-17 |
| 29 | Preserve prior complete release and compatible state; test rollback against final candidate. | LEGACY-PERSIST, INT-14, INT-16, INT-17, INT-20 |
| 30 | Descriptive migration and behavior-preserving reduction after accepted 0.7. | External 0.8 DRIVER-EXTRACTION-01 and INT-18; not a 0.7 package |
| 31-32 | Behavioral test names, normative references where applicable, redistributable tests and preserved/improved coverage. | Every affected 0.7 repository, INT-17 |
| 33-34 | Applicable CI and fresh exact-HEAD review; Daybreak and physical validation remain release gates. | Owning repositories, INT-17, INT-19, INT-20, INT-21 |
| 35 | PV envelope accounting for mixed-origin partial updates and malformed identity rejection. | INT-05, INT-08, INT-17 |
| 36 | Pairing/SHIP/SPINE and trusted/offline UI parity; physical topology is tested on the final candidate. | INT-03, INT-10, INT-15, INT-17, INT-20 |

## Candidate invalidation and remaining boundary

For 0.7, a code, configuration, dependency or package fix during Daybreak or
hardware validation invalidates earlier evidence. The changed final BOM requires a
fresh Daybreak review plus affected hardware and conformance revalidation before
INT-21 publishes it. A missing device remains a blocker and fixtures cannot stand
in for a claimed physical result.

INT-04 still owes the concrete versioned schema/package contract, capability-pack
catalog, source/version dispositions, compatibility migration and cross-protocol
identity rules. INT-06 and INT-09 finalize the generic runtime SPI and Portal
contract. Deterministic serialization, provenance-cycle rejection, false-identity
and ambiguous-route rejection, partial failure, revision consistency, restart,
withdrawal, timeout and degraded-driver fixtures remain repository-owned proof.
Transport and normative conformance remain the owning repository's declared gate;
private or restricted vectors are not published.
