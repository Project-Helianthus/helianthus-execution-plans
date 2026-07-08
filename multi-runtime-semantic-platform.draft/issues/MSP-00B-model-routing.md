# MSP-00B - Lock Model Routing Lanes

## What

Lock model routing for the eeBUS VR940f raw-first execution path to
`GPT-5.3-Codex-Spark`, `gpt-5.4-mini`, and `GPT-5.5` medium/high/xhigh.

## Why

The execution path includes protocol, security, MCP-contract, and cross-repo
consumer risks. The model map must be current and executable before assigning
work. Outdated lanes must not appear in issue bodies or reviewer instructions.

## Acceptance Criteria

- [ ] Model lanes are documented in `00-canonical.md`,
      `14-execution-roadmap-issues-and-gates.md`, and
      `92-m0-issue-matrix.yaml`.
- [ ] Complexity 1-2 maps to `GPT-5.3-Codex-Spark`.
- [ ] Complexity 3-4 maps to `gpt-5.4-mini`.
- [ ] Complexity 5 maps to `GPT-5.5 medium`.
- [ ] Complexity 6-7 maps to `GPT-5.5 high`.
- [ ] Complexity 8-10 maps to `GPT-5.5 xhigh`.
- [ ] No outdated model lane appears in the draft.
- [ ] `./scripts/validate_plans_repo.sh` passes.
- [ ] `git diff --check` passes.

## Dependencies

- MSP-00A

## Routing

- Repo: `helianthus-execution-plans`
- Complexity: 4
- Model lane: `gpt-5.4-mini`
- Review: Spark smoke plus routing consistency review

## Gates

- Doc gate: not required
- Transport gate: not required
- Security gate: not required

## Rollback

Revert the routing table changes in the plan files and matrix.
