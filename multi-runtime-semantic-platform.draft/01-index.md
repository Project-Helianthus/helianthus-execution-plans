# Multi-Runtime Semantic Platform Draft Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `de84f3f35afecd3317e2a62089fdaa78150adb4b62110771296b7fd7c7ab24df`

This directory contains an owner-approved draft for turning Helianthus into a
multi-runtime native protocol gateway. It uses the standard execution-plan
layout so it can later be promoted to a locked plan, but the `.draft` suffix is
intentional and outside the current active-plan validator.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk repeats the canonical hash for drift detection.
- Each chunk is reviewable in isolation and declares:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is execution-oriented, not a replacement for the canonical file.
- Gateway `0.4.0` is the named direct eBUS baseline throughout this draft.

## Chunk Map

1. [10-platform-taxonomy-and-boundaries.md](./10-platform-taxonomy-and-boundaries.md)
   defines the transport/base protocol/profile/runtime/native registry/semantic
   boundaries.

2. [11-ebus-040-baseline-and-profile-split.md](./11-ebus-040-baseline-and-profile-split.md)
   captures the gateway `0.4.0` eBUS baseline and the required split between
   classic eBUS and vendor profiles.

3. [12-eebus-mcp-first-vr940f.md](./12-eebus-mcp-first-vr940f.md)
   defines the eeBUS raw-first path, `helianthus-eebusreg` boundary,
   `eebus-go v0.7.0` feasibility gates, VR940f lab target, trust model,
   deterministic MCP, and leaf-promotion lock.

4. [13-semantic-fact-graph-and-integration.md](./13-semantic-fact-graph-and-integration.md)
   defines canonical semantic facts, provenance, conflict handling, and
   cross-runtime integration.

5. [14-execution-roadmap-issues-and-gates.md](./14-execution-roadmap-issues-and-gates.md)
   maps milestones M0-M9, model lanes, issue gates, doc gates, transport
   gates, and review sequencing.

## M0 Operational Artifacts

- [92-m0-issue-matrix.yaml](./92-m0-issue-matrix.yaml) is the
  machine-readable control-plane seed for issue creation. It carries
  complexity, model lane, repo serialization, doc owner, gate applicability,
  rollback, review, and acceptance data for each planned issue.
- [93-eebus-transport-gate-v0.md](./93-eebus-transport-gate-v0.md) defines the
  eeBUS transport/protocol gate used by M3, M5, M6, M8, and later eeBUS runtime
  changes.
- [issues/MSP-00A-control-plane-matrix.md](./issues/MSP-00A-control-plane-matrix.md),
  [issues/MSP-00B-model-routing.md](./issues/MSP-00B-model-routing.md), and
  [issues/MSP-00C-eebus-transport-gate-v0.md](./issues/MSP-00C-eebus-transport-gate-v0.md)
  are ready-to-file M0 issue bodies.
- [94-m1-docs-bootstrap-evidence.md](./94-m1-docs-bootstrap-evidence.md)
  records local M1 docs bootstrap evidence and validation results.
- [issues/MSP-020-eebusreg-bootstrap.md](./issues/MSP-020-eebusreg-bootstrap.md)
  is the handoff body for creating the raw runtime/evidence repo shell before
  MSP-02A starts.
- [95-msp-020-eebusreg-bootstrap-evidence.md](./95-msp-020-eebusreg-bootstrap-evidence.md)
  records the `helianthus-eebusreg` bootstrap repository, issue, commit, and
  local CI result.
- [96-gate-readiness-audit-2026-07-08.md](./96-gate-readiness-audit-2026-07-08.md)
  records the current gate decision before MSP-02A: mechanical checks pass, but
  PR #35 and PR #334 still require review/merge acceptance.
- [issues/MSP-02A-raw-runtime-identity-contract.md](./issues/MSP-02A-raw-runtime-identity-contract.md)
  was the handoff body for the raw runtime identity contract.
- [97-m2-raw-contracts-architecture-review.md](./97-m2-raw-contracts-architecture-review.md)
  records the accepted M2 raw identity, evidence envelope, raw-correlation
  policy, and end-of-milestone architecture review.
- [98-msp-03a-facade-spike-evidence.md](./98-msp-03a-facade-spike-evidence.md)
  records the accepted MSP-03A internal `eebus-go v0.7.0` facade spike,
  boundary evidence, verification results, and GPT-only review ledger.
- [98-msp-03b-toolchain-boundary-evidence.md](./98-msp-03b-toolchain-boundary-evidence.md)
  records the accepted MSP-03B local and build-container module/toolchain
  proof, CI evidence, and GPT-only review ledger.
- [98-msp-03c-ha-network-proof-gate-evidence.md](./98-msp-03c-ha-network-proof-gate-evidence.md)
  records the merged MSP-03C HA add-on proof gate and docs gate, with lab-run
  evidence still pending.
- [98-msp-03c-lab-attempt-2026-07-08.md](./98-msp-03c-lab-attempt-2026-07-08.md)
  records the first MSP-03C live lab attempt and the mDNS degraded result.

## Coverage Matrix

| Source content | Destination chunk |
| --- | --- |
| Platform model, architectural rules, target architecture | `10-platform-taxonomy-and-boundaries.md` |
| Gateway `0.4.0`, eBUS runtime boundary, base/profile split | `11-ebus-040-baseline-and-profile-split.md` |
| eeBUS repo, MCP raw-first, trust/security, VR940f lab target | `12-eebus-mcp-first-vr940f.md` |
| Semantic status model, fact provenance, integration rules | `13-semantic-fact-graph-and-integration.md` |
| Milestones, model routing, issue gates, acceptance | `14-execution-roadmap-issues-and-gates.md` |

## Review Target

The draft is ready for adversarial review when reviewers can falsify:

- whether `0.4.0` is sufficient as the eBUS baseline;
- whether the taxonomy prevents protocol/profile leakage;
- whether eeBUS can start raw-first without GraphQL or HA dependencies;
- whether `helianthus-eebusreg` is contained as raw runtime/evidence plumbing
  rather than becoming a semantic registry fork;
- whether the `GPT-5.3-Codex-Spark` / `gpt-5.4-mini` / `GPT-5.5` lane split is
  sufficient for one-shot issue execution;
- whether semantic provenance is strong enough for future Modbus, CAN, UART,
  and KM-Bus families.
