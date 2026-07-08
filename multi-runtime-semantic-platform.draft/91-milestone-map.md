# Milestone Map

Status: `Draft`
Baseline: `Gateway 0.4.0`

| Milestone | Primary repo(s) | Depends on | Gate |
| --- | --- | --- | --- |
| M0 - Control Plane And Issue Matrix | helianthus-execution-plans | none | Issue matrix, model lanes, repo serialization, rollback/review ledgers, and `eebus-transport-gate v0` exist. |
| M1 - Documentation Grounding | helianthus-docs-ebus, helianthus-docs-eebus | M0 | Platform ownership ADR, eeBUS docs bootstrap, and provenance policy are merged in order. |
| M2 - Raw Identity, Snapshot, Evidence, And Correlation Drafts | helianthus-eebusreg, helianthus-docs-ebus | M0, M1 | `helianthus-eebusreg` exists as a raw runtime/evidence module; raw identity, snapshot, evidence, and raw-correlation drafts are reviewable and mark unknowns explicitly. |
| M3 - eeBUS Runtime Feasibility | helianthus-eebusreg, helianthus-ha-addon | M2 | `eebus-go v0.7.0` facade, toolchain/container proof, HA runtime network proof, fake peer, and live VR940f smoke pass with disposable credentials. |
| M3.5 - Raw Runtime Contract Freeze | helianthus-eebusreg | M3 | Raw identity, snapshot envelope, and evidence object replay deterministically. |
| M4 - Production Trust, First-Trust, And Security | helianthus-eebusreg | M3.5 | Production store, first-trust, admin-local, restore/clone, quarantine, and redaction tests pass. |
| M4.5 - Trust And Admin State Freeze | helianthus-eebusreg | M4 | Trust, pairing, admin-local, restore, and quarantine semantics are frozen for gateway/MCP consumption. |
| M5 - Gateway Sidecar Integration | helianthus-ebusgateway | M4.5 | eeBUS config and disabled-by-default sidecar integrate without eBUS behavior drift. |
| M6 - Read-Only eeBUS MCP v1 | helianthus-ebusgateway | M5 | Read-only `eebus.v1.*` tools pass deterministic snapshot/hash/auth/error/anti-leak tests. |
| M6.5 - Synchronized Evidence Recorder | helianthus-ebusgateway | M6 | Recorder captures synchronized eeBUS/eBUS/myVaillant bundles using existing read-only eBUS surfaces only. |
| M7 - Draft Candidate Fact Graph | helianthus-ebusgateway | M6.5 | Candidate facts exist with raw evidence and no promotion or consumer exposure. |
| M8 - Multi-Runtime Coexistence | helianthus-ebusgateway | M7 | eBUS and eeBUS coexist with separate raw surfaces and no existing consumer drift. |
| M8.5 - Leaf Promotion Lock | helianthus-ebusgateway | M8 | Per-leaf dossiers are locked after coexistence evidence. |
| M9 - GraphQL, Portal, And HA Consumers | helianthus-ebusgateway, helianthus-ha-integration, helianthus-ha-addon | M8.5 | Consumers expose only promoted leaves and preserve existing eBUS/HA identity. |

## Parallelism

M1 work is serialized by repository: ownership ADR first, docs-eebus bootstrap
second, provenance third. M3 feasibility issues may overlap only when they are
in different repos and the one-active-PR-per-repo rule is still satisfied. M9
is ordered `GraphQL -> Portal -> HA`; HA work may not start before GraphQL
promotion contracts merge.

## Review Checkpoints

- Architecture review after every milestone.
- Dual review and doc gate per PR/issue.
- Code-structure review after M3.5/M4.
- Code-structure review after M5/M6.
- Final code-structure review after M9 or after any early stop decision.
