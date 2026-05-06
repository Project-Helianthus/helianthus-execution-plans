# Issue Map — Address-Table Registry

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

Per-repo issue rollup. Each repo gets exactly one issue per milestone touch (per `one_issue_per_repo_at_a_time` invariant). cruise-preflight will create these on Phase A activation.

| Milestone | Repo | Issue title (proposed) | Topology node |
| --- | --- | --- | --- |
| M0_DOC_SPEC | helianthus-execution-plans | Plan ATR-w19-26: lock + meta-issue | ATR-00 |
| M0_DOC_SPEC | helianthus-docs-ebus | docs(ATR): address-table model + companion + ACK/NACK + seed canonicals | ATR-01 |
| M0A_TRANSPORT_BASELINE | helianthus-ebusgateway | infra(ATR): T01..T88 baseline matrix run pre-change | ATR-02 |
| M0B_TDD_GATE | helianthus-ebusreg | test(ATR): RED tests for AddressSlot accessor parity + aliasing | ATR-03 |
| M0B_TDD_GATE | helianthus-ebusgo | test(ATR): RED tests for `Companion()` operator-pinned cases | ATR-04 |
| M0B_TDD_GATE | helianthus-ebus-vaillant-productids | test(ATR): RED tests for static seed table + feature flag default | ATR-05 |
| M0B_TDD_GATE | helianthus-ebusgateway | test(ATR): RED tests for first-observation + corroboration + 0xFF disambiguation | ATR-06 |
| M1_REGISTRY_ARRAY_REFACTOR | helianthus-ebusreg | refactor(ATR): replace map[byte]*deviceEntry with [256]*AddressSlot behind typed accessor | ATR-07 |
| M2_COMPANION_PURE_FUNC | helianthus-ebusgo | feat(ATR): add `Companion(addr) (byte, bool)` pure protocol func | ATR-08 |
| M2A_OBSERVATION_CORRELATOR_SPEC | helianthus-ebusgateway | feat(ATR): observationcorrelator package + golden traces | ATR-09 |
| M3_FIRST_OBSERVATION | helianthus-ebusgateway | feat(ATR): first-observation insertion (positive ACK only, position-aware 0xFF) | ATR-10 |
| M4_COMPANION_INSERT_WITH_CORROBORATION | helianthus-ebusgateway | feat(ATR): companion-pair insertion gate with corroboration window | ATR-11 |
| M5A_SEED_API_CONTRACT | helianthus-ebus-vaillant-productids | feat(ATR): static seed API contract + feature flag | ATR-12 |
| M5_STATIC_SEED_TABLE | helianthus-ebus-vaillant-productids + helianthus-ebusreg | feat(ATR): NETX3 + BASV2 seed entries + registry init wiring | ATR-13 |
| M8_LIVE_VALIDATION | helianthus-ebusgateway | test(ATR): live HA falsifiability gate (P1..P6 + N1..N5 + AD14) | ATR-14 |
| M9_TRANSPORT_VERIFY | helianthus-ebusgateway | infra(ATR): T01..T88 post-change matrix verify diff | ATR-15 |
| M0C_DOC_EVIDENCE_UPDATE | helianthus-docs-ebus | docs(ATR): post-merge evidence rollup | ATR-16 |

Phase B (deferred):
| M6_ENRICHMENT_MERGE | helianthus-ebusgateway + helianthus-ebusreg | feat(ATR): SN-driven enrichment merge with denylist gate |
| M7_EVIDENCEBUFFER_MIGRATION | helianthus-ebusgateway | refactor(ATR): wire address-table events to replace direct EvidenceBuffer wiring |

PR strategy:
- Each milestone delivers exactly one PR per repo it touches.
- Squash + merge only.
- Doc-gate: M0 + M0C are authored as paired PRs in `helianthus-docs-ebus`; cruise-doc-gate companion-link skill verifies.
- Transport-gate: M0A + M9 are evidence artifacts captured in PR body of their containing milestones.
