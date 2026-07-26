# W30/26 Original Plan And Current-State Reconciliation

Date: `2026-07-26`
Status: `Locked additive reconciliation`
Amendment: `M6.25 Raw SPINE Feature Acquisition`

Current routing, readiness, and completion-token authority is `92-m0-issue-matrix.yaml` plus generated `107-ad-docs-02-topology-audit.md`; `106-ad-docs-02-integrity.json` is the immutable historical M5 integrity record.

## Provenance

The original multi-runtime plan was locked by
`Project-Helianthus/helianthus-execution-plans` PR `#57`, squash
`3f87f90365ef7f51dba1b80911b79b4ac762dad5`. Its M0-M6 history remains valid.
This record is append-only: it does not rewrite an earlier milestone, invalidate
an accepted artifact, or reset the plan.

The current-state comparison uses only public-safe plan, repository, release,
CI, binary, and aggregate-count evidence. Raw identities, restricted endpoint
details, payloads, and trust material are deliberately excluded.

## Reconciled Milestone State

| Milestone | Current classification | What the classification means |
| --- | --- | --- |
| M0-M4.5 | `complete` | Historical plan, documentation, runtime, trust, and admin gates remain accepted. |
| M5 | `complete` | The production runtime and gateway sidecar path are implemented beyond the July 18 plan snapshot. |
| M6 | `complete` | The single read-only `eebus.v1` namespace, topology, snapshots, local/raw boundary, public/redacted boundary, reconnect, and anti-leak checks exist. |
| M6.5 | `framework_complete` / `live_partial` | Recorder structure and synthetic evidence exist, but the currently observed live system is not proof of synchronized eeBUS, eBUS, and cloud value acquisition. |
| M7 | `synthetic_only` / `partial` | Candidate-fact framework exists; no live promoted leaf is established. |
| M8 | `synthetic_only` / `partial` | Synthetic coexistence/no-drift evidence exists; it is not a complete live multi-runtime run. |
| M8.5 | `synthetic_only` / `partial` | Administrative closure recorded zero promoted leaves. No leaf dossier can unlock consumers. |
| M9 | `not_started_substantively` | No GraphQL, Portal, Home Assistant, or add-on consumer work is authorized by a promoted leaf. |

## Administrative Closure Versus Live Completion

An issue, milestone, or cruise row may be administratively closed because its
framework, synthetic fixtures, or explicit no-op path completed. That closure
does not prove that the corresponding live capability exists.

For this plan:

- the historical `MSP-065`, `MSP-07`, `MSP-08`, and `MSP-085` rows remain in
  the matrix as preserved history;
- their classifications are not accepted completion states for the new live
  chain;
- zero promoted leaves is a valid administrative outcome but cannot authorize
  M9;
- live progress resumes only through the additive M6.25 chain and the explicit
  `MSP-065-LIVE-R1 -> MSP-07-LIVE-R1 -> MSP-08-LIVE-R1 ->
  MSP-085-LIVE-R1` sequence.

## Gap Requiring M6.25

Topology proves that devices, entities, features, and declared use cases are
discoverable. It does not prove that canonical typed SPINE function-data can be
read or safely mutated. The M6 surface therefore cannot supply direct values to
the synchronized recorder or candidate-fact graph.

M6.25 closes only that acquisition and bounded reversible-mutation gap. It does
not promote semantics and does not expose GraphQL, Portal, Home Assistant, or a
second API namespace.

## Forward-Only Result

The plan remains `locked`. Its current milestone is `M6.25`. The next
dispatchable row is `MSP-0625-PLAN`; after that plan record is published, the
live implementation path begins with `MSP-0625-DOCS-E`.
