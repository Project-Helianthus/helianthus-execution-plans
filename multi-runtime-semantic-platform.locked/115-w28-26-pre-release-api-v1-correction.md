# W28-26 Pre-Release API v1 Correction

Date: 2026-07-18
Decision: GO for one initial exact-address runtime API; NO-GO for shipping both v1 and v2 in the first release.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

## Trigger

The production prerequisite chain introduced `ConfigV2`, `NewV2`, and
`PairingPolicyV2` to preserve an earlier public source shape. Before gateway
adoption, a release audit proved that `helianthus-eebusreg` has no tag or
release and no downstream workspace consumer imports either runtime
constructor. Carrying both shapes into the first release would therefore turn
a pre-release correction into permanent API debt without protecting a real
consumer.

The source history and the earlier API publication remain evidence. They are
not rewritten or described as a released compatibility promise.

## Corrected chain

1. `MSP-05P-REG-API-V1-CLEANUP` runs after the production runtime proof.
2. The root `Config` and `New` surface becomes the exact-address contract with
   explicit state root, interface, discovery policy, remote allowlist, and
   closed pairing policy.
3. The additive v2 names and the legacy listen-port-only shape are removed.
4. The active API v1 reference and manifest are regenerated from the final
   source commit and record this pre-release correction explicitly.
5. `MSP-05A-R1` may import the runtime only after the cleanup completion token
   exists; `MSP-05B` remains downstream.

## Compatibility evidence

The cleanup must fail closed unless all of the following remain true at its
exact head: no repository tag, no GitHub release, no gateway import, and no
other known downstream module consumer. Any discovered consumer converts the
work into an explicit compatibility decision before code merge.

## Rollback

If the cleanup cannot be proven, gateway adoption remains blocked and the
unreleased additive API stays in source until a new forward correction is
accepted. No history rewrite, force push, or silent alias is allowed.

## Next ready

`MSP-05P-REG-API-V1-CLEANUP` is the sole dispatchable row. Its companion API
documentation must merge before the code change.
