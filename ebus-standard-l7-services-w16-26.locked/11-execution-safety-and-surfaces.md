# ebus_standard 11: Execution Safety, Surfaces, and Delivery

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`

Depends on: `10-scope-decisions.md` — establishes the catalog authority,
catalog identity key, and NM subsumption that this chunk's
execution-safety and surface gating rely on.

Scope: Locked Decisions 9-14 covering safety classes and default-deny,
the `system_nm_runtime` compile-time whitelist, the single
execution-policy module, GraphQL gating, portal gating and hardening,
shared-infrastructure isolation between providers, and responder
feasibility spike structure; plus the Execution Safety Policy normative
summary, the Target Repositories list, and the Delivery Order.

Idempotence contract: Declarative-only. Reapplying this chunk must not
weaken default-deny, widen the `system_nm_runtime` whitelist, introduce a
runtime widening path, add new caller contexts, or exempt shared
infrastructure from namespace-isolation tests.

Falsifiability gate: Review fails this chunk if it proposes a runtime
widening of the whitelist, allows `rpc.invoke` to execute
`mutating|destructive|broadcast|memory_write` methods from user context,
removes the deny-parity tests between `rpc.invoke` and provider-direct
invocation, ships portal without the decode-sandbox hardening, or
permits GraphQL exposure of denied classes in first delivery.

Coverage: Locked Decisions 9-14; Execution Safety Policy normative
summary; Target Repositories; Delivery Order.

## Locked Decisions 9-14

### 9. Execution-safety policy: safety classes and default-deny

Each catalog method declares a `safety_class`:

- `read_only_safe`
- `read_only_bus_load`
- `mutating`
- `destructive`
- `broadcast`
- `memory_write`

First-delivery execution policy:

- `rpc.invoke` accepts `read_only_safe` and `read_only_bus_load`.
- `rpc.invoke` default-denies `mutating`, `destructive`, `broadcast`,
  `memory_write`.
- Default-deny applies to every user-facing caller AND to every internal
  caller EXCEPT the named caller context
  `caller_context=system_nm_runtime`.

The `system_nm_runtime` whitelist is keyed by the full catalog identity
tuple (`namespace`, `PB`, `SB`, `selector_path`, `telegram_class`,
`direction`, `request_or_response_role`, `broadcast_or_addressed`,
`answer_policy`, `length_prefix_mode`, `selector_decoder`,
`service_variant`, `transport_capability_requirements`, `version`).

First-delivery whitelist contents (exact variants):

- `0xFF 00` broadcast (NM reset status on join/reset)
- `0xFF 02` broadcast (NM failure signal, payload-less per spec)
- `0xFF 03` responder (net status)
- `0xFF 04` responder (monitored participants)
- `0xFF 05` responder (failed nodes)
- `0xFF 06` responder (required services)
- `0x07 FF` broadcast (sign of life, cadence-floor gated)

Adjacent variants sharing PB/SB but differing on any other axis remain
denied. A deny-parity test covers adjacent variants for each whitelisted
entry.

The whitelist is a compile-time constant. It cannot be widened at
runtime. Every allowed invocation produces a structured audit log entry
(catalog identity, caller, timestamp, outcome). A general operator
override path is out of scope for first delivery; a future locked plan
is the only widening mechanism.

### 10. Single execution-policy module

- One shared execution-policy module is consulted by `rpc.invoke`,
  generated provider methods, and the NM runtime.
- Every call site passes a `caller_context` and the full catalog identity.
- Tests prove denial parity across entry points: direct provider
  invocation and MCP `rpc.invoke` deny identical sets by default.
- The `system_nm_runtime` exception is honoured only when the caller
  context is set and only for whitelisted identities.

### 11. GraphQL parity is gated on MCP semantic lock

- GraphQL parity begins only after `M4B_read_decode_lock` freezes the
  list/get/decode envelope and `M4D_responder_lock` freezes responder
  capability/status fields where relevant.
- `mutating|destructive|broadcast|memory_write` methods NEVER appear in
  GraphQL in first delivery.

### 12. Portal consumer rollout gating and hardening

- Portal read/list/decode UI depends on `M4B_read_decode_lock`.
- Portal responder UI (if any) depends on `M4D_responder_lock`.
- Portal decode sandbox enforces:
  - strict hex validation
  - max payload length
  - max decoded-field count
  - worker/timeout isolation
  - HTML escaping for CHAR, raw, and catalog strings
  - no unsafe Markdown or HTML rendering
- Tests cover malformed hex, oversized input, invalid CHAR bytes, and
  replacement-value display.

### 13. Shared-infrastructure isolation between providers

- Namespace-isolation tests cover shared codec, registry lookup,
  generated method identifiers, MCP envelope helpers, and catalog
  versioning.
- A regression proves Vaillant `0xB5` quirks do not affect
  `ebus_standard` decode results and vice versa.

### 14. Responder feasibility is a dedicated spike

- The responder feasibility spike that existed as `M7a` in the deprecated
  NM plan moves here as `M4b1` (transport primitives in
  `helianthus-ebusgo`) and `M4b2` (gateway capability observation plus
  go/no-go signal).
- Proxy or firmware changes, if required by the spike, are opened as new
  issues in `helianthus-ebus-adapter-proxy` or firmware repositories with
  explicit dependency edges. They do NOT ride inside `M4b`.

## Execution Safety Policy (normative summary)

- User-facing `rpc.invoke`: accept `read_only_safe`,
  `read_only_bus_load`. Deny everything else.
- NM runtime (`caller_context=system_nm_runtime`): additionally accept
  the compile-time whitelist, matched by the full catalog identity.
- Any other caller context (provider direct invocation, future runtime
  callers): accept the user-facing set and nothing else unless a future
  locked plan names and scopes a new caller context.
- Audit: every allowed invocation in `system_nm_runtime` is logged with
  catalog identity, caller, timestamp, and outcome.
- Widening the whitelist, adding caller contexts, or exposing
  mutating/destructive/broadcast/memory-write surfaces via GraphQL is a
  new locked-plan decision, not a code change.

## Target Repositories

- `helianthus-docs-ebus` — normative catalog, type rules, safety policy,
  NM adopt-and-extend, transport matrix publication.
- `helianthus-ebusgo` — L7 type primitives, responder transport
  primitives.
- `helianthus-ebusreg` — catalog schema + data, generic provider.
- `helianthus-ebusgateway` — MCP surfaces, execution-policy module,
  `rpc.invoke` integration, NM runtime wiring to catalog, responder
  runtime, matrix artifact.
- `helianthus-ebusgateway` (portal surface: `portal/explorer.go` + `portal/web/src/app.js`) — portal read/list/decode UI with hardening (target corrected from `helianthus-vrc-explorer` per amendment).
- `helianthus-ha-integration` — compatibility checkpoint only
  (`M5b_HA_NOOP_COMPAT`), no consumer rollout first delivery.

Conditional (not in `target_repos`; opened as new issues only if `M4b2`
requires):

- `helianthus-ebus-adapter-proxy`
- firmware repositories

## Delivery Order

1. `helianthus-docs-ebus` (`M0_DOC_GATE`).
2. `helianthus-ebusgo` (`M1_TYPES`).
3. `helianthus-ebusreg` (`M2_CATALOG` then `M3_PROVIDER`).
4. `helianthus-ebusgateway` (`M4_GATEWAY_MCP` then
   `M4B_read_decode_lock`).
5. Responder lane (strict serial, go-signal gated):
   `M4b1` (ebusgo) → `M4b2` (gateway) → `M4c1` (ebusgo) → `M4c2`
   (gateway) → `M4D_responder_lock` (gateway).
6. Consumers: `M5_PORTAL` (ebusgateway portal surface) and
   `M5b_HA_NOOP_COMPAT` (helianthus-ha-integration), both gated on
   `M4B_read_decode_lock`.
7. Matrix: `M6a` (gateway) → `M6b` (docs publication and NM plan
   deprecation close-out).
