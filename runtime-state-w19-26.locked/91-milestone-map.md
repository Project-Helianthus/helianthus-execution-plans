# Milestone Map — Runtime State File

Source: [00-canonical.md](./00-canonical.md)

Topology nodes per milestone × repo. Used by `cruise-topology` for
DAG validation and `cruise-state-sync` for run-time tracking.

| Milestone | Repo | Topology ID | Depends on |
|-----------|------|-------------|------------|
| M0_PLAN_LOCK | helianthus-execution-plans | RTS-00 | (root) |
| M0_DOC_GATE | helianthus-docs-ebus | RTS-01 | RTS-00 |
| M0A_TRANSPORT_BASELINE | helianthus-ebusgateway | RTS-02 | RTS-01 |
| M1_TDD_RED_GATEWAY | helianthus-ebusgateway | RTS-03 | RTS-01 |
| M1_TDD_RED_ADDON | helianthus-ha-addon | RTS-04 | RTS-01 |
| M2_GATEWAY_LOADER | helianthus-ebusgateway | RTS-05 | RTS-03 |
| M3_GATEWAY_PERSISTER | helianthus-ebusgateway | RTS-06 | RTS-05 |
| M4_JOINER_HINT | helianthus-ebusgateway | RTS-07 | RTS-06 |
| M5_ADDRESS_TABLE_REVALIDATE | helianthus-ebusgateway | RTS-08 | RTS-07 |
| M6_HA_ADDON_MIGRATION | helianthus-ha-addon | RTS-09 | RTS-04, RTS-05 |
| M7_LIVE_VALIDATION | helianthus-ebusgateway | RTS-10 | RTS-08, RTS-09 |
| M8_TRANSPORT_VERIFY | helianthus-ebusgateway | RTS-11 | RTS-08 |

## DAG (DOT-style)

```
RTS-00 → RTS-01
RTS-01 → RTS-02
RTS-01 → RTS-03 → RTS-05 → RTS-06 → RTS-07 → RTS-08 → RTS-10
RTS-01 → RTS-04 → RTS-09 → RTS-10
RTS-08 → RTS-11
RTS-05 ← RTS-09  (cross-edge: addon depends on loader contract)
```

## Parallelization opportunities

- RTS-02 (transport-matrix baseline) parallel with RTS-03/RTS-04 (RED tests).
- RTS-03 lane (gateway impl: M1→M2→M3→M4→M5) and RTS-04 lane (addon impl:
  M1_addon→M6) are independent until they fan in to RTS-10 (M7 live).
- RTS-11 (M8 transport verify) parallel with RTS-10 (M7 live) once RTS-08
  (M5) is merged.

## Critical path

```
M0_PLAN_LOCK → M0_DOC_GATE → M1_TDD_RED_GATEWAY → M2_LOADER →
M3_PERSISTER → M4_JOINER_HINT → M5_REVALIDATE → M7_LIVE_VALIDATION
```

8 milestones, gateway-heavy. Add-on lane (M1_TDD_RED_ADDON → M6) joins at
M7 but does not gate the gateway-side critical path until then.
