# Milestone Map

| Milestone | Scope | Primary repo | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0_DOC_GATE` | Normative catalog + type rules + safety policy + adopt-and-extend preface | `helianthus-docs-ebus` | none | **ready** |
| `M1_TYPES` | L7 primitive types with positive+negative golden vectors | `helianthus-ebusgo` | `M0` | queued |
| `M2_CATALOG` | Catalog schema + YAML + identity key + collision test + SHA pinning | `helianthus-ebusreg` | `M0` | queued |
| `M3_PROVIDER` | Generic provider + identity provenance + namespace-isolation tests + disable switch | `helianthus-ebusreg` | `M2` | queued |
| `M4_GATEWAY_MCP` | MCP surfaces + execution-policy module + `rpc.invoke` gating + NM broadcast wiring | `helianthus-ebusgateway` | `M1`, `M3` | queued |
| `M4B_read_decode_lock` | Freeze list/get/decode envelope + safety metadata + error/replacement schemas + version reporting | `helianthus-ebusgateway` | `M4` | queued |
| `M4b1` | Transport feasibility primitives for slave-address receive/reply | `helianthus-ebusgo` | `M1` | parallel-spike |
| `M4b2` | Gateway capability observation + go/no-go | `helianthus-ebusgateway` | `M4b1` | queued |
| `M4c1` | Transport support for responder-mode frames on approved transports | `helianthus-ebusgo` | `M4b2=go` | blocked-on-feasibility |
| `M4c2` | Responder runtime for `07 04` + `FF 03/04/05/06` | `helianthus-ebusgateway` | `M4c1` | blocked-on-feasibility |
| `M4D_responder_lock` | Freeze responder capability/status fields | `helianthus-ebusgateway` | `M4c2` | blocked-on-feasibility |
| `M5_PORTAL` | Portal read/list/decode UI with decode-sandbox hardening | `helianthus-vrc-explorer` | `M4B_read_decode_lock` | queued |
| `M5b_HA_NOOP_COMPAT` | HA compatibility checkpoint: no new entities/fields | `helianthus-ha-integration` | `M4B_read_decode_lock` | queued |
| `M6a` | Live-bus matrix artifact | `helianthus-ebusgateway` | `M4B`, `M4D`, `M5`, `M5b` | queued |
| `M6b` | Matrix publication + NM plan `.maintenance` transition | `helianthus-docs-ebus` | `M6a` | queued |

## Ordering Rules

- Default order:
  `M0 → M1 → M2 → M3 → M4 → M4B → M4b1 → M4b2 → M4c1 → M4c2 → M4D → M5 → M5b → M6a → M6b`.
- `M4b1` may start as soon as `M1` exists and runs in parallel with `M2`,
  `M3`, and `M4`, but it only gates `M4b2`.
- Responder lane `M4c1`/`M4c2`/`M4D` begins only if `M4b2` returns a
  go-signal. On no-go, the responder lane is explicitly documented as
  not-pursued in first delivery; `M4D_responder_lock` is a no-op
  artifact documenting the transport outcome; `M5_PORTAL` and `M5b`
  still land on `M4B_read_decode_lock`.
- `M4B_read_decode_lock` is a hard gate for `M5_PORTAL` and
  `M5b_HA_NOOP_COMPAT`.
- `M4D_responder_lock` is a hard gate for any portal responder UI, not
  for read/list/decode UI.
- `M6a` depends on the complete set of earlier gates including `M4D` (or
  its no-op form on no-go). `M6b` closes the deprecated plan only after
  `M6a` lands.
- Conditional proxy/firmware work opens new issues with explicit
  dependency edges to `M4b2` outcome. It never rides inside `M4b` or
  `M4c`.
