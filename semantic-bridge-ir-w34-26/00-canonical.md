# Helianthus Semantic Bridge IR and Multi-Projection Registry

Status: draft execution guide

Plan issue: Project-Helianthus/helianthus-execution-plans#93

Prepared: 2026-08-17

Implementation state: not started

Hard stop: publication or merge of this plan does not start implementation

## 1. Objective

Build a protocol-neutral semantic registry for the Helianthus bridge as a
stable, typed intermediate representation between southbound device runtimes
and any number of northbound protocol or API projections.

The model is a semantic superset, not a least-common denominator. Southbound
drivers preserve every native fact, capability, operation and derivation that
can be established. Northbound bindings select only what their target protocol
and version can represent and report every omission, approximation or policy
block explicitly.

The first three runtime families are:

- eBUS, including standard services, vendor-specific profiles, B509 and the
  Vaillant B524 regulator aggregation surface;
- EEBUS, including SHIP, SPINE, use-case discovery, features and mutations;
- Modbus, including standard SunSpec families and evidence-backed vendor
  profiles.

The architecture must remain open to later CAN BMS, OCPP-native, GREE, BACnet,
KNX and other drivers without changing the semantic kernel, gateway bootstrap
or existing northbound contracts.

### 1.1 Release target and activation conditions

The coordinated rewrite delivers **Helianthus Bridge 0.7.0**. The product
release includes the vNext gateway/add-on composition and a release bill of
materials for the exact HSIR and three driver-family dependencies.

Execution of this plan begins only after both prerequisite programs are
complete and reconciled against current GitHub state:

1. the current minimal Modbus program is complete for the declared SunSpec,
   Fronius and Huawei scope, with its owning tests, docs and qualification
   evidence green;
2. the current EEBUS implementation is finalized/completed at its declared
   runtime, API, interoperability and documentation boundary.

The prerequisites are implementation baselines, not HSIR coverage substitutes.
This plan still owns the later exhaustive semantic catalogs and vNext driver
rewrite.

If either prerequisite is incomplete, unstable, has an active overlapping
gateway/add-on/Modbus write-set, or lacks a reproducible green baseline, plan
execution waits. The earlier operator-supplied lane snapshot is a coordination
hint only and must be refreshed at activation.

The M4-04 gateway fix is merged on gateway main at
`6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b` and becomes the gateway baseline
for M0. Before vNext work starts, the follow-on legacy add-on 0.6.51 release
must complete its strictly bounded repin, version, provenance, changelog and
test work, publish/deploy, and read-only M4-04 validation. That stabilization
release does not create an HSIR or DriverManager runtime lane.

Version 0.7.0 is the functional architecture and cutover release. A mandatory
post-0.7 cleanup wave follows stabilization; it is not mixed into the semantic
rewrite before cutover. That wave covers production code and the test corpus:
large or mixed-responsibility tests, opaque internal identifiers and test names
that do not state the behavior under verification.

## 2. Architectural decision

The public contract is named **Helianthus Semantic Intermediate Representation
(HSIR)**.

HSIR is an intermediate representation language in the same sense that a
compiler IR is a typed, versioned interchange model between producers and
consumers. It is declarative, not a general-purpose programming language. Its
language elements are:

- stable resource and topology identities;
- typed observations, states, capabilities and operations;
- exact quantities, time, quality and uncertainty;
- source bindings and native evidence references;
- provenance and transformation graphs;
- versioned capability packs;
- internal relation planes and purpose-specific lenses;
- deterministic presentation-selection records;
- projection manifests and loss reports;
- bidirectional semantic operation requests and results.

The protocol-neutral code owner is a new public repository:

~~~text
Project-Helianthus/helianthus-semreg
~~~

The kernel must import no gateway, transport, eBUS, EEBUS, Modbus, Matter,
EVCC, OCPP, GraphQL or vendor package. Protocol runtimes and northbound
projectors import HSIR contracts, never the reverse.

## 3. Product boundary

Helianthus Bridge and the future white-box ESCO regulator are separate
products.

~~~mermaid
flowchart LR
    Native["Native devices and buses<br/>eBUS, EEBUS, Modbus, future CAN"]
    Drivers["Southbound drivers<br/>decode, map, preserve evidence"]
    Bridge["Helianthus Bridge<br/>HSIR registry and projections"]
    Bindings["Northbound bindings<br/>GraphQL, EEBUS, Matter, EVCC, OCPP"]
    Smart["Smart home and Home Assistant"]
    Regulator["Future white-box ESCO regulator"]
    Dispatcher["Energy dispatcher or aggregator"]

    Native --> Drivers
    Drivers --> Bridge
    Bridge --> Bindings
    Bindings --> Smart
    Bindings --> Regulator
    Bindings --> Dispatcher
    Regulator --> Bindings
    Dispatcher --> Bindings
~~~

### 3.1 Bridge responsibilities

The bridge:

- discovers and supervises driver instances;
- ingests typed semantic candidates and source shadows;
- preserves source identity, fidelity, time, quality and lineage;
- selects one explained default presentation when equivalent representations
  exist;
- exposes all alternatives on privileged diagnostic surfaces;
- projects semantic subsets into target protocols and APIs;
- validates and routes externally requested operations;
- serializes writes per native actuator;
- checks capabilities, gates, preconditions, idempotency and deadlines;
- prevents bounded command and event feedback loops;
- reports protocol acknowledgement and readback evidence separately.

The bridge does not:

- optimize energy use;
- choose comfort, price, carbon or grid objectives;
- generate dispatch schedules autonomously;
- decide which legitimate external controller should win;
- convert a tariff or forecast into a setpoint;
- implement portfolio or ESCO tenant policy.

### 3.2 Future regulator responsibilities

The future ESCO regulator:

- consumes one or more bridges;
- calculates objectives, forecasts, schedules and dispatch;
- coordinates customer preference, tariffs, grid constraints and comfort;
- claims or receives control authority through an explicit external contract;
- issues semantic operation requests;
- handles indeterminate outcomes and recovery policy;
- provides white-label tenancy, explainability and audit.

HSIR may represent Schedule, Forecast, Tariff, Constraint and PreferencePolicy.
On the bridge these are transported semantic documents. Their presence in the
type system does not authorize the bridge to create or prioritize them.

## 4. Layering and dependency direction

~~~mermaid
flowchart TB
    Transport["Transport and protocol engines"]
    NativeRegistry["Native registries and profiles"]
    Driver["Complete runtime driver"]
    HSIR["helianthus-semreg<br/>HSIR kernel and packs"]
    Host["Gateway host<br/>DriverManager and registry runtime"]
    Projection["Northbound projection engine"]
    Consumers["Consumers and external controllers"]
    Evidence["Protected native evidence stores"]

    Transport --> NativeRegistry
    NativeRegistry --> Driver
    HSIR --> Driver
    HSIR --> Host
    Driver --> Host
    Host --> Projection
    HSIR --> Projection
    Projection --> Consumers
    Driver --> Evidence
    Evidence -. reference only .-> HSIR
~~~

Required dependency invariants:

1. HSIR is a dependency leaf.
2. A complete driver may import its protocol engine, native registry and HSIR.
3. The gateway host owns lifecycle and composition, not protocol semantics.
4. A northbound projector imports HSIR and its target protocol only.
5. A southbound driver imports no northbound projector or consumer.
6. Raw frames, Modbus words, SPINE payloads and private identifiers remain in
   evidence stores; HSIR carries typed facts and access-controlled references.
7. No pairwise eBUS-to-Matter, Modbus-to-EEBUS or similar translator is
   permitted outside the HSIR boundary.

## 5. HSIR kernel

The stable kernel is deliberately smaller than the domain vocabulary.

| Kernel type | Purpose |
|---|---|
| ResourceID | Opaque stable identity independent of protocol address or path |
| EnergyResource | Physical, logical or virtual semantic resource |
| Terminal | Electrical, hydraulic, thermal, air or other connection point |
| TopologyEdge | Typed relation between resources or terminals |
| FactKey | Exact identity of an observable semantic property |
| ObservationNode | One immutable observation from one source binding |
| StateEvent | Time-qualified semantic state transition |
| SourceBinding | Mapping between one native path and one semantic claim |
| TransformationActivity | Cache, conversion, quantization, aggregation or derivation |
| CandidateFactSet | All representations that may describe one FactKey |
| CanonicalFactEnvelope | Default presentation plus alternatives and explanation |
| CapabilitySnapshot | Instance capability, constraints and evidence state |
| SemanticOperation | Typed readable, writable or actionable affordance |
| SemanticOperationRequest | Externally originated request to execute an affordance |
| CommandResult | Admission, dispatch, acknowledgement and verification result |
| Schedule | Time-indexed target or availability document |
| Forecast | Time-indexed expected quantity or state document |
| Tariff | Price or incentive document with scope and provenance |
| ProjectionManifest | Versioned source-to-target mapping inventory |
| ProjectionReport | Per-emission loss and omission explanation |
| ExtensionCapsule | Typed namespaced forward-compatible extension |

