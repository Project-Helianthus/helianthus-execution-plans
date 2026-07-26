# W30/26 M6.25 Raw SPINE Feature Acquisition

Date: `2026-07-26`
Status: `Locked additive contract`
Depends on: `MSP-06`

Current routing, readiness, and completion-token authority is
`92-m0-issue-matrix.yaml` plus generated
`107-ad-docs-02-topology-audit.md`; `106-ad-docs-02-integrity.json` is the
immutable historical M5 integrity record.

## Scope And Definitions

M6.25 adds raw SPINE feature-data acquisition and bounded reversible mutation
between the completed topology surface and the live evidence/candidate chain.

The following definitions are frozen:

- topology is capability metadata; topology is not data acquisition;
- `raw` means canonical typed SPINE function-data represented by the public
  protocol types;
- `raw` never means arbitrary SHIP/SPINE frames, headers, trust bytes, packet
  captures, or transport transcripts;
- M6.25 supports full `READ` and full `WRITE` only;
- partial reads/writes, selectors, `filterDelete`, and invoke operations are
  rejected before remote contact;
- `helianthus-ship-go` is unchanged.

No semantic mapping or consumer surface is added. M6.25 exposes no GraphQL,
Portal, Home Assistant, candidate reference, alias, v2 namespace, or semantic
registry leaf.

## Frozen Component Path

The only command path is:

```text
MCP
  -> gateway EEBusCommandRouter
  -> eebusreg RawFeatureRuntimeV1 and mutation coordinator
  -> eebus-go exact feature executor
  -> spine-go correlated round-trip
  -> existing SHIP session
```

Each boundary owns a separate responsibility:

| Boundary | Responsibility |
| --- | --- |
| MCP | Shape validation, scope validation, authentication, stable envelopes, and zero-contact denial. |
| Gateway `EEBusCommandRouter` | Single command entry point, runtime selection, and policy handoff; no direct entity-adapter write. |
| `RawFeatureRuntimeV1` | Versioned DTOs and exact typed feature-data operations. |
| eebusreg coordinator | Durable epochs/generations, WAL/FSM, writer lease, CAS, idempotency, constraints, and audit. |
| eebus-go | Exact feature/function selection and full READ/WRITE request construction. |
| spine-go | One atomic correlated request/reply primitive. |
| Existing SHIP | Existing encrypted session transport, unchanged by M6.25. |

## spine-go Atomic Correlated Round-Trip

`helianthus-spine-go` adds one context-aware atomic round-trip primitive. It
must:

1. allocate a connection-generation-bound monotonic correlation key and
   register the reply callback before send;
2. reject duplicate in-flight keys and never reuse a retired key within a
   connection generation;
3. send only after callback registration succeeds;
4. complete exactly once on reply, send failure, timeout, or cancellation;
5. remove the callback on every terminal path;
6. tolerate a synchronous reply delivered during the send call;
7. retain a bounded tombstone through the connection generation so a late
   reply after timeout/cancellation cannot complete an ABA successor request;
8. expose bounded in-flight accounting and pass race tests.

The synchronous-reply test must fail if registration occurs after send. Cleanup
tests must prove the callback table returns to its prior size after success,
send failure, timeout, cancellation, disconnect, and malformed/remote-error
reply. An ABA test must deliver a late reply after timeout and cleanup, attempt
key reuse, and prove that neither the retired nor a newer request completes
from that reply.

## eebusreg Runtime Authority

eebusreg owns the durable command contract:

- `runtime_epoch` is durable and changes whenever persisted runtime identity or
  trust binding is replaced, repaired, or reset;
- `connection_generation` is monotonic within a runtime epoch and changes on
  each newly admitted live SPINE connection;
- every read token and mutation binds both values plus target device, entity,
  feature, function, canonical request shape, principal class, and mask tier;
- a mismatch discovered before dispatch returns a session/CAS error with zero
  remote frames;
- DTOs are versioned under `RawFeatureRuntimeV1`;
- one global runtime writer lease serializes all M6.25 writes and rollbacks;
- reads may be concurrent subject to bounded round-trip capacity;
- the durable WAL and mutation FSM are written and synced before the
  corresponding remote side effect;
- audit records contain public-safe classifications and JCS commitments, never
  restricted preimages.

The read result carries a one-use or explicitly reusable `read_token` according
to the function profile. A write requires the token. Under the global writer
lease, the coordinator performs a fresh full READ and compares its canonical
value hash with the token's before-image immediately before recording
`dispatch_intent`; a remote conditional WRITE may replace this guard only when
it provides equivalent atomic comparison. The token is rejected when the
epoch, generation, target, function, value hash, principal, tool, expiry, or
fresh current value differs. A stale binding fails before runtime/session
contact; a current-value mismatch may perform the guard READ but emits zero
WRITE frames.

