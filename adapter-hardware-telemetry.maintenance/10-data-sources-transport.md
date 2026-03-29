# Adapter Hardware Telemetry Plan 01: Data Sources & Transport API

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0f9d24008521a5cf918a0959cd2a30e1ee559092f149416c75b8e7ca545d7391`

Depends on: None. This is the foundation chunk.

Scope: Enhanced protocol INFO data source catalog (IDs 0x00-0x07), version
gating rules (wire-observable, not firmware-date based), and the ebusgo
transport-layer API for requesting and parsing adapter info.

Idempotence contract: Reapplying this chunk must not create duplicate INFO ID
constants, duplicate parse functions, or conflicting transport method signatures.

Falsifiability gate: A review fails this chunk if any INFO ID is missing from
the catalog, version-gate rules are ambiguous or reference firmware dates instead
of wire-observable evidence, or the transport API contract leaves response
framing undefined.

Coverage: Sections 1-2 from the source plan (Summary, Data Sources, Transport API).

---

## 1. Data Sources: Enhanced Protocol INFO IDs

All INFO queries use the enhanced protocol `<INFO>` command (`ENHReqInfo`/`ENHResInfo`, command symbol 0x3). The adapter responds with `<INFO> <length> <data_0> ... <data_N-1>`.

### 1A. Identity IDs (static per adapter session)

| ID | Name | Response Length | Fields | Version Gate |
|----|------|---------------|--------|-------------|
| 0x00 | Version | 2/5/8 bytes | `version`, `features`, `checksum` (len>=5), `jumpers` (len>=5), `bootloader_version`, `bootloader_checksum` (len==8) | All (length varies by firmware generation) |
| 0x01 | Hardware ID | 9 bytes | 9-byte hardware identifier | All |
| 0x02 | Hardware Config | 3 or 8 bytes | chip-specific config, arbitration delay (bits 0-5 of byte 2, steps of 10us) | All (length varies by chip) |

### 1B. Telemetry IDs (volatile, periodic polling)

| ID | Name | Response Length | Fields | Unit | Version Gate |
|----|------|---------------|--------|------|-------------|
| 0x03 | Temperature | 2 bytes | `temp_H`, `temp_L` | deg C (uint16 big-endian) | All |
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
- `version_len >= 5`: jumper bits available, WiFi/Ethernet flags derivable
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
- `readTimeout` expiry before complete response: return error, reset parser
- Unexpected command during INFO read: return error, queue unexpected frame
- INFO with length 0: return empty slice, no error
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