### 5.1 Identity

ResourceID is an opaque installation-scoped identifier. It must not be derived
from:

- eBUS address;
- SPINE entity path;
- Modbus unit/register;
- Service plane path;
- gateway host/port;
- a northbound endpoint number.

Native addresses and existing Service paths become aliases and source
bindings. This replaces the current eBUS projection invariant in which node
identity is derived from the canonical Service path while preserving those
paths as compatibility aliases.

Identity linking has explicit states:

~~~text
unlinked
candidate
proven_equivalent
proven_distinct
conflicted
retired
~~~

No value similarity may promote candidate identity to proven equivalence.

### 5.2 FactKey

FactKey includes all dimensions needed to prevent false equivalence:

~~~text
subject resource
property identifier
measurement or control point
terminal and location
reference frame and direction
phase
aggregation or counter basis
temporal basis
capacity, reserve or SoC basis where applicable
~~~

Examples that remain distinct:

- BMS offered charge limit versus inverter-applied limit;
- DC battery power versus AC converted power;
- raw pack SoC versus reserve-adjusted usable SoC;
- cumulative energy versus session energy;
- physical room temperature versus a controller estimate.

### 5.3 Exact quantity and time

Quantities use exact coefficient plus decimal exponent, dimension, canonical
unit and retained source unit/scale. Binary floating point alone is not a
reconstruction contract.

Every observation distinguishes:

- phenomenon time, when supplied by the original source;
- source read time;
- cache refresh time, when known;
- publisher report time;
- gateway receive time;
- clock domain and uncertainty.

A recent gateway receive time never fabricates a recent phenomenon time.

Quality is orthogonal:

- validity;
- freshness;
- source-reported quality;
- accuracy and resolution;
- estimated or derived status;
- completeness;
- time quality;
- contradiction state.

## 6. Source bindings and provenance

One driver can publish many SourceBindings for the same FactKey.

~~~text
SourceBindingV1
  binding_id
  driver_instance_id
  driver_generation
  native_identity
  publisher_endpoint
  subject_resource
  fact_key
  view_kind
  origin_assertion
  lineage_parents
  transform_chain
  fidelity
  source_time_contract
  profile_version
  capability_conditions
  read_role
  write_role
  native_evidence_ref
~~~

Allowed view kinds:

~~~text
direct_measurement
device_owned_state
controller_cache
mirror
aggregate
derived
estimated
command_endpoint
command_echo
unknown
~~~

Provenance relations are evidence-qualified:

~~~text
exact_same_phenomenon
derived_from
aggregate_of
possibly_same
distinct
unknown
~~~

Lineage uses a directed acyclic graph. A mapping that depends on its own
ResolvedFact or descendant is rejected as a provenance cycle.

Minimum transformation activities:

~~~text
cache
quantize
filter
smooth
unit_normalize
enum_coarsen
aggregate
clip
reserve_adjust
estimate
protocol_republish
~~~

Each activity records algorithm/version, inputs, output, parameters, loss
class, error bound, source-age behavior and evidence.

### 6.1 eBUS example

The eBUS driver must retain parallel native bindings rather than force one
protocol-wide precedence:

~~~mermaid
flowchart LR
    Boiler["Boiler or sensor state"]
    Standard["Standard eBUS service<br/>legacy or cross-vendor"]
    B509["Vendor and generation-specific B509"]
    Regulator["Vaillant regulator worldview"]
    B524["B524 aggregated controller view"]
    Driver["eBUS driver"]
    Fact["HSIR CandidateFactSet"]

    Boiler --> Standard
    Boiler --> B509
    Boiler --> Regulator
    Regulator --> B524
    Standard --> Driver
    B509 --> Driver
    B524 --> Driver
    Driver --> Fact
~~~

B524 is the regulator-side aggregation surface for the system structure known
to that regulator. It may be device-owned state for regulator configuration
and a cached or aggregated representation for boiler, circuit or sensor data.
B509 identifiers may differ by brand, product and generation. Older equipment
may expose a standard eBUS service instead.

Therefore the mapping catalog is keyed by observed profile evidence and the
individual semantic property. There is no global B524-over-B509,
B509-over-standard or vendor-over-standard rule.

### 6.2 BMS and inverter example

The future CAN BMS case is an architecture fixture, not a fourth driver
implementation milestone.

~~~mermaid
flowchart LR
    Cells["Cell sensing"]
    BMS["BMS state and algorithms"]
    CAN["Future CAN BMS driver"]
    Cache["Inverter BMS cache"]
    Modbus["Modbus inverter driver"]
    HSIR["HSIR facts"]

    Cells --> BMS
    BMS --> CAN
    BMS --> Cache
    Cache --> Modbus
    CAN --> HSIR
    Modbus --> HSIR
~~~

The BMS binding is normally closest to cell telemetry, pack-internal state,
faults and permissible DC limits. The inverter binding is closest to MPPT,
conversion, AC measurements, grid state and applied PCS limits. An inverter
copy of BMS SoC shares a provenance cohort only when its basis and derivation
are proven. A reserve-adjusted or display SoC is a separate FactKey.

## 7. Presentation selection, not regulation

The bridge produces one CanonicalFactEnvelope for ordinary consumers while
preserving CandidateFactSet for diagnostics and advanced clients.

~~~text
CandidateFactSetV1
  fact_key
  candidates
  equivalence assertions
  derivation assertions

CanonicalFactEnvelopeV1
  fact_key
  effective_observation
  alternatives
  origin cohort
  lineage summary
  freshness and fidelity
  selection reason
  policy version
  resolution epoch
~~~

The deterministic selection process:

1. require proven semantic identity;
2. reject withdrawn driver generations;
3. reject unusable or unvalidated observations;
4. calculate real source-age bounds without receipt-time laundering;
5. collapse representations from one origin cohort to the least-loss eligible
   observation;
6. compare independent origin cohorts only after time alignment;
7. select the declared source-of-record representation for that property;
8. report conflicts and alternatives without hiding them.

This is epistemic presentation selection. It does not choose a control
objective or generate a command.

Required selection states:

~~~text
direct
mirrored_exact
mirrored_bounded
mirrored_age_unknown
derived_lossy
conflicted
stale
unavailable
~~~

Statistical fusion is opt-in and creates a new DerivedObservation with
lineage. It is never the generic duplicate-resolution strategy.

## 8. Internal planes and lenses

A plane is a named set of typed relations over the same ResourceIDs. It is not
a separate registry or source of truth.

~~~mermaid
flowchart TB
    Graph["One canonical HSIR graph"]
    Service["ServiceRuntime plane"]
    Physical["Physical plane"]
    Flow["FlowTopology plane"]
    Observe["Observability plane"]
    Control["Control plane"]
    Source["SourceEvidence plane"]
    Dependency["DependencyImpact plane<br/>later optional"]

    Graph --> Service
    Graph --> Physical
    Graph --> Flow
    Graph --> Observe
    Graph --> Control
    Graph --> Source
    Graph -.-> Dependency
~~~

| Plane | Primary relationships |
|---|---|
| ServiceRuntime | driver hosts, discovers, publishes, depends-on-runtime |
| Physical | has-part, installed-at, inside-enclosure, serves-zone |
| FlowTopology | terminals, connections and direction by energy/material carrier |
| Observability | observes, meters, derived-from, corroborates, contradicts |
| Control | controls, actuates, constrains, exposes-operation |
| SourceEvidence | decoded-from, normalized-as, projected-as, validated-by |
| DependencyImpact | availability, communication, safety and measurement dependency |

FlowTopology is parameterized by carrier:

~~~text
electricity_ac
electricity_dc
heat
water
air
refrigerant
gas
fuel
~~~

Lenses are query definitions over multiple planes:

| Lens | Composition |
|---|---|
| Diagnostics | ServiceRuntime + Observability + SourceEvidence + faults |
| CircuitMapping | electrical FlowTopology + Physical + meters |
| EnergyManagement | FlowTopology + capabilities + schedules + forecasts + tariffs |
| DemandManagement | EnergyManagement + constraints + external requests |
| Compliance | capability evidence + target/version conformance |
| Dispatcher | site/GCP topology + flexibility + sessions + operations |

Plane invariants:

- one opaque ResourceID in every plane;
- no copied mutable properties;
- one canonical revision token for a multi-plane snapshot;
- versioned plane definitions;
- lineage for derived edges;
- caches are rebuildable and never authoritative;
- plane membership grants neither access nor commandability.

