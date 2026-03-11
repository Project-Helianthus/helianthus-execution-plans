# Writable Maintenance & Installer Properties — Dual-Source Plan

## Context

Add readable and writable maintenance/installer properties from **two eBUS sources** — the VRC controller (BASV2, B524) and the boiler (BAI00, B509) — through a unified semantic, GraphQL, MCP, and HA integration surface.

**Motivation:** myVaillant app parity for installer contact info, maintenance scheduling, and service menu codes — editable directly from Home Assistant.

**Design constraint:** Both sources produce **consistent but independent** GraphQL/MCP surfaces. Field naming follows a shared convention but each lives under its own domain object (`system.config.*` vs `boilerStatus.config.*`). HA entities use parallel naming with source-prefix disambiguation.

### Source-Ownership Rules

Fields are **never merged** across B524 and B509. Each source owns its own domain:

| Domain | Owner | GraphQL Parent | MCP Parent | HA Entity Prefix |
|--------|-------|---------------|------------|-----------------|
| Controller installer/maintenance | VRC (B524, 0x15) | `system.config` | `ebus.v1.semantic.system` | `helianthus_` |
| Boiler installer/maintenance | BAI (B509, 0x08) | `boilerStatus.config` | `ebus.v1.semantic.boiler_status` | `helianthus_boiler_` |

Overlapping field names (e.g., `installerMenuCode`) exist in both domains but are **independent values** with **independent ranges** (controller: 0..999 u16, boiler: 0..255 UCH). HA entities disambiguate via entity ID: `number.helianthus_installer_menu_code` (controller) vs `number.helianthus_boiler_installer_menu_code` (boiler).

---

## Source Inventory

### Source A: VRC Controller (BASV2, addr 0x15) — B524 Protocol

| Register | Field | Type | Documented Constraints | Live Value | Status |
|----------|-------|------|----------------------|------------|--------|
| 0x002C | `maintenanceDate` | date (HDA:3, 3 bytes DD.MM.YY) | — | 2027-02-15 | **Proven**: read OK |
| 0x006C | `installerName1` | string | **maxLength 6** | empty | **Proven**: read OK |
| 0x006D | `installerName2` | string | **maxLength 6** | empty | **Proven**: read OK |
| 0x006F | `installerPhone1` | string | **maxLength 6** | empty | **Proven**: read OK |
| 0x0070 | `installerPhone2` | string | **maxLength 6** | empty | **Proven**: read OK |
| 0x0076 | `installerMenuCode` | u16 | **0..999** | 0 | **Proven**: read OK |
| 0x0096 | `maintenanceDue` | bool (u8) | — | — | **Proven**: already in semantic layer |

**Note:** Register 0x006E (between name2 and phone1) — **Unknown**: does not respond on this controller.
**Note:** Registers 0x006A, 0x0075, 0x0077 — **Unknown**: adjacent `user_RW` registers in same cluster, not investigated. Out of scope for this plan; documented for future adjudication.

### Source B: Boiler (BAI00, addr 0x08) — B509 Protocol

| Register | Field | Type | Access | Description | Status |
|----------|-------|------|--------|-------------|--------|
| 0x4904 | `password` (d.97) | UCH (1 byte) | r;ws | Installer menu code | **Hypothesis**: readable via B509, needs probe |
| 0x8104 | `phoneNumber` (d.98) | HEX:8 (8 bytes) | r;wi | Installer phone number | **Hypothesis**: readable via B509, needs probe |
| 0x2004 | `hoursTillService` (d.84) | hoursum2 (2 bytes) | r;wi | Hours until maintenance | **Hypothesis**: readable via B509, needs probe |
| 0x8204 | `language` (d.99) | UCH (1 byte) | r;ws | Language selection | **Hypothesis**: readable, out of scope |

---

## Phase 0: Live Bus Validation (BLOCKER)

**Before any feature code is written** (M2/M3/M4), validate both B524 and B509 read/write capabilities. Probes use existing RPC infrastructure (no prerequisite PRs needed).

### Phase 0A: B524 Controller Probes (BASV2 addr 0x15)

All probes via `rpc.invoke` with `set_ext_register`/`get_ext_register` on `plane: "system"`, `address: 21` (BASV2 0x15). Use **byte array** format for `data` parameter (NOT Go-style escape strings).

**Mandatory RPC params for B524 ext-register probes:**
- `source`: 49 (0x31 — matches `mutationSourceAddr` at `mutations.go:87`, used by existing `applyConfigMutation()`). Note: probes MUST use the same source address as the feature code mutation path. The gateway's semantic poller uses 0x71, but the GraphQL mutation path uses 0x31. Using 0x71 for probes could give false positives if the controller checks source address for write authorization.
- `group`: 0 (GG=0x00, Regulator group — all installer registers are in this group)
- `instance`: 0 (instance 0 for all probes)
- `addr`: register address (uint16 or hex string)
- `data`/`payload`: byte array for writes (either key accepted)
- `intent`: `"MUTATE"` for write probes (not needed for reads)
- `allow_dangerous`: `true` for write probes
- `idempotency_key`: unique non-empty string per MUTATE call (mandatory — MCP rejects MUTATE without it)

**All probes follow read-save-mutate-restore pattern**: read current value first, save it, mutate, verify, then restore saved value. Never hard-code restore targets.

1. **CString write**: Read register 0x006C (save original). Write `data: [84,101,115,116,0,0]` ("Test\0\0", 6 bytes padded) → readback → document payload shape. Restore saved original.
2. **CString width**: Write `data: [65,66,67,68,69,70,0]` ("ABCDEF\0", 7 bytes = maxLength 6 + null) to 0x006C → readback → confirm maxLength 6. Restore saved original.
3. **CString overflow**: Write 8+ bytes to 0x006C → expect NAK or truncation → document behavior. Restore saved original.
4. **CString clear**: Write `data: [0]` (single null byte) to 0x006C → readback → verify clears. Restore saved original.
5. **Date write**: Read register 0x002C (save original). Write `data: [15,3,27]` (2027-03-15) → readback → verify. Restore saved original.
6. **uint16 write**: Read register 0x0076 (save original). Write current value back (no-op) → readback → verify. Then write a different value → readback → verify. Restore saved original.

**Determines:**
- Whether CString writes are accepted at all → **Proven / Falsified**
- Actual register payload width and null-padding behavior → **Proven**
- Date write format correctness → **Proven / Falsified**
- uint16 write acceptance for `installerMenuCode` → **Proven / Falsified**

If writes fail for a type → that type falls back to **read-only mode** (sensors only, no mutations). Each type is independently gated.

### Phase 0 Degraded-Mode Contract

Probe outcomes determine what ships. The plan supports 3 degradation levels per source:

**CRITICAL: Field-additive degradation only.** Both `setSystemConfig` and `setBoilerConfig` mutations already exist and serve other fields (e.g., boiler config already handles `flowsetHcMaxC`). Degradation ONLY affects the new installer/maintenance fields added by this plan. Existing mutation names, dispatch, and supported field specs are never removed or altered.

