# Milestone Map

Status: `Locked`
Baseline: `Gateway 0.4.0`
Current milestone: `M5_PRODUCTION_PREREQUISITES`
Amendment: `MSP-05B production-prerequisite correction`

| Milestone | Primary repo(s) | Depends on | Gate |
| --- | --- | --- | --- |
| RECOVERY_RECONCILIATION | helianthus-execution-plans, helianthus-docs-eebus, helianthus-docs-ebus, helianthus-eebusreg | completed local MSP-R00 | Initial ready rows are exactly MSP-R00-L and DOCS-VERIFY. The complete active serial sequence is represented only by the matrix completion tokens. Dirty rescue code has no runtime successor-unlock authority. |
| M3 - eeBUS Runtime Feasibility | helianthus-eebusreg | matrix-defined completion tokens | MSP-03D-R requires MSP-DOCS-CLEAN and MSP-03C completion tokens; MSP-03D-G01 is evidence-only. M3 remains open until G17 and G19 receive owner acceptance. |
| M3.5 - Raw Runtime Contract Freeze | helianthus-eebusreg | M3 | Raw identity, snapshot envelope, and evidence object replay deterministically; no trust/lifecycle/availability authority is frozen. |
| M4 - Store, Raw View, Lifecycle Facade, And Trust Security | helianthus-eebusreg, helianthus-docs-eebus | M3.5 | MSP-04A internal store/schema, MSP-036 immutable raw view, exact-head MSP-DOCS-API-CANDIDATE before MSP-055 source merge, MSP-DOCS-API-FREEZE active API docs, then first-trust/OOB/admin and repair flows. |
| M4.5 - Trust And Admin State Freeze | helianthus-eebusreg | M4 | Trust, pairing, admin-local, restore, and quarantine semantics are frozen for gateway/MCP consumption. |
| M5 - Production Prerequisites And Gateway Sidecar Integration | helianthus-docs-eebus, helianthus-ship-go, helianthus-eebus-go, helianthus-eebusreg, helianthus-ebusgateway | M4.5 and M5A | Freeze activation contract, implement exact-address SHIP plus independent mDNS policy, thread it through eebus-go, install protected identity and real runtime construction, map gateway config losslessly, then add the disabled-by-default sidecar. |
| M6 - Read-Only eeBUS MCP v1 | helianthus-ebusgateway | M5 | Read-only `eebus.v1.*` tools pass deterministic snapshot/hash/auth/error/anti-leak tests. |
| M6.5 - Synchronized Evidence Recorder | helianthus-ebusgateway | M6 | Recorder captures synchronized eeBUS/eBUS/myVaillant bundles using existing read-only eBUS surfaces only. |
| M7 - Draft Candidate Fact Graph | helianthus-ebusgateway | M6.5 | Candidate facts exist with raw evidence and no promotion or consumer exposure. |
| M8 - Multi-Runtime Coexistence | helianthus-ebusgateway | M7 | EEBUS-G18 proves eBUS and eeBUS coexist with separate raw surfaces and no existing consumer drift. |
| M8.5 - Leaf Promotion Lock | helianthus-ebusgateway | M8 | Per-leaf dossiers are locked after coexistence evidence. |
| M9 - GraphQL, Portal, And HA Consumers | helianthus-ebusgateway, helianthus-ha-integration, helianthus-ha-addon | M8.5 | Consumers expose only promoted leaves and preserve existing eBUS/HA identity. |

## Parallelism

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

AD-DOCS-02 inserts serial PLATFORM, PUBLISH, and issue-backed AGGREGATE gates.
Historical readiness snapshot,
logical-ready, dispatchable, and selected-batch remain separate; a selected
batch cannot create a completion token.

The historical initial ready rows were MSP-R00-L and DOCS-VERIFY. MSP-R00 is
completed locally for issue #14 with architecture review PASS, no code
acceptance, and no runtime successor unlock. MSP-R00-L publishes only opaque
public ledger IDs/classes/dispositions/redaction metadata.

After DOCS-VERIFY, documentation is serialized:
MSP-DOCS-API-SCHEMA -> MSP-DOCS-PLATFORM -> MSP-DOCS-E2 ->
MSP-DOCS-E2R-PLATFORM -> MSP-DOCS-E2R-PUBLISH ->
MSP-DOCS-E2R-AGGREGATE -> MSP-DOCS-CLEAN.
`MSP-DOCS-CANDIDATE-CLEANUP` is dormant and activates only
when a candidate expires or a source PR closes unmerged; it is not initially
ready and is not a normal predecessor. Once active, it also blocks the bound
cross-repo source merge until a fresh candidate cycle completes.

After MSP-DOCS-CLEAN, eebusreg rows are serialized one PR at a time:
MSP-03D-R, MSP-035, MSP-04A, MSP-036, MSP-055, MSP-04B, MSP-04C, MSP-045.
After MSP-036, the single MSP-055 source PR is prepared but remains unmerged;
MSP-DOCS-API-CANDIDATE merges the exact-head candidate first. MSP-055 then
passes exact-match, candidate-state, expiry, and no-active-cleanup gates, and
MSP-DOCS-API-FREEZE runs before MSP-04B. M4.5 and M5A are now complete.

The sole current ready row is MSP-05P-REG-API-V1-CLEANUP. The completed M5
production prerequisites are followed by the pre-release API v1 correction,
gateway remapping, and MSP-05B.
MCP, evidence, candidate, coexistence, promotion, and consumer work remain
downstream.

## Review Checkpoints

- Architecture review after every milestone.
- Dual review and doc gate per PR/issue.
- Code-structure review after M3.5/M4.
- Code-structure review after M5/M6.
- Extra final code-structure review after M9 or any early stop decision.
