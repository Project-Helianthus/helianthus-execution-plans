# Execution Roadmap, Issues, And Gates

Canonical-SHA256: `71bd97f3eb9939bfb7e1f472f9e8aa79bd01a195a9917b0e1740eeaf0d42dfcc`

Depends on:
All previous chunks.

Scope:
Defines issue slicing, model routing, validation gates, review gates, recovery
reconciliation, and locked execution criteria for the raw-first eeBUS VR940f
path.

Idempotence contract:
The roadmap may be converted into issues repeatedly. Duplicate issue creation
must be avoided by checking the issue map first. One active PR per repo remains
mandatory, and dirty local rescue code never unlocks successors.

Falsifiability gate:
Each issue must have a testable gate. If implementers cannot prove the gate
without subjective judgment, the issue is not ready for locked execution.

Coverage:
Covers the executable milestone order, recovery reconciliation, M0 control
plane, doc gates, transport/security gates, and consumer promotion gates.

## Required Row Contract

Every row in `92-m0-issue-matrix.yaml` must include:

- issue id, repo, milestone, complexity from 1 to 10, and exact GPT-only model
  lane;
- predecessor edges, including explicit empty predecessor lists;
- canonical docs owner and doc-gate result;
- transport and security gate classification;
- rollback ledger, review ledger, TDD mode, smoke scope, and acceptance list.

Model lanes are fixed for this plan:

- complexity 1-2: `GPT-5.3-Codex-Spark`;
- complexity 3-4: `gpt-5.4-mini`;
- complexity 5: `GPT-5.5 medium`;
- complexity 6-7: `GPT-5.5 high`;
- complexity 8-10: `GPT-5.5 xhigh`.

No other model lane is valid for this plan.

## Locked Milestone Order

1. `RECOVERY_RECONCILIATION`
2. `M3 - eeBUS Runtime Feasibility` completion by clean-main MSP-03D-R only
3. `M3.5 - Raw Runtime Contract Freeze`
4. `M4 - Store, Raw View, Lifecycle Facade, And Trust Security`
5. `M4.5 - Trust And Admin State Freeze`
6. `M5 - Gateway Sidecar Integration`
7. `M6 - Read-Only eeBUS MCP v1`
8. `M6.5 - Synchronized Evidence Recorder`
9. `M7 - Draft Candidate Fact Graph`
10. `M8 - Multi-Runtime Coexistence`
11. `M8.5 - Leaf Promotion Lock`
12. `M9 - GraphQL, Portal, And HA Consumers`

Historical M0, M1, M2, MSP-03A, MSP-03B, MSP-03C, and the merged MSP-03D
EEBUS-G01 fake-peer harness slice remain preserved evidence. They do not let
M3 close without MSP-R00, DOCS-VERIFY, and MSP-03D-R.

## Initial Ready Rows

The initial ready set after lock is only:

- `MSP-R00` in `helianthus-eebusreg`, with a redacted companion ledger in
  `helianthus-execution-plans` and no predecessor;
- `DOCS-VERIFY` in `helianthus-docs-eebus`, with no predecessor.

`MSP-R00` is the recovery reconciliation gate. It requires a taint/file split
ledger, secret scan, synthetic-fixture and redaction rules, local never-pushed
rescue branch, one source-only forensic WIP commit, and a source-only git
bundle SHA-256. Public git and public bundles must not contain packet captures,
raw transcripts, keys, PEM blocks, tokens, trust stores, raw SKI, raw SHIPID,
raw IP/MAC address, or raw serial values. Full fidelity is encrypted outside
git with mode `0600` or discarded. Only a redacted ledger is public. Preflight
must be fully green before recovery mutation.

`DOCS-VERIFY` blocks runtime successors until license, canonical owners, issue
template compliance, path layout, and cross-seeding to `helianthus-docs-ebus`
are verified.

## Clean-Main Serialized Sequence

After the initial ready rows merge, eebusreg work is serialized one PR at a
time:

