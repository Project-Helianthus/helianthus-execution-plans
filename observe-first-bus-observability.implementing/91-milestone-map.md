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
  `ISSUE-GW-18B`, `ISSUE-GW-18C`, `ISSUE-GW-18D`, `ISSUE-GW-18E`,
  `ISSUE-GW-18F`, `ISSUE-GW-18G`, `ISSUE-GW-18H`, `ISSUE-GW-18I`, and
  `ISSUE-DOC-05`
  converge. The `GW-03A/B` extension opened from the post-matrix dual-review
  cycle on 2026-03-10 is now settled and merged through `ISSUE-GW-03`.
- The first clean `GW-18` passive suite artifact (`...gw18-passive-smoke-v4`)
  moved `M1` from “missing proof lane” to “proof lane exists, runtime failures
  exposed”; the new blockers are explicit rather than implicit.
- The `P06` reruns `...gw18b-p06-v1` and `...gw18b-p06-v2` further narrowed the
  `ebusd-tcp` negative-path problem: startup degradation is now fixed in code,
  while the remaining proof gap is matrix `ebusd` config/image compatibility.
- After stacked merges `d5e4011` (`#357`) and `acad9a09` (`#359`) into
  `issue/351-passive-topology-smoke`, the next active `GW-18` proof step is a
  rerun on parent PR `#354`, resuming at `P03`; docs PR `#207` remains open and
  clean but does not close `M1` by itself.
- A new stacked lane `ISSUE-GW-18F` is now open as issue `#360` / PR `#361`
  on top of parent branch `issue/351-passive-topology-smoke`; this is still
  proof-remediation work inside `M1`, not proof closure.
- A further stacked lane `ISSUE-GW-18G` is now open as issue `#362` / PR `#363`
  on top of `ISSUE-GW-18F`; this is still proof-remediation work inside `M1`,
  not proof closure.
- A further stacked lane `ISSUE-GW-18H` is now open as issue `#364` / PR `#365`
  on top of `ISSUE-GW-18G`; this is still proof-remediation work inside `M1`,
  not proof closure.
- A further stacked lane `ISSUE-GW-18I` is now active on stacked PR `#369` at
  head `daaa1cb`; rerun artifact
  `results-matrix-ha/20260311T202655Z-issue369-p03-rerun` failed, so `#369`
  remains the active blocked lane and is not ready to fold upward into `#367` /
  parent PR `#354`. This is still proof-remediation work inside `M1`, not proof
  closure.
- Locked decisions in `00-canonical.md` override milestone shorthand in this
  file if drift appears.