## MCP Contract

The unreleased namespace remains exactly `eebus.v1`. The M6.25 tool suffix set
is exactly:

- `features.get`
- `features.data.get`
- `features.data.set`
- `mutations.get`
- `mutations.rollback`

The corresponding registered names are those five suffixes under
`eebus.v1`; no alias or compatibility endpoint is permitted.

`features.get` returns feature/function metadata and declared possible
operations. `features.data.get` performs full typed READ and returns the
canonical data plus a bound read token. `features.data.set` submits one full
typed WRITE under the durable mutation FSM. `mutations.get` returns durable
state and public-safe audit classifications. `mutations.rollback` requests the
same verified rollback path used by probe-TTL expiry.

## Authorization And Contact Order

Scopes are:

- `eebus.raw.read` for feature/function discovery, data reads, and mutation
  status;
- `eebus.raw.write` for data writes and rollback.

Write scope is accepted only on the owner-authorized `AF_UNIX` surface. A public
or LAN request is denied after parse/tool-shape/scope validation and before
provider lookup, gateway routing, runtime selection, connection lookup, or
remote contact. Tests instrument every downstream boundary and require zero
calls and zero frames.

The local/raw surface may return authorized typed function-data. Public
surfaces remain redacted. No tier returns private keys, tokens, trust-store
bytes, arbitrary frames, restricted identifiers, or payload transcripts.

## Constraints And Changeability

A write is admissible only when:

- the function declares full `WRITE`;
- the target is changeable under the current feature profile;
- the requested typed value satisfies every known enum, range, step, unit,
  cardinality, and cross-field constraint;
- the target is in the lab-safe allowlist and the global writer lease is held;
- the read token, runtime epoch, and connection generation still match;
- a rollback before-image exists and is representable as a full WRITE;
- heating, DHW, bus, and runtime safety predicates are green.

`constraints_unknown` fails closed by default. It is allowed only for an
explicit versioned lab profile entry that binds the exact target/function,
permitted typed values or bounds, probe TTL, safety predicates, and rollback
shape. A generic wildcard, device-family inference, or sibling-feature
inheritance is forbidden.

## Idempotency And Concurrent Writers

The idempotency identity is:

```text
(runtime_epoch, principal, tool, idempotency_key)
```

The durable record also binds the canonical request JCS hash. Reuse with the
same hash returns the original mutation identity/state without a second frame.
Reuse with a different hash is a conflict. Idempotency does not cross runtime
epochs or principals.

Only one write or rollback may own the global runtime writer lease. Concurrent
writers either observe the same idempotent mutation or receive a deterministic
busy/conflict result. They never queue unboundedly and never interleave frames.

## Durable Mutation FSM

The durable states and legal meaning are:

| State | Meaning |
| --- | --- |
| `prepared` | Request, before-image, read token, constraints decision, rollback data, deadline, and JCS commitments are durable; no frame sent. |
| `dispatch_intent` | The WAL records that a WRITE may be sent; this state is durable before send. |
| `reply_observed` | A correlated success reply was observed; this is not proof that the value applied. |
| `verify_pending` | A full READ-after-WRITE is required. |
| `applied` | The verified readback equals the requested canonical typed value. |
| `probe_active` | The applied value is under a persisted probe TTL and must be rolled back by deadline. |
| `rollback_intent` | Rollback ownership and expected current value are durable; no rollback frame sent yet. |
| `rollback_dispatch_intent` | A rollback WRITE may have been sent. |
| `rollback_reply_observed` | A correlated rollback reply was observed; restoration is not yet proven. |
| `rollback_verify_pending` | A full READ-after-rollback is required. |
| `rolled_back` | Verified readback equals the original canonical before-image. |
| `outcome_unknown` | A send may have occurred but no trustworthy final observation exists. Blind retry is forbidden. |
| `conflict` | Observed data matches neither the expected current value nor the permitted convergence target. |
| `failed_no_contact` | Validation, authorization, lease, CAS, session, or send setup failed before any frame. |
| `rejected` | The remote returned a correlated rejection and readback confirms no accepted effect. |

Every transition is append-only, synced, and audit-linked. `reply_observed` and
`rollback_reply_observed` can never transition directly to `applied` or
`rolled_back`; a verified full READ is mandatory. A successful send or ACK
alone is never `applied`.

`conflict` quarantines all writes for the runtime. Reads and mutation status
remain available. Only an owner-authorized recovery that proves a coherent
current value may clear quarantine.

## Crash And Restart Recovery

Crash injection is required after every durable transition. Recovery follows
these rules:

