# Acceptance Criteria and Falsifiability — Phase A

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

Depends on: `11-milestones-phase-a.md` (M3, M4, M5, M8), `00-canonical.md` decision matrix AD04..AD08, AD14, predecessor PRs `helianthus-ebusgateway#560` + `#562` merged baseline.

Scope: define the live-validation falsifiability surface for Phase A. Each assertion is binary (pass/fail); M8_LIVE_VALIDATION enforces the full set. HA consumer compatibility (AD14) is checked separately and recorded in the M8 PR body.

Idempotence contract: each assertion is repeatable on the live HA (192.168.100.4) — re-running M8 produces the same pass/fail outcome until the bus topology changes. Assertions are rate-limited to avoid overloading the bus.

Falsifiability gate: this chunk IS the falsifiability gate for Phase A. M8 PR cannot be merged unless every positive assertion passes AND every negative assertion holds (i.e. the negative condition is observed to NOT happen).

Coverage: this chunk covers the live HA validation surface. Per-milestone unit-level acceptance is specified in `11-milestones-phase-a.md` per milestone. Phase B acceptance is in `12-milestones-phase-b.md`.

## Positive assertions (P1..P6)

### P1 — 0xF6 visible via passive observation alone

Procedure:
- Set `EnableStaticSeedTable=false` in addon config
- Deploy gateway; let it run ≥10 minutes during normal NETX3 polling activity
- Query GraphQL `{ devices { address discoverySource verificationState } }`

Expected: device with `address=0xF6 (246) discoverySource=passive_observed verificationState=corroborated`.

Provenance: NETX3's master 0xF1 emits frames during normal operation; Phase A's M3+M4 derives companion (0xF1 → 0xF6) and inserts slot[0xF6] after second corroborating observation.

### P2 — 0x04 visible via static seed (with flag enabled)

Procedure:
- Set `EnableStaticSeedTable=true` in addon config
- Restart addon; let it run ≥30 seconds
- Query GraphQL `{ devices { address discoverySource verificationState } }`

Expected: device with `address=0x04 (4) discoverySource=static_seed verificationState=candidate`.

### P3 — 0xEC visible via static seed (with flag enabled)

Same procedure as P2. Expected: device with `address=0xEC (236) discoverySource=static_seed verificationState=candidate`.

### P4 — Existing devices unchanged

Procedure: same as P1.
Expected: 0x08 (BAI00), 0x15 (BASV2), 0x26 (VR_71) appear with `verificationState=identity_confirmed` (preserved from PR #560/#562 logic) — no regression.

### P5 — bus_admission preserved

Procedure: query `{ busSummary { status { bus_admission { source_selection { state outcome selected_source companion_target active_probe { status } } } } } }`.
Expected: `state=active outcome=active_probe_passed selected_source=127 (0x7F) companion_target=132 (0x84) active_probe.status=active_probe_passed`. Identical to pre-Phase-A.

### P6 — Transport matrix parity

Procedure: re-run T01..T88 transport matrix (M9). Diff against M0A baseline.
Expected: zero unexpected `fail` deltas; zero unexpected `xpass` deltas. Any infra-blocked cases must use the documented `adapter_no_signal` reason.

## Negative assertions (N1..N5)

### N1 — NACK-only observations do NOT insert

Procedure: send a synthetic frame ZZ=0x99 (a known-non-existent address) from the gateway's admitted source, expect NACK (0xFF in ACK position) from the bus. Query GraphQL.
Expected: NO entry at address 0x99 in `devices`.

### N2 — Broadcast 0xFE does NOT insert at 0xFE slot

Procedure: observe natural broadcast traffic (e.g. B510 `07 FF` sign-of-life). Query GraphQL.
Expected: NO entry at address 0xFE OR 0xFF (when 0xFF appears as broadcast destination class).

### N3 — ACK byte 0xFF does NOT insert at 0xFF slot via ACK position

Procedure: observe traffic that produces NACK (0xFF) in ACK position. Query GraphQL.
Expected: NO entry at address 0xFF UNLESS a separate frame-start observation of 0xFF as src/dst exists. Test this with a negative golden trace AND positive golden trace separately.

### N4 — Self-source does NOT insert

Procedure: gateway sends frames from admitted source 0x7F. Query GraphQL.
Expected: NO entry at address 0x7F. (0x7F is initiator-capable; if accidentally inserted, it would surface.)

### N5 — Single corroboration does NOT companion-insert

Procedure: send a single frame triggering 0xF1 master observation (one ACK from a 0xF1-sourced request). Query GraphQL within 1 second.
Expected: NO entry at address 0xF6 (companion of 0xF1) — corroboration window not yet closed.

After observation window (default 5s) + second corroborating observation: 0xF6 entry MUST appear (P1 fires). N5 is the "before-second" check.

## HA consumer compatibility (AD14)

Procedure:
- Deploy gateway with seed table enabled
- Restart HA core
- Inspect HA's helianthus integration entity list

Expected:
- Existing entities (boiler, regulator, system) remain stable, no regression
- For 0x04 / 0xEC / 0xF6 candidate-state entities: EITHER the integration filters `verification_state=candidate` from primary entity creation (acceptable if intentional) OR creates entities tagged in attribute as static-seed-derived, OR creates entities and the operator explicitly accepts them as candidates.

The integration MUST NOT crash, MUST NOT generate spurious entities for arbitrary addresses, and MUST NOT regress existing user-visible entity state.

## Rollback criteria

If ANY positive assertion fails OR ANY negative assertion is violated, the M8 PR MUST NOT merge. Rollback steps:
1. Revert M3, M4, M5 PRs (in reverse merge order)
2. Revert M5A_SEED_API_CONTRACT (productids)
3. Revert M2A correlator package
4. Revert M2 Companion func
5. Revert M1 registry refactor
6. M0 doc PRs may remain (no runtime impact)

Rollback decision is made by the operator after reviewing the failed assertion log + transport-matrix diff.
