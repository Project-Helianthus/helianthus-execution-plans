# Milestone Map

Status: `Locked`
Source plan: `source-address-selection-admission`

| Milestone | Primary repo | Depends on | Gate |
| --- | --- | --- | --- |
| M0 - Plan Draft And Lock | helianthus-execution-plans | none | Plan review converges and operator approves lock. |
| M1 - Docs Source Address Selection | helianthus-docs-ebus | M0 | Docs freeze source table from local official specs, supersede current join-era docs, lock probe/NM/degraded semantics, and fix 0xFF context. |
| M2 - ebusgo Selection API | helianthus-ebusgo | M1 merged | Breaking API replaces old join symbols; tests mirror docs-owned static table anchor/version/hash. |
| M2a - HA Add-On Wrapper Source-Config Migration | helianthus-ha-addon | M1 merged | Add-on stops raw source reuse/persistence and maps public config to gateway source-selection contract. |
| M3a - Gateway MCP/Artifact Admission Migration | helianthus-ebusgateway | M1 merged, M2 merged, M2a merged, parent-SHA transport baseline captured | Gateway implements active-probe FSM, MCP/status/artifact contract, recovery surfaces, no-eBUSd admission submatrix, and singular admitted-source authority for all gateway-owned bus-reaching paths. |
| M3b - Gateway GraphQL Parity | helianthus-ebusgateway | M3a | GraphQL parity is generated from the frozen M3a contract and committed as HA-consumable artifacts. |
| M4 - Public API And Legacy Terminology Removal | ebusgo + gateway + docs + HA + ha-addon | M3b merged and M6 merged | Active code/docs use source-selection vocabulary and public snake_case-only admission/status fields; old schema fails; add-on cleanup gate is closed. |
| M5 - ebusreg No-Op Boundary Proof | helianthus-ebusreg | M2 | Opportunistic after M2; ebusreg remains source-byte-only and admission-agnostic. |
| M6 - HA Diagnostics And Empty-Payload Guard | helianthus-ha-integration | may develop against M3b PR-head schema artifact; may merge only after M3b merged | HA surfaces degraded admission, migrates to new schema, removes fixed `0x31` write fallbacks, and does not silently clean up on empty inventory. |
| M7 - Live Rollout And Coexistence Evidence | helianthus-execution-plans | M3b, M6, all M4 lanes, M5 satisfied | Post-merge rollout/rollback artifact references M3 evidence bundle and records eBUSd stopped/proxy-guard state plus operator-approved coexistence evidence. |

## Parallelism

M1 docs and M2 ebusgo can overlap during development, but M1 must merge before
M2 merges. M2a can run after M1 and must merge before M3a runtime validation.
M3a must wait for M2, M2a, and a parent-SHA transport baseline, freezes MCP and
artifact status first, and validates no-eBUSd admission via temporary addon
binary override, not production rollout. M3b adds GraphQL parity from that frozen
contract. M6 may develop against M3b PR-head schema artifacts pinned by commit
SHA, but M6 may merge only after M3b has merged. M4 removes old public schema
only after M6 is merged; the M4 rows are numerically
named for continuity but execute after M6. M5 can run any time after M2 if a
boundary PR is needed, or a committed no-PR-needed decision artifact must mark
M5 satisfied. M7 is post-merge rollout evidence and waits for M3b/M6/all M4
lanes/M5 satisfied.
