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
| `ISSUE-DOC-01` | `helianthus-docs-ebus` | Entry points and stale-claim correction | merged | issue `Project-Helianthus/helianthus-docs-ebus#208`, PRs `#209` / `#210`, merge commits `c0b2ecd` / `a278af3`; `#208` closed after `#210` confirmed the rewritten docs realignment scope was exhausted |
| `ISSUE-DOC-02` | `helianthus-docs-ebus` | Create `DOC-04`, `DOC-05`, `DOC-06`, `DOC-09` draft contracts | merged | issue `Project-Helianthus/helianthus-docs-ebus#211`, PR `#212`, merge commit `577ac0d` |
| `ISSUE-DOC-03` | `helianthus-docs-ebus` | Create `DOC-07`, `DOC-08` protocol caveats and validation docs | merged | issue `Project-Helianthus/helianthus-docs-ebus#213`, PR `#214`, merge commit `7620102` |
| `ISSUE-DOC-04` | `helianthus-docs-ebus` | Rename and migrate stale B555 references | merged | issue `Project-Helianthus/helianthus-docs-ebus#215`, PR `#216`, merge commit `0da202a` |
| `ISSUE-EG-00` | `helianthus-ebusgo` | Add replay and testdata fixtures for observer hooks | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-GW-00` | `helianthus-ebusgateway` | Build gateway replay corpus for passive tap scenarios | merged | `Project-Helianthus/helianthus-ebusgateway#334` |

