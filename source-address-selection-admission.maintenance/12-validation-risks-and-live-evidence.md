# Validation Risks And Live Evidence

Canonical-SHA256: `0675509fd10408c4102f15b108f8152e1fd985293f14f7f870b3bc4176bab720`

Depends on: `10-terminology-and-api-contract.md`,
`11-implementation-milestones.md`

Scope: Test cases, live-bus evidence, and operational risks for source address
selection and gateway startup admission.

Idempotence contract: Validation can be rerun against the same code and bus
state without changing persistent source selection unless gateway active
admission probe succeeds and the persistence key matches current topology.

Falsifiability gate: A reviewer can reject this chunk if any required test
case is ambiguous, depends on unspecified bus state, or cannot fail against the
current known defects.

Coverage: Unit tests, integration tests, live evidence, transport gate, schema
checks, terminology cleanup, and operational risk mitigations.

## Known Defect RED Matrix

Before implementation starts, each known defect must have a RED artifact at the
actual implementation parent SHA. The artifact is invalid unless it contains the
actual 40-hex `parent_sha` observed by `git rev-parse HEAD` in the listed
workdir before code changes. M4 cleanup gates are listed separately below
because they are future-removal checks, not current known-defect RED tests.
The `Parent SHA` cells below are artifact requirements: the executor records the
actual 40-hex parent SHA in the RED artifact before the implementation commit,
and the artifact is rejected if that value is absent or differs from the listed
workdir's `git rev-parse HEAD` at test time.

Every RED artifact must also include `implementation_parent_sha`,
`red_test_commit_sha`, proof that `red_test_commit_sha` is a direct child of
`implementation_parent_sha`, `git status --short`, `git diff --name-only
<implementation_parent_sha>..<red_test_commit_sha>`, exact test file path,
expected selected-test count, machine-readable selected-test proof (`go test
-json` or `pytest --collect-only`/report output), process exit code, and a grep
of the expected failure string. The red-test commit must contain only
tests/fixtures needed to expose the defect, enforced by a diff allowlist.
Artifacts are rejected for "no tests to run", zero pytest selection, selected
count mismatch, unrelated compile/CI failure, or failure strings that do not
match the matrix row.

Every parent/baseline artifact must prove a clean tree with `git rev-parse
HEAD`, `git status --short`, `git diff --exit-code`, `git diff --cached
--exit-code`, and `git show --no-patch --format='%H %P %s'`. A dirty tree
invalidates the parent artifact unless the artifact is explicitly the tests-only
RED commit and records its implementation parent.

Current fixed-source code paths in gateway GraphQL mutations, MCP source guards,
`internal/rpc_source`, Vaillant B503 wiring, Portal explorer, and the HA add-on
wrapper are known defects for this plan. They are expected only as parent-SHA
RED evidence at the implementation parent; after M3/M2a they are merge blockers
unless removed, admitted-source gated, or explicitly limited to
transport-specific MCP diagnostic one-request override.

