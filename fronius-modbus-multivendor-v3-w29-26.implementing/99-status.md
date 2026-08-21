# Implementing status

Plan state: `implementing`

Last reconciled against GitHub and merged repository state: `2026-08-21`.

## Reconciled execution status

GitHub and the merged code repositories are authoritative for execution progress. This
file is a human-readable summary; it is not an authorization mechanism or mutable
workflow state.

- planned nodes: 46
- completed nodes: 36
- remaining nodes: 10
- completed public milestones: M1, M2, M3, M4, M5, and M7
- active FMV3 public code PRs: none
- next unresolved prerequisite: `FMV3-M0-04`

The public Fronius/Modbus delivery is complete through mixed-catalog closure:

- M0 public repositories and ownership documentation are complete;
- M1-M3 transport, registry, SunSpec, and Fronius foundations are complete;
- M4 gateway composition, raw MCP, add-on configuration, live read-only qualification,
  and sanitized evidence are complete;
- M5 canonical PV semantics, semantic MCP, GraphQL, Portal, Home Assistant, packaging,
  and rollout are complete; and
- M7 SunSpec expansion, Growatt disposition, independent SmartLogger/S-Dongle/EMMA
  disposition, and fail-closed mixed-catalog conformance are complete.

Representative merged checkpoints are:

- execution-plan M5-03 semantic lock: `9d353c8514a77d3af46a798f5caa3e5a2445c81f`;
- `helianthus-modbus` transport prerequisite main:
  `c78030472c24f0f2b849fd30124611157a81f834`;
- `helianthus-modbusreg` M7-05 main:
  `1967cae7681860e23f2da809684a60095d913940`; and
- public M7-05 documentation main:
  `736fd599cf0128b32257c178b454114893b5dc57`.

The remaining nodes are the private output-binding tracks and their governance/docs
prerequisites:

- M0: `FMV3-M0-04`, `FMV3-M0-05`, and `FMV3-M0-07`;
- M6: `FMV3-M6-00` through `FMV3-M6-03`; and
- M8: `FMV3-M8-00` through `FMV3-M8-02`.

The planned private repositories `helianthus-eebus-binding-private` and
`helianthus-matter-binding-private` do not yet exist. M6 and M8 therefore remain
unstarted. They consume only `PUBLIC_GRAPHQL_M2M_V1`; they do not read Modbus or registry
internals and do not redefine canonical PV semantics.

Nonblocking public backlog remains tracked separately in `helianthus-modbusreg` issues
`#25`, `#32`, and `#35`. Those P3 items do not reopen completed FMV3 milestones.

## Original plan-cycle declaration

The following inventory is retained verbatim because the current read-only validator
checks the original M0-M3 planning boundary. It describes the plan cycle that first
published this guide, not the current GitHub execution position:

Machine-readable inventory:

- issues: 46
- milestones: 9
- retained domain contracts: 7
- current-cycle last issue: `FMV3-M3-03`
- hard stop: immediately before `FMV3-M4-01`
- gateway work: blocked

## Lifecycle meaning

`implementing` is a lifecycle label for the cross-repository roadmap. It is not a grant
of permission and does not start work. Agents read the merged `main` plan and then use
normal issue/branch/PR workflow in the code repository that owns the selected issue.

The original cycle retained M0-M3 planning and stopped after the Fronius disposition.
Later explicit operator decisions crossed that stop through normal issue/branch/PR,
review, CI, deployment, and live-test boundaries. The retained block above does not
re-block the already merged M4-M7 implementation.

## Simplified validation

The active validator is local, read-only, and structural/semantic. It checks YAML parsing
and duplicate keys, unique IDs, known repositories, dependency existence, DAG acyclicity,
Markdown mirrors, contract IDs/versions, declared order, review-policy invariants, the
M3-03 boundary, and the hard stop.

It does not query GitHub, inspect another checkout, scan arbitrary implementation source,
or cause post-merge actions. Product proof remains in code repositories through
interfaces/types, golden fixtures, conformance tests, and compatibility tests.

## Archived Modbus M1 process history

Before the simplified process, this repository carried executable Modbus M1 admission,
remote-review, release, and post-merge proof machinery. That machinery and its
CI-discovered tests are retired. The former records referenced docs PR `#376` at merge
`711a556fee344c6fe7f1ecf3253fcdb3f5f22d06`, Modbus runtime PR `#6` at reviewed head
`0aac61ddad62f664b47900334c48803587183fa3`, and execution-plans PR `#84`.

Those references are historical facts only. Current state comes from the merged plan and
current GitHub/code-repository state; no trust anchor, review attestation, release token,
or post-merge proof is required or consulted.

## Review

Review has no arbitrary round cap. Fresh exact-HEAD review continues while P0-P2 findings
exist. Merge requires `NO_BLOCKING_FINDINGS` on exact HEAD and all prior P0-P2 resolved or
independently validated as by design. P3/P4 are triaged and nonblocking; duplicates do not
reopen; one independent opinion resolves a by-design dispute.

## Current stop condition

No further action starts merely because this status file is merged. The public lane is at
a clean stop after `FMV3-M7-05`. Continuing the original plan starts with private-repository
governance at `FMV3-M0-04`, followed by the M6 and M8 documentation/bootstrap dependencies.

Private repository creation, credentials, myVaillant lab mutations, releases, and live
installation retain their applicable action-time safety boundaries. The draft semantic
bridge PR `#94` is unrelated and does not change this FMV3 status.
