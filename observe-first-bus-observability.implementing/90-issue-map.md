# Issue Map

This plan uses canonical issue identifiers inside the split chunks. GitHub issue
numbers may be created later in the target repositories, but the canonical IDs
below remain the stable mapping surface for the plan itself.

Status legend:
- `planned`: defined in the plan, GitHub issue not yet linked here
- `active`: current execution focus
- `blocked`: depends on earlier milestone completion

## M0

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-DOC-01` | `helianthus-docs-ebus` | Create `DOC-01`, `DOC-02`, `DOC-03` skeleton docs | active |
| `ISSUE-DOC-02` | `helianthus-docs-ebus` | Create `DOC-04`, `DOC-05`, `DOC-06`, `DOC-09` draft contracts | active |
| `ISSUE-DOC-03` | `helianthus-docs-ebus` | Create `DOC-07`, `DOC-08` protocol caveats and validation docs | planned |
| `ISSUE-DOC-04` | `helianthus-docs-ebus` | Rename and migrate stale B555 references | planned |
| `ISSUE-EG-00` | `helianthus-ebusgo` | Add replay and testdata fixtures for observer hooks | planned |
| `ISSUE-GW-00` | `helianthus-ebusgateway` | Build gateway replay corpus for passive tap scenarios | planned |

## M1

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-EG-01` | `helianthus-ebusgo` | Design TinyGo-safe observer interface and extend `BusConfig` | blocked |
| `ISSUE-EG-02` | `helianthus-ebusgo` | Wire observer events into `protocol.Bus` | blocked |
| `ISSUE-EG-03` | `helianthus-ebusgo` | Surface transport reset events for passive consumers | blocked |
| `ISSUE-GW-17` | `helianthus-ebusgateway` | Bump `helianthus-ebusgo` pin after M1 ebusgo work | blocked |
| `ISSUE-GW-18` | `helianthus-ebusgateway` | Add passive-topology smoke coverage | blocked |
| `ISSUE-GW-01` | `helianthus-ebusgateway` | Introduce `PassiveBusTap` | blocked |
| `ISSUE-GW-01B` | `helianthus-ebusgateway` | Implement `PassiveTransactionReconstructor` | blocked |
| `ISSUE-GW-01C` | `helianthus-ebusgateway` | Add active/passive deduplicator | blocked |
| `ISSUE-GW-02` | `helianthus-ebusgateway` | Refactor `BroadcastListener` to consume classified passive events | blocked |
| `ISSUE-GW-03` | `helianthus-ebusgateway` | Add `BusObservabilityStore` and Prometheus exporter | blocked |
| `ISSUE-DOC-05` | `helianthus-docs-ebus` | Update docs after M1 implementation | blocked |

## M2-M5

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-04` | `helianthus-ebusgateway` | Implement MCP observe-first tools | blocked |
| `ISSUE-DOC-06` | `helianthus-docs-ebus` | Freeze MCP contract against real output | blocked |
| `ISSUE-GW-05` | `helianthus-ebusgateway` | Implement GraphQL parity | blocked |
| `ISSUE-DOC-07` | `helianthus-docs-ebus` | Freeze GraphQL contract | blocked |
| `ISSUE-GW-06` | `helianthus-ebusgateway` | Implement `WatchCatalog` | blocked |
| `ISSUE-GW-07` | `helianthus-ebusgateway` | Implement bounded `ShadowCache` | blocked |
| `ISSUE-GW-08` | `helianthus-ebusgateway` | Add feature flags before behavior changes | blocked |
| `ISSUE-GW-09` | `helianthus-ebusgateway` | Implement family policy engine | blocked |
| `ISSUE-DOC-08` | `helianthus-docs-ebus` | Update architecture docs with watch, flags, and family rules | blocked |
| `ISSUE-GW-10` | `helianthus-ebusgateway` | Integrate `ShadowCache` into `SemanticReadScheduler` | blocked |
| `ISSUE-GW-11` | `helianthus-ebusgateway` | Add watch-summary surfaces | blocked |
| `ISSUE-GW-12` | `helianthus-ebusgateway` | Add watch-efficiency metrics | blocked |
| `ISSUE-DOC-09` | `helianthus-docs-ebus` | Freeze watch-summary and scheduler/shadow contracts | blocked |

## M6-M9

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-GW-13` | `helianthus-ebusgateway` | Semantic publish groundwork for observe-first rollout | blocked |
| `ISSUE-GW-14` | `helianthus-ebusgateway` | Portal rollout work for observe-first evidence surfaces | blocked |
| `ISSUE-DOC-10` | `helianthus-docs-ebus` | Freeze Portal and semantic publish docs for M6 | blocked |
| `ISSUE-GW-15` | `helianthus-ebusgateway` | Proof gate and default-flip preparation | blocked |
| `ISSUE-GW-16` | `helianthus-ebusgateway` | Final validation and rollout gate work | blocked |
| `ISSUE-DOC-11` | `helianthus-docs-ebus` | Finalize proof and rollout docs | blocked |
| `ISSUE-TE-01` | `helianthus-tinyebus` | tinyebus M8 parallel-track groundwork | blocked |
| `ISSUE-TE-02` | `helianthus-tinyebus` | tinyebus M8 follow-up implementation work | blocked |
| `ISSUE-DOC-12` | `helianthus-docs-ebus` | tinyebus and final rollout documentation | blocked |
| `ISSUE-HA-01` | `helianthus-ha-integration` | Home Assistant consumer rollout | blocked |