| Defect | Repo | Workdir | Parent SHA | Red test | Command | Expected RED failure | Green assertion | Artifact path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `0xFF` rejected as overflow | helianthus-ebusgo | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo` | actual parent SHA in artifact | `TestSourceAddressSelector_FFCompanionWrapsTo04` | `go test ./protocol -run '^TestSourceAddressSelector_FFCompanionWrapsTo04$' -count=1` | returns `companion-target-overflows-byte` | companion is `0x04`; rejection, if any, is occupancy/unknown | `artifacts/sas/red/ebusgo-ff-companion-wrap.log` |
| passive silence admits `0xFF` | helianthus-ebusgo | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo` | actual parent SHA in artifact | `TestSourceAddressSelector_PassiveSilenceDoesNotMarkCompanionFree` | `go test ./protocol -run '^TestSourceAddressSelector_PassiveSilenceDoesNotMarkCompanionFree$' -count=1` | absent `0x04` traffic treated as free | `0xFF` withheld when `0x04` is unknown/stale | `artifacts/sas/red/ebusgo-passive-silence.log` |
| `PreviousValidatedSource` reorders policy | helianthus-ebusgo | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo` | actual parent SHA in artifact | `TestSourceAddressSelector_PreviousValidatedSourceDoesNotReorder` | `go test ./protocol -run '^TestSourceAddressSelector_PreviousValidatedSourceDoesNotReorder$' -count=1` | previous source prepended or selected outside normal order | previous source is metadata only when reached normally | `artifacts/sas/red/ebusgo-previous-source-order.log` |
| official table checker catches mutation | helianthus-docs-ebus | `/Users/razvan/Desktop/Helianthus Project/helianthus-docs-ebus` | actual parent SHA in artifact | `test_source_address_table_mutation_canary` | `pytest -q tests/test_source_address_table_checker.py::test_source_address_table_mutation_canary --json-report --json-report-file artifacts/sas/red/docs-source-table-mutation-canary.report.json` | one corrupted frozen source-address cell is not reported with exact row/column failure | real docs pass; mutated copy fails with exact row/column/source-file evidence and checker-script failure is distinguished from checker assertion failure | `artifacts/sas/red/docs-source-table-mutation-canary.log` |
| unsafe active admission probe allowed | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestStartupAdmissionProbe_AllowsOnlyDirected0704` | `go test ./... -run '^TestStartupAdmissionProbe_AllowsOnlyDirected0704$' -count=1` | `0x07FE`, `0x0F`, NM, broadcast, or mutating probe accepted | only bounded directed `0x07/0x04` accepted | `artifacts/sas/red/gateway-probe-allowlist.log` |
| `0xF7` timeout can continue scan | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestStartupAdmission_SelectedSourceF7TimeoutExcludesAndRetries` | `go test ./... -run '^TestStartupAdmission_SelectedSourceF7TimeoutExcludesAndRetries$' -count=1` | startup scan attempted after active-probe timeout | `0xF7` quarantined; next candidate or degraded zero traffic | `artifacts/sas/red/gateway-f7-timeout.log` |
| degraded admission can emit NM traffic | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestStartupAdmission_DegradedSuppressesAllHelianthusEbusTraffic` | `go test ./... -run '^TestStartupAdmission_DegradedSuppressesAllHelianthusEbusTraffic$' -count=1` | NM `FF00`/`FF02`, `07FF`, invoke, or companion response emitted | no Helianthus-originated eBUS traffic | `artifacts/sas/red/gateway-degraded-zero-traffic.log` |
| explicit `0x71` success path missing | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestStartupAdmission_Explicit71SuccessScansWith71AndCompanion76` | `go test ./... -run '^TestStartupAdmission_Explicit71SuccessScansWith71AndCompanion76$' -count=1` | explicit source not actively validated or not used | scan uses `0x71`, companion `0x76`, validate-only mode | `artifacts/sas/red/gateway-explicit71.log` |
| raw `source_addr.last` override/mismatch | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestStartupAdmission_LegacyRawSourceAddrLastIgnored` | `go test ./... -run '^TestStartupAdmission_LegacyRawSourceAddrLastIgnored$' -count=1` | legacy raw byte influences selection | raw byte diagnostic only until current active probe succeeds | `artifacts/sas/red/gateway-source-addr-last.log` |
| fixed or fallback source authority bypasses admission | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestGatewayBusReachingPathsUseAdmittedSource` | `go test ./... -run '^TestGatewayBusReachingPathsUseAdmittedSource$' -count=1` | any MCP, GraphQL, semantic, scheduler, poller, or HA-driven gateway path emits hard-coded `0x71`, fallback `0x31`, or caller-selected source before admission | normal gateway-owned paths fail closed until `active_probe_passed`, then use admitted source; only transport-specific MCP diagnostic override can use an explicit user source for one request | `artifacts/sas/red/gateway-source-authority.log` |
| transport-specific MCP override leaks into normal source authority | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestTransportSpecificMCPExplicitSourceOverrideIsUserScoped` | `go test ./... -run '^TestTransportSpecificMCPExplicitSourceOverrideIsUserScoped$' -count=1` | explicit override is accepted by normal MCP/GraphQL/Portal/HA paths, persists, or mutates admitted source | only transport-specific diagnostic MCP accepts one explicit source for one audited non-persistent request | `artifacts/sas/red/gateway-mcp-explicit-source-override.log` |
| B503 dispatcher hard-coded source | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestB503DispatcherUsesAdmittedSourceOrFailsClosed` | `go test ./cmd/gateway -run '^TestB503DispatcherUsesAdmittedSourceOrFailsClosed$' -count=1` | B503 dispatcher emits `0x71` or any configured constant independent of admission | B503 fails closed before admission, then emits only admitted source | `artifacts/sas/red/gateway-b503-source-authority.log` |
| B503 GraphQL bridge hard-coded source | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestB503GraphQLBridgeUsesAdmittedSource` | `go test ./cmd/gateway ./graphql -run '^TestB503GraphQLBridgeUsesAdmittedSource$' -count=1` | GraphQL bridge reaches B503 dispatcher with `0x71`, `0x31`, or caller-selected source independent of admission | B503 GraphQL bridge fails closed before admission, then passes only admitted source into dispatcher | `artifacts/sas/red/gateway-b503-graphql-bridge-source-authority.log` |
| NM runtime hard-coded gateway source | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestNMRuntimeUsesAdmittedSourceAfterAdmission` | `go test ./internal/nm_runtime -run '^(TestNMRuntimeUsesAdmittedSourceAfterAdmission|TestNMRuntimeFailsClosedBeforeAdmission)$' -count=1` | NM emits `FF00`/`FF02` from `rpc_source.Gateway` or fixed `0x71` | NM fails closed before admission/degraded, then uses only admitted source | `artifacts/sas/red/gateway-nm-source-authority.log` |
| Portal explorer independent source override | helianthus-ebusgateway | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestPortalExplorerRejectsSourceOverride` | `go test ./portal -run '^(TestPortalExplorerUsesAdmittedSource|TestPortalExplorerRejectsSourceOverride)$' -count=1` | Portal default, body, or query source overrides admitted source | Portal uses admitted source after admission, rejects source override, and fails closed before admission/degraded | `artifacts/sas/red/gateway-portal-source-authority.log` |
| adaptermux external client source isolation | helianthus-ebusgateway + helianthus-ebus-adapter-proxy | `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgateway` | actual parent SHA in artifact | `TestAdaptermuxExternalClientSourceDoesNotAffectAdmittedSource` | `go test ./internal/adaptermux -run '^TestAdaptermuxExternalClientSourceDoesNotAffectAdmittedSource$' -count=1` | external proxy client source is rejected because it differs from admitted source, or it mutates gateway admitted source | external proxy sessions may use their own source while gateway active path remains admitted-source-only | `artifacts/sas/red/adaptermux-external-source-isolation.log` |
| add-on raw source reuse bypasses gateway validation | helianthus-ha-addon | `/Users/razvan/Desktop/Helianthus Project/helianthus-ha-addon` | actual parent SHA in artifact | `test_source_addr_auto_does_not_reuse_raw_state_file` | `pytest -k 'source_addr_auto_does_not_reuse_raw_state_file'` | wrapper promotes `/data/source_addr.last` into `-source-addr` | `auto` passes source-selection default policy only | `artifacts/sas/red/addon-source-addr-state.log` |
| HA healthy-empty cleanup | helianthus-ha-integration | `/Users/razvan/Desktop/Helianthus Project/helianthus-ha-integration` | actual parent SHA in artifact | `test_admission_degraded_empty_inventory_blocks_cleanup` | `pytest -k 'admission_degraded_empty_inventory_blocks_cleanup'` | degraded/empty fixture lacks repair or permits stale cleanup | repair/diagnostic created; cleanup suppressed | `artifacts/sas/red/ha-empty-cleanup.log` |

