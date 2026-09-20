#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path
from typing import Any
import re

import yaml


EXPECTED_REPOSITORIES = {
    "Project-Helianthus/.github": {"owner_status": "existing"},
    "Project-Helianthus/helianthus-gateway": {"owner_status": "existing"},
    "Project-Helianthus/helianthus-semreg": {"owner_status": "existing"},
}
EXPECTED_OWNERS = {
    "DRIVER-EXTRACTION-01": "Project-Helianthus/.github",
    "INT-18": "Project-Helianthus/.github",
    "INT-22": "Project-Helianthus/helianthus-gateway",
    "INT-23": "Project-Helianthus/helianthus-gateway",
    "INT-24": "Project-Helianthus/helianthus-gateway",
}
EXPECTED_ROOT_KEYS = {
    "schema_version",
    "slug",
    "state",
    "release_prerequisite",
    "tracking",
    "repositories",
    "packages",
}
TABLE_HEADER = ("ID", "Release", "Owner", "Outcome", "Prerequisites")


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_graph(packages: list[dict[str, Any]]) -> None:
    package_ids = {package["id"] for package in packages}
    successors = {package_id: [] for package_id in package_ids}
    degree = {package_id: 0 for package_id in package_ids}
    for package in packages:
        for dependency in package["depends_on"]:
            require(dependency in package_ids, f"{package['id']} has unknown dependency")
            successors[dependency].append(package["id"])
            degree[package["id"]] += 1
    ready = deque(package_id for package_id, value in degree.items() if value == 0)
    visited = 0
    while ready:
        package_id = ready.popleft()
        visited += 1
        for successor in successors[package_id]:
            degree[successor] -= 1
            if degree[successor] == 0:
                ready.append(successor)
    require(visited == len(packages), "0.8 package dependency graph must be acyclic")


def table_projection(path: Path) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    started = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if started:
                break
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if not started:
            if cells == TABLE_HEADER:
                started = True
            continue
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        require(len(cells) == len(TABLE_HEADER), "0.8 milestone map has a malformed package row")
        rows.append((cells[0], cells[1], cells[2], cells[4]))
    require(started, "0.8 milestone map is missing the package table")
    return rows


def validate_plan(plan_dir: Path) -> dict[str, int]:
    plan = yaml.safe_load((plan_dir / "plan.yaml").read_text(encoding="utf-8"))
    require(isinstance(plan, dict), "plan.yaml root must be a mapping")
    require(set(plan) == EXPECTED_ROOT_KEYS, "0.8 plan.yaml root fields are invalid")
    require(plan.get("schema_version") == 1, "0.8 schema_version is invalid")
    require(plan.get("slug") == "software-declarative-08", "slug is invalid")
    require(plan.get("state") == "locked", "0.8 must remain locked")
    require(plan.get("release_prerequisite") == "accepted-0.7", "0.7 prerequisite is invalid")
    require(plan.get("tracking") == {
        "software_07_project": "https://github.com/orgs/Project-Helianthus/projects/2",
        "software_08_project": "https://github.com/orgs/Project-Helianthus/projects/4",
    }, "0.8 project tracking links are invalid")
    require(plan.get("repositories") == EXPECTED_REPOSITORIES, "0.8 repository boundary is invalid")
    packages: Any = plan.get("packages")
    require(isinstance(packages, list), "packages must be a list")
    expected = ["DRIVER-EXTRACTION-01", "INT-18", "INT-22", "INT-23", "INT-24"]
    require([package.get("id") for package in packages] == expected, "0.8 package IDs are invalid")
    for package in packages:
        require(set(package) == {"id", "release", "owner", "depends_on"}, "0.8 package fields are invalid")
        require(package.get("release") == "0.8", "0.8 package release is invalid")
        require(package.get("owner") == EXPECTED_OWNERS[package["id"]], "0.8 package owner is invalid")
    require(packages[0].get("depends_on") == [], "driver extraction must have no dependencies")
    require(packages[1].get("depends_on") == ["DRIVER-EXTRACTION-01"], "INT-18 must follow driver extraction")
    require(packages[2].get("depends_on") == ["INT-18"], "INT-22 must follow INT-18")
    require(packages[3].get("depends_on") == ["INT-22"], "INT-23 must follow INT-22")
    require(packages[4].get("depends_on") == ["INT-23"], "INT-24 must follow INT-23")
    validate_graph(packages)
    expected_table = [
        (package["id"], package["release"], package["owner"], ", ".join(package["depends_on"]) or "None")
        for package in packages
    ]
    require(
        table_projection(plan_dir / "91-milestone-map.md") == expected_table,
        "0.8 milestone map does not mirror plan.yaml",
    )
    return {"packages": len(packages), "repositories": len(plan.get("repositories", {}))}


if __name__ == "__main__":
    try:
        result = validate_plan(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
    except (OSError, ValidationError, yaml.YAMLError) as error:
        print(f"0.8 declarative plan invalid: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"0.8 declarative plan valid: {result['packages']} packages, {result['repositories']} owners")
