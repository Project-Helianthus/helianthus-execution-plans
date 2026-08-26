# Fronius-first Modbus and multi-vendor PV roadmap

Status: `implementing`

This directory is a human-readable cross-repository plan. It records issue IDs,
dependencies, repository ownership, retained contract identifiers, review policy, and
rollback intent. It does not run work in
other repositories and it does not grant permission to create repositories, issues,
branches, commits, pull requests, reviews, or merges.

Normal agents use the merged `main` version of this plan as context. They then create
and execute ordinary issue/branch/PR work in the repository named by the selected issue,
subject to that repository's own rules. Merged changes in this repository have no
post-merge side effects.

## Plan boundary

The machine-readable surface is intentionally small:

- `plan.yaml` contains the 46 issue nodes with concise acceptance, applicable gates, and
  rollback, plus 9 milestones, repository ownership, dependency edges, two declarative
  decision records, retained domain contract IDs and versions, ordering constraints, review
  policy, and the M3-03 transport-neutral boundary;
- `validate_plan.py` reads local files and checks only structural and semantic
  consistency;
- the Markdown files explain architecture, acceptance intent, rollback, and risks for
  humans;
- implementation proof belongs to the code repositories that own the behavior.

The plan validator does not inspect arbitrary implementation source, query GitHub,
check out another repository, compare pull-request state, or trigger changes. It does
not reproduce implementation contracts as Python prose.

An earlier PR91 revision tried to turn this plan into a runtime control plane. That
approach was removed. Historical process machinery is not part of the active contract.

## Goal

Deliver a read-only PV path in deliberate stages:

1. establish shared Modbus protocol and transport foundations;
2. establish a transport-neutral profile registry and observation model;
3. use Fronius as the first vertical, with only the minimal SunSpec slice needed by its
   evidence;
4. promote tested raw/profile observations through MCP, canonical
   PV semantics, GraphQL, Portal, Home Assistant, and packaging;
5. expand SunSpec and decide Growatt and Huawei support after the Fronius vertical; and
6. keep generic private eeBUS and Matter output bindings downstream of the public
   machine-to-machine contract.

## Architecture

The ownership direction is:

```text
helianthus-modbus
  -> helianthus-modbusreg
  -> helianthus-ebusgateway
  -> helianthus-ebusreg canonical PV semantics
  -> GraphQL / Portal / Home Assistant / add-on
  -> generic private eeBUS and Matter bindings
```

`helianthus-modbus` owns protocol framing, TCP and RTU transports, endpoint lifecycle,
limits, and recovery. `helianthus-modbusreg` owns standard and vendor profile families,
catalogs, detection, codecs, observations, and provenance. The gateway composes those
libraries behind its protocol-agnostic adapter boundary; it does not absorb their
ownership.

Public repositories must not import or depend on either private binding repository.
Private bindings consume only the published public contract assigned to them and do not
become alternate sources of canonical semantics.

## Repository set

The roadmap retains these repository boundaries:

| Repository | Responsibility |
|---|---|
| `Project-Helianthus/.github` | Organization repository governance |
| `Project-Helianthus/helianthus-modbus` | Modbus protocol and transports |
| `Project-Helianthus/helianthus-modbusreg` | Standard/vendor profiles and observations |
| `Project-Helianthus/helianthus-ebusgateway` | Gateway adapter, MCP, GraphQL, and Portal consumer |
| `Project-Helianthus/helianthus-ebusreg` | Protocol-independent canonical PV semantics |
| `Project-Helianthus/helianthus-ha-integration` | Home Assistant GraphQL consumer |
| `Project-Helianthus/helianthus-ha-addon` | Deployment and recovery packaging |
| `Project-Helianthus/helianthus-docs-ebus` | Public contracts and reusable evidence |
| `Project-Helianthus/helianthus-eebus-binding-private` | Generic private eeBUS output binding |
| `Project-Helianthus/helianthus-matter-binding-private` | Generic private Matter output binding |
| `Project-Helianthus/helianthus-execution-plans` | Cross-repository decisions only |

No per-vendor repository is added. Fronius, Growatt, and Huawei profiles remain in the
shared registry repository. The eeBUS and Matter repositories remain generic private
output bindings rather than vendor-specific products.

## Retained domain contracts

The following names and versions must survive planning changes:

