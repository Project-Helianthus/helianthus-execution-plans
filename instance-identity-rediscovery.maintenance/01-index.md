# Stable Helianthus Instance Identity — Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `1d501312433ef888f2447cc6fd7fb48babbb9a0f4b2fd9bd3cf398e98d3bcdf6`

This directory contains the canonical stable-identity plan plus a lossless split
into execution-sized chunks.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk repeats:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is lossless apart from deliberate dependency repetition.
- Drift detection is explicit through the canonical SHA recorded here and in each chunk.

## Chunk Map

1. [10-identity-contract-and-gateway-addon.md](./10-identity-contract-and-gateway-addon.md)
   Covers the identity contract, persistence semantics, and gateway/add-on implementation.
2. [11-ha-rebind-migration-and-docs.md](./11-ha-rebind-migration-and-docs.md)
   Covers HA discovery verification, rebind rules, legacy migration, docs, and acceptance criteria.

## Sequencing Rules

- Gateway and add-on work can proceed in parallel once the identity contract is locked.
- HA rediscovery/rebind depends on the gateway exposing GraphQL `gatewayIdentity` and Zeroconf `instance_guid`.
- Docs can land alongside code but are merge-blocking at release time.

## Coverage Matrix

| Source range | Destination chunk |
| --- | --- |
| Summary; Sections 1-5 | `10-identity-contract-and-gateway-addon.md` |
| Sections 6-10 | `11-ha-rebind-migration-and-docs.md` |
