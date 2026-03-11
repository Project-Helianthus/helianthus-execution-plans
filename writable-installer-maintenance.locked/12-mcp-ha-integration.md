# Writable Installer/Maintenance Plan 03: MCP Server & HA Integration

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `34d2c8b70b8852a694fb09916744fe3670f3f386016de83d65c1f239b85213b7`

Depends on: `11-gateway-semantic-graphql.md` (Gateway types and mutations must
exist before MCP tools and HA entities can consume them).

Scope: MCP server write tools (Phase 4), HA integration coordinator queries,
entity platforms, backward-compat contract, and data merge strategy (Phase 5).

Idempotence contract: Reapplying this chunk must not create duplicate MCP tools,
duplicate HA entities, or conflicting coordinator query constants. New tools and
entities are additive. Existing MCP GET tool parity hashes are unaffected.

Falsifiability gate: A review fails this chunk if MCP tool classification is not
`core_stable` (mandatory per naming convention), if HA entities don't override
the `available` property (null != unavailable), if the data merge strategy is
absent, or if the backward-compat contract could break existing entities on old
gateways.

Coverage: Phases 4-5 from the source plan (MCP Server, HA Integration).

---

## Phase 4: MCP Server

File: `mcp/server.go`

### 4A: Types

Add JSON-tagged fields (snake_case) to MCP `SystemConfig` and `BoilerConfig`
structs. Update clone functions.

### 4B: `ebus.v1.semantic.system.set_config`

Tool args: `{ field: string, value: string }`. Return: standard envelope
`{meta, data, error}` with `data: {success: bool}`.

The `field` argument accepts camelCase Go field spec keys (matching GraphQL
mutation field names). MCP GET output uses snake_case JSON tags.

Must update: tool constants, dispatch, classification (`core_stable` -- mandatory
per `tool_classification_test.go:76-78`), parity contract (new hash entry),
server test coverage.

### 4C: `ebus.v1.semantic.boiler_status.set_config`

Same pattern as system.set_config for B509 boiler registers.

### Shared Write Logic

B524 and B509 write pipelines are structurally different. Shared in
`internal/configwrite/`: value validation, encoder/decoder functions, readback
comparison. Protocol-specific: field spec resolution, write execution.

MCP tools delegate to injected `SystemConfigWriter`/`BoilerConfigWriter`.

## Phase 5: HA Integration

### 5.1: Coordinator Query Updates

File: `coordinator.py`

CRITICAL backward-compat: Adding fields to existing queries causes whole-query
validation failure on older gateways. Solution: 4 separate optional queries.

New queries:
- `QUERY_SYSTEM_INSTALLER`: maintenanceDate, installerName1/2, installerPhone1/2
- `QUERY_SYSTEM_SENSITIVE`: installerMenuCode
- `QUERY_BOILER_INSTALLER`: phoneNumber, hoursTillService
- `QUERY_BOILER_SENSITIVE`: installerMenuCode

Per-source coordinator flags (4 independent booleans):
- `_system_installer_available`, `_system_sensitive_available`
- `_boiler_installer_available`, `_boiler_sensitive_available`

Error classification:
- Schema/validation error: flag False permanently (until HA restart)
- Transport/transient error: do NOT set False, retry next cycle

Data merge strategy:
- System: results merge into `data["config"]`
- Boiler: results merge into `data["boilerStatus"]["config"]`
- Entity access: `self.coordinator.data["config"].get("maintenanceDate")`

Entity availability:
- Each entity MUST override `available` property to check coordinator flag
- null field -> `native_value` returns None -> HA shows "unknown" (NOT "unavailable")
- flag False -> `available` returns False -> HA shows "unavailable"

### 5.2: Text Platform (text.py, NEW)

4 B524 text entities (raw parts, not combined):
- Installer Name Part 1/2, Installer Phone Part 1/2 (each maxLength 6)

1 B509 text entity:
- Boiler Phone Number (hex-encoded 8 bytes, native_max=16)

Input validation: ASCII-only for B524, hex-only for B509.
Properties: EntityCategory.CONFIG, TextMode.TEXT.

### 5.3: Date Platform (date.py, NEW)

1 writable DateEntity: Maintenance Date. Reject sentinel 2015-01-01 on write.
Properties: EntityCategory.CONFIG, icon mdi:calendar-clock.

### 5.4: Number / Sensor Entities

2 writable NumberEntity: Controller menu code (0-999), Boiler menu code (0-255).
Both: `entity_registry_visible_default=False`, `entity_registry_enabled_default=False`.
Note: `entity_registry_visible_default` is first-time use in this integration.

1 read-only sensor: Hours Till Service (SensorDeviceClass.DURATION, unit h,
EntityCategory.DIAGNOSTIC). Read-only -- B509 service counter must not be written.

### 5.5: Platform Registration

Add `"text"` and `"date"` to PLATFORMS list in `__init__.py`.
