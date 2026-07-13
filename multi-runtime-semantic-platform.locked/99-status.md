# Status

State: `locked`
Started: `2026-04-12`
Last revised: `2026-07-10`
Current milestone: `RECOVERY_RECONCILIATION`
Cruise phase: `RECOVERY_RECONCILIATION`
Amendment count: `1`
Amendment: `AD-DOCS-01 external-only-documentation`
Accepted through: `MSP-03C plus merged MSP-03D EEBUS-G01 fake-peer harness only`
Dirty rescue candidate: `true`
Successor unlocks: `false until MSP-R00-L and MSP-03D-R merge from clean main`
Baseline: `Gateway 0.4.0`

## Current Position

AD-DOCS-02 is the current amendment. Publication-contract v2 and the live
46-row audit are recorded in `106-ad-docs-02-integrity.json` and
`107-ad-docs-02-topology-audit.md`; `100-topology-audit.md` remains the
immutable AD-DOCS-01 snapshot. Candidate cleanup fails closed and any consumed
evidence is corrected only by a forward fix.

The plan is locked after five accepted adversarial rounds and the AD-DOCS-01
external-only-documentation amendment. Historical evidence is preserved through
M0, M1, M2, MSP-03A, MSP-03B, MSP-03C, and the merged MSP-03D EEBUS-G01
fake-peer harness slice. M3 and MSP-03D remain open.

Dirty rescue work may be useful as a candidate, but it is not accepted code,
does not unlock successors, and must be reconciled through clean-main recovery
rows.

`MSP-R00` is completed locally for issue #14 with no code acceptance, no
runtime successor unlock, and architecture review PASS. Public artifacts omit
local commit SHA, private paths, raw HMAC mappings, source-bundle detail, raw
paths, volume, sizes, timestamps, bytes, deterministic IDs, and raw hashes.

The final plan-lock architecture review is recorded in
`102-plan-lock-architecture-review.md` with verdict `PASS`.

## Ready Rows

- `MSP-DOCS-API-SCHEMA`: ready after execution-plans PR #62 merges; its only
  predecessor `DOCS-VERIFY` is already complete.

## Completed Recovery Publication

- `MSP-R00-L`: completes only when execution-plans PR #62 merges. Because the
  redacted ledger and these state surfaces merge atomically, the post-merge
  state is complete and the MSP-R00-L predecessor is satisfied.
- `DOCS-VERIFY`: completed in Project-Helianthus/helianthus-docs-eebus PR #5
  at 954b6353.

No runtime successor may start from dirty code or local recovery artifacts.

## Accepted Historical Evidence

- M0 control-plane plan update and transport-gate seed:
  `2860d742e2682fbc42d1a5d98906031a0ff3e45d` and
  `93ef8cebadf842ebdffb5f3a0eb34806d5766ff5`.
- MSP-01A platform docs ownership:
  `55f5482e0513ceb3bed8ddd5f2656d3b3ae7be41`.
- MSP-01B/MSP-01C docs-eebus bootstrap/provenance:
  `9d3637e09d9573d9d7f31bdda86b1039770ba41b`.
- MSP-020 eebusreg bootstrap/hardening:
  `f441e4a1987f775367ad3046e68ba1caf04b2f20`.
- MSP-02A raw runtime identity:
  `28d2f8162b67ea274c089ed1686c9ce84b054e7d`.
- MSP-02B raw snapshot/evidence:
  `c064c0d1d19cd0c392734bede136f55040b76c67`.
- MSP-02C raw correlation and Leaf Promotion Dossier policy:
  `70a4921f287116f539cb4ce522ee9809cd9bf3c6`.
- MSP-03A internal facade spike:
  `2b5b06315bd873dc214f602e9c5e9d0d6922208b`.
- MSP-03B local/build-container toolchain proof:
  `82f8f3cfd42d8e5c830d1e8e4e9e029614c14a7e`.
- MSP-03C HA add-on proof gate:
  `b3c9930ca244dfe636f79356b8d482c6c84e043c`; canonical docs:
  `c1fc6bde5a273fdd1ccbe1826479769fe0731a71`.
- MSP-03D fake-peer harness slice:
  `0e58327dfdb86ef243a19e18d590564813feaa00`; only EEBUS-G01 is accepted.

## Open Work

- Run MSP-DOCS-API-SCHEMA after execution-plans PR #62 merges.
- Run MSP-DOCS-PLATFORM after MSP-DOCS-API-SCHEMA completes; after
  execution-plans PR #62 merges, its MSP-R00-L side is satisfied.
- Continue the serialized docs chain with MSP-DOCS-E2 and MSP-DOCS-CLEAN only
  after their predecessors complete.
- Re-run clean-main MSP-03D-R with revised G17 and G19 after DOCS-CLEAN.
- Close MSP-035, MSP-04A, MSP-036, MSP-055, MSP-04B, MSP-04C, and MSP-045 in
  one eebusreg PR at a time.
- After MSP-036, prepare and pin the single MSP-055 source PR, merge
  MSP-DOCS-API-CANDIDATE against its exact head, then merge MSP-055 only after
  the exact-match gate passes.
- Run MSP-DOCS-API-FREEZE after MSP-055 and before MSP-04B.
- Continue gateway M5, MCP M6, evidence, candidates, coexistence, promotion,
  and consumer work only after predecessor gates merge.

## Gate Corrections

- G17 means configured local SHIP advertisement/discovery, myVaillant trust
  visibility, and negative/TTL behavior. It is not evidence that the VR940f
  advertises a server.
- G18 means M8 coexistence no drift only.
- G19 means direct outbound VR940f TCP/TLS/WebSocket/SHIP access completion
  plus first post-access SPINE data.
- MSP-03D closes only after both revised G17 and G19 pass with owner
  acceptance.
- Feature graph completeness and reconnect durability belong to MSP-055/M6,
  not G17.

## Scope Blocks

GraphQL, Portal, Home Assistant, command routing, raw writes, and promoted
semantics remain out of scope until their later milestones and per-leaf locks.

No public artifact may contain packet captures, raw transcripts, keys, PEM
blocks, tokens, trust stores, raw SKI, raw SHIPID, raw IP/MAC address, or raw
serial values. The additional ban on raw or identifying paths, volume, sizes,
timestamps, byte counts, deterministic IDs, and raw hashes applies specifically
to MSP-R00/MSP-R00-L recovery publication. Later gate evidence may publish the
redacted timestamps, acceptance metadata, and cryptographic commitments its
locked public-safe template requires, but never restricted preimages or raw
payloads. Full fidelity remains encrypted outside git with mode `0600` or is
discarded.

Durable language-neutral platform contracts remain canonical in
`helianthus-docs-ebus/docs/platform/`. eeBUS protocol behavior lives in
`helianthus-docs-eebus/protocols/`; runtime/adapter/trust/persistence/lifecycle
architecture lives in `helianthus-docs-eebus/architecture/`; and eeBUS-specific
Go public API schema/reference/examples live in `helianthus-docs-eebus/api/`.
Every page has `canonical_source`. `helianthus-eebusreg` has no `docs/`
directory and no substantive protocol, architecture, API, harness, test, or
user documentation.
