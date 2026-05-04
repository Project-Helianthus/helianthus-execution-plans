# Issue Map

Status: `Locked`
Source plan: `source-address-selection-admission`

No GitHub issues are created by this locked plan. The map below is the intended issue
shape for later promotion.

| Draft ID | Repo | Milestone | Depends on | What |
| --- | --- | --- | --- | --- |
| SAS-00 | helianthus-execution-plans | M0 | none | Lock source address selection admission plan. |
| SAS-01 | helianthus-docs-ebus | M1 | SAS-00 | Freeze source-address table from local official specs, supersede current join-era docs, define NM/degraded zero-traffic semantics, and fix 0xFF source-vs-NACK context. |
| SAS-02 | helianthus-ebusgo | M2 | SAS-01 merged | Replace old join API with `SourceAddressSelector` over static docs-referenced table and fix companion validation. |
| SAS-02A | helianthus-ha-addon | M2a | SAS-01 merged | Stop wrapper-side raw source reuse/persistence, map add-on `source_addr` to gateway source-selection contract, and update rollback docs/tests. |
| SAS-03A | helianthus-ebusgateway | M3a | SAS-01 merged, SAS-02 merged, SAS-02A merged, parent matrix baseline captured | Migrate startup admission to active-probed source selection, freeze MCP/status/artifact contract, recovery surfaces, and no-eBUSd admission submatrix. |
| SAS-03B | helianthus-ebusgateway | M3b | SAS-03A | Add GraphQL parity artifacts from the frozen MCP/artifact contract. |
| SAS-04 | helianthus-ha-integration | M6 | may develop against SAS-03B PR-head artifact; may merge only after SAS-03B merged | Migrate HA to `bus_admission.source_selection`, remove fixed `0x31` write fallbacks, surface degraded admission, and suppress unsafe stale cleanup on empty gateway payload. |
| SAS-05 | helianthus-ebusgateway | M4 | SAS-03B merged, SAS-04 merged | Remove legacy public admission artifact/log/schema terminology and add executable schema/terminology removal gates after HA is merged against the new schema. |
| SAS-06 | helianthus-ebusgo | M4 | SAS-03B merged, SAS-04 merged | Verify legacy aliases and terminology are gone from ebusgo. |
| SAS-07 | helianthus-docs-ebus | M4 | SAS-03B merged, SAS-04 merged | Remove current-doc legacy terminology and document the public API migration matrix. |
| SAS-08 | helianthus-ha-integration | M4 | SAS-03B merged, SAS-04 merged | Verify HA has no camelCase/legacy admission dependency and old schema tests fail. |
| SAS-08A | helianthus-ha-addon | M4 | SAS-03B merged, SAS-04 merged, SAS-02A merged | Verify add-on has no legacy raw source-authority cleanup gaps after gateway/HA migration. |
| SAS-09 | helianthus-ebusreg | M5 | SAS-02 | Satisfy ebusreg boundary proof, either via merged no-op boundary PR or committed no-PR-needed decision artifact. |
| SAS-10 | helianthus-execution-plans | M7 | SAS-03B, SAS-04, SAS-05, SAS-06, SAS-07, SAS-08, SAS-08A, SAS-09 satisfied | Capture live rollout/rollback runbook, eBUSd stopped/proxy-guard proof, and operator-approved coexistence evidence. |

## Issue Template Reminder

Every future issue must include:

- What
- Why
- Acceptance Criteria
- Dependencies
