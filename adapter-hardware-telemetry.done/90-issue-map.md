# Adapter Hardware Telemetry — Issue Map (Closed)

## Issue Catalog

All milestones closed. Final backfill 2026-03-29.

| Issue ID | Repo | Milestone | Title | Status | Linked execution |
|----------|------|-----------|-------|--------|------------------|
| ISSUE-DOC-01 | helianthus-docs-ebus | M0 | Enhanced protocol INFO reference document | merged | issue #231, PR #232, merge commit `a788415` |
| ISSUE-GO-01 | helianthus-ebusgo | M1 | Transport INFO request/response API | merged | issue #117, PR #119, merge commit `c61c8fb` |
| ISSUE-GO-02 | helianthus-ebusgo | M1 | Parsed adapter info types and version gating | merged | issue #117, PR #119 (bundled with GO-01); follow-up PR #121 (`e5d3f66`) |
| ISSUE-PROXY-01 | helianthus-ebus-adapter-proxy | M2 | Identity INFO caching on startup | merged | issue #82, PR #83, merge commit `0007894` |
| ISSUE-PROXY-02 | helianthus-ebus-adapter-proxy | M2 | Telemetry INFO passthrough + RESETTED invalidation | merged | issue #82, PR #83 (bundled with PROXY-01) |
| ISSUE-GW-01 | helianthus-ebusgateway | M3 | AdapterHardwareInfo semantic model | merged | issue #383, PR #440, merge commit `becf3b5` |
| ISSUE-GW-02 | helianthus-ebusgateway | M3 | Adapter telemetry Prometheus metrics | merged | issue #383, PR #440 (bundled) |
| ISSUE-GW-03 | helianthus-ebusgateway | M3 | adapter.info.get MCP tool | merged | issue #383, PR #440 (bundled) |
| ISSUE-GW-04 | helianthus-ebusgateway | M3 | adapterHardwareInfo GraphQL query | merged | issue #383, PR #440 (bundled) |
| ISSUE-GW-05 | helianthus-ebusgateway | M3 | Populate adapterStatus.firmwareVersion | merged | issue #383, PR #442, merge commit `ba0def9` |
| ISSUE-GW-06 | helianthus-ebusgateway | M4 | Portal Adapter Hardware panel | merged | issue #383, PR #440 (bundled with M3) |
| ISSUE-HA-01 | helianthus-ha-integration | M5 | Adapter device enrichment (sw_version, hw_version, serial) | merged | issue #168, PR #169, merge commit `e983661` |
| ISSUE-HA-02 | helianthus-ha-integration | M5 | Adapter diagnostic sensors | merged | issue #168, PR #169 (bundled); follow-up PR #176, #178 |

## Dependency Graph

```
ISSUE-DOC-01 ─────────────────────────────────────┐
                                                   │
ISSUE-GO-01 ──┬── ISSUE-PROXY-01 ──┬── ISSUE-GW-01 ──┬── ISSUE-GW-06
ISSUE-GO-02 ──┘   ISSUE-PROXY-02 ──┘   ISSUE-GW-02   │   ISSUE-HA-01
                                        ISSUE-GW-03   │   ISSUE-HA-02
                                        ISSUE-GW-04 ──┘
                                        ISSUE-GW-05
```

## Notes

- Execution order deviated from plan: M1 → M3/M4 → M5 → M2 → M0 (plan specified M0 → M1 → M2 → M3 → M4 → M5)
- No contract mismatches from out-of-order execution (blast-radius review: all 5 checks OK)
- Gateway M3/M4 bundled into single PR #440; proxy M2 bundled into single PR #83
- HA M5 landed before gateway M3 was merged (consumed draft API shape that proved stable)
