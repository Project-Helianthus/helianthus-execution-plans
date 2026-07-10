# MSP-02A - Draft Raw Runtime Identity Contract

Status: `prepared-not-filed`

Do not file or start this issue until these remaining predecessor gates are
accepted:

- Project-Helianthus/helianthus-execution-plans#35
- Project-Helianthus/helianthus-docs-ebus#334

Already accepted prerequisite PRs:

- Project-Helianthus/helianthus-docs-eebus#3
- Project-Helianthus/helianthus-eebusreg#3

## What

Draft the versioned raw runtime identity contract for `helianthus-eebusreg`.

## Why

The gateway needs raw eeBUS runtime identity before snapshots, trust store,
gateway sidecar, or MCP tools can be built. This issue defines identity as raw
evidence-bearing data, not as a semantic registry, not as a consumer-facing
projection, and not as a pairing/trust mutation surface.

## Acceptance Criteria

- [ ] Contract is versioned and reviewable.
- [ ] Unknown eeBUS and SPINE fields stay unknown and are carried as raw
      opaque evidence, not silently normalized.
- [ ] No public package exposes `enbility`, SHIP, SPINE, semantic, projection,
      registry, or gateway-owned types.
- [ ] Pre-M4.5 public API remains read-only plus lifecycle; no public
      `RegisterRemoteSKI`, `UnregisterRemoteSKI`, `SetPairingWindow`, trust
      store mutation, pairing-window mutation, listener, or admin operation is
      exposed.
- [ ] Raw identity redaction and masking risks are explicitly documented,
      including local SKI, remote SKI, fingerprints, stable peer identifiers,
      pairing state, and session identifiers.
- [ ] Security gate artifact proves the raw identity contract cannot leak
      unmasked stable identity through public APIs, logs, test fixtures, issue
      text, or docs.
- [ ] No semantic registry fork language appears in public API names or docs.
- [ ] Local CI passes.
- [ ] CI green.

## Dependencies

- Depends on Project-Helianthus/helianthus-execution-plans#35.
- Depends on Project-Helianthus/helianthus-docs-ebus#334.
- Depends on Project-Helianthus/helianthus-docs-eebus#3.
- Depends on Project-Helianthus/helianthus-eebusreg#3.

## Complexity And Lane

- Complexity: 6
- Lane: `GPT-5.5 high`

## Repo Serialization

This is a `helianthus-eebusreg` issue. It may start only when no other
`helianthus-eebusreg` PR is active.

## Doc Gate

Required. Canonical owner: `helianthus-docs-ebus/docs/platform`.

Code PR text must link merged canonical docs commits, not merely open docs PRs.

## Transport/Security Gates

Transport gate: none.

Security gate: required for raw identity redaction and masking boundaries.

## Rollback

Revert the raw identity contract draft. No runtime state or user data should
exist in this issue.

## Review Ledger

Review must check versioning, unknown-field handling, redaction/masking,
absence of trust mutation surface, public package boundary, and absence of
semantic registry fork language.
