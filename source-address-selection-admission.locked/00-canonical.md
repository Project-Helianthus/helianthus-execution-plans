# Source Address Selection Admission

State: `locked`
Slug: `source-address-selection-admission`
Started: `2026-05-03`
Planner: `Codex gpt-5.5 high`

## Summary

The current startup admission implementation uses legacy "join" vocabulary for
a behavior that is not a protocol join. The code observes passive traffic,
chooses a candidate source address for Helianthus-originated active frames, and
derives the associated companion target address. That behavior should be named
and modeled directly.

This plan replaces the legacy gentlejoin/joiner model with a clear
`SourceAddressSelector` / `SourceAddressSelection` API in `helianthus-ebusgo`.
The gateway expresses operational intent and asks the lower protocol layer for
one of four modes:

1. Default policy: no standard source description, priority, or address is
   configured. The selector uses `HelianthusGatewayDefaultPolicy`, a
   Helianthus policy with explicit spec provenance for every address.
2. Source-description constrained policy: a standard source description and
   optionally an arbitration priority are configured. The selector may only use
   addresses from that standard-source list after applying the priority filter.
3. Priority-filtered default policy: a priority is configured without a
   standard source description. The selector filters
   `HelianthusGatewayDefaultPolicy` only.
4. Explicit address: an exact source address is configured. Candidate selection
   is bypassed, but source and companion availability validation remains
   mandatory.

`helianthus-ebusreg` remains outside admission. It receives the selected source
byte and continues to provide `Scan` and `ScanDirected` behavior.

## Live Problem Statement

On the real Home Assistant runtime, adapter-direct ENS selected source `0xF7`
during startup admission. Active probes using source `0xF7` then timed out.
Manual explorer reads using source `0x71` succeeded. This proves that the bus
and adapter are usable, but the selected source address was not operationally
validated before becoming the startup scan source.

A second defect is already clear: `helianthus-ebusgo` rejects `0xFF` with
reason `companion-target-overflows-byte`. The eBUS companion address rule is
byte modulo arithmetic. Therefore `0xFF + 0x05` yields companion target `0x04`.
`0xFF` is protocol-valid. It may still be unsafe on a specific bus if `0x04` is
observed as occupied, but that rejection must be an occupancy or collision
reason, not an overflow reason.

## Terminology Decision

Recommended replacement vocabulary:

| Legacy concept | Replacement |
| --- | --- |
| `Joiner` | `SourceAddressSelector` |
| `JoinResult` | `SourceAddressSelection` |
| `JoinConfig` | `SourceAddressSelectionConfig` |
| `JoinBus` | `SourceAddressObservationBus` |
| source address standard description | `SourceAddressStandardDescription` |
| eBUS priority index p0..p4 | `SourceAddressPriorityIndex` |
| `join` admission path | `source_selection` |
| explicit override path | `explicit_validate_only` |

Rationale: the new terms say what the code actually does. It selects and
validates a source address for active frames. It does not perform a formal bus
membership protocol. Gateway-level startup admission remains the operational
workflow; source address selection becomes the lower-level protocol mechanic.

The final cleanup milestone must remove legacy names from code, logs,
schemas, test names, and active documentation. Historical references may remain
inside this execution plan only where they explain the migration.

`SourceAddressStandardDescription` and `SourceAddressPriorityIndex` are
deliberately separate. The local official eBUS source-address table assigns each
source address a priority index (`p0`..`p4`) and a source-address description.
The physical arbitration byte pattern is the source address low nibble
(`0x0`, `0x1`, `0x3`, `0x7`, or `0xF`); this plan calls that value the
`arbitration_nibble`. Some rows are preallocated descriptions; other rows are
free-use rows with a recommendation for a device family. Recommendation is not
the same thing as the standard description. Priority index is not a role, class,
or Helianthus desirability signal.

Official arbitration rank is separate from the Helianthus gateway default
candidate order. During eBUS contention, the lower arbitration bit pattern wins:
p0 / `0x0` outranks p1 / `0x1`, then p2 / `0x3`, p3 / `0x7`, and p4 / `0xF`.
Within otherwise equal contention the lower source byte wins. The gateway
default intentionally starts with p4/free-use/PC-style candidates as Helianthus
policy; implementation and docs must never call p4 "higher priority."

Thermostat, mixer circuit, heating source, and profile/device categories are
not eBUS-generic source-address descriptions unless the source-address table
names them. Those concepts belong in profile-specific or target/responder
taxonomy, not in the source selection API.

## Standard Source Address Table

`helianthus-docs-ebus` owns the normative versioned source-address table.
`helianthus-ebusgo` implements the same static table as code constants and
tests reference the exact docs section as the normative source. There is no
JSON/YAML table import and no generated table artifact. This is static protocol
data; we implement it once and keep the docs reference close to the code/tests.
M1 docs must merge before M2 ebusgo merges.

The docs table must cite and be mechanically checked against the local official
specification files already present in this workspace:

- `docs/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:28-60` for the prescribed
  25 source/master address rows and free-use recommendation note;
- `docs/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:69-77` for the `0x04`
  companion reservation for master/source `0xFF`;
- `docs/Spec_Prot_12_V1_3_1_E.en.md:178-184` for the source-plus-five
  companion rule and the `0xFF -> 0x04` special case;
- `docs/Spec_Prot_12_V1_3_1_E.en.md:254-256` for the source address
  arbitration definition and 25-address limit;
- `docs/Spec_Prot_12_V1_3_1_E.en.md:320-349` and
  `docs/SRC/Spec_Prot_12_V1_3_1_E.md:320-349` for the priority-class /
  sub-address split used to derive `priority_index` and `arbitration_nibble`;
- `docs/Spec_Prot_12_V1_3_1_E.en.md:471-478` for ACK `0x00` / NACK `0xFF`
  context.

The docs table must have a stable anchor, table version, and Markdown content
hash. `helianthus-ebusgo` constants embed that anchor/version/hash as test
fixtures so drift is visible without importing generated data. M1 docs CI also
checks every table row against the local official spec excerpts above so a bad
Helianthus docs table cannot become self-ratifying.

Lock values before plan promotion:

- docs anchor: `#ebus-source-address-table-v1`;
- table version: `ebus-source-address-table/v1`;
- hash algorithm: SHA-256 over the exact Markdown table block from the header
  row through the last data row, UTF-8 encoded, LF line endings, trailing spaces
  stripped per line, and exactly one terminal LF. The heading and surrounding
  prose are excluded. Docs CI and ebusgo tests verify the same normalized bytes;
- current normalized table hash: `e78954445087f63064818ab60a2739b9a6b9bf0ae0147fbe92aac5ac76592103`.

