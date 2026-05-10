# Milestone Map — Address-Table Registry

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

Lifecycle state: `draft` → `locked` after validator passes; transitions to `implementing` on first impl-milestone merge; back to `locked` (terminal) after final milestone merged.

## Phase A dependency DAG

```
                         ┌──────────────┐
                         │ M0_DOC_SPEC  │
                         └──────┬───────┘
                                │
                         ┌──────▼─────────────┐
                         │ M0A_TRANSPORT_BASELINE │
                         └──────┬─────────────┘
                                │
            ┌───────────────────┴─────────────────────┐
            │                                         │
   ┌────────▼─────────────┐                ┌──────────▼──────────┐
   │ M0B_TDD_GATE         │                │ (parallel:           │
   │  ebusreg ◄ ebusgo ◄  │                │  M5A_SEED_API_       │
   │  productids ◄ gateway │                │  CONTRACT)           │
   └────────┬─────────────┘                └──────────┬───────────┘
            │                                         │
   ┌────────▼─────────────┐                          │
   │ M1_REGISTRY_ARRAY_REFACTOR │                    │
   │ (ebusreg)            │                          │
   └────────┬─────────────┘                          │
            │                                         │
   ┌────────▼──────────────┐                         │
   │ M2_COMPANION_PURE_FUNC │                        │
   │ (ebusgo)               │                        │
   └────────┬───────────────┘                        │
            │                                         │
   ┌────────▼─────────────────────┐                  │
   │ M2A_OBSERVATION_CORRELATOR_SPEC │               │
   │ (gateway, spec only)             │              │
   └────────┬─────────────────────┘                  │
            │                                         │
   ┌────────▼────────────────┐                       │
   │ M3_FIRST_OBSERVATION    │                       │
   │ (gateway)               │                       │
   └────────┬────────────────┘                       │
            │                                         │
   ┌────────▼─────────────────────────────┐          │
   │ M4_COMPANION_INSERT_WITH_CORROBORATION │        │
   │ (gateway)                              │        │
   └────────┬───────────────────────────────┘        │
            │                                         │
            │                              ┌──────────▼─────────────┐
            │                              │ M5_STATIC_SEED_TABLE   │
            │                              │ (productids + ebusreg) │
            │                              └──────────┬─────────────┘
            │                                         │
            └─────────────────┬───────────────────────┘
                              │
                     ┌────────▼─────────────┐
                     │ M8_LIVE_VALIDATION   │
                     │ (gateway + HA deploy) │
                     └────────┬─────────────┘
                              │
                     ┌────────▼─────────────┐
                     │ M9_TRANSPORT_VERIFY  │
                     │ (gateway)            │
                     └────────┬─────────────┘
                              │
                     ┌────────▼─────────────┐
                     │ M0C_DOC_EVIDENCE_UPDATE │
                     │ (docs)               │
                     └──────────────────────┘
```

## Iteration vs Merge Dependencies

| Milestone | Repo | Complexity | Transport-gate | Doc-gate | Routing |
| --- | --- | --- | --- | --- | --- |
| M0_DOC_SPEC | docs-ebus | 5 | not-required | REQUIRED | Codex |
| M0A_TRANSPORT_BASELINE | gateway | 3 | required-baseline | not-required | Codex |
| M0B_TDD_GATE (4 repos) | ebusreg, ebusgo, productids, gateway | 3 each | not-required | not-required | Codex per-repo |
| M1_REGISTRY_ARRAY_REFACTOR | ebusreg | 5 | not-required | not-required | Codex |
| M2_COMPANION_PURE_FUNC | ebusgo | 3 | not-required | not-required | Codex |
| M2A_OBSERVATION_CORRELATOR_SPEC | gateway | 3 | not-required | not-required | Codex |
| M3_FIRST_OBSERVATION | gateway | 5 | REQUIRED | not-required | Codex |
| M4_COMPANION_INSERT_WITH_CORROBORATION | gateway | 6 | REQUIRED | not-required | Claude |
| M5A_SEED_API_CONTRACT | productids | 3 | not-required | not-required | Codex |
| M5_STATIC_SEED_TABLE | productids + ebusreg | 4 | not-required | not-required | Codex |
| M8_LIVE_VALIDATION | gateway | 3 | REQUIRED | not-required | Claude (orchestrator) |
| M9_TRANSPORT_VERIFY | gateway | 2 | REQUIRED | not-required | Codex |
| M0C_DOC_EVIDENCE_UPDATE | docs-ebus | 2 | not-required | REQUIRED | Codex |

| Milestone | iteration_depends_on | merge_depends_on |
| --- | --- | --- |
| M0_DOC_SPEC | — | — |
| M0A_TRANSPORT_BASELINE | M0 | M0 |
| M0B_TDD_GATE/ebusreg | M0 | M0 |
| M0B_TDD_GATE/ebusgo | M0 | M0 |
| M0B_TDD_GATE/productids | M0, M0B/ebusreg | M0, M0B/ebusreg |
| M0B_TDD_GATE/gateway | M0, M0B/{ebusreg,ebusgo,productids} | M0, M0B/{ebusreg,ebusgo,productids} |
| M1 | M0, M0B/ebusreg | M0, M0A, M0B/ebusreg |
| M2 | M0, M0B/ebusgo | M0, M0A, M0B/ebusgo |
| M2A | M0, M0B/gateway | M0, M0A, M1, M2, M0B/gateway |
| M3 | M0, M2A, M2 | M0, M0A, M1, M2, M2A, M0B/gateway |
| M4 | M0, M3 | M0, M0A, M1, M2, M2A, M3, M0B/gateway |
| M5A | M0, M0B/productids | M0, M0B/productids |
| M5 | M0, M5A, M1 | M0, M0A, M1, M5A, M0B/productids |
| M8 | M0, M3, M4, M5 | M0, M0A, M1, M2, M2A, M3, M4, M5, M5A, M0B/all |
| M9 | M0, M8 | M0, M0A, M8, all impl milestones |
| M0C | M0, M8, M9 | M0, M0A, M8, M9 |

## Routing summary

- 11 of 13 Phase A milestones routed to Codex (easy/medium dev). 2 Claude-routed (M4 corroboration gate logic, M8 live validation orchestration).
- Transport-gate REQUIRED for 4 milestones (M0A, M3, M4, M9). M8 also includes transport-matrix re-run as part of falsifiability.
- Doc-gate REQUIRED for 2 milestones (M0, M0C); both in `helianthus-docs-ebus`.
