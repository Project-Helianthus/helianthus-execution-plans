# vaillant/b503 12: Milestones, Routing, Dependencies, Acceptance

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`

Depends on: [10-scope-decisions.md](./10-scope-decisions.md) and [11-execution-safety-and-surfaces.md](./11-execution-safety-and-surfaces.md). No milestone may merge without the AD01..AD15 invariants and the session model defined there being honoured.

Scope: Per-milestone execution specification. Each milestone lists primary repo, routing (docs-researcher / codex-dev / claude-dev + adversarial-review flag), complexity (1-10 per AGENTS.md §4.1), dependencies, PR body checklist, and falsifiable acceptance criteria.

Idempotence contract: Re-reading this chunk must not reorder the DAG, reduce adversarial-review obligations on M2a / M5, or soften acceptance criteria. New milestones require an amendment (plan bump + new SHA256 per AGENTS.md §8.4).

Falsifiability gate: Review fails if any milestone's acceptance is non-falsifiable, if M5 does not block M2b, if M2a or M5 are routed to codex-dev, or if any milestone's scope re-introduces install writes or cross-device F.xxx normalization.

Coverage: §Dependency DAG, §M0..M5 specifications, §Cross-milestone invariants, §Routing ladder policy.

## Dependency DAG

```text
M0_DOC_GATE
   ▼
M1_DECODER
   ▼
M2a_GATEWAY_MCP
   ▼
M5_TRANSPORT_MATRIX                 ◀── blocks public contract publish
   ▼
M2b_GATEWAY_GRAPHQL
   ├──▶ M3_PORTAL
   └──▶ M4_HA
