# Multi-Runtime Semantic Platform Locked Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `f2392801ccdc00dfeaaf48166582cbbea42770a4d14998ca082b2624b1e9e18e`

This directory contains the locked execution plan for turning Helianthus into a
multi-runtime native protocol gateway. It is currently in
`RECOVERY_RECONCILIATION`: M3/MSP-03D remain open, accepted evidence stops at
MSP-03C plus the merged MSP-03D EEBUS-G01 fake-peer harness slice, and dirty
rescue code has no successor-unlock authority. AD-DOCS-01 amends the locked
plan with external-only eeBUS documentation ownership, public evidence privacy,
and the serialized docs/API freeze gates.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk repeats the canonical hash for drift detection.
- Each chunk is reviewable in isolation and declares:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- Gateway `0.4.0` is the named direct eBUS baseline throughout this plan.

## Chunk Map

1. [10-platform-taxonomy-and-boundaries.md](./10-platform-taxonomy-and-boundaries.md)
   defines the transport/base protocol/profile/runtime/native registry/semantic
   boundaries.

2. [11-ebus-040-baseline-and-profile-split.md](./11-ebus-040-baseline-and-profile-split.md)
   captures the gateway `0.4.0` eBUS baseline and the required split between
   classic eBUS and vendor profiles.

3. [12-eebus-mcp-first-vr940f.md](./12-eebus-mcp-first-vr940f.md)
   defines the eeBUS raw-first path, `helianthus-eebusreg` boundary, revised
   G17/G19 gates, trust model, deterministic MCP, and leaf-promotion lock.

4. [13-semantic-fact-graph-and-integration.md](./13-semantic-fact-graph-and-integration.md)
   defines canonical semantic facts, provenance, conflict handling, and
   cross-runtime integration.

5. [14-execution-roadmap-issues-and-gates.md](./14-execution-roadmap-issues-and-gates.md)
   maps locked recovery reconciliation, clean-main sequencing, symbolic routing
   contracts,
   issue gates, doc gates, transport gates, and review sequencing.

## Operational Artifacts

- [90-issue-map.md](./90-issue-map.md) is the human-readable locked issue map.
- [91-milestone-map.md](./91-milestone-map.md) is the locked milestone DAG.
- [92-m0-issue-matrix.yaml](./92-m0-issue-matrix.yaml) is the machine-readable
  control-plane matrix with every row's complexity, routing contract or historical
  routing evidence, completion-token dependencies, docs owner/gate, transport/security gate, rollback ledger,
  review ledger, TDD mode, smoke scope, and acceptance.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.
- [93-eebus-transport-gate-v0.md](./93-eebus-transport-gate-v0.md) defines the
  eeBUS transport/protocol gate and exact G17/G18/G19 meanings.
- [94-m1-docs-bootstrap-evidence.md](./94-m1-docs-bootstrap-evidence.md)
  records local M1 docs bootstrap evidence and validation results.
- [95-msp-020-eebusreg-bootstrap-evidence.md](./95-msp-020-eebusreg-bootstrap-evidence.md)
  records the `helianthus-eebusreg` bootstrap repository, issue, commit, and
  local CI result.
- [96-gate-readiness-audit-2026-07-08.md](./96-gate-readiness-audit-2026-07-08.md)
  records the historical gate-readiness audit before MSP-02A.
- [97-m2-raw-contracts-architecture-review.md](./97-m2-raw-contracts-architecture-review.md)
  records the accepted M2 raw identity, evidence envelope, raw-correlation
  policy, and end-of-milestone architecture review.
- [98-msp-03a-facade-spike-evidence.md](./98-msp-03a-facade-spike-evidence.md)
  records accepted MSP-03A evidence.
- [98-msp-03b-toolchain-boundary-evidence.md](./98-msp-03b-toolchain-boundary-evidence.md)
  records accepted MSP-03B evidence.
- [98-msp-03c-ha-network-proof-gate-evidence.md](./98-msp-03c-ha-network-proof-gate-evidence.md),
  [98-msp-03c-lab-attempt-2026-07-08.md](./98-msp-03c-lab-attempt-2026-07-08.md),
  [98-msp-03c-lab-acceptance-2026-07-08.md](./98-msp-03c-lab-acceptance-2026-07-08.md),
  and [98-msp-03c-ha-network-proof-lab-run.json](./98-msp-03c-ha-network-proof-lab-run.json)
  record MSP-03C evidence.
- [98-msp-03d-fake-peer-live-blocker-evidence.md](./98-msp-03d-fake-peer-live-blocker-evidence.md)
  records the merged MSP-03D EEBUS-G01 fake-peer harness slice and historical
  live blocker.
- [100-topology-audit.md](./100-topology-audit.md) proves no cycles/orphans
  and the initial ready set.
- [101-g19-canonical-evidence-template.md](./101-g19-canonical-evidence-template.md)
  defines the canonical G19 evidence schema and redaction rules.
- [102-plan-lock-architecture-review.md](./102-plan-lock-architecture-review.md)
  records the final post-adversarial architecture, routing, security, and DAG
  review before cruise registration.
- [103-ad-docs-01-amendment.md](./103-ad-docs-01-amendment.md) records the
  accepted external-only-documentation amendment after five adversarial
  amendment rounds.
- [104-msp-r00-l-public-redacted-ledger.json](./104-msp-r00-l-public-redacted-ledger.json)
  records the MSP-R00-L public-safe redacted recovery ledger.
- [99-status.md](./99-status.md) records the locked current state.

## Coverage Matrix

| Source content | Destination chunk |
| --- | --- |
| Platform model, architectural rules, target architecture | `10-platform-taxonomy-and-boundaries.md` |
| Gateway `0.4.0`, eBUS runtime boundary, base/profile split | `11-ebus-040-baseline-and-profile-split.md` |
| eeBUS repo, MCP raw-first, trust/security, VR940f lab target | `12-eebus-mcp-first-vr940f.md` |
| Semantic status model, fact provenance, integration rules | `13-semantic-fact-graph-and-integration.md` |
| Recovery, milestones, model routing, issue gates, acceptance | `14-execution-roadmap-issues-and-gates.md` |

## Review Target

The locked plan is ready for preflight when reviewers can falsify:

- whether recovery/docs verification is the only initial ready set;
- whether dirty rescue code is prevented from unlocking successors;
- whether AD-DOCS-01 keeps substantive eeBUS docs out of `helianthus-eebusreg`;
- whether public recovery evidence uses only opaque IDs/classes/dispositions;
- whether G17/G18/G19 meanings are mechanically distinct;
- whether `helianthus-eebusreg` remains raw runtime/evidence plumbing rather
  than a semantic registry fork;
- whether docs ownership prevents protocol/platform duplication;
- whether GraphQL, Portal, Home Assistant, command routing, raw writes, and
  promoted semantics remain out until their later locks.
