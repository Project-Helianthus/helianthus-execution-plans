# Issue map

This is the human-readable dependency mirror of `plan.yaml`. It records 46 future
code-repository issue nodes. Each YAML issue also carries one bounded functional
acceptance statement, its applicable gates, and one rollback or fallback statement. Rows
do not create, start, or approve work.

| ID | Milestone | Repository | Depends on |
|---|---|---|---|
| FMV3-M0-01 | M0 | Project-Helianthus/.github | - |
| FMV3-M0-02 | M0 | Project-Helianthus/helianthus-modbus | FMV3-M0-01 |
| FMV3-M0-03 | M0 | Project-Helianthus/helianthus-modbusreg | FMV3-M0-01 |
| FMV3-M0-04 | M0 | Project-Helianthus/.github | FMV3-M0-01 |
| FMV3-M0-05 | M0 | Project-Helianthus/helianthus-eebus-binding-private | FMV3-M0-04 |
| FMV3-M0-07 | M0 | Project-Helianthus/helianthus-matter-binding-private | FMV3-M0-04 |
| FMV3-M0-06 | M0 | Project-Helianthus/helianthus-docs-ebus | - |
| FMV3-M1-00 | M1 | Project-Helianthus/helianthus-docs-ebus | FMV3-M0-02, FMV3-M0-06 |
| FMV3-M1-01 | M1 | Project-Helianthus/helianthus-modbus | FMV3-M0-02, FMV3-M1-00 |
| FMV3-M1-02 | M1 | Project-Helianthus/helianthus-modbus | FMV3-M1-01 |
| FMV3-M1-03 | M1 | Project-Helianthus/helianthus-modbus | FMV3-M1-02 |
| FMV3-M1-04 | M1 | Project-Helianthus/helianthus-modbus | FMV3-M1-02, FMV3-M1-03 |
| FMV3-M1-05 | M1 | Project-Helianthus/helianthus-docs-ebus | FMV3-M1-04 |
| FMV3-M1-06 | M1 | Project-Helianthus/helianthus-modbus | FMV3-M1-04, FMV3-M1-05 |
| FMV3-M2-01 | M2 | Project-Helianthus/helianthus-modbusreg | FMV3-M0-03, FMV3-M1-00, FMV3-M1-01, FMV3-M1-06 |
| FMV3-M2-02 | M2 | Project-Helianthus/helianthus-modbusreg | FMV3-M1-00, FMV3-M2-01 |
| FMV3-M2-03 | M2 | Project-Helianthus/helianthus-modbusreg | FMV3-M1-00, FMV3-M2-01, FMV3-M2-02 |
| FMV3-M3-01 | M3 | Project-Helianthus/helianthus-docs-ebus | FMV3-M0-06, FMV3-M2-01 |
| FMV3-M3-02 | M3 | Project-Helianthus/helianthus-modbusreg | FMV3-M1-02, FMV3-M2-03, FMV3-M3-01 |
| FMV3-M3-03 | M3 | Project-Helianthus/helianthus-modbusreg | FMV3-M3-02 |
| FMV3-M4-01 | M4 | Project-Helianthus/helianthus-ebusgateway | FMV3-M0-06, FMV3-M1-02, FMV3-M3-03 |
| FMV3-M4-02 | M4 | Project-Helianthus/helianthus-ebusgateway | FMV3-M4-01 |
| FMV3-M4-03 | M4 | Project-Helianthus/helianthus-ha-addon | FMV3-M4-01 |
| FMV3-M4-04 | M4 | Project-Helianthus/helianthus-ebusgateway | FMV3-M4-02, FMV3-M4-03 |
| FMV3-M4-05 | M4 | Project-Helianthus/helianthus-docs-ebus | FMV3-M3-01, FMV3-M4-04 |
| FMV3-M5-01 | M5 | Project-Helianthus/helianthus-ebusreg | FMV3-M5-02 |
| FMV3-M5-02 | M5 | Project-Helianthus/helianthus-docs-ebus | FMV3-M4-05 |
| FMV3-M5-03 | M5 | Project-Helianthus/helianthus-execution-plans | FMV3-M5-04 |
| FMV3-M5-04 | M5 | Project-Helianthus/helianthus-ebusgateway | FMV3-M5-01, FMV3-M5-02 |
| FMV3-M5-09 | M5 | Project-Helianthus/helianthus-docs-ebus | FMV3-M5-03 |
| FMV3-M5-05 | M5 | Project-Helianthus/helianthus-ebusgateway | FMV3-M5-09 |
| FMV3-M5-06 | M5 | Project-Helianthus/helianthus-ebusgateway | FMV3-M5-05 |
| FMV3-M5-07 | M5 | Project-Helianthus/helianthus-ha-integration | FMV3-M5-06 |
| FMV3-M5-08 | M5 | Project-Helianthus/helianthus-ha-addon | FMV3-M5-06, FMV3-M5-07 |
| FMV3-M6-00 | M6 | Project-Helianthus/helianthus-docs-ebus | FMV3-M5-08 |
| FMV3-M6-01 | M6 | Project-Helianthus/helianthus-eebus-binding-private | FMV3-M0-05, FMV3-M6-00 |
| FMV3-M6-02 | M6 | Project-Helianthus/helianthus-eebus-binding-private | FMV3-M6-01 |
| FMV3-M6-03 | M6 | Project-Helianthus/helianthus-docs-ebus | FMV3-M6-02 |
| FMV3-M7-01 | M7 | Project-Helianthus/helianthus-docs-ebus | FMV3-M0-06, FMV3-M1-04, FMV3-M2-03, FMV3-M5-09 |
| FMV3-M7-02 | M7 | Project-Helianthus/helianthus-modbusreg | FMV3-M1-04, FMV3-M2-03, FMV3-M3-03, FMV3-M7-01 |
| FMV3-M7-03 | M7 | Project-Helianthus/helianthus-modbusreg | FMV3-M7-02 |
| FMV3-M7-04 | M7 | Project-Helianthus/helianthus-modbusreg | FMV3-M7-03 |
| FMV3-M7-05 | M7 | Project-Helianthus/helianthus-modbusreg | FMV3-M7-04 |
| FMV3-M8-00 | M8 | Project-Helianthus/helianthus-docs-ebus | FMV3-M5-08 |
| FMV3-M8-01 | M8 | Project-Helianthus/helianthus-matter-binding-private | FMV3-M0-07, FMV3-M8-00 |
| FMV3-M8-02 | M8 | Project-Helianthus/helianthus-matter-binding-private | FMV3-M8-01 |

The exact titles and issue-level acceptance, gates, and rollback remain adjacent to each
node in `plan.yaml`; protocol details and outcome-gate semantics are summarized in
`11-fronius-readonly-and-semantic-lock.md` and `13-roadmap-gates-and-risks.md`. The M3
boundary is historical. The reconciled public delivery stops after `FMV3-M7-05`; the ten
remaining M0/M6/M8 private-binding nodes retain their declared dependencies.
