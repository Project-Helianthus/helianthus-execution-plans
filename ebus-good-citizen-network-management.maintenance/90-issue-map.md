# Issue Map

This plan uses canonical issue identifiers. GitHub issue and PR linkage is
backfilled here when it exists, but the canonical IDs below remain the stable
mapping surface for the workstream.

Status legend:
- `planned`: defined in the locked plan, not yet started
- `queued`: waiting on an earlier milestone or prerequisite
- `parallel-spike`: may start early in background without unblocking the full plan
- `optional`: gated consumer or optional-later lane
- `conditional`: starts only if an earlier feasibility result proves it needed

## Core Docs and Lower Layer

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-DOC-00` | `helianthus-docs-ebus` | Integrate official NM and OSI 7 services into Helianthus normative docs | planned | not yet linked |
| `ISSUE-DOC-01` | `helianthus-docs-ebus` | Discovery realignment and indirect-NM interpretation | queued | not yet linked |
| `ISSUE-DOC-02` | `helianthus-docs-ebus` | Local participant behavior, transport capability matrix, and bus-load policy | queued | not yet linked |
| `ISSUE-GO-01` | `helianthus-ebusgo` | Raw read-only transceive/capture primitive set | queued | not yet linked |
| `ISSUE-GO-01A` | `helianthus-ebusgo` | Responder feasibility spike for slave-address listening/reply | parallel-spike | not yet linked |

## Identity and Registry

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-REG-01` | `helianthus-ebusreg` | `PhysicalDevice + BusFace + CompanionPair` identity model | queued | not yet linked |
| `ISSUE-REG-02` | `helianthus-ebusreg` | Registry support for face-aware views consumed by gateway NM/discovery | queued | not yet linked |

## Gateway Runtime and MCP

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-00` | `helianthus-ebusgateway` | Raw MCP contention strategy versus semantic poller and active bus use | queued | not yet linked |
| `ISSUE-GW-01` | `helianthus-ebusgateway` | Raw MCP capture/list/replay surfaces | queued | not yet linked |
| `ISSUE-GW-02` | `helianthus-ebusgateway` | Optional active raw transceive after contention proof | queued | not yet linked |
| `ISSUE-GW-03` | `helianthus-ebusgateway` | MCP registry `devices.*` alias-address parity and snapshot lookup correctness | queued | not yet linked |
| `ISSUE-GW-JOIN-01` | `helianthus-ebusgateway` | Integrate gateway address-selection authority with Joiner output where available; expose local master/slave pair provenance to NM runtime | queued | not yet linked |
| `ISSUE-GW-NM-01` | `helianthus-ebusgateway` | NM state machine: `NMInit/NMReset/NMNormal`, start flag, target-configuration population, self entry | queued | not yet linked |
| `ISSUE-GW-NM-02` | `helianthus-ebusgateway` | Default/override cycle-time model, passive/active/self event bridge, status chart, and net-status computation | queued | not yet linked |
| `ISSUE-GW-NM-03` | `helianthus-ebusgateway` | NM MCP surfaces with provenance and confidence markers | queued | not yet linked |
| `ISSUE-GW-NM-04` | `helianthus-ebusgateway` | Discovery integration with passive evidence and NM runtime | queued | not yet linked |
| `ISSUE-GW-NM-05` | `helianthus-ebusgateway` | Mandatory broadcast lane: `FF 00` and `FF 02` (`FE 01` explicitly out of lock baseline) | queued | not yet linked |
| `ISSUE-GW-NM-06` | `helianthus-ebusgateway` | Optional broadcast lane: `FF 01` and `07 FF` with explicit cadence floor | queued | not yet linked |
| `ISSUE-GW-NM-07` | `helianthus-ebusgateway` | Local participant responder integration for `07 04` and `FF 03/04/05/06` | queued | not yet linked |

## Conditional / Optional Follow-On

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-PROXY-01` | `helianthus-ebus-adapter-proxy` | Conditional responder-path mediation if transport spike requires it | conditional | not yet linked |
| `ISSUE-HA-01` | `helianthus-ha-integration` | Optional NM consumer entities once API is stable | optional | not yet linked |
