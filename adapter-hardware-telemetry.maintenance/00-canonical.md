# Adapter Hardware Telemetry & Identity Propagation

Revision: `v1.0-converged`
Date: `2026-03-10`
Status: `Maintenance`
Maintenance since: `2026-03-29`

Lifecycle note: this document is the converged locked design plus archival
execution record. All primary milestones are merged; no blocking follow-up
remains for this plan.

## Summary

This plan implements end-to-end extraction, caching, semantic modeling, and consumer exposure of eBUS adapter hardware telemetry and identity data sourced from the ebusd enhanced protocol INFO commands (IDs 0x00–0x07).

The data splits into two categories:
- **Identity (static):** firmware version, hardware ID, hardware config, jumper settings, bootloader version — queried once on connect, cached indefinitely per adapter session.
- **Telemetry (volatile):** hardware temperature, supply voltage, bus voltage min/max, reset cause/count, WiFi RSSI — polled periodically, exposed as Prometheus metrics and semantic state.

All data is version-gated per wire-observable evidence from the INFO 0x00 response (response length and jumper bits), not magic firmware date constants.

The implementation spans six layers in dependency order:
1. `helianthus-docs-ebus` — enhanced protocol INFO reference, version-gate matrix
2. `helianthus-ebusgo` — transport-layer INFO request/response API
3. `helianthus-ebus-adapter-proxy` — proxy INFO caching + passthrough policy
4. `helianthus-ebusgateway` — semantic model, Prometheus metrics, MCP, GraphQL, Portal
5. `helianthus-ha-integration` — HA device enrichment, diagnostic sensors
6. `helianthus-ha-addon` — no code change expected (passthrough container)

### Relationship to Observe-First Observability

The observe-first bus observability plan owns passive bus traffic metrics and the `ebus_` Prometheus namespace for bus-level counters. This plan owns adapter-hardware-level telemetry under a new `ebus_adapter_` metric prefix. The two are complementary:
- Observe-first: bus traffic, frame counters, shadow cache, dedup, warmup
- This plan: adapter hardware health (voltage, temperature, WiFi, resets, identity)

Both share the gateway `/metrics` endpoint and the same bounded-series discipline.

## 1. Data Sources: Enhanced Protocol INFO IDs

All INFO queries use the enhanced protocol `<INFO>` command (`ENHReqInfo`/`ENHResInfo`, command symbol 0x3). The adapter responds with `<INFO> <length> <data_0> ... <data_N-1>`.

### 1A. Identity IDs (static per adapter session)

| ID | Name | Response Length | Fields | Version Gate |
|----|------|---------------|--------|-------------|
| 0x00 | Version | 2/5/8 bytes | `version`, `features`, `checksum` (len>=5), `jumpers` (len>=5), `bootloader_version`, `bootloader_checksum` (len==8) | All (length varies by firmware generation) |
| 0x01 | Hardware ID | 9 bytes | 9-byte hardware identifier | All |
| 0x02 | Hardware Config | 3 or 8 bytes | chip-specific config, arbitration delay (bits 0-5 of byte 2, steps of 10µs) | All (length varies by chip) |

### 1B. Telemetry IDs (volatile, periodic polling)

| ID | Name | Response Length | Fields | Unit | Version Gate |
|----|------|---------------|--------|------|-------------|
| 0x03 | Temperature | 2 bytes | `temp_H`, `temp_L` | °C (uint16 big-endian) | All |
| 0x04 | Supply Voltage | 2 bytes | `millivolt_H`, `millivolt_L` | mV (uint16 big-endian, 0=unknown) | All |
| 0x05 | Bus Voltage | 2 bytes | `voltage_max`, `voltage_min` | 0.1V per byte (0=unknown) | All |
| 0x06 | Reset Info | 2 bytes | `reset_cause` (enum), `restart_count` | cause: 1-7, count: uint8 | version_len == 8 |
| 0x07 | WiFi RSSI | 1 byte | `rssi` | dBm (int8 signed, 0=unknown) | version_len >= 5 AND jumper bit 0x08 |

### 1C. Version response length gating (wire-observable)

Version gating is determined entirely from the INFO 0x00 response length, not from firmware date constants. The response length is the first byte returned in the INFO response and is directly observable on the wire:

```
version_len == 2:  legacy firmware (version, features only)
version_len == 5:  mid-generation (+ checksum_H, checksum_L, jumpers)
version_len == 8:  modern firmware (+ bootloader_version, bootloader_checksum_H, bootloader_checksum_L)
```

Capability inference from version_len:
- `version_len >= 5`: jumper bits available → WiFi/Ethernet flags derivable
- `version_len >= 8`: bootloader info available, reset info (ID 0x06) supported
- WiFi RSSI (ID 0x07): requires `version_len >= 5` AND `jumpers & 0x08`

This replaces all references to "firmware_date" thresholds. The wire-observable response length is the sole gating signal. No version-byte-to-date lookup table is needed.

### 1D. Jumper bit definitions

| Bit | Meaning |
|-----|---------|
| 0x01 | Enhanced mode enabled |
| 0x02 | High-speed mode |
| 0x04 | Ethernet interface |
| 0x08 | WiFi interface |
| 0x10 | v3.1 hardware |
| 0x20 | Ignore hard jumpers (soft config) |

### 1E. Reset cause enum

| Value | Cause |
|-------|-------|
| 1 | Power-on |
| 2 | Brown-out |
| 3 | Watchdog |
| 4 | Clear |
| 5 | External reset |
| 6 | Stack overflow |
| 7 | Memory failure |

### 1F. Feature bits

| Bit | Meaning |
|-----|---------|
| 0 | Additional INFO queries supported |
| 1 | Planned: full message sending (not implemented) |
| 2-7 | Reserved (TBD) |

### 1G. No undocumented INFO IDs

Source code analysis of ebusd `device_trans.cpp` (lines 542-651) confirms exactly 8 INFO IDs (0x00-0x07). The default/unknown handler at line 643 logs but does not parse. No HEAP, uptime, or flash metrics exist in the protocol. The adapter firmware lives in a separate repository (`john30/ebusd-esp`) and implements only these 8 IDs.

## 2. Layer 1: ebusgo Transport API

### 2A. New types

```go
// AdapterInfoID represents an enhanced protocol INFO query ID.
type AdapterInfoID byte

const (
    AdapterInfoVersion      AdapterInfoID = 0x00
    AdapterInfoHardwareID   AdapterInfoID = 0x01
    AdapterInfoHardwareConf AdapterInfoID = 0x02
    AdapterInfoTemperature  AdapterInfoID = 0x03
    AdapterInfoSupplyVoltage AdapterInfoID = 0x04
    AdapterInfoBusVoltage   AdapterInfoID = 0x05
    AdapterInfoResetInfo    AdapterInfoID = 0x06
    AdapterInfoWiFiRSSI     AdapterInfoID = 0x07
)
```

### 2B. New method on ENHTransport

```go
// RequestInfo sends an INFO request for the given ID and returns the raw
// response payload. The caller must hold no bus arbitration.
// Returns ErrInfoUnsupported if the adapter does not support INFO queries
// (feature bit 0 not set during INIT).
func (t *ENHTransport) RequestInfo(id AdapterInfoID) ([]byte, error)
```

Protocol flow:
1. Send `ENHReqInfo(byte(id))` encoded frame
2. Read first INFO response frame: `ENHResInfo(length)` — the data byte is the total response length N
3. Read N subsequent INFO data frames: each `ENHResInfo(data_byte)` carries one payload byte
4. Return the assembled N-byte payload

Edge cases:
- `readTimeout` expiry before complete response → return error, reset parser
- Unexpected command during INFO read → return error, queue unexpected frame
- INFO with length 0 → return empty slice, no error
- Concurrent INFO requests are not supported (protocol limitation: new INFO request terminates previous)

### 2C. Parsed response types

```go
type AdapterVersion struct {
    Version           byte
    Features          byte
    Checksum          uint16  // 0 if unavailable (version_len < 5)
    Jumpers           byte    // 0 if unavailable (version_len < 5)
    BootloaderVersion byte    // 0 if unavailable (version_len < 8)
    BootloaderChecksum uint16 // 0 if unavailable
    HasChecksum       bool
    HasBootloader     bool
    IsWiFi            bool    // jumpers & 0x08
    IsEthernet        bool    // jumpers & 0x04
    IsHighSpeed       bool    // jumpers & 0x02
    IsV31             bool    // jumpers & 0x10
    SupportsInfo      bool    // features & 0x01
}

type AdapterResetInfo struct {
    Cause        string // human-readable from enum
    CauseCode    byte
    RestartCount byte
}
```

