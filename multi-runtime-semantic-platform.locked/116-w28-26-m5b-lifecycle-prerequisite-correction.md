# W28-26 M5B Lifecycle-Prerequisite Correction

Date: 2026-07-18
Decision: NO-GO for direct MSP-05B; GO after one combined gateway prerequisite.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

## Trigger

The production runtime, initial exact-address API v1, and MSP-05A-R1 gateway
mapping are complete. A fresh MSP-05B architecture pre-review then found two
gateway prerequisites that must close before lifecycle ownership is safe:

- worker and helper `Fatal`/`Exit` calls can bypass deferred cleanup;
- remote SKIs are validated case-insensitively but emitted in input order and
  case instead of the canonical lowercase ascending identity.

The same review confirmed that runtime Start performs synchronous acquisition
and worker launch only. It is not a sustained-readiness signal.

## Corrected Chain

1. `MSP-05B-PLAN-R1` publishes this corrected DAG and sidecar contract.
2. `MSP-05A-R2` uses strict externally observed RED before implementation and
   exact-head GREEN after implementation to establish main as the sole
   process-exit boundary and canonicalize remote SKIs.
3. Revised `MSP-05B` may then integrate the disabled-by-default sidecar.

MSP-05A-R2 is one combined serialized gateway prerequisite because both changes
protect lifecycle construction and cleanup at the same boundary. It adds no
sidecar, socket, discovery, trust, MCP, GraphQL, semantic, or eBUS transport
behavior.

## Revised MSP-05B Contract

- Disabled configuration performs zero resolver, runtime New, Start, and
  Shutdown calls.
- Interface resolution uses `net.InterfaceByName` and accepts typed
  `*net.IPNet` or `*net.IPAddr` values only; tests also reject an unsupported
  `net.Addr` implementation.
- The selected interface zone is attached only to IPv6 link-local addresses;
  IPv4 and global IPv6 remain unzoned.
- Runtime New or Start failure aborts gateway startup. Every constructed
  runtime is shut down exactly once.
- A named run result uses `errors.Join` to combine Shutdown failure with any
  existing run error, including later eBUS or HTTP startup failure. Lifecycle
  tests prove `errors.Is` reaches both causes.
- Successful Start means synchronous activation only. Sustained readiness and
  asynchronous runtime health remain outside this slice.

EEBUS-G00, EEBUS-G05, security review, and eBUS no-drift remain mandatory.
The stable transport-gate definition is unchanged.

## Rollback

MSP-05B rollback disables or removes sidecar lifecycle wiring while retaining
the already merged `helianthus-eebusreg` dependency and MSP-05A-R1/MSP-05A-R2
mapper state. Completed source history is not rewritten. After MSP-05B consumes
MSP-05A-R2, any correction is forward-only.

## Next Ready

Publication of this amendment completes `MSP-05B-PLAN-R1` and makes
`MSP-05A-R2` the sole dispatchable row.
