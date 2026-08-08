# Helianthus Execution Plans

This repository holds human-readable cross-repository plans for Helianthus. It records
architecture decisions, issue IDs, dependency graphs, repository boundaries, contract
IDs/versions, rollback intent, and explicit stop conditions.

It is not a product runtime, execution service, repository mutation service, or substitute for
code-repository issues and pull requests.

## Normal workflow

1. Discuss and review a cross-repository plan.
2. Merge the accepted human-readable plan to `main`.
3. An agent reads merged `main`.
4. The agent creates or selects the normal issue, branch, and PR in the code repository
   that owns the next DAG node.
5. The code repository proves behavior through its own interfaces/types, golden fixtures,
   conformance tests, and compatibility tests.
6. Reusable architecture or protocol knowledge is published in the public docs repo.

Merging a plan has no post-merge effect. It does not create repositories, issues,
branches, PRs, commits, deployments, or follow-up jobs.

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

## Validation

Run:

```bash
./scripts/validate_plans_repo.sh
```

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
