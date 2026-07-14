# Vendor expansion and private bindings

Canonical-SHA256: `d01dcf33f46878f30c3a627e7e037a69660d55ab8d23ee8294923261b3979ee6`

Depends on: `10-architecture-and-repo-boundaries.md`; locked public semantic contracts for private bindings; M1/M2 shared contracts and FMV3-M3-03 for profile expansion.
Scope: SunSpec, Growatt, Huawei SmartLogger/S-Dongle, EMMA deferral, generic private eeBUS and Matter outputs, and licensing direction.
Idempotence contract: Reprocessing the same evidence produces the same applicability classification; adding a profile or private capability does not duplicate repositories, alter existing canonical IDs, or change unrelated profile selection.
Falsifiability gate: Reject expansion if evidence loses branch/gateway/version identity, a profile is selected from an unconfirmed fact, EMMA semantics or a profile enters scope without admission evidence, EMMA cannot be distinguished but Huawei auto-eligibility remains possible, or a private binding uses anything except its documented public ingress.
Coverage: Decisions D02-D03, D05, D07-D10; issues M6-M8; risks R01, R04-R06, R08.

## Claim register

**Proven**

- The named operator Huawei corpus contains separate SmartLogger and S-Dongle material,
  gate/enrichment Markdown, live snapshots, and audits.
- That corpus treats v49 and v52 as parallel firmware branches with potentially different
  or deleted register definitions.

**Hypothesis**

- Shared detector and codec contracts can host all three expansion tracks without a
  vendor-specific runtime.
- Locked PV semantics can be mapped by generic private eeBUS and Matter products without
  leaking profile knowledge into those products.

**Unknown**

- Which exact Growatt and Huawei model/gateway/firmware combinations will qualify.
- EMMA applicability and semantics.
- myVaillant acceptance of the proposed eeBUS output until M6 hardware proof.

## Expansion admission

FMV3-M7-01 waits until the critical public docs lane reaches FMV3-M5-09, then serves as the
explicit public companion for M7-02, M7-03, and M7-04. M7 profile work also retains the
complete Fronius vertical at FMV3-M3-03. Before M7-01 closes, the public companion publishes
the complete Growatt candidate and admission contracts, qualified candidate facts, admission
criteria, provenance/licensing, explicit unsupported disposition, and exact code/document
mapping for both dispositions. It also inventories EMMA gateway, model, software, and
version discriminators, marking each one unavailable where reliable evidence is absent,
while keeping EMMA semantics and profile admission deferred. The
single `helianthus-modbusreg` lane is then strictly serialized: SunSpec model/version
expansion -> Growatt disposition -> Huawei -> mixed-catalog closure. FMV3-M7-03 records
`PROFILE_ADMITTED` only when bounded evidence and licensing analysis permit implementation,
or `NO_ADMISSIBLE_PROFILE` with retained evidence and explicit unsupported status. M7-03
consumes the already-merged companion. `PROFILE_ADMITTED` alone invokes RED-first fixtures
and code, with no later companion docs change. `NO_ADMISSIBLE_PROFILE` preserves the
pre-published public evidence/disposition, creates no implementation commit, catalog entry,
support claim, or later companion docs change, and still releases FMV3-M7-04 without a
conditional GO gate. There is no
same-repository profile parallelism.

SunSpec packages implement versioned standard model families and remain manufacturer
neutral. Vendor packages may reuse those standard decoders and add overlays supported by
their own evidence. Profile availability does not automatically create a canonical PV
field or consumer. Each newly proposed meaning needs live evidence and a later semantic
lock if the existing public contract does not already cover it.

FMV3-M7-02, every admitted FMV3-M7-03 profile, and FMV3-M7-04 exercise every applicable
multi-register word order, intra-word byte order, and string encoding/packing/padding case
declared by their versioned SunSpec, Growatt, or Huawei codecs. FMV3-M7-01 records source applicability for those
choices. The protocol runtime still returns uninterpreted words/bytes in received order;
only `helianthus-modbusreg` codecs compose or unpack them and record the selected codec
version and descriptor in provenance.

