# Adapter Hardware Telemetry — Issue Map

## Issue Catalog

Backfill snapshot: `helianthus-ebusgo#121` merged, `helianthus-ebus-adapter-proxy#83`
still open, `helianthus-ebusgateway#442` merged and closed `GW-05`,
`helianthus-ha-integration#169` and `#178` are both merged, and docs backfill
is still pending.

| Issue ID | Repo | Milestone | Title | Status |
|----------|------|-----------|-------|--------|
| ISSUE-DOC-01 | helianthus-docs-ebus | M0 | Enhanced protocol INFO reference document | open |
| ISSUE-GO-01 | helianthus-ebusgo | M1 | Transport INFO request/response API | merged |
| ISSUE-GO-02 | helianthus-ebusgo | M1 | Parsed adapter info types and version gating | merged |
| ISSUE-PROXY-01 | helianthus-ebus-adapter-proxy | M2 | Identity INFO caching on startup | open |
| ISSUE-PROXY-02 | helianthus-ebus-adapter-proxy | M2 | Telemetry INFO passthrough + RESETTED invalidation | open |
| ISSUE-GW-01 | helianthus-ebusgateway | M3 | AdapterHardwareInfo semantic model | merged |
| ISSUE-GW-02 | helianthus-ebusgateway | M3 | Adapter telemetry Prometheus metrics | merged |
| ISSUE-GW-03 | helianthus-ebusgateway | M3 | adapter.info.get MCP tool | merged |
| ISSUE-GW-04 | helianthus-ebusgateway | M3 | adapterHardwareInfo GraphQL query | merged |
| ISSUE-GW-05 | helianthus-ebusgateway | M3 | Populate adapterStatus.firmwareVersion | merged |
| ISSUE-GW-06 | helianthus-ebusgateway | M4 | Portal Adapter Hardware panel | merged |
| ISSUE-HA-01 | helianthus-ha-integration | M5 | Adapter device enrichment (sw_version, hw_version, serial) | merged |
| ISSUE-HA-02 | helianthus-ha-integration | M5 | Adapter diagnostic sensors | merged |

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

## GitHub Issue Tracking

Issues will be created on each target repo as milestones are activated.
Issue titles follow the pattern: `[AHT-{ID}] {Title}` where AHT = Adapter Hardware Telemetry.
