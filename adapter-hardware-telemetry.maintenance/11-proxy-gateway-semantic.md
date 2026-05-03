# Adapter Hardware Telemetry Plan 02: Proxy, Gateway, Semantic Model

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `bb4d05e2a963dd76ac2185183eb4640c3b2e05fae1157046457f47ee8570911d`

Depends on: Plan 01 (data sources, transport API). Transport `RequestInfo` and
parsed types are the foundation for proxy caching and gateway semantic modeling.

Scope: Proxy identity caching with singleflight semantics and 4-state cache
machine, gateway AdapterHardwareInfo semantic model with wire-observable gating,
Prometheus metrics (48 series budget), MCP tool with standard envelope, GraphQL
schema (non-null contract), Portal panel, and adapterStatus enrichment with
separated transport/INFO health concerns.

Idempotence contract: Reapplying this chunk must not create duplicate cache
entries, duplicate Prometheus metric families, or duplicate GraphQL types.

Falsifiability gate: A review fails this chunk if proxy caching policy is
ambiguous for any INFO ID, the cache state machine has missing transitions,
singleflight semantics are undefined for edge cases, Prometheus metric
names/types are undefined or series budget is exceeded, GraphQL schema has
untyped fields or uses nullable root query, MCP tool contract is incomplete or
lacks standard envelope, or any gating logic references firmware dates instead
of wire-observable evidence.

Coverage: Sections 3-4 from the source plan (Proxy, Gateway).

---

## 3. Layer 2: Adapter Proxy

### 3A. Current behavior

The proxy currently forwards INFO requests verbatim to upstream and routes responses to the requesting session only (`deliverPendingInfo`). It does not cache or interpret INFO data.

### 3B. Required changes

**Identity caching:** On startup (after INIT), the proxy queries IDs 0x00, 0x01, 0x02 from upstream and caches the raw responses. Subsequent downstream INFO requests for these IDs are served from cache without upstream round-trip.

**Telemetry passthrough:** IDs 0x03-0x07 are always forwarded to upstream. The proxy does not cache volatile telemetry.

**Cache invalidation:** Identity cache is cleared on upstream RESETTED events (adapter reboot/reconnect). The proxy re-queries identity IDs after reconnect.

**ID 0x06 passthrough:** ID 0x06 (Reset Info) is NOT cached — it is always forwarded to upstream (see Section 3F).

### 3C. No new REST endpoint

The proxy exposes adapter info only via the enhanced protocol INFO command, not via a new REST API. This keeps the proxy's role as a transparent protocol multiplexer. The gateway is the semantic layer that exposes structured data.

### 3D. Multi-client INFO serialization (singleflight)

**Current bug:** The proxy's `pendingInfo` field is overwritten by each new INFO request (`server.go:793`), meaning a second concurrent request silently hijacks the response delivery. This is a pre-existing defect.

**Required fix (part of this plan):** Implement singleflight semantics for INFO requests:
- If a request for the same INFO ID is already in-flight, the second caller waits for the in-flight response and receives a copy. No second upstream request is made.
- If a request for a different INFO ID arrives while another is in-flight, it is queued and executed after the current response completes (protocol limitation: new INFO request terminates previous).
- Maximum queue depth: 8 (reject with `ENHResErrorHost` if exceeded).

For cached identity IDs, the singleflight path is never reached because the cache serves immediately.

### 3E. Identity cache state machine

The proxy identity cache has four explicit states per ID:
- `cold`: no cached value, first request must go upstream
- `refreshing`: upstream query in-flight (startup prefetch or post-RESETTED requery)
- `valid`: cached value available, serve directly
- `invalidated`: upstream RESETTED received, cache cleared

State transitions:
- `cold -> refreshing`: startup INIT triggers prefetch
- `refreshing -> valid`: successful upstream response cached
- `refreshing -> cold`: upstream query failed (error/timeout)
- `valid -> invalidated`: upstream RESETTED event
- `invalidated -> refreshing`: re-query triggered after RESETTED

On proxy startup, all identity IDs start in `cold` state.

Client request behavior per state:
- `cold`: forward to upstream (joins singleflight if one is in-flight)
- `refreshing`: wait for in-flight upstream query via singleflight, then serve result
- `valid`: serve from cache immediately, no upstream round-trip
- `invalidated`: trigger re-query (transitions to `refreshing`), wait for result

