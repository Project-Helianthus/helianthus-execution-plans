# Writable Installer/Maintenance Plan 03: MCP Server & HA Integration

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `76ba52c1c0e115e69fec268ade5d5291bb47dedae4b6c6d42649fadb14143da7`

Implementation reconciliation note (2026-04-09):
- HA menu code surfaces are text entities with hidden/disabled defaults.
- Controller installer fields are aggregated in coordinator/query contract.
- Boiler phone UX is digit-string; gateway performs BCD encoding.

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

B524 and B509 write pipelines are structurally different, but the delivered
shape keeps both behind the injected `SystemConfigWriter` /
`BoilerConfigWriter` paths. Validation/encoding lives in the existing gateway
mutation + semantic writer flow; there is no required `internal/configwrite/`
package in the implemented design.

## Phase 5: HA Integration

### 5.1: Coordinator Query Updates

File: `coordinator.py`

CRITICAL backward-compat: Adding fields to existing queries causes whole-query
validation failure on older gateways. Solution: 4 separate optional queries.

New queries:
- `QUERY_SYSTEM_INSTALLER`: maintenanceDate, installerName, installerPhone
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

Delivered text entities:
- System `installerName` (maxLength 12)
- System `installerPhone` (maxLength 12)
- Boiler `phoneNumber` (maxLength 16, digit-string UX)
- System `installerMenuCode` (sensitive text entity)
- Boiler `installerMenuCode` (sensitive text entity)

Input validation:
- system installer name: printable ASCII
- system installer phone: digits and `+() `
- boiler phone: digit-string UX normalized before BCD encoding in gateway
- menu code text entities: digit-only with range enforcement by source

Properties: `EntityCategory.CONFIG`, `TextMode.TEXT`.

### 5.3: Date Platform (date.py, NEW)

1 writable DateEntity: Maintenance Date. Reject sentinel 2015-01-01 on write.
Properties: EntityCategory.CONFIG, icon mdi:calendar-clock.

### 5.4: Sensor / Sensitive-Entity Contract

- No installer menu-code `number.py` entities in the implemented design.
- Both menu-code surfaces live in `text.py` with hidden/disabled defaults.
- `hoursTillService` is a read-only diagnostic sensor
  (`SensorDeviceClass.DURATION`, unit `h`, `EntityCategory.DIAGNOSTIC`).

### 5.5: Platform Registration

Add `"text"` and `"date"` to PLATFORMS list in `__init__.py`.
