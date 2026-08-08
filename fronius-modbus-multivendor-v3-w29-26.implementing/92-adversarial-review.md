# Adversarial review policy

## Scope

Review tests this plan against its acceptance criteria and declared threat model:

- 46 issue IDs and 9 milestones remain present and unique;
- repository owners and dependencies remain correct and acyclic;
- public documentation precedes producers and producers precede consumers;
- retained contract IDs and versions do not drift;
- public/private dependency direction remains one way;
- Fronius remains the first vertical before broader SunSpec/Growatt/Huawei expansion;
- M3-03 remains a transport-neutral read-only profile boundary;
- the exact hard stop remains before `FMV3-M4-01` and all gateway work stays blocked;
- rollback remains local and compatibility-preserving.

Product-runtime correctness, implementation-source security, protocol conformance, race
behavior, API compatibility, and hardware support claims are reviewed and tested in the
repositories that own that code.

## Severity and repetition

There is no arbitrary review-round cap.

Fresh exact-HEAD review continues while any P0, P1, or P2 finding remains. Merge requires
a fresh exact-HEAD `NO_BLOCKING_FINDINGS` verdict and confirmation that every prior P0-P2
finding was resolved or independently validated as by design.

P3 and P4 findings are triaged as fix, backlog, or by design. They are nonblocking and do
not force another round. Duplicate findings do not reopen.

One independent opinion resolves a disputed by-design classification. That opinion
checks the same acceptance criteria and threat model; it does not widen scope.

## P2 quality bar

A P2 finding is valid only when it includes all of:

1. a concrete scenario reachable under the declared threat model;
2. the wrong observable behavior;
3. the relevant impact on an acceptance criterion or retained contract;
4. a verifiable criterion for the fix.

A theoretical possibility outside the threat model is not P2. A preference, optional
hardening idea, or unrelated product concern is P3/P4 or out of scope.

## Review state

Review state lives in the pull-request review system. This repository does not encode a
review epoch machine, mirror finding prose into Python/YAML, or require repeated
empty-result artifacts. The durable plan records only the review policy and accepted
architecture decisions.

## Accepted architecture decisions

Prior adversarial work established the durable decisions retained here:

- shared Modbus runtime and shared profile registry repositories;
- explicit public/private dependency direction;
- docs -> producer -> consumer ordering;
- Fronius-first vertical with minimal SunSpec before broader vendor expansion;
- evidence-qualified `STANDARD_ONLY` or `OVERLAY_REQUIRED` at M3-03;
- canonical semantics and semantic MCP before public GraphQL consumers;
- generic private eeBUS and Matter output bindings downstream of
  `PUBLIC_GRAPHQL_M2M_V1`;
- rollback local to the owning layer;
- hard stop before gateway issue `FMV3-M4-01`.

The former PR91 runtime-control design was removed. It is not an acceptance criterion and
must not be recreated as a review requirement.
