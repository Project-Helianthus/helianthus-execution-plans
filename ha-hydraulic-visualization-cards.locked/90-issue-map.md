# Issue Map

This plan uses canonical issue identifiers inside the split chunks. GitHub
issue numbers may be created later in the target repository, but the
canonical IDs below remain the stable mapping surface for the plan itself.

Status legend:
- `planned`: defined in the plan, GitHub issue not yet linked here
- `active`: current execution focus
- `blocked`: depends on earlier milestone completion

## M0

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-HA-VIZ-01` | `helianthus-ha-integration` | Build pipeline: frontend toolchain, `async_setup` registration, hello card, `manifest.json` version pin | active |

## M1

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-HA-VIZ-02` | `helianthus-ha-integration` | Card 1: Burner Hydraulics — full SVG layout, entity mapping, animations, config validation, `boiler_type` gating | blocked |

Ordering rule:
- `ISSUE-HA-VIZ-02` depends on `ISSUE-HA-VIZ-01` (build pipeline must be
  working before Card 1 implementation begins).

## M2

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-HA-VIZ-03` | `helianthus-ha-integration` | Card 2: System Hydraulics — topology-adaptive SVG, circuit/cylinder/solar/DHW rendering, config validation, topology dependency rules | blocked |

Ordering rule:
- `ISSUE-HA-VIZ-03` depends on `ISSUE-HA-VIZ-02` merging first (Card 1
  proves the rendering patterns and shared utilities).

## M3

| Canonical ID | Repo | Summary | Status |
| --- | --- | --- | --- |
| `ISSUE-HA-VIZ-04` | `helianthus-ha-integration` | Polish: SVG refinement, card picker preview images, `getStubConfig`, configuration examples, bundle size gate | blocked |

Ordering rule:
- `ISSUE-HA-VIZ-04` depends on `ISSUE-HA-VIZ-03` merging first (both cards
  must be functional before polish).
