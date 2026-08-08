# W28/2026 M4 Architecture Closure

Status: `closed_pass_with_carried_evidence`
Recorded: `2026-07-17`
Canonical cruise state: [execution-plans issue #58](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/58)

This append-only checkpoint records the final M4 architecture closure verdict.
It does not amend protocol, architecture, or API documentation. Those remain
exclusively owned by `Project-Helianthus/helianthus-docs-eebus`.

## Verdict

- M4: `PASS_WITH_CARRIED_EVIDENCE`
- Blockers: `none`
- MSP-045: `GO`

The fresh bounded milestone review accepted the previously merged M4 evidence,
confirmed the corrective pre-dial dependency chain, and verified that the
shutdown/removal race discovered during the first closure attempt is closed in
the exact production composition.

## Final Dependency State

`helianthus-eebusreg` main is
`b0484ca2f647d1cce832c103eaaa4bd2a3d725de` and requires:

- `github.com/Project-Helianthus/helianthus-eebus-go v0.7.1-helianthus.1`
- `github.com/Project-Helianthus/helianthus-ship-go v0.6.1-helianthus.2`
- `github.com/Project-Helianthus/helianthus-spine-go v0.7.1-helianthus.1`

The published module has zero `replace` directives. The active docs API
manifest and generated eebusreg manifest remain byte-identical at 95,207 bytes
with SHA-256
`c93492bd275b5e14d3c9e05da701730d6d34a197e0653e6b169d103418bfcc8c`.

## Shutdown Race Closure

The prior M4 closure attempt exposed a real race between
`Hub.Shutdown()` and asynchronous exact connection removal in ship-go `.1`.
The strict repair chain is:

- ship-go tests-only RED:
  `60d7abd4fa42e3cd3041d3a3564ee3e8c0947f94`
- ship-go RED CI: `29558017458`
- ship-go GREEN:
  `12527637fc43d029e79d609de688ab57ab1f23f1`
- ship-go exact-head CI: `29558460383`
- ship-go squash merge:
  `91c302d939a57e60406e1329962e1be8729ceb86`
- ship-go post-merge CI: `29558641311`
- annotated release: `v0.6.1-helianthus.2`
- tag object:
  `4c774ead7847463a32d96c27912f8bdd4a4b54aa`
- peeled commit:
  `91c302d939a57e60406e1329962e1be8729ceb86`
- release tree:
  `8a84f9889845ed6aa2a1acae6c452f8604aa61df`
- provenance manifest SHA-256:
  `54f91f18ab094825f68db61cad0423b4fadf2720179a09d2168d7cd988a43097`

The release inventory contains 25 modules, 64 module-graph edges, and 226
package dependencies. The remote annotated tag and peeled commit were verified
after publication.

The eebusreg adoption chain is:

- tests-only pin RED:
  `ca00e2742e61a11e06d67b7b6d8fa44c2cafecb1`
- RED CI: `29558891249`
- GREEN adoption:
  `27a47f4f943e8915165d17c013f34673b3e844db`
- exact-head CI: `29559147615`
- squash merge:
  `b0484ca2f647d1cce832c103eaaa4bd2a3d725de`
- post-main CI: `29559299794`

Post-main jobs `87818134322`, `87818134318`, and `87818134341` passed.
The PR and squash-merge trees are identical at
`748ac152b78b409ed495307b4ef7660bfd5282aa`.

The exact production-composition test that captured the original race,
`TestMSP04CR2ExecutedArtifactRejectsCallbackOnlyAccountingAndRedactsPrivateBindings`,
passed under `-race -count=20` after adoption of ship-go `.2`.

## Closure Criteria

| Criterion | Disposition |
|---|---|
| SHIP/SPINE raw-runtime boundary | Satisfied; no eBUS transport/router/registry or consumer leakage. |
| Read-only public API and admin-local mutation | Satisfied; frozen API hash and docs manifest remain exact. |
| Trust, restore, revocation, quarantine, and repair | Satisfied by accepted MSP-04C and MSP-04C-R evidence. |
| Durable authorization before every outgoing dial | Satisfied for selected paths, fallback, and reconnect, including stale callback and restart denial. |
| Shutdown/removal lifecycle | Satisfied by the reviewed `.2` release and exact race-trigger proof. |
| Documentation, provenance, and temporary-fork policy | Satisfied; docs ownership is external to code repos and upstream repatriation remains post-M4. |
| M4.5 consumability | Satisfied; MSP-045 can freeze and version the state model without ad hoc security policy. |

## Carried Evidence

- MSP-04C source merge:
  `843cf4a6bb109d8d3ff44c6cf7c52911af712beb`; exact CI
  `29467283318`; post-main `29467383548`.
- MSP-04C-R docs merge:
  `b67c3a48c072da1cc4d350580f3f866bbf05775d`.
- MSP-04C-R source merge:
  `4842b91567e5edd124372e17b742094d05ebc31c`; exact CI
  `29478088923`; post-main `29478228948`.
- Previously accepted M2/M3 and G17/G19 evidence remains closed. The
  dependency-local race repair did not require new same-LAN claims.

## Forward State

MSP-045 is unlocked. M4.5 owns state-version, migration, and consumer
conformance freeze. M5 and M6 retain their own sidecar isolation,
disabled-default, feature-graph, MCP snapshot, and no-drift gates.

The temporary SHIP/SPINE/eeBUS forks remain patch carriers until the accepted
changes are proposed upstream and equivalent tagged upstream releases exist.
Repatriation is not an M4 blocker and must preserve checkpoint 111's provenance
and equivalence requirements.
