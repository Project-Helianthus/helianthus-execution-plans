# eBUS Good-Citizen Network Management + Raw MCP

State: `locked`
Slug: `ebus-good-citizen-network-management`
Locked on: `2026-04-10`
Canonical revision: `v1.0-locked`

## Summary

Helianthus should become a standards-aligned eBUS participant, but the plan
must follow the eBUS standard's actual network-management model rather than an
invented probe-centric one.

The critical spec-grounded interpretation is:

- eBUS network management is optional
- eBUS NM is indirect and passive
- NM monitors whether normal cyclic application traffic from monitored nodes
  arrives within configured cycle times
- `FFh 03h/04h/05h/06h` are optional interrogation surfaces that expose NM
  state; they are not the monitoring mechanism itself
- `FFh 00h` and `FFh 02h` are the mandatory NM services for nodes that choose
  to implement NM
- `FFh 01h` and `FFh 03h..06h` remain optional

The plan is split into four lanes:

1. raw eBUS wire visibility via MCP
2. identity and discovery realignment
3. a spec-aligned gateway NM runtime
4. wire-level good-citizen behavior, split into:
   - broadcasts we can originate with initiator mode
   - optional interrogation responses that require slave-address responder mode

This means "good citizen" does not mean "ship everything at once." It means:

- Helianthus deliberately implements optional NM because it improves topology
  visibility, failure signaling, and standards alignment
- the runtime model follows `NMInit -> NMReset -> NMNormal`
- peer `PB=FFh` support is never assumed
- responder-grade features ship only after the transport stack proves it can
  listen and reply on the active local slave address

## Evidence Snapshot

### Proven

- On the live installation, Vaillant addresses `0x15`, `0xEC`, `0x04`, and
  `0xF6` are relevant to the regulator/gateway topology.
- `0xEC` resolves to canonical device `0x15 / BASV2` in the live registry.
- `0xF6` resolves to canonical device `0x04 / NETX3` in the live registry.
- `07 04` identification works through `ebusctl hex -n`.
- Standard NM interrogations through `ebusctl hex -n` against `0x15`, `0xF6`,
  and `0x04` returned empty payloads (`00`) or wire noise, not useful
  `FF03/04/05/06` data.
- Current gateway discovery is not yet aligned with the eBUS NM model. It does
  not maintain:
  - target configuration
  - cycle-time monitoring
  - status chart
  - net status
  - start flag
  - `NMInit -> NMReset -> NMNormal`
- Continuous observation infrastructure already exists in the live codebase:
  passive tap, transaction reconstruction, bounded observability store, and MCP
  bus message listing. The gap is integration into discovery and NM state, not
  the complete absence of passive observation.
- The current active send path already handles broadcast target `0xFE` without
  waiting for slave ACK/response semantics, which supports the gateway-only
  assumption for the first `FF00/FF02` broadcast milestone.
- Portal and GraphQL already preserve alias-address lists. The specific parity
  gap is narrower: `ebus.v1.registry.devices.list/get` serialize `deviceInfo`
  without an alias-address field, and snapshot-mode `findDeviceInfoByAddress`
  searches only the canonical serialized address.

### Hypothesis

- Vaillant does not meaningfully implement `PB=FFh` NM on the observed system,
  so Helianthus must treat peer NM as optional best-effort input, not required
  truth.
- A spec-aligned Helianthus NM runtime can still be useful even when peers do
  not answer `FF03/04/05/06`, because the spec's core model is passive
  cycle-time monitoring of ordinary traffic.
- Local interrogation responder support for `07 04` and `FF03/04/05/06` may
  require transport, proxy, or firmware work that is not currently present in
  the stack.

### Unknown

- Whether the current transport/adapters can safely support full local
  responder mode on the slave address without firmware or proxy work.
- Whether `ebusd-tcp` can ever support responder-grade local participant
  behavior. Current expectation is probably not.
- Whether active raw transceive can coexist with the current semantic poller
  without a new contention policy.
- Whether `FFh 01h` and `07h FFh` should ship in the first broadcast milestone
  or only after field validation of the mandatory subset.

## Problem Statement

The current stack has four architecture gaps:

