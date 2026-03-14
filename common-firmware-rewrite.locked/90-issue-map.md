# Issue Map

This plan uses canonical issue identifiers inside the split chunks. Target-repo
GitHub issue and PR linkage is backfilled here when it exists, but the
canonical IDs below remain the stable mapping surface for the workstream.

Status legend:
- `planned`: defined in the plan, GitHub issue not yet linked here
- `active`: current execution focus
- `merged`: canonical work merged on the target repo `main`
- `blocked`: depends on earlier milestone completion
- `optional`: gated feature lane that may remain intentionally unstarted

Cross-workstream note:
- observe-first canonical IDs `ISSUE-TE-01` and `ISSUE-TE-02` are re-homed
  here as deferred parallel-track tinyebus work.

## Cross-Workstream Re-Home Mapping

| Observe-first canonical ID | Re-home status | Primary owner in this plan | Follow-up owner(s) in this plan | Notes |
| --- | --- | --- | --- | --- |
| `ISSUE-TE-01` | deferred/re-homed | `ISSUE-CFW-T0-02` | `ISSUE-CFW-M1-02`, `ISSUE-CFW-M2-01` | tinyebus groundwork now executes under the firmware rewrite T0->M2 chain |
| `ISSUE-TE-02` | deferred/re-homed | `ISSUE-CFW-M3-01` | `ISSUE-CFW-M4-01`, `ISSUE-CFW-M8-01` | tinyebus follow-up and optional augmentation now execute under firmware rewrite M3+ |

## T0

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-T0-01` | `helianthus-docs-ebus` | Publish testing-first principles, feature eligibility draft, stress taxonomy, observability contract, proof templates, and harness architecture docs | planned | not yet linked |
| `ISSUE-CFW-T0-02` | `helianthus-tinyebus` | Freeze Go-oracle test vector export surface for SPEC and PARSE harnesses | planned | not yet linked |

## M0

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M0-01` | `helianthus-docs-ebus` | Record reference captures, HIL rig specs, RE test catalog, and family capability profile drafts | blocked | not yet linked |
| `ISSUE-CFW-M0-02` | `helianthus-tinyebus` | Backfill family characterisation fixtures and proof inputs discovered during hardware truth work | blocked | not yet linked |

## M1

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M1-01` | `helianthus-docs-ebus` | Finalise common behavioural contract, HAL docs, multi-client policy, and fault-injection plan | blocked | not yet linked |
| `ISSUE-CFW-M1-02` | `helianthus-tinyebus` | Land SPEC and PARSE oracle tests plus compile-clean harness stubs | blocked | not yet linked |

## M2

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M2-01` | `helianthus-tinyebus` | Build per-family proof tooling for memory, timing, counter layout, and Tier-B parser compilation | blocked | not yet linked |
| `ISSUE-CFW-M2-02` | `helianthus-ebusgo` | Provide host-side support needed by skeleton validation and compatibility comparison | blocked | not yet linked |

## M3

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M3-01` | `helianthus-tinyebus` | Implement ENH, ENS, and STD behavioural parity with mandatory observability counters from first functional firmware milestone | blocked | not yet linked |
| `ISSUE-CFW-M3-02` | `helianthus-docs-ebus` | Freeze protocol parity and observability compliance docs against firmware output | blocked | not yet linked |

## M4

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M4-01` | `helianthus-tinyebus` | Add network, reconnect, and fault-recovery behaviour per family | blocked | not yet linked |
| `ISSUE-CFW-M4-02` | `helianthus-ebus-adapter-proxy` | Align endpoint and reconnect expectations with firmware network behaviour | blocked | not yet linked |

## M5

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M5-01` | `helianthus-tinyebus` | Prove and implement optional multi-client support for eligible families | optional | not yet linked |
| `ISSUE-CFW-M5-02` | `helianthus-ebus-adapter-proxy` | Validate fairness and non-interference assumptions against multi-client firmware where enabled | optional | not yet linked |

## M6

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M6-01` | `helianthus-ebusgateway` | Integrate the full compatibility harness and topology runner against firmware artefacts | blocked | not yet linked |
| `ISSUE-CFW-M6-02` | `helianthus-ha-addon` | Package family-specific firmware validation paths in addon/runtime documentation where required | blocked | not yet linked |

## M7

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M7-01` | `helianthus-tinyebus` | Run soak, hardening, fault, observability, and cross-family parity gates | blocked | not yet linked |
| `ISSUE-CFW-M7-02` | `helianthus-docs-ebus` | Publish determinism, soak, and fault proof results as reusable knowledge | blocked | not yet linked |

## M8

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M8-01` | `helianthus-tinyebus` | Pursue tinyebus augmentation features only where proof-gated eligibility survives | optional | not yet linked |

## M9

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-CFW-M9-01` | `helianthus-tinyebus` | Cut release candidates per family with release-gate coverage and rollback docs | blocked | not yet linked |
| `ISSUE-CFW-M9-02` | `helianthus-docs-ebus` | Finalise doc-gate closure, release notes, and integration guidance | blocked | not yet linked |
