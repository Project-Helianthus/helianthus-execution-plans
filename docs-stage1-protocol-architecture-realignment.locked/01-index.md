# Docs Stage 1 Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `762f47b9c2b2eaf45849f7cd51bdb0038d76bf41c6476207bc6fa5de37037572`

This directory contains the canonical Stage 1 docs realignment plan plus a
lossless execution-oriented split into reviewable chunks. The split exists so
reviewers and implementation agents can attack bounded parts of the workstream
without losing the source contract.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk stays below `10000` tokens on both the GPT-5-family tokenizer and
  the Claude tokenizer.
- Each chunk is reviewable in isolation and repeats:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is lossless except for deliberate dependency repetition needed for
  isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical
  hash of `00-canonical.md`.

## Sequencing Rules

- The default milestone order is `M0 -> M1 -> M2 -> M3 -> M4`.
- `M0` is the locked-plan import and downstream issue scaffolding gate.
- `M1` fixes entrypoints, naming, and navigation before deeper page surgery.
- `M2` performs the protocol-versus-architecture split.
- `M3` finishes API, timer, and terminology alignment once the boundary cleanup
  is in place.
- `M4` performs the proof sweep, broken-link closeout, and maintenance handoff.
- Locked decisions in the canonical plan override milestone shorthand if drift
  appears between this split and the source document.

## Chunk Map

1. [`10-entrypoints-and-taxonomy.md`](./10-entrypoints-and-taxonomy.md)
   Covers the top-level docs story, stale-claim correction, Vaillant protocol
   entrypoints, the `B523` stub, the `basv.md` rename, and the normalized
   regulator catalog.
2. [`11-protocol-boundary-surgery.md`](./11-protocol-boundary-surgery.md)
   Covers the surgical extraction of Helianthus-specific runtime, architecture,
   and development material out of `protocols/`.
3. [`12-api-runtime-and-timer-alignment.md`](./12-api-runtime-and-timer-alignment.md)
   Covers the canonical timer story, `schedules` in API docs, `B524 read_timer`
   positioning, and `/ui` versus `/portal` terminology.
4. [`13-execution-proof-and-mapping.md`](./13-execution-proof-and-mapping.md)
   Covers milestone wiring, repo sanitation, issue and PR contract alignment,
   proof gates, and residual unknowns that remain explicit.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Evidence and Uncertainty; Locked Decisions 1-2; Workstream M1 | `10-entrypoints-and-taxonomy.md` |
| Locked Decision 3; Workstream M2 | `11-protocol-boundary-surgery.md` |
| Locked Decision 4; Workstream M3 | `12-api-runtime-and-timer-alignment.md` |
| Locked Decisions 5-6; Workstream M0 and M4; Execution and Proof Contract | `13-execution-proof-and-mapping.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every
chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
