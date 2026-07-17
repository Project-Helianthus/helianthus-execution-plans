# Status

State: `locked`
Started: `2026-04-12`
Last revised: `2026-07-17`
Current milestone: `M5_PRODUCTION_PREREQUISITES`
Cruise phase: `M5_PRODUCTION_PREREQUISITES`
Amendment count: `3`
Amendment: `MSP-05B production-prerequisite correction`
Accepted through: `MSP-05A with M4.5 trust and admin state frozen`
Dirty rescue candidate: `false`
Successor unlocks: `only through the corrected production-prerequisite chain`
Baseline: `Gateway 0.4.0`

## Current Position

The MSP-05B production-prerequisite correction is current. Publication schema
v2 remains stable while its control-plane amendment binding and the complete
live audit are recorded in `106-ad-docs-02-integrity.json` and
`107-ad-docs-02-topology-audit.md`; `100-topology-audit.md` remains the
immutable AD-DOCS-01 snapshot. Candidate cleanup fails closed and any consumed
evidence is corrected only by a forward fix.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

The plan remains locked after five accepted adversarial rounds. Recovery, M3,
M3.5, M4, M4.5, and the inert M5A gateway scaffold are closed by their
published artifacts. The M5B preflight found production runtime stubs and a
lossy gateway-to-runtime configuration boundary, so direct M5B dispatch is now
forbidden.

`MSP-R00` is completed locally for issue #14 with no code acceptance, no
runtime successor unlock, and architecture review PASS. Public artifacts omit
local commit SHA, private paths, raw HMAC mappings, source-bundle detail, raw
paths, volume, sizes, timestamps, bytes, deterministic IDs, and raw hashes.

The final plan-lock architecture review is recorded in
`102-plan-lock-architecture-review.md` with verdict `PASS`.

## Ready Rows

- `MSP-DOCS-05P`: sole ready row. It freezes production activation, protected
  material, exact listener scope, independent discovery policy, and lossless
  gateway configuration mapping before dependent code begins.

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

- Merge MSP-DOCS-05P in `helianthus-docs-eebus`.
- Implement exact-address listener and independently gated mDNS in
  `helianthus-ship-go`, preserving the legacy constructor.
- Thread the policy through an additive `helianthus-eebus-go` constructor.
- Serialize the additive bind-address API, host-bound protected identity, and
  real production runtime construction in `helianthus-eebusreg`.
- Map gateway configuration exactly in MSP-05A-R1, then implement MSP-05B.
- Continue M6 and later milestones only after all completion tokens validate.

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
