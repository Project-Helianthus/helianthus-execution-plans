# 0.7 work-package and dependency map

Stable IDs describe planned outcomes. They do not encode runtime state, authorize
execution or replace repository-owned issues. `PUBLIC-01` through `PUBLIC-08` are
an ordered priority queue, not false technical dependencies: independent ready work
can proceed in parallel under the owning repository workflow.

| ID | Release | Owner | Outcome | Prerequisites |
|---|---|---|---|---|
| PUBLIC-01 | 0.7 | Project-Helianthus/.github | Truthful gateway README and organization profile | None |
| PUBLIC-02 | 0.7 | Project-Helianthus/.github | Anonymous clone/build/test proof and evidence-led quickstart correction | None |
| PUBLIC-03 | 0.7 | Project-Helianthus/.github | Public product maturity matrix and `main` versus add-on pin clarity | None |
| PUBLIC-04 | 0.7 | Project-Helianthus/.github | Public/private, licensing and existing-CLA boundary clarification | None |
| PUBLIC-05 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Existing PV SunSpec to SemReg, MCP, GraphQL and Portal evidence | None |
| PUBLIC-06 | 0.7 | Project-Helianthus/.github | First contributor/profile demonstration quick path | None |
| PUBLIC-07 | 0.7 | Project-Helianthus/helianthus-eebusreg | Useful public eebusreg README | None |
| PUBLIC-08 | 0.7 | Project-Helianthus/.github | Temporary upstream-fork badges and active-branch clarity | None |
| GOV-01 | 0.7 | Project-Helianthus/.github | Roles and runtime binding reconciliation | None |
| CLEAN-01 | 0.7 | Project-Helianthus/.github | Historical issue reconciliation without lost acceptance | None |
| STD-01 | 0.7 | Project-Helianthus/helianthus-docs-eebus | Pin applicable eeBUS normative corpus | None |
| SEMREG-BOOTSTRAP | 0.7 | Project-Helianthus/.github | Reconcile historical bootstrap intent with existing public SemReg/docs owners | INT-04 |
| LEGACY-PERSIST | 0.7 | Project-Helianthus/helianthus-ebusgateway | Persistent state, migration and restart acceptance | None |
| LEGACY-IDENTITY | 0.7 | Project-Helianthus/helianthus-ebusgateway | Address, enrichment and passive-tap acceptance | None |
| LEGACY-MUX | 0.7 | Project-Helianthus/helianthus-ebusgateway | Historical mux qualification reconciliation | None |
| NATIVE-01 | 0.7 | Project-Helianthus/helianthus-ebusreg | VR940f identity and address grouping regression | None |
| NATIVE-02 | 0.7 | Project-Helianthus/helianthus-eebus-go | SHIP discovery and pending pairing | None |
| NATIVE-03 | 0.7 | Project-Helianthus/helianthus-modbusreg | SunSpec/Fronius read-only qualification readiness | None |
| NATIVE-04 | 0.7 | Project-Helianthus/helianthus-modbusreg | Huawei read-only identity, profiles, providers and qualification outcomes (H01, H03-H06, H15-H16) | H06 |
| NATIVE-05 | 0.7 | Project-Helianthus/helianthus-canbusreg | Gree CAN replay and qualification readiness | None |
| NATIVE-06 | 0.7 | Project-Helianthus/helianthus-canbusreg | Growatt BMS CAN V1.04 readiness | None |
| NATIVE-07-GROWATT-II | 0.7 | Project-Helianthus/helianthus-modbusreg | Growatt Protocol II readiness | None |
| NATIVE-07-GROWATT-BMS | 0.7 | Project-Helianthus/helianthus-modbusreg | Growatt BMS RS485 readiness | None |
| NATIVE-07-TESLA-GEN3 | 0.7 | Project-Helianthus/helianthus-modbusreg | Tesla Gen3 native readiness | None |
| NATIVE-07-TESLA-LEGACY | 0.7 | Project-Helianthus/helianthus-modbusreg | Tesla legacy native readiness | None |
| NATIVE-07-OUTBACK | 0.7 | Project-Helianthus/helianthus-modbusreg | OutBack native readiness | None |
| NATIVE-08 | 0.7 | Project-Helianthus/helianthus-ebusreg | Source-selection no-op proof | None |
| NATIVE-09 | 0.7 | Project-Helianthus/helianthus-vrc-explorer | VRC Explorer reproducible product acceptance | None |
| INT-00 | 0.7 | Project-Helianthus/helianthus-execution-plans | Current 0.7 scope and historical-draft reconciliation | None |
| INT-01 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Existing SunSpec Qualify-to-Refresh test | None |
| INT-02 | 0.7 | Project-Helianthus/helianthus-ha-addon | Existing packaging and M2M checks | None |
| INT-03 | 0.7 | Project-Helianthus/helianthus-ha-integration | Existing HA acceptance reconciliation | None |
| INT-04 | 0.7 | Project-Helianthus/helianthus-execution-plans | Versioned 0.7 semantic contract design | INT-00, STD-01 |
| INT-05 | 0.7 | Project-Helianthus/helianthus-semreg | Existing SemReg contract implementation and capability packs | INT-04 |
| INT-06 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Generic north/south contract and driver extension hooks | INT-04 |
| INT-07 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Driver composition without native FSM/decoder ownership | INT-05, INT-06, NATIVE-01, NATIVE-02, NATIVE-03, NATIVE-04, NATIVE-05, NATIVE-06, NATIVE-07-GROWATT-II, NATIVE-07-GROWATT-BMS, NATIVE-07-TESLA-GEN3, NATIVE-07-TESLA-LEGACY, NATIVE-07-OUTBACK |
| INT-08 | 0.7 | Project-Helianthus/helianthus-ebusgateway | North/south MCP and GraphQL projections | INT-05, INT-06, INT-07 |
| INT-09 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Extensible Portal and driver UI contribution design | INT-04, INT-06 |
| INT-10 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Portal implementation and extensibility proof | INT-08, INT-09 |
| INT-11 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Common transport and semantic metrics | INT-06, INT-08 |
| INT-12 | 0.7 | Project-Helianthus/helianthus-ebusgateway | eeBUS output binding | INT-08, STD-01 |
| INT-13 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Matter output binding | INT-08 |
| INT-14 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Gateway rename | INT-10, INT-11, INT-12, INT-13, INT-15 |
| INT-15 | 0.7 | Project-Helianthus/helianthus-ha-integration | HA GraphQL consumer contract | INT-03, INT-08 |
| INT-16 | 0.7 | Project-Helianthus/helianthus-ha-addon | Exact-BOM 0.7 candidate package | INT-01, INT-02, INT-10, INT-11, INT-12, INT-13, INT-14, INT-15, H10, H11, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-17 | 0.7 | Project-Helianthus/helianthus-gateway | Offline acceptance and hardware-test preparation | INT-16, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX, NATIVE-01, NATIVE-02, NATIVE-03, NATIVE-04, NATIVE-05, NATIVE-06, NATIVE-07-GROWATT-II, NATIVE-07-GROWATT-BMS, NATIVE-07-TESLA-GEN3, NATIVE-07-TESLA-LEGACY, NATIVE-07-OUTBACK, NATIVE-09, H12 |
| INT-19 | 0.7 | Project-Helianthus/helianthus-gateway | Daybreak Blue review of final candidate | INT-17 |
| INT-20 | 0.7 | Project-Helianthus/helianthus-gateway | Exhaustive real-hardware validation | INT-19, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-21 | 0.7 | Project-Helianthus/helianthus-gateway | Publish only the final validated 0.7 BOM | INT-20, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| H01 | 0.7 | Project-Helianthus/helianthus-docs-modbus | Observed Huawei identity, child-routing and applicability contract | None |
| H02 | 0.7 | Project-Helianthus/helianthus-docs-ebus | Several Modbus TCP endpoints with per-endpoint family and driver instances | None |
| H03 | 0.7 | Project-Helianthus/helianthus-modbusreg | Clean-room Huawei identity fixtures, qualification cards and dispositions | H01 |
| H04 | 0.7 | Project-Helianthus/helianthus-docs-modbus | Huawei read-only monitoring, read-pacing and provider-acquisition contracts | H01 |
| H05 | 0.7 | Project-Helianthus/helianthus-modbusreg | SUN2000, LUNA2000 and Huawei-gateway meter monitoring profiles with capability detection | H03, H04 |
| H06 | 0.7 | Project-Helianthus/helianthus-modbusreg | Read-only production providers for SmartLogger, EMMA and S-Dongle installations | H05 |
| H07 | 0.7 | Project-Helianthus/helianthus-docs-semantic | Mapping of Huawei SUN2000, LUNA2000 and gateway-meter observations to the PV, Storage and Infrastructure packs | H04, H05 |
| H08 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Several Modbus TCP endpoints as independently qualified managed driver instances | H02, H13, H14 |
| H09 | 0.7 | Project-Helianthus/helianthus-ha-addon | Add-on endpoint-list options and Huawei acceptance rows | H02, H08 |
| H10 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Managed read-only Huawei driver and PV publication | H06, H07, H08 |
| H11 | 0.7 | Project-Helianthus/helianthus-ebusgateway | Huawei storage and meter publication, Portal views and composed offline acceptance | H10 |
| H12 | 0.7 | Project-Helianthus/helianthus-ha-integration | Huawei PV, storage and meter assets through the shared semantic snapshot; live confirmation follows H11 | H07 |
| H13 | 0.7 | Project-Helianthus/helianthus-modbus | Tolerant Modbus TCP framing and device-identification decoding for logger-class devices | None |
| H14 | 0.7 | Project-Helianthus/helianthus-docs-modbus | Tolerant framing and device-identification modes for logger-class devices in the transport contract | H13 |
| H15 | 0.7 | Project-Helianthus/helianthus-modbusreg | Observed S-Dongle single-inverter identity with clean-room fixtures and a qualification card | H03, H16 |
| H16 | 0.7 | Project-Helianthus/helianthus-docs-modbus | Observed S-Dongle single-inverter identity and the same-class hard-stop supersession rule | None |

