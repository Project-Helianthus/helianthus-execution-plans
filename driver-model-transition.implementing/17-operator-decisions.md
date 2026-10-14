# Operator decisions

Canonical-SHA256: `6ab51b73652cbcd4413b4dfeb4c6afe802e95bb4ba19e3a44b42e43fd7f0cac3`
Depends on: [15-northbound-and-amendments.md](./15-northbound-and-amendments.md), [16-tests-and-acceptance.md](./16-tests-and-acceptance.md).
Scope: Pending choices and hard stops.
Idempotence contract: Re-reading creates no work; fixed fixtures preserve outputs, and lifecycle retries reuse receipts and exact uncertain bytes.
Falsifiability gate: Compare pre-move characterization, ownership, parity and applicable transport evidence; unmet decisions stop the affected node.
Coverage: Canonical section 7; O1–O12.

## 7. Decisions needed from the operator

Binding architecture; implementation/release choices are pending proposals.

| ID | Choice and recommendation | Blocks |
|---|---|---|
| O1 | Board accepts 0.7 seams/managed adapters/#1021, 0.8 full moves, pre-1.0 ownership completion; reconciles G5/G6 item ordering without INT-04/INT-05/STD-01 ancestry, separately from INT-06/07 epic closure and existing 0.8 DRIVER-EXTRACTION-01/INT-18. Retain original integration/physical acceptance. | Dispatch under amended packages; no automatic existing-guide supersession |
| O2 / G5 D1 | New epoch on RESTART/START-after-STOP versus contract-style same-epoch generation replacement. Draft requests NEW epoch; recommend honoring it only with an explicit hub/contract amendment and successor/recovery vectors. Specify stable SourceID, generation mapping, single reservation and retire-before-start. G4 AdmitSource/Activate cannot already do this. | G5 bridge; O6-default PR 0a; new epoch adds PR 0b (Cx 5) before PR 1 |
| O3 / G5 D2 | Approve fresh missing-namespace RUNNING bootstrap and disabled-config precedence; recommend shell available/eBUS withheld on corrupt, unreadable or unsupported control state. Preserve add-on migration-required behavior and stored STOPPED. | G5 durable bootstrap/recovery |
| O4 / G5 D3 | Choose namespace version, durable transaction/restore format, numeric ledger capacity/retention/rollback window, compaction, digest encoding, initial counters and observed-only catalog revision behavior. Recommend bounded refusal over eviction of reachable receipts; no numeric default invented here. | G5 persistence/control |
| O5 / G5 D4 | Approve experimental runtime tool names/envelope and exact trusted principal/authority/deadline adapter, read/control caller policy. Lifecycle authority must not imply pairing/device-write authority. | G5 operator MCP exposure |
| O6 / G5 D5 | Approve lifecycle-only eBUS registration, no fabricated binding, synthetic nonempty recovery proof, finite semantic retry/cleanup budgets; restore default PR 0a: gateway-owned semhub export/restore hooks persist complete accepted record: accepted publication batches AND accepted control transitions (withdrawals/fences, retirements, admissions) with results, settled state and monotonic points, snapshots/cursors/index and pending work, plus pending envelopes without recorded results. Restore resolves pending by cursor comparison/exact-byte resubmission; replay reconstructs kernel from record; persisted SnapshotID/digest mismatch fails closed per asset. No SemReg change; alternative: SemReg snapshot-restore API replaces PR 0a, external prerequisite, issue Cx 8. Shared-asset/LIFE-22 separately blocked. | G5 proof/managed adapters |
| O7 / G5 D6 | O6/D5 default (Cx 9 with/without O2 PR 0b): PR 0a restoration bridge, Cx 5; PR 0b only for O2 new epoch/restart: hub-native A2 succession, Cx 5, public docs before/with it; PR 1 goldens/registration/store/service/eBUS/replay/restoration test, Cx 8; PR 2 kernel-owned operator boundary/tools, Cx 4. Selected PR 0a/0b precede PR 1 then PR 2. O6 alternative: no PR 0a; external SemReg snapshot-restore API prerequisite; issue Cx 8. Keep exact merged G4 contract/docs/gates. First slice: config.go/gateway.go/startup_scan untouched; else rescope with physical/smoke obligations. | G5 dispatch; no standing live authorization |
| O8 | Confirm G5 defaults: compiled packages in gateway repository, descriptor v1 owned by gateway contract, hook schemas owned by DM-HOOKS. No repository split/dynamic loader now; native libraries stay owners. | DM-DOC (records the default as provisional), DM-G5, DM-HOOKS and 0.8 extraction manifests |
| O9 | Confirm CAN→Modbus→eeBUS→eBUS order after current transport/evidence reconciliation; assign CAN transport/binding owner and disposition unsupplied runtime. | CAN move and any priority change |
| O10 | 0.8 northbound framework only or framework plus virtual Modbus smart meter. Recommend concrete read-only TCP case if profile evidence exists; select exact dialect/model, source/freshness/unavailable policy and peer hardware. Cost is in section 4; optional issue chain stays nonmandatory until selected. | Concrete northbound chain and claimed support |
| O11 | Explicit owner for cross-driver selection/aggregation/translation policy, loss/freshness and operation route. Recommend typed separate binding policy with native encoders in drivers; no generic kernel battery policy. | EV station/battery translation/aggregation examples, all outside this guide's selected concrete scope |
| O12 | Is real Pi UART/eBUS frontend/backend available for northbound qualification? Default is outside 1.0; if available, create separately approved implementation/timing/hardware work and amend release scope only after qualification. | eBUS northbound; never southbound extraction completion |

Guide merges have no repository/issue/branch/commit/PR/deployment/runtime effects. Hashes check consistency only. Owning code repos retain proof. Family docs own native knowledge; docs-ebus owns runtime/API knowledge until amended; SemReg/docs-semantic own canonical semantics.

No execution resumes from #126 Phase B. Code work later reads accepted merged main and reconciles its DAG node in the owning repo. This task ends with local validation, uncommitted. Pending decisions, missing profile/physical evidence, uncertain close/recovery or unreviewed public contracts are hard stops, never PASS.
