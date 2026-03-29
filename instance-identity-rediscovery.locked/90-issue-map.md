# Stable Helianthus Instance Identity — Issue Map

## Issue Catalog

| Lane | Repo | Milestone | Issue | PR | Status |
| --- | --- | --- | --- | --- | --- |
| GW | helianthus-ebusgateway | M1 | #443 | #444 | draft PR open, live verified |
| ADDON | helianthus-ha-addon | M1 | #108 | #109 | draft PR open, live verified |
| HA | helianthus-ha-integration | M2 | #179 | #180 | draft PR open, live verified |
| DOCS | helianthus-docs-ebus | M3 | #233 | #234 | draft PR open |
| PLAN | helianthus-execution-plans | closure | #3 | #4 | draft PR open |

## Dependency Graph

```text
gateway#443 ──────┐
                  ├── ha-integration#179
ha-addon#108 ─────┘

docs-ebus#233 accompanies M1/M2 and must merge before final release notes.
execution-plans#3 tracks locked-plan status until all repo PRs merge.
```

## Tracking Notes

- Live deploy evidence is attached in the draft PRs for gateway, add-on, HA integration, and docs.
- The HA lane subsumes both GUID-native create/rebind and reachable legacy adoption because they shipped together in PR #180.