## 9. Versioned capability packs

The kernel is stable. Domain growth occurs through versioned packs.

| Family | Initial packs |
|---|---|
| Core | identity-topology, quantity-quality-time, source-lineage, capability-gates, command-lifecycle, driver-lifecycle |
| Electrical | measurement, energy-counters, power-quality, electrical-topology, grid-conditions-limits |
| Flexibility | tariff-price-incentive, forecast-schedule, energy-preference, DER-control-curves |
| EVSE | asset-connector, session-metering, targets-schedules, authorization, V2X |
| BESS | asset-cells, state-health, control, grid-services |
| Solar | array-string-MPPT, inverter-measurement, DER-control, hybrid-PCS |
| Thermal | temperature-setpoint, HVAC-operation, heat-pump, water-heater-DHW, fan-pump-flow, hydronic-circuit |
| Environment | IAQ-occupancy-context |
| Appliance | operational-flexibility |

If an upstream construction does not fit without invented equivalence, the
pack is extended or a new pack is versioned. It is not flattened into a generic
value.

Capability evidence progresses through:

~~~text
schema_known
observed
decoded
validated
commandable
~~~

Commandable additionally requires a current instance generation, inverse
binding, access authority, safety/precondition checks and conformance evidence.

## 10. Southbound DriverV1

A driver maps native state and operations into HSIR and is unaware of every
northbound consumer.

Conceptual contract:

~~~text
DriverV1
  Descriptor
  Start
  Stop
  Snapshot
  Capabilities
  Execute

SemanticPublisherV1
  UpsertResource
  PublishObservation
  PublishStateEvent
  PublishCapability
  PublishOperation
  WithdrawGeneration
~~~

Drivers may keep transport and protocol sessions internally. They do not own
global energy policy, presentation projections or consumer-specific DTOs.

### 10.1 drivers.v1 lifecycle

~~~text
desired_state = running | stopped

observed_state =
  registered | starting | running | degraded |
  stopping | stopped | failed | backoff
~~~

Required behavior:

- desired state persists;
- observed state is runtime-derived;
- list/get/start/stop/restart are typed control operations, not diagnostic
  hints;
- start, stop and restart are idempotent, require expected revision plus an
  idempotency key and do not restart the gateway process;
- every start/restart creates a new driver generation;
- capability publication is generation-bound;
- stop/failure atomically withdraws the active generation and successful
  start/restart atomically republishes the new generation;
- a driver panic/startup/restart error cannot terminate the gateway;
- gateway API and health start before and independently from all configured
  drivers;
- gateway readiness permits per-driver stopped, failed or degraded state;
- cleanup, retry, backoff and circuit breaking are bounded;
- MCP and HTTP expose typed list/get/start/stop/restart;
- Portal exposes start/stop/restart controls with current revision and typed
  result;
- Home Assistant exposes response-only switches/buttons/services that call
  drivers.v1 and never access a driver directly;
- every surface returns desired state, observed state, revision, generation,
  health and the command result.

DriverManager and these controls exist only in the vNext HSIR gateway. The
legacy gateway receives no new lifecycle manager or driver-control surface.

## 11. Bidirectional semantic operations

Northbound adapters translate a target-specific command into one
SemanticOperationRequest. The bridge validates and routes it to exactly one
native RouteBinding.

~~~mermaid
sequenceDiagram
    participant C as External controller
    participant N as Northbound projector
    participant S as HSIR operation service
    participant R as Route resolver
    participant D as Southbound driver
    participant X as Native device

    C->>N: Matter, EEBUS, EVCC, GraphQL or OCPP request
    N->>S: SemanticOperationRequest
    S->>S: Schema, access, capability, generation and precondition checks
    S->>R: Resolve one RouteBinding
    R->>D: Execute typed native operation
    D->>X: Native write or action
    X-->>D: Protocol response
    D-->>S: acknowledged or indeterminate
    D->>X: Optional readback
    X-->>D: Observed postcondition
    S-->>N: CommandResult
    N-->>C: Target-specific result
~~~

SemanticOperationRequest carries:

~~~text
ingress adapter instance
principal and externally supplied authority context
semantic target and operation
typed arguments
correlation and causation IDs
idempotency key
expected fact revision
deadline
~~~

It does not carry bridge-generated optimization or priority.

CommandResult distinguishes:

~~~text
accepted
rejected
dispatched
protocol_acknowledged
readback_verified
failed
indeterminate
~~~

Writes never fan out across B524, B509 and a standard service. Fallback is
allowed before dispatch, or after a provably non-delivered/idempotent attempt.
An ambiguous timeout returns indeterminate and is not automatically retried
through another binding.

### 11.1 Loop and echo prevention

Every operation/event that can retain metadata carries a causality envelope:

~~~text
semantic event ID
correlation ID
causation ID
origin adapter instance
hop trace
projection revision
bounded TTL
~~~

An EmissionLedger provides bounded deduplication when a protocol loses part of
the envelope. The bridge may serialize an actuator, reject stale preconditions
and report controller conflict. It must not decide which external controller
objective should win.

## 12. Projection IR

Internal planes are lossless views of HSIR. Northbound projections are
target-version mappings and may be lossy.

Each ProjectionManifest row records:

~~~text
source pack/type/path/version
target protocol/profile/version/path
forward transform
inverse transform or explicit none
required capabilities and gates
loss disposition
quantization/error bound
test-vector IDs
source-shadow reference
~~~

Allowed dispositions:

~~~text
exact
normalized_lossless
quantized_with_bound
derived_with_lineage
defaulted
native_only
omitted_unsupported
omitted_policy
blocked_authorization
withheld_unproven
~~~

An advertised target capability is the intersection of:

~~~text
active southbound capability
target-version representability
current bridge access and safety admission
proven inverse operation binding for writes
~~~

Unknown terms fail closed for mutation.

### 12.1 Target projections

| Target | Intended surface |
|---|---|
| GraphQL M2M | Rich typed resources, planes, facts, provenance, capabilities, operations and subscriptions |
| MCP | Prototype, diagnostics, reverse engineering, raw/source-shadow access and semantic inspection |
| EEBUS northbound | Actor/use-case/SPINE subset with feature and scenario gates |
| Matter | Device types, clusters, feature maps, attributes, events and commands by exact revision |
| EVCC | Optional device interfaces for meters, PV, BESS and chargers |
| SunSpec northbound | Model ID/revision-specific register projection |
| OCPP | Separate 2.0.1 and 2.1 station/CSMS, transaction, smart charging and DER surfaces |
| Portal | Operator and reverse-engineering views |
| Home Assistant | Stable GraphQL-derived entities, controls and diagnostics |

No projector imports native driver types. No driver emits target-specific
objects.

EEBUS northbound is a real local SPINE server projection. It materializes
local server entities and features, advertises only supported use cases,
implements SPINE read and subscribe behavior and exposes only commands whose
HSIR operation, authority, safety, precondition and conformance gates are
currently true. GraphQL or MCP must never be described as EEBUS northbound
merely because they expose EEBUS-originated facts.

## 13. Consumer concepts

### 13.1 Smart home and Home Assistant

~~~mermaid
flowchart LR
    Bridge["One site bridge"]
    Matter["Matter projection<br/>certifiable smart-home subset"]
    EEBUS["EEBUS projection<br/>local HEMS actors/use cases"]
    GraphQL["GraphQL M2M<br/>full-fidelity stable API"]
    HA["Home Assistant integration"]
    Smart["Smart-home controllers"]
    HEMS["Third-party HEMS"]

    Bridge --> Matter --> Smart
    Bridge --> EEBUS --> HEMS
    Bridge --> GraphQL --> HA
~~~

Matter receives only representable device/cluster capabilities. EEBUS receives
only supported actors, features and use cases. Home Assistant consumes stable
GraphQL facts and operations and receives diagnostic quality without raw
register awareness.

### 13.2 White-box ESCO regulator

The regulator may consume one or many customer bridges through GraphQL M2M,
EEBUS or another supported standard. GraphQL M2M is the reference full-fidelity
surface because it can expose CandidateFactSet, provenance, constraints and
operation lifecycle without target-standard loss.

~~~mermaid
flowchart TB
    B1["Customer bridge A"]
    B2["Customer bridge B"]
    B3["Customer bridge C"]
    API["Stable semantic M2M contract"]
    Reg["White-box ESCO regulator<br/>external product"]
    Decisions["Schedules, constraints and operation requests"]

    B1 --> API
    B2 --> API
    B3 --> API
    API --> Reg
    Reg --> Decisions
    Decisions --> API
~~~

The bridge exposes what can be controlled and the current constraints. The
regulator decides what should be controlled.

