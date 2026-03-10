# Helianthus Execution Plans

This repository is the canonical home for locked Helianthus execution plans.

It is not a brainstorm dump and it is not a substitute for code-repo issues.
Its job is to hold the hardened version of non-trivial workstreams after they
survive adversarial review and before, during, and after implementation.

## What Lives Here

- locked execution plans for cross-repo, milestone, architecture, protocol, and
  API workstreams
- Discussions used to attack, revise, and harden those plans before lock
- issue and milestone mappings for the target code repositories
- a validator and CI gate for plan layout, token budgets, and proof metadata

## Plan States

Plans appear in this repository only from `locked` onward.

- `Discussion`: pre-lock incubation in GitHub Discussions
- `slug.locked/`: canonical plan accepted and merged
- `slug.implementing/`: first code PR has opened in a target repository
- `slug.maintenance/`: main implementation wave is merged; only follow-ups,
  bugfixes, docs capture, and maintenance remain

Only one active directory may exist for a given slug.

## Required Layout

```text
<slug>.<state>/
  plan.yaml
  00-canonical.md
  01-index.md
  10-*.md
  90-issue-map.md
  91-milestone-map.md
  99-status.md
```

## Discussion Workflow

Discussions in this repository are the official venue for:

- adversarial planning
- multi-agent attacks and defenses
- deep research passes
- plan hardening before lock

Recommended discussion comment markers:

- `ATTACK`
- `DEFENSE`
- `RESEARCH`
- `REVISION`
- `LOCK`

Default lock threshold:

- at least 2 independent adversarial passes
- at least 1 deep research pass for architecture, protocol, or API work

## Validation

Run:

```bash
./scripts/validate_plans_repo.sh
```

The validator checks:

- plan directory layout
- single active state per slug
- `plan.yaml` consistency
- canonical hash drift
- required chunk headers
- token budgets below `10000` for GPT-5-family and Claude tokenizers

## Seed Plan

The repository is seeded with:

- `observe-first-bus-observability.implementing/`

This imports the active observability workstream from the existing workspace into
the new canonical plan layout.