| Source | Priority index | Arbitration nibble | Official description summary | Canonical description | Free-use | Recommended for | Companion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `0x00` | p0 | `0x0` | PC/Modem | PC/Modem | no | none | `0x05` |
| `0x10` | p0 | `0x0` | Heating controller | Heating regulator | no | none | `0x15` |
| `0x30` | p0 | `0x0` | Heating circuit controller 1 | Heating circuit regulator 1 | no | none | `0x35` |
| `0x70` | p0 | `0x0` | Heating circuit controller 2 | Heating circuit regulator 2 | no | none | `0x75` |
| `0xF0` | p0 | `0x0` | Heating circuit controller 3 | Heating circuit regulator 3 | no | none | `0xF5` |
| `0x01` | p1 | `0x1` | Hand programmer / Remote control | Handheld programmer / remote | no | none | `0x06` |
| `0x11` | p1 | `0x1` | Bus interface / Climate controller | Bus interface / climate regulator | no | none | `0x16` |
| `0x31` | p1 | `0x1` | Bus interface | Bus interface | no | none | `0x36` |
| `0x71` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0x76` |
| `0xF1` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0xF6` |
| `0x03` | p2 | `0x3` | Burner controller 1 | Combustion controller 1 | no | none | `0x08` |
| `0x13` | p2 | `0x3` | Burner controller 2 | Combustion controller 2 | no | none | `0x18` |
| `0x33` | p2 | `0x3` | Burner controller 3 | Combustion controller 3 | no | none | `0x38` |
| `0x73` | p2 | `0x3` | Burner controller 4 | Combustion controller 4 | no | none | `0x78` |
| `0xF3` | p2 | `0x3` | Burner controller 5 | Combustion controller 5 | no | none | `0xF8` |
| `0x07` | p3 | `0x7` | empty | Not preallocated | yes | none | `0x0C` |
| `0x17` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x1C` |
| `0x37` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x3C` |
| `0x77` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x7C` |
| `0xF7` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0xFC` |
| `0x0F` | p4 | `0xF` | Clock module / Radio clock module | Clock/radio-clock module | no | none | `0x14` |
| `0x1F` | p4 | `0xF` | Burner controller 6 recommendation | Not preallocated | yes | Combustion controller 6 | `0x24` |
| `0x3F` | p4 | `0xF` | Burner controller 7 recommendation | Not preallocated | yes | Combustion controller 7 | `0x44` |
| `0x7F` | p4 | `0xF` | Burner controller 8 recommendation | Not preallocated | yes | Combustion controller 8 | `0x84` |
| `0xFF` | p4 | `0xF` | PC | PC | no | none | `0x04` |

Priority-index mapping is normative and must be tested for all 25 source
addresses: p0 has arbitration nibble `0x0`, p1 has `0x1`, p2 has `0x3`, p3 has
`0x7`, and p4 has `0xF`. The implementation must document which source address
wins during eBUS contention according to the standard, but must not treat
`SourceAddressPriorityIndex` as Helianthus desirability. Ordering within a
priority index and the choice to prefer the gateway default list are Helianthus
policy, not standard arbitration semantics.
The docs checker compares the summary columns with an official-spec fixture that
also records the exact source lines, source file SHA-256 values, italic/free-use
markers, and recommendation provenance. The Markdown table keeps readable
summaries; it does not pretend those cells are verbatim OCR/source text.

## Helianthus Gateway Default Policy

When the gateway does not specify a standard source description, priority, or
exact address, the selector uses this exact candidate order:

1. p4: `0xFF`, `0x7F`, `0x3F`, `0x1F`
2. p3: `0xF7`, `0x77`, `0x37`, `0x17`, `0x07`
3. p1: `0x11`, `0x31`
4. p0: `0x00`

This is not a standard eBUS source description. It is the Helianthus
gateway/tool default policy. Every candidate must still pass occupancy checks
and gateway active validation before it can be used for startup scan or
persistence.

`helianthus-ebusgo` may expand any standard description for diagnostic or
library use. Gateway startup admission has a stricter allowlist:
`PC`, `PCModem`, `BusInterfaceClimateRegulator`, `BusInterface`, and
`NotPreallocated`. `official_description_summary`, `canonical_description`,
`free_use`, and `recommended_for` are separate fields. `recommended_for` is
informational only and does not constrain or authorize gateway startup selection.
Gateway startup must not impersonate
combustion-controller, clock/radio-clock, heating regulator, or heating circuit
regulator descriptions unless the operator uses explicit address mode or a
separate diagnostic-only mode outside automatic startup.

When the gateway specifies an allowed standard source description, the selector
expands the standard table for that description only. When it also specifies a
priority, priority intersects that table. If priority is specified without a
description, gateway startup admission filters `HelianthusGatewayDefaultPolicy`
to that priority only; it never searches all standard descriptions at that
priority.

When the gateway specifies an exact address, the selector performs
validate-only behavior. Persisted last-known state cannot override the explicit
address. Candidate fallback is not performed inside `helianthus-ebusgo`.

## API Contract

`helianthus-ebusgo/protocol` owns the reusable protocol mechanics:

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

type SourceAddressSelection struct {
    Source          byte
    CompanionTarget byte
    Mode            SourceAddressSelectionMode
    Metrics         SourceAddressSelectionMetrics
}

type SourceAddressSelector struct {
    // implementation private
}

func NewSourceAddressSelector(
    bus SourceAddressObservationBus,
    cfg SourceAddressSelectionConfig,
) (*SourceAddressSelector, error)

func ValidateSourceAddressSelectionConfig(cfg SourceAddressSelectionConfig) error

func (s *SourceAddressSelector) Select(ctx context.Context) (SourceAddressSelection, error)

