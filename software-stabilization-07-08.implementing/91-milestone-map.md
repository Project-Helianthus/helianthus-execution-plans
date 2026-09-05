# Work-package and dependency map

Stable IDs identify planned outcomes. They do not encode mutable runtime state, authorize execution, or replace repository-owned issues. Each owner below is accountable for splitting cross-repository work into issues owned by the affected code repositories before implementation. Detailed acceptance follows the canonical guide and retained legacy assertions.

| ID | Release | Owner | Outcome | Prerequisites |
|---|---|---|---|---|
| GOV-01 | 0.7 | Project-Helianthus/.github | Adopt clear roles and reconcile runtime bindings | None |
| CLEAN-01 | 0.7 | Project-Helianthus/.github | Reconcile and close historical issues without losing acceptance | None |
| STD-01 | 0.7 | Project-Helianthus/helianthus-docs-eebus | Verify and pin the current eeBUS normative corpus | None |
| SEMREG-BOOTSTRAP | 0.7 | Project-Helianthus/.github | Establish public semreg code and docs-semantic documentation destinations and contract boundaries | INT-04 |
| LEGACY-PERSIST | 0.7 | Project-Helianthus/helianthus-ebusgateway | Reconcile persistent state, migration and restart acceptance | None |
| LEGACY-IDENTITY | 0.7 | Project-Helianthus/helianthus-ebusgateway | Reconcile address-table, enrichment and passive-tap acceptance | None |
| LEGACY-MUX | 0.7 | Project-Helianthus/helianthus-ebusgateway | Resolve the historical mux qualification gap against current code | None |
| NATIVE-01 | 0.7 | Project-Helianthus/helianthus-ebusreg | Close VR940f identity and address grouping regression | None |
| NATIVE-02 | 0.7 | Project-Helianthus/helianthus-eebus-go | Close native SHIP discovery and observable pending pairing | None |
| NATIVE-03 | 0.7 | Project-Helianthus/helianthus-modbusreg | Make the existing SunSpec/Fronius native path reproducibly ready for read-only hardware qualification | None |
| NATIVE-04 | 0.7 | Project-Helianthus/helianthus-modbusreg | Close Huawei qualification preparation with separate SmartLogger, EMMA and S-Dongle outcomes | None |
| NATIVE-05 | 0.7 | Project-Helianthus/helianthus-canbusreg | Close Gree CAN candidate receive-only replay and qualification readiness | None |
| NATIVE-06 | 0.7 | Project-Helianthus/helianthus-canbusreg | Close Growatt low-voltage BMS CAN V1.04 native readiness | None |
| NATIVE-07-GROWATT-II | 0.7 | Project-Helianthus/helianthus-modbusreg | Close Growatt Protocol II v1.24 TL3-X native readiness for software 0.7 | None |
| NATIVE-07-GROWATT-BMS | 0.7 | Project-Helianthus/helianthus-modbusreg | Close Growatt BMS RS485 1xSxxP ESS native readiness for software 0.7 | None |
| NATIVE-07-TESLA-GEN3 | 0.7 | Project-Helianthus/helianthus-modbusreg | Close Tesla Gen3 HSC native readiness for software 0.7 | None |
| NATIVE-07-TESLA-LEGACY | 0.7 | Project-Helianthus/helianthus-modbusreg | Close Tesla legacy FBE0/FDE0 native readiness for software 0.7 | None |
| NATIVE-07-OUTBACK | 0.7 | Project-Helianthus/helianthus-modbusreg | Close OutBack AXS SunSpec native readiness for software 0.7 | None |
| NATIVE-08 | 0.7 | Project-Helianthus/helianthus-ebusreg | Close source-selection registry no-op proof | None |
| NATIVE-09 | 0.7 | Project-Helianthus/helianthus-vrc-explorer | Include VRC explorer in reproducible product acceptance | None |
| INT-00 | 0.7 | Project-Helianthus/helianthus-execution-plans | Reconcile the 0.7 software scope, merged baseline, and semantic draft | None |
| INT-01 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Close the SunSpec producer Qualify → Refresh test | None |
| INT-02 | 0.7 | Project-Helianthus/helianthus-ha-addon | Close the existing packaging and M2M checks | None |
| INT-03 | 0.7 | Project-Helianthus/helianthus-ha-integration | Reconcile and close existing HA acceptance without duplicate rewrites | None |
| INT-04 | 0.7 | Project-Helianthus/helianthus-execution-plans | Design the complete Semantic Layer on Matter 1.7 draft and current eeBUS | INT-00, STD-01 |
| INT-05 | 0.7 | Project-Helianthus/helianthus-semreg | Implement semreg and all 0.7 software capability packs | INT-04, SEMREG-BOOTSTRAP |
| INT-06 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Design the north-south flow and complete driver contract | INT-04 |
| INT-07 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Connect all drivers and native acquisition into the gateway composition | INT-05, INT-06, NATIVE-01, NATIVE-02, NATIVE-03, NATIVE-04, NATIVE-05, NATIVE-06, NATIVE-07-GROWATT-II, NATIVE-07-GROWATT-BMS, NATIVE-07-TESLA-GEN3, NATIVE-07-TESLA-LEGACY, NATIVE-07-OUTBACK |
| INT-08 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Implement the north-south flow and MCP/GraphQL projections | INT-05, INT-06, INT-07 |
| INT-09 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Design the extensible Portal and driver UI contributions | INT-04, INT-06 |
| INT-10 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Implement the new Portal and verified extensibility | INT-08, INT-09 |
| INT-11 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Coherent Prometheus for transports and semantics | INT-06, INT-08 |
| INT-12 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Design and implement the eeBUS output binding | INT-08, STD-01 |
| INT-13 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Design and implement the Matter output binding | INT-08 |
| INT-14 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Rename helianthus-ebusgateway to helianthus-gateway | INT-10, INT-11, INT-12, INT-13, INT-15 |
| INT-15 | 0.7 | Project-Helianthus/helianthus-ha-integration | HA consumes the full 0.7 software contract through GraphQL | INT-03, INT-08 |
| INT-16 | 0.7 | Project-Helianthus/helianthus-ha-addon | Package the 0.7 software candidate at the exact BOM before review and the hardware gate | INT-01, INT-02, INT-10, INT-11, INT-12, INT-13, INT-14, INT-15, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-17 | 0.7 | Project-Helianthus/helianthus-gateway | Close offline acceptance and prepare hardware testing | INT-16, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX, NATIVE-01, NATIVE-02, NATIVE-03, NATIVE-04, NATIVE-05, NATIVE-06, NATIVE-07-GROWATT-II, NATIVE-07-GROWATT-BMS, NATIVE-07-TESLA-GEN3, NATIVE-07-TESLA-LEGACY, NATIVE-07-OUTBACK, NATIVE-09 |
| INT-18 | 0.8 | Project-Helianthus/.github | 0.8: design and implement declarative IR/codegen and measured code reduction | INT-21 |
| INT-19 | 0.7 | Project-Helianthus/helianthus-gateway | 0.7: Daybreak Blue review of the complete candidate | INT-17 |
| INT-20 | 0.7 | Project-Helianthus/helianthus-gateway | 0.7: exhaustive validation on real hardware | INT-19, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-21 | 0.7 | Project-Helianthus/helianthus-gateway | Publish release0.7 after all gates | INT-20, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-22 | 0.8 | Project-Helianthus/helianthus-gateway | 0.8: Daybreak Blue review after the declarative transformation | INT-18 |
| INT-23 | 0.8 | Project-Helianthus/helianthus-gateway | 0.8: exhaustive validation on real hardware | INT-22 |
| INT-24 | 0.8 | Project-Helianthus/helianthus-gateway | Publish release0.8 with measured actual reduction | INT-23 |

