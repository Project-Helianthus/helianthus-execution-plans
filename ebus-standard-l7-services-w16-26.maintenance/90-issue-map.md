# Issue Map

Lifecycle state: `maintenance` as of 2026-04-20. All main-wave rows below are
merged; BENCH-REPLACE remains a manual, non-lifecycle-blocking follow-up.

This plan uses canonical issue identifiers. GitHub issue and PR linkage is
backfilled here as it lands. Canonical IDs remain the stable mapping
surface for the workstream.

Status legend:
- `planned`: defined in the locked plan, not yet started
- `queued`: waiting on an earlier milestone or prerequisite
- `parallel-spike`: may start early in background without unblocking the
  full plan
- `optional`: gated consumer or optional-later lane
- `conditional`: starts only if an earlier feasibility result proves it
  needed
- `merged`: landed on main via squash; the squash SHA is the stable merge
  reference
- `final`: last milestone in its lane; plan seals after all `final`
  entries merge

## Docs and Types (M0, M1)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-DOC-EBS-00` | `helianthus-docs-ebus` | Normative `ebus_standard` catalog; adopt-and-extend NM docs `#251/#253/#256` | **merged** | [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) → [PR #267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) (squash `b85e7084`) |
| `ISSUE-DOC-EBS-01` | `helianthus-docs-ebus` | L7 type rules | **merged** | grouped into [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) → [PR #267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) |
| `ISSUE-DOC-EBS-02` | `helianthus-docs-ebus` | Execution-safety policy + whitelist contract | **merged** | grouped into [#266](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/266) → [PR #267](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/267) |
| `ISSUE-GO-EBS-01` | `helianthus-ebusgo` | L7 type primitives with golden vectors | **merged** | [#136](https://github.com/Project-Helianthus/helianthus-ebusgo/issues/136) → [PR #137](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/137) (squash `3964e341`) |

## Registry and Provider (M2, M3)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-REG-EBS-01` | `helianthus-ebusreg` | Catalog schema + data + identity key + collision test + SHA pinning | **merged** | [#120](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/120) → [PR #121](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/121) (squash `ae05a98a`) |
| `ISSUE-REG-EBS-02` | `helianthus-ebusreg` | Generic provider + identity provenance + disable switch | **merged** | [#122](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/122) → [PR #123](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/123) (squash `30aa69a0`) |
| `ISSUE-REG-EBS-03` | `helianthus-ebusreg` | Namespace-isolation tests vs Vaillant 0xB5 | **merged** | grouped into [PR #123](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/123) (squash `30aa69a0`) |
| `ISSUE-DOC-EBS-M3-COMP` | `helianthus-docs-ebus` | M3 provider-contract doc companion + runtime enforcement section | **merged** | [#268](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/268) → [PR #269](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/269) (squash `1a623666`) |

## Gateway MCP and Safety (M4, M4B)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-EBS-01` | `helianthus-ebusgateway` | MCP surfaces `services.list`/`commands.list`/`command.get`/`decode` | **merged** | [#504](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/504) → [PR #505](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/505) (squash `92fb98cc`) |
| `ISSUE-GW-EBS-02` | `helianthus-ebusgateway` | Execution-policy module + `rpc.invoke` safety gating + caller_context | **merged** | grouped into [PR #505](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/505) (squash `92fb98cc`) |
| `ISSUE-GW-EBS-03` | `helianthus-ebusgateway` | NM runtime wiring to catalog | **merged** | grouped into [PR #505](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/505) (squash `92fb98cc`) |
| `ISSUE-DOC-EBS-M4-COMP` | `helianthus-docs-ebus` | M4 MCP-envelope doc companion + RPC source=113 + policy module | **merged** | [#270](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/270) → [PR #271](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/271) (squash `4fa6796b`) |
| `ISSUE-GW-EBS-06` | `helianthus-ebusgateway` | `M4B_read_decode_lock` semantic-lock artifact | **merged** | [#272](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/272) → [PR #273](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/273) (squash `91bcb34c`) — landed in docs-ebus per normative-lock discipline |

## Responder Lane (M4b1, M4b2, M4c1, M4c2, M4D)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GO-EBS-02` | `helianthus-ebusgo` | Transport feasibility primitives (`M4b1`) | **done** | spike branch `spike/m4b1-responder-feasibility` @ `930aedf`; artifact `_spike/m4b1-responder-feasibility.md` (not merged; feasibility evidence only) |
| `ISSUE-GW-EBS-04` | `helianthus-execution-plans` | Responder capability observation + go/no-go (`M4b2`) | **merged** | [execution-plans#17](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/17) (squash `567a6798`) — decision artifact `decisions/m4b2-responder-go-no-go.md` |
| `ISSUE-GO-EBS-03` | `helianthus-ebusgo` | Transport support for responder-mode frames (`M4c1`) | **merged** (PR-A + PR-B) | [#138](https://github.com/Project-Helianthus/helianthus-ebusgo/issues/138) → [PR #139](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/139) (squash `e5c8841f`) + [PR #140](https://github.com/Project-Helianthus/helianthus-ebusgo/pull/140) (squash `721165d7`) |
| `ISSUE-GW-EBS-05` | `helianthus-ebusgateway` | Responder runtime for `07 04` + `FF 03/04/05/06` (`M4c2`) | **merged** | [#508](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/508) → [PR #509](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/509) (squash `547fd4ed`) |
| `ISSUE-GW-EBS-07` | `helianthus-docs-ebus` | `M4D_responder_capability_lock` semantic-lock artifact | **merged** | [#278](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/278) → [PR #279](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/279) (squash `2fe399af`) — landed in docs-ebus per normative-lock discipline |

## Consumers (M5, M5b)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-EBS-09` | `helianthus-ebusgateway` | Portal read/list/decode UI with hardened decode sandbox (ebus_standard consumer extension of `portal/explorer.go`; renamed from `ISSUE-VRC-EBS-01` per target amendment [execution-plans#18](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/18) squash `7828f4d7`) | **merged** | [#506](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/506) → [PR #507](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/507) (squash `205c2a81`) |
| `ISSUE-HA-EBS-01` | `helianthus-ha-integration` | Compatibility checkpoint: identity/provenance regression | **merged** | [#185](https://github.com/Project-Helianthus/helianthus-ha-integration/issues/185) → [PR #186](https://github.com/Project-Helianthus/helianthus-ha-integration/pull/186) (squash `1335d81e`) |

## Matrix and Close-out (M6a, M6b)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-EBS-08` | `helianthus-ebusgateway` | Live-bus matrix artifact + forward-compat golden + BENCH-REPLACE carry-forward (`M6a`) | **merged** | [#513](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/513) → [PR #514](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/514) (squash `686dfaf0`) — issue CLOSED pending BENCH-REPLACE operator bench |
| `ISSUE-DOC-EBS-03` | `helianthus-docs-ebus` | Matrix publication cross-reference + completion marker (`M6b`) | **merged** | [#280](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/280) → [PR #281](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/281) (squash `17399095`) — **final** |

## Chores (no canonical plan row; opened during execution)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `CHORE-GW-GOFMT` | `helianthus-ebusgateway` | Branch-wide gofmt cleanup (14 files) after M5_PORTAL merge exposed drift | **merged** | [PR #510](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/510) (squash `58b9d23a`) |
| `CHORE-GW-SILENT-FAILURES` | `helianthus-ebusgateway` | Silent-failures dev sweep (37 errcheck + 4 staticcheck + 16 extras per-site judgment; 0 bugs surfaced) | **merged** | [#511](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/511) → [PR #512](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/512) (squash `af50fda5`) |

## Conditional (not opened)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-PROXY-EBS-01` | `helianthus-ebus-adapter-proxy` | Responder-path mediation if `M4b2` proves it needed | **not-needed** | M4b1 spike evidence concluded ENH/ENS PARTIAL (no proxy mediation required); M4b2 decision doc formalized ebusd-tcp as BLOCKED and ENH/ENS as viable without proxy intervention. Conditional row remains for audit trail only. |

## BENCH-REPLACE operator follow-up

The `responderAckBudget = 15 * time.Millisecond` placeholder in
`helianthus-ebusgo/protocol/responder/timing_harness.go` (carried through
M4c2 gateway runtime) awaits a live BASV2-rig bench measurement per
decision doc §7.1(1) and `helianthus-ebusgateway/matrix/M6a-transport-matrix.md`
§7 (4-step operator procedure). This obligation is intentionally **unchained**
from the cruise-control FSM — it may land via a separate operator-manual
PR chain at any time. M6a issue #513 and PR #514 are merged/closed; the
BENCH-REPLACE follow-up remains tracked as operator maintenance work until the
matrix §7 status flips from `PLACEHOLDER` to `MEASURED`.
