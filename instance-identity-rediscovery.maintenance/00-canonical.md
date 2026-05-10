# Stable Helianthus Instance Identity & Verified Rediscovery Rebind

Revision: `v1.0-locked`
Date: `2026-03-29`
Status: `Maintenance`
Maintenance since: `2026-03-29`

Lifecycle note: the locked plan has been implemented and merged across gateway,
add-on, HA integration, and docs. `plan.yaml.wave_outcome` records the completed
main wave; `current_milestone` is maintenance.

## Summary

This plan replaces mutable endpoint coordinates as the primary Home Assistant identity with one installation-scoped stable GUID named `instanceGuid`.

The first implementation wave is intentionally narrow:

- The Home Assistant add-on generates and persists a lowercase UUIDv4 at `/data/instance_guid`.
- The gateway receives that value via `-instance-guid`, advertises it in Zeroconf TXT as `instance_guid`, and exposes it through GraphQL as `gatewayIdentity.instanceGuid`.
- The Home Assistant integration binds `config_entry.unique_id` to the verified GUID and treats `host`, `port`, `path`, and `transport` as mutable transport coordinates.
- Rediscovery may rewrite those coordinates only after GraphQL actively verifies the same GUID as the discovered TXT payload.

The goal is to solve identity drift for HA add-on deployments without introducing a generic service registry.

## 1. Goals

1. Stop using mutable Docker/LAN coordinates as canonical Helianthus identity in Home Assistant.
2. Guarantee that normal restart and add-on update with preserved `/data` keep the same instance identity.
3. Allow Zeroconf-guided rediscovery to rebind an existing HA config entry to a new host/IP/path after active GraphQL verification.
4. Keep multiple Helianthus instances on one LAN disambiguated by GUID instead of service name or address.
5. Make reinstall without restored `/data` produce a new identity and therefore a new HA instance.

## 2. Non-Goals

- No generic service registry.
- No attempt to infer identity from adapter hardware IDs.
- No attempt to guarantee automatic persistence for standalone gateway binaries launched outside the HA add-on.
- No mDNS-only rebinding path.

## 3. Canonical Contract

### 3.1 Identity Field

- Canonical identity name: `instanceGuid`
- Wire/storage format: lowercase UUIDv4

### 3.2 Persistence Owner

- Owner: `helianthus-ha-addon`
- File path: `/data/instance_guid`
- Creation policy:
  - Create on first start if missing or invalid
  - Write atomically with temp-file + rename
  - Never expose as user-editable add-on config

### 3.3 Gateway Contract

- New runtime flag: `-instance-guid <uuid>`
- GraphQL field:

```graphql
query {
  gatewayIdentity {
    instanceGuid
  }
}
```

- Zeroconf TXT additions:
  - `instance_guid=<uuid>`
  - Existing `path`, `transport`, and `version` stay in place

### 3.4 HA Contract

- `ConfigEntry.unique_id == instanceGuid`
- Stored data:
  - `instance_guid`
  - `host`
  - `port`
  - `path`
  - `transport`
  - `version` when available
- Identity is never derived from:
  - service instance name
  - mDNS hostname
  - IP address
  - adapter hardware identifiers

## 4. Discovery and Verification Flow

### 4.1 Zeroconf Parse

The HA integration parses:

- `host`
- `addresses`
- `port`
- `path`
- `transport`
- `version`
- `instance_guid`

### 4.2 Active Verification

Verification order:

1. Try GraphQL at discovered `transport://host:port/path`
2. If that fails, retry against each advertised IP address with the same `port/path`
3. Query `gatewayIdentity { instanceGuid }`
4. Accept only if:
   - GraphQL returns a valid lowercase UUIDv4
   - the value matches Zeroconf TXT `instance_guid` when discovery supplied one

### 4.3 Rebind Rules

For an existing GUID-backed config entry:

- Same GUID and same coordinates: no-op
- Same GUID and different coordinates:
  - verify the newly discovered endpoint first
  - then verify the currently stored endpoint
  - if the current endpoint no longer verifies, update the entry in place and reload
  - if both old and new endpoints verify to the same GUID, refuse automatic switching as a duplicate-GUID collision

### 4.4 Failure Rules

- Missing `instance_guid` in discovery: abort
- TXT/GraphQL mismatch: abort
- Pre-GUID gateway on new setup: fail with upgrade-required error
- Unreachable legacy entry: do not guess identity from discovery

## 5. Persistence Semantics

| Lifecycle event | `/data` preserved | Result |
| --- | --- | --- |
| Add-on restart | yes | same GUID |
| Add-on update | yes | same GUID |
| Reinstall without restore | no | new GUID |
| Restored backup including `/data/instance_guid` | yes | same GUID |

The first-wave durability guarantee is scoped to the HA add-on lifecycle.

## 6. Repo Slices

### 6.1 `helianthus-ebusgateway`

- Add `InstanceGUID` config/flag plumbing
- Validate lowercase UUIDv4 input
- Publish `instance_guid` in mDNS TXT
- Add GraphQL `gatewayIdentity.instanceGuid`
- Add unit coverage for flag parsing, GraphQL, and TXT payload

