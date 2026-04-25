# Milestone Map — vaillant/b503

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`

Depends on: [12-milestones-issues-acceptance.md](./12-milestones-issues-acceptance.md) and [13-amendment-1-dispatcher-portal-ux.md](./13-amendment-1-dispatcher-portal-ux.md) for scope + acceptance detail.

Scope: Short milestone summary with primary repo, dependency, and status. Populated by cruise-preflight and cruise-dev-supervise as milestones progress.

Idempotence contract: Append-only state column updates; table rows themselves are fixed at lock time (per amendment).

Falsifiability gate: Review fails if the table diverges from `12-milestones-issues-acceptance.md` + `13-amendment-1-dispatcher-portal-ux.md` DAG, if M5 is not marked as blocking M2b, if M2a/M5/M6 lose the adversarial-review flag, if M6/M7/M8 lose the amendment-1 invariants, or if `m7_blocks_terminal` / `m8_blocks_terminal` are downgraded.

Coverage: All 11 milestones (7 v1.0 baseline + 4 v1.1 amendment-1); status column mutable.

| Milestone | Scope | Primary repo | Routing | Complexity | Depends on | Status |
|---|---|---|---|---|---|---|
| `M0_DOC_GATE` | Normative B503 spec incl. FSM, safety classes, EXPIRED normalization rule | `helianthus-docs-ebus` | docs-researcher | 5 | none | merged 2026-04-22 (docs-ebus#283 b4cb1c7) |
| `M1_DECODER` | `protocol/vaillant/b503` package: encoder + decoders + invoke-safety enum + golden fixtures | `helianthus-ebusgo` | codex-dev | 4 | `M0` | merged 2026-04-22 (ebusgo#142 5491494d) |
| `M2a_GATEWAY_MCP` | MCP tools `ebus.v1.vaillant.*.get` + session model w/ epoch semantics | `helianthus-ebusgateway` | **claude-dev + adversarial** | 8 | `M1` | merged 2026-04-22 (ebusgateway#516 d74dc89b) |
| `M5_TRANSPORT_MATRIX` | Transport-gate artefact w/ B524 regression rows — **blocks M2b** | `helianthus-ebusgateway` | **claude-dev + adversarial** | 7 | `M2a` | merged 2026-04-23 (ebusgateway#518 2b8fcd1c) |
| `M2b_GATEWAY_GRAPHQL` | GraphQL parity + `vaillantCapabilities.b503` signal | `helianthus-ebusgateway` | codex-dev | 5 | `M2a`, `M5` | merged 2026-04-23 (ebusgateway#520 07385b01) |
| `M3_PORTAL` | Vaillant pane (errors/service/live-monitor tabs) read-only | `helianthus-ebusgateway` | codex-dev | 4 | `M2b` | merged 2026-04-23 (ebusgateway#522 45846270) |
| `M4_HA` | Diagnostic sensor + history attribute; capability-signal-driven lifecycle | `helianthus-ha-integration` | codex-dev | 4 | `M2b` | merged 2026-04-23 (ha-integration#188 d9355e5f) |
| **`M0b_DOC_DISPATCHER_BRIDGE`** (amend1) | Normative spec for production dispatcher contract + 8-row capability truth table + error mapping + lock-order invariant | `helianthus-docs-ebus` | docs-researcher | 4 | none (parallel; merge-blocks M6) | **not started** |
| **`M6_DISPATCHER_BRIDGE`** (amend1) | Replace `b503StubDispatcher` with production `RawFrameDispatcher`; epoch-tagged in-flight; 4 concurrency tests; 8 truth-table tests; mechanical lock tracer | `helianthus-ebusgateway` | **claude-dev + adversarial** | 8 | `M4`, `M0b` | **not started** |
| **`M7_BENCH_REPLACE`** (amend1) | Operator-attested live-bus captures; matrix §9 `[bridge-PASS]→[bridge-LIVE-PASS]`; 3 attestation gates; WAIT_OPERATOR | `helianthus-ebusgateway` | codex-dev + operator-attest | 5 | `M6` | **not started** |
| **`M8_PORTAL_UX_GAPS`** (amend1) | Per-target portal awareness; full reason matrix; projection fold-in; session-state strip; history sub-tab; AD02 banner; F7 cruise-consult; LANE A | `helianthus-ebusgateway` | codex-restricted | 6 | `M6` (parallel to M7) | **not started** |

## Invariants

### v1.0 baseline

- M5 BLOCKS M2b (transport gate before public contract publish).
- M2a and M5 are mandatory-adversarial-review milestones; consultant escalation triggers after 2 fail loops on the same PR.
- No milestone amends install-write exposure without a formal plan amendment per AGENTS.md §8.4.

### v1.1 amendment-1 (additive)

- M6 is mandatory-adversarial-review (joins M2a, M5).
- M0b BLOCKS M6 (doc-gate companion required).
- M6 BLOCKS both M7 and M8.
- M7 PR open/review BLOCKED until M6 merged on `main` (`m7_pr_blocked_until_m6_merged`).
- M8 PR open/review BLOCKED until M6 merged on `main` (`m8_pr_blocked_until_m6_merged`).
- Both M7 and M8 BLOCK plan transition `.implementing → .locked → .maintenance`.
- M7 auto-merge FORBIDDEN — `cruise-merge-gate` `WAIT_OPERATOR` mandatory.
- M7 attestation requires 3 concurrent gates (trailer + label + capture-artefact).
- M8 is LANE A (user-visible-breaking) — `WAIT_OPERATOR` mandatory.
- M8 has F7 `cruise-consult` decision gate (REST-shim symmetry) before dev start.
