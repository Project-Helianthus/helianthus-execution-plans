# Docs Stage 1 Execution Plan 02: Protocol Boundary Surgery

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `762f47b9c2b2eaf45849f7cd51bdb0038d76bf41c6476207bc6fa5de37037572`

Depends on: `10-entrypoints-and-taxonomy.md`. Canonical names and entrypoints must be fixed before hard-cut moves and link rewrites begin.

Scope: Surgical extraction of Helianthus-specific architecture, runtime, integration, and development material out of `protocols/` while preserving protocol evidence and implementability.

Idempotence contract: Reapplying this chunk must not remove protocol evidence, duplicate moved pages, or produce competing canonical homes for the same runtime or architecture material.

Falsifiability gate: A review fails this chunk if it strips protocol-relevant evidence from `protocols/`, leaves Helianthus runtime or API material embedded there, or makes `protocols/` insufficient for an independent implementation.

Coverage: Locked Decision 3; Workstream M2.

---

## Boundary Rule

- `protocols/` keeps everything needed for an independent implementation:
  - wire behavior
  - selector and register semantics
  - evidence
  - observed protocol behavior
  - protocol-relevant FSM material
- `protocols/` loses only Helianthus-specific material that is not necessary for
  independent implementation:
  - GraphQL and MCP field contracts
  - semantic publication rules
  - code anchors
  - rollout paths
  - implementation debt notes

## Locked Moves

- move `protocols/ebus-vaillant-B524-structural-decisions.md` to
  `architecture/b524-structural-decisions.md`
- move Helianthus runtime behavior currently mixed into
  `protocols/ebus-overview.md` to `architecture/ebus-runtime.md`
- move BASV orchestration and enrichment behavior to
  `architecture/regulator-identity-enrichment.md`
- move B555 validation logs, captures, and implementation-path notes to
  `development/b555-timer-validation.md`

## Surgical Page Rules

- `B509` and `B524` pages remain protocol pages first.
- evidence stays in place when it supports protocol interpretation.
- FSM material stays in `protocols/` when it explains protocol behavior or
  message sequencing needed by an independent implementation.
- only explicit Helianthus publication and API mapping material moves out.
- a moved section must land in a better destination page, not disappear.

## Workstream Plan

### M2

- `ISSUE-DOC-04`: perform the boundary surgery across:
  - `B524 structural decisions`
  - BASV orchestration and enrichment
  - `ebus-overview` runtime material
  - Helianthus-only publication and API mapping content in `B509` and `B524`

## Review Notes

- The correctness test for this chunk is not “less Helianthus in `protocols/`”.
- The correctness test is that `protocols/` remains implementation-sufficient
  while architecture and development material become easier to find in their own
  sections.