| ID | Version | Owner/use |
|---|---:|---|
| `OPAQUE_RUNTIME_ACQUISITION_V1` | 1 | Public runtime companion contract |
| `helianthus.modbus.opaque-runtime-acquisition` | 1 | Runtime schema identity |
| `published_attempt_v1` | 1 | Published attempt projection schema |
| `helianthus.fmv3-m1-06-conformance-report.v3` | 3 | M1-06 conformance report schema |
| `helianthus.fmv3-m3-03-completion.v2` | 2 | M3-03 completion record schema |
| `RTU_PHYSICAL_QUALIFICATION_V1` | 1 | Physical RTU qualification gate |
| `PUBLIC_GRAPHQL_M2M_V1` | 1 | Public machine-to-machine consumer contract |

This repository retains only those identifiers and ordering implications. Interfaces,
types, golden fixtures, conformance tests, and compatibility tests in the producing and
consuming code repositories prove their actual behavior.

## Ordering

Public companion documentation precedes the producer that implements a contract. A
tested producer precedes consumers. The main chains are:

- M1 docs -> Modbus protocol/runtime -> registry contracts;
- Fronius/SunSpec evidence -> minimal SunSpec -> Fronius disposition -> gateway;
- canonical PV docs -> canonical semantics -> semantic MCP -> lock decision -> public
  GraphQL docs -> GraphQL -> Portal -> Home Assistant -> packaging;
- packaged public GraphQL -> public binding docs -> private eeBUS or Matter binding;
- Fronius completion -> expanded SunSpec -> Growatt disposition -> Huawei profiles ->
  mixed-catalog conformance.

The issue DAG is authoritative for the exact edges. The order declarations in
`plan.yaml` are validation assertions over that DAG, not a second scheduler.

## Fronius M3 boundary

`FMV3-M3-03` uses Modbus TCP only as the phase-1 evidence and acquisition path. Any
production profile logic added by that issue must remain transport-neutral and read-only.
The public disposition is exactly `STANDARD_ONLY` or `OVERLAY_REQUIRED`.

The implementation repository proves this boundary through its own interfaces, package
types, fixtures, and tests. The plan validator only checks that the issue, repository,
dependencies, wording, and retained completion schema agree.

## Historical and reconciled boundaries

The original M0-M3 plan cycle ended after `FMV3-M3-03` and immediately before
`FMV3-M4-01`. That historical boundary explains the first implementation wave; it is not
an active authorization mechanism and does not re-block later merged work.

The reconciled public delivery stops after `FMV3-M7-05`. The ten remaining nodes are
private-binding governance and implementation tracks: M0-04/M0-05/M0-07, M6-00 through
M6-03, and M8-00 through M8-02. Their dependencies and action-time safety boundaries
remain recorded in the issue DAG. This plan neither creates private repositories nor
starts a node, branch, review, merge, deployment, or live action.

## Review policy

Review has no arbitrary round cap. Continue fresh exact-HEAD review while any P0, P1,
or P2 finding remains. Merge requires a fresh exact-HEAD `NO_BLOCKING_FINDINGS` verdict
and every prior P0-P2 finding either resolved or independently validated as by design.

P3 and P4 findings are triaged as fix, backlog, or by design. They are nonblocking and
do not force another review round. Duplicate findings do not reopen. A disputed by-design
decision receives one independent opinion.

Reviewers stay within this plan's acceptance criteria and declared threat model. A P2
must state a concrete reachable scenario, the wrong behavior, relevant impact, and a
verifiable fix criterion. A theoretical possibility outside the threat model is not P2.

## Threat model

In scope are dependency mistakes, wrong repository ownership, public/private dependency
inversion, contract ID/version drift, premature consumer work, accidental gateway
readiness, write-capable scope, transport coupling in M3-03, and acceptance or rollback
contradictions.

Runtime correctness, source-level security, race behavior, protocol conformance, release
compatibility, and hardware claims are tested in their owning code repositories. A
malicious repository owner, compromised GitHub service, and compromise of an operator's
local machine are outside this documentation plan's threat model.

## Rollback principle

Rollback stays inside the repository that owns the failed behavior. Before publication,
an unpublished candidate may be removed or replaced. After a public contract ships,
retain its IDs and compatibility surface, disable the faulty capability or report it
unavailable, and issue a forward-compatible correction. A private binding failure never
forces a public API rollback, and a vendor profile failure never rewrites shared runtime
history.
