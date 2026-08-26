# Terminology And API Contract

Canonical-SHA256: `0675509fd10408c4102f15b108f8152e1fd985293f14f7f870b3bc4176bab720`

Depends on: `00-canonical.md`

Scope: `helianthus-ebusgo/protocol`, gateway call sites that consume the API,
and docs vocabulary. This chunk defines the target names and contract,
including the separation between standard source description, Helianthus
gateway policy, priority index, and arbitration nibble. It does not prescribe implementation internals beyond observable
behavior.

Idempotence contract: Reapplying this terminology does not change protocol
semantics. The same source selection request over the same observation snapshot
must produce the same selected source, companion target, rejection reasons, and
metrics.

Falsifiability gate: A reviewer can reject this chunk if any remaining active
API name implies a formal bus membership operation instead of source address
selection, if source description and priority are conflated, if the gateway
default is misrepresented as a standard source description, or if the API cannot
express default, source-description-constrained, priority-filtered, and explicit
validate-only modes.

Coverage: Terminology replacement, docs-owned static source table, priority
filtering, gateway default policy, constrained policy, explicit validate-only
mode, companion modulo behavior, persistence handoff, active-probe FSM, and
snake_case public naming.

## Decision

Use `SourceAddressSelector` and `SourceAddressSelection` as the public concepts
in `helianthus-ebusgo/protocol`.

| Existing concept | Replacement |
| --- | --- |
| `Joiner` | `SourceAddressSelector` |
| `JoinResult` | `SourceAddressSelection` |
| `JoinConfig` | `SourceAddressSelectionConfig` |
| `JoinBus` | `SourceAddressObservationBus` |
| `JoinMetrics` | `SourceAddressSelectionMetrics` |
| standard source-address description | `SourceAddressStandardDescription` |
| eBUS p0..p4 priority index | `SourceAddressPriorityIndex` |
| admission path value `join` | `source_selection` |
| override selection bypass | `explicit_validate_only` |

The replacement terms are intentionally literal. The component selects and
validates a source address for active eBUS frames. It does not perform a formal
bus membership protocol.

`SourceAddressStandardDescription` is not priority. It represents exact
source-address descriptions found in the eBUS source-address table. Free-use
reservation and recommended-for are separate fields. Preallocated heating
regulator or combustion controller descriptions must not absorb p3/p4 free-use
recommendation rows.

`SourceAddressPriorityIndex` represents the p0..p4 table priority index. The
source address low nibble is the `arbitration_nibble` (`0x0`, `0x1`, `0x3`,
`0x7`, or `0xF`). The priority index can filter or order candidates, but it must
not be treated as a device class, source description, or Helianthus desirability
signal.
Official bus arbitration rank is lower-is-stronger: p0 / `0x0` outranks p1 /
`0x1`, then p2 / `0x3`, p3 / `0x7`, and p4 / `0xF`; lower source bytes win
within otherwise equal contention. `HelianthusGatewayDefaultPolicy` is a
gateway policy and must not describe p4 as higher bus priority.

## Policy Modes

The selector accepts one policy object with three mutually exclusive effective
modes.

Default policy:

- selected when no source description, priority, or exact address is
  configured;
- expands to `HelianthusGatewayDefaultPolicy`;
- may consider a previous validated source only when gateway passes it as a
  metadata-scoped hint and it still belongs to the policy.

Source-description-constrained policy:

- selected when a source description is configured;
- expands only the requested standard source-address table rows;
- may then be filtered or ordered by `SourceAddressPriorityIndex` if priority is
  also configured;
- must not return a source outside that constrained list;
- returns a no-available-source error if the constrained list cannot validate.

Gateway startup may use only these exact gateway-safe
`SourceAddressStandardDescription` constants: `PC`, `PCModem`,
`BusInterfaceClimateRegulator`, `BusInterface`, and `NotPreallocated`.
`recommended_for` is informational only and never authorizes or constrains
gateway startup. Combustion-controller, clock/radio-clock, heating regulator,
and heating circuit regulator descriptions require explicit address mode or a
separate diagnostic-only path outside automatic startup.

Priority-only policy:

- selected when priority is configured without a standard source description;
- for gateway startup admission, applies the priority to the Helianthus
  gateway default policy only;
