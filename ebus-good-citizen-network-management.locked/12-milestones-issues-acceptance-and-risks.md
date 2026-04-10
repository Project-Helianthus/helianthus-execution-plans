# eBUS Good-Citizen NM 03: Milestones, Issues, Acceptance, and Risks

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `eb11742d60722b1389dca6822b956c15ddee542aacf95901299fefcd1a27dfcf`

Depends on:
- [`10-evidence-decisions-and-wire-behaviour.md`](./10-evidence-decisions-and-wire-behaviour.md)
- [`11-runtime-discovery-and-policy.md`](./11-runtime-discovery-and-policy.md)

Scope: Milestone ordering, cross-repo sequencing, canonical issue set,
acceptance criteria, and plan-level risks.

Idempotence contract: Declarative-only. Reapplying this chunk must not reorder
milestones, change repository ownership, or weaken acceptance criteria.

Falsifiability gate: A review fails this chunk if milestone dependencies permit
M4 before `ISSUE-GW-JOIN-01`, collapse the `M7a/M7b` gate, hide cross-repo
ordering, or state acceptance criteria that are not testable.

Coverage: Milestone Plan; Canonical Issues; Acceptance Criteria; Risks from the
canonical plan.

## Milestone Plan

| Milestone | Scope | Primary repo(s) | Result |
| --- | --- | --- | --- |
| `M0` | Docs integration of official NM + OSI 7 services into Helianthus normative docs | `helianthus-docs-ebus` | Normative interpretation frozen |
| `M1` | Raw wire primitives and bounded read-only substrate | `helianthus-ebusgo` | Safe lower-layer raw primitive set |
| `M2a` | MCP raw capture, frame listing, replay/decode-friendly evidence | `helianthus-ebusgateway` | No more `ebusd` dependence for passive/raw inspection |
| `M2b` | Active raw read-only transceive, conditional on contention proof | `helianthus-ebusgateway` | Safe active raw probing without poller regression |
| `M3` | Identity model refactor for `PhysicalDevice`, `BusFace`, and companion pairs | `helianthus-ebusreg`, `helianthus-ebusgateway` | Face-aware topology substrate |
| `M4` | Gateway NM runtime: local address-pair authority, target-configuration population, default/override cycle times, passive/active/self event bridge, self-monitoring, status chart, net status, start flag, `NMInit/NMReset/NMNormal` | `helianthus-ebusgateway` | Spec-aligned internal NM model |
| `M5` | NM-aligned discovery integration + MCP NM surfaces + face-parity fixes in MCP registry tools | `helianthus-ebusgateway`, `helianthus-ebusreg` | Discovery and NM fed by passive/runtime evidence |
| `M6` | Broadcast lane: `FF 00` on join/reset, `FF 02` on failure | `helianthus-ebusgateway` | Mandatory NM broadcasts working on initiator-only transports via the existing broadcast-capable send path |
| `M7a` | Responder feasibility spike: local slave-address receive/reply on ENH/ENS and capability determination for other transports | `helianthus-ebusgo`, conditional proxy/firmware repos | Go/no-go for responder lane |
| `M7b` | Local participant responder: targeted `07 04` + `FF 03/04/05/06` | `helianthus-ebusgateway`, `helianthus-ebusgo`, conditional proxy/firmware repos | Optional interrogation surfaces on proven transports |
| `M8` | Optional-later broadcast lane: `FF 01`, `07 FF`, policy hardening | `helianthus-ebusgateway` | Extended good-citizen signaling with explicit `07 FF` cadence floor |
| `M9` | GraphQL/HA optional consumer parity | `helianthus-ebusgateway`, `helianthus-ha-integration` | Stable consumer surfaces |
| `M10` | Real-bus validation, transport matrix, rollback criteria | all touched repos | Deployment-grade proof |

## Cross-Repo Ordering

- `M3`: `ISSUE-REG-01` lands first; `ISSUE-GW-03` consumes afterward.
- Pre-`M4`: `ISSUE-GW-JOIN-01` lands before `ISSUE-GW-NM-01`.
- `M5`: `ISSUE-REG-02` lands first if still required; `ISSUE-GW-NM-03` and
  `ISSUE-GW-NM-04` consume afterward.
- `M6`: gateway-only unless implementation falsifies the lower-layer
  broadcast-path assumption.

## Canonical Issues

