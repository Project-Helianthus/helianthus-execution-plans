# Milestone Map — vaillant/b503

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `896a82e720b33eefb449ea532570e0a962bfa76504519996825f13d92ec9bb28`

Depends on: [12-milestones-issues-acceptance.md](./12-milestones-issues-acceptance.md) for scope + acceptance detail.

Scope: Short milestone summary with primary repo, dependency, and status. Populated by cruise-preflight and cruise-dev-supervise as milestones progress.

Idempotence contract: Append-only state column updates; table rows themselves are fixed at lock time.

Falsifiability gate: Review fails if the table diverges from `12-milestones-issues-acceptance.md` DAG, if M5 is not marked as blocking M2b, or if M2a/M5 lose the adversarial-review flag.

Coverage: All 7 milestones; status column mutable.

| Milestone | Scope | Primary repo | Routing | Complexity | Depends on | Status |
|---|---|---|---|---|---|---|
| `M0_DOC_GATE` | Normative B503 spec incl. FSM, safety classes, EXPIRED normalization rule | `helianthus-docs-ebus` | docs-researcher | 5 | none | **not started** |
| `M1_DECODER` | `protocol/vaillant/b503` package: encoder + decoders + invoke-safety enum + golden fixtures | `helianthus-ebusgo` | codex-dev | 4 | `M0` | **not started** |
| `M2a_GATEWAY_MCP` | MCP tools `ebus.v1.vaillant.*.get` + session model w/ epoch semantics | `helianthus-ebusgateway` | **claude-dev + adversarial** | 8 | `M1` | **not started** |
| `M5_TRANSPORT_MATRIX` | Transport-gate artefact w/ B524 regression rows — **blocks M2b** | `helianthus-ebusgateway` | **claude-dev + adversarial** | 7 | `M2a` | **not started** |
| `M2b_GATEWAY_GRAPHQL` | GraphQL parity + `vaillantCapabilities.b503` signal | `helianthus-ebusgateway` | codex-dev | 5 | `M2a`, `M5` | **not started** |
| `M3_PORTAL` | Vaillant pane (errors/service/live-monitor tabs) read-only | `helianthus-ebusgateway` | codex-dev | 4 | `M2b` | **not started** |
| `M4_HA` | Diagnostic sensor + history attribute; capability-signal-driven lifecycle | `helianthus-ha-integration` | codex-dev | 4 | `M2b` | **not started** |

## Invariants

- M5 BLOCKS M2b (transport gate before public contract publish).
- M2a and M5 are the only mandatory-adversarial-review milestones; consultant escalation triggers after 2 fail loops on the same PR.
- No milestone amends install-write exposure without a formal plan amendment per AGENTS.md §8.4.
