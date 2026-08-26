#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ACTIVE_STATES = ("locked", "implementing", "maintenance")
COMMON_FILES = (
    "00-canonical.md",
    "01-index.md",
    "90-issue-map.md",
    "91-milestone-map.md",
    "99-status.md",
    "plan.yaml",
)


class ValidationError(ValueError):
    pass


def validate_active_plan_structure(root: Path) -> int:
    plans = sorted(
        path
        for state in ACTIVE_STATES
        for path in root.glob(f"*.{state}/plan.yaml")
    )
    if not plans:
        raise ValidationError("no active plan.yaml files found")

    for plan_path in plans:
        plan_dir = plan_path.parent
        try:
            document: Any = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValidationError(f"{plan_path}: invalid YAML: {exc}") from exc
        if not isinstance(document, dict):
            raise ValidationError(f"{plan_path}: root must be a mapping")

        state = document.get("state")
        if state not in ACTIVE_STATES:
            raise ValidationError(f"{plan_path}: state must be an active lifecycle")
        if not plan_dir.name.endswith(f".{state}"):
            raise ValidationError(f"{plan_path}: state does not match directory suffix")

        slug = document.get("slug")
        if not isinstance(slug, str) or not slug:
            raise ValidationError(f"{plan_path}: slug must be a nonempty string")
        if plan_dir.name != f"{slug}.{state}":
            raise ValidationError(f"{plan_path}: slug does not match directory name")

        missing = [name for name in COMMON_FILES if not (plan_dir / name).is_file()]
        if missing:
            raise ValidationError(
                f"{plan_path}: missing common active-plan files: {', '.join(missing)}"
            )

    return len(plans)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        count = validate_active_plan_structure(root)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Active plan structure valid: {count} plan files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
