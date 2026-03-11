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
| `ISSUE-DOC-01` | `helianthus-docs-ebus` | Create `DOC-01`, `DOC-02`, `DOC-03` skeleton docs | planned | not yet linked |
| `ISSUE-DOC-02` | `helianthus-docs-ebus` | Create `DOC-04`, `DOC-05`, `DOC-06`, `DOC-09` draft contracts | planned | not yet linked |
| `ISSUE-DOC-03` | `helianthus-docs-ebus` | Create `DOC-07`, `DOC-08` protocol caveats and validation docs | planned | not yet linked |
| `ISSUE-DOC-04` | `helianthus-docs-ebus` | Rename and migrate stale B555 references | planned | not yet linked |
| `ISSUE-EG-00` | `helianthus-ebusgo` | Add replay and testdata fixtures for observer hooks | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-GW-00` | `helianthus-ebusgateway` | Build gateway replay corpus for passive tap scenarios | merged | `Project-Helianthus/helianthus-ebusgateway#334` |

## M1

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-EG-01` | `helianthus-ebusgo` | Design TinyGo-safe observer interface and extend `BusConfig` | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-EG-02` | `helianthus-ebusgo` | Wire observer events into `protocol.Bus` | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-EG-03` | `helianthus-ebusgo` | Surface transport reset events for passive consumers | merged | `Project-Helianthus/helianthus-ebusgo#116` |
| `ISSUE-GW-17` | `helianthus-ebusgateway` | Bump `helianthus-ebusgo` pin after M1 ebusgo work | merged | `Project-Helianthus/helianthus-ebusgateway#334` |
| `ISSUE-GW-18` | `helianthus-ebusgateway` | Add passive-topology smoke coverage | active | `Project-Helianthus/helianthus-ebusgateway#351`, PR `#354`; first clean suite artifact `results-matrix-ha/20260311T062516Z-gw18-passive-smoke-v4/index.json` exposed follow-ups |
| `ISSUE-GW-18A` | `helianthus-ebusgateway` | Investigate supported passive smoke failures on `P01..P05` | active | `Project-Helianthus/helianthus-ebusgateway#352` |
| `ISSUE-GW-18B` | `helianthus-ebusgateway` | Degrade cleanly on passive `ebusd-tcp` smoke negative path | active | `Project-Helianthus/helianthus-ebusgateway#353`, code in PR `#354`; reruns `P06 v1/v2` moved the remaining blocker to matrix harness compatibility |
| `ISSUE-GW-18C` | `helianthus-ebusgateway` | Supply an `ebusd`-compatible matrix config source for `P06` | active | `Project-Helianthus/helianthus-ebusgateway#355`, current proof artifacts `results-matrix-ha/20260311T064844Z-gw18b-p06-v1` and `results-matrix-ha/20260311T065409Z-gw18b-p06-v2` |
| `ISSUE-GW-18D` | `helianthus-ebusgateway` | Correct the direct-adapter passive support/proof contract surfaced by `P01` / `P02` | active | issue `Project-Helianthus/helianthus-ebusgateway#356`, stacked PR `#357` reviewed clean by Codex and squash-merged into `issue/351-passive-topology-smoke` as `d5e4011`; parent PR `#354` remains the active draft proof lane |
| `ISSUE-GW-18E` | `helianthus-ebusgateway` | Require active confirmation before imported-only startup success | active | issue `Project-Helianthus/helianthus-ebusgateway#358`, stacked PR `#359` squash-merged into `issue/351-passive-topology-smoke` as `acad9a09`; parent PR `#354` remains open/draft and the next proof rerun resumes from `P03` |
| `ISSUE-GW-18F` | `helianthus-ebusgateway` | Fix `P03` proxy-single startup discovery timeout | active | issue `Project-Helianthus/helianthus-ebusgateway#360`, stacked PR `#361` from `issue/360-p03-proxy-single-startup-timeout` into parent branch `issue/351-passive-topology-smoke`; latest head `8529569`, parent PR `#354` remains open/draft |
| `ISSUE-GW-18G` | `helianthus-ebusgateway` | Fix `P03` active startup discovery through proxy-single ENS | active | issue `Project-Helianthus/helianthus-ebusgateway#362`, stacked PR `#363` from `issue/362-p03-active-startup-through-proxy-single` into `issue/360-p03-proxy-single-startup-timeout`; latest head `916bc455`, parent PR `#354` remains open/draft and `#361` remains open |
| `ISSUE-GW-18H` | `helianthus-ebusgateway` | Fix `P03` startup source-address contract on proxy-single ENS | active | issue `Project-Helianthus/helianthus-ebusgateway#364`, stacked PR `#365` from `issue/364-p03-startup-source-addr-contract` into `issue/362-p03-active-startup-through-proxy-single`; latest head `78eacdb2`, `#363` remains open and parent PR `#354` remains open/draft |
| `ISSUE-GW-18I` | `helianthus-ebusgateway` | Fix passive proxy-session contract on proxy-single ENS | active | issue `Project-Helianthus/helianthus-ebusgateway#366`, stacked PR `#373` on the `GW-18I` proof chain; latest head `0b5292e`, rerun artifact `results-matrix-ha/20260312T000413Z-issue373-p03-rerun` failed after reaching `LIVE_READY` with all four devices present, and `#373` remains the active blocked lane not ready to fold upward into `#371` / `#369` / `#367` / parent PR `#354` |
| `ISSUE-GW-01` | `helianthus-ebusgateway` | Introduce `PassiveBusTap` | merged | `Project-Helianthus/helianthus-ebusgateway#335` |
| `ISSUE-GW-01B` | `helianthus-ebusgateway` | Implement `PassiveTransactionReconstructor` | merged | `Project-Helianthus/helianthus-ebusgateway#337` |
| `ISSUE-GW-01C` | `helianthus-ebusgateway` | Add active/passive deduplicator | merged | `Project-Helianthus/helianthus-ebusgateway#338`, follow-up `#340` |
| `ISSUE-GW-02` | `helianthus-ebusgateway` | Refactor `BroadcastListener` to consume classified passive events | merged | issue `Project-Helianthus/helianthus-ebusgateway#339`, PR `#341` |
| `ISSUE-GW-03` | `helianthus-ebusgateway` | Add `BusObservabilityStore` and Prometheus exporter | merged | issue `Project-Helianthus/helianthus-ebusgateway#342`, PR `#343`; review follow-up fixes settled in `#346` and the final `#343` merge |
| `ISSUE-GW-03A` | `helianthus-ebusgateway` | Bootstrap passive warmup when the store attaches after the tap is already connected | merged | issue `Project-Helianthus/helianthus-ebusgateway#344`; code landed via `Project-Helianthus/helianthus-ebusgateway#346` and final merge `#343` |
| `ISSUE-GW-03B` | `helianthus-ebusgateway` | Wire runtime local-address snapshotting into `local_participant_inbound` labeling | merged | issue `Project-Helianthus/helianthus-ebusgateway#345`; code landed via `Project-Helianthus/helianthus-ebusgateway#346` and final merge `#343` |
| `ISSUE-DOC-05` | `helianthus-docs-ebus` | Update docs after M1 implementation | active | issue `Project-Helianthus/helianthus-docs-ebus#206`, PR `#207`; same-cycle docs follow-up amended for the passive transport contract, reviewed clean by Codex, still open, and not merged |