func ValidateSourceAddress(
    observation SourceAddressObservation,
    source byte,
) (SourceAddressValidation, error)
```

The selector used by gateway startup is passive-only. It must not issue
`InquiryExistence`, active reads, scans, or writes. Any future bus inquiry API is
diagnostic-only or must be called by the gateway-owned active admission FSM
after a candidate source has been selected.

Transport capability has two separate booleans. `source_selection_active_capable`
means the transport can emit a bounded active admission probe after candidate
selection. `passive_observe_first_capable` means the transport can build a
current passive occupancy snapshot before selection. Direct ENH/ENS may be
`source_selection_active_capable` while lacking enough passive evidence after a
cold boot; in that case gateway may actively validate only against configured
or current bounded probe targets, otherwise it must degrade with zero eBUS
traffic. The code must not infer passive availability merely from the transport
being ENH/ENS-capable.

`KnownAddresses` carries topology/cache evidence into the selector. Cache-only
or topology-only evidence must preserve its provenance and freshness; it cannot
be silently downgraded to passive non-observation.

`PreviousValidatedSource` never reorders candidates. It is metadata attached to
a candidate when that byte is reached in the normal candidate order and all
metadata dimensions still match. A previous source outside the current policy
or with mismatched metadata is diagnostic-only and is not passed as a selection
hint.

`ExplicitAddress` is mutually exclusive with `StandardDescription` and
`Priority` in the first implementation. `ExplicitAddress +
StandardDescription` or `ExplicitAddress + Priority` is a configuration error.
This avoids implicit filtering around an operator-selected exact source.

Errors must be typed by kind: `config`, `validation`, `no_available_source`,
and `bus_observation`. Reason strings are stable test fixtures.

## Public API Migration Matrix

Snake_case-only applies to source-selection admission/status public surfaces,
not to unrelated GraphQL fields such as message `sourceAddress` unless a
separate GraphQL naming plan is opened. Final M4 merged state has no aliases,
wrappers, or compatibility fields for the old admission names. M3 is additive:
it publishes the new schema while retaining old public fields until HA is green.

| Old public/API item | New path or removal | Surface | Owner | Removal milestone | Required test |
| --- | --- | --- | --- | --- | --- |
| `Joiner`, `JoinConfig`, `JoinResult`, `JoinMetrics`, `NewJoiner`, `.Join(...)` | `SourceAddressSelector`, `SourceAddressSelectionConfig`, `SourceAddressSelection`, `SourceAddressSelectionMetrics`, `NewSourceAddressSelector`, `.Select(...)` | Go API | ebusgo + gateway | M2/M3 compile migration | compile failure/red test for old symbols; green test for new API |
| artifact `admission.admission_path_selected` | `admission.source_selection.mode` | JSON artifact/schema | gateway | M4 | M3 accepts both; M4 rejects old field and accepts new field |
| artifact enum `join` | `source_selection` in `source_selection.mode` | artifact/logs/metrics | gateway | M4 | old enum rejected in M4 |
| artifact enum `override` | `explicit_validate_only` in `source_selection.mode` | artifact/logs/metrics | gateway | M4 | old enum rejected in M4 |
| artifact/log `join_result`, `joiner_selection` | `source_selection.selection` | artifact/logs | gateway | M4 | schema/log golden tests |
| expvar `startup_admission_degraded_total` | `startup_source_selection_degraded_total` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_state` | `startup_source_selection_state` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_override_active` | `startup_source_selection_explicit_source_active` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_warmup_events_seen` | `startup_source_selection_warmup_events_seen` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_warmup_cycles_total` | `startup_source_selection_warmup_cycles_total` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_override_bypass_total` | `startup_source_selection_explicit_validate_only_total` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_override_conflict_detected` | `startup_source_selection_explicit_source_conflict_detected` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_degraded_escalated` | `startup_source_selection_degraded_escalated` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_degraded_since_ms` | `startup_source_selection_degraded_since_ms` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_consecutive_rejoin_failures` | `startup_source_selection_consecutive_failures` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| expvar `startup_admission_degraded_cumulative_ms` | `startup_source_selection_degraded_cumulative_ms` | expvar | gateway | M4 | expvar snapshot proves old key absent and new key present |
| CLI `--startup-source-override` | retained as operator explicit source config unless a separate CLI rename issue is opened | CLI | gateway | not removed by this plan | CLI compatibility test documents scope |
| CLI/config `-source-addr` | maps to explicit source config or is renamed in a separate CLI issue; never means selector bypass | CLI | gateway | M3 semantics, optional M4 rename | CLI/config migration test |
| add-on `source_addr` | maps to gateway explicit source config; `auto` uses source-selection default policy | add-on config | ha-addon + gateway docs | M3 semantics | add-on config rendering test |
| add-on `source_addr_state_file` / legacy `/data/source_addr.last` | legacy raw-byte migration input only; new persistence is metadata-scoped | add-on config + persistence | ha-addon + gateway | M3 migration, M4 docs cleanup | persistence migration and rollback test |
| MCP `status.bus_admission` without nested source selection | `status.bus_admission.source_selection` | MCP JSON | gateway | M4 for old flat admission fields | golden JSON test |
| MCP `ebus.v1.rpc.invoke` fixed source `0x71` invariant | normal bus-reaching invoke uses active-probed `SourceAddressSelection.Source`; invoke fails closed until `active_probe_passed` | MCP RPC | gateway + docs | M3 | rpc.invoke source authority tests |
| GraphQL internal `BusAdmission` mapper with no public field | M3b adds only `busSummary.status.bus_admission.source_selection`; no temporary public `busAdmission` alias is introduced | GraphQL | gateway + HA | M3b | introspection proves new snake_case field exists and `busAdmission` remains absent |
| GraphQL `daemonStatus.initiatorAddress` and `daemon_status.initiator_address` | retained only as display/status mirrors of `source_selection.selected_source`; neither is an independent source authority | GraphQL | gateway + HA | M3/M4 | introspection and HA query tests cover both aliases |
| MCP/GraphQL/HA public `params.source` / `invoke.params.source` | normal operations do not use caller source as source authority; missing source uses admitted source, matching source is accepted only as redundant diagnostic input, nonmatching source is rejected, and degraded admission fails closed | MCP + GraphQL + HA writes | gateway + HA | M3/M6/M4 | missing/matching/nonmatching/degraded tests |
| Transport-specific MCP explicit source override | only transport-specific diagnostic MCPs may use a non-admitted user source; override is per-request, explicit, audited, non-persistent, and never updates admitted source | MCP transport diagnostics | gateway | M3/M4 | explicit override tests prove no leakage into normal operations |
| GraphQL bus-reaching mutations `setCircuitConfig`, `setSystemConfig`, `setZoneConfig`, `setBoilerConfig`, `setZoneTimeProgram`, `setDhwTimeProgram`, and snake_case aliases using hidden or fallback source authority such as `mutationSourceAddr=0x31` | every gateway-owned bus-reaching mutation uses admitted source after `active_probe_passed` or fails closed when admission is degraded/untrusted | GraphQL | gateway + HA | M3/M6 | mutation unit tests remove fixed `0x31` authority for config, boiler, zone time-program, and DHW time-program alias families |
| Vaillant B503 dispatcher and B503 MCP/GraphQL bridge hard-coded gateway source `0x71` | B503 dispatcher source comes only from admitted source after `active_probe_passed`; B503 bus writes fail closed before admission | gateway internal + MCP + GraphQL | gateway | M3 | `TestB503DispatcherUsesAdmittedSourceOrFailsClosed`, `TestB503GraphQLBridgeUsesAdmittedSource` |
| NM runtime `FF00`/`FF02` gateway-originated emits through `rpc_source.Gateway` or equivalent fixed `0x71` | NM source comes only from admitted source after `active_probe_passed`; NM fails closed before admission and while degraded | gateway NM | gateway | M3 | `TestNMRuntimeUsesAdmittedSourceAfterAdmission`, `TestNMRuntimeFailsClosedBeforeAdmission` |
| Portal explorer default or request/query source override | Portal explorer is a normal gateway-owned bus-reaching surface: it uses admitted source after `active_probe_passed`, rejects independent source overrides, and fails closed before admission/degraded | Portal | gateway | M3/M4 | `TestPortalExplorerUsesAdmittedSource`, `TestPortalExplorerRejectsSourceOverride` |
| adaptermux/proxy external client source authority, including the Python `helianthus-vrc-explorer` application and ebusd | external proxy clients keep their own per-session eBUS source on their ENS/ENH/TCP proxy connection; gateway active path still uses only admitted source and external sessions never update admitted source | adaptermux/proxy | gateway + adapter-proxy | M3/M7 | `SAS-SRC-01..02` source-isolation cases prove admitted-source immutability; `PX01..PX12` remains adjunct wire-semantics evidence only |
| HA write fallback source `0x31` | removed; HA writes omit source or use admitted source from source-selection status, and fail closed on degraded/untrusted admission | HA integration | HA | M6 | climate/water-heater/write service tests |
| HA-consumed healthy-empty payload without admission status | `schema_incompatible` repair from missing `bus_admission.source_selection` | HA integration | HA | M6 | setup test for missing field |
| docs text `gentle-join` / `gentlejoin` / `join-capable` for current behavior | `source address selection`, `source-selection capable`, or historical-only exception | docs | docs + gateway | M1 for normative docs, M4 for cleanup gate | terminology gate with historical allowlist |

