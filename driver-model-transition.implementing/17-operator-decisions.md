# Operator decisions

Canonical-SHA256: `ca9edfc928fe862162c6d349c4f226580aa05145d04ae53c81a0aa557c464a85`
Depends on: [15-northbound-and-amendments.md](./15-northbound-and-amendments.md), [16-tests-and-acceptance.md](./16-tests-and-acceptance.md).
Scope: Explicit pending choices and hard stops.
Idempotence contract: Re-reading creates no work; fixed fixtures preserve outputs, and lifecycle retries reuse receipts and exact uncertain bytes.
Falsifiability gate: Compare pre-move characterization, ownership, parity and applicable transport evidence; unmet decisions stop the affected node.
Coverage: Canonical section 7; O1–O12.

## 7. Decisions needed from the operator

The architectural direction above is binding. These are implementation/release choices it leaves open; recommendations below are proposals, not accepted answers.

| ID | Choice and recommendation | Blocks |
|---|---|---|
| O1 | Board accepts 0.7 seams/managed adapters/#1021, 0.8 full moves, pre-1.0 ownership completion; reconciles G5/G6 item ordering without INT-04/INT-05/STD-01 ancestry, separately from INT-06/07 epic closure and existing 0.8 DRIVER-EXTRACTION-01/INT-18. Retain original integration/physical acceptance. | Dispatch under amended packages; no automatic existing-guide supersession |
| O2 / G5 D1 | New epoch on RESTART/START-after-STOP versus contract-style same-epoch generation replacement. Draft requests NEW epoch; recommend honoring it only with an explicit hub/contract amendment and successor/recovery vectors. Specify stable SourceID, generation mapping, single reservation and retire-before-start. G4 AdmitSource/Activate cannot already do this. | G5 bridge; split a prerequisite if amendment exceeds Cx 8 |
| O3 / G5 D2 | Approve fresh missing-namespace RUNNING bootstrap and disabled-config precedence; recommend shell available/eBUS withheld on corrupt, unreadable or unsupported control state. Preserve add-on migration-required behavior and stored STOPPED. | G5 durable bootstrap/recovery |
| O4 / G5 D3 | Choose namespace version, durable transaction/restore format, numeric ledger capacity/retention/rollback window, compaction, digest encoding, initial counters and observed-only catalog revision behavior. Recommend bounded refusal over eviction of reachable receipts; no numeric default invented here. | G5 persistence/control |
| O5 / G5 D4 | Approve experimental runtime tool names/envelope and exact trusted principal/authority/deadline adapter, read/control caller policy. Lifecycle authority must not imply pairing/device-write authority. | G5 operator MCP exposure |
| O6 / G5 D5 | Approve lifecycle-only eBUS registration with no fabricated binding, synthetic nonempty recovery proof and finite semantic retry/cleanup budgets; decide full durable hub restore prerequisite/scope. Shared-asset/LIFE-22 stays separately blocked. | G5 proof boundary and managed adapters |
| O7 / G5 D6 | Accept revised G5 manifest/Cx, exact merged G4 contract, public docs deliverable and gate applicability. Keep config.go/gateway.go/startup_scan untouched in proposed first slice; if needed, rescope with actual physical/smoke obligations. | G5 dispatch, never a standing live authorization |
| O8 | Confirm compiled driver packages in gateway repository initially, registration descriptor version and hook schema ownership. Recommend no repository split/dynamic loader now; named native libraries stay owners. | DM-HOOKS and 0.8 extraction manifests |
| O9 | Confirm CAN→Modbus→eeBUS→eBUS order after current transport/evidence reconciliation; assign CAN transport/binding owner and disposition unsupplied runtime. | CAN move and any priority change |
| O10 | 0.8 northbound framework only or framework plus virtual Modbus smart meter. Recommend concrete read-only TCP case if profile evidence exists; select exact dialect/model, source/freshness/unavailable policy and peer hardware. Cost is in section 4; optional issue chain stays nonmandatory until selected. | Concrete northbound chain and claimed support |
| O11 | Explicit owner for cross-driver selection/aggregation/translation policy, loss/freshness and operation route. Recommend typed separate binding policy with native encoders in drivers; no generic kernel battery policy. | EV station/battery translation/aggregation examples, all outside this guide's selected concrete scope |
| O12 | Is real Pi UART/eBUS frontend/backend available for northbound qualification? Default is outside 1.0; if available, create separately approved implementation/timing/hardware work and amend release scope only after qualification. | eBUS northbound; never southbound extraction completion |

No guide merge creates/mutates repositories, issues, branches, commits, PRs, deployments or runtime state. Planning hashes check document consistency only; they are not authorization/review/release proofs. Implementation evidence stays in owning producer/consumer code repos. Native reusable knowledge belongs in family docs; generic runtime/API knowledge uses docs-ebus until an explicit docs-owner amendment. SemReg/docs-semantic retain canonical semantics.

This is issue #126 Phase B planning, not a resume of 0.7/0.8 execution. Normal implementation later reads accepted merged main and reconciles the next DAG node in its own repository. The current task ends with local validation and an uncommitted new guide. Pending decisions, unavailable profile evidence, uncertain close/recovery, missing physical rows and unreviewed public contract changes remain hard stops, never PASS labels.
