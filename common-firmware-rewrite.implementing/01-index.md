# Common eBUS Adapter Firmware Rewrite — Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Revision: `v2.0-testing-first` (replaces v1.0-initial)

This directory contains the canonical common firmware rewrite plan plus a
lossless execution-oriented split into sub-10k-token chunks.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk must stay below `10000` tokens on both the GPT-5-family tokenizer
  and the Claude tokenizer.
- Each chunk must be reviewable in isolation and repeat:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is lossless: source content is mapped once to a chunk, except for
  intentional dependency repetition needed for isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical
  hash of `00-canonical.md`.

## Sequencing Rules

- The default milestone order is `T0 -> M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M9`.
- T0 has no dependencies and must complete before M0 begins.
- M0 tracks are parallelizable across families (v5/C6 pin validation, v3.x RE, ESERA RE).
- M2 per-family skeletons are parallelizable after M1.
- M3-M4 per-family are parallelizable after respective M2.
- M5 depends on M4 and compute proofs. v3.x is EXEMPT from M5.
- M6 depends on M3 (all families) for harness integration.
- M7 depends on M6.
- M8 is a parallel optional track, depends on M5 for eligible families.
- M9 depends on M7 (and M8 if pursued).

## Chunk Map

1. [`10-testing-first-philosophy-decisions.md`](./10-testing-first-philosophy-decisions.md)
   Covers testing-first philosophy (scope derivation, proof classes, lock/de-scope criteria, instrumentation) and adversarially locked decisions (11 decisions including 3 new).
2. [`11-tinyebus-adjudication-feature-matrix.md`](./11-tinyebus-adjudication-feature-matrix.md)
   Covers tinyebus adjudication (five roles, per-family tier assessment, minimal common subset, drift safeguards) and feature eligibility matrix (25 features × 4 families).
3. [`12-behavioural-contract-test-taxonomy.md`](./12-behavioural-contract-test-taxonomy.md)
   Covers common behavioural contract (preserved from v1.0 + test traceability) and full test taxonomy (13 categories: SPEC, PARSE, XPORT, TIME, ARB, SESS, RES, SOAK, FAULT, RE, XFAM, OBS, release-gate).
4. [`13-observability-per-family-hals.md`](./13-observability-per-family-hals.md)
   Covers deterministic observability contract (mandatory/optional counters, event markers, ring buffers, timing/memory budgets) and per-family HAL additions.
5. [`14-multi-client-security-stress-framework.md`](./14-multi-client-security-stress-framework.md)
   Covers multi-client policy (preserved), security/safety (preserved), stress-test variant matrix (13 axes, variant ID scheme), and testing-drives-feature-set decision framework (10 rules).
6. [`15-milestones-t0-m9.md`](./15-milestones-t0-m9.md)
   Covers revised milestone plan: T0 (new) + M0-M9 (tightened) with test-before-code enforcement.
7. [`16-doc-gate.md`](./16-doc-gate.md)
   Covers mega doc-gate list (30 entries across 4 categories: testing foundation, hardware/protocol, contract/policy, implementation).
8. [`17-adversarial-self-attack-assumptions.md`](./17-adversarial-self-attack-assumptions.md)
   Covers adversarial self-attack (10 attacks on the plan itself) and assumptions/defaults/out-of-scope (expanded from v1.0).

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Section 1 (Testing-First Philosophy); Section 2 (Adversarially Locked Decisions) | `10-testing-first-philosophy-decisions.md` |
| Section 3 (tinyebus Adjudication); Section 4 (Feature Eligibility Matrix) | `11-tinyebus-adjudication-feature-matrix.md` |
| Section 5 (Common Behavioural Contract); Section 6 (Test Taxonomy) | `12-behavioural-contract-test-taxonomy.md` |
| Section 7 (Deterministic Observability Contract); Section 8 (Per-Family HALs) | `13-observability-per-family-hals.md` |
| Section 9 (Multi-Client); Section 10 (Security/Safety); Section 11 (Stress-Test Matrix); Section 12 (Testing Framework) | `14-multi-client-security-stress-framework.md` |
| Section 13 (Revised Milestones T0-M9) | `15-milestones-t0-m9.md` |
| Section 14 (Mega Doc-Gate) | `16-doc-gate.md` |
| Section 15 (Adversarial Self-Attack); Section 16 (Assumptions, Defaults, Out of Scope) | `17-adversarial-self-attack-assumptions.md` |

## Review Target

The split is acceptable only if adversarial review can confirm, for every chunk:

- self-contained execution scope
- explicit upstream dependencies
- idempotent rerun semantics
- falsifiable acceptance language
- no material contract loss relative to the canonical source
