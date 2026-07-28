# W31/26 M6.25 Raw Mutation Contract Correction

Date: `2026-07-28`
Status: `Locked append-only correction`
Depends on: `MSP-0625-PLAN`

This amendment corrects the pre-release M6.25 mutation contract before
`MSP-0625-REG-MUT` RED/GREEN work. It is forward-only: amendment
`118-w30-26-m625-raw-spine-feature-acquisition.md` remains immutable history,
and this file is authoritative wherever the two conflict.

Current routing, readiness, and completion-token authority is
`92-m0-issue-matrix.yaml` plus generated
`107-ad-docs-02-topology-audit.md`; `106-ad-docs-02-integrity.json` is the
immutable historical M5 integrity record.

## Scope

The correction is limited to recovery outcome semantics, mutation interface
compatibility, and write authorization. It does not change the M6.25 DAG,
milestone boundaries, issue rows, tool names, or delivery order.

No v2 or legacy interface, alias, compatibility shim, `candidate_ref`,
semantic mapping, consumer promotion, GraphQL, Portal, Home Assistant, or
other consumer surface is introduced.

## Corrected Recovery Outcomes

After a possible send, a trustworthy full READ that verifies equality with the
canonical before-image terminates as `no_effect`.

`no_effect` means only that the verified final value equals the before-image.
It does not prove that the remote endpoint never transiently executed the
requested mutation. The terminal record therefore has:

```yaml
state: no_effect
protocol_accepted: null
observed_after: before_image
error: {code: no_effect, retriable: false} # terminal ErrorV1
outcome_evidence: # OutcomeEvidenceV1
  possible_side_effect: true
  blind_retry_forbidden: true
  last_durable_state: dispatch_intent
  recorded_at: <time>
no_effect_verification:
  relation: observed_after_equals_before
  verified: true
  equal_value_hash: <HashV1>
  verified_at: <time>
```

The exact public DTO field is
`no_effect_verification: {relation: observed_after_equals_before, verified:
true, equal_value_hash: <HashV1>, verified_at: <time>}`. The terminal envelope
must carry `ErrorV1 {code: no_effect, retriable: false}`. `OutcomeEvidenceV1`
retains `possible_side_effect: true`, `blind_retry_forbidden: true`,
`last_durable_state`, and `recorded_at`; `MutationV1.observed_after` carries
the verified before-image. Public evidence retains only permitted
classifications and commitments.

A requested-value readback after a possible send may recover to `applied`, or
to `probe_active` when a persisted probe policy applies, with
`protocol_accepted: null` only when both conditions hold:

1. durable uncertainty evidence proves that dispatch may have occurred but no
   trustworthy correlated acceptance or rejection was established; and
2. a trustworthy full READ explicitly verifies equality with the canonical
   requested value.

A trustworthy correlated protocol rejection remains `rejected`; requested
value equality cannot rewrite that correlated rejection as `applied` or
`probe_active`. A trustworthy third value is `conflict` and quarantines
writes. An unreadable readback remains `outcome_unknown`. Incomplete, stale,
or unbound evidence is untrustworthy. An untrustworthy readback remains
`outcome_unknown`.
None of these recovery paths permits blind resend.

The terminal recovery matrix is therefore:

| Evidence after possible send | Terminal/recovered state | `protocol_accepted` |
| --- | --- | --- |
| Trustworthy full READ equals before-image | `no_effect` | `null` |
| Uncertainty evidence plus trustworthy full READ equals requested value | `applied` or `probe_active` | `null` |
| Trustworthy correlated rejection | `rejected` | `false` |
| Trustworthy full READ equals a third value | `conflict` | `null` |
| Readback unreadable or untrustworthy | `outcome_unknown` | `null` |

## Runtime Interface Compatibility

The existing read-only `RawFeatureRuntimeV1` interface and existing `Runtime`
method sets remain unchanged. Mutation methods must not be added to either
interface.

Mutation capability is exposed through a separate `RawMutationRuntimeV1`
interface. An internal eebusreg coordinator owns WAL/FSM transitions, the
global writer lease, CAS/read-token checks, idempotency, constraints, probe
TTL, verified rollback, recovery, quarantine, and audit. The coordinator is
not added to either existing read-only method set.

The gateway must explicitly assert `RawMutationRuntimeV1` capability before
routing `features.data.set` or `mutations.rollback`. A missing, nil, stale, or
wrong-version mutation capability fails closed before provider/session lookup
or remote contact. Read-only runtimes remain valid implementations and do not
gain mutation authority implicitly.

## Authorization Compatibility

`WriteAuthorizationV1` is distinct from the existing read authorization type
and carries the raw-write scope. It is required for `features.data.set` and
`mutations.rollback`; read authorization cannot be widened, cast, or inferred
into write authorization.

The required write scope remains `eebus.raw.write` on the owner-authorized
`AF_UNIX` surface. `mutations.get` remains read authorization under
`eebus.raw.read`. This correction does not rename or add any MCP tool.

## Dependency Gate

```yaml
contract_gate:
  prerequisite: Project-Helianthus/helianthus-docs-eebus#78
  gated: Project-Helianthus/helianthus-eebusreg#85
  transition: before_strict_red_publication
```

`Project-Helianthus/helianthus-docs-eebus#78` is the canonical documentation
gate for this correction and must merge before
`Project-Helianthus/helianthus-eebusreg#85` proceeds beyond strict test-only
RED. This gate refines the existing `MSP-0625-DOCS-E ->
MSP-0625-REG-MUT` dependency; it adds no DAG node or edge.

## Idempotence Contract

Reapplying this amendment changes nothing once this exact correction is
present. Existing historical files, matrix rows, tool suffixes, and milestone
ordering remain byte-identical unless repository metadata regeneration
requires a canonical hash projection.

## Falsifiability Gate

The correction fails if any validator or implementation permits:

- before-image recovery without explicit trustworthy verification;
- `no_effect` without the exact `no_effect_verification` field and terminal
  non-retriable `ErrorV1`;
- `no_effect` to claim that transient execution was disproved;
- requested-value recovery without durable uncertainty evidence and verified
  equality;
- correlated rejection to become `applied` or `probe_active`;
- third-value or untrustworthy readback to avoid `conflict` or
  `outcome_unknown`, respectively;
- mutation methods on `RawFeatureRuntimeV1` or `Runtime`;
- gateway mutation routing without an asserted `RawMutationRuntimeV1`;
- read authorization to grant raw-write scope;
- `mutations.get` to require write authorization;
- any DAG, tool-name, v2/legacy, `candidate_ref`, or consumer-promotion change.

## Coverage

Plan validation must project every corrected invariant above, verify the
docs-eebus `#78` gate over eebusreg `#85`, and prove that the M6.25 DAG and
exact five tool suffixes remain unchanged.