1. We cannot inspect arbitrary raw frames via first-class MCP surfaces.
2. Discovery is not yet integrated with the spec-aligned NM model.
3. We do not have a gateway NM runtime that tracks:
   - target configuration
   - cycle times
   - status chart
   - net status
   - start flag
   - `NMInit -> NMReset -> NMNormal`
4. We do not behave as a standards-speaking local participant on the wire.

As a result:

- reverse engineering still leans on `ebusd`
- discovery still over-relies on startup scan and explicit probes
- topology evidence is not promoted into a standards-shaped runtime model
- Helianthus is not yet a "good citizen" participant from the point of view of
  eBUS network-management expectations

## Locked Decisions

### 1. Helianthus deliberately implements OPTIONAL eBUS NM

- The eBUS spec makes NM optional.
- Helianthus is choosing to implement it because it materially improves:
  - topology visibility
  - failure detection
  - standards-speaking behavior
  - MCP and reverse-engineering ergonomics
- Peer support remains optional and must never be assumed.

### 2. The Helianthus NM model follows the spec's passive, indirect design

- The internal NM model is not a probe graph.
- The internal NM model is:
  - target configuration
  - cycle-time monitoring
  - per-node status chart (`OK/NOK`)
  - net status summary
  - start flag
  - `NMInit -> NMReset -> NMNormal`
- Monitoring is driven by observation of ordinary cyclic application traffic.
- `NMReset -> NMNormal` is automatic after state initialization. It is not
  gated on receiving a follow-up reset message from another node.
- `FF03/04/05/06` are optional interrogation surfaces over that state.

### 3. Discovery realignment is adjacent to NM, not identical to NM

- Continuous discovery remains necessary, but it is not the same as NM.
- Discovery must fuse:
  - passive `07 04`
  - passive `FF 00`
  - passive `FF 01`
  - observed new cyclic traffic from unseen addresses
  - bounded active confirmation with `07 04`
  - bounded, explicitly indirect `07 FE` use only where justified
- `07 FE` is not treated as an active discovery query with a direct answer. It
  is only an indirect existence/reset signal if used at all.
- `07 FF` sign-of-life is in scope as a later good-citizen emit path because it
  aligns naturally with the NM cycle-time model.

### 4. Identity must distinguish physical devices from bus faces

- The model must separate:
  - `PhysicalDevice`
  - `BusFace` / observed address
  - `CompanionPair`
  - `TargetConfigurationEntry`
  - `NMEdge`
- Alias resolution remains multi-source:
  - direct protocol alias evidence from scan response source/target mismatch
  - serial number
  - MAC address
  - bounded fallback signature (`manufacturer + deviceId + SW + HW`)
- Canonicalization must not erase observed face addresses.
- Portal and GraphQL are already face-capable enough to preserve addresses; the
  required parity work is specifically on MCP registry device serialization and
  snapshot lookup behavior.

### 5. Synthetic NM runtime lives in the gateway

- The NM state machine is runtime state and belongs in `helianthus-ebusgateway`.
- `helianthus-ebusreg` remains an identity/projection layer.
- Registry work is limited to supplying identity, bus-face, and companion-pair
  data that the gateway NM runtime consumes.
- If the gateway later exposes registry projections of NM state, those are
  views over gateway-owned truth, not registry-owned state machines.

### 6. Wire-level good-citizen behavior is split into two lanes

- Lane A: broadcasts we can originate with initiator mode.
- Lane B: interrogation responses that require slave-address responder mode.

#### 6A. Broadcast lane

- Mandatory-first broadcast set:
  - `FF 00` reset status NM on join/reset
  - `FF 02` failure message on monitored-node failure
- Optional-later broadcast set:
  - `FF 01` reset target configuration
  - `07 FF` sign of life
- Broadcast lane does not require responder-mode transport support.
- `FF 00` is emitted only after the gateway has a valid active local master
  address from the address-selection authority.
- Helianthus does not fabricate an `FF 00` before join/address selection has
  completed.
- When a real join or rejoin completes, `FF 00` is emitted from the currently
  active local master address, not from a stale remembered example.