### 3F. ID 0x06 policy (unambiguous)

ID 0x06 (Reset Info) is classified as **telemetry passthrough**, not identity-cached. The `reset_cause` field is semi-static but `restart_count` changes within a power cycle. The simplicity of always forwarding 0x06 to upstream outweighs the minor cost of one extra round-trip. This avoids the ambiguity of partial caching.

### 3G. No proxy metrics

The proxy is intentionally lean. No Prometheus metrics added. Gateway owns all observability.

## 4. Layer 3: Gateway Semantic Model

### 4A. AdapterHardwareInfo struct

```go
type AdapterHardwareInfo struct {
    // Identity (static per session)
    FirmwareVersion    string    // "major.minor" from INFO 0x00
    FirmwareChecksum   string    // hex, empty if version_len < 5
    BootloaderVersion  string    // "major.minor", empty if version_len < 8
    BootloaderChecksum string    // hex, empty if version_len < 8
    HardwareID         string    // hex-encoded 9-byte ID from INFO 0x01
    HardwareConfig     string    // hex-encoded config from INFO 0x02
    Features           byte
    Jumpers            byte
    JumperFlags        []string  // human-readable: ["enhanced", "wifi", "v3.1", ...]
    IsWiFi             bool
    IsEthernet         bool

    // Telemetry (refreshed periodically)
    TemperatureC       *float64  // nil if unavailable
    SupplyVoltageMV    *int      // nil if unavailable or 0
    BusVoltageMaxDV    *int      // nil if unavailable or 0, unit: 0.1V
    BusVoltageMinDV    *int      // nil if unavailable or 0, unit: 0.1V
    ResetCause         *string   // nil if version_len < 8
    ResetCauseCode     *byte
    RestartCount       *byte     // nil if version_len < 8
    WiFiRSSIDBm        *int      // nil if not WiFi or version_len < 5

    // Metadata
    LastIdentityQuery  time.Time
    LastTelemetryQuery time.Time
    VersionResponseLen int       // wire-observable: 2, 5, or 8
    InfoSupported      bool      // feature bit 0
}
```

**Gating invariant:** All capability gating uses `VersionResponseLen` and `IsWiFi`, never calendar-date constants. `FirmwareDate` is removed from the API contract. If a human-readable firmware date is needed for display, it may be derived externally but MUST NOT be used for gating decisions in any layer.

### 4B. Query strategy

**On connect (after INIT):**
1. Query INFO 0x00 (version) — parse to determine firmware capabilities
2. Query INFO 0x01 (hardware ID)
3. Query INFO 0x02 (hardware config)
4. Query INFO 0x06 (reset info) if supported
5. Query INFO 0x07 (WiFi RSSI) if supported
6. Query INFO 0x03 (temperature)
7. Query INFO 0x04 (supply voltage)
8. Query INFO 0x05 (bus voltage)

**Periodic telemetry refresh:**
- Default interval: `30s`
- Configurable range: `10s..5m`
- Queries: 0x03, 0x04, 0x05, and conditionally 0x06, 0x07
- Must not compete with active bus operations — telemetry queries use the same bus mutex and are lower priority than semantic reads/writes
- Telemetry queries are scheduled in the existing semantic poller loop, not a separate goroutine

**On adapter reset (RESETTED):**
- Clear cached identity
- Re-query all IDs in connect sequence

### 4C. Prometheus metrics

All metrics use the `ebus_adapter_` prefix. Series budget for this feature: `48` max.

