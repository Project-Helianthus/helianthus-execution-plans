# Milestone map

This is the human-readable mirror of the 9 milestones in `plan.yaml`. Milestones group
issues; only issue dependencies define readiness.

| Milestone | Title |
|---|---|
| M0 | Governance, repository bootstraps, and boundary documentation |
| M1 | helianthus-modbus foundation |
| M2 | helianthus-modbusreg framework |
| M3 | Minimal SunSpec family and Fronius applicability |
| M4 | Gateway raw MCP integration and live read-only proof |
| M5 | Canonical PV semantic lock and public consumer promotion |
| M6 | Generic private eeBUS binding and myVaillant lab proof |
| M7 | SunSpec, Growatt, and Huawei profile expansion |
| M8 | Generic private Matter binding |

## Historical and current boundaries

The original cycle ended after M3 issue `FMV3-M3-03` and before `FMV3-M4-01`. That is
historical process context only. Reconciled public delivery ends after M7 issue
`FMV3-M7-05`; the remaining ten M0/M6/M8 nodes are private-binding governance and
implementation tracks.

## Main dependency direction

```text
M0 -> M1/M2 -> M3 -> M4 -> M5 -> M6 and M8
                         \
                          -> M7 -> reconciled public stop
```

Within M5, public canonical documentation precedes semantics, semantic MCP precedes its
lock decision, and public GraphQL documentation precedes consumers. Within M6 and M8,
public companion documentation precedes private implementation.