## Huawei program placement

H01 to H16 are the Huawei implementation tickets of the 24 October 2026 operator
decision recorded in the [canonical guide](./00-canonical.md). They are the last rows of
the package table above and are mirrored in `plan.yaml` as a sub-DAG: the Prerequisites column
holds their edges, and the structural companion checks their unique IDs, owner
allowlist, dependency existence, acyclicity and Markdown agreement like every other
package. Each ticket is worked in its owning repository; issue links are in the
[issue map](./90-issue-map.md). The placement is scheduling metadata: it encodes no
runtime state and authorizes no execution.

NATIVE-04 carries the native-side tickets H01, H03 to H06, H15 and H16, depends on
H06 (the read-only providers) and keeps feeding INT-07 composition and INT-17 offline
acceptance; INT-07 itself is unchanged. H10 and H11 are prerequisites of the INT-16
candidate package and H12 is a prerequisite of INT-17 hardware-test preparation, which
makes the Huawei program a 0.7 release gate under the 24 October 2026 decision. The
[driver-model guide](../driver-model-transition.implementing/00-canonical.md) maps
Huawei to DM-COMP-SMARTLOGGER, DM-COMP-EMMA, DM-COMP-SDONGLE and DM-COMP-SUN2000;
the Modbus TCP part of DM-G6 is absorbed by H08, which follows the transport ticket
H13 and its documentation H14.