## M1

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-EG-01` | `helianthus-ebusgo` | Design TinyGo-safe observer interface and extend `BusConfig` | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-EG-02` | `helianthus-ebusgo` | Wire observer events into `protocol.Bus` | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-EG-03` | `helianthus-ebusgo` | Surface transport reset events for passive consumers | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-GW-17` | `helianthus-ebusgateway` | Bump `helianthus-ebusgo` pin after M1 ebusgo work | merged | `Project-Helianthus/helianthus-ebusgateway#334` |
| `ISSUE-GW-18` | `helianthus-ebusgateway` | Add passive-topology smoke coverage | merged | issue `Project-Helianthus/helianthus-ebusgateway#351`, PR `#354`, merge commit `ef4e64e`; parent proof artifact `results-matrix-ha/20260312T094435Z-pr354-parent-passive-p01-p06/index.json` records `P01..P06` all `pass`, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` records `P03..P06` all `pass` on gateway `ef4e64e` + proxy `a141fe0` |
| `ISSUE-GW-18A` | `helianthus-ebusgateway` | Investigate supported passive smoke failures on `P01..P05` | merged | issue `Project-Helianthus/helianthus-ebusgateway#352`; merged through parent PR `#354` (`ef4e64e`); final parent artifact records `P01..P05` all `pass` |
| `ISSUE-GW-18B` | `helianthus-ebusgateway` | Degrade cleanly on passive `ebusd-tcp` smoke negative path | merged | issue `Project-Helianthus/helianthus-ebusgateway#353`; merged through parent PR `#354` (`ef4e64e`); parent artifact and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` both record `P06` `pass` with `passive_mode=unsupported_or_misconfigured` |
| `ISSUE-GW-18C` | `helianthus-ebusgateway` | Supply an `ebusd`-compatible matrix config source for `P06` | merged | issue `Project-Helianthus/helianthus-ebusgateway#355`; merged through parent PR `#354` (`ef4e64e`); parent artifact and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` both record `P06` `pass` end-to-end |
| `ISSUE-GW-18D` | `helianthus-ebusgateway` | Correct the direct-adapter passive support/proof contract surfaced by `P01` / `P02` | merged | issue `Project-Helianthus/helianthus-ebusgateway#356`, stacked PR `#357`, merge commit `d5e4011`; final parent artifact records `P01` / `P02` `pass` with direct-adapter `passive_mode=unsupported_or_misconfigured` |
| `ISSUE-GW-18E` | `helianthus-ebusgateway` | Require active confirmation before imported-only startup success | merged | issue `Project-Helianthus/helianthus-ebusgateway#358`, stacked PR `#359`, merge commit `acad9a09`; converged in parent PR `#354` and final parent artifact |
| `ISSUE-GW-18F` | `helianthus-ebusgateway` | Fix `P03` proxy-single startup discovery timeout | merged | issue `Project-Helianthus/helianthus-ebusgateway#360`, stacked PR `#361`, merge commit `af922558`; converged in parent PR `#354`, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` reconfirms `P03=pass` |
| `ISSUE-GW-18G` | `helianthus-ebusgateway` | Fix `P03` active startup discovery through proxy-single ENS | merged | issue `Project-Helianthus/helianthus-ebusgateway#362`, stacked PR `#363`, merge commit `2d2870c`; converged in parent PR `#354`, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` reconfirms `P03=pass` |
| `ISSUE-GW-18H` | `helianthus-ebusgateway` | Fix `P03` startup source-address contract on proxy-single ENS | merged | issue `Project-Helianthus/helianthus-ebusgateway#364`, stacked PR `#365`, merge commit `25f3f92`; converged in parent PR `#354`, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` reconfirms `P03=pass` |
| `ISSUE-GW-18I` | `helianthus-ebusgateway` | Fix passive proxy-session contract on proxy-single ENS | merged | issue `Project-Helianthus/helianthus-ebusgateway#366`, stacked PR `#367`, merge commit `dc27960`; proxy issue `#80` / PR `#81` closed the remaining stream-shape gap, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` reconfirms `P03=pass` |
| `ISSUE-GW-18J` | `helianthus-ebusgateway` | Hold semantic startup barrier until post-scan B524 root coherence succeeds | merged | issue `Project-Helianthus/helianthus-ebusgateway#368`, stacked PR `#369`, merge commit `b26a55b`; converged in parent PR `#354`, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` reconfirms `P03=pass` |
| `ISSUE-GW-18K` | `helianthus-ebusgateway` | Align semantic poller B524 discovery source with proxy startup source on proxy-single ENS | merged | issue `Project-Helianthus/helianthus-ebusgateway#370`, stacked PR `#371`, merge commit `ccf759f`; converged in parent PR `#354`, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` reconfirms `P03=pass` |
| `ISSUE-GW-18L` | `helianthus-ebusgateway` | Fix proxy-single ENS passive observer classification so warmup can confirm availability | merged | issue `Project-Helianthus/helianthus-ebusgateway#372`, stacked PR `#373`, merge commit `bddf082`; focused artifact `results-matrix-ha/20260312T091947Z-proxy81-acb894c-gateway373-97da9f9-p03-rerun/index.json`, parent artifact, and merged-head rerun all pass |
| `ISSUE-GW-18M` | `helianthus-ebusgateway` | Add proxy ENS observer replay harness for passive reconstructor contract | merged | issue `Project-Helianthus/helianthus-ebusgateway#374`, stacked PR `#375`, merge commit `97da9f9`; PR `#375` adds the replay harness/tests, proxy issue `#80` / PR `#81` closes the routed stream-shape gap, and merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` reconfirms `P03=pass` |
| `ISSUE-GW-01` | `helianthus-ebusgateway` | Introduce `PassiveBusTap` | merged | `Project-Helianthus/helianthus-ebusgateway#335` |
| `ISSUE-GW-01B` | `helianthus-ebusgateway` | Implement `PassiveTransactionReconstructor` | merged | `Project-Helianthus/helianthus-ebusgateway#337` |
| `ISSUE-GW-01C` | `helianthus-ebusgateway` | Add active/passive deduplicator | merged | `Project-Helianthus/helianthus-ebusgateway#338`, follow-up `#340` |
| `ISSUE-GW-02` | `helianthus-ebusgateway` | Refactor `BroadcastListener` to consume classified passive events | merged | issue `Project-Helianthus/helianthus-ebusgateway#339`, PR `#341` |
| `ISSUE-GW-03` | `helianthus-ebusgateway` | Add `BusObservabilityStore` and Prometheus exporter | merged | issue `Project-Helianthus/helianthus-ebusgateway#342`, PR `#343`; review follow-up fixes settled in `#346` and the final `#343` merge |
| `ISSUE-GW-03A` | `helianthus-ebusgateway` | Bootstrap passive warmup when the store attaches after the tap is already connected | merged | issue `Project-Helianthus/helianthus-ebusgateway#344`; code landed via `Project-Helianthus/helianthus-ebusgateway#346` and final merge `#343` |
| `ISSUE-GW-03B` | `helianthus-ebusgateway` | Wire runtime local-address snapshotting into `local_participant_inbound` labeling | merged | issue `Project-Helianthus/helianthus-ebusgateway#345`; code landed via `Project-Helianthus/helianthus-ebusgateway#346` and final merge `#343` |
| `ISSUE-DOC-05` | `helianthus-docs-ebus` | Update docs after M1 implementation | merged | issue `Project-Helianthus/helianthus-docs-ebus#206`, PR `#207`, merge commit `4323a4c`; the documented passive contract is reconfirmed by merged-head rerun `results-matrix-ha/20260312T105720Z-main-ef4e64e-proxy-a141fe0-passive-p03-p06/index.json` |