1. `MSP-03D-R` - G17+G19 harness and canonical recovery evidence.
2. `MSP-035` - raw identity/snapshot/evidence freeze.
3. `MSP-04A` - internal persistent store/schema only.
4. `MSP-036` - public immutable raw snapshot/view only.
5. `MSP-055` - disabled-by-default read-only lifecycle facade.
6. `MSP-04B` - first-trust, OOB confirmation, and admin-local boundary.
7. `MSP-04C` - restore, revocation, quarantine, and repair.
8. `MSP-045` - trust and admin state freeze.

Gateway M5, MCP M6, evidence/candidates/coexistence/promotion, and consumers
remain blocked until the prior canonical docs and eebusreg contracts merge.
GraphQL, Portal, Home Assistant, command routing, raw writes, and promoted
semantics stay out until their later milestones and per-leaf locks.

## Documentation Gates

`helianthus-docs-ebus/docs/platform/` owns cross-protocol ADRs and the
eebusreg-vs-shared-registry boundary/conformance contract.

`helianthus-docs-eebus` owns eeBUS protocol identity, SHIP/SPINE discovery
notes, VR940f protocol identity notes, and eeBUS-native evidence-workbench
docs.

Code repo docs are summary/local usage only. They must link to canonical
sources and must not carry normative requirements, issue template policy,
promotion policy, security acceptance criteria, or duplicated path layouts.

`DOCS-VERIFY` must prove license, owner, issue-template, path-layout, and
cross-seeding compliance before runtime successors begin. Gateway import is
blocked until prior canonical docs and eebusreg contracts are merged.

## Transport And Security Gates

`eebus-transport-gate v0` is required for SHIP/SPINE runtime, listener,
discovery, pairing, trust, snapshot/replay, or gateway sidecar wiring changes.
eBUS T01..T88 is required only when eBUS transport or eBUS capture code is
touched.

Exact gate meanings:

- `EEBUS-G17`: configured local SHIP advertisement/discovery, myVaillant trust
  visibility, and negative/TTL behavior. It is not evidence that the VR940f
  advertises a server.
- `EEBUS-G18`: M8 coexistence no drift only.
- `EEBUS-G19`: direct outbound VR940f TCP/TLS/WebSocket/SHIP access completion
  plus first post-access SPINE data.

MSP-03D closes only after both revised G17 and G19 pass with owner acceptance.
Feature graph completeness and reconnect durability belong to MSP-055/M6, not
G17.

## Raw View And Lifecycle Boundaries

`MSP-036` can export only versioned immutable raw snapshot/view fields. It has
no semantic device ID, lifecycle authority, trust/pairing mutation, or
availability guarantee. It depends on internal store schema plus migration and
conformance tests.

`MSP-055` is disabled by default. The public lifecycle facade is read-only.
Outbound sockets require explicit config plus pre-seeded trust or an allowlist.
No public trust or pairing mutation is allowed. First-trust/OOB/admin mutation
stays in later admin-local gated rows.

## MCP And Consumer Gates

M6 freezes final read-only `eebus.v1.*` only after raw contracts, immutable raw
views, lifecycle facade constraints, and trust/admin state are composed.

M7 creates draft candidate facts only. M8 proves coexistence. M8.5 locks
individual leaf promotion. M9 consumers are ordered GraphQL, Portal, Home
Assistant, then add-on exposure, and they expose only promoted leaves.

## Review Gates

Dual review and doc gate are per PR/issue, not only per milestone. Every
milestone ends with complete architecture review. Final execution adds one
extra code-structure review.

No PR may merge unless it links:

- doc-gate result;
- rollback ledger entry;
- relevant transport/security gate artifact;
- review disposition for every comment.

## Lock Criteria

This plan is locked when:

- plan state is `locked` and current milestone is `RECOVERY_RECONCILIATION`;
- accepted-through text names only MSP-03C plus merged MSP-03D EEBUS-G01
  fake-peer harness;
- dirty rescue code is explicitly non-authoritative;
- recovery/docs verification rows are the only initial ready rows;
- all future dependencies are explicit and acyclic;
- the canonical SHA-256 is synchronized through the index and split chunks.
