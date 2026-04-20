# Milestone Map

| Milestone | Scope | Primary repo | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0_DOC_GATE` | Normative catalog + type rules + safety policy + adopt-and-extend preface | `helianthus-docs-ebus` | none | **merged** squash `b85e7084` (docs-ebus#267) |
| `M1_TYPES` | L7 primitive types with positive+negative golden vectors | `helianthus-ebusgo` | `M0` | **merged** squash `3964e341` (ebusgo#137) |
| `M2_CATALOG` | Catalog schema + YAML + identity key + collision test + SHA pinning | `helianthus-ebusreg` | `M0` | **merged** squash `ae05a98a` (ebusreg#121) |
| `M3_DOC_COMPANION` | M3 provider-contract doc + runtime enforcement section | `helianthus-docs-ebus` | `M2` | **merged** squash `1a623666` (docs-ebus#269) |
| `M3_PROVIDER` | Generic provider + identity provenance + namespace-isolation tests + disable switch | `helianthus-ebusreg` | `M2` | **merged** squash `30aa69a0` (ebusreg#123) |
| `M4_DOC_COMPANION` | M4 MCP-envelope doc + RPC source=113 + policy module | `helianthus-docs-ebus` | `M3` | **merged** squash `4fa6796b` (docs-ebus#271) |
| `M4_GATEWAY_MCP` | MCP surfaces + execution-policy module + `rpc.invoke` gating + NM broadcast wiring | `helianthus-ebusgateway` | `M1`, `M3` | **merged** squash `92fb98cc` (ebusgateway#505) |
| `M4B_read_decode_lock` | Freeze list/get/decode envelope + safety metadata + error/replacement schemas + version reporting | `helianthus-docs-ebus` (normative lock) | `M4` | **merged** squash `91bcb34c` (docs-ebus#273) |
| `M4b1` | Transport feasibility primitives for responder receive/reply | `helianthus-ebusgo` | `M1` | **done** (parallel-spike; not merged — branch `spike/m4b1-responder-feasibility` @ `930aedf`) |
| `M4b2_responder_go_no_go` | Responder lane go/no-go decision artifact (option_go_transport_scoped) | `helianthus-execution-plans` (decision artifact) | `M4b1` | **merged** squash `567a6798` (execution-plans#17) |
| `M4c1_pr_a` | `ResponderTransport` interface + ENH `SendResponderBytes` | `helianthus-ebusgo` | `M4b2=go` | **merged** squash `e5c8841f` (ebusgo#139) |
| `M4c1_pr_b` | `protocol/responder` package: decoder + dispatcher + FSM + timing harness | `helianthus-ebusgo` | `M4c1_pr_a` | **merged** squash `721165d7` (ebusgo#140) |
| `M4c2` | Gateway responder runtime for FF 03-06 + `meta.capabilities.responder` v1.minor emission | `helianthus-ebusgateway` | `M4c1` | **merged** squash `547fd4ed` (ebusgateway#509) |
| `M4D_responder_capability_lock` | Normative freeze of `meta.capabilities.responder` shape | `helianthus-docs-ebus` | `M4c2` | **merged** squash `2fe399af` (docs-ebus#279) |
| `M5_PORTAL` | Portal read/list/decode UI with decode-sandbox hardening + XSS audit-log + smart PB/SB radix + observability bucket | `helianthus-ebusgateway` (portal surface) | `M4B` | **merged** squash `205c2a81` (ebusgateway#507) |
| `M5b_HA_NOOP_COMPAT` | HA forward-compat checkpoint + `M5B_FORWARD_COMPAT_POSTURE` sentinel (no new entities) | `helianthus-ha-integration` | `M4B` | **merged** squash `1335d81e` (ha-integration#186) |
| `M6a_transport_matrix_artifact` | Live-bus matrix + rollback criteria + forward-compat golden + BENCH-REPLACE §7 carry-forward | `helianthus-ebusgateway` | `M4B`, `M4D`, `M5`, `M5b` | **merged** squash `686dfaf0` (ebusgateway#514) — issue CLOSED pending BENCH-REPLACE operator bench |
| `M6b_docs_publication_and_closeout` | Matrix publication cross-reference + completion marker | `helianthus-docs-ebus` | `M6a` | **merged** squash `17399095` (docs-ebus#281) — **final** |

## Chores (opened during execution; not in canonical plan)

| Chore | Repo | Summary | Status |
| --- | --- | --- | --- |
| `chore_gofmt_cleanup` | `helianthus-ebusgateway` | gofmt drift cleanup across 14 files | **merged** squash `58b9d23a` (ebusgateway#510) |
| `fix_silent_failures_sweep` | `helianthus-ebusgateway` | 37 errcheck + 4 staticcheck + 16 extras per-site judgment (0 bugs surfaced) | **merged** squash `af50fda5` (ebusgateway#512) |

## Plan-maintenance operations (direct-on-main commits)

| Operation | Squash | Notes |
| --- | --- | --- |
| Target amendment M5_PORTAL | `7828f4d7` (execution-plans#18) | Corrected from `helianthus-vrc-explorer` (Python CLI) → `helianthus-ebusgateway` (portal surface) |

## Ordering Rules (historical — plan is sealed)

- Default order executed:
  `M0 → M1 → M2 → M3_DOC_COMPANION → M3_PROVIDER → M4_DOC_COMPANION → M4_GATEWAY_MCP → M4B → M4b1 (parallel-spike) → M4b2 → M4c1 PR-A → M5b (parallel) → M4c1 PR-B → M4c2 → M5_PORTAL (parallel) → chore_gofmt → fix_silent_failures → M4D → M6a → M6b`.
- `M4b1` ran as parallel-spike during M2/M3.
- Responder lane (`M4c1`/`M4c2`/`M4D`) fired after `M4b2 = go_transport_scoped`. Actual verdict: ENH+ENS responder-capable partial; ebusd-tcp BLOCKED permanently.
- `M4B` and `M4D` landed in docs-ebus (not ebusgateway) per the normative-lock convention separating protocol contracts from runtime code.
- Conditional proxy/firmware work (`ISSUE-PROXY-EBS-01`) remained not-needed per M4b1 spike evidence.

## BENCH-REPLACE operator follow-up (unchained from plan close-out)

The `responderAckBudget = 15 * time.Millisecond` placeholder is intentionally deferred to an operator-manual follow-up chain. See `matrix/M6a-transport-matrix.md` §7 and `90-issue-map.md` for the 4-step procedure. Plan close-out (this map → all milestones merged; plan dir → `.locked`) does NOT block on BENCH-REPLACE.
