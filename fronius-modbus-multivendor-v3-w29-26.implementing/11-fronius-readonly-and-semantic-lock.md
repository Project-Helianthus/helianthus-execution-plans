# Fronius read-only vertical and semantic promotion

## M0: repositories and public boundary

M0 retains the two public Modbus repositories, the existing public platform
repositories, and two generic private output-binding repositories. Public and private
dependency direction is documented before implementation. Repository work occurs only
through normal organization and destination-repository issues after agents read merged
`main`; this plan performs none of those actions.

## M1: shared Modbus foundation

M1 is vendor-neutral. `helianthus-modbus` owns bounded protocol types and read codecs,
the TCP endpoint runtime, the RTU implementation against the same public runtime
contract, and transport conformance/recovery tests.

Public documentation precedes implementation. The retained M1 identities are:

| Contract | Version |
|---|---:|
| `OPAQUE_RUNTIME_ACQUISITION_V1` | 1 |
| `helianthus.modbus.opaque-runtime-acquisition` | 1 |
| `published_attempt_v1` | 1 |
| `helianthus.fmv3-m1-06-conformance-report.v3` | 3 |
| `RTU_PHYSICAL_QUALIFICATION_V1` | 1 |

The code repository owns interfaces, types, lifecycle behavior, bounds, and tests for
these contracts. This repository retains names, versions, owners, and dependency order
only.

The M1 functional floor is explicit in each issue's acceptance criteria:

- protocol code admits only FC03 holding-register reads, FC04 input-register reads, and
  bounded FC2B/MEI0E device identification, keeping FC03 and FC04 provenance distinct;
- TCP has one fair bounded scheduler and transaction allocator per socket, isolates unit
  and profile state, coalesces only compatible reads, replays each dependent's exact
  logical slice, and prevents abandoned or late responses from crossing connection
  generations through bounded tombstone recovery;
- RTU shares protocol types but proves serial scheduling, CRC, silent intervals,
  abandonment, and timeout or cancellation quarantine independently;
- TCP and RTU conformance cover the complete read allowlist, malformed responses,
  exceptions, segmentation, reconnect, late-response handling, and recovery with no
  unexpected fail or xpass;
- opaque runtime acquisition and its registry consumer preserve wire-response,
  logical-view, sample, generation, normalization, and source provenance through bounded
  one-shot lifecycle, cancellation, exhaustion, and deterministic non-reconstructing
  tombstone reclamation.

RTU fixture conformance may complete without physical hardware, but RTU remains disabled
and experimental. Only `RTU_PHYSICAL_QUALIFICATION_V1` supports an enabled or supported
physical RTU claim. That condition does not block TCP-sufficient Fronius work.

## M2: profile framework

`helianthus-modbusreg` consumes the merged runtime contract and defines:

- profile and codec interfaces;
- profile catalog and deterministic detection;
- source-observation identity, coherence, and provenance;
- bounded read-only probe plans;
- sanitized fixture and replay harnesses;
- cross-profile conformance and compatibility tests.

The registry remains transport-neutral. It receives runtime observations through public
interfaces and cannot own sockets, serial ports, reconnect loops, or gateway state.

## M3: Fronius first

Fronius is the first vertical because it supplies concrete phase-1 Modbus TCP evidence.
The sequence is strict:

1. `FMV3-M3-01` publishes a provenance-qualified Fronius and SunSpec evidence packet and
   sanitized fixture manifest;
2. `FMV3-M3-02` implements only the minimal standard SunSpec slice required by that
   evidence;
3. `FMV3-M3-03` records `STANDARD_ONLY` or `OVERLAY_REQUIRED` and adds vendor code only
   when qualified evidence requires it.

`STANDARD_ONLY` means no Fronius overlay. `OVERLAY_REQUIRED` means a narrowly scoped,
read-only overlay in `helianthus-modbusreg`. In either case, Modbus TCP is evidence and
acquisition, not a production profile dependency. Fronius profile logic must remain
transport-neutral.

The completion record uses `helianthus.fmv3-m3-03-completion.v2` version 2. The owning
code repository proves the disposition with interfaces/types, golden fixtures,
conformance tests, and compatibility tests. This plan does not inspect implementation
files.

## Hard stop after M3

The active plan cycle ends when M3-03 is complete. It stops immediately before
`FMV3-M4-01`. Gateway adapter work, raw MCP, add-on configuration, live gateway smoke,
semantic promotion, and every later consumer remain blocked.

No merged documentation, status edit, validator success, or review result crosses this
stop. A later operator decision must explicitly start the next plan cycle after examining
merged code-repository evidence.

## Deferred M4 raw integration

When separately started, M4 will place one owned Modbus TCP endpoint behind the existing
protocol-agnostic gateway adapter boundary, expose bounded raw/profile MCP before
semantics, configure and recover the add-on path, run a real read-only Fronius smoke, and
publish sanitized applicability evidence. These are retained roadmap nodes, not current
work.

The public endpoint-ownership and bounded raw/profile MCP contract belongs to
`FMV3-M0-06`. It must be current before `FMV3-M4-01` or `FMV3-M4-02` merges; both code
issues carry `doc_gate`. `FMV3-M4-05` remains a separate post-smoke evidence publication.

The live smoke records `GO`, `NO_GO`, or `STOP`. `FMV3-M4-05` packages any of those
outcomes so failed or stopped work remains reviewable. The result informs explicit
GitHub triage and operator direction; it does not release or authorize an M5 issue.

## Deferred M5 semantic promotion

M5 preserves this order:

1. live evidence supports public canonical PV documentation;
2. `helianthus-ebusreg` defines protocol-independent PV IDs and compatibility rules;
3. the gateway implements candidate mapping and semantic MCP;
4. golden and live tests establish the candidate behavior;
5. `FMV3-M5-03` records the lock decision for that tested version;
6. public `PUBLIC_GRAPHQL_M2M_V1` documentation precedes GraphQL implementation;
7. Portal, Home Assistant, and add-on packaging consume the stable contract.

Raw Portal diagnostics remain bounded and separate from semantic GraphQL. Home Assistant
consumes GraphQL, not raw register or unstable MCP representations.

The semantic review also records `GO`, `NO_GO`, or `STOP`. The result preserves candidate
and review evidence for explicit GitHub triage and operator direction. It does not
release, authorize, or automatically block GraphQL, public rollout, eeBUS, or Matter
issues.

## Proof location

For every implemented node, the producer repository owns proof of behavior and the
consumer repository owns compatibility proof. Expected mechanisms include:

- public interfaces and types that express repository boundaries;
- golden protocol/profile fixtures;
- conformance and race/recovery tests where relevant;
- compatibility tests across published contract versions;
- hardware evidence only for claims that require hardware.

This plan's local validator never substitutes document text or source scanning for those
tests.
