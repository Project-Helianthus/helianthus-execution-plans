# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | documentation skeletons and replay corpus | `helianthus-docs-ebus`, `helianthus-ebusgo`, `helianthus-ebusgateway` | none | merged |
| `M1` | low-level instrumentation, passive tap, smoke coverage, and docs closure | `helianthus-ebusgo`, `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M0` | merged |
| `M2` | MCP-first rollout | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M1` | merged |
| `M3` | GraphQL parity | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M2` | merged |
| `M4` | watch catalog, shadow cache, flags, family policy | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M3` | merged |
| `M5` | scheduler integration and watch surfaces | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M4` | merged |
| `M6` | semantic publish and Portal rollout | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M5` | merged |
| `M7` | proof gate and default-state decision | `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M6` | merged |
| `M8` | tinyebus parallel track (re-homed to `common-firmware-rewrite.locked`) | `helianthus-tinyebus`, `helianthus-docs-ebus` | `ISSUE-GW-03` and `ISSUE-DOC-05` frozen | deferred/re-homed |
| `M9` | Home Assistant consumer rollout and final validation | `helianthus-ha-integration`, `helianthus-ebusgateway`, `helianthus-docs-ebus` | `M7` | merged |

## Ordering Rules

- The default order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M9`.
- `M8` is the explicit parallel-track carve-out and does not start before the
  shared metric contract freezes at `ISSUE-GW-03` and `ISSUE-DOC-05`.
- In this observe-first plan, `ISSUE-TE-01` and `ISSUE-TE-02` are now tracked
  as deferred and re-homed to `common-firmware-rewrite.locked`; the
  `ISSUE-DOC-12` final-rollout-doc tail is deferred and non-blocking.
- `M0` is now fully merged on `main`. `ISSUE-DOC-01` is merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#208` and PRs `#209` / `#210`;
  `ISSUE-DOC-02` is now merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#211`, PR `#212`, merge commit
  `577ac0d`; `ISSUE-DOC-03` is now merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#213`, PR `#214`, merge commit
  `7620102`; `ISSUE-DOC-04` is now merged via docs issue
  `Project-Helianthus/helianthus-docs-ebus#215`, PR `#216`, merge commit
  `0da202a`. The replay-corpus half of `M0` is already merged through
  `ISSUE-EG-00` and `ISSUE-GW-00`.
- `M1` is now merged on `main`: gateway PR `#354` (`ef4e64e`), proxy PR `#81`
  (`a141fe0`), and docs PR `#207` (`4323a4c`) all landed on 2026-03-12.
- Final parent artifact
  `results-matrix-ha/20260312T094435Z-pr354-parent-passive-p01-p06/index.json`
  records `P01..P06` all `pass`.
- Fresh merged-head passive rerun
  `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json`
  records `P03..P06` all `pass` on gateway `ef4e64e` and proxy `a141fe0`.
- No `GW-18`-family gateway issue and no related proxy/docs issue remains open
  on GitHub. The final tail issue, `ISSUE-GW-18M` /
  `Project-Helianthus/helianthus-ebusgateway#374`, is closed; proxy issue
  `Project-Helianthus/helianthus-ebus-adapter-proxy#80` and docs issue
  `Project-Helianthus/helianthus-docs-ebus#206` are also closed.
- The parent artifact plus the merged-head rerun freeze the merged
  transport/proof contract for `M1`:
  `P01` / `P02` prove the corrected direct-adapter contract with
  `passive_mode=unsupported_or_misconfigured`; `P03` / `P04` / `P05` prove the
  required passive-capable proxy paths on merged gateway/proxy heads; and
  `P06` proves the `ebusd-tcp` negative-path contract with
  `passive_mode=unsupported_or_misconfigured` on merged heads.