- must not search all standard source descriptions unless a source description
  is explicitly configured.

Explicit validate-only:

- selected when `ExplicitAddress` is configured;
- bypasses candidate search and persisted last-good selection;
- validates only the exact address;
- returns either a valid `SourceAddressSelection` or a validation error.

## Gateway Default Policy

The default policy order is:

1. p4: `0xFF`, `0x7F`, `0x3F`, `0x1F`
2. p3: `0xF7`, `0x77`, `0x37`, `0x17`, `0x07`
3. p1 bus-interface addresses: `0x11`, `0x31`
4. p0 PC/modem address: `0x00`

This list is a Helianthus policy with spec provenance for each row, not a
standard source role. Device/profile roles are not selected by default merely
because they share a priority.

## Public Naming

The source-selection public API uses snake_case for exposed admission/status
fields. This plan intentionally removes old public camelCase and legacy join
field names instead of carrying compatibility aliases.
`helianthus-ha-integration` migrates in the same plan cycle.

Snake_case-only is scoped to source-selection admission/status fields and does
not rename unrelated GraphQL fields. M3 is additive and publishes the new
schema while old public admission fields remain. Public removal is M4-only
after the HA migration PR is green against the M3b GraphQL parity schema artifact.
Final merged state has no compatibility wrappers.

## Public API Migration Matrix

