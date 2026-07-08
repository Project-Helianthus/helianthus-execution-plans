# M1 Docs Bootstrap Evidence

Status: `local-evidence`
Date: `2026-07-08`

## Scope

This evidence note records local M1 progress after the M0 control-plane seed:

- platform ownership ADR added to `helianthus-docs-ebus`;
- eeBUS-native docs repository created as `helianthus-docs-eebus`;
- provenance and publication policy seeded;
- local CI run for both docs paths.

## Artifacts

Filed M0 issues:

- MSP-00A: https://github.com/Project-Helianthus/helianthus-execution-plans/issues/33
- MSP-00B: https://github.com/Project-Helianthus/helianthus-execution-plans/issues/32
- MSP-00C: https://github.com/Project-Helianthus/helianthus-execution-plans/issues/34

Execution-plan draft PR:

- https://github.com/Project-Helianthus/helianthus-execution-plans/pull/35

Filed M1 issues:

- MSP-01A: https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/333
- MSP-01B: https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/1
  closed by bootstrap commit `d15353296605e057a7fe5e0a11e4e066cdfb405c`
- MSP-01C: https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/2
  closed by bootstrap commit `d15353296605e057a7fe5e0a11e4e066cdfb405c`

`helianthus-docs-ebus`:

- Issue: https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/333
- Draft PR: https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/334
- Bootstrap-order fix commit in PR #334:
  `b6af8ef291b124e7ffe6488303f04e20f72de3e4`
- `docs/platform/README.md`
- `docs/platform/ownership-and-doc-gates.md`
- `docs/platform/eebus-raw-first-contract.md`
- `README.md` documentation map update

`helianthus-docs-eebus`:

- Repository: https://github.com/Project-Helianthus/helianthus-docs-eebus
- Bootstrap commit: `d15353296605e057a7fe5e0a11e4e066cdfb405c`
- VR940f summary-only hygiene PR:
  https://github.com/Project-Helianthus/helianthus-docs-eebus/pull/3
- VR940f summary-only hygiene merge commit:
  `9d3637e09d9573d9d7f31bdda86b1039770ba41b`
- `README.md`
- `AGENTS.md`
- `development/contributing.md`
- `protocols/ship-spine-overview.md`
- `devices/vr940f.md`
- `evidence/README.md`
- `evidence/evidence-template.md`
- `re-notes/template.md`
- `scripts/ci_local.sh`

## Validation

Commands run:

```bash
PATH="$(go env GOPATH)/bin:$PATH" ./scripts/ci_local.sh
```

Result in `helianthus-docs-ebus`: PASS after installing the documented
`jv v0.7.0` checker with `go install`.

Result for updated PR #334 after adding the MSP-020 order: PASS.

```bash
./scripts/ci_local.sh
```

Result in `helianthus-docs-eebus`: PASS.

Result for VR940f summary-only hygiene PR #3: local CI PASS. No GitHub checks
were reported for that repository branch. PR #3 was squash-merged.

Execution-plan validation remains green:

```bash
./scripts/validate_plans_repo.sh
git diff --check
```

## Remaining Work

- Merge `helianthus-docs-ebus` PR #334 after review.
- Link MSP-01A to the merged docs PR once accepted.
- File later milestone issues from the M0 matrix only after M1 doc ownership is
  accepted.