## M2-M5

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-04` | `helianthus-ebusgateway` | Implement MCP observe-first tools | merged | issue `Project-Helianthus/helianthus-ebusgateway#376`, PR `#377`, merge commit `3daf4be`; passive proof artifact `results-matrix-ha/20260312T175648Z-pr377-gw04-26ee758-passive-p01-p06-recovery/index.json` records `P01..P06` all `pass`; standard `T01` probe `results-matrix-ha/20260312T175250Z-pr377-gw04-26ee758-recovery/full88-probe-t01-after-adapter-reboot/index.json` remained `blocked-infra` with `infra_reason=adapter_no_signal` after an adapter reboot, so merge proceeded under owner override once the official addon/runtime restore was re-verified clean |
| `ISSUE-DOC-06` | `helianthus-docs-ebus` | Freeze MCP contract against real output | merged | PR `#218`, merge commit `f037e16131e0efddbd825e4c3f2462f6163eec16`; `ISSUE-DOC-06` is now merged/closed and the `M2` docs freeze is complete |
| `ISSUE-GW-05` | `helianthus-ebusgateway` | Implement GraphQL parity | merged | issue `Project-Helianthus/helianthus-ebusgateway#378`, PR `#379`, merge commit `83e9c7b1ba927a282d87599269e91be817ff3582`; the gateway half of `M3` is now closed on `main` |
| `ISSUE-DOC-07` | `helianthus-docs-ebus` | Freeze GraphQL contract | merged | issue `Project-Helianthus/helianthus-docs-ebus#219`, PR `#220`, merge commit `cbdf89aa795083093631da7849df5e12e8d448c5`; `ISSUE-DOC-07` is now merged/closed and `M3` is fully closed on `main` |
| `ISSUE-GW-06` | `helianthus-ebusgateway` | Implement `WatchCatalog` | merged | issue `Project-Helianthus/helianthus-ebusgateway#380`, PR `#381`, merge commit `873c970459d1933ba50638df5e6fb349a6a9a3a2`; `ISSUE-GW-06` is now merged/closed on gateway `main` |
| `ISSUE-GW-07` | `helianthus-ebusgateway` | Implement bounded `ShadowCache` | merged | issue `Project-Helianthus/helianthus-ebusgateway#382`, PR `#385`, merge commit `9e9e6904e0337812ffa87591a83ad6f4a5c0ea44`; `ISSUE-GW-07` is now merged/closed on gateway `main` |
| `ISSUE-GW-08` | `helianthus-ebusgateway` | Add feature flags before behavior changes | merged | issue `Project-Helianthus/helianthus-ebusgateway#386`, PR `#387`, merge commit `23e46011f3c57d08148cf3cdd51acd6958303f90`; `ISSUE-GW-08` is now merged/closed on gateway `main` |
| `ISSUE-GW-09` | `helianthus-ebusgateway` | Implement family policy engine | merged | issue `Project-Helianthus/helianthus-ebusgateway#388`, PR `#389`, merge commit `db09bbae687912a16fbc9f0a2f3a5616b84931e8`; `ISSUE-GW-09` is now merged/closed on gateway `main` |
| `ISSUE-DOC-08` | `helianthus-docs-ebus` | Update architecture docs with watch, flags, and family rules | merged | issue `Project-Helianthus/helianthus-docs-ebus#221`, PR `#222`, merge commit `bf8587f41dedb3be8372b30cf7cd667abc1c0226`; `ISSUE-DOC-08` is now merged/closed on docs `main` |
| `ISSUE-GW-10` | `helianthus-ebusgateway` | Integrate `ShadowCache` into `SemanticReadScheduler` | merged | issue `Project-Helianthus/helianthus-ebusgateway#390`, PR `#391`, merge commit `75ee6aa639bb44e8e859835293ae3912dc4d7b48`; `ISSUE-GW-10` is now merged/closed on gateway `main` |
| `ISSUE-GW-11` | `helianthus-ebusgateway` | Add watch-summary surfaces | merged | issue `Project-Helianthus/helianthus-ebusgateway#392`, PR `#393`; `ISSUE-GW-11` is now merged/closed on gateway `main` |
| `ISSUE-GW-12` | `helianthus-ebusgateway` | Add watch-efficiency metrics | merged | issue `Project-Helianthus/helianthus-ebusgateway#394`, PR `#395`; `ISSUE-GW-12` is now merged/closed on gateway `main` |
| `ISSUE-DOC-09` | `helianthus-docs-ebus` | Freeze watch-summary and scheduler/shadow contracts | merged | PR `#224` (clean merge); `ISSUE-DOC-09` is now merged/closed and the `M5` doc-gate is closed |

