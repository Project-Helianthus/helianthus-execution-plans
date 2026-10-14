# Tests and acceptance

Canonical-SHA256: `d0a36bfd392bb82100b40cd6741e6d5116ba708096c5ecae442b41d092d8f997`
Depends on: [15-northbound-and-amendments.md](./15-northbound-and-amendments.md).
Scope: Characterization, parity, transport, lifecycle and rollback proof.
Idempotence contract: Re-reading creates no work; fixed fixtures preserve outputs, and lifecycle retries reuse receipts and exact uncertain bytes.
Falsifiability gate: Compare pre-move characterization, ownership, parity and applicable transport evidence; unmet decisions stop the affected node.
Coverage: Canonical section 6; 92 retained acceptance.

## 6. Test strategy and completion evidence

Before **each family move**, commit characterization fixtures/goldens against the exact pre-move code, with production unchanged, as gateway #1024 commit 1 did. Then commit extraction and rerun the same fixtures in one review frame. Cover success, empty/disabled, unknown/candidate, stale generation, malformed evidence, failure and withdrawn outputs, using fixed clocks and sanitized native bytes. No public shape change without goldens; schema/output goldens document intended changes but cannot authorize a breaking stable v1 change. Approved cutovers have old→new comparison, consumer migration and explicit contract amendment.

| Family | Characterization and move proof |
|---|---|
| CAN | Growatt V1.04 projection/evidence and Gree raw/candidate DTOs; do not promote VRF evidence to a battery. New acquisition requires native transport lifecycle fixtures and exact profile disposition. No CAN tool/metrics shape is invented as an existing golden. |
| Modbus | SunSpec chain/identity/qualification→PV snapshots; exact Growatt RTU→storage; Tesla completed outcomes→EVSE. Preserve first-incarnation IDs, native error/provenance/loss, conditional tools and M2M/Portal/Prometheus/Matter views. Exercise lazy multi-asset PV, identity rotation, predecessor/successor and rejected publications. |
| eeBUS | SHIP/trust/pairing/listener/outgoing slot, raw feature authorization/mutation outcomes, configured vs applied participation, overlay replay and unknown/frozen dispositions. Prove terminal fence and no stale callbacks/implicit trust promotion. |
| eBUS | Native bytes/ACK reconstruction/dedup, identity/address promotion, mux/proxy/B503 session ordering, scans/polling/cache/watch, state revalidation and thermal/native public views. Preserve aliases and write admission. #1021 keeps full request/response bytes and provenance with no automatic qualification. |

Surface fixtures compare actual MCP discovery/schema/envelopes and MCP↔GraphQL parity, GraphQL aliases/subscriptions, Portal catalog/native explorer/action/readiness, setup validation/options/argv, state namespace compatibility, health and exact Prometheus text. G5 tools use the kernel-owned peer-credential socket and compare to the typed internal service; no GraphQL lifecycle counterpart is added. Fallback has no tools; prove service behavior and no exposure. Existing status parity runs. Consumer fixtures cover HA, secure M2M and Matter feed where used. Close classification coverage gaps rather than assume every `v1` tool is stable.

Lifecycle proof boots `runGatewayLifecycle` with no native endpoint, STOPPED, slow/failing starts and two independently failing fixtures. Test direction/collision/ownership, durable receipt/revision replay, shell-first startup, generation-owned tasks, restart non-overlap, stale native callbacks and staged publication rejection. Crash at acceptance/ACTIVE/reservation/submit-result-loss/withdrawal/close; prove exact uncertain bytes and retained snapshots/cursors, not digest reconstruction. `EpochJournal` alone is insufficient. Shared-asset isolation/LIFE-22 has its own accepted prerequisite; G4 one-source assets cannot prove it.

Transport gates are owning-repository behavior evidence: retain eBUS T01..T88/AD01..AD12, required real P01–P06 smoke, independent offline Modbus RTU conformance, and applicable eeBUS/CAN native gates. Inventory anchors `GW scripts/transport_gate.sh:82,151,422`, `scripts/passive_smoke_gate.sh:7,335,344` describe current classification; classify actual final diff and behavior before execution. Physical eBUS override never skips offline RTU and is scope-specific, not granted by this plan. Guarded config/gateway/startup/observer changes need the required smoke before push. New code placement cannot evade behavior gates. Fixtures cannot replace final physical acceptance.

Code PRs record exact HEAD, commands/results, fixtures/goldens, docs/native contract versions and unrun/blocked checks. Run appropriate CI/race tests, no sibling checkout dependency. Fresh independent opposite-camp exact-HEAD review continues while P0–P2 remain; merge only at NO_BLOCKING_FINDINGS with prior blockers resolved or independently validated by design. P3/P4 disposition does not force another round; no round cap. Supplied G4 older round-cap wording is not retained. This planning task performs no code tests or independent product acceptance.

Rollback is an owning-repository deliverable: preserve the prior complete package/BOM and compatible state; test upgrade/downgrade with unknown namespaces, stable GUID, identities, trust/pairing and receipts. Never roll back after uncertain native work by resending under a new key; reconcile outcomes first. A code/config/dependency/package change after candidate review invalidates affected evidence: fresh Daybreak and affected hardware/conformance tests apply to the changed final BOM. Missing claimed hardware remains a release blocker.

Issue complexity is a planning estimate, not acceptance. Each future issue body follows G4 rigor: exact source/contract baseline, bounded production/test manifest, scope/non-goals, concrete reachable negative scenarios, verifiable acceptance, docs/gate applicability, rollback and decisions. Re-estimate if a move exceeds its manifest; split within that owning repository without silently weakening acceptance.
