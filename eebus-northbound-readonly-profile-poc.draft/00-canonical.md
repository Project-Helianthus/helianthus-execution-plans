# eeBUS Northbound Read-Only Consumption Profile v1 - NBP-00

## Status and objective

This is an inert, human-readable execution guide. Publishing it does not
create downstream work or expose a runtime capability.

Its sole objective is to bound one future public-documentation node: an
eeBUS Northbound Read-Only Consumption Profile v1. That node may describe
how an external integrator should understand the already separated
northbound surfaces without claiming that a new endpoint, tool, schema, or
consumer feature exists.

## Scope

The future profile is documentation-only and read-only. It is intended to
make these existing architectural boundaries consumable together:

- SHIP establishes connection and trust relationship state; SPINE is the
  protocol-native information topology browsed within a usable relationship.
- Raw, protocol-native read-only MCP exploration is distinct from a promoted
  semantic GraphQL contract. A raw observation is not thereby a semantic
  fact.
- Portal and Home Assistant are consumers of a typed gateway boundary. They
  do not directly use private operator sockets, secrets, or trust stores.
- A trusted but disconnected peer, an unavailable peer, and an unadvertised
  topology are relationship or availability conditions, not semantic values.

The future profile must not define or promise a route, endpoint, MCP tool,
GraphQL field, request or response schema, enum/status wire value, pairing
operation, trust mutation, deployment, live-device behavior, or capability
not already implemented and independently evidenced.

## Repository DAG and stop boundary

```text
NBP-00 -> NBP-01 docs-ebus -> HARD STOP
```

`NBP-00` is this execution-guide change in
`helianthus-execution-plans`. `NBP-01 docs-ebus` means a future,
independently preflighted documentation-only change in
`helianthus-docs-ebus`; it is not authorized or started by this guide.
`HARD STOP` applies after that future node: no runtime code, gateway change,
semantic-registry work, consumer rollout, pairing/trust operation, live I/O,
or deployment follows from this guide.

## Future NBP-01 candidate

Only after this guide is merged, a new read-only preflight may determine
whether the public documentation gap is still material. If it is, the
candidate is one ordinary issue, branch, and PR in `helianthus-docs-ebus`,
with an initially proposed write-set of:

- `docs/platform/eebus-northbound-readonly-consumption-profile-v1.md`
- a discovery link from
  `api/eebus-northbound-integrator-reference.md`
- only essential documentation checks and, if needed after preflight, a
  platform-index link.

The final write-set, repository main SHA, current issues/PRs, and the wording
must be rechecked at that later preflight. The document must remain a
language-neutral public contract in `helianthus-docs-ebus`, not a replacement
for protocol behavior documentation in `helianthus-docs-eebus` and not a
promotion of candidate documentation into runtime support.

## Acceptance criteria

1. The repository DAG remains exactly the sequence shown above.
2. NBP-01 remains docs-only, read-only, and subject to its own preflight and
   normal issue/branch/PR cycle.
3. The future document distinguishes SHIP relationship state from SPINE
   browsing, and raw protocol-native observations from promoted semantic
   exposure, without inventing a runtime interface.
4. The future document makes the typed gateway boundary and the exclusions
   for secrets, operator sockets, and trust stores explicit.
5. No node in this guide creates or modifies `helianthus-docs-eebus`,
   `helianthus-eebusreg`, gateway, Home Assistant, add-on, semantic-registry,
   or runtime code.
6. After NBP-01, the stated hard stop is observed. Any actual external
   runtime POC requires a separately selected, independently preflighted
   contract and an available gateway owner; active gateway work is outside
   this guide.

## Gates and risks

| Gate | NBP-00 | Future NBP-01 |
| --- | --- | --- |
| Documentation | Planning artifact only | Required: public cross-surface contract review |
| TDD | Not applicable | Docs-only; no behavior change |
| Transport matrix | Not applicable | Not applicable |
| Smoke/live I/O/deployment | Not applicable | Not applicable and prohibited |
| Fresh exact-HEAD review | Required | Required |

The material risk is documentation wording that consumers could mistake for a
currently available API. The mitigation is explicit non-claims, preservation
of the raw-versus-promoted boundary, and the hard stop before any runtime
work.

## Parallel-work note

Execution-plans PR #94 is a draft confined to
`semantic-bridge-ir-w34-26/00-canonical.md`. This guide is confined to
`eebus-northbound-readonly-profile-poc.draft/00-canonical.md`; the artifacts
share no dependency or write-set. This narrowly scoped parallel publication
does not authorize either plan's downstream execution.