Final GraphQL source-selection path:
`busSummary.status.bus_admission.source_selection`. The field is nullable until
startup admission has reported at least one state; nested fields are snake_case:
`state`, `mode`, `outcome`, `reason`, `selected_source`, `failed_source`,
`companion_target`, `active_probe`, `retryable`, `next_action`,
`last_successful_source`, `automatic_retry_scheduled`, and
`rejected_candidates`. Introspection tests prove this path exists, old
admission aliases are absent in M4, and unrelated GraphQL fields such as
`busMessages.items.sourceAddress` remain unchanged.

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

Stable source-selection taxonomy for GraphQL/MCP/HA:

- `state`: `pending`, `active`, or `degraded`;
- `mode`: `default_policy`, `source_description_constrained_policy`,
  `priority_filtered_default_policy`, or `explicit_validate_only`;
- `outcome`: `not_started`, `active_probe_passed`,
  `candidate_quarantined`, `all_candidates_failed`, or `operator_action_required`;
- gateway `reason`: `bus_silent_occupancy_unknown`, `active_probe_failed`,
  `all_candidates_failed`, `explicit_source_active_probe_failed`,
  `companion_occupied`, `companion_unknown`, `collision_active_probe`,
  `collision_startup_scan`, or `collision_early_poll`;
- HA repair codes: `schema_incompatible`, `admission_degraded`, and
  `empty_inventory_untrusted`;
- `selected_source`, `failed_source`, `companion_target`;
- `active_probe.target`, `active_probe.opcode`, `active_probe.status`;
- `retryable`, `automatic_retry_scheduled`, `next_action`;
- `last_successful_source`;
- `rejected_candidates` with reason, occupancy state, and evidence provenance.

## Candidate Expansion Semantics

| Request | Candidate universe |
| --- | --- |
| no standard description, no priority, no explicit address | `HelianthusGatewayDefaultPolicy`: p4, then p3, then p1, then p0 |
| standard description only | standard source-address table rows for that exact description |
| standard description + priority | intersection of source-description rows and requested priority |
| priority only | `HelianthusGatewayDefaultPolicy` filtered to that priority |
| explicit address | validate only the exact address; no selection, no fallback, no persisted override |

The priority-only case is intentionally conservative for gateway startup. It
does not mean "all standard descriptions at this priority." A diagnostic or
reverse-engineering tool may add such a mode later, but gateway startup
admission must not impersonate heating regulator, heating circuit regulator, or
combustion-controller descriptions merely because they share a priority.

Validation computes `CompanionTarget` with byte modulo arithmetic:

```go
companion := byte(uint16(source) + 0x05)
```

The `0xFF -> 0x04` case is expected and must be tested. If `0x04` is observed
as occupied, the validation reason must be companion occupancy, not overflow.
The `0xF7 -> 0xFC` case is also explicit because it is the live failing source.
Tests must cover all 25 source-to-companion mappings.

## Occupancy Model

Passive non-observation is not proof of availability. Source and companion
addresses carry one of these states:

- `unknown`: insufficient current evidence;
- `observed_free`: explicitly validated by current positive free evidence;
- `observed_occupied`: current evidence shows use as source or companion;
- `stale_known_device`: known from cache/topology but not seen in this warmup.

Silent bus warmup, failed inquiry, or missing passive traffic leaves companion
state `unknown` or `stale_known_device`, not free. Startup admission must not
select `0xFF` merely because `0x04` was absent from a short observation window.
Companion occupancy checks include current source observations, frequently
addressed targets, discovered-device/topology data, and stale-known-device
cache. On this installation, known `0x04` NETX3 occupancy must skip `0xFF` with
a companion-occupied reason before active probing. The validation object must
preserve the address, occupancy state, evidence provenance, and stale/current
classification for each rejected source and companion.

The only valid provenances for `observed_free` are a same-cycle successful
gateway active validation lease, an explicit operator-exclusive reservation, or
an isolated lab fixture used by unit tests. Passive silence is never
`observed_free`. In live default startup, `0xFF` is skipped unless companion
`0x04` has positive free evidence; unknown or stale `0x04` withholds `0xFF`.

`ForceIfAllOccupied` is removed from gateway startup admission. Any future
force mode is diagnostic-only, performs no active scan/write, never persists,
and requires explicit operator confirmation.

## Active Admission Probe FSM

Gateway owns active usability validation. `helianthus-ebusgo` returns a
candidate and passive validation metadata; gateway must not start discovery
scan or semantic polling with that source until active admission probe succeeds.

Required FSM:

1. observe warmup and build occupancy snapshot;
2. select candidate using policy and current `Exclude` set;
3. run one non-destructive active admission probe with the selected source;
4. on success, mark `active_probe_passed`, allow startup scan, and only then
   allow persistence;
5. on timeout/NACK/collision, record reason, quarantine the source for this
   boot, append it to `Exclude`, and reselect;
6. retry at most eight candidates per boot, one active probe per candidate;
7. if all candidates fail or no bounded target exists for the active probe,
   enter `DEGRADED_SOURCE_SELECTION` and emit no Helianthus-originated eBUS
   traffic.

The active admission probe is a read-only directed probe against an explicit
bounded target candidate. `AdmissionProbeTarget` records address, provenance,
profile hint, selected opcode/payload, and why it is safe. Target order is:
configured startup targets, then passive promoted suspects with current directed
traffic evidence. Documented lab topology is not an automatic third source; it
is valid only when materialized as explicit operator configuration. Mere
non-observation cannot create a probe target. At most three probe targets may be
considered for one candidate source. The only first-implementation admission probe is addressed
`0x07/0x04` identity against a bounded target, classified
`read_only_bus_load`. M1 must explicitly supersede the current
`startup-admission-and-discovery.md` rule that directed probes happen only after
admission: this is a bounded pre-discovery source-validation exception and it
counts against the startup `0x07/0x04` budget. Admission probes explicitly forbid
`0x07/0xFE`, `0x07/0xFF`, all `0x0F` test commands, NM `0xFF` messages,
broadcasts, memory writes, mutating services, full-range probes, and any
`system_nm_runtime` caller-context bypass. If no bounded target exists, gateway
enters `DEGRADED_SOURCE_SELECTION` without eBUS traffic.

`AdmissionProbeTarget` has its own validation gate before any probe is emitted.
The target must have configured or current positive target provenance and must
not be broadcast, SYN, ESC, an initiator-pattern address, the selected source,
or the selected companion. The gate rejects at least `0xFE`, `0xAA`, `0xA9`,
valid initiator-pattern destinations, selected source, selected companion, and
any target with only passive non-observation as evidence. This prevents an
i2i/no-response destination from being mistaken for a source-usability timeout.

When `passive_observe_first_capable=false`, pre-probe eligibility is stricter.
Gateway may tentatively probe a candidate only if source and companion are not
known occupied or stale-known and the operator supplied an exclusive
reservation or a configured/current positive target exists for the bounded
probe. If source or companion occupancy is unknown and no such reservation or
bounded target exists, startup degrades with zero eBUS traffic. If source or
companion is known occupied or stale-known, the candidate is rejected without
probing.

Explicit address mode follows the same active-probe rule. On the current HA
topology, explicit `0x71` active-probe success is a gateway merge blocker
because it is the known-good field control. If explicit `0x71` fails during M3
evidence, the PR blocks and the operator must investigate before continuing.
`0x71` is not an automatic default fallback merely because it succeeded in this
incident.