Fixture-only results may publish only an `experimental_opt_in` profile that is disabled by
default. Explicit operator opt-in still runs every identity, version, gateway, ambiguity,
coherence, and read-only gate and does not create a support claim. A profile becomes
`auto_eligible` only when a hardware qualification record matches its profile version,
model, gateway, firmware/software branch, and transport. Missing, mismatched, revoked, or
disabled records prevent or demote automatic activation. FMV3-M7-05 tests opt-in,
qualification, mismatch, revocation, disable, demotion, and restart lifecycle; therefore
M7 remains `hardware_conditional`.

## Huawei clean-room and version work

The operator-authored Tancabesti/wlrcs analysis and converted Markdown are inputs to an
evidence process, not normative register truth. Intake creates a neutral inventory with
source identity, provenance, permission/license status, document branch/version, target
model, gateway, software package, access, and whether a fact is documentary or live.
Exact private material paths and secrets are not copied into this package or public CI.

SmartLogger and S-Dongle maps remain separate. The implementation must rediscover and
version-gate register presence, type, scale, and access from qualified sources and
sanitized fixtures. Detection revalidates available model or MEI identity, software
package identity, gateway class, and bounded read-only discriminator probes. It does not
infer a later branch from a larger version number.

M7-01 enumerates every detector operation/PDU per candidate and admits only probes already
owned by the versioned `helianthus-modbus` allowlist: FC03, FC04, or FC2B/MEI0E Device
Identification. Unsupported operations force `NO_ADMISSIBLE_PROFILE`; modbusreg cannot
implement framing to bypass that disposition.

Before M7-01 closes, every SmartLogger and S-Dongle candidate has either a merged public,
provenance/licensing-qualified packet covering register map, codec, gateway, branch, version,
detection, and exact code/document mapping, or `NO_ADMISSIBLE_PROFILE`. Only
`PROFILE_ADMITTED` triggers RED-first code plus positive gateway/branch/version/detection/codec
fixtures. `NO_ADMISSIBLE_PROFILE` creates no implementation commit, catalog entry, or support
claim.

v49 and v52 are parallel applicability branches. A fact in one branch has no default
precedence over the other. Absence, changed type, deletion, conflicting source, failed
probe, and unconfirmed live behavior produce Unknown or unsupported status. The M7
catalog tests include branch mismatch and deleted/absent fact cases. This plan intentionally
contains no exact Huawei register claim.

EMMA semantics and profile admission remain deferred. No EMMA implementation issue or
profile package exists in this DAG. FMV3-M7-01 still inventories EMMA gateway, model,
software, and version discriminators or marks each discriminator unavailable. FMV3-M7-04
and FMV3-M7-05 then run negative fixtures for an EMMA endpoint and an insufficiently
distinguished endpoint. Each must return only `no_match` or `insufficient_evidence`, must
never activate SmartLogger or S-Dongle, and must keep Huawei automatic eligibility blocked
whenever reliable discrimination is unavailable. Future EMMA admission additionally
requires an evidence packet that identifies model/gateway, software branches, read-only
detection, register provenance, license boundary, fixtures, and hardware target.

## Generic private eeBUS binding

FMV3-M6-00 first publishes the sanitized permissive companion for reusable GraphQL ingress,
SHIP/SPINE, trust, identity, encoding, capability, PV exchange, and security knowledge.
FMV3-M6-01 carries that companion and cannot merge private protocol code before it.

Only after the complete M5 public consumer and packaged rollout may
`helianthus-eebus-binding-private` start implementation. It is a generic output product for
every future canonical device class. Its concrete semantic ingress is exactly
`PUBLIC_GRAPHQL_M2M_V1`, documented by FMV3-M5-09, implemented by FMV3-M5-05, and
packaged/tested by FMV3-M5-08 from a separately deployed external service context. It uses
that contract's noninteractive, least-privilege, bounded query/polling access over an
authenticated confidential channel with verified server identity. Plaintext external access
and untrusted server identity fail closed before credentials are sent; the contract does not
prescribe a channel mechanism.
No GraphQL subscription is assumed or invented. Its core owns deployment/configuration,
schema/contract compatibility, ingress reconnect/backoff, explicit disable,
quality/stale/unavailable propagation, minimum eeBUS SHIP/SPINE discovery, SHIP TLS and
pairing, persisted trust, reconnect, revocation/reset, disable recovery,
session/capability negotiation, output identity, and eeBUS encoding. PV is the first
adapter. No public eeBUS implementation repository is created or implied by this plan.