- `FF 02` is payload-less per the wire spec.
- Before responder lane support exists, `FF 02` is therefore a standards-shaped
  failure signal with limited interrogability rather than a detailed report of
  which monitored node failed.

#### 6B. Responder lane

- Local participant self-identification and NM interrogation response are gated
  on responder feasibility.
- This lane includes:
  - targeted `07 04` identification for the Helianthus local participant
  - `FF 03` net status
  - `FF 04` monitored participants
  - `FF 05` failed nodes
  - `FF 06` required services
- The interrogation target is the active local slave address derived from the
  active local master address.
- `0x71 -> 0x76` is only the current installation example, not a locked
  constant.
- This requires a transport/protocol substrate that can:
  - detect incoming frames addressed to the local slave address
  - ACK them
  - emit slave responses
  - receive the final initiator ACK
- This substrate does not exist today as a proven stack capability and needs an
  explicit feasibility spike before lock-to-implementation promotion.

#### 6C. The local address pair is runtime-selected, not hardcoded

- The NM runtime must consume a canonical local address-pair source rather than
  hardcoded constants.
- On transports where gentle join is supported, that source is the Joiner
  result:
  - local master = `JoinResult.Initiator`
  - local slave = `JoinResult.CompanionTarget`
- On transports where gentle join is unavailable or intentionally disabled,
  notably the current `ebusd-tcp` path, the source remains the configured local
  initiator policy plus the derived companion target.
- The plan therefore treats the local address pair as runtime state with
  provenance, not as static configuration baked into the NM model.
- A rejoin that changes the selected local address pair is an NM-relevant event:
  the runtime re-enters `NMInit`, transitions through `NMReset`, and only then
  returns to `NMNormal`.
- Joiner warmup observations are useful seed evidence for discovery/NM, but
  they do not promote devices directly without the normal discovery rules.
- A transport disconnect without a completed rejoin is not treated as a fake
  wire-level NM reset.
- During such a transport gap, the runtime:
  - forces `self` to `NOK`
  - freezes remote-node cycle-time advancement because Helianthus no longer has
    trustworthy observation continuity
  - suppresses new NM-originated broadcasts that require a valid active local
    address
- A transport disconnect by itself does not synthesize `NMInit`.
- A completed join or rejoin does.
- Once transport continuity and address authority are restored through a
  completed join or rejoin:
  - the runtime enters `NMInit`
  - performs the automatic `NMReset -> NMNormal` transition after
    re-initialization
  - resumes monitoring from a fresh observation baseline rather than
    back-filling synthetic failures

#### 6D. `Init_NM` triggers are explicit

- Helianthus enters `NMInit` on:
  - process start
  - first successful acquisition of a valid local address pair
  - completed join or rejoin after transport recovery
  - explicit operator-triggered NM reset
  - configuration changes that invalidate the current target configuration
- A transport disconnect by itself does not invoke `NMInit`; it produces local
  blindness handling until a completed join or rejoin occurs.

### 7. Raw MCP is capture-first and contention-safe

- Raw MCP must remove dependence on `ebusd` for protocol inspection.
- But active raw transceive may collide with or starve the semantic poller if
  it is naively routed through the existing active bus path.
- Therefore the first raw MCP milestone is:
  - capture
  - last-frames listing
  - replay/decode-friendly evidence surfaces
- Active read-only transceive is allowed only after a contention strategy is
  explicitly designed and proven.

### 8. Cycle-time policy must be explicit

- The NM spec allows:
  - one default cycle time for all monitored nodes
  - node-specific cycle times
- The v1 Helianthus plan will start with:
  - a documented default cycle-time model
  - an override table per role/address where the default is clearly wrong
- The lock-baseline default for dynamically enrolled monitored nodes is
  provisionally `120s`.
- Rationale:
  - it is conservative enough to avoid false `NOK` on mixed transports and
    sparse observed traffic
  - it still aligns with the current gateway's minute-scale active runtime
    behavior better than a many-minute fallback
- This `120s` value is a planning default, not a claim that live bus cadence
  has already proved it correct for every monitored node class.
- The first implementation wave must record observed message cadence for the
  monitored node classes it enrolls and either:
  - justify the default against that evidence
  - or attach an explicit override before treating repeated absence as `NOK`