Parse functions:
```go
func ParseAdapterVersion(data []byte) (AdapterVersion, error)
func ParseAdapterResetInfo(data []byte) (AdapterResetInfo, error)
```

### 2D. Feature-gate helper

```go
// SupportsInfoID returns whether the adapter firmware supports a given INFO ID
// based on wire-observable evidence from the version response.
func (v AdapterVersion) SupportsInfoID(id AdapterInfoID) bool
```

Rules (wire-observable, no magic dates):
- IDs 0x00-0x05: always supported when `SupportsInfo` (features bit 0) is set
- ID 0x06: requires `HasBootloader` (version_len == 8)
- ID 0x07: requires `HasChecksum` (version_len >= 5) AND `IsWiFi` (jumpers & 0x08)

### 2E. Transport exclusivity contract

`RequestInfo` is transport-exclusive: it must hold the same `readMu`+`writeMu` that protects `ReadByte`/`Write`/`StartArbitration`. While an INFO request/response exchange is in progress, no other transport operation may interleave. This is required because the ENH parser is shared state — interleaved `ENHResReceived` bytes during an INFO response would corrupt the parsed payload.

The caller (gateway telemetry poller) must acquire the bus mutex before calling `RequestInfo`, same as for any bus I/O. This is not a new constraint; it aligns with the existing arbitration model.

### 2F. Transport interface extension

The existing `Transport` interface in ebusgo is byte-oriented (`ReadByte`, `Write`). The INFO API is a separate opt-in interface:

```go
// InfoRequester is implemented by transports that support enhanced protocol INFO queries.
type InfoRequester interface {
    RequestInfo(id AdapterInfoID) ([]byte, error)
}
```

Gateway checks for this interface via type assertion. Plain TCP and UDP transports do not implement it.

### 2G. Test requirements

- Round-trip encode/decode for all 8 INFO IDs
- Timeout handling (partial response)
- Concurrent call rejection (must error if called while another INFO is in-flight)
- Feature-gate validation for IDs 0x06, 0x07
- Parser state integrity after INFO exchange
- **Interleaved traffic test**: verify that `ENHResReceived` bytes arriving during INFO response are detected as an error and do not corrupt payload
- **RESETTED during INFO**: verify parser reset and error propagation
- **Golden captures**: wire-format golden test vectors for all 8 IDs, derived from real ebusd-esp adapter captures

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
- `cold → refreshing`: startup INIT triggers prefetch
- `refreshing → valid`: successful upstream response cached
- `refreshing → cold`: upstream query failed (error/timeout)
- `valid → invalidated`: upstream RESETTED event
- `invalidated → refreshing`: re-query triggered after RESETTED

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

MCP↔GraphQL parity: every field in the MCP response must have a corresponding GraphQL field and vice versa. Parity tests are mandatory per AGENTS.md.

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
- `adapterStatus.firmwareVersion` → from INFO 0x00 parsed version string

Transport connectivity status (`adapterStatus.status`) is NOT changed by this plan. Transport health and INFO capability are separate concerns:
- Transport status reflects TCP/serial connection health (existing behavior)
- INFO health is exposed as the separate `ebus_adapter_info_health` Prometheus metric and the `infoSupported` field in `AdapterHardwareInfo`

This separation prevents false "degraded" states for adapters that are connected but don't support INFO, or for transient INFO poll failures on an otherwise healthy connection.

## 5. Layer 4: Home Assistant Integration

### 5A. Adapter device enrichment

The existing HA `Adapter` device (currently hardcoded `manufacturer="Helianthus"`, `model="eBUS Adapter"`) will be enriched:

```python
device_kwargs = {
    "manufacturer": "eBUS",  # or derive from HW ID if mappable
    "model": f"ebusd-esp ({hw_config})",
    "sw_version": firmware_version,
    "hw_version": hardware_id_hex,
    "serial_number": hardware_id_hex,  # HW ID serves as unique identifier
}
```

### 5B. New diagnostic sensors on Adapter device