`DEGRADED_SOURCE_SELECTION` has one invariant everywhere: gateway emits no
Helianthus-originated eBUS traffic until a later admission cycle succeeds or the
operator explicitly selects a validated source. This includes startup scan,
semantic polling, MCP/GraphQL bus-reaching invoke, NM `FF 00` / `FF 02`, `07 FF`
sign-of-life, and companion responder activity. It is not enough to avoid only
the last failed source.

## Persistence Contract

`helianthus-ebusgo` must not write last-good source state after passive
selection. Persistence is gateway-owned and committed only after:

- source and companion validation pass;
- active admission probe passes;
- the source was not explicitly configured validate-only, unless the operator
  explicitly enables explicit-source persistence;
- the persistence key matches current instance, transport family, adapter/proxy
  identity, policy fingerprint, companion, schema version, and validation type.

Persistence records are metadata objects, not raw bytes. They include source,
companion, policy fingerprint, config source, transport family, adapter/proxy
identity, validation type, active-probe result, timestamp, and schema version.
Writes are atomic. Failed active probes quarantine the source for the current
boot and must not update persistence.

Legacy raw `source_addr.last` is untrusted migration input. It may be read only
to emit a diagnostic explaining why it was ignored. It is not passed as
`PreviousValidatedSource`, not used for scan, and not rewritten until active
probe succeeds under the current metadata key. Any metadata mismatch for
transport family, adapter/proxy identity, companion, policy fingerprint, schema
version, validation type, or topology freshness invalidates the persisted hint
for selection.

Persistence is also delayed until the first directed startup scan window is
collision-clean. Collision thresholds are phase-specific:

- active probe: one collision quarantines the candidate for the boot;
- startup scan: two collisions within the initial directed scan window
  invalidate persistence and trigger reselection/degraded;
- early poll: three collisions within five minutes invalidate last-good
  persistence and trigger operator-visible degraded state;
- coexistence run: any collision aborts the coexistence sub-run and restores
  eBUSd stopped state.

## Repository Responsibilities

`helianthus-ebusgo`:

- owns the selector, policy expansion, passive observation interpretation,
  source occupancy checks, companion occupancy checks, explicit validate-only
  mode, and selection metrics.
- implements the docs-owned standard source-address table as static code
  constants/definitions, with tests that cite the exact docs section.
- fixes `0xFF` companion derivation.
- exposes stable, readable names for the new contract.

`helianthus-ebusgateway`:

- owns startup admission orchestration, transport admission dispatch,
  gateway configuration, operator override semantics, active-probe validation,
  retry/fallback after active probe failure, artifacts, logs, and metrics.
- owns source persistence, quarantine, active-probe transcript, and HA-facing
  degraded-state propagation.
- adapts `PassiveTransactionReconstructor` events into
  `SourceAddressObservationBus`.
- does not duplicate selector candidate policy.
- owns migration of every gateway-owned bus-reaching path away from current
  fixed, fallback, or caller-selected source assumptions: no Helianthus-origin
  traffic may be emitted until `active_probe_passed`; emitted frames use the
  admitted source unless the request is a transport-specific diagnostic MCP
  call with an explicit user-scoped, single-request source override.
- explicitly migrates Vaillant B503 dispatcher/bridge, NM runtime emits, and
  Portal explorer source handling; these are not allowed to retain hard-coded
  `0x71`, fallback `0x31`, or Portal-specific source overrides.
- current hard-coded gateway sources in GraphQL mutations, MCP source guards,
  `internal/rpc_source`, Vaillant B503 wiring, Portal explorer, and the HA add-on
  wrapper are known implementation defects for this plan. Their presence at the
  implementation parent is expected only as RED-test evidence; they are merge
  blockers after M3/M2a implementation and must not be treated as accepted
  runtime behavior.
- RED evidence must separately cover the transport-specific MCP one-request
  explicit source override, B503 dispatcher, B503 GraphQL bridge, NM runtime,
  Portal explorer admitted-source-only behavior, and adaptermux external-client
  source isolation. Each row records command, parent SHA, expected RED failure,
  green assertion, and artifact path.

`helianthus-ha-integration`:

- migrates to the new source-selection admission/status schema before gateway
  removes public legacy/camelCase admission fields.
- treats degraded admission and healthy-looking empty inventory as untrusted
  data, not as permission to delete existing entities.
- removes write fallback sources (`0x31`) and routes write calls through admitted
  source-selection authority or fails closed when admission is degraded/untrusted.

`helianthus-ha-addon`:

- owns add-on wrapper/config migration before M3a runtime validation.
- stops wrapper-side raw source reuse and raw-byte persistence from
  `source_addr_state_file`; leftover `/data/source_addr.last` becomes migration
  input for gateway diagnostics only.
- maps `source_addr=auto` to gateway default source-selection policy and exact
  `source_addr` values to gateway explicit validate-only configuration.
- updates README/config/run-script tests and rollback handling for leftover
  legacy files.

`helianthus-ebusreg`:

- remains admission-agnostic.
- continues to accept `source byte` in `Scan` and `ScanDirected`.
- receives a no-op boundary proof rather than new admission logic.

`helianthus-docs-ebus`:

- records the durable protocol and architecture knowledge: standard source
  descriptions, priorities, gateway default policy, constrained policy,
  explicit validate-only mode, companion modulo behavior, and
  gateway/ebusgo/ebusreg separation.
- replaces stale docs that excluded `0xFF` as a source-address candidate due to
  NACK confusion: `0xFF` is valid as a source address; `0xFF` remains NACK in
  ACK/NACK byte context.
- supersedes or updates all current normative join/admission/NM docs before M2
  merges, including `architecture/startup-admission-and-discovery.md`,
  `architecture/nm-participant-policy.md`, `architecture/nm-model.md`,
  `architecture/nm-discovery.md`, `architecture/decisions.md`,
  `protocols/ebus-services/ebus-overview.md`, and
  `architecture/ebus_standard/10-rpc-source-113.md`.

## Milestones

M0 - Plan draft and lock:

- Create and review this execution plan.
- Promote to `.locked` only after adversarial review converges.

M1 - Docs source address selection:

- Add architecture docs for source address selection and validation.
- Document `HelianthusGatewayDefaultPolicy` and constrained policy behavior.
- Document that standard source description and priority are separate
  dimensions.
- Freeze the standard source-address table, `HelianthusGatewayDefaultPolicy`,
  all 25 companion mappings, priority-index mapping, and arbitration-nibble
  mapping.
- Assign a stable docs anchor, table version, and Markdown table hash for the
  source-address table.
- Cite the local official spec files listed in this plan and add docs CI that
  fails if the Helianthus source table drifts from those excerpts. The checker
  has an explicit `HELIANTHUS_OFFICIAL_SPEC_DIR` contract and records SHA-256
  for every official spec file read; repo-only CI must use a committed excerpt
  fixture with source hashes and provenance.
- Document official arbitration rank separately from Helianthus candidate
  preference: p0 outranks p1, then p2, p3, and p4; lower source byte wins within
  otherwise equal contention.
- Document standard description, free-use flag, and recommended-for as separate
  fields.
