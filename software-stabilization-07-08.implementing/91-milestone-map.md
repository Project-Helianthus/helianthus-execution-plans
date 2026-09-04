# Work-package and dependency map

Stable IDs identify planned outcomes. They do not encode mutable runtime state, authorize execution, or substitute for repository-owned issues. Detailed acceptance follows the canonical guide and retained legacy assertions; implementation issues refine it in their owning repositories.

| ID | Release | Outcome | Prerequisites |
|---|---|---|---|
| GOV-01 | 0.7 | Adopt clear roles and reconcile runtime bindings | None; provider-owned prerequisites verified at dispatch |
| CLEAN-01 | 0.7 | Reconcile and close historical issues without losing acceptance | None; provider-owned prerequisites verified at dispatch |
| STD-01 | 0.7 | Verify and pin the current eeBUS normative corpus | None; provider-owned prerequisites verified at dispatch |
| SEMREG-BOOTSTRAP | 0.7 | Establish the public semantic repository and contract boundary | INT-04 |
| LEGACY-PERSIST | 0.7 | Reconcile persistent state, migration and restart acceptance | None; provider-owned prerequisites verified at dispatch |
| LEGACY-IDENTITY | 0.7 | Reconcile address-table, enrichment and passive-tap acceptance | None; provider-owned prerequisites verified at dispatch |
| LEGACY-MUX | 0.7 | Resolve the historical mux qualification gap against current code | None; provider-owned prerequisites verified at dispatch |
| NATIVE-01 | 0.7 | Close VR940f identity and address grouping regression | None; provider-owned prerequisites verified at dispatch |
| NATIVE-02 | 0.7 | Close native SHIP discovery and observable pending pairing | None; provider-owned prerequisites verified at dispatch |
| NATIVE-03 | 0.7 | Make the existing SunSpec/Fronius native path reproducibly ready for read-only hardware qualification | None; provider-owned prerequisites verified at dispatch |
| NATIVE-04 | 0.7 | Close Huawei qualification preparation with separate SmartLogger, EMMA and S-Dongle outcomes | None; provider-owned prerequisites verified at dispatch |
| NATIVE-05 | 0.7 | Close Gree CAN candidate receive-only replay and qualification readiness | None; provider-owned prerequisites verified at dispatch |
| NATIVE-06 | 0.7 | Close Growatt low-voltage BMS CAN V1.04 native readiness | None; provider-owned prerequisites verified at dispatch |
| NATIVE-07-GROWATT-II | 0.7 | Close Growatt Protocol II v1.24 TL3-X native readiness for software 0.7 | None; provider-owned prerequisites verified at dispatch |
| NATIVE-07-GROWATT-BMS | 0.7 | Close Growatt BMS RS485 1xSxxP ESS native readiness for software 0.7 | None; provider-owned prerequisites verified at dispatch |
| NATIVE-07-TESLA-GEN3 | 0.7 | Close Tesla Gen3 HSC native readiness for software 0.7 | None; provider-owned prerequisites verified at dispatch |
| NATIVE-07-TESLA-LEGACY | 0.7 | Close Tesla legacy FBE0/FDE0 native readiness for software 0.7 | None; provider-owned prerequisites verified at dispatch |
| NATIVE-07-OUTBACK | 0.7 | Close OutBack AXS SunSpec native readiness for software 0.7 | None; provider-owned prerequisites verified at dispatch |
| NATIVE-08 | 0.7 | Close source-selection registry no-op proof | None; provider-owned prerequisites verified at dispatch |
| NATIVE-09 | 0.7 | Include VRC explorer in reproducible product acceptance | None; provider-owned prerequisites verified at dispatch |
| INT-00 | 0.7 | Reconciliază scope software 0.7, baza merged și draftul semantic | None; provider-owned prerequisites verified at dispatch |
| INT-01 | 0.7 | Închide testul producătorului SunSpec Qualify → Refresh | None; provider-owned prerequisites verified at dispatch |
| INT-02 | 0.7 | Închide verificările existente de ambalare și M2M | None; provider-owned prerequisites verified at dispatch |
| INT-03 | 0.7 | Reconcile și închide acceptanța HA existentă, fără rescriere duplicată | None; provider-owned prerequisites verified at dispatch |
| INT-04 | 0.7 | Proiectează Semantic Layer complet pe Matter 1.7 draft și eeBUS curente | INT-00, STD-01 |
| INT-05 | 0.7 | Implementează semreg și toate capability packs software 0.7 | INT-04, SEMREG-BOOTSTRAP |
| INT-06 | 0.7 | Proiectează fluxul north-south și contractul complet de driver | INT-04 |
| INT-07 | 0.7 | Conectează toate driverele și achizițiile native în compoziția gateway | INT-05, INT-06, NATIVE-01, NATIVE-02, NATIVE-03, NATIVE-04, NATIVE-05, NATIVE-06, NATIVE-07-GROWATT-II, NATIVE-07-GROWATT-BMS, NATIVE-07-TESLA-GEN3, NATIVE-07-TESLA-LEGACY, NATIVE-07-OUTBACK |
| INT-08 | 0.7 | Implementează fluxul north-south și proiecțiile MCP/GraphQL | INT-05, INT-06, INT-07 |
| INT-09 | 0.7 | Proiectează Portalul extensibil și contribuțiile de UI ale driverelor | INT-04, INT-06 |
| INT-10 | 0.7 | Implementează Portalul nou și extensibilitatea verificată | INT-08, INT-09 |
| INT-11 | 0.7 | Prometheus coerent pentru transporturi și semantici | INT-06, INT-08 |
| INT-12 | 0.7 | Proiectează și implementează binding-ul eeBUS de ieșire | INT-08, STD-01 |
| INT-13 | 0.7 | Proiectează și implementează binding-ul Matter de ieșire | INT-08 |
| INT-14 | 0.7 | Redenumește helianthus-ebusgateway în helianthus-gateway | INT-10, INT-11, INT-12, INT-13, INT-15 |
| INT-15 | 0.7 | HA consumă întregul contract software 0.7 prin GraphQL | INT-03, INT-08 |
| INT-16 | 0.7 | Ambalează candidatul software 0.7 la BOM exact înaintea review-ului și hardware gate | INT-01, INT-02, INT-10, INT-11, INT-12, INT-13, INT-14, INT-15, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-17 | 0.7 | Închide acceptanța offline și pregătește testarea hardware | INT-16, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX, NATIVE-01, NATIVE-02, NATIVE-03, NATIVE-04, NATIVE-05, NATIVE-06, NATIVE-07-GROWATT-II, NATIVE-07-GROWATT-BMS, NATIVE-07-TESLA-GEN3, NATIVE-07-TESLA-LEGACY, NATIVE-07-OUTBACK, NATIVE-08, NATIVE-09 |
| INT-18 | 0.8 | 0.8: proiectează și implementează IR/codegen declarativ și reducerea măsurată de cod | INT-21 |
| INT-19 | 0.7 | 0.7: review Daybreak Blue pe candidatul complet | INT-17 |
| INT-20 | 0.7 | 0.7: validare exhaustivă pe hardware real | INT-19, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-21 | 0.7 | Publică release0.7 după toate gates | INT-20, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-22 | 0.8 | 0.8: review Daybreak Blue după transformarea declarativă | INT-18 |
| INT-23 | 0.8 | 0.8: validare exhaustivă pe hardware real | INT-22 |
| INT-24 | 0.8 | Publică release0.8 cu reducerea reală măsurată | INT-23 |

## Repository-local ownership

Native IDs own only provider-local artifacts. INT-07 owns gateway acquisition, INT-08 public semantic surfaces, INT-17 the integrated matrix. LEGACY items close offline reconciliation/proof; their live assertions remain INT-20 release gates. This avoids cyclic readiness between the release candidate and hardware tests.

SEMREG-BOOTSTRAP establishes the public implementation owner before INT-05. INT-06 is design and can advance while bootstrap completes. STD-01 gates normative mapping freeze, not conceptual exploration or independent fixes.

The rename waits for Portal, observability, bindings and HA freeze, then coordinates all affected remote/module/import/image/pin references before packaging. Multi-repository packages split into one issue per owning repository, with explicit cross-repo predecessor links.

The structural companion used during preparation verified unique IDs, dependency existence and DAG acyclicity. It is not installed as a plan runtime or required by contributors.
