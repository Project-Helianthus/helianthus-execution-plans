# Address-Table Registry — Network Management

State: `draft` (will become `locked` post-validator)
Slug: `address-table-registry-w19-26`
Started: `2026-05-06`
Planner: `Codex gpt-5.5 high (3 adversarial rounds, ready_to_lock=true)`
Consultant: `Claude consultant subagent (eBUS NM design validation, GO recommendation, 3 mandatory corrections)`
Parent plan: `ebus-good-citizen-network-management.maintenance` (deferred M3 completion)
Predecessor PRs: `helianthus-ebusgateway#560` (structural startup-probe seed) + `helianthus-ebusgateway#562` (EvidenceBuffer-based runtime promotion) — both merged.

## Summary

PR #562 wired a runtime passive-promotion pipeline based on `EvidenceBuffer`,
but architectural review confirmed it cannot detect slave-only Vaillant
addresses: `0x04` (NETX3 secondary slave), `0xF6` (NETX3 primary slave),
`0xEC` (SOL00). These addresses never appear as src/dst in passive frames on
the operator's bus (24h Prometheus capture: zero observations). The fix
requires a registry-side architectural change — completing the
`PhysicalDevice + BusFace + companion-pair` identity model that was scoped
as M3 in `ebus-good-citizen-network-management` but superseded before
implementation.

## Objective

Replace `helianthus-ebusreg`'s `map[byte]*deviceEntry` registry storage
with a `[256]*AddressSlot` array indexed by byte address. Each
`AddressSlot` carries `{addr, role, source, confidence, *DeviceEntry}`.
`DeviceEntry` owns `Identity (Manufacturer, DeviceID, SN) + Faces []BusFace`
independently of slot state. Insertion at slot[ZZ] AND slot[companion(ZZ)]
fires when a previously-unknown address responds at link layer (positive
ACK from frame-start), with a second-corroboration gate before companion
slot is filled. Static seed table in `helianthus-ebus-vaillant-productids`
covers structurally-undetectable addresses (0x04, 0xEC) per Vaillant
hardware-ownership facts. PR #562's `EvidenceBuffer` becomes optional
downstream consumer of address-table events in Phase A; full migration
deferred to Phase B.

## Decision matrix

