# Writable Installer/Maintenance Plan 02: Gateway Semantic Types, Poller & GraphQL

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `76ba52c1c0e115e69fec268ade5d5291bb47dedae4b6c6d42649fadb14143da7`

Implementation reconciliation note (2026-04-09):
- Controller API contract is aggregated (`installerName`, `installerPhone`).
- Boiler phone mutation path uses digit-string input and BCD wire encoding.
- `internal/configwrite/` extraction is not a required delivered milestone.

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

Implemented shape:
```
MaintenanceDate   *string  // ISO "YYYY-MM-DD" from HDA:3
InstallerName     *string  // aggregated 0x006C + 0x006D, maxLength 12
InstallerPhone    *string  // aggregated 0x006F + 0x0070, maxLength 12
InstallerMenuCode *int     // 0..999
```

Implementation note:
- Aggregation happens at the gateway surface while the underlying write path
  still targets the paired B524 CString registers.
- `cloneSystemConfig()` must deep-copy the aggregated installer fields.

### 1B: BoilerConfig (B509)

File: `graphql/semantic.go` (BoilerConfig at line ~191)
Clone helper: `graphql/semantic_live.go` (cloneBoilerConfig at line ~605)

Implemented shape:
```
InstallerMenuCode  *int     // 0..255 (UCH)
PhoneNumber        *string  // digit-string UX, BCD-encoded on wire
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

Boiler (B509): `SetBoilerConfig()` remains the writer/publish anchor.

System (B524): the delivered implementation wires `SystemConfigWriter`
through the existing builder/schema path so `setSystemConfig` also patches the
snapshot and republishes immediately after successful writes.

Delivered wiring scope:
1. `SystemConfigWriter` interface in `graphql/builder.go`
2. builder field + setter
3. `buildMutationType()` / `NewSchema()` pass-through
4. `setSystemConfig` resolver uses the writer path
5. `semantic_vaillant.go` patches and publishes the updated system snapshot
6. gateway startup injects the writer

MCP write path: the MCP server delegates to the same writer-backed system/boiler
config paths. A dedicated `internal/configwrite/` package is not part of the
implemented contract.

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
| `installerName` | 0x006C + 0x006D | configValueCString | maxLen: 12 |
| `installerPhone` | 0x006F + 0x0070 | configValueCString | maxLen: 12 |
| `installerMenuCode` | 0x0076 | configValueUint16 | min: 0, max: 999 |

B509 `boilerConfigFieldSpecs` additions:

| Field | Addr | Codec | Constraints |
|-------|------|-------|-------------|
| `installerMenuCode` | `[]uint16{0x4904}` | boilerConfigCodecUCH | min: 0, max: 255 |
| `phoneNumber` | `[]uint16{0x8104}` | BCD/digit-string codec | max 16 digits |

`hoursTillService` is read-only (not in `boilerConfigFieldSpecs`).

Encoding details:
- CString: printable ASCII validation, null-pad/split across the paired B524
  registers as needed for aggregated controller values.
- DateHDA3: ISO parse, calendar validate, encode [DD, MM, YY-2000], reject 2015-01-01.
- UCH: integer 0-255, single byte.
- Boiler phone: normalize user input to digits, then encode to 8-byte BCD.

### 3C: B509 Pipeline Type Generalization

Existing `SetBoilerConfig` pipeline had to generalize beyond float-only updates
so phone/menu code writes could flow through the same snapshot/publish path.

Required changes in M3:
1. Union value type: `boilerConfigValue interface{}` (float64/string/int)
2. Generalize `parseBoilerConfigValue()` return type
3. Generalize `encodeBoilerConfigPayload()` input type
4. Extend `boilerSnapshotWithConfigValue()` for `*string`, `*int` fields
5. Add codec handling for UCH and boiler phone digit-string/BCD payloads

Size: ~100-150 lines changed in `semantic_vaillant.go`.
