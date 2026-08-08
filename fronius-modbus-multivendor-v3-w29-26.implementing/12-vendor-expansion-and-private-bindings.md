# Vendor expansion and private bindings

All work in this file is downstream of the current hard stop. The issue nodes remain in
the roadmap so ownership and dependency direction are explicit; they are not made ready
by this plan cycle.

## Expansion order

The first vertical is Fronius with the minimum required SunSpec support. Broad vendor
expansion follows only after that path and its critical public contract lane:

```text
Fronius phase 1
  -> additional SunSpec models
  -> Growatt disposition
  -> Huawei SmartLogger and S-Dongle disposition
  -> mixed-catalog conformance
```

This ordering prevents vendor-specific assumptions from defining shared runtime or
registry interfaces.

## M7 public evidence

`FMV3-M7-01` publishes separate, provenance-qualified evidence packets for SunSpec,
Growatt, and Huawei. Evidence records source applicability, device/gateway/model/software
identity, licensing, address normalization, unknowns, and the exact boundary between
standard and vendor-specific behavior.

Evidence that cannot support a profile remains a documented unsupported or unknown
disposition. It does not create code, a catalog entry, or a support claim.

## SunSpec expansion

`FMV3-M7-02` expands the minimal M3 standard slice with additional versioned SunSpec
models. Standard model packages remain manufacturer-neutral. Vendor packages may consume
standard model observations but must not redefine their wire meaning.

Rollback disables the affected profile version while leaving the shared runtime and
unrelated catalog entries intact.

## Growatt admission

`FMV3-M7-03` decides whether qualified evidence supports a Growatt profile. Admission
requires deterministic model/firmware applicability and public, reviewable fixture
provenance. A no-admission result is a valid completed disposition and adds no code or
support claim.

Rollback disables only the admitted Growatt profile. New qualified evidence may reopen a
previous no-admission decision through a new normal code-repository issue.

## Huawei admission

`FMV3-M7-04` covers SmartLogger and S-Dongle as separate evidence branches. Positive
support requires reliable gateway/model/software/version discrimination. If EMMA or
another gateway family cannot be distinguished safely, automatic eligibility stays
blocked.

No private corpus path, secret, or unlicensed artifact enters public source, fixtures,
CI, or documentation. Unsupported operations or ambiguous identity yield no admission.

Rollback disables the affected Huawei profile and returns unconfirmed fields to
`Unknown`; it does not change shared runtime contracts.

## Mixed-catalog closure

`FMV3-M7-05` closes deterministic detection, ambiguity, version compatibility, fixture
conformance, activation, and lifecycle behavior across the admitted catalog. A failed new
profile is independently disabled or pinned back without removing passing profiles.

## Generic private eeBUS binding

The private eeBUS repository is a generic output binding. It is not a Fronius product and
does not import Modbus, profile-registry internals, or gateway internals.

The order is:

1. public `PUBLIC_GRAPHQL_M2M_V1` is implemented and packaged in M5;
2. `FMV3-M6-00` publishes reusable eeBUS/SHIP/SPINE binding documentation;
3. `FMV3-M6-01` implements the private binding using only the public M2M contract;
4. `FMV3-M6-02` tests myVaillant interoperability as a lab hypothesis;
5. `FMV3-M6-03` publishes sanitized reusable findings or records `STOP`.

Private-only knowledge cannot satisfy the public documentation milestone. A failed lab
disables or reverts the private output and preserves public contracts.

## Generic private Matter binding

The Matter repository follows the same one-way dependency rule:

1. M5 packages the public M2M contract;
2. `FMV3-M8-00` publishes the public Matter binding companion;
3. `FMV3-M8-01` implements a generic private binding from exactly
   `PUBLIC_GRAPHQL_M2M_V1`;
4. `FMV3-M8-02` adds PV as the first capability slice while every Matter claim continues
   to consume `PUBLIC_GRAPHQL_M2M_V1` as its sole ingress and remains conformant to the
   locked PV contract without changing or bypassing it.

The binding rejects alternate ingress from Modbus, registry internals, gateway internals,
or undocumented network paths. Rollback disables the private capability without changing
the public API.

M8 has no dependency on M6. The two private bindings may progress independently after
their shared M5 public-contract prerequisites are satisfied.

## Public-private rule

Public repositories, tests, builds, and documentation do not depend on private artifacts.
Private repositories may package licensed implementation details, but reusable protocol,
identity, compatibility, and security knowledge is published when provenance permits.

Neither private binding can cross the hard stop or become active from a merge in this
repository.
