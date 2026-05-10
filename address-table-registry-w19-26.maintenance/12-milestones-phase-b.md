# Phase B Milestones — Deferred (Address-Table Registry)

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

Depends on: Phase A complete, M8 live validation green, parent plan `ebus-good-citizen-network-management.maintenance/91-milestone-map.md` for context.

Scope: define Phase B (deferred) milestones M6 (enrichment merge with SN sanity gate) and M7 (EvidenceBuffer migration to address-table-event consumer). Phase B is NOT in scope for the operator's 2h target; it is a future follow-up after Phase A live evidence is collected.

Idempotence contract: re-reading this chunk yields the same Phase B specification. Phase B starts only after Phase A is fully merged + live-validated. Promoting Phase B to Phase A would require a new plan amendment with canonical-hash bump.

Falsifiability gate: Phase B milestones have their own falsifiability criteria, deferred until Phase A evidence informs final design. The Phase A plan does not gate on Phase B completion.

Coverage: this chunk covers Phase B milestones only. Phase A is in `11-milestones-phase-a.md`. Live validation criteria are in `13-acceptance-criteria-and-falsifiability.md` (Phase A criteria; Phase B criteria authored at activation time).

## M6_ENRICHMENT_MERGE — SN-driven pointer-merge with denylist gate

- Repos: `helianthus-ebusgateway`, `helianthus-ebusreg`
- Complexity: 7
- Routing: Claude (correctness-critical merge logic)
- Transport-gate: REQUIRED (semantic identity reconciliation can affect runtime behavior)
- Doc-gate: REQUIRED (AD06 SN merge gate becomes normative; updates `sn-merge-gate.md` from forward-reference to active spec)
- Scope:
  - Triggered by B509 ScanID 0x29 reply or coherent B524 identity-bearing response
  - For each AddressSlot whose Device.Identity has non-empty (Mfr, DevID, SN) and SN ∉ denylist `{0x00000000, 0xFFFFFFFF, 0x7FFFFFFF}`:
    - search across registry for any other AddressSlot whose Device.Identity matches the same triple
    - if found: pointer-merge — `slot[target].Device = slot[source].Device`; merge `Faces` lists (deduplicated by addr); promote `verification_state` to `identity_confirmed` on all affected slots
    - if matching SN but missing Mfr or DevID: log warning + DO NOT merge (gate-fail)
  - Configurable denylist via gateway flag `--sn-merge-denylist` (default: `0x00000000,0xFFFFFFFF,0x7FFFFFFF`)
  - Static-seeded slots whose Identity gets enriched by post-merge identity fold: promote from `verification_state=candidate` to `identity_confirmed`
- Acceptance:
  - Unit: spike `(Vaillant, BASV2, 0x12345678)` reply seen at 0x15, separately at 0xEC → both slots converge to single DeviceEntry with merged Faces.
  - Negative: same SN reply at 0x15 with SN=0 → no merge, log warning.
  - Live: when 0xEC's underlying hardware (BASV2) sends a B524 identity reply, runtime merge collapses the static seed entry into the live one.

## M7_EVIDENCEBUFFER_MIGRATION — Wire address-table to deprecate / supplement EvidenceBuffer

- Repo: `helianthus-ebusgateway`
- Complexity: 7
- Routing: Claude
- Transport-gate: REQUIRED
- Doc-gate: REQUIRED (announce the migration; deprecate `evidence_buffer.md` from `helianthus-docs-ebus`)
- Scope:
  - Address-table emits domain events `AddressTableSlotInserted{addr, role, source, confidence}` and `AddressTableMergeCompleted{merged_addrs, identity}`
  - EvidenceBuffer (PR #562) becomes a downstream consumer of these events: on `SlotInserted{source=passive_observed}` → `EvidenceBuffer.Record(weak)`; on `MergeCompleted` → no-op (address-table is now authoritative)
  - PR #562's direct passive-frame → EvidenceBuffer wiring is REMOVED. EvidenceBuffer becomes purely event-driven from address-table.
  - PassiveDiscoveryPromoter (PR #562) becomes redundant for slot insertion and is replaced by AddressTable's own bounded active-confirmation logic. Promoter is deprecated and deleted.
  - Configurable kill-switch `--enable-legacy-evidence-buffer` for one release cycle (default: false; enables the old direct path for rollback)
- Acceptance:
  - Unit: address-table inserts trigger EvidenceBuffer events; legacy direct path is dead code.
  - Live: after M7 deploy, `passive_discovery_promoter` log lines disappear; address-table-driven inserts produce identical user-visible outcome.
  - Transport-matrix re-run: zero unexpected fail/xpass deltas vs M0A baseline.

## Phase B activation

Phase B starts when ALL conditions hold:
1. Phase A merged and live-validated (M8 GREEN).
2. Operator approves Phase B activation explicitly (this is a separate operator decision, not auto-triggered).
3. New cruise-state meta-issue created OR same meta-issue revived with explicit phase-transition comment.

Phase B execution follows the same cruise-control protocol as Phase A.
