# M2 Raw Contracts Architecture Review

Status: `m2-complete`
Date: `2026-07-08`

## Scope

This review closes M2 for the eeBUS raw-first VR940f plan:

- `helianthus-eebusreg` raw runtime identity contract;
- `helianthus-eebusreg` raw snapshot/evidence envelope contract;
- `helianthus-docs-ebus` raw correlation and Leaf Promotion Dossier policy.

It does not approve `enbility/eebus-go` runtime integration, trust-store
implementation, gateway import, MCP serving, candidate semantic facts, or any
consumer exposure.

## Artifacts

| Item | Repo | Issue | PR | Merge commit |
| --- | --- | --- | --- | --- |
| MSP-02A raw runtime identity contract | `helianthus-eebusreg` | [#4](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/4) | [#5](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/5) | `28d2f8162b67ea274c089ed1686c9ce84b054e7d` |
| MSP-02B raw snapshot/evidence envelope | `helianthus-eebusreg` | [#6](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/6) | [#7](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/7) | `c064c0d1d19cd0c392734bede136f55040b76c67` |
| MSP-02C raw correlation and leaf-promotion dossier | `helianthus-docs-ebus` | [#335](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/335) | [#336](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/336) | `70a4921f287116f539cb4ce522ee9809cd9bf3c6` |

## Validation Evidence

MSP-02A:

- `./scripts/ci_local.sh` in `helianthus-eebusreg`: PASS.
- GitHub Actions validate: PASS on PR #5.
- Two GPT-5.5 high reviews were run; findings were addressed before merge.

MSP-02B:

- `./scripts/ci_local.sh` in `helianthus-eebusreg`: PASS.
- `GOWORK=off go test -race -count=1 ./...`: PASS.
- `git diff --check`: PASS.
- GitHub Actions validate: PASS on PR #7.
- GitHub Codex connector was unavailable for that repo; three local GPT-only
  reviews were run instead. Findings on runtime digest binding, forged
  `data_hash`, API-boundary relaxation, lowercase digests, and defensive
  object copying were fixed before merge.

MSP-02C:

- `PATH="$PATH:$(go env GOPATH)/bin" ./scripts/ci_local.sh` in
  `helianthus-docs-ebus`: PASS.
- `git diff --check`: PASS.
- GitHub Docs Checks: PASS on PR #336.
- GitHub Codex review found the M7/M8 coexistence-field ambiguity; local
  GPT-5.5 reviews found source-family identity, replay/hash binding, and
  mutable-proof dossier gaps. All were fixed before merge.

## Architecture Review

### Raw Boundary

Verdict: PASS.

`helianthus-eebusreg` public packages remain constrained to raw runtime,
identity, and evidence contracts. The API boundary gate still rejects public
registry, projection, semantic, SHIP/SPINE, `enbility`, GraphQL, Portal, Home
Assistant, command-routing, trust-store, trust-mutation, pairing-window,
snapshot-name, evidence-ref, and dereference surfaces before their later gates.

### Anti-Leak And Promotion

Verdict: PASS.

MSP-02C explicitly blocks raw `eebus.v1.*` fields, paths, labels, evidence refs,
and candidate facts from merging into `ebus.v1.*`, GraphQL, Portal, Home
Assistant, command routing, or `helianthus-ebusreg` semantic outputs. Candidate
correlation remains evidence-only until M8 coexistence and M8.5 leaf-promotion
lock.

### Determinism And Replay

Verdict: PASS for M2 draft contracts.

MSP-02B defines stable envelope hashing with runtime/contract/tool/scope/mask
tier/auth binding, UTC timestamps, stable ordering, lowercase digest
validation, stale or forged `data_hash` rejection, and defensive copying.
MSP-02C requires replay/hash comparability bindings in each promotion dossier.

### Security And Privacy

Verdict: PASS for M2 draft contracts.

Raw stable identifiers are redacted. Runtime evidence refs require a digest
binding. Unknown fields remain opaque and redacted. `vendor_restricted` content
is quarantined from public repos/issues/PRs/reviews/ADR rationale, and public
claims must cite publishable evidence IDs.

### Documentation Ownership

Verdict: PASS.

Cross-protocol contracts live in `helianthus-docs-ebus/docs/platform/`.
eeBUS-native notes live in `helianthus-docs-eebus` and cross-seed durable
promotion knowledge back to the platform contract. M2 does not move protocol
ownership into `helianthus-eebusreg`.

### M3 Readiness

Verdict: READY WITH BOUNDS.

M3 may start with MSP-03A only. The allowed scope is an internal facade spike
against pinned `github.com/enbility/eebus-go v0.7.0` and toolchain/module
boundary proof. M3 must still not add production trust store, gateway import,
MCP server, raw writes, GraphQL, Portal, Home Assistant, command routing, or
promoted semantics.

## Remaining M3 Gate Risks

- `eebus-go v0.7.0` is pre-v1 and must stay behind internal facades until the
  M3/M3.5 gates prove boundaries.
- HA networking, mDNS, manual endpoint, and credential persistence are not
  proven by M2 and remain MSP-03C/MSP-03D work.
- Live VR940f smoke and fake-peer evidence are not proven by M2 and remain
  blocked until the M3 feasibility sequence reaches those issues.
- Trust, pairing, admin-local, restore, quarantine, and first-trust behavior
  remain M4/M4.5 work.