- Document `0xFF -> 0x04` and `0xF7 -> 0xFC` companion modulo behavior.
- Replace stale docs that excluded `0xFF` due to NACK byte context.
- Explicitly amend startup admission docs: directed `0x07/0x04` may be used as a
  bounded pre-discovery source-validation exception only after source selection,
  counts against the startup `0x07/0x04` budget, and does not permit broadcast
  existence probes or test commands.
- Replace `JoinResult`/configured fallback as NM local address-pair authority
  with `active_probe_passed` `SourceAddressSelection`.
- Reconcile `architecture/nm-model.md` and `architecture/nm-discovery.md` so
  current normative docs label `0x07/0xFE` as inquiry and `0x07/0xFF` as
  sign-of-life.
- Define `DEGRADED_SOURCE_SELECTION` as no Helianthus-originated eBUS traffic:
  no startup scan, no semantic polling, no MCP/GraphQL bus invoke, no NM
  broadcast, no `0x07/0xFF`, and no companion responder activity.

M2 - ebusgo selection API:

- Replace the old join symbols with `SourceAddressSelector` API.
- Implement default, constrained, and explicit validate-only modes.
- Implement source-address table expansion from static constants mirrored from
  the docs-owned table.
- Embed the docs anchor, table version, and table hash in constants/tests.
- Fix `0xFF` companion calculation and replace overflow rejection with
  companion occupancy validation.
- Implement known-address evidence input for topology/cache/stale companion
  occupancy.
- Remove gateway-startup `ForceIfAllOccupied`; any force behavior is
  diagnostic-only and non-persistent.
- Add typed config/validation/no-available-source/bus-observation errors.

M2a - HA add-on wrapper source-config migration:

- Stop add-on wrapper-side reuse of `/data/source_addr.last` before gateway
  validation.
- Stop wrapper-side raw source persistence. The add-on may preserve the legacy
  file for rollback, but it must not rewrite or promote it into active source
  config.
- Map `source_addr=auto` to gateway default source-selection policy and exact
  `source_addr` values to the best gateway-supported explicit-source contract.
  For old gateways, exact values continue to render as legacy `-source-addr`
  after wrapper-side raw persistence has been disabled. For M3a+ gateways, exact
  values render as explicit validate-only. Unknown gateway capability fails
  closed or uses the old-gateway legacy arg path without claiming
  validate-only.
- Update add-on README/config/run-script tests and rollback notes for leftover
  legacy files.
- Forbid new gateway-only flags unless version-gated, and test new add-on + old
  gateway, old add-on + new gateway, and new add-on + M3a gateway.
- Merge before M3a binary override or live runtime validation.

M3 - gateway admission migration:

- Replace gateway usage of legacy join APIs with the new selector API.
- Rename observation adapter, admission artifact fields, logs, tests, and
  metrics to source-selection vocabulary.
- Implement the active admission probe FSM exactly as specified above.
- Define `AdmissionProbeTarget` and reject unbounded probe target derivation.
- Stage M3 as MCP/artifact first, GraphQL parity second:
  - M3a freezes the MCP status payload and raw admission artifact contract;
  - M3b exposes GraphQL parity from that frozen contract and commits generated
    schema artifacts for HA tests;
  - M6 HA consumes only the M3b GraphQL parity artifact pinned by commit SHA.
- Add the new GraphQL/MCP/artifact source-selection schema as an additive public
  surface and commit generated schema artifacts for HA tests:
  `docs/schemas/source-selection-admission.graphql` and
  `docs/schemas/source-selection-admission.schema.json`.
- Migrate every gateway-owned bus-reaching path so source selection is the
  single local source authority: MCP invoke, GraphQL invoke, semantic writers,
  scheduler/time-program writers, poller writes, HA write call sites, and all
  gateway-owned GraphQL bus-reaching mutation alias families. The old
  fixed-`0x71`, hidden/fallback `0x31`, and caller-selected normal-source
  invariants are removed or rewritten in M3 docs/tests; gateway-owned
  bus-reaching operations fail closed until `active_probe_passed`, then use
  the admitted source.
- Migrate GraphQL bus-reaching mutations `setCircuitConfig`, `setSystemConfig`,
  `setZoneConfig`, `setBoilerConfig`, `setZoneTimeProgram`,
  `setDhwTimeProgram`, and snake_case aliases away from hidden fixed `0x31`
  or any other independent source authority.
- Make adapter-direct ENS live evidence, explicit `0x71` success, cold boot /
  power-cycle evidence, and before/after transport matrix evidence merge
  blockers for this milestone.
- Record both transport capability flags in evidence:
  `source_selection_active_capable` and `passive_observe_first_capable`.
  Adapter-direct ENH/ENS evidence must prove that a missing passive snapshot
  does not silently authorize automatic active probing without a configured or
  current bounded target.
- Split transport evidence:
  - capture the full T01..T88 baseline at the parent SHA before M3 code edits and
    rerun at PR head with per-case expected eBUSd state from the matrix;
  - capture a separate no-eBUSd adapter-direct admission submatrix for M3 source
    selection, with eBUSd/proxy listener disabled or guarded for the whole
    evidence window.
- Add a SAS-specific transport evidence validator in gateway CI, lock the
  parent expected-failure inventory/hash, reject unlisted xfail/xpass, and
  require `PX01..PX12` adjunct evidence for any proxy/coexistence run unless the
  proxy checks are explicitly observational-only.
- Require an independent bus-boundary transcript in the SAS evidence manifest
  before M3 can merge. The manifest records artifact path and SHA-256, capture
  point (`adapter`, `proxy`, `socket`, `tcpdump`, or a transport shim below
  gateway admission logic), and command transcript. Assertions prove degraded
  zero traffic, the bounded `0x07/0x04` probe, `0xF7` quarantine, and explicit
  `0x71` success. Gateway raw admission artifacts, status counters, logs, and
  GraphQL snapshots cannot be the sole evidence source.
- Use temporary addon binary override for M3 pre-merge lab validation. This is
  not production rollout. Production rollout is M7.
- M3 includes its own evidence runbook with exact commands and artifact paths
  for eBUSd stopped proof, proxy listener guard, adaptermux external-session
  count, binary override deploy/rollback, admission artifact capture, GraphQL
  snapshots, and explicit `0x71` validation.
- Before any M3 binary override can touch the HA runtime, implement minimal
  operator recovery surfaces: status, clear-persistence, clear-quarantine,
  re-admit, explicit-source validate, and rollback. Tests prove rollback with
  leftover new persistence does not brick old gateway/new HA pairings.
- Keep public legacy/camelCase admission/status removal blocked until the HA
  migration PR is green against the M3b GraphQL parity schema artifact; final state
  still has no compatibility aliases.
- Persist source state only after active probe success.

M4 - public API and legacy terminology removal:

- Remove public camelCase/legacy admission/status fields only after HA tests
  pass against the new snake_case source-selection schema.
- Enforce that temporary aliases and legacy names are gone after gateway and
  downstream consumers are migrated and cross-repo CI proves no references
  remain.
- Enforce an `rg` terminology gate across relevant repos for active code and
  docs, with explicit exception only for historical execution-plan references.

M5 - ebusreg no-op boundary proof:

- Confirm `helianthus-ebusreg` remains admission-agnostic.
- Add or update tests only if they protect the boundary without introducing
  admission concepts.

