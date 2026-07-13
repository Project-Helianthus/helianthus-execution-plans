# AD-DOCS-02 Amendment

Status: `PASS`
Date: `2026-07-13`
Anchor: `f25d9ac7d3f25f0f45821cdff27ff968a0ef5cfb`

## Decision

AD-DOCS-02 is append-only. The mutable allowlist is `plan.yaml`, `00-*`,
`01-*`, `10-*` through `14-*`, `90-*` through `92-*`, `99-*`, validation
scripts, tests, and `105-*` through `107-*`. All other plan evidence is
protected byte-for-byte from the anchor. In particular,
`100-topology-audit.md` remains AD-DOCS-01 historical evidence and is not a
live control surface.

The live chain is serial and token-authoritative:
`MSP-DOCS-E2 -> MSP-DOCS-E2R-PLATFORM -> MSP-DOCS-E2R-PUBLISH ->
MSP-DOCS-E2R-AGGREGATE -> MSP-DOCS-CLEAN -> MSP-03D-R`.

`MSP-R00` issue/14 and `MSP-03D-G01` are forensic evidence inputs only; they
cannot mint successor tokens. Consumers recompute a post-merge token envelope
that binds producer and consumer IDs, repository, PR, base/head/merge/tree
objects, evidence-core SHA-256, prior-token digest, observation source, and
schema version.

## Rejections

Reject token replay, wrong repository, wrong base, wrong head, wrong merge,
wrong tree, moving ref, and base drift. Reject a generic predecessor edge where
a completion token is required. A consumed merge is never rolled back: the
only remediation is a forward fix.

## Routing and readiness

Future rows carry a symbolic routing contract resolved at dispatch by the
canonical resolver and policy digest; observed terminal rows carry routing
evidence only. Exact vendor/model selections are execution records, not plan
inputs. Historical readiness snapshot, logical-ready, dispatchable, and
selected-batch are distinct states.
