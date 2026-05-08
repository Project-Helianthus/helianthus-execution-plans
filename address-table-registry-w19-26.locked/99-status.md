# Status — Address-Table Registry

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

State: `implementing` (Phase A complete + Phase A.5 runtime wire-up merged; Phase B deferred per AD14)

## Phase A milestones

| Milestone | State | PR | Notes |
| --- | --- | --- | --- |
| M0_DOC_SPEC | merged | docs-ebus#295 | normative ATR specs (01..07 + README) |
| M0A_TRANSPORT_BASELINE | merged | gateway#563 | 88-case dry-run baseline captured |
| M0B_TDD_GATE/ebusreg | merged | ebusreg#131 | RED→GREEN bundled with M1+M5A+M5 |
| M0B_TDD_GATE/ebusgo | merged | ebusgo#148 | RED→GREEN bundled with M2 + ACKCorrelation |
| M0B_TDD_GATE/productids | merged | ebusreg#131 | productids package lives in ebusreg |
| M0B_TDD_GATE/gateway | merged | gateway#564 | RED→GREEN bundled with M2A+M3+M4 |
| M1_REGISTRY_ARRAY_REFACTOR | merged | ebusreg#131 | AddressSlot/SlotRole/DiscoverySource/VerificationState + LookupSlot + AliasAddresses |
| M2_COMPANION_PURE_FUNC | merged | ebusgo#148 | protocol.Companion(byte) (byte, bool) |
| M2A_OBSERVATION_CORRELATOR_SPEC | merged | ebusgo#148 + gateway#564 | ACKCorrelation type + reconstructor population |
| M3_FIRST_OBSERVATION | merged | gateway#564 | AddressTable + AddressTableInserter |
| M4_COMPANION_INSERT_WITH_CORROBORATION | merged | gateway#564 | second-corroboration companion-insert |
| M5A_SEED_API_CONTRACT | merged | ebusreg#131 | LoadSeedTable + StaticSeedEntry |
| M5_STATIC_SEED_TABLE | merged | ebusreg#131 | NETX3 + BASV2 entries |
| M3.5_RUNTIME_WIREUP (Phase A.5) | merged | gateway#565 | inserter instantiated + admission-gated subscription wired into cmd/gateway/main.go |
| M3.6_SRC_INSERTION (Phase A.6) | merged | gateway#566 | spec-compliance fix per AD05 Address Eligibility — request src now inserted as initiator (PR #564 missed this; live evidence: 0xF1→0x15 frame seen but 0xF1 absent from registry) |
| M8_LIVE_VALIDATION | mechanism-green; tap-SYN-drop is upstream-blocker | post-final-deploy (md5 993387ab) | A.7-A.9+M6+M6.1+wires deployed. Registry shows CORRECT canonical aliasing live: BAI 0x03↔0x08 + BASV2 0x10↔0x15 collapsed into 1 DeviceEntry each (via entry.Addresses() multi-address). 0x38 false-positive ELIMINATED. 0x64 + 0xA0 emerge as new fp's. NETX3 (0xF1/0xF6/0x04/0xFF) still absent because A.8 forensic logs revealed root cause: passive tap loses SYN delimiter bytes between frames → reconstructor consumes mid-frame bytes as new frame start → impossible src classifications (e.g. 0x26 as initiator) → corrupted_request before M2A correlator runs. Affects ALL src=0xF1 frames + creates new false-positives. Real fix is upstream in adaptermux/tap. P2/P3 N/A by default flag |
| A.7a_CANONICAL_API | merged | ebusgo#149 c2b8efb | CompanionOfSource/SourceOfCompanion/IsCanonicalSource/IsCanonicalCompanion/SourceTier/IsFreeUseSource derived from sourceAddressTableV1 |
| A.7b_PAIR_ALIASING | merged | gateway#567 2586f23 | maybeAliasCanonicalCompanion + MCP/GraphQL parity for Addresses field |
| A.7c_AUDIT_LOG | merged | gateway#568 c468c14 | INFO log on insert + alias for runtime audit trail |
| A.7d_TIER_LABELS | merged | gateway#569 438a270 | PriorityTier + FreeUse propagation to AddressSlot |
| A.7e_CANONICAL_SNAPSHOT | merged | gateway#570 7115281 | CanonicalAddressTableSnapshot with observation state |
| A.8_FORENSIC_LOGGING | merged | gateway#571 d1474dc | passive_reconstructor abandon log with raw bytes — REVEALED tap SYN drop root cause |
| A.9_ABANDON_COUNTERS | merged | gateway#572 f3549a8 | ebus_passive_reconstructor_abandons_total per-reason Prometheus counter |
| M6.1_MARKSLOT_API | merged | ebusreg#132 b3f2f1a | thread-safe MarkSlotPassiveObserved API |
| M6_IDENTITY_MERGE | merged | ebusreg#133 856f3a1 | identity-merge contract tests for passive→enrichment timeline |
| MARKSLOT_USE_SITE | merged | gateway#573 a62aec2 | inserter switched from direct slot mutation to MarkSlotPassiveObserved |
| ENRICHMENT_TRIGGER | merged | gateway#574 9e38183 | post-passive-insertion semanticPoller.EnqueueDiscoveryRefresh wires M6 trigger |
| TAP_SYN_FIX | not-started | adaptermux | UPSTREAM blocker — tap loses SYN bytes between frames; reconstructor sees mid-frame as frame-start → false src classifications (0x26 initiator, etc) and corrupted_request blocking ALL 0xF1 detection. Out of scope for this locked plan; tracked for next adaptermux work |
| M9_TRANSPORT_VERIFY | merged | post-merge dry-run | 88-case dry-run on main matches M0A baseline (0 diffs) |
| M0C_DOC_EVIDENCE_UPDATE | open | docs-ebus#296 | Phase A.5 evidence + follow-ups appended to 07-live-validation-acceptance.md |