- `prepared` or `failed_no_contact`: emit no frame; resume only through a fresh
  binding/lease check;
- `rollback_intent`: reacquire the global writer lease, bind the current
  runtime epoch and connection generation, and perform a full READ; dispatch
  rollback only when the observed value still equals the expected requested
  value, treat an already-restored before-image as `rolled_back`, and enter
  `conflict` for any third value;
- `dispatch_intent`, `rollback_dispatch_intent`, timeout, cancellation, or
  disconnect after possible send: enter `outcome_unknown`;
- `reply_observed` or `verify_pending`: perform readback, never resend blindly;
- `applied` or `probe_active`: re-arm the persisted probe deadline;
- expired `probe_active`: begin rollback immediately after identity and
  readback convergence checks;
- `rollback_reply_observed` or `rollback_verify_pending`: verify restoration,
  never resend blindly;
- `rolled_back`, `rejected`, and `failed_no_contact`: remain terminal;
- any unexpected value enters `conflict` and quarantines writes.

An original `connection_generation` is not silently reused after reconnect.
Recovery may bind the new generation only after a full READ proves that the
same canonical target currently equals either the before-image or requested
value. Before-image means no effect and may terminate as rejected/no-effect;
requested value resumes verification or rollback; any third value is conflict.
This rule provides `outcome_unknown` convergence without duplicate writes.

Probe-TTL rollback survives restart. The persisted absolute deadline is
authoritative. If rollback cannot be verified before its bounded recovery
deadline, the runtime remains quarantined and reports conflict/outcome-unknown;
it never reports success from an ACK.

## JCS And Audit Commitments

RFC 8785/JCS canonical JSON is used for request, before-image, requested value,
observed value, rollback value, and transition commitments. Non-finite numbers
and negative zero are forbidden; exact decimals and unsafe-range integers are
strings. Each transition links the prior transition hash. Public evidence may
publish only the schema, classifications, aggregate results, and commitments,
not restricted preimages.

`MSP-085-LIVE-R1` mints a completion token whose JCS-hashed claim binds the
milestone id, positive integer `promoted_leaf_count`, promotion dossier root,
and evidence root. The token carries the claim digest. Missing, malformed,
zero, negative, non-integer, or digest-mismatched counts cannot satisfy any M9
unlock predicate.

## DAG

```text
MSP-06
  -> MSP-0625-PLAN
  -> MSP-0625-DOCS-E
       -> MSP-0625-SPINE
            -> MSP-0625-EEBUS
                 -> MSP-0625-REG-EXEC
                      -> MSP-0625-REG-MUT
                           -> MSP-0625-GW-ROUTER
                                -> MSP-0625-GW-MCP
                                     -> MSP-0625-LAB
       -> MSP-0625-DOCS-P

MSP-0625-LAB + MSP-0625-DOCS-P
  -> MSP-065-LIVE-R1
  -> MSP-07-LIVE-R1
  -> MSP-08-LIVE-R1
  -> MSP-085-LIVE-R1
  -> M9 only when promoted_leaf_count > 0
```

`MSP-0625-DOCS-P` may execute after `MSP-0625-DOCS-E`. It does not block
`MSP-0625-SPINE`, but it must complete before `MSP-065-LIVE-R1`.

## Acceptance And Falsification

M6.25 is not complete unless tests falsify all of the following:

- synchronous reply during send is correlated because callback registration
  happened first;
- callbacks are cleaned up on every terminal path;
- generation-bound monotonic correlation keys and tombstones prevent ABA
  completion by late replies;
- stale CAS/read token or epoch/generation mismatch emits zero frames;
- a same-generation out-of-band value change is detected by a fresh guarded
  READ under the writer lease and emits zero WRITE frames;
- same-key/same-request idempotency emits at most one write;
- same-key/different-request is rejected;
- concurrent writers cannot interleave and only one global lease exists;
- public denial causes zero provider, router, runtime, connection, and remote
  contact;
- changeability and known constraints are enforced before dispatch;
- `constraints_unknown` succeeds only through an exact profile allowlist;
- crash after every durable transition converges under the recovery table;
- restart from `rollback_intent` performs rebind, lease, and readback before
  any rollback dispatch;
- probe TTL survives restart and forces verified rollback;
- rollback conflict quarantines all writes;
- `outcome_unknown` converges by readback without blind resend;
- READ-after-WRITE and READ-after-rollback are mandatory;
- JCS hashes are deterministic and transition-linked;
- raw function-data and restricted identity do not leak to public MCP,
  `ebus.v1`, semantic registry, GraphQL, Portal, or Home Assistant.

The focused architecture review for this amendment is one review of this
contract, DAG, safety model, and validator projection. It is not a repeated
multi-round planning exercise.
