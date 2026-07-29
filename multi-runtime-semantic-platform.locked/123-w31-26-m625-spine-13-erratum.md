# W31/26 M6.25 Bounded SPINE 1.3 Erratum

Date: `2026-07-30`
Status: `Locked additive successor amendment`
Depends on: `122-w31-26-m625-implementation-state-reconciliation.md`

Current routing, readiness, and completion-token authority is
`92-m0-issue-matrix.yaml` plus generated
`107-ad-docs-02-topology-audit.md`; `106-ad-docs-02-integrity.json` is the
immutable historical M5 integrity record.

This successor record is additive. Records 100 through 122 remain historical;
`100-topology-audit.md` and `106-ad-docs-02-integrity.json` remain immutable.
The generated current topology audit at `107-ad-docs-02-topology-audit.md`
continues to project the active matrix.

## Current Control

<!-- M625_RELEASE_PROJECTION_BEGIN -->
Release-proof control: `released_chain_redeployed`
Cruise phase: `MSP-0625-S13-DOCS`
Current milestone: `MSP-0625-S13-DOCS`
LAB acceptance state: `accepted`
Selected batch: `MSP-0625-S13-DOCS`
Accepted through: `Base M6.25 LAB remains accepted after released-chain redeploy, but stable-MCP/M6.25 final closure is held by the bounded SPINE 1.3 erratum; zero promoted leaves`
<!-- M625_RELEASE_PROJECTION_END -->

The base M6.25 LAB remains accepted. Its
`lab_release_proof=released_chain_redeployed` value is not reset, weakened, or
reinterpreted. Stable-MCP/M6.25 final closure is held by this bounded erratum,
so `MSP-065-LIVE-R1` is no longer dispatchable until the new final token exists.

## Exact Issue And Token Chain

The exact issue chain is:

```text
Project-Helianthus/helianthus-docs-eebus#96
  -> Project-Helianthus/helianthus-spine-go#15
  -> Project-Helianthus/helianthus-eebus-go#23
  -> Project-Helianthus/helianthus-eebusreg#103
  -> Project-Helianthus/helianthus-ebusgateway#762
```

The exact additive completion-token chain is:

```text
MSP-0625-LAB + MSP-0625-DOCS-P
  -> MSP-0625-S13-DOCS
  -> MSP-0625-S13-SPINE
  -> MSP-0625-S13-EEBUS
  -> MSP-0625-S13-REG
  -> MSP-0625-S13-GW-LAB
  -> MSP-065-LIVE-R1
```

Every pre-existing completion-token edge remains unchanged. The only change to
an existing row is appending `MSP-0625-S13-GW-LAB` as an additional predecessor
of `MSP-065-LIVE-R1`.

## Public Baseline

The public baseline is aggregate READ evidence only:

| Operation | Declared | Success | Failure |
| --- | ---: | ---: | ---: |
| `READ` | 49 | 26 | 23 |

The public evidence commitments are:

| Evidence set | SHA-256 |
| --- | --- |
| declarations | `6ff2d9061dab29b32ed2914377aabea0b2a1dcb8c7345023f7e5870442a553b8` |
| targets | `00cd8388b5f384c0d77a56c2de59045f0514759f115c05a44544f7abbee3aa43` |
| result table | `f106bb5ba09ff7bb14230fac48113dedce152e5887d6b2a27beaf3b0998d7cf9` |

No raw identity, endpoint, target address, payload, transcript, trust material,
or restricted preimage is recorded. The hashes bind the public-safe aggregate
evidence; they do not authorize recovery of raw identity.

## Bounded Scope And Provenance

The SPINE implementation row may use only the following minimal provenance:

| Commit | Authorized provenance scope |
| --- | --- |
| `d5f89c767706ef411fc622cd6771c479b7fd1b26` | Relevant SPINE 1.3 setpoint-description, selector, HVAC relation value-type, and function-data factory corrections. |
| `a6cb0727a1509dd04454c8e8edce899f4111fb3a` | Relevant SPINE 1.3 HVAC system-function selector and operation-mode relation value-type corrections. |
| `4f986b14324a0d9ed719121b82c2621d50f58303` | Relevant HVAC system-function operation-mode selector correction only. |
| `9970150f6d81ffa06605fecddedcdf0e38174543` | Identifier value-type portion only: setpoint description `MeasurementId` and `TimeTableId` use their identifier value types. |

These commits are provenance anchors, not authorization to cherry-pick or merge
them wholesale. The bounded scope explicitly excludes:

- the `9970150` eebus:key/update-engine changes, including `eebus:"key"` tags;
- duplicate cherry-picks `9f07e2a30a0c138bbc7e13b19f61ac4981f0a68f`
  and `06d9bf07e351c268656532a0b8046c79f3797d23`;
- a wholesale merge from upstream `dev`;
- SPINE 1.4 or any other specification-version uplift.

## Preserved Surface And Safety Invariants

The exact M6.25 tool suffixes remain:

```json
["features.get","features.data.get","features.data.set","mutations.get","mutations.rollback"]
```

The erratum adds no tool, alias, namespace, v2 or legacy surface.
`candidate_ref` remains prohibited. No semantic, GraphQL, Portal, Home
Assistant, or consumer-promotion surface is introduced.

Erratum execution is READ-only. Every existing no-write stop remains
fail-closed, and this amendment authorizes no new WRITE dispatch, rollback
dispatch, or remote mutation. Owner-local raw access and public redacted output
remain separate: authorized raw facts never enter public evidence, while public
evidence contains only the aggregate counts and commitments above.

## Idempotence Contract

Reapplying this amendment creates no additional row, edge, issue, or evidence
record. It preserves every historical ID and edge, keeps the five issue rows
strictly serial, and leaves `lab_release_proof` at
`released_chain_redeployed`.

## Falsifiability Gate

This amendment fails if any old edge changes; if either old
`MSP-065-LIVE-R1` predecessor is removed or reordered; if more than the single
new final predecessor is appended; if dispatch starts anywhere other than
`MSP-0625-S13-DOCS`; if a raw identity enters public evidence; if a WRITE is
authorized; if `candidate_ref` appears as an allowed surface; or if the scope
imports excluded upstream work or SPINE 1.4.

The post-redeploy live gate also fails unless all 49 target identities bound by
the baseline target commitment are attempted as READ and receive one terminal
classification; all 26 baseline-success targets remain successful; no HVAC
description READ ends `internal` because of a factory type mismatch; and no
setpoint-description or HVAC-relation READ fails because of the superseded
scalar-versus-list or enum-versus-scaled-number model. Every remaining result
must be bound to its function and correlation and classified as a typed-empty
reply, remote rejection, unknown field, or another identified model mismatch.
A typed-empty reply is not silently promoted to successful non-empty data.
`operationModeId=2` remains unlabeled unless its nominal description is
actually read. Any WRITE, SET, rollback dispatch, or mutation probe fails the
gate.

## Coverage

Plan validation must prove the 75-row exact-ID DAG, every old edge, the exact
five-row erratum chain, the additional final predecessor, the DOCS initial and
current ready set, the exact issue references, public baseline and hashes,
bounded provenance and exclusions, unchanged tool suffixes, fail-closed
no-write behavior, public/raw separation, and byte-identical immutable
`100-topology-audit.md` and `106-ad-docs-02-integrity.json`. It must also prove
the exact 49-target terminal-result coverage, non-regression of all 26 prior
successes, removal of the identified factory/cardinality mismatch classes,
exact classification of residual errors, and the no-fabricated-label rule.