## Phase C milestones (frame-type-aware transport, AD24..AD30)

| Milestone | State | PR | Notes |
| --- | --- | --- | --- |
| M-C0 | merged | docs-ebus#297 | 256-byte Address Taxonomy + frame-type contract + validator contract enriched into `12-address-table.md` (renamed from 12-source-address-table.md); taxonomy-section block hash `316baf20ab0d0a64b36613bb8c7604d7570fecc01071daca94931029ae82ebec` pinned via `scripts/check_address_table_taxonomy_hash.sh` |
| M-C0A | merged | gateway#575 | 88-case `transport-matrix-baseline-phase-c.json` captured (artifact_schema=2; full topology fields per case); commit 4e373e8 |
| M-C1 | merged | ebusgo#150 | `protocol.AddressClass` enum (Reserved=0, Master, Slave, Broadcast) + 256-byte `AddressClassOf` table; commit bbf557d |
| M-C2 | merged | ebusgo#151 | `Frame.FrameType` field (additive, zero=derive) + `Frame.EffectiveFrameType` + `Frame.Validate` |
| M-C3 | merged | docs-ebus#297 | bundled with M-C0 enrichment (FrameType ENUM unification across emitter + parser) |
| M-C4 | merged | ebusgo#151 | `ValidateFrameAddressing(ft, src, dst)` 6-clause contract + `ErrInvalidFrameAddress` sentinel |
| M-C5 | merged | ebusgo#152 | `Bus.Send.Validate` enforcement at top of Send + `InvalidFrameAddressTotal()` atomic counter |
| M-C6a | merged | ebusreg#134 | `DeviceEntry.AddressByRole(SlotRole)` + `PrimaryDisplayAddress` (additive); SlotRoleUnknown fallback via `protocol.AddressClassOf` (Codex P2 fix) so active-scanned entries get a useful answer |
| M-C6b | merged | gateway#576 (squash 2f37e402) | gateway migration of all 33+ `entry.Address()` callers to `PrimaryDisplayAddress()` for display + new `TargetAddressForRouting`/`EntryContainsAddress` helpers for routing/containment; 11 alias-aware Codex P2/P3 threads addressed across 6 commits (b57e3a8 → 2e1f50a) |
| M-C6c | merged | ebusreg#135 (squash 77b56516) | `DeviceEntry.Address()` REMOVED (BREAKING) — build-break safety net dry-run from gateway/main (post-#576) confirmed zero missed callers (per AD30: removal NOW, no deprecation window) |
| M-C6d | merged | gateway#578 (squash e9fc5f73) | post-M-C6c `go.mod` bump activating the build-break safety net on `main`; GH Actions 4/4 green + local CI exit 0 prove M-C6b's caller migration was exhaustive |
| M-C7 | merged | gateway#577 (squash c2f4bbf5) | explicit `Frame.FrameType` at every active send site (19 sites total): 14 strict `FrameTypeInitiatorTarget` (smoke.go ×2, cmd/gateway/semantic_vaillant.go ×8, cmd/gateway/vaillant_b503_dispatcher.go ×1, smoke 0x07/0x04 ×1, unknown_device_dump strict ×0 left, portal/explorer strict ×0 left, plus 2 cleanups) + 8 probe sites with `FrameTypeForTarget` (3 in unknown_device_dump.go + 5 in portal/explorer.go); 2 Codex P2 review iterations (845fc67 + a7ca594) refined probe-vs-known-slave classification |
| M-C8 | pending | (live HA validation) | post-deploy validation: aliased BAI 0x03↔0x08 routes M2S to 0x08; misrouted M2S sends fail Validate with `ErrInvalidFrameAddress` and increment `InvalidFrameAddressTotal`; runbook `/tmp/m_c8_live_validation.sh` |
| M-C9 | merged | post-#576 dry-run (in-tree m9-gen) | 88-case post-Phase-C topology byte-identical to M-C0A baseline; SHA256 `46431e22d8ed3909db19a34196df72575df8afb7ae03658be32cde0f2734a143` matches both `baseline_topology.json` and `post_phase_c_topology.json`; verified post-#576-main and M-C7 branch — internal/matrix/ untouched by Phase C, zero-diff structurally guaranteed |
| M-C10 | this-PR | plans (this commit) | Phase C evidence rollup |

