# Writable Installer/Maintenance Plan 02: Gateway Semantic Types, Poller & GraphQL

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `34d2c8b70b8852a694fb09916744fe3670f3f386016de83d65c1f239b85213b7`

Depends on: `10-source-inventory-probes.md` (Phase 0 probe results gate all work here).

Scope: Gateway-side semantic type extensions (Phase 1), semantic poller reads
and write-through cache (Phase 2), GraphQL schema and mutations (Phase 3),
including B509 pipeline type generalization and SystemConfigWriter injection.

Idempotence contract: Reapplying this chunk must not create duplicate Go struct
fields, duplicate field spec entries, or conflicting mutation function
signatures. New types are additive only.

Falsifiability gate: A review fails this chunk if the SystemConfigWriter
injection is incomplete (must list all files touched), if the B509 float64
pipeline limitation is not addressed for HEX:8, if `boilerConfigFieldSpec.addrs`
is shown as singular instead of `[]uint16`, or if `readB524CString()` charset
sanitization would regress zone names.

Coverage: Phases 1-3 from the source plan (Semantic Types, Semantic Poller,
GraphQL Schema & Mutations).

---

## Phase 1: Semantic Types

### 1A: SystemConfig (B524)

File: `graphql/semantic.go` (SystemConfig at line ~235, cloneSystemConfig at ~461)

Add 6 new fields:
```
MaintenanceDate   *string  // ISO "YYYY-MM-DD" from HDA:3
InstallerName1    *string  // maxLength 6
InstallerName2    *string  // maxLength 6
InstallerPhone1   *string  // maxLength 6
InstallerPhone2   *string  // maxLength 6
InstallerMenuCode *int     // 0..999
```

Update `cloneSystemConfig()` with deep-copy for all 6 fields.

### 1B: BoilerConfig (B509)

File: `graphql/semantic.go` (BoilerConfig at line ~191)
Clone helper: `graphql/semantic_live.go` (cloneBoilerConfig at line ~605)

Add 3 new fields:
```
InstallerMenuCode  *int     // 0..255 (UCH)
PhoneNumber        *string  // hex-encoded 8 bytes
HoursTillService   *int     // hours (hoursum2)
```

## Phase 2: Semantic Poller

File: `cmd/gateway/semantic_vaillant.go`

### 2A: B524 Controller Reads

Dedicated slow-config tier with 30-minute interval -- same pattern as existing
boiler tier scheduler (interval-based, no freshness/expiry tracking).

### 2B: B509 Boiler Reads

B509 register reads for Password, PhoneNumber, HoursTillService using opcode
0x0D. Same interval-based slow-config tier.

### 2C: Write-Through Cache

Boiler (B509): Already has `SetBoilerConfig()` at line 4896 with patch+publish.

System (B524): Currently `setSystemConfig` resolver at `mutations.go:431` calls
`setSystemConfigResolve()` directly -- no builder-injected writer, no snapshot
patch. Must be fixed in M2:

1. Define `SystemConfigWriter` interface in `graphql/builder.go`
2. Add `systemConfigWriter` field + `SetSystemConfigWriter()` to Builder
3. Change `buildMutationType()` signature at `mutations.go:168` (5th param)
4. Change `NewSchema()` at `mutations.go:140` to pass through
5. Rewrite resolver closure at `mutations.go:424-433`
6. Implement in `semantic_vaillant.go` (patch+publish pattern)
7. Inject at startup in `cmd/gateway/main.go`

Files touched: `builder.go`, `mutations.go`, `semantic_vaillant.go`, `main.go`.

MCP write path: Add `ConfigWriter` interface to `mcp/server.go` alongside
existing `SemanticProvider` (line 344) and `ScheduleWriter` (line 339).

## Phase 3: GraphQL Schema & Mutations

### 3A: Schema

6 new SystemConfig fields (5 String + 1 Int), 3 new BoilerConfig fields.

### 3B: Mutations

Two new B524 `configValueType` variants: `configValueCString`,
`configValueDateHDA3`. Add `maxLen int` to `configFieldSpec` struct.

B524 `systemConfigFieldSpecs` additions:

| Field | Addr | Type | Constraints |
|-------|------|------|-------------|
| `maintenanceDate` | 0x002C | configValueDateHDA3 | -- |
| `installerName1` | 0x006C | configValueCString | maxLen: 6 |
| `installerName2` | 0x006D | configValueCString | maxLen: 6 |
| `installerPhone1` | 0x006F | configValueCString | maxLen: 6 |
| `installerPhone2` | 0x0070 | configValueCString | maxLen: 6 |
| `installerMenuCode` | 0x0076 | configValueUint16 | min: 0, max: 999 |

B509 `boilerConfigFieldSpecs` additions (uses `addrs []uint16` plural):

| Field | addrs | Codec | Constraints |
|-------|-------|-------|-------------|
| `installerMenuCode` | `[]uint16{0x4904}` | boilerConfigCodecUCH | min: 0, max: 255 |
| `phoneNumber` | `[]uint16{0x8104}` | boilerConfigCodecHex8 | -- |

`hoursTillService` is read-only (not in `boilerConfigFieldSpecs`).

Encoding details:
- CString: ASCII-only, maxLen, null-pad. Use `readB524CStringSanitized()` wrapper
  (NOT base `readB524CString()` -- base is also used by zone names at line 5665).
- DateHDA3: ISO parse, calendar validate, encode [DD, MM, YY-2000], reject 2015-01-01.
- UCH: integer 0-255, single byte.
- Hex8: hex string to 8 bytes.

### 3C: B509 Pipeline Type Generalization

Existing `SetBoilerConfig` pipeline is float64-only. HEX:8 cannot pass through.

Required changes in M3:
1. Union value type: `boilerConfigValue interface{}` (float64/string/int)
2. Generalize `parseBoilerConfigValue()` return type
3. Generalize `encodeBoilerConfigPayload()` input type
4. Extend `boilerSnapshotWithConfigValue()` for `*string`, `*int` fields
5. Add `boilerConfigCodecUCH` and `boilerConfigCodecHex8`

Size: ~100-150 lines changed in `semantic_vaillant.go`.