| Old public/API item | New path or removal | Surface | Owner | Removal milestone | Required test |
| --- | --- | --- | --- | --- | --- |
| `Joiner`, `JoinConfig`, `JoinResult`, `JoinMetrics`, `NewJoiner`, `.Join(...)` | `SourceAddressSelector`, `SourceAddressSelectionConfig`, `SourceAddressSelection`, `SourceAddressSelectionMetrics`, `NewSourceAddressSelector`, `.Select(...)` | Go API | ebusgo + gateway | M2/M3 compile migration | compile/red test old symbols, green test new API |
| `admission.admission_path_selected` | `admission.source_selection.mode` | JSON artifact/schema | gateway | M4 | M3 accepts both; M4 rejects old field |
| enum `join` | `source_selection` in `source_selection.mode` | artifact/logs/metrics | gateway | M4 | old enum rejected |
| enum `override` | `explicit_validate_only` in `source_selection.mode` | artifact/logs/metrics | gateway | M4 | old enum rejected |
| `join_result`, `joiner_selection` | `source_selection.selection` | artifact/logs | gateway | M4 | golden tests |
| `startup_admission_degraded_total` | `startup_source_selection_degraded_total` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_state` | `startup_source_selection_state` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_override_active` | `startup_source_selection_explicit_source_active` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_warmup_events_seen` | `startup_source_selection_warmup_events_seen` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_warmup_cycles_total` | `startup_source_selection_warmup_cycles_total` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_override_bypass_total` | `startup_source_selection_explicit_validate_only_total` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_override_conflict_detected` | `startup_source_selection_explicit_source_conflict_detected` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_degraded_escalated` | `startup_source_selection_degraded_escalated` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_degraded_since_ms` | `startup_source_selection_degraded_since_ms` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_consecutive_rejoin_failures` | `startup_source_selection_consecutive_failures` | expvar | gateway | M4 | expvar snapshot test |
| `startup_admission_degraded_cumulative_ms` | `startup_source_selection_degraded_cumulative_ms` | expvar | gateway | M4 | expvar snapshot test |
| `--startup-source-override` | retained as explicit source config unless separate CLI issue is opened | CLI | gateway | not removed by this plan | CLI scope test |
| `-source-addr` | maps to explicit source config or is renamed in a separate CLI issue; never bypasses validation | CLI | gateway | M3 semantics, optional M4 rename | CLI/config test |
| add-on `source_addr` | `auto` maps to source-selection default policy; exact byte maps to explicit validate-only | add-on config | ha-addon + gateway docs | M3 | add-on config rendering test |
| add-on `source_addr_state_file` / `/data/source_addr.last` | legacy raw-byte migration input only; new persistence is metadata-scoped | add-on config + persistence | ha-addon + gateway | M3/M4 docs cleanup | persistence migration and rollback test |
| MCP flat `bus_admission` admission fields | `status.bus_admission.source_selection` | MCP | gateway | M4 for old flat fields | golden JSON test |
| MCP `ebus.v1.rpc.invoke` fixed source `0x71` invariant | normal bus-reaching invoke uses active-probed `SourceAddressSelection.Source`; invoke fails closed until `active_probe_passed` | MCP RPC | gateway + docs | M3 | rpc.invoke source authority tests |
| GraphQL internal `BusAdmission` mapper with no public field | M3b adds only `busSummary.status.bus_admission.source_selection`; no temporary public `busAdmission` alias is introduced | GraphQL | gateway + HA | M3b | introspection proves new snake_case field exists and `busAdmission` remains absent |
| GraphQL `daemonStatus.initiatorAddress` and `daemon_status.initiator_address` | retained only as display/status mirrors of `source_selection.selected_source`; neither is an independent source authority | GraphQL | gateway + HA | M3/M4 | introspection and HA query tests cover both aliases |
| MCP/GraphQL/HA public `params.source` / `invoke.params.source` | normal operations do not use caller source as source authority; missing source uses admitted source, matching source is accepted only as redundant diagnostic input, nonmatching source is rejected, and degraded admission fails closed | MCP + GraphQL + HA writes | gateway + HA | M3/M6/M4 | missing/matching/nonmatching/degraded tests |
| Transport-specific MCP explicit source override | only transport-specific diagnostic MCPs may use a non-admitted user source; override is per-request, explicit, audited, non-persistent, and never updates admitted source | MCP transport diagnostics | gateway | M3/M4 | explicit override tests prove no leakage into normal operations |
| GraphQL bus-reaching mutations `setCircuitConfig`, `setSystemConfig`, `setZoneConfig`, `setBoilerConfig`, `setZoneTimeProgram`, `setDhwTimeProgram`, and snake_case aliases using hidden or fallback source authority such as `mutationSourceAddr=0x31` | every gateway-owned bus-reaching mutation uses admitted source after `active_probe_passed` or fails closed when admission is degraded/untrusted | GraphQL | gateway + HA | M3/M6 | mutation unit tests remove fixed `0x31` authority for config, boiler, zone time-program, and DHW time-program alias families |
| Vaillant B503 dispatcher and B503 MCP/GraphQL bridge hard-coded gateway source `0x71` | B503 dispatcher source comes only from admitted source after `active_probe_passed`; B503 bus writes fail closed before admission | gateway internal + MCP + GraphQL | gateway | M3 | `TestB503DispatcherUsesAdmittedSourceOrFailsClosed`, `TestB503GraphQLBridgeUsesAdmittedSource` |
| NM runtime `FF00`/`FF02` gateway-originated emits through `rpc_source.Gateway` or equivalent fixed `0x71` | NM source comes only from admitted source after `active_probe_passed`; NM fails closed before admission and while degraded | gateway NM | gateway | M3 | `TestNMRuntimeUsesAdmittedSourceAfterAdmission`, `TestNMRuntimeFailsClosedBeforeAdmission` |
| Portal explorer default or request/query source override | Portal explorer is a normal gateway-owned bus-reaching surface: it uses admitted source after `active_probe_passed`, rejects independent source overrides, and fails closed before admission/degraded | Portal | gateway | M3/M4 | `TestPortalExplorerUsesAdmittedSource`, `TestPortalExplorerRejectsSourceOverride` |
| adaptermux/proxy external client source authority, including the Python `helianthus-vrc-explorer` application and ebusd | external proxy clients keep their own per-session eBUS source on their ENS/ENH/TCP proxy connection; gateway active path still uses only admitted source and external sessions never update admitted source | adaptermux/proxy | gateway + adapter-proxy | M3/M7 | `SAS-SRC-01..02` source-isolation cases prove admitted-source immutability; PX01..PX12 remains adjunct wire-semantics evidence only |
| HA write fallback source `0x31` | removed; HA writes omit source or use admitted source from source-selection status, and fail closed on degraded/untrusted admission | HA integration | HA | M6 | climate/water-heater/write service tests |
| missing source-selection status on healthy-empty payload | `schema_incompatible` repair | HA | HA | M6 | setup test |
| current docs text `gentle-join` / `gentlejoin` / `join-capable` | `source address selection`, `source-selection capable`, or historical-only exception | docs | docs + gateway | M1 for normative docs, M4 for cleanup gate | terminology gate with historical allowlist |

GraphQL final path is `busSummary.status.bus_admission.source_selection` with
snake_case nested fields. Introspection tests prove the path exists, M4 old
admission aliases are absent, and unrelated fields such as
`busMessages.items.sourceAddress` remain.

After admission succeeds, normal Helianthus source authority is singular:
gateway-owned bus-reaching operations use `SourceAddressSelection.Source`. That
source may come from validated startup configuration, automatic source address
selection, or metadata-scoped cached source validation, but normal MCP tools,
GraphQL mutations, Portal explorer requests, semantic pollers/writers,
schedulers, NM runtime, B503 dispatcher/bridge, HA writes, and gateway-internal
callers must not hard-code or independently choose `0x71`, `0x31`, or any other
source byte. A source override is allowed only for transport-specific
diagnostic MCP requests made explicitly by the user; it is a single-request,
audited, non-persistent transport diagnostic and does not update the admitted
source. Portal explorer is not part of this override exception. The name
`VRC Explorer` refers here to the separate Python `helianthus-vrc-explorer`
application when it connects as an external proxy client, not to Portal
explorer. The gateway active path connects to adaptermux with the admitted
source and then uses only that source/companion pair. Other adaptermux/proxy
clients that connect over ENS, ENH, TCP, or equivalent proxy surfaces, including
the Python `helianthus-vrc-explorer` application and ebusd, are outside gateway
source authority; they may use their own eBUS source address on their own
session and must not mutate the gateway admitted source.

## Proposed API

```go
type SourceAddressObservationBus interface {
    Listen(ctx context.Context, onFrame func(Frame)) error
}