## Required Unit Tests

`helianthus-ebusgo`:

- default policy order starts with `0xFF`, `0x7F`, `0x3F`, `0x1F`;
- exact `HelianthusGatewayDefaultPolicy` is
  `FF,7F,3F,1F,F7,77,37,17,07,11,31,00`;
- standard source-address table has 25 static rows matching the referenced docs
  anchor, table version, and Markdown table hash;
- docs source-address table CI compares every row with
  `docs/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md` and companion arithmetic with
  `docs/Spec_Prot_12_V1_3_1_E.en.md`;
- docs CI runs with explicit spec root:
  `HELIANTHUS_OFFICIAL_SPEC_DIR=/Users/razvan/Desktop/Helianthus\ Project/docs`
  and records SHA-256 for every official spec file read. Repo-only CI must use a
  committed excerpt fixture with hashes and provenance instead of comparing
  docs against docs;
- docs source-address table CI also compares priority-index /
  arbitration-nibble mapping against
  `docs/Spec_Prot_12_V1_3_1_E.en.md:320-349`;
- docs hash uses SHA-256 over exact normalized Markdown table bytes: header row
  through last data row, UTF-8, LF, trailing spaces stripped per line, one
  terminal LF;
- `official_description_summary` matches a non-self-ratifying local official
  spec fixture, while `canonical_description` is the enum consumed by code;
- standard description, free-use flag, and recommended-for are stored and
  tested separately, including `0x07` with `recommended_for=none`;
- priority mapping covers all addresses: p0 low nibble `0x0`, p1 `0x1`,
  p2 `0x3`, p3 `0x7`, p4 `0xF`;
