# Source Address Selection Admission Locked Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `0675509fd10408c4102f15b108f8152e1fd985293f14f7f870b3bc4176bab720`

This directory contains a locked execution plan for replacing legacy join
terminology and behavior with source address selection plus validation.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk repeats the canonical hash for drift detection.
- Each chunk is reviewable in isolation and declares:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is execution-oriented, not a replacement for durable protocol docs.

## Chunk Map

1. [10-terminology-and-api-contract.md](./10-terminology-and-api-contract.md)
   defines the vocabulary replacement, source-description/priority separation,
   source table ownership, and the `helianthus-ebusgo` selector API.

2. [11-implementation-milestones.md](./11-implementation-milestones.md)
   maps the cross-repo work into milestone order and merge gates.

3. [12-validation-risks-and-live-evidence.md](./12-validation-risks-and-live-evidence.md)
   captures falsifiability gates, live-bus acceptance, and risks.

## Coverage Matrix

| Source content | Destination chunk |
| --- | --- |
| Terminology decision, source-description/priority separation, API contract, source policy | `10-terminology-and-api-contract.md` |
| Repository responsibilities, milestones, merge order | `11-implementation-milestones.md` |
| Falsifiability gates, live evidence, risks | `12-validation-risks-and-live-evidence.md` |

## Review Target

The locked plan remains falsifiable through:

- whether `SourceAddressSelector` names the behavior clearly enough;
- whether ebusgo's static source table matches the referenced docs section;
- whether source description and p0..p4 priority are separate and fully
  testable;
- whether free-use and recommended-for are separate from exact standard
  descriptions;
- whether explicit address validate-only mode plus active probe prevents
  persisted-state surprises;
- whether `0xFF -> 0x04` is handled as modulo companion derivation;
- whether gateway active-probe FSM covers the observed `0xF7` timeout failure;
- whether the public API migration matrix is enumerable and HA avoids
  healthy-empty behavior under degraded admission.
