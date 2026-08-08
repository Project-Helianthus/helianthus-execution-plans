# Gate Readiness Audit - 2026-07-08

Status: `m0-accepted-m1-review-blocked`
Date: `2026-07-08`

## Scope

This audit records whether the eeBUS raw-first plan may proceed from M0/M1 and
MSP-020 into MSP-02A.

## Inputs

- Execution-plan PR: https://github.com/Project-Helianthus/helianthus-execution-plans/pull/35
- Platform docs PR: https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/334
- eeBUS raw runtime repo: https://github.com/Project-Helianthus/helianthus-eebusreg
- eeBUS docs repo: https://github.com/Project-Helianthus/helianthus-docs-eebus
- Bootstrap hardening PR: https://github.com/Project-Helianthus/helianthus-eebusreg/pull/3
- VR940f docs hygiene PR: https://github.com/Project-Helianthus/helianthus-docs-eebus/pull/3

## Mechanical State

`helianthus-execution-plans` PR #35:

- State: merged
- Draft: no
- Merge state: merged by squash
- CI: pass
- Merge commit: `2860d742e2682fbc42d1a5d98906031a0ff3e45d`
- Reviews: Codex comments addressed; active review threads reached zero before
  merge

`helianthus-docs-ebus` PR #334:

- State: open
- Draft: no
- Merge state: blocked by branch policy/formal approval
- Docs CI: pass
- Review decision: empty
- Reviews: Codex re-review reported no major issues
- Active review threads: zero
- Current head: `89ebd1393991db9a97a962be929d2afa51cba729`

`helianthus-eebusreg`:

- Repository exists.
- MSP-020 issue #1 is closed.
- Bootstrap commit `6c4fa77435db48f5cdecfb6b2d586ae0b22d8837` is on `main`.
- GitHub Actions CI passed for the bootstrap commit.
- Bootstrap hardening PR #3 is merged at
  `f441e4a1987f775367ad3046e68ba1caf04b2f20`.

`helianthus-docs-eebus`:

- VR940f summary-only hygiene PR #3 is merged at
  `9d3637e09d9573d9d7f31bdda86b1039770ba41b`.

## Gate Decision

MSP-02A is **not yet cleared to start as an implementation PR**.

Reasons:

- PR #334 has not been merged, so MSP-01A has not established the platform docs
  ownership gate.
- The plan explicitly requires MSP-02A to wait for MSP-020 plus M0/M1
  predecessor acceptance.

## Safe Work Before MSP-02A

Allowed:

- review PR #334;
- address any new review comments;
- refresh gate evidence;
- keep `helianthus-eebusreg` bootstrap CI green;
- prepare, but not file, MSP-02A issue text until predecessor gates are
  accepted.

Forbidden:

- adding an `enbility/eebus-go` facade;
- adding trust-store or listener code;
- importing `helianthus-eebusreg` from the gateway;
- opening an MSP-02A implementation PR before M0/M1 acceptance.

## Adversarial Review

Six sidecar review agents were launched on 2026-07-08 because the operator
requested multi-agent adversarial pressure on this plan. The intended seventh
agent could not be spawned because the agent thread limit was reached.

Review focus areas:

- architecture and semantic-boundary leakage;
- security and trust boundary leakage;
- doc-gate ownership and cross-seeding;
- issue matrix consistency;
- fast mechanical smoke checks;
- portability and toolchain independence.

Findings:

- Architecture/security reviewers found that the initial `helianthus-eebusreg`
  bootstrap exposed public runtime, pairing/trust, raw identity, snapshot, and
  evidence-reference shapes before MSP-02A/MSP-02B/M4 were accepted.
- Issue-matrix review found that MSP-02A directly depended only on MSP-020,
  which could falsely unlock MSP-02A if automation saw MSP-020 closed while
  M0/M1 PRs were still unmerged.
- Issue-matrix review found MSP-02A acceptance too weak versus the canonical
  M2 gate because it did not require a versioned, reviewable contract or the
  eeBUS half of the unknown-field rule.
- Security review found MSP-02A needed a security gate because raw identity can
  expose local SKI, remote SKI, fingerprints, pairing state, and peer/session
  identifiers before MCP masking exists.
- Portability review found the bootstrap package-name gate would block future
  `internal/...` facade packages.
- Documentation review found the platform raw-first order should explicitly
  include MSP-020 before raw identity/snapshot/evidence drafts.

Actions taken:

- Opened `helianthus-eebusreg` PR #3 to remove premature public runtime/raw
  identity/pairing/evidence contract shapes and keep only reserved public
  package boundaries.
- Updated `helianthus-docs-ebus` PR #334 so the platform required order names
  MSP-020 before raw identity/snapshot/evidence drafts.
- Opened `helianthus-docs-eebus` PR #3 so the VR940f page links canonical
  platform promotion ownership instead of restating the rule as local policy.
- Updated the matrix so MSP-020 and MSP-02A directly depend on M0/M1 gates.
- Updated MSP-02A to require a security gate and stronger acceptance for
  versioning, reviewability, unknown eeBUS/SPINE fields, and redaction/masking
  risk.
- Removed trust/pairing mutation methods from the pre-M4.5 public runtime API;
  `RegisterRemoteSKI`, `UnregisterRemoteSKI`, and `SetPairingWindow` are now
  explicitly internal/admin-gated until the M4/M4.5 security model freezes.
- Updated MSP-03A so the M3 facade spike depends on MSP-02C, which is
  transitive on all M2 raw identity, snapshot/evidence, and correlation drafts.
- Moved fake-peer handshake gate ownership out of MSP-03A; MSP-03A now carries
  module/dependency evidence only, while EEBUS-G01 remains on MSP-03D.
- Updated MSP-09C so HA integration depends on MSP-09B Portal ordering, matching
  the canonical GraphQL -> Portal -> HA consumer rollout.
- Codex re-review found an accidental MSP-02B/MSP-02C cycle and an MSP-09B
  self-dependency introduced while applying ordering fixes; both were removed
  before merge-readiness was reported.
- Clarified that `eebus-go v0.7.0` is pinned by the M3 facade spike, not by the
  MSP-020 bootstrap.

## Current Verdict

M0 is accepted and mechanical readiness is good after the
`helianthus-eebusreg` and `helianthus-docs-eebus` PR #3 merges, but M1
predecessor acceptance is still missing. The next required action is formal
approval and merge of PR #334, not MSP-02A runtime work.