- The model remains `default + override`, not "all nodes behave the same."
- Full arbitrary per-node cycle-time configuration is not required for the
  first lock baseline, but the model must not preclude it.

### 9. Target configuration is discovery-fed and self-inclusive

- The gateway NM target configuration is not a static hardcoded topology.
- The v1 population strategy is:
  - always include the Helianthus local participant as `self`, bound to the
    runtime-selected local address pair
  - dynamically enroll confirmed canonical devices/bus faces that Helianthus
    actively polls, depends on semantically, or has promoted through discovery
  - allow bounded operator/static seed entries where an installation requires
    monitoring before first observation
- When Joiner warmup metrics are available, they seed initial evidence and
  enrollment candidates, but they do not bypass discovery promotion rules.
- The handoff path is:
  - Joiner warmup observation
  - gateway discovery evidence buffer / suspect seeding
  - normal discovery promotion
  - target-configuration enrollment
- Joiner warmup alone does not create device identity; it only seeds address-
  level evidence for later promotion.
- Unconfirmed passive suspects do not enter target configuration directly. They
  must first pass the discovery promotion rules.
- Every target-configuration entry carries:
  - monitored address/face
  - canonical device reference where known
  - enrollment source (`self`, `discovery`, `active-runtime`, `static-override`)
  - cycle time (`default` or explicit override)
- A monitored node's cycle timer resets on either:
  - passive observation of a CRC-valid fully reconstructed application
    transaction whose sender can be attributed to that address/face
  - a successful addressed response to a Helianthus-originated query that
    proves the monitored node is alive, even when the responder identity is
    inferred from transaction structure rather than carried as a request source
  - for `self`, a successfully completed Helianthus-originated bus transaction
    such as a poll read, discovery probe, or NM broadcast
- Passive decode faults do not reset NM cycle timers. They are observability
  evidence, not trusted liveness evidence.
- Passive tap disconnect/discontinuity events are separate observability-loss
  signals that the NM runtime consumes to pause remote-node timing semantics
  without inventing remote silence.

### 10. Self-monitoring is mandatory

- The Helianthus node must appear in its own NM status chart.
- `self` transitions to `OK` when Helianthus successfully completes a local
  bus transaction within its configured cycle time.
- `self` transitions to `NOK` when Helianthus cannot do so within that cycle
  time.
- `self` is keyed to the currently active local address pair, not to a fixed
  literal address.
- This is the intended surface for:
  - transport loss
  - arbitration starvation
  - adapter disconnects
  - self-induced inability to speak on the bus
- The first lock baseline uses the same `120s` default for `self` unless an
  earlier milestone produces proof for a tighter safe override.
- This NM-shaped `self` signal is not the only or fastest transport-health
  detector.
- Existing transport and adapter health surfaces remain responsible for the
  low-latency detection path; NM `self` status is the standards-shaped summary
  surface.

### 11. NM failures and general errors are not the same surface

- This plan implements `FF 02` as the NM-specific failure message because it is
  part of the mandatory NM subset for nodes that choose to implement NM.
- `FE 01` general error broadcast exists in OSI 7, but it is not the same thing
  as NM failure signaling.
- `FE 01` is therefore explicitly out of the first lock baseline unless a later
  doc-gated issue defines a concrete Helianthus-wide error taxonomy and wire
  policy for it.

### 12. Good-citizen behavior must be falsifiable

- "Good citizen" is not accepted as branding language only.
- It must map to measurable contracts:
  - standards-aligned discovery behavior
  - explicit NM state machine behavior
  - explicit reset/failure semantics
  - bounded bus-load policy
  - visible degraded-state behavior
- The bus-load policy must use the eBUS formula from the spec and must freeze a
  numeric Helianthus-originated NM traffic budget before lock.
- For `07 FF`, the first lock baseline sets a hard floor of `>= 10s` between
  emissions, with a more conservative default expected for initial rollout.
- Locked planning assumption:
  - outside reset/rejoin windows: `<= 0.5%` sustained NM-only load
  - during reset/rejoin windows: `<= 2.0%` bounded burst load

## Target Repositories