- `M2` is now merged on the merged `M1` baseline: `ISSUE-GW-04` landed via
  gateway issue `Project-Helianthus/helianthus-ebusgateway#376`, PR `#377`,
  merge commit `3daf4be`, and `ISSUE-DOC-06` landed via docs PR `#218`,
  merge commit
  `f037e16131e0efddbd825e4c3f2462f6163eec16`. `ISSUE-DOC-06` is now
  merged/closed, so the MCP docs freeze is complete.
- `M3` is now merged on `main`: `ISSUE-GW-05` landed via gateway issue
  `Project-Helianthus/helianthus-ebusgateway#378`, PR `#379`, merge commit
  `83e9c7b1ba927a282d87599269e91be817ff3582`, and `ISSUE-DOC-07` landed via
  docs issue `Project-Helianthus/helianthus-docs-ebus#219`, PR `#220`, merge
  commit `cbdf89aa795083093631da7849df5e12e8d448c5`. The GraphQL contract is
  now frozen on the merged `M3` surface.
- `M4` is now merged on `main`: `ISSUE-GW-08` landed via gateway issue
  `Project-Helianthus/helianthus-ebusgateway#386`, PR `#387`, merge commit
  `23e46011f3c57d08148cf3cdd51acd6958303f90`.
- `ISSUE-GW-09` is now merged/closed on gateway `main` via issue
  `Project-Helianthus/helianthus-ebusgateway#388`, PR `#389`, merge commit
  `db09bbae687912a16fbc9f0a2f3a5616b84931e8`.
- `ISSUE-DOC-08` is now merged/closed on docs `main` via issue
  `Project-Helianthus/helianthus-docs-ebus#221`, PR `#222`, merge commit
  `bf8587f41dedb3be8372b30cf7cd667abc1c0226`.
- `ISSUE-GW-10` is now merged/closed on gateway `main` via issue
  `Project-Helianthus/helianthus-ebusgateway#390`, PR `#391`, merge commit
  `75ee6aa639bb44e8e859835293ae3912dc4d7b48`.
- `ISSUE-GW-11` is now merged/closed on gateway `main` via issue
  `Project-Helianthus/helianthus-ebusgateway#392`, PR `#393`.
- `ISSUE-GW-12` is now merged/closed on gateway `main` via issue
  `Project-Helianthus/helianthus-ebusgateway#394`, PR `#395`.
- `ISSUE-DOC-09` is now merged/closed on docs `main` via PR `#224`.
- `M5` is now fully merged on `main`.
- `ISSUE-GW-14` is now merged/closed on gateway `main` via issue
  `Project-Helianthus/helianthus-ebusgateway#398`, PR `#399`, merge commit
  `858e0ec75ad7ba6004e7af62f9043d8304fbd362`, after required HA smoke passed
  on 2026-03-14.
- `M6` is now fully merged on `main`: `ISSUE-GW-13` landed via gateway issue
  `Project-Helianthus/helianthus-ebusgateway#396`, PR `#397`, merge commit
  `9f4a1df`; `ISSUE-GW-14` landed via gateway issue
  `Project-Helianthus/helianthus-ebusgateway#398`, PR `#399`, merge commit
  `858e0ec`; and `ISSUE-DOC-10` landed via docs issue
  `Project-Helianthus/helianthus-docs-ebus#225`, PR `#226`, merge commit
  `5ab82fb`.
- `M7` is now fully merged on `main`. `ISSUE-GW-15` and `ISSUE-GW-16` are
  merged/closed on gateway `main`, and `ISSUE-DOC-11` landed via docs issue
  `Project-Helianthus/helianthus-docs-ebus#229`, PR `#230`, merge commit
  `fc63c43af7dc5cf5d8882ea54dc3920c60ef88cd`.
- `M9` is also now closed on the explicit optional-rollout no-op path:
  `ISSUE-HA-01` is linked to
  `Project-Helianthus/helianthus-ha-integration#170`, which was closed on
  2026-03-29 after confirming the HA integration remains a semantic GraphQL
  consumer with parity guardrails and does not need a new observe-first
  diagnostics surface for this plan closure.
- Locked decisions in `00-canonical.md` override milestone shorthand in this
  file if drift appears.
