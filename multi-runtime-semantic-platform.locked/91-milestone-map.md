# Milestone Map

Status: `Locked`
Baseline: `Gateway 0.4.0`
Current milestone: `RECOVERY_RECONCILIATION`
Amendment: `AD-DOCS-01 external-only-documentation`

| Milestone | Primary repo(s) | Depends on | Gate |
| --- | --- | --- | --- |
| RECOVERY_RECONCILIATION | helianthus-execution-plans, helianthus-docs-eebus, helianthus-docs-ebus, helianthus-eebusreg | completed local MSP-R00 | Initial ready rows are exactly MSP-R00-L and DOCS-VERIFY. MSP-R00 is local completed/no-code-acceptance. The serialized docs chain is API-SCHEMA -> PLATFORM -> E2 -> CLEAN. Dirty rescue code has no runtime successor-unlock authority. |
| M3 - eeBUS Runtime Feasibility | helianthus-eebusreg | MSP-DOCS-CLEAN, MSP-03C, MSP-03D-G01 | MSP-03D-R passes revised G17 and G19 with owner acceptance. M3 remains open until then. |
| M3.5 - Raw Runtime Contract Freeze | helianthus-eebusreg | M3 | Raw identity, snapshot envelope, and evidence object replay deterministically; no trust/lifecycle/availability authority is frozen. |
| M4 - Store, Raw View, Lifecycle Facade, And Trust Security | helianthus-eebusreg, helianthus-docs-eebus | M3.5 | MSP-04A internal store/schema, MSP-036 immutable raw view, exact-head MSP-DOCS-API-CANDIDATE before MSP-055 source merge, MSP-DOCS-API-FREEZE active API docs, then first-trust/OOB/admin and repair flows. |
| M4.5 - Trust And Admin State Freeze | helianthus-eebusreg | M4 | Trust, pairing, admin-local, restore, and quarantine semantics are frozen for gateway/MCP consumption. |
| M5 - Gateway Sidecar Integration | helianthus-ebusgateway | M4.5 | Gateway import only after canonical docs and eebusreg contracts merge; disabled default opens no sockets and causes no eBUS drift. |
| M6 - Read-Only eeBUS MCP v1 | helianthus-ebusgateway | M5 | Read-only `eebus.v1.*` tools pass deterministic snapshot/hash/auth/error/anti-leak tests. |
| M6.5 - Synchronized Evidence Recorder | helianthus-ebusgateway | M6 | Recorder captures synchronized eeBUS/eBUS/myVaillant bundles using existing read-only eBUS surfaces only. |
| M7 - Draft Candidate Fact Graph | helianthus-ebusgateway | M6.5 | Candidate facts exist with raw evidence and no promotion or consumer exposure. |
| M8 - Multi-Runtime Coexistence | helianthus-ebusgateway | M7 | EEBUS-G18 proves eBUS and eeBUS coexist with separate raw surfaces and no existing consumer drift. |
| M8.5 - Leaf Promotion Lock | helianthus-ebusgateway | M8 | Per-leaf dossiers are locked after coexistence evidence. |
| M9 - GraphQL, Portal, And HA Consumers | helianthus-ebusgateway, helianthus-ha-integration, helianthus-ha-addon | M8.5 | Consumers expose only promoted leaves and preserve existing eBUS/HA identity. |

## Parallelism

Only MSP-R00-L and DOCS-VERIFY are initially ready. MSP-R00 is already
completed locally for issue #14 with architecture review PASS, no code
acceptance, and no runtime successor unlock. MSP-R00-L publishes only opaque
public ledger IDs/classes/dispositions/redaction metadata.

After DOCS-VERIFY, documentation is serialized:
MSP-DOCS-API-SCHEMA -> MSP-DOCS-PLATFORM -> MSP-DOCS-E2 ->
MSP-DOCS-CLEAN. `MSP-DOCS-CANDIDATE-CLEANUP` is dormant and activates only
when a candidate expires or a source PR closes unmerged; it is not initially
ready and is not a normal predecessor.

After MSP-DOCS-CLEAN, eebusreg rows are serialized one PR at a time:
MSP-03D-R, MSP-035, MSP-04A, MSP-036, MSP-055, MSP-04B, MSP-04C, MSP-045.
After MSP-036, the single MSP-055 source PR is prepared but remains unmerged;
MSP-DOCS-API-CANDIDATE merges the exact-head candidate first. MSP-055 then
passes its exact-match merge gate, and MSP-DOCS-API-FREEZE runs before MSP-04B. Gateway, MCP,
evidence, candidate, coexistence, promotion, and consumer work remain
downstream.

## Review Checkpoints

- Architecture review after every milestone.
- Dual review and doc gate per PR/issue.
- Code-structure review after M3.5/M4.
- Code-structure review after M5/M6.
- Extra final code-structure review after M9 or any early stop decision.
