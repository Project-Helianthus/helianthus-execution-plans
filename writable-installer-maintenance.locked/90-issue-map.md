# Issue Map

This plan uses canonical issue identifiers inside the split chunks. Target-repo
GitHub issue and PR linkage is backfilled here when it exists, but the
canonical IDs below remain the stable mapping surface for the plan itself.

Status legend:
- `planned`: defined in the plan, GitHub issue not yet linked here
- `active`: current execution focus
- `merged`: canonical work merged on the target repo `main`
- `blocked`: depends on earlier milestone completion

## M0

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-DOC-01` | `helianthus-docs-ebus` | Document B524 installer/maintenance registers (0x002C, 0x006C-0x0070, 0x0076) | planned | not yet linked |
| `ISSUE-DOC-02` | `helianthus-docs-ebus` | Document B509 installer/maintenance registers (0x4904, 0x8104, 0x2004) | planned | not yet linked |

## M1

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-PROBE-A` | -- | B524 live bus probes (Phase 0A, operator notebook) | planned | not yet linked |
| `ISSUE-PROBE-B` | -- | B509 live bus probes (Phase 0B, operator notebook) | planned | not yet linked |

## M2

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-01` | `helianthus-ebusgateway` | Extract `internal/configwrite` encoding utilities | blocked | not yet linked |
| `ISSUE-GW-02` | `helianthus-ebusgateway` | SystemConfig type extension (6 new fields) | blocked | not yet linked |
| `ISSUE-GW-03` | `helianthus-ebusgateway` | SystemConfigWriter injection + write-through cache | blocked | not yet linked |
| `ISSUE-GW-04` | `helianthus-ebusgateway` | B524 systemConfigFieldSpecs (4 new configValueTypes) | blocked | not yet linked |
| `ISSUE-GW-05` | `helianthus-ebusgateway` | MCP system.set_config tool + classification + parity | blocked | not yet linked |
| `ISSUE-GW-06` | `helianthus-ebusgateway` | B524 slow-config poller tier reads | blocked | not yet linked |
| `ISSUE-GW-07` | `helianthus-ebusgateway` | readB524CStringSanitized charset wrapper | blocked | not yet linked |

## M3

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-10` | `helianthus-ebusgateway` | BoilerConfig type extension (3 new fields) | blocked | not yet linked |
| `ISSUE-GW-11` | `helianthus-ebusgateway` | B509 pipeline type generalization (float64 -> union) | blocked | not yet linked |
| `ISSUE-GW-12` | `helianthus-ebusgateway` | B509 boilerConfigFieldSpecs (UCH + Hex8 codecs) | blocked | not yet linked |
| `ISSUE-GW-13` | `helianthus-ebusgateway` | MCP boiler_status.set_config tool | blocked | not yet linked |
| `ISSUE-GW-14` | `helianthus-ebusgateway` | B509 slow-config poller tier reads | blocked | not yet linked |

## M4

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-HA-01` | `helianthus-ha-integration` | System coordinator optional queries + flags | blocked | not yet linked |
| `ISSUE-HA-02` | `helianthus-ha-integration` | text.py platform (4 B524 + 1 B509 text entities) | blocked | not yet linked |
| `ISSUE-HA-03` | `helianthus-ha-integration` | date.py platform (maintenance date entity) | blocked | not yet linked |
| `ISSUE-HA-04` | `helianthus-ha-integration` | number.py additions (2 menu code entities) | blocked | not yet linked |
| `ISSUE-HA-05` | `helianthus-ha-integration` | sensor.py addition (hours till service sensor) | blocked | not yet linked |
| `ISSUE-HA-06` | `helianthus-ha-integration` | Boiler coordinator optional queries + flags (M4b) | blocked | not yet linked |
| `ISSUE-HA-07` | `helianthus-ha-integration` | Backward-compat coordinator regression tests | blocked | not yet linked |
