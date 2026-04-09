# Gateway-Embedded Proxy 04: Migration, Rollback, and HA Addon

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0bc9965756418f65ae4c709b90ff08d152612e2c9894ca8e684e8ba36e0cd8a8`

Depends on: [00-canonical.md](./00-canonical.md),
[11-gateway-integration-paths.md](./11-gateway-integration-paths.md),
[12-external-proxy-endpoint.md](./12-external-proxy-endpoint.md).

Scope: HA addon configuration changes, migration path (proxy-based to
adapter-direct), rollback contract (adapter-direct to proxy-based), scope
coordination with the proxy-wire-semantics-fidelity plan. Covers milestone M4
and canonical Sections 8-10.

Idempotence contract: Declarative-only. Reapplying this chunk must not modify
addon config schemas, create duplicate config knobs, or weaken rollback
guarantees.

Falsifiability gate: Review fails this chunk if: addon cannot start in both
modes (adapter-direct and proxy-based) from config alone, rollback contract
is absent, or scope overlap with proxy plan is claimed.

Coverage: Canonical Section 3 (M4), Sections 8-10.

## 1. M4: HA Addon + Migration

Repos: `helianthus-ha-addon`, `helianthus-docs-ebus`

### 1.1 Addon Config Schema Changes

New options in `config.json`:

```json
{
  "adapter_direct_enabled": false,
  "adapter_direct_address": ""
}
```

- `adapter_direct_enabled` (bool, default `false`): when `true`, the gateway
  starts with `--adapter-direct` and connects directly to the adapter. The
  standalone proxy process is not spawned.
- `adapter_direct_address` (string): adapter endpoint, e.g. `boiler.local:9999`.
  Required when `adapter_direct_enabled` is `true`.

Existing options preserved:
- `adapter_proxy_enabled`, `adapter_proxy_upstream`, `adapter_proxy_port`:
  used when `adapter_direct_enabled` is `false` (backward compatible).

When both `adapter_direct_enabled` and `adapter_proxy_port` are set:
- Gateway starts with `--adapter-direct` AND `--proxy-listen` (embedded proxy
  endpoint for ebusd coexistence).

### 1.2 Startup Script Logic

```
if adapter_direct_enabled:
    gateway_args += "--adapter-direct enh://${adapter_direct_address}"
    if adapter_proxy_port:
        gateway_args += "--proxy-listen :${adapter_proxy_port}"
    # Do NOT start proxy process
else:
    if adapter_proxy_enabled:
        start proxy process with adapter_proxy_upstream
        gateway_args += "--transport enh://localhost:${adapter_proxy_port}"
    else:
        gateway_args += configured transport flags
```

### 1.3 Falsifiability

Review fails if:
- Addon cannot start in adapter-direct mode from config alone
- Addon cannot start in proxy-based mode from config alone
- Setting `adapter_direct_enabled: false` does not restore proxy-based behavior

## 2. Migration Path

### 2.1 Forward Migration (Proxy-Based to Adapter-Direct)

Prerequisites:
- Gateway version includes M2 (active/passive integration) and M3 (proxy
  endpoint) support.
- Addon version includes M4 config schema.

Steps:
1. Edit addon configuration:
   - Set `adapter_direct_enabled: true`
   - Set `adapter_direct_address: "boiler.local:9999"` (or actual adapter address)
   - Optionally set `adapter_proxy_port: 19001` for ebusd coexistence
2. Restart addon (`ha addons restart local_helianthus`)
3. Verify gateway log shows `adapter-direct` transport mode
4. Verify active polling functions (check MCP tools, e.g. `zones.get`)
5. Verify passive observation functions (check observe-first coverage)
6. If ebusd coexistence enabled, verify ebusd connects to proxy endpoint

### 2.2 Standalone Gateway Migration (Non-Addon)

Steps:
1. Stop gateway process
2. Change gateway startup command:
   - Replace: `--transport enh --network tcp --address localhost:19001`
   - With: `--adapter-direct enh://boiler.local:9999`
   - Optionally add: `--proxy-listen :19001`
3. If proxy endpoint is enabled, reconfigure ebusd to connect to gateway's
   proxy port instead of standalone proxy
4. Stop standalone proxy process (no longer needed)
5. Start gateway with new flags

### 2.3 Zero-Downtime Note

Zero-downtime migration is NOT required. Addon/gateway restart is acceptable.
The eBUS bus operates independently — restarting the gateway does not affect
the physical bus or other masters (ebusd, VRC700).

## 3. Rollback Contract

### 3.1 Config-Level Rollback

At any point after migration:
1. Set `adapter_direct_enabled: false` in addon config
2. Ensure `adapter_proxy_enabled: true` and proxy upstream are configured
3. Restart addon
4. Gateway reverts to proxy-based topology
5. Standalone proxy process is spawned as before
6. ebusd reconnects to standalone proxy

### 3.2 Code-Level Rollback

No code rollback is needed. Adapter-direct is additive:
- Existing transport modes (enh, ens, ebusd-tcp) are unchanged
- `--adapter-direct` flag activates the new path; omitting it reverts
- Multiplexer code in `internal/adaptermux/` is dormant when not activated

### 3.3 Per-Milestone Rollback

| Milestone | Rollback impact |
|-----------|----------------|
| M0 | Plan only. No code to revert. |
| M1 | Multiplexer code exists but is not wired to startup. Dormant. |
| M2 | `--adapter-direct` flag exists but defaults off. Omit to revert. |
| M3 | `--proxy-listen` flag exists but defaults off. Omit to revert. |
| M4 | Addon config flag controls topology. Set `false` to revert. |
| M5 | Matrix tests are documentation. No runtime impact. |

## 4. Scope Coordination with Proxy Plan

### 4.1 No Overlap

The `proxy-wire-semantics-fidelity` plan covers standalone proxy improvements.
This plan covers the gateway-embedded multiplexer. Scope is disjoint:

| Aspect | Proxy Plan | This Plan |
|--------|-----------|-----------|
| Target repo | `helianthus-ebus-adapter-proxy` | `helianthus-ebusgateway` |
| Code location | `internal/adapterproxy/` | `internal/adaptermux/` |
| Matrix IDs | PX01..PX12 | AD01..AD12 |
| Owner model | N-session lowest-address | 2-class gateway-priority |
| Product status | Standalone product (unchanged) | Gateway enhancement |
| Target emulation | Yes (M4) | No |
| UDP-plain | Yes | No |

### 4.2 Shared Knowledge

The embedded multiplexer's wire phase tracker (M1) is informed by the proxy's
minimal direct-mode phase tracker (proxy M3). The arbitration model is informed
by the proxy's boundary-based arbitration (proxy M2). These are design
influences, not code extractions — the implementations are separate.

### 4.3 Coexistence

Both products can coexist:
- Standalone proxy serves users without the gateway
- Embedded multiplexer serves gateway users who want direct adapter access
- A user can run the standalone proxy AND the gateway (in proxy-based mode)
  simultaneously — existing behavior, unchanged
- A user CANNOT run the standalone proxy and the gateway in adapter-direct
  mode simultaneously (they would compete for the single adapter connection)
