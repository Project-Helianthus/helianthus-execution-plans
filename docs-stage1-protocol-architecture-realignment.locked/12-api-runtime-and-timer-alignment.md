# Docs Stage 1 Execution Plan 03: API, Runtime, and Timer Alignment

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `762f47b9c2b2eaf45849f7cd51bdb0038d76bf41c6476207bc6fa5de37037572`

Depends on: `10-entrypoints-and-taxonomy.md` and `11-protocol-boundary-surgery.md`. The timer and API story must be aligned only after the canonical protocol pages and boundaries are stable.

Scope: Canonical timer positioning around `B555`, API doc alignment for `schedules`, low-level `B524 read_timer` framing, and `/ui` versus `/portal` terminology cleanup.

Idempotence contract: Reapplying this chunk must not create parallel timer stories, duplicate API canon, or conflicting terminology for the same user-facing surfaces.

Falsifiability gate: A review fails this chunk if timers still read as primarily a `B524` story, if `schedules` is absent from API docs, or if `/ui` and `/portal` remain semantically conflated.

Coverage: Locked Decision 4; Workstream M3.

---

## Timer Canon

- `B555` is the canonical timer protocol story for Stage 1.
- `api/graphql.md` and `api/mcp.md` must document `schedules` as the canonical
  timer surface.
- retained `B524 read_timer` material must be positioned as low-level, limited,
  and non-canonical.

## Runtime and Naming Alignment

- `/ui` and `/portal` terminology must be clarified everywhere touched by this
  workstream.
- the distinction must be explicit enough that readers can tell apart
  projection-explorer surfaces from the dynamic Portal surface.

## Workstream Plan

### M3

- `ISSUE-DOC-05`: update the timer and API docs around `B555` and `schedules`,
  then normalize `/ui` versus `/portal` terminology in the touched pages.

## Review Notes

- This chunk is complete only when the timer story has a single obvious
  canonical path for new readers.
- Low-level retention is allowed, but the docs must stop implying that the
  low-level `B524` surface is the primary timer contract.
