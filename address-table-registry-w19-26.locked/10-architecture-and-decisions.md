# Architecture and Decisions — Address-Table Registry

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

Depends on: parent plan `ebus-good-citizen-network-management.maintenance/00-canonical.md` (M3 deferred), predecessor PRs `helianthus-ebusgateway#560` + `#562` (merged), consultant report (eBUS NM GO) and Codex adversarial rounds 1-3.

Scope: define the AddressSlot / DeviceEntry / BusFace data model, the companion-derivation algorithm including bit-pattern validity, the ACK/NACK insertion rules with 0xFF dual-meaning resolution, the SN merge gate forward-referenced from Phase B, and static-seed semantics with `EnableStaticSeedTable` default-off policy.

Idempotence contract: re-running any decision below MUST yield the same outcome. Decisions are pinned by AD identifier; revisions require a new plan amendment with explicit canonical-hash bump. Any code that consults a decision by AD-id must continue to compile after a future amendment without runtime ambiguity (each AD-id has exactly one resolution at any plan version).

Falsifiability gate: each AD has a unit-testable assertion in the corresponding milestone. Live validation re-checks AD04, AD05, AD07, AD08 explicitly via positive AND negative HA-side observations.

Coverage: this chunk covers the architecture surface; milestone-level breakdown lives in `11-milestones-phase-a.md` and `12-milestones-phase-b.md`. Decision matrix entries AD01..AD15 here are the authoritative reference for implementation prompts.

## AD01 — Address-storage primitive

`[256]*AddressSlot` indexed array in `helianthus-ebusreg/registry`. Replaces existing `map[byte]*deviceEntry`. Constant-time lookup at any byte address. Matches the canonical `ebusd` reference implementation (`bushandler.h: symbol_t m_seenAddresses[256];`).

Nil slot at index `i` means "address `i` has not been observed and is not statically seeded". Non-nil slot means an `AddressSlot` instance exists. Multiple slots may share the same `*DeviceEntry` pointer (slot aliasing for multi-address devices like NETX3).

## AD02 — Slot-vs-Identity separation

```
type AddressSlot struct {
    Addr             byte
    Role             SlotRole         // master | slave | broadcast
    DiscoverySource  DiscoverySource  // passive_observed | static_seed | active_confirmed
    VerificationState VerificationState // candidate | corroborated | identity_confirmed
    Device           *DeviceEntry     // pointer (multiple slots may share)
    FirstObservedAt  time.Time
    LastObservedAt   time.Time
}

type DeviceEntry struct {
    Identity Identity                // Manufacturer, DeviceID, SerialNumber
    Faces    []BusFace               // role-aware bus participation records
    // ... existing fields preserved
}

type BusFace struct {
    Addr             byte
    Role             SlotRole
    DiscoverySource  DiscoverySource
    VerificationState VerificationState
    AccessProtocols  []string         // e.g. ["B509", "B524", "B504"]
}
```

`AddressSlot` carries slot-level state (role/source/confidence). `DeviceEntry` carries identity + role-aware faces. Slot aliasing is the unique mechanism by which multiple addresses converge to one device.

## AD03 — Companion derivation

Pure function in `helianthus-ebusgo/protocol`:

```
func Companion(addr byte) (byte, bool) {
    if isInitiatorCapable(addr) {           // master?
        return addr + 0x05, true            // slave companion
    }
    candidate := byte((int(addr) - 5) & 0xFF) // slave→master arithmetic
    if isInitiatorCapable(candidate) {
        return candidate, true
    }
    return 0, false                         // no companion
}
```

`isInitiatorCapable(addr)` is the existing `helianthus-ebusgo/protocol.IsInitiatorCapableAddress` (each nibble must be in `{0x0, 0x1, 0x3, 0x7, 0xF}`).

Pinned test cases (operator-confirmed):
- `Companion(0x04) = (0xFF, true)` — NETX3 secondary slave → master 0xFF
- `Companion(0xF1) = (0xF6, true)` — NETX3 master → primary slave
- `Companion(0x08) = (0x03, true)` — boiler slave → master 0x03 (init-cap: high=0, low=3)
- `Companion(0x10) = (0x15, true)` — master → slave
- `Companion(0x26) = (0, false)` — no master pair (0x21 fails bit-pattern: low=1 ok but high=2 not init-cap)
- `Companion(0xEC) = (0, false)` — no master pair (0xE7 fails: high=E not init-cap)

## AD04 — 0xFF dual-meaning resolution (consultant C1)

0xFF is BOTH the NACK byte AND a valid lowest-priority master address (per eBUS bit-pattern rule: high=F, low=F, both init-cap).

Rule: insert at slot[0xFF] only when 0xFF appears at frame-start as `src` or `dst`, NEVER in ACK position. The pre-existing `bus_observability_store` reconstructor distinguishes positions by frame structure (request header → ACK → response header → ACK). The address-table inserter MUST consume only the request-header-position frame fields, never raw byte stream.

## AD05 — Insertion soundness gate (consultant C2)

Slot insertion fires on:
1. Positive ACK byte (`0x00`) following a complete request frame.
2. Coherent identity reply (B509 ScanID 0x29 or B524 capability echo).

