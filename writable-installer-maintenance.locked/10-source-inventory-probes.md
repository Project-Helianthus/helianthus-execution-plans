# Writable Installer/Maintenance Plan 01: Source Inventory & Live Bus Probes

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `34d2c8b70b8852a694fb09916744fe3670f3f386016de83d65c1f239b85213b7`

Depends on: None. This is the foundation chunk.

Scope: Dual-source register inventory (B524 controller + B509 boiler), source
ownership rules, Phase 0 live bus validation probes, and the degraded-mode
contract that gates all downstream milestones.

Idempotence contract: Reapplying this chunk must not create duplicate probe
sequences, conflicting source-ownership rules, or alter existing mutation
behavior. All probes follow read-save-mutate-restore and leave the bus in its
original state.

Falsifiability gate: A review fails this chunk if any probe is missing mandatory
RPC params (source, group, instance, addr, idempotency_key for MUTATE), if the
degraded-mode contract affects existing mutations (it must be field-additive
only), or if probe source addresses don't match the feature code mutation path.

Coverage: Context, Source-Ownership Rules, Source Inventory, Phase 0 (all of
Phase 0A, Phase 0B, Degraded-Mode Contract) from the source plan.

---

## Context

Add readable and writable maintenance/installer properties from two eBUS
sources -- the VRC controller (BASV2, B524) and the boiler (BAI00, B509) --
through a unified semantic, GraphQL, MCP, and HA integration surface.

Motivation: myVaillant app parity for installer contact info, maintenance
scheduling, and service menu codes -- editable directly from Home Assistant.

Design constraint: Both sources produce consistent but independent GraphQL/MCP
surfaces. Field naming follows a shared convention but each lives under its own
domain object (`system.config.*` vs `boilerStatus.config.*`).

## Source-Ownership Rules

Fields are never merged across B524 and B509. Each source owns its own domain:

| Domain | Owner | GraphQL Parent | MCP Parent | HA Entity Prefix |
|--------|-------|---------------|------------|-----------------|
| Controller installer/maintenance | VRC (B524, 0x15) | `system.config` | `ebus.v1.semantic.system` | `helianthus_` |
| Boiler installer/maintenance | BAI (B509, 0x08) | `boilerStatus.config` | `ebus.v1.semantic.boiler_status` | `helianthus_boiler_` |

Overlapping field names (e.g., `installerMenuCode`) exist in both domains but
are independent values with independent ranges (controller: 0..999 u16, boiler:
0..255 UCH). HA entities disambiguate via entity ID prefix.

## Source A: VRC Controller (BASV2, addr 0x15) -- B524 Protocol

| Register | Field | Type | Constraints | Status |
|----------|-------|------|-------------|--------|
| 0x002C | `maintenanceDate` | HDA:3 (3 bytes DD.MM.YY) | -- | Proven: read OK |
| 0x006C | `installerName1` | string | maxLength 6 | Proven: read OK |
| 0x006D | `installerName2` | string | maxLength 6 | Proven: read OK |
| 0x006F | `installerPhone1` | string | maxLength 6 | Proven: read OK |
| 0x0070 | `installerPhone2` | string | maxLength 6 | Proven: read OK |
| 0x0076 | `installerMenuCode` | u16 | 0..999 | Proven: read OK |
| 0x0096 | `maintenanceDue` | bool (u8) | -- | Proven: already in semantic layer |

Register 0x006E (between name2 and phone1): Unknown, does not respond.
Registers 0x006A, 0x0075, 0x0077: Unknown, out of scope.

## Source B: Boiler (BAI00, addr 0x08) -- B509 Protocol

| Register | Field | Type | Access | Status |
|----------|-------|------|--------|--------|
| 0x4904 | `password` (d.97) | UCH (1 byte) | r;ws | Hypothesis |
| 0x8104 | `phoneNumber` (d.98) | HEX:8 (8 bytes) | r;wi | Hypothesis |
| 0x2004 | `hoursTillService` (d.84) | hoursum2 (2 bytes) | r;wi | Hypothesis |
| 0x8204 | `language` (d.99) | UCH (1 byte) | r;ws | Hypothesis, out of scope |

## Phase 0A: B524 Controller Probes (BASV2 addr 0x15)

All probes via `rpc.invoke` with `set_ext_register`/`get_ext_register` on
`plane: "system"`, `address: 21`.

Mandatory RPC params:
- `source`: 49 (0x31 -- matches `mutationSourceAddr` at `mutations.go:87`)
- `group`: 0 (GG=0x00, Regulator group)
- `instance`: 0
- `addr`: register address (uint16 or hex string)
- `data`/`payload`: byte array for writes
- `intent`: `"MUTATE"` for write probes
- `allow_dangerous`: `true` for write probes
- `idempotency_key`: unique non-empty string per MUTATE call (mandatory)

All probes follow read-save-mutate-restore pattern.

1. CString write: Register 0x006C, write `[84,101,115,116,0,0]` ("Test")
2. CString width: Write `[65,66,67,68,69,70,0]` (7 bytes) to confirm maxLength 6
3. CString overflow: Write 8+ bytes, expect NAK or truncation
4. CString clear: Write `[0]` (single null byte)
5. Date write: Register 0x002C, write `[15,3,27]` (2027-03-15)
6. uint16 write: Register 0x0076, no-op writeback then different value

## Phase 0B: B509 Boiler Probes (BAI00 addr 0x08)

B509 register access already exists in `helianthus-ebusreg`:
- `get_register` -- B509 command 0x0D
- `set_register` -- B509 command 0x0E

Accessible via `rpc.invoke` on `plane: "system"`, `address: 8`.

Mandatory RPC params:
- `source`: 113 (0x71 -- matches `p.source` used by `writeB509Value()`)
- `addr`: register address
- `data`/`payload`: byte array for writes
- Write probes: `intent: "MUTATE"`, `allow_dangerous: true`, `idempotency_key`

Read probes:
1. `get_register(addr: 0x4904)` -- expect 1 byte UCH
2. `get_register(addr: 0x8104)` -- expect 8 bytes HEX:8
3. `get_register(addr: 0x2004)` -- expect 2 bytes hoursum2

Write probes (only for registers whose read succeeded):
4. UCH write: 0x4904, no-op writeback then different value
5. HEX:8 write: 0x8104, write `[0x54,0x65,0x73,0x74,0,0,0,0]`
6. hoursum2: intentionally read-only (service counter, no write probe)

## Degraded-Mode Contract

CRITICAL: Field-additive degradation only. Existing `setSystemConfig` and
`setBoilerConfig` mutations are UNAFFECTED. Degradation only affects new
installer/maintenance fields.

B524 degradation levels:
- All writes pass: 6 new field specs, MCP tool, writable HA entities
- Some writes fail: only proven-writable specs; failed = read-only sensors
- All writes fail: no new specs, no MCP tool; read-only sensors only
- All reads fail: nothing ships for B524 installer surface

B509 degradation levels: same pattern, independently gated per register/type.

Per-type proof gates for B509:
- UCH write proven: boiler menu code writable
- HEX:8 write proven: boiler phone writable
- hoursum2: read-only by design (sensor only, no write mutation)
