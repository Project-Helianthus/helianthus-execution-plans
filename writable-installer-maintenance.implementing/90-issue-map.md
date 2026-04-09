# Issue Map

Canonical IDs remain stable. Descriptions and statuses below are reconciled to
the implemented design and local merged evidence.

Status legend:
- `planned`: defined but not started
- `active`: open execution in this plan cycle
- `merged`: merged on target repo `main`
- `unarchived`: implemented lane exists but this plan lacks archived probe/run artifact links

## M0

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-DOC-01` | `helianthus-docs-ebus` | B524 installer/maintenance documentation lane | merged | commit `7c4fc5a` (`WIM-M0`) |
| `ISSUE-DOC-02` | `helianthus-docs-ebus` | B509 installer/maintenance documentation lane | merged | commit `7c4fc5a` (`WIM-M0`) |

## M1

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-PROBE-A` | -- | B524 probe evidence lane (operator notebook) | unarchived | no archived artifact linked in plan repo |
| `ISSUE-PROBE-B` | -- | B509 probe evidence lane (operator notebook) | unarchived | no archived artifact linked in plan repo |

## M2

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-01` | `helianthus-ebusgateway` | System writer wiring and immediate publish contract | merged | commit `c9c8f59` (`WIM-M2+M3`) |
| `ISSUE-GW-02` | `helianthus-ebusgateway` | `SystemConfig` extension with aggregated installer fields | merged | commit `c9c8f59` (`WIM-M2+M3`) |
| `ISSUE-GW-03` | `helianthus-ebusgateway` | B524 mutation/spec wiring for installer/maintenance fields | merged | commit `c9c8f59` (`WIM-M2+M3`) |
| `ISSUE-GW-04` | `helianthus-ebusgateway` | MCP `system.set_config` + classification/parity coverage | merged | commit `c9c8f59` (`WIM-M2+M3`) |

## M3

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-10` | `helianthus-ebusgateway` | `BoilerConfig` extension for installer/service fields | merged | commit `c9c8f59` (`WIM-M2+M3`) |
| `ISSUE-GW-11` | `helianthus-ebusgateway` | Boiler write path for menu code and phone handling | merged | commit `c9c8f59` (`WIM-M2+M3`) |
| `ISSUE-GW-12` | `helianthus-ebusgateway` | B509 read/publish lane for installer/service fields | merged | commit `c9c8f59` (`WIM-M2+M3`) |
| `ISSUE-GW-13` | `helianthus-ebusgateway` | MCP `boiler_status.set_config` tool and tests | merged | commit `c9c8f59` (`WIM-M2+M3`) |
| `ISSUE-GW-14` | `helianthus-ebusgateway` | `hoursTillService` read-only diagnostic contract | merged | commit `c9c8f59` (`WIM-M2+M3`) |

## M4

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-HA-01` | `helianthus-ha-integration` | Optional query split and availability flags | merged | commit `7c818c6` (`WIM-M4`) |
| `ISSUE-HA-02` | `helianthus-ha-integration` | `text.py` entities (system installer, boiler phone, sensitive menu codes) | merged | commit `7c818c6` (`WIM-M4`) |
| `ISSUE-HA-03` | `helianthus-ha-integration` | `date.py` maintenance entity | merged | commit `7c818c6` (`WIM-M4`) |
| `ISSUE-HA-04` | `helianthus-ha-integration` | Sensitive menu code policy (hidden + disabled defaults) | merged | commit `7c818c6` (`WIM-M4`) |
| `ISSUE-HA-05` | `helianthus-ha-integration` | `hoursTillService` read-only sensor | merged | commit `7c818c6` (`WIM-M4`) |
| `ISSUE-HA-06` | `helianthus-ha-integration` | Boiler optional query + merge path | merged | commit `7c818c6` (`WIM-M4`) |
| `ISSUE-HA-07` | `helianthus-ha-integration` | Backward-compat coordinator behavior lane | active | merged behavior present; explicit artifact backfill pending in plan repo |