### 13.3 Energy dispatcher and aggregator

The bridge is suitable for small PV parks, prosumer sites, BESS installations,
EV charging stations and hybrid sites.

~~~mermaid
flowchart LR
    Site1["Prosumer<br/>PV + meter"]
    Site2["Small PV park<br/>inverters + weather"]
    Site3["Charging site<br/>EVSE + meter + BESS"]
    Bridge1["Bridge"]
    Bridge2["Bridge"]
    Bridge3["Bridge"]
    Dispatcher["Energy dispatcher or aggregator"]
    Grid["Grid and market interfaces"]

    Site1 --> Bridge1
    Site2 --> Bridge2
    Site3 --> Bridge3
    Bridge1 --> Dispatcher
    Bridge2 --> Dispatcher
    Bridge3 --> Dispatcher
    Dispatcher --> Grid
    Dispatcher --> Bridge1
    Dispatcher --> Bridge2
    Dispatcher --> Bridge3
~~~

The dispatcher-facing semantic surface includes:

- stable site and GCP identity;
- electrical topology and meter placement;
- actual and available power;
- import/export energy with counter basis;
- PV, BESS and EVSE capability envelopes;
- schedules, forecasts and externally requested limits;
- sessions and transactions where applicable;
- command results and postcondition evidence;
- time, accuracy, freshness and source lineage.

Fleet optimization, bidding, dispatch selection and market policy remain
outside every bridge.

## 14. Standards coverage

The implementation is complete only when every upstream element has an
explicit versioned disposition.

### 14.1 EEBUS

Baseline SPINE 1.3 inventory:

- 32 FeatureType values;
- 143 FunctionType values;
- 48 EntityType values;
- 36 UseCaseName values.

Every element receives a row:

~~~text
source version and identity
canonical type/capability pack
source binding and transformation
evidence state
northbound projection disposition
test vectors
~~~

The canonical catalog and runtime materialization are separate:

- the versioned catalog covers all 32 FeatureType, 143 FunctionType, 48
  EntityType and 36 UseCaseName values plus a diff to the latest accessible
  normative revision;
- every catalog element has a typed HSIR representation, capability-pack
  disposition and projection rule;
- a concrete device materializes only capabilities, entities, features,
  functions, use cases and operations that it advertised or that were
  observed and decoded;
- catalog completeness never fabricates per-device capability support.

The current 18 promoted EEBUS semantic leaves remain a compatibility baseline,
not the final coverage target. Raw SPINE stays separate from canonical HSIR.

### 14.2 Matter

The initial target is the exact Project-Chip machine-readable
data_model/1.6.1 snapshot used by the architecture research, with explicit
provisional status until the matching normative CSA revision is confirmed.

Coverage includes all energy and thermal device types and their applicable
clusters, features, attributes, events and commands, including electrical
measurement, energy, topology, EVSE, device energy management, tariffs,
storage, solar, thermostat, heat pump, water heater, fan, pump and
environmental context.

### 14.3 SunSpec and Modbus

Pin and inventory the full official model catalog at an exact source revision.
Current read-only models remain compatibility fixtures, but the ledger must
classify every model/profile. Model ID and revision are semantic identity.
Missing source timestamps remain absent; receipt time is not substituted.

### 14.4 EVCC and OCPP

EVCC is versioned by release and API commit. OCPP 2.0.1 and 2.1 remain separate
projection targets, including their exact editions and errata. OCPP 2.1 DER
semantics must never be silently flattened into OCPP 2.0.1.

## 15. Big-bang rewrite and cutover

This architecture is a rewrite, not an incremental semantic migration.

The existing gateway remains the frozen production baseline while the complete
HSIR-based vNext stack is built and validated separately. There is no runtime
dual publication, no feature-by-feature activation, no legacy/new semantic
core mixture and no fallback from a vNext driver to a legacy driver inside one
process.

DriverManager, drivers.v1 MCP/HTTP controls, Portal controls and Home Assistant
driver controls are implemented only in vNext. The single cutover activates
HSIR, DriverManager, all configured vNext drivers and all control surfaces in
one release. Whole-release rollback removes them together and returns to the
complete legacy runtime.

Development still follows the repository DAG so that contracts are reviewable,
but production activation is one coordinated cutover.

~~~mermaid
flowchart LR
    Legacy["Frozen legacy release<br/>current gateway and semantic stack"]
    Build["Parallel vNext build<br/>HSIR + gateway + three drivers"]
    Shadow["Offline replay and shadow-lab comparison"]
    Gate["Whole-system cutover gate"]
    VNext["One vNext production release"]
    Rollback["Whole-release rollback<br/>legacy artifact"]

    Legacy --> Build
    Build --> Shadow
    Shadow --> Gate
    Gate --> VNext
    VNext -. failure .-> Rollback
~~~

Rewrite rules:

1. The old semantic implementation accepts no architectural extension beyond
   critical maintenance required to keep the baseline trustworthy.
2. helianthus-semreg and the vNext gateway are greenfield owners of the new
   semantic runtime.
3. eBUS, EEBUS and Modbus implement only the new DriverV1 in the vNext
   composition; the vNext gateway does not adapt a legacy semantic provider.
4. Compatibility is proven offline with shared fixtures, captures and golden
   public responses, not by publishing two live values.
5. All three drivers, the HSIR registry, required planes, public API surfaces
   and operational tooling must be ready before cutover.
6. The final gateway cutover replaces the active semantic/runtime composition
   in one release.
7. A failed cutover rolls back the complete gateway release and configuration,
   never selected semantic components.
8. Legacy internal semantic code remains isolated and rollback-available
   through the stabilization window, then is removed in the M11 cleanup wave
   rather than retained as a compatibility runtime.

The new registry does not import the old semantic cache as truth. It rebuilds
current state from driver discovery and native observations. Historical raw
evidence may be retained under its existing provenance, but stale legacy
derived values are not promoted into HSIR.

vNext persistent state uses a separate namespace and path. Cutover copies or
translates only explicitly documented configuration and identity material; it
does not destructively migrate the legacy semantic cache, EEBUS pairing/trust
state or add-on configuration in place. Untouched legacy state remains usable
by whole-release rollback.

Stable external identity is migrated explicitly:

- preserve the installation gateway instance GUID;
- produce an offline alias manifest from current public paths/entity IDs to
  new opaque ResourceIDs;
- keep public GraphQL field names and HA entity identity where compatibility
  is required;
- treat the alias manifest as compatibility data, not canonical identity.

The cutover gate compares old and new stacks from identical replay inputs and
checks value, unit, identity, availability, freshness, operation result and
public serialization. This comparator is test infrastructure only; it does not
run two semantic stacks in production.

Compatibility requirements:

- no current GraphQL field disappears or changes meaning;
- MCP raw tools remain separate and available;
- Portal keeps raw and semantic diagnostic views;
- HA entity IDs and stable gateway identity do not change;
- last-known-value behavior never converts stale data into fresh data;
- a missing new capability remains unavailable, not remapped to a weaker fact.

## 16. Repository ownership and required changes

### 16.1 New semantic repository

**Project-Helianthus/helianthus-semreg**

Owns:

- HSIR kernel and serialization;
- capability pack schemas;
- ResourceID and identity-link contracts;
- SourceBinding and provenance DAG types;
- candidate/presentation selection contracts;
- planes, lenses and canonical revision rules;
- SemanticOperation and command-result contracts;
- DriverV1 and drivers.v1 public types;
- ProjectionManifest and ProjectionReport;
- schema, property and round-trip test harnesses.

Does not own:

- native decode or transport;
- gateway processes;
- target protocol implementations;
- optimization or regulator policy.

### 16.2 Gateway

**Project-Helianthus/helianthus-ebusgateway**

Required changes:

- replace the existing semantic runtime with a new helianthus-semreg-based
  vNext composition at the coordinated cutover;
- implement DriverManager and persistent desired state;
- compose eBUS, EEBUS and Modbus through DriverV1;
- isolate startup/restart failures per driver;
- host presentation selection and projection services;
- expose drivers.v1 status and typed list/get/start/stop/restart through
  MCP/HTTP, Portal and Home Assistant;
- add semantic M2M GraphQL types and subscriptions additively;
- implement the operation admission/router and EmissionLedger;
- reimplement required GraphQL/MCP/Portal/HA contracts directly over HSIR;
- keep legacy/new comparison outside production rather than adding runtime
  compatibility facades between the two semantic cores;
- remove direct eBUS/Vaillant DTO dependencies from the vNext shared semantic
  and northbound packages before cutover;
- keep raw evidence surfaces distinct and access-controlled.

The gateway does not become the semantic type owner and does not acquire
regulator/optimizer behavior.