**B524 (Phase 0A):**
| Probe result | What ships in M2 |
|-------------|-----------------|
| All writes pass (CString, DateHDA3, uint16) | 6 new field specs added to `systemConfigFieldSpecs`; MCP `system.set_config` tool added; all 6 writable HA entities |
| Some writes fail | Only proven-writable field specs added; failed fields become read-only sensors in HA (no `async_set_value`); MCP tool still added (with fewer writable fields) |
| All writes fail | No new field specs added to `systemConfigFieldSpecs`; no MCP `system.set_config` tool; all 6 fields are read-only sensors. Existing `setSystemConfig` mutation and its pre-existing fields are UNAFFECTED |
| All reads fail | Nothing ships for B524 installer surface |

**B509 (Phase 0B):**
| Probe result | What ships in M3 |
|-------------|-----------------|
| All writes pass (UCH, HEX:8) | 2 new field specs added to `boilerConfigFieldSpecs`; MCP `boiler_status.set_config` tool added; writable HA entities |
| Some writes fail | Only proven-writable field specs added; failed fields become read-only sensors; MCP tool still added (with fewer writable fields) |
| All writes fail | No new field specs added to `boilerConfigFieldSpecs`; no MCP `boiler_status.set_config` tool; all fields are read-only sensors. Existing `setBoilerConfig` mutation and its pre-existing fields are UNAFFECTED |
| All reads fail | Nothing ships for B509 installer surface; M3 dropped |

The milestone table uses "M1A proven" / "M1B proven" to mean "at least reads succeed for at least one register." Full write capability is a bonus, not a gate for the milestone itself.

### Phase 0B: B509 Boiler Probes (BAI00 addr 0x08)

B509 raw register access **already exists** in the `helianthus-ebusreg` registry. The Vaillant `system` plane (in `helianthus-ebusreg/vaillant/system/b509_register_access.go`) exposes:
- `get_register` — B509 command `0x0D` (read register by 2-byte address), returns decoded payload
- `set_register` — B509 command `0x0E` (write register by 2-byte address + data), returns readback

These are accessible via `ebus.v1.rpc.invoke` on the system plane (`plane: "system"`, `address: 8`). No new M1-pre PR is needed — the transport infrastructure is already production-ready with test coverage (`router/vaillant_register_access_test.go`).

**Probing uses existing infrastructure:** All Phase 0B probes use `rpc.invoke` with `method: "get_register"` / `method: "set_register"` on `plane: "system"`, `address: 8` (BAI00).

