#!/usr/bin/env python3
"""Local document structure only; no network, subprocesses, writes or product scans."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import yaml


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
REQUIRED = {
    "slug", "title", "state", "source_discussion", "target_repos", "knowledge_repo",
    "canonical_file", "split_index", "started_on", "current_milestone",
}
KNOWN_REPOS = {
    "helianthus-execution-plans", "helianthus-ebusgateway", "helianthus-gateway",
    "helianthus-docs-ebus", "helianthus-docs-modbus", "helianthus-docs-canbus",
    "helianthus-docs-eebus", "helianthus-docs-semantic", "helianthus-modbus",
    "helianthus-modbusreg", "helianthus-canbus", "helianthus-canbusreg",
    "helianthus-eebusreg", "helianthus-ebusgo", "helianthus-ebusreg",
    "helianthus-semreg", "helianthus-ha-addon", "helianthus-ha-integration",
}
RELEASE_RANK = {"planning": 0, "0.7": 1, "0.8": 2, "pre-1.0": 3}
FAMILY_ORDER = {
    ("DM-CAN", "DM-MODBUS-RUNTIME"),
    ("DM-MODBUS-SURFACES", "DM-EEBUS-RUNTIME"),
    ("DM-EEBUS-SURFACES", "DM-EBUS-TRANSPORT"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rows(text, header):
    result, active = [], False
    for line in text.splitlines():
        if not line.startswith("|"):
            if active:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not active:
            active = cells == header
            continue
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        require(len(cells) == len(header), f"malformed table row: {line}")
        result.append(cells)
    require(active, f"missing table: {header}")
    return result


def graph(records, external=None):
    external = external or {}
    by_id = {r["id"]: r for r in records}
    require(len(by_id) == len(records), "duplicate IDs")
    require(not (set(by_id) & set(external)), "local/external ID collision")
    nodes = {**external, **by_id}
    done, visiting, lineage = set(), set(), {}

    def visit(key):
        require(key not in visiting, f"dependency cycle: {key}")
        if key in done:
            return lineage[key]
        visiting.add(key)
        deps = nodes[key].get("depends_on", []) if key in external else nodes[key]["depends_on"]
        require(isinstance(deps, list) and len(set(deps)) == len(deps), f"invalid dependencies: {key}")
        require(set(deps) <= set(by_id) | set(external), f"unknown prerequisite: {key}")
        found = set(deps)
        for dep in deps:
            found.update(visit(dep))
        visiting.remove(key)
        done.add(key)
        lineage[key] = found
        return found

    for key in nodes:
        visit(key)
    return by_id, lineage


def release_order(nodes):
    for key, record in nodes.items():
        require(record.get("release") in RELEASE_RANK, f"unknown release: {key}")
    for key, record in nodes.items():
        for dep in record.get("depends_on", []):
            require(RELEASE_RANK[nodes[dep]["release"]] <= RELEASE_RANK[record["release"]],
                    f"dependency from later release: {dep} -> {key}")
            require(dep != "R-INT21" or RELEASE_RANK[record["release"]] >= RELEASE_RANK["0.8"],
                    f"R-INT21 dependency below 0.8: {key}")


def validate(directory):
    plan = yaml.load((directory / "plan.yaml").read_text(), Loader=UniqueLoader)
    require(isinstance(plan, dict) and REQUIRED <= set(plan), "missing required metadata")
    require(plan["slug"] == "driver-model-transition" and plan["state"] == "implementing", "slug/state")
    require(directory.name == f"{plan['slug']}.{plan['state']}", "directory/state mismatch")
    require(plan["source_discussion"] == "https://github.com/Project-Helianthus/helianthus-execution-plans/issues/126", "source issue")
    require(plan["knowledge_repo"] == "helianthus-docs-ebus", "knowledge owner")
    require(plan["canonical_file"] == "00-canonical.md" and plan["split_index"] == "01-index.md", "canonical/index filenames")
    require(plan["process_model"] == {"authority": "guidance_only", "post_merge_effects": "none"}, "planning boundary")
    require(set(plan["target_repos"]) == KNOWN_REPOS and len(plan["target_repos"]) == len(KNOWN_REPOS), "repository allowlist")
    files = ["00-canonical.md", "01-index.md", "90-issue-map.md", "91-milestone-map.md", "92-retained-acceptance.md", "99-status.md"]
    require(all((directory / f).is_file() for f in files), "required document missing")
    docs = {f: (directory / f).read_text() for f in files}
    canonical = docs["00-canonical.md"]
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    chunks = plan["chunks"]
    require(chunks == sorted(x.name for x in directory.glob("1[0-9]-*.md")), "chunk inventory/order")
    bodies = []
    for filename in files[1:] + chunks:
        text = (directory / filename).read_text()
        require(re.findall(r"Canonical-SHA256: `([0-9a-f]{64})`", text) == [digest], f"canonical digest: {filename}")
        if filename in chunks:
            for field in ("Depends on", "Scope", "Idempotence contract", "Falsifiability gate", "Coverage"):
                require(re.search(rf"^{field}: .+", text, re.M), f"missing {field}: {filename}")
            # Without a tokenizer this deliberately conservative byte bound keeps every
            # split chunk below 10,000 byte-BPE tokens. It is not an exact token count.
            require(len(text.encode()) <= 6100, f"chunk exceeds conservative size budget: {filename}")
            bodies.append(text.split("\n\n", 2)[2].rstrip())
        docs[filename] = text
    preamble = (directory / "reference-preamble.md").read_text()
    require(canonical == preamble + "\n" + "\n\n".join(bodies) + "\n",
            "canonical preamble/chunk mirror")
    docs["reference-preamble.md"] = preamble
    for filename in ("reference-decision.md", "reference-inventory.md"):
        docs[filename] = (directory / filename).read_text()
    decision = docs["reference-decision.md"].strip()
    require(decision and docs["10-decision-and-registration.md"].count(decision) == 1
            and canonical.count(decision) == 1, "binding decision mirror")
    for filename, text in docs.items():
        for link in re.findall(r"\]\(\./([^)#]+)(?:#[^)]*)?\)", text):
            require("/" not in link and (directory / link).is_file(), f"broken/escaping link: {filename}: {link}")

    external = plan["external_prerequisites"]
    require(all(r["repo"] in KNOWN_REPOS and r["description"] for r in external.values()), "external ownership")
    issues, ancestors = graph(plan["issues"], external)
    milestones, _ = graph(plan["milestones"])
    release_order({**external, **issues})
    release_order(milestones)
    require(plan["current_milestone"] in milestones, "current milestone")
    for key, r in issues.items():
        require(r["repo"] in KNOWN_REPOS and r["milestone"] in milestones, f"unknown owner/milestone: {key}")
        require(type(r["complexity"]) is int and 1 <= r["complexity"] <= 10, f"complexity: {key}")
        require(
            {r["author_camp"], r["reviewer_camp"]} == {"Claude", "Codex"}
            or (r["author_camp"], r["reviewer_camp"]) == ("camp decided at dispatch", "opposite author camp"),
            f"cross-camp review: {key}",
        )
        require(set(r["decisions"]) <= {f"O{i}" for i in range(1, 13)}, f"unknown decision: {key}")
        require(r["release"] == milestones[r["milestone"]]["release"], f"release/milestone mismatch: {key}")
        if r["release"] in ("0.8", "pre-1.0"):
            require("R-INT21" in ancestors[key], f"missing accepted 0.7 prerequisite: {key}")
        if not r["optional"]:
            require(not any(issues[d]["optional"] for d in ancestors[key] if d in issues), f"optional case made mandatory: {key}")
    require(FAMILY_ORDER <= {tuple(pair) for pair in plan["ordering"]}, "required family-order pairs missing")
    for before, after in plan["ordering"]:
        require(before in ancestors[after], f"ordering not represented in DAG: {before} -> {after}")

    header = ["ID", "Repository", "Title", "Prerequisites", "Cx", "Author camp", "Reviewer camp", "Milestone", "Decisions / optional"]
    expected = []
    for r in plan["issues"]:
        title = r["title"] + (f" (#{r['existing_issue']})" if r["existing_issue"] else "")
        choice = ", ".join(r["decisions"]) or "None"
        choice += "; optional O10 concrete case" if r["optional"] else ""
        expected.append([r["id"], "Project-Helianthus/" + r["repo"], title, ", ".join(r["depends_on"]) or "None", str(r["complexity"]), r["author_camp"], r["reviewer_camp"], r["milestone"], choice])
    require(rows(docs["90-issue-map.md"], header) == expected, "issue Markdown/YAML mirror")
    expected = [[m["id"], m["release"], ", ".join(m["depends_on"]) or "None", m["outcome"]] for m in plan["milestones"]]
    require(rows(docs["91-milestone-map.md"], ["ID", "Release", "Prerequisites", "Outcome"]) == expected, "milestone mirror")
    expected = [[m["id"], ", ".join(r["id"] for r in plan["issues"] if r["milestone"] == m["id"])] for m in plan["milestones"]]
    require(rows(docs["91-milestone-map.md"], ["Milestone", "Planned issue IDs"]) == expected, "milestone membership mirror")
    contracts = plan["contracts"]
    require(len({c["id"] for c in contracts}) == len(contracts), "duplicate retained contract IDs")
    require(all(c["owner"] in KNOWN_REPOS and c["version"] for c in contracts), "contract owner/version")
    expected = [[c["id"], c["version"], "Project-Helianthus/" + c["owner"], c["disposition"]] for c in contracts]
    require(rows(docs["92-retained-acceptance.md"], ["ID", "Version", "Owner", "Retained disposition"]) == expected, "contract/version mirror")
    require(len(plan["hard_stops"]) == len(set(plan["hard_stops"])) >= 8, "hard stops missing/duplicated")
    require(rows(docs["99-status.md"], ["Hard stop"]) == [[stop] for stop in plan["hard_stops"]],
            "hard-stop text mirror")
    decision_rows = rows(docs["17-operator-decisions.md"], ["ID", "Choice and recommendation", "Blocks"])
    require([re.fullmatch(r"(O[1-9]|O1[0-2])(?: / G5 D[1-6])?", row[0]).group(1)
             if re.fullmatch(r"(O[1-9]|O1[0-2])(?: / G5 D[1-6])?", row[0]) else None
             for row in decision_rows] == [f"O{i}" for i in range(1, 13)], "exact decision-row inventory")
    return len(issues), len(milestones), len(chunks), digest


if __name__ == "__main__":
    try:
        result = validate(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print(f"Driver-model plan invalid: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Driver-model plan valid: {result[0]} issues, {result[1]} milestones, {result[2]} chunks")
    print(f"Canonical SHA256: {result[3]} (document consistency only)")
    print("Chunk size gate: each <= 6,100 UTF-8 bytes; exact tokenizer counts unavailable")