### 16.3 eBUS driver family

Logical composition:

~~~text
helianthus-ebusgo + helianthus-ebusreg + gateway driver adapter
~~~

Required changes:

- keep transport/framing/timing in helianthus-ebusgo;
- keep eBUS discovery, native schema, B509/B524/standard-service mappings and
  vendor profiles in helianthus-ebusreg;
- implement DriverV1 and SemanticPublisherV1 at the complete runtime boundary;
- publish parallel SourceBindings instead of silently collapsing B524, B509
  and standard paths;
- classify controller cache, aggregate, direct state and command endpoint;
- retain native evidence and source-time uncertainty;
- map existing Service/Observability planes to opaque HSIR IDs while preserving
  paths as aliases;
- expose inverse operation bindings with exact preconditions and readback;
- preserve all required eBUS behavior through offline replay/golden parity
  before the whole-system cutover.

### 16.4 EEBUS driver family

Logical composition:

~~~text
helianthus-ship-go + helianthus-spine-go +
helianthus-eebus-go + helianthus-eebusreg
~~~

Required changes:

- keep SHIP and SPINE protocol mechanics in their current foundations;
- keep raw device/entity/feature/use-case evidence in helianthus-eebusreg;
- implement DriverV1 and semantic mappings in the EEBUS runtime composition;
- generate exhaustive versioned catalogs for 32/143/48/36 SPINE elements;
- map typed features and functions to capability packs without value:any;
- keep catalog completeness separate from per-device advertised/observed
  materialization;
- preserve unknown enums/fields and raw source shadows;
- express schema-known, observed, decoded, validated and commandable
  separately;
- bind mutations only after authority, safety, preconditions and conformance;
- support northbound EEBUS as a real local SPINE server projection with
  server entities/features, advertised use cases, reads, subscriptions and
  gated commands;
- withdraw/re-publish capabilities by driver generation;
- preserve current 18 promoted leaves through offline old-versus-vNext
  replay/golden parity.

### 16.5 Modbus driver family

Logical composition:

~~~text
helianthus-modbus + helianthus-modbusreg
~~~

Required changes:

- keep transport, PDU, TCP/RTU lifecycle and bounds in helianthus-modbus;
- treat the existing `internal/modbusadapter.ExecuteReadWithReconnect` under
  `executeMu` as the Modbus adapter/transport seam: future DriverV1 reuses it
  or relocates it with behavior preserved; DriverManager must not duplicate
  reconnect, retry ownership, quota or healthy-generation teardown logic;
- keep standard and vendor profile detection, decode and native provenance in
  helianthus-modbusreg;
- remove cross-protocol canonical PV ownership from eBUS-specific packages;
- implement DriverV1 and HSIR SourceBindings for every qualified profile;
- preserve raw words, exact transport generation and documented absence of
  source time;
- inventory the full SunSpec model catalog and revisions;
- distinguish inverter-owned, BMS-mirrored, cached, calculated and applied
  values where vendor evidence exists;
- publish exact AC/DC terminals, phase, direction, aggregation and counter
  basis;
- keep writes disabled until separate conformance and hardware qualification;
- use the future direct CAN BMS scenario as a no-core-change architecture test,
  not as current implementation scope.

### 16.6 Documentation

**Project-Helianthus/helianthus-docs-ebus** remains the current human-readable
architecture owner during this rewrite. A repository rename or split is a
separate decision.

Required documentation:

- architecture/semantic-bridge-ir.md;
- architecture/driver-contract.md;
- architecture/source-lineage-and-presentation.md;
- architecture/planes-lenses-and-projections.md;
- architecture/bidirectional-operation-routing.md;
- architecture/bridge-versus-regulator.md;
- API contracts for HSIR GraphQL M2M and drivers.v1;
- protocol mapping catalogs for eBUS, EEBUS and Modbus/SunSpec;
- northbound projection coverage and loss manifests;
- compatibility and deprecation guide;
- consumer deployment concepts for home, ESCO and dispatcher use.

Protocol-specific reverse-engineering evidence remains in the appropriate
public protocol documentation lane. Machine-readable schemas and conformance
fixtures live with their producer code.

### 16.7 Consumers

- helianthus-ha-integration migrates only after GraphQL parity;
- Portal consumes gateway APIs, not semreg internals;
- Matter/EEBUS/EVCC/SunSpec/OCPP projectors receive HSIR only;
- future ESCO regulator and dispatcher are consumer contracts, not current code
  deliverables.

## 17. Execution DAG

~~~mermaid
flowchart TB
    PRE["Activation gates<br/>minimal SunSpec/Fronius/Huawei + current EEBUS complete"]
    P0["M0 Evidence and compatibility baseline"]
    D1["M1 Public architecture and contract docs"]
    O1["M1 Organization creates helianthus-semreg"]
    S1["M2 HSIR kernel, packs and conformance harness"]
    G1["M3 Gateway DriverManager and empty HSIR host"]
    E1["M4 eBUS DriverV1 in vNext"]
    EE1["M5 EEBUS exhaustive mapping"]
    M1["M5 Modbus/SunSpec mapping"]
    R1["M6 Presentation selection, lineage and planes"]
    A1["M7 GraphQL/MCP/Portal compatibility and M2M API"]
    N1["M8 Northbound target projections"]
    H1["M9 Whole-system cutover readiness"]
    CUT["Single coordinated cutover"]
    C1["M10 Post-cutover closure and certification readiness"]
    CLEAN["M11 Post-0.7 structural cleanup"]

    PRE --> P0
    P0 --> D1
    P0 --> O1
    D1 --> S1
    O1 --> S1
    S1 --> G1
    G1 --> E1
    E1 --> EE1
    E1 --> M1
    EE1 --> R1
    M1 --> R1
    R1 --> A1
    A1 --> N1
    A1 --> H1
    N1 --> H1
    H1 --> CUT
    CUT --> C1
    C1 --> CLEAN
~~~

EEBUS and Modbus may execute in parallel only after the eBUS reference driver
proves the shared contract and only when repository write sets do not overlap.

## 18. Milestones

### M0 — Evidence and compatibility baseline

Repositories: gateway, eBUS, EEBUS, Modbus, HA, docs.

Deliverables:

- exact current heads and green local CI;
- gateway baseline at or descended from M4-04 squash merge
  `6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b`, plus completed legacy add-on
  0.6.51 stabilization and read-only validation evidence;
- frozen GraphQL/MCP/Portal/HA compatibility snapshots;
- current 18 EEBUS promoted-leaf fixture;
- eBUS B524/B509/standard-source catalog;
- EEBUS 32/143/48/36 inventory;
- full pinned SunSpec model inventory;
- current runtime and driver lifecycle inventory;
- live Modbus M4-04 regression fixtures proving endpoint-free
  `modbus.v1.raw.read` provider errors and at most one raw MCP reconnect+retry
  inside one total bounded context after a TCP reset, owner-gated by
  `Snapshot.ReconnectRequired`, with one quota and an immutable PDU, including
  two concurrent raw callers that cause one reconnect and do not tear down the
  healthy generation;
- source/version ledger for Matter, EVCC and OCPP.

Exit:

- every current public behavior has a named compatibility owner;
- unknown source relationships remain unknown rather than inferred.

### M1 — Documentation and repository ownership

Repositories: docs, organization governance.

Deliverables:

- public HSIR ADR and glossary;
- bridge-versus-regulator boundary;
- repository creation for helianthus-semreg;
- explicit supersession of eBUS-specific cross-protocol semantic ownership;
- no implementation side effects from plan/docs merge.

### M2 — HSIR kernel

Repository: helianthus-semreg.

Deliverables:

- stable kernel types;
- exact quantity/time/quality types;
- SourceBinding and provenance DAG;
- CandidateFactSet and CanonicalFactEnvelope;
- capability-pack registration/versioning;
- planes/lenses model;
- semantic operation and driver contracts;
- projection manifest/report;
- deterministic serialization and schema lint.

Exit tests:

- kernel imports no protocol/gateway package;
- no any/untyped value in public schemas;
- unknown enum/extension round-trip;
- graph cycle rejection;
- property-based exact quantity conversion;
- deterministic replay.

### M3 — Gateway host and drivers.v1

Repository: gateway.

Deliverables:

- semreg host;
- DriverManager desired/observed state;
- per-driver failure isolation;
- capability generation withdrawal;
- empty projection engine;
- typed drivers.v1 status and control surfaces;
- MCP/HTTP list/get/start/stop/restart;
- Portal driver controls;
- Home Assistant response-only switch/button/service contract;
- API/health startup independent from driver startup.

Exit tests:

- one driver startup/restart panic or error cannot terminate the gateway;
- restart does not reuse stale capabilities;
- gateway can be ready with one failed driver;
- eBUS, EEBUS or Modbus start/restart errors remain non-fatal and visible
  through every drivers.v1 surface;
- controls change persistent desired state without restarting the process;
- Portal and HA control responses match MCP/HTTP results;
- no protocol-specific branch in shared manager logic.

### M4 — eBUS reference rewrite

Repositories in dependency order: docs, ebusreg, gateway; ebusgo only if native
evidence/time contracts require it.

Deliverables:

- complete eBUS DriverV1;
- parallel B524/B509/standard SourceBindings;
- opaque ID compatibility aliases;
- offline old-versus-vNext replay and golden comparator;
- inverse operation bindings;
- zero public regression.

M4 proves the architecture before additional vNext drivers are admitted. It
does not switch the production runtime.

### M5 — EEBUS and Modbus drivers

EEBUS repository order:

~~~text
docs -> spine-go/eebus-go when necessary -> eebusreg -> gateway adapter
~~~

Modbus repository order:

~~~text
docs -> modbus when necessary -> modbusreg -> gateway adapter
~~~

Deliverables:

- exhaustive EEBUS coverage and current-leaf compatibility;
- separate catalog completeness and per-device advertised/observed
  materialization;
- real EEBUS northbound SPINE server features/use cases/read/subscribe and
  gated commands;
- full SunSpec inventory and qualified profile mappings;
- DriverV1 reuse or behavior-preserving relocation of the atomic Modbus
  `internal/modbusadapter.ExecuteReadWithReconnect` seam rather than
  reconnect/retry duplication in DriverManager;
- generation-bound lifecycle;
- source shadows and lineage;
- read-only canonical parity before any new mutation.

### M6 — Presentation, planes and provenance

Repositories: semreg, gateway, docs.

Deliverables:

- mechanical presentation selection;
- conflict and alternative reporting;
- ServiceRuntime, Physical, FlowTopology, Observability, Control and
  SourceEvidence planes;
- Diagnostics, CircuitMapping and EnergyManagement lenses;
- B524 cache/aggregation and BMS/inverter fixture tests.

### M7 — Public API compatibility and M2M

Repositories: gateway, docs.

Deliverables:

- additive HSIR GraphQL M2M API;
- direct vNext implementation of the required existing GraphQL contract;
- MCP semantic/raw parity;
- Portal diagnostic support;
- operation admission/router;
- bounded EmissionLedger;
- subscriptions with one revision-consistent snapshot.

### M8 — Northbound projections

Repositories: target binding owners, semreg, docs.

Order:

1. read-only projection manifests and golden outputs;
2. capability negotiation;
3. events/subscriptions;
4. writes only after inverse mapping and conformance.

Targets are versioned independently. Official external certification is not a
merge substitute.

### M9 — Whole-system cutover readiness

Repositories: gateway, HA integration, add-on, Portal owner and consumer
bindings.

Deliverables:

- HA parity and diagnostics against the complete vNext stack;
- Portal and HA driver start/stop/restart acceptance against the complete vNext
  stack;
- smart-home reference topology;
- multi-bridge regulator reference flow;
- dispatcher/prosumer/PV/EVSE reference flow;
- installation/configuration transition instructions;
- preserved instance GUID and public identity alias manifest;
- complete legacy release artifact and tested rollback procedure;
- no regulator optimization implementation;
- no partial production activation before every cutover prerequisite is green.

### CUT — Single coordinated production replacement

The operator separately authorizes the cutover at action time.

The cutover:

- stops the legacy release;
- installs the complete Helianthus Bridge 0.7.0 vNext gateway/add-on release;
- starts the HSIR registry and all configured vNext drivers;
- rebuilds current semantic state from native discovery;
- runs bounded health and public API smoke checks;
- either remains entirely on vNext or rolls back entirely to the preserved
  legacy release.

There is no in-process legacy fallback and no mixed semantic state.

### M10 — Post-cutover closure and certification readiness

Deliverables:

- 100 percent coverage manifests;
- fake peers and golden vectors;
- cross-protocol projection reports;
- failure injection and reconnect tests;
- interoperability runs;
- read-only live-lab evidence;
- separately authorized write-lab evidence;
- stabilization evidence from the complete vNext runtime;
- fresh exact-HEAD no-blocking-findings review in every touched code repo.

Official Matter, EEBUS, SunSpec or OCPP certification remains a separate
external activity.

### M11 — Post-0.7 structural cleanup

This wave begins only after 0.7.0 stabilization and uses behavior-preserving
issues/PRs separate from the semantic rewrite.

The baseline audit must inventory:

- production files around 10,000 lines;
- functions spanning multiple pages or unrelated responsibilities;
- duplicated GraphQL/MCP/Portal/driver transformations;
- gateway composition, lifecycle and schema chokepoints;
- obsolete legacy semantic code left after the stabilization gate;
- packages whose public surface prevents isolated tests;
- test files and fixtures with mixed responsibilities or excessive size;
- test cases whose names are opaque work-item identifiers such as `MSP1234`
  instead of behavioral contracts;
- duplicated, obsolete, over-mocked or implementation-coupled tests;
- conformance tests that can be grounded in published protocol test
  specifications, especially EEBUS test specifications.

Large size is an inspection trigger rather than the sole defect. Cleanup
acceptance is responsibility-based:

- each decomposed module has one coherent owner;
- composition roots contain composition rather than domain implementation;
- protocol, semantic, projection and consumer DTO logic no longer share giant
  functions;
- extracted units have focused tests and unchanged golden behavior;
- legacy semantic code is deleted after proof that vNext owns every required
  path;
- no cleanup PR intentionally changes HSIR meaning or public API behavior;
- executable test names describe precondition, behavior and expected outcome;
- issue, milestone or historical identifiers remain metadata/traceability
  aliases only and never serve as the sole test name;
- where a normative conformance test specification exists, the suite records
  its exact standard/version/test-case reference and uses the standard's
  behavioral terminology without claiming certification; protected standard
  text or restricted vectors are not copied into a public repository;
- EEBUS conformance cases are organized by normative feature, use case and
  test-case identity, while Helianthus-specific regressions are clearly marked
  as implementation tests;
- renamed or decomposed tests preserve or improve coverage and retain golden
  evidence for unchanged behavior;
- every dependent parallel lane follows the plan #93 merge train and reruns
  exact-HEAD validation after predecessors merge.

The cleanup wave may produce a 0.7.x maintenance release. A later 0.8 product
scope is outside this plan.

## 19. Planned issue outline

Issue numbers are assigned only in their owning repositories during execution.
Publishing this plan does not create them.

| ID | Repository | Objective | Depends on |
|---|---|---|---|
| DOC-IR-01 | helianthus-docs-ebus | HSIR architecture and boundaries | M0 |
| ORG-IR-01 | .github | Create helianthus-semreg | merged plan |
| SEM-IR-01 | helianthus-semreg | Kernel and type system | DOC-IR-01, ORG-IR-01 |
| SEM-IR-02 | helianthus-semreg | Provenance, planes and selection | SEM-IR-01 |
| SEM-IR-03 | helianthus-semreg | Capabilities, operations and projections | SEM-IR-01 |
| GW-IR-01 | helianthus-ebusgateway | DriverManager and semreg host | SEM-IR-01 |
| EBUS-IR-01 | helianthus-ebusreg | eBUS SourceBindings and DriverV1 | GW-IR-01 |
| GW-IR-02 | helianthus-ebusgateway | vNext eBUS integration and offline compatibility comparator | EBUS-IR-01 |
| EEBUS-IR-01 | helianthus-eebusreg | Exhaustive SPINE-to-HSIR mapping | GW-IR-02, SEM-IR-02 |
| MODBUS-IR-01 | helianthus-modbusreg | SunSpec/profile-to-HSIR mapping | GW-IR-02, SEM-IR-02 |
| GW-IR-03 | helianthus-ebusgateway | EEBUS/Modbus integration and planes | EEBUS-IR-01, MODBUS-IR-01 |
| GW-IR-04 | helianthus-ebusgateway | Direct vNext GraphQL/MCP/Portal M2M implementation | GW-IR-03, SEM-IR-03 |
| NB-IR-REQ | target binding owners | Required cutover GraphQL/EEBUS/Matter and declared target projections | GW-IR-04 |
| HA-IR-01 | helianthus-ha-integration | Complete vNext GraphQL consumer parity | GW-IR-04 |
| CUT-IR-01 | helianthus-ebusgateway | Atomic legacy-to-vNext composition replacement | NB-IR-REQ, HA-IR-01 |
| DOC-IR-02 | helianthus-docs-ebus | Final mappings, operations and deployment concepts | producer PRs |
| CLEAN-IR-* | touched vNext repositories | Post-0.7 responsibility-driven code/test decomposition, descriptive test taxonomy and legacy removal | 0.7.0 stabilization |

