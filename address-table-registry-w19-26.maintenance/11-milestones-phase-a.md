# Phase A Milestones — Address-Table Registry

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

Depends on: `00-canonical.md` decision matrix AD01..AD15, `10-architecture-and-decisions.md`, predecessor PRs `helianthus-ebusgateway#560` + `#562` merged.

Scope: detailed per-milestone specifications for Phase A (M0..M9) targeting passive detection of 0xF6 via companion derivation and static visibility of 0x04 + 0xEC via seed table, with all consultant-mandated corrections (C1, C2, C3) and Codex-flagged constraints (TDD strict, transport-gate, per-repo sequencing) integrated.

Idempotence contract: each milestone description is the authoritative implementation contract. Re-issuing a dev-supervise prompt for the same milestone MUST yield identical scope. Implementation amendments require new plan amendment with canonical-hash bump. Milestones are merged via squash; each milestone delivers exactly one PR per repo it touches.

Falsifiability gate: each milestone has explicit acceptance criteria and unit-test surface listed below. M8_LIVE_VALIDATION is the integration falsifier covering all positive AND negative assertions enumerated in `13-acceptance-criteria-and-falsifiability.md`.

Coverage: this chunk covers Phase A milestones only. Phase B (deferred) lives in `12-milestones-phase-b.md`. Live validation acceptance lives in `13-acceptance-criteria-and-falsifiability.md`.

## M0_DOC_SPEC — Doc-gate canonical specification

- Repo: `helianthus-docs-ebus`
- Complexity: 5
- Routing: Codex (Sonnet/easy dev)
- Transport-gate: not-required
- Doc-gate: REQUIRED (this IS the doc-gate milestone)
- Output: 7 normative docs per AD13 list
- Acceptance: each doc references AD-id from `00-canonical.md`; doc-gate companion check passes (cruise-doc-gate skill)

## M0A_TRANSPORT_BASELINE — Transport matrix pre-change baseline

- Repo: `helianthus-ebusgateway`
- Complexity: 3
- Routing: Codex
- Output: T01..T88 transport matrix run captured as `transport-matrix-baseline-w19-26.json` artifact in PR
- Acceptance: matrix output checksum recorded; ready for M9 diff comparison

## M0B_TDD_GATE — Per-repo RED test commits

