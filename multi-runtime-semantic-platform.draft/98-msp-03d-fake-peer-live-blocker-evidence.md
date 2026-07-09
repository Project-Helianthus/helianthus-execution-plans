# MSP-03D Fake-Peer Harness And Live VR940f Blocker Evidence

Status: `partial`
Date: `2026-07-09`

## Scope

MSP-03D requires both an independent black-box fake peer and a live
VR940f/myVaillant smoke run before M3 runtime feasibility can close.

This artifact records a partial merge only:

- EEBUS-G01 fake-peer handshake evidence is accepted.
- EEBUS-G17 live VR940f remains blocked because no `_ship._tcp` service is
  visible to the harness.

This does not approve MSP-035, production trust, gateway import, MCP,
GraphQL, Portal, Home Assistant, command routing, raw writes, promoted
semantics, or B509/B524/B555 enrichment.

## GitHub Evidence

- Repo: `Project-Helianthus/helianthus-eebusreg`
- Issue: [#12](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/12)
- PR: [#13](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/13)
- Merge commit: `0e58327dfdb86ef243a19e18d590564813feaa00`
- PR head before squash: `35b0408f35d1d22cb79f99eebbe308cebeb1c641`
- Docs gate: `helianthus-docs-ebus` PR
  [#340](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/340)
  at `114072fe8bdf027cfdd3472d7f2b0896a2496db4`

Issue #12 was reopened after the partial merge so the live VR940f gate remains
tracked.

## Accepted Implementation

The merged `helianthus-eebusreg` slice adds an internal-only smoke harness under
`internal/eebusinteropsmoke`:

- `fake-peer` mode starts two local disposable `eebus-go v0.7.0` SHIP/SPINE
  services and requires the fake peer to import no Helianthus facade under
  test.
- `live-vr940f` mode probes `_ship._tcp` mDNS visibility and records BLOCKED
  when no service is visible or no approved remote SKI is supplied.
- Reports use contract `helianthus.eebus.transport-gate.v0`, include repo,
  branch, commit, Go/toolchain/module evidence, and redact public identifiers.
- Disposable credentials are in-memory only; no production trust-store state is
  written.
- Boundary gates continue to reject public API, gateway imports, MCP, GraphQL,
  Portal, Home Assistant, command routing, raw writes, production trust-store
  surfaces, and promoted facts.

The PR also fixed Linux/Go 1.22 mDNS socket portability by using
`golang.org/x/sys/unix` for `SO_REUSEADDR` and `SO_REUSEPORT` instead of the
non-portable `syscall.SO_REUSEPORT` constant.

## Verification

Local verification before merge:

```bash
GOWORK=off go test ./internal/eebusinteropsmoke
GOOS=linux GOARCH=amd64 GOWORK=off go test -c ./internal/eebusinteropsmoke -o /tmp/eebusinteropsmoke-linux-amd64.test
./scripts/ci_local.sh
GOWORK=off go run ./internal/eebusinteropsmoke -mode fake-peer -timeout 30s
GOWORK=off go run ./internal/eebusinteropsmoke -mode live-vr940f -timeout 3s || true
git diff --check
./scripts/api_boundary_gate.sh
```

GitHub CI on PR #13:

- `validate` passed with Go `1.22` lane and
  `HELIANTHUS_EEBUSREG_MAX_GO_VERSION=1.22`.
- `build-container-proof` passed in the Go `1.26` Alpine container lane.

Local redaction scan found only intentional redaction-test fixtures and standard
mDNS multicast constants. No public production trust, key, SKI, IP, MAC, serial,
gateway secret, or pairing-history evidence is published by this artifact.

## Gate Results

| Case | Status | Evidence |
| --- | --- | --- |
| EEBUS-G01 fake-peer handshake | PASS | Disposable in-memory certificates, fake-peer import-boundary check, SHIP session connected both directions. |
| EEBUS-G17 live VR940f smoke | BLOCKED | `live-vr940f-mdns-probe-attempted`, `live-vr940f-no-ship-service-visible`, error `no_visible_ship_service`. |

The final local post-commit reports were generated from PR head
`35b0408f35d1d22cb79f99eebbe308cebeb1c641`.

## Review Ledger

The intended GPT-only reviewers were assigned but the agent runtime was
temporarily unavailable due rate limits:

- `GPT-5.5 xhigh` security/redaction review: cancelled and replaced with local
  security/redaction review.
- `GPT-5.5 high` transport semantics review: cancelled and replaced with local
  transport semantics review.
- `gpt-5.4-mini` docs/boundary review: cancelled and replaced with local
  docs/boundary review.

Local review found:

- PR #13 correctly stated EEBUS-G17 was blocked and did not claim live VR940f
  pass.
- The stable public packages and API boundary remained unchanged.
- The only new `enbility/...` imports live under `internal/eebusinteropsmoke`.
- Public artifacts remain redacted and do not publish lab addresses or
  credentials.

## Gate Decision

MSP-03D is not accepted. The fake-peer harness slice is merged and EEBUS-G01 is
accepted, but M3 runtime feasibility remains open until EEBUS-G17 passes against
a visible VR940f/myVaillant `_ship._tcp` service and approved remote SKI.

MSP-035, production trust, gateway sidecar import, and read-only MCP work remain
blocked.