## M2-M5

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-04` | `helianthus-ebusgateway` | Implement MCP observe-first tools | blocked | not yet linked |
| `ISSUE-DOC-06` | `helianthus-docs-ebus` | Freeze MCP contract against real output | blocked | not yet linked |
| `ISSUE-GW-05` | `helianthus-ebusgateway` | Implement GraphQL parity | blocked | not yet linked |
| `ISSUE-DOC-07` | `helianthus-docs-ebus` | Freeze GraphQL contract | blocked | not yet linked |
| `ISSUE-GW-06` | `helianthus-ebusgateway` | Implement `WatchCatalog` | blocked | not yet linked |
| `ISSUE-GW-07` | `helianthus-ebusgateway` | Implement bounded `ShadowCache` | blocked | not yet linked |
| `ISSUE-GW-08` | `helianthus-ebusgateway` | Add feature flags before behavior changes | blocked | not yet linked |
| `ISSUE-GW-09` | `helianthus-ebusgateway` | Implement family policy engine | blocked | not yet linked |
| `ISSUE-DOC-08` | `helianthus-docs-ebus` | Update architecture docs with watch, flags, and family rules | blocked | not yet linked |
| `ISSUE-GW-10` | `helianthus-ebusgateway` | Integrate `ShadowCache` into `SemanticReadScheduler` | blocked | not yet linked |
| `ISSUE-GW-11` | `helianthus-ebusgateway` | Add watch-summary surfaces | blocked | not yet linked |
| `ISSUE-GW-12` | `helianthus-ebusgateway` | Add watch-efficiency metrics | blocked | not yet linked |
| `ISSUE-DOC-09` | `helianthus-docs-ebus` | Freeze watch-summary and scheduler/shadow contracts | blocked | not yet linked |

## M6-M9

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-13` | `helianthus-ebusgateway` | Semantic publish groundwork for observe-first rollout | blocked | not yet linked |
| `ISSUE-GW-14` | `helianthus-ebusgateway` | Portal rollout work for observe-first evidence surfaces | blocked | not yet linked |
| `ISSUE-DOC-10` | `helianthus-docs-ebus` | Freeze Portal and semantic publish docs for M6 | blocked | not yet linked |
| `ISSUE-GW-15` | `helianthus-ebusgateway` | Proof gate and default-flip preparation | blocked | not yet linked |
| `ISSUE-GW-16` | `helianthus-ebusgateway` | Final validation and rollout gate work | blocked | not yet linked |
| `ISSUE-DOC-11` | `helianthus-docs-ebus` | Finalize proof and rollout docs | blocked | not yet linked |
| `ISSUE-TE-01` | `helianthus-tinyebus` | tinyebus M8 parallel-track groundwork | blocked | not yet linked |
| `ISSUE-TE-02` | `helianthus-tinyebus` | tinyebus M8 follow-up implementation work | blocked | not yet linked |
| `ISSUE-DOC-12` | `helianthus-docs-ebus` | tinyebus and final rollout documentation | blocked | not yet linked |
| `ISSUE-HA-01` | `helianthus-ha-integration` | Home Assistant consumer rollout | blocked | not yet linked |
