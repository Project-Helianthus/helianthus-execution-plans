# Adapter Hardware Telemetry Plan 03: HA, Docs, Delivery & Acceptance

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0f9d24008521a5cf918a0959cd2a30e1ee559092f149416c75b8e7ca545d7391`

Depends on: Plans 01-02. Transport API and gateway semantic model must be
defined before HA integration can consume them. Documentation references the
complete data source catalog from Plan 01.

Scope: Home Assistant integration device enrichment and diagnostic sensors with
dedicated adapter_info_coordinator, protocol documentation, delivery order,
acceptance criteria (11 falsifiable tests including fault injection), and risk
analysis.

Idempotence contract: Reapplying this chunk must not create duplicate HA
sensors, duplicate documentation files, or conflicting delivery milestones.

Falsifiability gate: A review fails this chunk if HA sensor entity definitions
are incomplete, version-gated sensor creation rules are ambiguous or reference
firmware dates, acceptance tests are not falsifiable, delivery dependencies have
cycles, or fault-injection tests are missing.

Coverage: Sections 5-11 from the source plan (HA, Docs, Delivery, Issues,
Acceptance, Risks, Out of Scope).

---

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
| Adapter Temperature | `temperature` | deg C | `measurement` | `diagnostic` |
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
- Prometheus `/metrics` contains `ebus_adapter_temperature_celsius` with a plausible value (0-80 deg C)
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

### 9F-2. Proxy reconnect during INFO test

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