| Entity | Device Class | Unit | State Class | Category |
|--------|-------------|------|-------------|----------|
| Adapter Temperature | `temperature` | °C | `measurement` | `diagnostic` |
| Adapter Supply Voltage | `voltage` | mV | `measurement` | `diagnostic` |
| eBUS Voltage Max | `voltage` | V (converted from 0.1V) | `measurement` | `diagnostic` |
| eBUS Voltage Min | `voltage` | V (converted from 0.1V) | `measurement` | `diagnostic` |
| WiFi Signal Strength | `signal_strength` | dBm | `measurement` | `diagnostic` |
| Adapter Restart Count | — | — | `total_increasing` | `diagnostic` |
| Adapter Reset Cause | `enum` | — | — | `diagnostic` |

All sensors are `entity_category: diagnostic` (not shown in main dashboard by default).

### 5C. GraphQL query extension

```graphql
query AdapterInfo {
  adapterHardwareInfo {
    firmwareVersion
    firmwareChecksum
    bootloaderVersion
    hardwareId
    hardwareConfig
    jumperFlags
    isWifi
    isEthernet
    temperatureCelsius
    supplyVoltageMillivolts
    busVoltageMaxDecivolts
    busVoltageMinDecivolts
    resetCause
    restartCount
    wifiRssiDbm
    infoSupported
  }
}
```

### 5D. Polling strategy in HA

A new `adapter_info_coordinator` is added (separate from the existing status coordinator). This coordinator:
- Fetches `adapterHardwareInfo` via GraphQL on a 60s scan interval
- Is created at integration setup alongside existing coordinators
- Triggers entity updates for all adapter diagnostic sensors

The existing status coordinator is NOT reused because:
- It only queries `daemonStatus`/`adapterStatus` (not `adapterHardwareInfo`)
- Adding a large new query to it would increase its failure surface
- Adapter info entities need their own update lifecycle

### 5E. Late capability appearance

If `infoSupported` transitions from `false` to `true` (rare: adapter replacement or firmware update), the integration must handle this via a config entry reload. Sensors are created at setup based on the initial coordinator data. If capabilities change, the user reloads the integration entry to pick up new sensors.

This is the same pattern used for radio device discovery: entities are created at setup, not dynamically.

### 5F. Version-gated entity creation

Sensors are created conditionally based on `infoSupported` and field availability:
- WiFi RSSI sensor: only if `isWifi` is true and `wifiRssiDbm` is not null
- Reset cause/count: only if `resetCause` is not null (version_len == 8)
- Temperature/voltage: always created if `infoSupported`, but show `unavailable` if adapter returns 0

## 6. Layer 5: Documentation

### 6A. New doc: Enhanced Protocol INFO Reference

Location: `helianthus-docs-ebus/protocols/enh-info-reference.md`

Contents:
- Complete INFO ID table with field layouts, byte offsets, endianness
- Version-gate matrix based on wire-observable response lengths
- Jumper bit definitions
- Reset cause enum
- Feature bit definitions
- Wire format examples (hex dumps)
- Version response length detection algorithm

### 6B. Architecture doc update

Update `ARCHITECTURE.md` section on adapter info flow to reference the new telemetry pipeline.

## 7. Delivery Order

Strict dependency chain:

```
M0: helianthus-docs-ebus          — INFO reference doc
M1: helianthus-ebusgo             — transport INFO API + parsed types
M2: helianthus-ebus-adapter-proxy — identity caching + passthrough
M3: helianthus-ebusgateway        — semantic model + Prometheus + MCP + GraphQL
M4: helianthus-ebusgateway        — Portal UI panel
M5: helianthus-ha-integration     — device enrichment + diagnostic sensors
```

M0-M1 can be parallelized (docs and Go types are independent).
M2 depends on M1 (proxy uses ebusgo INFO types).
M3 depends on M1 (gateway uses ebusgo INFO types). M3 does NOT hard-depend on M2: the gateway can query INFO directly on an ENH connection without proxy caching. Proxy caching (M2) is an optimization layer, not a prerequisite.
M4 depends on M3 (Portal consumes GraphQL).
M5 depends on M3 (HA consumes GraphQL).
M2 and M3 can therefore be parallelized after M1 completes.

## 8. Issue Map (Preliminary)

