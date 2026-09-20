#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
import re
import sys
from pathlib import Path
from typing import Any

import yaml


PLAN_SLUG = "software-stabilization-07"
PUBLIC_PRIORITY = [f"PUBLIC-{number:02d}" for number in range(1, 9)]
FUTURE_IDS = {"INT-18", "INT-22", "INT-23", "INT-24"}
RENAMED_GATEWAY = "Project-Helianthus/helianthus-gateway"
CURRENT_GATEWAY = "Project-Helianthus/helianthus-ebusgateway"
TABLE_HEADER = ("ID", "Release", "Owner", "Outcome", "Prerequisites")


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def ancestors(package_id: str, packages: dict[str, dict[str, Any]]) -> set[str]:
    found: set[str] = set()
    pending = list(packages[package_id]["depends_on"])
    while pending:
        dependency = pending.pop()
        if dependency not in found:
            found.add(dependency)
            pending.extend(packages[dependency]["depends_on"])
    return found


def validate_graph(packages: dict[str, dict[str, Any]]) -> None:
    successors = {package_id: [] for package_id in packages}
    degree = {package_id: 0 for package_id in packages}
    for package_id, package in packages.items():
        dependencies = package["depends_on"]
        require(isinstance(dependencies, list), f"{package_id} depends_on must be a list")
        require(len(dependencies) == len(set(dependencies)), f"{package_id} has duplicate dependencies")
        for dependency in dependencies:
            require(dependency in packages, f"{package_id} has unknown dependency {dependency}")
            successors[dependency].append(package_id)
            degree[package_id] += 1
    ready = deque(package_id for package_id, value in degree.items() if value == 0)
    visited = 0
    while ready:
        package_id = ready.popleft()
        visited += 1
        for successor in successors[package_id]:
            degree[successor] -= 1
            if degree[successor] == 0:
                ready.append(successor)
    require(visited == len(packages), "package dependency graph must be acyclic")


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
        require(len(cells) == len(TABLE_HEADER), "91-milestone-map.md has a malformed package row")
        rows.append((cells[0], cells[1], cells[2], cells[4]))
    require(started, "91-milestone-map.md is missing the package table")
    return rows


def validate_plan(plan_dir: Path) -> dict[str, int]:
    plan = yaml.safe_load((plan_dir / "plan.yaml").read_text(encoding="utf-8"))
    require(isinstance(plan, dict), "plan.yaml root must be a mapping")
    require(plan.get("slug") == PLAN_SLUG, "slug is invalid")
    require(plan.get("state") == "implementing", "0.7 must remain implementing")
    require(plan.get("tracking") == {
        "software_07_project": "https://github.com/orgs/Project-Helianthus/projects/2",
        "software_08_project": "https://github.com/orgs/Project-Helianthus/projects/4",
    }, "project tracking links are invalid")

    repositories = plan.get("repositories")
    require(isinstance(repositories, dict), "repositories must be a mapping")
    for owner in ("Project-Helianthus/helianthus-semreg", "Project-Helianthus/helianthus-docs-semantic"):
        require(repositories.get(owner) == {"owner_status": "existing"}, f"{owner} must remain existing")
    require(repositories.get(RENAMED_GATEWAY) == {"owner_status": "planned", "bootstrap": "INT-14"}, "renamed gateway state is invalid")

    records = plan.get("packages")
    require(isinstance(records, list) and len(records) == 49, "0.7 must retain 41 established packages plus 8 public priorities")
    packages: dict[str, dict[str, Any]] = {}
    for package in records:
        require(isinstance(package, dict), "each package must be a mapping")
        require(set(package) == {"id", "release", "owner", "depends_on"}, "package fields are invalid")
        package_id = package["id"]
        require(isinstance(package_id, str) and package_id not in packages, "package IDs must be unique")
        require(package["release"] == "0.7", f"{package_id} is not a 0.7 package")
        require(package_id not in FUTURE_IDS, f"{package_id} belongs exclusively to 0.8")
        require(package["owner"] in repositories, f"{package_id} has unknown owner")
        packages[package_id] = package
    require(plan.get("priority_order") == PUBLIC_PRIORITY, "public priority order is invalid")
    for package_id in PUBLIC_PRIORITY:
        require(packages.get(package_id, {}).get("depends_on") == [], f"{package_id} must not encode a false technical dependency")
    validate_graph(packages)

    require("INT-04" in ancestors("INT-05", packages), "INT-05 must follow INT-04")
    require("INT-14" in ancestors("INT-17", packages), "INT-17 must follow INT-14")
    require("INT-19" in ancestors("INT-20", packages), "INT-20 must follow INT-19")
    require({"INT-19", "INT-20"} <= ancestors("INT-21", packages), "INT-21 must follow Daybreak and hardware validation")
    require(packages["INT-06"]["owner"] == CURRENT_GATEWAY, "INT-06 must remain owned by the current gateway")
    for package_id in ("INT-17", "INT-19", "INT-20", "INT-21"):
        require(packages[package_id]["owner"] == RENAMED_GATEWAY, f"{package_id} must use the renamed gateway")

    expected_table = [(record["id"], record["release"], record["owner"], ", ".join(record["depends_on"]) or "None") for record in records]
    require(table_projection(plan_dir / "91-milestone-map.md") == expected_table, "91-milestone-map.md does not mirror plan.yaml")
    canonical = (plan_dir / "00-canonical.md").read_text(encoding="utf-8")
    require(plan["matter_anchor"]["commit"] in canonical, "canonical Matter anchor does not match plan.yaml")
    return {"packages": len(packages), "repositories": len(repositories)}


if __name__ == "__main__":
    try:
        result = validate_plan(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
    except (OSError, ValidationError, yaml.YAMLError) as error:
        print(f"0.7 stabilization plan invalid: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"0.7 stabilization plan valid: {result['packages']} packages, {result['repositories']} owners")