- **AD01** Address-storage primitive: `[256]*AddressSlot` indexed array (matches `ebusd` reference impl `m_seenAddresses[256]`). Operator-stated, consultant-validated.
- **AD02** Slot↔Identity separation: `AddressSlot` carries pointer to `*DeviceEntry`; multiple slots may share one DeviceEntry. Slot-level state (role, source, confidence) is distinct from device-level identity (Mfr/DevID/SN/Faces).
- **AD03** Companion derivation: per eBUS standard `companion(master X) = X+5 (mod 0x100)`; `companion(slave Y) = Y-5 (mod 0x100)` IFF `Y-5` is initiator-capable per bit-pattern rule (each nibble in `{0x0, 0x1, 0x3, 0x7, 0xF}`). 0x26 and 0xEC have no master pair (0x21, 0xE7 fail bit-pattern); 0x04↔0xFF holds (0xFF is valid lowest-priority master).
- **AD04** 0xFF dual-meaning resolution (Codex C1): 0xFF is BOTH NACK byte AND lowest-priority master. Insert at slot[0xFF] only when 0xFF appears at frame-start as src/dst, NOT in ACK position. Pre-existing reconstructor distinguishes positions.
- **AD05** Insertion soundness gate (Codex C2): Insert slot[ZZ] on positive ACK (0x00) following complete request, NOT on NACK. Companion-pair insertion requires SECOND corroborating observation (twice ACK, OR one ACK + one identity reply). Self-source excluded.
- **AD06** Merge sanity gate (Codex C3): Pointer-merge slots only when `(Manufacturer, DeviceID, SN)` triple matches AND SN ∉ `{0x00000000, 0xFFFFFFFF, 0x7FFFFFFF}`. Gate-fail → log warning + leave entries separate. (Phase B M6.)
- **AD07** Static seed semantics (Codex Round 2): seed entries create AddressSlots with `source=static_seed, confidence=low`. They make addresses visible (GraphQL devices) but DO NOT collapse identities. M6 SN-merge later promotes confidence on coherent identity match.
- **AD08** Static seed default (Codex Round 3): `EnableStaticSeedTable` feature flag, default **false** initially. Operator opts in via addon config for Phase A live validation. Forward-promotion to default-true requires docs establishing entries as model-level Vaillant facts.
- **AD09** TDD strict mode (Codex Round 2): every implementation milestone preceded by per-repo RED test commit (cruise-dev-supervise enforced). Per-repo staging avoids cross-repo dependency deadlock.
- **AD10** Phase A vs Phase B split (operator's 2h target): Phase A delivers passive/static visibility for {0xF6 via companion derivation, 0x04 + 0xEC via static seed}. Phase B (deferred) delivers SN-driven enrichment merge + EvidenceBuffer migration.
- **AD11** Predecessor preservation: PR #560 + PR #562 logic remains untouched in Phase A. Address-table emits events that EvidenceBuffer can OPTIONALLY consume (additive). No deprecation in Phase A.
- **AD12** Transport-gate: REQUIRED. M3/M4 alter link-layer interpretation of ACK/NACK and 0xFF disambiguation. Pre-change baseline at M0A; post-change verify at M9.
- **AD13** Doc-gate: REQUIRED. Address-table model + companion rules + ACK/NACK semantics + SN merge gate + static seed provenance + passive-detection limits + live-validation acceptance — all canonicalized in `helianthus-docs-ebus`.
- **AD14** GraphQL/HA consumer compatibility (Codex Round 3): static candidates exposed with explicit `discovery_source` and `verification_state` fields. HA integration verified to either filter candidate-only entries OR handle the metadata correctly. M8 acceptance covers this.
- **AD15** Cross-repo sequencing: M0B_TDD_GATE staged per-repo (ebusreg → ebusgo → productids → gateway) to avoid the `one_pr_per_repo_at_a_time` invariant deadlock (Codex Round 3).

## Live-verified constraints (24h Prometheus on operator's bus)

- 0xFF as master src: **0 observations** → companion-derivation alone CANNOT detect 0x04 → M5 static seed required.
- 0xEC as src/dst: **0 observations** → structurally undetectable in pure-passive mode → M5 static seed required.
- 0xF6 (NETX3 slave) as src/dst: **0 observations**, but 0xF1 master src: **9 observations in 3h** → companion derivation `companion(0xF1) = 0xF6` covers detection.

## Phase A milestones (target: 2h wall-clock)

`M0_DOC_SPEC → M0A_TRANSPORT_BASELINE → M0B_TDD_GATE → M1_REGISTRY_ARRAY_REFACTOR → M2_COMPANION_PURE_FUNC → M2A_OBSERVATION_CORRELATOR_SPEC → M3_FIRST_OBSERVATION → M4_COMPANION_INSERT_WITH_CORROBORATION → (parallel: M5A_SEED_API_CONTRACT → M5_STATIC_SEED_TABLE) → M8_LIVE_VALIDATION → M9_TRANSPORT_VERIFY → M0C_DOC_EVIDENCE_UPDATE`

Detailed milestone scope: see `11-milestones-phase-a.md`.

## Phase B milestones (deferred)

- `M6_ENRICHMENT_MERGE` (complexity 7) — SN-driven pointer-merge with denylist gate.
- `M7_EVIDENCEBUFFER_MIGRATION` (complexity 7) — wire address-table events to deprecate / supplement `EvidenceBuffer`.

Detail: `12-milestones-phase-b.md`.

## Falsifiability gate (live HA validation)

After Phase A merge + deploy:

**Positive assertions:**
- GraphQL devices includes `0xF6` discovered via passive observation alone (NETX3 0xF1 traffic → companion-derive → slot[0xF6] insert with `source=passive_observed`).
- GraphQL devices includes `0x04` and `0xEC` via static seed (`source=static_seed, confidence=low`) when `EnableStaticSeedTable=true`.
- Existing 0x08/0x15/0x26 unchanged (PR #560/#562 logic intact).

**Negative assertions:**
- NACK-only observations do NOT insert.
- Broadcast `0xFE` as dst does NOT insert.
- ACK byte `0xFF` in ACK position does NOT insert.
- Self-source (gateway's admitted source) does NOT insert.
- Single-corroboration companion does NOT insert (must have second observation OR identity reply).

**Transport gate:** T01..T88 matrix re-run, no unexpected fail/xpass deltas vs M0A baseline.

Detail: `13-acceptance-criteria-and-falsifiability.md`.

## References

- Consultant validation report: `consultant agent run aa67dc058ee96d896` (eBUS NM spec compliance + ebusd reference impl alignment).
- ebusd source: `bushandler.h` `symbol_t m_seenAddresses[256];` (canonical reference for [256] array model).
- eBUS App Layer V1.6.1 §FFh (NM service catalog 00h..06h; storage representation NOT mandated).
- Maintenance plan ancestor: `ebus-good-citizen-network-management.maintenance` (M3 originally scoped this work).
- Predecessor merged PRs: `Project-Helianthus/helianthus-ebusgateway#560` + `#562`.
