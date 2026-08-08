# AGENTS

This repository is the human-readable planning layer for cross-repository Helianthus
work. It records architecture, issue IDs, dependencies, repository ownership, retained
contract IDs/versions, rollback intent, and hard stops.

## Boundary

- Do not implement product behavior in this repository.
- Do not use a plan merge to create or mutate repositories, issues, branches, commits,
  pull requests, deployments, or runtime state.
- Do not add post-merge jobs or product execution services.
- Do not validate a plan by querying GitHub, checking out another repository, or scanning
  arbitrary implementation source.
- Keep implementation proof in the code repository that owns the behavior.

Normal agents read the merged `main` plan, identify a ready DAG node, and then use the
normal issue/branch/PR workflow in that node's repository. Repository-local rules remain
authoritative for code work.

## Plan format

Prefer concise Markdown. Add only a small `plan.yaml` when structured IDs, dependencies,
repository boundaries, contract versions, ordering assertions, or a hard stop need local
machine validation.

An active structured plan normally contains:

- `00-canonical.md`
- `01-index.md`
- focused `10-*.md` architecture/roadmap files
- `90-issue-map.md`
- `91-milestone-map.md`
- `99-status.md`
- `plan.yaml`
- a small read-only `validate_plan.py`

Do not mirror long Markdown contracts into Python. Validators are structural/semantic:
YAML parsing and duplicate keys, unique IDs, known repositories, dependency existence,
DAG acyclicity, human-readable mirror agreement, retained contract IDs/versions, declared
ordering, repository boundaries, and hard stops.

## Review

There is no arbitrary review-round cap.

- Continue fresh exact-HEAD review while P0-P2 findings exist.
- Merge only on fresh exact-HEAD `NO_BLOCKING_FINDINGS` with all prior P0-P2 resolved or
  independently validated as by design.
- Triage P3/P4 as fix, backlog, or by design; they are nonblocking and do not force
  another round.
- Duplicate findings do not reopen.
- Give a disputed by-design decision one independent opinion.
- Keep review inside acceptance criteria and the declared threat model.
- Require every P2 to state a concrete reachable scenario, wrong behavior, relevant
  impact, and a verifiable fix criterion.
- Do not classify theoretical out-of-threat-model possibilities as P2.

## Documentation ownership

This repository owns planning intent. Reusable protocol, topology, runtime, or API
knowledge belongs in `Project-Helianthus/helianthus-docs-ebus` or the corresponding
protocol documentation repository. Interfaces, types, golden fixtures, conformance tests,
and compatibility tests belong in producer and consumer code repositories.

## Validation

Run `./scripts/validate_plans_repo.sh`. It must stay local and read-only. CI may contain
only the small read-only validation job and must have no post-merge effects.
