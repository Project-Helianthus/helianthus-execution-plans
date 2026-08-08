# MSP-03A Facade Spike Evidence

Status: `accepted`
Date: `2026-07-08`

## Scope

MSP-03A is the first M3 runtime feasibility row. It proves
`github.com/enbility/eebus-go v0.7.0` can be pinned and compiled behind the
`helianthus-eebusreg/internal/...` boundary without approving runtime start,
pairing mutation, trust-store persistence, gateway import, MCP, GraphQL, Portal,
Home Assistant, raw writes, or candidate semantics.

This is not the end-of-M3 architecture review. M3 remains open until MSP-03B,
MSP-03C, and MSP-03D prove toolchain/container boundaries, HA runtime networking,
black-box fake peer behavior, and live VR940f smoke.

## GitHub Evidence

- Repo: `Project-Helianthus/helianthus-eebusreg`
- Issue: [#8](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/8)
- PR: [#9](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/9)
- Merge commit: `2b5b06315bd873dc214f602e9c5e9d0d6922208b`
- Branch: `issue/8-eebus-go-internal-facade`

## Accepted Implementation

The merged spike:

- pins `github.com/enbility/eebus-go v0.7.0` in `go.mod`;
- adds `internal/eebusfacade` only;
- exposes only plain internal evidence structs;
- allows direct `github.com/enbility/...` imports only under `internal/`;
- compile-binds read-only/configuration observations from `eebus-go/api`;
- records upstream lifecycle and pairing mutators as excluded hazards, not
  approved Helianthus facade calls;
- adds tests for module pin/no replace, exact approved reader surface,
  callback-shape drift, no premature runtime imports/effects, and no exported
  facade signature leakage through direct types or local aliases;
- documents local scope and verification in
  `helianthus-eebusreg/docs/internal-facade-spike.md`.

## Verification

Local verification before merge:

```bash
./scripts/ci_local.sh
GOWORK=off go test -race -count=1 ./...
GOWORK=off go mod tidy -diff
GOWORK=off go mod verify
GOWORK=off go list -m -json github.com/enbility/eebus-go
! git grep -n 'github.com/enbility' -- '*.go' ':!internal/**'
GOWORK=off go list -m all
git diff --check
```

GitHub CI:

- `validate` passed on PR #9.

Recorded module evidence:

```text
Path: github.com/enbility/eebus-go
Version: v0.7.0
Time: 2024-09-21T16:05:36Z
GoVersion: 1.22.0
Sum: h1:Uh3i+HMmTYecWA+BBlYYhNFuNtqzWWQarbv4z9n/aQI=
GoModSum: h1:ftoVhXGC00IEcfN4RZSb1PbBIglE9i3JYqwrjhXnYSA=
```

## Review Ledger

GPT-only review passes were run before PR creation:

- `gpt-5.5 xhigh`: flagged runtime/pairing mutators being promoted into the
  expected facade surface; fixed by moving them into explicit excluded hazards.
- `gpt-5.5 high`: flagged hard-coded service-reader evidence, weak alias-leak
  tests, and subset-only surface tests; fixed with reflected callback-shape
  checks, recursive local type-spec leak tests, and exact slice assertions.
- `gpt-5.4-mini high`: flagged incomplete verification docs and README wording;
  fixed before merge.

## Gate Decision

MSP-03A is accepted. MSP-03B is now the next ready `helianthus-eebusreg` row,
subject to one-PR-per-repo serialization.

No M3 milestone architecture review is due yet. The M3 review must wait until
MSP-03D completes the black-box fake peer and live VR940f smoke gates.
