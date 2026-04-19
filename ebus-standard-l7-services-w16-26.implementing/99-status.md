# Status

State: `implementing`
Implementation started: `2026-04-19`

## Current Position

- Plan locked on `2026-04-18`
- Directory state transition `.locked` → `.implementing` on `2026-04-19` (first code PR merged triggered the rename per plan convention).
- **M0_DOC_GATE** merged 2026-04-18 (squash `b85e7084` via helianthus-docs-ebus#267)
- **M1_TYPES** merged 2026-04-19 (squash `3964e341` via helianthus-ebusgo#137)
- **M2_CATALOG** merged 2026-04-19 (squash `ae05a98a` via helianthus-ebusreg#121)
- Current milestone target: `M3_PROVIDER` (ready; deps M0 + M2 satisfied)
- Plan slug: `ebus-standard-l7-services-w16-26.implementing`
- Canonical revision: `v1.0-locked`
- Canonical-SHA256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`

## Merged Deliverables

| Milestone | Repo | Issue | PR | Squash SHA | Summary |
|---|---|---|---|---|---|
| M0_DOC_GATE | helianthus-docs-ebus | [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) | [#267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) | `b85e7084` | 9 normative docs under `architecture/ebus_standard/`; adopt-and-extend of NM docs #251/#253/#256 (NOT rewritten) |
| M1_TYPES | helianthus-ebusgo | [#136](https://github.com/Project-Helianthus/helianthus-ebusgo/issues/136) | [#137](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/137) | `3964e341` | L7 primitives BYTE/CHAR/DATA1c/raw/composite-BCD/length-selector + 50+ golden vectors; 7 review rounds, 11 findings addressed |
| M2_CATALOG | helianthus-ebusreg | [#120](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/120) | [#121](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/121) | `ae05a98a` | 14-tuple identity, collision + ambiguity detection, SHA-pinned YAML catalog, TinyGo build-tag discipline; 9 review rounds, 15 findings addressed |

## Parallel Spike

| Spike | Repo | Branch | Status | Output |
|---|---|---|---|---|
| M4b1 — responder feasibility | helianthus-ebusgo | `spike/m4b1-responder-feasibility` | DONE | `_spike/m4b1-responder-feasibility.md`; verdict: ENH/ENS=PARTIAL (bounded work), ebusd-tcp=BLOCKED (plan hypothesis confirmed); no M4b2 issue opened (ownership per §14 in ebusgateway) |

## Adversarial Review Summary (Plan Lock)

- R1: 9 attacks, 3 concessions, 9 PLAN_FIX, 2 ESCALATE (E1 mutating invocation, E2 NM ownership).
- R2: 9 attacks, 3 concessions, 9 PLAN_FIX, 1 ESCALATE (E3 system NM broadcasts).
- R3: 3 lock-blockers, 3 concessions, 3 PLAN_FIX, 0 escalations.
- R4: PLAN_STABLE.
- Operator resolutions: E1=(c) mixed safety-class default-deny; E2=(c) adopt-and-extend NM plan; E3=(a) compile-time whitelist exception.

## Deprecation Obligation

- `ebus-good-citizen-network-management.locked` superseded via adopt-and-extend.
- Merged NM docs `#251/#253/#256` remain authoritative (M0 preserves them unmodified).
- `.maintenance` transition deferred until `M6b` reconciliation.

## Active Focus

- **M3_PROVIDER** in `helianthus-ebusreg` — generic provider consuming M2 catalog; catalog-driven method generation; identity provenance; namespace-isolation tests vs Vaillant `0xB5`; feature-flag disable switch. Doc-gate REQUIRED per plan.
- **M4_GATEWAY_MCP** queued (deps M1 + M3).

## Blockers

- None. M3 ready to begin after operator confirms routing (codex_restricted vs claude_subagent).

## Next Actions

1. Operator to authorize Wave 3 preflight (`cruise-preflight` for M3_PROVIDER in `helianthus-ebusreg`).
2. Discuss routing choice (codex MCP has stabilized in this session, but operator may prefer claude_subagent continuation per wave-2 precedent).
3. M3 companion doc updates in `helianthus-docs-ebus` — provider registration + identity provenance contracts added to existing `ebus_standard` doc set (doc-gate trigger).
