# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | documentation skeletons and replay corpus | `helianthus-docs-ebus`, `helianthus-ebusgo`, `helianthus-ebusgateway` | none | implementing |
| `M1` | low-level instrumentation, passive tap, smoke coverage, and docs closure | `helianthus-ebusgo`, `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M0` | implementing |
| `M2` | MCP-first rollout | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M1` | queued |
| `M3` | GraphQL parity | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M2` | queued |
| `M4` | watch catalog, shadow cache, flags, family policy | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M3` | queued |
| `M5` | scheduler integration and watch surfaces | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M4` | queued |
| `M6` | semantic publish and Portal rollout | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M5` | queued |
| `M7` | proof gate and default flip | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M6` | queued |
| `M8` | tinyebus parallel track | `helianthus-tinyebus`, `helianthus-docs-ebus` | `ISSUE-GW-03` and `ISSUE-DOC-05` frozen | queued |
| `M9` | Home Assistant consumer rollout and final validation | `helianthus-ha-integration`, `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M7` | queued |

## Ordering Rules

- The default order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M9`.
- `M8` is the explicit parallel-track carve-out and does not start before the
  shared metric contract freezes at `ISSUE-GW-03` and `ISSUE-DOC-05`.
- `M1` remains implementing until `ISSUE-GW-18`, `ISSUE-GW-18A`,
  `ISSUE-GW-18B`, and `ISSUE-DOC-05` converge. The `GW-03A/B` extension opened
  from the post-matrix dual-review cycle on 2026-03-10 is now settled and
  merged through `ISSUE-GW-03`.
- The first clean `GW-18` passive suite artifact (`...gw18-passive-smoke-v4`)
  moved `M1` from “missing proof lane” to “proof lane exists, runtime failures
  exposed”; the new blockers are explicit rather than implicit.
- Locked decisions in `00-canonical.md` override milestone shorthand in this
  file if drift appears.
