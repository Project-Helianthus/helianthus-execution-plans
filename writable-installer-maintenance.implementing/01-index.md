# Writable Installer/Maintenance Execution Plan Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `76ba52c1c0e115e69fec268ade5d5291bb47dedae4b6c6d42649fadb14143da7`

This plan is now in `.implementing`. The canonical file was reconciled to the
implemented design on `2026-04-09`.

## Split Contract

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Chunk files remain the bounded execution artifacts from the locked baseline.
- Where chunk wording differs from current behavior, canonical decisions win.
- Drift tracking remains explicit through the canonical hash and
  `90-issue-map.md` + `91-milestone-map.md` + `99-status.md`.

## Design Reconciliation Highlights

- Controller installer fields are canonicalized as aggregated
  `installerName` / `installerPhone` (not split `*1/*2` API fields).
- Menu code entities are canonicalized in `text.py` (sensitive text entities),
  not `number.py`.
- Boiler phone write semantics are canonicalized as digit-string UX with BCD
  wire encoding.
- `internal/configwrite/` extraction is no longer a required milestone claim.

## Chunk Map

1. [`10-source-inventory-probes.md`](./10-source-inventory-probes.md)
2. [`11-gateway-semantic-graphql.md`](./11-gateway-semantic-graphql.md)
3. [`12-mcp-ha-integration.md`](./12-mcp-ha-integration.md)
4. [`13-tests-deployment-verification.md`](./13-tests-deployment-verification.md)

## Coverage Matrix

| Coverage | File |
| --- | --- |
| Source inventory and probe contract | `10-source-inventory-probes.md` |
| Gateway semantic/GraphQL/mutation contract | `11-gateway-semantic-graphql.md` |
| MCP and HA integration contract | `12-mcp-ha-integration.md` |
| Tests and deployment verification | `13-tests-deployment-verification.md` |
| Issue tracking | `90-issue-map.md` |
| Milestone tracking | `91-milestone-map.md` |
| Live status | `99-status.md` |

## Review Target

The split is acceptable only if reviewers can confirm:

- canonical contract matches current implementation,
- issue and milestone maps are aligned with merged evidence,
- residual gaps (if any) are explicit and falsifiable.

