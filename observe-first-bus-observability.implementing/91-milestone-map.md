# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | documentation skeletons and replay corpus | `helianthus-docs-ebus`, `helianthus-ebusgo`, `helianthus-ebusgateway` | none | implementing |
| `M1` | low-level instrumentation, passive tap, smoke coverage, and docs closure | `helianthus-ebusgo`, `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M0` | merged |
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
- `M0` remains implementing only because the docs-canonicalization items
  `ISSUE-DOC-01`, `ISSUE-DOC-02`, `ISSUE-DOC-03`, and `ISSUE-DOC-04` are still
  unlinked/unmerged on `helianthus-docs-ebus` `main`. The replay-corpus half of
  `M0` is already merged through `ISSUE-EG-00` and `ISSUE-GW-00`.
- `M1` is now merged on `main`: gateway PR `#354` (`ef4e64e`), proxy PR `#81`
  (`a141fe0`), and docs PR `#207` (`4323a4c`) all landed on 2026-03-12.
- Final parent artifact
  `results-matrix-ha/20260312T094435Z-pr354-parent-passive-p01-p06/index.json`
  records `P01..P06` all `pass`.
- The last open gateway `GW-18`-family issue, `ISSUE-GW-18M` /
  `Project-Helianthus/helianthus-ebusgateway#374`, is now satisfied on merged
  `main`: gateway PR `#375` (`97da9f9`) added the replay harness/tests, proxy
  PR `#81` (`a141fe0`) resolved the routed stream-shape defect, and the final
  parent artifact confirms `P03=pass`.
- That final artifact freezes the merged transport/proof contract for `M1`:
  `P01` / `P02` prove the corrected direct-adapter contract with
  `passive_mode=unsupported_or_misconfigured`, `P03` / `P04` / `P05` prove the
  required passive-capable proxy paths, and `P06` proves the `ebusd-tcp`
  negative-path contract with `passive_mode=unsupported_or_misconfigured`.
- `M2` remains queued until the earlier `M0` docs-canonicalization backlog is
  reconciled and a fresh MCP-first issue set is opened from the merged `M1`
  baseline.
- Locked decisions in `00-canonical.md` override milestone shorthand in this
  file if drift appears.
