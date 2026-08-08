# W28/2026 MSP-04C-R2 Forward Checkpoint

Status: `active_corrective_execution`
Recorded: `2026-07-16`
Canonical cruise state: [execution-plans issue #58](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/58)

This append-only checkpoint records execution state after the bounded M4
architecture closure review. It does not amend protocol, architecture, or API
documentation. Those remain exclusively owned by
`Project-Helianthus/helianthus-docs-eebus`.

## Accepted M4 History

- MSP-04C source merge: `843cf4a6bb109d8d3ff44c6cf7c52911af712beb`.
- MSP-04C exact-head CI: run `29467283318`, success.
- MSP-04C post-merge CI: run `29467383548`, success.
- MSP-04C-R docs merge: `b67c3a48c072da1cc4d350580f3f866bbf05775d`.
- MSP-04C-R source merge: `4842b91567e5edd124372e17b742094d05ebc31c`.
- MSP-04C-R source exact-head CI: run `29478088923`, success.
- MSP-04C-R source post-merge CI: run `29478228948`, success.

The resulting code preserves the frozen public eeBUS API boundary and closes
the original restore, quarantine, retry-accounting, revocation-withdrawal, and
restart-composition findings. MSP-045 remains blocked because the follow-up
architecture review found that authorization still occurs after the dependency
has begun an autonomous outgoing connection attempt.

## R2 Corrective Decision

The pinned upstream pair `github.com/enbility/ship-go@v0.6.0` and
`github.com/enbility/eebus-go@v0.7.0` does not expose a public seam capable of
proving authorization before every concrete outgoing network dial. Callback
injection is therefore not valid pre-dial evidence.

The smallest accepted correction is:

1. `helianthus-ship-go` adds an optional synchronous fail-closed outgoing
   attempt gate immediately before each concrete dial, including path fallback
   and hostname/IP retry calls.
2. Every permit carries an attempt identity and cancellable context. Denial
   produces no network call or automatic reannounce for that attempt.
3. `helianthus-eebus-go` exposes only the internal configuration bridge needed
   to install the gate and propagate attempt identity.
4. `helianthus-eebusreg` durably commits `ATTEMPT_RESERVED` before returning a
   permit, treats unresolved restart reservations fail-closed, rejects stale
   callbacks, and serializes revocation against the same attempt context.
5. Injectable-dialer and fake TLS/SHIP peer evidence binds permits and durable
   reservations to actual dial starts and peer accepts.

No fork type or protocol-specific mutation is added to the frozen public
`helianthus-eebusreg` API. No `replace` directive is accepted in a published
module graph.

## Public Work Items

- Contract: [helianthus-docs-eebus issue #28](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/28).
- Contract PR: [helianthus-docs-eebus PR #29](https://github.com/Project-Helianthus/helianthus-docs-eebus/pull/29), head `7a1835463c72e6649624f89367b3d6acefb3a178`.
- SHIP fork: [helianthus-ship-go issue #1](https://github.com/Project-Helianthus/helianthus-ship-go/issues/1), based on upstream `v0.6.0` commit `760c312bf723d726d8882af3bb06650ddcd11ca9`.
- eeBUS fork: [helianthus-eebus-go issue #1](https://github.com/Project-Helianthus/helianthus-eebus-go/issues/1), based on upstream `v0.7.0`.
- Runtime adoption: [helianthus-eebusreg issue #32](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/32).

## Serialized Forward Order

1. Merge the reviewed MSP-04C-R2 contract.
2. Implement, review, merge, and immutably tag the SHIP fork.
3. Implement, review, merge, and immutably tag the eeBUS bridge fork.
4. Adopt exact fork tags in `helianthus-eebusreg` under strict RED-first TDD.
5. Bind G10/G11/G16 pre-dial artifacts and rerun the bounded M4 architecture
   closure review.
6. Unlock MSP-045 only after `PASS` or `PASS_WITH_CARRIED_EVIDENCE`.

Hardware evidence remains SSH-only after resume. Direct multicast, mDNS, and
same-LAN reachability are not assumed or claimed by this checkpoint.
