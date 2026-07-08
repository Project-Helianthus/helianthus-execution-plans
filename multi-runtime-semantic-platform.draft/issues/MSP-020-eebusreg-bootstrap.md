# MSP-020 - Bootstrap helianthus-eebusreg Raw Runtime Repo

## What

Create `helianthus-eebusreg` as the raw eeBUS runtime/evidence module shell.

## Why

MSP-02A and later runtime contracts need a repo boundary before any code can
land. The repo must prove by construction that `helianthus-eebusreg` is raw
runtime/evidence plumbing, not a semantic registry fork, and that `enbility`,
SHIP, SPINE, gateway imports, listeners, and trust-store code remain out until
their later gated issues.

## Acceptance Criteria

- [ ] Module path is `github.com/Project-Helianthus/helianthus-eebusreg`.
- [ ] Public package names are limited to `eebusruntime`, `eebusraw`, and
      `eebusevidence`.
- [ ] Public API contains no `registry`, `reg`, `projection`, `semantic`, or
      `enbility` export names.
- [ ] No `github.com/enbility/*`, SHIP, SPINE, gateway, trust-store, listener,
      pairing, or network runtime code exists.
- [ ] CI enforces terminology, public-boundary, gofmt, vet, build, and tests.
- [ ] README and AGENTS.md point to the platform docs ownership ADR and raw
      repo boundary.
- [ ] Local CI passes.
- [ ] CI green.

## Dependencies

- Depends on Project-Helianthus/helianthus-execution-plans#35, which accepts
  MSP-00A/MSP-00B/MSP-00C including issue #34.
- Depends on Project-Helianthus/helianthus-docs-ebus#334, which accepts MSP-01A
  platform docs ownership and the required order for MSP-020 before MSP-02A.
- Depends on Project-Helianthus/helianthus-docs-eebus#3, which accepts the
  eeBUS-native docs bootstrap/provenance hygiene for MSP-01B/MSP-01C.
- Current state is repo-local landed, not successor-unlocking accepted, until
  all predecessor PRs above are merged.

## Complexity And Lane

- Complexity: 4
- Lane: `gpt-5.4-mini`

## Repo Serialization

This is the first `helianthus-eebusreg` issue and PR. No other PR may be open
in that repo while it is active.

## Doc Gate

Required. Canonical owner: `helianthus-docs-ebus/docs/platform`.

## Transport/Security Gates

Transport gate: none. Security gate: none.

This issue must not introduce protocol/runtime code that would trigger the
M3 transport gate or M4 trust/security gate.

## Rollback

Archive or delete the empty bootstrap repo and revert links from the execution
plan if the repo boundary is rejected.

## Review Ledger

Review must check repo naming, public API/package boundary, CI coverage,
absence of runtime/listener/trust code, and absence of semantic registry fork
language in public API names.