- `helianthus-docs-ebus`
- `helianthus-ebusgo`
- `helianthus-ebusreg`
- `helianthus-ebusgateway`
- `helianthus-ebus-adapter-proxy` (conditional on responder feasibility)
- `helianthus-ha-integration` (optional later consumer rollout)

Conditional note:

- adapter firmware repo(s) may become follow-up participants if `M7a` proves a
  transport dependency outside the currently enumerated repos

## Delivery Order

1. `helianthus-docs-ebus`
2. `helianthus-ebusgo`
3. `helianthus-ebusreg`
4. `helianthus-ebusgateway`
5. conditional proxy / firmware work if required by responder feasibility
6. optional consumer rollout

`M7a` may begin as soon as `M1` provides the minimum lower-layer substrate. It
is allowed to run in parallel with `M2a` through `M5`, but it gates only
`M7b`, not the internal NM runtime or broadcast lane.

`ISSUE-GW-JOIN-01` is a pre-`M4` gateway prerequisite. The NM runtime must
take its local master/slave pair from the gateway's address-selection
authority, preferring Joiner output where the transport supports gentle join
and falling back to the documented configured-source path where it does not.

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

Cross-repo ordering inside milestones:

- `M3`: `ISSUE-REG-01` lands first in `helianthus-ebusreg`; `ISSUE-GW-03`
  consumes that shape afterward in `helianthus-ebusgateway`.
- Pre-`M4`: `ISSUE-GW-JOIN-01` lands before `ISSUE-GW-NM-01` so the NM
  runtime consumes a runtime-selected local master/slave pair instead of fixed
  example addresses.
- `M5`: `ISSUE-REG-02` lands first if additional face-aware registry views are
  still required; `ISSUE-GW-NM-03` and `ISSUE-GW-NM-04` consume that support
  afterward in `helianthus-ebusgateway`.
- `M6`: the planning assumption is gateway-only because broadcast-capable send
  support already exists in the lower layer; if implementation falsifies that,
  the plan must add a new lower-layer issue instead of smuggling the change
  into the milestone silently.

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
- The gateway NM runtime maintains:
  - a runtime-selected local master/slave pair with provenance
  - documented target-configuration population rules
  - target configuration
  - cycle times
  - self-monitoring
  - status chart
  - net status
  - start flag
  - `NMInit/NMReset/NMNormal`
- The NM runtime resets cycle timers from a defined event bridge that includes:
  - passive observed traffic
  - active responses
  - successful Helianthus-originated local bus transactions for `self`
- Passive disconnect/discontinuity events from the observability path are fed
  into the NM runtime as local-blindness signals distinct from remote-node
  absence.
- On transports that support gentle join, the NM runtime consumes the current
  local address pair from `JoinResult`; on transports that do not, the fallback
  address source is explicit and documented.
- A transport disconnect without completed rejoin:
  - forces `self` to `NOK`
  - pauses remote-node cycle-time advancement
  - does not synthesize fake remote-node failures solely from local blindness
- NM MCP surfaces expose the active local address pair and its provenance.
- Face addresses such as `0x15/0xEC` and `0x04/0xF6` remain first-class
  evidence in the runtime model and in MCP registry device surfaces.
- Discovery no longer depends on startup scan plus coarse periodic rescan
  alone; passive/runtime evidence participates in promotion and staleness.
- `FF 00` and `FF 02` broadcasts are implemented behind explicit rollout gates.
- `FF 00` is emitted only after the gateway has a valid active local master
  address.
- If `FF 02` ships before responder lane support, the documentation and MCP
  surfaces explicitly state that the signal is payload-less and only partially
  interrogable until `FF03/04/05/06` exist.
- If `07 FF` ships, its emitted cadence never violates the lock baseline floor
  of `>= 10s`.
- Interrogation responder support (`07 04`, `FF03/04/05/06`) ships only on
  transports proven by `M7a`; if `ebusd-tcp` cannot support it, that
  incompatibility is explicit and documented rather than hand-waved.
- The bus-load budget for Helianthus-originated NM traffic is documented,
  measured, and enforced.
- Remote-node cycle-time defaults and overrides are backed by observed cadence
  artifacts for the enrolled node classes, not by assumption alone.

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
