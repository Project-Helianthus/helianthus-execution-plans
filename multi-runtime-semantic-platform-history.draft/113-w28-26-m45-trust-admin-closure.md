# W28/2026 M4.5 Trust And Admin Projection Closure

Status: `closed_pass`
Recorded: `2026-07-17`
Canonical cruise state: [execution-plans issue #58](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/58)

This append-only checkpoint closes MSP-045 and the M4.5 trust/admin projection
freeze. It records execution evidence only. Protocol, architecture, and API
documentation remain exclusively owned by
`Project-Helianthus/helianthus-docs-eebus`.

## Verdict

- MSP-045: `PASS`
- M4.5: `PASS`
- Unresolved P0-P2 findings: `none`
- M5 gateway sidecar: `GO`

The implementation makes the first-trust coordinator the sole authority for
read-only trust and pairing observations. Configuration admission and
SHIP/SPINE callbacks cannot promote trust. The projection remains internal,
derived, immutable at publication, and absent from the public Go API and disk
schema.

## Documentation Gate

The companion documentation issue and PR are
`Project-Helianthus/helianthus-docs-eebus#32` and `#33`.

- docs merge/main:
  `c309dcae4278089c74b07b949aa2ed84351ce1c9`
- docs post-main CI: `29575838602`
- docs post-main job: `87869942442`
- docs result: `PASS` in `40m41s`

The docs gate passed the full 391-test policy suite, provenance verification,
and publication-evidence step. No substantive eeBUS documentation was added to
the code repository.

## Runtime TDD And Publication Chain

The source issue and PR are
`Project-Helianthus/helianthus-eebusreg#36` and `#37`.

- tests-only RED:
  `03d2110fb09e7cc78c5f80cd54e4702c08dcc7a5`
- RED CI: `29577474161`
- RED validate job: `87875144818`
- RED container job: `87875144853`
- RED API attestation job: `87875144821` (`PASS`)
- initial GREEN:
  `fe4c718461906cef3c51ab5011b9c7051c16039b`
- initial GREEN CI: `29580812141` (`3/3 PASS`)
- bounded review remediation:
  `68939aaa64815ea8bc64e2dbe12d901381df204f`
- remediation exact-head CI: `29583122025`
- exact-head validate: `87893399756`
- exact-head container proof: `87893399746`
- exact-head API attestation: `87893399757`
- squash merge/main:
  `40623a40ddd214868cc4cf2b28a73ada569d79d2`
- post-main CI: `29583263589`
- post-main validate: `87893857031`
- post-main container proof: `87893857071`
- post-main API attestation: `87893857040`

Every exact-head and post-main job passed. The source worktree and topic branch
were removed after publication. The historical primary checkout remained on
`issue/14-recover-dirty-eebus-runtime` at
`4bbbadfdf455d78f5f443c27048e4898c3ff0746` and was not modified.

## Security And Architecture Review

The fresh complexity-9 review found two P1 and four P2 blockers at the initial
GREEN head:

1. stale observer delivery could overwrite a newer denial;
2. shutdown could freeze stale paired fields;
3. a candidate sharing a configured SKI could mutate public liveness before
   durability;
4. an unknown recovery reason could lose structural precedence;
5. a malformed zero-version protected anchor could project paired;
6. a future `PrepareControl` outcome could restore or retain trust.

The bounded remediation added:

- coordinator-owned monotonic projection revisions and stale-delivery fencing;
- serialized projection emission;
- close-time terminal snapshot handoff before public shutdown freeze;
- same-SKI candidate liveness suppression until durable trust;
- a closed recovery-reason classifier;
- one shared exact protected-anchor validator;
- fail-closed handling for every future prepare outcome across confirmation,
  revocation, repair, retry, and pre-dial paths.

Dedicated regression tests cover each finding. Per operator direction, the
cycle closed after targeted verification, full local CI, and exact-head CI;
there was no second broad audit round.

## Frozen Boundaries

| Boundary | Closed value |
| --- | --- |
| Internal contract | `helianthus.eebus.trust-admin-projection.v1` |
| Trust authority | `first_trust_coordinator_only` |
| Public API bytes | `95207` |
| Public API SHA-256 | `c93492bd275b5e14d3c9e05da701730d6d34a197e0653e6b169d103418bfcc8c` |
| Disk/control schema | `v3_unchanged` |
| Candidate public rows | `absent_before_durability` |
| Callback trust role | `liveness_only` |
| GraphQL/Portal/HA | `not_exposed` |
| Raw writes/commands | `not_exposed` |

Local validation passed focused MSP-045 tests, MSP-045 race tests, MSP-04B and
MSP-04C compatibility race tests, public lifecycle and facade terminal-handoff
tests, full `go test -race -count=1 ./...`, API boundary checks, build, vet,
formatting, and `./scripts/ci_local.sh`.

## Scope And Live-Evidence Boundary

M4.5 makes no new same-LAN or VR940f live-connectivity claim. This closure was
completed off-LAN and is based on deterministic code, persistence, fake-peer,
and contract evidence. Hardware access for later milestones remains SSH-only
until an explicit same-LAN session is re-established.

No GraphQL, Portal, Home Assistant, command routing, raw write, promoted
semantic, B509/B524/B555 enrichment, or consumer behavior is unlocked by this
checkpoint alone.

## Rollback And Forward State

Rollback is the squash revert of
`40623a40ddd214868cc4cf2b28a73ada569d79d2`; the docs contract remains as a
candidate record and the public API and disk schema remain unchanged.

M5 may now integrate the disabled-by-default eeBUS gateway sibling runtime.
M6 remains responsible for the stable read-only `eebus.v1.*` MCP namespace,
snapshot binding, deterministic hashes, structured degraded states, and
anti-leak checks. M6.5 and later evidence, candidate semantics, coexistence,
per-leaf promotion, and consumers retain their original gates.

The temporary SHIP/SPINE/eeBUS forks remain patch carriers. Upstream PRs are a
post-M4.5 lifecycle action and must preserve checkpoint 111 provenance and
equivalence requirements before any fork is replaced by an upstream release.
