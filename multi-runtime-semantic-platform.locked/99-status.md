# Status

State: `locked`
Started: `2026-04-12`
Last revised: `2026-07-30`
<!-- M625_RELEASE_PROJECTION_BEGIN -->
Release-proof control: `released_chain_redeployed`
Cruise phase: `MSP-0625-S13-DOCS`
Current milestone: `MSP-0625-S13-DOCS`
LAB acceptance state: `accepted`
Selected batch: `MSP-0625-S13-DOCS`
Accepted through: `Base M6.25 LAB remains accepted after released-chain redeploy, but stable-MCP/M6.25 final closure is held by the bounded SPINE 1.3 erratum; zero promoted leaves`
<!-- M625_RELEASE_PROJECTION_END -->
Amendment count: `9`
Amendment: `M6.25 bounded SPINE 1.3 erratum`
Dirty rescue candidate: `false`
Successor unlocks: `only through the M6.25 and live-completion chain`
Baseline: `Gateway 0.4.0`

## Current Position

Successor record 123 adds a bounded SPINE 1.3 erratum after record 122's
published M6.25 implementation reconciliation. M0-M6 history remains valid;
`100-topology-audit.md` remains the immutable AD-DOCS-01 snapshot.
`106-ad-docs-02-integrity.json` remains the unchanged AD-DOCS-02 integrity
record, while `107-ad-docs-02-topology-audit.md` is regenerated from the active
matrix. Candidate cleanup still fails closed and consumed evidence is corrected
only by a forward fix.

Current routing, readiness, and completion-token authority is `92-m0-issue-matrix.yaml` plus generated `107-ad-docs-02-topology-audit.md`; `106-ad-docs-02-integrity.json` is the immutable historical M5 integrity record.

The plan remains locked after five accepted adversarial rounds. M5 and M6 are
complete. Base M6.25 LAB remains accepted after released-chain redeploy. The
current gap is the bounded SPINE 1.3 erratum needed before stable-MCP/M6.25
final closure; the selected row is `MSP-0625-S13-DOCS`.

Record 121 remains authoritative for recovery and authorization. Record 122
leaves the DAG and exact five M6.25 tool names unchanged while recording
completed/published PLAN, DOCS-E, SPINE, EEBUS, REG-EXEC, REG-MUT, GW-ROUTER,
GW-MCP, and DOCS-P. LAB operational acceptance used terminal quarantine, has
no auto-rollback claim, and promotes no mutable leaf. The generated
release-proof projection above is authoritative for current LAB state.

Record 123 adds the exact docs-eebus#96 -> spine-go#15 -> eebus-go#23 ->
eebusreg#103 -> ebusgateway#762 chain. Its DOCS row requires accepted
`MSP-0625-LAB` and completed `MSP-0625-DOCS-P`. All old edges remain exact,
and only `MSP-0625-S13-GW-LAB` is appended to the two existing
`MSP-065-LIVE-R1` predecessors.

The public baseline is exactly 49 READ declarations, 26 successes, and 23
failures with three public-safe evidence hashes. No raw identity is recorded.
Scope is limited to the pinned SPINE 1.3 value-type and function-data
corrections; `9970150` key/update-engine changes, duplicate
`9f07e2a`/`06d9bf0` cherry-picks, a wholesale upstream `dev` merge, and SPINE
1.4 are excluded.

Historical M6.5 is framework-complete/live-partial. Historical M7, M8, and M8.5
are synthetic-only/partial, with zero promoted leaves. Their administrative
closure does not prove live completion and cannot unlock M9. M9 has not started
substantively.

`MSP-R00` is completed locally for issue #14 with no code acceptance, no
runtime successor unlock, and architecture review PASS. Public artifacts omit
local commit SHA, private paths, raw HMAC mappings, source-bundle detail, raw
paths, volume, sizes, timestamps, bytes, deterministic IDs, and raw hashes.

The final plan-lock architecture review is recorded in
`102-plan-lock-architecture-review.md` with verdict `PASS`.

## Ready Rows

The generated release-proof projection is the sole selected-batch authority.

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

- Publish the bounded SPINE 1.3 erratum docs gate, then release and explicitly
  repin the spine-go -> eebus-go -> eebusreg -> gateway dependency chain.
- Redeploy that erratum chain and repeat the owner-only, read-only 49-READ
  sweep while preserving the already accepted base M6.25 lab proof.
- Execute the live M6.5-R1 through M8.5-R1 chain.
- Keep M9 blocked until `MSP-085-LIVE-R1` and
  machine-checkable `promoted_leaf_count > 0`.

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

GraphQL, Portal, Home Assistant, candidate references, aliases, v2 surfaces,
and promoted semantics remain out of scope until their later milestones and
live per-leaf locks. M6.25 raw WRITE exists only as owner-local bounded
acquisition through the gateway router and durable mutation coordinator.
The SPINE 1.3 erratum itself is READ-only. The exact five M6.25 tool suffixes,
all no-write stops, the `candidate_ref` prohibition, and the owner-local
raw/public-redacted boundary remain fail-closed and unchanged.

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