| ID | Plan node |
|---|---|
| H01 | NATIVE-04 documentation gate for R-M5A, R-M5B-EMMA, R-M5B-SDONGLE and R-M6B |
| H02 | DM-G6 and INT-07 documentation gate |
| H03 | NATIVE-04, prerequisite of R-M5A |
| H04 | Documentation gate for R-M6B |
| H05 | NATIVE-04, R-M6B |
| H06 | NATIVE-04, R-M5A, R-M5B-EMMA, R-M5B-SDONGLE |
| H07 | Semantic documentation gate for H10 and H11 |
| H08 | DM-G6 (Modbus TCP part), INT-07 |
| H09 | INT-16 and INT-17 preparation |
| H10 | DM-COMP-SMARTLOGGER, DM-COMP-SUN2000 (PV); prerequisite of INT-16 |
| H11 | DM-COMP-EMMA, DM-COMP-SDONGLE, DM-COMP-SUN2000 (storage); prerequisite of INT-16 |
| H12 | INT-15 slice; prerequisite of INT-17 |
| H13 | Transport prerequisite of H08 and H10 |
| H14 | Documentation companion of H13, before the first gateway consumer H08 |
| H15 | NATIVE-04, identity slice of R-M5B-SDONGLE |
| H16 | Documentation companion of H15 |

## Boundary and sequencing

The SemReg and docs-semantic repositories already exist publicly. The retained
`SEMREG-BOOTSTRAP` ID records the historical ownership decision only; it does not
assert a pending repository bootstrap. Native packages close provider-local
evidence. INT-06 and INT-07 retain generic gateway composition while driver-native
packages own protocol FSMs, decoders and qualification.

INT-19, INT-20 and INT-21 are the 0.7 Daybreak, physical-validation and release
chain. T01..T88 is deferred and unrun until the approved hardware step, but is
mandatory before 0.7.0. The future [0.8 guide](../software-declarative-08.locked/00-canonical.md)
starts after INT-21 acceptance and has no package in this table.

Any code, configuration, dependency or package fix during `INT-19` or `INT-20`
invalidates earlier candidate evidence. A changed final BOM receives fresh Daybreak
review plus affected hardware and conformance revalidation before `INT-21` publishes
it; release names only that validated BOM.

The local structural companion validates only this table's local structure. It
does not query GitHub, execute work, or prove implementation behavior.

## Priority issue links

1. [PUBLIC-01](https://github.com/Project-Helianthus/.github/issues/8)
2. [PUBLIC-02](https://github.com/Project-Helianthus/.github/issues/9)
3. [PUBLIC-03](https://github.com/Project-Helianthus/.github/issues/10)
4. [PUBLIC-04](https://github.com/Project-Helianthus/.github/issues/11)
5. [PUBLIC-05](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/985)
6. [PUBLIC-06](https://github.com/Project-Helianthus/.github/issues/12)
7. [PUBLIC-07](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/135)
8. [PUBLIC-08](https://github.com/Project-Helianthus/.github/issues/13)
