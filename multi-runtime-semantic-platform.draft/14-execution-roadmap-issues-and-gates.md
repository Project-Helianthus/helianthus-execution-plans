# Execution Roadmap, Issues, And Gates

Canonical-SHA256: `f7c48073085d32dbe1de9e352f454a29fa60b6b7ac05954c5f253cb9593dccdc`

Depends on:
All previous chunks.

Scope:
Defines milestone order, issue slicing rules, validation gates, and draft
promotion criteria.

Idempotence contract:
The roadmap may be converted into issues repeatedly. Duplicate issue creation
must be avoided by checking existing issue maps first.

Falsifiability gate:
Each milestone must have a testable gate. If implementers cannot prove the gate
without subjective judgment, the milestone is not ready for locked execution.

Coverage:
Covers the canonical milestone list, execution rules, and acceptance criteria.

## Milestone Order

1. `M0 - Gateway 0.4.0 Baseline Lock`
2. `M1 - Platform Vocabulary ADR`
3. `M2 - eBUS Runtime Boundary`
4. `M3 - eBUS Base/Profile Split`
5. `M4 - Semantic Provenance v1`
6. `M5 - helianthus-eebusreg`
7. `M6 - eeBUS MCP Raw First`
8. `M7 - eeBUS Semantic Candidate`
9. `M8 - Multi-Runtime Coexistence`
10. `M9 - GraphQL, Portal, HA`
11. `M10 - Next Runtime Families`

## Issue Slicing

Each issue must touch one layer:

- transport;
- base protocol;
- profile;
- runtime instance;
- native registry;
- semantic projection;
- MCP;
- GraphQL;
- Portal;
- Home Assistant.

If an issue needs two layers, split it.

## Gates

- M0 gate: gateway `0.4.0` builds, deploys, and smokes on the real HA/RPi4 lab
  without the external eBUS proxy.
- M1 gate: every future protocol component can be classified using the platform
  vocabulary.
- M2 gate: current eBUS MCP, GraphQL, Portal, and Home Assistant outputs remain
  unchanged.
- M3 gate: raw/classic eBUS works without Vaillant semantics.
- M4 gate: semantic facts carry runtime/profile/evidence metadata.
- M5 gate: eeBUS raw registry can run without consumer dependencies.
- M6 gate: VR940f raw discovery is visible through MCP.
- M7 gate: candidate/promoted/withheld statuses are visible through MCP.
- M8 gate: eBUS and eeBUS run together without raw surface merging.
- M9 gate: HA exposes no candidate, conflicted, or withheld semantic entities.
- M10 gate: a new protocol family can start raw-first without changing eBUS
  compatibility behavior.

## Draft Promotion Criteria

Before promotion to `.locked/`:

- run adversarial review passes against taxonomy leakage;
- run deep research on eeBUS/SPINE and `enbility/eebus-go` integration shape;
- confirm gateway `0.4.0` lab baseline artifacts;
- convert milestones to concrete cross-repo issues;
- update `plan.yaml` state and directory suffix from `.draft` to `.locked`;
- update canonical hash references after any content changes.

## Git Hygiene

This draft is added directly on `main` by owner override. It must not stage or
modify existing dirty files in other plan directories.