Slot insertion does NOT fire on:
- NACK byte (`0xFF` in ACK position).
- Self-source (gateway's admitted source).
- Broadcast destination class (`0xFE`, `0xFF` if disambiguated as NACK per AD04).

Companion-slot insertion (slot[companion(ZZ)]) requires SECOND corroborating observation:
- Two ACKs ≥ N seconds apart (N to be tuned in M4; default 5s), OR
- One ACK + one identity reply.

This prevents false-positive companion entries from a single noisy NACK on the bus.

## AD06 — SN merge gate (consultant C3, Phase B M6)

Pointer-merge (slot[a].Device = slot[b].Device for distinct slots that have separate DeviceEntry pointers today) fires only when:
1. `(Manufacturer, DeviceID, SerialNumber)` triple matches.
2. `SerialNumber ∉ {0x00000000, 0xFFFFFFFF, 0x7FFFFFFF}` (sentinel denylist; configurable).

Gate-fail → log warning `merge_gate_rejected addr=0x{a} addr=0x{b} reason={sentinel|missing_id}` and DO NOT merge. Entries remain separate.

Phase A ships the merge gate AS A NO-OP infrastructure (helper exists, not called). Phase B M6 wires the call site.

## AD07 — Static seed semantics

Static seed entries (M5) create `AddressSlot{ source: static_seed, confidence: candidate }` AND a corresponding `DeviceEntry` with empty `Identity` (placeholder for future enrichment). NO identity merge happens at seed-load time. Slots are visible in GraphQL devices with `discovery_source=static_seed verification_state=candidate`.

Phase B M6 may later promote the seeded entry to `verification_state=identity_confirmed` if a B509 ScanID reply matches the seeded address and SN passes AD06 gate.

## AD08 — Static seed default

`EnableStaticSeedTable` feature flag, default **false** in M5 release. Operator must opt in via addon config to receive the seed entries. Rationale: seed entries derive from operator's observed hardware (NETX3, BASV2/SOL00); other Vaillant deployments may have different topology. Promoting to default-true requires `helianthus-docs-ebus` to establish the entries as model-level Vaillant facts (i.e. unconditional for all deployments running the listed firmware versions).

## AD09 — TDD strict mode

Every implementation milestone (M1, M3, M4, M5) is preceded by a per-repo RED test commit (cruise-dev-supervise enforced via TDD_STRICT). Test commits land on the same branch as the impl commit; cruise-pr-review-loop verifies RED→GREEN ordering before approving merge.

## AD10 — Phase A vs Phase B split

Phase A delivers: passive detection of 0xF6 via companion derivation, static visibility of 0x04 + 0xEC via seed table. Phase B delivers: SN-driven enrichment merge, EvidenceBuffer migration. Operator's 2h target applies to Phase A only.

## AD11 — Predecessor preservation

PR #560 + PR #562 logic UNTOUCHED in Phase A. Address-table emits domain events (e.g. `AddressTableSlotInserted`); EvidenceBuffer can OPTIONALLY consume them as additional `EvidencePresenceOnly` records. No deprecation, no rewiring. Phase B M7 owns the migration.

## AD12 — Transport-gate (REQUIRED)

M3, M4 alter link-layer interpretation. M0A captures pre-change baseline. M9 verifies post-change parity. T01..T88 matrix re-run with no unexpected fail/xpass deltas.

## AD13 — Doc-gate (REQUIRED)

Canonical updates in `helianthus-docs-ebus`:
- `address-table-model.md` — AddressSlot / DeviceEntry / BusFace separation, slot lifecycle.
- `companion-derivation.md` — bit-pattern rule, exception list, pinned test cases.
- `ack-nack-insertion-rules.md` — AD04 + AD05 in normative form.
- `sn-merge-gate.md` — AD06 forward-reference for Phase B.
- `static-seed-provenance.md` — seed table source, opt-in semantics, AD08.
- `passive-detection-limits.md` — 0x04/0xEC undetectable in pure-passive; 0xF6 via 0xF1 observation.
- `live-validation-acceptance.md` — positive + negative assertions.

M0_DOC_SPEC writes the spec; M0C_DOC_EVIDENCE_UPDATE appends post-merge evidence.

## AD14 — GraphQL/HA consumer compatibility

`devices` GraphQL field exposes `discoverySource` and `verificationState` per device. HA integration (`helianthus-ha-integration` repo) MUST be verified to either filter `verification_state=candidate` rows from primary entity creation OR handle the metadata correctly without creating spurious entities. M8 acceptance covers this.

## AD15 — Cross-repo TDD sequencing

M0B_TDD_GATE staged per-repo to avoid `one_pr_per_repo_at_a_time` deadlock:
1. ebusreg RED tests for AddressSlot accessors (no upstream deps) →
2. ebusgo RED tests for `Companion()` (no upstream deps) →
3. productids RED tests for seed API (depends on ebusreg AddressSlot via go.work workspace pin) →
4. gateway RED tests for first-observation/correlator (depends on ebusreg + ebusgo + productids).

Each repo PR carries its own RED commit observable by cruise-dev-supervise.
