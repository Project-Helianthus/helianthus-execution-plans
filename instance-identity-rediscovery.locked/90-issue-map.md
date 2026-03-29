# Stable Helianthus Instance Identity — Issue Map

## Issue Catalog

| Lane | Repo | Milestone | Issue | PR | Merge Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| GW | helianthus-ebusgateway | M1 | #443 | #444 | `ab22eda98ae58da13b49d452a774d26c44f846ad` | merged on `main` |
| ADDON | helianthus-ha-addon | M1 | #108 | #109 | `a547cab79a9d002a859d35edec88c012181ee02f` | merged on `main` |
| HA | helianthus-ha-integration | M2 | #179 | #180 | `7a09fc9ff335d0a1594c948bfa64be9f0d44890f` | merged on `main` |
| DOCS | helianthus-docs-ebus | M3 | #233 | #234 | `57b9844e089586692176348c346b75059b73b8c3` | merged on `main` |
| PLAN | helianthus-execution-plans | closure | #3 | #4 | via this PR | closes the plan on merge |

## Dependency Graph

```text
gateway#443 ──────┐
                  ├── ha-integration#179
ha-addon#108 ─────┘

docs-ebus#233 accompanied M1/M2 and is now merged.
execution-plans#3 records closure after all dependent repo PRs landed on `main`.
```

## Tracking Notes

- Live deploy evidence is attached in the draft PRs for gateway, add-on, HA integration, and docs.
- The HA lane subsumes both GUID-native create/rebind and reachable legacy adoption because they shipped together in PR #180.
