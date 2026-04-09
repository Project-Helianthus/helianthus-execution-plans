# Writable Maintenance & Installer Properties — Implementing Canonical

Revision: `v2.0-design-reconciled`
Date: `2026-04-09`
Status: `Implementing`

## Summary

This canonical was reconciled after implementation landed on `main`. It records
the **implemented design** (including post-implementation design corrections),
not the earlier locked assumptions.

Scope remains the same: expose writable installer and maintenance surfaces from
controller (`B524`) and boiler (`B509`) through semantic, GraphQL, MCP, and HA.

## 1. Implemented Design Corrections

The following corrections are now canonical:

1. Controller installer text fields are exposed as **aggregated values**:
   - `installerName` (aggregates registers `0x006C` + `0x006D`)
   - `installerPhone` (aggregates registers `0x006F` + `0x0070`)
   - Max length exposed at API/UI is `12`, not two separate `6`-char fields.
2. Menu code entities are exposed as **text entities** (zero-padded digits),
   not as `number.py` entities.
3. Boiler phone is handled as **digit-string UX with BCD wire encoding** in
   gateway/HA write paths. The prior locked `HEX:8` user-facing assumption is
   superseded by this implemented behavior.
4. `hoursTillService` remains **read-only** (diagnostic sensor).
5. The implementation did **not** extract an `internal/configwrite/` package.
   Writer wiring and codecs were delivered in existing gateway paths.

## 2. Source Ownership (unchanged)

| Domain | Owner | GraphQL Parent | MCP Parent | HA Prefix |
| --- | --- | --- | --- | --- |
| Controller installer/maintenance | BASV2 (B524, `0x15`) | `system.config` | `ebus.v1.semantic.system` | `helianthus_` |
| Boiler installer/maintenance | BAI00 (B509, `0x08`) | `boilerStatus.config` | `ebus.v1.semantic.boiler_status` | `helianthus_boiler_` |

No cross-source merge is allowed. Same field names across sources are
independent values.

## 3. Canonical Field Contract (implemented)

### 3.1 Controller (`system.config`)

| Field | Backing registers | Type | Write |
| --- | --- | --- | --- |
| `maintenanceDate` | `0x002C` | ISO date string | yes |
| `installerName` | `0x006C` + `0x006D` | string (max 12) | yes |
| `installerPhone` | `0x006F` + `0x0070` | string (max 12) | yes |
| `installerMenuCode` | `0x0076` | int `0..999` | yes |

Implementation notes:
- Aggregated string writes split into two B524 CString registers.
- `installerPhone` write validation allows digits and `+() `.
- Successful writes patch snapshot immediately and publish.

### 3.2 Boiler (`boilerStatus.config`)

| Field | Backing register | Type | Write |
| --- | --- | --- | --- |
| `installerMenuCode` | `0x4904` | int `0..255` | yes |
| `phoneNumber` | `0x8104` | digit string (max 16 digits) | yes (BCD encoded on wire) |
| `hoursTillService` | `0x2004` | int hours | no (read-only) |

Implementation notes:
- Boiler phone writer strips formatting and encodes digits to 8-byte BCD.
- Boiler menu code writer enforces `0..255`.
- `hoursTillService` is intentionally not writable.

## 4. Gateway / MCP / HA Surfaces (implemented)

### 4.1 Gateway

- GraphQL `SystemConfig` includes:
  `maintenanceDate`, `installerName`, `installerPhone`, `installerMenuCode`.
- GraphQL `BoilerConfig` includes:
  `installerMenuCode`, `phoneNumber`, `hoursTillService`.
- `SystemConfigWriter` path is wired and used by `setSystemConfig`.
- Boiler write path includes explicit handlers for `phoneNumber` and
  `installerMenuCode`.

### 4.2 MCP

- `ebus.v1.semantic.system.set_config` exists.
- `ebus.v1.semantic.boiler_status.set_config` exists.
- Classification/parity entries exist in gateway MCP tests.

### 4.3 HA Integration