| ID | Repo | Summary |
| --- | --- | --- |
| `ISSUE-DOC-00` | `helianthus-docs-ebus` | Integrate official NM and OSI 7 services into Helianthus normative docs |
| `ISSUE-DOC-01` | `helianthus-docs-ebus` | Discovery realignment and indirect-NM interpretation |
| `ISSUE-DOC-02` | `helianthus-docs-ebus` | Local participant behavior, transport capability matrix, and bus-load policy |
| `ISSUE-GO-01` | `helianthus-ebusgo` | Raw read-only transceive/capture primitive set |
| `ISSUE-GO-01A` | `helianthus-ebusgo` | Responder feasibility spike for slave-address listening/reply |
| `ISSUE-REG-01` | `helianthus-ebusreg` | `PhysicalDevice + BusFace + CompanionPair` identity model |
| `ISSUE-REG-02` | `helianthus-ebusreg` | Registry support for face-aware views consumed by gateway NM/discovery |
| `ISSUE-GW-00` | `helianthus-ebusgateway` | Raw MCP contention strategy versus semantic poller and active bus use |
| `ISSUE-GW-01` | `helianthus-ebusgateway` | Raw MCP capture/list/replay surfaces |
| `ISSUE-GW-02` | `helianthus-ebusgateway` | Optional active raw transceive after contention proof |
| `ISSUE-GW-03` | `helianthus-ebusgateway` | MCP registry `devices.*` alias-address parity and snapshot lookup correctness |
| `ISSUE-GW-JOIN-01` | `helianthus-ebusgateway` | Integrate gateway address-selection authority with Joiner output where available; expose local master/slave pair provenance to NM runtime |
| `ISSUE-GW-NM-01` | `helianthus-ebusgateway` | NM state machine: `NMInit/NMReset/NMNormal`, start flag, target-configuration population, self entry |
| `ISSUE-GW-NM-02` | `helianthus-ebusgateway` | Default/override cycle-time model, passive/active/self event bridge, status chart, and net-status computation |
| `ISSUE-GW-NM-03` | `helianthus-ebusgateway` | NM MCP surfaces with provenance and confidence markers |
| `ISSUE-GW-NM-04` | `helianthus-ebusgateway` | Discovery integration with passive evidence and NM runtime |
| `ISSUE-GW-NM-05` | `helianthus-ebusgateway` | Mandatory broadcast lane: `FF 00` and `FF 02` (`FE 01` explicitly out of lock baseline) |
| `ISSUE-GW-NM-06` | `helianthus-ebusgateway` | Optional broadcast lane: `FF 01` and `07 FF` with explicit cadence floor |
| `ISSUE-GW-NM-07` | `helianthus-ebusgateway` | Local participant responder integration for `07 04` and `FF 03/04/05/06` |
| `ISSUE-PROXY-01` | `helianthus-ebus-adapter-proxy` | Conditional responder-path mediation if transport spike requires it |
| `ISSUE-HA-01` | `helianthus-ha-integration` | Optional NM consumer entities once API is stable |

## Acceptance Criteria

- Helianthus normative docs explicitly state why it is implementing optional
  eBUS NM and how that maps to the official specs.
- Raw frame capture is available via MCP without depending on `ebusd`.
- If active raw transceive ships, it does so only with an explicit contention
  strategy and proof that it does not regress poller behavior.
- The gateway NM runtime maintains the locked state model and exposes the
  runtime-selected local address pair with provenance.
- The timer-reset event bridge includes passive observed traffic, active
  responses, successful local transactions for `self`, and observability-loss
  signals from passive disconnect/discontinuity events.
- Discovery promotion and staleness use passive/runtime evidence rather than
  startup scan plus coarse periodic rescan alone.
- `FF 00` and `FF 02` are rollout-gated and `FF 00` emits only after a valid
  active local master address exists.
- If `FF 02` ships before responder support, its payload-less/partially
  interrogable nature is documented and exposed through MCP surfaces.
- `07 FF`, if shipped, never violates the `>= 10s` cadence floor.
- Responder surfaces ship only on transports proven by `M7a`.
- Cycle-time defaults and overrides are backed by observed cadence artifacts.
- Bus-load budgets are documented, measured, and enforced.

## Risks

| # | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| 1 | Responder lane may require lower-layer changes or firmware/proxy work not visible from gateway code | HIGH | explicit `M7a` feasibility spike and conditional repo expansion |
| 2 | `ebusd-tcp` may be fundamentally incompatible with responder-grade local participant behavior | HIGH | transport-capability gate; do not promise responder support there |
| 3 | Raw active transceive may contend with semantic polling and degrade the bus path | HIGH | capture-first approach and explicit contention strategy issue |
| 4 | Synthetic/runtime NM may overclaim certainty or diverge from the official model | HIGH | gateway-owned state machine aligned to spec; provenance on every exposed edge/value |
| 5 | Face canonicalization may erase evidence needed for topology and RE | HIGH | preserve `BusFace` as first-class model/API entity |
| 6 | Broadcast reset/failure messages from Helianthus may confuse peer devices | HIGH | staged rollout, field validation, and rollback criteria |
| 7 | Cycle-time defaults may be wrong for some nodes and cause false NOK signals | MEDIUM | default-plus-override model with explicit review of live evidence |
| 8 | "Good citizen" may remain vague and unfalsifiable | MEDIUM | freeze numeric bus-load and rollout criteria before lock |
