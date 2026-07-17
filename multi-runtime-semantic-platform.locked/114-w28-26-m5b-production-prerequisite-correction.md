# W28-26 M5B Production-Prerequisite Correction

Date: 2026-07-17
Decision: NO-GO for direct MSP-05B; GO for the corrected prerequisite chain.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

## Trigger

MSP-05A completed as an inert, disabled-by-default gateway configuration scaffold. The MSP-05B preflight then inspected `helianthus-eebusreg` main at `40623a40ddd214868cc4cf2b28a73ada569d79d2` and found that enabled production construction cannot yet succeed:

- protected runtime material loading terminates with `protected runtime material provider is not installed`;
- SHIP service construction terminates with `scoped SHIP listener is unavailable`;
- the current SHIP listener binds a wildcard address and starts mDNS as part of the same startup policy;
- the M5A gateway contract permits multiple interfaces/subnets and separate certificate, key, and trust-store paths, while the current runtime v1 accepts one interface plus `StateRoot` and has no explicit bind address.

Silently ignoring, collapsing, or aliasing those fields would violate the M4.5 security freeze and transport gate G05. A disabled-only adapter that always fails when enabled would repeat M5A without advancing the runtime.

The public checkpoint is `Project-Helianthus/helianthus-execution-plans#58`, comment `5006833004`.

## Corrected chain

1. `MSP-DOCS-05P` freezes the production activation, protected-provider, listener-scope, discovery, and gateway mapping contract.
2. `MSP-05P-SHIP` adds an exact-address listener and independently gated mDNS publication while preserving the legacy constructor.
3. `MSP-05P-EEBUS` threads that policy through an additive eebus-go service constructor.
4. `MSP-05P-REG-API-V2` adds an explicit bind-address runtime API while preserving v1.
5. `MSP-05P-REG-ID` installs host-bound protected identity material and fail-closed persistence.
6. `MSP-05P-REG-RUNTIME` replaces the production stubs with real scoped construction.
7. `MSP-05A-R1` maps gateway configuration losslessly and rejects unsupported or ambiguous inputs before construction.
8. `MSP-05B` may then add the disabled-by-default sibling runtime adapter.

Every code node remains blocked by its canonical docs contract, strict RED/GREEN evidence, security gate where applicable, and `eebus-transport-gate v0` where networking or protocol behavior changes. Pairing remains closed. Default gateway behavior performs no eeBUS construction, filesystem access, goroutine, socket, or mDNS operation.

## Rollback

The amendment is control-plane only. Rollback is removal of the seven inserted prerequisite rows and restoration of the previous M5B completion tokens. No runtime, trust state, listener, or consumer surface is changed by this amendment.

## Next ready

`MSP-DOCS-05P` is the sole dispatchable row. One issue and one pull request per repository remain serialized.
