# Stable Helianthus Instance Identity — HA Rebind, Migration, Docs

Source: [00-canonical.md](./00-canonical.md)
Canonical-SHA256: `8ac8c738c46de9fe9173521f7dd1285ca6f2acba6c3ac45951ee4d1a8826398c`

Depends on: [10-identity-contract-and-gateway-addon.md](./10-identity-contract-and-gateway-addon.md).

Scope: Zeroconf parse of `instance_guid`, GraphQL verification before
create/rebind, GUID-backed `config_entry.unique_id`, reachable legacy-entry
adoption, and repo-local plus durable docs.

Idempotence contract: Rediscovery of unchanged coordinates must be a no-op.
Repeating legacy adoption on an already migrated entry must not create a
duplicate entry. Repeating discovery for the same GUID across stale/live
endpoints must produce the same accept/refuse decision.

## HA Tasks

1. Parse `instance_guid` from Zeroconf TXT
2. Verify discovery by querying `gatewayIdentity.instanceGuid`
3. Create new entries with `unique_id == instanceGuid`
4. Rebind stale entries in place when a matching GUID verifies at new coordinates
5. Refuse automatic switching when both old and new endpoints are live with the same GUID
6. Migrate reachable legacy entries in place on setup

## Docs Tasks

- Update `helianthus-ha-integration` architecture and README
- Update gateway README discovery/API notes
- Publish the durable contract in `helianthus-docs-ebus`

Falsifiability gate: Missing TXT `instance_guid` must abort discovery.
TXT/GraphQL mismatch must abort discovery. Reachable legacy entries must adopt a
GUID without changing `entry.entry_id`. New entries against pre-GUID gateways
must fail with an upgrade-required error.

Coverage: Pure HA integration tests for discovery parsing and GraphQL identity
verification; legacy adoption coverage at helper/setup level; operator-facing
docs for restart/update/reinstall semantics.
