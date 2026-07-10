# Topology Audit

Status: `Locked`
Matrix: `92-m0-issue-matrix.yaml`
Audited: `2026-07-10`
Amendment: `AD-DOCS-01 external-only-documentation`

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
accepted = {
    "accepted",
    "accepted_partial_no_successor_unlock",
    "completed_local_no_code_acceptance",
}
ready = [
    r["id"] for r in data["issues"]
    if r.get("acceptance_state") == "ready"
    and all(by[d].get("acceptance_state") in accepted for d in r.get("predecessors", []))
]
lanes = []
for r in data["issues"]:
    c = r["complexity"]
    expected = (
        "GPT-5.3-Codex-Spark" if c in (1, 2)
        else "gpt-5.4-mini" if c in (3, 4)
        else "GPT-5.5 medium" if c == 5
        else "GPT-5.5 high" if c in (6, 7)
        else "GPT-5.5 xhigh"
    )
    if r["model_lane"] != expected:
        lanes.append((r["id"], r["model_lane"], expected))
cleanup = by["MSP-DOCS-CANDIDATE-CLEANUP"]
cleanup_ok = (
    cleanup["acceptance_state"] == "dormant_conditional"
    and cleanup.get("conditional", {}).get("initially_ready") is False
    and cleanup.get("conditional", {}).get("required_predecessor_for_normal_successors") is False
    and cleanup.get("conditional", {}).get("blocks_cross_repo_source_rows") == ["MSP-055"]
)
print(len(ids), len(set(ids)), missing, cycles, ready, lanes, cleanup_ok)
PY
```

## Result

- Row count: `43`
- Unique IDs: `43`
- Missing predecessor references: `[]`
- Cycles: `[]`
- Initial ready set: `["MSP-R00-L", "DOCS-VERIFY"]`
- Model-lane mismatches: `[]`
- Dormant conditional cleanup row with `MSP-055` cross-repo blocker:
  `MSP-DOCS-CANDIDATE-CLEANUP`

The two ready rows target different serialization groups:
`helianthus-execution-plans` and `helianthus-docs-eebus`. `MSP-R00` is already
completed locally with no code acceptance and no runtime successor unlock.
MSP-R00-L publishes only the opaque public ledger. The documentation chain then
runs API-SCHEMA -> PLATFORM -> E2 -> CLEAN before MSP-03D-R.

After MSP-036, MSP-DOCS-API-CANDIDATE is the explicit pre-merge gate for the
single MSP-055 source PR. The source PR may be prepared and pinned, but remains
unmerged until docs-eebus merges the exact-head candidate manifest and
provenance. MSP-055 then depends on that merged candidate.

`MSP-DOCS-CANDIDATE-CLEANUP` is deliberately dormant. It is not initially
ready and is not a normal required predecessor; it activates only when a
candidate expires or a source PR closes unmerged, then preempts same-repo
successors and blocks the bound `MSP-055` source merge until cleanup and a
fresh candidate cycle restore eligibility.

Historical accepted rows with no predecessors are not ready rows and do not
unlock successors. Runtime successors remain blocked until the recovery/docs
verification gates, external-only documentation cleanup, and clean-main
MSP-03D-R merge.
