#!/usr/bin/env python3
"""Read-only structural validation for the software stabilization guide."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import re
import sys
from typing import Any

import yaml


EXPECTED_ROOT_KEYS = {
    "schema_version",
    "slug",
    "state",
    "repositories",
    "packages",
}
PACKAGE_FIELDS = {"id", "release", "owner", "depends_on"}
TABLE_HEADER = ("ID", "Release", "Owner", "Outcome", "Prerequisites")
PLAN_SLUG = "software-stabilization-07-08"
PLAN_STATE = "implementing"
PUBLIC_BOOTSTRAP_ID = "SEMREG-BOOTSTRAP"
PUBLIC_SEMREG = "Project-Helianthus/helianthus-semreg"


class ValidationError(ValueError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValidationError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_mapping,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValidationError(f"invalid YAML: {exc}") from exc
    _require(isinstance(document, dict), "plan.yaml root must be a mapping")
    return document


def _table(path: Path) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    found = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if found and rows:
                break
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if not found:
            if cells == TABLE_HEADER:
                found = True
            continue
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        _require(len(cells) == len(TABLE_HEADER), "91-milestone-map.md has a malformed package row")
        rows.append((cells[0], cells[1], cells[2], cells[3], cells[4]))
    _require(found, "91-milestone-map.md is missing the package table")
    return rows


def _ancestors(package_id: str, packages: dict[str, dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    pending = list(packages[package_id]["depends_on"])
    while pending:
        dependency = pending.pop()
        if dependency not in result:
            result.add(dependency)
            pending.extend(packages[dependency]["depends_on"])
    return result


def _validate_graph(packages: dict[str, dict[str, Any]]) -> None:
    successors = {package_id: [] for package_id in packages}
    indegree = {package_id: 0 for package_id in packages}
    for package_id, package in packages.items():
        dependencies = package["depends_on"]
        _require(isinstance(dependencies, list), f"{package_id} depends_on must be a list")
        _require(len(dependencies) == len(set(dependencies)), f"{package_id} has duplicate dependencies")
        for dependency in dependencies:
            _require(isinstance(dependency, str), f"{package_id} dependency must be a string")
            _require(dependency in packages, f"{package_id} has unknown dependency {dependency}")
            _require(dependency != package_id, f"{package_id} cannot depend on itself")
            successors[dependency].append(package_id)
            indegree[package_id] += 1
    ready = deque(package_id for package_id, count in indegree.items() if count == 0)
    visited = 0
    while ready:
        package_id = ready.popleft()
        visited += 1
        for successor in successors[package_id]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    _require(visited == len(packages), "package dependency graph must be acyclic")


def _validate_repositories(value: Any) -> dict[str, dict[str, str]]:
    _require(isinstance(value, dict) and value, "repositories must be a nonempty mapping")
    repositories: dict[str, dict[str, str]] = {}
    planned: list[tuple[str, dict[str, str]]] = []
    for repository, metadata in value.items():
        _require(
            isinstance(repository, str) and re.fullmatch(r"Project-Helianthus/[a-z0-9.-]+", repository),
            "repository keys must be canonical Project-Helianthus names",
        )
        _require(isinstance(metadata, dict), f"{repository} metadata must be a mapping")
        status = metadata.get("owner_status")
        _require(status in {"existing", "planned"}, f"{repository} owner_status is invalid")
        expected_fields = {"owner_status", "bootstrap"} if status == "planned" else {"owner_status"}
        _require(set(metadata) == expected_fields, f"{repository} metadata fields are invalid")
        if status == "planned":
            _require(isinstance(metadata["bootstrap"], str), f"{repository} bootstrap must be a string")
            planned.append((repository, metadata))
        repositories[repository] = metadata
    _require(
        planned == [(PUBLIC_SEMREG, {"owner_status": "planned", "bootstrap": PUBLIC_BOOTSTRAP_ID})],
        "the sole planned public repository must be helianthus-semreg bootstrapped by SEMREG-BOOTSTRAP",
    )
    return repositories


def validate_plan(plan_dir: Path) -> dict[str, int]:
    plan_dir = plan_dir.resolve()
    plan = _load(plan_dir / "plan.yaml")
    _require(set(plan) == EXPECTED_ROOT_KEYS, "plan.yaml root fields are invalid")
    _require(plan["schema_version"] == 1, "schema_version must be 1")
    _require(plan["slug"] == PLAN_SLUG, "slug is invalid")
    _require(plan["state"] == PLAN_STATE, "state must be implementing")
    repositories = _validate_repositories(plan["repositories"])

    package_rows = plan["packages"]
    _require(isinstance(package_rows, list), "packages must be a list")
    _require(len(package_rows) == 45, "the guide must retain 45 work packages")
    packages: dict[str, dict[str, Any]] = {}
    for index, package in enumerate(package_rows):
        _require(isinstance(package, dict), f"packages[{index}] must be a mapping")
        _require(set(package) == PACKAGE_FIELDS, f"packages[{index}] fields are invalid")
        package_id = package["id"]
        _require(
            isinstance(package_id, str) and re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", package_id),
            f"packages[{index}] has an invalid id",
        )
        _require(package_id not in packages, f"duplicate package id {package_id}")
        _require(package["release"] in {"0.7", "0.8"}, f"{package_id} release is invalid")
        _require(package["owner"] in repositories, f"{package_id} has unknown owner {package['owner']}")
        packages[package_id] = package
    _validate_graph(packages)

    bootstrap = packages.get(PUBLIC_BOOTSTRAP_ID)
    _require(bootstrap is not None, "SEMREG-BOOTSTRAP is missing")
    _require("INT-05" in packages, "INT-05 is missing")
    _require(
        PUBLIC_BOOTSTRAP_ID in _ancestors("INT-05", packages),
        "INT-05 must remain downstream of SEMREG-BOOTSTRAP",
    )

    expected_table = [
        (
            package["id"],
            package["release"],
            package["owner"],
            ", ".join(package["depends_on"]) if package["depends_on"] else "None",
        )
        for package in package_rows
    ]
    actual_table = _table(plan_dir / "91-milestone-map.md")
    actual_projection = [(row[0], row[1], row[2], row[4]) for row in actual_table]
    _require(actual_projection == expected_table, "91-milestone-map.md does not mirror plan.yaml")
    return {"packages": len(packages), "repositories": len(repositories)}


def main(argv: list[str]) -> int:
    plan_dir = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent
    try:
        counts = validate_plan(plan_dir)
    except (OSError, ValidationError) as exc:
        print(f"Software stabilization plan invalid: {exc}", file=sys.stderr)
        return 1
    print(f"Software stabilization plan valid: {counts['packages']} packages, {counts['repositories']} owners")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