```

Rationale: the GraphQL schema is the public v1 consumer contract. It must not lock onto behaviour that transport validation has not yet demonstrated. M5 therefore BLOCKS M2b, not the reverse. Portal and HA consume GraphQL and both fan out from M2b.

## M0_DOC_GATE — Normative B503 specification

- Repo: `helianthus-docs-ebus`
- Routing: `docs-researcher` (Claude)
- Complexity: 5
- Depends on: none
- PR body requires: all §Scope items below with explicit doc-gate checklist per AGENTS.md §1.4.

Scope:
1. Promote `protocols/vaillant/ebus-vaillant-B503.md` from RE notes to normative spec.
2. Selector catalog with wire vectors (all 7 selectors).
3. Invoke-safety table (READ / SERVICE_WRITE / INSTALL_WRITE).
4. Sentinel rules (0xFFFF empty slot) + `first_active_error` derivation.
5. Live-monitor FSM diagram (IDLE/ENABLING/ACTIVE/DISABLED + internal EXPIRED).
6. Gateway operational contract: BUSY / EXPIRED / UNAVAILABLE error model; quiesce timing bounds; ownership-release rules; reconnect handling; idle-timeout semantics; stable API error model.
7. F.xxx decimal caveat: LOCAL_CAPTURE-only provenance, no cross-device guarantee.
8. Explicit install-writes non-exposure list.
9. Public normalization rules: EXPIRED → SESSION_BUSY after bounded 1 retry; TRANSPORT_DOWN / UNKNOWN never collapsed.

Acceptance:
- Companion-link annotation present for downstream code PRs.
- FSM diagram renders (mermaid or equivalent).
- `.claude/doc-gate-checklist` all items green.
- Reviewer can cite every §Scope item against a specific anchor in the merged doc.

## M1_DECODER — `protocol/vaillant/b503` package

- Repo: `helianthus-ebusgo`
- Routing: `codex-dev`
- Complexity: 4
- Depends on: M0_DOC_GATE (merged)

Scope:
1. Package `protocol/vaillant/b503`.
2. Request encoder for `(family, selector)` pair.
3. Per-selector response decoders (5 read selectors).
4. Invoke-safety enum + per-selector classification constants.
5. 5-slot error parser with 0xFFFF sentinel handling.
6. Golden fixtures from LOCAL_CAPTURE.
7. NO cross-device F.xxx lookup table.
8. NO protocol-specific code leaks into `helianthus-ebusreg`.

Acceptance:
- 100% selector coverage round-trip test.
- 0xFFFF sentinel test (all empty, all full, mixed).
- `first_active_error` derivation test across mixed sentinel positions.
- Invoke-safety classifier covers every catalog entry.
- Package API godoc references AD01..AD05 inline.
- `helianthus-ebusreg` diff = 0.

## M2a_GATEWAY_MCP — MCP surface + session gate

- Repo: `helianthus-ebusgateway`
- Routing: `claude-dev` (complexity 8 — hard concurrency). **Mandatory adversarial review.** Consultant escalation after 2 fail loops.
- Complexity: 8
- Depends on: M1_DECODER (merged)

Scope:
1. MCP tools `ebus.v1.vaillant.errors.get`, `.errors.history.get`, `.service.current.get`, `.service.history.get`, `.live_monitor.get`.
2. Live-monitor session model per AD04: ownership key, BUSY/EXPIRED/UNAVAILABLE error model, 30s idle auto-disable, separate `liveMonitorMu`, guaranteed quiesce release on disconnect.
3. NO MCP tool surface for install writes (`Clearerrorhistory`, `Clearservicehistory`).

Acceptance:
- `ebus.v1.*` envelope conformance (meta/data/error, data_hash, stable ordering).
- Determinism test on all five read tools.
- Concurrency test matrix (each a separate test):
  - Poller + MCP read concurrent.
  - Second-owner claimant under active session → BUSY.
  - Disconnect during ACTIVE → session released, no leaked lock.
  - Reconnect with stale handle → EXPIRED internal → retry once → outcome per AD14.
- Negative test: `mcp/server_test.go` asserts no tool named `*clear*` is registered under `ebus.v1.vaillant.*`.

## M5_TRANSPORT_MATRIX — Transport gate before contract publish

- Repo: `helianthus-ebusgateway`
- Routing: `claude-dev` (complexity 7 — transport arbitration). **Mandatory adversarial review.**
- Complexity: 7
- Depends on: M2a_GATEWAY_MCP (merged). **Blocks M2b.**

Scope:
1. Transport families covered: `adapter-direct`, `ebusd_tcp`; `ebusd_serial` if lab-available (escalation note otherwise).
2. Per-transport scenarios:
   - Passive read decode on all 5 read selectors.
   - Live-monitor enable → read → explicit disable.
   - Reconnect-during-session.
   - Session-expiry during quiesce.
   - Stale-owner cleanup after disconnect.
3. Regression rows (AD12):
   - B524 poll group throughput unchanged under new `liveMonitorMu`.
   - At least one B524 read test under concurrent B503 live-monitor session.
4. Artefact: `matrix/M6a-vaillant-b503.md` with per-transport pass/fail rows, angry-tester command log, PASS/FAIL verdicts.

Acceptance:
- Matrix file merged with all scenarios × transports rows filled.
- Zero regression in B524 baseline numbers.
- If any transport family unavailable, operator escalation note present and explicit narrowing applied to v1 supported-transports list.
- Reconnect tests pass.

## M2b_GATEWAY_GRAPHQL — GraphQL parity + capability signal

- Repo: `helianthus-ebusgateway`
- Routing: `codex-dev`
- Complexity: 5
- Depends on: M2a_GATEWAY_MCP AND M5_TRANSPORT_MATRIX (both merged)

Scope:
1. GraphQL queries: `vaillantErrors`, `vaillantErrorHistory(index: Int)`, `vaillantServiceCurrent`, `vaillantServiceHistory(index: Int)`, `vaillantLiveMonitor`.
2. `vaillantCapabilities { b503 { available, reason } }` with enum `B503Availability { AVAILABLE, NOT_SUPPORTED, TRANSPORT_DOWN, SESSION_BUSY, UNKNOWN }`.
3. EXPIRED never in public enum — resolver 1-retry policy per AD14; refresh revealing TRANSPORT_DOWN/UNKNOWN surfaced literally (R4 R2).
4. Schema v1 tag: raw semantics only, no F.xxx derived fields.
5. All resolvers wrap MCP layer. No new execution path.

Acceptance:
- Schema introspection matches MCP tool signatures 1:1.
- Parameterized capability test for each `B503Availability` value.
- Reconnect-between-enable-and-read test: public outcome is `AVAILABLE`-with-data OR `SESSION_BUSY`, never a leaked `EXPIRED`.
- Schema changelog entry present.

## M3_PORTAL — Vaillant read-only pane

- Repo: `helianthus-ebusgateway`
- Routing: `codex-dev`
- Complexity: 4
- Depends on: M2b_GATEWAY_GRAPHQL (merged)

Scope:
1. Portal Vaillant pane with three tabs: errors / service / live-monitor.
2. Tabs check `vaillantCapabilities.b503.available` before rendering data views.
3. Live-monitor tab auto-disables session on tab leave / component unmount.
4. No install-write UI affordances anywhere (not behind flag, not hidden).

Acceptance:
- Playwright: three tabs render under AVAILABLE state.
- Playwright: live-monitor tab auto-disables on navigation away.
- DOM audit: no element references `clear`, `delete`, `reset` in the Vaillant pane.
- Playwright: tabs show empty-state under NOT_SUPPORTED and unavailable-state under transient reasons.

## M4_HA — Diagnostic sensor entity

- Repo: `helianthus-ha-integration`
- Routing: `codex-dev`
- Complexity: 4
- Depends on: M2b_GATEWAY_GRAPHQL (merged)

Scope:
1. Diagnostic sensor `boiler_active_error` (decimal state) + attribute `error_history` (5-slot list).
2. Entity keyed off `vaillantCapabilities.b503.available`.
3. Lifecycle per AD11 + AD15: NOT_SUPPORTED → no entity (after 3-poll hysteresis if prior state differed); TRANSPORT_DOWN/UNKNOWN/SESSION_BUSY → entity present, state=unavailable.
4. No F.xxx translation in entity state. No service-history entity.

Acceptance:
- Coordinator tick cadence pinned (default 30s; hysteresis window ≥90s — documented in entity docstring).
- Tests cover: initial discovery both outcomes; transient TRANSPORT_DOWN → recovery; NOT_SUPPORTED flip with <3 confirmations → entity preserved; NOT_SUPPORTED for 3 consecutive polls → entity destroyed.
- No registry churn under flapping capability signals.

## Cross-milestone invariants

- Single issue / single PR per milestone per repo (AGENTS.md §1.1).
- Squash + merge only.
- Doc-gate companion link required for M1, M2a, M2b, M3, M4 (docs-ebus#M0 is the source).
- Transport-gate artefact for M2a and M5.
- MCP envelope conformance for M2a; GraphQL schema changelog for M2b.
- No milestone may amend install-write exposure without a formal plan amendment per AGENTS.md §8.4.

## Routing ladder

| Routing | Acceptance gate |
|---|---|
| docs-researcher | doc-gate checklist; companion-link tags |
| codex-dev | bounded scope; Codex primary; Claude second-opinion on review |
| codex-restricted | bounded scope + tighter narrowing; Claude pre-PR review |
| claude-dev + adversarial review | Claude primary; Codex adversarial review; consultant escalation after 2 fail loops on same PR |
| operator-attest | cruise-merge-gate WAIT_OPERATOR; merge after operator smoke-test |

`M2a`, `M5`, and `M6` (amendment-1) are the `claude-dev + adversarial review` milestones in this plan. `M7` (amendment-1) is `operator-attest`. `M8` (amendment-1) is `codex-restricted` LANE A — WAIT_OPERATOR.

## Amendment-1 milestones (v1.1, 2026-04-25)

The four amendment-1 milestones (M0b, M6, M7, M8) are specified in detail in [13-amendment-1-dispatcher-portal-ux.md](./13-amendment-1-dispatcher-portal-ux.md). Brief summary:

| Milestone | Repo | Routing | Complexity | Depends on |
|---|---|---|---|---|
| M0b_DOC_DISPATCHER_BRIDGE | helianthus-docs-ebus | docs-researcher | 4 | none (parallel; merge-blocking gate for M6) |
| M6_DISPATCHER_BRIDGE | helianthus-ebusgateway | claude-dev + adversarial | 8 | M4_HA, M0b |
| M7_BENCH_REPLACE | helianthus-ebusgateway | codex-dev + operator-attest | 5 | M6 |
| M8_PORTAL_UX_GAPS | helianthus-ebusgateway | codex-restricted | 6 | M6 (parallel to M7) |

DAG (v1.1): `M0 → M1 → M2a → M5 → M2b → {M3, M4} → M6 → {M7, M8} → terminal`. M0b parallel docs companion to M6. Both M7 and M8 block `.implementing → .locked → .maintenance` terminal.

Cross-milestone invariants (v1.1 additions to v1.0):

- M6 is mandatory adversarial review (joins M2a, M5).
- M7 is auto-merge-FORBIDDEN — must transit cruise-merge-gate `WAIT_OPERATOR` with operator smoke-test.
- M7 PR cannot be opened, reviewed, or lifted from draft until M6 merged on `main`.
- M8 PR cannot be opened, reviewed, or lifted from draft until M6 merged on `main`.
- M7 attestation requires three concurrent gates: trailer-on-HEAD + label `bench-replace-signoff` + capture-artefact appendix files.
- M8 is LANE A (user-visible-breaking — modifies existing Vaillant pane semantics, alters navigation through Projection cross-linking).
- M8 includes an F7 `cruise-consult` decision gate before dev work begins (REST-shim symmetry).