type SourceAddressKnownAddressEvidence struct {
    Address    byte
    State      SourceAddressOccupancyState
    Provenance string
    RoleHint   string
    ObservedAt time.Time
}

type SourceAddressPolicy struct {
    StandardDescription *SourceAddressStandardDescription
    Priority        *SourceAddressPriorityIndex
    ExplicitAddress *byte
    PreviousValidatedSource *byte
    Exclude         []byte
}

type SourceAddressSelectionConfig struct {
    ListenWarmup       time.Duration
    Policy             SourceAddressPolicy
    KnownAddresses     []SourceAddressKnownAddressEvidence
}

type SourceAddressSelectionMode string

const (
    SourceAddressSelectionDefaultPolicy SourceAddressSelectionMode = "default_policy"
    SourceAddressSelectionConstrained   SourceAddressSelectionMode = "source_description_constrained_policy"
    SourceAddressSelectionPriorityOnly  SourceAddressSelectionMode = "priority_filtered_default_policy"
    SourceAddressSelectionExplicitOnly  SourceAddressSelectionMode = "explicit_validate_only"
)

type SourceAddressSelection struct {
    Source          byte
    CompanionTarget byte
    Mode            SourceAddressSelectionMode
    Metrics         SourceAddressSelectionMetrics
}

func NewSourceAddressSelector(
    bus SourceAddressObservationBus,
    cfg SourceAddressSelectionConfig,
) (*SourceAddressSelector, error)

func ValidateSourceAddressSelectionConfig(cfg SourceAddressSelectionConfig) error

