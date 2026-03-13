# Hydraulic Visualization Cards Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `da004d202f208e9e161fb5b1ccd0effa8ad5596fa101414dcf36852b2bcb61a2`

This directory contains the canonical Hydraulic Visualization Cards plan plus a
lossless execution-oriented split into reviewable chunks. The split exists so
Opus, Sonnet, and implementation agents can attack bounded pieces without losing
the source contract.

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

- The default milestone order is `M0 -> M1 -> M2 -> M3`.
- M0 must prove the full artifact pipeline (build, serve, register, render)
  before any card implementation begins.
- M1 (Card 1) is simpler and proves the SVG rendering patterns and shared
  utilities. M2 (Card 2) builds on these.
- M3 is polish only — both cards must be functionally complete before M3.
- Locked decisions in the canonical plan override milestone shorthand if drift
  appears between this split and the canonical source.

## Chunk Map

1. [`10-evidence-and-vaillant-reference.md`](./10-evidence-and-vaillant-reference.md)
   Covers summary, evidence status, unknowns, and Vaillant boiler internal
   reference (model naming, component inventory, pipe order).
2. [`11-card1-burner-hydraulics.md`](./11-card1-burner-hydraulics.md)
   Covers Card 1 SVG layout, entity mapping, configuration schema, and
   reactive behavior.
3. [`12-card2-system-hydraulics.md`](./12-card2-system-hydraulics.md)
   Covers Card 2 visual elements, topology derivation, entity mapping,
   configuration schema, and behavior.
4. [`13-frontend-architecture.md`](./13-frontend-architecture.md)
   Covers technology stack, component structure, artifact supply chain,
   Lovelace resource registration, and HA integration contract.
5. [`14-delivery-scope-risks-notes.md`](./14-delivery-scope-risks-notes.md)
   Covers milestone delivery order (M0-M3), scope boundaries, risks, and
   implementation notes.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Sections 1-2 | `10-evidence-and-vaillant-reference.md` |
| Section 3 | `11-card1-burner-hydraulics.md` |
| Section 4 | `12-card2-system-hydraulics.md` |
| Section 5 | `13-frontend-architecture.md` |
| Sections 6-9 | `14-delivery-scope-risks-notes.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every
chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