### 19.1 Plan #93 parallel-lane exception

For this plan only, the operator authorizes parallel PRs in the same repository
when all of the following are true:

- every PR uses a separate worktree and branch;
- file/module ownership is disjoint and announced before the first write;
- participating lanes send reciprocal notice and adjust around merged changes;
- every shared file has exactly one owner at a time;
- merges use an explicit merge train;
- after each predecessor merge, every dependent PR rebases on current main and
  reruns full exact-HEAD CI and fresh review.

Integration chokepoints are single-owner and may not be split across concurrent
lanes:

- cmd/gateway/main.go and the gateway composition root;
- the public HSIR schema/contracts;
- the Home Assistant add-on wrapper/configuration and release packaging.

This is a scoped exception for plan #93 and does not change the organization
default. Documentation-gate companions follow the code lane that owns each
semantic or protocol change.

### 19.2 Mandatory Fronius lane coordination

Before every gateway, add-on or Modbus lane begins, its agent notifies task
019f47bb-70ff-72d1-9b7f-4a1bacbd5451 with:

~~~text
own task/thread ID
repository and issue
branch
base branch and exact base SHA
exact current HEAD
declared file/module write-set
integration chokepoint owner, when applicable
~~~

The same task receives checkpoints at merge, release and live/deployment
boundaries. This is coordination, not workflow authority; current GitHub and
runtime state must still be re-read.

Initial reference state supplied by the operator on 2026-08-17, superseded
where noted by later same-day coordination updates:

- Fronius declares zero active lane;
- add-on main and deployed version are 0.6.50 at
  cd6017bf554987b8ebb423b4de88af391461b125;
- Modbus lane is GO;
- eBUS live no-signal is a separate condition.

Every lane reconciles this snapshot because it can become stale.

The coordinated lane is gateway issue #833 and PR #834 on branch
`issue/833-modbus-mcp-reconnect-redaction`, for two live Modbus M4-04 P2
defects against add-on 0.6.50. It started from exact base/HEAD
`7f1cbea90e0b189486febc656632e9e7430c8500`. Its documentation gate is already
merged at `1ca1438813ec80b12a9c4e9565086cecd6160e19`:

- `modbus.v1.raw.read error.message` leaks a private endpoint;
- raw MCP does not reconnect/retry after a TCP reset until the add-on restarts.

The gateway lane owned the following exact six-file write-set exclusively
through squash merge:

~~~text
helianthus-ebusgateway:
  cmd/gateway/modbus_mcp_provider.go
  cmd/gateway/modbus_mcp_provider_test.go
  internal/modbusadapter/adapter.go
  internal/modbusadapter/adapter_reconnect_test.go
  mcp/modbus_v1.go
  mcp/modbus_v1_test.go
~~~

There was zero concrete overlap with HSIR or DriverManager. The reservation is
now released by the final squash merge recorded below; future work still uses
normal live write-set reconciliation rather than treating historical release
as permanent ownership.

The Fronius lane explicitly excludes `cmd/gateway/main.go` and the composition
root, `go.mod`, `go.sum`, semantic Vaillant code, eBUS, EEBUS, DriverManager,
adaptermux, the add-on and live deployment. This negative scope is not
permission to overlap another active reservation.

Public checkpoint evidence for issue #833 / PR #834:

- initial RED commit: `77885ddac7021804b523c7a6b93adf3163aaa816`;
- prior GREEN public HEAD:
  `d5cd63caaf508c9927af32a7662dca33883be2fa`;
- focused real-TCP reset/reconnect race: green;
- full local CI: Portal 43/43, full Go race, Python
  168+6+9+7+6+2, lint 0;
- a fresh P2 review at `d5cd63caaf508c9927af32a7662dca33883be2fa`
  found that provider `Snapshot` to reconnect ownership was not atomic between
  two raw callers;
- atomicity RED commit: `822fa53588f74853ac5e4ea3a50cd2646e88cb5f`;
- final premerge HEAD: `ce0d0ac4f10d7880188a291bea00984115ab2354`;
- `Snapshot` to reconnect ownership is closed through owner-atomic
  `ExecuteReadWithReconnect` under `executeMu`;
- an assertion scoped specifically to `error.message` closes the second P2
  test-flake;
- final local and GitHub gates are 4/4 green with fresh
  `NO_BLOCKING_FINDINGS`; both prior P2 findings are closed, with zero other
  code P0-P2 and zero P3/P4;
- gateway squash merge on main:
  `6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b`;
- issue #833 is closed, PR #834 is merged, the feature branch is deleted and
  gateway main is clean.

The six-file reservation is closed. The merged gateway SHA is the new M0
baseline. The following Fronius program is legacy add-on 0.6.51: its current
issue #212 lane is packaging-only, while publish/deploy and M4-04 read-only
validation remain later boundaries. It is not an HSIR manager runtime lane in
gateway or add-on, and plan #93 remains plan-only.

Both defects become M0 baseline requirements and vNext compatibility fixtures.
The implementation contract is endpoint-free provider errors plus at most one
raw MCP reconnect+retry within one total bounded context after a TCP reset,
only when the owning snapshot sets `Snapshot.ReconnectRequired`. The retry uses
one shared quota and the original PDU remains immutable. Ownership moves into
the atomic Modbus transport operation `ExecuteReadWithReconnect` under
`executeMu`: first execute, owner-snapshot gate, at most one reconnect and one
retry. A two-caller regression must prove exactly one reconnect and no teardown
of the healthy generation. The offline comparator and future DriverV1 reuse
this existing Modbus seam; DriverManager must not duplicate it. These legacy
fixes do not add DriverManager or any vNext lifecycle API to the legacy runtime.

### 19.3 Legacy add-on 0.6.51 reservation

The active add-on coordination lane is issue #212 on branch
`issue/212-release-0651-modbus-mcp-recovery`, based on
`cd6017bf554987b8ebb423b4de88af391461b125`, targeting release 0.6.51 and pinning
gateway `6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b`.

Its exact packaging-only write-set is owner-exclusive until squash merge or
explicit handoff:

~~~text
helianthus-ha-addon:
  .github/workflows/build.yml
  helianthus/config.json
  helianthus/Dockerfile
  helianthus/CHANGELOG.md
  helianthus/README.md
  README.md
  SMOKE_RUNBOOK.md
  scripts/check_eebus_wrapper.py
  scripts/check_source_addr_wrapper.py
  fixtures/gateway_parity_artifact_pass.json
  tests/test_eebus_admin_wrapper.py
  tests/test_modbus_runtime_guard.py
~~~

Wrapper/schema/runtime implementation, deployment and live validation are
outside issue #212. Publish/deploy and M4-04 read-only validation are later
release boundaries, not implied by packaging merge.

Gateway CI run `32032466778` for main SHA
`6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b` is in progress at this checkpoint:
build, lint and terminology are green, while the test job is still running.
The parity artifact is hard-stopped until that run reaches `SUCCESS`. This is a
revalidated dependency gate, not plan authorization machinery.

There is zero overlap with the HSIR plan-only lane. Future executors must not
claim the listed add-on files until issue #212 records squash merge or explicit
handoff, and must re-read the run and lane because this checkpoint can become
stale. No HSIR or DriverManager runtime work exists in gateway or add-on.

## 20. Validation and gates

### Required for every producer

- repository-local build, vet, lint and race tests;
- deterministic serialization;
- golden fixtures;
- unknown-value preservation;
- capability withdrawal/republication;
- restart generation;
- explicit negative and withheld states;
- public API compatibility snapshots.

### Semantic and projection tests

- native-to-HSIR-to-same-native round-trip where declared exact;
- unit, scale, direction, phase, terminal and counter-basis property tests;
- cache and quantization lineage;
- absent source timestamp;
- private transport endpoints are sanitized from public Modbus MCP errors;
- raw Modbus MCP performs at most one reconnect+retry within one total bounded
  context after a TCP reset, only when the owning snapshot sets
  `Snapshot.ReconnectRequired`, using one quota and an immutable original PDU,
  without requiring an add-on restart;
- two concurrent raw callers use atomic `ExecuteReadWithReconnect` under
  `executeMu`, produce one reconnect and do not tear down the healthy transport
  generation;
- false identity rejection;
- projection loss golden reports;
- no invented enum equivalence;
- command route ambiguity rejection;
- no write fan-out;
- indeterminate outcome does not retry another route;
- loop/echo suppression;
- snapshot revision consistency.

### Driver failure tests

- start failure;
- runtime panic/error;
- stop timeout;
- restart during publication;
- stale capability generation;
- partial driver availability;
- primary representation withdrawal and bounded fallback.

