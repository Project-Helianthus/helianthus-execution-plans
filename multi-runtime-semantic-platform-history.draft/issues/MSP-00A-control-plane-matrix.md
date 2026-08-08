# MSP-00A - Create M0 Issue Matrix And Control-Plane Fields

## What

Create the machine-readable M0 issue matrix for the eeBUS VR940f raw-first
execution path.

## Why

The plan forbids runtime implementation until every planned issue has
complexity, model lane, repo ownership, predecessor edges, doc owner, gate
requirements, rollback, and review ledger fields. This prevents high-risk
protocol/security work from starting as an underspecified milestone.

## Acceptance Criteria

- [ ] `92-m0-issue-matrix.yaml` exists and parses as YAML.
- [ ] Every issue row contains: id, repo, milestone, complexity, model lane,
      assigned route, predecessors, repo serialization group, doc owner,
      doc-gate, transport gate, security gate, rollback ledger, review ledger,
      and acceptance list.
- [ ] Complexity values match the declared model lane.
- [ ] Predecessor edges enforce one active PR per repo.
- [ ] Hard blockers are listed for runtime import, MCP v1, and consumer work.
- [ ] `./scripts/validate_plans_repo.sh` passes.
- [ ] `git diff --check` passes.

## Dependencies

None.

## Routing

- Repo: `helianthus-execution-plans`
- Complexity: 3
- Model lane: `gpt-5.4-mini`
- Review: Spark smoke plus docs/control-plane review

## Gates

- Doc gate: not required
- Transport gate: not required
- Security gate: not required

## Rollback

Revert the local control-plane matrix and remove references from the split
index/status files.
