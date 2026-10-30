# Helianthus Execution Plans

> **Deprecated on 2026-10-30.** Do not add plan directories, and do not treat this
> repository as the planning system. Completed plans are closed GitHub Projects.
> Active software planning is
> [Project #2, 0.7 Stabilization](https://github.com/orgs/Project-Helianthus/projects/2)
> and
> [Project #4, 0.8 Declarative and Driver Extraction](https://github.com/orgs/Project-Helianthus/projects/4).
> The markdown in this repository stays as the historical record. This repository
> is not archived, because the 0.7 and 0.8 guides are still read from `main`.

This repository holds human-readable cross-repository plans for Helianthus. It records
architecture decisions, issue IDs, dependency graphs, repository boundaries, contract
IDs/versions, rollback intent, and explicit stop conditions.

It is not a product runtime, execution service, repository mutation service, or substitute for
code-repository issues and pull requests.

## Where completed plans went

Each closed Project below is public, every imported item is Done, and open follow-ups
were left on their existing issues instead of being marked Done.

| Plan | Project |
| --- | --- |
| Superseded 0.7/0.8 combined guide | [#5](https://github.com/orgs/Project-Helianthus/projects/5) |
| Multi-runtime platform history | [#6](https://github.com/orgs/Project-Helianthus/projects/6) |
| Superseded Fronius bridge draft | [#7](https://github.com/orgs/Project-Helianthus/projects/7) |
| Startup admission and discovery | [Helianthus Software — 0.5 Startup admission and discovery](https://github.com/orgs/Project-Helianthus/projects/8) |
| Address-table registry | [Helianthus Software — 0.5 Address-table registry](https://github.com/orgs/Project-Helianthus/projects/9) |
| Superseded gateway refactor draft | [#10](https://github.com/orgs/Project-Helianthus/projects/10) |
| Source-address selection | [#11](https://github.com/orgs/Project-Helianthus/projects/11) |
| Proxy wire-semantics fidelity | [#12](https://github.com/orgs/Project-Helianthus/projects/12) |
| Adapter hardware telemetry | [#13](https://github.com/orgs/Project-Helianthus/projects/13) |
| Stable instance identity | [#14](https://github.com/orgs/Project-Helianthus/projects/14) |
| Gateway-embedded adapter multiplexer | [Helianthus Software — 0.4 Gateway-embedded adapter multiplexer](https://github.com/orgs/Project-Helianthus/projects/15) |
| eBUS good-citizen network management | [#16](https://github.com/orgs/Project-Helianthus/projects/16) |
| eBUS standard L7 services | [Helianthus Software — 0.5 eBUS Standard L7 services](https://github.com/orgs/Project-Helianthus/projects/17) |
| Observe-first bus observability | [#18](https://github.com/orgs/Project-Helianthus/projects/18) |

These plans were not closed, because their own status still has unfinished work
or they never started:

- `software-stabilization-07.implementing` remains the 0.7 guide. Its board is Project #2.
- `software-declarative-08.locked` remains the 0.8 guide. Its board is Project #4.
- `driver-model-transition.implementing`
- `fronius-modbus-multivendor-v3-w29-26.implementing`
- `fix-p11-midwrite-byte-routing-w21-26.implementing` (stopped at M4 NO_GO)
- `runtime-state-w19-26.implementing` (M7 live validation)
- `vaillant-b503-namespace-w17-26.implementing`
- `multi-runtime-semantic-platform.locked`
- `writable-installer-maintenance.implementing`
- `common-firmware-rewrite.locked`
- `docs-stage1-protocol-architecture-realignment.locked`
- `energy-v1-split-source-backfill.locked`
- `ha-hydraulic-visualization-cards.locked`
- `proxy-v0699-synth-stress-baseline.locked`
- `eebus-northbound-readonly-profile-poc.draft`

## Current software release program

The active [0.7 stabilization guide](software-stabilization-07.implementing/00-canonical.md)
covers present software convergence, public-proof priorities and its Daybreak and
hardware gates. The separate [0.8 declarative guide](software-declarative-08.locked/00-canonical.md)
is future work, locked until 0.7 acceptance. Track that work on Projects #2 and #4.
A guide merge has no execution side effects.

## Normal workflow

This section is history. It is not an instruction to start work.

Do not select the next task from a plan directory, a DAG node, or `plan.yaml`.
Task selection for the active programs comes from GitHub Projects:

- 0.7 work is selected from [Project #2](https://github.com/orgs/Project-Helianthus/projects/2).
- 0.8 work is selected from [Project #4](https://github.com/orgs/Project-Helianthus/projects/4).

The other unfinished directories listed above do not authorize new issues. Ask
the operator before starting any of them.

Historically, someone discussed a plan, merged the Markdown to `main`, and an
agent then opened the issue, branch, and pull request in the code repository
that owned the next node. Proof stayed in that code repository. Merging a plan
never created repositories, issues, branches, pull requests, commits,
deployments, or follow-up jobs.

## Plan contents

A plan is primarily Markdown. It may include a small `plan.yaml` when machine-readable
IDs, dependencies, repository boundaries, contract versions, or a hard stop materially
reduce drift.

The common layout is:

```text
<slug>.<state>/
  00-canonical.md
  01-index.md
  10-*.md
  90-issue-map.md
  91-milestone-map.md
  99-status.md
  plan.yaml
  validate_plan.py
```

Lifecycle labels are descriptive:

- `locked`: accepted roadmap, no code work started;
- `implementing`: at least one code-repository issue is in progress;
- `maintenance`: the main wave is complete and follow-up context remains.

These labels do not grant permission or change repository state.

Legacy `.draft` directories are archived planning history. Repository validation does
not execute their validators or treat their machine-oriented fields as current workflow
state.

## Validation

Set up the repository-owned development dependency in a disposable environment, then
run the gate:

```bash
python3 -m venv /tmp/helianthus-execution-plans-venv
/tmp/helianthus-execution-plans-venv/bin/python -m pip install -r requirements-dev.txt
PATH="/tmp/helianthus-execution-plans-venv/bin:$PATH" ./scripts/validate_plans_repo.sh
```

The validation script never installs dependencies or accesses the network. If PyYAML is
not available in the selected interpreter, it exits with the setup instruction above.

Repository CI is one read-only job. It parses local YAML with duplicate-key rejection,
runs local structural/semantic validators, and runs the unit-test suite. Validators may
check IDs, known repositories, dependencies, acyclicity, Markdown mirrors, retained
contract versions, declared ordering, and hard stops.

Validators must not:

- query GitHub or another network service;
- check out another repository or PR;
- create or mutate product repositories;
- scan arbitrary implementation source to prove product behavior;
- trigger post-merge work;
- duplicate long implementation contracts as Python strings.

The execution-plans repository must not carry active admission or release manifests,
authorization or release tokens, trust-anchor validators, remote review attestations,
or post-merge proof checkers. Historical references to retired mechanisms must be
plainly labeled as archived and have no effect on issue readiness, review, or merge.

## Review policy

Review has no arbitrary round cap. Fresh exact-HEAD review continues while P0-P2
findings exist. Merge requires a fresh exact-HEAD `NO_BLOCKING_FINDINGS` verdict and all
prior P0-P2 resolved or independently validated as by design.

P3/P4 findings are triaged as fix, backlog, or by design. They are nonblocking and do not
force another round. Duplicate findings do not reopen. A disputed by-design decision gets
one independent opinion.

Reviewers stay within acceptance criteria and the declared threat model. A P2 requires a
concrete reachable scenario, wrong behavior, relevant impact, and a verifiable fix
criterion; theoretical out-of-threat-model possibilities are not P2.

## Knowledge ownership

This repository tracks planning intent. Durable public protocol, topology, runtime, and
API knowledge belongs in `Project-Helianthus/helianthus-docs-ebus` or the corresponding
future protocol documentation repository. Product behavior and its proof belong in the
code repository that owns that behavior.
