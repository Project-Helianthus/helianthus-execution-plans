# AD-DOCS-02 Live Topology Audit

Anchor: `f25d9ac7d3f25f0f45821cdff27ff968a0ef5cfb`
Matrix: `92-m0-issue-matrix.yaml`

## Computed result

- Row count: `46`
- Unique IDs: `46`
- Missing completion-token references: `[]`
- Cycles: `[]`
- requires_completion_tokens: authoritative post-merge edges only.
- evidence_inputs: forensic or partial observations only.

## Readiness separation

- Historical readiness snapshot: the anchor's observed record; it is immutable.
- logical-ready: all required completion tokens validate.
- dispatchable: logical-ready plus no expiry, cleanup, or policy failure.
- selected-batch: a dispatchable row selected by the scheduler; it is not proof
  of logical readiness.

The serial chain is `MSP-DOCS-E2 -> MSP-DOCS-E2R-PLATFORM ->
MSP-DOCS-E2R-PUBLISH -> MSP-DOCS-E2R-AGGREGATE -> MSP-DOCS-CLEAN ->
MSP-03D-R`. `MSP-R00` and `MSP-03D-G01` appear only as evidence_inputs and
cannot authorize a successor token. Planned expiry blocks publication; candidate
cleanup fails closed, and once evidence is consumed remediation is forward-fix.

`100-topology-audit.md` is checked against the anchor. This 107 audit is the
live 46-row topology/readiness/routing audit.
