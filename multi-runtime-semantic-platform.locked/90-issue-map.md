# Issue Map

Status: `Locked`
Baseline: `Gateway 0.4.0`
<!-- M625_RELEASE_PROJECTION_BEGIN -->
Release-proof control: `released_chain_redeployed`
S13 completion proof: `published_evidence_verified`
Cruise phase: `MSP-065-LIVE-R1`
Current milestone: `MSP-065-LIVE-R1`
LAB acceptance state: `accepted`
Selected batch: `MSP-065-LIVE-R1`
Accepted through: `M6.25 stable MCP and the bounded SPINE 1.3 erratum are accepted after released-chain redeploy, live 49-READ non-regression, and restart-persistence proof; zero promoted leaves`
<!-- M625_RELEASE_PROJECTION_END -->
Successor unlocks: `only through the M6.25 and live-completion chain`
Amendment: `M6.25 bounded SPINE 1.3 erratum`

This map preserves historical evidence and adds the M6.25/live-completion rows
without rewriting M0-M6. One active PR per repo remains mandatory.

## Dependency guidance

`92-m0-issue-matrix.yaml` records dependency guidance. Current readiness comes from GitHub and the owning code repositories.
This page deliberately does not duplicate routing contracts, provider or model selections,
or predecessor edges. Neither this page nor the matrix authorizes a successor or changes
repository state.

## Historical Accepted Evidence

