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
- **M4_DOC_COMPANION** merged 2026-04-19 (squash `4fa6796b` via helianthus-docs-ebus#271)
- **M4_GATEWAY_MCP** merged 2026-04-19 (squash `92fb98cc` via helianthus-ebusgateway#505)
- **M4B_read_decode_lock** merged 2026-04-19 (squash `91bcb34c` via helianthus-docs-ebus#273)
- **M4b2_responder_go_no_go** merged 2026-04-19 (squash `567a6798` via helianthus-execution-plans#17; decision artifact at `decisions/m4b2-responder-go-no-go.md`)
- Current milestone target: `M4c1_ebusgo_responder_transport` (ebusgo RED/IMPL/GREEN; ResponderTransport + protocol/responder package)
- Parallel unblocked (by M4B lock merge): `M5_PORTAL` (target corrected to `helianthus-ebusgateway` portal surface) + `M5b_HA_NOOP_COMPAT`
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
| M4_DOC_COMPANION | helianthus-docs-ebus | [#270](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/270) | [#271](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/271) | `4fa6796b` | `09-mcp-envelope.md` (envelope shape + data_hash determinism + golden-fixture discipline) + `10-rpc-source-113.md` (gateway source byte invariant) + `05-execution-safety.md` policy-module extension; 2 Codex rounds, 4 findings addressed |
| M4_GATEWAY_MCP | helianthus-ebusgateway | [#504](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/504) | [#505](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/505) | `92fb98cc` | 4 MCP surfaces + single execution-policy module (14-tuple whitelist per AD09) + NM runtime wiring (catalog-driven emit; declared events only) + RPC source=113 invariant + envelope-golden tests + data_hash determinism; 11 Codex + 1 Copilot rounds, 31 findings addressed |
| M4B_read_decode_lock | helianthus-docs-ebus | [#272](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/272) | [#273](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/273) | `91bcb34c` | Semantic lock of envelope/error/safety/decode scaffold/catalog-version + v1.minor additive policy + forward-compat conformance golden; cruise-consult dual-vendor 2 rounds consensus (option_a_prime/option_d); 3 Codex P2 APPLY rounds |
| M4b2_responder_go_no_go | helianthus-execution-plans | n/a (decision artifact) | [#17](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/17) | `567a6798` | Decision artifact `decisions/m4b2-responder-go-no-go.md`: option_go_transport_scoped (M4c1+M4c2+M4D GO for ENH/ENS; ebusd-tcp BLOCKED with `command_bridge_no_companion_listen`); cruise-consult dual-vendor 2 rounds consensus; 4 Codex review rounds on predecessor closed docs-ebus#275 (5 findings APPLY + THUMBS_UP) before relocation |

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

- **M4c1_ebusgo_responder_transport** — ebusgo RED/IMPL/GREEN for ResponderTransport interface + protocol/responder package (inbound decoder, local-slave dispatch, ACK/response/final-ACK FSM); PASS/FAIL on ENH live-bus timing bench (BASV2).
- **M4c2_gateway_responder_runtime** — hard-depends on M4c1 merge + gateway go.mod bump.
- **M4D_responder_capability_lock** — parallel with M4c2 IMPL once M4c1 green; freezes `meta.capabilities.responder` into docs-ebus/architecture/ebus_standard/ (new file, e.g. `13-responder-capability-signal.md`).
- **M5_PORTAL** + **M5b_HA_NOOP_COMPAT**: **unblocked now** by M4B merge (read+decode locked); can dispatch in parallel with M4c lane.

## Blockers

- None.

## Next Actions

1. **M4c1** dispatch in helianthus-ebusgo — ResponderTransport interface + protocol/responder package per `decisions/m4b2-responder-go-no-go.md` §6.1 (two PRs: PR-A interface/ENH impl, PR-B decoder/FSM).
2. **M5_PORTAL** + **M5b_HA_NOOP_COMPAT** preflight — read+decode consumer work can launch in parallel with M4c lane (unblocked by M4B merge).
3. After M4c1 green → M4c2 (gateway responder runtime) + M4D (capability signal freeze into docs-ebus).
