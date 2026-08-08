#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1

python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise SystemExit(f"duplicate YAML key in {current}: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    unique_mapping,
)
root = Path(sys.argv[1])
plans = sorted(root.glob("*.*/plan.yaml"))
if not plans:
    raise SystemExit("no plan.yaml files found")
for current in plans:
    value = yaml.load(current.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if not isinstance(value, dict):
        raise SystemExit(f"{current}: root must be a mapping")
print(f"YAML valid: {len(plans)} plan files")
PY

PLAN="$ROOT/fronius-modbus-multivendor-v3-w29-26.implementing"
python3 "$PLAN/validate_plan.py" "$PLAN"
python3 -m unittest discover -s "$ROOT/tests" -p "test*.py"