- official arbitration-rank tests prove p0 outranks p1, p1 outranks p2, p2
  outranks p3, p3 outranks p4, and lower source byte wins within otherwise
  equal contention;
- p4 priority-only default returns only `0xFF`, `0x7F`, `0x3F`, or
  `0x1F`;
- p3 priority-only default returns only `0xF7`, `0x77`, `0x37`, `0x17`,
  `0x07`;
- p1 priority-only default returns only `0x11` or `0x31`;
- p0 priority-only default returns only `0x00`;
- priority-only gateway policy filters `HelianthusGatewayDefaultPolicy`, not
  all standard descriptions;
- no thermostat/mixer/heating-source source description appears in the
  eBUS-generic source-description enum;
- description-only tests for PC, bus interface, heating regulator, heating
  circuit regulator, combustion controller, clock module, and not-preallocated
  return only exact standard table rows for those descriptions;
- free-use recommendation rows are not returned by preallocated
  heating-regulator or combustion-controller description tests;
- p4 priority-only default excludes `0x0F`;
- description+priority tests return only the source-description/priority
  intersection;
- explicit address combined with source description or priority is a config
  error;
- explicit `0x71` returns validate-only mode and ignores persisted `0xF7`;
- explicit invalid source returns `explicit-source-invalid`;
- all 25 companion mappings are tested, including `0xFF -> 0x04` and
  `0xF7 -> 0xFC`;
- `0xFF` is not rejected for overflow;
- occupied, unknown, or stale-known `0x04` rejects or withholds `0xFF` for
  companion occupancy/unknown-state;
- `0xFF` validation table-tests `observed_free`, `observed_occupied`,
  `unknown`, and `stale_known_device` for `0x04` with exact reason strings;
- `observed_free` can be created only by same-cycle successful active
  validation, explicit operator-exclusive reservation, or isolated lab fixture;
- excluded `0xF7` is not selected after active-probe feedback.

`helianthus-ebusgateway`:

- adapter-direct remains classified as source-selection capable when the
  underlying transport is ENH/ENS;
- adapter-direct ENH/ENS separately reports
  `source_selection_active_capable` and `passive_observe_first_capable`;
- `TestStartupAdmission_SourceSelectionActiveCapableDoesNotImplyPassiveObserveFirstCapable`;
- direct ENH/ENS with no passive occupancy snapshot and no configured/current
  bounded probe target enters degraded zero-traffic state;
- direct ENH/ENS with a configured/current bounded probe target emits only the
  first-implementation directed `0x07/0x04` admission probe;
- documented/stale lab topology alone does not create an admission probe target
  and degrades with zero eBUS traffic unless materialized as explicit operator
  configuration;
- `TestAdmissionProbeTargetValidationRejectsInvalidTargets` covers `0xFE`,
  `0xAA`, `0xA9`, initiator-pattern destinations, selected source, selected
  companion, and targets without configured/current positive provenance;
- `TestStartupAdmission_PassiveUnavailablePreProbeEligibility` covers the
  no-passive branches: known/stale source or companion rejects without probing;
  unknown without reservation/target degrades; reservation or current bounded
  target may probe;
- startup admission passes the intended policy to ebusgo;
- gateway startup rejects non-allowlisted standard descriptions unless the
  operator uses explicit address or diagnostic-only mode;
- explicit source configuration maps to explicit validate-only;
- persisted `source_addr.last` cannot override explicit source configuration;
- stale raw `source_addr.last` is ignored and logged but not passed as
  `PreviousValidatedSource`;
- persisted-source metadata mismatch tests cover transport, adapter/proxy
  identity, companion, policy fingerprint, schema version, validation type, and
  topology freshness, instance, config source, and explicit-persistence flag;
- `PreviousValidatedSource` preserves normal candidate order and never prepends
  or reorders the default policy;
- active-probe timeout for selected source records a failure and does not allow
  continued startup scan, semantic polling, NM traffic, MCP/GraphQL bus invoke,
  or companion response with any unvalidated source;
- active admission probe allowlist accepts only bounded directed `0x07/0x04`
  identity in the first implementation and rejects `0x07FE`, `0x07FF`, all
  `0x0F` test commands, NM `0xFF` messages, broadcasts, memory writes, mutating
  services, full-range probes, and `system_nm_runtime` bypasses;
