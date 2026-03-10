# Docs Stage 1 Execution Plan 01: Entrypoints and Taxonomy

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `762f47b9c2b2eaf45849f7cd51bdb0038d76bf41c6476207bc6fa5de37037572`

Depends on: None. This chunk establishes the reader-facing entrypoint story and the naming rules that later surgery depends on.

Scope: Top-level docs navigation, stale-claim correction, Vaillant protocol entrypoints, `B523` stub creation, `basv.md` replacement, and regulator catalog normalization.

Idempotence contract: Reapplying this chunk must not create duplicate entry pages, parallel regulator catalogs, or competing names for the same canonical pages.

Falsifiability gate: A review fails this chunk if the docs still leave `B523` or `B555` out of the Vaillant story, preserve `basv.md` as the canonical page name, or leave new readers with stale “stub-only” framing.

Coverage: Summary; Evidence and Uncertainty; Locked Decisions 1-2; Workstream M1.

---

## Summary

- Stage 1 starts by fixing navigation and naming rather than deeper page
  surgery.
- The goal is to make the docs readable and truthfully indexed before
  relocating Helianthus-specific material.

## Evidence and Uncertainty

### Proven

- `protocols/ebus-vaillant.md` currently omits `B523`.
- `B555` is not exposed consistently through the main docs entrypoints.
- `protocols/basv.md` is misnamed for the job it is doing.
- regulator knowledge is duplicated and not normalized.
- top-level pages still contain stale framing about incomplete runtime or API
  surfaces.

### Hypothesis

- fixing entrypoints and names first will make the later boundary surgery easier
  to review and less error-prone.

### Unknown

- some second-order link repairs may only become visible once the hard-cut
  rename lands.

## Locked Decisions

- `protocols/ebus-vaillant.md` becomes the canonical Vaillant index page and
  must list `B523`, `B524`, and `B555`.
- `protocols/ebus-vaillant-B523.md` is added now as a stub with observed scope,
  known targets, current limits, and explicit unknowns. It must not invent a
  wire spec.
- `README.md` and `architecture/overview.md` must stop advertising outdated
  “stub-only” or incomplete surface descriptions where they are now false.
- `protocols/basv.md` is replaced by
  `protocols/ebus-vaillant-regulators.md`.
- the regulator story is normalized into a single table with explicit columns
  for `device_id`, family or series, role, branding, generation or revision,
  canonical label, and notes.
- duplicated “known regulators” sections are merged into that one canonical
  catalog.

## Workstream Plan

### M1

- `ISSUE-DOC-01`: repair top-level entrypoints and stale claims in
  `README.md` and `architecture/overview.md`.
- `ISSUE-DOC-02`: replace `basv.md` with
  `ebus-vaillant-regulators.md` and normalize the regulator catalog.
- `ISSUE-DOC-03`: update the Vaillant protocol index and add the `B523` stub.

## Review Notes

- The locked import and repo-sanitation scaffolding live outside this chunk.
- This chunk is done only when a new reader can discover the Vaillant protocol
  surfaces from the top-level docs without guessing page names.
- The normalized regulator catalog must become the only canonical “known
  regulators” surface after the hard cut.
