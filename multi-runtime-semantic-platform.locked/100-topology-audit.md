# Topology Audit

Status: `Locked`
Matrix: `92-m0-issue-matrix.yaml`
Audited: `2026-07-10`

## Command

```bash
python3 - <<'PY'
from pathlib import Path
import yaml
p = Path("92-m0-issue-matrix.yaml")
data = yaml.safe_load(p.read_text())
ids = [r["id"] for r in data["issues"]]
missing = [
    (r["id"], dep)
    for r in data["issues"]
    for dep in r.get("predecessors", [])
    if dep not in ids
]
by = {r["id"]: r for r in data["issues"]}
vis, cycles = {}, []
def dfs(n, stack):
    if vis.get(n) == 1:
        cycles.append(stack + [n])
        return
    if vis.get(n) == 2:
        return
    vis[n] = 1
    for dep in by[n].get("predecessors", []):
        dfs(dep, stack + [n])
    vis[n] = 2
for n in ids:
    dfs(n, [])
ready = [
    r["id"] for r in data["issues"]
    if not r.get("predecessors") and r.get("acceptance_state") == "ready"
]
print(len(ids), len(set(ids)), missing, cycles, ready)
PY
```

## Result

- Row count: `36`
- Unique IDs: `36`
- Missing predecessor references: `[]`
- Cycles: `[]`
- Initial ready set: `["MSP-R00", "DOCS-VERIFY"]`

The two ready rows target different serialization groups:
`helianthus-eebusreg` and `helianthus-docs-eebus`. Recovery mutation is
therefore preflighted against the repo it changes. The redacted ledger is
published only by downstream MSP-R00-L in execution-plans. MSP-03D-R depends
on MSP-R00-L, so recovery cannot appear complete before that public ledger is
reviewed and merged.

Historical accepted rows with no predecessors are not ready rows and do not
unlock successors. Runtime successors remain blocked until the recovery/docs
verification gates and clean-main MSP-03D-R merge.