## Repository ownership and sequencing

Native IDs close provider-local artifacts only. INT-07 owns gateway acquisition, INT-08 public semantic surfaces, and INT-17 the integrated matrix. LEGACY packages close offline reconciliation/proof; their live assertions remain INT-20 acceptance and block INT-21. A release candidate can therefore be built before the hardware tests that need it.

SEMREG-BOOTSTRAP establishes the planned public implementation repository before INT-05. INT-06 is the gateway's runtime driver/provider SPI and north-south composition contract; durable documentation, types, and fixtures are published by their actual producer and consumer owners, with protocol-neutral canonical domain types owned by semreg. It is design and may advance while bootstrap completes. STD-01 gates normative mapping freeze, not conceptual exploration or independent fixes.

INT-12 and INT-13 have the public gateway as their accountable software owner. If the approved design chooses new public binding repositories, update the owner map and bootstrap dependencies before dispatch. The separate private hardware repository cannot own these public software outputs.

INT-18 is a cross-repository0.8 design/delivery package owned by platform governance; its implementation must be split into the selected compiler/native/semantic repositories after that design. No compiler implementation belongs in .github or execution-plans merely because those repositories coordinate the work.

The rename waits for Portal, observability, bindings and HA freeze, then migrates all affected repository, documentation, project, remote, module, import, image, and pin references before packaging. Packages INT-17 and INT-19 through INT-24 use the planned post-rename repository only after INT-14. NATIVE-08 is P3 evidence-only cleanup under CLEAN-01 and is nonblocking for release.

The local read-only plan.yaml companion and validate_plan.py validate IDs, known owners, dependencies, DAG acyclicity, the bootstrap boundary and this table. The existing repository gate checks this guide explicitly. They neither query GitHub nor execute the plan.
