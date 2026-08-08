# Implementing status

Plan state: `implementing`

Machine-readable inventory:

- issues: 46
- milestones: 9
- retained domain contracts: 7
- current-cycle last issue: `FMV3-M3-03`
- hard stop: immediately before `FMV3-M4-01`
- gateway work: blocked

## Current meaning

`implementing` is a lifecycle label for the cross-repository roadmap. It is not a grant
of permission and does not start work. Agents read the merged `main` plan and then use
normal issue/branch/PR workflow in the code repository that owns the selected issue.

The current cycle retains M0-M3 planning and stops after the Fronius disposition. M4-M8
remain non-executable roadmap context until a later operator decision.

## Simplified validation

The active validator is local, read-only, and structural/semantic. It checks YAML parsing
and duplicate keys, unique IDs, known repositories, dependency existence, DAG acyclicity,
Markdown mirrors, contract IDs/versions, declared order, review-policy invariants, the
M3-03 boundary, and the hard stop.

It does not query GitHub, inspect another checkout, scan arbitrary implementation source,
or cause post-merge actions. Product proof remains in code repositories through
interfaces/types, golden fixtures, conformance tests, and compatibility tests.

## Review

Review has no arbitrary round cap. Fresh exact-HEAD review continues while P0-P2 findings
exist. Merge requires `NO_BLOCKING_FINDINGS` on exact HEAD and all prior P0-P2 resolved or
independently validated as by design. P3/P4 are triaged and nonblocking; duplicates do not
reopen; one independent opinion resolves a by-design dispute.

## Stop condition

No gateway issue, branch, PR, import, code change, deployment, or add-on change is started
by this plan cycle. The first blocked node is `FMV3-M4-01`; all later gateway work remains
behind it.

Crossing the stop requires a separate operator decision after merged M1-M3 code-repository
evidence has been reviewed.
