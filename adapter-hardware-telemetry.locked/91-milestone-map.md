# Adapter Hardware Telemetry — Milestone Map

## Milestone Sequence

| Milestone | Repo | Issues | Description | Dependencies |
|-----------|------|--------|-------------|-------------|
| M0 | helianthus-docs-ebus | ISSUE-DOC-01 | Enhanced protocol INFO reference document | None |
| M1 | helianthus-ebusgo | ISSUE-GO-01, ISSUE-GO-02 | Transport INFO API and parsed types | None (parallel with M0) |
| M2 | helianthus-ebus-adapter-proxy | ISSUE-PROXY-01, ISSUE-PROXY-02 | Proxy identity caching and passthrough | M1 |
| M3 | helianthus-ebusgateway | ISSUE-GW-01..05 | Semantic model, Prometheus, MCP, GraphQL | M1, M2 |
| M4 | helianthus-ebusgateway | ISSUE-GW-06 | Portal Adapter Hardware panel | M3 |
| M5 | helianthus-ha-integration | ISSUE-HA-01, ISSUE-HA-02 | HA device enrichment and diagnostic sensors | M3 |

## Parallelization

```
M0 ─────────┐
             ├── M2 ── M3 ──┬── M4
M1 ─────────┘               └── M5
```

M0 and M1 are fully parallel (docs and Go types have no code dependency).
M4 and M5 are parallel (Portal and HA consume the same GraphQL).

## Estimated Complexity

| Milestone | Complexity | Routing |
|-----------|-----------|---------|
| M0 | 3 | Co-Pilot or Orchestrator |
| M1 | 6 | Orchestrator |
| M2 | 5 | Orchestrator |
| M3 | 8 | Orchestrator |
| M4 | 4 | Co-Pilot or Orchestrator |
| M5 | 5 | Orchestrator |

## Gate Requirements

Each milestone requires:
- All issues merged with squash+merge
- CI passing (local CI gate)
- Doc-gate: documentation updated before or alongside code
- Transport-gate: no transport-level regressions