func (s *SourceAddressSelector) Select(ctx context.Context) (SourceAddressSelection, error)
```

Gateway startup selector operation is passive-only. It does not issue inquiry,
active reads, scans, or writes. Inquiry behavior belongs to diagnostic tooling
or the gateway-owned active-probe FSM after candidate selection.

Transport capability is split into `source_selection_active_capable` and
`passive_observe_first_capable`. ENH/ENS direct transports can be capable of
bounded active validation without having enough passive evidence after a cold
boot. Gateway must then use only configured or current bounded probe targets; if
none exist, it enters `DEGRADED_SOURCE_SELECTION` and emits no eBUS traffic.
Tests must prove ENH/ENS capability is not treated as proof that passive
occupancy is known.
An active probe target also must pass target-address validation: no broadcast,
SYN, ESC, initiator-pattern destination, selected source, selected companion, or
target without configured/current positive target provenance.

`ExplicitAddress` cannot be combined with `StandardDescription` or `Priority`
in the first implementation. That combination is a configuration error, not a
narrowed validate-only request.

Config/validation errors are typed and stable: `config`, `validation`,
`no_available_source`, and `bus_observation`. `NewSourceAddressSelector`
returns config errors before warmup begins.

There is no gateway-startup `ForceIfAllOccupied` option. Any future force mode
is diagnostic-only, emits no active scan/write frames, never persists, and is
outside automatic startup admission.

Persistence is not part of `SourceAddressSelector`. Gateway owns persistence
and may pass a metadata-validated previous source as
`PreviousValidatedSource`; gateway commits new persistence only after active
admission probe success.
`PreviousValidatedSource` never changes candidate order; it is metadata only
when the same byte is reached in normal policy order.

## Candidate Expansion Table

| Policy fields | Effective candidate universe |
| --- | --- |
| none | `HelianthusGatewayDefaultPolicy` |
| `StandardDescription` | standard source-address table rows for the requested exact description |
| `StandardDescription + Priority` | intersection of source-description rows and requested priority |
| `Priority` only | `HelianthusGatewayDefaultPolicy` filtered to requested priority |
| `ExplicitAddress` | the exact address only, validate-only |

The priority-only row is deliberately not "all standard descriptions at this
priority" for gateway startup admission. All-description priority scans belong
to diagnostic or reverse-engineering tooling, not automatic gateway startup.

The implementation may additionally expose a validator helper when tests or
gateway fallback benefit from direct validation:

```go
func ValidateSourceAddress(
    observation SourceAddressObservation,
    source byte,
) (SourceAddressValidation, error)
```

## Companion Rule

Companion target derivation is byte modulo arithmetic:

```go
companion := byte(uint16(source) + 0x05)
```

Therefore `0xFF` has companion target `0x04`. This is protocol-valid and must
not be rejected as overflow. A live bus may still reject `0xFF` because `0x04`
is occupied or frequently addressed, but the rejection reason must name that
occupancy or collision condition.

All 25 source-to-companion mappings are table-tested. `0xF7 -> 0xFC` is called
out explicitly so the live failure can distinguish source active-probe failure
from companion occupancy.

## Occupancy And Active Validation

Passive non-observation does not prove availability. Source and companion
state is one of `unknown`, `observed_free`, `observed_occupied`, or
`stale_known_device`. `observed_free` requires same-cycle successful gateway
active validation, explicit operator-exclusive reservation, or isolated lab
fixture evidence. Silent bus warmup cannot make `0x04` free for `0xFF`.

Gateway active admission probe is required before startup scan:

`observe -> select -> active read-only directed probe -> persist/scan on
success OR quarantine/exclude/reselect on failure`.

The gateway retries at most eight candidates per boot, one active probe per
candidate. Active probe targets are bounded `AdmissionProbeTarget` records with
address, provenance, opcode/payload, and safety reason; non-observation cannot
create a target. If no bounded target exists or all candidates fail, it enters
`DEGRADED_SOURCE_SELECTION` and emits no Helianthus-originated eBUS traffic.

## Metrics And Rejection Reasons

Metrics must preserve the debugging value of the existing selection path:

- requested standard description;
- requested priority;
- effective candidate universe;
- occupancy state;
- active-probe status;
- persistence eligibility;
- quarantined sources;
- candidates considered;
- rejected candidates with reasons;
- observed source addresses;
- observed source-address-capable addresses;
- observed probable target addresses;
- top talkers by source;
- selected mode.

Required log events are `startup_admission_begin`, `candidate_rejected`,
`active_probe_failed`, `source_quarantined`, `admission_degraded`, and
`source_persisted`. GraphQL/MCP/HA degraded payloads include reason enum,
selected/failed source, companion, active probe target/opcode/status,
retryable, next action, last successful source, and retry schedule.
Bounded metrics may label only by mode, reason, phase, and transport family;
addresses, opcodes, provenance, candidates, and top talkers belong only in
structured logs/artifacts.

Reason names should describe observable facts. Examples:

- `source-observed-occupied`
- `companion-observed-as-source`
- `companion-frequently-addressed`
- `explicit-source-invalid`
- `policy-excluded`
- `active-probe-failed`

`companion-target-overflows-byte` must disappear from active code because byte
wrap is the required behavior.
