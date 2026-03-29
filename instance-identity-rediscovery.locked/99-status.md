# Stable Helianthus Instance Identity — Status

## Current State

- Plan state: locked
- Code state: code complete, live deployed, awaiting merge
- Docs state: repo-local docs shipped with code lanes; durable docs repo draft PR is open

## Live Validation Snapshot

- Add-on persisted GUID file exists at `/mnt/data/supervisor/addons/data/local_helianthus/instance_guid`
- Add-on log emitted `Using persisted stable instance GUID 3678381d-034e-4f6a-ab72-fce6eaa91245`
- Add-on log emitted `Using gateway binary override from /data/helianthus-gateway`
- GraphQL returned `gatewayIdentity.instanceGuid = 3678381d-034e-4f6a-ab72-fce6eaa91245`
- Zeroconf TXT advertised `instance_guid=3678381d-034e-4f6a-ab72-fce6eaa91245`
- HA config entry `01KK2FYJ7KCXCZ4A766ZPJSPE9` migrated in place to `unique_id=3678381d-034e-4f6a-ab72-fce6eaa91245`
- HA smoke profile passed against `http://192.168.100.4:8080/graphql`

## Open Risks

- Duplicate GUIDs caused by cloned `/data`
- Rediscovery environments where mDNS hostnames fail and only address fallback works
- Upgrade sequencing where HA integration is newer than the gateway and must surface upgrade-required errors cleanly

## History

| Date | Event |
| --- | --- |
| 2026-03-29 | Plan created and locked in `helianthus-execution-plans` |
| 2026-03-29 | Gateway/add-on/HA/docs implementation completed in local worktrees |
| 2026-03-29 | Live HA deploy verified: stable GUID persisted, exposed, and adopted in place |
| 2026-03-29 | Draft PRs opened for gateway (#444), add-on (#109), HA integration (#180), docs (#234) |