**Mandatory RPC params for B509 register probes:**
- `source`: 113 (gateway 0x71 — matches `p.source` used by `writeB509Value()` at line 4829. B509 writes go through the poller's bus layer, not through `applyConfigMutation()`, so 0x71 is correct here)
- `addr`: register address (uint16 or hex string)
- `data`/`payload`: byte array for writes (either key accepted)
- Write probes additionally require: `intent: "MUTATE"`, `allow_dangerous: true`, `idempotency_key: <unique non-empty string>`

**Internal poller helpers:** The gateway's semantic poller (`semantic_vaillant.go:4755`/`4817`) has its own internal `readB509Value()`/`writeB509Value()` helpers that use the same B509 opcodes directly via the bus layer. These are internal to the poller (not RPC-accessible) and are the read/write path for the semantic poll cycle and `SetBoilerConfig`. The probes use the RPC path; the feature code uses the internal helpers.

**Probe sequence (3 read probes, then 2 per-type write probes):**

#### Read probes (via `rpc.invoke`, plane: "system", address: 8, method: "get_register"):
1. `get_register(addr: 0x4904)` → expect 1 byte (UCH), value = 17
2. `get_register(addr: 0x8104)` → expect 8 bytes (HEX:8), likely all zeros
3. `get_register(addr: 0x2004)` → expect 2 bytes (hoursum2)

**Gate:** If ANY read probe returns error → **B509 path is Falsified** for that register. Remaining probes continue. Each register is independently gated.

#### Write probes (via `rpc.invoke`, plane: "system", address: 8, method: "set_register"; only for registers whose read succeeded; all follow read-save-mutate-restore):
4. **UCH write:** Read 0x4904 (save original). Write saved value back (no-op) → readback → expect match. Then write a different value → readback → expect match. Restore saved original.
5. **HEX:8 write:** Read 0x8104 (save original). Write `[0x54,0x65,0x73,0x74,0,0,0,0]` → readback → expect same 8 bytes. Restore saved original.
6. **hoursum2 write:** This probe is intentionally **read-only**. `hoursTillService` is a service counter with `r;wi` (write-installer) access. Writing an arbitrary value risks corrupting the service schedule. The no-op writeback (`set_register(0x2004, [H,L])` with current value) only proves framing, not semantic write safety. Therefore: **`hoursTillService` is read-only in this plan** — exposed as a diagnostic sensor, never as a writable entity. No write probe is performed.

**Per-type proof gates:**
- UCH write proven → `configValueUCH` type proceeds (boiler menu code writable)
- HEX:8 write proven → `configValueHex8` type proceeds (boiler phone writable)
- hoursum2: **read-only by design** — exposed as sensor, no write mutation, no MCP write tool
- If a type's write probe fails → that field becomes **read-only sensor** (no mutation, no MCP write tool for it)

**Determines:**
- B509 read works per-register → **Proven / Falsified** (independently per register)
- B509 write works per-type → **Proven / Falsified** (independently: UCH, HEX:8)
- Data format and framing correctness → **Proven**
- hoursum2 read works → **Proven / Falsified** (read-only sensor; no write probe)

---

## Phase 1: Gateway — Semantic Types

### 1A: Extend SystemConfig (B524 controller fields)

**Type def:** `helianthus-ebusgateway/graphql/semantic.go` (SystemConfig at line ~235)
**Clone helper:** `helianthus-ebusgateway/graphql/semantic.go` (cloneSystemConfig at line ~461)

Add to `SystemConfig` struct:
```go
MaintenanceDate   *string  // ISO "YYYY-MM-DD" from HDA:3
InstallerName1    *string  // maxLength 6
InstallerName2    *string  // maxLength 6
InstallerPhone1   *string  // maxLength 6
InstallerPhone2   *string  // maxLength 6
InstallerMenuCode *int     // 0..999
```

Update `cloneSystemConfig()` with deep-copy for all 6 fields.

### 1B: Extend BoilerConfig (B509 boiler fields)

**Type def:** `helianthus-ebusgateway/graphql/semantic.go` (BoilerConfig at line ~191)
**Clone helper:** `helianthus-ebusgateway/graphql/semantic_live.go` (cloneBoilerConfig at line ~605)

Add to `BoilerConfig` struct:
```go
InstallerMenuCode  *int     // 0..255 (UCH)
PhoneNumber        *string  // hex-encoded 8 bytes
HoursTillService   *int     // hours (hoursum2)
```

Update `cloneBoilerConfig()` with deep-copy for all 3 fields.

---

## Phase 2: Gateway — Semantic Poller

**File:** `helianthus-ebusgateway/cmd/gateway/semantic_vaillant.go`

### 2A: B524 Controller Reads (in `refreshSystem()`)

Add register constants and reads. **Polling optimization:** use a **dedicated slow-config tier** (separate from `refreshSystem()`) with 30-minute interval — same pattern as the existing boiler tier scheduler (`semantic_vaillant.go:1063-1070`), which is purely interval-based (fast/medium/slow tiers with fixed intervals, no freshness/expiry tracking). Do NOT stuff a timestamp check inside `refreshSystem()`.

### 2B: B509 Boiler Reads (in `refreshBoilerStatus()`)

Add B509 register reads for Password, PhoneNumber, HoursTillService. B509 read uses opcode `0x0D` with the register address. Same interval-based slow-config tier approach.

### 2C: Write-Through Cache

After any successful mutation (both B524 and B509), immediately patch the in-memory semantic snapshot AND trigger a publish. Do NOT rely on the 30-minute poll to reflect write results.

**Current state of write-through by source:**
- **Boiler (B509):** Already has a dedicated writer path that patches the snapshot and republishes (via `graphql/builder.go` → `semantic_vaillant.go:SetBoilerConfig()` at line 4896). New B509 installer fields follow this existing pattern.
- **System (B524):** Currently, `applyConfigMutation()` (at `mutations.go:579`) writes directly via `set_ext_register` with NO snapshot patch or publish hook. The `setSystemConfig` resolver (at `mutations.go:431`) calls `setSystemConfigResolve(params, registry, invoker)` directly — there is no builder-injected writer callback (unlike boiler, which uses `boilerWriter.SetBoilerConfig()`). Post-write, the semantic snapshot stays stale until the next `refreshSystem()` poll. **This must be fixed in M2:**
  1. Define `SystemConfigWriter` interface in `graphql/builder.go` (matching existing `BoilerConfigWriter`)
  2. Add `systemConfigWriter` field + `SetSystemConfigWriter()` method to `Builder`
  3. Change `buildMutationType()` signature at `mutations.go:168` to accept `systemWriter SystemConfigWriter` (5th param)
  4. Change `NewSchema()` at `mutations.go:140` to pass `builder.systemConfigWriter()` through
  5. Rewrite `setSystemConfig` resolver closure at `mutations.go:424-433` to call `systemWriter.SetSystemConfig()` instead of `setSystemConfigResolve()`
  6. Implement `SetSystemConfig()` in `semantic_vaillant.go` — internally calls `applyConfigMutation()`, then patches snapshot + publishes (same pattern as `SetBoilerConfig()` at line 4896)
  7. Inject at gateway startup in `cmd/gateway/main.go`

  **Files touched:** `builder.go`, `mutations.go`, `semantic_vaillant.go`, `cmd/gateway/main.go` (4 files, medium refactor)

**MCP write path:** The MCP `system.set_config` and `boiler_status.set_config` tools must also trigger the same patch+publish. This requires adding a `ConfigWriter` (or equivalent callback) interface to `mcp/server.go` alongside the existing `SemanticProvider` (line 344) and `ScheduleWriter` (line 339) dependencies. The MCP server currently has no system/boiler config-writer injection point — M2 must add one. Both GraphQL and MCP write paths call the same underlying `SystemConfigWriter`/`BoilerConfigWriter` implementation.

Extract shared `patchAndPublishSystemConfig()` / `patchAndPublishBoilerConfig()` functions (in `semantic_vaillant.go`) usable by both GraphQL mutations and MCP tool handlers via the injected writer interfaces.

### 2D: Snapshot lifecycle updates

For each source (system + boiler):
- `merge*SnapshotNonDestructive()`
- `clone*Snapshot()`
- `publish*()`
- `*StatusEquals()`

---

## Phase 3: Gateway — GraphQL Schema & Mutations

### 3A: Schema (queries.go)

Add field resolvers:
- `systemConfigType`: 6 new fields (5 String + 1 Int)
- `boilerConfigType`: 3 new fields (1 Int + 1 String + 1 Int)

### 3B: Mutations (mutations.go)

**New infrastructure — two new `configValueType` variants:**

```go
configValueCString   // null-terminated string, with maxLen
configValueDateHDA3  // 3-byte date [DD, MM, YY]
```

Add `maxLen int` field to `configFieldSpec` struct.

**Extend `systemConfigFieldSpecs`:**

| Field | Addr | Type | Constraints |
|-------|------|------|-------------|
| `maintenanceDate` | 0x002C | `configValueDateHDA3` | — |
| `installerName1` | 0x006C | `configValueCString` | maxLen: **6** |
| `installerName2` | 0x006D | `configValueCString` | maxLen: **6** |
| `installerPhone1` | 0x006F | `configValueCString` | maxLen: **6** |
| `installerPhone2` | 0x0070 | `configValueCString` | maxLen: **6** |
| `installerMenuCode` | 0x0076 | `configValueUint16` | min: 0, max: **999** |

**Extend existing `boilerConfigFieldSpecs` map** (add B509 installer fields to existing `setBoilerConfig` mutation at `semantic_vaillant.go:4889`). Note: `boilerConfigFieldSpec` uses `addrs []uint16` (plural, with multi-address fallback via `resolveB509BoilerConfigAddr` at line 5026). New entries use single-element slices:

| Field | addrs | Codec | Constraints |
|-------|-------|-------|-------------|
| `installerMenuCode` | `[]uint16{0x4904}` | `boilerConfigCodecUCH` (new, 1-byte) | min: 0, max: 255 |
| `phoneNumber` | `[]uint16{0x8104}` | `boilerConfigCodecHex8` (new, 8-byte hex) | — |

**Read-only B509 fields** (not in `boilerConfigFieldSpecs`, no mutation):

| Field | B509 Addr | Type | Reason |
|-------|-----------|------|--------|
| `hoursTillService` | 0x2004 | hoursum2 (2 bytes) | Service counter — write risks corrupting service schedule |

**New value types needed for B509:**
- `configValueUCH` — single unsigned byte (0-255)
- `configValueHex8` — 8 bytes, input/output as hex string

**Extend 3 existing functions** (`encodeConfigValue`, `confirmDecodableReadback`, `configReadbackMatchesWrite`) for all 4 new types: CString, DateHDA3, UCH, Hex8.

**Encoding details:**
- **CString**: validate ASCII-only (reject bytes > 0x7F), enforce maxLen, pad with null to maxLen+1. Readback comparison: trim trailing nulls, then `bytes.Equal`.
- **DateHDA3**: parse ISO "YYYY-MM-DD" → full calendar validation (reject Feb 30, etc.) → encode `[DD, MM, YY-2000]`. Reject sentinel 2015-01-01 on encode. Readback: compare first 3 bytes exactly.
- **UCH**: parse integer 0-255 → single byte. Readback: single byte compare.
- **Hex8**: parse hex string → 8 bytes. Readback: 8-byte compare.

**Read path charset safety:** Add Latin-1→UTF-8 sanitization **in a new wrapper** `readB524CStringSanitized()`, NOT in the base `readB524CString()`. The base function is also called by `readB524ZoneNamePart()` (at line 5665) for zone names — adding sanitization there would replace legitimate non-ASCII characters (e.g., German umlauts) with `?`, a regression. The sanitized wrapper is used ONLY for the 4 installer string fields (installerName1/2, installerPhone1/2). If a byte > 0x7F is found on read, replace with `?` and log. Write path rejects non-ASCII. **Does NOT apply to B509 HEX:8 fields** — `phoneNumber` is raw bytes encoded as hex, not a text string, and must not be charset-sanitized.

### 3C: B509 Mutation Infrastructure

The existing `applyConfigMutation()` assumes B524 `set_ext_register`/`get_ext_register`. B509 writes use opcode `0x0E` with different framing.

**Options:**
- (a) Extract `applyConfigMutation()` into a protocol-agnostic interface with B524 and B509 implementations
- (b) Create separate `applyBoilerConfigMutation()` for B509

**Recommended:** Option (b) — simpler, keeps B524 and B509 write paths independent. `applyBoilerConfigMutation()` follows the same write-then-readback pattern but uses B509 opcodes.

**CRITICAL: B509 pipeline type generalization required.** The existing `SetBoilerConfig` pipeline is **float64-only**:
- `parseBoilerConfigValue()` at line 4953 returns `(float64, error)`
- `encodeBoilerConfigPayload()` at line 4987 takes `float64`
- `boilerSnapshotWithConfigValue()` at line 4967 sets `*float64` pointers

This works for existing numeric fields (`partloadHcKW`, `flowsetHcMaxC`) but **cannot handle `configValueHex8`** (a hex string "5465737400000000"). UCH (0-255) fits float64 fine, but HEX:8 does not.

**Required changes to `SetBoilerConfig` in M3:**
1. Introduce union value type: `boilerConfigValue` as `interface{}` wrapping `float64` (existing codecs) or `string` (Hex8) or `int` (UCH)
2. Generalize `parseBoilerConfigValue()` to return `(boilerConfigValue, error)` — codec determines return type
3. Generalize `encodeBoilerConfigPayload()` to accept `boilerConfigValue`
4. Extend `boilerSnapshotWithConfigValue()` to set `*string` (PhoneNumber) and `*int` (InstallerMenuCode, HoursTillService) fields in addition to existing `*float64`
5. Add `boilerConfigCodecUCH` and `boilerConfigCodecHex8` to the codec enum

This is the largest single refactor in M3. Size: ~100-150 lines changed in `semantic_vaillant.go`.

---

## Phase 4: Gateway — MCP Server

**File:** `helianthus-ebusgateway/mcp/server.go`

### 4A: Types

Add JSON-tagged fields to both MCP `SystemConfig` and `BoilerConfig` structs. Update clone functions.

### 4B: New MCP write tool: `ebus.v1.semantic.system.set_config`

```
Tool: ebus.v1.semantic.system.set_config
Args: { field: string, value: string }
Returns: { success: bool, error: string }
```

**Field naming:** The `field` argument accepts the camelCase Go field spec key (e.g., `"installerName1"`, `"maintenanceDate"`), matching internal `systemConfigFieldSpecs` map keys. This is intentional — it matches the GraphQL mutation field names. The MCP GET output uses snake_case JSON tags (`installer_name_1`, `maintenance_date`), but the SET input uses the spec key. This asymmetry is consistent with existing `setSystemConfig` / `setBoilerConfig` mutation field names.

**Return format:** Uses the standard `ebus.v1.*` response envelope `{meta, data, error}` (per `AGENTS.md` MCP contract and `mcp/server.go:997`). The `{success, error}` fields shown above are the `data` payload inside that envelope, NOT the top-level response. Example success: `{meta: {...}, data: {success: true}, error: null}`. Example failure: `{meta: {...}, data: null, error: "field 'badField' not found"}`.

**Must update:**
- Tool constants + list
- Tool dispatch (`handleToolsCall`)
- **Tool classification** — add to `tool_classification_test.go` as `core_stable` (mandatory: `tool_classification_test.go:76-78` enforces that all `ebus.v1.*` tools must be `core_stable`)
- **Parity contract test** — new schema hash entry for `system.set_config`. Note: existing GET tool parity hashes (`system.get`, `boiler_status.get`) do NOT need updates — the parity test hashes only `inputSchema` (tool arguments), not output shape. Adding output fields to SystemConfig/BoilerConfig does not affect parity.
- **Server test** (new tool coverage)

**Shared write logic:** The B524 and B509 write pipelines are **structurally different** — B524 uses `configFieldSpec` (at `mutations.go:76`: `{group, addr, valueType, min, max, enum}`) while B509 uses `boilerConfigFieldSpec` (at `semantic_vaillant.go:4875`: `{addrs []uint16, min, max, codec}`). A full unification is not viable without a large refactor.

What CAN be shared in `internal/configwrite/`:
- **Value validation utilities**: hex string parsing, ASCII validation, range checking, date calendar validation
- **New value type encoders/decoders**: CString encode/decode, DateHDA3 encode/decode, UCH encode/decode, Hex8 encode/decode (pure functions: `string → []byte` and `[]byte → string`)
- **Readback comparison logic**: null-trimming for CString, byte-exact for others

What stays protocol-specific:
- B524: `configFieldSpec` resolution, `applyConfigMutation()` (uses `set_ext_register`/`get_ext_register`)
- B509: `boilerConfigFieldSpec` resolution, `SetBoilerConfig()` (uses `writeB509Value`/`readB509Value`)

The MCP `set_config` tools delegate to the same protocol-specific writer implementations (via injected `SystemConfigWriter`/`BoilerConfigWriter` interfaces), NOT to a unified write pipeline. The shared package only provides encoding utilities.

### 4C: New MCP write tool: `ebus.v1.semantic.boiler_status.set_config`

Same pattern as system.set_config but for B509 boiler registers. Same classification/parity/test requirements including standard envelope format. Tool name uses `boiler_status` (matching the existing `ebus.v1.semantic.boiler_status.get` tool and the source-ownership table). Only the new write tool needs a parity hash entry (existing `boiler_status.get` hash is unaffected — parity test hashes inputSchema only).

---

## Phase 5: HA Integration

### 5.1: Coordinator Query Updates

**File:** `helianthus-ha-integration/custom_components/helianthus/coordinator.py`

**CRITICAL backward-compat contract:**

Adding new fields to `QUERY_SYSTEM` or `QUERY_BOILER` causes **whole-query GraphQL validation failure** on older gateways that don't have these fields in their schema. This is NOT a null-field situation — the query itself is rejected. On cold start with an old gateway, entities go unavailable.

**Solution: Two separate optional queries** (NOT extending existing queries):

**`QUERY_SYSTEM_INSTALLER`** (new, optional):
```graphql
{ system { config {
  maintenanceDate installerName1 installerName2
  installerPhone1 installerPhone2
} } }
```

**`QUERY_SYSTEM_SENSITIVE`** (new, optional):
```graphql
{ system { config { installerMenuCode } } }
```

**`QUERY_BOILER_INSTALLER`** (new, optional):
```graphql
{ boilerStatus { config { phoneNumber hoursTillService } } }
```

**Schema contract for partial reads:** The gateway **always** includes all 3 B509 fields (`phoneNumber`, `hoursTillService`, `installerMenuCode`) in the `boilerConfigType` GraphQL schema, regardless of probe results. Fields whose underlying register read fails return `null`. This means:
- The HA query shape is always the same (no compile-time pruning needed)
- HA entities are always created (platform registration is unconditional)
- Entities whose backing field is `null`: `native_value` returns `None` → HA shows state as **"unknown"** (NOT "unavailable"). To show "unavailable" when the optional query flag is `False`, entities must override the `available` property to check the coordinator's availability flag (e.g., `_system_installer_available`). This matches existing patterns: `HelianthusRadioSensor` overrides `available` for staleness, `HelianthusSolarSensor` overrides for FM5 mode.
- The gateway semantic poller simply doesn't populate fields for unreadable registers (leaves them as `nil` in the Go struct)

This is consistent with Phase 3A's fixed `boilerConfigType` definition and avoids schema variability.

**`QUERY_BOILER_SENSITIVE`** (new, optional):
```graphql
{ boilerStatus { config { installerMenuCode } } }
```

**Coordinator behavior — per-source flags:**

Each coordinator (system, boiler) manages its own independent flags:

`HelianthusSystemCoordinator`:
- `_system_installer_available: bool` — tracks `QUERY_SYSTEM_INSTALLER`
- `_system_sensitive_available: bool` — tracks `QUERY_SYSTEM_SENSITIVE`

`HelianthusBoilerCoordinator`:
- `_boiler_installer_available: bool` — tracks `QUERY_BOILER_INSTALLER`
- `_boiler_sensitive_available: bool` — tracks `QUERY_BOILER_SENSITIVE`

**Query sequencing (per coordinator, per poll cycle):**
1. Fire main query (`QUERY_SYSTEM` / `QUERY_BOILER`) — **UNCHANGED**
2. If `_*_installer_available` is not False: fire installer query. On error → classify (see below)
3. If `_*_sensitive_available` is not False: fire sensitive query. **Independent of step 2** — sensitive query fires even if installer query failed
4. All 4 flags are **independent** — system installer can work while boiler installer fails, and vice versa. Sensitive can work while installer fails, and vice versa.

**Error classification for optional queries:**
- **Schema/validation error** (GraphQL response contains `errors` with field-not-found or validation messages): set flag False permanently (until HA restart). This means the gateway doesn't support these fields.
- **Transport/transient error** (connection refused, timeout, HTTP 5xx, resolver exception): do NOT set flag False. Log warning, skip this poll cycle, retry next cycle. Transient failures must not permanently disable a supported feature.
- **Distinction mechanism:** check the GraphQL error `extensions.code` or error message pattern. Schema validation errors typically contain "Cannot query field" or similar. All other errors are treated as transient.

**M4a/M4b alignment:**
- M4a (B524 HA entities) only uses `_system_installer_available` and `_system_sensitive_available`. No boiler flags needed.
- M4b (B509 HA entities) adds `_boiler_installer_available` and `_boiler_sensitive_available` to the boiler coordinator.

**HA entity behavior:**
- B524 installer entities: override `available` → return `False` if `_system_installer_available` is False → entity shows **"unavailable"**. When available but field is `None` → entity shows "unknown"
- B524 menu code entity: override `available` → return `False` if `_system_sensitive_available` is False
- B509 installer entities: override `available` → return `False` if `_boiler_installer_available` is False
- B509 menu code entity: override `available` → return `False` if `_boiler_sensitive_available` is False
- All entities created regardless — they stay "unavailable" until gateway supports the fields
- Each entity class MUST override the `available` property to check its coordinator flag (matching existing patterns like `HelianthusRadioSensor.available` in `sensor.py:1280`)
- `entity_registry_visible_default=False`, `entity_registry_enabled_default=False` for all menu code entities. Note: `entity_registry_visible_default` is first-time use in this integration (existing code only uses `entity_registry_enabled_default`). Verify against deployed HA core version (attribute `_attr_entity_registry_visible_default` on `Entity` base class).

**Data merge strategy:**

Optional query results merge into the existing coordinator data dicts at the same level as existing config fields:

- **System coordinator** (`_async_update_data` returns `{"state": dict, "config": dict, "properties": dict}`):
  - `QUERY_SYSTEM_INSTALLER` results merge into `data["config"]` — e.g., `data["config"]["maintenanceDate"]`, `data["config"]["installerName1"]`
  - `QUERY_SYSTEM_SENSITIVE` results merge into `data["config"]` — e.g., `data["config"]["installerMenuCode"]`
  - If optional query failed (flag False), these keys are simply absent from `data["config"]`

- **Boiler coordinator** (`_async_update_data` returns `{"boilerStatus": dict_or_None}`):
  - `QUERY_BOILER_INSTALLER` results merge into `data["boilerStatus"]["config"]` — e.g., `data["boilerStatus"]["config"]["phoneNumber"]`
  - `QUERY_BOILER_SENSITIVE` results merge into `data["boilerStatus"]["config"]` — e.g., `data["boilerStatus"]["config"]["installerMenuCode"]`
  - If optional query failed (flag False), these keys are absent

**Entity data access pattern:** `self.coordinator.data["config"].get("maintenanceDate")` (system) or `self.coordinator.data["boilerStatus"]["config"].get("phoneNumber")` (boiler). Entities check for `None` (key absent or field null) and return `None` from `native_value` → HA shows "unknown".

**Cold start safety:** On HA restart against old gateway, main queries succeed (existing entities work), all 4 optional queries fail independently and are disabled. No blanking, no stale data issues.

### 5.2: New `text.py` platform (combined installer strings)

**New file:** `helianthus-ha-integration/custom_components/helianthus/text.py`

**Decision: 4 raw part entities** (NOT combined entities). This avoids paired-writer complexity, eliminates atomicity concerns, and maps 1:1 to physical registers.

4 writable `TextEntity` instances for controller:
- **Installer Name Part 1** — `system.config.installerName1`, `native_max=6`
- **Installer Name Part 2** — `system.config.installerName2`, `native_max=6`
- **Installer Phone Part 1** — `system.config.installerPhone1`, `native_max=6`
- **Installer Phone Part 2** — `system.config.installerPhone2`, `native_max=6`

Each entity maps to exactly one B524 register. No split/join logic needed.

**Degraded mode:** If Phase 0A proves reads succeed but CString writes fail, these entities ship as **read-only** `SensorEntity` instances instead of writable `TextEntity`. The entity type is a compile-time decision based on probe results — the shipped code either includes `async_set_value` or it doesn't. Same applies to the date entity (read-only sensor if DateHDA3 write fails) and menu code (read-only sensor if uint16 write fails). The gateway schema always includes all fields regardless (nullable) — degradation only affects whether mutations/write tools exist.

1 writable `TextEntity` for boiler phone number:
- **Boiler Phone Number** — `boilerStatus.config.phoneNumber`, `native_max=16` (8 hex bytes as hex string)

**Input validation:**
- B524 text entities: reject non-ASCII input (bytes > 0x7F) with descriptive error
- Boiler phone entity: reject non-hex characters, enforce exactly 16 hex chars (8 bytes), case-insensitive input

Properties: `EntityCategory.CONFIG`, `TextMode.TEXT`

### 5.3: New `date.py` platform (maintenance date)

**New file:** `helianthus-ha-integration/custom_components/helianthus/date.py`

1 writable `DateEntity`:
- **Maintenance Date** — `maintenanceDate` from controller
- Reject sentinel date 2015-01-01 on write

Properties: `EntityCategory.CONFIG`, icon `mdi:calendar-clock`

### 5.4: Number / Sensor entities

Add to `number.py` (writable):
- **Controller Installer Menu Code** — from `QUERY_SYSTEM_SENSITIVE`, min=0, max=999, step=1, `EntityCategory.CONFIG`
- **Boiler Installer Menu Code** — from `QUERY_BOILER_SENSITIVE`, min=0, max=255, step=1, `EntityCategory.CONFIG`

**Security (menu codes only):** Both menu code entities: `entity_registry_visible_default=False` AND `entity_registry_enabled_default=False`. Data sourced from separate sensitive query. Users must explicitly enable in HA entity registry.

**Privacy scope note:** The sensitive queries (`QUERY_SYSTEM_SENSITIVE`, `QUERY_BOILER_SENSITIVE`) fetch menu code values from the gateway regardless of whether entities are enabled in HA. The "hidden+disabled" protection is UI-level only — it prevents casual exposure in dashboards and automations but does not prevent data collection. This is acceptable because: (a) the gateway already holds these values in memory (they are always in the semantic snapshot), (b) the HA coordinator only stores them as entity state (not logged, not exposed to external APIs), (c) the values are numeric codes, not credentials. Full data-collection prevention would require the coordinator to check entity enablement before issuing queries, which adds complexity without meaningful security benefit since the gateway exposes the data unconditionally.

Add to `sensor.py` (read-only):
- **Hours Till Service** — `boilerStatus.config.hoursTillService`, `SensorDeviceClass.DURATION`, native_unit `h`, `EntityCategory.DIAGNOSTIC`, `SensorStateClass.MEASUREMENT`

This is a read-only diagnostic sensor, not a writable number entity. The B509 `hoursTillService` register is a service counter that must not be written to.

### 5.5: Register platforms in `__init__.py`

Add `"text"` and `"date"` to `PLATFORMS` list.

---

## Phase 6: Tests

### Gateway (Go)

**`mutations_test.go` / `mutations_unit_test.go`:**
- `encodeConfigValue` for 4 new types:
  - CString: empty, normal, max-len=6, too-long (rejected), non-ASCII byte 0x80 (rejected), single null, all-spaces
  - DateHDA3: valid ISO "2027-06-15", invalid format "15/06/2027" (rejected), year 1999 (rejected), year 2100 (rejected), Feb 29 leap (accepted), Feb 29 non-leap (rejected), Feb 30 (rejected), sentinel 2015-01-01 (rejected), day 0 (rejected), month 13 (rejected)
  - UCH: 0, 127, 255, 256 (rejected), -1 (rejected), non-integer (rejected)
  - Hex8: valid 16-char hex, odd-length hex (rejected), 14-char hex (rejected), 18-char hex (rejected), non-hex chars (rejected)
- `confirmDecodableReadback` for 4 new types with edge cases (truncated data, extra bytes, all-zero)
- `configReadbackMatchesWrite` for 4 new types:
  - CString: asymmetric null-padding (write 4 bytes, readback 7 bytes with trailing nulls → match), mismatch detection
  - DateHDA3: exact 3-byte match, mismatch on any byte
  - UCH: exact 1-byte match
  - Hex8: exact 8-byte match

**`internal/configwrite/` package tests:**
- Encode/decode round-trip for all 4 new types (CString, DateHDA3, UCH, Hex8)
- Value validation: hex parsing, ASCII-only enforcement, range checking, calendar validation
- Readback comparison: null-trimming CString, byte-exact others
- Note: field spec resolution is NOT in this package — it stays protocol-specific

**B509 read/write tests (existing in `helianthus-ebusreg/router/vaillant_register_access_test.go`):**
- `get_register`: has request encoding + response decoding coverage
- `set_register`: has request encoding coverage (frame building). Does NOT cover full write-then-readback verification at the transport layer — that's tested end-to-end via the gateway's `SetBoilerConfig` path.
- Additional coverage in `helianthus-ebusreg/vaillant/system/projections_test.go`
- No new ebusreg-level tests needed for B509 transport — existing frame-building coverage validates the infrastructure. Write-readback verification is tested at the gateway layer (in `semantic_vaillant_test.go`).

**Read path charset tests (`semantic_vaillant_test.go`):**
- `readB524CStringSanitized()`: Non-ASCII byte 0xE4 → replaced with `?` in returned string
- `readB524CStringSanitized()`: Pure ASCII string → returned unchanged
- `readB524CStringSanitized()`: All-null bytes → empty string
- `readB524CString()` (base): Non-ASCII bytes preserved (regression guard for zone names)

**`semantic_vaillant_test.go`:**
- Snapshot merge/clone/equals for all new fields in both system and boiler snapshots
- Slow-config tier interval behavior (interval not elapsed → no re-read, interval elapsed → re-read, write-through → immediate patch without waiting for next poll)
- Write-through cache: verify immediate post-write snapshot update (write → snapshot patched → publish called → next poll doesn't overwrite)
- All new fields present in published snapshots (gateway always publishes all fields; installer/sensitive separation is HA-layer concern)

**`mcp/server_test.go`:**
- Tool dispatch tests for `system.set_config` and `boiler_status.set_config`
  - Valid field + value → success
  - Unknown field → error
  - Out-of-range value → error
- **Tool classification test** — new tools must be `core_stable` (enforced by naming convention test)
- **Parity contract test** — new schema hash entries for both tools

**`queries_test.go`:**
- GraphQL field resolvers for all 9 new fields return correct types (String/Int/null)
- `setSystemConfig` mutation: valid field, invalid field, out-of-range value
- `setBoilerConfig` mutation: valid field, invalid field, out-of-range value

**Degraded-mode test strategy:** All tests above are written assuming full write capability (the "happy path"). If Phase 0 probes falsify specific write types, the corresponding mutation/tool tests are removed or converted to "mutation returns error for read-only field" tests. This is a compile-time decision: the test suite shipped in M2/M3 matches the proven capabilities. There is no runtime degradation — the codebase either includes write support for a type or it doesn't.

### HA (Python)

**`test_text.py`:**
- Entity creation (5 text entities: 4 controller parts + 1 boiler phone)
- B524 text write flow: valid ASCII string → gateway mutation called with correct field name
- B524 ASCII validation: non-ASCII input rejected with descriptive error
- B524 empty string write → clears field
- B524 max-length enforcement: 7-char input to 6-max entity → rejected
- Boiler phone write flow: valid 16-char hex string → gateway mutation with correct field/value
- Boiler phone hex validation: non-hex chars rejected, wrong length rejected (14 chars, 18 chars)
- Entity attributes: `entity_category=CONFIG`, `mode=TEXT`

**`test_date.py`:**
- Entity creation (1 date entity)
- Date conversion: Python `date` → ISO string → gateway mutation
- Sentinel 2015-01-01 rejection on write
- Valid date range acceptance
- Entity attributes: `entity_category=CONFIG`, icon `mdi:calendar-clock`

**`test_number.py` (additions):**
- 2 new number entities: controller menu code (0-999), boiler menu code (0-255)
- Both: `entity_registry_visible_default=False`, `entity_registry_enabled_default=False`
- Write flow: value → gateway mutation with correct field/value

**`test_sensor.py` (additions):**
- Hours Till Service sensor: read-only, `SensorDeviceClass.DURATION`, unit `h`, `EntityCategory.DIAGNOSTIC`
- Verify no write method exposed

**`test_coordinator.py`:**
- **Backward-compat regression (CRITICAL):** mock gateway without new fields → verify system/boiler main query data not blanked, existing entities preserved
- **System installer query failure:** mock `QUERY_SYSTEM_INSTALLER` returning GraphQL error → verify `_system_installer_available = False`, main data intact, B524 installer entities unavailable
- **Boiler installer query failure:** mock `QUERY_BOILER_INSTALLER` returning GraphQL error → verify `_boiler_installer_available = False`, main data intact, B509 installer entities unavailable
- **Independent flag isolation:** mock system installer succeeds + boiler installer fails → verify B524 installer entities available, B509 installer entities unavailable (cross-source independence)
- **Sensitive independent of installer:** mock `QUERY_SYSTEM_INSTALLER` fails + `QUERY_SYSTEM_SENSITIVE` succeeds → verify menu code entity IS available despite installer failure (step 3 fires regardless of step 2)
- **Cold start all-fail (schema error):** mock all 4 optional queries returning schema validation errors on first poll → verify all flags False, no retry, main data intact
- **Transient error recovery:** mock `QUERY_SYSTEM_INSTALLER` returning transport error (timeout/5xx) → verify flag NOT set False, query retried on next poll cycle
- **Schema vs transient distinction:** mock schema validation error → flag permanently disabled; mock transport error → flag stays enabled

---

## Phase 7: Deployment Verification

**Note:** Steps marked `[write-gated]` only apply if the corresponding write type was proven in Phase 0. Steps marked `[B509-gated]` only apply if M3 shipped. All MCP field names use **snake_case** (e.g., `installer_name_1`, `maintenance_date`, `phone_number`, `hours_till_service`, `installer_menu_code`).

1. **Gateway binary** → deploy to RPi4
2. `ebus.v1.semantic.system.get` → confirm new fields in `config` object (count depends on M1A results: 6 if all reads passed, fewer if some registers failed)
3. `[B509-gated]` `ebus.v1.semantic.boiler_status.get` → confirm new fields in `config` object (count depends on M1B results)
4. `[write-gated: CString]` Read `installer_name_1` (save original) → `system.set_config(field: "installerName1", value: "Test")` → re-read → confirm → restore saved original
5. `[write-gated: DateHDA3]` Read `maintenance_date` (save original) → `system.set_config(field: "maintenanceDate", value: "2027-06-15")` → re-read → confirm → restore saved original
6. `[B509-gated, write-gated: UCH]` Read boiler `installer_menu_code` (save original) → `boiler_status.set_config(field: "installerMenuCode", value: <saved>)` → re-read → confirm (no-op writeback)
7. HA deployment → verify all entities appear (installer entities available or unavailable depending on probe results; menu code entities hidden+disabled by default)
8. `[write-gated]` HA write test → change maintenance date via HA UI → verify on controller
9. **Backward-compat smoke test**: temporarily revert gateway to pre-feature binary → verify HA main queries still work, installer entities show "unavailable" (via `available` override), no errors in HA log beyond initial "optional query failed" warning

---

## Milestone & Dependency Map

### Milestone Order

```
M0 (Docs)            ──────────────────────────────────────────→ doc-gate
M1 (Phase 0 Probes)  ──────────────────────────────────────────→ proof-gate
  ├─ M1A: B524 probes (Phase 0A)  ─→ proven/falsified per-type (uses existing set_ext_register)
  └─ M1B: B509 probes (Phase 0B)  ─→ proven/falsified per-type (uses existing get_register/set_register)
M2 (Gateway B524)    ─── depends on: M0 + M1A ────────────────→ transport-gate
M3 (Gateway B509)    ─── depends on: M0 + M1B + M2 merged ────→ transport-gate
M4 (HA Integration)  ─── depends on: M2 merged ───────────────→ MCP-gate
                          (+ M3 merged for boiler entities)
```

**Key constraints:**
- M0 (docs) is the doc-gate: canonical register docs must be reviewed before **feature code** (M2, M3, M4)
- M1A and M1B are **independent** — B524 failure does NOT block B509 and vice versa
- M1B uses existing `get_register`/`set_register` methods on the system plane (no prerequisite PR needed)
- M2 is the first gateway PR: extracts `configwrite` package (ungated — protocol-agnostic infrastructure) + implements B524 surface (gated on M1A). If M1A fails entirely, M2 still ships configwrite extraction with zero B524 field specs.
- M3 **depends on M2 merged** (reuses `configwrite` package). M3 cannot parallelize with M2.
- M4 (HA) can ship B524 entities after M2 merged. B509 entities are added to M4 after M3 merged. This means M4 may ship in 2 PRs: one for B524 entities, one adding B509 entities after M3.
- If M1B fails entirely → M3 is dropped; M2 + M4(B524-only) still ship
- If M1A fails entirely (all reads fail) → nothing ships for B524 installer surface (consistent with degraded-mode contract). **M2 still ships as an infrastructure-only PR** containing the `configwrite` package extraction (shared encode/decode/readback logic) and the 4 new `configValueType` constants, but with zero B524 field specs. M3 reuses `configwrite` from this M2 PR. The configwrite extraction is NOT gated on M1A — it is protocol-agnostic infrastructure.

### PR Strategy

| Milestone | Repo | PR | Depends On |
|-----------|------|----|------------|
| M0 | `helianthus-docs-ebus` | Document installer/maintenance registers (B524 + B509) | — |
| M1A | — | B524 live bus probes (operator notebook, no PR) | — |
| M1B | — | B509 live bus probes (operator notebook, uses existing `get_register`/`set_register` on system plane) | — |
| M2 | `helianthus-ebusgateway` | B524 installer/maintenance: `internal/configwrite` encoding utilities + semantic + GraphQL + MCP | M0 doc-gate, M1A proven |
| M3 | `helianthus-ebusgateway` | B509 installer/maintenance: semantic + GraphQL + MCP (reuses `configwrite` encoding utilities from M2) | M0 doc-gate, M1B proven, M2 merged |
| M4a | `helianthus-ha-integration` | B524 text/date/number entities + coordinator optional queries | M2 merged |
| M4b | `helianthus-ha-integration` | B509 number/text entities (additive to M4a) | M3 merged, M4a merged |

**Notes:**
- M1A uses existing `set_ext_register`/`get_ext_register` on the system plane via `rpc.invoke`. M1B uses existing `get_register`/`set_register` (B509) on the system plane via `rpc.invoke`. No prerequisite gateway PR is needed for either probe set.
- M3 depends on M2 merged because it reuses the `configwrite` package extracted in M2.
- M4 splits into M4a (B524 entities, ships immediately after M2) and M4b (B509 entities, ships after M3). This allows B524 HA entities to ship without waiting for B509 validation.

---

## Proof Matrix

| Claim | Status | Evidence | Blocks |
|-------|--------|----------|--------|
| B524 controller registers 0x002C-0x0076 are readable | **Proven** | Live MCP probe 2026-03-11 | — |
| B524 CString writes are accepted by BASV2 | **Hypothesis** | Phase 0A will validate | M2: CString fields become read-only sensors if falsified |
| B524 CString maxLength = 6 | **Proven** | Docs: `ebus-vaillant-B524-register-map.md` line 261-264 | — |
| B524 CString null-padding behavior | **Unknown** | Phase 0A probe 2 will characterize (does controller pad to 6+null or accept shorter?) | M2: encode/readback logic |
| B524 installer_menu_code range 0..999 | **Proven** | Docs: register map line 266 | — |
| B524 date write format [DD,MM,YY] | **Hypothesis** | Inferred from HDA:3 read format; Phase 0A will validate | M2: date mutations disabled if falsified |
| B524 uint16 write acceptance (installerMenuCode) | **Hypothesis** | Phase 0A probe 6 will validate | M2: menu code mutation disabled if falsified |
| B509 register 0x4904 (Password) readable | **Hypothesis** | Phase 0B probe 1 will validate | M3: boiler menu code |
| B509 register 0x8104 (PhoneNumber) readable | **Hypothesis** | Phase 0B probe 2 will validate | M3: boiler phone number |
| B509 register 0x2004 (HoursTillService) readable | **Hypothesis** | Phase 0B probe 3 will validate | M3: hours till service |
| B509 UCH write works (opcode 0x0E) | **Hypothesis** | Phase 0B probe 4 will validate | M3: boiler menu code mutation |
| B509 HEX:8 write works (opcode 0x0E) | **Hypothesis** | Phase 0B probe 5 will validate | M3: boiler phone mutation |
| B509 hoursum2 is safely writable | **Unknown** | Service counter — plan designates read-only; no write probe performed | hoursTillService exposed as read-only sensor only |
| B509 `get_register`/`set_register` on system plane works for installer registers | **Hypothesis** | Existing RPC methods in ebusreg; validated by M1B probes | M3: all B509 features |
| Controller charset is ASCII-only | **Unknown** | Observational: if any existing register data contains bytes > 0x7F, charset is wider. Phase 0A cannot directly test this with ASCII-only payloads. Charset remains Unknown until non-ASCII data is encountered in production. Read-path sanitization handles both cases. | M2: read-path sanitization always active regardless |
| HA coordinator separate optional queries work without breaking main queries | **Hypothesis** | Design uses 4 independent optional queries; must be validated in M4 integration tests | M4: backward compat |
| Register 0x006E exists on other controllers | **Unknown** | Does not respond on this unit; out of scope | — |
| Registers 0x006A, 0x0075, 0x0077 purpose | **Unknown** | Adjacent user_RW; out of scope | — |

---

## Risks & Mitigations

| # | Risk | Severity | Mitigation | Status |
|---|------|----------|------------|--------|
| 1 | CString write format unproven on B524 | CRITICAL | Phase 0A live validation; fallback to read-only sensors | OPEN |
| 2 | B509 read/write unproven (per-register, per-type) | CRITICAL | Phase 0B per-type proof gates; each register/type independently gated | OPEN |
| 3 | HA backward-compat: new QUERY fields on old gateway | HIGH | 4 separate optional queries; main queries unchanged; per-source availability flags | MITIGATED (design) |
| 4 | Stale post-write semantic state (30-min poll) | HIGH | Write-through cache: immediate patch+publish after mutation | MITIGATED (design) |
| 5 | MCP tool missing classification/parity/tests | HIGH | Explicit checklist in Phase 4B/4C; test matrix in Phase 6 | MITIGATED (design) |
| 6 | Shared write logic private to graphql package | HIGH | Extract to `internal/configwrite/` in M2 (first gateway PR) | MITIGATED (design) |
| 7 | installerMenuCode secret exposure | HIGH | Tier 2 separate query + HA entity hidden+disabled by default | MITIGATED (design) |
| 8 | Charset: Latin-1 on read, ASCII-only on write | MEDIUM | Read-path sanitization + ASCII write enforcement | MITIGATED (design) |
| 9 | Date sentinel 2015-01-01 write hole | MEDIUM | Reject on encode + readback validation | MITIGATED (design) |
| 10 | Slow-poll implementation design | MEDIUM | Dedicated interval-based tier (same pattern as existing boiler tiers) | MITIGATED (design) |
| 11 | B509 register access via system plane RPC must work for installer registers | MEDIUM | Existing `get_register`/`set_register` in ebusreg already tested; M1B probes validate specific registers | MITIGATED (existing infrastructure) |
| 12 | M3 depends on M2 merged (configwrite extraction) | MEDIUM | Explicit dependency in milestone map; no parallel gateway PRs | MITIGATED (design) |
| 13 | Plan contract non-compliance | HIGH | Must rewrite into canonical chunked form before lock | OPEN |

---

## Critical Files

**Gateway:**
- `helianthus-ebusgateway/graphql/mutations.go` — core write logic, 4 new configValueTypes
- `helianthus-ebusgateway/cmd/gateway/semantic_vaillant.go` — poller reads, snapshot lifecycle, write-through
- `helianthus-ebusgateway/graphql/semantic.go` — SystemConfig + BoilerConfig types
- `helianthus-ebusgateway/graphql/queries.go` — GraphQL field resolvers
- `helianthus-ebusgateway/mcp/server.go` — MCP types + 2 new write tools
- `helianthus-ebusgateway/mcp/tool_classification_test.go` — tool classification
- `helianthus-ebusgateway/mcp/parity_contract_test.go` — parity contract hashes

**HA Integration:**
- `helianthus-ha-integration/custom_components/helianthus/coordinator.py` — query backward-compat
- `helianthus-ha-integration/custom_components/helianthus/text.py` — NEW
- `helianthus-ha-integration/custom_components/helianthus/date.py` — NEW
- `helianthus-ha-integration/custom_components/helianthus/number.py` — menu code entities
- `helianthus-ha-integration/custom_components/helianthus/sensor.py` — hours till service sensor (read-only)
- `helianthus-ha-integration/custom_components/helianthus/__init__.py` — platform registration

**Docs:**
- `helianthus-docs-ebus/protocols/ebus-vaillant-B524-register-map.md` — register reference
- `helianthus-docs-ebus/protocols/ebus-vaillant-B509-boiler-register-map.md` — BAI register reference

---

## Next Steps Before Lock

**Content convergence** (this document) must complete before formatting:

1. ✅ Content adversarial review convergence (Rounds 8-10 Codex, Rounds 11-12 Claude Opus — CONVERGED at R12: 0 P0, 0 P1)
2. Rewrite into canonical execution-plan format in `helianthus-execution-plans/` repo:
   - `writable-installer-maintenance.locked/plan.yaml`
   - `writable-installer-maintenance.locked/00-canonical.md`
   - `writable-installer-maintenance.locked/01-index.md`
   - `writable-installer-maintenance.locked/10-*.md` chunks (with Depends on / Scope / Idempotence / Falsifiability / Coverage headers)
   - `writable-installer-maintenance.locked/90-issue-map.md`
   - `writable-installer-maintenance.locked/91-milestone-map.md`
   - `writable-installer-maintenance.locked/99-status.md`
3. Final adversarial review round on canonical form (formatting + contract compliance)

**Phase 0 probes happen AFTER lock** — the plan is locked with Hypotheses. Probe results update `99-status.md` proof matrix, not the canonical plan itself. If probes falsify critical claims, a plan amendment is issued.
