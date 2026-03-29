# Adapter Hardware Telemetry — Status

## Current State

- **Plan state:** Done — all milestones merged on main across all 5 target repos
- **Closed on:** 2026-03-29

## Adversarial Review Summary

### Plan convergence (pre-implementation)
5 rounds of adversarial review via Codex gpt-5.4 (xhigh reasoning):
- R1: 10 findings (2 CRITICAL, 6 HIGH, 2 MEDIUM) — all addressed
- R2: 8 findings (3 CRITICAL, 4 HIGH, 1 MEDIUM) — all addressed
- R3: 2 findings (1 CRITICAL, 1 HIGH) — all addressed
- R4: 1 finding (1 HIGH) — addressed
- R5: CONVERGED — no findings

### Implementation review (post-merge)

**ebusgo (Codex gpt-5.4):** 4 findings
- HIGH: `RawTransportOp` callbacks un-cancelable once started — bounded by PR #121 chatter timeout
- MEDIUM: queue priority bypass, timeout drops buffered chatter
- LOW: re-entry deadlock risk (comment-guarded)

**Gateway (Claude Opus 4.6 manual):** 20 findings, 0 CRITICAL
- HIGH #3 (temperature scaling): FALSE POSITIVE — live MCP data confirms firmware returns degrees C directly
- HIGH #9 (NonNull empty strings): MEDIUM — transient at bootstrap (<1s), no crash
- MEDIUM: duplicate constructor code, dual error path, mutex contention (bounded by copy-on-write), clone duplication, type inconsistency across layers, expvar test interference
- LOW: stale telemetry, nil provider (safe), rebootstrap scope, double clone, byte/int types, torn portal snapshot, no jitter, no per-query timeout

**Blast-radius (out-of-order execution):** All 5 checks OK
1. go.mod pins: correct across gateway and proxy
2. GraphQL schema: 23/23 fields match between HA and gateway
3. Proxy bypass: INFO traverses proxy correctly (ENH frame level)
4. Prometheus naming: `ebus_adapter_` prefix consistent
5. Unsupported adapters: multi-layer defense (type assertion, capability gating, nil handling)

### Runtime verification (2026-03-29)
- MCP `adapter_info.get`: all fields populated (temp 25°C, supply 5105mV, bus 20.0V/9.8V, WiFi, power_on)
- MCP snapshot: 7 planes consistent (adapter_info, zones, dhw, boiler_status, system, circuits, runtime_status)
- Portal Adapter panel: Identity + Telemetry tables rendered correctly, auto-refresh active
- Portal Bus panel: passive observability available, feature flags clean
- Gateway: LIVE_READY, adapter running, daemon running

## Blockers

None — plan is closed.

## History

| Date | Event |
|------|-------|
| 2026-03-10 | Plan created, canonical + split authored |
| 2026-03-10 | Adversarial R1-R5 completed, CONVERGED |
| 2026-03-29 | M1: `ebusgo#119` merged (transport INFO API); `#121` follow-up (chatter-bounded timeout) |
| 2026-03-29 | M5: `ha-integration#169` merged (adapter enrichment + diagnostics); `#176`, `#178` follow-ups |
| 2026-03-29 | M3/M4: `ebusgateway#440` merged (semantic model, MCP, GraphQL, Portal); `#442` merged (GW-05 live status) |
| 2026-03-29 | M2: `ebus-adapter-proxy#83` merged (identity cache + RESETTED invalidation) |
| 2026-03-29 | M0: `docs-ebus#232` merged (ENH INFO ID reference document) |
| 2026-03-29 | Adversarial + blast-radius + runtime review completed; plan closed |