Implemented entity surfaces:
- `text.py`:
  - system: `installerName`, `installerPhone`
  - boiler: `phoneNumber`
  - sensitive text entities: both `installerMenuCode` fields
- `date.py`:
  - system `maintenanceDate`
- `sensor.py`:
  - boiler `hoursTillService` diagnostic sensor (read-only)
- `__init__.py` platform list includes `text` and `date`.

Coordinator backward-compat model:
- Optional installer/sensitive queries are split by source and isolated with
  independent availability flags.

## 5. Milestones and Evidence (local workspace)

### M0 — Docs lane

- Evidence commit on docs: `7c4fc5a` (`WIM-M0`)
- Ancestor of `origin/main`: yes

### M1A / M1B — Probe lane

- Earlier plan expected explicit probe artifacts before feature code.
- Implementation proceeded and merged; explicit probe artifacts are not linked
  in this plan directory.
- Canonical stance: lane treated as functionally satisfied by merged behavior,
  but evidence archive is incomplete.

### M2 + M3 — Gateway lane

- Evidence commit on gateway: `c9c8f59` (`WIM-M2+M3`)
- Ancestor of `origin/main`: yes

### M4 — HA lane

- Evidence commit on HA integration: `7c818c6` (`WIM-M4`)
- Ancestor of `origin/main`: yes

## 6. Canonical Issue Split (reconciled)

The IDs remain stable for plan tracking. Their descriptions are aligned to the
implemented shape.

### M0

- `ISSUE-DOC-01`: B524 installer/maintenance docs lane (`7c4fc5a`)
- `ISSUE-DOC-02`: B509 installer/maintenance docs lane (`7c4fc5a`)

### M1

- `ISSUE-PROBE-A`: B524 probes (not archived here)
- `ISSUE-PROBE-B`: B509 probes (not archived here)

### M2 (controller gateway lane)

- `ISSUE-GW-01`: system writer wiring + immediate publish
- `ISSUE-GW-02`: `SystemConfig` surface extension (aggregated fields)
- `ISSUE-GW-03`: B524 mutation/spec wiring for installer/maintenance
- `ISSUE-GW-04`: MCP `system.set_config` delivery and test contracts
- Linked execution evidence: gateway commit `c9c8f59`

### M3 (boiler gateway lane)

- `ISSUE-GW-10`: `BoilerConfig` extension (installer/menu/service fields)
- `ISSUE-GW-11`: boiler write path for menu code + phone handling
- `ISSUE-GW-12`: B509 read/publish coverage for installer/service fields
- `ISSUE-GW-13`: MCP `boiler_status.set_config` delivery and tests
- `ISSUE-GW-14`: `hoursTillService` read-only diagnostic contract
- Linked execution evidence: gateway commit `c9c8f59`

### M4 (HA lane)

- `ISSUE-HA-01`: optional query separation and availability flags
- `ISSUE-HA-02`: `text.py` entities (system installer + boiler phone + menu code)
- `ISSUE-HA-03`: `date.py` maintenance entity
- `ISSUE-HA-04`: sensitive menu-code policy in UI entities
- `ISSUE-HA-05`: `hoursTillService` sensor contract
- `ISSUE-HA-06`: boiler optional query and data merge path
- `ISSUE-HA-07`: backward-compat behavioral coverage lane
- Linked execution evidence: HA commit `7c818c6`

## 7. Open Gaps Keeping This Plan in `.implementing`

1. Plan repo tracking files were stale and are now being reconciled in this
   cycle.
2. Probe evidence for `M1A/M1B` is not archived in this plan directory.
3. Docs wording still needs a final consistency pass against aggregated
   controller field naming and BCD phone write semantics if any mismatch
   remains outside the merged docs lane.

## 8. Exit Criteria to Move to `.maintenance`

1. `90-issue-map.md`, `91-milestone-map.md`, and `99-status.md` fully aligned
   with merged evidence and residual gaps.
2. Explicit decision recorded for M1 evidence handling:
   - either backfill probe artifacts, or
   - formally waive probe artifact backfill based on merged runtime evidence.
3. No unresolved canonical drift between this file and implemented gateway/HA
   behavior.

