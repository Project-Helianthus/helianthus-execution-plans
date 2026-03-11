# Writable Installer/Maintenance Plan 04: Tests & Deployment Verification

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `34d2c8b70b8852a694fb09916744fe3670f3f386016de83d65c1f239b85213b7`

Depends on: `11-gateway-semantic-graphql.md` and `12-mcp-ha-integration.md`
(tests cover features defined in those chunks).

Scope: Complete test matrix for gateway (Go) and HA (Python) covering all 4
new value types, mutation wiring, MCP tool dispatch, coordinator backward-compat,
and end-to-end deployment verification steps.

Idempotence contract: Reapplying this chunk must not create duplicate test
functions. Test names and file locations are specified to prevent collision.

Falsifiability gate: A review fails this chunk if any new value type lacks
encode/decode/readback test coverage, if the HA backward-compat regression test
is missing, or if deployment steps don't account for degraded (probe-gated)
rollouts.

Coverage: Phase 6 (Tests) and Phase 7 (Deployment Verification) from the source
plan.

---

## Gateway Tests (Go)

### mutations_test.go / mutations_unit_test.go

`encodeConfigValue` for 4 new types:
- CString: empty, normal, max-len=6, too-long, non-ASCII 0x80, single null, all-spaces
- DateHDA3: valid ISO, invalid format, year boundaries, leap/non-leap Feb 29,
  Feb 30, sentinel 2015-01-01, day 0, month 13
- UCH: 0, 127, 255, 256 (reject), -1 (reject), non-integer (reject)
- Hex8: valid 16-char, odd-length, wrong-length (14/18), non-hex chars

`confirmDecodableReadback` for 4 types with edge cases.
`configReadbackMatchesWrite` including CString asymmetric null-padding.

### internal/configwrite/ package tests

Encode/decode round-trip for all 4 types. Value validation (hex, ASCII, range,
calendar). Readback comparison logic. Field spec resolution is NOT in this
package.

### B509 transport tests (existing)

`get_register`: request encoding + response decoding coverage exists.
`set_register`: request encoding exists; write-readback tested at gateway layer.
No new ebusreg-level tests needed.

### Read path charset tests (semantic_vaillant_test.go)

- `readB524CStringSanitized()`: Non-ASCII replacement, pure ASCII passthrough,
  all-null to empty
- `readB524CString()` base: Non-ASCII preserved (zone name regression guard)

### semantic_vaillant_test.go

- Snapshot merge/clone/equals for all new fields
- Slow-config tier interval behavior
- Write-through cache verification
- All new fields present in published snapshots

### mcp/server_test.go

- Tool dispatch for both set_config tools
- Tool classification: both `core_stable`
- Parity contract: new hash entries

### queries_test.go

- Field resolvers for all 9 new fields
- Mutation tests (valid, invalid field, out-of-range)

### Degraded-mode test strategy

All tests assume full write capability. If Phase 0 falsifies specific types,
corresponding mutation/tool tests are removed or converted to read-only-field
error tests. Compile-time decision.

## HA Tests (Python)

### test_text.py
- 5 text entities (4 B524 parts + 1 boiler phone)
- Write flows, ASCII/hex validation, empty/max-length edge cases

### test_date.py
- 1 date entity, date conversion, sentinel rejection

### test_number.py (additions)
- 2 menu code entities, hidden+disabled defaults, write flows

### test_sensor.py (additions)
- Hours Till Service: read-only, duration, diagnostic

### test_coordinator.py
- Backward-compat regression (CRITICAL): old gateway, main data intact
- Independent flag isolation: cross-source independence
- Sensitive independent of installer: step 3 fires regardless of step 2
- Cold start all-fail: schema errors, no retry
- Transient error recovery: transport error, retry next cycle
- Schema vs transient distinction

## Phase 7: Deployment Verification

Steps marked [write-gated] or [B509-gated] only apply if corresponding probes
passed. All MCP field names use snake_case.

1. Gateway binary deploy to RPi4
2. `system.get` -- confirm new config fields
3. [B509-gated] `boiler_status.get` -- confirm new config fields
4. [write-gated: CString] system.set_config installerName1 round-trip
5. [write-gated: DateHDA3] system.set_config maintenanceDate round-trip
6. [B509-gated, write-gated: UCH] boiler_status.set_config no-op writeback
7. HA deployment -- verify entities appear
8. [write-gated] HA write test -- maintenance date via UI
9. Backward-compat smoke: revert gateway, verify main queries intact
