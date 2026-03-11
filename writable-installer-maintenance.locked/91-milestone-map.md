# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | Document installer/maintenance registers (B524 + B509) | `helianthus-docs-ebus` | none | planned |
| `M1A` | B524 live bus probes (Phase 0A, operator notebook) | -- | none | planned |
| `M1B` | B509 live bus probes (Phase 0B, operator notebook) | -- | none | planned |
| `M2` | B524 installer/maintenance: configwrite + semantic + GraphQL + MCP | `helianthus-ebusgateway` | `M0`, `M1A` | blocked |
| `M3` | B509 installer/maintenance: semantic + GraphQL + MCP | `helianthus-ebusgateway` | `M0`, `M1B`, `M2` | blocked |
| `M4a` | B524 HA text/date/number entities + coordinator optional queries | `helianthus-ha-integration` | `M2` | blocked |
| `M4b` | B509 HA number/text entities (additive to M4a) | `helianthus-ha-integration` | `M3`, `M4a` | blocked |

## Ordering Rules

- The default order is `M0 -> M1 -> M2 -> M3 -> M4`.
- `M1A` and `M1B` are independent parallel tracks -- B524 failure does NOT
  block B509 and vice versa.
- `M2` is the first gateway PR: extracts `internal/configwrite` encoding
  utilities (ungated -- protocol-agnostic infrastructure) plus B524 surface
  (gated on `M1A`). If `M1A` fails entirely, `M2` still ships configwrite
  extraction with zero B524 field specs.
- `M3` depends on `M2` merged because it reuses the `configwrite` package.
- `M4` splits into `M4a` (B524 entities, ships after `M2`) and `M4b` (B509
  entities, ships after `M3`). This allows B524 HA entities to ship without
  waiting for B509 validation.
- If `M1B` fails entirely, `M3` is dropped; `M2` + `M4a` still ship.
- If `M1A` fails entirely (all reads fail), nothing ships for B524 installer
  surface. `M2` still ships as infrastructure-only. `M3` still proceeds if
  `M1B` passes.
- Locked decisions in `00-canonical.md` override milestone shorthand in this
  file if drift appears.

## PR Strategy

| Milestone | Repo | PR Summary | Depends On |
|-----------|------|----|------------|
| M0 | `helianthus-docs-ebus` | Document installer/maintenance registers | -- |
| M1A | -- | B524 live bus probes (operator notebook) | -- |
| M1B | -- | B509 live bus probes (operator notebook) | -- |
| M2 | `helianthus-ebusgateway` | B524 installer/maintenance: configwrite + semantic + GraphQL + MCP | M0, M1A |
| M3 | `helianthus-ebusgateway` | B509 installer/maintenance: semantic + GraphQL + MCP | M0, M1B, M2 |
| M4a | `helianthus-ha-integration` | B524 text/date/number entities + coordinator | M2 |
| M4b | `helianthus-ha-integration` | B509 number/text entities (additive) | M3, M4a |

## Proof Matrix

| Claim | Status | Blocks |
|-------|--------|--------|
| B524 registers 0x002C-0x0076 readable | Proven | -- |
| B524 CString writes accepted | Hypothesis | M2 |
| B524 date write format [DD,MM,YY] | Hypothesis | M2 |
| B524 uint16 write acceptance | Hypothesis | M2 |
| B509 register 0x4904 readable | Hypothesis | M3 |
| B509 register 0x8104 readable | Hypothesis | M3 |
| B509 register 0x2004 readable | Hypothesis | M3 |
| B509 UCH write works | Hypothesis | M3 |
| B509 HEX:8 write works | Hypothesis | M3 |
| HA optional queries backward-compat | Hypothesis | M4 |

## Risks

| # | Risk | Severity | Mitigation | Status |
|---|------|----------|------------|--------|
| 1 | CString write format unproven on B524 | CRITICAL | Phase 0A validation; fallback to read-only | OPEN |
| 2 | B509 read/write unproven per-register | CRITICAL | Phase 0B per-type proof gates | OPEN |
| 3 | HA backward-compat on old gateway | HIGH | 4 separate optional queries | MITIGATED |
| 4 | Stale post-write semantic state | HIGH | Write-through cache | MITIGATED |
| 5 | MCP tool classification/parity | HIGH | Explicit checklist | MITIGATED |
| 6 | Shared write logic private to graphql | HIGH | Extract to internal/configwrite | MITIGATED |
| 7 | installerMenuCode exposure | HIGH | Separate query + hidden+disabled | MITIGATED |
| 8 | Charset Latin-1/ASCII asymmetry | MEDIUM | Sanitized wrapper + ASCII write | MITIGATED |
| 9 | Date sentinel 2015-01-01 | MEDIUM | Reject on encode | MITIGATED |
| 10 | Slow-poll design | MEDIUM | Interval-based tier | MITIGATED |
| 11 | B509 register access RPC | MEDIUM | Existing infrastructure | MITIGATED |
| 12 | M3 depends on M2 | MEDIUM | Explicit dependency | MITIGATED |
| 13 | Plan contract non-compliance | HIGH | Canonical format rewrite | CLOSED |
