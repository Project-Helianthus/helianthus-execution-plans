# FMV3-M5-03 Canonical PV Semantic Lock

## Decision

`GO` is recorded on 2026-08-17 for the exact tested read-only semantic surface
below. The locked candidate is `helianthus.canonical-pv/v1` as returned by MCP
tool `modbus.v1.semantic.pv.get` under `helianthus-modbus-mcp` version 1.0.

This decision records evidence and operator disposition. It is not an
authorization runtime, does not amend `plan.yaml`, and does not release Modbus
writes or consumer publication automatically. Current GitHub state and the
owning repositories remain authoritative.

## Exact Tested Release

| Component | Tested identity |
|---|---|
| Canonical contract docs | `helianthus-docs-ebus` PR #465, merge `e6feb0f847a0df9029a878850fac34f45f17599d` |
| Canonical PV registry | `helianthus-ebusreg` PR #147, merge `f8b7082b3fa4d4843315039b6d95dbf68141d596` |
| Registry dependency | `github.com/Project-Helianthus/helianthus-ebusreg v0.0.0-20260817174811-f8b7082b3fa4` |
| SunSpec registry dependency | `github.com/Project-Helianthus/helianthus-modbusreg v0.2.1` |
| Modbus transport dependency | `github.com/Project-Helianthus/helianthus-modbus v0.0.0-20260810083147-eab30aed9eb6` |
| Gateway producer | PR #836, premerge `a49b9f36dd3163e93da2ec90617ff5c26855755e`, merge `d8bdb0f66b30a30c09690935d18a887ff5c84f64` |
| Packaged add-on | PR #215, merge `a07bbc6ae7bf491d8a5c276b0bde68f1bc258bf5`, version `0.6.52` |
| Installed image | `ghcr.io/project-helianthus/helianthus-ha-addon:0.6.52`, multi-architecture digest `sha256:7ef93ea26077e9f046a162e2e18f48c741cc64a3dbe3f94b3a5828d76af3cdd8` |

The installed ARM64 image resolved through that manifest and reported gateway
merge `d8bdb0f66b30a30c09690935d18a887ff5c84f64`.

## Tested Source Observation

The live read-only qualification used profile
`sunspec.inverter.three_phase.monitoring@1.0.0`, sample `sunspec-1-2`, poll
generation 1, and deadline identity 2. The source was terminal verified and the
Fronius Gen24 float flavor matched.

The observed structural chain was:

```text
1/65 -> 113/60 -> 120/26 -> 121/30 -> 122/44 -> 123/24
     -> 160/88 -> 124/24 -> 65535/0
```

All eight model occurrences preceding the terminator were admitted by the
tested registry revision; no occurrence was retained as opaque unknown in this
sample. The profile MCP retained 18 logical source views and exact read-only
replay provenance. Raw words, wire bytes, endpoint material, serial identity,
and the generated asset reference are intentionally omitted from this public
decision record.

Profile MCP data hash was
`16fdc242384749f67153535d12262c2d4f04a127ec99f3047f4394c92234c7d9`.
It is evidence for this observation, not an authorization token.

## Canonical Projection

Capability `helianthus.pv.inverter.three_phase.telemetry.v1` was `SATISFIED`.
The semantic result contained 11 facts, all `AVAILABLE`, `GOOD`, and `FRESH`:

| Canonical fact | Dimensions | Unit |
|---|---|---|
| `pv.ac.current` | `phase=L1`, `phase=L2`, `phase=L3` | `A` |
| `pv.ac.voltage.line_to_neutral` | `phase=L1`, `phase=L2`, `phase=L3` | `V` |
| `pv.ac.power.active` | `scope=total` | `W` |
| `pv.ac.frequency` | `scope=total` | `Hz` |
| `pv.energy.active_export_total` | `scope=total` | `Wh` |
| `pv.temperature` | `sensor_id=cabinet` | `Cel` |
| `pv.operating.state` | `scope=total` | `1`; value `OPERATING` in this sample |