M6 - HA diagnostics and empty-payload guard:

- M6 develops against the M3b GraphQL parity schema artifacts by commit SHA. "HA
  green" means HA CI passes against that exact schema artifact and a gateway test
  fixture from the M3 branch, before public removal in M4.
- Add HA integration behavior for degraded admission and empty GraphQL payloads.
- Expose a repair issue or diagnostic entity when gateway admission is degraded.
- Prevent stale HA device/entity cleanup when gateway reports degraded
  admission or healthy-looking empty inventory.
- Add a smoke test proving HA surfaces admission failure instead of silently
  showing no entities.
- Add an admission preflight/coordinator before stale cleanup. Persist
  `admission_trusted=false` until `bus_admission.source_selection` is present
  and non-degraded. Mark entities unavailable while false. Cleanup resumes only
  after two consecutive healthy non-empty coordinator refreshes or explicit
  operator acknowledgement; rollback resets the acknowledgement.
- Remove and test all HA fixed `0x31` write fallbacks: climate, water heater,
  zone schedule helper, and DHW schedule helper.

M7 - live rollout and coexistence evidence:

- Record the live HA rollout and rollback runbook as an execution-plan evidence
  artifact, not as a second gateway code PR.
- Snapshot config, source-selection persistence, HA entity state, and eBUSd
  state before deployment.
- Use the AGENTS.md HA-addon local builder commands for binary override:
  stop addon, copy binary, chmod, start addon, then verify logs, GraphQL, portal,
  HA repairs, HA entity availability, and source-selection artifact.
- Back up and restore exact files/paths used for gateway config,
  source-selection persistence, HA `.storage` repair/entity state, and addon
  binary override. The runbook includes deploy, verify, clear persistence,
  clear quarantine, force re-admit, explicit-source validate, rollback binary,
  rollback config, rollback persistence, restart addon, and HA repair cleanup.
- Record a version-pair rollback matrix: old gateway + old HA, new gateway +
  old HA during additive M3, new gateway + new HA, and rollback gateway + new
  HA after M4 removal.
- Keep eBUSd stopped for M3 no-eBUSd admission evidence and M7 baseline evidence.
  Any eBUSd/proxy coexistence run requires explicit operator approval, command
  transcript, pre/post state, and restore-to-stopped proof.
- Baseline proof must record addon config, listening sockets, absence of
  reconnectable proxy listener exposure such as `127.0.0.1:8888`, ebusd
  add-on/container/process absence, adapter upstream single-owner state, and
  adaptermux external-session count zero before/during/after.
- Coexistence sub-run contract: written operator approval, max ten-minute
  runtime, exact topology, external clients started before re-admission or
  forced re-admission after they connect, external source+companion marked
  occupied, selected gateway source+companion proven disjoint, allowed read-only
  traffic only, abort on same source/companion even without collision, collision
  abort threshold of one, and timestamped restore-to-stopped proof.
- If coexistence evidence claims Python `helianthus-vrc-explorer`
  compatibility, run that application as an external proxy client with explicit
  per-session source and capture command line, client transcript, bus-boundary
  artifact, adaptermux session/source snapshot, gateway
  `bus_admission.source_selection` snapshot before/after, and proof that the
  client source did not update admitted source. The artifacts live under
  `artifacts/sas/m3/vrc-explorer-proxy-client/` and are listed in the M3
  runbook and manifest.
- PX01..PX12 is adjunct wire-semantics evidence only. Source-authority
  isolation is proven by separate `SAS-SRC-01..02` cases: generic external
  ENS/ENH/TCP proxy session with non-admitted source, and Python
  `helianthus-vrc-explorer` when that compatibility is claimed. Each case
  proves gateway `bus_admission.source_selection.selected_source` is unchanged
  before/after, records adaptermux session/source snapshots, and correlates an
  independent bus-boundary transcript. The SAS evidence validator rejects
  coexistence claims without the required passing `SAS-SRC` case artifacts.

Operator recovery surfaces are mandatory before M7: status, clear-persistence,
clear-quarantine, re-admit, explicit-source validate, and rollback. `next_action`
values map one-to-one to those actions.

## Falsifiability Gates

- `0xFF` with unoccupied `0x04`: selectable, companion is `0x04`, no overflow
  rejection reason.
- `0xFF` with occupied, unknown, or stale-known `0x04`: rejected or withheld
  for companion occupancy/unknown-state, never treated as free by absence.
- all 25 companion mappings are table-tested, including `0xF7 -> 0xFC`.
- standard description, free-use flag, and recommended-for are tested
  separately; preallocated heating-regulator/combustion-controller descriptions
  do not include free-use recommendation rows.
- `0xF7` active timeout: gateway does not continue startup scan with `0xF7`;
  it quarantines `0xF7`, excludes it for this boot, and proves both paths:
  next candidate succeeds and scan uses that source; all candidates fail and
  `DEGRADED_SOURCE_SELECTION` emits no Helianthus-originated eBUS traffic.
- explicit address vs persisted last-known conflict: explicit `0x71` wins over
  persisted `0xF7`, active-probes before scan, and does not persist into
  default policy unless explicitly enabled.
- stale raw `source_addr.last` and any metadata-mismatched persisted source are
  ignored until current active-probe success.
- NM local address-pair authority is bound to `active_probe_passed`
  `SourceAddressSelection`; failed `0xF7`, withheld `0xFF`, and degraded
  admission cannot emit `FF 00`, `FF 02`, `07 FF`, or companion responses.
- default ordering uses the exact `HelianthusGatewayDefaultPolicy` table.
- constrained standard-description policy never returns an address outside the
  specified description and optional priority intersection.
- gateway startup standard-description policy is limited to the gateway-safe
  allowlist; broader descriptions are diagnostic-only or explicit address.
- priority-only policy filters `HelianthusGatewayDefaultPolicy` only and does
  not leak into other standard source descriptions.
- explicit address combined with standard description or priority is rejected
  as a config error.
- `PreviousValidatedSource` never changes candidate order; it is only metadata
  when the same byte is reached in normal policy order.
- gateway all-occupied/unknown behavior degrades; it never force-selects.
- explicit `0x71` succeeds on the current HA topology before M3 can merge.
- before/after transport matrix passes before M3 can merge.
- every gateway-owned bus-reaching MCP, GraphQL, semantic writer, scheduler,
  poller, and HA-driven path fails closed until active source selection is
  validated, then uses the admitted source rather than hard-coded `0x71`,
  fallback `0x31`, or any caller-selected normal source. Only
  transport-specific diagnostic MCP requests may use an explicit user source
  for one audited, non-persistent request.
- transport-specific MCP explicit source override is red/green tested as
  user-scoped and single-request: it must not be accepted by normal
  MCP/GraphQL/Portal/HA paths, persist, or mutate admitted source.
- B503 dispatcher and B503 GraphQL bridge are red/green tested independently:
  both fail closed before admission and pass only admitted source after
  `active_probe_passed`.
- Python `helianthus-vrc-explorer` external-proxy compatibility is proven with
  an actual proxy-client run and before/after gateway admitted-source snapshots,
  not only by generic adaptermux tests.
- PX01..PX12 is never accepted as source-authority proof; it remains
  wire-semantics adjunct evidence. `SAS-SRC-01..02` are the source-authority
  proof cases for external proxy-client source isolation.
