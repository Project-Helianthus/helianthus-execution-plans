#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1

if ! python3 -c 'import yaml' >/dev/null 2>&1; then
    echo "PyYAML is required. Follow the local setup in README.md using requirements-dev.txt." >&2
    exit 2
fi

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
plans = sorted(
    path
    for state in ("locked", "implementing", "maintenance")
    for path in root.glob(f"*.{state}/plan.yaml")
)
if not plans:
    raise SystemExit("no active plan.yaml files found")
for current in plans:
    value = yaml.load(current.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if not isinstance(value, dict):
        raise SystemExit(f"{current}: root must be a mapping")
print(f"YAML valid: {len(plans)} plan files")
PY

python3 "$ROOT/scripts/validate_active_plan_structure.py"

PLAN="$ROOT/fronius-modbus-multivendor-v3-w29-26.implementing"
python3 "$PLAN/validate_plan.py" "$PLAN"
python3 -m unittest discover -s "$ROOT/tests" -p "test*.py"
