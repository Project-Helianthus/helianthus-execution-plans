# Implementing status

Canonical-SHA256: `76e676f1c0c724d5f26a078253f8ecbb698ca921b02e7ed6053a175b01bc215c`

State: implementing
Current milestone: M0
Review epoch: 3
Review state: PASSED
Accepted adversarial rounds: 5/5
Review target: TERMINAL_NO_FINDINGS
Lock authorized: yes, for plan publication only
Implementation authorized: yes, for the pre-gateway M0-M3 issue allowlist only
Authorization scope authority: exact authorized_issues allowlist; milestone labels are non-authoritative
Authorization anchor: PR #91 exact squash merge plus external review attestation required; PR #89 is predecessor provenance only; issue #90 is tracking only
Canonical main authority: fixed GitHub API for Project-Helianthus/helianthus-execution-plans; origin is identity-only
External review attestation: successful exact-head canonical pull_request workflow run, one authenticated official Codex review, two owner process attestations, and unedited aggregate binding workflow-run and review IDs
Docs R2 rebind: complete; exact docs PR #386 head/tree, canonical-main ancestry, exact-head CI, and review chain bound
Repository creation authorized: yes, through FMV3-M0-01
Private repository action: deferred; creation requires future explicit authorization
Commit/push authorized: yes, for the plan package and authorized pre-gateway issues only
Gateway work authorized: no; stop before FMV3-M4-01
Private creation/bootstrap authorized: no; FMV3-M0-04, FMV3-M0-05, and FMV3-M0-07 deferred

This package supersedes `fronius-modbus-eebus-bridge-w28-26.draft` as execution
intent while preserving that directory unchanged as forensic history.

Completed through terminal epoch 3 R5, PR #89 predecessor provenance, and the PR #91
correction tracked by issue #90:

- canonical and four isolated implementation chunks authored;
- 46-issue one-repository DAG and nine milestone groupings authored;
- additive FMV3-M1-05 public companion and FMV3-M1-06 runtime corrective authorized,
  with FMV3-M2-01 depending on the merged corrective producer and retaining the original
  companion history;
- PR #91 authorization requires a successful exact-head pull_request workflow run, one authenticated official Codex review, two owner exact-head/tree `NO_FINDINGS` process attestations, and an aggregate binding their IDs,
  canonical-main API resolution, one-parent squash topology, and trusted-launcher materialization
  of the anchored validator before execution;
- direct predecessor completion is fail-closed: completed dependencies use exact static live-GitHub
  issue/PR/title/relation/tree/topology/check bindings; unresolved direct predecessors require exact-set,
  bounded GitHub-authenticated `dependencies` certificates with no missing, duplicate, or extra rows;
- the exact docs R2 commit/tree, complete predecessor-inclusive normative closure, canonical-main
  ancestry, successful exact-head required checks, official Codex zero-inline review, and two fresh
  owner `NO_FINDINGS` reviews after CI are bound; the expanded machine projection including
  `bounded_values` is bound; M1-06 and M2-01
  still require docs PR #386 merged at that exact head/tree;
- M2-01 treats its bounded M1-06 issue/PR/commit/run/review values only as selectors. Live GitHub
  must prove the immutable marker/title, exact closing squash topology and main ancestry, test-only
  RED ancestor/page bounds plus exact-PR hosted `ci_local` failure, exact-head GREEN/checks-job
  success, canonical-template official and owner review gates, and the fixed closed conformance
  report binding exact production declarations and nonempty validator-pinned Go tests/PASS;
- strict hosted RED/GREEN, full producer-SHA pin, source-private capability trust,
  complete bounded claim/attempt lifecycles, one-shot seal-before-publish, deterministic
  synchronous fixed-ring reclamation, lossless normalization, and fresh revision-bound
  adversarial gates are explicit;
- R1 snapshot records reviewer verdict `FINDINGS`, integration `CLOSED`, and eleven
  preserved CLOSED findings;
- R2 snapshot records reviewer verdict `FINDINGS`, integration `CLOSED`, and seven
  preserved CLOSED findings;
- R3 snapshot records reviewer verdict `FINDINGS`, integration `CLOSED`, and R3-F01
  through R3-F05 CLOSED;
- R4 snapshot records reviewer verdict `FINDINGS`, integration `CLOSED`, and R4-F01
  through R4-F05 CLOSED;
- R5 snapshot records reviewer verdict `FINDINGS`, integration `CLOSED`, and R5-F01
  CLOSED after adding the missing FMV3-M5-05 security gate without changing its GraphQL design;
- epoch 1 transitioned to `FAILED` only after R5 integration closure and is archived
  immutably with its R1-R5 findings and concessions preserved;
