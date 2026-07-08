# eeBUS Transport Gate v0

Status: `Draft`
Applies to: M3, M5, M6, M8, and any later issue that changes SHIP/SPINE
runtime behavior, eeBUS listener behavior, eeBUS discovery, pairing, trust,
snapshot/replay, or gateway eeBUS sidecar wiring.

## Purpose

`eebus-transport-gate v0` is the eeBUS equivalent of the eBUS transport-gate
discipline. It is not T01..T88. T01..T88 remains required only when eBUS
transport or eBUS capture code changes.

This gate proves that raw eeBUS runtime behavior is bounded, observable,
replayable, and safe before any semantic or consumer work depends on it.

## Required Artifacts

Every gate run produces an artifact bundle with:

- repo, branch, commit, and issue id;
- gateway/add-on build id when applicable;
- `go version`, `go env GOVERSION GOTOOLCHAIN GOWORK`;
- module evidence for `github.com/enbility/eebus-go v0.7.0` when applicable;
- network topology and interface/subnet under test;
- trust-store path and whether credentials are disposable proof credentials or
  production credentials;
- command log or scripted harness log;
- redacted MCP or snapshot output;
- PASS/FAIL table for every required case.

## Case Matrix

| Case | Required from | PASS condition |
| --- | --- | --- |
| EEBUS-G00 disabled default | M5 | `eebus.enabled=false` opens no SHIP listener, emits no mDNS advertisement, and creates no trust files. |
| EEBUS-G01 fake peer handshake | M3 | Independent black-box fake peer completes SHIP/TLS/session setup without importing the facade under test. |
| EEBUS-G02 pairing closed | M4 | Closed pairing window refuses unknown peers and performs no trust-store write. |
| EEBUS-G03 pairing open candidate | M4 | One ephemeral candidate is held; no persistent write occurs before OOB fingerprint confirmation. |
| EEBUS-G04 pairing race | M4 | Two racing peers produce one candidate and one deterministic denial; wrong fingerprint leaves store unchanged. |
| EEBUS-G05 listener scope | M3/M5 | Listener binds only configured interface/subnet; wildcard and unexpected bridge exposure fail. |
| EEBUS-G06 mDNS positive | M3 | LAN peer outside add-on namespace can browse/resolve expected service. |
| EEBUS-G07 mDNS negative | M3 | With mDNS/Avahi/DBus disabled or pairing closed, advertisement is absent or stops after TTL. |
| EEBUS-G08 manual endpoint fallback | M3 | Manual endpoint reaches peer when discovery is unavailable. |
| EEBUS-G09 cert/SKI persistence | M3/M4 | Disposable proof credentials survive proof restart; production credentials satisfy M4 store semantics. |
| EEBUS-G10 restore/clone lock | M4 | Copied or restored `/data/eebus` cannot reach `PAIRED_TRUSTED` on another host or old generation. |
| EEBUS-G11 retry/backoff/quarantine | M4 | Repeated bad handshakes enter bounded retry/quarantine and persist across restart. |
| EEBUS-G12 snapshot capture | M6 | `snapshot.capture` returns immutable snapshot root or declared scoped snapshot. |
| EEBUS-G13 snapshot replay | M6 | Snapshot-bound reads remain byte-stable after live runtime mutation. |
| EEBUS-G14 snapshot auth/mask binding | M6 | Ref dereference requires exact runtime/contract/tool/scope/mask/auth binding. |
| EEBUS-G15 drop/expiry | M6 | `snapshot.drop` returns `dropped` or `already_gone`; descendants fail `snapshot_gone`. |
| EEBUS-G16 redaction | M4/M6 | Shareable outputs contain no PEM, key, token, full fingerprint, IP/MAC/serial, local identity, stable peer id, or pairing history. |
| EEBUS-G17 VR940f live smoke | M3 | Live VR940f discovery, pairing/session establishment, feature graph extraction, and reconnect after restart pass. |
| EEBUS-G18 coexistence no drift | M8 | Existing eBUS MCP, GraphQL, HA, and debug outputs remain unchanged with eeBUS candidate facts present. |

## Failure Rules

- Any required case failure blocks the issue.
- A failed redaction case blocks merge even if runtime behavior otherwise works.
- A same-container or same-bridge networking proof is insufficient for cases
  that require LAN-side evidence.
- Fake peer success is supporting evidence only; live VR940f smoke is required
  before gateway import.
- If an issue touches eBUS transport or creates new B509/B524/B555 capture
  paths, run the eBUS transport gate in addition to this gate.

## Minimum Issue Mapping

- MSP-03A: dependency/module evidence only; no fake-peer handshake case is
  required in the facade spike.
- MSP-03C: EEBUS-G05, G06, G07, G08, G09.
- MSP-03D: EEBUS-G01 and G17.
- MSP-04A/B/C: EEBUS-G02, G03, G04, G09, G10, G11, G16.
- MSP-05B: EEBUS-G00, G05, and disabled-default eBUS no-drift proof.
- MSP-06: EEBUS-G12, G13, G14, G15, G16.
- MSP-08: EEBUS-G18.

## Acceptance Language

The issue PR must include a compact PASS/FAIL table:

```text
eebus-transport-gate-v0
issue: <MSP-ID>
commit: <sha>
required_cases: <ids>
result: PASS|FAIL
artifacts: <paths or links>
operator_notes: <optional, non-normative>
```

Operator notes are never protocol facts and cannot promote a semantic leaf.
