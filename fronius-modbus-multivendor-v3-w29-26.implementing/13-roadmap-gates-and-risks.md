# Roadmap gates, rollback, and risks

## Milestone path

| Milestone | Outcome |
|---|---|
| M0 | Repository boundaries and public/private direction exist |
| M1 | Shared Modbus protocol and TCP/RTU foundation exists |
| M2 | Transport-neutral profile and observation framework exists |
| M3 | Minimal SunSpec and Fronius disposition exist |
| M4 | Gateway raw MCP and read-only live proof exist |
| M5 | Canonical PV semantics and public consumers exist |
| M6 | Generic private eeBUS binding and lab result exist |
| M7 | SunSpec/Growatt/Huawei catalog expansion is resolved |
| M8 | Generic private Matter binding exists |

The issue DAG, not milestone labels, controls order. Documentation nodes precede their
producers, producers precede consumers, and private outputs remain downstream of the
packaged public contract.

## Current stop gate

The current cycle includes planning through `FMV3-M3-03` and stops immediately before
`FMV3-M4-01`. All gateway work is blocked. Nothing in this repository can cross that
boundary automatically or as a post-merge effect.

The stop may be reconsidered only through a later operator decision after the relevant
code-repository interfaces, fixtures, conformance tests, compatibility tests, and public
evidence have merged.

## Read-only scope

The roadmap is read-only through the current cycle. A write-capable Modbus, profile,
gateway, semantic, Portal, HA, eeBUS, or Matter primitive is outside scope and requires a
new plan. Raw diagnostic surfaces remain bounded, authenticated where externally exposed,
and separate from stable semantic APIs.

## Decision records

`FMV3-M4-04` records the live-smoke result and `FMV3-M4-05` publishes the sanitized
evidence. `FMV3-M5-03` records the reviewed semantic disposition. These records inform
operator and issue-triage decisions; they do not release, authorize, or automatically
block other work.

The ordinary `depends_on` DAG describes planned order only. Before starting a row, the
agent reads the merged plan and reconciles current GitHub state, owning-repository state,
applicable code-repository gates, and operator direction. A negative or stopped decision
is recorded and the affected follow-up issues are explicitly triaged in GitHub rather
than interpreted by a plan-local runtime.

## Review gate

There is no arbitrary review-round cap.

- Continue fresh exact-HEAD review while P0-P2 findings exist.
- Merge only on a fresh exact-HEAD `NO_BLOCKING_FINDINGS` verdict after every prior
  P0-P2 is resolved or independently validated as by design.
- Triage P3/P4 as fix, backlog, or by design; they are nonblocking and do not force
  another round.
- Duplicate findings do not reopen.
- A disputed by-design decision receives one independent opinion.
- Reviewers stay within acceptance criteria and the declared threat model.
- Every P2 states a concrete reachable scenario, wrong behavior, relevant impact, and a
  verifiable fix criterion.
- Theoretical possibilities outside the declared threat model are not P2.

Review evidence belongs to the PR review system. This plan does not require repetitive
empty-result artifacts or mirror reviewer prose into YAML.

## Implementation evidence

The issue-owning code repository proves implementation claims. Depending on the layer,
that proof includes interfaces and types, golden fixtures, protocol/profile conformance,
race and recovery tests, API compatibility tests, and hardware evidence. This plan checks
only local graph and documentation consistency.

## Rollback intent

Rollback is local to the owning repository and preserves published compatibility.

| Scope | Rollback intent |
|---|---|
| Empty repository/bootstrap | Remove only if unused; once used, correct forward without rewriting history |
| Public documentation | Correct before implementation; after publication, issue a versioned forward correction |
| Modbus protocol API | Revert an unpublished API or add a compatible successor before consumer release |
| TCP runtime | Disable the endpoint and pin the last compatible runtime without touching gateway state |
| RTU runtime | Disable RTU registration while retaining shared protocol and TCP behavior |
| Runtime conformance | Hold only the failing transport disabled behind explicit capability state |
| Opaque acquisition contracts | Disable delivery and pin compatible consumers; retain the published IDs/versions |
| Registry contracts | Version an unpublished contract or add a compatible successor before profile release |
| Detection | Disable automatic detection and require explicit profile selection with the same gates |
| Fixtures/profile evidence | Quarantine disputed fixtures or claims and retain them as hypotheses/unknowns |
| SunSpec/Fronius profile | Disable the affected profile/overlay while raw Modbus and unrelated profiles remain available |
| Gateway endpoint/MCP | Disable Modbus configuration or raw tools without changing eBUS behavior |
| Add-on/live smoke | Restore the prior compatible image pair and disable Modbus configuration |
| Canonical semantics | Before publication remove the candidate; after publication retain IDs and report unavailable or add a compatible successor |
| GraphQL/Portal/HA | Preserve published schema/IDs, disable the faulty surface independently, and forward-fix compatibility |
| Private eeBUS/Matter | Disable or revert the private artifact without changing public contracts |
| Growatt/Huawei expansion | Disable only the affected admitted profile; unsupported candidates retain no code/support claim |

No rollback in one layer silently rewrites another layer's contract or historical data.

## Key risks

| Risk | Required response |
|---|---|
| Transport behavior leaks into profiles | Keep profile interfaces transport-neutral and prove the boundary in `helianthus-modbusreg` |
| Fronius drives shared abstractions | Implement only the minimum standard slice, then require evidence for any overlay |
| Consumer precedes stable producer | Enforce docs -> producer -> consumer reachability in the issue DAG |
| Gateway starts early | Preserve the exact hard stop before `FMV3-M4-01` |
| Public code depends on private artifacts | Reject the dependency and publish reusable knowledge where licensing permits |
| RTU support is claimed from fixtures | Require `RTU_PHYSICAL_QUALIFICATION_V1` for enabled/supported physical claims |
| Growatt/Huawei evidence is ambiguous | Record no admission or `Unknown`; do not add code or automatic eligibility |
| Published semantic IDs drift during rollback | Retain IDs and compatibility, disable or report unavailable, then forward-fix |
| Review severity is inflated by theory | Require the concrete P2 evidence fields and declared-threat-model reachability |
| Plan validation becomes a runtime system | Keep it local, read-only, structural, and free of network or product-source inspection |

## Acceptance summary

The plan is internally consistent when it retains exactly 46 unique issue IDs and 9
unique milestones; all repositories are known; every dependency exists; the DAG is
acyclic; issue and milestone Markdown mirrors agree with YAML; retained contract IDs and
versions are exact; every issue has acceptance, gates, and rollback; decision evidence is
retained without plan-local release authority; declared ordering is reachable; M3-03
remains transport-neutral; and the hard stop remains after M3-03 and
before M4-01 with gateway work blocked.