### Gate applicability

- documentation gate: mandatory for architecture, semantic, protocol, state
  machine and reverse-engineering changes;
- T01..T88 transport gate: mandatory only when eBUS transport/protocol paths
  are modified;
- equivalent EEBUS transport/interoperability gates: mandatory when
  SHIP/SPINE behavior changes;
- Modbus transport gate: mandatory when TCP/RTU behavior changes;
- live writes: require explicit operator confirmation at action time;
- HA end-to-end deployment remains a separate operator boundary.

### TDD applicability

- RED-first tests are required where behavior is introduced or changed:
  HSIR serialization, identity/linking, lineage, presentation selection,
  DriverManager lifecycle, capability generation, operation routing,
  projection loss and compatibility output;
- docs-only and read-only standards inventory lanes do not require artificial
  RED commits;
- repository-local TDD evidence follows the normal issue/PR workflow and is
  not encoded as plan authorization state.

### Test corpus quality

- test names are behavioral and searchable, not opaque milestone identifiers;
- legacy identifiers such as `MSP1234` may be retained only in structured
  traceability metadata, comments or manifests beside a descriptive test name;
- protocol conformance suites pin the normative source and edition for each
  imported or derived test case;
- committed test code, descriptions and fixtures must be redistributable;
  restricted specifications are cited by identity while independently created
  tests encode only the behavior the project is entitled to implement;
- EEBUS standard test cases and Helianthus-specific regression tests remain
  distinguishable in reports;
- cleanup test moves/renames prove unchanged outcomes before deleting aliases
  or obsolete fixtures.

Validation effort should remain proportionate, approximately 25–30 percent of
development, and may exceed that for command, protocol, safety and live-device
work.

## 21. Acceptance criteria

The architecture milestone is complete only when:

1. the minimal SunSpec/Fronius/Huawei Modbus prerequisite and current EEBUS
   completion prerequisite are reconciled green, gateway M0 includes merge
   `6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b`, and legacy add-on 0.6.51
   stabilization/read-only validation is complete before vNext execution
   starts;
2. Helianthus Bridge 0.7.0 has a complete vNext release bill of materials;
3. helianthus-semreg exists and its kernel has no protocol or gateway import;
4. every public HSIR field is typed; value:any is absent;
5. opaque ResourceID replaces Service-path identity internally with compatible
   aliases;
6. eBUS, EEBUS and Modbus operate through one DriverV1 without shared-manager
   protocol branches;
7. B524, B509 and standard eBUS sources can coexist as distinct SourceBindings;
8. all 32 FeatureType, 143 FunctionType, 48 EntityType and 36 UseCaseName
   values have explicit EEBUS dispositions;
9. catalog completeness does not instantiate unsupported EEBUS device
   capabilities, and per-device materialization is limited to
   advertised/observed facts;
10. EEBUS northbound passes local SPINE server feature/use-case discovery,
   read, subscribe and gated-command conformance;
11. the pinned SunSpec catalog has complete model/revision dispositions;
12. raw SPINE, frames and Modbus words remain separate from HSIR;
13. existing GraphQL, MCP, Portal and HA contracts pass parity tests;
14. drivers.v1 list/get/start/stop/restart works through MCP/HTTP, Portal and
    Home Assistant without process restart and with persistent desired state,
    separate observed state, expected revision and idempotency;
15. the current 18 promoted EEBUS leaves pass offline old-versus-vNext replay
    and golden parity;
16. driver stop/restart withdraws and republishes capabilities atomically by
    generation;
17. gateway API/health becomes ready independently and no eBUS, EEBUS or
    Modbus driver failure terminates the gateway;
18. every target projection has a versioned manifest and golden loss report;
19. commands route to exactly one native binding and distinguish
    acknowledgement from readback verification;
20. multi-northbound feedback loops are bounded and tested;
21. smart-home, regulator and dispatcher reference flows use the same HSIR
    without driver knowledge of those consumers;
22. no optimizer, scheduler, dispatch policy or ESCO product code is added to
    the bridge milestone;
23. a future CAN BMS driver can be modeled in fixtures without an HSIR or
    gateway-core schema change;
24. the complete vNext stack passes the cutover rehearsal without any mixed
    legacy/vNext runtime or state;
25. DriverManager and all driver-control surfaces exist only in vNext and
    activate atomically at cutover;
26. the plan #93 parallel-lane ownership, merge-train and rebase/full-review
    rules are exercised without overlapping writes;
27. gateway/add-on/Modbus lanes record the required Fronius coordination
    notices and checkpoints;
28. the vNext comparator preserves the merged M4-04 endpoint-free provider
    error contract and at-most-one TCP-reset reconnect+retry in one total
    bounded context, owner-gated by `Snapshot.ReconnectRequired`, with one
    quota, an immutable PDU, atomic two-caller ownership and no teardown of the
    healthy generation; future DriverV1 reuses `ExecuteReadWithReconnect` and
    does not duplicate this behavior in DriverManager or import DriverManager
    into legacy;
29. whole-release rollback to the frozen legacy artifact and untouched legacy
    state is tested;
30. the post-0.7 cleanup inventory and issue wave cover the identified
    page-scale functions, approximately 10,000-line production files and
    mixed-responsibility test files;
31. test cases have descriptive behavioral names; opaque identifiers such as
    `MSP1234` survive only as traceability metadata, and applicable EEBUS tests
    cite their exact normative test specification/version/case;
32. cleanup preserves or improves coverage and separates normative
    conformance cases from Helianthus regression tests in reports;
33. code repositories finish with applicable CI and fresh exact-HEAD
    NO_BLOCKING_FINDINGS;
34. official external certifications are reported separately from internal
    certification readiness.

## 22. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Semantic kernel becomes a monolithic union struct | Small kernel plus versioned packs |
| B524/B509/standard values are falsely unified | Binding-level identity and evidence-qualified lineage |
| Cached mirrors launder freshness | Separate phenomenon/source/cache/receive times |
| Plane registries diverge | Planes are rebuildable relation views over one graph |
| Northbound projectors select different facts | One CanonicalFactEnvelope plus exposed alternatives |
| Bridge turns into HEMS/regulator | Product boundary and explicit non-goals |
| Two controllers oscillate a setpoint | Report/serialize mechanically; coordination remains external |
| Ambiguous write is executed twice | Exactly-one route and indeterminate outcome |
| Protocol additions require gateway rewrite | DriverV1 and leaf HSIR dependency |
| Big-bang cutover breaks legacy consumers | Frozen public contracts, offline full-stack replay, cutover rehearsal and whole-release rollback |
| Cleanup changes behavior or merely reshuffles giant files | Post-stabilization, behavior-preserving PRs with golden parity and responsibility-based acceptance |
| Opaque test IDs hide intent or overstate standards coverage | Descriptive behavioral names plus versioned normative traceability metadata |
| Normative tests are copied without redistribution rights | Exact references plus independently authored, redistributable tests and fixtures |
| Source shadow leaks secrets or identifiers | Protected evidence stores and access-controlled refs |
| Matter/EEBUS/SunSpec revisions drift | Exact version manifests and explicit diffs |
| Certification readiness is misreported as certification | Separate acceptance and external proof |

## 23. Rollback principles

- Production rollback is atomic at the complete release boundary.
- The legacy gateway/add-on artifact, configuration and data remain preserved
  and tested until the vNext stabilization gate closes.
- The bridge never runs legacy and vNext semantic cores together as a rollback
  mechanism.
- Native observations and source shadows are append-only evidence and retain
  their originating runtime/schema identity across rollback.
- vNext driver generations are never reused after restart or rollback.
- A failed vNext startup does not import or reinterpret partial vNext state
  into the legacy release.
- Disabled or failed vNext facts become unavailable; they are never silently
  remapped to weaker legacy meanings.
- Repository/module renames are not required for architectural completion.

## 24. Explicit hard stops

This plan stops after the requested plan review/publication boundary.

Implementation must stop separately:

- before any live-device write without operator confirmation;
- before regulator/optimizer product development;
- before official certification claims;
- before committing protected standards text or restricted conformance vectors
  without verified redistribution rights;
- before repository/module/binary renaming;
- before the single cutover unless every whole-system prerequisite and rollback
  rehearsal is green;
- before retiring required public compatibility surfaces;
- before deleting legacy release artifacts or internal code until the
  stabilization gate closes;
- before starting structural code/test cleanup until 0.7.0 stabilization is
  recorded, except for decomposition strictly required to build the vNext
  architecture safely;
- when a required normative source or mapping equivalence is unproven.

Merging this plan creates no issue, branch, PR, repository, deployment or
runtime effect in another repository.
