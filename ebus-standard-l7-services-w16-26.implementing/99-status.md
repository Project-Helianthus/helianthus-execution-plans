# Status

State: `implementing`
Implementation started: `2026-04-19`

## Current Position

- Plan locked on `2026-04-18`
- Directory state transition `.locked` → `.implementing` on `2026-04-19` (first code PR merged triggered the rename per plan convention).
- **M0_DOC_GATE** merged 2026-04-18 (squash `b85e7084` via helianthus-docs-ebus#267)
- **M1_TYPES** merged 2026-04-19 (squash `3964e341` via helianthus-ebusgo#137)
- **M2_CATALOG** merged 2026-04-19 (squash `ae05a98a` via helianthus-ebusreg#121)
- **M3_DOC_COMPANION** merged 2026-04-19 (squash `1a623666` via helianthus-docs-ebus#269)
- **M3_PROVIDER** merged 2026-04-19 (squash `30aa69a0` via helianthus-ebusreg#123)
- Current milestone target: `M4_GATEWAY_MCP` (deps M1 + M3 satisfied; Wave 4 preflight pending operator discussion)
- Plan slug: `ebus-standard-l7-services-w16-26.implementing`
- Canonical revision: `v1.0-locked`
- Canonical-SHA256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`

## Merged Deliverables

| Milestone | Repo | Issue | PR | Squash SHA | Summary |
|---|---|---|---|---|---|
| M0_DOC_GATE | helianthus-docs-ebus | [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) | [#267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) | `b85e7084` | 9 normative docs under `architecture/ebus_standard/`; adopt-and-extend of NM docs #251/#253/#256 (NOT rewritten) |
| M1_TYPES | helianthus-ebusgo | [#136](https://github.com/Project-Helianthus/helianthus-ebusgo/issues/136) | [#137](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/137) | `3964e341` | L7 primitives BYTE/CHAR/DATA1c/raw/composite-BCD/length-selector + 50+ golden vectors; 7 review rounds, 11 findings addressed |
| M2_CATALOG | helianthus-ebusreg | [#120](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/120) | [#121](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/121) | `ae05a98a` | 14-tuple identity, collision + ambiguity detection, SHA-pinned YAML catalog, TinyGo build-tag discipline; 9 review rounds, 15 findings addressed |
| M3_DOC_COMPANION | helianthus-docs-ebus | [#268](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/268) | [#269](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/269) | `1a623666` | Runtime enforcement section in `05-execution-safety.md` + new `08-provider-contract.md` + `00-namespace.md` cross-namespace invariant; 1 review + 1 fix |
| M3_PROVIDER | helianthus-ebusreg | [#122](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/122) | [#123](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/123) | `30aa69a0` | Generic provider + 14-tuple identity + ABI snapshot + namespace isolation (`internal/`) + invoke-boundary safety (`ErrSafetyClassDenied`) + disable switch (`EBUS_STANDARD_PROVIDER_ENABLED`); 6 Codex+1 Copilot rounds, 12 findings addressed |

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

- **M4_GATEWAY_MCP** in `helianthus-ebusgateway` — MCP surfaces (`ebus.v1.ebus_standard.services.list` / `.commands.list` / `.command.get` / `.decode`) + execution-policy module shared with `rpc.invoke` + NM runtime wiring to catalog emit/responder. Doc-gate REQUIRED. Transport-gate REQUIRED.
- **M4b1 responder spike**: DONE (findings doc on `helianthus-ebusgo/spike/m4b1-responder-feasibility`). Verdicts: ENH/ENS=PARTIAL, ebusd-tcp=BLOCKED.
- **M4B_read_decode_lock** queued after M4.
- **M4b2 responder go/no-go** (gateway) queued after M4b1+M4.

## Blockers

- None. Wave 4 preflight pending operator discussion (routing + scope).

## Next Actions

1. **Operator discussion** required before Wave 4 preflight:
   - Routing for M4: Codex MCP was not tested post-wave-2 start; claude_subagent continuation precedent vs codex_restricted re-attempt.
   - Scope confirmation: MCP surfaces list + execution-policy module + NM runtime wiring. Any additional robustness checkpoints parallel to M3's ABI-snapshot / isolation / safety-enforcement triplet?
   - M4 plan specifies doc-gate + transport-gate REQUIRED — plan a multi-repo batch (M4_DOC_COMPANION in docs-ebus + M4_GATEWAY_MCP in ebusgateway + possibly M4_TRANSPORT_MATRIX ancillary).
2. M4b2 responder-lane go/no-go signal can run as parallel spike once M4 starts (M4b1 findings already available).
3. M4_GATEWAY_MCP is the highest blast-radius milestone (user-visible MCP surfaces; downstream consumers depend on envelope shape stability post M4B_read_decode_lock).