- Repos: `helianthus-ebusreg`, `helianthus-ebusgo`, `helianthus-ebus-vaillant-productids`, `helianthus-ebusgateway` (4 separate PRs, staged per AD15)
- Complexity: 3 per repo
- Routing: Codex per-repo
- Per-repo RED scope:
  - **ebusreg**: `TestAddressSlotLookupParity` (asserts `[256]*AddressSlot` accessor returns same entries as legacy map for all known addresses); `TestAddressSlotAliasing` (multiple slots → same DeviceEntry pointer)
  - **ebusgo**: `TestCompanion_OperatorPinnedCases` (operator's confirmed list); `TestCompanion_NoMasterPair` (0x26, 0xEC return false); `TestCompanion_MasterToSlave_OffsetFive`
  - **productids**: `TestStaticSeedTable_NETX3_OwnsThreeAddresses`; `TestStaticSeedTable_BASV2_OwnsTwoAddresses`; `TestStaticSeedTable_FeatureFlagDefaultFalse`
  - **gateway**: `TestFirstObservation_PositiveACKOnly`; `TestFirstObservation_NoNACKInsertion`; `TestFirstObservation_SelfSourceExcluded`; `TestCompanionInsert_RequiresCorroboration`; `TestFFDisambiguation_FrameStartVsACKPosition`
- Acceptance: each test fails with the SAME error class expected post-impl (e.g. `accessor not implemented`, `function undefined`); cruise-dev-supervise observes RED commit hash before approving impl.

## M1_REGISTRY_ARRAY_REFACTOR — `[256]*AddressSlot` storage

- Repo: `helianthus-ebusreg`
- Complexity: 5
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: not-required (consumed M0)
- Scope:
  - Add `AddressSlot`, `DiscoverySource`, `VerificationState`, `BusFace` types per AD02
  - Replace `map[byte]*deviceEntry` with `[256]*AddressSlot` behind typed accessor `Lookup(addr byte) (*AddressSlot, bool)`
  - `Register(info DeviceInfo)` returns `*DeviceEntry` and creates AddressSlot{addr=info.Address, role=inferred, source=active_confirmed, verification_state=identity_confirmed, device→entry}
  - All callers migrated. Behavior preserved: legacy code paths see identical responses for existing addresses.
- Acceptance: M0B ebusreg RED tests turn GREEN; existing test suite passes; no behavior delta detected by `helianthus-ebusgateway` integration tests pinned at the new ebusreg branch.

## M2_COMPANION_PURE_FUNC — `Companion(addr) (byte, bool)`

- Repo: `helianthus-ebusgo` (`protocol` package)
- Complexity: 3
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: not-required
- Scope: pure func per AD03 algorithm. No package-private state, no dependencies.
- Acceptance: M0B ebusgo RED tests turn GREEN; `IsInitiatorCapableAddress` re-used (no duplication).

## M2A_OBSERVATION_CORRELATOR_SPEC — Internal correlator package

- Repo: `helianthus-ebusgateway`
- Complexity: 3
- Routing: Codex
- Transport-gate: not-required (spec only)
- Doc-gate: not-required (consumed M0)
- Scope: new package `internal/observationcorrelator/` with types + spec doc + golden trace fixtures. No runtime use yet (M3 wires it).
  - Correlator key: `(reconstructorEpoch, requestSequenceN, srcAddr, dstAddr, primarySecondary)`
  - Self-source exclusion: filter via `cfg.AdmittedSource()`
  - Broadcast exclusion: dst ∈ {0xFE} (and 0xFF via AD04 disambiguation)
  - Observation window: `LastObservedAt - FirstObservedAt > N seconds` for corroboration
  - Duplicate suppression: identical correlator key within 100ms collapses to single observation
  - Golden traces: `testdata/`
    - `ack_positive.bin`: ZZ=0x15 → ACK=0x00 (insert slot[0x15])
    - `ack_negative.bin`: ZZ=0x99 → NACK=0xFF (DO NOT insert)
    - `ff_frame_start.bin`: ZZ=0xFF appears as src (master 0xFF) (insert slot[0xFF])
    - `ff_ack_position.bin`: NACK byte 0xFF in ACK position (DO NOT insert at 0xFF)
    - `broadcast.bin`: dst=0xFE (insert slot[src] only, NOT slot[0xFE])
    - `self_source.bin`: src=admitted_source (DO NOT insert)
- Acceptance: spec doc reviewed; golden trace fixtures stored; type contracts compile; M3/M4 will reference these.

## M3_FIRST_OBSERVATION — Insert slot[ZZ] on positive ACK

- Repo: `helianthus-ebusgateway`
- Complexity: 5
- Routing: Codex
- Transport-gate: REQUIRED (M0A baseline + M9 verify)
- Doc-gate: not-required (consumed M0)
- Scope:
  - Wire correlator into `bus_observability_store.OnPassiveClassifiedEvent` and active-side `OnBusEvent`
  - On positive ACK from frame-start request: `registry.Lookup(ZZ); if nil → registry.Register(...)` with `source=passive_observed, verification_state=corroborated_pending`
  - 0xFF disambiguation per AD04: position-aware (frame-start src/dst → master 0xFF; ACK position → NACK, no insert)
  - Self-source filter: cfg.AdmittedSource()
  - NACK position filter
  - Broadcast 0xFE filter
- Acceptance: M0B gateway first-observation RED tests turn GREEN; M2A golden traces produce expected slot states.

## M4_COMPANION_INSERT_WITH_CORROBORATION — companion-pair insertion gate

- Repo: `helianthus-ebusgateway`
- Complexity: 6
- Routing: Claude (correctness-heavy gate logic)
- Transport-gate: REQUIRED
- Doc-gate: not-required
- Scope:
  - On second corroborating observation OR identity reply: lookup `Companion(addr)`; if companion exists AND slot[companion] is nil → insert with `source=passive_observed, verification_state=corroborated`
  - Default corroboration window: 5s (configurable)
  - Identity reply detection: B509 ScanID 0x29 OR coherent B524 reply
  - 0xFF master pair (companion(0x04) = 0xFF) — special-case logging since 0xFF master src is rare
- Acceptance: M0B gateway companion-corroboration RED tests turn GREEN; manual test: simulate `0xF1 → 0x15` traffic twice, observe slot[0xF6] populated; simulate single observation, observe slot[0xF6] STAYS empty.

## M5A_SEED_API_CONTRACT — Static seed API contract

- Repo: `helianthus-ebus-vaillant-productids`
- Complexity: 3
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: not-required (consumed M0)
- Scope: package-level types + interface, no runtime data yet:
  ```
  type StaticSeedEntry struct {
      Manufacturer string
      DeviceID     string
      Addresses    []SeedAddressEntry
      Source       string  // e.g. "vaillant_static_seed_w19_26"
  }
  type SeedAddressEntry struct {
      Addr  byte
      Role  string  // "master" | "slave"
      Confidence string  // "candidate"
  }
  func LoadSeedTable(enabled bool) []StaticSeedEntry
  ```
  - Feature flag `EnableStaticSeedTable` default false (AD08)
  - Failure mode: missing seed file → return empty slice + log degraded; do NOT panic; do NOT block registry init
- Acceptance: M0B productids RED tests turn GREEN; importable from registry without circular dep.

## M5_STATIC_SEED_TABLE — Static seed data + registry wiring

- Repos: `helianthus-ebus-vaillant-productids` (data) + `helianthus-ebusreg` (consumer)
- Complexity: 4
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: not-required (consumed M0)
- Scope:
  - productids: seed table data
    - `NETX3` entry: `Manufacturer=Vaillant, DeviceID=NETX3, Addresses=[{0xF1, master, candidate}, {0xF6, slave, candidate}, {0x04, slave, candidate}]`
    - `BASV2` entry: `Manufacturer=Vaillant, DeviceID=BASV2, Addresses=[{0x15, slave, candidate}, {0xEC, slave, candidate}]`
  - ebusreg: registry init reads seed table when flag enabled, populates AddressSlots with `source=static_seed, verification_state=candidate, device=newly-created DeviceEntry with empty Identity`
  - Slots are visible in GraphQL devices with explicit metadata
- Acceptance: with flag=true and live HA deploy, GraphQL devices includes 0x04 + 0xEC + 0xF6 + 0xF1 with `discoverySource=static_seed verificationState=candidate`; with flag=false (default), no seed entries surface.

## M8_LIVE_VALIDATION — Falsifiability gate, live HA deploy

- Repo: `helianthus-ebusgateway` (deploy + assertions)
- Complexity: 3
- Routing: Claude orchestrator (live validation, multi-criteria assertions)
- Transport-gate: REQUIRED
- Doc-gate: not-required
- Scope: cross-compile + deploy gateway to HA (192.168.100.4) per existing flow; run positive + negative assertion suite per `13-acceptance-criteria-and-falsifiability.md`
- Acceptance: ALL positive AND negative assertions pass; HA consumer compatibility verified per AD14 (HA integration shows 0xF6 entity, OR `verification_state=candidate` filtered, no spurious entities created).

## M9_TRANSPORT_VERIFY — Transport-gate post-change verify

- Repo: `helianthus-ebusgateway`
- Complexity: 2
- Routing: Codex
- Transport-gate: REQUIRED (this IS the post-change verify)
- Doc-gate: not-required
- Scope: re-run T01..T88 transport matrix; diff vs M0A baseline; require zero unexpected fail/xpass deltas; PR body carries the diff as evidence per cruise-merge-gate.

## M0C_DOC_EVIDENCE_UPDATE — Post-merge evidence rollup

- Repo: `helianthus-docs-ebus`
- Complexity: 2
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: REQUIRED (closes the loop opened in M0)
- Scope: append post-merge evidence section to M0 normative docs:
  - actual passively-observed addresses on operator's bus pre/post Phase A
  - actual GraphQL device count delta
  - actual transport-matrix baseline + verify diff
  - link to M8 PR + M9 PR + cruise-state meta-issue
- Acceptance: cruise-doc-gate skill verifies M0 + M0C alignment; companion docs PR satisfies code-PR doc requirement.
