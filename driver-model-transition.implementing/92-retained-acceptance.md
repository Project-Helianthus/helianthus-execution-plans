# Retained acceptance and contract references

Canonical-SHA256: `ca9edfc928fe862162c6d349c4f226580aa05145d04ae53c81a0aa557c464a85`

Retained IDs/versions are traceability, not contract implementation or PASS claims. Exact pins are supplied snapshot evidence and must be reconciled in the code repository. This guide defines no release/admission manifest or attestation.

| ID | Version | Owner | Retained disposition |
|---|---|---|---|
| runtime-driver-provider-contract | v1 | Project-Helianthus/helianthus-ebusgateway | Proposed implementation contract; retain G4 deviations; O2/O6 amendment pending |
| semreg-publication | v1 | Project-Helianthus/helianthus-semreg | Canonical meaning stays SemReg; per-asset cursor and fence semantics retained |
| portal-contribution | v1 | Project-Helianthus/helianthus-ebusgateway | Generation/revision-fenced detached contributions; no claims replace native authority |
| participation-contract | v1 | Project-Helianthus/helianthus-eebusreg | Configured/applied provenance/loss; concrete wiring not claimed |
| LEGACY-PERSIST | retained-0.7 | Project-Helianthus/helianthus-ebusgateway | Atomic state/GUID/migration; physical rows retained |
| LEGACY-IDENTITY | retained-0.7 | Project-Helianthus/helianthus-ebusgateway | Keep #23 disposition and P/N acceptance; cache never live authority |
| LEGACY-MUX | retained-0.7 | Project-Helianthus/helianthus-ebusgateway | Keep #30 unqualified-mode disposition and transport/physical evidence |

The inventory used GW bf09d80f75cf045b81b906284d24b3c34f3471f2, while G5 draft used 87b6268e8bafdbf0b4edb1e21144e53653d52338 and G4 issue cited 2097c311. GW’s inventoried semreg pin was 089ed6ae9004, native sibling HEAD ba8b85630bfa66eb7ca507920ef1084ee0642e6c. These are separate evidence layers, not a single current contract baseline.

| Acceptance group | Successor and retained obligation |
|---|---|
| G4 S1–S7 | DM-G5/managed adapters keep stable asset/source and per-incarnation binding/service/capability identities, per-asset cursors vs HubSeq, transactional publication, read fences, overflow/resync and legacy first-incarnation goldens. No new semantic ErrorIDs. |
| G4 deviations 1–5 | Per-asset sequence instead of global; legacy declared epoch repeats across processes; nonzero generation may exceed 1; Tesla successor new epoch/gen+1; PV admission sample after open. Removal needs a family contract/golden migration, never silent generalization. |
| G5 S1–S6, CTL-01..11, applicable LIFE rows | DM-G5 retains durable ordered control, principal/revision/idempotency, transaction/recovery, source/epoch/native-generation fencing, independent semantic/native cleanup and shell/status isolation. O2–O7 must resolve exact amendments first. |
| LIFE-22/shared assets | Remains a separate prerequisite: G4 one-source-per-asset and asset-wide read gates do not establish shared-source isolation. No complete SPI claim from lifecycle-only eBUS proof. |
| INT-06/07/08/09/10/11/12/13/15 | Registration/composition hooks do not erase native qualification, public parity, Portal, observability, eeBUS/Matter projection loss and HA consumer acceptance. Package closure remains integrated acceptance, not provider DTO availability. |
| LEGACY-PERSIST P1–P6/N1–N4 | DM-G5/state moves preserve sole gateway writer, add-on GUID ownership, atomic same-directory fsync/rename/no EXDEV fallback, migration-required token/marker/exit, quarantine and opaque namespaces. Cached hints never current admission. Preserve all named live rows in existing INT-20. |
| LEGACY-IDENTITY P1–P6/N1–N5 and Phase B M6/M7 | DM-RAW (#1021) requires satisfied R-G2C (gateway PR #1018 merged 2026-10-14, main 2097c311; supplied review facts) before ownership moves. G2’s remaining operator smoke session at the existing site is a dispatch-time overlap constraint on the same raw 07 04 identification evidence, not a prerequisite; DM-RAW and the DM-DOC → DM-G5 chain do not descend from STD-01 or from G2’s site smoke session, while the leaf compositions keep the lane checkpoints (C1, X1, Board dispositions) and every DM-07 node follows O1 through DM-PLAN; DM-RAW/eBUS moves retain raw request/response and promotion lineage, SYN/address negative controls, full qualified identity/merge rules and dual-consumer parity; #23 disposition/live evidence remains original program. |
| LEGACY-MUX historical NO_GO | eBUS transport move retains narrow arbitration/echo predicate or explicitly evidenced replacement, contention qualification/observable targets, transport parity and exact-BOM rollback/waiver disposition. #30 is not closed by moving packages. |
| INT-16/17/19/20/21 | Existing exact-BOM packaging/offline readiness→Daybreak→physical→release chain remains. Code/config/pin changes invalidate affected prior evidence; missing claimed device stays a blocker. |

Reusable family contracts belong in docs-ebus/docs-modbus/docs-canbus/docs-eebus; canonical semantics in docs-semantic. Interfaces, golden fixtures and conformance/parity tests belong in their producer/consumer code repos. No long implementation contract is mirrored into the structural validator.