Projection accounting was closed: 14 requested source outputs produced 14
projection rows, of which 11 were `MAPPED` and three were `WITHHELD`. The
withheld outputs were `inverter.ac.current.total`, `inverter.events.1`, and
`inverter.events.2`; this lock does not imply canonical support for them.

The source wall-clock state was `UNAVAILABLE`. This does not conflict with the
11 `FRESH` facts: canonical lifecycle policy uses monotonic local receipt time
for freshness and expiry, and source time does not drive expiry. The semantic
payload preserved source validity as `terminal_verified` and reported:

- source protocol `sunspec_modbus`;
- source profile version `1.0.0`;
- source registry reference
  `sha256:e21d5d4914fba2249c68cc147243c22f89cc9e1f2be71e4565a3950f31e94750`;
- source observation reference
  `sha256:69b5c7d65210f63d9d6faa83fe3f9595fc5242bd3ddf36c0c06e7adc33f845f4`;
- evidence reference
  `sha256:7247374b35bb70e6a60fcb95af499541a030b77d6b6e9fb6edde30e0a66ae142`.

`produced_at` and MCP `data_timestamp` were both
`2026-08-17T19:22:35.7287976Z`. Semantic MCP data hash was
`0ad7a3fa4e9ed19113cca9a98e6d15e444d5663322edf277136db6b697c5ed84`.

## Golden And Live Results

The gateway producer completed RED-first mapping and MCP tests, focused race
tests, full Go race, Portal 43/43, repository Python suites
168+6+9+7+6+2, lint with zero findings, GitHub terminology/build/test/lint, and
fresh exact-HEAD review before squash merge. Deterministic serialization had a
dedicated corrective RED before the final GREEN.

The add-on release completed wrapper 4/4, Modbus 26/26, parity 3/3,
rollout/post-parity/private-IP checks, five architecture builds, syntax,
CodeQL, and fresh exact-HEAD review before squash merge and publication.

On the installed 0.6.52 runtime:

- startup qualification returned `decision=GO`, `outcome=qualified`,
  `category=registry_match`, attempts 1, without recovery;
- two independent semantic reads of the same profile/sample returned
  byte-identical payloads; their serialized payload SHA-256 was
  `400861d9943cbc3a2148665d7f6298bcbfd86067a471cc6811cde4f67dc01879`;
- semantic consistency mode was `RETAINED_CANONICAL_OBSERVATION`;
- semantic output contained no endpoint, raw words, or wire-response bytes;
- the raw/profile MCP surface remained available for separate bounded
  diagnostic replay;
- `ebus.v1.runtime.status.get` remained `running` and
  `eebus.v1.runtime.status.get` remained `ready` after deployment.

No Modbus write function or inverter configuration mutation was used.

## Compatibility And Boundary

This lock applies only to the exact contract/tool/profile versions above.
Consumers may rely on canonical IDs, dimensions, units, quality, freshness,
availability, provenance references, closed projection accounting, and
deterministic replay. They must not depend on source register layout, Fronius
flavor details, raw MCP payloads, generated asset-reference format, or the
three withheld outputs.

A producer update under the same V1 contract may change source mappings only
when every emitted fact, enum, unit, dimension, and capability-pack member is
already defined by the closed V1 catalog and its meaning and accounting remain
unchanged. Any added fact, enum, unit, dimension, or required pack member needs
a new contract or capability-pack ID and a new lock decision. A breaking
identity, lifecycle, or provenance change has the same requirement.
Source/profile failure returns canonical stale or unavailable state through
registry-owned policy; it must not silently substitute a newer sample for
replay of an older sample identity.

GraphQL, Portal, Home Assistant, private eeBUS, and private Matter publication
remain downstream work. This record does not expose or implement those
surfaces.

## Operator Disposition And Rollback

The operator authorized continued Modbus execution on cruise control and
explicitly directed that draft PR #94 and `helianthus-semreg` be ignored for
this lane. The disposition for this exact semantic MCP version is therefore
`GO`.

Rollback is to disable or remove the unpublished mapping while preserving raw
Modbus/profile MCP and the published canonical IDs, or to return affected facts
as unavailable under the V1 lifecycle. A later incompatible correction must be
published under a compatible successor and reviewed as a new lock decision.
