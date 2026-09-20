#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_plan(plan_dir: Path) -> dict[str, int]:
    plan = yaml.safe_load((plan_dir / "plan.yaml").read_text(encoding="utf-8"))
    require(isinstance(plan, dict), "plan.yaml root must be a mapping")
    require(plan.get("slug") == "software-declarative-08", "slug is invalid")
    require(plan.get("state") == "locked", "0.8 must remain locked")
    require(plan.get("release_prerequisite") == "accepted-0.7", "0.7 prerequisite is invalid")
    packages: Any = plan.get("packages")
    require(isinstance(packages, list), "packages must be a list")
    expected = ["DRIVER-EXTRACTION-01", "INT-18", "INT-22", "INT-23", "INT-24"]
    require([package.get("id") for package in packages] == expected, "0.8 package IDs are invalid")
    for package in packages:
        require(package.get("release") == "0.8", "0.8 package release is invalid")
    require(packages[1].get("depends_on") == ["DRIVER-EXTRACTION-01"], "INT-18 must follow driver extraction")
    require(packages[2].get("depends_on") == ["INT-18"], "INT-22 must follow INT-18")
    require(packages[3].get("depends_on") == ["INT-22"], "INT-23 must follow INT-22")
    require(packages[4].get("depends_on") == ["INT-23"], "INT-24 must follow INT-23")
    return {"packages": len(packages), "repositories": len(plan.get("repositories", {}))}


if __name__ == "__main__":
    try:
        result = validate_plan(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
    except (OSError, ValidationError, yaml.YAMLError) as error:
        print(f"0.8 declarative plan invalid: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"0.8 declarative plan valid: {result['packages']} packages, {result['repositories']} owners")
