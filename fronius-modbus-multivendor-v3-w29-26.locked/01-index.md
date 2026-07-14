# Locked package index

Canonical-SHA256: `d01dcf33f46878f30c3a627e7e037a69660d55ab8d23ee8294923261b3979ee6`

| File | Purpose |
|---|---|
| `plan.yaml` | Machine-readable decisions, milestones, risks, gates, and issue DAG |
| `00-canonical.md` | Canonical human review surface |
| `01-index.md` | Package index and canonical digest mirror |
| `10-architecture-and-repo-boundaries.md` | Layer, ownership, runtime, licensing, and import contracts |
| `11-fronius-readonly-and-semantic-lock.md` | Fronius phase 1, raw MCP, live proof, and semantic promotion |
| `12-vendor-expansion-and-private-bindings.md` | SunSpec, Growatt, Huawei, eeBUS, Matter, and EMMA deferral |
| `13-roadmap-gates-and-risks.md` | DAG interpretation, gates, recovery, risks, and stop/go rules |
| `90-issue-map.md` | Executable one-repository issue rows |
| `91-milestone-map.md` | Cross-repository grouping and critical-path view |
| `92-adversarial-review.md` | Bounded review epochs, immutable history, and active placeholders |
| `99-status.md` | Current locked and authorization state |
| `validate_plan.py` | Structural validator for this locked package |

Review order: canonical, chunks 10 through 13, issue map, milestone map, review
contract, then status. `plan.yaml` is authoritative for machine-readable topology;
`00-canonical.md` is authoritative for human-readable decisions.
