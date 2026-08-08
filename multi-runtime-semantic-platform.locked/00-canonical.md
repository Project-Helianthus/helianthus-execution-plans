# Helianthus Multi-Runtime Semantic Platform

Status: `locked`

This is a human-readable dependency guide. It does not authorize work, calculate
readiness, mint tokens, verify attestations, select agents, or cause post-merge effects.
Actual state comes from current GitHub issues, pull requests, checks, reviews, and the
implementation repository that owns each row.

## Architecture

Helianthus keeps transport, protocol decode, registry, semantic projection, and consumer
bindings separate. eBUS is the proven baseline. eeBUS is the first additional native
runtime and must preserve its SHIP/SPINE identity, raw evidence, lifecycle, and security
semantics before projecting canonical facts.

The relevant repository chain is:

1. public architecture and protocol documentation;
2. `helianthus-ship-go` and `helianthus-spine-go` protocol foundations;
3. `helianthus-eebus-go` runtime composition;
4. `helianthus-eebusreg` raw identity, evidence, lifecycle, and feature access;
5. `helianthus-ebusgateway` MCP-first integration and live coexistence;
6. GraphQL, Portal, Home Assistant, and add-on consumers only after stable promoted facts.

## Execution

`92-m0-issue-matrix.yaml` contains 75 issue rows and 101 ordinary `depends_on` edges.
For each candidate row, the agent must first inspect current GitHub state and confirm that
every predecessor is actually merged or otherwise satisfied in its owning repository.
Work then follows the normal issue, branch, PR, CI, review, and squash-merge process.

Historical completion labels, hashes, reviews, and lab records are preserved only in
`multi-runtime-semantic-platform-history.draft/`. They are evidence context, not workflow
state.

## Invariants

- One active issue and PR per repository unless the operator explicitly coordinates a
  safe exception.
- Protocol and semantic changes keep their public documentation gate.
- Transport changes retain the applicable eeBUS or eBUS transport gate.
- Implementation behavior is proved in code repositories through types, fixtures,
  conformance tests, compatibility tests, and CI.
- MCP remains the first consumer surface; GraphQL and end consumers follow stable
  semantics.
- Public repositories never depend on private binding artifacts.
- Review continues on fresh exact HEAD while valid P0-P2 findings exist and stops at
  `NO_BLOCKING_FINDINGS`; P3/P4 are explicitly triaged and nonblocking.

## Continuation

The historical checkpoint named `MSP-065-LIVE-R1` as the next candidate. That is not a
readiness declaration. Before continuing, reconcile every row and predecessor against
current GitHub state, then select the first incomplete row whose dependencies are proven.