| Issue ID | Repo | Milestone | Title |
|----------|------|-----------|-------|
| ISSUE-DOC-01 | helianthus-docs-ebus | M0 | Enhanced protocol INFO reference document |
| ISSUE-GO-01 | helianthus-ebusgo | M1 | Transport INFO request/response API |
| ISSUE-GO-02 | helianthus-ebusgo | M1 | Parsed adapter info types and version gating |
| ISSUE-PROXY-01 | helianthus-ebus-adapter-proxy | M2 | Identity INFO caching on startup |
| ISSUE-PROXY-02 | helianthus-ebus-adapter-proxy | M2 | Telemetry INFO passthrough + RESETTED invalidation |
| ISSUE-GW-01 | helianthus-ebusgateway | M3 | AdapterHardwareInfo semantic model |
| ISSUE-GW-02 | helianthus-ebusgateway | M3 | Adapter telemetry Prometheus metrics |
| ISSUE-GW-03 | helianthus-ebusgateway | M3 | adapter.info.get MCP tool |
| ISSUE-GW-04 | helianthus-ebusgateway | M3 | adapterHardwareInfo GraphQL query |
| ISSUE-GW-05 | helianthus-ebusgateway | M3 | Populate adapterStatus.firmwareVersion |
| ISSUE-GW-06 | helianthus-ebusgateway | M4 | Portal Adapter Hardware panel |
| ISSUE-HA-01 | helianthus-ha-integration | M5 | Adapter device enrichment (sw_version, hw_version, serial) |
| ISSUE-HA-02 | helianthus-ha-integration | M5 | Adapter diagnostic sensors |

## 9. Acceptance Criteria

### 9A. Falsifiable end-to-end test

Given: ebusd-esp adapter with version_len == 8 and WiFi jumper set (full capability)
When: Gateway starts and completes INIT
Then:
- MCP `adapter.info.get` returns all 8 INFO fields with correct values
- GraphQL `adapterHardwareInfo` returns non-null with firmware version populated
- Prometheus `/metrics` contains `ebus_adapter_temperature_celsius` with a plausible value (0-80°C)
- Prometheus `/metrics` contains `ebus_adapter_bus_voltage_max_decivolts` with a plausible value (100-250, representing 10.0-25.0V for a nominal 15V eBUS)
- HA shows Adapter device with `sw_version` matching firmware version
- HA shows diagnostic sensor `eBUS Voltage Max` with plausible reading

### 9B. Version-gated degradation tests (wire-observable)

**9B-1. version_len == 2 (legacy firmware)**
Given: Adapter returns 2-byte version response (no checksum, no jumpers)
Then:
- IDs 0x03-0x05 are queried (telemetry always available when INFO supported)
- IDs 0x06, 0x07 are NOT queried
- `resetCause`, `restartCount`, `wifiRssiDbm` are null
- `versionResponseLen` == 2 in GraphQL
- HA does not create WiFi RSSI or Reset Cause sensors

**9B-2. version_len == 5, WiFi jumper set**
Given: Adapter returns 5-byte version response, jumper bit 0x08 set
Then:
- IDs 0x03-0x05, 0x07 are queried
- ID 0x06 is NOT queried (requires version_len >= 8)
- `resetCause`, `restartCount` are null
- `wifiRssiDbm` is populated
- HA creates WiFi RSSI sensor, does NOT create Reset Cause sensor

**9B-3. version_len == 5, no WiFi jumper**
Given: Adapter returns 5-byte version response, jumper bit 0x08 NOT set
Then:
- IDs 0x03-0x05 queried, 0x06 and 0x07 NOT queried
- `wifiRssiDbm` is null

**9B-4. version_len == 8, WiFi (full capability)**
Given: Adapter returns 8-byte version response, WiFi jumper set
Then: All IDs 0x00-0x07 queried, all fields populated

### 9C. Proxy identity cache test

Given: Two gateway clients connected through proxy, cache in `valid` state
When: Both query INFO 0x01 (hardware ID)
Then:
- Zero upstream INFO requests (both served from cache)
- Both clients receive identical hardware ID responses

### 9C-2. Proxy singleflight concurrent test

Given: Two clients, cache in `cold` state (or `invalidated` after RESETTED)
When: Both query INFO 0x03 (temperature, uncached) concurrently
Then:
- Exactly one upstream INFO 0x03 request
- Both clients receive the same response
- `pendingInfo` is not overwritten (regression test for the pre-existing bug)

### 9C-3. Proxy singleflight different-ID queue test

