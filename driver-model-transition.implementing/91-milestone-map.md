# Milestone map

Canonical-SHA256: `9005ab0cbcc166c60c997d787f744db55b0424a69cd12680a012a21e55e34bce`

Milestones describe intended acceptance; no live readiness/completion state is encoded. Issue dependencies are the finer DAG in plan.yaml and 90. Accepted 0.7/INT-21 is external to this guide, not created by its seam milestone.

| ID | Release | Prerequisites | Outcome |
|---|---|---|---|
| PHASE-B | planning | None | Uncommitted guide, local checks and explicit pending Board choices |
| DM-07 | 0.7 | PHASE-B | Registration/lifecycle and provider composition seams; #1021 evidence owner; existing 0.7 integration/release chain retained |
| DM-08-HOOKS | 0.8 | DM-07 | After external R-INT21, complete contribution hooks and fixtures |
| DM-08-FAMILIES | 0.8 | DM-08-HOOKS | CAN then Modbus then eeBUS then eBUS; packaging/consumer parity |
| DM-08-NORTHBOUND | 0.8 | DM-08-HOOKS, DM-08-FAMILIES | Framework mandatory; five virtual meter nodes conditional on O10 |
| DM-PRE1 | pre-1.0 | DM-08-FAMILIES, DM-08-NORTHBOUND | Complete ownership and exact-BOM evidence; eBUS northbound excluded unless O12 hardware qualification succeeds |

| Milestone | Planned issue IDs |
|---|---|
| PHASE-B | DM-PLAN |
| DM-07 | DM-DOC, DM-G5, DM-MANAGED-PV, DM-MANAGED-GROWATT, DM-MANAGED-EEBUS, DM-MANAGED-TESLA, DM-G6, DM-G7-SEAM, DM-G7, DM-G7B, DM-RAW, DM-COMP-SMARTLOGGER, DM-COMP-FRONIUS, DM-COMP-TESLA, DM-COMP-SUN2000, DM-COMP-EMMA, DM-COMP-SDONGLE, DM-COMP-GROWATT-II, DM-COMP-OUTBACK, DM-COMP-BLOCKED |
| DM-08-HOOKS | DM-HOOKS |
| DM-08-FAMILIES | DM-CAN-BASE, DM-DOC-CAN, DM-CAN, DM-DOC-MODBUS, DM-MODBUS-RUNTIME, DM-MODBUS-SURFACES, DM-DOC-EEBUS, DM-EEBUS-RUNTIME, DM-EEBUS-SURFACES, DM-DOC-EBUS, DM-EBUS-TRANSPORT, DM-EBUS-SEMANTICS, DM-EBUS-SURFACES, DM-EBUS-DECOUPLE, DM-ADDON, DM-HA-PARITY |
| DM-08-NORTHBOUND | DM-NB, DM-METER-DOC, DM-METER-SERVER, DM-METER-ENCODER, DM-METER-BINDING, DM-METER-ADDON |
| DM-PRE1 | DM-COMPLETE |

0.7 DM-07 is only this transition’s seam contribution. INT-06/07 epic closure, all G8–G19 integrations, exact candidate packaging, Daybreak, exhaustive physical acceptance and INT-21 remain the existing 0.7 program. No family extraction is smuggled into DM-07.

DM-08-FAMILIES follows census/risk order CAN→Modbus→eeBUS→eBUS; docs and packaging live in their own repositories. Existing 0.8 declarative roadmap must be reconciled under O1 rather than duplicated. Northbound framework proceeds after Modbus surfaces, while remaining family moves continue serially.

DM-PRE1 requires full inventory ownership coverage, no-eBUS host proof and accepted consumer/transport/BOM evidence. If O10 chooses a concrete meter, add its optional-chain completion and real peer qualification before declaring DM-PRE1 complete. eBUS native northbound is excluded absent O12-qualified Pi UART hardware; this exception does not defer protocol ownership extraction.