## M6-M9

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-13` | `helianthus-ebusgateway` | Semantic publish groundwork for observe-first rollout | merged | issue `Project-Helianthus/helianthus-ebusgateway#396`, PR `#397`, merge commit `9f4a1df2837cbf075c03e9dc65b7419dceb9ae47`; required HA smoke passed externally on 2026-03-14 |
| `ISSUE-GW-14` | `helianthus-ebusgateway` | Portal rollout work for observe-first evidence surfaces | active | issue `Project-Helianthus/helianthus-ebusgateway#398`; next `M6` critical path after merged `ISSUE-GW-13` |
| `ISSUE-DOC-10` | `helianthus-docs-ebus` | Freeze Portal and semantic publish docs for M6 | blocked | not yet linked |
| `ISSUE-GW-15` | `helianthus-ebusgateway` | Proof gate and default-flip preparation | blocked | not yet linked |
| `ISSUE-GW-16` | `helianthus-ebusgateway` | Final validation and rollout gate work | blocked | not yet linked |
| `ISSUE-DOC-11` | `helianthus-docs-ebus` | Finalize proof and rollout docs | blocked | not yet linked |
| `ISSUE-TE-01` | `helianthus-tinyebus` | tinyebus M8 parallel-track groundwork | blocked | not yet linked |
| `ISSUE-TE-02` | `helianthus-tinyebus` | tinyebus M8 follow-up implementation work | blocked | not yet linked |
| `ISSUE-DOC-12` | `helianthus-docs-ebus` | tinyebus and final rollout documentation | blocked | not yet linked |
| `ISSUE-HA-01` | `helianthus-ha-integration` | Home Assistant consumer rollout | blocked | not yet linked |
