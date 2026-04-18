# Issue Map

This plan uses canonical issue identifiers. GitHub issue and PR linkage is
backfilled here when it exists. Canonical IDs remain the stable mapping
surface for the workstream.

Status legend:
- `planned`: defined in the locked plan, not yet started
- `queued`: waiting on an earlier milestone or prerequisite
- `parallel-spike`: may start early in background without unblocking the
  full plan
- `optional`: gated consumer or optional-later lane
- `conditional`: starts only if an earlier feasibility result proves it
  needed

## Docs and Types (M0, M1)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-DOC-EBS-00` | `helianthus-docs-ebus` | Normative `ebus_standard` catalog; adopt-and-extend NM docs `#251/#253/#256` | **merged** | [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) → [PR #267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) (squash `b85e7084`) |
| `ISSUE-DOC-EBS-01` | `helianthus-docs-ebus` | L7 type rules | **merged** | grouped into [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) → [PR #267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) |
| `ISSUE-DOC-EBS-02` | `helianthus-docs-ebus` | Execution-safety policy + whitelist contract | **merged** | grouped into [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) → [PR #267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) |
| `ISSUE-GO-EBS-01` | `helianthus-ebusgo` | L7 type primitives with golden vectors | ready | not yet linked |

## Registry and Provider (M2, M3)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-REG-EBS-01` | `helianthus-ebusreg` | Catalog schema + data + identity key + collision test + SHA pinning | queued | not yet linked |
| `ISSUE-REG-EBS-02` | `helianthus-ebusreg` | Generic provider + identity provenance + disable switch | queued | not yet linked |
| `ISSUE-REG-EBS-03` | `helianthus-ebusreg` | Namespace-isolation tests vs Vaillant 0xB5 | queued | not yet linked |

## Gateway MCP and Safety (M4, M4B)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-EBS-01` | `helianthus-ebusgateway` | MCP surfaces `services.list`/`commands.list`/`command.get`/`decode` | queued | not yet linked |
| `ISSUE-GW-EBS-02` | `helianthus-ebusgateway` | Execution-policy module + `rpc.invoke` safety gating + caller_context | queued | not yet linked |
| `ISSUE-GW-EBS-03` | `helianthus-ebusgateway` | NM runtime wiring to catalog | queued | not yet linked |
| `ISSUE-GW-EBS-06` | `helianthus-ebusgateway` | `M4B_read_decode_lock` semantic-lock artifact | queued | not yet linked |

## Responder Lane (M4b1, M4b2, M4c1, M4c2, M4D)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GO-EBS-02` | `helianthus-ebusgo` | Transport feasibility primitives (`M4b1`) | parallel-spike | not yet linked |
| `ISSUE-GW-EBS-04` | `helianthus-ebusgateway` | Responder capability observation + go/no-go (`M4b2`) | queued | not yet linked |
| `ISSUE-GO-EBS-03` | `helianthus-ebusgo` | Transport support for responder-mode frames (`M4c1`) | conditional | not yet linked |
| `ISSUE-GW-EBS-05` | `helianthus-ebusgateway` | Responder runtime for `07 04` + `FF 03/04/05/06` (`M4c2`) | conditional | not yet linked |
| `ISSUE-GW-EBS-07` | `helianthus-ebusgateway` | `M4D_responder_lock` semantic-lock artifact | conditional | not yet linked |

## Consumers (M5, M5b)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-VRC-EBS-01` | `helianthus-vrc-explorer` | Portal read/list/decode UI with hardened decode sandbox | queued | not yet linked |
| `ISSUE-HA-EBS-01` | `helianthus-ha-integration` | Compatibility checkpoint: identity/provenance regression | queued | not yet linked |

## Matrix and Close-out (M6a, M6b)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-EBS-08` | `helianthus-ebusgateway` | Live-bus matrix artifact (`M6a`) | queued | not yet linked |
| `ISSUE-DOC-EBS-03` | `helianthus-docs-ebus` | Matrix publication + NM plan `.maintenance` transition (`M6b`) | queued | not yet linked |

## Conditional

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-PROXY-EBS-01` | `helianthus-ebus-adapter-proxy` | Responder-path mediation if `M4b2` proves it needed | conditional | not yet linked |