- `TestStartupAdmission_SelectedSourceF7TimeoutExcludesAndRetries`;
- `TestStartupAdmission_SelectedSourceF7TimeoutNextCandidateSucceedsAndScans`;
- `TestStartupAdmission_AllCandidatesTimeoutDegradesWithoutScan`;
- `TestStartupAdmission_DegradedSuppressesAllHelianthusEbusTraffic`;
- `TestStartupAdmission_DoesNotPersistF7AfterActiveProbeTimeout`;
- `TestStartupAdmission_DoesNotPersistUntilInitialScanCollisionClean`;
- `TestStartupAdmission_Explicit71OverridesPersistedF7`;
- `TestStartupAdmission_Explicit71SuccessScansWith71AndCompanion76`;
- `TestStartupAdmission_Explicit71ValidationFailureDoesNotScan`;
- `TestResolveAdmissionPath_EbusdTCPRemainsStaticFallback`;
- `TestGatewayBusReachingPathsUseAdmittedSource` covers MCP invoke, GraphQL
  invoke, Portal explorer, Vaillant B503 dispatcher/bridge, NM runtime emits,
  semantic writers, scheduler/time-program writers, poller writes, HA-driven
  writes, and every gateway-owned GraphQL mutation alias family;
- `TestGraphQLBusReachingMutationsUseAdmittedSourceOrFailClosed` covers config,
  boiler, zone time-program, and DHW time-program aliases in both camelCase and
  snake_case forms;
- `TestB503DispatcherUsesAdmittedSourceOrFailsClosed` and
  `TestB503GraphQLBridgeUsesAdmittedSource` prove B503 paths cannot use
  hard-coded `0x71`;
- `TestNMRuntimeUsesAdmittedSourceAfterAdmission` and
  `TestNMRuntimeFailsClosedBeforeAdmission` prove NM `FF00`/`FF02` emits use
  admitted source only after admission;
- `TestPortalExplorerUsesAdmittedSource` and
  `TestPortalExplorerRejectsSourceOverride` prove Portal explorer is a normal
  gateway-owned bus-reaching surface, not an override surface;
- `TestAdaptermuxExternalClientSourceDoesNotAffectAdmittedSource` and
  `SAS-SRC-01..02` prove adaptermux/proxy clients such as the Python
  `helianthus-vrc-explorer` application and ebusd may use their own source on
  their own session without changing gateway admitted source. PX01..PX12 is
  adjunct wire-semantics evidence only and does not prove source authority;
- `TestTransportSpecificMCPExplicitSourceOverrideIsUserScoped` proves only
  transport-specific diagnostic MCPs may use a non-admitted source, and only for
  one explicit, audited, non-persistent user request;
- M3 schema tests prove additive `source_selection` and
  `busSummary.status.bus_admission.source_selection` exist and no temporary
  public `busAdmission` alias is introduced.
- M4 schema tests reject `admission_path_selected`, enum `join`, enum
  `override`, `join_result`, `joiner_selection`, GraphQL/MCP old admission
  aliases, and expvar `startup_admission_consecutive_rejoin_failures` on
  source-selection admission/status surfaces.

`helianthus-ha-integration`:

- setup with `devices=[]`, `zones=[]`, `dhw=null`, and degraded admission
  creates a repair/diagnostic surface;
- missing `bus_admission.source_selection` creates `schema_incompatible`;
- degraded admission creates `admission_degraded`;
- healthy-looking empty inventory without trusted admission creates
  `empty_inventory_untrusted`;
- stale cleanup is suppressed while admission is degraded;
- existing entities are not removed solely because gateway inventory is empty;
- entities are marked unavailable during degraded admission and cleanup resumes
  only after two consecutive healthy non-empty coordinator refreshes or
  explicit operator acknowledgement;
- admission preflight runs before stale cleanup and persists
  `admission_trusted=false` until source-selection status is healthy.
- climate, water-heater, zone schedule helper, and DHW schedule helper writes
  remove fixed `0x31` fallback and fail closed on degraded/untrusted admission.

`helianthus-ebusreg`:

- scan tests remain unchanged except for any boundary assertion that no
  selection API is imported.

## M4 Cleanup Gates

These are executable removal checks for the future public cleanup milestone, not
known-defect RED tests at the initial implementation parent SHA.