| ID | Repo | Issue | PR | Merge commit | Acceptance state |
| --- | --- | --- | --- | --- | --- |
| MSP-00A/MSP-00B/MSP-00C | `helianthus-execution-plans` | [#33](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/33), [#32](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/32), [#34](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/34) | [#35](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/35), [#37](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/37) | `2860d742e2682fbc42d1a5d98906031a0ff3e45d`, `93ef8cebadf842ebdffb5f3a0eb34806d5766ff5` | accepted |
| MSP-01A | `helianthus-docs-ebus` | [#333](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/333) | [#334](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/334) | `55f5482e0513ceb3bed8ddd5f2656d3b3ae7be41` | accepted |
| MSP-01B/MSP-01C | `helianthus-docs-eebus` | [#1](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/1), [#2](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/2) | [#3](https://github.com/Project-Helianthus/helianthus-docs-eebus/pull/3) | `9d3637e09d9573d9d7f31bdda86b1039770ba41b` | accepted |
| MSP-020 | `helianthus-eebusreg` | [#1](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/1), [#2](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/2) | [#3](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/3) | `f441e4a1987f775367ad3046e68ba1caf04b2f20` | accepted |
| MSP-02A | `helianthus-eebusreg` | [#4](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/4) | [#5](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/5) | `28d2f8162b67ea274c089ed1686c9ce84b054e7d` | accepted |
| MSP-02B | `helianthus-eebusreg` | [#6](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/6) | [#7](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/7) | `c064c0d1d19cd0c392734bede136f55040b76c67` | accepted |
| MSP-02C | `helianthus-docs-ebus` | [#335](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/335) | [#336](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/336) | `70a4921f287116f539cb4ce522ee9809cd9bf3c6` | accepted |
| MSP-03A | `helianthus-eebusreg` | [#8](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/8) | [#9](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/9) | `2b5b06315bd873dc214f602e9c5e9d0d6922208b` | accepted |
| MSP-03B | `helianthus-eebusreg` | [#10](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/10) | [#11](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/11) | `82f8f3cfd42d8e5c830d1e8e4e9e029614c14a7e` | accepted |
| MSP-03C | `helianthus-ha-addon` | [#166](https://github.com/Project-Helianthus/helianthus-ha-addon/issues/166), [execution-plans #48](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/48) | [#167](https://github.com/Project-Helianthus/helianthus-ha-addon/pull/167) | `b3c9930ca244dfe636f79356b8d482c6c84e043c` | accepted |
| MSP-03C doc-gate | `helianthus-docs-ebus` | [#337](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/337) | [#338](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/338) | `c1fc6bde5a273fdd1ccbe1826479769fe0731a71` | accepted |
| MSP-03D-G01 | `helianthus-eebusreg` | [#12](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/12), [execution-plans #50](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/50) | [#13](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/13) | `0e58327dfdb86ef243a19e18d590564813feaa00` | EEBUS-G01 fake peer accepted only; MSP-03D and M3 remain open |

## Hard Blockers

- Current dispatch decisions require current GitHub and owning-repository state.
- Base M6.25 LAB remains accepted and
  `lab_release_proof=released_chain_redeployed` remains unchanged.
- The bounded SPINE 1.3 erratum is completed under the independent
  `s13_completion_proof=published_evidence_verified` control.
- M6 topology and live counts do not prove canonical typed feature-data
  acquisition.
- Historical `MSP-065`, `MSP-07`, `MSP-08`, and `MSP-085` closure cannot
  make any `*-LIVE-R1` row ready.
- Public write denial must occur before every downstream contact.
- M9 is blocked until `MSP-085-LIVE-R1` completes and
  `promoted_leaf_count > 0`.

## M6.25 Additive Rows

| ID | Repo | Purpose | State |
| --- | --- | --- | --- |
| MSP-0625-PLAN | `helianthus-execution-plans` | Publish additive contract and DAG | completed_published |
| MSP-0625-DOCS-E | `helianthus-docs-eebus` | Freeze SPINE data/operation, runtime, and API contract | completed_published |
| MSP-0625-SPINE | `helianthus-spine-go` | Atomic correlated callback-before-send round-trip | completed_published |
| MSP-0625-EEBUS | `helianthus-eebus-go` | Exact full READ/WRITE feature executor | completed_published |
| MSP-0625-REG-EXEC | `helianthus-eebusreg` | `RawFeatureRuntimeV1`, epochs, generations, DTOs, reads | completed_published |
| MSP-0625-REG-MUT | `helianthus-eebusreg` | WAL/FSM, lease, CAS, idempotency, rollback, audit | completed_published |
| MSP-0625-GW-ROUTER | `helianthus-ebusgateway` | Add `EEBusCommandRouter` policy boundary | completed_published |
| MSP-0625-GW-MCP | `helianthus-ebusgateway` | Register the exact five M6.25 tool suffixes | completed_published |
| MSP-0625-LAB | `helianthus-docs-eebus` | Public-safe live acquisition/mutation/rollback evidence | see release-proof projection |
| MSP-0625-DOCS-P | `helianthus-docs-ebus` | Thin public methodology cross-seed | completed_published |

## M6.25 SPINE 1.3 Erratum Rows

| ID | Issue | Purpose | State |
| --- | --- | --- | --- |
| MSP-0625-S13-DOCS | `helianthus-docs-eebus#96` | Freeze bounded SPINE 1.3 scope and 49/26/23 public READ baseline | completed_published |
| MSP-0625-S13-SPINE | `helianthus-spine-go#15` | Apply only pinned value-type and function-data corrections | completed_published |
| MSP-0625-S13-EEBUS | `helianthus-eebus-go#23` | Adopt corrected SPINE 1.3 types in existing exact READ execution | completed_published |
| MSP-0625-S13-REG | `helianthus-eebusreg#103` | Preserve DTO/JCS/binding contracts for corrected READ results | completed_published |
| MSP-0625-S13-GW-LAB | `helianthus-ebusgateway#762` | Integrate and prove aggregate READ outcomes with zero mutation | completed_published |

The issue chain is strict in table order. The DOCS row requires accepted
`MSP-0625-LAB` plus completed `MSP-0625-DOCS-P`. The final GW-LAB token is the
only predecessor appended to existing row `MSP-065-LIVE-R1`; all old edges and
both old LIVE-R1 predecessors remain exact.
`MSP-065-LIVE-R1` is the sole current and initial ready row.

The exact five M6.25 tool suffixes, fail-closed no-write stop,
`candidate_ref` prohibition, and owner-local raw/public-redacted boundary
remain unchanged. Public evidence contains only aggregate counts and the three
commitments in record 123, never raw identity. SPINE 1.4, upstream `dev`
wholesale merge, `9970150` key/update-engine changes, and duplicate
`9f07e2a`/`06d9bf0` cherry-picks are excluded.

The append-only correction is tracked by
[`helianthus-execution-plans#82`](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/82).
[`helianthus-docs-eebus#78`](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/78)
must merge before
[`helianthus-eebusreg#85`](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/85)
proceeds beyond strict test-only RED. This refines the existing docs gate and
does not add or reorder a row.

## Preserved Historical And Live Rows

| Row family | Classification | Dependency meaning |
| --- | --- | --- |
| `MSP-065` | `framework_complete` | none for live chain |
| `MSP-07`, `MSP-08`, `MSP-085` | `synthetic_only` | none for live chain |
| `MSP-065-LIVE-R1` -> `MSP-07-LIVE-R1` -> `MSP-08-LIVE-R1` -> `MSP-085-LIVE-R1` | proposed live chain | predecessor order only |
| `MSP-09A` through `MSP-09D` | not started substantively | require live M8.5 plus positive promoted-leaf count |

## Historical AD-DOCS-02 dependency chain

The matrix records `MSP-DOCS-CLEAN` and `MSP-03C` as predecessors of
`MSP-03D-R`; `MSP-03D-G01` is evidence-only. Current GitHub state and
implementation-repository evidence determine whether work may proceed.

- No publication of MSP-R00 private details: local SHA, private path, raw HMAC
  mapping, source-bundle detail, raw paths, volume, sizes, timestamps, bytes,
  deterministic IDs, raw hashes, or sensitive evidence.
- No runtime successor unlock from dirty code existence.
- No public artifact may contain packet captures, raw transcripts, keys, PEM,
  tokens, trust stores, raw SKI, raw SHIPID, raw IP/MAC address, or raw serial.
- No `helianthus-eebusreg/docs/` on clean main and no substantive code-repo
  protocol, architecture, API, harness, test, or user documentation.
- No gateway import before canonical docs and eebusreg contracts merge.
- No GraphQL, Portal, HA, or promoted semantics before the live per-leaf lock.