The repository must not import `helianthus-modbusreg`, raw Modbus types, register maps,
Fronius detection, gateway internals, or private input facts. A public semantic field that
cannot map cleanly is reported as unsupported; the binding does not redefine the public
field. A test-only RED commit must be CI-observed before implementation. Deterministic
M6-01 acceptance deploys/configures the binding against exactly the packaged contract,
tests compatible and incompatible versions, bounded polling, plaintext rejection,
untrusted-server-identity rejection, credential disable/recovery, reconnect/backoff,
capability disable, unavailable/stale inputs, then covers discovery, SHIP
TLS/pairing, trust persistence, reconnect, revocation/reset, disable recovery,
session/capability negotiation, identity, encoding, and a complete PV exchange before
hardware.

myVaillant interoperability is a separate real-lab-only hypothesis; simulator acceptance
belongs entirely to M6-01. M6-02 records exactly `GO`, `NO_GO`, or `STOP`; completion is
not progress and `GO` is the sole objective success. `GO` requires an enabled, qualified
live Fronius endpoint throughout the run and a traced observation that is available,
non-stale, and generated after the recorded lab-run start. The same observation identity
and value must traverse `PUBLIC_GRAPHQL_M2M_V1` and eeBUS into an accepted myVaillant-side
observable with matching canonical/source identity, value, unit/value semantics, quality,
source observation time, and receipt time. Replayed, synthetic, retained-cache-only,
fixture-only, simulator-only, handshake-only, or packet-only input cannot produce `GO`.
The existing identity/time/quality contract is sufficient and no new public schema field is
required. The record also includes the private binding version, advertised
capabilities, discovery, SHIP TLS/pairing, trust persistence across restart/reconnect,
revocation/reset and repair, disable recovery, sanitized result, and recovery. Fixture-only
or simulator-only qualification remains in M6-01. `NO_GO` or `STOP` retains honest evidence
but does not complete the plan objective or unlock success. No outcome adds vendor logic or
distorts the public schema. FMV3-M6-03 then publishes every reusable sanitized finding with
provenance/licensing; if required knowledge cannot be published permissively, the result is
`STOP` and no private-only interoperability or support claim is allowed.

## Generic private Matter binding

FMV3-M8-00 first publishes a sanitized permissive companion for reusable Matter ingress,
identity/capability/encoding, trust, compatibility, unavailable, recovery, and import-boundary
knowledge. `helianthus-matter-binding-private` follows the same one-way dependency rule and
generic device-class design. PV is its first conformance slice. FMV3-M8-01 depends on the
companion, which retains packaged FMV3-M5-08 ancestry, and has exactly one semantic ingress:
`PUBLIC_GRAPHQL_M2M_V1`. No second M8 ingress is permitted.

The Matter kernel uses authenticated bounded query/polling, rejects incompatible contract
versions, requires noninteractive least privilege, a confidential channel, and verified
server identity, and rejects plaintext or untrusted identity before credential use. Its
tests cover credential provision, rotation, revocation, disable, and recovery plus bounded
reconnect/backoff, explicit disable, and stale/unavailable propagation. The M8-01 security
gate rejects subscriptions and any ingress/import from `helianthus-modbus`,
`helianthus-modbusreg`, gateway internals, private upstream state, or undocumented network
paths. M8 depends on no M6 issue and remains independent of the eeBUS/myVaillant result.
Simulator tests are required. Hardware remains optional until a concrete Matter
product-support claim is proposed.

## Licensing and release direction

M0 fixes repository visibility and license before code. Public evidence and fixtures must
be redistributable or represented by independently reproducible sanitized test material.
Restricted inputs remain outside public artifacts and cannot become hidden build
dependencies. Private repositories may package licensed private protocol behavior, but
their generated outputs, tests, and CI are never prerequisites for public release.

Each profile version and private capability has an independent catalog/feature disable.
Profile qualification revocation or mismatch demotes automatic eligibility and stops new
observations without converting old data into a new sample. Rollback disables the new
profile or output while retaining shared contracts. A bad vendor profile must not force
transport rollback; a failed private lab must not force public API rollback.