| Gate | Repo | Command | Required assertion |
| --- | --- | --- | --- |
| gateway legacy schema rejection | helianthus-ebusgateway | `go test ./... -run '^(TestSourceSelectionM4RejectsLegacyAdmissionFields|TestStartupSourceSelectionExpvarSnapshot)$' -count=1` | old admission fields/enums and old expvar names fail; new snake_case fields and new expvars pass |
| HA no legacy admission dependency | helianthus-ha-integration | `pytest -k 'source_selection_schema_no_legacy_admission_fields or writes_use_admitted_source_without_fallback'` | HA uses only `bus_admission.source_selection` and has no `0x31` fallback |
| docs/source terminology cleanup | helianthus-docs-ebus | `./scripts/ci_local.sh` | current docs reject legacy source-selection vocabulary except historical migration notes |
| ebusgo/gateway public symbol cleanup | helianthus-ebusgo + helianthus-ebusgateway | `./scripts/ci_local.sh` in each repo | old selector symbols and old source-selection public aliases are absent |
| add-on source config cleanup | helianthus-ha-addon | `pytest -k 'source_addr_auto_does_not_reuse_raw_state_file or source_addr_exact_maps_to_explicit_validate_only'` | wrapper cannot promote or persist raw `source_addr.last` as active authority |

## Required Live Evidence

The live evidence target is the Home Assistant runtime with adapter-direct ENS.
Current observed state before this plan:

- source `0xF7` selected during startup admission;
- active reads with source `0xF7` timed out;
- explicit reads with source `0x71` succeeded;
- eBUSd was stopped during investigation.

Acceptance evidence for M3 gateway merge:

- default startup does not keep using `0xF7` after active-probe timeout;
- raw artifact shows source quarantine, retry, or
  `DEGRADED_SOURCE_SELECTION`;
- explicit `0x71` validate-only succeeds on the current HA topology; failure
  blocks the M3 PR and escalates;
- cold boot / power-cycle evidence covers persistence-preserved and
  persistence-cleared cases, silent-bus retry/backoff, and operator-triggered
  re-admission;
- boot matrix covers addon restart, HA host reboot, adapter power-cycle, and
  bus/HVAC power-cycle, each with persistence-preserved and persistence-cleared
  variants where practical;
- `0xFF` behavior includes an artifact row for candidate `0xFF`, companion
  `0x04`, occupant/evidence source `NETX3` or stale-known topology entry,
  rejection reason, and provenance category;
- MCP status and raw artifact freeze first; GraphQL parity reports the same
  source-selection state without legacy naming.

Evidence bundle must include commit SHA, full gateway config, timestamped proof
that eBUSd is stopped before/during/after no-eBUSd admission runs,
process/container absence, addon config, listening sockets, proxy listener
disabled/guarded state, adapter upstream single-owner state, adaptermux
external-session count zero, raw admission artifact, selected source, rejected
candidates, quarantined sources, active probe target/opcode, timeout/success
logs, GraphQL snapshots, and HA integration state after restart. Any eBUSd/proxy
coexistence run is separate, operator-approved, and restores eBUSd/proxy to the
baseline stopped/disabled state afterward.

If the coexistence evidence claims Python `helianthus-vrc-explorer`
compatibility, the bundle must include an explicit run of that application as an
external adaptermux/proxy client with a configured per-session source: command
line, client transcript, bus-boundary capture, adaptermux session/source
snapshot, gateway `bus_admission.source_selection` snapshot before and after,
and proof that the client source did not update admitted source. The M3 runbook
and manifest must record exact paths for these artifacts under
`artifacts/sas/m3/vrc-explorer-proxy-client/`.

## Transport Gate

Transport-gate scope is required because this plan changes startup admission
behavior and active source selection.

Rows or cases must cover:

- ENH direct;
- ENS direct;
- adapter-direct ENH/ENS;
- UDP-plain if still classified source-selection capable;
- TCP-plain if still classified source-selection capable;
- ebusd-tcp static fallback, unchanged except for naming where visible.

Required artifacts:

- parent-SHA baseline matrix captured before M3 code edits;
- parent-SHA expected-failure inventory captured before M3 code edits, with
  hash recorded in the PR artifact;
- expected-failure inventory schema:
  top-level object with exactly `schema_version`, `parent_sha`, `topology_id`,
  `case_set_version`, and `cases`; no extra keys are allowed. `cases` is an
  array of exactly 88 objects ordered lexicographically by `case_id` from `T01`
  through `T88`. Each case object has exactly `case_id`, `expected_outcome`,
  `expected_failure_reason`, `ebusd_state`, `proxy_state`,
  `source_selection_active_capable`, and `passive_observe_first_capable`.
  Allowed values are: `expected_outcome` = `pass`, `fail`, `xfail`, or `skip`;
  `expected_failure_reason` is a non-empty string if and only if
  `expected_outcome == "xfail"`, and is `null` otherwise; `ebusd_state` =
  `stopped`, `running`, or `not_applicable`;
  `proxy_state` = `disabled`, `guarded`, `running`, or `not_applicable`;
  capability fields are booleans. Canonical hash is SHA-256 over RFC 8785 JSON
  canonicalization bytes, with UTF-8 encoding, no trailing whitespace, and no
  optional/null fields beyond those named here;
