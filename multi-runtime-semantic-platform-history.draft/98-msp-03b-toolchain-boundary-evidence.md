# MSP-03B Toolchain Boundary Evidence

Status: `accepted`
Date: `2026-07-08`

## Scope

MSP-03B proves the `helianthus-eebusreg` module and toolchain boundaries after
the MSP-03A internal facade spike. It does not start SHIP/SPINE services, open
listeners, create credentials, persist trust state, import the gateway, expose
MCP tools, or run HA networking checks.

This is not the end-of-M3 architecture review. M3 remains open until MSP-03C
and MSP-03D prove HA runtime networking, independent black-box fake peer
behavior, and live VR940f smoke.

## GitHub Evidence

- Repo: `Project-Helianthus/helianthus-eebusreg`
- Issue: [#10](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/10)
- PR: [#11](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/11)
- Merge commit: `82f8f3cfd42d8e5c830d1e8e4e9e029614c14a7e`
- Branch: `issue/10-toolchain-boundary-proof`

## Accepted Implementation

The merged proof:

- adds `scripts/toolchain_boundary_proof.sh`;
- forces `GOWORK=off` and `GOTOOLCHAIN=local`;
- pre-scans `go.mod` for any `replace` directive before any module-graph
  dependent `go run`;
- rejects any `replace` directive in the checker;
- validates the active Go binary, `go` directive, and future `toolchain`
  directive against the configured maximum Go language version for each lane;
- validates `github.com/enbility/eebus-go v0.7.0` module JSON and no
  replacement;
- runs boundary gates, tidy diff semantics, `go mod verify`, `go list -m all`,
  `go test ./...`, and `go build ./...`;
- emits checksums for `go.mod`, `go.sum`, and the module graph;
- hardens `git grep` calls so fatal grep failures cannot be treated as no-match
  success;
- extends the no-runtime/no-trust implementation gate across internal packages
  except boundary-checker tooling and tests;
- adds GitHub CI jobs for Go 1.22 validation and Go 1.26 Alpine build-container
  proof with `/workspace` configured as a Git safe directory.

## Verification

Local verification before merge:

```bash
./scripts/toolchain_boundary_proof.sh
./scripts/ci_local.sh
GOWORK=off GOTOOLCHAIN=local go test -race -count=1 ./...
GOWORK=off GOTOOLCHAIN=local go mod tidy -diff
GOWORK=off GOTOOLCHAIN=local go mod verify
git diff --check
```

GitHub CI on PR #11:

- `validate` passed with Go `1.22.12` and
  `HELIANTHUS_EEBUSREG_MAX_GO_VERSION=1.22`.
- `build-container-proof` passed in `golang:1.26-alpine` with
  `HELIANTHUS_EEBUSREG_MAX_GO_VERSION=1.26`.

## Review Ledger

GPT-only review passes were run before PR creation:

- `gpt-5.5 xhigh`: flagged checker trust through the module graph,
  implementation-wide runtime/trust coverage, and Go-version lane ambiguity.
  Fixed with a shell pre-scan before `go run`, no-`replace` policy, repo-wide
  implementation grep, and explicit Go 1.22/Go 1.26 lane documentation.
- `gpt-5.5 high`: flagged unsafe `git grep` status handling, Docker
  `safe.directory`, active Go binary validation, and prerelease-version parsing.
  Fixed with checked grep wrappers, Docker safe-directory setup, active Go
  validation, and `go/version` language-version comparison.
- `gpt-5.4-mini high`: no documentation findings after scope review.

The first GitHub CI run exposed two portability issues:

- Go 1.22 does not support `go mod tidy -diff`; fixed with tidy fallback plus
  `git diff --exit-code -- go.mod go.sum`.
- The Docker shell did not preserve PATH for `go`; fixed by exporting
  `/usr/local/go/bin` in the container command.

Both GitHub jobs passed after the fix.

## Gate Decision

MSP-03B is accepted. MSP-03C is now the next ready M3 row in
`helianthus-ha-addon`, subject to repo serialization.

No M3 milestone architecture review is due yet. The M3 review must wait until
MSP-03D completes the black-box fake peer and live VR940f smoke gates.