- HA integration does not present degraded admission as healthy empty data.
- HA never deletes entities on the first empty payload, marks entities
  unavailable while admission is degraded, and resumes cleanup only after a
  healthy non-empty admission cycle or explicit operator acknowledgement.
- ebusreg boundary: no source-selection API appears in `helianthus-ebusreg`.

## Operational Evidence And Logging

Required log events are `startup_admission_begin`, `candidate_rejected`,
`active_probe_failed`, `source_quarantined`, `admission_degraded`, and
`source_persisted`. Bounded metrics may use only mode, reason, phase, and
transport family labels. Addresses, opcodes, provenance strings, target lists,
and top talkers are structured log/artifact fields only, never metric labels.
Artifact arrays are capped at 16 rejected candidates, 8 quarantined sources,
and 3 probe targets per candidate. Evidence must prove these events appear in
logs, expvars or equivalent metrics, GraphQL/MCP status, and the raw admission
artifact.

Live evidence must include a row for the actual `0xFF -> 0x04` field case:
candidate `0xFF`, companion `0x04`, occupant/evidence source `NETX3` or
stale-known topology entry, rejection reason, and whether the reason came from
current observation, frequent target evidence, or cache/topology.

For M3 no-eBUSd admission evidence and baseline M7 evidence, eBUSd remains
stopped and the proxy listener is disabled or mechanically guarded. The evidence
bundle must include timestamped proof before, during, and after the run:
service/addon state, absence of `ebusd` process/container, addon config,
listening sockets, absence of `127.0.0.1:8888` exposure when applicable,
proxy/adapter client state, adapter upstream single-owner state, and adaptermux
external-session count zero. Preflight aborts if eBUSd, an unexpected proxy
client, or an exposed reconnectable proxy listener is active. Coexistence with
eBUSd/proxy is a separate operator-approved run only.

Coexistence sub-runs start external clients before re-admission, mark every
external source and companion as occupied evidence, force gateway re-admission,
prove the selected gateway source and companion are disjoint, and abort on same
source/companion even without an observed collision.

## Canonical Evidence Gate Contract

Known-defect RED artifacts are valid only when they prove a tests-only RED
commit directly above the implementation parent. Each artifact records
`implementation_parent_sha`, `red_test_commit_sha`, proof that the red commit's
parent is the implementation parent, `git status --short`, changed paths between
the two commits, exact test file path, expected selected-test count,
machine-readable selected-test proof (`go test -json` or pytest collection /
JSON report), process exit code, and a grep of the expected failure string.
The red commit may touch only test/fixture paths needed to expose the defect.
Artifacts with zero selected tests, "no tests to run", unrelated compile/CI
failure, dirty parent tree, or mismatched failure string are invalid.

The docs source-table checker has a mutation-canary RED test, not just a direct
script invocation. M1 adds
`tests/test_source_address_table_checker.py::test_source_address_table_mutation_canary`,
run with `pytest --json-report`. The test copies docs to a temp tree, corrupts
one frozen source-address cell, invokes the checker with
`HELIANTHUS_OFFICIAL_SPEC_DIR`, and requires an exact row/column/source-file
failure. The green assertion is that real docs pass and the mutated copy fails
for the intended reason, distinct from missing-script/runtime failure.

Every parent/baseline artifact proves a clean tree with `git rev-parse HEAD`,
`git status --short`, `git diff --exit-code`, `git diff --cached --exit-code`,
and `git show --no-patch --format='%H %P %s'`. A dirty tree invalidates the
parent artifact unless it is explicitly the tests-only RED commit and records
its clean implementation parent.

The M3 transport expected-failure inventory is a closed JSON schema. The
top-level object has exactly `schema_version`, `parent_sha`, `topology_id`,
`case_set_version`, and `cases`; no extra keys are allowed. `cases` is exactly
88 entries ordered lexicographically from `T01` through `T88`. Each case has
exactly `case_id`, `expected_outcome`, `expected_failure_reason`, `ebusd_state`,
`proxy_state`, `source_selection_active_capable`, and
`passive_observe_first_capable`. `expected_outcome` is `pass`, `fail`, `xfail`,
or `skip`; `expected_failure_reason` is a non-empty string if and only if
`expected_outcome == "xfail"`, and `null` otherwise. `ebusd_state` is `stopped`,
`running`, or `not_applicable`; `proxy_state` is `disabled`, `guarded`,
`running`, or `not_applicable`; capability fields are booleans. The inventory
hash is SHA-256 over RFC 8785 canonical JSON bytes; PR-head validation rejects
unlisted xfail and all xpass unless an operator override artifact names the
case and reason.

The SAS validator command is
`go run ./cmd/sas-evidence-validator --manifest artifacts/sas/m3/manifest.json`
from `helianthus-ebusgateway`. The manifest records artifact paths and SHA-256
values for the expected-failure inventory, T01..T88 results, no-eBUSd
submatrix, PX report when applicable, `SAS-SRC-01..02` source-authority cases
when any coexistence/external-client source claim is made, independent
bus-boundary transcript, M3 runbook, GraphQL snapshots, and rollback logs.
Proxy/coexistence evidence uses
`helianthus-ebus-adapter-proxy/profiles/proxy-wire-semantics/px-cases.md` as
the authoritative PX01..PX12 wire-semantics case set and the
`PROXY_SEMANTICS_MATRIX_REPORT` schema from the adapter-proxy transport gate.
PX is not a substitute for the `SAS-SRC` source-authority cases.

M3 must commit `artifacts/sas/m3/RUNBOOK.md` before merge. The template includes
exact commands, required output regexes, artifact paths, rollback commands, and
waiver rules for every boot-matrix variant. The completed runbook captures
eBUSd stopped proof, proxy listener guard proof, adaptermux external-session
count, addon binary override deploy/rollback, admission artifact, GraphQL
snapshots, explicit `0x71` validation, default `0xF7` quarantine or degraded
evidence, and source-selection persistence rollback.

M3 also requires an independent bus-boundary transcript below gateway admission
logic: adapter, proxy, socket, tcpdump, or transport-shim capture. The SAS
manifest records the transcript path, SHA-256, capture point, and command
transcript. Assertions prove degraded zero traffic, the bounded `0x07/0x04`
probe, `0xF7` quarantine, and explicit `0x71` success. Gateway raw admission
artifacts, logs, status counters, and GraphQL snapshots cannot be the sole
evidence source.

## Risks

- API breakage in `helianthus-ebusgo`: this plan intentionally coordinates the
  breaking change with gateway and HA migration rather than carrying old public
  compatibility names.
- Artifact/schema consumers may depend on legacy `join` strings: mitigate with
  a coordinated breaking schema/API migration to snake_case and an HA
  integration PR in the same plan.
- Active-probe fallback can hide transport issues: mitigate with bounded
  retries, explicit counters, and degraded state when all candidates fail.
- Priority-3 "any" can be interpreted as all standard source descriptions
  instead of `HelianthusGatewayDefaultPolicy`: mitigate by freezing the exact
  p3 list and requiring explicit source description for constrained selection.
- Terminology cleanup can trip project terminology gates: assemble any banned
  historical tokens in tests if a test must verify legacy cleanup behavior.