## Phase B milestones (deferred)

| Milestone | State | PR | Notes |
| --- | --- | --- | --- |
| M6_ENRICHMENT_MERGE | deferred | — | gated on Phase A complete + operator approval |
| M7_EVIDENCEBUFFER_MIGRATION | deferred | — | gated on M6 + operator approval |

## Phase A.5 follow-up debt

| Item | Severity | Notes |
| --- | --- | --- |
| `*AddressSlot` mutation race | P2 | inserter mutates DiscoverySource/VerificationState/Role/timestamps via LookupSlot pointer without registry lock; sidestepped by tests via DeviceEntry interface; benign for current MCP/GraphQL surface. Fix: add `(*DeviceRegistry).MarkSlotPassiveObserved` API in ebusreg. |
| Async-path test coverage debt | P3 | gateway runtime test exercises only synchronous static-fallback admission wire-in. activeProbePassed wire-in (source-selection-capable + observe-first) unit-uncovered. |

## Cruise-state mirror

cruise-state-sync v1 comment will be pinned on the meta-issue. Active skill on Phase A.5 close = cruise-merge-gate (state=POST_MERGE_VERIFY).

## Plan history

- 2026-05-06 — drafted, 3 adversarial rounds with Codex gpt-5.5 high (thread `019dfd04-18e8-78f1-8651-760fea1b3092`), `ready_to_lock=true` on round 3.
- 2026-05-06 — locked + Phase A milestones M0..M5 merged across 5 PRs (docs#295, gateway#563/#564, ebusgo#148, ebusreg#131).
- 2026-05-06 — Phase A.5 added: live deployment surfaced runtime wire-up gap (inserter type-defined but not instantiated). PR #565 merged with admission-gated subscription via 3 wire-in points; Codex review loop completed (gpt-5.5 + GitHub Codex bot, 4 P2 findings addressed).
- 2026-05-06 — M9 dry-run vs M0A baseline: 0 diffs. M0C docs evidence rollup PR #296 opened.
- 2026-05-06 — Phase A.6 added: post-A.5 live observation surfaced AD05 spec-compliance regression in PR #564 — inserter inserted dst + companion(src after 2x) but never request src itself. PR #566 merged adding maybeInsert(srcAddr, "initiator", ...) call; Codex review APPROVE.
- 2026-05-06 — Post-A.6 live observation (50+ min uptime): registry grew 3→5 devices. 0x10 (BASV2 master companion) and 0x38 inserted as passive_observed initiators, confirming wire-up + AD05 src-insertion both work end-to-end in runtime. NETX3 (0xF1) specifically not emitted in observation window — needs operator KNX trigger or longer wait for periodic enrichment cycle.
- 2026-05-07 — Phase C amendment locked (commit c994c9a, plans#24): defense-in-depth FrameType-aware transport (AD24..AD30) covering aliased-pair routing-vs-display split + transport-level frame-type enforcement.
- 2026-05-07 — Phase C M-C0..M-C5 merged: docs-ebus#297 (taxonomy + contracts), gateway#575 (M-C0A baseline), ebusgo#150 (AddressClass), ebusgo#151 (Frame.FrameType + Validate), ebusgo#152 (Bus.Send enforcement).
- 2026-05-07 — Phase C M-C6a merged (ebusreg#134): AddressByRole + PrimaryDisplayAddress additive surface, with AddressClass fallback for active-scanned entries.
- 2026-05-07 — Phase C M-C6b merged (gateway#576 squash 2f37e402): 33+ caller migration + 11 alias-aware Codex P2/P3 fixes across 6 commits + 2 new helpers (`TargetAddressForRouting`/`EntryContainsAddress`); GH Actions 4/4 green; local CI exit 0 with documented owner overrides.
- 2026-05-07 — Phase C M-C9 verified PRE-merge of M-C7: 88-case topology byte-identical to M-C0A baseline (SHA256 46431e22…); zero-diff structurally guaranteed since internal/matrix/ was not touched by Phase C.
- 2026-05-07 — Phase C M-C6c merged (ebusreg#135 squash 77b56516): DeviceEntry.Address() removed (BREAKING).
- 2026-05-07 — Phase C M-C7 merged (gateway#577 squash c2f4bbf5): per-API-site Frame.FrameType enrichment across 19 sites (14 strict M2S + 8 probe-derived). 2 Codex P2 review iterations addressed before merge.
- 2026-05-07 — Phase C M-C6d merged (gateway#578 squash e9fc5f73): go.mod bump to post-M-C6c ebusreg activates build-break safety net on main. CI 4/4 green proves M-C6b caller migration was exhaustive.
- 2026-05-07 — Phase C M-C9 re-verified post-M-C7 + post-M-C6d: same SHA256 46431e22… across baseline, post-Phase-C, and post-M-C7 topology snapshots. Zero-diff structurally maintained end-to-end.
- 2026-05-08 — Phase C M-C8 + M-C10 merged: gateway#576/#577/#578 deployed live to HA at 192.168.100.4 (binary SHA256 11491e49…); 10-min observation window confirmed pre-Phase-C bug (M2S to master byte) fixed — all gateway sends route to slave bytes 0x08/0x15/0x26, zero misroutes, zero ErrInvalidFrameAddress. M-C10 docs rollup landed in docs-ebus#299 (squash 741ddba8), plan-status PR #25 (squash 49b78cdd).
- 2026-05-08 — Post-Phase-C live observation surfaced 5 follow-up issues unrelated to FrameType but requiring a separate cruise (P0..P5):
  - **REGRESSION-IDENTITY**: BASV2 0x10↔0x15 + NETX3 0xF6↔0xF1 aliased correctly but with empty manufacturer / deviceID / serialNumber. Root cause: pre-existing AliasAddresses defect (ebusreg commit fcc4f61) destroys identity-bearing secondary at alias merge. **Phase C deploy surfaced it because gateway restarted with empty state** — pre-deploy 24h+ uptime had identity from active scan time before fcc4f61 landed.
  - **PHANTOM-INSERTIONS**: 0x24 + 0x84 entries appear despite not existing on bus. Root cause: gateway A.6 (PR #566) feeds AbandonedTransaction events into address_table_inserter; abandoned phase-3 no_response abandons retain populated ACKCorrelation, inserter accepts them as if successful M2A.
  - **MISSING-MASTER-ALIAS**: BAI 0x03 missing from registry. Root cause: A.6 narrowed startup scan to slave-only targets {0x08, 0x15, 0x26}; pre-A.6 the response.Source!=target alias path implicitly grouped 0x03↔0x08 with identity at scan time. Post-A.6 only 0x08 enters from active scan.
  - **MISSING-BROADCAST-FACES**: 0x04 + 0xFF (NETX3 broadcast pair) absent from registry. Root cause: 3 compounding gates — (a) productids.LoadSeedTable is dead code (zero non-test callers), (b) inserter's M2A path doesn't fire on broadcast frames (no ACKCorrelation by construction), (c) TAP_SYN_FIX upstream blocker corrupts most NETX3 broadcast traffic.
  - **NO-IDENTITY-MERGE**: Cross-class merge (master↔slave or broadcast↔canonical) doesn't happen for NETX3 because identity-merge requires SerialNumber, populated only by active scan + B5.09 ScanID. Passive-only entries never get a probe.
- 2026-05-08 — 6-item post-Phase-C cruise opened (operator-approved 2026-05-08):
  - **P0** (ebusreg#136): preserve secondary identity in AliasAddresses via absorbIdentityLocked. 3 unit tests cover BASV2/NETX3/symmetric scenarios.
  - **P1+P1.5** (gateway#579): inserter kind-filter rejects AbandonedTransaction events; reconstructor strips stale ACKCorrelation for NoResponse/AmbiguousRetransmit/CRCMismatch abandons.
  - **P2** (gateway#580): canonical-pair alias on directed-scan completion; restores BAI 0x03↔0x08 grouping via reg.AliasAddresses(companion, addr) post-scan.
  - **P3** (gateway#581 + ha-addon#124): wire productids.LoadSeedTable into gateway startup; addon `enable_static_seed_table` config flag (default false). Plants NETX3 0xF1+0xF6+0x04 + BASV2 0x15+0xEC at boot.
  - **P4** (gateway#582): broadcast insertion path; OnPassiveClassifiedEvent dispatches BroadcastFrame events to handleBroadcastFrameEvent which inserts the broadcaster's source byte (NETX3 0xFF). Stacked on P1.
  - **P5** (gateway#583): per-address identity probe after passive insert via new EnqueueAddressIdentityProbe(addr) on the semantic poller; bounded one-shot via sync.Map. Closes the identity-population loop.
  - **P6** (TAP_SYN_FIX): tracked separately as adaptermux/proxy work item. Not in this cruise.
