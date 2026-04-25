# vaillant/b503 13: Amendment-1 — Production dispatcher + portal UX gaps

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`

Depends on: [10-scope-decisions.md](./10-scope-decisions.md) for AD16..AD19; [11-execution-safety-and-surfaces.md](./11-execution-safety-and-surfaces.md) for the FSM and capability-signal contract that this amendment extends; [12-milestones-issues-acceptance.md](./12-milestones-issues-acceptance.md) for the v1.0 milestone DAG that amendment-1 extends with M0b/M6/M7/M8.

Scope: Defines the four amendment-1 milestones in full — M0b_DOC_DISPATCHER_BRIDGE (docs companion), M6_DISPATCHER_BRIDGE (production raw-frame dispatch), M7_BENCH_REPLACE (operator-attested live-bus captures), M8_PORTAL_UX_GAPS (portal F1..F8 closure). Records the R1..R5 adversarial provenance for the amendment, the AD16..AD19 invariants, and the explicit DAG/topology constraints introduced. Authoritative source for amendment-1 acceptance criteria.

Idempotence contract: Re-reading this chunk must not soften any AD16..AD19 invariant, reduce the M6 acceptance test set (4 concurrency tests + 8 truth-table tests + epoch-rollover test), reorder M7 attestation gates, or downgrade M8 from LANE A. New milestones added post-amendment-1 require an amendment-2 with its own R1..Rn provenance.

Falsifiability gate: Review fails this chunk if any milestone's acceptance is non-falsifiable, if M6 lock-order assertion lacks a mechanical verification mechanism (timeout-only is insufficient), if epoch-tagged in-flight metadata is missing from M6 scope, if M7 omits any of the three attestation gates (trailer + label + capture artefact), if M8 omits target-switch invalidation or epoch-rollover frontend coverage, or if the DAG permits M7/M8 to merge before M6.

Coverage: §M0b spec, §M6 spec, §M7 spec, §M8 spec, §New DAG invariants, §Adversarial provenance R1..R5, §Open follow-ups.

## Why this amendment exists

All 7 v1.0 baseline milestones merged 2026-04-22..23, but `cmd/gateway/vaillant_b503_wiring.go` injects `b503StubDispatcher{}` which always returns `errB503DispatcherNotWired`. Live gateway probes (192.168.100.4) on 2026-04-25 confirmed:

- `vaillantCapabilities.b503 = { available: false, reason: UNKNOWN }`
- `mcp.ebus.v1.vaillant.errors.get` → `UPSTREAM_RPC_FAILED: "b503: production raw-frame dispatch not yet wired — see execution-plans#19 M2b/M3 follow-up"`
- Matrix `M6a-vaillant-b503.md` §8: 12 rows are `[~]` (stub-pass) with BENCH-REPLACE not executed.

Plan was incorrectly transitioned `.implementing → .locked → .maintenance` on 2026-04-23/2026-04-25 despite `plan.yaml::post_implementation_obligations` flagging `raw_frame_dispatcher` (status: pending) and `bench_replace` (status: pending_operator_bench, blocks_m2b_publication: true). Operator detection on 2026-04-25 forced rollback to `.implementing`; amendment-1 codifies the production-wiring + live-bus + portal-UX gap closure as 4 new milestones plus 4 new decision-matrix entries (AD16..AD19).

Operator additionally added portal-side findings F1..F8 (per-target awareness, full reason matrix, projection fold-in, session-state strip, history sub-tab, AD02 banner, REST-shim decision, tests) — folded into M8.

## M0b_DOC_DISPATCHER_BRIDGE — Docs companion for production dispatcher contract

- Repo: `helianthus-docs-ebus`
- Routing: `docs-researcher` (Claude)
- Complexity: 4
- Depends on: none (parallel to M6 dispatch; merge-blocking gate for M6)
- Lane: docs-only (TDD-exempt per cruise-preflight Row 8)

Scope (NORMATIVE-only — process/governance machinery lives in workflow, not in spec body):

1. New section in `helianthus-docs-ebus/protocols/vaillant/ebus-vaillant-B503.md` titled "Production dispatcher contract" with the following normative content:
   1.1. `RawFrameDispatcher.Invoke` contract — request shape, response shape, error mapping, cancellation discipline.
   1.2. Shared adaptermux/router routing semantics — same path as B524/B525; no parallel transport.
   1.3. Capability-signal 8-state truth table (mirror of AD18; canonical source is plan AD18, doc cites it).
   1.4. Error-mapping table: `transport_down → TRANSPORT_DOWN`, `timeout → UPSTREAM_TIMEOUT`, `NAK/CRC → UPSTREAM_RPC_FAILED` with `structured.detail` keys.
   1.5. Lock acquisition order invariant: `liveMonitorMu → readMu`, never reversed.

Acceptance:

- 8-row truth table renders cleanly (mermaid or table).
- Error-mapping table cites cross-references that M6 tests assert against.
- `.claude/doc-gate-checklist` all green.
- Companion-link annotation present for downstream M6 PR.
- No content drift from plan AD16/AD18 — section explicitly cites plan as canonical source.

## M6_DISPATCHER_BRIDGE — Production raw-frame dispatch

- Repo: `helianthus-ebusgateway`
- Routing: `claude_subagent` (developer) + **mandatory adversarial review**
- Complexity: 8
- Depends on: M4_HA (merged) AND M0b_DOC_DISPATCHER_BRIDGE (merged)
- Lane: code (TDD strict)

Scope:

1. Implement `RawFrameDispatcher` in `cmd/gateway/` satisfying `mcp.RPCDispatcher`.
2. Route `Invoke(ctx, target byte, payload []byte) ([]byte, error)` through the gateway's existing adaptermux/router substrate (same path used for B524/B525 invocations). No parallel transport. (AD16)
3. Preserve `b503session.Manager` single-owner semantics across MCP+GraphQL (already wired by M2b — must not regress).
4. Preserve epoch semantics — BUSY/EXPIRED/UNAVAILABLE error model per AD04 + AD14.
5. Preserve install-write rejection at ebusgo encode layer (AD02 — must not regress).
6. **Replace `b503StubDispatcher{}` injection** in `vaillant_b503_wiring.go::installVaillantB503()`.
7. Error-mapping discipline per M0b error map: `transport_down → TRANSPORT_DOWN`, `timeout → UPSTREAM_TIMEOUT`, `NAK/CRC → UPSTREAM_RPC_FAILED` with structured detail; never collapse legitimate B503 protocol errors into transport errors.
8. **Epoch-tagged in-flight requests (AD18 + R3 A2 fix):** every dispatch request MUST capture `Manager.epoch` into an in-flight request record at issue-time. Reply/NAK/timeout completion paths MUST compare against the stored epoch BEFORE waking waiters or mutating capability. Epoch comparison is request-side metadata, not derived from `Manager` at receive time.
9. Propagate transport disconnect to `b503session.Manager.OnTransportDisconnect()` so AD04 quiesce-release fires.
10. Remove `UPSTREAM_RPC_FAILED: "...not yet wired..."` stub-error literal from `vaillant_b503_wiring.go` and tests.
11. Matrix `M6a-vaillant-b503.md` §3 honest-framing notes preserved (no dilution of `-race` trip-wire claim).
12. Matrix `M6a-vaillant-b503.md` §9 added: production-dispatcher rows (5 read selectors + live-monitor enable/read/disable + 1 mixed-traffic regression × 2 transports = 16 rows). M6 lands these as `[bridge-PASS]`; M7 flips to `[bridge-LIVE-PASS]`.

Acceptance — TDD strict (RED commit first):

- All 5 MCP read tools + live-monitor enable/read/disable have RED tests against a mocked transport that injects byte streams matching LOCAL_CAPTURE.
- Integration test wires `installVaillantB503` with stub adaptermux and asserts production dispatcher is selected (NOT `b503StubDispatcher`).
- Existing B524 transport tests pass unchanged (no regression in router substrate).
- T01..T88 transport-gate baseline unchanged + new §9 rows green.

Acceptance — mixed-traffic concurrency (mandatory, each row a separate test) (R1 A2 + R2 A2 fix):

| Test ID | Scenario | Lock-order assert (mechanical) | Owner-release assert | Cross-route assert |
|---|---|---|---|---|
| `M6-CONC-01` | disconnect during ENABLE handshake | tracer: `liveMonitorMu→readMu` preserved; no reverse acquisition | `manager.OnTransportDisconnect` fires; epoch++ | no B524 frame mis-routes to B503 caller |
| `M6-CONC-02` | disconnect during steady-state READ | tracer: same | session releases; outstanding read returns TRANSPORT_DOWN | concurrent B524 stream uninterrupted |
| `M6-CONC-03` | disconnect during DISABLE | tracer: same | manager idempotent on already-disabled state | concurrent B525 stream uninterrupted |
| `M6-CONC-04` | reconnect under concurrent B524/B525 traffic | tracer: same | new epoch fully constructed before first B503 dispatch admitted | no stale-epoch frames cross |

**Mechanical lock-order verification (R3 A1 fix):** test harness installs a build-tagged lock tracer/hook on `liveMonitorMu` and `readMu` that records every `Lock()`/`Unlock()` with goroutine ID + timestamp. Each `M6-CONC-*` test asserts via the tracer that no goroutine ever entered `readMu` while holding `liveMonitorMu` in the forbidden order, AND no goroutine entered `liveMonitorMu` while waiting on `readMu`. `-race` and 30s deadlock timeout are SECONDARY trip-wires, not the primary proof.

Acceptance — capability-signal 8-state truth table (each row a separate test, AD18 + R1 A3 + R2 A1 fix):

8 tests covering:

1. `cold-boot` → `UNKNOWN`.
2. `post-first-success` → `AVAILABLE`.
3. `disconnect during ACTIVE` → `TRANSPORT_DOWN` literal (NOT collapsed).
4. `reconnect, before first post-reconnect dispatch` → `UNKNOWN` (NOT sticky AVAILABLE).
5. `reconnect, post-first-success-after-reconnect` → `AVAILABLE`.
6. `timeout/NAK/CRC during dispatch` → caller gets `UPSTREAM_RPC_FAILED`; capability stays last-known.
7. `session-expiry detected` → `EXPIRED` internal → AD14 1-retry → `AVAILABLE` OR `TRANSPORT_DOWN` literal.
8. **Stale-epoch in-flight completion** (R2 A1): dispatch on epoch N, transport drop, reconnect to epoch N+1, then injected late epoch-N reply. Assert: completion path discards the late frame WITHOUT inspecting new manager state (epoch comparison is request-side metadata); capability remains last-known; no pending waiter affected.

Forbidden states (assertion targets):
- sticky `AVAILABLE` after transport loss
- premature `AVAILABLE` before first real dispatch
- silent fallback to `UNKNOWN` once `TRANSPORT_DOWN` is knowable

Acceptance — capability recovery test (R1 A3):
- simulate transport reconnect during ENABLED session
- verify session releases and capability surfaces `TRANSPORT_DOWN` literal (per AD14 R4 R2)

## M7_BENCH_REPLACE — Operator-attested live-bus captures

- Repo: `helianthus-ebusgateway`
- Routing: `codex_dev` (PR scaffold) + **operator-attest** (cruise-merge-gate WAIT_OPERATOR)
- Complexity: 5
- Depends on: M6_DISPATCHER_BRIDGE (merged) — `m7_pr_blocked_until_m6_merged: true`
- Lane: A — user-visible-breaking (matrix row state transitions for downstream consumers)

Scope:

1. Per matrix `M6a-vaillant-b503.md` §6 BENCH-REPLACE protocol, run live-bus captures on `adapter-direct` + `ebusd_tcp` transports.
2. Capture artefact appendix file per transport family: `helianthus-ebusgateway/matrix/captures/M7-<transport>-<YYYY-MM-DD>.txt`.
3. Matrix §9 rows transition `[bridge-PASS] → [bridge-LIVE-PASS]` with capture refs.
4. **Three concurrent attestation gates (AD17 + R1 A4 + R2 A4 fix):**
   - PR-head commit trailer `BENCH-REPLACE-SIGNOFF: <YYYY-MM-DD>` (immutable git history evidence — semantic proof);
   - GitHub PR label `bench-replace-signoff` (workflow-gate evidence; PR scaffold step adds it via `gh pr edit --add-label bench-replace-signoff` at PR-open time, idempotent);
   - Capture-artefact appendix files under `matrix/captures/` (factual evidence).
5. cruise-merge-gate MUST validate BOTH (a) trailer-on-HEAD AND (b) label BEFORE allowing operator to lift WAIT_OPERATOR. If label missing only: merge-gate posts targeted comment `bench-replace-label-missing — re-run scaffold step or manually add label via gh pr edit. Trailer + captures are valid; label is the workflow gate.`
6. Trailer + captures remain authoritative semantic proof; label is workflow-gate evidence with explicit remediation path when missing only.
7. Merge-gate squash body composition includes the trailer verbatim (operator's squash inherits it).

Acceptance:

- All matrix §9 rows `[bridge-LIVE-PASS]` with capture-evidence ref.
- PR HEAD commit has `BENCH-REPLACE-SIGNOFF` trailer.
- PR has `bench-replace-signoff` label.
- cruise-merge-gate WAIT_OPERATOR transition logged on meta-issue.
- Schema-stable publication gate (M2b §8) marked satisfied.
- Plan transition unblocked: `.implementing → .locked → .maintenance` permitted post-merge (joint with M8 also merged).

## M8_PORTAL_UX_GAPS — Per-target / reason matrix / projection fold-in / session strip

- Repo: `helianthus-ebusgateway`
- Routing: `codex_restricted` (developer; bounded UI scope but F1+F4 thread per-target state through GraphQL queries)
- Complexity: 6
- Depends on: M6_DISPATCHER_BRIDGE (merged) — `m8_pr_blocked_until_m6_merged: true`. Parallel to M7.
- Lane: A — user-visible-breaking (modifies existing Vaillant pane semantics; changes navigation through Projection cross-linking; alters interpretation of capability/session states). cruise-merge-gate WAIT_OPERATOR.

Pre-implementation decision gate: F7 REST-shim symmetry — `cruise-consult` dispatched (Claude consultant + Codex consultant) BEFORE M8 dev start. Decision artefact filed under `helianthus-ebusgateway/matrix/M6a-vaillant-b503.md §10 "REST shim decision"`. Choice: (a) add `/portal/api/v1/vaillant/*` shims for L7 parity, OR (b) document deliberate GraphQL-only choice in matrix + `helianthus-docs-ebus/architecture/ebus_standard/09-mcp-envelope.md`. Companion docs PR required iff (b).

Scope (F1..F8):

### F1 — Per-target awareness

- Target selector populated from same projection device list used in `section-projection` (controller-aware).
- Thread selection through every `vaillantB503-*` GraphQL query (errors / service / history / live-monitor / capability).
- Distinct availability state rendered per device, not a single global verdict.

### F2 — Render every B503Availability reason distinctly

Per-state UI contract (each state renders a distinct testable artefact, R4 A1 fix):

| State | Required `data-testid` | Required artefact |
|---|---|---|
| `AVAILABLE` | `b503-state-available` | live data section visible (errors-list / service-list / live-monitor controls) |
| `NOT_SUPPORTED` | `b503-state-not-supported` | "support limitation text" — copy referencing device's family + "B503 not implemented" |
| `TRANSPORT_DOWN` | `b503-state-transport-down` | "transport warning" — copy referencing adapter health + retry hint |
| `SESSION_BUSY` | `b503-state-session-busy` | "ownership warning" — copy referencing other-client ownership + retry-after-release hint |
| `UNKNOWN` | `b503-state-unknown` | "probe failure hint" — copy referencing probe error + diagnostic suggestion |

Test asserts each state's `data-testid` is present AND the required artefact element matches the state's row (one separate test per row). NEVER introduce a public `EXPIRED` state (AD14 invariant; collapse transient `EXPIRED` to `UNKNOWN` as GraphQL sanitizer already does).

### F3 — Projection fold-in

- In `section-projection`, when selected device's capability=`AVAILABLE`, render a fourth plane card titled "Vaillant B503" listing read-only verbs (errors / service-current / service-history / live-monitor).
- Same visual treatment as existing Service / Observability / Debug cards.
- Clicking the B503 plane card jumps to `section-vaillant-b503` with target preselected.
- L7 Standard same-shape fold-in: flagged as follow-up commit if it bloats the diff (separate PR allowed).

### F4 — Live-monitor session-state strip

- Surface session `State()` (Idle / Enabling / Active / transient expired-in-refresh) and `IsOwned()` in live-monitor tab.
- Enable / Disable buttons disabled while State=Enabling.
- "Owned by another client" indicator when `IsOwned()=true` but local user did not enable.
- On nav-away from `section-vaillant-b503`, `handleVaillantB503NavAway` (`app.js` line 512) explicitly issues disable when local user owns session.

### F5 — Errors history sub-tab

- "History" sub-tab next to Errors / Service / Live-Monitor showing last N records via `vaillantErrorsHistory` query.
- `VaillantB503HistoryRecord` type already exists in schema.

### F6 — AD02 install-writes banner

- Existing leading copy promoted to visible banner with "?" tooltip pointing to canonical plan.
- Banner element MUST carry `data-testid="b503-install-writes-banner"` (R4 A1 fix).
- Banner MUST contain a help affordance with stable target id `id="b503-ad02-tooltip-anchor"`.
- Tooltip target MUST point to canonical plan ref.

### F7 — REST shim decision (cruise-consult-gated)

- Decision artefact filed BEFORE M8 dev work begins.
- If (a): add `/portal/api/v1/vaillant/*` shims for L7 parity → companion docs PR not required.
- If (b): document deliberate GraphQL-only choice → companion docs PR in `helianthus-docs-ebus` required.

### F8 — Tests

Mandatory test set (each row a separate test, building on R4 A1+A2+A3 + R5 A1 fixes):

| Category | Test rows |
|---|---|
| Reason-render matrix (F2) | 5 tests, one per `B503Availability` state |
| Per-target wiring (F1) | M8-TGT-01 (capability invalidation), M8-TGT-02 (live-monitor ownership invalidation), M8-TGT-03 (history invalidation), **M8-TGT-04 (target-switch during live-monitor enable in-flight — R5 A1)** |
| Session-state strip transitions (F4) | Idle→Enabling→Active→Disabled, plus IsOwned()=true-by-other variant |
| History tab loading (F5) | mocked GraphQL response, render N records, empty-state |
| Nav-away disable (F4) | local user enabled session, navigate away → assert disable issued |
| AD02 banner (F6) | banner present with stable selectors; tooltip-anchor points to canonical plan |
| Projection integration (F3) | B503 plane card appears iff capability=`AVAILABLE` for selected device; ≥3 distinct target addresses |
| Frontend epoch-rollover (F3+F4 R4 A3) | composite 4-step: active → transport-down → unknown-pre-success → available-after-success |

**M8-TGT-04 contract (R5 A1 fix):** target-switch during live-monitor enable in-flight on T1 with switch to T2 before completion:
- T1 enable completion MUST NOT mutate T2 strip state.
- If local ownership is obtained on T1 after the switch, the frontend MUST immediately issue disable for T1 (preferred) — no relying on idle-timeout.
- Rationale: clean ownership semantics; prevents leaked active session on previously-selected target.

**Frontend epoch-rollover composite test (R4 A3 fix):**

| Step | Trigger | Required UI state |
|---|---|---|
| 1 | initial load with capability=AVAILABLE, session enabled, State=Active | strip shows Active; projection plane card shows AVAILABLE |
| 2 | mock GraphQL: transport-down event during active session | strip MUST leave Active immediately; render TRANSPORT_DOWN derived state; projection card downgrades to capability=TRANSPORT_DOWN within ≤1 poll cycle |
| 3 | mock GraphQL: reconnect, capability=UNKNOWN (pre first post-reconnect dispatch) | strip MUST show UNKNOWN-derived state (NOT stale Active); projection plane card MUST show UNKNOWN-state plane-card or hide if config requires AVAILABLE |
| 4 | mock GraphQL: first successful read post-reconnect, capability=AVAILABLE | strip back to Idle (NOT Active until user re-enables); projection plane card back to AVAILABLE |

Constraints:

- One PR per repo (gateway-only); F3 L7 fold-in may be follow-up if bloats diff.
- Capability-gated nav preserved (`applyCapabilityState` + `setNavState` invariants).
- XSS hardening: `textContent`, never `innerHTML` (M3_PORTAL audit-logged `FakeHTMLElement` pattern).
- NO protocol/dispatcher edits in M8 (gateway-portal only); flag-and-stop if any finding requires backend work.
- Live verification on 192.168.100.4:8080 only after M6 dispatcher merged; until then GraphQL responses mocked in component tests for each reason value.

Acceptance:

- All F1..F8 acceptance test rows green under `-race` + jsdom.
- DOM audit unchanged: no element references `clear`, `delete`, `reset` in Vaillant pane (M3 invariant preserved).
- Projection integration test passes for ≥3 distinct target addresses (BAI 0x08, BASV2 0x15, controller default).
- `matrix/M6a-vaillant-b503.md §10` REST-shim decision recorded with cruise-consult provenance.
- Companion docs PR present iff F7 outcome = (b).
- Capability=NOT_SUPPORTED vs TRANSPORT_DOWN vs SESSION_BUSY vs UNKNOWN rendered as distinct UI states (matrix-asserted via `data-testid`, not visual-only).
- Implementation contract: query/cache keys include target address as a first-class component; in-flight responses with mismatched target ARE discarded by the result handler before state mutation; one jsdom test per critical tab family (capability, live-monitor, history, enable-handshake).

## New DAG invariants (amendment-1)

```yaml
m5_blocks_m2b: true                       # v1.0 baseline
mcp_before_graphql_before_consumers: true # v1.0 baseline
m6_blocks_m7: true                        # NEW — raw-frame dispatcher must land before live-bus captures
m6_blocks_m8: true                        # NEW — portal target-aware UX needs production capability semantics
m7_pr_blocked_until_m6_merged: true       # NEW — cruise-topology rejects M7 PR open/review until M6 merged (R3 A3)
m8_pr_blocked_until_m6_merged: true       # NEW — same for M8
m7_blocks_terminal: true                  # NEW — bench replace gate to .locked→.maintenance
m8_blocks_terminal: true                  # NEW — portal UX gap closure also gates terminal
adversarial_review_required:              # v1.0 + amendment-1
  - M2a_GATEWAY_MCP
  - M5_TRANSPORT_MATRIX
  - M6_DISPATCHER_BRIDGE
```

## Adversarial provenance — amendment-1 R1..R5

Codex `gpt-5.4`, reasoning=high, mode=AMENDMENT_REVIEW (delta-bounded; baseline plan attacks out of scope).

| Round | Attacks (H/M/L) | Concessions | Outcome |
|---|---|---|---|
| R1 | 5 (2/3/0) | 2 | All integrated. M0b added (doc-gate companion). 4-test concurrency split required. Capability truth table introduced. BENCH-REPLACE-SIGNOFF dual gate (trailer + label). Transport-gate row coverage explicit. |
| R2 | 5 (2/2/1) | 2 | All integrated. AD18 expanded to 8 rows including stale-epoch discipline. M6-CONC-01..04 split by timing case. M0b scope trimmed (NORMATIVE-only). Label ownership assigned (PR scaffold step adds, merge-gate validates with remediation message). Lane subtype clarified (M6 LANE B vs M7 LANE A). |
| R3 | 3 (0/2/1) | 2 | Declared CONSENSUS. Inline-fix integrated: mechanical lock-order verification via build-tagged tracer; epoch as request-side metadata explicit; `m7_pr_blocked_until_m6_merged` topology invariant. |
| R4 | 3 (0/3/0) | 3 | Per-state `data-testid` rendering contract (replaces non-falsifiable "actionable copy"). Target-switch in-flight invalidation tests (M8-TGT-01..03). Frontend epoch-rollover composite test (M8). M8 reclassified LANE A. |
| R5 | 1 (0/1/0) | 3 | CONSENSUS. M8-TGT-04 added (target-switch during enable handshake; immediate disable on local-user-initiated abandoned session). Amendment locked. |

No ESCALATE_TO_OPERATOR. Total: 17 attacks (4 H, 11 M, 2 L), 12 concessions, 5 rounds.

## Open follow-ups (amendment-1 scope)

None as cruise-run residual. The pre-existing
`ebusstd_errsafetyclassdenied_restore` post-implementation obligation
(M2a interim fix waiting upstream `helianthus-ebusreg` symbol export)
remains documented in `plan.yaml::post_implementation_obligations` and
is unaffected by amendment-1.
