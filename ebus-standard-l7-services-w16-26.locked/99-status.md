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
- **M4c1 PR-A** merged 2026-04-19 (squash `e5c8841f` via helianthus-ebusgo#139; ResponderTransport interface + ENH SendResponderBytes)
- **M5b_HA_NOOP_COMPAT** merged 2026-04-19 (squash `1335d81e` via helianthus-ha-integration#186; forward-compat checkpoint + M5B_FORWARD_COMPAT_POSTURE sentinel)
- **M4c1 PR-B** merged 2026-04-19 (squash `721165d7` via helianthus-ebusgo#140; protocol/responder package: FrameDecoder + LocalResponderDispatcher + FSM + timing harness)
- **M4c2** merged 2026-04-20 (squash `547fd4ed` via helianthus-ebusgateway#509; gateway responder runtime + `meta.capabilities.responder` v1.minor emission + atomic.Pointer provider pattern + 8 invariants I1-I8)
- **M5_PORTAL** merged 2026-04-20 (squash `205c2a81` via helianthus-ebusgateway#507; ebus_standard L7 consumer UI + XSS hardening + smart decimal+0x radix + observability bucket)
- **chore_gofmt_cleanup** merged 2026-04-20 (squash `58b9d23a` via helianthus-ebusgateway#510; 14 files whitespace-only, unblocks gofmt gate)
- **fix_silent_failures_sweep** merged 2026-04-20 (squash `af50fda5` via helianthus-ebusgateway#512; 37 catalog + 16 extras per-site judgment; closeOrLog helper + 2 production log.Printf; 0 bugs surfaced on SA4011 investigation; LANE B internal-additive)
- **M4D_responder_capability_lock** merged 2026-04-20 (squash `2fe399af` via helianthus-docs-ebus#279; `architecture/ebus_standard/13-responder-capability-signal.md` 484 lines 12 §; 7 consumer rules incl. rule 7 scope-override for unknown active.transport; reason enum 3 values — transport_mux_bypass from producer-drift; Interpretation A shared-runtime downgrade)
- **M6a_transport_matrix_artifact** merged 2026-04-20 (squash `686dfaf0` via helianthus-ebusgateway#514; `matrix/M6a-transport-matrix.md` 176 lines 8 §; 14-row conformance matrix + 5-subsection rollback criteria + §7 BENCH-REPLACE carry-forward; forward-compat golden folded-in; clean first-pass 0 Codex rounds)
- Current milestone target: `M6b_docs_publication_and_closeout` (matrix publication în docs-ebus + NM plan `.maintenance` transition + issue-map reconciliation)
- **BENCH-REPLACE obligation pending operator** — blocks M6a issue CLOSED state (but M6a artifact MERGED): `responderAckBudget=15ms` placeholder pe ebusgo + ebusgateway; operator MUST run harness pe BASV2 live bus, commit measured value, flip `matrix/M6a-transport-matrix.md` §7 PLACEHOLDER → MEASURED, bump go.mod pins per decision §7.1(1)
- Plan slug: `ebus-standard-l7-services-w16-26.implementing`
- Canonical revision: `v1.0-locked`
- Canonical-SHA256: `23d973c55172df381adbee0c12ace33482cacf1627b5dfed994ef3ec82084a89`

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
| M4c1 PR-A | helianthus-ebusgo | [#138](https://github.com/Project-Helianthus/helianthus-ebusgo/issues/138) | [#139](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/139) | `e5c8841f` | `transport.ResponderTransport` interface + ENH `SendResponderBytes` (thin delegation to `Write()`, reuses single byte-send substrate; never calls StartArbitration); ebusd-tcp perpetual non-satisfaction (M4b2 §3 lock); ENS inherits via `NewENSTransport` returning `*ENHTransport`. 4/4 PR-A tests green; 13 PR-B tests `t.Skip("M4c1 PR-B impl pending")`. Codex THUMBS_UP clean; operator-directed skip-unskip pattern for CI isolation |
| M5b_HA_NOOP_COMPAT | helianthus-ha-integration | [#185](https://github.com/Project-Helianthus/helianthus-ha-integration/issues/185) | [#186](https://github.com/Project-Helianthus/helianthus-ha-integration/pull/186) | `1335d81e` | Forward-compat checkpoint: `tests/test_forward_compat_m4b.py` (6 tests) + synthetic envelope fixture (unknown meta.*/safety_class/validity/DecodedField/error.code + `meta.capabilities.responder` 3-transport shape); `M5B_FORWARD_COMPAT_POSTURE` sentinel in `coordinator.py` forcing future strict-parsing refactors to visibly delete the sentinel. 0 production-code functional change; 0 regressions (238 tests green). Codex THUMBS_UP clean |
| M4c1 PR-B | helianthus-ebusgo | [#138](https://github.com/Project-Helianthus/helianthus-ebusgo/issues/138) | [#140](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/140) | `721165d7` | `protocol/responder` package: FrameDecoder (header+CRC+PB/SB/selector/payload), LocalResponderDispatcher (ZZ filter; coarse-grained lock disjoint from FSM), FSM (Idle→AckReceived→ResponseSent→{FinalAck,Nack retry,Nack exhausted}; compare-before-increment MaxNackRetries), timing harness (clock-injected, responderAckBudget=15ms BENCH-REPLACE, WithinBudget rejects negative durations). All 13 skipped tests now green + 3 added in review (17/17 total). 3 Codex rounds (3 APPLY: off-by-one, negative-duration, Handle error propagation) |
| M4c2 | helianthus-ebusgateway | [#508](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/508) | [#509](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/509) | `547fd4ed` | Gateway responder runtime: internal/nm_runtime/responder_runtime.go (catalog-driven FF 03/04/05/06 emit through execution_policy + ErrResponderTransportUnavailable construction-time sentinel distinct from ErrSafetyClassDenied); envelope.go EnvelopeContractMinor 0→1 + atomic.Pointer provider pattern (SetResponderCapabilityProvider); 4 goldens bumped to v1.1 + 1 forward-compat synthetic; cmd/gateway/main.go canonicalizes transport + type-asserts actual runtime instance (adapter-direct mux bypass downgrades both ENH+ENS rows per Interpretation A). 3 Codex rounds (4 P1 APPLY: canonical I2, runtime capability type-assert, I3 row consistency) |
| M5_PORTAL | helianthus-ebusgateway | [#506](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/506) | [#507](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/507) | `205c2a81` | Portal L7 consumer UI: 4 REST shims `api/v1/ebus-standard/*` (in-process sub-server calls; no /mcp round-trip); "L7 Standard Catalog" section în app.js (services/commands/command/decode views); XSS-hardened decode sandbox (FakeHTMLElement audit-log harness + textContent-only output); smart PB/SB radix (decimal default + 0x prefix) matching MCP integer schema; capability-gated nav via applyCapabilityState + activateSection guard; observability bucket api.ebus_standard.*. 10 Codex rounds (11 APPLY: wiring + render + enum + PB/SB + nav + observability + 3×radix contract evolution). Conflict-rebased post-M4c2 merge |
| chore_gofmt_cleanup | helianthus-ebusgateway | n/a | [#510](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/510) | `58b9d23a` | 14 files `gofmt -w ./...` (cmd/gateway/semantic_vaillant*.go, startup_scan.go, graphql/queries.go, 11× internal/adaptermux/*.go); +252/-252 symmetric; unblocks gofmt gate + exposes 37 previously-masked lint findings |
| fix_silent_failures_sweep | helianthus-ebusgateway | [#511](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/511) | [#512](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/512) | `af50fda5` | 37 cataloged + 16 identical-pattern extras = 53 sites per-site judgment: 2 production log-lane (main.go proxyListener + envelope.go QF1012 Fprintf) + 48 test-teardown via closeOrLog(t, c, what) helper + 3 staticcheck style (QF1007/QF1011/SA4011 labeled break). SA4011 investigation concluded: NO true bug surfaced (test-loop inefficiency only). 0 Codex review rounds (clean first-pass THUMBS_UP). LANE B internal-additive. Operator overrides: TRANSPORT_GATE + PASSIVE_SMOKE_GATE (standard pattern for area-trigger gates on log-only diff) |
| M4D_responder_capability_lock | helianthus-docs-ebus | [#278](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/278) | [#279](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/279) | `2fe399af` | Normative freeze of `meta.capabilities.responder` shape at `contract.minor=1`. New chapter `architecture/ebus_standard/13-responder-capability-signal.md` (484 lines, 12 §sections). §3 invariants I1-I8 (incl. I3 shared-runtime downgrade Interpretation A); §4 consumer rule with 7 fail-closed MUST (rule 7 newly added — unknown active.transport scope-override precedence closing forward-minor gap); §5 enum catalogue (surfaces/reason/state/scope; reason=3 values incl. producer-drift transport_mux_bypass; policy_denied excluded for audit-channel separation); §6 subtree version orthogonal to contract.minor; §8 audit outcomes responded/suppressed_by_capability/policy_denied distinct channels. 1 Codex P2 APPLY (§6.2 rule 7 gap). Supersedes decision doc §4 forward-spec framing |
| M6a_transport_matrix_artifact | helianthus-ebusgateway | [#513](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/513) | [#514](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/514) | `686dfaf0` | Deployment-grade proof: `matrix/M6a-transport-matrix.md` (176 lines, 8 §sections, new top-level matrix/ dir distinct de internal/matrix/ runtime runner). §2 14-row conformance matrix (FC-1..FC-7 forward-compat + CM-01..CM-12 conformance); §3 Vaillant 0xB5 regression catalog (BAI00/BASV2/VR_71/SOL00/NETX3); §4 NM wire regression ref; §5 07 FF cadence floor ref; §6 rollback criteria per repo (5 concrete subsections cu specific SHAs + feature-flag triggers); §7 BENCH-REPLACE carry-forward cu status=PLACEHOLDER + 4-step operator procedure; §8 sign-off conditions (MERGED vs CLOSED distinction). Forward-compat golden `forward_compat_unknown_active_transport_v1_1.golden.json` folded-in cu 4 tests (GoldenParses/ProducerEmits/HashStable/ConsumerFailsClosed cu inline rule-7 canonical consumer). 0 Codex review rounds (clean first-pass THUMBS_UP) |

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

- **M6b_docs_publication_and_closeout** — docs-ebus publication of the matrix artifact cross-reference + `ebus-good-citizen-network-management.locked` plan `.maintenance` transition + issue-map reconciliation (final close-out).
- **BENCH-REPLACE operator follow-up** — manual, separat. Operator runs timing harness pe BASV2 live bus; commits measured `responderAckBudget` în ebusgo + ebusgateway; flips `matrix/M6a-transport-matrix.md` §7 status PLACEHOLDER → MEASURED; bumps go.mod pins. Decision §7.1(1). Blocks M6a issue CLOSED state (but M6a artifact deja MERGED; unchained).

## Blockers

- None.

## Next Actions

1. **M6b_docs_publication_and_closeout** dispatch în helianthus-docs-ebus — publish matrix artifact cross-reference (point to `helianthus-ebusgateway/matrix/M6a-transport-matrix.md` as the canonical location); reconcile issue map (90-issue-map.md + 91-milestone-map.md) across all 17 merged milestones; transition `ebus-good-citizen-network-management.locked` plan to `.maintenance` per deprecation obligation în canonical plan.
2. **BENCH-REPLACE** operator follow-up (manual, separate; unchained from cruise-control FSM): run timing harness pe BASV2 live bus, commit measured `responderAckBudget` în ebusgo + ebusgateway, flip matrix §7 status PLACEHOLDER → MEASURED, bump go.mod pins per decision §7.1(1) + matrix §7 4-step procedure.
3. Post-M6b: plan dir rename `.implementing` → `.locked` per execution-plans convention once all milestones fully closed (M6a CLOSED after BENCH-REPLACE).