### 6.2 `helianthus-ha-addon`

- Bootstrap `/data/instance_guid` in the run script
- Regenerate only when missing or invalid
- Pass `-instance-guid` to the gateway binary
- Document restart/update/reinstall semantics

### 6.3 `helianthus-ha-integration`

- Parse Zeroconf `instance_guid`
- Verify discovery via GraphQL before create/rebind
- Make new entries GUID-keyed
- Rebind matching GUID entries in place when stored coordinates are stale
- Migrate reachable legacy `host:port` entries in place on setup
- Preserve entity/device stability by keeping `entry.entry_id`

### 6.4 `helianthus-docs-ebus`

- Publish the durable identity contract and lifecycle semantics
- Document GraphQL and Zeroconf identity surfaces

### 6.5 `helianthus-execution-plans`

- Track this work in `instance-identity-rediscovery.maintenance`

## 7. Migration Semantics

### 7.1 Existing Reachable Entries

- On next setup/reload, the integration queries `gatewayIdentity.instanceGuid` from the configured endpoint
- It updates the existing config entry in place
- `entry.entry_id` does not change

### 7.2 Existing Unreachable Entries

- They remain stale
- A newly discovered GUID-bearing gateway is treated as a new instance
- No speculative rebind is allowed

### 7.3 Duplicate GUIDs

- If two live endpoints verify to the same GUID, automatic rebinding is refused
- Operator action is required because the likely cause is cloned `/data`

## 8. Acceptance Criteria

1. First add-on start with empty `/data` creates `/data/instance_guid` exactly once.
2. Restart and add-on update with preserved `/data` keep the same GUID.
3. `/data/instance_guid`, Zeroconf TXT `instance_guid`, and GraphQL `gatewayIdentity.instanceGuid` always match.
4. New HA entries use GUID identity rather than `host:port`.
5. Verified rediscovery updates stored coordinates in place without duplicating devices/entities.
6. TXT/GraphQL mismatch never creates or rebinds an entry.
7. Two Helianthus instances on one LAN create two distinct HA entries keyed by different GUIDs.
8. Reachable legacy entries migrate in place without changing `entry.entry_id`.
9. Reinstall without restored `/data` is treated as a new instance.

## 9. Recommended Issue Order

1. `helianthus-ebusgateway`: `-instance-guid`, GraphQL identity, Zeroconf TXT
2. `helianthus-ha-addon`: persistent `/data/instance_guid` bootstrap
3. `helianthus-ha-integration`: GUID-native create + verified rediscovery rebind
4. `helianthus-ha-integration`: reachable legacy-entry adoption and migration coverage
5. `helianthus-docs-ebus`: identity contract and lifecycle docs

## 10. Rejected Alternatives

- Service name as identity: mutable and operator-facing
- Adapter hardware ID as identity: wrong layer, breaks on adapter swap
- mDNS-only rebinding: unsafe without active verification
- Generic registry: overbuilt for the failure being solved

## 11. Amendment — File-Path Migration to runtime_state.json (2026-05-10)

Per `feedback_deprecation_enrichment.md` (extend, do not rewrite):
the canonical persistence path for `instance_guid` is migrated by the
`runtime-state-w19-26.locked` plan from the standalone file
`/data/instance_guid` to a namespaced field
`/data/runtime_state.json[meta][instance_guid]` in a new gateway-owned
runtime state file.

The locked-plan invariants in §3, §4, and §8 of this canonical survive
unchanged:

- The HA add-on still owns `instance_guid` GENERATION (UUIDv4 on first
  start with empty `/data`).
- HA `config_entry.unique_id == instanceGuid` remains the rebind anchor.
- Active GraphQL verification of `gatewayIdentity.instanceGuid` on
  rediscovery is preserved.

What changes:

- The HA add-on no longer WRITES `/data/instance_guid`. Generation still
  happens add-on-side; the chosen value is passed to the gateway via the
  existing `-instance-guid` flag, and the gateway persists it eagerly
  (within the first second of startup) to
  `/data/runtime_state.json[meta][instance_guid]`. Sole writer of
  `runtime_state.json` is the gateway.
- The add-on reads `meta.instance_guid` from `runtime_state.json` at
  startup with the precedence documented in
  `runtime-state-w19-26.locked/11-decision-matrix.md` (AD09b).
- Migration is hard-cut, no read-fallback in code (operator-locked
  decision: manual deploy step). A guardrail (AD09a) prevents silent
  identity regeneration when legacy `/data/instance_guid` is detected
  alongside a missing `runtime_state.json`: the add-on emits the stable
  log token `HELIANTHUS_MIGRATION_REQUIRED`, writes a marker file
  `/data/.helianthus_migration_required`, and exits with code 1.
- On legacy/runtime mismatch (which should not occur post-migration),
  `runtime_state.json` is authoritative; legacy `/data/instance_guid` is
  treated as a post-migration audit artifact only.

Forward reference: see
[`runtime-state-w19-26.locked/00-canonical.md`](../runtime-state-w19-26.locked/00-canonical.md)
for the full schema, decision matrix, and falsifiability gate. This
canonical is not invalidated by that plan; it is extended.