Given: Client A queries INFO 0x03, Client B queries INFO 0x05 while 0x03 is in-flight
Then:
- 0x03 completes and is delivered to Client A
- 0x05 is then sent upstream and delivered to Client B
- Total: exactly two sequential upstream requests

### 9C-4. Proxy singleflight queue overflow test

Given: Queue depth configured to 3 (test override). The queue tracks pending upstream-bound requests only; singleflight-merged waiters do not consume queue slots.
When: 5 concurrent INFO requests arrive: IDs 0x03, 0x04, 0x05, 0x06, 0x03
Then:
- Request 1 (ID 0x03): goes upstream immediately (active slot, not queued)
- Request 2 (ID 0x04): queued (queue occupancy: 1)
- Request 3 (ID 0x05): queued (queue occupancy: 2)
- Request 4 (ID 0x06): queued (queue occupancy: 3 = full)
- Request 5 (ID 0x03): singleflight-merged with active request 1, NOT queued (same ID)
- A 6th request with a new unique ID would be rejected with `ENHResErrorHost` (queue full)
- All 5 requests eventually receive correct responses
- No upstream corruption

### 9D. Non-enhanced transport test

Given: Gateway connected via plain TCP transport (no enhanced protocol)
When: Gateway attempts to query adapter info
Then:
- `adapterHardwareInfo` returns non-null with `infoSupported = false`
- All telemetry fields are null, identity fields are empty/zero
- `ebus_adapter_info_supported` metric is 0
- No other INFO-related Prometheus metrics are emitted
- HA Adapter device retains hardcoded fallback attributes
- No errors logged

### 9E. Transport exclusivity test (ebusgo unit test)

Given: ENHTransport with active INFO request in-flight
When: Concurrent `ReadByte()` or `StartArbitration()` call is attempted
Then:
- Second call blocks on readMu/writeMu until INFO completes (or errors deterministically)
- Parser state is not corrupted
- INFO response is correctly assembled despite concurrent pressure

Given: Two concurrent `RequestInfo()` calls on the same transport
Then:
- Second call returns error immediately (concurrent INFO rejection)
- First call completes normally

### 9F. Adapter reset mid-INFO test

Given: Gateway has completed identity query
When: Adapter sends RESETTED during a telemetry INFO response (partial response)
Then:
- Current INFO request returns error
- Parser state is reset
- Identity cache is cleared
- Re-query sequence fires within 5s
- No stale identity data persists

### 9F. Proxy reconnect during INFO test

Given: Two clients connected through proxy
When: Upstream connection drops during an INFO response
Then:
- Pending INFO request to requesting session gets error response
- Proxy identity cache transitions to `invalidated`
- After upstream reconnect, proxy re-queries identity IDs
- Subsequent client INFO requests succeed

### 9G. Gateway restart with partial identity test

Given: Gateway restarts after acquiring only INFO 0x00 (version crashed mid-sequence)
When: Gateway reconnects
Then:
- All identity fields are re-queried from scratch
- No partial identity persists from previous session
- `ebus_adapter_info_health` is 0 until full sequence completes

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| INFO queries contend with bus operations | Telemetry poll delays semantic reads | Schedule INFO during idle windows; lower priority than semantic reads |
| Proxy identity cache stale after firmware update | Wrong version reported | Clear cache on RESETTED; RESETTED is mandatory after firmware flash |
| Adapter does not support INFO (old firmware) | No telemetry | Graceful degradation: all telemetry fields nil, no error |
| WiFi RSSI unexpected response length | Parse error | Strict: accept only 1-byte response per upstream source. Log and reject unexpected lengths as protocol error. |
| Bus voltage values in 0.1V need unit conversion for HA | Confusing display | Convert to V (float) for HA sensors; keep raw decivolts in gateway metrics |

## 11. Out of Scope

- **HEAP/memory metrics**: not available in the protocol (confirmed by ebusd source analysis)
- **Adapter firmware updates**: OTA update mechanism is out of scope
- **ebusd-esp firmware modifications**: we consume the protocol as-is
- **Tinyebus adapter telemetry**: separate track, may consume same types later
- **Proxy REST API for adapter info**: proxy remains protocol-transparent
- **Historical telemetry storage**: gateway exposes current values only, no time-series beyond Prometheus scrape
