# AGENTS

This repository is the canonical home for locked Helianthus execution plans.

## Scope

Use this repository for workstreams that are:

- cross-repo
- milestone-driven
- architecture-affecting
- protocol-affecting
- API-affecting

Small one-repo bugfixes do not need a locked plan here unless the owner asks for
it explicitly.

## Discussions First

Plans do not appear in the repository before lock.

The expected flow is:

1. open a Discussion
2. attack the plan with adversarial reviews
3. add deep research when the problem is architectural, protocol-facing, or API-facing
4. promote the plan into `slug.locked/` via PR
5. rename to `slug.implementing/` when the first code PR opens
6. rename to `slug.maintenance/` when the main wave is merged

## Required Plan Contract

Every active plan directory must contain:

- `plan.yaml`
- `00-canonical.md`
- `01-index.md`
- `10-*.md`
- `90-issue-map.md`
- `91-milestone-map.md`
- `99-status.md`

Every chunk file under `10-*.md` must:

- stay below `10000` tokens on GPT-5-family and Claude tokenizers
- be reviewable in isolation
- declare `Depends on`
- declare `Scope`
- declare `Idempotence contract`
- declare `Falsifiability gate`
- declare `Coverage`

## Proof Quality

Plans should make only claims that reviewers can try to falsify.

Use:

- `Proven`
- `Hypothesis`
- `Unknown`

Do not hide uncertainty inside confident prose.

## Knowledge Capture

If a plan is implemented and produces reusable protocol, topology, runtime, or
API knowledge, that knowledge belongs in `helianthus-docs-ebus`.

The plan repo tracks execution intent. The docs repo tracks durable knowledge.
