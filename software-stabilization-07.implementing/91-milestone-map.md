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
| NATIVE-04 | 0.7 | Project-Helianthus/helianthus-modbusreg | Huawei qualification outcomes | None |
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
| INT-16 | 0.7 | Project-Helianthus/helianthus-ha-addon | Exact-BOM 0.7 candidate package | INT-01, INT-02, INT-10, INT-11, INT-12, INT-13, INT-14, INT-15, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-17 | 0.7 | Project-Helianthus/helianthus-gateway | Offline acceptance and hardware-test preparation | INT-16, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX, NATIVE-01, NATIVE-02, NATIVE-03, NATIVE-04, NATIVE-05, NATIVE-06, NATIVE-07-GROWATT-II, NATIVE-07-GROWATT-BMS, NATIVE-07-TESLA-GEN3, NATIVE-07-TESLA-LEGACY, NATIVE-07-OUTBACK, NATIVE-09 |
| INT-19 | 0.7 | Project-Helianthus/helianthus-gateway | Daybreak Blue review of final candidate | INT-17 |
| INT-20 | 0.7 | Project-Helianthus/helianthus-gateway | Exhaustive real-hardware validation | INT-19, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |
| INT-21 | 0.7 | Project-Helianthus/helianthus-gateway | 0.7 release after all gates | INT-20, LEGACY-PERSIST, LEGACY-IDENTITY, LEGACY-MUX |

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
