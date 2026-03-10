# Docs Stage 1: Protocol / Architecture Realignment

Revision: `v1.0-lock-import`
Date: `2026-03-10`
Status: `Locked bootstrap import`

## Summary

- This plan creates the Stage 1 realignment contract for `helianthus-docs-ebus`.
- The fixed objective is boundary repair, not a full tree redesign:
  - `protocols/` must stay sufficient for an independent third-party
    implementation of the eBUS/Vaillant adapter
  - Helianthus-specific architecture, runtime, API, and rollout material must
    be split out of `protocols/` surgically
- Stage 1 is a hard-cut cleanup:
  - no compatibility shim pages
  - no fake protocol completeness
  - no removal of evidence or protocol-relevant FSM material simply because it
    also informed Helianthus implementation
- The immediate execution target is a locked import in
  `helianthus-execution-plans`.
- The downstream implementation target remains `helianthus-docs-ebus`.

## Evidence and Uncertainty

### Proven

- `protocols/ebus-vaillant.md` is missing `B523` even though it is part of the
  observed Vaillant protocol story.
- `B555` is missing from key entrypoints and navigation surfaces even though the
  repository now contains dedicated timer protocol documentation for it.
- `protocols/basv.md` is misnamed for its actual role and does not read like a
  stable canonical page title.
- Regulator knowledge is duplicated across incompatible sections and mixed
  together with gateway and family-orchestration concerns.
- `protocols/` currently mixes protocol knowledge with Helianthus-specific
  runtime, API, integration, and rollout material.
- top-level and overview pages still contain stale claims about gateway or API
  surfaces being incomplete or stub-like where that is no longer true.
- `helianthus-docs-ebus` currently has two non-`main` remote branches that
  should not survive Stage 1 repo hygiene:
  - `issue/203-b555-timer-protocol` is stale relative to `origin/main`
    (`3 behind, 0 ahead`)
  - `feature/adr-026-wave2-comprehensive-icons` is topology-diverged
    (`1 behind, 1 ahead`) but its effective content is already represented on
    `origin/main`

### Hypothesis

- A surgical Stage 1 split is enough to restore clean boundaries without a full
  `docs/<protocol>/...` rewrite.
- The current documentation can be realigned without damaging the evidence trail
  or the ability of a third party to implement from `protocols/` alone.

### Unknown

- Additional low-volume cleanup may be needed after the first boundary sweep,
  especially where small Helianthus-specific notes are embedded inside otherwise
  canonical protocol pages.
- Some link repairs may expose second-order naming problems not visible until
  the hard-cut rename set lands.

## Locked Decisions

### 1. Entry Points and Canonical Protocol Pages

- `protocols/ebus-vaillant.md` becomes the Vaillant entry index and must list
  `B523`, `B524`, and `B555`.
- `protocols/ebus-vaillant-B523.md` is added now as an honest stub:
  - observed purpose
  - known targets and usage context
  - current documentation limits
  - explicit unknowns
- The `B523` page must not invent a wire contract or fake completeness.
- `README.md` and `architecture/overview.md` must expose the current state of
  the docs and runtime surfaces accurately enough that a new reader can find the
  live protocol, architecture, API, and validation pages without stale
  “stub-only” framing.

### 2. Naming and Taxonomy

- `protocols/basv.md` is replaced by
  `protocols/ebus-vaillant-regulators.md`.
- The regulator story is normalized into one canonical catalog with explicit
  columns for:
  - `device_id`
  - family or series
  - role
  - branding
  - generation or revision
  - canonical label
  - notes
- Duplicated “known regulators” sections are merged into that single normalized
  catalog.
- BASV-specific orchestration and enrichment behavior is not part of the
  regulator catalog and must move to architecture material.

### 3. Boundary Surgery Rules

- `protocols/` keeps all material required for an independent implementation:
  - wire behavior
  - selector and register semantics
  - evidence
  - observed protocol behavior
  - protocol-relevant FSM material
- Material leaves `protocols/` only when it is Helianthus-specific and not
  necessary for an independent implementation. Examples:
  - GraphQL or MCP field contracts
  - semantic publication rules
  - code anchors
  - local gateway rollout paths
  - implementation debt notes
- `protocols/ebus-vaillant-B524-structural-decisions.md` moves to
  `architecture/b524-structural-decisions.md`.
- Helianthus runtime behavior currently mixed into `protocols/ebus-overview.md`
  moves into `architecture/ebus-runtime.md`.
- BASV orchestration and enrichment behavior moves into
  `architecture/regulator-identity-enrichment.md`.
- B555 validation logs, captures, and implementation-path notes move into
  `development/b555-timer-validation.md`.

### 4. API, Runtime, and Timer Canon

- `B555` becomes the canonical timer protocol story in the docs set.
- `api/graphql.md` and `api/mcp.md` must document `schedules` as the canonical
  timer surface.
- Any retained `B524` timer read material must be documented as low-level,
  limited, and non-canonical rather than the primary timer contract.
- `/ui` and `/portal` terminology must be clarified everywhere touched by this
  plan so readers can distinguish projection-explorer surfaces from the dynamic
  Portal surface.

### 5. Hard-Cut Migration and Proof Discipline

- Stage 1 uses hard-cut renames:
  - no redirect pages
  - no compatibility aliases
  - no shadow copies of renamed pages