- PR-head full T01..T88 matrix with the same topology and per-case expected
  eBUSd/proxy state;
- separate no-eBUSd adapter-direct admission submatrix with eBUSd stopped and
  reconnectable proxy listeners disabled or mechanically guarded;
- transport capability snapshot with `source_selection_active_capable` and
  `passive_observe_first_capable` as separate columns for ENH direct, ENS
  direct, adapter-direct ENH/ENS, UDP-plain, TCP-plain, and ebusd-tcp;
- before/after matrix result filenames containing commit SHA;
- explicit row proving ebusd-tcp does not instantiate the selector;
- explicit row proving adapter-direct ENS runs selector before scan;
- explicit row proving adapter-direct ENH/ENS without passive evidence and
  without configured/current bounded target degrades with zero eBUS traffic;
- explicit row proving active-probe failure suppresses startup scan;
- explicit row proving source persistence is not updated after active failure.
- SAS-specific validator output proving all required metadata/submatrices are
  present. The validator command is
  `go run ./cmd/sas-evidence-validator --manifest artifacts/sas/m3/manifest.json`
  from `helianthus-ebusgateway`; the manifest names every artifact path and
  hash, including `SAS-SRC-01..02` whenever any coexistence/external-client
  source-authority claim is made. The existing generic transport gate is not
  sufficient by itself.
- `PX01..PX12` adjunct wire-semantics results for any proxy/coexistence run,
  unless the run is explicitly documented as observational-only with no
  proxy-semantics claim. PX evidence does not prove gateway admitted-source
  immutability or external-client source authority isolation. PX evidence uses
  `helianthus-ebus-adapter-proxy/profiles/proxy-wire-semantics/px-cases.md` as
  the authoritative case set, records its SHA-256 in the SAS manifest, and
  consumes the same `PROXY_SEMANTICS_MATRIX_REPORT` schema enforced by
  `helianthus-ebus-adapter-proxy/scripts/transport_gate.sh`.
- `SAS-SRC-01..02` source-authority coexistence cases for any claim that
  external adaptermux/proxy clients can use their own per-session source while
  gateway active path remains admitted-source-only:
  `SAS-SRC-01` runs a generic ENS/ENH/TCP external proxy session with a
  non-admitted source, captures adaptermux session/source state, proves
  gateway `bus_admission.source_selection.selected_source` is unchanged
  before/after, and correlates the session with an independent bus-boundary
  transcript. `SAS-SRC-02` repeats the same proof with the Python
  `helianthus-vrc-explorer` application when compatibility is claimed. The SAS
  evidence validator fails any coexistence claim unless the relevant
  `SAS-SRC` cases are present, passing, hashed, and listed in the manifest.

Unexpected xfail/xpass results block the M3 gateway PR unless the operator
records an explicit transport-gate override.
PR-head validation rejects any xfail not present in the locked parent inventory
and rejects every xpass unless an operator override artifact names the case and
reason.

## M3 Evidence Runbook Gate

M3 cannot merge on a deferred M7 runbook. The M3 evidence artifact must contain
a committed template at `artifacts/sas/m3/RUNBOOK.md` with exact commands,
required output regexes, artifact paths, rollback commands, and waiver rules for
each boot-matrix variant. The completed runbook includes command transcripts
and paths for:

- eBUSd stopped proof before, during, and after the run;
- proxy listener absence or mechanical guard proof;
- adaptermux external-session count zero;
- addon binary override deploy and rollback;
- admission artifact capture path;
- GraphQL snapshots for source-selection status;
- explicit `0x71` validate-only run;
- default startup `0xF7` quarantine/retry/degraded evidence;
- rollback of binary, config, quarantine, and source-selection persistence.
- independent bus-boundary transcript: adapter/proxy/tcpdump/socket capture or
  transport shim write log with command transcript and SHA-256. Assertions cover
  zero traffic in degraded state, the `0x07/0x04` admission probe, `0xF7`
  quarantine, and explicit `0x71` success.

## Expvar Migration Inventory

M4 must cover the complete current `helianthus-ebusgateway` expvar inventory.
The default decision is rename; retaining an old `startup_admission_*` key
requires a row-specific rationale and an explicit retention test.

