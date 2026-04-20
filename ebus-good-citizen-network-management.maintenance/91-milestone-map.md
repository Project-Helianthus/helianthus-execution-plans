# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `M0` | Docs integration of official NM + OSI 7 services into Helianthus normative docs | `helianthus-docs-ebus` | none | locked-ready |
| `M1` | Raw wire primitives and bounded read-only substrate | `helianthus-ebusgo` | `M0` | queued |
| `M2a` | MCP raw capture, frame listing, replay/decode-friendly evidence | `helianthus-ebusgateway` | `M1` | queued |
| `M2b` | Active raw read-only transceive, conditional on contention proof | `helianthus-ebusgateway` | `M2a`, `ISSUE-GW-00` | queued |
| `M3` | Identity model refactor for `PhysicalDevice`, `BusFace`, and companion pairs | `helianthus-ebusreg`, `helianthus-ebusgateway` | `M1` | queued |
| `M4` | Gateway NM runtime: local address-pair authority, target configuration, cycle times, event bridge, self-monitoring, status chart, net status | `helianthus-ebusgateway` | `M3`, `ISSUE-GW-JOIN-01` | queued |
| `M5` | NM-aligned discovery integration + MCP NM surfaces + face-parity fixes | `helianthus-ebusgateway`, `helianthus-ebusreg` | `M4` | queued |
| `M6` | Broadcast lane: `FF 00` on join/reset, `FF 02` on failure | `helianthus-ebusgateway` | `M4` | queued |
| `M7a` | Responder feasibility spike | `helianthus-ebusgo` | `M1` | parallel-spike |
| `M7b` | Local participant responder: `07 04` + `FF 03/04/05/06` | `helianthus-ebusgateway`, `helianthus-ebusgo` | `M4`, `M7a` | blocked-on-feasibility |
| `M8` | Optional-later broadcast lane: `FF 01`, `07 FF`, policy hardening | `helianthus-ebusgateway` | `M6` | optional |
| `M9` | GraphQL/HA optional consumer parity | `helianthus-ebusgateway`, `helianthus-ha-integration` | `M5` | optional |
| `M10` | Real-bus validation, transport matrix, rollback criteria | all touched repos | `M6`, `M7b` if pursued, `M8` if pursued | queued |

## Ordering Rules

- Default order:
  `M0 -> M1 -> M2a -> M2b -> M3 -> M4 -> M5 -> M6 -> M7a -> M7b -> M8 -> M9 -> M10`.
- `M7a` may start as soon as `M1` exists and may run in parallel with `M2a`
  through `M5`, but it blocks only `M7b`.
- `ISSUE-GW-JOIN-01` must land before `M4`.
- `M3` is registry-first, gateway-second.
- `M5` is registry-support-first only if still required, then gateway
  consumers.
- `M6` is gateway-only unless implementation falsifies the existing
  broadcast-capable send-path assumption.
- Optional consumer work does not redefine the API shape; MCP and canonical
  gateway surfaces remain the source of truth.
