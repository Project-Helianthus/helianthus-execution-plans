# Docs Stage 1 Execution Plan 04: Execution Proof and Mapping

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `762f47b9c2b2eaf45849f7cd51bdb0038d76bf41c6476207bc6fa5de37037572`

Depends on: `10-entrypoints-and-taxonomy.md`, `11-protocol-boundary-surgery.md`, and `12-api-runtime-and-timer-alignment.md`. This chunk closes the workstream contract and assumes the content changes are already defined.

Scope: Milestone wiring, repo sanitation, canonical issue mapping, `.github` template alignment, proof gates, and the explicit unknowns that remain after the Stage 1 lock.

Idempotence contract: Reapplying this chunk must not create conflicting issue IDs, relax proof requirements, or permit downstream work to proceed without canonical-plan linkage.

Falsifiability gate: A review fails this chunk if downstream issues or PRs can omit the canonical plan URL, if repo-sanitation targets remain ambiguous, if proof gates do not protect the hard-cut rename set, or if residual uncertainty is hidden instead of named.

Coverage: Locked Decisions 5-6; Workstream M0 and M4; Execution and Proof Contract.

---

## Milestone Wiring

- `M0`: locked-plan import, docs-repo sanitation, and downstream issue scaffolding
- `M1`: entrypoints, naming, and navigation
- `M2`: protocol-boundary surgery
- `M3`: API, timer, and terminology alignment
- `M4`: proof closeout and transition toward `.maintenance/`

## Canonical Issue Contract

- `ISSUE-DOC-00`: repo sanitation and remote branch cleanup
- `ISSUE-DOC-01`: entrypoints and stale-claim correction
- `ISSUE-DOC-02`: `basv.md` rename and regulator catalog normalization
- `ISSUE-DOC-03`: Vaillant protocol index alignment with `B523` and `B555`
- `ISSUE-DOC-04`: surgical protocol and architecture split for `B524`, `B509`,
  BASV, and `ebus-overview`
- `ISSUE-DOC-05`: API, timer, and terminology alignment
- `ISSUE-DOC-06`: proof sweep, broken-link cleanup, and maintenance handoff

## Downstream Workflow Contract

- once this import merges, every related task issue must use the org Task
  template and fill `Canonical plan`, `Doc-gate`, `Knowledge capture`, and
  `Proof / Evidence`
- once this import merges, every related PR must fill `Canonical Plan`,
  `Commands Run`, `Proof / Evidence`, `Doc-Gate`, `Knowledge Capture`, and
  `PASS / FAIL`
- any new reverse-engineering discovery in this workstream must use the
  `re-finding` template with raw evidence, hypothesis, falsification path, docs
  target, and canonical plan link

## Repo Sanitation Contract

- the sanitation target set is fixed:
  - `origin/issue/203-b555-timer-protocol`
  - `origin/feature/adr-026-wave2-comprehensive-icons`
- `issue/203-b555-timer-protocol` is treated as stale and removable because it
  has no unique content relative to `origin/main`
- `feature/adr-026-wave2-comprehensive-icons` is treated as
  objective-equivalent and removable once parity against `origin/main` is
  proven for the ADR-026 wave-2 content
- accepted sanitation proof consists of:
  - remote head listing from `git ls-remote --heads origin`
  - ahead/behind counts from
    `git rev-list --left-right --count origin/main...<branch>`
  - zero content diff on the relevant touched path against `origin/main`

## Proof Sweep

- validate the plan import with `scripts/validate_plans_repo.sh`
- require the canonical plan URL in all downstream issues and PRs before work
  proceeds
- complete `ISSUE-DOC-00` before opening the main Stage 1 docs-edit lane
- fail the Stage 1 proof sweep if any of the following remain true after
  downstream implementation:
  - `issue/203-b555-timer-protocol` still exists as a remote branch
  - `feature/adr-026-wave2-comprehensive-icons` still exists as a remote branch
  - `protocols/basv.md` is still referenced as canonical
  - the old `B524 structural decisions` path is still referenced as canonical
  - top-level pages still describe live gateway or API surfaces as stubs when
    that is false
  - `B523`, `B524`, and `B555` are not reachable from top-level entrypoints
  - hard-cut renames leave broken relative links
  - `protocols/` is no longer sufficient for an independent implementation

## Explicit Unknowns

- additional small cleanup may emerge after the first link and naming sweep
- a second-order boundary audit may reveal more embedded Helianthus-specific
  notes to extract later
- those findings do not justify weakening the hard-cut, surgical Stage 1 rules
