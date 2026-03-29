# Stable Helianthus Instance Identity — Milestone Map

## Milestone Sequence

| Milestone | Repo | Issues | Description | Dependencies | State |
| --- | --- | --- | --- | --- | --- |
| M1 | helianthus-ebusgateway, helianthus-ha-addon | #443, #108 | Stable GUID generation, persistence, GraphQL, Zeroconf | None | merged on `main` |
| M2 | helianthus-ha-integration | #179 | Verified rediscovery rebind and reachable legacy adoption | M1 | merged on `main` |
| M3 | helianthus-docs-ebus | #233 | Durable contract publication | M1, M2 | merged on `main` |

## Parallelization

```text
M1 (gateway + add-on in parallel) ──> M2 (HA integration) ──> M3 (docs closure)
```

## Gate Requirements

- GraphQL identity and Zeroconf TXT must agree on the same GUID
- HA integration must verify identity before create/rebind
- Legacy reachable entries must migrate in place
- Restart/update/reinstall semantics must be documented

## Wave Outcome

- Live add-on persistence file: `/mnt/data/supervisor/addons/data/local_helianthus/instance_guid`
- Live GUID validated across file, GraphQL, and Zeroconf TXT: `3678381d-034e-4f6a-ab72-fce6eaa91245`
- Live HA entry migrated in place: `entry_id=01KK2FYJ7KCXCZ4A766ZPJSPE9`, `unique_id=3678381d-034e-4f6a-ab72-fce6eaa91245`