| Metric | Type | Labels | Max Series | Description |
|--------|------|--------|-----------|-------------|
| `ebus_adapter_temperature_celsius` | Gauge | — | 1 | Adapter board temperature |
| `ebus_adapter_supply_voltage_millivolts` | Gauge | — | 1 | Adapter supply rail voltage |
| `ebus_adapter_bus_voltage_max_decivolts` | Gauge | — | 1 | eBUS maximum voltage (0.1V units) |
| `ebus_adapter_bus_voltage_min_decivolts` | Gauge | — | 1 | eBUS minimum voltage (0.1V units) |
| `ebus_adapter_wifi_rssi_dbm` | Gauge | — | 1 | WiFi signal strength |
| `ebus_adapter_restart_count` | Gauge | — | 1 | Restart count within current power cycle |
| `ebus_adapter_reset_cause` | Gauge | `cause` | 7 | One-hot gauge over reset cause enum |
| `ebus_adapter_info_queries_total` | Counter | `id`, `outcome` | 32 | INFO query attempts |
| `ebus_adapter_info_supported` | Gauge | — | 1 | 0/1 whether adapter supports INFO |
| `ebus_adapter_info_health` | Gauge | — | 1 | 0/1 whether latest INFO poll succeeded |

Label domains:
- `cause`: `power_on`, `brown_out`, `watchdog`, `clear`, `external_reset`, `stack_overflow`, `memory_failure` (7)
- `id`: `version`, `hw_id`, `hw_config`, `temperature`, `supply_voltage`, `bus_voltage`, `reset_info`, `wifi_rssi` (8)
- `outcome`: `success`, `error`, `timeout`, `unsupported` (4)

Maximum series (worst case): `6 + 7 + 32 + 1 + 1 = 47`. With lazy creation (only observed combinations), steady-state is ~20 series. Budget is `48` to allow headroom.

### 4D. MCP tool

```
Tool: ebus.v1.adapter.info.get
Description: Get eBUS adapter hardware identity and telemetry.
Parameters: none
Returns: standard meta/data/error envelope per gateway MCP conventions
```

The tool uses the same `meta/data/error` response envelope as all other `ebus.v1.*` tools (see `server.go` envelope pattern). The `data` field contains the AdapterHardwareInfo JSON. When INFO is not supported, the tool returns a successful response with `data.infoSupported = false` and all telemetry fields null — it does not return an error.

MCP-GraphQL parity: every field in the MCP response must have a corresponding GraphQL field and vice versa. Parity tests are mandatory per AGENTS.md.

### 4E. GraphQL schema

```graphql
type AdapterHardwareInfo {
  firmwareVersion: String!
  firmwareChecksum: String
  bootloaderVersion: String
  bootloaderChecksum: String
  hardwareId: String!
  hardwareConfig: String
  features: Int!
  jumpers: Int!
  jumperFlags: [String!]!
  isWifi: Boolean!
  isEthernet: Boolean!

  temperatureCelsius: Float
  supplyVoltageMillivolts: Int
  busVoltageMaxDecivolts: Int
  busVoltageMinDecivolts: Int
  resetCause: String
  resetCauseCode: Int
  restartCount: Int
  wifiRssiDbm: Int

  lastIdentityQuery: String
  lastTelemetryQuery: String
  versionResponseLen: Int!
  infoSupported: Boolean!
}

extend type Query {
  adapterHardwareInfo: AdapterHardwareInfo!
}
```

The query always returns a non-null `AdapterHardwareInfo` object. When INFO is not supported (non-enhanced transport or feature bit 0 not set), the object has `infoSupported = false`, identity fields set to empty/zero, and all telemetry fields null. This avoids the problem of `null` making `infoSupported` unreachable in client code.

### 4F. Portal UI

Add an "Adapter Hardware" panel to the existing Portal dashboard:
- Identity section: firmware version, bootloader, hardware ID, jumper flags
- Telemetry section: temperature, voltages, WiFi RSSI, reset info
- Auto-refresh aligned with telemetry poll interval
- Consumes the `/graphql` endpoint (`adapterHardwareInfo` query)

### 4G. Existing adapterStatus enrichment

The existing `adapterStatus` GraphQL field and MCP `runtime.status.get` tool currently return empty firmware version. This plan populates:
- `adapterStatus.firmwareVersion` from INFO 0x00 parsed version string

Transport connectivity status (`adapterStatus.status`) is NOT changed by this plan. Transport health and INFO capability are separate concerns:
- Transport status reflects TCP/serial connection health (existing behavior)
- INFO health is exposed as the separate `ebus_adapter_info_health` Prometheus metric and the `infoSupported` field in `AdapterHardwareInfo`

This separation prevents false "degraded" states for adapters that are connected but don't support INFO, or for transient INFO poll failures on an otherwise healthy connection.