- The proof standard is path and meaning preservation:
  - links must be updated
  - protocol material must remain implementable
  - moved Helianthus-specific material must land in a more appropriate section
    rather than simply disappear
- Every downstream issue and PR in this workstream must reference the canonical
  plan URL once the import merges.

### 6. Repository Sanitation

- Stage 1 includes a repository-sanitation pass for `helianthus-docs-ebus` as
  part of `M0`.
- Remote branches that carry no content beyond what already exists on
  `origin/main` must not remain as pseudo-objectives or stale execution lanes.
- The sanitation target set for this plan is explicit:
  - delete `issue/203-b555-timer-protocol` because it is stale and has no unique
    content relative to `origin/main`
  - delete `feature/adr-026-wave2-comprehensive-icons` after confirming that
    the `ADR-026` wave-2 objective content already exists on `origin/main`
- After sanitation, `main` remains the only canonical source of truth for those
  objectives; the deleted branch names may still be referenced in historical
  notes, but not as active repo state.

## Workstream Plan

### M0. Locked Import and Issue Scaffolding

- Create the locked plan package in `helianthus-execution-plans`.
- Sanitize the `helianthus-docs-ebus` remote branch inventory before downstream
  content execution starts.
- Split the canonical document into reviewable chunks under the repository token
  budget.
- Define canonical issue IDs, milestone order, and status tracking files.
- Require downstream issues and PRs to carry the canonical plan URL once it
  exists.

`ISSUE-DOC-00`: sanitize the docs repo branch inventory by removing stale or
objective-equivalent remote branches once parity against `origin/main` is
proven.

### M1. Entry Points, Naming, and Navigation

- `ISSUE-DOC-01`: correct stale top-level and overview claims, and repair the
  docs entrypoint story.
- `ISSUE-DOC-02`: replace `basv.md` with
  `ebus-vaillant-regulators.md` and normalize the regulator catalog.
- `ISSUE-DOC-03`: align the Vaillant protocol index with `B523`, `B524`, and
  `B555`, including the new `B523` stub.

### M2. Protocol Boundary Surgery

- `ISSUE-DOC-04`: perform the surgical split between protocol canon and
  Helianthus-specific architecture or development material.
- This milestone includes:
  - `B524 structural decisions` relocation
  - BASV orchestration and enrichment extraction
  - `ebus-overview` runtime extraction
  - B509 and B524 page surgery limited to Helianthus-specific publication and
    API mapping material

### M3. API, Timer, and Terminology Alignment

- `ISSUE-DOC-05`: make the timer story canonical around `B555`, document
  `schedules` in GraphQL and MCP docs, and clarify `/ui` versus `/portal`.
- Explicitly position any `B524 read_timer` story as low-level and non-canonical.

### M4. Proof Sweep and Maintenance Handoff

- `ISSUE-DOC-06`: run the proof sweep, repair broken relative links, and verify
  that `protocols/` still stands on its own as an implementation-facing source.
- After the proof sweep, transition the plan toward `.maintenance/` when the
  main correction wave is merged.

## Execution and Proof Contract

- The plan import must validate with
  `scripts/validate_plans_repo.sh` in `helianthus-execution-plans`.
- Every split chunk must remain below the token budget for both GPT-5-family and
  Claude tokenizers and must carry the canonical hash of this document.
- After this import merges, all downstream task issues must use the org Task
  template and fill:
  - `Canonical plan`
  - `Doc-gate`
  - `Knowledge capture`
  - `Proof / Evidence`
- After this import merges, all downstream PRs must fill:
  - `Canonical Plan`
  - `Commands Run`
  - `Proof / Evidence`
  - `Doc-Gate`
  - `Knowledge Capture`
  - `PASS / FAIL`
- The `M0` sanitation pass must prove remote-branch disposition with repository
  evidence:
  - `git ls-remote --heads origin`
  - `git rev-list --left-right --count origin/main...<branch>`
  - `git diff <branch>..origin/main -- <touched paths>`
- The sanitation pass is complete only when:
  - `issue/203-b555-timer-protocol` is removed from the remote branch set
  - `feature/adr-026-wave2-comprehensive-icons` is removed from the remote
    branch set after parity confirmation against `origin/main`
- Any reverse-engineering discovery made during execution must use the
  `re-finding` template and include:
  - raw evidence
  - current hypothesis
  - falsification path
  - docs target
  - canonical plan link
- The Stage 1 proof sweep fails if any of the following remain true after
  downstream implementation:
  - surviving references to `protocols/basv.md`
  - surviving references to the old `B524 structural decisions` path
  - `README.md` or overview pages still describe live gateway or API surfaces as
    stubs when that is false
  - `B523`, `B524`, and `B555` are not reachable from top-level docs entrypoints
  - hard-cut renames leave broken relative links
  - `protocols/` no longer contains enough protocol material to support an
    independent implementation without consulting Helianthus architecture docs
- Assumptions locked into this import:
  - no GitHub Discussion exists yet, so this plan uses a bootstrap source marker
  - this workstream consumes `.github` templates as process constraints but does
    not modify the `.github` repo itself
  - `target_repos` stays limited to `helianthus-docs-ebus`
  - Stage 1 remains surgical and conservative rather than a full structural
    migration