- epoch 2 R1 records reviewer verdict `FINDINGS`, integration `CLOSED`, and E2-R1-F01
  through E2-R1-F03 CLOSED for TCP connection correlation, reused M2 public docs ancestry,
  and fail-closed confidential external GraphQL;
- epoch 2 R2 records reviewer verdict `FINDINGS`, integration `CLOSED`, and E2-R2-F01
  through E2-R2-F03 CLOSED for socket-lifetime TCP tombstones/generation rollover, the
  serialized PUBLIC_GRAPHQL_M2M_V1 docs gate, and RTU abandonment quarantine/recovery;
- epoch 2 R3 records reviewer verdict `FINDINGS`, integration `CLOSED`, and exact
  E2-R3-F01 through E2-R3-F06 CLOSED for transport-write linearization, profile doc gates,
  conditional profile TDD, repository serialization/mutex, myVaillant GO, and generic
  exact review finding metadata;
- epoch 2 R4 records reviewer verdict `FINDINGS`, integration `CLOSED`, and exact
  E2-R4-F01 through E2-R4-F03 CLOSED for the five-result transport parity contract,
  pre-published Growatt admission documentation, and live Fronius myVaillant GO evidence;
- epoch 2 R5 records reviewer verdict `FINDINGS`, integration `CLOSED`, and exact
  E2-R5-F01 through E2-R5-F03 CLOSED for terminal `PASSED` review semantics, separate
  full-transmit response-wait behavior, and the repaired claim register;
- epoch 2 transitioned to `FAILED` only after R5 integration closure and is archived
  immutably at snapshot `987d594f721af943fc65f6f47e5f48d8d3b72011b656fd2db79dd13adceb4796`;
- epoch 3 R1 records reviewer verdict `FINDINGS` against snapshot
  `d0e23922b27030b241688dec85d5e79f28de4d6730e6964511e71b6ff10b1c36`, integration
  `CLOSED`, and exact E3-R1-F01 through E3-R1-F05 closure for semantic MCP-before-lock
  ordering, physical wire/per-observation logical-view coalescing identity, fail-closed EMMA
  discrimination, RTU physical qualification disposition, and sole secured Matter ingress;
- epoch 3 R2 records reviewer verdict `FINDINGS` against snapshot
  `19f83175eaffc54e6e6ea5bb0f8282d0c6400e9c440ceacc80cbf5b75725f07b`, integration
  `CLOSED`, and E3-R2-F01 closure for public licensed SmartLogger/S-Dongle admission packets,
  conditional positive fixtures/code, and fail-closed non-admission;
- epoch 3 R3 records reviewer verdict `FINDINGS` against snapshot
  `3dcfab8e8c094d8be6010caa50015100163741e460ce109c5b32ab6154eccf30`, integration
  `CLOSED`, and E3-R3-F01/F02 closure through public eeBUS/Matter companion issues,
  sanitized post-lab knowledge publication or STOP, and consistent active review state;
- epoch 3 R4 records reviewer verdict `FINDINGS` against snapshot
  `ddc3962b53f4ce8d5d29a737c501cd4eab2e30ccd2e3e4bab12a16113c95a58e`, integration
  `CLOSED`, and E3-R4-F01 closure through runtime-owned FC2B/MEI0E identity and M7 detector
  operation admission gates;
- epoch 3 R5 records `NO_FINDINGS` against snapshot
  `320f9383d26b640a423ad5902cad90643dc42e18d2c76544f6293d46253866ea`, with no finding IDs
  and integration `NOT_REQUIRED`;
- epoch 3 is the sole terminal `PASSED` epoch at 5/5, targeting `TERMINAL_NO_FINDINGS`;
- structural validator remains bounded and does not simulate runtime behavior.

Current corrective state: R3d is active, not terminal. The authorization suite has added
app-bound checks, bounded pagination, anchor-derived dependency identities, exact merge-time
issue closure, honest owner process attestations, self-provisioned docs validation, and
report-bound mutation patches with compile/no-tests success before mapped-test failure. A fresh
exact-tree adversarial `NO_FINDINGS` verdict and exact-head hosted evidence are still required.

Terminal review closure did not itself lock the plan. The operator separately authorized
lock and publication on 2026-07-14. After PR #91 merges, its exact merge commit is the sole
current immutable anchor for the corrected pre-gateway allowlist and M1/M2 machine fields;
PR #89 remains predecessor provenance only, while issue #90 is tracking metadata and not
authorization evidence. The hard stop remains before FMV3-M4-01; gateway and private
binding work remain unauthorized.

Not performed:

- semantic lock, gateway implementation, or private binding implementation;
- any issue outside the explicit M0-M3 pre-gateway allowlist.