| Current key | Target key | Decision |
| --- | --- | --- |
| `startup_admission_degraded_total` | `startup_source_selection_degraded_total` | rename |
| `startup_admission_state` | `startup_source_selection_state` | rename |
| `startup_admission_override_active` | `startup_source_selection_explicit_source_active` | rename |
| `startup_admission_warmup_events_seen` | `startup_source_selection_warmup_events_seen` | rename |
| `startup_admission_warmup_cycles_total` | `startup_source_selection_warmup_cycles_total` | rename |
| `startup_admission_override_bypass_total` | `startup_source_selection_explicit_validate_only_total` | rename |
| `startup_admission_override_conflict_detected` | `startup_source_selection_explicit_source_conflict_detected` | rename |
| `startup_admission_degraded_escalated` | `startup_source_selection_degraded_escalated` | rename |
| `startup_admission_degraded_since_ms` | `startup_source_selection_degraded_since_ms` | rename |
| `startup_admission_consecutive_rejoin_failures` | `startup_source_selection_consecutive_failures` | rename |
| `startup_admission_degraded_cumulative_ms` | `startup_source_selection_degraded_cumulative_ms` | rename |

## Terminology Gate

After M4, active code and current docs should not contain the legacy source
selection API vocabulary. The check should cover:

- `helianthus-ebusgo`;
- `helianthus-ebusgateway`;
- `helianthus-docs-ebus`;
- `helianthus-ebusreg`;
- `helianthus-execution-plans`, excluding historical migration references.

The exact regex should be implemented carefully so it does not conflict with
the repository's existing terminology gate tests.

Required gate shape:

- regex and allowlist are documented: active code/docs reject at least
	  `\bJoiner\b|\bJoinBus\b|\bJoinConfig\b|\bJoinResult\b|\bJoinMetrics\b|\bJoinStateStore\b|\bNewJoiner\b|\.Join\(|\bjoiner\b|\bjoinbus\b|\bgentlejoin\b|\bjoin_result\b|\bjoiner_selection\b|\badmission_path_selected\b|\bstartup_admission_consecutive_rejoin_failures\b|\bbusAdmission\b|\bcompanionTarget\b|\bsourceSelection\b|\bexplicitValidateOnly\b`;
- the inventory also covers `gentle-join`, `join-capable`,
  `startup_admission_override_active`,
  `startup_admission_override_bypass_total`,
  `startup_admission_override_conflict_detected`, `-source-addr`,
  `source_addr`, `source_addr_state_file`, and
  `daemonStatus.initiatorAddress`, and `daemon_status.initiator_address`; each
  is either migrated or retained with an explicit public-surface rationale;
- schema/API red tests prove old fields and enum values `join` and `override`
  fail on source-selection admission/status surfaces;
- red/green tests exist;
- tests that mention historical legacy words assemble tokens from split
  substrings to avoid tripping the repository terminology gate;
- historical references are allowed only under execution-plan migration notes.

## Risks And Mitigations

Risk: cross-repo API breakage.

Mitigation: this plan intentionally coordinates breaking API changes across
ebusgo, gateway, docs, and HA; gateway/HA PRs migrate to snake_case and CI
proves no old public names remain.

Risk: schema consumers depend on legacy admission strings or camelCase fields.

Mitigation: schema/API migration is explicit and breaking in this plan; HA
integration is in scope and must be green against the new schema before public
legacy/camelCase fields are removed.

Risk: source fallback hides a real transport failure.

Mitigation: active admission probe FSM has one probe per candidate, eight
candidates per boot, source quarantine, and degraded state with no startup scan
after all-candidate failure.

Risk: priority-only selection leaks into non-default standard descriptions.

Mitigation: docs freeze `HelianthusGatewayDefaultPolicy`; priority-only
filters that policy only.

Risk: `0xFF` is protocol-valid but unsafe on this installation because `0x04`
may be occupied.

Mitigation: reject or withhold `0xFF` based on observed/unknown/stale-known
companion occupancy, not overflow, and expose the rejection reason.

Risk: persisted last-known source surprises operators.

Mitigation: explicit address validate-only mode ignores persisted source for
selection, and persistence is gateway-owned metadata committed only after
active admission probe success.

Risk: legacy raw `source_addr.last` or metadata-mismatched persisted state
reintroduces the failed `0xF7` path.

Mitigation: raw legacy state is diagnostic-only migration input; mismatched
metadata invalidates the hint and tests prove it is not used or rewritten until
current active-probe success.

Risk: bus silence after power-cycle is misread as free addresses.

Mitigation: occupancy state distinguishes `unknown` from `observed_free`; bus
silence leads to `bus_silent_occupancy_unknown` degraded state, not a forced
source.
